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
 *   - 2026-06-16: Sprint 57.130 — loop_terminated → flip pending tool + terminated record coverage
 *   - 2026-06-12: Sprint 57.108 — HITL tool/reason + traceId/spanId/tokens/duration capture coverage
 *   - 2026-06-11: Sprint 57.101 B1 — message_injected → UserTurn(injected) coverage
 *   - 2026-06-03: Sprint 57.75 — span_started/span_ended/memory_accessed → spans + memoryOps slice coverage
 *   - 2026-06-02: Sprint 57.69 — agent_handoff pivot + handoffBanner / pivotSession / dismiss coverage
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 1 / US-B3)
 */

import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type {
  AgentTurn,
  HITLTurn,
  LoopEvent,
  Session,
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
  inputTokens?: number;
  outputTokens?: number;
}): LoopEvent => ({
  type: "llm_response",
  data: {
    content: opts.content ?? "",
    thinking: opts.thinking ?? null,
    tool_calls: opts.toolCalls ?? [],
    // Sprint 57.108: per-call token actuals (omitted by default — old-frame shape).
    input_tokens: opts.inputTokens,
    output_tokens: opts.outputTokens,
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

const subChild = (
  id: string,
  innerType: string,
  inner: Record<string, unknown>,
): LoopEvent => ({
  type: "subagent_child",
  data: { subagent_id: id, inner_type: innerType, inner },
});

const approvalRequested = (id: string, level = "HIGH", kind = "tool"): LoopEvent => ({
  type: "approval_requested",
  data: { approval_request_id: id, risk_level: level, kind },
});

// Sprint 57.108: the tool-escalate frame shape — tool_name + reason on the wire.
const approvalRequestedWithContext = (
  id: string,
  toolName: string | null,
  reason: string,
): LoopEvent => ({
  type: "approval_requested",
  data: { approval_request_id: id, risk_level: "HIGH", kind: "tool", tool_name: toolName, reason },
});

const approvalReceived = (id: string, decision = "APPROVED"): LoopEvent => ({
  type: "approval_received",
  data: { approval_request_id: id, decision },
});

const guardrailTriggered = (): LoopEvent => ({
  type: "guardrail_triggered",
  data: { guardrail_type: "input", action: "block", reason: "PII detected" },
});

const loopStart = (sessionId: string): LoopEvent => ({
  type: "loop_start",
  data: { session_id: sessionId },
});

const spanStarted = (
  spanId: string,
  opts: { parent?: string; type?: string; name?: string } = {},
): LoopEvent => ({
  type: "span_started",
  data: {
    span_id: spanId,
    parent_span_id: opts.parent ?? "",
    span_type: opts.type ?? "LOOP",
    span_name: opts.name ?? "agent_loop",
  },
});

const spanEnded = (
  spanId: string,
  opts: { type?: string; name?: string; durationMs?: number } = {},
): LoopEvent => ({
  type: "span_ended",
  data: {
    span_id: spanId,
    span_type: opts.type ?? "LOOP",
    span_name: opts.name ?? "agent_loop",
    duration_ms: opts.durationMs ?? 1420,
  },
});

const memoryAccessed = (
  key: string,
  opts: { layer?: string; operation?: string; summary?: string; timeScale?: string } = {},
): LoopEvent => ({
  type: "memory_accessed",
  data: {
    layer: opts.layer ?? "user",
    operation: opts.operation ?? "read",
    key,
    summary: opts.summary ?? "5-whys + timeline",
    time_scale: opts.timeScale ?? "permanent",
  },
});

const agentHandoff = (
  newSessionId = "sess-child",
  targetAgent = "researcher",
  reason = "needs deep research",
): LoopEvent => ({
  type: "agent_handoff",
  data: {
    target_agent: targetAgent,
    reason,
    parent_session_id: "sess-parent",
    new_session_id: newSessionId,
  },
});

const messageInjected = (text: string): LoopEvent => ({
  type: "message_injected",
  data: { text },
});

// Sprint 57.130: a Cat-8 fatal terminate frame (reason + nullable detail/state).
const loopTerminated = (
  reason = "max_retries_exhausted",
  detail: string | null = "tool failed 3×",
): LoopEvent => ({
  type: "loop_terminated",
  data: { reason, detail, last_state_version: null },
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

  test("turn_start captures the frame trace_id + links the running TURN span (Sprint 57.108)", () => {
    useChatStore
      .getState()
      .mergeEvent(spanStarted("sp-turn-1", { type: "TURN", name: "agent_loop.turn" }));
    useChatStore.getState().mergeEvent({
      type: "turn_start",
      data: { turn_num: 1, trace_id: "tr-abc" },
    } as unknown as LoopEvent);
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.traceId).toBe("tr-abc");
    expect(t.spanId).toBe("sp-turn-1");
  });

  test("second turn links its own TURN span, not the first turn's (Sprint 57.108)", () => {
    useChatStore.getState().mergeEvent(spanStarted("sp-t1", { type: "TURN" }));
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(spanEnded("sp-t1", { type: "TURN", durationMs: 500 }));
    useChatStore.getState().mergeEvent(spanStarted("sp-t2", { type: "TURN" }));
    useChatStore.getState().mergeEvent(turnStart());
    const state = useChatStore.getState();
    const agentTurns = state.turns.filter((t) => t.role === "agent") as AgentTurn[];
    expect(agentTurns[0].spanId).toBe("sp-t1");
    expect(agentTurns[0].durationMs).toBe(500); // TURN span_ended filled it
    expect(agentTurns[1].spanId).toBe("sp-t2");
  });

  test("llm_response token actuals overwrite the llm_request estimate (Sprint 57.108)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(llmRequest(100));
    useChatStore
      .getState()
      .mergeEvent(llmResponse({ content: "hi", inputTokens: 1200, outputTokens: 345 }));
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.tokensIn).toBe(1200);
    expect(t.tokensOut).toBe(345);
  });

  test("llm_response without token actuals keeps prior values (old frames; Sprint 57.108)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(llmRequest(100));
    useChatStore.getState().mergeEvent(llmResponse({ content: "hi" }));
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.tokensIn).toBe(100); // llm_request estimate preserved
    expect(t.tokensOut).toBeNull();
  });

  test("message_injected appends a UserTurn tagged injected (Sprint 57.101 B1)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(messageInjected("also check the db pool"));
    const { turns } = useChatStore.getState();
    expect(turns).toHaveLength(2);
    const injected = turns[1];
    expect(injected.role).toBe("user");
    if (injected.role === "user") {
      expect(injected.text).toBe("also check the db pool");
      expect(injected.injected).toBe(true);
    }
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

  // --- loop_terminated (Sprint 57.130) ------------------------------------

  test("loop_terminated flips a dangling pending ToolBlock to error (stuck-chip fix)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    // a tool was requested but never got a result — the loop died mid-tool.
    useChatStore
      .getState()
      .mergeEvent(llmResponse({ toolCalls: [{ id: "tc-1", name: "metrics.query", arguments: {} }] }));
    expect((lastAgentTurn(useChatStore.getState().turns).blocks[0] as ToolBlock).status).toBe(
      "pending",
    );
    useChatStore.getState().mergeEvent(loopTerminated("max_retries_exhausted"));
    const tool = lastAgentTurn(useChatStore.getState().turns).blocks[0] as ToolBlock;
    expect(tool.status).toBe("error");
    expect(tool.isError).toBe(true);
    expect(tool.output).toContain("max_retries_exhausted");
  });

  test("loop_terminated records turn.terminated + sets status completed (composer unfreezes)", () => {
    useChatStore.getState().mergeEvent(loopStart("sess-x"));
    useChatStore.getState().mergeEvent(turnStart());
    expect(useChatStore.getState().status).toBe("running");
    useChatStore.getState().mergeEvent(loopTerminated("budget_exceeded", "token budget cap"));
    const state = useChatStore.getState();
    expect(state.status).toBe("completed");
    const t = lastAgentTurn(state.turns);
    expect(t.terminated).toEqual({ reason: "budget_exceeded", detail: "token budget cap" });
    expect(t.waiting).toBe(false);
  });

  test("loop_terminated with no pending tool records terminated + preserves rawEvents (no crash)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(llmResponse({ content: "partial answer" }));
    useChatStore.getState().mergeEvent(loopTerminated("circuit_open", null));
    const state = useChatStore.getState();
    const t = lastAgentTurn(state.turns);
    expect(t.terminated).toEqual({ reason: "circuit_open", detail: null });
    expect(t.blocks.some((b) => b.type === "tool")).toBe(false);
    expect(state.rawEvents.some((e) => e.type === "loop_terminated")).toBe(true);
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

  test("subagent_completed sets mode + tokensUsed on the fork block entry (Sprint 57.103 B2b)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(subSpawned("sa-tok", "teammate"));
    useChatStore.getState().mergeEvent(subCompleted("sa-tok"));
    const t = lastAgentTurn(useChatStore.getState().turns);
    const fork = t.blocks.find((b) => b.type === "subagent_fork") as SubagentForkBlock;
    expect(fork.agents[0].mode).toBe("teammate");
    expect(fork.agents[0].tokensUsed).toBe(42);
  });

  // --- subagent_child (Sprint 57.96 Scope B turn-stream) -----------------

  test("subagent_child appends a projected ChildTurnEvent to the matching node", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(subSpawned("sa-c1", "fork"));
    useChatStore.getState().mergeEvent(subChild("sa-c1", "turn_start", { turn_num: 1 }));
    useChatStore
      .getState()
      .mergeEvent(subChild("sa-c1", "llm_response", { content: "child says hi" }));
    useChatStore
      .getState()
      .mergeEvent(
        subChild("sa-c1", "tool_call_request", { tool_name: "echo", tool_call_id: "c1" }),
      );
    const node = useChatStore.getState().subagents.find((n) => n.subagentId === "sa-c1");
    expect(node?.childEvents).toHaveLength(3);
    expect(node?.childEvents[0]).toMatchObject({ kind: "turn_start", turn: 1 });
    expect(node?.childEvents[1]).toMatchObject({ kind: "llm_response", text: "child says hi" });
    expect(node?.childEvents[2]).toMatchObject({
      kind: "tool_call_request",
      toolName: "echo",
      toolCallId: "c1",
    });
  });

  test("subagent_child before its spawn defensive-creates the node", () => {
    useChatStore.getState().mergeEvent(subChild("sa-orphan", "llm_response", { content: "hi" }));
    const node = useChatStore.getState().subagents.find((n) => n.subagentId === "sa-orphan");
    expect(node).toBeDefined();
    expect(node?.childEvents).toHaveLength(1);
    expect(node?.childEvents[0]).toMatchObject({ kind: "llm_response", text: "hi" });
  });

  test("subagent_child message_injected projects text from inner.text (Sprint 57.103 B2b)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(subSpawned("sa-tm", "teammate"));
    useChatStore
      .getState()
      .mergeEvent(subChild("sa-tm", "message_injected", { text: "also check the db pool" }));
    const node = useChatStore.getState().subagents.find((n) => n.subagentId === "sa-tm");
    expect(node?.childEvents).toHaveLength(1);
    expect(node?.childEvents[0]).toMatchObject({
      kind: "message_injected",
      text: "also check the db pool",
    });
  });

  test("subagent_child guardrail_triggered projects action + reason (Sprint 57.110 B4)", () => {
    // A governed child's guardrail fire rides the relay: the event keeps the
    // guardrail's truthful action (escalate) while the child RUN fail-closes.
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(subSpawned("sa-gv", "fork"));
    useChatStore
      .getState()
      .mergeEvent(
        subChild("sa-gv", "guardrail_triggered", {
          guardrail_type: "input",
          action: "escalate",
          reason: "input matched escalation phrase: 'forbidden topic'",
        }),
      );
    const node = useChatStore.getState().subagents.find((n) => n.subagentId === "sa-gv");
    expect(node?.childEvents).toHaveLength(1);
    expect(node?.childEvents[0]).toMatchObject({
      kind: "guardrail_triggered",
      action: "escalate",
      text: "input matched escalation phrase: 'forbidden topic'",
    });
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

  test("approval_requested carries the pause kind onto the HITLTurn (Sprint 57.100)", () => {
    useChatStore.getState().mergeEvent(approvalRequested("ap-v", "HIGH", "verification"));
    const hitl = useChatStore.getState().turns.find((t) => t.role === "hitl") as HITLTurn;
    expect(hitl.kind).toBe("verification");
  });

  test("approval_requested with no kind on the wire falls back to '' (Sprint 57.100)", () => {
    useChatStore.getState().mergeEvent({
      type: "approval_requested",
      data: { approval_request_id: "ap-nok", risk_level: "HIGH" },
    } as unknown as LoopEvent);
    const hitl = useChatStore.getState().turns.find((t) => t.role === "hitl") as HITLTurn;
    expect(hitl.kind).toBe("");
  });

  test("approval_requested carries real tool context onto the HITLTurn (Sprint 57.108)", () => {
    useChatStore
      .getState()
      .mergeEvent(approvalRequestedWithContext("ap-t", "wire_transfer", "matched risky-action pattern"));
    const hitl = useChatStore.getState().turns.find((t) => t.role === "hitl") as HITLTurn;
    expect(hitl.tool).toBe("wire_transfer");
    expect(hitl.rationale).toBe("matched risky-action pattern");
  });

  test("approval_requested without tool context falls back to '—' (Sprint 57.108)", () => {
    useChatStore.getState().mergeEvent(approvalRequested("ap-old"));
    const hitl = useChatStore.getState().turns.find((t) => t.role === "hitl") as HITLTurn;
    expect(hitl.tool).toBe("—");
    expect(hitl.rationale).toBe("—");
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

  // --- Sprint 57.75 A-5: spans slice (Trace) ----------------------------

  test("span_started opens a SpanNode (status=running, durationMs=null)", () => {
    useChatStore.getState().mergeEvent(spanStarted("sp-loop", { type: "LOOP", name: "agent_loop" }));
    const { spans } = useChatStore.getState();
    expect(spans).toHaveLength(1);
    expect(spans[0].spanId).toBe("sp-loop");
    expect(spans[0].spanType).toBe("LOOP");
    expect(spans[0].status).toBe("running");
    expect(spans[0].durationMs).toBeNull();
  });

  test("span_started dedups by span_id (re-emit keeps first open record)", () => {
    useChatStore.getState().mergeEvent(spanStarted("sp-loop"));
    useChatStore.getState().mergeEvent(spanStarted("sp-loop"));
    expect(useChatStore.getState().spans).toHaveLength(1);
  });

  test("span_ended closes matching span (durationMs set + status=done)", () => {
    useChatStore.getState().mergeEvent(spanStarted("sp-loop", { type: "LOOP" }));
    useChatStore.getState().mergeEvent(spanEnded("sp-loop", { durationMs: 910 }));
    const { spans } = useChatStore.getState();
    expect(spans).toHaveLength(1);
    expect(spans[0].status).toBe("done");
    expect(spans[0].durationMs).toBe(910);
  });

  test("span_ended without prior span_started defensively creates a closed span", () => {
    useChatStore.getState().mergeEvent(spanEnded("sp-orphan", { durationMs: 42 }));
    const { spans } = useChatStore.getState();
    expect(spans).toHaveLength(1);
    expect(spans[0].status).toBe("done");
    expect(spans[0].durationMs).toBe(42);
    expect(spans[0].parentSpanId).toBe("");
  });

  test("span_ended TURN fills the matching AgentTurn.durationMs (Sprint 57.108 — no turn_end event)", () => {
    useChatStore.getState().mergeEvent(spanStarted("sp-turn", { type: "TURN" }));
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(spanEnded("sp-turn", { type: "TURN", durationMs: 1234 }));
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.durationMs).toBe(1234);
  });

  test("span_ended non-TURN does not touch AgentTurn.durationMs (Sprint 57.108)", () => {
    useChatStore.getState().mergeEvent(spanStarted("sp-llm", { type: "LLM_CALL" }));
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(spanEnded("sp-llm", { type: "LLM_CALL", durationMs: 77 }));
    const t = lastAgentTurn(useChatStore.getState().turns);
    expect(t.durationMs).toBeNull();
  });

  test("nested spans preserve parent_span_id linkage (LOOP → TURN → LLM_CALL)", () => {
    useChatStore.getState().mergeEvent(spanStarted("loop", { type: "LOOP" }));
    useChatStore.getState().mergeEvent(spanStarted("turn", { parent: "loop", type: "TURN" }));
    useChatStore
      .getState()
      .mergeEvent(spanStarted("llm", { parent: "turn", type: "LLM_CALL" }));
    const byId = new Map(useChatStore.getState().spans.map((s) => [s.spanId, s]));
    expect(byId.get("turn")?.parentSpanId).toBe("loop");
    expect(byId.get("llm")?.parentSpanId).toBe("turn");
  });

  // --- Sprint 57.75 A-5: memoryOps slice (Memory) ------------------------

  test("memory_accessed appends a MemoryOp with scope/timeScale/key/summary + client at", () => {
    const before = Date.now();
    useChatStore
      .getState()
      .mergeEvent(
        memoryAccessed("preferences.rca_format", {
          layer: "user",
          operation: "read",
          summary: "5-whys + timeline",
          timeScale: "permanent",
        }),
      );
    const { memoryOps } = useChatStore.getState();
    expect(memoryOps).toHaveLength(1);
    expect(memoryOps[0].op).toBe("read");
    expect(memoryOps[0].scope).toBe("user");
    expect(memoryOps[0].timeScale).toBe("permanent");
    expect(memoryOps[0].key).toBe("preferences.rca_format");
    expect(memoryOps[0].summary).toBe("5-whys + timeline");
    expect(memoryOps[0].at).toBeGreaterThanOrEqual(before);
  });

  test("multiple memory_accessed accumulate in arrival order", () => {
    useChatStore.getState().mergeEvent(memoryAccessed("k1", { layer: "user" }));
    useChatStore.getState().mergeEvent(memoryAccessed("k2", { layer: "tenant" }));
    const { memoryOps } = useChatStore.getState();
    expect(memoryOps.map((m) => m.key)).toEqual(["k1", "k2"]);
    expect(memoryOps.map((m) => m.scope)).toEqual(["user", "tenant"]);
  });

  test("span + memory events still record rawEvents (audit trail)", () => {
    useChatStore.getState().mergeEvent(spanStarted("sp-1"));
    useChatStore.getState().mergeEvent(memoryAccessed("k1"));
    expect(useChatStore.getState().rawEvents).toHaveLength(2);
  });

  test("agent_handoff pivot resets spans + memoryOps to empty child", () => {
    useChatStore.getState().mergeEvent(spanStarted("sp-1"));
    useChatStore.getState().mergeEvent(memoryAccessed("k1"));
    expect(useChatStore.getState().spans).toHaveLength(1);
    useChatStore.getState().mergeEvent(agentHandoff());
    const state = useChatStore.getState();
    expect(state.spans).toEqual([]);
    expect(state.memoryOps).toEqual([]);
  });

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

// === Sprint 57.69 A-3b slice 2 — HANDOFF session-pivot + banner =============

const sessionFixture = (id: string): Session => ({
  id,
  title: `Session ${id}`,
  agent: "incident_responder",
  turns: 3,
  status: "done",
  time: "10:00",
  // Sprint 57.107 B3: Session shape change (dropped domain; +handoffParentId/agentRole).
  handoffParentId: null,
  agentRole: "incident_responder",
});

describe("chatStore HANDOFF pivot + banner (Sprint 57.69)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("agent_handoff pivots: sessionId + activeSessionId = new_session_id", () => {
    // Build up some parent-session state first.
    useChatStore.getState().mergeEvent(loopStart("sess-parent"));
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(loopEnd("handoff", 1));

    useChatStore.getState().mergeEvent(agentHandoff("sess-child", "researcher", "go deep"));
    const state = useChatStore.getState();
    expect(state.sessionId).toBe("sess-child");
    expect(state.activeSessionId).toBe("sess-child");
  });

  test("agent_handoff resets turns + conversation slices to the empty child", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().mergeEvent(approvalRequested("ap-h", "HIGH"));
    expect(useChatStore.getState().turns.length).toBeGreaterThan(0);

    useChatStore.getState().mergeEvent(agentHandoff());
    const state = useChatStore.getState();
    expect(state.turns).toEqual([]);
    expect(state.status).toBe("idle");
    expect(state.totalTurns).toBe(0);
    expect(state.stopReason).toBeNull();
    expect(state.errorMessage).toBeNull();
    expect(state.approvals).toEqual({});
    expect(state.verifications).toEqual([]);
    expect(state.subagents).toEqual([]);
  });

  test("agent_handoff sets handoffBanner to {targetAgent, reason}", () => {
    useChatStore
      .getState()
      .mergeEvent(agentHandoff("sess-child", "reviewer", "policy review needed"));
    expect(useChatStore.getState().handoffBanner).toEqual({
      targetAgent: "reviewer",
      reason: "policy review needed",
    });
  });

  test("agent_handoff still records the rawEvent (audit trail preserved)", () => {
    useChatStore.getState().mergeEvent(turnStart()); // rawEvents[0]
    useChatStore.getState().mergeEvent(agentHandoff()); // rawEvents[1]
    const { rawEvents } = useChatStore.getState();
    expect(rawEvents).toHaveLength(2);
    expect(rawEvents[1].type).toBe("agent_handoff");
  });

  test("agent_handoff preserves the sessions sidebar list", () => {
    useChatStore.getState().setSessions([sessionFixture("a"), sessionFixture("b")]);
    useChatStore.getState().mergeEvent(agentHandoff());
    const { sessions } = useChatStore.getState();
    expect(sessions.map((s) => s.id)).toEqual(["a", "b"]);
  });

  test("loop_start clears the handoffBanner (continuing in the child dismisses it)", () => {
    useChatStore.getState().mergeEvent(agentHandoff());
    expect(useChatStore.getState().handoffBanner).not.toBeNull();
    useChatStore.getState().mergeEvent(loopStart("sess-child"));
    expect(useChatStore.getState().handoffBanner).toBeNull();
  });

  test("dismissHandoffBanner clears the banner", () => {
    useChatStore.getState().mergeEvent(agentHandoff());
    expect(useChatStore.getState().handoffBanner).not.toBeNull();
    useChatStore.getState().dismissHandoffBanner();
    expect(useChatStore.getState().handoffBanner).toBeNull();
  });

  test("pivotSession action pivots + sets banner directly (no event)", () => {
    useChatStore.getState().mergeEvent(turnStart());
    useChatStore.getState().setSessions([sessionFixture("keep")]);
    useChatStore
      .getState()
      .pivotSession("sess-direct", { targetAgent: "planner", reason: "decompose plan" });
    const state = useChatStore.getState();
    expect(state.sessionId).toBe("sess-direct");
    expect(state.activeSessionId).toBe("sess-direct");
    expect(state.turns).toEqual([]);
    expect(state.handoffBanner).toEqual({ targetAgent: "planner", reason: "decompose plan" });
    expect(state.sessions.map((s) => s.id)).toEqual(["keep"]); // preserved
  });
});
