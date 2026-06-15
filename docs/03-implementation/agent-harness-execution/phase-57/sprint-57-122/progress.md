# Sprint 57.122 Progress — HITL policy read-side load-bearing

**Slice**: `AD-HITL-Policy-ReadSide-Potemkin-Phase58` (flagship 載重 gap). Make the per-tenant `HITLPolicy` thresholds load-bearing at tool execution.
**Branch**: `feature/sprint-57-122-hitl-policy-readside` (from `main` `f57135ef`).
**Plan / Checklist**: [`sprint-57-122-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-122-plan.md) · [`sprint-57-122-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-122-checklist.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

**Branch**: `git checkout -b feature/sprint-57-122-hitl-policy-readside` from `f57135ef` ✅

### Prong 1 — path verify ✅
All target files present: `_contracts/hitl.py` · `orchestrator_loop/loop.py` · `guardrails/tool/tool_guardrail.py` · `platform_layer/governance/hitl/manager.py` · `.../hitl/policy_store.py` · `platform_layer/governance/service_factory.py`. `CHANGE-089` free; design-note `35-*` free. Test homes located: unit `tests/unit/agent_harness/guardrails/test_tool_guardrail.py` + `test_capability_matrix.py`; integration `tests/integration/agent_harness/governance/test_hitl_centralization.py`.

### Prong 2 — content verify (drift findings)
- **D-manager-wired** ✅ (CRUX confirmed, NO scope change): `service_factory.py:124` builds `DBHITLPolicyStore`; `:134-137` `DefaultHITLManager(..., policy_store=self.get_hitl_policy_store())`. The loop's `hitl_manager` is the factory instance (`handler.py:267/705/768`). → `get_policy(tenant_id)` reads the real DB policy. The crux read-side wiring is ALREADY done — the gap is purely that the loop never CALLS it.
- **D-getpolicy-shape** ✅: `manager.py:271-296` `get_policy(tenant_id, *, trace_context=None) -> HITLPolicy` — resolution DB→default_policy→hardcoded LOW/MEDIUM. It does **NOT** catch a store exception (`await self._policy_store.get(...)` unguarded) → **the loop call MUST try/except fail-open** to a conservative default.
- **D-risklevel-order** ✅: `_contracts/hitl.py:37-43` `RiskLevel(Enum)` is a plain `str Enum`, NOT orderable → a `RISK_ORDER` map + `risk_ge`/`risk_le` helpers are required (cannot compare enums directly).
- **D-toolspec-risk** ✅: `_contracts/tools.py:95` `ToolSpec.risk_level: RiskLevel = RiskLevel.LOW` — always-set (NOT Optional), single-source from `_contracts.hitl`. The loop holds `self._tool_registry` (`loop.py:452`); `ToolRegistryImpl.get(name) -> ToolSpec | None` (`tools/registry.py:66`) → resolve risk via `self._tool_registry.get(tc.name).risk_level`, default LOW for a spec-not-found.
- **D-cat9-anchors** ✅: `_cat9_tool_check` (`loop.py:859-941`) — `guardrail_engine.check_tool_call`; on `action != PASS`: `ESCALATE + hitl_manager → _cat9_hitl_branch; else → soft-block GuardrailTriggered`. `_cat9_hitl_branch` (`:943-1023`) hardcodes `RiskLevel.HIGH` at `:1007`. `tenant_id = self._tenant_id or ctx.tenant_id` (`:987`). `GuardrailAction` = PASS/BLOCK/ESCALATE/SANITIZE/REROLL (`guardrails/_abc.py:47-54`). The `_cat9_hitl_branch` docstring (`:975-978`) explicitly flags this gap: "Risk level defaults to HIGH ... Future sprints may pull from RiskPolicy via a callable injected at ctor time."

### 🆕 NEW drift findings (scope CLARIFICATION — net reduction, not expansion)
- **D-6-hardcoded-HIGH** 🆕: there are **SIX** hardcoded `RiskLevel.HIGH  # ESCALATE default` sites in `loop.py` — `:786` (`_cat9_input_hitl_pause`), `:1007` (`_cat9_hitl_branch` = TOOL), `:1410` (between-turns), `:1575` / `:1818` (output pauses). **Scope boundary**: only the **TOOL path (`:1007`)** is in scope (the carryover is specifically about `ToolGuardrail` Stage 3 `requires_approval`). The input / output / between-turns escalations are **content-guardrail** escalations (jailbreak / PII / unsafe output) where the tenant risk-thresholds should NOT apply — a tenant must not be able to auto-approve a jailbreak. Keeping those hardcoded-escalate is **correct** for safety. ⇒ scope confirmed to the tool path; NO creep.
- **D-permission-checker** 🆕: `ToolSpec.hitl_policy` (AUTO/ASK_ONCE/ALWAYS_ASK, `tools.py:94`) + a `PermissionChecker` (Sprint 51.1, "consumes hitl_policy + risk_level") exist as a **parallel** HITL abstraction, but are **NOT wired into the loop** (the loop `__init__` has no PermissionChecker; the live tool-gating path is `guardrail_engine.check_tool_call` → `ToolGuardrail` Stage 3 → the capability-matrix `requires_approval` bool). ⇒ this sprint fixes the **LIVE** guardrail→loop path (per the user's "ToolSpec.risk_level" decision); PermissionChecker / `hitl_policy` is a dormant parallel abstraction (out of scope; flag as a possible separate Potemkin for a future audit — NOT this slice).
- **D-test-homes** ✅: unit (pure functions, no `_contracts` test dir exists) → `tests/unit/agent_harness/guardrails/test_hitl_decision.py` (co-located with the Cat 9 guardrail tests); integration (loop policy path + multi-tenant) → `tests/integration/agent_harness/governance/test_loop_hitl_policy.py` (NEW, alongside `test_hitl_centralization.py`).

### Prong 3 — schema ✅ (confirm-only, NO new table/migration)
`hitl_policies` table (migration 0013) exists with columns mirroring `HITLPolicy` (per the Sprint 55.3 D6 correction). This sprint adds NO table / migration / ORM change.

### Baselines (cited from 57.121 closeout; re-verify at gate)
pytest **2648+5skip** · wire **24** · Vitest **888** · mockup **51** · mypy `src` **0/371** · run_all **10/10**. Backend-only sprint (Vitest/mockup unchanged by definition — no FE).

### Go/no-go → 🟢 **GO**
Scope **confirmed + slightly reduced** (tool path only; PermissionChecker + the 5 content-guardrail HIGH sites explicitly OUT). The crux wiring (manager↔DB store) is pre-done → the sprint is a contained loop decision + a pure contract + tests + drive-through. No >20% shift.

**Final design** (locked):
- `_contracts/hitl.py` += `RISK_ORDER` + `risk_ge`/`risk_le` + `decide_tool_hitl(risk, policy, *, rule_requires_approval) -> bool` (escalate-first: `risk ≥ require_approval_min_risk → True`; then `risk ≤ auto_approve_max_risk → False`; else `rule_requires_approval`) + `resolve_tool_risk(spec_risk, *, rule_requires_approval) -> RiskLevel` (spec_risk else MEDIUM-if-flagged-else-LOW).
- `loop.py`: `_cat9_tool_check` restructured — BLOCK/SANITIZE/REROLL soft-block (unchanged); PASS/ESCALATE → resolve risk (`_tool_registry.get(tc.name).risk_level`) + policy (cached, fail-open) → `decide_tool_hitl` → escalate (`_cat9_hitl_branch(..., risk=R)`) or fall-through (auto-approve/pass). ESCALATE-without-manager preserves the pre-57.122 fail-closed soft-block. `_cat9_hitl_branch` takes `risk` → `ApprovalRequest.risk_level` (drop hardcoded HIGH).

---

## Day 1 — Pure decision contract (US-1) ✅

- **`_contracts/hitl.py`** += `RISK_ORDER` + `risk_ge`/`risk_le` + `resolve_tool_risk` + `decide_tool_hitl` (pure, no DB). MHist + Last Modified.
- **Key semantic refinement** (caught BEFORE running — a real safety call): `ToolSpec.risk_level` defaults LOW, so a flagged tool (`requires_approval=True`) with the default LOW spec would have AUTO-APPROVED under the DEFAULT policy = a SILENT safety relaxation for default-policy tenants. Fix: the per-rule flag is a **MEDIUM risk floor** in `resolve_tool_risk` (`max(base, MEDIUM)` when flagged) → flagged tools still escalate under DEFAULT (backward-compatible), while a permissive tenant (auto≥MEDIUM) can still auto-approve (load-bearing). Aligned with the user's 企業安全剛需 motivation (tighter, not looser). Documented in the docstring + (Day 4) design note 35.
- **`tests/.../guardrails/test_hitl_decision.py`** (NEW): table-driven across risk × {DEFAULT, PERMISSIVE, STRICT, WIDE-grayband, OVERLAP-misconfigured} × flag + `resolve_tool_risk` (floor cases) + `RISK_ORDER` + backward-compat guard (flagged-LOW still escalates) + load-bearing proof (permissive auto-approves flagged). **38 passed**.

## Day 2 — Loop integration (US-2/US-3) + integration/multi-tenant tests (US-4) ✅

- **`loop.py`** (EDIT): `+self._hitl_policy_cache` + `_resolve_hitl_policy(ctx)` (read `get_policy(tenant_id)`, **try/except fail-open** to DEFAULT — `get_policy` does NOT catch store errors; cached per run) + `_resolve_tool_call_risk(tool_name, flagged)` (reads `self._tool_registry.get(name).risk_level`). `_cat9_tool_check` restructured: BLOCK/SANITIZE/REROLL soft-block (unchanged); PASS/ESCALATE → resolve risk + policy → `decide_tool_hitl` → escalate (`_cat9_hitl_branch(..., risk=R)`) or fall-through (auto-approve/pass); ESCALATE-without-manager preserves the pre-57.122 fail-closed soft-block. `_cat9_hitl_branch` += `risk` param → `ApprovalRequest.risk_level` (hardcoded `RiskLevel.HIGH` dropped). MHist + Last Modified.
- **Scope held**: only the TOOL path (`:1007`) touched; the 5 content-guardrail HIGH sites (input/output/between-turns) intentionally UNCHANGED (per D-6-hardcoded-HIGH — a tenant must not auto-approve a jailbreak).
- **`tests/integration/.../governance/test_loop_hitl_policy.py`** (NEW): drives `_cat9_tool_check` with configurable (guardrail action, ToolSpec.risk_level, HITLPolicy); proves escalate-by-flag / auto-approve-override / escalate-by-threshold (new high-risk-unflagged trigger) / gray-band / **same flagged tool → different decision per tenant** (load-bearing) / resolved-risk-on-ApprovalRequest / policy-resolved-once-cached. **9 passed**.
- **Regression fixed (1)** — `test_stage3_escalation_e2e.py::test_stage3_approved_tool_runs_normally` asserted the pre-57.122 hardcoded `RiskLevel.HIGH`; the flagged LOW-spec tool now resolves to MEDIUM (floor) → updated the assertion to `RiskLevel.MEDIUM` + comment + MHist (the escalate→approve→run flow is UNCHANGED; only the risk VALUE on the ApprovalRequest is now policy-resolved). This is the intended behavior change, NOT a bug. **7 passed** after fix.
- **Gate sweep**: mypy `src` **0/371** (unchanged — new functions in existing files) · `run_all.py` **10/10 green** · black/isort/flake8 clean · full pytest **2695 passed / 5 skip** (2648 baseline + 38 + 9; 1 stale assertion updated). Vitest/mockup untouched (backend-only). `tool_guardrail.py` / `capability_matrix.py` / `service_factory.py` / `manager.py` / `policy_store.py` / migrations / events / sse / codegen / frontend UNTOUCHED.

## Day 3 — Drive-through (US-5) — real chat-v2 + real backend + real LLM ✅ PASS

**Clean restart (Risk Class E — `.py` changed)**: `dev.py restart backend` → fresh PID **42820** (worker 6824); `Win32_Process` PID/PPID/StartTime sweep confirmed both created 7:32 PM today, no stale spawn-worker orphan → backend serves the NEW loop code. (A prior-session background "start backend" task failed exit 255 = port-in-use, no orphan.)

**Setup**: dev-login `dan@acme.com` / **admin** / acme-prod (`tenant_id=09eb1b62-9fd3-439a-8229-1c923cc667e9`; admin lets the SAME session both PUT the policy + drive chat). Baseline: `GET .../hitl-policies` → `items:[]` (no row → DEFAULT auto=LOW/require=MEDIUM). Real LLM = `gpt-5.2`.

**The proof — SAME tool call, different per-tenant policy → different runtime HITL outcome (load-bearing):**

| Leg | Policy (admin PUT) | Tool call | Trace outcome |
|-----|--------------------|-----------|---------------|
| **A** | DEFAULT (auto=LOW/require=MEDIUM) | `echo_tool` | `approval_requested risk=MEDIUM` → `awaiting_approval` (**escalate**) |
| **B** | PERMISSIVE (auto=HIGH/require=CRITICAL) | `python_sandbox` print(6*7) | `tool_call_request` → **`TOOL_EXEC` span (executed, 16ms)**, NO approval_requested (**auto-approve**) |
| **C** | STRICT (auto=LOW/require=LOW) | `python_sandbox` print(6*7) — **identical to B** | `approval_requested risk=MEDIUM` → `awaiting_approval` (**escalate**) |

- **Leg B vs Leg C = the decisive delta**: the IDENTICAL `python_sandbox(print(6*7))` call **auto-approves** under the permissive policy but **escalates** under the strict policy — the runtime read the per-tenant DB policy (set via admin PUT) and the HITL decision flipped. This is the load-bearing gap closed, proven LIVE (NOT gate-only).
- **`risk=MEDIUM`** on every escalation (not the pre-57.122 hardcoded `RiskLevel.HIGH`) — direct live proof the `ApprovalRequest` now carries the policy-resolved risk (US-3).
- **LLM-determinism note (honest)**: `gpt-5.2` would NOT reliably call the trivial `echo_tool` (it answered the echo directly in 4/5 fresh sessions — Legs B/C-with-echo were `0 tool calls` confounds). `python_sandbox` (the model cannot run Python itself) was the reliable deterministic trigger → used for the B/C contrast. Leg A captured the one echo_tool escalation. The confound was the LLM's tool-calling choice, NOT the harness.
- **Screenshots**: `sprint-57-122-legA-default-policy-escalates.png` · `sprint-57-122-legB-permissive-autoapprove.png` · `sprint-57-122-legC-strict-policy-escalates.png`. **AP-4 clear** — real tool calls, real per-tenant policy read, real outcome flip.
- **Hygiene**: restored acme-prod policy to default-equivalent (auto=LOW/require=MEDIUM) after the drive-through.

## Day 4 — Design note 35 + CHANGE-089 + closeout

(in progress)
