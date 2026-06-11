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
 *     - llm_request        → update active AgentTurn.tokensIn
 *     - llm_response       → append ThinkingBlock (if thinking) + ToolBlock per tool_call
 *     - tool_call_request  → defensive append ToolBlock if missing (rare path)
 *     - tool_call_result   → update matching ToolBlock status/output/durationMs
 *     - loop_end           → set status=completed + active turn stopReason
 *     - approval_requested → push HITLTurn + update approvals dict (dual-emit)
 *     - approval_received  → update HITLTurn decision + approvals dict (dual-emit)
 *     - guardrail_triggered → rawEvents only (Phase-2+ may render warning)
 *     - prompt_built / context_compacted / state_checkpointed / tripwire_triggered
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
 * Last Modified: 2026-06-10
 *
 * Modification History:
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
  SubagentEntry,
  SubagentForkBlock,
  Turn,
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

  // Actions
  setMode: (m: ChatMode) => void;
  setStatus: (s: ChatStatus) => void;
  setError: (msg: string | null) => void;
  setSessions: (sessions: Session[]) => void;
  setActiveSessionId: (id: string | null) => void;
  pivotSession: (newSessionId: string, banner: HandoffBanner) => void;
  dismissHandoffBanner: () => void;
  pushUserMessage: (content: string) => void;
  mergeEvent: (ev: LoopEvent) => void;
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
});

let _turnCounter = 0;
const nextTurnId = (): string => `t_${++_turnCounter}`;

const nowIso = (): string => new Date().toISOString();

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
 * BOTH the `agent_handoff` mergeEvent case and the `pivotSession` action (the
 * store factory exposes only `set`, no `get`, so the pivot logic must live in
 * a pure helper to avoid duplication).
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
});

export const useChatStore = create<ChatStoreState>((set) => ({
  ..._initial(),
  // Honest default: real_llm so a user who just opens the page and sends a
  // message gets the LIVE agent, not the offline echo mock. echo_demo stays
  // available via the InputBar toggle for deterministic / offline use.
  mode: "real_llm",

  setMode: (m) => set({ mode: m }),
  setStatus: (s) => set({ status: s }),
  setError: (msg) => set({ errorMessage: msg }),
  setSessions: (sessions) => set({ sessions }),
  setActiveSessionId: (id) => set({ activeSessionId: id }),

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
      const rawEvents = [...s.rawEvents, ev];

      switch (ev.type) {
        case "loop_start": {
          // Sprint 57.69: a new turn cycle in the (possibly child) session
          // dismisses any handoff transition notice.
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
            turns: s.turns.map((t) =>
              t.role === "agent" && t.waiting ? { ...t, waiting: false } : t,
            ),
          };
        }

        case "turn_start": {
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
            traceId: null,
            spanId: null,
          };
          return { ...s, rawEvents, turns: [...s.turns, newAgentTurn] };
        }

        case "llm_request": {
          return {
            ...s,
            rawEvents,
            currentModel: ev.data.model,
            turns: updateLastAgentTurn(s.turns, (t) => ({
              ...t,
              tokensIn: ev.data.tokens_in,
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
              return { ...t, blocks: newBlocks };
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
            tool: "—",
            // Sprint 57.100: carry the pause kind so HITLTurn can branch REJECT
            // (verification → coach one turn; others → terminate). "" for an
            // older replayed event with no kind on the wire.
            kind: ev.data.kind ?? "",
            payload: "—",
            rationale: "—",
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

        case "prompt_built":
        case "context_compacted":
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
            return { ...s, rawEvents, spans: [...s.spans, span] };
          }
          const nextSpans = s.spans.slice();
          nextSpans[idx] = {
            ...nextSpans[idx],
            durationMs: ev.data.duration_ms,
            status: "done",
          };
          return { ...s, rawEvents, spans: nextSpans };
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
            turns: 0,
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
                a.id === sid ? { ...a, status: "done" } : a,
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
                  : undefined,
            toolName: typeof inner.tool_name === "string" ? inner.tool_name : undefined,
            toolCallId: typeof inner.tool_call_id === "string" ? inner.tool_call_id : undefined,
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
