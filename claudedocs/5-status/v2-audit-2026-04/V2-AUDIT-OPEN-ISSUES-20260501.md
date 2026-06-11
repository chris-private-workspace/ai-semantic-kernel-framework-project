# V2 Audit Open Issues — 2026-05-01 (UPDATED 2026-05-02 post-Sprint 52.5 merge)

**Audit window**: W1+W2 (2026-04-29) + W3 (2026-05-01) + mini-W4-pre (2026-05-01 evening)
**Coverage**: 9/22 V2 sprints fully audited + 49.4 fully covered (Day 1-2 W2 + Day 3-5 W4P-1) = **45%**
**Systematic pattern identified**: AP-4 Potemkin variant — "ABC + components delivered, main flow integration missing" (3 cases: W3-2 / W4P-1 / W4P-4)
**Tracking**: GitHub issues + this index doc + monthly review

> **2026-05-02 update**: Sprint 52.5 cleanup PR #19 merged into main as commit
> `d4ba89ef`. **All 8 P0 + 4 P1 closed.** 5 new Audit Debt items recorded
> in retrospective.md (Q5) — see "New Audit Debt" section below for the
> consolidated list.

---

## P0 Status (8) — ALL CLOSED ✅

All P0 carryover items closed in Sprint 52.5 PR #19 (merged d4ba89ef
on 2026-05-02). Phase 53.x worker fork no longer blocked by these items.

### Week 3 issues (4)

| # | Issue | Status | Resolved by |
|---|-------|--------|-------------|
| [#11](https://github.com/laitim2001/ai-semantic-kernel-framework-project/issues/11) | chat router multi-tenant 隔離 (W3-2 Critical 1) | ✅ Closed (Sprint 52.5) | fe0722ea + dc301732 |
| [#12](https://github.com/laitim2001/ai-semantic-kernel-framework-project/issues/12) | TraceContext propagation at chat handler (W3-2 Critical 2) | ✅ Closed (Sprint 52.5) | fe0722ea + dc301732 |
| [#13](https://github.com/laitim2001/ai-semantic-kernel-framework-project/issues/13) | audit_log hash chain verifier (W1-3) | ✅ Closed (Sprint 52.5) | 99eb327c + 9a0f65cb |
| [#14](https://github.com/laitim2001/ai-semantic-kernel-framework-project/issues/14) | JWT replace X-Tenant-Id header (W1-2) | ✅ Closed (Sprint 52.5) | 3d75ff68 + 0e883dab |

### mini-W4-pre new issues (4) — 2026-05-01 evening

| # | Issue | Status | Resolved by |
|---|-------|--------|-------------|
| [#15](https://github.com/laitim2001/ai-semantic-kernel-framework-project/issues/15) | OTel SDK version lock to ==1.22.0 (W4P-1) | ✅ Closed (Sprint 52.5) | c7796c2b |
| [#16](https://github.com/laitim2001/ai-semantic-kernel-framework-project/issues/16) | OTel main-flow tracer span coverage (audit-critical place, W4P-1) | ✅ Closed (Sprint 52.5) | a074eb29 + dc301732 |
| [#17](https://github.com/laitim2001/ai-semantic-kernel-framework-project/issues/17) | SubprocessSandbox Windows Docker isolation (W4P-3, CARRY-022) | ✅ Closed (Sprint 52.5) | c4aa6e86 |
| [#18](https://github.com/laitim2001/ai-semantic-kernel-framework-project/issues/18) | memory_tools handler tenant from ExecutionContext (W4P-4, CARRY-030) | ✅ Closed (Sprint 52.5) | dbfb906c |

**Originally-estimated total effort**: 12-17 days. **Actual**: ~1 day intensive sprint (single session).

**Sprint 52.5 PR**: https://github.com/laitim2001/ai-semantic-kernel-framework-project/pull/19 (merged d4ba89ef).

**Labels**: `audit-carryover` + `priority/P0`

---

## P1 Status (8)

> **2026-05-02 update**: PR #10 was OPEN, NOT actually merged when this doc
> originally claimed `✅ Fixed`. That was Audit Debt #1 (recorded in Sprint
> 52.5 retrospective Q5). The W1-2 #3 + W2-1 #5 work was redone within
> Sprint 52.5 (commits referenced below) and PR #10 closed as superseded.

| # | Item | Status | Resolution |
|---|------|--------|------------|
| W1-2 #3 | delete `backend/src/middleware/{tenant,auth}.py` stubs | ✅ Closed (Sprint 52.5) | 0e883dab (broader: also deleted auth.py + replaced with platform_layer/identity/auth.py); supersedes PR #10 commit ab0d727d |
| W2-1 #5 | CI lint scope expansion | ✅ Closed (Sprint 52.5) | 54a80243 (broader: codebase-wide black/isort/flake8 hygiene clearing 45+ pre-existing violations); supersedes PR #10 commit d3070e12 |
| W2-1 #4 | `adapters/azure_openai/tests/test_integration.py` | ✅ Closed (Sprint 52.5) | 54a80243 |
| W2-2 #6 | `requirements.txt` Celery cleanup + temporalio TODO | ✅ Closed (Sprint 52.5) | 54a80243 |
| W2-2 #7 | unify `runtime/workers/` ↔ `platform_layer/workers/` | ✅ Closed (Sprint 52.5) | 54a80243 (re-export shim instead of physical move; reversal-safe direction documented) |
| W2-2 #8 | AgentLoopWorker docstring stub warning | ✅ Closed (Sprint 52.5) | 54a80243 |
| W3-1 | mutable `LoopState` → frozen + reducer | ⏳ Phase 53.1 | Carryover (CARRY-007) transparently noted; not in Sprint 52.5 scope |
| W3-1 | `ToolCallExecuted/Failed` event owner drift | ⏳ Phase 51.x | Carryover (CARRY-009) transparently noted; not in Sprint 52.5 scope |

**Sprint 52.5 P1 closure rate**: 6/6 actionable items (W3-1 carryovers
remain owned by their target sprints, not Sprint 52.5 scope).

---

## New Audit Debt (Sprint 52.5 retrospective Q5) — 5 items

Recorded during Sprint 52.5 cleanup work — for audit session to integrate
into next audit cycle / OPEN-ISSUES tracking.

| # | Item | Status | Owner / Action |
|---|------|--------|---------------|
| AD-1 | OPEN-ISSUES.md `✅ Fixed` status set on PR-open instead of PR-merge (PR #10 stale state surfaced this) | ✅ Fixed inline above | This update closes the stale entries |
| AD-2 | Parallel audit session committed directly to main mid-sprint (commits 5c18869a + 69b83f96) — caused 2 recovery cycles | 📝 Process | Audit sessions to use feature branch + PR during active cleanup sprints |
| AD-3 | Graphify post-checkout/post-commit hooks were disabled for cleanup duration; user opted not to restore (effect: knowledge graph rebuild paused) | 📝 Decision | User decision; not a regression |
| AD-4 | `disabled_in_production: python_sandbox` flag was a proposed mitigation in W4P-3 but never landed as code (no production manifest exists yet) — N/A action | 📝 Documented | Phase 55+ deployment manifest authors take note |
| AD-5 | **CI infra 100% fail rate on main**: backend-ci.yml, ci.yml, e2e-tests.yml, lint.yml all failed last 3 runs each. Sprint 52.5 PR #19 fixed mypy+lint scope but CI infra (lint.yml needs sqlalchemy install, e2e needs Playwright setup, etc.) is broken at workflow-level. Admin-merge bypassed. | 🔴 NEW HIGH-PRIORITY | New cleanup sprint: 'CI infra restoration'. Estimated 3-5 days. |

---

## Process Fixes (W3 #1-#5 + mini-W4-pre #6)

| # | Fix | Status | Location |
|---|-----|--------|----------|
| 1 | Sprint plan template 加 Audit Carryover 段落 | ✅ Done | `phase-52-context-prompt/sprint-52-2-plan.md` §10 |
| 2 | Retrospective template 加 Audit Debt 段落 | ✅ Done | `phase-52-context-prompt/sprint-52-2-checklist.md` Day 4.9 |
| 3 | GitHub issue per P0/P1 | ✅ Done | This doc + issues #11-18 |
| 4 | 每月 Audit Status Review | ⏳ Scheduled | Manual review (next: 2026-06-01) |
| 5 | Audit re-verify 每 2-3 sprint | ⏳ Scheduled | W4 audit post-cleanup + 52.2 close |
| 6 | **Sprint retrospective 必答「主流量整合驗收」** (mini-W4-pre proposal) | ⏳ Proposed | per `MINI-W4-PRE-SUMMARY` §8 — counter to systematic AP-4 pattern |

---

## Audit Deliverables (19 reports)

### Week 1 (2026-04-29)
- `V2-AUDIT-BASELINE-20260429.md` — 起點 baseline (54 交付項 + 24 高風險)
- `V2-AUDIT-W1-CONTRACTS.md` — `_contracts/` 跨 sprint 一致性 ✅
- `V2-AUDIT-W1-RLS.md` — RLS + tenant_id 0-leak ✅
- `V2-AUDIT-W1-AUDIT-HASH.md` — Audit hash chain ⚠️ (P0 #3 source)
- `V2-AUDIT-W1-ORM-LOCK.md` — ORM TenantScopedMixin + StateVersion ✅
- `V2-AUDIT-WEEK1-SUMMARY.md`

### Week 2 (2026-04-29)
- `V2-AUDIT-W2-ADAPTER.md` — Adapter + LLM Neutrality ✅
- `V2-AUDIT-W2-WORKER.md` — Worker queue + agent_loop_worker ⚠️
- `V2-AUDIT-WEEK2-SUMMARY.md`

### Week 3 (2026-05-01)
- `V2-AUDIT-W3-0-CARRYOVER.md` — Process drift ❌ (7/8 P1 dropped)
- `V2-AUDIT-W3-1-PHASE50-1.md` — Cat 1 Loop + AP-1 lint ✅
- `V2-AUDIT-W3-2-PHASE50-2.md` — Phase 50.2 主流量 🟡 (P0 #1+#2 source)
- `V2-AUDIT-WEEK3-SUMMARY.md` — 雙層問題決策報告

### mini-W4-pre (2026-05-01 evening)
- `V2-AUDIT-W4P-1-PHASE49-4-D3-5.md` — 49.4 Day 3-5 OTel + pg_partman + Lint ⚠️ (P0 #5+#6 source)
- `V2-AUDIT-W4P-2-PHASE51-0.md` — 51.0 Mock 企業工具 ✅ (healthiest)
- `V2-AUDIT-W4P-3-PHASE51-1.md` — 51.1 Tool Layer L3 🟡 (P0 #7 source: Windows sandbox)
- `V2-AUDIT-W4P-4-PHASE51-2.md` — 51.2 Memory L3 ⚠️ (P0 #8 source: handler tenant)
- `V2-AUDIT-MINI-W4-PRE-SUMMARY.md` — Systematic AP-4 pattern + 8 P0 + Process fix #6 proposal

### Cleanup Template
- `V2-AUDIT-CLEANUP-SPRINT-TEMPLATE.md` — Sprint plan + checklist template (593 行) — **needs revision** for 8 P0 (was 4 P0)

---

## W4 Audit Trigger — READY (2026-05-02)

**Pre-conditions** (all hold):
1. ✅ All **8 P0 issues** (#11-18) closed (Sprint 52.5 PR #19 d4ba89ef)
2. ✅ 4 pending P1 resolved (Sprint 52.5 commit 54a80243)
3. ⏳ Sprint 52.2 — separate session; not gating W4 partial start
4. ✅ Sprint 52.5 retrospective filed at `docs/03-implementation/agent-harness-execution/phase-52-5/sprint-52-5-audit-carryover/retrospective.md`

**W4 scope**:
- Re-verify W1-2 (RLS + JWT) post-fix #11/#14
- Re-verify W1-3 (audit hash verifier) post-fix #13
- Re-verify W3-2 (Phase 50.2 main flow) post-fix #11/#12
- Re-verify W4P-1 (OTel coverage) post-fix #15/#16
- Re-verify W4P-3 (sandbox Windows isolation) post-fix #17
- Re-verify W4P-4 (memory tenant injection) post-fix #18
- Audit Sprint 52.1 (Cat 4 Context Mgmt) — already done, **first time covered**
- Audit Sprint 52.2 (PromptBuilder) — first time covered
- Audit cleanup sprint itself (process discipline check)
- **Systematic AP-4 pattern re-check** (per mini-W4-pre §3): main-flow integration coverage for all categories

**Estimated W4 duration**: 6-8 hours (larger than W3 due to expanded scope)

---

## Index Maintenance

This doc is the single source of truth for V2 audit follow-up status. Update when:
- Issue closes → mark P0 status `✅ Fixed (issue #N)`
- New audit week completes → add new row + update W4 trigger conditions
- Process fix matures → flip ⏳ to ✅

**Last updated**: 2026-05-02 (post-Sprint 52.5 merge — 8/8 P0 + 4/4 actionable
P1 closed; PR #19 admin-merged at d4ba89ef; 5 new Audit Debt items
recorded incl. critical CI infra failure; W4 trigger ready)
