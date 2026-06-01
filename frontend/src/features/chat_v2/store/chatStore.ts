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
 *
 *   Dual-emit pattern preserves Sprint 57.11 inline VerificationPanel + Sprint 57.12
 *   SubagentTree behavior (they consume verifications + subagents slices) while
 *   ALSO feeding the new Turn block render path for /chat-v2 mockup-fidelity.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.3)
 * Last Modified: 2026-06-02
 *
 * Modification History:
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

import type { SubagentNode } from "../../subagent/types";
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

type ChatStoreState = {
  // Session metadata (preserved)
  sessionId: string | null;
  status: ChatStatus;
  totalTurns: number;
  stopReason: string | null;
  errorMessage: string | null;
  mode: ChatMode;

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

  // Actions
  setMode: (m: ChatMode) => void;
  setStatus: (s: ChatStatus) => void;
  setError: (msg: string | null) => void;
  setSessions: (sessions: Session[]) => void;
  setActiveSessionId: (id: string | null) => void;
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
  | "turns"
  | "sessions"
  | "activeSessionId"
  | "rawEvents"
  | "approvals"
  | "verifications"
  | "subagents"
> => ({
  sessionId: null,
  status: "idle",
  totalTurns: 0,
  stopReason: null,
  errorMessage: null,
  turns: [],
  sessions: [],
  activeSessionId: null,
  rawEvents: [],
  approvals: {},
  verifications: [],
  subagents: [],
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

export const useChatStore = create<ChatStoreState>((set) => ({
  ..._initial(),
  mode: "echo_demo",

  setMode: (m) => set({ mode: m }),
  setStatus: (s) => set({ status: s }),
  setError: (msg) => set({ errorMessage: msg }),
  setSessions: (sessions) => set({ sessions }),
  setActiveSessionId: (id) => set({ activeSessionId: id }),

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
          return {
            ...s,
            rawEvents,
            sessionId: ev.data.session_id ?? null,
            status: "running",
            errorMessage: null,
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
            turns: updateLastAgentTurn(s.turns, (t) => ({
              ...t,
              tokensIn: ev.data.tokens_in,
            })),
          };
        }

        case "llm_response": {
          // Append ThinkingBlock (if thinking) + ToolBlock per tool_call.
          // Visual order matches mockup (thinking before tools in same turn).
          return {
            ...s,
            rawEvents,
            turns: updateLastAgentTurn(s.turns, (t) => {
              const newBlocks: Block[] = [...t.blocks];
              if (ev.data.thinking) {
                newBlocks.push({ type: "thinking", text: ev.data.thinking });
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

  reset: () => set({ ..._initial() }),
}));
