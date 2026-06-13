# Sprint 57.113 — Checklist (Skills System, thin vertical / model-invoked lazy-load: a system-global `SkillRegistry` loads bundled `SKILL.md` files, a cheap "## Available Skills" block rides the `system_prompt` persona seam, and a `read_skill` tool lazy-loads a skill's full instructions on-demand — the first spike of the Skills System epic, cc-parity row 9; per-tenant catalogs / slash command / wire event deferred)

[Plan](./sprint-57-113-plan.md)

---

## Day 0 — Plan-vs-Repo Verify + Branch ✅

### 0.1 Three-prong Day-0 verify (against `main` HEAD `e133d92f`) — DONE, catalogued in progress.md D1-D7
- [x] **Prong 1 — path verify**: NEW absent (Glob-0) — `agent_harness/skills/` · `backend/config/skills/` · `31-skills-system-spike.md` · CHANGE-080 · test files; EDIT present (Glob-1) — all 7 targets; design note 31 + CHANGE 080 free
- [x] **Prong 2 — content verify** (drift findings in progress.md):
  - [x] **D1 D-system-prompt-seam (CRITICAL) = 🟢 GREEN**: `loop.py:1899-1901` prepends `system_prompt` → `_run_turns` → `state.transient.messages` → builder `_extract_conversation` (`builder.py:529-536`) → `artifact.messages` → chat call (`loop.py:2293/2374`). Persona rides this path (proven by 57.106) → **append-to-`system_prompt` reaches the LLM; NO PromptBuilder rewire**
  - [x] **D2 D-capability-gate = 🟢 GREEN + DRIFT**: chat path builds the matrix from the LIVE registry (`handler.py:555-563` `tool_rules = {spec.name: PermissionRule(...) for spec in registry.list()}`) — NOT from `capability_matrix.yaml` → `read_skill` auto-gets a PASS rule once registered → **DROP the yaml edit (FCL #9)**
  - [x] **D3 D-tool-handler-convention = 🟢 GREEN**: `ToolHandler = Callable[[ToolCall], Awaitable[str|dict]]` async (`executor.py:101-104`); echo `async def echo_handler(call: ToolCall) -> str: return str(call.arguments.get("text",""))` (`echo_tool.py:55-57`); invoked `executor.py:225-228`
  - [x] **D4 D-register-echo-block = 🟢 GREEN**: echo `_register_all.py:256-258`; opt-in precedent (handoff) `:281-284` → mirror `if skill_registry is not None:`
  - [x] **D5 D-config-path = 🟡 DRIFT**: no `core/config` field resolves `backend/config/` → **co-locate bundled skills in `agent_harness/skills/bundled/*.md`** (resolve via `Path(__file__).parent/"bundled"`; robust, packaged-with-code, matches CC `skills/bundled/`)
  - [x] **D6 D-yaml = 🟡 DRIFT**: PyYAML used (`capability_matrix.py:57`) but NOT in `requirements.txt` → **ADD `PyYAML`** (the loader needs `yaml.safe_load`; 57.112 pyotp precedent)
  - [x] **D7 D-import-cycle = 🟢 GREEN**: `skills/` → `_contracts/tools.py` is a clean Cat 5 → contracts import; `from __future__ import annotations`
- [x] **Prong 3 — schema verify**: N/A (NO DB / NO migration this spike) — noted in progress.md
- [x] **Catalog drift** findings in progress.md Day 0 (D1-D7 + implications)
- [x] **Go/no-go**: 🟢 GO — D1 confirms the append works (no pivot); 3 adjustments net-neutral-or-simpler (DROP yaml edit / ADD PyYAML / repoint bundled dir); < 20% shift

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-113-skills-system-spike` (from `main` `e133d92f`)

---

## Day 1 — Backend: SkillRegistry + loader + bundled skills (US-1) ✅

### 1.1 Skill model + SkillRegistry + from_dir loader
- [x] **`requirements.txt`** (D6): added `PyYAML>=6.0,<7.0`; smoke-tested (`yaml 6.0.3` already installed transitively)
- [x] **`agent_harness/skills/registry.py`** (NEW): `Skill` frozen dataclass; `SkillRegistry` (`register` dup→ValueError + `get` + `list`); `from_dir(path)` — sorted `*.md`, `_parse_frontmatter` split `---` maxsplit=2 + `yaml.safe_load`, require name+description+body, **skips malformed with a logged warning (never raises)**; `get_default_skill_registry()` singleton (lazy `from_dir(Path(__file__).parent/"bundled")` per D5); `render_catalog_block` (empty → `""`); file header + WHY
- [x] **`agent_harness/skills/__init__.py`** (NEW): re-exports `Skill`/`SkillRegistry`/`get_default_skill_registry`/`render_catalog_block`/`READ_SKILL_TOOL_SPEC`/`make_read_skill_handler`
  - DoD: ✅ mypy `src` 0 (3 files); black/isort/flake8 0

### 1.2 Bundled skills (REAL, not stubs — AP-4) — co-located `agent_harness/skills/bundled/` (D5)
- [x] **`agent_harness/skills/bundled/code-review.md`** (NEW): frontmatter + body — Summary + Risks table (`| Severity | Issue | Location |`, security>correctness>perf) + Suggested fixes; "no praise/filler"
- [x] **`agent_harness/skills/bundled/summarize.md`** (NEW): frontmatter + body — Decisions / Action Items (owner — task) / Open Questions
  - DoD: ✅ both load via `get_default_skill_registry()` (names `code-review`+`summarize`, non-empty instructions; test_bundled_skills_load asserts len(instructions)>50)

### 1.3 Unit tests (US-1)
- [x] **`tests/unit/agent_harness/skills/test_registry.py`** (NEW, ×10): valid parse · malformed/frontmatter-less skipped (not crash) · missing-dir → empty · dup → ValueError · get hit/miss · `list` deterministic (sorted glob) · 2 bundled load · `render_catalog_block([])` → "" · catalog lists names+descriptions+read_skill instruction · singleton identity stable
  - DoD: ✅ **10 passed**; mypy `src` 0; black/isort/flake8 0

---

## Day 2 — Backend: read_skill tool + main-flow wiring (US-2) ✅

### 2.1 read_skill tool
- [x] **`agent_harness/skills/tool.py`** (NEW — written Day 1): `READ_SKILL_TOOL_SPEC` (read-only, `additionalProperties:false`, `risk_level=LOW`, `tags=("skills",)`); `make_read_skill_handler(registry)` — `async def(call: ToolCall) -> str` per D3; known → framed `# Skill:` + instructions + "Follow these instructions…"; unknown/missing-arg → recoverable "Unknown skill … Available: …" (no raise); read-only, no DB
- [x] **Unit tests ADD** `tests/unit/agent_harness/skills/test_skills_tool.py` (NEW, ×4): framed for known · unknown → recoverable (no raise) · missing-arg → recoverable · spec survives `ToolRegistryImpl.register` (valid Draft-2012)
  - DoD: ✅ 4 pass; mypy 0; flake8 0 (renamed `test_tool.py`→`test_skills_tool.py` for unique basename — pytest rootdir collision vs `verification/test_registry.py`, the 57.109 D-DAY1-2 lesson)

### 2.2 make_default_executor opt-in + build_handler + router wiring
- [x] **`business_domain/_register_all.py`**: `make_default_executor(..., skill_registry=None)` — `if skill_registry is not None: registry.register(READ_SKILL_TOOL_SPEC); handlers["read_skill"] = make_read_skill_handler(skill_registry)` (mirror echo + handoff opt-in); import + TYPE_CHECKING `SkillRegistry`; MHist 1-line
- [x] **`api/v1/chat/handler.py`**: threaded `skill_registry` through BOTH `build_handler` (dispatcher) AND `build_real_llm_handler` (wiring); `build_real_llm_handler` appends `render_catalog_block` to `system_prompt` (rides the persona seam, D1) + passes `skill_registry` to `make_default_executor`; import + TYPE_CHECKING; comments
- [x] **`api/v1/chat/router.py`**: pass `skill_registry=get_default_skill_registry()` to `build_handler(...)`; import; comment
- [x] ~~`capability_matrix.yaml` allowlist~~ — DROPPED (D2: chat path derives the matrix from the live registry → `read_skill` auto-PASSes once registered)
- [x] **Integration tests ADD** `tests/integration/api/test_skills_wiring.py` (NEW, ×6): executor opt-in registers read_skill (+ negative guard) · read_skill executes through `executor.execute` → framed · `build_handler(skill_registry=reg)` → `loop._system_prompt` has "## Available Skills" + code-review + summarize + read_skill(name) · `build_handler` no-registry → `== DEMO_SYSTEM_PROMPT` (regression) · scripted MockChatClient read_skill call → ToolCallExecuted result carries framed instructions (lazy-load on the SSE flow). Azure-call-free (57.64 keystone fake-env pattern)
  - DoD: ✅ 6 pass; mypy `src` **0/366** (+3 skills); run_all **10/10** (count 24); full pytest **2566+5skip** (+20, 0 del); `loop.py`/wire/codegen/migrations UNTOUCHED

---

## Day 3 — Full gates + drive-through (US-3) + CHANGE-080

### 3.1 Full gate sweep ✅
- [x] mypy `src` **0/366** (+3) · black/isort/flake8 0 (changed files, CI-identical) · run_all **10/10** (count 24 — no codegen diff; `check_event_schema_sync`+`check_llm_sdk_leak`+`check_cross_category_import` green) · full pytest **2566+5skip** (+20, 0 del) · Vitest 840 + mockup-fidelity 51 UNCHANGED (zero FE touched) · `loop.py`/wire diff empty

### 3.2 Drive-through (US-3 — real chat-v2 :3007 + fresh single-process backend + real Azure LLM; Risk Class E clean restart) ✅
- [x] **Clean restart + probe**: no orphan workers; fresh no-reload backend pid 38620 sole owner of :8000 (startup clean); runtime probe `get_default_skill_registry()` → `['code-review','summarize']` (CR 1179 / SUM 740 chars)
- [x] **Leg A (discover+load+follow) PASS**: `Review this Python function: …SQL string-concat…` → `read_skill("code-review")` (Trace `agent_loop.tool.read_skill` span; `mentionsReadSkill: true`) → output `## Summary` + `## Risks` table (High SQL injection / Med type / Med None) + `## Suggested fixes` (parameterized). `dt57113-A-code-review.png`
- [x] **Leg B (2nd skill) PASS**: `Summarize this thread: …Postgres/Friday/MySQL/benchmark…` → `read_skill("summarize")` → `## Decisions` + `## Action Items` (`Bob — …` / `Dave — …` owner—task) + `## Open Questions`. `dt57113-B-summarize.png`
- [x] **Leg C (no false trigger) PASS**: `What is 2 + 2, and why?` → `mentionsReadSkill: false`, direct answer, NO read_skill. `dt57113-C-no-trigger.png`
- [x] Screenshots in `artifacts/` + observed-vs-intended in progress.md; no dead control / no fixture / no mislabeled output; teardown stopped pid 38620 + removed temp log
  - DoD: ✅ discover→load→follow drivable e2e on real UI+backend+LLM; output shape DISTINCTLY follows the skill (load+follow proven, AP-4 guard); negative leg proves no false-positive

### 3.3 CHANGE-080 ✅
- [x] `claudedocs/4-changes/feature-changes/CHANGE-080-skills-system-spike.md` (1-page, incl. the 3-leg drive-through)

---

## Day 4 — Closeout ✅

### 4.1 Closeout
- [x] retrospective.md Q1-Q7 + calibration (NEW `skills-system-spike` 0.60 1st data point ratio ~0.94 IN band KEEP; agent-delegated: no) + progress.md final
- [x] **Spike design note `31-skills-system-spike.md`** (§5.5) — 8-point quality gate all ✓, ~95% verified ratio (retro Q6)
- [x] Navigators: CLAUDE.md Current-Sprint row + Last-Updated (minimal touch); MEMORY.md quality pointer + memory subfile `project_phase57_113_skills_system_spike.md`; next-phase-candidates — Skills System epic OPENED + 6 deferred items; sprint-workflow matrix NEW `skills-system-spike` 0.60 1st data point; 17.md — N/A (no new contract — identity/MFA precedent; noted in design note §4)
- [x] **Anti-pattern self-check** (retro Q5/Q7): AP-4 ✅ real drivable skills (dt output shape proves followed, not stub; negative-guard tests); AP-2 ✅ reachable from main flow (router→build_handler→executor + block→system_prompt); AP-8 ✅ rides the proven system_prompt seam (no second prompt-assembly path); AP-3 ✅ skills in `agent_harness/skills/` + tool reg in the established `_register_all.py`
- [ ] PR (push + open on user authorization)
