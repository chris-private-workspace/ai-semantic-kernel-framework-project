# Sprint 57.118 Retrospective — Skills Bundled Scripts (system-bundled `run_skill_script`)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-118-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-118-checklist.md) · [Progress](./progress.md) · CHANGE-085 · [Design note 34](../../../agent-harness-planning/34-skills-bundled-scripts.md)

**Closed**: 2026-06-15 · **Branch**: `feature/sprint-57-118-skills-bundled-scripts` · **Base**: `main` `de4fffc7` (post-#292)

---

## Q1 — What was delivered?

The Skills epic's **executable half** (closes the system-bundled leg of `AD-Skills-Bundled-Scripts`, the 4th Skills slice + cc-parity row 9's last missing piece). A SYSTEM-BUNDLED skill may now ship a sibling `<stem>.py` next to its `SKILL.md`; the model runs it on demand via a new Cat-2 `run_skill_script(skill_name)` tool, through the SAME `SandboxBackend` that powers `python_sandbox`. `Skill.script: str | None` (Cat 5, loaded by `from_dir` from the sibling file — SERVER-controlled, never an LLM arg); `RUN_SKILL_SCRIPT_TOOL_SPEC` + `make_run_skill_script_handler` with a lazy process-wide sandbox singleton (Cat 2); the `skill_registry` opt-in in `make_default_executor` now registers it (auto-PASS via the risk-blind permission matrix); a demo `bundled/digest.{md,py}` (prints a runtime sha256 the LLM cannot fabricate). NO DB / migration / wire event (count 24) / codegen / frontend. Tests +14 backend. Drive-through PASS in a REAL Docker sandbox.

## Q2 — Estimate accuracy / calibration

- Scope class **`skills-bundled-script-spike` 0.60 — NEW, 1st data point**.
- Bottom-up est ~6.5 hr → class-calibrated commit ~3.9 hr (mult 0.60, 3-segment form; parent-direct `agent_factor` 1.0).
- Actual ≈ 3.6 hr — ratio **~0.92 IN band**. The slice ran clean: the Day-0 三-prong RESOLVED the #1 risk (D-permission-gate) in the design's favour AND produced 2 scope-REDUCING refinements (lazy `default_sandbox()` singleton over per-request probe; integration injects `SubprocessSandbox()` directly over a Docker-availability skip). The executor + integration test consolidated into the existing `test_skills_wiring.py` (1 fewer new file than plan).
- **KEEP 0.60** (1st data point; pending 2-3 sprint validation). The class sits at the same 0.60 as `subagent-child-loop-spike` — the markdown/frontmatter loader + a real bundled script + the sandbox reuse put it a touch above a pure-wiring spike, but it reuses the proven 57.113 registry/opt-in machinery + the existing `SandboxBackend`, so 0.60 (not higher) held. If a 2nd `skills-bundled-script-spike` (e.g. the tenant-authored leg) diverges > 30%, re-point.
- **Agent-delegated: no** (parent-direct; plan said `partial` but no code-implementer agent was used — the surface was small + precise across the known Skills file set, the only novelty being the sandbox-reuse + the lazy singleton, both better kept parent-direct). `agent_factor` 1.0.

## Q3 — What went well?

- **Day-0 三-prong RESOLVED the whole risk profile before code**: the #1 risk (a destructive/risk permission gate blocking a MEDIUM-risk tool on the chat path) dissolved — `handler.py:588-592` derives the matrix risk-blind from `registry.list()`, so `run_skill_script` auto-PASSes exactly like `read_skill`; no `capability_matrix.yaml` entry. Prong-3 N/A (no new table). The probe also confirmed Docker reachable (29.5.2) → a REAL-Docker drive-through, not the Subprocess fallback.
- **Reusing the existing `SandboxBackend` was the right boundary**: `run_skill_script` is one more `ToolSpec` over the same sandbox `python_sandbox` already trusts — no new isolation surface, no new ABC, no 17.md contract. The dedicated tool (vs telling the model to paste the script into `python_sandbox`) keeps the source server-controlled so the value is provably script-produced.
- **The digest demo made the drive-through decisive**: `digest.py` prints a runtime sha256 the LLM cannot fabricate, so the reported value matching the local `hashlib.sha256(...).hexdigest()` byte-for-byte is the FIRST main-flow proof that the sandbox ACTUALLY executed a bundled script — not a Potemkin (the alternative — a model reciting a plausible value — is impossible for a sha256).
- **2 Day-0 scope-reducing refinements held**: the lazy process-wide `_get_default_sandbox()` singleton avoids a Docker probe per chat request (correctness, not just speed), and injecting `SubprocessSandbox()` into the integration test made it deterministic on Windows + Docker-less CI (no skip) while the drive-through still exercised the real Docker path.

## Q4 — What to improve / lessons

- **Risk Class E clean-restart was essential and smooth**: the running backend (PID 28700) was 57.117-vintage and the digest skill is a NEW bundled file → a restart was mandatory (a `--reload` worker would NOT re-run the registry load). The `Win32_Process` sweep confirmed a single python.exe owned :8000 (no orphan spawn-worker), so a clean kill + fresh startup sufficed; the startup-log probe (`pricing loader wired` + `startup complete`) confirmed the new code loaded before driving. No false "it doesn't work" detour (the 57.97 orphaned-worker trap did not recur because the process tree was clean this time).
- **Plan said agent-delegated `partial`; reality was parent-direct** — small precise surface, kept parent-direct. The plan-time `Agent-delegated:` field correctly surfaced the choice, but the actual call (no agent) is the honest record (`agent_factor` 1.0). Lesson: the `TBD-Day-1-decision` value would have been more accurate than `partial` for a spike whose delegation hinges on Day-0 risk findings.

## Q5 — Anti-pattern audit (04-anti-patterns.md)

- **AP-1** (pipeline-as-loop) N/A. **AP-2** (side-track): ✅ the whole path rides 主流量 — `Skill.script` (loaded by `from_dir`) → `run_skill_script` tool → executor register → chat → drive-through; nothing dead. **AP-3** (cross-dir scatter): ✅ `Skill.script` + the loader in Cat 5 `skills/registry.py`; the tool in Cat 2 `skills/tool.py`; the sandbox reuse in Cat 2 `tools/sandbox.py`; the wiring in business_domain — each piece in its own category, `check_cross_category_import` green (skills→tools is Cat2→Cat2, legal). **AP-4** (Potemkin): ✅ the drive-through proves the sandbox ACTUALLY runs the script — the reported sha256 equals the local compute byte-for-byte (a fixture/recited value is impossible for a runtime hash); the tool is wired (registered + executed), the label real (`run_skill_script` shows the true `skill_name` input + the real JSON output), the result renders in both the turn block and the Loop visualizer. **AP-6** (speculative abstraction): ✅ system-bundled-ONLY (no tenant-script storage / multi-file resources / authoring UI / script args), reuses the existing `SandboxBackend` (no new isolation layer) — every speculative extension explicitly deferred (design note 34 §5). **AP-7/8** N/A. **AP-9** (verification): the in-loop llm_judge passed (0.99) on the drive-through. **AP-10** (mock vs real): ✅ the integration test's injected `SubprocessSandbox` + the drive-through's real `DockerSandbox` both EXECUTE the same script and agree on the digest. **AP-11** (version suffix): ✅ none.
- 0 violations.

## Q6 — Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/34-skills-bundled-scripts.md`
**Verified ratio (estimated)**: ~96%
**8-Point Quality Gate**:
- [x] 1. Section headers map to the spike user stories (US-1..US-6 as wired)
- [x] 2. Every technical claim has a file:line (`registry.py:54-68/130-160`, `tool.py:114-202/153-161`, `_register_all.py:306-310`, `handler.py:588-592`)
- [x] 3. Decision matrices (trust model: system-bundled vs tenant-authored; tool: dedicated `run_skill_script` vs reuse `python_sandbox`) with chosen + rejected reasons
- [x] 4. Verification commands (the skills+wiring pytest selector; the drive-through reproduce with the local sha256 compare)
- [x] 5. Test fixtures referenced (`bundled/digest.{md,py}` are real fixtures; `_StubSandbox` for unit cases)
- [x] 6. Open invariants demarcated (tenant-authored / multi-file / args / deny-list scan / authoring-UI — all "NOT verified here")
- [x] 7. Rollback path (additive + opt-in; revert 2 code commits → exact 57.117 state, no migration; Subprocess fallback already in place)
- [x] 8. 17.md cross-ref (explicit "NO new contract" decision with the 57.113/114/115 precedent)

**Reviewer pass**: self-review (parent-direct spike).

## Q7 — Carryover + Closeout checklist

- `AD-Skills-Bundled-Scripts` **system-bundled leg CLOSED**; the **tenant-authored leg** is carried (🟡 — needs `tenant_skills.script` + sandbox quota + deny-list scan of the tenant source + abuse/billing controls; a tenant becomes an untrusted code author). **Multi-file script resources** + **script input/args** + **automated deny-list scan of bundled scripts** carried (🟢 YAGNI; design note 34 §5).
- Remaining Skills epic ADs (3 left in the "順序執行" sequence): `AD-Skills-Authoring-UI` (57.119) · `AD-ChatV2-Inspector-Turn-Metadata-Wire` (57.120) · `AD-Skills-SlashMenu-Mockup` (57.121 — ⚠️ needs a mockup authored first).
- **Closeout**: [x] CHANGE-085 · [x] **design note 34** (spike — 8-point gate passed above) · [x] retro Q1-Q7 + calibration (`skills-bundled-script-spike` 0.60 1st data point) · [x] navigators (CLAUDE.md Current-Sprint + Last-Updated / MEMORY.md pointer + subfile / next-phase-candidates `AD-Skills-Bundled-Scripts` system-bundled CLOSED + tenant-leg carried / sprint-workflow matrix `skills-bundled-script-spike` 0.60 1st-point) · [x] 17.md N/A (no new contract — explicit decision in design note §4) · [ ] PR (push on user authorization → CI green → merge, gh-verified MERGED before main sync)
