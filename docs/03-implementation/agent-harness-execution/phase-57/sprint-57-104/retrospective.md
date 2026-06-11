# Sprint 57.104 Retrospective — Per-tenant Model Policy (C1)

**Closed**: 2026-06-11
[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-104-plan.md) · [Progress](./progress.md)

---

## Q1 — What shipped?

The first config-tiering vertical (harness-deepening Workflow C slice C1): a tenant governs its own `{action, cheap}` LLM model selection. Backend resolution chain (neutral `ModelPolicy` value object + TTL-cached resolver + `build_azure_model_profile(policy)` reshape + per-request wiring) + a pricing-validated admin write/read (`PUT`/`GET /admin/tenants/{id}/model-policy`) + a "Model Policy" tab in the tenant-settings operator IA. Commits `2816e883` (backend) + `ae2aed96` (FE). `loop.py` diff 0; no DB migration; no new wire event.

## Q2 — Estimate accuracy (calibration)

- Scope class **`config-tiering-model-policy-spike` (NEW, 0.60, 1st data point)** — full-stack new-domain config-tiering vertical (resolver + cache + builder reshape + admin write/read + FE tab mirror).
- Bottom-up est ~19 hr → class-calibrated commit ~11.5 hr (mult 0.60).
- **Actual ≈ 10-11 hr** (backend ~6 parent-direct + FE ~3 agent-delegated-then-re-verified + drive-through ~1.5). Ratio `actual / committed ≈ 0.9-0.95` — **IN band**. 0.60 holds for the 1st data point; KEEP pending 2-3 sprint validation.
- **Agent-delegated: partial** — the backend (US-1..US-5, the cross-layer resolve seam) was parent-direct (`agent_factor` n/a, careful hands); the FE tab (US-6, mechanical QuotasTab mirror) was code-implementer-delegated then parent-re-verified (every gate re-run + code reviewed). This mixed mode is why a single `agent_factor` wasn't applied — the calibration is the blended full-stack 0.60.

## Q3 — What went well?

- **The `resolve_session_persona` precedent was the keystone** — finding it (Day-1, `handler.py:654`) resolved the sync/async boundary cleanly: resolve in the async router, thread the neutral `ModelPolicy` into the sync builders. No async-DB-in-the-wiring-layer, no builder signature churn beyond the one intended reshape.
- **Day-0 three-prong caught the load-bearing facts up front** (0% backend scope shift): D2 (only 2 `build_azure_model_profile` callers → low-risk reshape), D3 (BaseSettings None-override trap → conditional kwargs), D6 (cost_ledger flows from `event.model` → simpler than assumed, no router wiring), D9 (the FE operator home EXISTS → corrected the plan's FE-deferral assumption).
- **The drive-through was strong** — a single-tenant-two-policies flow (nano → mini via the tab) proved the WHOLE chain INCLUDING cache invalidation, with a natural pre-C1 gpt-5.2 baseline already in `cost_ledger` for the before/after. Cleaner than two static tenants.
- **Delegated FE + parent re-verify worked** — the agent mirrored QuotasTab faithfully (English copy, no dead controls, correct 422 surfacing); the parent re-ran every gate (incl. `check:mockup-fidelity`) + reviewed the 422 path end-to-end (Before-Commit item 7 honored).

## Q4 — What to improve / lessons?

- **The D9 FE-scope correction mid-Day-0 cost a plan churn** — the initial plan deferred the FE on a "no FE home" assumption that Day-0 Prong-2.5 disproved. Lesson: for any admin/operator feature, run Prong-2.5 (FE tree audit) BEFORE writing §9 Out-of-Scope, not after. The cost was small (the plan is a draft + the user confirmed include-the-tab), but the §3.6/§4/§7/§9 rewrite churn was avoidable.
- **GET returns stored-only, not stored∪defaults** — the plan said "∪ defaults"; I reduced to stored-sparse (UI shows "System default" for unset) to avoid exposing env deployment names via the admin API. A reasonable simplification, recorded — but it was a silent §-deviation noticed at test-time; should have been a Day-1 explicit drift note.
- **The drive-through screenshot coverage was partial** — I screenshotted the nano set + 422 but proved the mini chat + clear via the cost_ledger query (not a screenshot). Acceptable (the query IS stronger evidence than a screenshot), but a future drive-through of a cost-differentiation feature should screenshot the cost dashboard too if it renders the sub_type.

## Q5 — Carryover / next

- **C2** (compaction cheap tier + 30-turn quality gate), **C3** (per-tenant verification/HITL/guardrail policy + risky-action detector), **C4** (non-Azure profile builders) — later C-workflow slices.
- **`AD-RBAC-DB-To-JWT-Wiring-Phase58`** — the production-OIDC admin-authz gap (shared across all admin endpoints) — its own slice; unblocks production drivability of every admin write.
- The **10-slice roadmap** remaining (per `harness-deepening-proposal-20260610.md`): B3 (HANDOFF 收尾), C3, C2, B4, A3 + the deferred B2b inject UI (§2.5 detached teammate).
- Cheap-tier per-tenant override: gate-verified, not drive-through-verified (the drive-through exercised the action override). → opportunistic drive-through next C-slice.

## Q6 — Discipline self-check

- ☑ Plan → Checklist → Day-0 three-prong → Code → Update Checklist → Progress (5-step honored).
- ☑ No unchecked `[ ]` deleted (the wiring unit test marked 🚧 DEFERRED with reason — now drive-through-proven).
- ☑ Multi-tenant 鐵律 (resolver tenant-scoped; PUT meta_data tenant-scoped; isolation test).
- ☑ LLM Provider Neutrality (`ModelPolicy` neutral; agent_harness untouched; `check_llm_sdk_leak` 0).
- ☑ Drive-Through Hard Constraint (real UI + real Azure + real cost_ledger — PASS, not gate-only).
- ☑ Delegated FE parent-re-verified (Before-Commit item 7).

## Q7 — Design Note Extract (spike sprint — required per §Step 5.5)

**File**: `docs/03-implementation/agent-harness-planning/27-per-tenant-model-policy-design.md`
**Verified ratio (estimated)**: ~95% (every invariant carries a file:line or a drive-through/test reference).
**8-Point Quality Gate**: all ✅ (self-reviewed in design note §8) — section headers map to the spike / file:line claims / decision matrices / verification command / test fixtures / open-invariant fence / rollback path / 17.md cross-ref.
**Reviewer pass**: self-review (solo-dev). C1 is a genuine NEW domain (config tiering), so the design note is required (not a composition continuation like 57.102/103).
