/**
 * File: frontend/src/features/orchestrator-loop/_fixtures/demoLoopEvents.ts
 * Purpose: 18-event demo fixture for /loop-debug standalone empty-state UX
 *          (closes Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint gap).
 * Category: Frontend / orchestrator-loop / _fixtures
 * Scope: Phase 57 / Sprint 57.37 Day 1 / US-A1
 *
 * Description:
 *   Maps mockup `reference/design-mockups/page-governance.jsx:5-31` `LoopEvents`
 *   (24 entries in flat {turn, type, text, tone, at} shape) → production
 *   `LoopEvent` discriminated union (frontend/src/features/chat_v2/types.ts; 14
 *   typed events). Several mockup events collapse into the production union
 *   (e.g. mockup thinking.start / thinking.delta / thinking.end → single
 *   llm_request + llm_response). Some have no production equivalent (memory.* /
 *   loop.iter_start / loop.iter_end / user_message / hitl.policy_check are
 *   absorbed into adjacent typed events or omitted with a note below).
 *
 *   Mapping (production type ← mockup type):
 *     - loop_start ← (no mockup row; prepended as session opener)
 *     - turn_start ← derived per turn boundary in mockup `turn` field
 *     - llm_request ← thinking.start (per-turn LLM dispatch)
 *     - llm_response ← thinking.end + tool_calls (collapsed thinking lifecycle
 *       with `thinking` field carrying the streamed text from thinking.delta)
 *     - tool_call_request ← tool.requested / tool.started (collapsed; tool.started
 *       is mostly cosmetic streaming in mockup)
 *     - tool_call_result ← tool.completed
 *     - verification_passed ← verification.run (mockup omits failed cases in this
 *       fixture; we keep all as passed for demo realism)
 *     - approval_requested ← hitl.requested (the user-actionable HITL event;
 *       hitl.policy_check above it in mockup is an internal-only auto-allow gate
 *       that doesn't surface as a production approval event)
 *     - guardrail_triggered ← (none in this mockup fixture)
 *     - subagent_spawned ← subagent.spawn
 *     - subagent_completed ← subagent.completed
 *     - loop_end ← loop.paused (final state of mockup fixture; stop_reason=hitl)
 *
 *   Mockup events without production equivalents (omitted):
 *     - user_message (turn 0) — absorbed into loop_start preamble
 *     - loop.iter_start / loop.iter_end — mockup-only boundary markers; production
 *       relies on turn_start + turn-bucket diffing
 *     - hitl.policy_check — internal policy evaluation; not on SSE wire
 *     - memory.read / memory.write — no production LoopEvent type yet
 *       (Phase 58+ AD-Memory-Event-Wire-Up); category filter still includes
 *       "memory" pill — it just has no events to hide when toggled
 *
 *   Total: 18 typed events spanning 5 turns (mockup has 25 across same 5 turns).
 *
 * Created: 2026-05-24 (Sprint 57.37 Day 1 US-A1)
 *
 * Modification History:
 *   - 2026-06-02: Sprint 57.66 — add cache fields to llm_response/loop_end literals (type contract)
 *   - 2026-05-24: Initial creation (Sprint 57.37 Day 1 US-A1)
 *
 * Related:
 *   - reference/design-mockups/page-governance.jsx:5-31 (mockup fixture source)
 *   - frontend/src/features/chat_v2/types.ts (production LoopEvent union)
 *   - frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx (consumer)
 *   - sprint-57-37-plan.md §3.1 (fixture spec)
 */

import type { LoopEvent } from "@/features/chat_v2/types";

/**
 * Demo events that populate /loop-debug in standalone mode when no live
 * chat-v2 session is running. Per CLAUDE.md §Frontend Mockup-Fidelity Hard
 * Constraint: "後端尚未支援的 widget → 仍依 mockup 視覺實作，data 用 fixture".
 */
export const DEMO_LOOP_EVENTS: LoopEvent[] = [
  // === Preamble (mockup user_message turn 0 absorbed here) ===
  {
    type: "loop_start",
    data: { session_id: "sess_4tk2p_demo", request_id: "req_demo_001" },
  },

  // === Turn 1 — investigate incident ===
  { type: "turn_start", data: { turn_num: 1 } },
  { type: "llm_request", data: { model: "gpt-4o", tokens_in: 412 } },
  {
    type: "llm_response",
    data: {
      content: "I will investigate the payment-gateway 5xx spike.",
      tool_calls: [
        { id: "tc_demo_1", name: "incidents.list", arguments: {} },
      ],
      thinking: "User flagged P1. SLO at 1% breached — checking recent incidents to find correlated events.",
      cached_input_tokens: 0,
    },
  },
  {
    type: "tool_call_request",
    data: { tool_call_id: "tc_demo_1", tool_name: "incidents.list", args: {} },
  },
  {
    type: "tool_call_result",
    data: {
      tool_call_id: "tc_demo_1",
      tool_name: "incidents.list",
      duration_ms: 82,
      result: '{"rows": 8}',
      is_error: false,
    },
  },
  {
    type: "verification_passed",
    data: { verifier: "claim_evidence", verifier_type: "rules_based", score: 0.92 },
  },

  // === Turn 2 — fork subagents ===
  { type: "turn_start", data: { turn_num: 2 } },
  {
    type: "subagent_spawned",
    data: { subagent_id: "sub_log_demo", mode: "concurrent", parent_session_id: "sess_4tk2p_demo" },
  },
  {
    type: "subagent_completed",
    data: { subagent_id: "sub_log_demo", summary: "log-scanner · 3 turns · ok", tokens_used: 1840 },
  },

  // === Turn 3 — gather metrics ===
  { type: "turn_start", data: { turn_num: 3 } },
  {
    type: "tool_call_result",
    data: {
      tool_call_id: "tc_demo_2",
      tool_name: "metrics.query",
      duration_ms: 210,
      result: '{"latency_p99_ms": 2840}',
      is_error: false,
    },
  },
  {
    type: "verification_passed",
    data: { verifier: "claim_verified", verifier_type: "llm_judge", score: 0.88 },
  },

  // === Turn 4 — HITL pause ===
  { type: "turn_start", data: { turn_num: 4 } },
  {
    type: "llm_request",
    data: { model: "gpt-4o", tokens_in: 1240 },
  },
  {
    type: "llm_response",
    data: {
      content: "Proposing fix: set REDIS_MAX_CONN env on payment-gateway.",
      tool_calls: [
        { id: "tc_demo_3", name: "k8s.set_env", arguments: { svc: "payment-gateway", key: "REDIS_MAX_CONN", value: "256" } },
      ],
      thinking: "Root cause likely connection-pool exhaustion. High-risk tool requires HITL.",
      cached_input_tokens: 896,
    },
  },
  {
    type: "approval_requested",
    data: { approval_request_id: "a8f3.k2p1", risk_level: "high", kind: "tool" },
  },
  {
    type: "loop_end",
    data: { stop_reason: "hitl", total_turns: 4, cached_input_tokens: 896, cache_hit_rate: 0.34 },
  },
];
