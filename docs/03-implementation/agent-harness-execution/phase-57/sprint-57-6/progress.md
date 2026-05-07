# Sprint 57.6 — Progress

> **Sprint**: 57.6 — Reality Gap Fix Sprint + merged Phase 57.7 doc updates
> **Branch**: `feature/sprint-57-6-reality-gap-fix` (off main `426fce7b`)
> **Goal**: Close Sprint 57.5 V2 Reality Check top 5 RED findings (R1+R2+R3+R4-partial+R5) + merged 5 doc updates per Decision 4 (b)。Closes 10 NEW AD-Reality-N + AD-Sprint-Plan-7。
> **Calibration**: `reality-gap-fix` 0.50 NEW class 1st application; bottom-up est ~25-29 hr × 0.50 = ~13-15 hr commit。
> **Plan / Checklist**: [plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-6-plan.md) / [checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-6-checklist.md)

---

## Day 0 — 2026-05-08 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch + plan + checklist commit ✅

- Branch: `feature/sprint-57-6-reality-gap-fix` off main `426fce7b`
- Commit `90b77807`: plan (663 lines) + checklist (295 lines)。Format mirrors 57.5 (plan 9 sections / checklist Day 0-4)
- Pushed with `-u origin` upstream tracking

### 0.2 Day-0 三-prong 探勘 ✅

#### Prong 1 Path Verify (10 path checks)

| # | Path | Status | Note |
|---|------|--------|------|
| 1 | `scripts/dev.py` | ✅ exists | |
| 2 | `backend/src/api/main.py` | ✅ exists | The **REAL** V2 entry — has `_lifespan` + `create_app` + 7 routers |
| 3 | `backend/src/main.py` | ⚠️ exists | But is **49.1 minimum stub**(only `/health`,docstring says port 8001),NOT the real entry |
| 4 | `frontend/vite.config.ts` | ✅ exists | |
| 5 | `backend/requirements.txt` | ✅ exists | |
| 6 | `backend/src/api/v1/chat.py` | ❌ **DRIFT** | Checklist 假設此 single-file path;real = **`backend/src/api/v1/chat/` folder** with handler.py / router.py / sse.py / schemas.py / _verifier_factory.py / session_registry.py / README.md |
| 7 | `scripts/lint/*.py` | ⚠️ partial drift | 8 lint scripts exist but **names 不同於 checklist 期望** — 詳見 D-Reality-1.6 |
| 8 | `.github/workflows/` | ✅ exists | 6 workflows: backend-ci / frontend-ci / e2e-tests / lint / playwright-e2e / deploy-production |
| 9 | `backend/src/infrastructure/db/models/` | ✅ exists | 12 ORM model files |
| 10 | `backend/src/agent_harness/` | ✅ exists | Confirmed via re-run from project root cwd |

#### Prong 2 Content Verify (7 checks — major source code claims)

| # | Plan claim | Real grep result | Status |
|---|-----------|-----------------|--------|
| 1 | `scripts/dev.py` uvicorn invocation | L435: `'main:app'`(NOT `api.main:app`) | ❌ confirms 57.5 D-12 (entry-point drift) |
| 2 | `vite.config.ts` proxy target | L22: `target: "http://localhost:8001"`(NOT 8000) | ❌ confirms 57.5 D-21 (port drift) |
| 3 | `api/main.py` already has lifespan? | L72-83: `_lifespan()` exists with `configure_json_logging` + `setup_opentelemetry` only;NO `load_dotenv` | ⚠️ partial — US-2 task = ADD `load_dotenv()` to existing `_lifespan()`(NOT add new lifespan) |
| 4 | `requirements.txt` has python-dotenv | grep `python-dotenv` = 0 results | ❌ need add per US-2 |
| 5 | Codebase has `load_dotenv` import | grep `load_dotenv\|dotenv` in `backend/src` = 0 results | ❌ confirms 57.5 D-20 (no .env autoload) |
| 6 | 8 lint scripts in run_all.py | L60-73: confirm 8 lints orchestrated;real names 不同於 checklist | ⚠️ partial — see D-Reality-1.6 below |
| 7 | LLM SDK leak in agent_harness | grep hits 2 files(`compactor/semantic.py:20` / `token_counter/claude_counter.py:19,23`)— all are **docstring** explicitly forbidding import;lint excludes string content → **0 real imports** | ✅ matches 57.5 baseline 0 leak |

#### Prong 3 Schema Verify (4 ORM table checks)

| # | Plan claim | Real schema | Status |
|---|-----------|-------------|--------|
| 1 | `sessions` table exists | `class Session(Base, TenantScopedMixin)` at `sessions.py:73` | ✅ |
| 2 | `audit_log` table exists | `class AuditLog(Base, TenantScopedMixin)` at `audit.py:67` | ✅ |
| 3 | `cost_ledger` table has `input_tokens INT` + `output_tokens INT` + `cached_tokens INT` columns(per Sprint 57.2 AD-Cost-Ledger-Token-Split) | Real columns at `cost_ledger.py:81-87`: `cost_type` / `sub_type` / `quantity` / `unit` / `unit_cost_usd` / `total_cost_usd` / `session_id`。**NO direct `input_tokens` / `output_tokens` / `cached_tokens` columns** — token-split implemented via **2 entries with same `cost_type='llm'` + different `sub_type='input/output/cached'`** | ⚠️ NEW finding — schema interpretation drift (token-split is ROW-level not COLUMN-level) |
| 4 | `tool_calls` table has `tool_name` + `status` + `duration_ms` + `result_preview` columns | Real columns at `tools.py:151-167`: `tool_name` / `status` / `duration_ms` ✅; **NO `result_preview` column** | ⚠️ minor drift — observer hooks 須 omit result_preview OR record elsewhere |

### 0.2 Drift findings catalogued (10 cumulative)

#### Confirms 57.5 RED findings (6)

- **D-Reality-1.1 (R1 / 57.5 D-12)**: scripts/dev.py L435 用 `'main:app'` → 啟動 49.1 stub instead of real V2 app。**Day 1 US-1 fix**: change to `'api.main:app'`
- **D-Reality-1.2 (R1 / 57.5 D-21)**: vite.config.ts L22 target = 8001 (stub port) instead of 8000 (real V2 default)。**Day 1 US-1 fix**: change to 8000
- **D-Reality-1.3 (R1 / 57.5 D-27)**: backend/src/main.py 49.1 stub still exists + serves only /health。Once US-1 fixes dev.py to point at api.main:app,this stub becomes dead → **Day 1 US-1 closing decision**: remove file with reference to AD-Reality-1
- **D-Reality-1.4 (R2 / 57.5 D-20)**: backend/src 全 codebase 0 `load_dotenv` import → real_llm mode 503 confirmed cause。**Day 1 US-2 fix**: add `load_dotenv()` to existing `_lifespan()` + add `python-dotenv>=1.0` to requirements.txt
- **D-Reality-1.5 (R3 / 57.5 D-16/17/18)**: chat router structure = folder NOT single file (handler.py / router.py / sse.py / schemas.py / _verifier_factory.py / session_registry.py)。**Day 2 US-3 implementation point**: observer hooks likely go into `handler.py` (where SSE events emitted) — need investigate Day 2 morning before code
- **D-Reality-1.6 (R5 plan §0.2)**: 8 lint script names drift vs checklist — real names + checklist 假設:
  - check_ap1_pipeline_disguise.py(checklist 假設 check_ap1.py)
  - check_promptbuilder_usage.py(checklist 假設 check_promptbuilder.py)
  - check_sole_mutator.py ✓
  - check_llm_sdk_leak.py(checklist 假設 check_neutrality.py)
  - check_rls_policies.py ✓
  - check_cross_category_import.py(checklist 假設 check_cross_category.py)
  - check_duplicate_dataclass.py(checklist 沒列)
  - check_sync_callback.py(checklist 沒列)
  - **checklist 假設的 check_no_orphan_code.py / check_observability_spans.py NOT FOUND**
  - **Day 3 US-5 wire ap4 to run_all.py**: just add `("check_ap4_frontend_placeholder.py", [...])` to `LINTS = [...]` list — naming drift是 plan-side only,real lint 8/8 status unaffected

#### NEW findings (4)

- **D-Reality-1.7 (NEW)**: cost_ledger schema 是 ROW-level token-split(2 entries `sub_type=input` + `sub_type=output` per LLM call),NOT COLUMN-level。**Day 2 US-3 LLMResponded observer**: insert 2 cost_ledger rows per LLM call(各 input + output token type),NOT 1 row with multiple columns。AD-Cost-Ledger-Token-Split (Sprint 57.2) 真實 implementation 已採 row-level — no schema change needed
- **D-Reality-1.8 (NEW)**: tool_calls table 沒 `result_preview` column。**Day 2 US-3 ToolCallExecuted observer**: omit result_preview field OR truncate to args.preview JSON value (re-using `arguments` JSONB column);minor adjustment from plan
- **D-Reality-1.9 (NEW)**: backend/src/api/main.py 已有 `_lifespan()`(L72-83)but plan §US-2 假設 needs ADD lifespan from scratch。**Day 1 US-2 task adjusted**: ADD `load_dotenv()` call inside existing `_lifespan()` first line,plus 1 import line。Net delta 2-3 lines code change instead of new lifespan structure
- **D-Reality-1.10 (NEW)**: chat router file structure folder vs single-file。Plan-time references all to `chat.py` need replace with explicit sub-module paths in commit messages + checklist (handler.py for SSE event observer hooks based on file names — verify Day 2 morning)

### 0.3 Calibration multiplier pre-read ✅

- `reality-gap-fix` 0.50 NEW class 1st application
- Bottom-up est ~22-26 hr (5 USs reality fix) + ~3 hr (5 doc updates merged) = ~25-29 hr
- Calibrated commit ~13-15 hr (multiplier 0.50)
- Day 4 retro Q2 verify:若 ratio in [0.85, 1.20] band → 0.50 baseline validated
- Pending 2-3 sprint window evidence before AD-Sprint-Plan-7 promotion + this `reality-gap-fix` baseline promotion

### 0.4 Pre-flight verify(main green baseline)✅ partial

- ✅ `python -m pytest --collect-only -q` → **1598 tests collected** in 1.66s (matches 57.5 closeout baseline `426fce7b`)
- ✅ LLM SDK leak grep `backend/src/agent_harness/` → 2 files match but **all hits are docstring text explicitly forbidding import** (compactor/semantic.py L20 / claude_counter.py L19+23) — **0 real imports**;lint excludes string content
- ⚠️ mypy --strict / 8 V2 lints / frontend npm baselines: **trusted from 57.5 closeout `426fce7b`** since 57.6 Day 0.1 commit `90b77807` only added plan + checklist docs (zero source code change between baseline and current HEAD) — explicit live verify deferable to Day 1 if needed before code change starts

Per CLAUDE.md sacred rule:🚧 deferred items above marked + reason given。

### 0.5 Day 0 commit + push (this commit)

| Day 0 task | Status |
|-----------|--------|
| 0.1 Branch + plan + checklist commit | ✅ commit `90b77807` |
| 0.2 三-prong 探勘 v3(Path + Content + Schema) | ✅ 10 D-findings catalogued |
| 0.3 Calibration multiplier pre-read | ✅ `reality-gap-fix` 0.50 1st app |
| 0.4 Pre-flight verify | ✅ pytest 1598 + LLM leak 0;⚠️ rest trusted from 57.5 closeout zero-delta |
| 0.5 progress.md commit + push | ⏳ this commit |

**Day 0 attempt time**: ~50 min (探勘 ~30 min + progress.md ~15 min + commit ~5 min)。
**Day 0 D-findings**: 10 cumulative (6 confirms 57.5 RED + 4 NEW including 2 schema + 2 plan-claim)

### Day 1 scope adjustments per Day 0 findings (per AD-Plan-1 audit-trail)

- **US-1**:
  - scripts/dev.py L435 `main:app` → `api.main:app` (single edit)
  - vite.config.ts L22 `8001` → `8000` (single edit)
  - backend/src/main.py removal (49.1 stub now dead post-US-1)
- **US-2**:
  - api/main.py existing `_lifespan()` ADD `load_dotenv()` first line + import (NOT new lifespan)
  - requirements.txt ADD `python-dotenv>=1.0`
- **US-3 (Day 2)**:
  - chat router observer hooks — implement at handler.py(folder structure)
  - LLMResponded → 2 cost_ledger row inserts(input + output sub_type)NOT 1-row-with-columns
  - ToolCallExecuted → omit `result_preview` field(no such column)
- **US-5 (Day 3)**:
  - check_ap4_frontend_placeholder.py wire to run_all.py via `LINTS = [...]` list append
- **No plan revision needed** for any of these — all are real-implementation adjustments within US scope (not scope expansion)

---

(Day 1+ entries TBD)
