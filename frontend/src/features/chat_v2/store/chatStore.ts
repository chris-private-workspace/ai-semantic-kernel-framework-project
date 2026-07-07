/**
 * File: frontend/src/features/chat_v2/store/chatStore.ts
 * Purpose: Zustand store for chat-v2 — Turn-based reducer for SSE LoopEvent stream.
 * Category: Frontend / chat_v2 / store
 * Scope: Phase 50 / Sprint 50.2 + Phase 57.21 (Day 1 — Turn block sequence rewrite)
 *
 * Description:
 *   Single Zustand store holding session metadata + Turn[] + SessionList sidebar
 *   state + Sprint 57.x cross-cutting slices (rawEvents / approvals / verifications
 *   / subagents) that are still consumed by non-chat components.
 *
 *   Sprint 57.21 mergeEvent rewrite — folds 14 (Sprint 57.66: 18) SSE event types into Turn blocks:
 *     - loop_start         → set sessionId + status=running (preserve turns)
 *     - turn_start         → push new AgentTurn with empty blocks + null metadata
 *     - llm_request        → update active AgentTurn.tokensIn + model (Sprint 57.131)
 *     - llm_response       → append ThinkingBlock (if thinking) + ToolBlock per tool_call
 *     - tool_call_request  → defensive append ToolBlock if missing (rare path)
 *     - tool_call_result   → update matching ToolBlock status/output/durationMs
 *     - loop_end           → set status=completed + active turn stopReason
 *     - loop_terminated    → flip pending tool→error + terminated badge + status=completed
 *     - approval_requested → push HITLTurn + update approvals dict (dual-emit)
 *     - approval_received  → update HITLTurn decision + approvals dict (dual-emit)
 *     - guardrail_triggered → rawEvents only (Phase-2+ may render warning)
 *     - context_compacted  → push CompactionMarkerTurn into timeline (Sprint 57.159; Cat 4 L2→L3)
 *     - prompt_built / state_checkpointed / tripwire_triggered
 *                          → rawEvents only (Sprint 57.66; rich render DEFERRED A-5c)
 *     - verification_*     → append VerificationBlock + verifications slice (dual-emit)
 *     - subagent_spawned   → append/extend SubagentForkBlock + subagents slice (dual-emit)
 *     - subagent_completed → update SubagentEntry.status + subagents slice (dual-emit)
 *     - subagent_child     → append ChildTurnEvent to the node (Tree expands; Sprint 57.96)
 *
 *   Dual-emit pattern preserves Sprint 57.11 inline VerificationPanel + Sprint 57.12
 *   SubagentTree behavior (they consume verifications + subagents slices) while
 *   ALSO feeding the new Turn block render path for /chat-v2 mockup-fidelity.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.3)
 * Last Modified: 2026-06-16
 *
 * Modification History:
 *   - 2026-07-07: Sprint 57.159 — context_compacted pushes a CompactionMarkerTurn (was rawEvents-only; Cat 4 L2→L3)
 *   - 2026-06-16: Sprint 57.131 — llm_request stamps per-turn model on the AgentTurn (Inspector model row)
 *   - 2026-06-16: Sprint 57.130 — +loop_terminated case (flip pending tool→error + terminated badge)
 *   - 2026-06-16: Sprint 57.126 — +loadSessionHistory (fetch /events → replay) + user_message case
 *   - 2026-06-15: Sprint 57.120 — turn_start carries activeSkill onto AgentTurn (Inspector row)
 *   - 2026-06-13: Sprint 57.110 B4 — child guardrail_triggered projection (reason→text + action)
 *   - 2026-06-12: Sprint 57.108 — HITL tool/reason + turn traceId/spanId/tokens/duration captures
 *   - 2026-06-12: Sprint 57.107 B3 — +loadSessions (real GET /sessions → Session[]; replaces fixture)
 *   - 2026-06-11: Sprint 57.103 B2b — SubagentEntry +mode +tokensUsed; child text += inner.text
 *   - 2026-06-11: Sprint 57.101 B1 — message_injected → UserTurn(injected) (mid-run injection render)
 *   - 2026-06-10: Sprint 57.100 — HITLTurn carries kind from wire (verification reject UI branch)
 *   - 2026-06-09: Sprint 57.96 — +subagent_child case → SubagentNode.childEvents (Scope B turn-stream)
 *   - 2026-06-06: chat-v2 honest testing surface — default mode echo_demo→real_llm; +currentModel (from llm_request); reset() zeroes _turnCounter (CHANGE-054)
 *   - 2026-06-03: Sprint 57.75 A-5 — +spans / memoryOps derived slices + span_started/span_ended/memory_accessed cases (Inspector Trace + Memory tabs)
 *   - 2026-06-02: Sprint 57.69 A-3b slice 2 — agent_handoff now pivots session (pivotSession + handoffBanner state)
 *   - 2026-06-02: Sprint 57.68 A-3b — +agent_handoff passthrough case (rawEvents-only, Cat 11)
 *   - 2026-06-02: Sprint 57.66 — +4 diagnostic event passthrough cases (rawEvents-only)
 *   - 2026-05-17: Sprint 57.21 Day 1 — mergeEvent SSE → Turn block sequence; dual-emit
 *   - 2026-05-10: Sprint 57.12 US-6 — subagents slice + reducers (AD-Cat11-SSEEvents)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.3)
 *
 * Related:
 *   - ../types.ts (LoopEvent + Turn + Block + Session)
 *   - ../hooks/useLoopEventStream.ts (calls mergeEvent per SSE chunk)
 *   - ../../subagent/types.ts (SubagentNode UI tree node — Sprint 57.12)
 *   - reference/design-mockups/page-chat.jsx (Turn block visual target)
 */

import { create } from "zustand";

import type { ChildTurnEvent, SubagentNode } from "../../subagent/types";
import type { VerificationEvent } from "../../verification/types";
import {
  fetchSessionEvents,
  listSessions,
  type SessionListApiItem,
} from "../services/chatService";
import type {
  AgentTurn,
  ApprovalEntry,
  Block,
  ChatMode,
  ChatStatus,
  HITLTurn,
  LoopEvent,
  RiskSeverity,
  Session,
  SessionStatusUI,
  SubagentEntry,
  SubagentForkBlock,
  Turn,
  UserMessageEvent,
  UserTurn,
} from "../types";

/**
 * Sprint 57.69 A-3b slice 2: transition banner shown after a Cat 11 HANDOFF
 * pivots the active session to the child. Sourced from the `agent_handoff`
 * SSE event (target_agent + reason). Cleared on the next `loop_start` (the
 * child session's first turn) or via `dismissHandoffBanner`.
 */
export type HandoffBanner = { targetAgent: string; reason: string };

/**
 * Sprint 57.75 A-5 Trace tab: one OTel span derived from the SpanStarted /
 * SpanEnded SSE pair. `durationMs` is null while the span is still open (only
 * SpanStarted seen); set + status flips to "done" on SpanEnded. The Inspector
 * Trace tab folds these into a waterfall by `parentSpanId`.
 */
export type SpanNode = {
  spanId: string;
  parentSpanId: string;
  spanType: string;
  spanName: string;
  durationMs: number | null;
  status: "running" | "done";
};

/**
 * Sprint 57.75 A-5 Memory tab: one memory access derived from a MemoryAccessed
 * SSE event. `at` is the client receive time (the backend event carries no
 * timestamp — honest client-side stamp, not a fabricated server time).
 */
export type MemoryOp = {
  op: string;
  scope: string;
  timeScale: string;
  key: string;
  summary: string;
  at: number;
};

/**
 * Sprint 57.140 Inspector Todos tab: one structured plan item, narrowed from the
 * wire `todos_updated` event's generic `Record<string, unknown>[]` (the wire avoids
 * a 2nd named codegen element; the FE owns this hand-written shape). status drives
 * the per-row badge color.
 */
export type TodoItem = {
  id: string;
  title: string;
  status: "pending" | "in_progress" | "completed";
  // Sprint 57.156 DAG: ids of prerequisite todos (optional; older events omit it).
  depends_on?: string[];
};

type ChatStoreState = {
  // Session metadata (preserved)
  sessionId: string | null;
  status: ChatStatus;
  totalTurns: number;
  stopReason: string | null;
  errorMessage: string | null;
  mode: ChatMode;
  // Honest-surface: model name from the latest llm_request (null until the first
  // LLM call). Drives the ChatHeader model badge instead of a hardcoded fixture
  // ("claude-haiku-4-5"), so the badge reflects the ACTUAL model that ran.
  currentModel: string | null;

  // Sprint 57.69: HANDOFF transition banner (null when no active handoff notice)
  handoffBanner: HandoffBanner | null;

  // Sprint 57.21: Turn-based rendering replaces messages: Message[]
  turns: Turn[];

  // Sprint 57.21: SessionList sidebar state (Day 3 populates from fixture)
  sessions: Session[];
  activeSessionId: string | null;

  // Preserved cross-cutting slices (Sprint 57.x components still use these)
  rawEvents: LoopEvent[];
  approvals: Record<string, ApprovalEntry>;
  verifications: VerificationEvent[];
  subagents: SubagentNode[];

  // Sprint 57.75: Inspector Trace + Memory derived slices (from SSE span/memory events)
  spans: SpanNode[];
  memoryOps: MemoryOp[];

  // Sprint 57.140: the current durable todo list (research #1 task primitive),
  // replaced wholesale on each todos_updated SSE event; feeds the Inspector Todos tab.
  todos: TodoItem[];

  // Actions
  setMode: (m: ChatMode) => void;
  setStatus: (s: ChatStatus) => void;
  setError: (msg: string | null) => void;
  setSessions: (sessions: Session[]) => void;
  loadSessions: () => Promise<void>;
  setActiveSessionId: (id: string | null) => void;
  // Sprint 57.126: fetch a clicked session's persisted transcript + replay it
  // (conversation-only reset → mergeEvent each event → render historical turns).
  loadSessionHistory: (sessionId: string) => Promise<void>;
  pivotSession: (newSessionId: string, banner: HandoffBanner) => void;
  dismissHandoffBanner: () => void;
  pushUserMessage: (content: string) => void;
  // Sprint 57.126: param widened to include the persist-only UserMessageEvent so
  // loadSessionHistory can replay user prompts through the SAME reducer (live
  // callers pass LoopEvent — assignable to the wider input by contravariance).
  mergeEvent: (ev: LoopEvent | UserMessageEvent) => void;
  appendVerification: (event: VerificationEvent) => void;
  clearVerifications: () => void;
  clearSubagents: () => void;
  reset: () => void;
};

const _initial = (): Pick<
  ChatStoreState,
  | "sessionId"
  | "status"
  | "totalTurns"
  | "stopReason"
  | "errorMessage"
  | "currentModel"
  | "handoffBanner"
  | "turns"
  | "sessions"
  | "activeSessionId"
  | "rawEvents"
  | "approvals"
  | "verifications"
  | "subagents"
  | "spans"
  | "memoryOps"
  | "todos"
> => ({
  sessionId: null,
  status: "idle",
  totalTurns: 0,
  stopReason: null,
  errorMessage: null,
  currentModel: null,
  handoffBanner: null,
  turns: [],
  sessions: [],
  activeSessionId: null,
  rawEvents: [],
  approvals: {},
  verifications: [],
  subagents: [],
  spans: [],
  memoryOps: [],
  todos: [],
});

let _turnCounter = 0;
const nextTurnId = (): string => `t_${++_turnCounter}`;

const nowIso = (): string => new Date().toISOString();

// Sprint 57.140: narrow a wire `todos_updated` item's generic status to TodoItem's
// union (unknown / malformed → "pending"), mirroring the backend serde tolerance.
const narrowTodoStatus = (raw: unknown): TodoItem["status"] => {
  const text = String(raw ?? "");
  return text === "in_progress" || text === "completed" ? text : "pending";
};

/**
 * Sprint 57.107 B3: map the backend session status (active | handed_off |
 * completed) to the SessionStatusUI token. Unknown values default to "done"
 * (a terminal-looking state is the safe fallback for the sidebar indicator).
 */
const mapSessionStatus = (status: string): SessionStatusUI => {
  switch (status) {
    case "active":
      return "running";
    case "handed_off":
      return "handed_off";
    case "completed":
      return "done";
    default:
      return "done";
  }
};

/**
 * Sprint 57.107 B3: format a backend `started_at_ms` epoch into a short display
 * string. No relative-time helper exists in the codebase, so use the locale
 * date/time string (honest absolute stamp — not a fabricated "5m ago").
 */
const formatStartedAt = (ms: number): string => new Date(ms).toLocaleString();

/** Sprint 57.107 B3: map one snake_case API item to the camelCase Session UI shape. */
const sessionFromApi = (item: SessionListApiItem): Session => ({
  id: item.id,
  title: item.title,
  agent: item.agent_role,
  turns: item.total_turns,
  status: mapSessionStatus(item.status),
  time: formatStartedAt(item.started_at_ms),
  handoffParentId: item.handoff_parent_id,
  agentRole: item.agent_role,
});

/**
 * Map backend risk_level string (e.g. "HIGH" / "high" / "Critical") to the
 * frontend RiskSeverity token. Defensive default = "risk-medium".
 */
const mapRiskLevel = (s: string): RiskSeverity => {
  const k = s.toLowerCase();
  if (k.includes("critical")) return "risk-critical";
  if (k.includes("low")) return "risk-low";
  if (k.includes("high")) return "risk-high";
  return "risk-medium";
};

/**
 * Replace the last AgentTurn in `turns` via a pure updater. Returns the same
 * array reference if no agent turn exists yet (defensive: caller may receive
 * SSE events before turn_start has fired).
 */
const updateLastAgentTurn = (
  turns: Turn[],
  updater: (t: AgentTurn) => AgentTurn,
): Turn[] => {
  for (let i = turns.length - 1; i >= 0; i--) {
    if (turns[i].role === "agent") {
      const next = turns.slice();
      next[i] = updater(turns[i] as AgentTurn);
      return next;
    }
  }
  return turns;
};

/**
 * Sprint 57.69 A-3b slice 2: pure HANDOFF session-pivot transform. Shared by
 * BOTH the `agent_handoff` mergeEvent case and the `pivotSession` action — it
 * stays a pure (s) => state helper because the `agent_handoff` case only has the
 * `s` draft (Sprint 57.126 added `get` to the factory for the async
 * loadSessionHistory action, but this helper keeps no get-dependency).
 *
 * Preserves the sidebar `sessions` list + `mode`; keeps the accumulated
 * `rawEvents` audit log (caller passes the already-appended array); resets the
 * conversation slices (turns / status / counters / approvals / verifications /
 * subagents) for the fresh child session; points BOTH `sessionId` and
 * `activeSessionId` at the child (they were unlinked — `sessionId` is set only
 * by `loop_start`, `activeSessionId` by the sidebar) so the next message routes
 * to the child; and raises the transition banner.
 */
const applyPivot = (
  s: ChatStoreState,
  newSessionId: string,
  banner: HandoffBanner,
  rawEvents: LoopEvent[],
): ChatStoreState => ({
  ...s,
  rawEvents,
  sessionId: newSessionId,
  activeSessionId: newSessionId,
  handoffBanner: banner,
  turns: [],
  status: "idle",
  totalTurns: 0,
  stopReason: null,
  errorMessage: null,
  approvals: {},
  verifications: [],
  subagents: [],
  spans: [],
  memoryOps: [],
  todos: [],
});

export const useChatStore = create<ChatStoreState>((set, get) => ({
  ..._initial(),
  // Honest default: real_llm so a user who just opens the page and sends a
  // message gets the LIVE agent, not the offline echo mock. echo_demo stays
  // available via the InputBar toggle for deterministic / offline use.
  mode: "real_llm",

  setMode: (m) => set({ mode: m }),
  setStatus: (s) => set({ status: s }),
  setError: (msg) => set({ errorMessage: msg }),
  setSessions: (sessions) => set({ sessions }),

  // Sprint 57.107 B3: fetch the caller's real sessions from GET /sessions and
  // map them into the camelCase Session[] shape. On error, leave the existing
  // list untouched (the SessionList renders an empty state when none loaded) —
  // a transient fetch failure should not blank an already-populated sidebar.
  loadSessions: async () => {
    try {
      const items = await listSessions();
      set({ sessions: items.map(sessionFromApi) });
    } catch {
      // Swallow — keep whatever is already in `sessions`. The empty-state line
      // covers the never-loaded case; this avoids flicker on a transient 5xx.
    }
  },

  setActiveSessionId: (id) => set({ activeSessionId: id }),

  // Sprint 57.126: replay a historical session's conversation. Fetches the
  // persisted transcript (GET /events — agent-side events + the 57.126 user_message
  // rows), resets ONLY the conversation slices (preserve `sessions` + `mode` — model
  // on applyPivot, NOT reset() which nukes the sidebar list), then replays each
  // {type, data} through mergeEvent in sequence_num order → pixel-identical
  // historical turns. Setting `sessionId` makes the loaded session active so a
  // follow-up continues it (send() keys off the store sessionId). Guards: skip the
  // live running session (don't interrupt a stream); latest-clicked-wins.
  loadSessionHistory: async (sessionId) => {
    if (get().sessionId === sessionId && get().status === "running") return;
    // Conversation-only reset (preserve sessions + mode); point both ids at the
    // clicked session; zero the turn-id counter so replayed turn ids are fresh.
    _turnCounter = 0;
    set((s) => ({
      ...s,
      sessionId,
      activeSessionId: sessionId,
      turns: [],
      status: "idle",
      totalTurns: 0,
      stopReason: null,
      errorMessage: null,
      currentModel: null,
      handoffBanner: null,
      rawEvents: [],
      approvals: {},
      verifications: [],
      subagents: [],
      spans: [],
      memoryOps: [],
      todos: [],
    }));
    let events;
    try {
      events = await fetchSessionEvents(sessionId);
    } catch (err) {
      set({ errorMessage: (err as Error).message });
      return;
    }
    // Race guard: a newer click already re-pointed activeSessionId → drop this
    // stale result rather than replay it onto the newer session.
    if (get().activeSessionId !== sessionId) return;
    // Defensive sort (the backend already orders by sequence_num) → faithful order.
    const ordered = [...events].sort((a, b) => a.sequence_num - b.sequence_num);
    const merge = get().mergeEvent;
    for (const ev of ordered) {
      merge({ type: ev.type, data: ev.data } as unknown as LoopEvent | UserMessageEvent);
    }
  },

  // Sprint 57.69: HANDOFF pivot — reset the conversation onto the child session.
  pivotSession: (newSessionId, banner) =>
    set((s) => applyPivot(s, newSessionId, banner, [...s.rawEvents])),

  dismissHandoffBanner: () => set({ handoffBanner: null }),

  pushUserMessage: (content) =>
    set((s) => ({
      turns: [
        ...s.turns,
        { role: "user", id: nextTurnId(), at: nowIso(), text: content },
      ],
    })),

  mergeEvent: (ev) =>
    set((s) => {
      // Sprint 57.126: ev may be the persist-only UserMessageEvent (replay) — it
      // shares the {type, data} shape, so it is recorded in the LoopEvent[] audit
      // log via a narrowing cast (rawEvents stays LoopEvent[] — no consumer ripple).
      const rawEvents: LoopEvent[] = [...s.rawEvents, ev as LoopEvent];

      switch (ev.type) {
        case "user_message": {
          // Sprint 57.126: replay-only. The 57.126 backend persists the user's
          // prompt as a user_message row per send (NEVER streamed live — the live UI
          // uses pushUserMessage). Push a UserTurn so a replayed historical session
          // shows the user's questions. It precedes loop_start in the stream → the
          // loop_start active_skill stamping finds it (the chip reconstructs too).
          return {
            ...s,
            rawEvents,
            turns: [
              ...s.turns,
              { role: "user", id: nextTurnId(), at: nowIso(), text: ev.data.text },
            ],
          };
        }

        case "loop_start": {
          // Sprint 57.69: a new turn cycle in the (possibly child) session
          // dismisses any handoff transition notice.
          // Sprint 57.116: the server-confirmed force-load skill (or null). When
          // present, stamp it onto the LAST user turn (the one that triggered this
          // run, pushed by pushUserMessage just before send) so the timeline can
          // chip it. Truthy guard → a null (resume mirror / no force-load) never
          // overwrites an existing chip. Server-confirmed → an invalid name the FE
          // sent was dropped by the router → null → no chip (no AP-4 mislabel).
          const activeSkill = ev.data.active_skill;
          const lastUserIdx = activeSkill
            ? s.turns.reduce((acc, t, i) => (t.role === "user" ? i : acc), -1)
            : -1;
          return {
            ...s,
            rawEvents,
            sessionId: ev.data.session_id ?? null,
            status: "running",
            errorMessage: null,
            handoffBanner: null,
            // Sprint 57.88 (US-5): a new loop cycle — including a resume after a
            // deferred HITL approval — clears the stale "awaiting approval"
            // indicator from the turn that paused earlier. Once the loop is
            // running again, no prior agent turn is still awaiting. No-op on a
            // normal first send (no prior waiting turn).
            turns: s.turns.map((t, i) => {
              if (i === lastUserIdx && t.role === "user") {
                return { ...t, activeSkill: activeSkill ?? undefined };
              }
              if (t.role === "agent" && t.waiting) {
                return { ...t, waiting: false };
              }
              return t;
            }),
          };
        }

        case "turn_start": {
          // Sprint 57.108: trace_id rides EVERY frame (sse.py wrapper injects it).
          // The turn's TURN span opened just BEFORE TurnStarted (loop.py emission
          // order: SpanStarted(TURN) → TurnStarted), so the newest running TURN
          // span in the spans slice IS this turn's span — linking here, not in
          // span_started, avoids attaching to the previous turn.
          const turnSpan = [...s.spans]
            .reverse()
            .find((sp) => sp.spanType === "TURN" && sp.status === "running");
          // Sprint 57.120: carry the loop's force-loaded skill onto the AgentTurn so
          // the Inspector Turn tab can show an active_skill row (alongside trace_id).
          // loop_start stamped it onto the trigger user turn just before this; the
          // MOST-RECENT NON-INJECTED user turn IS that trigger — a 57.101 injected
          // mid-run turn carries no skill and is skipped (so an injection doesn't
          // clear the loop's skill), and a new no-skill loop's trigger has activeSkill
          // undefined → no stale leak from a prior skilled loop.
          const triggerSkill = [...s.turns]
            .reverse()
            .find((t): t is UserTurn => t.role === "user" && !t.injected)?.activeSkill;
          const newAgentTurn: AgentTurn = {
            role: "agent",
            id: nextTurnId(),
            at: nowIso(),
            stopReason: null,
            durationMs: null,
            blocks: [],
            tokensIn: null,
            tokensOut: null,
            tokensThinking: null,
            costUsd: null,
            // Sprint 57.133: null until this turn's first llm_response carries actual
            // cache-hit tokens (turn_start fires before any llm_response).
            cachedInputTokens: null,
            // Sprint 57.131: null until this turn's first llm_request stamps the model
            // (turn_start fires BEFORE llm_request, so the model isn't known yet).
            model: null,
            traceId: ev.data.trace_id ?? null,
            spanId: turnSpan?.spanId ?? null,
            activeSkill: triggerSkill,
          };
          return { ...s, rawEvents, turns: [...s.turns, newAgentTurn] };
        }

        case "message_injected": {
          // Sprint 57.101 B1: a mid-run injected instruction was DRAINED into the
          // loop at a turn boundary (the event fires on drain — proof it landed,
          // not on the inject POST). Render it as a user turn tagged `injected` so
          // the timeline shows it between the agent's turns.
          return {
            ...s,
            rawEvents,
            turns: [
              ...s.turns,
              {
                role: "user",
                id: nextTurnId(),
                at: nowIso(),
                text: ev.data.text,
                injected: true,
              },
            ],
          };
        }

        case "todos_updated": {
          // Sprint 57.140 (research #1 task primitive): the agent updated its
          // structured plan via write_todos. The wire carries the WHOLE list
          // (replace-whole-list); narrow each generic object to TodoItem (the wire
          // avoids a 2nd named codegen element). Feeds the Inspector Todos tab.
          const todos: TodoItem[] = ev.data.todos.map((t) => ({
            id: String(t.id ?? ""),
            title: String(t.title ?? ""),
            status: narrowTodoStatus(t.status),
            // Sprint 57.156 DAG: narrow the generic prerequisite-id list.
            depends_on: Array.isArray(t.depends_on)
              ? (t.depends_on as unknown[]).map((d) => String(d)).filter((d) => d !== "")
              : [],
          }));
          return { ...s, rawEvents, todos };
        }

        case "llm_request": {
          return {
            ...s,
            rawEvents,
            currentModel: ev.data.model,
            // Sprint 57.131: stamp the per-turn model alongside tokensIn (same
            // llm_request frame) so the Inspector Turn tab shows which model ran this
            // turn; a multi-call turn keeps the latest (overwrite, like tokensIn).
            turns: updateLastAgentTurn(s.turns, (t) => ({
              ...t,
              tokensIn: ev.data.tokens_in,
              model: ev.data.model,
            })),
          };
        }

        case "llm_response": {
          // Append ThinkingBlock (if thinking) + AnswerBlock (if final content)
          // + ToolBlock per tool_call. Visual order: thinking → answer → tools.
          return {
            ...s,
            rawEvents,
            turns: updateLastAgentTurn(s.turns, (t) => {
              const newBlocks: Block[] = [...t.blocks];
              if (ev.data.thinking) {
                newBlocks.push({ type: "thinking", text: ev.data.thinking });
              }
              // Honest-surface (CHANGE-054): render the agent's final text answer.
              // Only when non-empty — a tool-calling turn carries content="" until
              // the model produces its final reply, so this skips intermediate turns.
              if (ev.data.content) {
                newBlocks.push({ type: "answer", text: ev.data.content });
              }
              for (const tc of ev.data.tool_calls) {
                newBlocks.push({
                  type: "tool",
                  toolCallId: tc.id,
                  name: tc.name,
                  status: "pending",
                  input: JSON.stringify(tc.arguments, null, 2),
                  output: null,
                  durationMs: null,
                  isError: false,
                });
              }
              // Sprint 57.108: per-call token actuals (overwrite the llm_request
              // estimate; keep prior value for 0/absent — old frames lack the
              // fields and an unmeasured 0 must not masquerade as a real count).
              return {
                ...t,
                blocks: newBlocks,
                tokensIn: ev.data.input_tokens > 0 ? ev.data.input_tokens : t.tokensIn,
                tokensOut: ev.data.output_tokens > 0 ? ev.data.output_tokens : t.tokensOut,
                // Sprint 57.133: per-turn prompt-cache-hit tokens (same 0-guard — an
                // old frame / unmeasured 0 must not clobber a real prior count).
                cachedInputTokens:
                  ev.data.cached_input_tokens > 0
                    ? ev.data.cached_input_tokens
                    : t.cachedInputTokens,
              };
            }),
          };
        }

        case "tool_call_request": {
          // Defensive: if active agent turn lacks ToolBlock for this id, append.
          return {
            ...s,
            rawEvents,
            turns: updateLastAgentTurn(s.turns, (t) => {
              const exists = t.blocks.some(
                (b) => b.type === "tool" && b.toolCallId === ev.data.tool_call_id,
              );
              if (exists) return t;
              return {
                ...t,
                blocks: [
                  ...t.blocks,
                  {
                    type: "tool",
                    toolCallId: ev.data.tool_call_id,
                    name: ev.data.tool_name,
                    status: "pending",
                    input: JSON.stringify(ev.data.args, null, 2),
                    output: null,
                    durationMs: null,
                    isError: false,
                  },
                ],
              };
            }),
          };
        }

        case "tool_call_result": {
          return {
            ...s,
            rawEvents,
            turns: updateLastAgentTurn(s.turns, (t) => ({
              ...t,
              blocks: t.blocks.map((b) =>
                b.type === "tool" && b.toolCallId === ev.data.tool_call_id
                  ? {
                      ...b,
                      status: ev.data.is_error ? "error" : "ok",
                      output: ev.data.result,
                      durationMs: ev.data.duration_ms,
                      isError: ev.data.is_error,
                    }
                  : b,
              ),
            })),
          };
        }

        case "loop_end": {
          return {
            ...s,
            rawEvents,
            status: "completed",
            totalTurns: ev.data.total_turns,
            stopReason: ev.data.stop_reason,
            turns: updateLastAgentTurn(s.turns, (t) => ({
              ...t,
              stopReason: ev.data.stop_reason,
              waiting: ev.data.stop_reason !== "end_turn",
            })),
          };
        }

        case "loop_terminated": {
          // Sprint 57.130: a Cat-8 fatal terminate (ErrorTerminator) — the loop
          // yields this then returns with NO loop_end. Surface it so the run stops
          // hanging: (1) flip any dangling pending ToolBlock → error (the stuck-chip
          // fix — a tool was mid-flight when the loop died, so its tool_call_result
          // never arrived); (2) record turn.terminated (AgentTurn head shows a danger
          // badge with the reason); (3) set the chat status terminal ("completed" —
          // the proven loop_end unfreeze path, no new status enum) so the composer
          // re-enables. Closes AD-LoopTerminated-Wire-Surface.
          const termReason = ev.data.reason;
          const termDetail = ev.data.detail;
          return {
            ...s,
            rawEvents,
            status: "completed",
            turns: updateLastAgentTurn(s.turns, (t) => ({
              ...t,
              blocks: t.blocks.map((b) =>
                b.type === "tool" && b.status === "pending"
                  ? {
                      ...b,
                      status: "error",
                      output: `terminated: ${termReason}`,
                      isError: true,
                    }
                  : b,
              ),
              waiting: false,
              terminated: { reason: termReason, detail: termDetail },
            })),
          };
        }

        case "approval_requested": {
          // Dual-emit: (1) populate approvals dict (preserve existing
          // ApprovalCard workflow); (2) push HITLTurn into turns (new mockup
          // inline render). Dedup by request_id on both paths.
          const id = ev.data.approval_request_id;
          if (!id) return { ...s, rawEvents };
          if (s.approvals[id]) return { ...s, rawEvents };
          const hitlTurn: HITLTurn = {
            role: "hitl",
            id: nextTurnId(),
            at: nowIso(),
            title: `Approval required: ${ev.data.risk_level}`,
            severity: mapRiskLevel(ev.data.risk_level),
            // Sprint 57.108: real approval context from the wire — tool_name is
            // set only for kind="tool"; reason at all 5 escalate sites. "—" stays
            // the honest fallback for old frames / absent values.
            tool: ev.data.tool_name ?? "—",
            // Sprint 57.100: carry the pause kind so HITLTurn can branch REJECT
            // (verification → coach one turn; others → terminate). "" for an
            // older replayed event with no kind on the wire.
            kind: ev.data.kind ?? "",
            payload: "—",
            rationale: ev.data.reason || "—",
            approvalRequestId: id,
            decision: null,
            countdownSec: null,
          };
          return {
            ...s,
            rawEvents,
            approvals: {
              ...s.approvals,
              [id]: {
                approvalRequestId: id,
                riskLevel: ev.data.risk_level,
                decision: null,
                receivedAt: Date.now(),
              },
            },
            turns: [...s.turns, hitlTurn],
          };
        }

        case "approval_received": {
          // Dual-emit: update approvals dict + matching HITLTurn decision.
          const id = ev.data.approval_request_id;
          if (!id) return { ...s, rawEvents };
          const existing = s.approvals[id];
          const updatedApprovals = existing
            ? {
                ...s.approvals,
                [id]: { ...existing, decision: ev.data.decision },
              }
            : {
                ...s.approvals,
                [id]: {
                  approvalRequestId: id,
                  riskLevel: "UNKNOWN",
                  decision: ev.data.decision,
                  receivedAt: Date.now(),
                },
              };
          const updatedTurns = s.turns.map((t) =>
            t.role === "hitl" && t.approvalRequestId === id
              ? { ...t, decision: ev.data.decision }
              : t,
          );
          return {
            ...s,
            rawEvents,
            approvals: updatedApprovals,
            turns: updatedTurns,
          };
        }

        case "guardrail_triggered": {
          // Sprint 53.6 D2: rawEvents only — Phase-2+ may render warning banner.
          return { ...s, rawEvents };
        }

        case "context_compacted": {
          // Sprint 57.159 (Cat 4 L2→L3): surface the compaction as a persistent
          // timeline marker (was rawEvents-only — the 57.66 A-5c deferral left the
          // token reduction rendering nowhere). Push a compaction marker turn
          // (mirrors message_injected). Compaction fires BEFORE turn_started, so
          // the marker naturally precedes the turn it enabled. rawEvents retained.
          return {
            ...s,
            rawEvents,
            turns: [
              ...s.turns,
              {
                role: "compaction",
                id: nextTurnId(),
                at: nowIso(),
                tokensBefore: ev.data.tokens_before,
                tokensAfter: ev.data.tokens_after,
                strategy: ev.data.compaction_strategy,
                messagesCompacted: ev.data.messages_compacted,
              },
            ],
          };
        }

        case "prompt_built":
        case "state_checkpointed":
        case "tripwire_triggered": {
          // Sprint 57.66: recognized + typed + audit-trail only (rawEvents).
          // Rich Inspector render DEFERRED to A-5c (mirror guardrail_triggered).
          return { ...s, rawEvents };
        }

        case "agent_handoff": {
          // Sprint 57.69 A-3b slice 2 (Cat 11 HANDOFF): record the rawEvent, then
          // PIVOT the active session to the booted child (new_session_id) — reset
          // the conversation, point sessionId + activeSessionId at the child, and
          // raise the transition banner. Arrives post-stream (after loop_end per
          // the 57.68 router post-loop hook), so there is no mid-stream race.
          return applyPivot(
            s,
            ev.data.new_session_id,
            { targetAgent: ev.data.target_agent, reason: ev.data.reason },
            rawEvents,
          );
        }

        case "span_started": {
          // Sprint 57.75 A-5 Trace: open a SpanNode (duration null until ended).
          // Dedup by span_id (a re-emit keeps the first open record).
          const sid = ev.data.span_id;
          if (!sid || s.spans.some((sp) => sp.spanId === sid)) {
            return { ...s, rawEvents };
          }
          const span: SpanNode = {
            spanId: sid,
            parentSpanId: ev.data.parent_span_id,
            spanType: ev.data.span_type,
            spanName: ev.data.span_name,
            durationMs: null,
            status: "running",
          };
          return { ...s, rawEvents, spans: [...s.spans, span] };
        }

        case "span_ended": {
          // Sprint 57.75 A-5 Trace: close the matching open span (set duration +
          // status=done). If SpanStarted was missed, defensively create a closed
          // span so the waterfall still shows it (no parent linkage available).
          const sid = ev.data.span_id;
          if (!sid) return { ...s, rawEvents };
          // Sprint 57.108: a closing TURN span carries the turn's wall-clock —
          // fill the matching AgentTurn.durationMs (there is no turn_end event;
          // spanId-keyed so emission order doesn't matter).
          const nextTurns =
            ev.data.span_type === "TURN"
              ? s.turns.map((t) =>
                  t.role === "agent" && t.spanId === sid
                    ? { ...t, durationMs: ev.data.duration_ms }
                    : t,
                )
              : s.turns;
          const idx = s.spans.findIndex((sp) => sp.spanId === sid);
          if (idx === -1) {
            const span: SpanNode = {
              spanId: sid,
              parentSpanId: "",
              spanType: ev.data.span_type,
              spanName: ev.data.span_name,
              durationMs: ev.data.duration_ms,
              status: "done",
            };
            return { ...s, rawEvents, turns: nextTurns, spans: [...s.spans, span] };
          }
          const nextSpans = s.spans.slice();
          nextSpans[idx] = {
            ...nextSpans[idx],
            durationMs: ev.data.duration_ms,
            status: "done",
          };
          return { ...s, rawEvents, turns: nextTurns, spans: nextSpans };
        }

        case "memory_accessed": {
          // Sprint 57.75 A-5 Memory: append a MemoryOp (client receive time as
          // `at` — the backend event carries no timestamp; honest client stamp).
          const op: MemoryOp = {
            op: ev.data.operation,
            scope: ev.data.layer,
            timeScale: ev.data.time_scale,
            key: ev.data.key,
            summary: ev.data.summary,
            at: Date.now(),
          };
          return { ...s, rawEvents, memoryOps: [...s.memoryOps, op] };
        }

        case "verification_passed":
        case "verification_failed": {
          // Dual-emit: verifications slice (Sprint 57.11 VerificationPanel) +
          // VerificationBlock into active agent turn (Sprint 57.21 inline).
          const claim =
            ev.type === "verification_passed"
              ? "Verification passed"
              : ev.data.reason ?? "Verification failed";
          const evidence =
            ev.type === "verification_passed"
              ? `score: ${ev.data.score ?? "—"}`
              : ev.data.suggested_correction ?? "";
          return {
            ...s,
            rawEvents,
            verifications: [...s.verifications, ev as VerificationEvent],
            turns: updateLastAgentTurn(s.turns, (t) => ({
              ...t,
              blocks: [
                ...t.blocks,
                {
                  type: "verification",
                  verifier: ev.data.verifier,
                  ok: ev.type === "verification_passed",
                  claim,
                  evidence,
                },
              ],
            })),
          };
        }

        case "subagent_spawned": {
          // Dual-emit: subagents slice (Sprint 57.12 SubagentTree) + extend
          // SubagentForkBlock in active agent turn (Sprint 57.21 inline).
          const sid = ev.data.subagent_id;
          if (!sid) return { ...s, rawEvents };
          // (a) subagents slice — preserve Sprint 57.12 behavior
          const sliceHas = s.subagents.some((n) => n.subagentId === sid);
          const newSubagents = sliceHas
            ? s.subagents
            : [
                ...s.subagents,
                {
                  subagentId: sid,
                  parentId: ev.data.parent_session_id,
                  mode: ev.data.mode,
                  status: "running" as const,
                  summary: null,
                  tokensUsed: null,
                  spawnedAt: Date.now(),
                  childEvents: [],
                },
              ];
          // (b) SubagentForkBlock in active turn — find-or-create then append agent
          const newEntry: SubagentEntry = {
            id: sid,
            name: sid,
            task: ev.data.mode,
            status: "running",
            mode: ev.data.mode,
            tokensUsed: null,
          };
          const newTurns = updateLastAgentTurn(s.turns, (t) => {
            const forkIdx = t.blocks.findIndex((b) => b.type === "subagent_fork");
            if (forkIdx === -1) {
              return {
                ...t,
                blocks: [
                  ...t.blocks,
                  { type: "subagent_fork", agents: [newEntry] },
                ],
              };
            }
            const fork = t.blocks[forkIdx] as SubagentForkBlock;
            if (fork.agents.some((a) => a.id === sid)) return t;
            const newBlocks = t.blocks.slice();
            newBlocks[forkIdx] = {
              ...fork,
              agents: [...fork.agents, newEntry],
            };
            return { ...t, blocks: newBlocks };
          });
          return {
            ...s,
            rawEvents,
            subagents: newSubagents,
            turns: newTurns,
          };
        }

        case "subagent_completed": {
          // Dual-emit: subagents slice update + active turn's fork block entry.
          const sid = ev.data.subagent_id;
          if (!sid) return { ...s, rawEvents };
          // (a) subagents slice — preserve defensive-create
          const idx = s.subagents.findIndex((n) => n.subagentId === sid);
          let newSubagents: SubagentNode[];
          if (idx === -1) {
            newSubagents = [
              ...s.subagents,
              {
                subagentId: sid,
                parentId: null,
                mode: "unknown",
                status: "completed",
                summary: ev.data.summary,
                tokensUsed: ev.data.tokens_used,
                spawnedAt: Date.now(),
                childEvents: [],
              },
            ];
          } else {
            newSubagents = s.subagents.slice();
            newSubagents[idx] = {
              ...newSubagents[idx],
              status: "completed",
              summary: ev.data.summary,
              tokensUsed: ev.data.tokens_used,
            };
          }
          // (b) update agent entry in active turn's fork block
          const newTurns = updateLastAgentTurn(s.turns, (t) => {
            const forkIdx = t.blocks.findIndex((b) => b.type === "subagent_fork");
            if (forkIdx === -1) return t;
            const fork = t.blocks[forkIdx] as SubagentForkBlock;
            const newBlocks = t.blocks.slice();
            newBlocks[forkIdx] = {
              ...fork,
              agents: fork.agents.map((a) =>
                a.id === sid
                  ? { ...a, status: "done", tokensUsed: ev.data.tokens_used }
                  : a,
              ),
            };
            return { ...t, blocks: newBlocks };
          });
          return {
            ...s,
            rawEvents,
            subagents: newSubagents,
            turns: newTurns,
          };
        }

        case "subagent_child": {
          // Sprint 57.96 (Cat 11 Scope B): route a child loop's per-turn TAO event
          // to its subagent node (by subagent_id) so the Inspector Tree node EXPANDS
          // to show the child's loop. `inner` is an opaque Record on the wire; project
          // it to a ChildTurnEvent per inner_type with type guards (no casts).
          const sid = ev.data.subagent_id;
          if (!sid) return { ...s, rawEvents };
          const inner = ev.data.inner;
          const entry: ChildTurnEvent = {
            kind: ev.data.inner_type,
            turn: typeof inner.turn_num === "number" ? inner.turn_num : undefined,
            text:
              typeof inner.content === "string"
                ? inner.content
                : typeof inner.result === "string"
                  ? inner.result
                  : typeof inner.text === "string"
                    ? inner.text
                    : typeof inner.reason === "string"
                      ? inner.reason // guardrail_triggered (Sprint 57.110 B4)
                      : undefined,
            toolName: typeof inner.tool_name === "string" ? inner.tool_name : undefined,
            toolCallId: typeof inner.tool_call_id === "string" ? inner.tool_call_id : undefined,
            action: typeof inner.action === "string" ? inner.action : undefined,
          };
          const idx = s.subagents.findIndex((n) => n.subagentId === sid);
          let newSubagents: SubagentNode[];
          if (idx === -1) {
            // Defensive-create (child event before spawn — unlikely; spawn emits first).
            newSubagents = [
              ...s.subagents,
              {
                subagentId: sid,
                parentId: null,
                mode: "unknown",
                status: "running",
                summary: null,
                tokensUsed: null,
                spawnedAt: Date.now(),
                childEvents: [entry],
              },
            ];
          } else {
            newSubagents = s.subagents.slice();
            newSubagents[idx] = {
              ...newSubagents[idx],
              childEvents: [...newSubagents[idx].childEvents, entry],
            };
          }
          return { ...s, rawEvents, subagents: newSubagents };
        }

        default: {
          // Exhaustive switch — parser filters unknown upstream.
          const _exhaustive: never = ev;
          return { ...s, rawEvents: [...s.rawEvents, _exhaustive] };
        }
      }
    }),

  appendVerification: (event) =>
    set((s) => ({ verifications: [...s.verifications, event] })),

  clearVerifications: () => set({ verifications: [] }),

  clearSubagents: () => set({ subagents: [] }),

  reset: () => {
    // Zero the module-global turn counter so a fresh session's turns restart at
    // t_1 (otherwise "New session" inherits the prior session's climbing ids).
    _turnCounter = 0;
    set({ ..._initial() });
  },
}));
