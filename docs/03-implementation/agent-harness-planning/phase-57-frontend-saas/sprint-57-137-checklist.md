# Sprint 57.137 — Checklist (sandbox detect→restrict: fail-closed isolation + escape-rate spike)

[Plan](./sprint-57-137-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `ba4c5c13`)
- [x] **Prong 1 — path verify**: `sandbox.py` / `core/config/__init__.py` / `_register_all.py` / `risky_action_detector.py` / `tests/unit/agent_harness/tools/test_sandbox.py` exist; NEW files free (`benchmark_sandbox_escape.py`, `sandbox_escape_cases.yaml`, `test_benchmark_sandbox_escape.py`); `CHANGE-104` free; design note `41-*` free → ✅ all confirmed (EDIT targets present; 3 NEW free; fixtures/guardrails/ dir exists w/ siblings; CHANGE max=103; design-note max=40)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-denylist-shape** — ✅ `DEFAULT_SANDBOX_PATTERNS: tuple[str, ...]` at `risky_action_detector.py:64`, used `:104` → harness imports it (no copy drift)
  - [x] **D-default-sandbox-fallback** — ✅ `sandbox.py:399 def default_sandbox(*, image)`; `:417 return DockerSandbox`; `:426 return SubprocessSandbox()` (sole fallback site; `require_isolation` param ADDED to `:399` sig)
  - [x] **D-abc-shape** — ✅ `SandboxBackend(ABC)` `:115`; only 2 impls (`SubprocessSandbox :129`, `DockerSandbox :219`); no existing `@property`/`is_structurally` → net-new on 2 impls + `_FailClosedSandbox`
  - [x] **D-config-grep** — ✅ 0 matches for `sandbox_require_isolation\|isolation\|environment\|app_env` → net-new, no collision
  - [x] **D-register-site** — ✅ `_get_shared_sandbox()` `_register_all.py:101` + `sandbox_backend=_get_shared_sandbox()` `:288`
  - [x] **D-docker-available** — ✅ `python -c "import docker; docker.from_env().ping()"` → **DOCKER_REACHABLE** → docker arm + no-regression dt run for REAL; fail-closed arm deterministic regardless
- [x] **Prong 3 — schema verify**: N/A (no new DB table / migration / ORM column)
- [x] **D-baselines** — pytest 2765+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/374 · run_all 10/10 → recorded (57.136 closeout; `ba4c5c13` backend == `430f2434`, #326 docs-only)
- [x] **Catalog drift** — ✅ progress.md Day-0 table (7 D-rows + implication)
- [x] **Go/no-go** — ✅ all GREEN, **zero drift**, scope-shift 0% → PROCEED to Day 1

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-137-sandbox-detect-to-restrict` (from `main` `ba4c5c13`) → ✅ on branch

---

## Day 1 — Structural property + fail-closed resolver + config wire (US-1, US-2)

### 1.1 `is_structurally_isolated` property + `_FailClosedSandbox` — `sandbox.py`
- [x] **property on ABC + 2 impls + fail-closed backend**
  - DoD: `SandboxBackend.is_structurally_isolated` property; DockerSandbox→True, SubprocessSandbox→False; `_FailClosedSandbox(SandboxBackend)` with `is_structurally_isolated=True` (vacuous) + `execute()` returning a refusal `SandboxResult` (exit_code=1, explanatory stderr, runs nothing)
  - ✅ done: ABC property default `False` (conservative opt-in) + DockerSandbox→True + Subprocess inherits False + `_FailClosedSandbox` (True + refusal execute, 4 unused-args `# noqa: ARG002`)

### 1.2 `default_sandbox(require_isolation=...)` fail-closed
- [x] **fail-closed branch**
  - DoD: `default_sandbox(*, require_isolation: bool = False, image=None)`; Docker reachable→DockerSandbox (unchanged); Docker unreachable + require_isolation→`_FailClosedSandbox()` + ERROR log; Docker unreachable + not require_isolation→SubprocessSandbox() (unchanged WARNING)
  - ✅ done: 3-way branch + ERROR log (require) vs WARNING (fallback); `require_isolation` param added to the existing `*, image` sig

### 1.3 Config + registration wire
- [x] **`sandbox_require_isolation` setting + `_get_shared_sandbox()` read**
  - DoD: `sandbox_require_isolation: bool = False` (env `SANDBOX_REQUIRE_ISOLATION`) in Settings + MHist; `_get_shared_sandbox()` reads `get_settings().sandbox_require_isolation` → `default_sandbox(require_isolation=...)`; DEFAULT OFF preserves dev/CI fallback
  - ✅ done: config:143 + MHist; `_get_shared_sandbox()` inline `get_settings()` read → threads `require_isolation=`

### 1.4 Unit tests (property + fail-closed + config)
- [x] **`test_sandbox.py` + config/register test**
  - DoD: property asserts (Docker True / Subprocess False / FailClosed True); `default_sandbox(require_isolation=True)` with docker-unreachable (monkeypatch `docker.from_env`/`ping` raise) → `_FailClosedSandbox`; `=False` → SubprocessSandbox; `_FailClosedSandbox.execute()` returns refusal + never runs; `_get_shared_sandbox()` reads the setting (reset module singleton — Risk Class C)
  - ✅ done: `test_sandbox.py` +5 (property + 3 default_sandbox paths via `sys.modules["docker"]` fake + FailClosed refusal); NEW `test_shared_sandbox.py` +3 (threads True/False + caches singleton; autouse singleton-reset fixture — Risk Class C)

### 1.x Partial gate
- [x] `cd backend && mypy src && black . && isort . && flake8 .` clean + the FULL test surface of every edited src file (`test_sandbox.py` + config/register tests — 57.136 process lesson: a changed src file's full test surface, not just new tests)
  - ✅ done: `pytest test_sandbox.py + test_shared_sandbox.py + test_partial_swap.py` → **38 passed + 1 skip** (POSIX-only mem test skip on Windows) · black/isort/flake8 clean (1 E501 docstring trimmed) · **mypy src 0/374**

---

## Day 2 — Escape-rate measurement harness + real-Docker run (US-3) + detector reframe (US-4)

### 2.1 `benchmark_sandbox_escape.py` + corpus fixture
- [x] **mirror benchmark_correction_hygiene.py**
  - DoD: `load_cases / regex_screen (real DEFAULT_SANDBOX_PATTERNS) / docker_contain (run under DockerSandbox, assert no host effect) / build_report (regex_escape_rate, docker_containment_rate) / main() gated by RUN_DOCKER_INTEGRATION`; `sandbox_escape_cases.yaml` = host-touching primitives (should_match) + known bypasses (getattr/importlib/os.spawnl/encoded-exec)
  - ✅ done: full scaffold; corpus = 10 network-egress cases (4 caught + 6 missed); `main()` auto-detects via `is_structurally_isolated` (dogfoods the property) — docker arm runs iff isolated, else regex-only + gate-only warning. **Design note**: corpus focuses on NETWORK egress (cleanest single boundary); known-bypass set = urllib/http.client/importlib-concat/asyncio/ftplib/smtplib

### 2.2 CI-safe unit test
- [x] **MockChatClient-free regex/report test (no Docker)**
  - DoD: `test_benchmark_sandbox_escape.py` (importlib-load idiom) covers load_cases (schema/dup) · regex_screen with the real patterns (catches should-match, misses known bypasses) · build_report (rates); NO Docker in CI
  - ✅ done: +13 tests incl. the **key invariant** `regex_screen(code) is case.should_match` for every corpus case (real patterns) + gap-demonstration + docker_contain (fake backend) + build_report. 13 passed

### 2.3 Real-Docker escape run
- [x] **escape report (regex vs Docker)**
  - DoD: `RUN_DOCKER_INTEGRATION=1 python scripts/benchmark_sandbox_escape.py` → JSON report; regex_escape_rate (>0 = blocklist gap) + docker_containment_rate (~100% = restrict wins) recorded in progress.md Day 2 + copied to `artifacts/` (benchmark_reports gitignored). If Docker down (D-docker-available) → noted gate-only + the docker arm skipped explicitly
  - ✅ done: real DockerSandbox run → **regex_escape_rate 60% (6/10 missed)** · **docker_containment_rate 100% (10/10)** → detect→restrict confirmed. Report → `artifacts/sandbox_escape_report.{md,json}` + progress.md Day 2

### 2.4 Detector reframe (US-4)
- [x] **`risky_action_detector.py` docstring reframe**
  - DoD: docstring + `DEFAULT_SANDBOX_PATTERNS` section comment reframed (ESCALATE-for-visibility, NOT the boundary; boundary = mandatory Docker isolation); `check()` + patterns byte-unchanged; MHist line
  - ✅ done: "Security model" docstring paragraph + DEFAULT_SANDBOX_PATTERNS NOTE + MHist; `check()`/patterns byte-unchanged → `pytest -k risky` **23 passed** (no behavior regression)

### 2.x Full gate
- [x] mypy `src` 0/374 · run_all 10/10 · backend pytest 2765+ + new · Vitest 915 (unchanged) · `npm run lint && npm run build` clean (NO `--silent`) · mockup 51 (`diff` empty) · black/isort/flake8 clean · LLM-SDK-leak clean
  - ✅ done: **pytest 2786 passed + 5 skip** (baseline 2765 + 21 new) · **mypy src 0/374** · **v2 lints 10/10** (incl. check_llm_sdk_leak) · risky 23 passed (no regression) · black/isort/flake8 clean · Vitest 915 / mockup 51 unchanged sentinels (backend-only, no FE touched)

---

## Day 3 — Drive-through (US-5) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E)
- [x] kill stale `--reload` + orphan spawn-workers (Win32_Process PID/PPID/StartTime sweep); confirm fresh SOLE port owner + startup log; set `SANDBOX_REQUIRE_ISOLATION` to the value under test BEFORE restart (sandbox singleton resolved once at first registration)
  - ✅ done: backend NOT running (no python.exe, port free, no orphan — 57.97 trap clear); started FRESH single-process uvicorn (no `--reload`); startup log confirmed DB/Redis/Azure/pricing wired + "startup complete"; normal config (require_isolation off, real Docker) for the UI no-regression arm; the fail-closed arm forces config in the backend-runtime driver

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] **(a) fail-closed refusal** — `SANDBOX_REQUIRE_ISOLATION=true` + a non-isolating backend (force Docker-unreachable OR inject `_FailClosedSandbox`) → chat-v2 prompt that triggers python_sandbox → the tool returns the clear refusal (code NOT run); Inspector shows the tool result = refusal
  - ✅ done (backend runtime, deterministic, real `_get_shared_sandbox`→`default_sandbox`→handler path): require_isolation=true + Docker unreachable → `_FailClosedSandbox` → handler REFUSED (stdout empty, exit_code=1, "execution refused..."), code NOT run; ERROR log fired. (Backend runtime per 57.136 "兩者結合" — forcing Docker-unreachable in a live UI is artificial; the runtime path is the identical production wiring.)
- [x] **(b) no-regression** — normal Docker (`SANDBOX_REQUIRE_ISOLATION` off OR Docker reachable) → chat-v2 python_sandbox runs end-to-end (real DockerSandbox, like the 57.118 dt) → stdout renders; my changes did NOT break the normal path
  - ✅ done (real UI): chat-v2 + real Azure gpt-5.2 → python_sandbox `print(31337*1337)` → HITL approve → real DockerSandbox executes → answer "41897569" rendered + verification_passed (0.99) + end_turn. No-regression confirmed user-facing.
- [x] **THE walk (real UI)**: per-control — python_sandbox call visible in Inspector / result renders (refusal in (a), real output in (b)) / labels real
  - ✅ Inspector "BLOCK SEQUENCE: tool python_sandbox + answer 41897569 + verification claim verified"; HITL approval card real (Approve & continue worked); result rendered in message thread
- [x] Screenshot + observed-vs-intended → progress.md Day 3
  - ✅ `artifacts/dt-57137-no-regression-python-sandbox.jpeg` + progress.md Day 3 (runtime + UI tables + observed-vs-intended)

### 3.3 Decision record (evidence → reframe)
- [x] **escape-vs-containment verdict** — from the Day-2 report: regex_escape_rate (gap) + docker_containment_rate (boundary holds) → confirms detect-redundant-under-restrict + restrict-must-be-mandatory; recorded in progress.md + design note 41
  - ✅ regex_escape_rate 60% + docker_containment_rate 100% → detect→restrict confirmed; recorded in progress.md Day 2 (design note 41 = Day 4)

---

## Day 4 — CHANGE-104 + design note 41 + closeout

### 4.1 CHANGE-104 + design note (spike)
- [x] **`CHANGE-104-sandbox-detect-to-restrict.md`** (gap + fix + escape/containment numbers + drive-through PASS + AD closed) → ✅ done
- [x] **`41-sandbox-detect-to-restrict-design.md`** (spike design note — 8-point gate: section per US / decision = the escape-vs-containment verdict / verified invariants with file:line / open invariants / rollback = env-gate OFF + revert / 17.md cross-ref (Cat 2 ABC property — note if a row update needed) / verification commands / fixtures) → ✅ done (8/8 gate; NO new 17.md contract — Cat 2 internal property N/A justified §3)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`guardrail-restrict-spike` 0.60, 1st data point; flag if ratio out of band → re-point) → ✅ done (ratio ~0.97 IN band → KEEP 0.60)
- [x] Final gate sweep: mypy · run_all · pytest · Vitest · mockup · build · lint · LLM-SDK-leak → ✅ mypy 0/374 · run_all 10/10 · pytest 2786+5skip · black/isort/flake8 clean · LLM-SDK-leak clean · Vitest 915 / mockup 51 unchanged sentinels (backend-only, no FE touched — confirmed via git status)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Guardrail-Detect-To-Restrict`) · sprint-workflow matrix (`guardrail-restrict-spike` row / 1st data point) → ✅ all done
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → violations; v2 lints 10/10 → ✅ no violations; v2 lints 10/10
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
