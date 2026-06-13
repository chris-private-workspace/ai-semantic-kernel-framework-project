# Sprint 57.113 Progress — Skills System (thin vertical, model-invoked lazy-load)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-113-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-113-checklist.md)

---

## Day 0 — 2026-06-13 — Plan-vs-Repo Verify + Branch

Branch `feature/sprint-57-113-skills-system-spike` from `main` `e133d92f` (post-#287).

### Prong 1 — path verify (all GREEN)

NEW absent (Glob-0): `agent_harness/skills/` (whole dir) · `backend/config/skills/` · `31-skills-system-spike.md` · `CHANGE-080-*.md` · `tests/unit/agent_harness/skills/`. EDIT present (Glob-1): `_register_all.py` · `handler.py` · `router.py` · `prompt_builder/builder.py` · `_contracts/tools.py` · `tools/registry.py` · `capability_matrix.py`. Design note 31 free; CHANGE 080 free.

### Prong 2 — content verify (drift findings)

- **D1 — D-system-prompt-seam = 🟢 GREEN (CRITICAL, no pivot)**: traced `system_prompt` → the LLM. `loop.py:1899-1901` prepends `Message(role="system", content=self._system_prompt)` to the local `messages`, passed to `_run_turns(messages=…)` → into `state.transient.messages`. The per-turn LLM call uses `artifact.messages` (`loop.py:2293` `chat_messages = list(artifact.messages)` → `:2374 ChatRequest(messages=chat_messages)`), and the builder's `_extract_conversation(state, user_msg)` (`builder.py:529-536`) returns `state.transient.messages` minus the current user msg — so the persona system message rides into the conversation section of `artifact.messages`. The builder's own `_build_system_section` uses `SYSTEM_ROLE_TEMPLATE` (`builder.py:421-437`, `make_chat_prompt_builder` passes no `system_role_text`), but the **persona reaches the LLM via the `system_prompt` → conversation path** (proven transitively: personas + harness-policy visibly change behavior, 57.106). → **Appending the "## Available Skills" block to `system_prompt` at `build_handler` reaches the LLM.** No PromptBuilder rewire (plan §8-risk-1 fallback NOT triggered).
- **D2 — D-capability-gate = 🟢 GREEN, but DRIFT (drop a planned edit)**: `tool_guardrail.py:97-103` is default-DENY (an unknown tool → `BLOCK` HIGH). BUT the chat path does NOT use `capability_matrix.yaml` — `handler.py:555-563` builds the matrix from the LIVE registry: `tool_rules = {spec.name: PermissionRule(requires_approval=spec.name in escalate_tools) for spec in registry.list()}`. Every registered tool gets a PASS rule (approval only for `CHAT_HITL_ESCALATE_TOOLS = {"echo_tool"}`). The registry is built at `make_default_executor` (`handler.py:470`) BEFORE `:555` iterates it → once `read_skill` is registered in the registry, it AUTO-gets a PASS rule. **→ NO `capability_matrix.yaml` edit needed** (plan File Change List #9 DROPPED). Implication: simpler scope.
- **D3 — D-tool-handler-convention = 🟢 GREEN**: `ToolHandler = Callable[[ToolCall], Awaitable[str | dict]]` (or dual-arity with `ExecutionContext`) — `executor.py:101-104`; ASYNC; reads args via `call.arguments.get(...)`; returns `str | dict`. `echo_handler` (`echo_tool.py:55-57`): `async def echo_handler(call: ToolCall) -> str: return str(call.arguments.get("text", ""))`. Invoked at `executor.py:225-228` (`await handler(call)` or `await handler(call, ctx)`). → `make_read_skill_handler` returns `async def handler(call: ToolCall) -> str` reading `call.arguments.get("name")`.
- **D4 — D-register-echo-block = 🟢 GREEN**: echo registers at `_register_all.py:256-258` (`registry.register(ECHO_TOOL_SPEC); handlers["echo_tool"] = echo_handler`); `ECHO_TOOL_SPEC` in `echo_tool.py:29-52`. Opt-in precedent (`handoff_targets`) `_register_all.py:281-284`: `if handoff_targets is not None: … registry.register(spec); handlers[spec.name] = _adapt_subagent_handler(handler)`. → mirror for `if skill_registry is not None: registry.register(READ_SKILL_TOOL_SPEC); handlers["read_skill"] = make_read_skill_handler(skill_registry)`.
- **D5 — D-config-path = 🟡 DRIFT (repoint bundled dir)**: `CapabilityMatrix.from_yaml` takes an EXPLICIT path from callers (`capability_matrix.py:135`); the chat path never loads the yaml (D2). No `core/config` field / env var resolves `backend/config/`. Rather than introduce a fragile `parents[N]` walk to `backend/config/skills/`, **co-locate the bundled skills INSIDE the package**: `agent_harness/skills/bundled/{code-review,summarize}.md`, resolved via `Path(__file__).parent / "bundled"` — robust (no CWD/layout dependence), packaged with the code, and matches CC's `skills/bundled/` naming. **→ plan File Change List #4/#5 repoint from `backend/config/skills/` to `agent_harness/skills/bundled/`.**
- **D6 — D-yaml = 🟡 DRIFT (add a dep)**: `import yaml  # type: ignore[import-untyped, unused-ignore]` is used (`capability_matrix.py:57`) and works at runtime, but **PyYAML is NOT declared in `requirements.txt`** (transitive only). The `from_dir` frontmatter loader uses `yaml.safe_load` (matches the capability-matrix convention; robust for description strings with colons) → **ADD `PyYAML` to `requirements.txt`** (hygiene + the loader needs it; the 57.112 `pyotp` precedent). Mirror the cross-platform `# type: ignore[import-untyped, unused-ignore]`.
- **D7 — D-import-cycle = 🟢 GREEN**: `agent_harness/skills/` importing `ToolSpec`/`RiskLevel`/`ToolHITLPolicy` from `_contracts/tools.py` is a Cat 5 → contracts import (contracts are the shared bottom layer; no reverse import). Use `from __future__ import annotations` for forward refs.

### Prong 3 — schema verify

N/A this spike — NO DB / NO migration / NO new table / NO ORM change.

### Existing-test scan (convert-not-delete)

No assertion on the exact built-in tool COUNT or on `DEMO_SYSTEM_PROMPT` content found (the one `len(registry) == 1` in `test_chat_category_activation_wiring.py` is the verifier_registry, not the tool registry — unaffected). `read_skill` + the catalog block only appear when `skill_registry` is passed → non-skills tests are unaffected by default.

### Go/no-go: 🟢 GO

3 scope adjustments, all net-neutral-or-simpler (< 20% shift): DROP capability_matrix.yaml edit (D2), ADD requirements.txt PyYAML (D6), repoint bundled dir to `agent_harness/skills/bundled/` (D5). The critical D1 confirms the append-to-`system_prompt` injection works → no PromptBuilder rewire. Proceeding to Day 1.

---

## Day 1 — 2026-06-13 — SkillRegistry + loader + bundled skills (US-1) ✅

**Shipped**: `agent_harness/skills/registry.py` (`Skill` frozen dataclass + `SkillRegistry` register/get/list + `from_dir` frontmatter loader + `get_default_skill_registry` singleton + `render_catalog_block`) · `tool.py` (`READ_SKILL_TOOL_SPEC` + `make_read_skill_handler` — written Day 1 so `__init__` re-exports cleanly) · `__init__.py` re-exports · 2 REAL bundled skills `skills/bundled/{code-review,summarize}.md` · `requirements.txt` += `PyYAML>=6.0,<7.0` (D6) · `tests/unit/agent_harness/skills/test_registry.py` ×10.

**Loader design**: `_parse_frontmatter` splits `---` with `maxsplit=2` (keeps `---` inside the body — markdown rules / table separators — intact) + `yaml.safe_load` for the name/description (robust for descriptions with `:`). A malformed / frontmatter-less / missing-field file is SKIPPED with a logged warning (never raises) so a bad bundled file can't crash chat startup. Bundled dir resolved via `Path(__file__).parent / "bundled"` (D5 — co-located, no CWD dependence).

**Gate**: ✅ 10/10 unit pass (0.13s) · mypy `src` 0 (3 files) · black/isort/flake8 0 · PyYAML 6.0.3 (already installed transitively). No DB / no wire / no FE touched.

**Est vs actual**: registry+loader+tool+bundled+tests ~3 hr est → actual ~2.5 hr (the from_dir loader + 2 real skill bodies were the bulk; the tool.py spec mirrored echo_tool.py directly).

---

## Day 2 — 2026-06-13 — read_skill tool + main-flow wiring (US-2) ✅

**Shipped**: `make_default_executor(skill_registry=None)` opt-in (registers `read_skill` mirroring the echo + handoff opt-in) · `build_handler` + `build_real_llm_handler` threaded `skill_registry` (the dispatcher forwards; the real builder appends `render_catalog_block` to `system_prompt` + passes the registry to the executor) · `router.py` passes `get_default_skill_registry()` · `test_skills_tool.py` ×4 + `test_skills_wiring.py` ×6.

**Seam confirmed at runtime (D1 GREEN proof)**: the integration test `test_build_handler_appends_skills_block_to_system_prompt` asserts the constructed `loop._system_prompt` contains "## Available Skills" + both bundled skill names + the `read_skill(name)` instruction — and the no-registry test asserts it stays `== DEMO_SYSTEM_PROMPT`. The scripted-LLM test (`test_chat_path_read_skill_executes`) drives a `read_skill("code-review")` tool call through the real `AgentLoopImpl` SSE flow (MockChatClient, Azure-call-free) → `ToolCallExecuted.result_content` carries the framed instructions. This is CI-safe proof of the full discover→advertise→load chain (約束 2); the drive-through adds the real-LLM self-selection confirmation.

**Pytest basename collision (fixed)**: `skills/test_registry.py` collided with `verification/test_registry.py` (test dirs have no `__init__.py` → pytest rootdir import uses the bare module name). Renamed both skills unit tests to unique basenames `test_skills_{registry,tool}.py` (the 57.109 D-DAY1-2 lesson + Risk Class catalog).

**Gate (full sweep, Day 3.1 done early)**: ✅ mypy `src` **0/366** (+3 vs 363) · black/isort/flake8 0 (changed files, CI-identical) · run_all **10/10** (count 24 — no codegen/wire diff; `check_cross_category_import` green = Cat 5 `skills/` → `_contracts` ToolSpec import clean; `check_llm_sdk_leak` green; `check_event_schema_sync` green) · full pytest **2566 passed + 5 skipped** (+20 vs 2546, 0 del) · Vitest/mockup-fidelity UNCHANGED (zero FE touched) · `loop.py`/wire/codegen/migrations UNTOUCHED.

**Est vs actual**: tool + executor opt-in + handler/router wiring + 10 tests ~5 hr est → actual ~4 hr (the keystone fake-Azure test pattern was directly reusable; the basename rename was the only surprise).

---

## Day 3 — 2026-06-13 — Drive-through (US-3) + CHANGE-080 ✅

**Setup (Risk Class E clean start)**: no orphan uvicorn/spawn python workers (Win32_Process sweep); :8000 free → started a fresh no-reload single-process backend (`python -m uvicorn api.main:app --app-dir src`, NO `--reload`, pid 38620) — startup log clean ("startup complete", pricing/billing wired, root `.env` autoloaded via `load_dotenv()` walking up from backend). Runtime skill-load probe: `get_default_skill_registry()` → `['code-review', 'summarize']` (CR 1179 / SUM 740 chars) confirming `Path(__file__).parent/"bundled"` resolves in the server runtime. Frontend :3007 (Vite, node) already up. Real Azure (real_llm mode, non-echo).

**Drive-through (real chat-v2 UI :3007 + real backend + real Azure gpt, dev-login jamie@acme.com · acme-prod · operator; Playwright):**

- **Leg A (code-review — discover→load→follow) PASS**: typed `Review this Python function: def get_user(uid): return db.execute("SELECT * FROM users WHERE id = " + uid).fetchone()`. The model (seeing "## Available Skills") emitted a `read_skill("code-review")` tool call (the Inspector Trace shows `agent_loop.tool.read_skill` TOOL_EXEC span; page DOM `mentionsReadSkill: true`) → the tool result returned the full instructions → the assistant produced output in the EXACT skill shape: `## Summary` ("SQL injection vulnerability … not safe to merge as-is") + a `## Risks` markdown table (`| Severity | Issue | Location |` — High SQL injection / Medium type-quoting / Medium None-handling, security ranked first) + `## Suggested fixes` (parameterized query, `int(uid)` validation). Screenshot `artifacts/dt57113-A-code-review.png`.
- **Leg B (summarize — a different skill) PASS**: new session → `Summarize this thread: Alice proposed moving to Postgres. Bob … migration plan by Friday. Carol … MySQL for analytics, still undecided. Dave will benchmark …`. `read_skill("summarize")` fired (`mentionsReadSkill: true`) → output in the skill shape: `## Decisions` (Move to Postgres) + `## Action Items` (**`Bob — produce a migration plan by Friday`** / **`Dave — benchmark Postgres vs MySQL next week`** — the skill's exact `owner — task` format) + `## Open Questions` (keep MySQL for analytics — undecided). Proves the model self-selected the CORRECT (different) skill. Screenshot `artifacts/dt57113-B-summarize.png`.
- **Leg C (no false trigger) PASS**: new session → `What is 2 + 2, and why?` → `mentionsReadSkill: false`; the assistant answered directly ("2 + 2 = 4, because addition combines quantities…") with NO read_skill call. The model does not force a skill where none fits. Screenshot `artifacts/dt57113-C-no-trigger.png`.

**Observed vs intended**: matches exactly — the cheap "## Available Skills" block reached the system prompt (the model knew the two skills existed), the model self-selected + lazy-loaded the right one via `read_skill`, and the output shape DISTINCTLY followed the loaded skill (not a generic answer) — the AP-4 guard the drive-through exists to confirm. The negative leg proves no false-positive coupling. No dead control, no fixture, no mislabeled output.

**Teardown (Risk Class E)**: stopped the dt backend (pid 38620 → :8000 free); removed the temp `dt_backend.log`; the Vite node :3007 left running (not ours to stop). Screenshots moved to `artifacts/` (never-commit, local evidence).

**CHANGE-080** written (`claudedocs/4-changes/feature-changes/CHANGE-080-skills-system-spike.md`).

**Est vs actual**: drive-through ~1 hr est → actual ~1 hr (3 legs + screenshots; the dev-login → chat-v2 path was straightforward).

---
