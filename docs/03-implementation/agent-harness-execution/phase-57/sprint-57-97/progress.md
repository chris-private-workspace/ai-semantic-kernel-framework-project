# Sprint 57.97 Progress — Multi-model profile (cheap tier for verification)

**Plan**: [`sprint-57-97-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-97-plan.md)
**Checklist**: [`sprint-57-97-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-97-checklist.md)
**Branch**: `feature/sprint-57-97-multi-model-profile` (from `main` `1ecee053`)

---

## Day 0 — 2026-06-09 — Plan-vs-Repo Verify + Branch

### Three-prong Day-0 verify (Explore recon + targeted reads)

- **Prong 1 (path)** — confirmed: `ChatClient` ABC `adapters/_base/chat_client.py:69-93` has NO `model=` param (model fixed at adapter `__init__`); `AzureOpenAIAdapter.__init__(config)` `azure_openai/adapter.py:121`; `build_real_llm_handler` `handler.py:297` builds ONE `AzureOpenAIAdapter(AzureOpenAIConfig())`; verifier factory `make_chat_verifier_registry(chat_client, template)` `handler.py:479`; compactor `make_chat_compactor(chat_client)` `:364`; `LLMJudgeVerifier.__init__(chat_client=)` `llm_judge.py:74`; `adapters/_base/__init__.py` re-export pattern (import + `__all__`).
- **Prong 2 (content)** — confirmed: verifier + compactor + memory accept a `ChatClient` at construction → cheap routing is DI-only (ABC/loop unchanged); grep-0 existing `ModelProfile`/`model_tier`/`model_registry`. **KEY**: `llm_judge.py:97-103` (Sprint 57.82 B-8) already captures `response.usage` + `response.model` into `VerificationResult` → a cheap verifier auto-reports the cheap model name for cost attribution.
- **Prong 2.5 (observability / drift)** — see Drift findings below (D-DAY0-1 design-note number; D-DAY1-1 cost mechanism surfaced Day-1).
- **Prong 3 (schema)** — N/A: no DB/migration/ORM/event-schema change.
- **Baseline**: `main` HEAD `1ecee053` (57.96 merged) — CI-green mypy 0/351 · pytest 2283 · run_all 10/10. Post-edit: mypy 0/**353** (+2 new modules).
- **Cheap deployment availability**: user confirmed a cheaper Azure deployment is available / can be created (AskUserQuestion 2026-06-09) → Day-3 drive-through can measure a real cost delta.
- **go/no-go = GO** — spike confirmed thin (DI-only verifier swap; cost attribution model-name already captured by 57.82; loop/ABC unchanged).

### Drift findings

- **D-DAY0-1 (design-note number)** — plan v0 assumed `21-multi-model-profile-design.md`; `Glob` showed **19-23 all taken** (19-pause-resume / 20-iam-deep-dive / 20-subagent-child-loop / 21-iam-invites / 22-iam-credentials / 23-iam-registration; note: a pre-existing duplicate `20-`). → use **24-multi-model-profile-design.md**. Plan + checklist fixed Day-0.
- **D-DAY1-1 (cost mechanism — refines plan §3.2/§3.4)** — the cost-ledger does NOT price via the adapter's `get_pricing()`. `cost_ledger.record_llm_call(provider, model, tokens, sub_type_suffix)` prices via `config/llm_pricing.yml` (`PricingLoader.get_llm_pricing(provider, model)`, model-keyed, Azure version-suffix stripped) and writes a sub_type `azure_openai_<model>_verification_input/output` (the `_verification` suffix is Sprint 57.82). **Consequences**: (a) the `AZURE_OPENAI_CHEAP_PRICING_*` env vars the plan proposed feed only the (vestigial) adapter config pricing — the cost-ledger ignores them (it ignores the strong tier's config pricing too) → they were a footgun → **dropped** (Karpathy §2). (b) The visible cost-ledger proof is the **model-attribution difference** in the sub_type (`_<cheap>_verification_*` vs `_<strong>_*`) — robust, no pricing dependency. (c) For a $ delta, BOTH the cheap and the strong model must be priced in `config/llm_pricing.yml`; per the FIX-022 §6.2 caveat the strong model may currently be unpriced ($0 rows) → Day-3 must align the yml. **Drive-through reframed** accordingly (model-attribution primary; $ delta secondary, needs yml).

### Branch
- Branch `feature/sprint-57-97-multi-model-profile` created from `main` `1ecee053`. Plan + checklist + this progress committed (Day-0 commit).

---

## Day 1 — 2026-06-09 — ModelProfile + cheap builder + verifier rewiring (US-1/US-2/US-3)

### Code (5 files)
- **`adapters/_base/model_profile.py` (NEW)** — `@dataclass(frozen=True) ModelProfile{action, cheap}`; provider-neutral (imports only `ChatClient`, no SDK); seam docstring.
- **`adapters/_base/__init__.py`** — re-export `ModelProfile` (import + `__all__` + single-source-map docstring).
- **`adapters/azure_openai/profile.py` (NEW)** — `build_azure_model_profile(strong_client)`: reads `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME`; set → 2nd `AzureOpenAIAdapter` (shared endpoint/key from env, overridden deployment + model name via explicit kwargs); unset → `cheap is strong_client` (byte-identical). Cost-attribution note in docstring (yml-keyed, not config pricing). **Simplified after D-DAY1-1**: dropped the cheap pricing env + `_env_float` + warning (footgun — cost-ledger uses yml).
- **`api/v1/chat/handler.py`** — `profile = build_azure_model_profile(chat_client)`; verifier ← `profile.cheap` (`make_chat_verifier_registry(profile.cheap, ...)`); loop / compactor / prompt / subagents keep `chat_client` (== profile.action). MHist + comment. `loop.py` UNCHANGED.
- **`.env.example`** — documented optional `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` + `AZURE_OPENAI_CHEAP_MODEL_NAME` (unset = fall back; cost via `config/llm_pricing.yml`).

### Validation (Day-1 partial — code-complete + type-clean; tests are Day-2)
- **mypy `src --strict` 0/353** (+2 new modules) ✅
- Tests (Day-2): `ModelProfile` value object / `build_azure_model_profile` fallback (unset→identity) + set (cheap config) / verifier-routing (judge ← cheap, loop ← action) / cost-attribution. Test location confirmed: `backend/tests/unit/adapters/_base/` (new) + `backend/tests/unit/adapters/azure_openai/`.
- `run_all` lints + full pytest + drive-through → Day-2/Day-3.

### Notes
- The wiring is honest-minimal: only the verifier moves to `profile.cheap`; the user-facing action turn + compaction + subagents stay strong. `ModelProfile` is constructed + consumed in `handler.py` (not threaded into the loop) — the seam is documented for future phases (compaction/thinking cheap-tier).
- **NOT claimed verified** — Day-1 is code-complete + mypy-clean ONLY. Behavioral tests (Day-2) + drive-through (Day-3, needs the cheap deployment + `llm_pricing.yml` alignment) pending.

### Remaining (as of Day 1)
- Day 2: backend tests (ModelProfile + builder + verifier-routing + cost-attribution) + run_all + full pytest.
- Day 3: align `config/llm_pricing.yml` (cheap + strong model) → drive-through (real UI + cheap deployment → verification sub_type = cheap model + $ delta).
- Day 4: design note `24-multi-model-profile-design.md` (8-pt gate) + CHANGE-064 + 17.md + closeout.

---

## Day 2 — 2026-06-09 — Tests + cost-attribution resolution + full gate (US-1..US-4)

### Tests (8 new, all green)
- `tests/unit/adapters/_base/test_model_profile.py` (3) — pairs action/cheap; frozen (reassign raises); same-instance fallback shape.
- `tests/unit/adapters/azure_openai/test_profile.py` (3) — unset → cheap IS action (identity); set → distinct cheap `AzureOpenAIAdapter` (cheap deployment + model name); model_name defaults to deployment when `AZURE_OPENAI_CHEAP_MODEL_NAME` unset.
- `tests/unit/api/v1/chat/test_handler.py` (+2) — `build_real_llm_handler`: verifier `_chat` deployment == cheap + loop `_chat_client` deployment == strong; cheap unset → verifier shares the loop's (action) client.

### Cost-attribution resolution (D-DAY1-1 follow-through)
- The plan's "verifier uses `self._chat.get_pricing()`" assumption was WRONG. The cost-ledger prices via `config/llm_pricing.yml` (model-keyed) and `LLMJudgeVerifier` ALREADY captures `response.model` (Sprint 57.82) → routing the verifier to the cheap client makes the cheap MODEL NAME flow to the cost-ledger automatically. **No cost-wiring code needed.** The dedicated "cheap-priced client → cheap cost" unit test is moot (client pricing isn't the cost source); attribution is covered by the builder test (cheap model name) + the routing test (verifier ← cheap). The $ delta proof = Day-3 drive-through (needs the cheap + strong model priced in `llm_pricing.yml`).
- LLM-call span `model` attribute (plan §3.4 conditional): **deferred to Day-3** — the cost-ledger sub_type (`azure_openai_<model>_verification_*`) already carries the model attribution; add a span attr only if the drive-through shows the Trace view needs it.

### Full gate (GREEN)
- mypy `src --strict` **0/353** (the Day-2 E501 fixes were comment/docstring-only; no logic change).
- `run_all` **10/10** (`check_llm_sdk_leak` 0 — ModelProfile holds only the ABC; `check_cross_category_import` OK; `check_event_schema_sync` unaffected).
- black / isort / flake8 (changed src + tests) clean — 3 E501 trimmed (profile.py Purpose + handler MHist + test docstring).
- full backend pytest **2291 passed, 4 skipped** (baseline 2283 → **+8** new, 0 deletions; 57.83 verification tests unchanged + green).
- `loop.py` diff = 0.

### Remaining (after Day 2)
- Day 3: align `config/llm_pricing.yml` (cheap + strong model) + drive-through (real UI + cheap deployment → verification recorded at the cheap model + $ delta). **Needs the cheap deployment name from the user.**
- Day 4: design note `24-multi-model-profile-design.md` (8-pt gate) + CHANGE-064 + 17.md + closeout.

---

## Day 3 — 2026-06-09 — Config alignment + DRIVE-THROUGH PASS (US-5)

### Config (user-provided)
- User: cheap deployment = **`gpt-5.4-mini`** (also has `gpt-5.4-nano`, same API key); strong = `gpt-5.2` (confirmed in `.env`, already priced 1.75/14.00).
- `config/llm_pricing.yml` — added `gpt-5.4-mini` (0.75 / 4.50 / 0.08) + `gpt-5.4-nano` (0.20 / 0.25 / 0.02) under `azure_openai`; `last_updated` → 2026-06-09. (FIX-022 §6.2 "gpt-5.2 unpriced" caveat already stale — yml prices gpt-5.2.)
- `.env` (root) — appended `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME=gpt-5.4-mini` + `AZURE_OPENAI_CHEAP_MODEL_NAME=gpt-5.4-mini`.

### 🔴 Drive-through finding D-DAY3-1 (Risk Class E — orphaned `multiprocessing.spawn` worker) — REINFORCES the rule
- **Symptom**: first 2 drive-through chats (France, Japan) recorded the verification at `gpt-5.2` (strong), NOT `gpt-5.4-mini` — the cheap routing appeared dead, despite `dev.py restart` reporting a fresh PID.
- **Root cause (NOT a code bug)**: a reproduce-script proved the code is correct (`build_azure_model_profile` builds a `gpt-5.4-mini` cheap client when the .env is loaded; `cheap IS action? False`). The real cause was **multiple orphaned `--reload` worker processes** sharing :8000 via SO_REUSEADDR: PID 38848 (a `multiprocessing.spawn` child of the long-dead 57.96 reloader 41464) was STILL ALIVE serving requests with **old code + old .env** (no cheap tier). `dev.py stop` + netstat + `taskkill /PID` all attributed the socket to the DEAD parent (41464) and missed the live orphaned child — the worker's cmdline is `python -c "from multiprocessing..."` (no "uvicorn"), so port-owner-based kills never found it. Enumerating `Win32_Process Name='python.exe'` by PID/PPID/StartTime exposed 3 live workers (38848 ← dead 41464 / 18864 ← dead 44412 / 56968 ← live 26332); the oldest (38848) won the requests.
- **Fix**: `Stop-Process -Force` the orphaned workers (38848 + 18864) directly by PID → only the fresh 26332 reloader + 56968 worker remained → :8000 served exclusively by the fresh backend.
- **Lesson (Risk Class E reinforcement)**: a clean restart must verify the **live serving process**, not the port-owner PID. `dev.py`/netstat/taskkill by port can leave orphaned `multiprocessing.spawn` workers from prior `--reload` sessions alive. The reliable check: `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` → inspect PID/PPID/StartTime → kill any worker whose parent is dead or whose StartTime predates the current restart. (To fold into `sprint-workflow.md §Risk Class E` + memory at closeout.)

### Drive-through PASS (real UI + real backend + real Azure)
- Fresh backend PID **26332** (reloader) + 56968 (worker), sole live :8000 listener (PowerShell-verified). chat-v2, jamie@acme-prod, real_llm.
- Prompt "Name three primary colors…" → answer rendered + `verification_passed score≈0.98`.
- **cost_ledger (this session, newest 4 rows)** — the proof:
  - `azure_openai_gpt-5.2-2025-12-11_input` qty 2101 → $0.003677 / `_output` qty 15 → $0.000210  (main turn = STRONG)
  - `azure_openai_gpt-5.4-mini-2026-03-17_verification_input` qty 234 → $0.000176 / `_output` qty 28 → $0.000126  (verification = **CHEAP**)
  - The model-version suffix (`-2026-03-17`) is stripped by `PricingLoader` → priced off the `gpt-5.4-mini` yml key (0.75/4.50).
- **$ delta**: the verification call cost ~$0.000301 on gpt-5.4-mini vs ~$0.00080 if it had run on gpt-5.2 → **~62% cheaper for the per-request verification**, while the user-facing action turn stays on gpt-5.2 (unchanged). Real, visible cost saving.
- Evidence: `artifacts/sprint-57-97-1-chat-answer-verification.png` (pre-fix France run) + `artifacts/sprint-57-97-2-drivethrough-pass-cheap-verification.png` (post-fix) + the cost_ledger rows above.
- The plan §3.4 "LLM-call span model attribute" was correctly DEFERRED — the cost-ledger sub_type model-attribution (`_gpt-5.4-mini_verification_*`) is sufficient visible proof; no span change needed.

### Remaining (after Day 3)
- Day 4: design note `24-multi-model-profile-design.md` (8-pt gate) + CHANGE-064 + 17.md `ModelProfile` registration + calibration + MEMORY subfile + CLAUDE.md lean + Risk-Class-E reinforcement fold-in + push/PR (user-authorized).

---

## Day 4 — 2026-06-10 — Closeout

All closeout artifacts written (docs-only; no code change — the code gate was green Day 2/3, `loop.py` diff = 0):
- **CHANGE-064** (`claudedocs/4-changes/feature-changes/CHANGE-064-multi-model-profile-verification.md`) — change record.
- **Design note `24-multi-model-profile-design.md`** — spike 8-pt quality gate ✅ (verified-ratio ≥95%; Decision Matrix 4-row; every claim file:line-anchored; Open Invariants fenced; rollback path; 17.md cross-ref).
- **`17-cross-category-interfaces.md` §2.1** — registered `ModelProfile` (value object WRAPS `ChatClient`; ABC unchanged; owner = design note 24).
- **retrospective.md** — Q1-Q7; calibration ratio actual/committed ≈ 0.93 IN band; design-note 8-pt self-check (Q6); anti-pattern audit (Q5).
- **Calibration**: NEW class `multi-model-profile-spike` 0.55 (1st data point) + `agent_factor` 1.0 (parent-direct) → `sprint-workflow.md §Scope-class matrix` row + `calibration-log.md §3` entry.
- **Risk Class E reinforcement** (D-DAY3-1 orphaned `multiprocessing.spawn` worker) folded into `sprint-workflow.md §Common Risk Classes Risk Class E` (verify the LIVE serving process via `Get-CimInstance Win32_Process` by PID/PPID/StartTime, not the port-owner PID).
- **MEMORY**: `project_phase57_97_multi_model_profile.md` subfile + MEMORY.md pointer (top of Recent Sprints).
- **CLAUDE.md lean**: Current Sprint row → 57.97 + Last Updated footer (no prev-sprint history rows added, per §Sprint Closeout policy).
- **next-phase-candidates.md**: 57.97 carryover section (compaction/memory/thinking cheap-tier / loop threading / per-tenant policy / cheap-judge accuracy / non-Azure builder).

### Remaining
- Day-4 closeout commit (docs + 17.md + calibration + memory + checklist/progress) — then **push + PR pending user authorization**.
