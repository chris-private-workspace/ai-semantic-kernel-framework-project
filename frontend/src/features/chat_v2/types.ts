/**
 * File: frontend/src/features/chat_v2/types.ts
 * Purpose: SSE LoopEvent types (14) + Turn/Block/Session UI aggregate types (Sprint 57.21).
 * Category: Frontend / chat_v2
 * Scope: Phase 50 / Sprint 50.2 + Phase 57.21 (Day 1 — Turn block model rewrite per mockup)
 *
 * Description:
 *   Three discriminated unions:
 *   1. LoopEvent — 14 SSE wire types (Sprint 50.2 + 53.5 + 53.6 + 57.11 + 57.12);
 *      1:1 backend serialize_loop_event output. Preserved EXACTLY in Sprint 57.21.
 *   2. Turn — UI aggregate per-turn model (user / agent / hitl) per mockup
 *      reference/design-mockups/page-chat.jsx L17-70 + L159-313. NEW in Sprint 57.21.
 *   3. Block — UI per-event presentation unit within an agent Turn (thinking /
 *      tool / verification / subagent_fork) per mockup L199-267. 4 of 5 mockup
 *      types ship Sprint 57.21; memory block DEFERRED to Phase-2+
 *      (AD-ChatV2-Memory-Block-Phase2 — requires NEW Cat 3 SSE event).
 *   4. Session — fixture-driven session list entry per mockup L5-12.
 *      Backend wire deferred (AD-ChatV2-SessionList-Backend Sprint 57.22+).
 *
 *   ToolCallEntry preserved as chatStore.mergeEvent internal pairing helper.
 *   ApprovalEntry preserved (HITL workflow Phase-1 keeps existing 2-action wire).
 *   Message removed — replaced by Turn. tsc compile gate surfaces consumer updates.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.2)
 * Last Modified: 2026-05-17
 *
 * Modification History:
 *   - 2026-05-17: Sprint 57.21 Day 1 — Turn/Block/Session unions; remove Message
 *   - 2026-05-10: Sprint 57.12 US-6 — Subagent{Spawned,Completed}Event + KNOWN set
 *   - 2026-05-04: Sprint 53.6 D2 — GuardrailTriggeredEvent defensive type
 *   - 2026-05-04: Sprint 53.5 US-2 — ApprovalRequested + ApprovalReceived events
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.2)
 *
 * Related:
 *   - backend/src/api/v1/chat/sse.py (server-side serializer)
 *   - reference/design-mockups/page-chat.jsx (Turn/Block visual target)
 *   - 02-architecture-design.md §SSE 事件規範
 *   - 17-cross-category-interfaces.md §SSE LoopEvent contracts
 */

// === LoopEvent SSE wire types ============================================
// PRESERVE EXACTLY from Sprint 50.2-57.12 — 1:1 backend contract.

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
    decision: string;
  };
};

export type GuardrailTriggeredEvent = {
  type: "guardrail_triggered";
  data: {
    guardrail_type: string;
    action: string;
    reason: string;
  };
};

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

export type SubagentSpawnedEvent = {
  type: "subagent_spawned";
  data: {
    subagent_id: string | null;
    mode: string;
    parent_session_id: string | null;
  };
};

export type SubagentCompletedEvent = {
  type: "subagent_completed";
  data: {
    subagent_id: string | null;
    summary: string;
    tokens_used: number;
  };
};

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
  | VerificationFailedEvent
  | SubagentSpawnedEvent
  | SubagentCompletedEvent;

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
  "verification_passed",
  "verification_failed",
  "subagent_spawned",
  "subagent_completed",
]);

// === Sprint 57.21: Block discriminated union ==============================
// 4 of 5 mockup block types ship Phase-1. Memory block (mockup L224-232)
// DEFERRED to Phase-2+ — requires NEW Cat 3 SSE event (AD-ChatV2-Memory-Block-Phase2).
// Why discriminated union: render dispatcher in TurnList/AgentTurn can narrow
// by block.type without runtime instanceof; tsc enforces exhaustive cases.

export type ToolBlockStatus = "pending" | "ok" | "error";

export type SubagentEntry = {
  id: string;
  name: string;
  task: string;
  status: "running" | "done";
  turns: number;
};

export type ThinkingBlock = {
  type: "thinking";
  text: string;
};

export type ToolBlock = {
  type: "tool";
  toolCallId: string;
  name: string;
  status: ToolBlockStatus;
  input: string;
  output: string | null;
  durationMs: number | null;
  isError: boolean;
};

export type VerificationBlock = {
  type: "verification";
  verifier: string;
  ok: boolean;
  claim: string;
  evidence: string;
};

export type SubagentForkBlock = {
  type: "subagent_fork";
  agents: SubagentEntry[];
};

export type Block = ThinkingBlock | ToolBlock | VerificationBlock | SubagentForkBlock;

// === Sprint 57.21: Turn discriminated union ===============================
// Per mockup L17-70 (TURNS data shape) + L159-313 (render dispatch).
// Inspector Turn tab metadata aggregated best-effort from existing SSE events;
// fields nullable when SSE source absent (placeholder "—" at render time).

export type RiskSeverity = "risk-low" | "risk-medium" | "risk-high" | "risk-critical";

export type UserTurn = {
  role: "user";
  id: string;
  at: string;
  text: string;
};

export type AgentTurn = {
  role: "agent";
  id: string;
  at: string;
  stopReason: string | null;
  durationMs: number | null;
  blocks: Block[];
  waiting?: boolean;
  // Inspector Turn tab metadata (Phase-1 best-effort; null placeholders allowed)
  tokensIn: number | null;
  tokensOut: number | null;
  tokensThinking: number | null;
  costUsd: number | null;
  traceId: string | null;
  spanId: string | null;
};

export type HITLTurn = {
  role: "hitl";
  id: string;
  at: string;
  title: string;
  severity: RiskSeverity;
  tool: string;
  payload: string;
  rationale: string;
  approvalRequestId: string;
  decision: string | null;
  countdownSec: number | null;
};

export type Turn = UserTurn | AgentTurn | HITLTurn;

// === Sprint 57.21: Session fixture type ===================================
// Per mockup L5-12. Backend wire deferred (AD-ChatV2-SessionList-Backend).

export type SessionDomain = "incident" | "audit" | "patrol" | "rca";
export type SessionStatusUI = "running" | "hitl" | "done";

export type Session = {
  id: string;
  title: string;
  agent: string;
  turns: number;
  status: SessionStatusUI;
  time: string;
  domain: SessionDomain;
};

// === UI aggregate types (preserved from Sprint 50.2 + 53.5) ===============
// ToolCallEntry: chatStore.mergeEvent internal pairing helper. Tool flow:
//   tool_call_request → enqueue ToolCallEntry; tool_call_result → finalize.
// On finalize, mergeEvent emits a ToolBlock into the active agent turn.

export type ToolCallEntry = {
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  result?: string;
  isError?: boolean;
  durationMs?: number;
};

/** Sprint 53.5 US-2: HITL approval card state. Phase-1 preserved (2-action backend wire). */
export type ApprovalEntry = {
  approvalRequestId: string;
  riskLevel: string;
  decision: string | null;
  receivedAt: number;
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
