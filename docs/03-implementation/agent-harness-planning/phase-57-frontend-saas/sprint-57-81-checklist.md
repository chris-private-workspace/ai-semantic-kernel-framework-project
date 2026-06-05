# Sprint 57.81 — Checklist (B-7 ErrorBudget Redis wiring)

**Plan**: `sprint-57-81-plan.md`
**Branch**: `feature/sprint-57-81-errorbudget-redis` (from `main` `18b6dd16`)
**Closes**: B-7 (ErrorBudget cross-instance + per-request correctness) / `AD-ErrorBudget-Redis-Wiring`

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (parent grep + code read, main `18b6dd16`; analysis doc 18 sprints old → all lines re-verified)
- [x] **Prong 1 (path)** — confirm: `error_handling/_redis_store.py` (RedisBudgetStore), `error_handling/budget.py` (Protocol + InMemory + TenantErrorBudget), `error_handling/__init__.py` (exports — RedisBudgetStore NOT exported), `api/main.py` (wire templates), `platform_layer/tenant/rate_limit_counter.py` (singleton pattern), `api/v1/chat/_category_factories.py` (factory), `loop.py` (consumer), `tests/.../error_handling/test_redis_budget_store.py` (FakeRedis fixture), `platform_layer/governance/` dir.
- [x] **Prong 2 (content)** — D-DAY0-1..7 in plan §0 (RedisBudgetStore impl + not-exported / state-in-store → per-request fix / gap site :236+:248-252+:257 / wire templates + singleton accessor pattern / **live consumer loop.py:320-322 record() — not Potemkin** / platform_layer singleton convention + import direction allowed / FakeRedis fixture).
- [x] **Prong 3 (schema)** — N/A (no DB table / migration / ORM change; RedisBudgetStore is pure Redis, no DB write-through).
- [x] **go/no-go** — GO; Tier 1 wiring (single obvious path per analysis doc); no scope fork. real_llm now LIVE (57.79/57.80) → B-7 timing appropriate.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-81-errorbudget-redis`
- [x] **Decisions locked**: singleton in `platform_layer/governance/` (convention: 3 existing wiring singletons in platform_layer; agent_harness DI-pure) NOT agent_harness; fail-open wire (mirror `_wire_rate_limit_counter`); NO DB session_factory / RLS (pure Redis — don't copy rate-limit over-wiring); NO real-Azure leg (budget increments on errors only → fakeredis accumulation test is the proof); parent-direct (NOT agent-delegated).
- [x] **Day-0 commit** plan + checklist + progress.md Day 0

---

## Day 1 — Provider + wiring + export + factory swap (US-1/US-2/US-3)

### 1.1 budget store provider singleton
- [ ] **NEW `platform_layer/governance/error_budget_provider.py`** — module-global `_budget_store` + `get_/maybe_get_/set_/reset_budget_store` (mirror `rate_limit_counter.py:526-558`); `BudgetStore` type via TYPE_CHECKING import
  - DoD: mypy clean; `maybe_get` lenient (None when unset); `get` strict-raises; `reset` clears

### 1.2 export RedisBudgetStore
- [ ] **`error_handling/__init__.py`** — add `RedisBudgetStore` to imports + `__all__` (so main.py imports via public path)
  - DoD: `from agent_harness.error_handling import RedisBudgetStore` works; mypy clean

### 1.3 startup wiring
- [ ] **`_wire_error_budget()` in `api/main.py`** — mirror `_wire_rate_limit_counter`: `Redis.from_url(settings.redis_url)` → `set_budget_store(RedisBudgetStore(client))`; whole body `except Exception` fail-open; `logger.info("api.main: error budget store wired")`
- [ ] **call in `_lifespan`** after `_wire_rate_limit_counter()` / `_wire_pricing_loader()`
  - DoD: NO session_factory / RLS / app.tenant_id (pure Redis); mypy clean

### 1.4 chat factory swap
- [ ] **`_category_factories.py:257`** — `TenantErrorBudget(maybe_get_budget_store() or InMemoryBudgetStore())` + import `maybe_get_budget_store`; update deferred comment :248-252 (AP-2 repaid)
  - DoD: mypy clean; MHist 1-line on factory file header

### 1.5 read changed code
- [ ] **re-read** — no loop.py / budget.py / RedisBudgetStore change; LLM-neutral; platform_layer→agent_harness import is TYPE_CHECKING-only / allowed

---

## Day 2 — Tests (US-4)

### 2.1 provider accessor unit tests
- [ ] **NEW `test_error_budget_provider.py`** — `set`→`maybe_get` returns it; `reset` clears; `get` raises when unset; reset isolation (autouse or explicit)

### 2.2 accumulation + fallback integration tests (the correctness claim)
- [ ] **accumulation** — wire `RedisBudgetStore(FakeRedis())` via `set_budget_store`; call `make_chat_error_deps()` TWICE; `record()` an error via each `TenantErrorBudget`; assert the 2nd reflects the ACCUMULATED count (per-request reset fixed) — contrast: InMemory baseline would NOT accumulate
- [ ] **fallback** — no wired store → `make_chat_error_deps()` returns `TenantErrorBudget` backed by `InMemoryBudgetStore` (no crash)
- [ ] reuse `FakeRedis(decode_responses=False)` fixture pattern from `test_redis_budget_store.py`

### 2.3 regression gate
- [ ] **targeted pytest** — provider + error_handling + chat factory tests green; confirm existing Cat 8 / factory tests unchanged

---

## Day 3 — Startup-log integration check (US-3) — local, no Azure

### 3.1 clean start + startup log (Risk Class E)
- [ ] **clean start backend** — :8000 free; fresh no-reload uvicorn
- [ ] **confirm startup log** `error budget store wired` (mirrors `pricing loader wired` / `rate-limit counter wired`) — proves wiring fires; no real LLM call needed
- [ ] **record** startup-log evidence in progress.md Day 3 (note: no real-Azure leg — budget increments on errors only; fakeredis accumulation test is the proof)

---

## Day 4 — Sweep + Closeout

### 4.1 Full sweep
- [ ] **Backend gates** — `mypy src/` 0 + `pytest` (new + regression) + `python scripts/lint/run_all.py` 10/10 (check_cross_category_import green for new platform→agent_harness import; check_llm_sdk_leak green; check_rls_policies unchanged — no schema)
- [ ] **No frontend** — 0 frontend changes (backend-only sprint)
- [ ] **Read all changed code** — wiring only; no loop.py/budget.py/store logic change; pure Redis (no over-wiring)

### 4.2 Closeout docs
- [ ] **CHANGE-048** in `claudedocs/4-changes/feature-changes/` (feature: wire RedisBudgetStore into main flow)
- [ ] **progress.md** Day 0-4 (incl. Day 3 startup-log evidence) + **retrospective.md** Q1-Q7
- [ ] **Checklist** all `[x]` (note any 🚧 carryover with reason)
- [ ] **Calibration** record (medium-backend 0.80; agent_factor 1.0 parent-direct; ratio)
- [ ] **AD status**: B-7 / `AD-ErrorBudget-Redis-Wiring` CLOSED; next-phase-candidates.md updated (B-8 / C-15 remain)
- [ ] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated)
- [ ] **Design note?** — NO (wiring of existing Cat 8 component; no new contract / no 17.md change)

### 4.3 Ship
- [ ] **Commit mapping** Day-0 / provider+wiring+factory / tests / closeout
- [ ] **Push + PR** (user-gated — explicit authorization required)
