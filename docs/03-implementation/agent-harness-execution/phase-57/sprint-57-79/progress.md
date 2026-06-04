# Sprint 57.79 Progress — C-11 billing-correctness 收尾

**Branch**: `feature/sprint-57-79-c11-billing-gaps` (from `main` `3c3e85df`)
**Closes**: `AD-Cost-Ledger-Model-Pricing-Key-Mismatch` + `AD-Adapter-MaxTokens-NewModel-Param`

---

## Day 0 — 2026-06-04 — Plan-vs-Repo Verify + Branch + Decisions

### Accomplishments
- Decision chain: Area-A program COMPLETE → user picked "先做 carryover/B vs ?" → investigated → B 區實際只剩 B-7(billing 束) → user picked **C-11 real-LLM 收尾** → investigated C-11 真實剩餘 = 2 billing gaps (e2e 閉環已 LIVE) → user picked **sprint 內跑真 Azure 驗證**.
- Plan + checklist drafted (mirror 57.78 9-section / Day 0-4 format).
- Branch created.

### Day-0 verify (Prong 1 path + Prong 2 content; Prong 3 N/A — no schema change)
- **Prong 1 (path)** ✅ — `pricing.py`, `llm_pricing.yml`, `adapter.py`, `config.py`, `test_pricing_loader.py`, `e2e-real-llm-smoke.yml` all confirmed present.
- **Prong 2 (content)** ✅ — D-DAY0-1..7 (plan §0): pricing key flow (response.model→exact lookup→None→$0); yaml lacks gpt-5.2; max_tokens hard-wired ×2 (`adapter.py:210-211`+`:282-283`); config has model_name/api_version/model_family; **config.model_name staleness trap (D-DAY0-6)**; test gaps.
- **Prong 3 (schema)** N/A — no DB table / migration / ORM change.

### Drift findings
- **D1 (no drift — confirms heavy path avoided)**: pricing fix is lookup-layer normalize, NOT a schema/model change. cost_ledger row keeps full model id (audit) while pricing matches base.
- **D2 (staleness trap, plan §8 Risk)**: Gap-2 branches off `config.model_name`; if stale (gpt-4o vs deployment gpt-5.2) → mis-branch. Day-3 real-LLM probe prints `response.model` to confirm + align.
- No scope shift (≤20%). GO for Day 1.

### Decisions locked
- Gap-1: **pricing-lookup date-suffix normalize** over yaml full-date-key (robustness — avoids silent $0 on future version bumps).
- Gap-2: adapter **`model_name`-prefix** param branch (`gpt-5` → max_completion_tokens).
- **parent-direct** (NOT agent-delegated — billing correctness care + real-LLM verify is parent/user collab). agent_factor 1.0.
- real-LLM Azure verify THIS sprint (user `.env` live key).

### Blockers / dependencies
- 🚧 **D1 (gpt-5.2 USD pricing — user-provided)**: Gap-1 yaml edit (task 1.2) BLOCKED until user provides real gpt-5.2 per-million pricing. Cannot fabricate. Normalize code (1.1) + tests (1.3, fixture price) + Gap-2 (Day 2) proceed unblocked meanwhile.
- **D2 (live Azure `.env`)**: Day-3 verification needs user env. Confirmed available.

### Remaining for Day 1+
- Day 1: Gap-1 normalize code + tests (yaml blocked on D1).
- Day 2: Gap-2 adapter param helper + call-site swaps + tests.
- Day 3: real-LLM Azure verify (clean restart + startup log + response.model + cost_ledger unit_cost>0 + no-400 token cap).
- Day 4: sweep + closeout.

### Notes
- Bottom-up est ~7.5 hr → calibrated ~6 hr (medium-backend 0.80, parent-direct).

---

## Day 1-2 — 2026-06-04 — Gap 1 + Gap 2 code + unit tests

### Accomplishments
- **Gap 1 (pricing normalize)**: `pricing.py` `get_llm_pricing` retries with `-YYYY-MM-DD` stripped on exact miss (`_strip_version_suffix` + `_VERSION_SUFFIX_RE`); `llm_pricing.yml` + `azure_openai.gpt-5.2` (input 1.75 / output 14.00 / cached 0.175 — user-provided) + bumped last_updated.
- **Gap 2 (adapter param)**: `adapter.py` `_max_tokens_param_name(model_name)` module helper (`gpt-5` prefix → max_completion_tokens); both call-sites (chat :210-211 + stream :282-283) swapped. Impl note: used module fn `_max_tokens_param_name(self.config.model_name)` directly (simpler than plan's instance wrapper).
- **Tests**: pricing +4 (gpt-5.2 exact / date-suffix normalize / date-suffixed-unknown None / non-date no-false-normalize); adapter NEW `test_max_tokens_param.py` (8 parametrized).

### Verification
- `pytest test_pricing_loader.py test_max_tokens_param.py` → 17 passed.
- `mypy src/platform_layer/billing/pricing.py src/adapters/azure_openai/adapter.py` → clean (2 files).
- adapter regression (`tests/unit/adapters/azure_openai/` + `tests/integration/adapters/azure_openai/`) → 49 passed, 3 skipped (integration skips = no live Azure).

### Deferred
- 🚧 **cost_ledger None-branch unit test (checklist 2.2)**: deferred to Day 3 real-LLM. Rationale: pricing normalize is fully unit-covered (4 tests); the cost_ledger→get_llm_pricing→unit_cost>0 path is end-to-end proven by the Day-3 real Azure run (avoids a redundant heavy mock). Not dropped — covered by a stronger gate.

### Remaining
- Day 3: real-LLM Azure verify (needs user collaboration — backend restart + .env + response.model + cost_ledger unit_cost>0 + no-400 token cap).
- Day 4: full sweep (mypy src/ + full pytest + run_all) + closeout.
