# Sprint 57.118 — Checklist (Skills Bundled Scripts, system-bundled + `run_skill_script`: a `Skill.script` field loaded from a sibling `<stem>.py` in `bundled/` (git-authored, immutable — NO tenant code) + a NEW `run_skill_script(skill_name)` Cat-2 tool that runs the skill's SERVER-controlled script through the EXISTING `SandboxBackend` + permission gate, feeding stdout/stderr back; registered via `make_default_executor`'s `skill_registry` opt-in (auto-PASS like `read_skill`); a demo skill+script whose sha256 output is provably script-produced → the FIRST main-flow drive-through of sandboxed execution. Closes the system-bundled leg of `AD-Skills-Bundled-Scripts`; tenant-authored scripts + multi-file resources + an authoring UI deferred. NO DB / NO migration / NO wire (count 24) / NO frontend; DESIGN NOTE 34 (spike))

[Plan](./sprint-57-118-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong; Prong-3 schema N/A — no new table / migration) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `de4fffc7`) — catalogued in progress.md ✅
- [x] **Prong 1 — path verify**: EDIT targets present; NEW free (`bundled/<name>.*` + `34-skills-bundled-scripts.md` absent; CHANGE-085 free); test basenames — `test_skills_registry.py`/`test_skills_tool.py`/`test_skills_overlay.py` all EDIT (no new basename collision); integration = a NEW unique basename
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-permission-gate** (🔴→🟢 #1 risk RESOLVED): `handler.py:588-592` derives the matrix as `{name: PermissionRule(requires_approval = name in escalate_tools) for spec in registry.list()}` — **NO risk/destructive gate** → `run_skill_script` auto-PASSes like `read_skill`; `RiskyActionDetector` only scans the `python_sandbox` `code` arg, not `{skill_name}`. NO explicit capability entry needed; NO scope add
  - [x] **D-sandbox-backend**: `register_builtin_tools` = `make_python_sandbox_handler(sandbox_backend)` (`tools/__init__.py:89-90`); `default_sandbox()` (`tools/sandbox.py:399`) is the factory. **Refinement**: resolve `default_sandbox()` **lazily in the handler** (first call), NOT at per-request executor build (avoids a Docker probe per request)
  - [x] **D-skill-ctor**: `service.py:286` `Skill(name=..., description=..., instructions=...)` keyword construction → a defaulted `script: str | None = None` (last field) is safe; `with_overlay` unaffected
  - [x] **D-from-dir**: `from_dir` globs `*.md` only → a sibling `<stem>.py` is a clean additive `md_path.with_suffix(".py")` read
  - [x] **D-init-exports**: `skills/__init__.py:12-29` re-exports the registry + `read_skill` symbols → add the 2 new ones (mirror)
  - [x] **D-router-thread**: `handler.py:483` already threads `skill_registry` → NO router change (the new tool registers off the same registry)
  - [x] **D-sandbox-skip** (refinement): the integration test **injects `SubprocessSandbox()` directly** (runs on Windows + Docker-less CI, no skip); the drive-through uses `default_sandbox()` (real)
- [x] **Prong 3 — N/A** (no new table / migration / ORM this sprint)
- [x] **D-sandbox-availability**: ✅ Docker reachable (`docker info` → ServerVersion **29.5.2**) → `default_sandbox()` = **DockerSandbox** here → the Day-3 drive-through exercises the REAL Docker sandbox
- [x] **Catalog drift**: 0 scope-invalidating; the #1 risk RESOLVED in the design's favour; 2 scope-REDUCING refinements (lazy `default_sandbox()`; integration injects `SubprocessSandbox()`)
- [x] **Go/no-go**: 🟢 **GO** — design holds end-to-end; no scope shift > 20%

### 0.2 Branch ✅
- [x] `git checkout -b feature/sprint-57-118-skills-bundled-scripts` (from `main` `de4fffc7`)

---

## Day 1 — Backend core: `Skill.script` + the `run_skill_script` tool (US-1, US-2)

### 1.1 `Skill.script` + the sibling-script loader (US-1) ✅
- [x] **`agent_harness/skills/registry.py`** (EDIT): `Skill` += `script: str | None = None` (frozen, keyword-defaulted last); `from_dir` reads a sibling `md_path.with_suffix(".py")` (if `is_file()`; OSError → warn + `None`) into `script`; WHY comment + MHist + Key Components
- [x] **`tests/unit/agent_harness/skills/test_skills_registry.py`** (EDIT +6): `Skill.script` defaults None · `from_dir` loads a sibling `<stem>.py` · no sibling → None · a lone `.py` ignored · the 2 bundled skills → `script=None` · `with_overlay` tenant skills → `script=None`
  - DoD: ✅ registry units pass; mypy 0; existing 2 bundled skills → `script=None`

### 1.2 The `run_skill_script` tool (US-2) ✅
- [x] **`agent_harness/skills/tool.py`** (EDIT): `RUN_SKILL_SCRIPT_TOOL_SPEC` (input `{skill_name}`; `read_only=False`, `risk_level=MEDIUM`, `tags=("skills","exec")`) + `make_run_skill_script_handler(registry, sandbox=None)`: unknown / no-script → message · else `backend.execute(skill.script, timeout_seconds=10, memory_mb=256, network_blocked=True)` → JSON; a process-wide `_get_default_sandbox()` lazy singleton (Day-0 refinement); WHY comment + MHist
- [x] **`agent_harness/skills/__init__.py`** (EDIT): re-export `RUN_SKILL_SCRIPT_TOOL_SPEC` + `make_run_skill_script_handler`
- [x] **`tests/unit/agent_harness/skills/test_skills_tool.py`** (EDIT +4): run over a stub `SandboxBackend` → JSON stdout (SERVER source ran) · unknown skill → message (nothing ran) · no-script skill → message (nothing ran) · spec registers in `ToolRegistryImpl`
  - DoD: ✅ tool units pass; the script source is server-controlled (input is only `skill_name`, no `code`)

---

## Day 2 — Wiring + demo asset + tests (US-3, US-4, US-5)

### 2.1 Chat-path wiring (US-3) ✅
- [x] **`business_domain/_register_all.py`** (EDIT): in `if skill_registry is not None:` (`:295`), after `read_skill`, `registry.register(RUN_SKILL_SCRIPT_TOOL_SPEC)` + `handlers["run_skill_script"] = make_run_skill_script_handler(skill_registry)` (sandbox=None → the lazy `_get_default_sandbox()` singleton in `skills/tool.py`; NO `default_sandbox` import here — Day-0 refinement); import block + WHY comment + MHist + Last Modified
- [x] **`tests/integration/api/test_skills_wiring.py`** (EDIT, consolidated — NOT a new business_domain file): `make_default_executor(skill_registry=)` registers `run_skill_script` + a no-registry negative guard
  - DoD: ✅ registration passes; the registry-derived matrix auto-PASSes it (Day-0 D-permission-gate confirmed; no explicit capability entry)

### 2.2 Demo bundled skill + script (US-4) ✅
- [x] **`agent_harness/skills/bundled/digest.md`** (NEW): frontmatter `name: digest`; body instructs the model to call `run_skill_script("digest")` for the canonical digest (do not compute it itself)
- [x] **`agent_harness/skills/bundled/digest.py`** (NEW): self-contained — `print(hashlib.sha256(b"agent-harness-bundled-skill").hexdigest())` (a runtime computation the LLM cannot fabricate; benign)
  - DoD: ✅ `get_default_skill_registry().get("digest").script` is the `.py` source; the existing 2 skills still load (`script=None`); `digest.py` typechecks clean (mypy 371)

### 2.3 Integration + gate sweep (US-5) ✅
- [x] **`tests/integration/api/test_skills_wiring.py`** (EDIT, consolidated — NOT a new file): `test_run_skill_script_runs_bundled_digest_in_real_sandbox` runs the demo script via a directly-injected **`SubprocessSandbox()`** (deterministic, runs on Windows + Docker-less CI — the Day-0 refinement over a skip) → `stdout.strip()` == the locally-computed sha256. `test_skills_registry.py` +1 (digest has a script)
- [x] Backend gate sweep: mypy `src` **0/371** (+1 `bundled/digest.py`) · black/isort/flake8 0 · `python scripts/lint/run_all.py` (repo root) **10/10** (count 24) · targeted skills+wiring **45 passed** · full pytest **2644 passed, 5 skipped** (+14, 0 del) vs 2630 · `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED · LLM-neutrality + `check_cross_category_import` green
  - Verify: ✅ `python -m mypy src` · `python -m pytest tests/unit/agent_harness/skills tests/integration/api/test_skills_wiring.py -q` (45) · `python scripts/lint/run_all.py`

---

## Day 3 — Drive-through (US-6) — real chat + real sandbox (the FIRST main-flow sandboxed-execution proof)

### 3.1 Clean restart + sandbox-backend probe
- [x] Risk Class E clean restart from repo-root (`Win32_Process` PID/PPID/StartTime orphan sweep + a startup probe); record whether `default_sandbox()` resolved to Docker (daemon reachable) or the Subprocess fallback (WARN logged) — both EXECUTE; note which for the drive-through → **DockerSandbox** (Docker 29.5.2); single python.exe owned :8000, no orphan worker; fresh backend startup-log `pricing loader wired` + `startup complete`

### 3.2 Drive-through (real chat + real sandbox + Playwright/API)
- [x] **Leg (bundled-script execution) PASS**: ask the model to use the demo skill for the canonical digest → it calls `run_skill_script('<name>')` → the sandbox runs `bundled/<name>.py` → the tool returns `{stdout: "<sha256>", exit_code: 0}` → the model reports the digest; **VERIFY** the reported value EQUALS the locally-computed `hashlib.sha256(b"...").hexdigest()` (provably script-produced — the LLM cannot fabricate a sha256). `artifacts/sprint-57-118-*.png` → **PASS**: read_skill→run_skill_script (span 546ms, exit_code 0) → final answer `039e824c…517b8b1e` == local ground truth byte-for-byte; verification 0.99
- [x] Each control driven (real tool execution + a real sandbox subprocess/container, not a fixture/echo): the FIRST main-flow drive-through of sandboxed execution (AP-4 — the primitive actually runs, the value matches). Observed-vs-intended + the backend (Docker/Subprocess) in progress.md → real chat-v2 :3007 + real Azure gpt-5.2 + real Docker container; observed == intended; backend = DockerSandbox
  - DoD: the digest matches the local compute; the tool call + result screenshotted; backend noted

---

## Day 4 — Design note 34 + CHANGE-085 + closeout (SPIKE — design note REQUIRED)

### 4.1 Design note (spike — sprint-workflow §5.5, 8-point quality gate)
- [x] **`docs/03-implementation/agent-harness-planning/34-skills-bundled-scripts.md`** (NEW): the spike-extract design note (Spike Summary / Decision Matrix [system-bundled vs tenant-authored; dedicated tool vs reuse python_sandbox] / Verified Invariants with file:line / Cross-Category Contracts [Cat 5 Skill.script + Cat 2 run_skill_script + the Cat 2 SandboxBackend reuse] / Open Invariants [tenant-authored / resources / args deferred] / Rollback / References / MHist); 8-point quality gate self-check in retrospective.md → DONE (8/8 gate passed, ~96% verified ratio)

### 4.2 CHANGE-085
- [x] **`claudedocs/4-changes/feature-changes/CHANGE-085-skills-bundled-scripts.md`** (1-page, incl. the drive-through)

### 4.3 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`skills-bundled-script-spike` 0.60 1st data point; ratio + KEEP/re-point note) + the 8-point design-note gate record + progress.md final → ratio ~0.92 IN band, KEEP 0.60
- [x] Final gate sweep: mypy 0/**371** (+1 digest.py) · run_all 10/10 (count 24) · full pytest **2644 passed, 5 skipped** (+14) vs 2630 · Vitest 873 unchanged · mockup 51 holds (no frontend)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated (minimal touch); MEMORY.md quality pointer + memory subfile `project_phase57_118_skills_bundled_scripts.md`; next-phase-candidates — `AD-Skills-Bundled-Scripts` system-bundled leg CLOSED + 57.118 carryover (tenant-authored scripts + multi-file resources + authoring-UI + script args carried) + remaining Skills ADs (119 authoring-UI / 120 inspector-metadata / 121 slash-menu-mockup) carried; sprint-workflow matrix `skills-bundled-script-spike` 0.60 1st-point add; 17.md — Day-0 decide if `run_skill_script` ToolSpec warrants a §registry line → **17.md NO new contract** (one more ToolSpec over the existing `build_handler(skill_registry=)` seam; documented in design note 34 §4)
- [x] **Anti-pattern self-check** (retro Q5/Q7): AP-4 (drive-through proves the sandbox actually runs the script — value matches local compute, not a fixture) · AP-2 (Skill.script → run_skill_script → executor register → chat; main flow) · AP-3 (Skill.script + loader in Cat 5 skills; the tool in Cat 2 skills/tool; sandbox reuse in Cat 2 tools) · AP-6 (system-bundled-only, no speculative tenant-script/multi-file/UI; reuses the existing sandbox) — target 0 violations → **0 violations** (retro Q5)
- [ ] PR (push + open on user authorization); CI → merge on green (gh-verified MERGED before main sync)
