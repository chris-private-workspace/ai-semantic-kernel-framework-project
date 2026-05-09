/**
 * File: frontend/src/features/chat_v2/types.ts
 * Purpose: SSE LoopEvent types — 1:1 alignment with 02-architecture-design.md §SSE.
 * Category: Frontend / chat_v2
 * Scope: Phase 50 / Sprint 50.2 (Day 3.2)
 *
 * Description:
 *   Discriminated union mirroring the backend SSE wire format. Sprint 50.2
 *   wires 8 event types end-to-end (loop_start / turn_start / llm_request /
 *   llm_response / tool_call_request / tool_call_result / loop_end +
 *   error / unknown fallback). Other 02.md §SSE event types
 *   (guardrail_check / tripwire_fired / compaction_triggered / hitl_required /
 *   verification_*) are reserved for later phases — frontend ignores them
 *   gracefully via the `unknown` arm.
 *
 *   Plus UI-side aggregate types: Message (rendered list item), ToolCallEntry
 *   (paired request+result), ChatSession, ChatMode.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.2)
 * Last Modified: 2026-04-30
 *
 * Modification History:
 *   - 2026-05-04: Add GuardrailTriggeredEvent type (Sprint 53.6 D2 — Day 0 探勘 finding)
 *     — backend yields GuardrailTriggered 7× in loop.py (Cat 9 Stage 1/2/3); frontend
 *     defensive type so KNOWN_LOOP_EVENT_TYPES includes the wire type and
 *     LoopEvent union recognises it (no UI surface yet — events route to chatStore.rawEvents).
 *   - 2026-05-04: Add ApprovalRequested + ApprovalReceived events (Sprint 53.5 US-2)
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.2)
 *
 * Related:
 *   - backend/src/api/v1/chat/sse.py (server-side serializer)
 *   - 02-architecture-design.md §SSE 事件規範
 */

// === LoopEvent SSE wire types ===============================================
// Each variant has a `type` discriminator + `data` payload matching the
// backend's serialize_loop_event() output.

export type LoopStartEvent = {
  type: "loop_start";
  data: { session_id: string | null; request_id: string };
};

export type TurnStartEvent = {
  type: "turn_start";
  data: { turn_num: number };
};

export type LLMRequestEvent = {
  type: "llm_request";
  data: { model: string; tokens_in: number };
};

export type LLMToolCall = {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
};

export type LLMResponseEvent = {
  type: "llm_response";
  data: {
    content: string;
    tool_calls: LLMToolCall[];
    thinking: string | null;
  };
};

export type ToolCallRequestEvent = {
  type: "tool_call_request";
  data: {
    tool_call_id: string;
    tool_name: string;
    args: Record<string, unknown>;
  };
};

export type ToolCallResultEvent = {
  type: "tool_call_result";
  data: {
    tool_call_id: string;
    tool_name: string;
    duration_ms: number;
    result: string;
    is_error: boolean;
  };
};

export type LoopEndEvent = {
  type: "loop_end";
  data: { stop_reason: string; total_turns: number };
};

// Sprint 53.5 US-2: HITL approval events. Loop emits ApprovalRequested when
// Cat 9 ESCALATE → HITLManager.request_approval persists; ApprovalReceived
// when wait_for_decision returns. Frontend renders inline ApprovalCard.

export type ApprovalRequestedEvent = {
  type: "approval_requested";
  data: {
    approval_request_id: string | null;
    risk_level: string;
  };
};

export type ApprovalReceivedEvent = {
  type: "approval_received";
  data: {
    approval_request_id: string | null;
    decision: string; // APPROVED / REJECTED / ESCALATED
  };
};

// Sprint 53.6 D2: GuardrailTriggered defensive type. Backend yields this 7×
// in loop.py (Cat 9 Stage 1 input / Stage 2 output / Stage 3 tool escalate
// reject/timeout block paths). No UI surface in 53.6 — event routes to
// chatStore.rawEvents only; future sprint may render warning banner.

export type GuardrailTriggeredEvent = {
  type: "guardrail_triggered";
  data: {
    guardrail_type: string; // input / output / tool
    action: string; // block / sanitize / escalate / reroll
    reason: string;
  };
};

// Sprint 57.11 US-5: Cat 10 Verification SSE events.
// Backend yields these from correction_loop.run_with_verification per verifier;
// SSE schema sourced from api/v1/chat/sse.py:243-265. AD-Frontend-SSE-Silent-
// Drop-Fix bundle (Sprint 57.10 D-PRE-13 codified): both type union AND
// KNOWN_LOOP_EVENT_TYPES set must list these so parseSSEFrame doesn't silently
// drop them per CONVENTION.md §7 3-edit checklist.

export type VerificationPassedEvent = {
  type: "verification_passed";
  data: {
    verifier: string;
    verifier_type: "rules_based" | "llm_judge" | "external";
    score: number | null;
  };
};

export type VerificationFailedEvent = {
  type: "verification_failed";
  data: {
    verifier: string;
    verifier_type: "rules_based" | "llm_judge" | "external";
    reason: string | null;
    suggested_correction: string | null;
  };
};

/**
 * Sprint 50.2 wired 7 known event types; Sprint 53.5 adds 2 (approval_*);
 * Sprint 53.6 adds 1 (guardrail_triggered); Sprint 57.11 adds 2 (verification_*).
 * Unknown event types from later phases are filtered at the SSE parser
 * (chatService.parseSSEFrame returns null) so the store never sees them —
 * preserving discriminated-union narrowing inside mergeEvent's switch.
 */
export type LoopEvent =
  | LoopStartEvent
  | TurnStartEvent
  | LLMRequestEvent
  | LLMResponseEvent
  | ToolCallRequestEvent
  | ToolCallResultEvent
  | LoopEndEvent
  | ApprovalRequestedEvent
  | ApprovalReceivedEvent
  | GuardrailTriggeredEvent
  | VerificationPassedEvent
  | VerificationFailedEvent;

/** Set of SSE event type names recognized by Sprint 50.2 + 53.5 + 53.6 + 57.11 frontend. */
export const KNOWN_LOOP_EVENT_TYPES = new Set<string>([
  "loop_start",
  "turn_start",
  "llm_request",
  "llm_response",
  "tool_call_request",
  "tool_call_result",
  "loop_end",
  "approval_requested",
  "approval_received",
  "guardrail_triggered",
  // Sprint 57.11 US-5: Cat 10 verification SSE events (AD-Frontend-SSE-Silent-Drop-Fix)
  "verification_passed",
  "verification_failed",
]);

// === UI aggregate types =====================================================

/**
 * Rendered message in the conversation. Built by chatStore.mergeEvent from
 * raw LoopEvents. ToolCallCards are folded into the assistant turn that
 * triggered them via the `tool_calls` array.
 */
export type Message =
  | { kind: "user"; id: string; content: string }
  | {
      kind: "assistant";
      id: string;
      content: string;
      thinking: string | null;
      toolCalls: ToolCallEntry[];
    };

export type ToolCallEntry = {
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  // populated when the matching tool_call_result event arrives
  result?: string;
  isError?: boolean;
  durationMs?: number;
};

/** Sprint 53.5 US-2: in-chat HITL approval card state. */
export type ApprovalEntry = {
  approvalRequestId: string;
  riskLevel: string;
  // updated when approval_received arrives; null while pending
  decision: string | null;
  receivedAt: number; // epoch ms when ApprovalRequested arrived
};

export type ChatStatus = "idle" | "running" | "completed" | "cancelled" | "error";

export type ChatMode = "echo_demo" | "real_llm";

export type ChatSession = {
  sessionId: string | null;
  status: ChatStatus;
  totalTurns: number;
  stopReason: string | null;
  errorMessage: string | null;
};
