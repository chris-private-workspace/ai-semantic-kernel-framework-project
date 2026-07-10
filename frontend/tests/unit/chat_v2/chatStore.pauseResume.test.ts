/**
 * File: frontend/tests/unit/chat_v2/chatStore.pauseResume.test.ts
 * Purpose: Vitest coverage for the durable HITL pause-resume continuation reducer path.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.88 Day 3 / US-5
 *
 * Description:
 *   Drives the FULL pause + resume SSE event sequence through chatStore.mergeEvent
 *   and asserts the rendered Turn[] is correct WITHOUT changing the reducer (the
 *   continuation rides the existing tool_call_result-by-id + turn_start handlers).
 *   The one Sprint 57.88 reducer change covered here: loop_start clears the stale
 *   "awaiting approval" indicator on the turn that paused earlier.
 *
 *   Pause stream:  loop_start → turn_start → llm_response(tool_call) →
 *                  approval_requested → loop_end("awaiting_approval")
 *   Resume stream: loop_start → approval_received(APPROVED) →
 *                  tool_call_result(same id) → turn_start → llm_response(answer) →
 *                  loop_end("end_turn")
 *
 * Created: 2026-06-08 (Sprint 57.88 Day 3)
 *
 * Modification History:
 *   - 2026-06-08: Initial creation (Sprint 57.88 Day 3 / US-5)
 */

import { afterEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { AgentTurn, HITLTurn, LoopEvent, ToolBlock, Turn } from "@/features/chat_v2/types";

const ESCALATED_TOOL_ID = "tc-escalate-1";
const APPROVAL_ID = "ar-1";

const loopStart = (sessionId: string): LoopEvent => ({
  type: "loop_start",
  data: { session_id: sessionId },
});
const turnStart = (n: number): LoopEvent => ({ type: "turn_start", data: { turn_num: n } });
const llmToolCall = (): LoopEvent => ({
  type: "llm_response",
  data: {
    content: "",
    thinking: null,
    tool_calls: [{ id: ESCALATED_TOOL_ID, name: "echo_tool", arguments: { text: "hi" } }],
  },
});
const llmAnswer = (content: string): LoopEvent => ({
  type: "llm_response",
  data: { content, thinking: null, tool_calls: [] },
});
const approvalRequested = (level = "HIGH"): LoopEvent => ({
  type: "approval_requested",
  data: { approval_request_id: APPROVAL_ID, risk_level: level },
});
const approvalReceived = (decision = "APPROVED"): LoopEvent => ({
  type: "approval_received",
  data: { approval_request_id: APPROVAL_ID, decision },
});
const toolResult = (): LoopEvent => ({
  type: "tool_call_result",
  data: {
    tool_call_id: ESCALATED_TOOL_ID,
    tool_name: "echo_tool",
    duration_ms: 120,
    result: "echoed: hi",
    is_error: false,
    error_taxonomy: null, // Sprint 57.164
  },
});
const loopEnd = (stop: string, total = 1): LoopEvent => ({
  type: "loop_end",
  data: { stop_reason: stop, total_turns: total },
});

const merge = (...events: LoopEvent[]): void => {
  const { mergeEvent } = useChatStore.getState();
  for (const ev of events) mergeEvent(ev);
};

const firstAgent = (turns: Turn[]): AgentTurn => turns.find((t) => t.role === "agent") as AgentTurn;
const toolBlockOf = (t: AgentTurn): ToolBlock =>
  t.blocks.find((b) => b.type === "tool") as ToolBlock;

describe("chatStore — durable HITL pause-resume (Sprint 57.88)", () => {
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("pause stream: escalated tool stays pending; turn shows awaiting; HITL turn pushed", () => {
    merge(loopStart("sess-1"), turnStart(1), llmToolCall(), approvalRequested("HIGH"), loopEnd("awaiting_approval"));

    const s = useChatStore.getState();
    expect(s.status).toBe("completed"); // SSE stream is genuinely closed during the pause
    expect(s.stopReason).toBe("awaiting_approval");

    const agent = firstAgent(s.turns);
    expect(agent.waiting).toBe(true); // "awaiting approval" indicator on the paused turn
    expect(toolBlockOf(agent).status).toBe("pending"); // escalated tool not yet executed

    const hitl = s.turns.find((t) => t.role === "hitl") as HITLTurn;
    expect(hitl).toBeDefined();
    expect(hitl.approvalRequestId).toBe(APPROVAL_ID);
    expect(hitl.decision).toBeNull();
  });

  test("resume stream: tool resolves by id, awaiting cleared, HITL decided, continuation answer rendered", () => {
    // Pause first.
    merge(loopStart("sess-1"), turnStart(1), llmToolCall(), approvalRequested("HIGH"), loopEnd("awaiting_approval"));
    // Resume continuation.
    merge(
      loopStart("sess-1"),
      approvalReceived("APPROVED"),
      toolResult(),
      turnStart(2),
      llmAnswer("echoed: hi"),
      loopEnd("end_turn"),
    );

    const s = useChatStore.getState();
    expect(s.status).toBe("completed");
    expect(s.stopReason).toBe("end_turn");

    // 3 turns: original agent (paused) → hitl → continuation agent.
    expect(s.turns.map((t) => t.role)).toEqual(["agent", "hitl", "agent"]);

    // Original agent turn: escalated tool now resolved + stale "awaiting" cleared.
    const original = s.turns[0] as AgentTurn;
    expect(original.waiting).toBeFalsy();
    const tool = toolBlockOf(original);
    expect(tool.status).toBe("ok");
    expect(tool.output).toBe("echoed: hi");

    // HITL turn decided APPROVED.
    const hitl = s.turns[1] as HITLTurn;
    expect(hitl.decision).toBe("APPROVED");

    // Continuation agent turn renders the final answer.
    const continuation = s.turns[2] as AgentTurn;
    expect(continuation.blocks.some((b) => b.type === "answer" && b.text === "echoed: hi")).toBe(true);
    expect(continuation.stopReason).toBe("end_turn");
  });

  test("reject path: HITL decided REJECTED, escalated tool never resolves (no continuation)", () => {
    merge(loopStart("sess-1"), turnStart(1), llmToolCall(), approvalRequested("HIGH"), loopEnd("awaiting_approval"));
    // A reject is recorded out-of-band; no resume stream is consumed (no tool result, no continuation turn).
    merge(approvalReceived("REJECTED"));

    const s = useChatStore.getState();
    const hitl = s.turns.find((t) => t.role === "hitl") as HITLTurn;
    expect(hitl.decision).toBe("REJECTED");
    expect(toolBlockOf(firstAgent(s.turns)).status).toBe("pending"); // tool never executed
    expect(s.turns.filter((t) => t.role === "agent")).toHaveLength(1); // no continuation turn
  });
});
