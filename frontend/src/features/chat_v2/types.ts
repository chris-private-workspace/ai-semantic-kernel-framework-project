/**
 * File: frontend/src/features/chat_v2/types.ts
 * Purpose: SSE LoopEvent types (18) + Turn/Block/Session UI aggregate types (Sprint 57.21).
 * Category: Frontend / chat_v2
 * Scope: Phase 50 / Sprint 50.2 + Phase 57.21 (Day 1 — Turn block model rewrite per mockup)
 *
 * Description:
 *   Three discriminated unions:
 *   1. LoopEvent — 18 SSE wire types (Sprint 50.2 + 53.5 + 53.6 + 57.11 + 57.12 + 57.66);
 *      1:1 backend serialize_loop_event output. Preserved EXACTLY in Sprint 57.21.
 *   2. Turn — UI aggregate per-turn model (user / agent / hitl) per mockup
 *      reference/design-mockups/page-chat.jsx L17-70 + L159-313. NEW in Sprint 57.21.
 *   3. Block — UI per-event presentation unit within an agent Turn (thinking /
 *      tool / verification / subagent_fork) per mockup L199-267. 4 of 5 mockup
 *      types ship Sprint 57.21; memory block DEFERRED to Phase-2+
 *      (AD-ChatV2-Memory-Block-Phase2 — requires NEW Cat 3 SSE event).
 *   4. Session — session list entry. Sprint 57.107 B3: now real-backend shaped
 *      (GET /sessions); was fixture-driven (mockup L5-12).
 *
 *   ToolCallEntry preserved as chatStore.mergeEvent internal pairing helper.
 *   ApprovalEntry preserved (HITL workflow Phase-1 keeps existing 2-action wire).
 *   Message removed — replaced by Turn. tsc compile gate surfaces consumer updates.
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.2)
 * Last Modified: 2026-06-16
 *
 * Modification History:
 *   - 2026-06-16: Sprint 57.131 — AgentTurn +model (per-turn LLM model for the Inspector Turn row)
 *   - 2026-06-16: Sprint 57.130 — AgentTurn +terminated? (LoopTerminated wire surface)
 *   - 2026-06-16: Sprint 57.126 — +UserMessageEvent (persist-only replay event; not a wire type)
 *   - 2026-06-15: Sprint 57.120 — AgentTurn +activeSkill? (Inspector active_skill row)
 *   - 2026-06-12: Sprint 57.107 B3 — Session now real-backend shaped (+handoffParentId +agentRole, title/agent nullable, drop domain) + SessionStatusUI +handed_off
 *   - 2026-06-11: Sprint 57.101 B1 — UserTurn +injected? (mid-run message_injected render tag)
 *   - 2026-06-10: Sprint 57.100 — HITLTurn +kind (pause kind from the approval_requested wire)
 *   - 2026-06-02: Sprint 57.67 — event types now re-exported from generated/loopEvents.generated (A-5b codegen)
 *   - 2026-06-02: Sprint 57.66 — +4 diagnostic events + cache fields on llm_response/loop_end
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
// Sprint 57.67 (A-5b): the 18 event interfaces + LLMToolCall element + the
// LoopEvent union + KNOWN_LOOP_EVENT_TYPES are now GENERATED from the single
// declarative registry backend/src/api/v1/chat/event_wire_schema.py (via
// scripts/codegen/generate_event_schemas.py). Re-exported here so every
// downstream `import { ... } from "../types"` keeps working unchanged. To add
// or change a wire-type, edit the registry + re-run the codegen — never edit
// the generated file or hand-write the type here. Drift is gated by
// scripts/lint/check_event_schema_sync.py + the pytest parity test.
export * from "./generated/loopEvents.generated";

// === Sprint 57.126: persist-only replay event (NOT a live wire type) ======
// The 57.126 backend writer persists the user's prompt as a `user_message`
// message_events row at the start of each send (the live UI shows it via
// pushUserMessage, so it is NEVER streamed — it is NOT in event_wire_schema /
// KNOWN_LOOP_EVENT_TYPES / the codegen union). chatStore.loadSessionHistory
// replays it through mergeEvent (a dedicated `user_message` case pushes the
// UserTurn) so a historical session's user prompts reappear. Hand-written here
// because it has no live wire schema entry (it does not count toward the wire total).
export type UserMessageEvent = {
  type: "user_message";
  data: { text: string };
};

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
  /** Sprint 57.103 B2b: spawn mode (fork / teammate / …) for the mode-aware inline label. */
  mode: string;
  /** Sprint 57.103 B2b: tokens once subagent_completed arrives (null while running). */
  tokensUsed: number | null;
};

export type ThinkingBlock = {
  type: "thinking";
  text: string;
};

// Honest-surface (CHANGE-054): the agent's final text answer (llm_response.content).
// The mockup's block set (thinking / tool / verification / subagent_fork) had NO
// assistant-answer block, so a plain Q&A turn (content, no tool call) rendered
// nothing — the user saw an empty turn. This block makes the answer visible.
export type AnswerBlock = {
  type: "answer";
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

export type Block =
  | ThinkingBlock
  | AnswerBlock
  | ToolBlock
  | VerificationBlock
  | SubagentForkBlock;

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
  // Sprint 57.101 B1: true when this is a mid-run injected instruction (rendered
  // from a message_injected event on drain), so the timeline can tag it.
  injected?: boolean;
  // Sprint 57.116: the force-loaded skill name (from the server-confirmed
  // loop_start.active_skill), stamped onto the turn that triggered the run so the
  // timeline can chip it. Undefined when no skill was force-loaded.
  activeSkill?: string;
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
  // Sprint 57.133: actual prompt-cache-hit tokens for this turn (captured from
  // llm_response.cached_input_tokens with the same 0-guard as tokensIn/Out). null
  // until the turn's first llm_response. Surfaced as the Inspector Turn tab
  // `tokens.cached` KV row + a derived `cache_hit` (cachedInputTokens / tokensIn);
  // closes the token-sweep leg of AD-ChatV2-Inspector-Turn-Metadata-Wire.
  cachedInputTokens: number | null;
  // Sprint 57.131: the LLM model that ran this turn (captured from llm_request.model
  // in the same mergeEvent case that sets tokensIn). null until the turn's first
  // llm_request fires (turn_start initializes it null; a multi-call turn keeps the
  // latest). Surfaced as the Inspector Turn tab `model` KV row (closes the model-row
  // leg of AD-ChatV2-Inspector-Turn-Metadata-Wire).
  model: string | null;
  traceId: string | null;
  spanId: string | null;
  // Sprint 57.120: the force-loaded skill for this turn's loop (carried from the
  // trigger UserTurn at turn_start), so the Inspector Turn tab can show an
  // active_skill row alongside trace_id. Undefined when no skill was force-loaded.
  activeSkill?: string;
  // Sprint 57.130: set when a Cat-8 fatal terminate (LoopTerminated) ended this
  // turn's loop (there is no loop_end). The head renders a danger badge with the
  // reason + any dangling pending tool block flips to error. Undefined for a
  // normally-completed turn.
  terminated?: { reason: string; detail?: string | null };
};

export type HITLTurn = {
  role: "hitl";
  id: string;
  at: string;
  title: string;
  severity: RiskSeverity;
  tool: string;
  // Sprint 57.100: the pause kind from the approval_requested wire
  // (tool/input/between_turns/output/verification) — the HITL card branches
  // REJECT on kind === "verification" (coach-one-turn vs terminate).
  kind: string;
  payload: string;
  rationale: string;
  approvalRequestId: string;
  decision: string | null;
  countdownSec: number | null;
};

export type Turn = UserTurn | AgentTurn | HITLTurn;

// === Sprint 57.21: Session fixture type ===================================
// Per mockup L5-12. Backend wire deferred (AD-ChatV2-SessionList-Backend).

// Sprint 57.107 B3: backend session status maps to one of these. `handed_off`
// is the Cat 11 HANDOFF child marker (backend `handed_off`); `hitl` has no
// backend source yet but is preserved for forward use.
export type SessionStatusUI = "running" | "hitl" | "handed_off" | "done";

export type Session = {
  id: string;
  // Sprint 57.107 B3: real backend `title` may be null (untitled session) — the
  // SessionList renders a fallback label.
  title: string | null;
  // Sprint 57.107 B3: backend `agent_role` (null when unassigned). Previously a
  // fixture-only display string.
  agent: string | null;
  turns: number;
  status: SessionStatusUI;
  // Sprint 57.107 B3: human-readable relative/absolute time derived from the
  // backend `started_at_ms`.
  time: string;
  // Sprint 57.107 B3: the handoff-chain parent session id (null for a root
  // session); non-null renders a chain badge in the SessionList row.
  handoffParentId: string | null;
  // Sprint 57.107 B3: the agent role label for the chain badge (null fallback).
  agentRole: string | null;
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
