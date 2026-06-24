# Sprint 57.137 Plan — sandbox detect→restrict: fail-closed isolation + escape-rate measurement spike

**Summary**: Close `AD-Guardrail-Detect-To-Restrict` (research #3). The Cat 9 `RiskyActionDetector` is a regex deny-list over python_sandbox code that loses a cat-and-mouse race (57.110 found the `os.popen` bypass of the `os.system` block); research §3 says structural restriction must be the boundary, not a blocklist. DockerSandbox (FIX-033 / Sprint 52.5 #17) ALREADY provides that structural restriction (network none / read-only fs / cap-drop ALL / non-root / no bind mounts) — but `default_sandbox()` SILENTLY degrades to the production-unsafe `SubprocessSandbox` when Docker is unreachable, leaving the bypassable regex as the only defense. This **evidence-first thin spike** (same shape as the just-merged 57.136): (1) MEASURE the regex deny-list's escape rate AND verify DockerSandbox structurally contains the escapes, with a permanent harness; (2) ship a surgical, env-gated **fail-closed** lever (`SANDBOX_REQUIRE_ISOLATION`) so python_sandbox refuses to run on a non-isolating backend instead of silently degrading; (3) reframe the detector docstring as ESCALATE-for-visibility, NOT the boundary. Backend-only, NO migration / NO new wire event / NO frontend. A drive-through is MANDATORY (python_sandbox runs on the chat-v2 主流量). A **design note (41)** is required — its headline is the measured escape-rate vs Docker-containment numbers + the detect→restrict reframe.

**Status**: Draft (user said「開始規劃和設計 AD-Guardrail-Detect-To-Restrict」2026-06-24 + AskUserQuestion picked **Option A — fail-closed 強制 + 量測 spike**; awaiting plan approval before Day-0 / code)
**Branch**: `feature/sprint-57-137-sandbox-detect-to-restrict`
**Base**: `main` HEAD `ba4c5c13` (PR #326 — flip Sprint 57.136 PR-pending → MERGED)
**Slice**: closes `AD-Guardrail-Detect-To-Restrict` (research #3; standalone; the 2nd-ranked research-derived candidate in `next-phase-candidates.md` §Research-Derived Candidates)
**Scope decisions**: (a) thin spike — MEASURE escape-rate + Docker-containment BEFORE relying on the structural boundary, mirroring 57.136's evidence-first pattern; (b) the structural decision lives in Cat 2 (`default_sandbox(require_isolation=...)` + a `SandboxBackend.is_structurally_isolated` property), the config read in the registration layer; (c) fail-closed = a refusing `_FailClosedSandbox` backend (tool stays visible + returns a clear auditable refusal), NOT silent tool absence; (d) `SANDBOX_REQUIRE_ISOLATION` DEFAULT OFF (dev/CI keep SubprocessSandbox fallback; prod opt-in — mirrors 57.135 destructive-opt-in posture); (e) the regex detector is KEPT (reframed as ESCALATE-visibility), NOT retired — a human still sees the attempt.

---

## 0. Background

### The gap (`AD-Guardrail-Detect-To-Restrict`)

- The Cat 9 `RiskyActionDetector` screens python_sandbox `code` against a regex deny-list (`DEFAULT_SANDBOX_PATTERNS`) and ESCALATEs (never BLOCKs) into HITL.
- A regex blocklist is a losing cat-and-mouse: 57.110's drive-through caught a child agent rewriting a blocked `os.system` as `os.popen` → a new pattern had to be added. There are unbounded equivalent encodings (`getattr`, `importlib`, `os.spawnl`, encoded `exec`, …) the list can never fully cover.
- DockerSandbox ALREADY contains these structurally — but the boundary is NOT mandatory: `default_sandbox()` silently falls back to the production-unsafe `SubprocessSandbox` when Docker is unreachable, and in that state the bypassable regex is the only defense.

### Why it matters (the missing capability)

Enterprise tenants run arbitrary LLM-authored code via python_sandbox on the 主流量. Research §3's thesis is "restrict > detect": the security boundary must be a structural sandbox the model can't talk its way past, not a pattern list. Today the structural boundary is best-effort (silent degrade) and the documented role of the regex blurs "supplementary visibility" with "the defense". The spike settles, with numbers, that the regex is redundant-for-containment under Docker, then makes the structural boundary mandatory (fail-closed) so a Docker-less host refuses rather than silently running unisolated arbitrary code.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `ba4c5c13`) | Anchor |
|-------|-------------------------------------|--------|
| regex deny-list is the screen | `DEFAULT_SANDBOX_PATTERNS` tuple of 11 word-bounded regexes; `pattern.search(code)` → ESCALATE HIGH | `risky_action_detector.py:64-79, 128-137` |
| cat-and-mouse is documented | MHist: *"Sprint 57.110 B4 — +os.popen/os.spawn*/os.exec* (dt found the popen bypass)"* | `risky_action_detector.py:31` |
| Docker IS the structural boundary | network none / read-only rootfs / cap-drop ALL / uid 65534 / pids-limit / no bind mounts | `sandbox.py:32-48` (docstring) + `DockerSandbox` `:219+` |
| network always blocked for sandbox | handler hardwires `network_blocked=True` | `exec_tools.py:93` |
| **silent degrade to unsafe backend** | Docker unreachable → `logger.warning(...)` + `return SubprocessSandbox()` (no fail-closed) | `sandbox.py:418-426` |
| no prod/isolation gate exists | no `ENVIRONMENT` / `is_production` / isolation setting in Settings | `core/config/__init__.py` (grep empty) |
| resolution / registration site | `_get_shared_sandbox()` → `default_sandbox()` → `register_builtin_tools(sandbox_backend=...)` | `_register_all.py:101-106, 288` |
| no structural distinguisher on the ABC | Docker vs Subprocess distinguished only by class type | `sandbox.py:115-126` (`SandboxBackend` ABC) |

→ The fix must (1) add a structural `is_structurally_isolated` property to the sandbox ABC, (2) add an env-gated `require_isolation` path so a non-isolated backend fail-closes instead of silently degrading, (3) MEASURE the regex escape-rate + Docker containment with a permanent harness, (4) reframe the detector docstring as visibility-not-boundary.

### The design (Cat 2 ABC property + env-gated fail-closed resolver + a mirror-benchmark escape harness)

```
# sandbox.py (Cat 2):
class SandboxBackend(ABC):
    @property
    def is_structurally_isolated(self) -> bool: ...     # DockerSandbox=True, SubprocessSandbox=False

class _FailClosedSandbox(SandboxBackend):               # runs NOTHING; refuses with a clear result
    is_structurally_isolated = True                     # vacuous (executes nothing)
    async def execute(...) -> SandboxResult:            # exit_code=1, stderr="execution refused: SANDBOX_REQUIRE_ISOLATION ..."

def default_sandbox(*, require_isolation: bool = False, image=None) -> SandboxBackend:
    # Docker reachable → DockerSandbox (unchanged)
    # Docker unreachable + require_isolation → _FailClosedSandbox()   # NEW: fail-closed, not silent degrade
    # Docker unreachable + not require_isolation → SubprocessSandbox() # unchanged (dev/CI)

# _register_all.py:  _get_shared_sandbox() reads get_settings().sandbox_require_isolation → default_sandbox(require_isolation=...)
# core/config:       sandbox_require_isolation: bool = False  (env SANDBOX_REQUIRE_ISOLATION)
# risky_action_detector.py:  docstring reframe — ESCALATE-for-visibility, NOT the boundary (boundary = mandatory Docker isolation)

# scripts/benchmark_sandbox_escape.py (mirror benchmark_correction_hygiene.py / benchmark_judge.py):
#   load_cases(yaml) → for each host-touching snippet: regex_caught? (real DEFAULT_SANDBOX_PATTERNS) +
#   docker_contained? (run under DockerSandbox, assert no host effect: net egress fails / host-fs write fails)
#   build_report: regex_escape_rate (HIGH = blocklist loses) · docker_containment_rate (~100% = restrict wins)
```

WHY this over a blind change: research confirms the blocklist is the wrong primary boundary, but the NUMBER (how leaky is the regex, how complete is Docker) is what justifies making Docker mandatory + reframing the regex — flipping behavior without the measurement would repeat the evidence-free risk 57.136's discipline avoided. The env gate (DEFAULT OFF) = zero-risk rollback: dev/CI keep the SubprocessSandbox fallback; only an operator who sets `SANDBOX_REQUIRE_ISOLATION=true` gets fail-closed.

### Ground truth (recon head-start — code read on `main` HEAD `ba4c5c13`; ALL re-verified §checklist 0.1)

- `risky_action_detector.py:64-79` — the 11-pattern deny-list (the escape harness imports this exact tuple so the measurement tracks real behavior).
- `sandbox.py:399-426` — `default_sandbox()` is the sole fallback decision site (the `require_isolation` param lands here).
- `sandbox.py:115-126` — `SandboxBackend` ABC (the `is_structurally_isolated` property lands here; both impls override).
- `_register_all.py:101-106, 288` — `_get_shared_sandbox()` singleton → `register_builtin_tools(sandbox_backend=...)` (the config read lands in the singleton).
- `skills/tool.py:156` — `_get_default_sandbox()` for `run_skill_script` runs BUNDLED (non-LLM) scripts — OUT of scope (§9; lower risk, no LLM-arbitrary code).
- `benchmark_correction_hygiene.py` (57.136) + `benchmark_judge.py` (57.111) — the measurement scaffold + golden-fixture + CI-safe-unit-test pattern to mirror.

**Baselines (57.136 closeout)**: pytest 2765+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/374 · run_all 10/10. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-denylist-shape** — re-grep `risky_action_detector.py:64-79` still a `tuple[str, ...]` of 11 patterns importable as `DEFAULT_SANDBOX_PATTERNS` → the harness imports it (no copy-paste drift).
- **D-default-sandbox-fallback** — confirm `default_sandbox()` (`sandbox.py:399-426`) still `return SubprocessSandbox()` on the except branch (the fail-closed insertion point) → the `require_isolation` param shifts §3.1.
- **D-abc-shape** — confirm `SandboxBackend` ABC (`sandbox.py:115-126`) signature + that DockerSandbox/SubprocessSandbox are the only two impls → the property lands on 3 classes (+ `_FailClosedSandbox`).
- **D-config-grep** — confirm no existing isolation/ENVIRONMENT setting in `core/config` → `sandbox_require_isolation` is net-new (no rename collision).
- **D-register-site** — confirm `_get_shared_sandbox()` (`_register_all.py:101-106`) is the sole chat python_sandbox backend resolver + `:288` the registration call → the config read lands there.
- **D-docker-available** — confirm Docker daemon reachable on the dev host (the 57.118 drive-through ran a real DockerSandbox) → the escape harness's docker-containment arm + the no-regression drive-through can run for real; if not, the docker arm is gated/skipped + noted.

## 1. Sprint Goal

Settle, with real numbers, that python_sandbox's regex deny-list is leaky (escape-rate > 0) while DockerSandbox structurally contains those escapes (containment-rate ~100%), and ship a pluggable, env-gated fail-closed isolation guarantee so a non-isolating backend refuses arbitrary code instead of silently degrading — the structural boundary becomes mandatory (research §3 "restrict > detect"), one config flip away. PROVEN by: the full gate set + a real-Docker escape-harness report (`benchmark_sandbox_escape`: regex_escape_rate / docker_containment_rate) + a MANDATORY chat-v2 drive-through (fail-closed refusal under `SANDBOX_REQUIRE_ISOLATION=true` with a non-isolating backend + no-regression normal Docker run). Produces **CHANGE-104** + a **design note (41)** carrying the measured numbers + the detect→restrict reframe.

## 2. User Stories

- **US-1** (structural distinguisher): 作為 harness 維護者，我希望 `SandboxBackend` 有 `is_structurally_isolated` property（DockerSandbox=True / SubprocessSandbox=False），以便 fail-closed 邏輯依結構性質判斷而非 isinstance（provider-neutral）。
- **US-2** (fail-closed lever): 作為 operator，我希望 `SANDBOX_REQUIRE_ISOLATION` env（DEFAULT OFF）讓 python_sandbox 在只有非隔離 backend 可用時 fail-closed（回明確 refusal）而非靜默降級到 production-unsafe 的 SubprocessSandbox，以便 prod 強制結構性邊界、dev/CI 不受影響。
- **US-3** (measurement): 作為決策者，我希望有可重跑的 escape harness 量測 regex deny-list 的 escape-rate 並驗證 DockerSandbox 對那些 escape 的 containment-rate，以便用證據（非假設）支撐「detect 在 restrict 下冗餘、restrict 須強制」。
- **US-4** (reframe): 作為 reviewer，我希望 `RiskyActionDetector` docstring 明確說明它是 ESCALATE-for-visibility 層、不是安全邊界（邊界 = 現在強制的 Docker 隔離），以便未來不再把 regex 當主防線（避免重蹈 cat-and-mouse）。
- **US-5** (drive-through, MANDATORY): 作為使用者，我希望在 chat-v2 觸發 python_sandbox 時：`require_isolation=true` + 非隔離 backend → 收到明確 refusal（不執行未隔離代碼）；正常 Docker → 照常執行（no-regression）。
- **US-6** (closeout): 設計筆記 41（spike 8-point gate）+ CHANGE-104 + calibration + navigators/next-phase-candidates 更新（CLOSE the AD）。

## 3. Technical Specifications

### 3.0 Architecture (backend-only — NO migration / NO new wire event / NO frontend)

```
EDIT  backend/src/agent_harness/tools/sandbox.py                 — SandboxBackend.is_structurally_isolated property (ABC + Docker True + Subprocess False) + _FailClosedSandbox + default_sandbox(require_isolation=...)
EDIT  backend/src/core/config/__init__.py                        — sandbox_require_isolation: bool = False (env SANDBOX_REQUIRE_ISOLATION)
EDIT  backend/src/business_domain/_register_all.py               — _get_shared_sandbox() reads the setting → default_sandbox(require_isolation=...)
EDIT  backend/src/agent_harness/guardrails/tool/risky_action_detector.py — docstring reframe (ESCALATE-visibility, NOT boundary); NO behavior change
NEW   backend/scripts/benchmark_sandbox_escape.py               — regex escape-rate + Docker containment harness (mirror benchmark_correction_hygiene.py)
NEW   backend/tests/fixtures/guardrails/sandbox_escape_cases.yaml — host-touching snippets + known bypasses corpus
NEW   backend/tests/unit/scripts/test_benchmark_sandbox_escape.py — CI-safe (no Docker) load/match/report logic
EDIT  backend/tests/unit/agent_harness/tools/test_sandbox.py    — is_structurally_isolated + _FailClosedSandbox + default_sandbox(require_isolation) (monkeypatch docker unreachable)
EDIT  backend/tests/unit/.../test_register_all*.py (or test_config) — _get_shared_sandbox reads the setting
UNTOUCHED  risky_action_detector check() behavior / DEFAULT_SANDBOX_PATTERNS / exec_tools handler / wire schema / resume() / frontend
```

### 3.1 Structural property + fail-closed resolver (US-1, US-2) — `sandbox.py`

- `SandboxBackend.is_structurally_isolated` — a `@property` (default could be abstract; concretely DockerSandbox returns `True`, SubprocessSandbox returns `False`). The fail-closed gate reads this, not `isinstance`.
- `_FailClosedSandbox(SandboxBackend)` — `execute()` runs nothing, returns `SandboxResult(stdout="", stderr="execution refused: structural isolation required (SANDBOX_REQUIRE_ISOLATION=true) but no isolating sandbox is available", exit_code=1, duration_seconds=0.0, killed_by_timeout=False)`; `is_structurally_isolated=True` (vacuous — executes nothing). Module-private (leading `_`).
- `default_sandbox(*, require_isolation: bool = False, image=None)` — Docker reachable → DockerSandbox (unchanged); Docker unreachable + `require_isolation` → `_FailClosedSandbox()` + a distinct ERROR log; Docker unreachable + not `require_isolation` → `SubprocessSandbox()` + the existing WARNING (unchanged dev/CI path).

### 3.2 Config + registration wire (US-2) — `core/config` + `_register_all.py`

- `sandbox_require_isolation: bool = False` in `Settings` (env `SANDBOX_REQUIRE_ISOLATION`; pydantic-settings auto-bind; DEFAULT OFF so dev/CI/test are byte-unchanged).
- `_get_shared_sandbox()` reads `get_settings().sandbox_require_isolation` and passes `require_isolation=` into `default_sandbox(...)`. The singleton-once-per-process behavior is unchanged.

### 3.3 Measurement harness (US-3) — `scripts/benchmark_sandbox_escape.py` + fixture

- Mirror `benchmark_correction_hygiene.py`: `load_cases(path)` (schema-validate the YAML) / `regex_screen(code)` (uses the real `DEFAULT_SANDBOX_PATTERNS` imported from `risky_action_detector`) / `docker_contain(code)` (run under DockerSandbox; assert no host effect — network egress fails under `network none`, host-fs write fails under read-only rootfs) / `build_report(...)` (pure: `regex_escape_rate`, `docker_containment_rate`, counts) / `main()` (gated by a `RUN_DOCKER_INTEGRATION` env, like 57.136's `RUN_AZURE_INTEGRATION`; writes a JSON report).
- Golden fixture `sandbox_escape_cases.yaml`: host-touching primitives the regex SHOULD catch (os.system / subprocess / socket / …) + KNOWN bypasses it MISSES (`getattr(os,'sys'+'tem')`, `importlib.import_module`, `os.spawnl`, base64-decoded `exec`, …) — the misses prove the cat-and-mouse gap; each labeled `should_match` so the harness reports false-negatives.
- pytest unit test mirrors `test_benchmark_correction_hygiene.py` (importlib-load idiom to avoid the `tests.unit.scripts` shadow; covers `load_cases` / `regex_screen` / `build_report` with the real patterns; NO Docker → the docker arm is exercised only by the gated `main()`).

### 3.4 Detector reframe (US-4) — `risky_action_detector.py`

- Docstring + the `DEFAULT_SANDBOX_PATTERNS` section comment reframed: this layer is **ESCALATE-for-visibility** (a human sees the attempt + a tenant can flag extra patterns), NOT the security boundary; the boundary is the now-mandatory (`SANDBOX_REQUIRE_ISOLATION`) DockerSandbox structural isolation. NO behavior change to `check()` / the patterns / the ESCALATE action (so no regression; the 57.106/57.110 tests stay green).

### 3.x What is explicitly NOT done

- **Retiring the regex detector** — KEPT (reframed as visibility); a human still benefits from seeing a flagged attempt + tenants keep extra_patterns. Removing it is a separate decision (would lose visibility).
- **`run_skill_script` / `_get_default_sandbox` (skills)** — OUT; it runs BUNDLED (non-LLM-authored) scripts, lower risk. The fail-closed gate this sprint covers the LLM-arbitrary python_sandbox path only (→ §9).
- **Per-tenant isolation profile** — OUT (that was Option C; settings/env-only this sprint — anti-AP-6).
- **Changing DockerSandbox hardening / the network_blocked hardwire / the deny-list patterns** — UNTOUCHED.

### 3.y Validation (US-1..US-6)

Gates: mypy `src` 0/374 · run_all 10/10 · pytest 2765+ (+ new) · Vitest 915 (unchanged — no FE) · mockup 51 (`diff` empty — no FE) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.3 real-Docker escape report + the MANDATORY §US-5 drive-through.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/tools/sandbox.py` | EDIT (`is_structurally_isolated` property + `_FailClosedSandbox` + `default_sandbox(require_isolation=...)`) |
| 2 | `backend/src/core/config/__init__.py` | EDIT (`sandbox_require_isolation` setting) |
| 3 | `backend/src/business_domain/_register_all.py` | EDIT (`_get_shared_sandbox()` reads the setting) |
| 4 | `backend/src/agent_harness/guardrails/tool/risky_action_detector.py` | EDIT (docstring reframe; NO behavior change) |
| 5 | `backend/scripts/benchmark_sandbox_escape.py` | NEW (escape-rate + Docker-containment harness) |
| 6 | `backend/tests/fixtures/guardrails/sandbox_escape_cases.yaml` | NEW (corpus) |
| 7 | `backend/tests/unit/scripts/test_benchmark_sandbox_escape.py` | NEW (CI-safe load/match/report) |
| 8 | `backend/tests/unit/agent_harness/tools/test_sandbox.py` | EDIT (property + `_FailClosedSandbox` + `default_sandbox(require_isolation)`) |
| 9 | `claudedocs/4-changes/feature-changes/CHANGE-104-sandbox-detect-to-restrict.md` | NEW |
| 10 | `docs/03-implementation/agent-harness-planning/41-sandbox-detect-to-restrict-design.md` | NEW (spike design note) |
| — | `risky_action_detector.check()` / `DEFAULT_SANDBOX_PATTERNS` / `exec_tools.py` / wire schema / `resume()` | **UNTOUCHED** |
| — | any frontend / migration / new DB table | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `SandboxBackend.is_structurally_isolated` property: DockerSandbox → True, SubprocessSandbox → False, `_FailClosedSandbox` → True (vacuous); unit test asserts all three.
2. `default_sandbox(require_isolation=True)` with Docker unreachable returns `_FailClosedSandbox` (NOT SubprocessSandbox); `require_isolation=False` returns SubprocessSandbox (unchanged); Docker reachable returns DockerSandbox (unchanged). Unit test (monkeypatch docker import/ping) asserts all paths.
3. `SANDBOX_REQUIRE_ISOLATION` settings resolves + threads through `_get_shared_sandbox()`; DEFAULT OFF → dev/CI byte-unchanged (SubprocessSandbox fallback preserved).
4. `_FailClosedSandbox.execute()` returns a clear refusal (`exit_code=1` + explanatory stderr); it NEVER runs the code.
5. `benchmark_sandbox_escape.py` produces a real-Docker report with `regex_escape_rate` (> 0 expected — proves the blocklist gap) + `docker_containment_rate` (~100% expected — proves structural restriction); CI-safe unit covers the pure logic with the real patterns + a fixture (no Docker).
6. `RiskyActionDetector` docstring reframed (visibility-not-boundary); `check()` behavior + patterns UNCHANGED (57.106/57.110 tests green = no regression).
7. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — chat-v2 python_sandbox: (a) `SANDBOX_REQUIRE_ISOLATION=true` + non-isolating backend → clear refusal rendered (code NOT run); (b) normal Docker → python_sandbox runs (no-regression); screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
8. `AD-Guardrail-Detect-To-Restrict` CLOSED; CHANGE-104 + design note 41 (8-point gate); calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `is_structurally_isolated` property (ABC + Docker + Subprocess + `_FailClosedSandbox`)
- [ ] US-2 `sandbox_require_isolation` setting + `default_sandbox(require_isolation=...)` fail-closed + `_get_shared_sandbox()` wire
- [ ] US-3 `benchmark_sandbox_escape.py` + corpus fixture + CI-safe unit test + real-Docker report
- [ ] US-4 `RiskyActionDetector` docstring reframe (no behavior change)
- [ ] US-5 chat-v2 python_sandbox drive-through (fail-closed refusal + no-regression) (MANDATORY)
- [ ] US-6 design note 41 + CHANGE-104 + closeout

## 7. Workload Calibration

- Scope class **`guardrail-restrict-spike` 0.60** (NEW class, 1st data point; analogous to `verification-context-hygiene-spike` 0.60 (57.136) + `verification-in-loop-spike` 0.60 (57.98) — a Cat 2/9 structural-guardrail spike paired with a measurement harness + an env-gated surgical change + drive-through; cite `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix).
- **Agent-delegated: no** (parent-direct; the spike's value is precise security judgment of escape-vs-containment evidence + a surgical Cat 2 fail-closed change — not mechanical pattern reuse). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~12 hr (Day0 三-prong ~1 · ABC property + config + fail-closed resolver + unit ~2.5 · escape harness + corpus + CI test + real-Docker run ~4 · drive-through (fail-closed + no-regression) ~2 · design note + CHANGE + closeout ~2.5) → class-calibrated commit ~7.2 hr (mult 0.60). Day-4 retro Q2 verifies. NOTE: per the 57.120/136 ceremony-not-code-accelerated insight, if the code lands much smaller than estimated the drive-through + design-note ceremony may pull the ratio up — flag at retro.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Docker unavailable on the dev host** → escape-harness docker arm + no-regression drive-through can't run for real | Day-0 D-docker-available probes the daemon; if down, the docker-containment arm is gated/skipped + explicitly noted "gate-only" (never implied), and the fail-closed refusal is driven instead (deterministic — it needs NO Docker) |
| **Fail-closed too aggressive** → breaks dev/CI (which legitimately use SubprocessSandbox) | DEFAULT OFF (`SANDBOX_REQUIRE_ISOLATION=false`); only an explicit prod opt-in fail-closes; unit asserts OFF = SubprocessSandbox fallback preserved |
| `_FailClosedSandbox` accidentally runs code | Unit asserts `execute()` returns the refusal + never invokes a real runner; `is_structurally_isolated=True` is vacuous (runs nothing) |
| Stale `--reload` backend masks the startup-resolved sandbox singleton | Risk Class E: clean restart + confirm sole live worker + startup log before the drive-through (the 57.97 spawn-worker trap); set `SANDBOX_REQUIRE_ISOLATION` BEFORE restart (singleton resolved once at first registration) |
| Module-level `_shared_sandbox_singleton` persists across tests | Risk Class C: the singleton is `_register_all` module-level — reset/monkeypatch it in the new unit test, or test `default_sandbox()` directly (no singleton) |
| Docstring reframe drifts the detector behavior | docstring-ONLY edit; `check()` + `DEFAULT_SANDBOX_PATTERNS` byte-unchanged; the 57.106/57.110 tests are the regression guard |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **`run_skill_script` / skills `_get_default_sandbox` fail-closed** — → `AD-SkillScript-Require-Isolation-Phase58` (bundled non-LLM scripts, lower risk; same `require_isolation` lever can extend later).
- **Per-tenant isolation profile** (Option C) — → `AD-Sandbox-PerTenant-Capability-Profile-Phase58` (network/fs scope per tenant; settings/env-only this sprint).
- **Retiring the regex detector** — KEPT as visibility; retirement is a separate decision that would lose human visibility into attempts.
- **The other research-derived candidates** (#2 pass^k / #5 OTel / #7 tool-lint / #8 key-condition / #4 layered compaction) — stay registered in `next-phase-candidates.md` §Research-Derived Candidates; selection-gated.
