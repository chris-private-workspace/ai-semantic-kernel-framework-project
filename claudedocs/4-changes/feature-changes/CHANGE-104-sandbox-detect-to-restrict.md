# CHANGE-104: Sandbox detect→restrict (fail-closed isolation + escape-rate spike)

**Date**: 2026-06-24
**Sprint**: 57.137
**Scope**: Cat 2 (Tool Layer — sandbox backend) + Cat 4 (Context/config — settings) + Cat 9 (Guardrails — detector reframe); backend-only, NO migration / NO new wire event / NO frontend

## Problem

The Cat 9 `RiskyActionDetector` screens `python_sandbox` code against a regex deny-list (`DEFAULT_SANDBOX_PATTERNS`) and ESCALATEs into HITL — but a regex blocklist is a losing cat-and-mouse. The detector's OWN MHist is the live evidence: Sprint 57.110's drive-through caught a child agent rewriting a blocked `os.system` as `os.popen`, forcing a new pattern. There are unbounded equivalent encodings (`getattr` / `importlib` / split literals / unlisted egress primitives) the list can never cover. Research §3's thesis is "restrict > detect": the boundary must be a structural sandbox the model can't talk past, not a pattern list. DockerSandbox ALREADY provides that structurally — but `default_sandbox()` **silently degraded** to the production-unsafe `SubprocessSandbox` when Docker was unreachable, leaving the bypassable regex as the only defense on a Docker-less host. Closes `AD-Guardrail-Detect-To-Restrict` (research opportunity #3, the highest-tension open reconciliation item after #6 closed in 57.136).

## Root Cause

Two structural gaps, both code-grounded (Day-0 三-prong, zero drift):

1. `default_sandbox()` (`sandbox.py:426` pre-sprint) returned `SubprocessSandbox()` on the Docker-unreachable except branch with only a `logger.warning` — there was no way for an operator to demand structural isolation; a misconfigured/Docker-less prod host silently ran arbitrary LLM-authored code with effectively no isolation (W4P-3: SubprocessSandbox is "decorative on Windows").
2. The `SandboxBackend` ABC had no structural distinguisher — Docker vs Subprocess were told apart only by `isinstance`, so any fail-closed logic would have to violate provider-neutrality.

And the regex deny-list's documented role blurred "supplementary visibility" with "the defense" — without a number, there was no evidence to settle that the regex is redundant-for-containment under Docker.

## Solution

Evidence-first thin spike (same shape as the just-merged 57.136): MEASURE the gap, then ship a surgical env-gated fail-closed lever, then reframe the detector.

1. **`sandbox.py`** (Cat 2): `SandboxBackend.is_structurally_isolated` `@property` (`:129-141`; default `False` = conservative opt-in) + `DockerSandbox` override `True` (`:258-263`) + `SubprocessSandbox` inherits `False` + NEW `_FailClosedSandbox` (`:428-455`; `is_structurally_isolated=True` vacuous + `execute()` returns a refusal `SandboxResult(exit_code=1, stderr="execution refused: structural isolation required …", stdout="")` — runs NOTHING). `default_sandbox(*, require_isolation: bool = False, image=None)` (`:463-506`) — Docker reachable → DockerSandbox (unchanged); Docker unreachable + `require_isolation` → `_FailClosedSandbox()` + ERROR log; Docker unreachable + not `require_isolation` → `SubprocessSandbox()` + the existing WARNING (dev/CI path byte-unchanged).
2. **`core/config/__init__.py`** (Cat 4): `sandbox_require_isolation: bool = False` (`:150`; env `SANDBOX_REQUIRE_ISOLATION`, pydantic-settings auto-bind). DEFAULT OFF → dev/CI/test byte-unchanged; production opts in (mirrors the 57.135 destructive-opt-in posture).
3. **`_register_all.py`**: `_get_shared_sandbox()` (`:101-116`) reads `get_settings().sandbox_require_isolation` → `default_sandbox(require_isolation=...)`. The process-wide singleton behavior is unchanged.
4. **`risky_action_detector.py`** (Cat 9): docstring "Security model" paragraph (`:23-36`) + a `DEFAULT_SANDBOX_PATTERNS` NOTE (`:80-82`) reframing the regex as **ESCALATE-for-visibility, NOT the boundary** (boundary = the now-mandatory Docker isolation); cites the measured 60% escape / 100% containment numbers + the cat-and-mouse history. `check()` / `DEFAULT_SANDBOX_PATTERNS` / the ESCALATE action are **byte-unchanged** (no behavior regression).
5. **`scripts/benchmark_sandbox_escape.py`** (Cat 9 eval, NEW): permanent harness mirroring `benchmark_correction_hygiene.py`. Two independent axes: `regex_screen(code)` imports the REAL `DEFAULT_SANDBOX_PATTERNS` (DETECT); `docker_contain(code, backend)` runs the snippet under the backend + checks a `__ESCAPED__` sentinel is absent (RESTRICT). `main()` dogfoods the 57.137 property — the docker arm runs iff `default_sandbox().is_structurally_isolated`, else regex-only + an explicit "gate-only, NOT a containment claim" warning. Golden fixture `tests/fixtures/guardrails/sandbox_escape_cases.yaml` (10 network-egress cases: 4 the deny-list catches + 6 it misses) + CI-safe unit `tests/unit/scripts/test_benchmark_sandbox_escape.py` (+13).

## Escape vs Containment (real Docker, 10 host-egress cases)

| axis | result |
|------|--------|
| regex caught (deny-list hit) | 4/10 |
| regex MISSED (blocklist gap) | 6/10 |
| **regex_escape_rate** | **60.00%** |
| docker contained (structural) | 10/10 |
| **docker_containment_rate** | **100.00%** |

**Verdict: detect→restrict confirmed.** The regex deny-list MISSES 60% of host-egress primitives (urllib / http.client / importlib-concat / asyncio / ftplib / smtplib — none enumerated), while DockerSandbox's `network none` structurally contains **all 10** regardless of primitive. The regex is **redundant for containment** under Docker → it must NOT be the primary boundary; the structural sandbox is made mandatory via the `SANDBOX_REQUIRE_ISOLATION` fail-closed gate, and the regex stays only as ESCALATE-for-visibility.

**Honesty note**: the measured boundary is NETWORK egress (Docker's clearest, most-testable structural guarantee + the one SubprocessSandbox most clearly fails). The other Docker guarantees (read-only fs / cap-drop / non-root / no bind mounts) are documented (sandbox.py docstring) but not each independently benchmarked this sprint — the network result is sufficient to settle the thesis. Harness is permanent + re-runnable on a broader corpus.

## Verification

- **Gate**: pytest **2786 passed + 5 skip** (baseline 2765 + 21 new = 8 Day-1 sandbox/shared_sandbox + 13 Day-2 escape) · mypy `src` **0/374** · v2 lints **10/10** (`python scripts/lint/run_all.py` cwd=root; incl. check_llm_sdk_leak — the harness uses the Cat 2 ABC, no LLM) · black/isort/flake8 clean. Frontend sentinels unchanged (backend-only): Vitest 915 / mockup 51 / wire 25.
- **Detector regression**: `pytest -k risky` → **23 passed** (docstring-only edit, `check()`/patterns byte-unchanged — the 57.106/57.110 tests are the regression guard).
- **Escape harness (real Docker)**: `RUN_DOCKER_INTEGRATION=1 python scripts/benchmark_sandbox_escape.py` → `regex_escape_rate 60%` + `docker_containment_rate 100%`; report → `sprint-57-137/artifacts/sandbox_escape_report.{md,json}`. CI-safe unit covers the pure logic + the real patterns + the corpus (no Docker).
- **Drive-through PASS (兩者結合)** (real UI + real backend + real LLM):
  - **Backend runtime** (real `_get_shared_sandbox()` → `default_sandbox(require_isolation=...)` → `make_python_sandbox_handler` path): ARM A `SANDBOX_REQUIRE_ISOLATION=true` + Docker unreachable → `_FailClosedSandbox` → handler **REFUSED** (stdout empty, exit_code=1, "execution refused …"; code NOT run; ERROR log fired) · ARM B require_isolation off + real Docker → DockerSandbox → `print(2+2)`→"4" (no-regression).
  - **UI** (chat-v2, real Azure gpt-5.2, jamie@acme.com·operator·acme-prod): `print(31337*1337)` → `python_sandbox` tool_call → HITL `risk=MEDIUM` pause → Approve & continue → **real DockerSandbox executes** → answer **"41897569"** rendered + `verification_passed` (llm_judge 0.99) → end_turn. The 57.137 wiring did NOT break the live tool path (no-regression confirmed user-facing). Screenshot: `sprint-57-137/artifacts/dt-57137-no-regression-python-sandbox.jpeg`.
  - **Why fail-closed is backend-runtime not UI**: forcing Docker-unreachable in a live UI is an artificial setup; the deterministic backend-runtime drive-through exercises the identical production wiring end-to-end. Same honest "兩者結合" pattern accepted for 57.136.

## Impact

Backend-only. Default behavior is byte-identical (`SANDBOX_REQUIRE_ISOLATION` unset → SubprocessSandbox fallback preserved on Docker-less hosts; Docker-reachable hosts → DockerSandbox unchanged). The fail-closed refusal is opt-in (prod sets `SANDBOX_REQUIRE_ISOLATION=true`). No schema, no new wire event, no frontend, no per-tenant surface. Rollback = unset the env (or revert the 4 src edits) — the unset path IS the pre-sprint code. The regex detector is KEPT (reframed), not retired. Follow-ups: `run_skill_script` fail-closed (`AD-SkillScript-Require-Isolation-Phase58`), per-tenant isolation profile (`AD-Sandbox-PerTenant-Capability-Profile-Phase58`).
