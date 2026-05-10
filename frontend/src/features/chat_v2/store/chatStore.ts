/**
 * File: frontend/src/features/chat_v2/store/chatStore.ts
 * Purpose: Zustand store for chat-v2 — accumulates messages from SSE events.
 * Category: Frontend / chat_v2 / store
 * Scope: Phase 50 / Sprint 50.2 (Day 3.3)
 *
 * Description:
 *   Single Zustand store holding session state + rendered messages list.
 *   Action `mergeEvent(ev)` is the canonical reducer that transforms raw
 *   LoopEvent stream into UI-friendly Message[] and tool-call card state.
 *
 *   Folding rules:
 *     - loop_start         → reset state, set sessionId
 *     - turn_start         → no-op (UI doesn't render turn boundaries directly)
 *     - llm_request        → no-op (covered by next llm_response)
 *     - llm_response       → push assistant Message; carry tool_calls into card array
 *     - tool_call_request  → ensure toolCallEntry exists on current assistant message
 *     - tool_call_result   → merge result/is_error/duration into matching toolCallEntry
 *     - loop_end           → set status=completed + total_turns + stop_reason
 *
 *   Each ChatRequest the user sends must be preceded by `pushUserMessage` to
 *   record their input in the rendered list before the SSE stream starts.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.3)
 * Last Modified: 2026-04-30
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.12 US-6 — add subagents slice + reducers + mergeEvent SSE branch (closes AD-Cat11-SSEEvents)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.3)
 *
 * Related:
 *   - ../types.ts (LoopEvent + Message + ToolCallEntry)
 *   - ../hooks/useLoopEventStream.ts (calls mergeEvent per SSE chunk)
 *   - ../../subagent/types.ts (SubagentNode UI tree node)
 */

import { create } from "zustand";

import type { SubagentNode } from "../../subagent/types";
import type { VerificationEvent } from "../../verification/types";
import type {
  ApprovalEntry,
  ChatMode,
  ChatStatus,
  LoopEvent,
  Message,
  ToolCallEntry,
} from "../types";

type ChatStoreState = {
  sessionId: string | null;
  status: ChatStatus;
  totalTurns: number;
  stopReason: string | null;
  errorMessage: string | null;
  mode: ChatMode;
  messages: Message[];
  rawEvents: LoopEvent[];
  // Sprint 53.5 US-2: HITL approval cards keyed by request_id (dedup-safe).
  approvals: Record<string, ApprovalEntry>;
  // Sprint 57.11 US-5: Cat 10 verification events for inline VerificationPanel
  // (chronological append; cleared on reset / new session).
  verifications: VerificationEvent[];
  // Sprint 57.12 US-6: Cat 11 subagent tree nodes for inline SubagentTree
  // (keyed-update by subagent_id; cleared on reset / new session).
  subagents: SubagentNode[];
  // actions
  setMode: (m: ChatMode) => void;
  setStatus: (s: ChatStatus) => void;
  setError: (msg: string | null) => void;
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
  | "messages"
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
  messages: [],
  rawEvents: [],
  approvals: {},
  verifications: [],
  subagents: [],
});

let _msgCounter = 0;
const nextMsgId = (): string => `m_${++_msgCounter}`;

export const useChatStore = create<ChatStoreState>((set) => ({
  ..._initial(),
  mode: "echo_demo",

  setMode: (m) => set({ mode: m }),
  setStatus: (s) => set({ status: s }),
  setError: (msg) => set({ errorMessage: msg }),

  pushUserMessage: (content) =>
    set((s) => ({
      messages: [...s.messages, { kind: "user", id: nextMsgId(), content }],
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

        case "turn_start":
        case "llm_request":
          // Frame markers — recorded in rawEvents, no UI fold.
          return { ...s, rawEvents };

        case "llm_response": {
          const toolCalls: ToolCallEntry[] = ev.data.tool_calls.map((tc) => ({
            toolCallId: tc.id,
            toolName: tc.name,
            args: tc.arguments,
          }));
          const assistantMsg: Message = {
            kind: "assistant",
            id: nextMsgId(),
            content: ev.data.content,
            thinking: ev.data.thinking,
            toolCalls,
          };
          return {
            ...s,
            rawEvents,
            messages: [...s.messages, assistantMsg],
          };
        }

        case "tool_call_request": {
          // Ensure the most recent assistant Message has this card.
          // (Llm_response carries tool_calls already; this branch covers
          // the rare case where Loop yields ToolCallRequested without a
          // preceding LLMResponded — defensive.)
          const updated = [...s.messages];
          for (let i = updated.length - 1; i >= 0; i--) {
            const m = updated[i];
            if (m.kind !== "assistant") continue;
            if (m.toolCalls.some((c) => c.toolCallId === ev.data.tool_call_id)) break;
            updated[i] = {
              ...m,
              toolCalls: [
                ...m.toolCalls,
                {
                  toolCallId: ev.data.tool_call_id,
                  toolName: ev.data.tool_name,
                  args: ev.data.args,
                },
              ],
            };
            break;
          }
          return { ...s, rawEvents, messages: updated };
        }

        case "tool_call_result": {
          const updated = s.messages.map((m) => {
            if (m.kind !== "assistant") return m;
            const idx = m.toolCalls.findIndex(
              (c) => c.toolCallId === ev.data.tool_call_id,
            );
            if (idx === -1) return m;
            const newCalls = m.toolCalls.slice();
            newCalls[idx] = {
              ...newCalls[idx],
              result: ev.data.result,
              isError: ev.data.is_error,
              durationMs: ev.data.duration_ms,
            };
            return { ...m, toolCalls: newCalls };
          });
          return { ...s, rawEvents, messages: updated };
        }

        case "loop_end": {
          return {
            ...s,
            rawEvents,
            status: "completed",
            totalTurns: ev.data.total_turns,
            stopReason: ev.data.stop_reason,
          };
        }

        case "approval_requested": {
          // 53.5 US-2: render inline ApprovalCard. Dedup by request_id.
          const id = ev.data.approval_request_id;
          if (!id) return { ...s, rawEvents };
          if (s.approvals[id]) return { ...s, rawEvents };
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
          };
        }

        case "approval_received": {
          // 53.5 US-2: update card to show reviewer outcome.
          const id = ev.data.approval_request_id;
          if (!id) return { ...s, rawEvents };
          const existing = s.approvals[id];
          if (!existing) {
            // Decision arrived without prior request — defensive create
            return {
              ...s,
              rawEvents,
              approvals: {
                ...s.approvals,
                [id]: {
                  approvalRequestId: id,
                  riskLevel: "UNKNOWN",
                  decision: ev.data.decision,
                  receivedAt: Date.now(),
                },
              },
            };
          }
          return {
            ...s,
            rawEvents,
            approvals: {
              ...s.approvals,
              [id]: { ...existing, decision: ev.data.decision },
            },
          };
        }

        // Sprint 53.6 D2: GuardrailTriggered routes to rawEvents only.
        // No UI surface in 53.6 — future sprint may render warning banner.
        case "guardrail_triggered": {
          return { ...s, rawEvents };
        }

        // Sprint 57.11 US-5: Cat 10 verification events. Append to verifications
        // array for inline VerificationPanel + raw event audit trail (rawEvents).
        // AD-Frontend-SSE-Silent-Drop-Fix bundle: type+set listed in types.ts
        // per CONVENTION.md §7 3-edit checklist.
        case "verification_passed":
        case "verification_failed": {
          return {
            ...s,
            rawEvents,
            verifications: [...s.verifications, ev as VerificationEvent],
          };
        }

        // Sprint 57.12 US-6: Cat 11 subagent lifecycle events. Spawned → push
        // a "running" node; Completed → update the matching node to "completed"
        // + summary + tokens (defensive create if Completed arrives without a
        // prior Spawned). UI status derived from event ordering per Day 1 D1-005.
        // AD-Cat11-SSEEvents: type+set listed in types.ts per CONVENTION.md §7.
        case "subagent_spawned": {
          const sid = ev.data.subagent_id;
          if (!sid) return { ...s, rawEvents };
          if (s.subagents.some((n) => n.subagentId === sid)) return { ...s, rawEvents };
          const node: SubagentNode = {
            subagentId: sid,
            parentId: ev.data.parent_session_id,
            mode: ev.data.mode,
            status: "running",
            summary: null,
            tokensUsed: null,
            spawnedAt: Date.now(),
          };
          return { ...s, rawEvents, subagents: [...s.subagents, node] };
        }

        case "subagent_completed": {
          const sid = ev.data.subagent_id;
          if (!sid) return { ...s, rawEvents };
          const idx = s.subagents.findIndex((n) => n.subagentId === sid);
          if (idx === -1) {
            // Defensive create — Completed arrived without prior Spawned.
            const node: SubagentNode = {
              subagentId: sid,
              parentId: null,
              mode: "unknown",
              status: "completed",
              summary: ev.data.summary,
              tokensUsed: ev.data.tokens_used,
              spawnedAt: Date.now(),
            };
            return { ...s, rawEvents, subagents: [...s.subagents, node] };
          }
          const updated = s.subagents.slice();
          updated[idx] = {
            ...updated[idx],
            status: "completed",
            summary: ev.data.summary,
            tokensUsed: ev.data.tokens_used,
          };
          return { ...s, rawEvents, subagents: updated };
        }

        default: {
          // Unreachable: parser filters unknown event types upstream.
          // Defensive return to keep TypeScript exhaustive-check happy.
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
