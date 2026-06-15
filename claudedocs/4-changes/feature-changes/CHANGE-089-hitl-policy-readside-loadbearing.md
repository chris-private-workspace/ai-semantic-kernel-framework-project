# CHANGE-089: HITL policy read-side load-bearing (per-tenant risk thresholds decide tool HITL)

**Date**: 2026-06-15
**Sprint**: 57.122
**Scope**: 範疇 9 (Guardrails / HITL) × 範疇 1 (Orchestrator Loop) — backend only
**Slice**: `AD-HITL-Policy-ReadSide-Potemkin-Phase58`

## Problem

The per-tenant `HITLPolicy` risk thresholds (`auto_approve_max_risk` / `require_approval_min_risk`) had a full write-side — DB store + admin GET/PUT — but were NEVER read at tool execution. The loop's Cat 9 tool path hardcoded `if rule.requires_approval: ESCALATE` (`tool_guardrail.py:151-160`) + a flat `RiskLevel.HIGH` for every escalation (`loop.py:1007`). Every tenant got the identical decision regardless of their stored thresholds — a flagship 載重 gap (load-bearing-empty: write齊全, execution零承重).

## Root Cause

The thresholds talk in `RiskLevel`, but the runtime never resolved a tool call's risk nor consulted `hitl_manager.get_policy(tenant_id)` (which the production manager IS wired to read from the DB — `service_factory.py:124/134-137`). The `_cat9_hitl_branch` docstring even flagged it: "Risk level defaults to HIGH … Future sprints may pull from RiskPolicy."

## Solution

Pure two-threshold decision in the contract layer + a loop integration (PR — pure backend, NO migration / wire / codegen / frontend):

- **`backend/src/agent_harness/_contracts/hitl.py`** — added `RISK_ORDER` + `risk_ge`/`risk_le` (RiskLevel is a non-orderable str Enum) + `resolve_tool_risk(spec_risk, *, rule_requires_approval)` (ToolSpec.risk_level; flagged → MEDIUM floor) + `decide_tool_hitl(risk, policy, *, rule_requires_approval) -> bool` (escalate-first: `risk ≥ require_min → escalate`; `risk ≤ auto_max → auto-approve`; gray band → per-rule bool).
- **`backend/src/agent_harness/orchestrator_loop/loop.py`** — `_resolve_hitl_policy(ctx)` (reads `get_policy`, try/except fail-open to DEFAULT, cached per run) + `_resolve_tool_call_risk(tool_name, flagged)` (via `self._tool_registry.get`); `_cat9_tool_check` restructured to apply `decide_tool_hitl` to PASS/ESCALATE (BLOCK/SANITIZE short-circuit; ESCALATE-without-manager keeps fail-closed); `_cat9_hitl_branch` takes `risk` → `ApprovalRequest.risk_level` (hardcoded HIGH dropped).
- Scope held to the **tool path**; the 5 content-guardrail HIGH sites (input/output/between-turns) are intentionally unchanged (a tenant must not auto-approve a jailbreak).

**Decisions** (user, 2026-06-15, via AskUserQuestion): two-thresholds-both-load-bearing + risk from `ToolSpec.risk_level` (no schema change). Implementation refinement: the per-rule flag is a MEDIUM risk floor → no silent safety relaxation for default-policy tenants. Full semantics: design note `35-hitl-risk-threshold-semantics.md`.

## Verification

- `pytest backend/tests/unit/agent_harness/guardrails/test_hitl_decision.py -q` → **38 passed** (table-driven risk × policy × flag + floor + backward-compat + load-bearing).
- `pytest backend/tests/integration/agent_harness/governance/test_loop_hitl_policy.py -q` → **9 passed** (loop path + multi-tenant same-tool-different-decision + resolved-risk + cached-once).
- Updated 1 stale assertion: `test_stage3_escalation_e2e.py::test_stage3_approved_tool_runs_normally` asserted the pre-57.122 hardcoded HIGH; the flagged LOW-spec tool now resolves to MEDIUM (floor) → assertion HIGH→MEDIUM (the escalate→approve→run flow is unchanged).
- Gate: mypy `src` **0/371** · `run_all.py` **10/10** · black/isort/flake8 clean · full pytest **2695 passed / 5 skip**.
- **Drive-through (real chat-v2 + real backend + gpt-5.2)**: the IDENTICAL `python_sandbox(print(6*7))` call **auto-approved** (`TOOL_EXEC`) under a permissive policy but **escalated** (`approval_requested risk=MEDIUM` → `awaiting_approval`) under a strict policy set via admin PUT — the runtime read the per-tenant DB policy → the SAME tool routes differently. NOT gate-only. 3 screenshots in `sprint-57-122/artifacts/`. (LLM-determinism note: gpt-5.2 wouldn't reliably call the trivial `echo_tool`; `python_sandbox` was the deterministic trigger.)

## Impact

Backend only. The per-tenant HITL risk thresholds are now load-bearing at tool execution; escalations carry the policy-resolved risk (reviewer routing + SLA become correct). No migration / wire / codegen / frontend. Backward-compatible: default-policy tenants see no change (the MEDIUM floor keeps flagged tools escalating). Spun off `AD-HITL-Policy-Threshold-Validation` (admin-PUT should validate `auto < require`).
