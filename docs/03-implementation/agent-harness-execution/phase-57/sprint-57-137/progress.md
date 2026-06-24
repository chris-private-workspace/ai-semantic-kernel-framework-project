# Sprint 57.137 Progress — sandbox detect→restrict (fail-closed isolation + escape-rate spike)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-137-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-137-checklist.md)

---

## Day 0 — 2026-06-24 — Plan-vs-Repo Verify (三-prong) + Branch

**Base**: `main` HEAD `ba4c5c13` (post-#326 flip of Sprint 57.136 PR-pending→MERGED; backend code identical to 57.136 close `430f2434` — #326 was docs-only). Branch `feature/sprint-57-137-sandbox-detect-to-restrict`.

### Drift findings (三-prong)

| ID | Prong | Finding | Implication |
|----|-------|---------|-------------|
| D-denylist-shape | 2 | `risky_action_detector.py:64` — `DEFAULT_SANDBOX_PATTERNS: tuple[str, ...]` (11 patterns), used at `:104` (`re.compile(p) for p in DEFAULT_SANDBOX_PATTERNS`). | ✅ no drift; the escape harness imports this exact tuple → measurement tracks real behavior (no copy-paste drift). |
| D-default-sandbox-fallback | 2 | `sandbox.py:399` `def default_sandbox(*, image: str \| None = None)`; `:417 return DockerSandbox(...)` (try); `:426 return SubprocessSandbox()` (except branch). | ✅ no drift; `:426` is the sole fallback insertion point. The `require_isolation: bool = False` param is ADDED to the `:399` signature (current sig = `*, image` only); fail-closed branches at `:426`. |
| D-abc-shape | 2 | `sandbox.py:115 class SandboxBackend(ABC)`; only 2 impls — `:129 SubprocessSandbox`, `:219 DockerSandbox`. No `@property` / `is_structurally_*` exists yet. | ✅ no drift; `is_structurally_isolated` property lands on the ABC + both impls + the NEW `_FailClosedSandbox` (net-new, no collision). |
| D-config-grep | 2 | grep `sandbox_require_isolation\|isolation\|environment\|app_env` in `core/config/__init__.py` → **0 matches**. | ✅ no drift; `sandbox_require_isolation` is net-new (no existing isolation/ENVIRONMENT setting → no rename collision; the env gate IS the prod signal). |
| D-register-site | 2 | `_register_all.py:101 def _get_shared_sandbox()` (singleton → `default_sandbox()`); `:288 sandbox_backend=_get_shared_sandbox()` (registration call). | ✅ no drift; the config read lands in `_get_shared_sandbox()` (`get_settings().sandbox_require_isolation` → `default_sandbox(require_isolation=...)`). |
| D-docker-available | 2 | `python -c "import docker; docker.from_env().ping()"` → **DOCKER_REACHABLE**. | ✅ GREEN; the escape-harness docker-containment arm + the no-regression UI drive-through can run for REAL (DockerSandbox, like the 57.118 dt). The fail-closed refusal arm is deterministic regardless (needs NO Docker). |
| Prong 1 (paths) | 1 | EDIT targets present: `sandbox.py` / `core/config/__init__.py` / `_register_all.py` / `risky_action_detector.py` / `tests/unit/agent_harness/tools/test_sandbox.py`. NEW free: `benchmark_sandbox_escape.py`, `tests/fixtures/guardrails/sandbox_escape_cases.yaml` (dir exists w/ sibling fixtures), `tests/unit/scripts/test_benchmark_sandbox_escape.py`. `CHANGE-104` free (max=103). design note `41-*` free (max=40). | ✅ all confirmed. |
| Prong 3 (schema) | 3 | N/A — no new DB table / migration / ORM column (settings-only config; no per-tenant row). | — |

### Baselines (57.136 closeout; `ba4c5c13` backend code == `430f2434`, #326 docs-only)

pytest **2765 + 5 skip** · mypy `src` **0/374** · run_all **10/10** · wire **25** / Vitest **915** / mockup **51** = unchanged sentinels (this sprint is **backend-only**, touches no frontend/wire). Re-confirm at Day-2 full gate.

### Go/no-go

All prongs **GREEN**; **zero drift** from the plan's recon (every file:line anchor confirmed: tuple importable / sole fallback site / ABC + 2 impls / no config collision / register site / no existing property). The only "shift" is additive (the `require_isolation` param on `default_sandbox`'s existing `*, image` signature) — not a drift. Scope-shift **0%** (well under the 20% revise threshold). Docker REACHABLE → both drive-through arms run for real. **PROCEED to Day 1.** The fix composes existing machinery: the `default_sandbox()` fallback (parameterized) + the `SandboxBackend` ABC (one property) + the `benchmark_correction_hygiene.py` measurement scaffold + a settings/env gate (the 57.135 DEFAULT-OFF pattern). No new primitive, no schema, no frontend, no wire event.

**Design decisions locked (Day 0)**: (a) fail-closed = a refusing `_FailClosedSandbox` backend (tool visible + clear auditable refusal), NOT silent tool absence; (b) `SANDBOX_REQUIRE_ISOLATION` DEFAULT OFF (dev/CI keep SubprocessSandbox fallback; prod opt-in); (c) the structural decision lives in Cat 2 `default_sandbox(require_isolation=...)` + a `SandboxBackend.is_structurally_isolated` property (provider-neutral, not isinstance); (d) the regex detector is KEPT + docstring-reframed (visibility-not-boundary), behavior byte-unchanged.

---

## Day 1 — 2026-06-24 — Structural property + fail-closed resolver + config wire (US-1, US-2)

- **`sandbox.py`** (Cat 2): `SandboxBackend.is_structurally_isolated` `@property` on the ABC (default `False` = conservative; a backend must opt IN) + DockerSandbox override `True` (real container isolation) + SubprocessSandbox inherits `False` (decorative on Windows). NEW `_FailClosedSandbox(SandboxBackend)` — `is_structurally_isolated=True` (vacuous; runs nothing) + `execute()` returns a refusal `SandboxResult(exit_code=1, stderr="execution refused: structural isolation required (SANDBOX_REQUIRE_ISOLATION=true) ...", stdout="", killed_by_timeout=False)` (4 unused args `# noqa: ARG002`, mirroring SubprocessSandbox's pattern). `default_sandbox(*, require_isolation: bool = False, image=None)` — Docker reachable→DockerSandbox (unchanged); Docker unreachable + require_isolation→`_FailClosedSandbox()` + ERROR log; Docker unreachable + not require_isolation→SubprocessSandbox() + the existing WARNING (dev/CI path unchanged). MHist + Last Modified bumped.
- **`core/config/__init__.py`** (Cat 4): `sandbox_require_isolation: bool = False` (env `SANDBOX_REQUIRE_ISOLATION`, pydantic-settings auto-bind) + comment + MHist. DEFAULT OFF → dev/CI/test byte-unchanged.
- **`_register_all.py`**: `_get_shared_sandbox()` now reads `get_settings().sandbox_require_isolation` (inline import, mirrors the `:268` business_domain_mode pattern) → `default_sandbox(require_isolation=...)`. Singleton-once-per-process unchanged.
- **Tests**: `test_sandbox.py` +5 (`is_structurally_isolated` property all 3 backends · `default_sandbox` docker-reachable→Docker · unreachable+no-require→Subprocess · unreachable+require→FailClosed · `_FailClosedSandbox.execute` refusal). Used a `sys.modules["docker"]` fake (reachable/unreachable) so the paths are testable whether or not a real daemon is present (robust on CI + on the Docker-reachable dev host). NEW `test_shared_sandbox.py` +3 (`_get_shared_sandbox` threads the setting True/False + caches the singleton; autouse fixture resets the module singleton — Risk Class C).
- **Day-0 decision applied**: `_WITHHELD_PLACEHOLDER`-style dead code avoided — the conservative `False` ABC default means SubprocessSandbox needs NO explicit override (inherits correctly), keeping the change minimal (no redundant overrides).
- **Partial gate** (full test surface of every edited src file — 57.136 process lesson): `pytest test_sandbox.py + test_shared_sandbox.py + test_partial_swap.py` → **38 passed + 1 skip** (the skip = POSIX-only RLIMIT mem test on Windows) · black (1 file reformatted: test_shared_sandbox) · isort/flake8 clean (1 E501 docstring trimmed) · **mypy src 0/374** (baseline held).

---

## Day 2 — 2026-06-24 — Escape-rate measurement harness + real-Docker run (US-3) + detector reframe (US-4)

### 2.1 + 2.2 — Harness + corpus + CI-safe test

- **`scripts/benchmark_sandbox_escape.py`** (Cat 9 eval, NEW): mirrors `benchmark_correction_hygiene.py`'s scaffold (`load_cases` / `regex_screen` / `docker_contain` / `build_report` / `report_to_markdown` / `_amain` / `main` + frozen `EscapeCase`/`CaseResult`/`EscapeReport` dataclasses). **Two independent axes**: `regex_screen(code)` imports the REAL `DEFAULT_SANDBOX_PATTERNS` (the DETECT axis); `docker_contain(code, backend)` runs the snippet under the backend + checks the `__ESCAPED__` sentinel is absent (the RESTRICT axis). `main()` dogfoods the 57.137 property — the docker arm runs iff `default_sandbox().is_structurally_isolated`, else regex-only + a "gate-only, NOT a containment claim" warning.
- **`tests/fixtures/guardrails/sandbox_escape_cases.yaml`** (NEW): 10 host-EGRESS attempts via diverse primitives (network egress = the cleanest single structural boundary, the one SubprocessSandbox most clearly fails). 4 the deny-list catches (socket literal / socket aliased / `__import__('soc'+'ket')` / subprocess) + 6 it MISSES (urllib / http.client / `importlib.import_module('soc'+'ket')` / asyncio.open_connection / ftplib / smtplib). Each prints `__ESCAPED__` only if egress reached out.
- **`tests/unit/scripts/test_benchmark_sandbox_escape.py`** (NEW, +13): importlib-load idiom (avoids `tests.unit.scripts` shadow). **Key invariant test** `test_regex_screen_matches_corpus_should_match`: for every corpus case, `regex_screen(code) is case.should_match` against the REAL patterns — keeps the corpus honest (a pattern change that breaks a claim fails loudly). + load_cases (schema/dup/non-list) · regex catches/misses known primitives · `docker_contain` sentinel detection (fake backend) · build_report (escape_rate / containment_rate / docker-skipped→None). 13 passed.

### 2.3 — Real-Docker escape run (US-3) — the spike's core evidence

Ran `RUN_DOCKER_INTEGRATION=1 python scripts/benchmark_sandbox_escape.py` against the real Docker daemon (DockerSandbox, image `ipa-v2-sandbox:latest`), 10 cases. Report → `artifacts/sandbox_escape_report.{md,json}` (`benchmark_reports/` gitignored → copied to artifacts as evidence).

| axis | result |
|------|--------|
| regex caught (deny-list hit) | 4/10 |
| regex MISSED (blocklist gap) | 6/10 |
| **regex_escape_rate** | **60.00%** |
| docker contained (structural) | **10/10** |
| **docker_containment_rate** | **100.00%** |

**Verdict: detect→restrict confirmed.** The regex deny-list MISSES 60% of host-egress primitives (urllib / http.client / importlib-concat / asyncio / ftplib / smtplib — none are enumerated), while DockerSandbox's `network none` structurally contains **all 10** regardless of primitive. So the regex is **redundant for containment** under Docker → it must NOT be the primary boundary; the structural sandbox must be mandatory (the `SANDBOX_REQUIRE_ISOLATION` fail-closed gate, Day 1) and the regex stays only as ESCALATE-for-visibility.

**Honesty note**: the measured boundary is NETWORK egress (Docker's clearest, most-testable structural guarantee + the one SubprocessSandbox most clearly fails). The other Docker guarantees (read-only fs / cap-drop / non-root / no bind mounts) are documented (sandbox.py docstring) but not each independently benchmarked this sprint — the network result is sufficient to settle the detect→restrict thesis. Harness is permanent + re-runnable on a broader corpus.

### 2.4 — Detector reframe (US-4)

- **`risky_action_detector.py`**: added a "Security model (Sprint 57.137 reframe)" paragraph to the module docstring (ESCALATE-for-VISIBILITY, NOT the boundary; cites the 60% escape / 100% containment numbers + the cat-and-mouse history) + a NOTE on the `DEFAULT_SANDBOX_PATTERNS` section comment ("intentionally INCOMPLETE — do NOT pattern-chase") + MHist. **`check()` / `DEFAULT_SANDBOX_PATTERNS` / the ESCALATE action are byte-unchanged** → `pytest -k risky` 23 passed (no behavior regression).

### 2.x — Full gate

- **v2 lints** (`python scripts/lint/run_all.py`, cwd=root): **10/10 green** (incl. check_llm_sdk_leak — the harness has no LLM; uses the Cat 2 SandboxBackend ABC).
- **mypy src**: **0/374** (baseline held).
- **risky detector regression**: 23 passed (docstring-only edit, no behavior change).
- **pytest full suite**: **2786 passed + 5 skip** (baseline 2765 + 21 new: 8 Day-1 sandbox/shared_sandbox + 13 Day-2 escape; the 5 skips incl. the POSIX-only RLIMIT mem test). No regressions.
- Frontend (Vitest 915 / mockup 51 / npm): unchanged sentinels — backend-only sprint.

---

## Day 3 — 2026-06-24 — Drive-through (US-5): backend runtime + UI ("兩者結合")

### Clean restart (Risk Class E)

Backend was NOT running (no python.exe, port 8000 free, no orphan spawn-worker — the 57.97 trap). Started a FRESH single-process uvicorn (`api.main:app --app-dir src`, NO `--reload` → no orphan risk; normal config: `SANDBOX_REQUIRE_ISOLATION` unset = default False, real Docker; api.main lifespan loaded root `.env`). Startup log confirmed DB/Redis/Azure/pricing wired + "startup complete" + `transcript retention job disabled (default off)`.

### Backend runtime drive-through (REAL `_get_shared_sandbox` → `make_python_sandbox_handler` path) — PASS

A driver (scratchpad, NOT committed) exercises the REAL chat python_sandbox wiring under both configs:

| arm | config | backend resolved | python_sandbox result |
|-----|--------|------------------|----------------------|
| **A fail-closed** | `SANDBOX_REQUIRE_ISOLATION=true` + Docker unreachable (`DOCKER_HOST=tcp://127.0.0.1:1`) | `_FailClosedSandbox` (isolated=True, vacuous) | **REFUSED** — stdout empty, exit_code=1, stderr "execution refused: structural isolation required (SANDBOX_REQUIRE_ISOLATION=true) ..."; code NOT run. ERROR log "failing closed: python_sandbox will REFUSE to run" fired. |
| **B no-regression** | require_isolation off + real Docker | `DockerSandbox` (isolated=True) | **RAN** — `print(2+2)` → stdout="4\n", exit_code=0, 0.375s |

This is the strongest deterministic evidence — the ACTUAL `_get_shared_sandbox()` (reads the setting) → `default_sandbox(require_isolation=...)` → `make_python_sandbox_handler` path, end-to-end, with real Azure-independent tool execution.

### UI drive-through (chat-v2 browser, real Azure gpt-5.2) — PASS (no-regression, user-facing)

Logged in via dev-login (jamie@acme.com · operator · acme-prod), drove chat-v2 (real_llm, gpt-5.2):

- **Prompt**: "Use the python_sandbox tool to compute 31337 * 1337 and print the result."
- **Turn 1**: LLM → `tool_call_request python_sandbox` `{"code": "print(31337 * 1337)"}` → `approval_requested risk=MEDIUM` → HITL pause (policy always_ask; the 57.106 risky-action / HITL flow). `loop_end stop=awaiting_approval`.
- **Approve & continue** clicked → python_sandbox executed on **real DockerSandbox** → tool result → Turn 2: agent final **answer "41897569"** (= 31337 × 1337, correct) rendered in the message thread + Inspector "BLOCK SEQUENCE: answer 41897569 / verification claim verified · llm_judge" → `verification_passed (llm_judge score=0.99)` → `loop_end stop=end_turn`. tokens cached 1,664 / cache_hit 69% / model gpt-5.2.
- Screenshot: `artifacts/dt-57137-no-regression-python-sandbox.jpeg`.

**Observed vs intended**: intended = python_sandbox still runs end-to-end after the 57.137 wiring change (default OFF → DockerSandbox normal path); observed = exactly that — tool ran on real Docker, correct result rendered, verification passed. My `_get_shared_sandbox`/`default_sandbox` change did NOT break the live tool path (no-regression confirmed user-facing).

### Drive-through verdict

- **Fail-closed** (require_isolation + Docker unreachable → refusal, code not run): backend runtime PASS (deterministic, real wiring), corroborated by the Day-1 8 unit tests + the escape harness's `is_structurally_isolated` dogfood.
- **No-regression** (normal Docker → python_sandbox runs): UI PASS (real chat-v2 + real Azure + real DockerSandbox → "41897569" rendered + verification passed).
- **Why fail-closed is backend-runtime not UI**: forcing Docker-unreachable in a live UI is an artificial setup; the deterministic backend-runtime drive-through exercises the identical production wiring (`_get_shared_sandbox` reads the setting) end-to-end. Same honest "兩者結合" pattern accepted for 57.136.
- Backend stopped + port 8000 confirmed free at Day-3 close (no orphan python).
