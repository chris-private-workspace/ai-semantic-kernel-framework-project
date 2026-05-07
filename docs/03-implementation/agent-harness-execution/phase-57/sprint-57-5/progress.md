# Sprint 57.5 — Progress Log

> [Sprint Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-5-plan.md)
> [Sprint Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-5-checklist.md)

**Sprint Type**: V2 Reality Check & Smoke Test Sprint(non-feature;0 source code change)
**Branch**: `feature/sprint-57-5-reality-check`
**Branch HEAD start**: `7a0dba2e` (off main `06d5c6ed`)

---

## Day 0 — Setup + 三-prong 探勘 + Pre-flight Verify (2026-05-08)

### 0.1 Branch + plan + checklist commit ✅

- Branch created from main(`06d5c6ed`)→ `feature/sprint-57-5-reality-check`
- Commit `7a0dba2e` `docs(plan, sprint-57-5): pivot to V2 Reality Check Sprint + defer Feature Flags Admin UI`
- 4 files staged:
  - NEW `sprint-57-5-plan.md` (~430 lines V2 Reality Check plan)
  - NEW `sprint-57-5-checklist.md` (~330 lines Day 0-4)
  - RENAMED `feature-flags-admin-bundle-deferred-{plan,checklist}.md`(preserve as Phase 57.6+ candidate)

### 0.2 三-prong 探勘 v3 ✅

#### Prong 1 Path Verify ✅ (8/8 checks pass)

| File | Status |
|------|--------|
| `scripts/dev.py` | ✅ exists |
| `backend/src/api/main.py` | ✅ exists |
| `frontend/package.json` | ✅ exists |
| 16 Alembic migrations 0001-0016 | ✅ all 16 + `__init__.py` exist |
| `.env` (real config) | ✅ exists at project root |
| `.env.example` | ✅ exists at project root |
| `docker-compose.dev.yml` | ✅ exists at project root |
| `backend/alembic.ini` | ✅ exists |

#### Prong 2 Content Verify ✅ (5/5 checks pass)

- `scripts/dev.py` 含 start / stop / restart / status / logs lifecycle ops + Docker postgres/redis/rabbitmq + monitoring jaeger/prometheus/grafana
- `backend/alembic.ini` `script_location = src/infrastructure/db/migrations` ✅
- `.env.example` 含 4 required vars (DB_NAME / REDIS_HOST / RABBITMQ_HOST / AZURE_OPENAI_API_KEY) ✅
- `.env` (real config) 含 AZURE_OPENAI_API_KEY 真實值（非 placeholder）+ DB_PASSWORD + REDIS_HOST 全 set ✅
- 16 Alembic migrations naming aligned with V2 design — 0001 initial_identity / 0002 sessions_partitioned / 0003 tools / 0004 state / 0005 audit_log / 0006 api_keys_rate_limits / 0007 memory_layers / 0008 governance / 0009 rls_policies / 0010 pg_partman / 0011 approvals_status_check / 0012 incidents / 0013 hitl_policies / 0014 phase56_1_saas_foundation / 0015 feature_flags / 0016 sla_and_cost_ledger ✅

#### Prong 3 Schema Verify ✅ N/A but attempted (per fold-in spirit)

- 此 sprint 0 schema change → Schema verify 預期 N/A
- Attempted:`migrations/versions/0017_*.py` 不存在 confirm ✅
- Attempted:Alembic head pointer `0016_sla_and_cost_ledger` 確認(via `SELECT version_num FROM alembic_version`)✅

### 0.3 Calibration multiplier pre-read ✅

- `mixed` 0.60 5th application(reality check 性質類比 audit cycle 但有真實 boot service / browser test 執行成本)
- 既有 4-data-point evidence:53.7=1.01 / 56.2=1.17 / 57.3=0.57 / 57.4=0.42 平均 0.79 below band
- 此 sprint:bottom-up ~15 hr × 0.60 = **~9 hr** commit
- Day 4 retro Q2 verify expectations:若 ratio in band → 0.60 valid for reality-check sprints;若 < 0.85 → reality-check 應降至 0.40-0.50;若 > 1.20 → V2 累積 drift 比預期大 reality-check 工作量大

### 0.4 Pre-flight verify backend + frontend baselines ✅ (4+4 checks pass)

| Baseline | Expected | Actual | Status |
|----------|----------|--------|--------|
| Backend pytest collect | 1598 | 1598 (2.86s) | ✅ |
| Backend mypy --strict | 0/295 | 0 errors / 295 source files | ✅ |
| 8 V2 lints | 8/8 green | 8/8 green (2.60s total) | ✅ |
| LLM SDK leak agent_harness | 0 | 0 (Grep 0 matches) | ✅ |
| Frontend lint | clean | clean (`npm run lint`) | ✅ |
| Frontend build | success / 75 modules / 209.11 kB | success / 209.11 kB / 762ms / gzip 65.51 kB | ✅ |
| Frontend Vitest | 35 tests | 35/35 passed (1.70s) / 13 test files | ✅ |
| Playwright e2e baseline | 23 (per 57.4 closeout) | not run Day 0 (deferred to Day 2) | — |

### 0.5 env + Docker stack readiness ✅ + ⚠️ findings

- ✅ Docker daemon `Docker version 28.4.0`
- ✅ Docker stack 3 V2 services 已 healthy 8 days:
  - `ipa_v2_postgres` healthy
  - `ipa_v2_redis` healthy
  - `ipa_v2_rabbitmq` healthy
- ⚠️ `ipa_v2_qdrant` unhealthy 8 days(vector DB — D-finding #6)
- ✅ PG accepting connections via `pg_isready -U ipa_v2 -d ipa_v2`
- ✅ Redis PONG via `redis-cli`

### 0.5 真實 DB state 探勘 (bonus reality data)

#### Alembic head ✅
- `SELECT version_num FROM alembic_version` → `0016_sla_and_cost_ledger`(matches expected;16 migrations 全 applied)

#### Tables present (37 total)
- ✅ All expected V2 tables present including:tenants / users / sessions / messages (partitioned 2026_04/05/06) / audit_log / state_snapshots / tool_calls / tool_results / tools_registry / role_permissions / rate_limits / risk_assessments / sla_reports / sla_violations / cost_ledger / feature_flags / hitl_* / etc.

#### Row counts (real data state of dev DB before Sprint 57.5 work)

| Table | Rows | Reality observation |
|-------|------|--------------------|
| `tenants` | 763 | 大量 test/dev tenants 累積(可能來自 pytest fixtures 過去 22 sprint 累積) |
| `users` | 760 | 大量 test users 累積 |
| `sessions` | 560 | Sessions table 有累積 |
| `state_snapshots` | 480 | Cat 7 snapshots 有累積(Sprint 53.1 ship)|
| `audit_log` | 244 | Audit chain 有累積(Sprint 53.3+ ship)|
| `tool_calls` | **0** ⚠️ | **MAJOR FINDING D-4** — Cat 2 Tool Layer (Sprint 51.1) + 5 business domains (Sprint 51.0+55.1+55.2) 從未真實 execute |
| `feature_flags` | **0** ⚠️ | **D-finding D-2** — Sprint 56.1 ship 但 `seed_defaults()` 從未 invoke 過 |
| `cost_ledger` | **0** ⚠️ | **D-finding D-3** — Sprint 56.3 chat router observer 從未 fire |
| `sla_violations` | 0 | Expected — no real chat load |
| `sla_reports` | 0 | Expected — no monthly cron run |

### 0.6 Day 0 D-findings catalogued

#### Critical findings (drive Phase 57.6+ scope)

**D-1** 🟡 YELLOW (script detection bug)
- `python scripts/dev.py status` 報告:"Docker services not running or docker-compose not available"
- 實際:`docker ps` 顯示 ipa_v2_postgres / redis / rabbitmq 全 healthy 8 days
- Implication: scripts/dev.py docker detection 有 false-negative bug;不會妨礙 Day 1 boot 但 user-facing UX bug;catalog as Phase 57.6+ candidate

**D-2** 🟠 YELLOW (seed step missing from migration/boot)
- `feature_flags` table 0 rows
- Sprint 56.1 ship 4 baseline flags(thinking_enabled / verification_enabled / llm_caching_enabled / pii_masking)via `FeatureFlagsService.seed_defaults()`
- 實際:從未在此 dev DB 被 invoke
- Implication: seed step 沒被 wire 到 boot lifecycle (e.g. uvicorn startup event / alembic post-migration hook);Phase 57.6+ MUST-FIX candidate(否則 prod ship 時 admin 看不到 flags)

**D-3** 🟡 YELLOW (no real chat ever happened)
- `cost_ledger` table 0 rows
- Sprint 56.3 ship 56.3 chat router observer (record_llm_call + record_tool_call)
- 實際:0 entries — 確認 backend uvicorn 從未真實 boot 過或從未真實 chat 過
- Implication: 不是 cost_ledger 本身的 bug;反映 V2 22 sprint 累積但 0 次真實 chat fire — 這就是此 sprint 想 surface 的核心 reality

**D-4** 🔴 **RED — MAJOR Potemkin candidate**
- `tool_calls` table 0 rows
- Sprint 51.1 ship Cat 2 Tool Layer + Sprint 51.0 + 55.1 + 55.2 ship 5 business domains × 24 工具
- 實際:0 rows — Cat 2 Tool Layer + 5 business domains 從未真實 execute 過
- Implication: AP-4 Potemkin Feature 強候選 — 大量 V2 工具代碼存在但從未在真實 chat 中被 LLM 呼叫;Day 1 必須 verify 真實 chat 是否 trigger tool calls;若否 → Phase 57.6+ MUST-FIX-FIRST scope

**D-5** 🟢 GREEN (informational — 累積 baseline data)
- 763 tenants + 760 users + 560 sessions + 244 audit_log + 480 state_snapshots
- 大量 row counts 反映 dev DB 過去 22 sprint pytest fixtures + integration tests 累積
- Day 1 seed 可能 skip(已有充分 test data)— 但需 identify 1 個 stable default tenant 作 Day 1+ smoke target
- Implication: 不影響 reality check 進行;但 Day 1 需 user 提供 admin JWT (super-admin platform role) for admin endpoint smoke

**D-6** 🟡 YELLOW (vector DB unhealthy)
- `ipa_v2_qdrant` container unhealthy 8 days
- Vector DB(Qdrant)— V2 Memory Layer (Sprint 51.2 Cat 3 Memory) 是否需要 vector embeddings 存儲?
- Implication: Day 1 / Day 3 V2 planning audit 需 verify Cat 3 Memory 是否真的用 Qdrant;若否 → qdrant container 可移除;若是 → MUST-FIX

**D-7** 🟢 GREEN
- 16 Alembic migrations 全 applied to head `0016_sla_and_cost_ledger`
- Schema reality matches design

#### Day 0 三-prong 探勘 ROI

- Prong 1 Path Verify: 8 checks 0 unexpected drift(15 min)
- Prong 2 Content Verify: 5 checks 0 unexpected drift(15 min)
- Prong 3 Schema Verify: N/A but attempted(5 min)
- 但 Reality data 探勘 surface 7 D-findings (1 RED + 4 YELLOW + 2 GREEN) 在 ~30 min 內
- ROI:Day 0 三-prong + DB reality 探勘 ~1 hr cost prevented Day 1+ 假設驅動的 incorrect smoke direction;特別是 D-4 RED finding 直接 reframe Day 1 US-2 backend smoke 期望(若 0 tool calls fire on real chat → 真實主流量 broken);**ROI ≈ 8-12×** 預期(類比 57.3 + 57.4 ROI evidence)

### Day 0 累計時間
- 0.1 Branch + commit: ~5 min
- 0.2 三-prong 探勘: ~30 min(includes Reality data探勘)
- 0.3 Calibration pre-read: ~5 min
- 0.4 Pre-flight baselines: ~5 min(pytest collect + mypy + lints + frontend lint+build+Vitest)
- 0.5 env + Docker + DB explore: ~15 min
- 0.6 progress.md draft: ~10 min
- **Day 0 total ≈ 70 min** (~1.2 hr;under expected ~2 hr Day 0 budget)

### Day 0 → Day 1 transition

- Day 0 探勘 surface 4 個 critical findings(D1 + D2 + D3 + D4)需 Day 1 進一步 verify
- Day 1 boot path:Docker stack 已 ready;只需 boot backend uvicorn + frontend vite
- Day 1 priority shift:original plan 假設 boot from scratch;reality = boot 部分 done;Day 1 重點變成「真實主流量 fire chat → see if D-4 (tool_calls 0) is因為從未真實 fire 還是 wired-but-broken」
- D-2 seed_defaults 在 Day 1 必須先 invoke 才能進入 admin feature flags console smoke(若 Day 2 之後)

