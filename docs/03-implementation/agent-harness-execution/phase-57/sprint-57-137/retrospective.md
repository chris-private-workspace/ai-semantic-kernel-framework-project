# Sprint 57.137 Retrospective — sandbox detect→restrict (fail-closed isolation + escape-rate spike)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-137-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-137-checklist.md) · [Progress](./progress.md)

**Closed**: 2026-06-24 · **Branch**: `feature/sprint-57-137-sandbox-detect-to-restrict` · **Base**: main `ba4c5c13`

---

## Q1. What was delivered?

A thin evidence-first spike closing `AD-Guardrail-Detect-To-Restrict` (research #3). The Cat 9 `RiskyActionDetector` regex deny-list over `python_sandbox` code was reframed from "the boundary" to ESCALATE-for-visibility, and the structural DockerSandbox isolation was made **mandatory** via an env-gated fail-closed lever (`SANDBOX_REQUIRE_ISOLATION`, DEFAULT OFF) that refuses execution on a non-isolating backend instead of silently degrading to the production-unsafe SubprocessSandbox. A permanent real-Docker escape harness (`benchmark_sandbox_escape.py` + 10-case corpus + 13 CI-safe tests) MEASURED the gap before any flip: **regex_escape_rate 60% · docker_containment_rate 100%** → the regex is redundant-for-containment under Docker, so restrict-must-be-mandatory + detect-stays-visibility. Backend-only, NO migration / NO new wire event / NO frontend. CHANGE-104 + design note 41.

## Q2. Calibration — estimate vs actual

- **Scope class**: `guardrail-restrict-spike` **0.60** (NEW, 1st data point). Analogous to `verification-context-hygiene-spike` 0.60 (57.136) + `verification-in-loop-spike` 0.60 (57.98) — a Cat 2/9 structural-guardrail spike paired with a measurement harness + an env-gated surgical change + drive-through.
- **Agent-delegated: no** (parent-direct; the value is precise security judgment of escape-vs-containment evidence + a surgical Cat 2 fail-closed change, not mechanical pattern reuse). `agent_factor` 1.0 → 3-segment form.
- **Estimate**: bottom-up ~12 hr → class-calibrated commit ~7.2 hr (mult 0.60).
- **Actual**: ~7 hr (Day 0 三-prong ~1 · Day 1 property+config+resolver+unit ~2 · Day 2 harness+corpus+CI test+real-Docker run+reframe ~2.5 · Day 3 drive-through ~1 · Day 4 closeout ~1.5, overlapping same-day). **Ratio actual/committed ≈ 0.97 — IN band.** Single data point → KEEP 0.60 pending 2–3 sprint validation. If a 2nd `guardrail-restrict-spike` diverges > 30%, re-point.
- The Day-0 三-prong found **zero drift** (every file:line anchor confirmed) → no scope shift; the fix composed existing machinery (the `default_sandbox()` fallback parameterized + one ABC property + the `benchmark_correction_hygiene.py` scaffold + the 57.135 DEFAULT-OFF env pattern). The ceremony-not-code-accelerated risk flagged in the plan §7 did NOT materialize — the code (one property + a refusing backend + a 3-way branch + a harness) was substantial enough that the drive-through + design-note ceremony didn't pull the ratio up.

## Q3. What went well?

- **Evidence-first discipline held**: measured the regex escape + Docker containment with a real harness BEFORE relying on the structural boundary. The 60/100 number is what justifies making Docker mandatory + reframing the regex — a blind flip would have repeated the evidence-free risk 57.136's discipline avoided.
- **Day-0 三-prong = zero drift, fast green**: all 6 D-rows confirmed on the first pass (tuple importable / sole fallback site / ABC + 2 impls / no config collision / register site / Docker reachable). Scope-shift 0% → straight to Day 1.
- **Provider-neutral by construction**: the fail-closed gate reads `is_structurally_isolated` (a property), NOT `isinstance` — a future isolating backend just returns `True`. The structural decision lives entirely in Cat 2; the registration layer only reads the setting.
- **DEFAULT OFF = zero rollback risk**: dev/CI keep the SubprocessSandbox fallback byte-unchanged; only an explicit prod opt-in fail-closes. The conservative `is_structurally_isolated` default (`False`) + `require_isolation=False` default mean any misconfiguration degrades to the safe pre-sprint path automatically.
- **Regex KEPT, not retired**: reframed as visibility (a human still sees a flagged attempt + tenants keep `extra_patterns`) with a byte-unchanged `check()` → 23 risky tests green, no regression. The reframe is docstring-only.
- **Drive-through "兩者結合" was honest**: backend runtime (deterministic, real `_get_shared_sandbox`→`default_sandbox`→handler path) proved the fail-closed refusal (code not run); UI (real chat-v2 + real Azure + real DockerSandbox → "41897569") proved no-regression. We did NOT force Docker-unreachable in a live UI (artificial); we said so plainly.
- **Partial-gate lesson from 57.136 applied**: Day 1 ran the FULL test surface of every edited src file (`test_sandbox.py` + `test_shared_sandbox.py` + `test_partial_swap.py`), not just the new tests — no regressions surfaced late.

## Q4. What to improve next sprint?

- **Escape corpus breadth**: only NETWORK egress was benchmarked (the cleanest single boundary). The other Docker guarantees (read-only fs / cap-drop / non-root / no-bind-mounts) are documented but not each independently measured. The harness is permanent + extensible — a future sprint wanting a fuller number can add host-fs-write / cap attempts to the corpus.
- **Real-isolation-fail-on-demand in a live UI** remains a gap (kin to 57.136's real-fail-on-demand): forcing Docker-unreachable in a live browser is artificial, so the fail-closed arm is driven via the backend-runtime path. A reusable "inject a non-isolating backend for one chat-v2 session" lever would make future fail-closed UI drive-throughs first-class.

## Q5. Anti-pattern self-check (04-anti-patterns / 11-point)

- **AP-1** (pipeline-as-loop): N/A — no loop logic changed; the sandbox is a tool backend.
- **AP-2** (orphan/dead code): ✅ `_FailClosedSandbox` is reachable via the `require_isolation` branch + tested; no placeholder/dead path. The regex detector is KEPT (live), not orphaned.
- **AP-3** (cross-dir scatter): ✅ Cat 2 change in `sandbox.py`; Cat 4 setting in `core/config`; registration read in `_register_all.py`; Cat 9 reframe in `risky_action_detector.py`; Cat 9 eval in `scripts/` + `tests/`. Each in its home.
- **AP-4** (Potemkin): ✅ the fail-closed refusal is runtime-driven (not just gated); the harness produces a real number; the property actually gates the backend choice (proven — ARM A resolves `_FailClosedSandbox`, refuses; ARM B resolves DockerSandbox, runs).
- **AP-6** (future-proofing): ✅ per-tenant isolation profile explicitly OUT (→ Phase 58 AD); skills `run_skill_script` fail-closed OUT (→ Phase 58 AD); settings/env-only this sprint — no speculative layer.
- **AP-8** (no centralized PromptBuilder): N/A — no prompt assembly.
- **AP-11** (version suffix / misnaming): ✅ no `_v2`/`_old`; `is_structurally_isolated` / `require_isolation` / `_FailClosedSandbox` name exactly what they do.
- **v2 lints**: 10/10 (incl. check_llm_sdk_leak — the harness uses the Cat 2 SandboxBackend ABC, no LLM).

## Q6. Process lesson (for the matrix / future plans)

**The plan's ceremony-not-code-accelerated risk flag (plan §7) is a useful pre-registration even when it doesn't fire.** Plan §7 noted "if the code lands much smaller than estimated the drive-through + design-note ceremony may pull the ratio up." It did NOT — the code was substantial (a property on 3 classes + a refusing backend + a 3-way factory branch + a ~150-line harness + a 10-case corpus). The lesson is the inverse of 57.120/57.122's re-points: a spike with a real-code core (vs a ~10-line surface change) calibrates cleanly at the spike multiplier (0.60) and does NOT need the ceremony-heavy 0.85 those tiny-code sprints required. The distinguisher for next time: **estimate the code-hours honestly — if the core is >~3 hr of real implementation, the spike multiplier holds; if it's a ~10-line surface change wrapped in full ceremony, expect ~0.85.** (Recorded; the matrix row notes this.)

## Q7. Carryover / open items

- `AD-SkillScript-Require-Isolation-Phase58` — extend the `require_isolation` lever to `run_skill_script` / skills `_get_default_sandbox` (bundled non-LLM scripts, lower risk; registered in next-phase-candidates).
- `AD-Sandbox-PerTenant-Capability-Profile-Phase58` — per-tenant network/fs isolation scope (was Option C; settings/env-only shipped).
- Non-network Docker guarantees benchmarked independently (read-only fs / cap-drop / non-root) — the harness corpus can extend; not measured this sprint.
- `AD-Guardrail-Detect-To-Restrict` itself — **CLOSED** (gap measured: 60% escape / 100% containment; fail-closed lever shipped; detector reframed).

---

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/41-sandbox-detect-to-restrict-design.md`
**Verified ratio (estimated)**: ≥ 95% (every claim file:line-anchored; the escape/containment is a reproducible real-Docker run)
**8-Point Quality Gate**:
- [x] 1. Section header maps to US
- [x] 2. file:line references
- [x] 3. Decision matrix (the regex-escape vs Docker-containment table)
- [x] 4. Verification command (per invariant + escape-harness rerun)
- [x] 5. Test fixture (`sandbox_escape_cases.yaml` + real-Docker run note)
- [x] 6. Open-invariant boundary
- [x] 7. Rollback path (env-gate OFF + revert; the unset path IS the pre-sprint code)
- [x] 8. 17.md cross-ref (NO new contract — justified N/A)

**Reviewer pass**: self-review (solo-dev)
