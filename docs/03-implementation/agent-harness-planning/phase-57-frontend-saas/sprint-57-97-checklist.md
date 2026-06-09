# Sprint 57.97 — Checklist (Multi-model profile — cheap tier for verification; the llm_judge runs on a cheaper deployment than the main action turn)

**Plan**: [`sprint-57-97-plan.md`](./sprint-57-97-plan.md)
**Created**: 2026-06-09
**Status**: Day 0-4 done — **DRIVE-THROUGH PASS** (verification on gpt-5.4-mini, ~62% cheaper; cost_ledger-proven). Risk Class E zombie-worker hunt (D-DAY3-1) reinforced into sprint-workflow.md. Closeout complete: CHANGE-064 + 17.md §2.1 `ModelProfile` + design note 24 (8-pt gate) + retrospective Q1-Q7 + calibration (`multi-model-profile-spike` 0.55) + MEMORY subfile + CLAUDE.md lean. **Only remaining: Day-4 closeout commit + push + PR (push/PR pending user authorization).**

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> **Spike** (new-domain: first multi-model profile) → Day-4 design-note extract MANDATORY (`sprint-workflow.md §Step 5.5` 8-pt gate) → `24-multi-model-profile-design.md`. Record = CHANGE-064 + 17.md `ModelProfile` registration. Gate = full backend pytest green (NET delta) + **drive-through PASS** (verification demonstrably ran on the cheap deployment with a visible cost delta vs the strong main turn). Locked scope (AskUserQuestion 2026-06-09): abstraction = **thin `ModelProfile` value object** `{action, cheap}`; first cheap-tier phase = **verification (llm_judge)**; cheap deployment **available** → drive-through measures a real cost delta. Out: compaction/memory/thinking cheap-tier, loop threading, per-tenant policy, `ModelProfileChatClient` ABC.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: re-confirm the Explore recon anchors — `ChatClient` ABC `adapters/_base/chat_client.py:69-93` (no `model=` param) / `AzureOpenAIAdapter.__init__` `azure_openai/adapter.py:121-127` + `config.py:34-98` (deployment/pricing) / `build_real_llm_handler` `api/v1/chat/handler.py:283-297` (single `AzureOpenAIAdapter`) + the verifier factory call (~`:265`) + `make_chat_compactor` (`:364`) / `LLMJudgeVerifier.__init__` `verification/llm_judge.py:74` + call `:90` / `loop.py:1954` action call / `check_llm_sdk_leak.py:37-43` / `adapters/_base/__init__.py` re-export pattern. (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirm — (a) per-call model param absent → per-construction seam; (b) verifier + compactor accept `ChatClient` at construction → cheap routing is DI-only, ABC/loop unchanged; (c) grep-0 existing `ModelProfile`/`model_tier`/`model_registry`; (d) `ModelProfile` holding only the ABC keeps neutrality; (e) **the verification cost path** — read WHERE the verification call cost/tokens are computed (verifier-local `self._chat.get_pricing()` vs central using the loop client) + whether `VerificationResult` captures `model`. (progress.md Day-0 Prong 2)
- [x] **Prong 2.5 (observability / drift)**: confirm — **D1**: does the LLM-call Trace span (Cat 12) carry a `model`/`deployment` attribute? (drive-through visible proof) — if NOT, adding it is in-scope (small). **D2**: the cheap config build path — can `AzureOpenAIConfig` (BaseSettings) be partially overridden via explicit kwargs (cheap deployment/pricing + shared endpoint/key) without a subclass? **D3**: `build_echo_demo_handler` has no real verifier → confirm only `build_real_llm_handler` builds the profile. **D4 (drift vs recon)**: the recon said "verifier shares THIS handler's adapter ~`:265`" — confirm the exact factory name (`make_chat_verifier_registry` vs `make_chat_verifier`) + signature accepts a `ChatClient`. (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM/event-schema change (`check_event_schema_sync` unaffected). Confirm no new table/column.
- [x] **Baseline capture**: baseline = `main` HEAD (57.96 merged `1ecee053`; CI-green pytest 2283 / mypy 0/351 / run_all 10/10) — capture exact pytest number at branch creation; record NET delta after edits
- [x] **Design-note number locate**: `Glob docs/03-implementation/agent-harness-planning/2*-*.md` → **CONFIRMED 24** is the next free number (19-23 taken: 19-pause-resume / 20-iam-deep-dive / 20-subagent-child-loop / 21-iam-invites / 22-iam-credentials / 23-iam-registration) — plan drift D1 (plan v0 assumed 21) fixed
- [x] **Cheap deployment availability**: confirm the cheaper Azure deployment exists / can be created + the env var names to set (`AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` + cheap pricing) — needed BEFORE the Day-3 drive-through restart
- [x] Catalogue Day-0/Day-1 drift in progress.md; **go/no-go decision = GO** (D-DAY0-1 design-note number + D-DAY1-1 cost mechanism catalogued) (feasibility: cheap routing is DI-only; loop/ABC unchanged; the cost-attribution + span-model are the conditional bits to confirm)

### 0.2 Branch
- [x] Branch `feature/sprint-57-97-multi-model-profile` from `main` (`1ecee053`)
- [x] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — `ModelProfile` value object + cheap config + verifier rewiring (US-1/US-2/US-3)

### 1.1 The `ModelProfile` value object (US-1)
- [x] **`adapters/_base/model_profile.py`** — NEW `@dataclass(frozen=True) ModelProfile` (`action: ChatClient`, `cheap: ChatClient`); imports ONLY `ChatClient` (no SDK); seam docstring (future tiers add a field defaulting to action); file-header
  - DoD: `mypy src/ --strict` 0; `ModelProfile(action=mock, cheap=mock)` constructs + is frozen
- [x] **`adapters/_base/__init__.py`** — re-export `ModelProfile` (match the package pattern); MHist
  - DoD: `from adapters._base import ModelProfile` works; `check_llm_sdk_leak` 0

### 1.2 Cheap config + fallback (US-2)
- [x] **cheap config builder** (in `handler.py` or `azure_openai` helper — Day-0 D2 pick): read `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME`; SET → build a cheap `AzureOpenAIConfig` (shared endpoint/api_key/api_version + cheap deployment/model/pricing from `AZURE_OPENAI_CHEAP_*`, documented defaults + warning log if pricing unset); UNSET → `cheap = action` (same instance); MHist
  - DoD: unset → `profile.cheap is profile.action`; set → distinct adapter, `cheap.get_pricing()` = cheap rate
- [x] **`.env.example`** — document `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` + cheap pricing (optional; unset = fall back to main deployment)

### 1.3 Verifier wired to the cheap tier (US-3)
- [x] **`api/v1/chat/handler.py`** — build `action` + `cheap` adapters → `profile = ModelProfile(...)`; verifier factory ← `profile.cheap`; `AgentLoopImpl(chat_client=profile.action)` + `make_chat_compactor(profile.action)` + memory extraction ← `profile.action`; MHist
  - DoD: `LLMJudgeVerifier._chat is profile.cheap`; loop `_chat_client is profile.action`; cheap unset → both same instance
- [x] **mypy clean** on the backend files (full `src --strict` 0)

---

## Day 2 — Cost attribution + observability (US-4) + tests (US-1..US-4)

### 2.1 Cost attribution + span model (US-4)
- [x] **verification cost path** — RESOLVED (D-DAY1-1): cost-ledger prices via `config/llm_pricing.yml` (model-keyed); `LLMJudgeVerifier` already captures `response.model` (57.82) → cheap verifier auto-reports the cheap model name. **No cost-wiring code needed**; the verifier client's `get_pricing()` is NOT the cost source.
  - DoD: covered by builder test (cheap model name) + routing test (verifier ← cheap); $ delta = Day-3 drive-through (needs cheap+strong in llm_pricing.yml)
- [ ] **LLM-call span `model` attribute** — 🚧 deferred to Day-3: the cost-ledger sub_type (`azure_openai_<model>_verification_*`) already carries the model attribution; add a span attr only if the drive-through Trace view shows it's needed (avoid speculative work — Karpathy §2)
  - DoD: decided during Day-3 drive-through
- [x] **`loop.py` diff = 0** — confirmed (handler-only wiring; loop receives profile.action == today's client)
- [x] **`check_llm_sdk_leak` 0** — `ModelProfile` + handler wiring don't leak an SDK import outside `adapters/<provider>/` (run_all 10/10)

### 2.2 Backend tests (US-1..US-4)
- [x] **`ModelProfile` value object** — constructs with 2 mock clients; frozen/immutable; same-instance fallback shape (NEW `test_model_profile.py`, 3 tests)
- [x] **cheap-config fallback** — env unset → `profile.cheap is profile.action` (identity); set → distinct adapter, cheap deployment + model name (NEW `test_profile.py`, 3 tests; pricing dropped per D-DAY1-1)
- [x] **verifier-routing** — `build_real_llm_handler` → verifier `_chat` deployment == cheap + loop `_chat_client` deployment == strong; cheap unset → verifier shares loop's client (2 NEW tests in `test_handler.py`)
- [ ] **cost-attribution** — 🚧 MOOT under D-DAY1-1 (cost via `llm_pricing.yml` model-key, NOT client pricing); attribution covered by builder (cheap model name) + routing (verifier ← cheap); $ delta verified Day-3 drive-through
- [x] **existing 57.83 verification + handler tests green** — full pytest 2291 passed (+8), 4 skipped; 57.83 verification tests unchanged + green

---

## Day 3 — Full regression + drive-through (US-5) + CHANGE-064

### 3.1 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — 2291 passed, 4 skipped (baseline 2283 → +8); NO test deleted; 57.83 verification tests UNCHANGED + green
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src --strict` 0/353; run_all **10/10** (LLM SDK leak 0); black/isort/flake8 (changed src+tests) clean — run independently

### 3.2 Drive-through (US-5 — verification ran on the cheap deployment, visible cost delta)
- [x] **Cheap deployment configured** — `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME=gpt-5.4-mini` set in `.env`; `gpt-5.4-mini`+`gpt-5.4-nano` priced in `llm_pricing.yml`
- [x] **Clean backend restart (Risk Class E)** — 🔴 D-DAY3-1: `dev.py`/netstat/taskkill-by-port MISSED orphaned `multiprocessing.spawn` worker 38848 (child of dead 57.96 reloader 41464) serving old code+env; `Get-CimInstance Win32_Process` exposed 3 live workers, `Stop-Process -Force` 38848+18864 → only fresh 26332+56968 remain (PowerShell-verified sole :8000 owner); frontend node untouched
- [x] **Drove a chat-v2 request through real UI + real backend + real Azure** — answer rendered + verification_passed; cost_ledger: main turn = `gpt-5.2` (strong), verification = `gpt-5.4-mini` (cheap). Observed-vs-intended in progress.md Day 3
  - Evidence: `artifacts/sprint-57-97-1-chat-answer-verification.png` (pre-fix) + `sprint-57-97-2-drivethrough-pass-cheap-verification.png` (post-fix) + cost_ledger rows
- [x] **Cost-delta confirm** — verification ~$0.000301 on gpt-5.4-mini vs ~$0.00080 on gpt-5.2 (~62% cheaper); action turn cost unchanged (gpt-5.2)

### 3.3 CHANGE-064 + design note + 17.md
- [x] `claudedocs/4-changes/feature-changes/CHANGE-064-multi-model-profile-verification.md` written
- [x] **`17-cross-category-interfaces.md`** — register `ModelProfile` (provider-neutral value object pairing `ChatClient`s; owner = design note 24) — added §2.1 row

---

## Day 4 — Closeout (+ spike design note)

### 4.1 Design note (MANDATORY — spike)
- [x] **`24-multi-model-profile-design.md`** (Day-0 confirmed number) — per `claudedocs/templates/spike-design-note-template.md`; 8-point quality gate verified in retrospective.md:
  - [x] 1. Section header maps to the spike US (US-1..US-5 §2.1-§2.5)
  - [x] 2. each technical claim has file:line (`model_profile.py:46-58` / `profile.py:54-82` / `chat_client.py:69-93` / `handler.py:~479` / `llm_judge.py:97-103`)
  - [x] 3. Decision matrix (per-call vs ABC-wrapper vs thin value object vs direct injection — 4 rows)
  - [x] 4. verification command (`pytest .../test_model_profile.py` etc. + drive-through reproduce)
  - [x] 5. test fixture reference (monkeypatch.setenv / cast placeholders / artifact PNG)
  - [x] 6. Open invariants split (§4 fenced: compaction/memory/thinking cheap-tier, loop threading, per-tenant policy, cheap-judge accuracy, non-Azure, span attr)
  - [x] 7. rollback path (soft = unset `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME`; hard = revert ~30 min)
  - [x] 8. 17.md cross-ref (`ModelProfile` registered §2.1)

### 4.2 Closeout
- [x] Full validation (parent re-verified): pytest **+8** (2283→2291) / mypy 0/**353** / run_all 10/10 / 57.83 verification tests unchanged / `loop.py` diff = 0 / **drive-through PASS** (cost_ledger ~62% cheaper verification; artifacts PNG)
- [x] progress.md (Day 0-3) + retrospective.md (Q1-Q7) + **design-note 8-pt gate self-check recorded** (retro Q6)
- [x] Calibration: `multi-model-profile-spike` 0.55 (1st data point) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3` + `sprint-workflow.md §Scope-class matrix` row; carryover (compaction/memory/thinking cheap-tier / loop threading / per-tenant policy / cheap-judge accuracy / non-Azure cheap tier) → next-phase-candidates.md
- [x] MEMORY.md pointer + `project_phase57_97_multi_model_profile.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-064 + design-note 24 + 17.md registration
- [ ] commit (Day 0-N) + push + PR — Day 0-3 committed (`3dab9a08`/`454d48c2`/`0c8c5013`); Day-4 closeout commit next; **push + PR pending user authorization**
