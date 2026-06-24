---
title: 41-sandbox-detect-to-restrict design note
purpose: Spike-extract design note from Sprint 57.137; documents the measured regex-escape vs Docker-containment gap + the env-gated fail-closed structural-isolation guarantee for python_sandbox
category: V2 extension docs (post-22-sprint era)
created: 2026-06-24 (Sprint 57.137 Day 4 closeout)
sprint_source: 57.137
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 41 — Sandbox detect→restrict Design Note (Sprint 57.137 extract)

## 8-Point Quality Gate (self-check)

- [x] **1. Section headers map to spike user stories** (§2.1 US-1 / §2.2 US-2 / §2.3 US-3 / §2.4 US-4 / §2.5 US-5)
- [x] **2. Every technical claim has file:line** (sandbox.py:129/258/428/463 · config:150 · _register_all.py:101-116 · risky_action_detector.py:23-36/80 · script + fixture + test paths)
- [x] **3. Decision rationale includes a comparison matrix** (§1 the regex-escape vs Docker-containment table + the detect→restrict verdict)
- [x] **4. Reproducible verification command** (§2.x per invariant + §3 escape-harness rerun command)
- [x] **5. Test fixture reference** (`sandbox_escape_cases.yaml` + the real-Docker run note)
- [x] **6. Open-invariant boundary explicit** (§4 — what this spike did NOT verify)
- [x] **7. Rollback / fallback path** (§5 — env-gate OFF + revert; the unset path IS the pre-sprint code)
- [x] **8. 17.md single-source cross-ref** (§3 — NO new cross-category contract; justified N/A)

---

## 0. Spike Summary

- **Sprint scope**: US-1 `is_structurally_isolated` property · US-2 env-gated fail-closed resolver + config wire · US-3 real-Docker escape-vs-containment measurement · US-4 detector docstring reframe · US-5 mandatory chat-v2 drive-through · US-6 closeout. Closes `AD-Guardrail-Detect-To-Restrict` (research #3).
- **Verified period**: 2026-06-24 (Day 0–3).
- **Calibration**: bottom-up ~12 hr → class-calibrated commit ~7.2 hr (`guardrail-restrict-spike` 0.60, 1st data point, agent_factor 1.0 parent-direct). Day-4 retro Q2 ratio.
- **Verification**: pytest +21 (8 Day-1 sandbox/shared_sandbox + 13 Day-2 escape) → 2786 passed + 5 skip; mypy 0/374; v2 lints 10/10; 1 real-Docker escape run (10 cases × [regex + container]); drive-through PASS (backend runtime fail-closed + UI no-regression).
- **Headline**: the regex deny-list misses **60%** of host-egress primitives; DockerSandbox's `network none` contains **100%** — the regex is redundant-for-containment under Docker, so the structural sandbox is made **mandatory** (`SANDBOX_REQUIRE_ISOLATION` fail-closed gate) and the regex reframed as ESCALATE-for-visibility. #3 = settled with evidence.

## 1. Decision Matrix — regex deny-list (detect) vs Docker isolation (restrict)

Real Docker daemon (DockerSandbox, image `ipa-v2-sandbox:latest`), 10 host-egress attempts via diverse primitives:

| axis | result | meaning |
|------|--------|---------|
| regex caught (deny-list hit) | 4/10 | the patterns DO catch literal socket / aliased socket / `__import__('soc'+'ket')` / subprocess |
| regex MISSED (blocklist gap) | 6/10 | urllib / http.client / importlib-concat / asyncio / ftplib / smtplib — none enumerated |
| **regex_escape_rate** | **60.00%** | the cat-and-mouse gap (unbounded equivalent encodings) |
| docker contained (structural) | 10/10 | `network none` blocks egress regardless of the primitive |
| **docker_containment_rate** | **100.00%** | the structural boundary holds for every case |

**Chosen: make the structural sandbox MANDATORY (env-gated fail-closed); KEEP the regex as ESCALATE-for-visibility, NOT as the boundary.** Reason (not "best practice"): with a measured 60% escape, the regex cannot be the primary defense — but Docker structurally contains 100% of those escapes, so the right move is to guarantee the structural boundary is present (fail closed when it isn't) rather than to keep chasing patterns. **Rejected — expand the regex**: the 57.110 `os.popen` history + the 6 misses prove the arms race is unwinnable; adding patterns is effort with no containment guarantee. **Rejected — retire the regex**: it still gives a human VISIBILITY of a flagged attempt + tenants keep `extra_patterns`; removing it loses that for zero containment gain. **Rejected — make Docker hard-required always**: that breaks dev/CI which legitimately have no daemon; the env gate (DEFAULT OFF) lets prod opt in while dev/CI keep the SubprocessSandbox fallback.

**Honesty caveat**: the measured boundary is NETWORK egress (Docker's clearest single guarantee + the one SubprocessSandbox most clearly fails). The other Docker guarantees (read-only fs / cap-drop ALL / non-root / no bind mounts) are documented (`sandbox.py:32-48`) but NOT each independently benchmarked this sprint. The network result is sufficient to settle detect→restrict; the harness is permanent and re-runnable on a broader corpus (§3 command).

## 2. Verified Invariants

### 2.1 US-1 — `is_structurally_isolated` property (provider-neutral structural distinguisher)

- **Implementation**: `SandboxBackend.is_structurally_isolated` `@property` at `backend/src/agent_harness/tools/sandbox.py:129-141` (default `False` = conservative; a backend must opt IN to claiming isolation); `DockerSandbox` override `True` at `:258-263`; `SubprocessSandbox` inherits `False` (its isolation is decorative on Windows — W4P-3); `_FailClosedSandbox` override `True` at `:431-434` (vacuous — runs nothing).
- **Behavior**: the fail-closed gate + the escape harness read this property, NOT `isinstance` — provider-neutral (a future isolating backend just returns `True`).
- **Verification**: `cd backend && pytest tests/unit/agent_harness/tools/test_sandbox.py -q` → property asserted for all 3 backends.
- **Test fixture**: `sys.modules["docker"]` fake (reachable/unreachable) in `test_sandbox.py` — no real daemon needed (robust on CI + on the Docker-reachable dev host).

### 2.2 US-2 — Env-gated fail-closed resolver + config wire (settings-only, per-tenant OUT)

- **Implementation**: `_FailClosedSandbox(SandboxBackend)` at `sandbox.py:428-455` — `execute()` returns `SandboxResult(stdout="", stderr="execution refused: structural isolation required (SANDBOX_REQUIRE_ISOLATION=true) but no isolating sandbox backend is available …", exit_code=1, duration_seconds=0.0, killed_by_timeout=False)`; runs NOTHING (4 unused args `# noqa: ARG002`, mirroring SubprocessSandbox's `network_blocked` noqa). `default_sandbox(*, require_isolation: bool = False, image=None)` at `:463-506` — 3-way branch: Docker reachable → `DockerSandbox` (unchanged); unreachable + `require_isolation` → `_FailClosedSandbox()` + a distinct ERROR log; unreachable + not `require_isolation` → `SubprocessSandbox()` + the existing WARNING. `sandbox_require_isolation: bool = False` at `core/config/__init__.py:150` (env `SANDBOX_REQUIRE_ISOLATION`). `_get_shared_sandbox()` at `business_domain/_register_all.py:101-116` reads `get_settings().sandbox_require_isolation` → threads `require_isolation=` into `default_sandbox(...)`.
- **Behavior**: DEFAULT OFF → dev/CI/test byte-unchanged (SubprocessSandbox fallback preserved). Only an explicit prod opt-in fail-closes. Defense-in-depth: the structural decision lives entirely in Cat 2 (`default_sandbox` + the property); the registration layer only reads the setting.
- **Verification**: `cd backend && pytest tests/unit/agent_harness/tools/test_sandbox.py tests/unit/business_domain/test_shared_sandbox.py -q` → `default_sandbox` docker-reachable→Docker / unreachable+no-require→Subprocess / unreachable+require→FailClosed + refusal-runs-nothing + `_get_shared_sandbox` threads the setting True/False + caches the singleton.
- **Test fixture**: `test_shared_sandbox.py` autouse fixture resets the module-level `_shared_sandbox_singleton` (Risk Class C — singleton across test event loops).

### 2.3 US-3 — Real-Docker escape-vs-containment measurement harness

- **Implementation**: `backend/scripts/benchmark_sandbox_escape.py` (NEW; mirrors `benchmark_correction_hygiene.py` / `benchmark_judge.py` scaffold: `load_cases` / `regex_screen` / `docker_contain` / `build_report` / `report_to_markdown` / `_amain` / `main` + frozen `EscapeCase`/`CaseResult`/`EscapeReport` dataclasses). Two independent axes: `regex_screen(code)` imports the REAL `DEFAULT_SANDBOX_PATTERNS` from `risky_action_detector` (the DETECT axis, no copy-paste drift); `docker_contain(code, backend)` runs the snippet under the backend + checks the `__ESCAPED__` sentinel is absent (the RESTRICT axis). `main()` dogfoods the 57.137 property — the docker arm runs iff `default_sandbox().is_structurally_isolated`, else regex-only + a "gate-only, NOT a containment claim" warning.
- **Behavior**: `regex_escape_rate` = host-reaching cases the deny-list MISSES; `docker_containment_rate` = host-egress structurally blocked. HIGH escape + ~100% containment ⇒ regex redundant-for-containment ⇒ make structural sandbox mandatory.
- **Verification (CI-safe, no Docker)**: `cd backend && pytest tests/unit/scripts/test_benchmark_sandbox_escape.py -q` → 13 passed (importlib-load idiom avoids the `tests.unit.scripts` shadow). **Key invariant** `test_regex_screen_matches_corpus_should_match`: for every corpus case, `regex_screen(code) is case.should_match` against the REAL patterns — keeps the corpus honest (a pattern change that breaks a claim fails loudly).
- **Verification (real Docker)**: `cd backend && RUN_DOCKER_INTEGRATION=1 python scripts/benchmark_sandbox_escape.py` → writes `benchmark_reports/` (gitignored; copied to `sprint-57-137/artifacts/sandbox_escape_report.{md,json}`). **Cost**: 10 short-lived containers per run (one per case, `network none`).
- **Test fixture**: `backend/tests/fixtures/guardrails/sandbox_escape_cases.yaml` (10 network-egress attempts: socket literal / socket aliased / `__import__('soc'+'ket')` / subprocess [4 caught] + urllib / http.client / importlib-concat / asyncio.open_connection / ftplib / smtplib [6 missed]; each prints `__ESCAPED__` only if egress reached out, each labeled `should_match`).

### 2.4 US-4 — Detector reframe (ESCALATE-for-visibility, NOT the boundary)

- **Implementation**: `backend/src/agent_harness/guardrails/tool/risky_action_detector.py` — a "Security model (Sprint 57.137 reframe)" docstring paragraph at `:23-36` (regex = ESCALATE-for-VISIBILITY layer; the boundary is the now-mandatory Docker structural isolation; cites the 60% escape / 100% containment numbers + the cat-and-mouse history) + a NOTE on the `DEFAULT_SANDBOX_PATTERNS` section comment at `:80-82` ("intentionally INCOMPLETE … do NOT pattern-chase here") + a 1-line MHist.
- **Behavior**: `check()` / `DEFAULT_SANDBOX_PATTERNS` / the ESCALATE action are **byte-unchanged** — docstring-only edit, zero behavior change. Future readers won't mistake the regex for a primary boundary.
- **Verification**: `cd backend && pytest -k risky -q` → 23 passed (the 57.106/57.110 tests are the no-regression guard).

### 2.5 US-5 — Drive-through (real UI + backend + LLM, "兩者結合")

- **Backend runtime** (real `_get_shared_sandbox()` → `default_sandbox(require_isolation=...)` → `make_python_sandbox_handler` path): ARM A `SANDBOX_REQUIRE_ISOLATION=true` + Docker unreachable (`DOCKER_HOST=tcp://127.0.0.1:1`) → `_FailClosedSandbox` → handler **REFUSED** (stdout empty, exit_code=1, "execution refused …"; code NOT run; ERROR log "failing closed: python_sandbox will REFUSE to run" fired). ARM B require_isolation off + real Docker → `DockerSandbox` → `print(2+2)`→"4\n", exit_code=0, 0.375s. This is the strongest deterministic evidence — the ACTUAL production wiring end-to-end.
- **UI** (chat-v2, real Azure gpt-5.2, jamie@acme.com·operator·acme-prod): `print(31337*1337)` → `python_sandbox` tool_call → `approval_requested risk=MEDIUM` HITL pause (the 57.106 risky-action / always_ask flow) → Approve & continue → **real DockerSandbox executes** → answer **"41897569"** (= 31337 × 1337) rendered in the thread + Inspector "BLOCK SEQUENCE: tool python_sandbox + answer 41897569 + verification claim verified · llm_judge" → `verification_passed` (0.99) → `loop_end stop=end_turn`. The 57.137 wiring did NOT break the live tool path (no-regression confirmed user-facing).
- **Why fail-closed is backend-runtime not UI**: forcing Docker-unreachable in a live UI is an artificial setup; the deterministic backend-runtime drive-through exercises the identical production wiring (`_get_shared_sandbox` reads the setting). Same honest "兩者結合" pattern accepted for 57.136.
- **Evidence**: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-137/artifacts/dt-57137-no-regression-python-sandbox.jpeg` + progress.md Day 3 (runtime + UI tables + observed-vs-intended).

## 3. Cross-Category Contracts

**No new cross-category contract** — nothing to register in `17-cross-category-interfaces.md`. `is_structurally_isolated` is a **Cat 2 internal property** added to the EXISTING `SandboxBackend` ABC (whose `execute()` contract is unchanged); `require_isolation` is an internal kwarg on the EXISTING `default_sandbox()` factory; the config read uses the EXISTING settings→registration wire pattern. No new ABC, no new wire event (`WIRE_SCHEMA` stays 25), no new DB table, no SSE stream change. Per the single-source rule, adding a 17.md row would be noise — correctly N/A.

## 4. Open Invariants (deferred / NOT verified in this spike)

- [ ] **`run_skill_script` / skills `_get_default_sandbox` fail-closed** — OUT; it runs BUNDLED (non-LLM-authored) scripts, lower risk. The same `require_isolation` lever can extend later → `AD-SkillScript-Require-Isolation-Phase58`.
- [ ] **Per-tenant isolation profile** (network/fs scope per tenant) — OUT (was Option C; settings/env-only this sprint, anti-AP-6) → `AD-Sandbox-PerTenant-Capability-Profile-Phase58`.
- [ ] **Non-network Docker guarantees benchmarked independently** — read-only fs / cap-drop / non-root / no-bind-mounts are documented but only network egress was measured. The harness corpus can extend (e.g. host-fs-write attempts under read-only rootfs).
- [ ] **Retiring the regex detector** — KEPT as visibility; retirement is a separate decision that would lose human visibility into flagged attempts.
- [ ] **`SANDBOX_REQUIRE_ISOLATION=true` driven through a LIVE UI** — the fail-closed arm was driven via the deterministic backend-runtime path (identical wiring); forcing Docker-unreachable in a live browser is artificial and was intentionally not done.

## 5. Rollback / Fallback

- **If fail-closed is too aggressive**: it is DEFAULT OFF — leave/set `SANDBOX_REQUIRE_ISOLATION` unset/false (the pre-57.137 byte-identical path: Docker-reachable → DockerSandbox, Docker-less → SubprocessSandbox fallback). Zero code change.
- **If the whole mechanism must be reverted**: revert the 4 src edits (`sandbox.py` property + `_FailClosedSandbox` + `default_sandbox(require_isolation)`, `config:150`, `_register_all.py:101-116`, `risky_action_detector.py` docstring) — the unset path IS the original code, so a revert restores exact prior behavior. Estimated effort ~30 min.
- **Sentinel already in place**: the conservative `is_structurally_isolated` default (`False`) means any non-opting backend is treated as non-isolated; `require_isolation=False` default means any caller that doesn't ask explicitly keeps the dev/CI fallback. Misconfiguration degrades to the safe pre-sprint behavior automatically.

## 6. References

- Sprint plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-137-plan.md`
- Sprint checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-137-checklist.md`
- Sprint progress + retrospective: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-137/{progress,retrospective}.md`
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-104-sandbox-detect-to-restrict.md`
- AD source: `claudedocs/1-planning/next-phase-candidates.md` §Research-Derived Candidates (`AD-Guardrail-Detect-To-Restrict`)
- Mirrored scaffold: `backend/scripts/benchmark_correction_hygiene.py` (Sprint 57.136) + `benchmark_judge.py` (Sprint 57.111)
- Related design: `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md` §範疇2 (Tool Layer) + §範疇9 (Guardrails & Safety)
- Prior sandbox work: `claudedocs/5-status/V2-AUDIT-W4P-3-PHASE51-1.md` (W4P-3 audit) + FIX-033 (chat python_sandbox on Docker) + Sprint 52.5 P0 #17 (DockerSandbox)
- Research: the 2026-06-22 consolidated analysis §3 (detect→restrict)

## Modification History

- 2026-06-24: Initial extract from Sprint 57.137 closeout (Day 4) — measured 60% regex escape / 100% Docker containment + env-gated fail-closed structural-isolation guarantee + detector reframe
