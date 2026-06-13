# Sprint 57.114 Retrospective — Per-Tenant Skills Catalog

**Closed**: 2026-06-13
**Scope class**: `per-tenant-catalog-table-backed` (NEW, 0.60, 1st data point)
**Outcome**: Full-stack per-tenant Skills overlay shipped; drive-through ALL 3 legs PASS; `AD-Skills-Per-Tenant-Catalog` CLOSED.

---

## Q1 — What did we ship?

The second slice of the Skills System epic: a **per-tenant overlay** on the 57.113 bundled registry.
- Cat 5: `SkillRegistry.with_overlay` (pure name-keyed merge, override-by-name).
- DB: `tenant_skills` table + `TenantSkill` ORM + migration `0030` (RLS two-policy, no sentinel).
- platform_layer: `TenantSkillService` (RLS-scoped CRUD) + `resolve_tenant_skill_registry` (TTL cache, fail-open).
- API: 4 admin CRUD endpoints + a **1-line** chat router swap (`handler.py`/`make_default_executor`/`loop.py` untouched).
- FE: a "Skills" tab (list-CRUD) in tenant settings + service + hooks + types + Vitest.

Gate: mypy 0 · run_all 10/10 (wire 24) · backend pytest 2602+5skip (+36) · FE lint 0 / build / Vitest 851 (+11) / mockup-fidelity 51. Drive-through (real chat-v2 + real Azure gpt-5.2, 2 tenants): A author→follow / B isolation+bundled / C override — ALL PASS; CRUD controls all live.

## Q2 — Estimate accuracy (calibration)

- Plan: bottom-up ~21 hr → class-calibrated commit ~12.5 hr (mult 0.60). Plan declared `Agent-delegated: partial`.
- **Actual**: ~11.5 hr-equiv, executed **parent-direct** (I wrote all backend + FE myself; no code-implementer agent this session — so the real classification is `agent-delegated: no`, `agent_factor 1.0`, not the planned `partial`). The class multiplier 0.60 alone was the effective calibration.
- **Ratio**: ~11.5 / 12.5 ≈ **0.92 → IN band**. KEEP `per-tenant-catalog-table-backed` **0.60** (1st data point; revisit at the 2nd). No matrix change.

## Q3 — What went well?

- **The 57.113 parameter seam paid off exactly as designed**: because `build_handler` already took `skill_registry`, the backend wiring was one line. Day-0 D-build-handler-uses (Prong-2) confirmed this upfront → no scope surprise.
- **Day-0 三-prong caught the real shape**: D-mypy-list-shadow (Sequence vs list), the RLS-minus-sentinel decision, the dedicated-table-vs-JSONB decision — all settled before Day-1 code.
- **The pre-commit projection invariant** (project `SkillResponse` before `db.commit()`) was reasoned out from the `expire_on_commit` + RLS interaction, not discovered via a failing test — the integration tests then confirmed it. A table-backed admin resource hits this where the model-policy/harness-policy (dict-projected) precedents did not.
- **Drive-through was decisive, not ceremonial**: Leg B's `read_skill` 0× and Leg C's override-vs-bundled contrast are exactly the load+follow + isolation evidence that a gate-only pass cannot give. dev-login's `[user,admin,platform_admin]` + auto-tenant-create made a 2-tenant drive-through cheap.

## Q4 — What to improve / lessons?

- **D-mypy-list-shadow is a reusable Python gotcha**: a `list[X]` annotation inside a class with a `list` method binds to the method for any method defined after it. Prefer `Sequence[X]`. (Already noted in progress.md; worth keeping in mind for any registry/collection class.)
- **The FE test path in the checklist was wrong** (`components/tabs/__tests__/` vs the real `tests/unit/**` from vite.config). Caught at Day-3 start, not a cost, but the plan/checklist templating should grep `vite.config.ts test.include` when citing an FE test path.
- **eslint-disable placement for multi-line `style={{`**: the directive must sit directly above the `style=` line (where the `no-restricted-syntax` node is), not above the `<div` opening tag. One re-run cost.

## Q5 — Anti-pattern self-check

- **AP-4 (Potemkin)**: ❌ none — the drive-through proves the skill genuinely changes model behavior (load+follow), not a stub; Leg B proves isolation (not a hardcoded pass); all CRUD controls driven (no dead control / no fixture).
- **AP-2 (reachable main flow)**: ✅ the overlay reaches chat via `router.py:264→308 → build_handler` (主流量, 約束 2).
- **AP-3 (no scattering)**: ✅ overlay in Cat 5 (`agent_harness/skills/`), DB service in `platform_layer/skills/`, endpoints in `admin/tenants.py`, table in `infrastructure/db/models/skill.py` — each in its home category.
- **Multi-tenant 鐵律**: ✅ `tenant_id NOT NULL` + RLS two-policy (`check_rls_policies` green) + the 3 mandatory tests (cross-read empty / cross-write 404 / RLS enforced) at the endpoint level.

## Q6 — Carryover / next

Carried (in `next-phase-candidates.md`): per-tenant authoring richness (bundled scripts / multi-file skill bundles), slash-command invocation, Inspector skill affordance, an authoring UI beyond raw text, per-tenant skill-count quota + body-size limits, multi-worker cache invalidation signal. `AD-Skills-Per-Tenant-Catalog` → CLOSED.

## Q7 — Design note extract (8-point quality gate)

**File**: `docs/03-implementation/agent-harness-planning/32-skills-per-tenant-catalog.md`
**Verified ratio (estimated)**: ~97%

| # | Gate | Pass |
|---|------|------|
| 1 | Section header maps to spike US | ✅ §1 (per-tenant overlay as wired 57.114) |
| 2 | Every claim has file:line | ✅ registry.py:111 / service.py:87,199,233,255 / skill.py:51 / router.py:264,308 / tenants.py:1857-2038 |
| 3 | Decision matrix | ✅ §2 dedicated-table vs JSONB + RLS-minus-sentinel |
| 4 | Verification command | ✅ per-§3 pytest paths + alembic up/down + run_all |
| 5 | Test fixture reference | ✅ the 5 test files (overlay/service/resolver/admin/wiring) |
| 6 | Open invariant fenced | ✅ §6 (authoring richness / slash-command / quota / multi-worker cache — NOT verified) |
| 7 | Rollback path | ✅ §7 (revert 2-line swap → bundled-only; bundled is the fail-open sentinel) |
| 8 | 17.md cross-ref | ✅ §4 — explicit decision: NO new contract (matches model-policy/harness-policy resolver precedent) |

**Reviewer pass**: self-review.
