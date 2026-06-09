# CHANGE-064: Multi-model profile — route verification (llm_judge) to a cheap tier

**Change Date**: 2026-06-10
**Change Type**: New Feature (adapters-layer seam + Cat 10/12 cost routing)
**Sprint**: 57.97
**Scope**: adapters/_base + adapters/azure_openai + api/v1/chat (× Cat 10 Verification × Cat 12 Observability)
**Status**: ✅ Completed — DRIVE-THROUGH PASS

## Change Summary

Today one `ChatClient` (Azure, single deployment) served every phase — the user-facing main turn AND the cheap-by-nature phases (verification / compaction / memory). This change introduces a thin, provider-neutral `ModelProfile{action, cheap}` value object pairing two pre-built `ChatClient`s by role, and routes the **per-request verification (Cat 10 `LLMJudgeVerifier`, default-ON since 57.83)** onto `profile.cheap` (a cheaper Azure deployment) while the main action turn (`loop.py:1954`) + compaction + prompt building + subagents keep `profile.action` (strong). Net: a real per-request cost saving on verification with the user-facing answer quality unchanged.

## Change Reason

The agent-harness-cc-parity assessment (`claudedocs/5-status/agent-harness-cc-parity-20260607.md` §4 C-class + 圖 D 波次 1) ranked **multi-model profile** the single highest-ROI untouched parity gap (cheap phases overpaid by running on the strong model). The provider-neutral `ChatClient` ABC already paved the road — the seam was a construction-time injection, not an ABC change.

## Detailed Changes

### NEW `ModelProfile` value object (US-1)
- `backend/src/adapters/_base/model_profile.py` — `@dataclass(frozen=True) ModelProfile{action: ChatClient, cheap: ChatClient}` (`:46-58`). Provider-neutral (imports ONLY the `ChatClient` ABC; no SDK). The ABC fixes the model at construction (`chat()`/`stream()` have no `model=` param — `chat_client.py:69-93`), so multi-model = "build N clients upfront, pick by phase"; `ModelProfile` IS the picker. NO per-call dispatch method (YAGNI — callers read `.action`/`.cheap`).
- `backend/src/adapters/_base/__init__.py` — re-export `ModelProfile` (import + `__all__` + single-source-map docstring).

### Azure cheap-tier builder + fallback (US-2)
- `backend/src/adapters/azure_openai/profile.py` (NEW) — `build_azure_model_profile(strong_client)` (`:54-82`): reads `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME`; **unset → `cheap IS strong_client`** (same instance, byte-identical behavior + cost); **set → a 2nd `AzureOpenAIAdapter`** reusing the shared endpoint/key/api_version (loaded from env by BaseSettings) with the cheap deployment + model name overridden via explicit kwargs.
- `.env.example` — documented optional `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` + `AZURE_OPENAI_CHEAP_MODEL_NAME` (unset = fall back; cost priced via `config/llm_pricing.yml`).

### Verification wired to the cheap tier (US-3)
- `backend/src/api/v1/chat/handler.py` — `profile = build_azure_model_profile(chat_client)`; verifier ← `profile.cheap` (`make_chat_verifier_registry(profile.cheap, ...)`, ~`:479`); loop / compactor / prompt / subagents keep `chat_client` (== `profile.action`). **`loop.py` diff = 0.**

### Cost attribution + pricing (US-4)
- The cost-ledger (`platform_layer/billing/cost_ledger.py`) prices an LLM call via `config/llm_pricing.yml` keyed by `(provider, model)` — NOT the adapter config pricing. `LLMJudgeVerifier` already captures `response.model` (Sprint 57.82, `llm_judge.py:97-103`), so routing the verifier to the cheap client makes the cheap MODEL NAME flow to the cost-ledger automatically — **no cost-wiring code needed**.
- `backend/config/llm_pricing.yml` — added `gpt-5.4-mini` (0.75 / 4.50 / 0.08) + `gpt-5.4-nano` (0.20 / 0.25 / 0.02) under `azure_openai`; `last_updated` → 2026-06-09. (Pricing values user-provided.)

## Modified Files List

| File | Change |
|------|--------|
| `backend/src/adapters/_base/model_profile.py` | NEW — `ModelProfile{action, cheap}` frozen dataclass |
| `backend/src/adapters/_base/__init__.py` | EDIT — re-export `ModelProfile` |
| `backend/src/adapters/azure_openai/profile.py` | NEW — `build_azure_model_profile` (cheap builder + fallback) |
| `backend/src/api/v1/chat/handler.py` | EDIT — build profile; verifier ← `profile.cheap`; loop/compactor ← `profile.action` |
| `backend/config/llm_pricing.yml` | EDIT — add `gpt-5.4-mini` + `gpt-5.4-nano` pricing |
| `.env.example` | EDIT — document optional cheap-tier env vars |
| `backend/tests/unit/adapters/_base/test_model_profile.py` | NEW — 3 tests (pairs / frozen / same-instance) |
| `backend/tests/unit/adapters/azure_openai/test_profile.py` | NEW — 3 tests (unset→identity / set→distinct / model_name default) |
| `backend/tests/unit/api/v1/chat/test_handler.py` | EDIT — +2 tests (verifier→cheap & loop→strong / cheap-unset→shared) |

**NOT changed**: `loop.py` (diff = 0 — receives `profile.action`) · `ChatClient` ABC (`chat_client.py` — WRAPPED, not changed) · DB/migration · event schema · frontend.

## Test Checklist
- [x] mypy `src --strict` **0/353** (+2 new modules)
- [x] `run_all` **10/10** (`check_llm_sdk_leak` 0 — `ModelProfile` holds only the ABC)
- [x] `black` / `isort` / `flake8` (changed src + tests) clean
- [x] full backend pytest **2291 passed, 4 skipped** (baseline 2283 → **+8** new, 0 deletions; 57.83 verification tests unchanged + green)
- [x] `loop.py` diff = 0

## Verification (Drive-Through PASS — real UI + real backend + real Azure)
Fresh backend (sole live :8000 listener, PowerShell-verified — see D-DAY3-1 below), chat-v2, jamie@acme-prod, real_llm. Prompt "Name three primary colors…" → answer rendered + `verification_passed score≈0.98`. The cost_ledger proof (newest 4 rows this session):
- `azure_openai_gpt-5.2-2025-12-11_input` qty 2101 → $0.003677 / `_output` qty 15 → $0.000210  (main turn = **STRONG**)
- `azure_openai_gpt-5.4-mini-2026-03-17_verification_input` qty 234 → $0.000176 / `_output` qty 28 → $0.000126  (verification = **CHEAP**)

**$ delta**: verification ~$0.000301 on gpt-5.4-mini vs ~$0.00080 if it had run on gpt-5.2 → **~62% cheaper per-request verification**; the action turn stays strong. Evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-97/artifacts/sprint-57-97-2-drivethrough-pass-cheap-verification.png`.

### D-DAY3-1 (Risk Class E reinforcement)
The first 2 drive-through chats recorded verification at `gpt-5.2` despite a `dev.py restart` reporting a fresh PID. Root cause was NOT a code bug (a reproduce-script proved the builder builds a `gpt-5.4-mini` cheap client): an **orphaned `multiprocessing.spawn` worker** (PID 38848, a child of the long-dead 57.96 reloader 41464) was still alive serving :8000 with old code + old `.env`. `dev.py`/netstat/`taskkill /PID` attributed the socket to the dead parent and missed the live orphaned child (its cmdline lacks "uvicorn"). `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` by PID/PPID/StartTime exposed it; `Stop-Process -Force` on the orphans fixed it. **Lesson folded into `.claude/rules/sprint-workflow.md §Risk Class E`.**

## Impact
Backend-only seam + cost routing. The action turn (user-facing) is NEVER cheap → answer quality preserved. Unset cheap env = byte-identical to 57.96 (safe to ship without a 2nd deployment). The seam is documented in `24-multi-model-profile-design.md` for future cheap-tier phases (compaction / memory / thinking) to add a field + read it without a new injection site.

## References
- Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-97-plan.md`
- Design note: `docs/03-implementation/agent-harness-planning/24-multi-model-profile-design.md`
- Retrospective: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-97/retrospective.md`
- 17.md `ModelProfile` registration: §2.1
