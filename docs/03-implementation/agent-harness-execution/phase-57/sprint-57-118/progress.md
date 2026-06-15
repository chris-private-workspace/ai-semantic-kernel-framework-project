# Sprint 57.118 Progress — Skills Bundled Scripts (system-bundled, model-invoked via `run_skill_script`)

**Branch**: `feature/sprint-57-118-skills-bundled-scripts` (from `main` `de4fffc7`)
**Plan**: [`sprint-57-118-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-118-plan.md) · **Checklist**: [`sprint-57-118-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-118-checklist.md)
**Slice**: Skills System epic — bundled scripts (system-bundled leg; closes 1st half of `AD-Skills-Bundled-Scripts`; item 2 of the 5 pending Skills ADs). SPIKE → design note 34.

---

## Thin spike (pre-plan recon) + scope alignment — 2026-06-15

**3 Explore-agent spikes** (tool-exec/sandbox infra · Skills current state · CC bundled-scripts reference) + direct reads established the ground truth:
- **The sandbox primitive ALREADY EXISTS on the 主流量**: `python_sandbox` Cat-2 tool (`tools/exec_tools.py:27-97`) over a `SandboxBackend` (`tools/sandbox.py`) — `DockerSandbox` (52.5 P0 #17, real OS isolation) when a daemon is reachable via `default_sandbox()` (`:399`), else legacy `SubprocessSandbox`. Gated by `RiskyActionDetector` (Cat 9 STRING deny-list, ESCALATE) + the registry-derived permission gate. → bundled scripts is NOT greenfield sandbox work.
- **A skill is text-only today**: `Skill(name, description, instructions)` (`registry.py:53-59`); bundled = `bundled/*.md`; tenant = `tenant_skills` text columns. No `script`/resource anywhere.
- **CC bundled scripts** = a skill folder carries an executable script the model can RUN (deterministic tooling vs prose re-derivation).

**Scope aligned with user** (AskUserQuestion 2026-06-15): (1) authoring = **System-bundled only** (git-authored, code-reviewed, immutable — NO tenant-authored arbitrary code); (2) execution = **a dedicated `run_skill_script(skill_name)` tool** (the model names the skill; the harness runs the SERVER-controlled script via the existing sandbox; the source never passes through the LLM). Reuse the existing sandbox + permission gate; one demo skill + script (a sha256 output provably script-produced); NO DB / NO wire / NO frontend.

---

## Day 0 — Plan-vs-Repo Verify (三-prong; Prong-3 schema N/A — no new table) + Branch — 2026-06-15

### Prong 1 — path verify (against `main` HEAD `de4fffc7`)
- ✅ EDIT targets present: `skills/registry.py` · `skills/tool.py` · `skills/__init__.py` · `business_domain/_register_all.py` · `skills/bundled/` (`code-review.md` + `summarize.md`, no sibling `.py` today).
- ✅ NEW free: `bundled/<name>.md`/`<name>.py` absent; `34-skills-bundled-scripts.md` absent; **CHANGE-085 free** (084 = 57.117 quota).
- ✅ **Test basenames** (the 57.109/114 unique-basename lesson): `tests/unit/agent_harness/skills/` has `test_skills_registry.py` · `test_skills_tool.py` · `test_skills_overlay.py` · `test_render_skill_instructions.py` — all EDIT targets (NO new basename collision for the registry/tool/overlay cases). The integration test is a NEW unique basename (e.g. `test_run_skill_script_sandbox.py`).

### Prong 2 — content verify (drift findings)
- **D-permission-gate** 🔴→🟢 **RESOLVED (#1 risk cleared)**: `handler.py:588-592` derives the chat permission matrix purely as `{spec.name: PermissionRule(requires_approval = spec.name in escalate_tools) for spec in registry.list()}` — **NO `risk_level`/`destructive` gate**. A registered `run_skill_script` (via the `skill_registry` opt-in) → `requires_approval=False` → **auto-PASS, exactly like `read_skill`**. The `RiskyActionDetector` is a SEPARATE Cat-9 guardrail that scans the `python_sandbox` `code` arg (+ tenant patterns) — it does NOT see `run_skill_script` (whose args are only `{skill_name}`, no code). → NO explicit `capability_matrix` entry needed; the design holds, NO scope add.
- **D-sandbox-backend** 🟢: `register_builtin_tools` (`tools/__init__.py:89-90`) = `make_python_sandbox_handler(sandbox_backend)`; `default_sandbox()` (`tools/sandbox.py:399`, exported in `tools.sandbox.__all__`) is the Docker-or-Subprocess factory. **Refinement** (scope-reducing): `default_sandbox()` probes the Docker daemon to choose a backend, and `make_default_executor` runs PER chat request → resolve `default_sandbox()` **lazily inside the handler closure** (first `run_skill_script` call, cached), NOT at per-request executor build → avoids a Docker probe per request.
- **D-skill-ctor** 🟢: the tenant overlay constructs `Skill(name=row.name, description=row.description, instructions=row.instructions)` (`platform_layer/skills/service.py:286`, keyword args) → adding `script: str | None = None` as the last defaulted field keeps it working (`script` defaults `None`). `with_overlay` (`registry.py:113-119`) unaffected.
- **D-from-dir** 🟢: `from_dir` (`registry.py:121-153`) globs `*.md` only → a sibling `<stem>.py` is a clean additive `md_path.with_suffix(".py")` read; a lone `.py` is ignored.
- **D-init-exports** 🟢: `skills/__init__.py:12-29` re-exports the registry symbols + `READ_SKILL_TOOL_SPEC` + `make_read_skill_handler` → add `RUN_SKILL_SCRIPT_TOOL_SPEC` + `make_run_skill_script_handler` (mirror).
- **D-router-thread** 🟢: `handler.py:483` already threads `skill_registry` into `make_default_executor` (+ `force_load_skill:288`) → NO router change; the new tool registers off the same registry.
- **D-sandbox-skip** 🟢 (refinement): instead of a Docker-availability skip, the **integration test injects `SubprocessSandbox()` directly** (runs on Windows + Docker-less CI, deterministic, no skip); the Day-3 drive-through uses `default_sandbox()` (the real prod-ish path).

### Prong 3 — N/A (no new table / migration / ORM)

### Extra — sandbox availability on this dev box
- ✅ **Docker IS reachable** (`docker info` → ServerVersion **29.5.2**, exit 0) → `default_sandbox()` resolves to **DockerSandbox** (real `--cap-drop=ALL` / `read_only` / `network=none` / non-root) here → the Day-3 drive-through exercises the REAL Docker sandbox (the strongest proof), not the Subprocess fallback.

### Catalog — drift summary
- 0 scope-invalidating drifts. The #1 risk (D-permission-gate) is RESOLVED in the design's favour (auto-PASS, no explicit capability). 2 scope-REDUCING refinements: (a) lazy `default_sandbox()` in the handler (avoid per-request Docker probe); (b) integration test injects `SubprocessSandbox()` directly (no skip needed). Baselines to re-verify at the gate: pytest 2630+5skip · wire 24 · Vitest 873 · mockup 51 · mypy 0/370 · run_all 10/10.

### Go/no-go: 🟢 **GO** — the design holds end-to-end (register `run_skill_script` via the `skill_registry` opt-in → auto-PASS; reuse `default_sandbox()` lazily; the registry loads a sibling `<stem>.py`; Docker is available for a real-sandbox drive-through); no scope shift > 20%.

### Branch
- ✅ `git checkout -b feature/sprint-57-118-skills-bundled-scripts` (from `main` `de4fffc7`)

---

## Day 1 — Backend core: `Skill.script` + the `run_skill_script` tool (US-1, US-2) — 2026-06-15

**US-1 `Skill.script` + sibling loader** (`agent_harness/skills/registry.py`): `Skill` += `script: str | None = None` (frozen, keyword-defaulted last → the tenant overlay's `Skill(name, description, instructions)` construction in `service.py:286` is unchanged, `script` defaults `None`); `from_dir`, after the name/description/body validation, reads a sibling `md_path.with_suffix(".py")` (`is_file()`; OSError → warn + `None`) into `script`. WHY comment (system-bundled-only trust boundary) + MHist + Key Components.

**US-2 `run_skill_script` tool** (`agent_harness/skills/tool.py`): `RUN_SKILL_SCRIPT_TOOL_SPEC` (input `{skill_name}` required, `additionalProperties:False`; `read_only=False`, `risk_level=MEDIUM`, `hitl_policy=AUTO`, `tags=("skills","exec")`) + `make_run_skill_script_handler(registry, sandbox=None)`: unknown skill → recoverable message · `script is None` → recoverable message · else `backend.execute(skill.script, timeout_seconds=10, memory_mb=256, network_blocked=True)` → JSON `{stdout,stderr,exit_code,duration_seconds,killed_by_timeout}` (mirrors `exec_tools.make_python_sandbox_handler`). A process-wide `_get_default_sandbox()` lazy singleton resolves `default_sandbox()` ONCE (first call) — NOT per request (the Day-0 refinement); tests inject a stub backend. `__init__.py` re-exports the 2 new symbols.

**Tests** (`test_skills_registry.py` +6, `test_skills_tool.py` +4): registry — `Skill.script` defaults None / `from_dir` loads a sibling `<stem>.py` / no-sibling → None / a lone `.py` is ignored / the 2 bundled skills have `script=None` / `with_overlay` tenant skills `script=None`; tool — run via a stub `SandboxBackend` returns the JSON stdout + the SERVER script source ran (not an LLM arg) / unknown skill → message (nothing ran) / no-script skill → message (nothing ran) / the spec registers in `ToolRegistryImpl`.

**Gate**: mypy `src` **Success 0/370** · black/isort/flake8 0 (changed files; 5 header E501s fixed) · `python scripts/lint/run_all.py` (from REPO ROOT) **10/10** — incl. `check_cross_category_import` (skills/tool.py → `agent_harness.tools.sandbox` is Cat 2 → Cat 2, allowed) + `check_event_schema_sync` (count 24 unchanged) · targeted `tests/unit/agent_harness/skills` **32 passed**. `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.

> Tooling note: `scripts/lint/run_all.py` lives at REPO ROOT (not `backend/`), and must be run WITHOUT a masking `| tail` (a pipe makes the pipeline exit 0 even on a python file-not-found). Run: `cd <repo-root> && python scripts/lint/run_all.py`.

## Day 2 — Wiring + demo skill/script + integration (US-3, US-4, US-5) — 2026-06-15

**US-3 chat-path wiring** (`business_domain/_register_all.py`): in the `if skill_registry is not None:` opt-in block (`:295`), after `read_skill`, `registry.register(RUN_SKILL_SCRIPT_TOOL_SPEC)` + `handlers["run_skill_script"] = make_run_skill_script_handler(skill_registry)` (sandbox=None → the lazy `_get_default_sandbox()` singleton in `skills/tool.py`; NO `default_sandbox` import here, NO per-request Docker probe). Import block + the WHY comment + MHist + Last Modified updated. The registry-derived permission matrix auto-PASSes it (Day-0 D-permission-gate).

**US-4 demo skill + script**: `bundled/digest.md` (frontmatter `name: digest` + instructions: "call `run_skill_script("digest")` … report the exact hex digest") + `bundled/digest.py` (`print(hashlib.sha256(b"agent-harness-bundled-skill").hexdigest())` — a RUNTIME computation the LLM cannot fabricate; benign, no risky calls). The 2 existing skills (no sibling `.py`) stay `script=None`; adding a 3rd bundled skill is safe (no test asserts exactly-2; catalog assertions use subset/substring).

**US-5 integration + executor registration**: `test_skills_wiring.py` +3 — `make_default_executor(skill_registry=)` registers `run_skill_script` (+ a no-registry negative guard) AND `test_run_skill_script_runs_bundled_digest_in_real_sandbox`: the bundled `digest` skill's script runs in a **REAL** `SubprocessSandbox` (injected directly — deterministic, runs on Windows + Docker-less CI) and `stdout.strip()` EQUALS the locally-computed `hashlib.sha256(b"agent-harness-bundled-skill").hexdigest()` (the genuine-execution proof at the test layer). `test_skills_registry.py` +1 — the bundled `digest` skill has a non-None `script`.

**Gate**: mypy `src` **Success 0/371** (+1 = `bundled/digest.py` typechecks clean) · black/isort/flake8 0 (changed files; 2 header E501s fixed) · `python scripts/lint/run_all.py` (repo root) **10/10** (count 24) · targeted `tests/unit/agent_harness/skills` + `tests/integration/api/test_skills_wiring.py` **45 passed** (incl. the real-SubprocessSandbox digest run) · full pytest **2644 passed, 5 skipped** (+14, 0 del) vs 2630. `loop.py`/`events.py`/`sse.py`/`event_wire_schema`/codegen/migration UNTOUCHED.

## Day 3 — Drive-through (real UI + real backend + real LLM + REAL Docker sandbox) — 2026-06-15

**Setup (Risk Class E clean restart)**: killed the stale 57.117 backend pair (uvicorn PID 28700 + its pwsh wrapper 28864) — `Win32_Process` sweep confirmed a SINGLE python.exe owning :8000 (no orphan `multiprocessing.spawn` worker), port freed cleanly. Started a fresh 57.118 backend from repo root (`PYTHONPATH=backend/src python -m uvicorn api.main:app --env-file .env`, no `--reload`, deterministic); startup log `pricing loader wired` + `startup complete` + `Uvicorn running on :8000`. Confirmed the new code loaded: `GET /api/v1/chat/skills` (dev-login acme-skills) lists **`digest`** ("Compute the canonical SHA-256 digest by running this skill's bundled script.") alongside code-review / summarize / release-notes. `default_sandbox()` resolves to **DockerSandbox** here (Docker 29.5.2).

**Ground truth (local)**: `hashlib.sha256(b"agent-harness-bundled-skill").hexdigest()` = `039e824cfd166d0c491ca12b290e28b6da2d89b0eaceca4b33a57231517b8b1e`.

**Drive (real chat-v2 :3007 UI + real Azure gpt-5.2)**: dev-login acme-skills (jamie@acme.com), mode `real_llm`, prompt: *"Use the digest skill to compute the canonical SHA-256 digest by running its bundled script, then report the exact hex digest it prints."* The agent loop ran 3 turns:

| Turn | Tool call (live SSE / Loop visualizer) | Result |
|------|----------------------------------------|--------|
| 0 | `read_skill` `{"name":"digest"}` | success — returned the digest skill instructions ("call `run_skill_script("digest")` … report it exactly") |
| 1 | `run_skill_script` `{"skill_name":"digest"}` | success, span `agent_loop.tool.run_skill_script` **duration_ms 546** — output JSON `{"stdout":"039e824c…517b8b1e\n","stderr":"","exit_code":0,"duration_seconds":0.484,"killed_by_timeout":false}` |
| 2 | (no tool calls) | final answer `039e824cfd166d0c491ca12b290e28b6da2d89b0eaceca4b33a57231517b8b1e` + `verification_passed llm_judge score=0.99` → `loop_end stop=end_turn` |

**Observed vs intended flow**: intended = model self-selects the digest skill → reads its instructions → calls the new `run_skill_script` tool → the bundled script runs in the sandbox → the model reports the script's exact stdout. Observed = EXACTLY that, end-to-end, with **zero** prompt scaffolding beyond naming the skill. The reported digest **equals the local ground truth byte-for-byte** — a value the model provably cannot fabricate, so this is the **first main-flow proof that the sandbox actually executed a bundled script** (vs the model reciting a value). `default_sandbox()` = **DockerSandbox** → it ran in a REAL hardened Docker container (`--cap-drop=ALL` / `read_only` / `network=none` / non-root), not the Subprocess fallback. No AP-4 Potemkin: the tool is wired (registered + executed), the label is real (`run_skill_script` shows the true skill_name input + the real JSON output), and the result genuinely renders in both the turn block and the Loop visualizer.

**Evidence**: `artifacts/sprint-57-118-drivethrough-digest.png` (chat-v2 turn blocks: read_skill → run_skill_script JSON → final digest + Verification 0.99; right Inspector Turn tab; Loop visualizer 3 turns).

**Verdict**: ✅ **PASS** — Drive-Through Acceptance satisfied (real UI + real backend + real LLM + real Docker sandbox); user-facing path is genuinely usable, not gate-only.

## Day 4 — (pending: design note 34 + CHANGE-085 + retrospective + navigators + PR)
