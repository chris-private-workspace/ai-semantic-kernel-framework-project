/**
 * File: frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts
 * Purpose: Vitest coverage for Sprint 57.21 mergeEvent Turn-block-sequence reducer.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.21 Day 1 / US-B3
 *
 * Description:
 *   Exercises each of the 14 SSE event types' new Phase-1 behavior:
 *   block emission into active AgentTurn + dual-emit preservation of legacy
 *   slices (rawEvents / approvals / verifications / subagents). Companion
 *   chatStore.subagents.test.ts + chatStore.verifications.test.ts continue
 *   to test those slices' Sprint 57.11/57.12 behavior; this file adds Phase-1
 *   Turn-side coverage.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 1)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 1 / US-B3)
 */

import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type {
  AgentTurn,
  HITLTurn,
  LoopEvent,
  SubagentForkBlock,
  ThinkingBlock,
  ToolBlock,
  Turn,
  VerificationBlock,
} from "@/features/chat_v2/types";

const turnStart = (): LoopEvent => ({ type: "turn_start", data: { turn_num: 1 } });

const llmRequest = (tokensIn = 100): LoopEvent => ({
  type: "llm_request",
  data: { model: "claude-haiku-4-5", tokens_in: tokensIn },
});

const llmResponse = (opts: {
  content?: string;
  thinking?: string | null;
  toolCalls?: Array<{ id: string; name: string; arguments: Record<string, unknown> }>;
}): LoopEvent => ({
  type: "llm_response",
  data: {
    content: opts.content ?? "",
    thinking: opts.thinking ?? null,
    tool_calls: opts.toolCalls ?? [],
  },
});

const toolReq = (id: string, name = "metrics.query", args: Record<string, unknown> = {}): LoopEvent => ({
  type: "tool_call_request",
  data: { tool_call_id: id, tool_name: name, args },
});

const toolResult = (id: string, isError = false): LoopEvent => ({
  type: "tool_call_result",
  data: {
    tool_call_id: id,
    tool_name: "metrics.query",
    duration_ms: 210,
    result: isError ? "boom" : "ok-output",
    is_error: isError,
  },
});

const loopEnd = (stop = "end_turn", total = 1): LoopEvent => ({
  type: "loop_end",
  data: { stop_reason: stop, total_turns: total },
});

const verifPassed = (verifier = "rules_v1"): LoopEvent => ({
  type: "verification_passed",
  data: { verifier, verifier_type: "rules_based", score: 0.95 },
});

const verifFailed = (verifier = "judge_v1"): LoopEvent => ({
  type: "verification_failed",
  data: {
    verifier,
    verifier_type: "llm_judge",
    reason: "missing-evidence",
    suggested_correction: "add metrics link",
  },
});

const subSpawned = (id: string, mode = "fork"): LoopEvent => ({
  type: "subagent_spawned",
  data: { subagent_id: id, mode, parent_session_id: "sess-1" },
});

const subCompleted = (id: string): LoopEvent => ({
  type: "subagent_completed",
  data: { subagent_id: id, summary: "done", tokens_used: 42 },
});

const approvalRequested = (id: string, level = "HIGH"): LoopEvent => ({
  type: "approval_requested",
  data: { approval_request_id: id, risk_level: level },
});

const approvalReceived = (id: string, decision = "APPROVED"): LoopEvent => ({
  type: "approval_received",
  data: { approval_request_id: id, decision },
});

const guardrailTriggered = (): LoopEvent => ({
  type: "guardrail_triggered",
  data: { guardrail_type: "input", action: "block", reason: "PII detected" },
});

const lastAgentTurn = (turns: Turn[]): AgentTurn => {
  for (let i = turns.length - 1; i >= 0; i--) {
    if (turns[i].role === "agent") return turns[i] as AgentTurn;
  }
  throw new Error("no agent turn");
};

describe("chatStore.mergeEvent Turn block sequence (Sprint 57.21 Day 1)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  // --- Lifecycle ----------------------------------------------------------

  test("pushUserMessage creates UserTurn with text + role=user", () => {
    useChatStore.getState().pushUserMessage("hello");
    const { turns } = useChatStore.getState();
    expect(turns).toHaveLength(1);
    expect(turns[0].role).toBe("user");
    if (turns[0].role === "user") expect(turns[0].text).toBe("hello");
  });

  test("turn_start pushes empty AgentTurn with null metadata", () => {
    useChatStore.getState().mergeEvent(turnStart());
    const { turns } = useChatStore.getState();
    expect(turns).toHaveLength(1);
    expect(turns[0].role).toBe("agent");
    const t = turns[0] as AgentTurn;
    expect(t.blocks).toEqual([]);
    expect(t.stopReason).toBeNull();
    expect(t.tokensIn).toBeNull();
    expect(t.tokensOut).toBeNull();
    expect(t.costUsd).toBeNull();
    expect(t.traceId).toBeNull();
  });

  test("llm_request populates active AgentTurn tokensIn", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(llmRequest(14820));
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.tokensIn).toBe(14820);
  });

  // --- llm_response → blocks ---------------------------------------------

  test("llm_response with thinking only appends ThinkingBlock", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(llmResponse({ thinking: "Hmm, let me think." }));
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.blocks).toHaveLength(1);
    expect(t.blocks[0].type).toBe("thinking");
    expect((t.blocks[0] as ThinkingBlock).text).toBe("Hmm, let me think.");
  });

  test("llm_response with tool_calls appends ToolBlock per call (status=pending)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(
      llmResponse({
        toolCalls: [
          { id: "tc-1", name: "incidents.list", arguments: { since: "30d" } },
          { id: "tc-2", name: "metrics.query", arguments: {} },
        ],
      }),
    );
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.blocks).toHaveLength(2);
    const tools = t.blocks.filter((b): b is ToolBlock => b.type === "tool");
    expect(tools).toHaveLength(2);
    expect(tools[0].toolCallId).toBe("tc-1");
    expect(tools[0].name).toBe("incidents.list");
    expect(tools[0].status).toBe("pending");
    expect(tools[1].toolCallId).toBe("tc-2");
  });

  test("llm_response with thinking + tool_calls: thinking first, then tools (mockup order)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(
      llmResponse({
        thinking: "I should query metrics first.",
        toolCalls: [{ id: "tc-1", name: "metrics.query", arguments: {} }],
      }),
    );
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.blocks.map((b) => b.type)).toEqual(["thinking", "tool"]);
  });

  // --- tool flow ----------------------------------------------------------

  test("tool_call_request defensively appends ToolBlock if not yet present", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(toolReq("tc-3", "memory.read"));
    const t = lastAgentTurn(useChatStore.getState().turns);
    const tool = t.blocks.find((b) => b.type === "tool") as ToolBlock;
    expect(tool.toolCallId).toBe("tc-3");
    expect(tool.name).toBe("memory.read");
    expect(tool.status).toBe("pending");
  });

  test("tool_call_request dedups when ToolBlock already present (from llm_response)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(
      llmResponse({ toolCalls: [{ id: "tc-4", name: "incidents.list", arguments: {} }] }),
    );
    useChatStore.getState().mergeEvent(toolReq("tc-4", "incidents.list"));
    const t = lastAgentTurn(useChatStore.getState().turns);
    const tools = t.blocks.filter((b) => b.type === "tool");
    expect(tools).toHaveLength(1);
  });

  test("tool_call_result success: ToolBlock status=ok + output + durationMs", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(toolReq("tc-5"));
    useChatStore.getState().mergeEvent(toolResult("tc-5", false));
    const t = lastAgentTurn(useChatStore.getState().turns);
    const tool = t.blocks.find((b) => b.type === "tool") as ToolBlock;
    expect(tool.status).toBe("ok");
    expect(tool.output).toBe("ok-output");
    expect(tool.durationMs).toBe(210);
    expect(tool.isError).toBe(false);
  });

  test("tool_call_result error: ToolBlock status=error + isError=true", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(toolReq("tc-6"));
    useChatStore.getState().mergeEvent(toolResult("tc-6", true));
    const t = lastAgentTurn(useChatStore.getState().turns);
    const tool = t.blocks.find((b) => b.type === "tool") as ToolBlock;
    expect(tool.status).toBe("error");
    expect(tool.isError).toBe(true);
  });

  // --- verification -------------------------------------------------------

  test("verification_passed dual-emit: VerificationBlock ok=true + verifications slice", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(verifPassed("rules_v1"));
    const state = useChatStore.getState();
    const t = lastAgentTurn(state.turns);
    const vBlock = t.blocks.find((b) => b.type === "verification") as VerificationBlock;
    expect(vBlock.ok).toBe(true);
    expect(vBlock.verifier).toBe("rules_v1");
    expect(state.verifications).toHaveLength(1); // dual-emit preserved
  });

  test("verification_failed dual-emit: VerificationBlock ok=false reason+correction", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(verifFailed());
    const state = useChatStore.getState();
    const t = lastAgentTurn(state.turns);
    const vBlock = t.blocks.find((b) => b.type === "verification") as VerificationBlock;
    expect(vBlock.ok).toBe(false);
    expect(vBlock.claim).toBe("missing-evidence");
    expect(vBlock.evidence).toBe("add metrics link");
    expect(state.verifications).toHaveLength(1);
  });

  // --- subagent_fork ------------------------------------------------------

  test("subagent_spawned dual-emit: SubagentForkBlock with 1 agent + subagents slice", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(subSpawned("sa-1", "fork"));
    const state = useChatStore.getState();
    const t = lastAgentTurn(state.turns);
    const fork = t.blocks.find((b) => b.type === "subagent_fork") as SubagentForkBlock;
    expect(fork.agents).toHaveLength(1);
    expect(fork.agents[0].id).toBe("sa-1");
    expect(fork.agents[0].status).toBe("running");
    expect(state.subagents).toHaveLength(1); // dual-emit preserved
  });

  test("second subagent_spawned in same turn extends existing SubagentForkBlock", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(subSpawned("sa-1"));
    useChatStore.getState().mergeEvent(subSpawned("sa-2"));
    const t = lastAgentTurn(useChatStore.getState().turns);
    const forkBlocks = t.blocks.filter((b) => b.type === "subagent_fork");
    expect(forkBlocks).toHaveLength(1);
    expect((forkBlocks[0] as SubagentForkBlock).agents).toHaveLength(2);
  });

  test("subagent_completed updates agent entry status='done' in fork block", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(subSpawned("sa-3"));
    useChatStore.getState().mergeEvent(subCompleted("sa-3"));
    const t = lastAgentTurn(useChatStore.getState().turns);
    const fork = t.blocks.find((b) => b.type === "subagent_fork") as SubagentForkBlock;
    expect(fork.agents[0].status).toBe("done");
  });

  // --- approval (HITL) ---------------------------------------------------

  test("approval_requested dual-emit: HITLTurn pushed + approvals dict populated", () => {
    useChatStore.getState().mergeEvent(approvalRequested("ap-1", "HIGH"));
    const state = useChatStore.getState();
    const hitl = state.turns.find((t) => t.role === "hitl") as HITLTurn;
    expect(hitl.approvalRequestId).toBe("ap-1");
    expect(hitl.severity).toBe("risk-high");
    expect(hitl.decision).toBeNull();
    expect(state.approvals["ap-1"]).toBeDefined();
    expect(state.approvals["ap-1"].decision).toBeNull();
  });

  test("approval_received dual-emit: HITLTurn decision + approvals dict update", () => {
    useChatStore.getState().mergeEvent(approvalRequested("ap-2", "CRITICAL"));
    useChatStore.getState().mergeEvent(approvalReceived("ap-2", "REJECTED"));
    const state = useChatStore.getState();
    const hitl = state.turns.find((t) => t.role === "hitl") as HITLTurn;
    expect(hitl.decision).toBe("REJECTED");
    expect(state.approvals["ap-2"].decision).toBe("REJECTED");
  });

  test("approval_requested risk_level mapping covers low/medium/high/critical", () => {
    useChatStore.getState().mergeEvent(approvalRequested("low-id", "low"));
    useChatStore.getState().mergeEvent(approvalRequested("med-id", "MEDIUM"));
    useChatStore.getState().mergeEvent(approvalRequested("hi-id", "High"));
    useChatStore.getState().mergeEvent(approvalRequested("crit-id", "CRITICAL"));
    const turns = useChatStore.getState().turns.filter((t) => t.role === "hitl") as HITLTurn[];
    expect(turns.map((t) => t.severity)).toEqual([
      "risk-low",
      "risk-medium",
      "risk-high",
      "risk-critical",
    ]);
  });

  // --- loop_end ----------------------------------------------------------

  test("loop_end with stop=end_turn: active turn stopReason='end_turn' + waiting=false", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(loopEnd("end_turn", 1));
    const state = useChatStore.getState();
    expect(state.status).toBe("completed");
    expect(state.stopReason).toBe("end_turn");
    const t = lastAgentTurn(state.turns);
    expect(t.stopReason).toBe("end_turn");
    expect(t.waiting).toBe(false);
  });

  test("loop_end with stop=tool_use: active turn waiting=true (interim stop)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(loopEnd("tool_use", 1));
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.waiting).toBe(true);
  });

  // --- guardrail + audit trail -------------------------------------------

  test("guardrail_triggered routes to rawEvents only (no turn changes)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    const turnsBefore = useChatStore.getState().turns;
    useChatStore.getState().mergeEvent(guardrailTriggered());
    const state = useChatStore.getState();
    expect(state.turns).toEqual(turnsBefore);
    expect(state.rawEvents).toHaveLength(2); // turn_start + guardrail
  });

  test("end-to-end turn lifecycle: user → turn_start → response → tool req/result → loop_end", () => {
    useChatStore.getState().pushUserMessage("investigate INC-4087");
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(llmRequest(5000));
    useChatStore.getState().mergeEvent(
      llmResponse({
        thinking: "Need metrics.",
        toolCalls: [{ id: "tc-x", name: "metrics.query", arguments: {} }],
      }),
    );
    useChatStore.getState().mergeEvent(toolResult("tc-x", false));
    useChatStore.getState().mergeEvent(loopEnd("end_turn", 1));
    const state = useChatStore.getState();
    expect(state.turns).toHaveLength(2);
    expect(state.turns[0].role).toBe("user");
    expect(state.turns[1].role).toBe("agent");
    const agent = state.turns[1] as AgentTurn;
    expect(agent.tokensIn).toBe(5000);
    expect(agent.stopReason).toBe("end_turn");
    expect(agent.blocks.map((b) => b.type)).toEqual(["thinking", "tool"]);
    expect((agent.blocks[1] as ToolBlock).status).toBe("ok");
  });
});
