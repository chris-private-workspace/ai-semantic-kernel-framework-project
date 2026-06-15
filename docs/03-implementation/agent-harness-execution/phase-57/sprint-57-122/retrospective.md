# Sprint 57.122 Retrospective — HITL policy read-side load-bearing

**Slice**: `AD-HITL-Policy-ReadSide-Potemkin-Phase58` (flagship 載重 gap). **Closed** 2026-06-15.
**Branch**: `feature/sprint-57-122-hitl-policy-readside` (from `main` `f57135ef`).

## Q1 — What shipped

The agent loop's Cat 9 tool path became policy-aware: it reads `hitl_manager.get_policy(tenant_id)` and applies a pure two-threshold decision (`decide_tool_hitl`) using `ToolSpec.risk_level`, and escalations carry the resolved risk into the `ApprovalRequest` (the hardcoded `RiskLevel.HIGH` dropped). The per-tenant `HITLPolicy` thresholds (`auto_approve_max_risk` / `require_approval_min_risk`) — write-side shipped 55.3/57.48/57.54, never read — are now **load-bearing**: the SAME tool call routes to escalate vs auto-approve per the tenant's stored policy. Backend only; NO migration / wire / codegen / frontend. Design note 35 + CHANGE-089.

## Q2 — Estimate accuracy + calibration

- **Plan**: bottom-up ~6.5 hr → class-calibrated commit ~3.9 hr (mult **0.60**, NEW class `harness-loadbearing-gap-fix`). Agent-delegated: **no** (parent-direct, `agent_factor` 1.0).
- **Actual**: ~7-7.25 hr (Day 0 探勘 ~0.75 incl. plan/checklist · Day 1 contract+38 unit+floor refinement ~1.0 · Day 2 loop+9 integration+1 regression fix+gate ~1.5 · Day 3 drive-through ~1.75 incl. the LLM-determinism detour · Day 4 design note 35 + CHANGE-089 + closeout ~1.5).
- **Ratio actual/committed ≈ 1.8** (OVER band by a lot); ratio actual/bottom-up ≈ 1.1 (the bottom-up was about right; the **0.60 multiplier was the miss**).
- **Calibration action**: `harness-loadbearing-gap-fix` **0.60 → re-point 0.85** (1st data point > 1.20 → per the matrix rule "re-point toward 0.80" + the Sprint 57.120 ceremony-not-code-accelerated insight). This was a parent-direct sprint with a real backend core + FULL ceremony (plan/checklist/Day-0/multi-leg drive-through/**design note**/CHANGE/retro) — that ceremony is not code-accelerated, so it lands ~0.85-1.0, not the 0.45-0.65 pure-repoint range. The 0.60 wrongly assumed AI/parent-direct acceleration that the ceremony-heavy shape doesn't get.

## Q3 — What went well

- **Day-0 三-prong pre-verified the crux** (`service_factory.py:124/134-137` already wires the DB store) → scope收斂 from "maybe wire the manager" to "pure loop decision" before any code. Saved a wrong-scope start.
- **Caught a silent safety regression BEFORE running** (Day 1): `ToolSpec.risk_level` defaults LOW → a flagged LOW-spec tool would have auto-approved under DEFAULT. The MEDIUM-floor refinement preserved backward-compat. This was a real correctness save driven by thinking through the semantics, not a test failure.
- **The drive-through delta is unambiguous**: SAME `python_sandbox` call, auto-approve under permissive vs escalate under strict, with `risk=MEDIUM` (not the old hardcoded HIGH) — live proof the new code path runs in real chat-v2.
- **Contained blast radius**: 2 src files + 2 new tests + 1 stale-assertion fix; mypy 0/371 unchanged, run_all 10/10.

## Q4 — What to improve

- **Drive-through tool choice up front**: I burned ~30 min on `echo_tool` (gpt-5.2 answered the trivial echo directly in 4/5 sessions = `0 tool calls`) before pivoting to `python_sandbox` (which the model cannot fake → reliable tool call). **Lesson**: for a drive-through that needs a deterministic tool call, pick a tool the LLM CANNOT self-answer (code execution / data retrieval), not a trivial transform. Candidate AD for the drive-through playbook.
- **Calibration**: the new-class 0.60 was too optimistic for a ceremony-heavy parent-direct sprint; the 57.120 insight should have been applied at plan time (start ~0.85). Re-pointed.

## Q5 — Anti-pattern self-check

- **AP-4 (Potemkin)**: ✅ this slice CLOSES a Potemkin (the load-bearing gap); drive-through proves the per-tenant delta live (not a dead control / fixture).
- **AP-1 (pipeline-as-loop)**: N/A (no new loop). **AP-2 (side-track)**: ✅ the decision is on the main `_cat9_tool_check` path. **AP-3 (scattering)**: ✅ pure helpers in the single-source `_contracts/hitl.py`, integration in `loop.py`; ToolGuardrail stays DB-free.
- **AP-6 (hybrid bridge debt)**: ✅ rejected the platform-ceiling-hybrid over-design; chose the minimal two-threshold semantics. **AP-8 (PromptBuilder)** / **AP-11 (version suffix)**: N/A.
- **0 violations**.

## Q6 — Design note 35 (spike-extract) — 8-Point Quality Gate

**File**: `docs/03-implementation/agent-harness-planning/35-hitl-risk-threshold-semantics.md`
**Verified ratio (estimated)**: ~95% (every technical claim has a file:line).

- [x] 1. Section header maps to the spike US (US-2/US-3 risk-threshold decision)
- [x] 2. file:line for every claim (`hitl.py:111-196` / `loop.py` helpers / `service_factory.py:124/134-137` / `tools/registry.py:66`)
- [x] 3. Decision matrix (risk-source A/B + precedence 3-option + the floor refinement)
- [x] 4. Verification command (the two pytest invocations + the drive-through)
- [x] 5. Test fixture reference (`test_hitl_decision.py` 38 + `test_loop_hitl_policy.py` 9)
- [x] 6. Open invariant boundary (§5 — validation deferred, content-guardrail HIGH out of scope, PermissionChecker parallel)
- [x] 7. Rollback path (§6 — contained revert, 1-2 hr, no infra)
- [x] 8. 17.md cross-ref (§4 — no new contract; extends the existing HITL single-source)

**Reviewer pass**: self-review.

## Q7 — Carryover

- `AD-HITL-Policy-Threshold-Validation` (🆕) — admin-PUT should validate `auto_approve_max_risk < require_approval_min_risk` (runtime is safe via escalate-first ordering, but a misconfigured overlap silently means "escalate").
- `AD-DriveThrough-Deterministic-Tool-Trigger` (🆕, process) — for drive-throughs needing a tool call, prefer a tool the LLM cannot self-answer (`python_sandbox` / retrieval), not a trivial transform (`echo_tool`).
- The remaining C-class 主流量 Potemkin items: `AD-FE-Tenant-Display-Fixture-Phase58` (sidebar/header fixture tenant) · `AD-ChatV2-HITL-Card-Tool-Name` (already shipped 57.108? verify) · `AD-HITL-Policy-ReadSide-Potemkin-Phase58` ✅ SHIPPED.
- `ToolSpec.hitl_policy` + the Sprint 51.1 `PermissionChecker` parallel HITL abstraction — possible separate Potemkin to audit (NOT this slice).
