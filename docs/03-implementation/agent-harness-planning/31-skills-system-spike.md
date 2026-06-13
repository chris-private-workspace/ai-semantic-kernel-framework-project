# 31 — Skills System Spike (model-invoked lazy-load)

**Purpose**: Extract the verified design of the Skills System first vertical (Sprint 57.113) — a Claude-Code-style model-invoked lazy-load skills capability.
**Category / Scope**: 範疇 5 (Prompt Construction) + 範疇 2 (Tool Layer) · Phase 57 · Sprint 57.113
**Created**: 2026-06-13
**Last Modified**: 2026-06-13
**Status**: Active (spike-extracted from shipped code)

> **Modification History**
> - 2026-06-13: Initial extract from Sprint 57.113 (Skills System epic — first thin vertical)

---

## 1. Spike Summary

**US-1 (the discovery substrate) + US-2 (discover→load→follow wired into the chat main flow), as shipped in Sprint 57.113.**

A skill is a markdown file with YAML frontmatter (`name`, `description`) + a full-instruction body. A system-global `SkillRegistry` loads the bundled skills once; the cheap name+description list is injected into the system prompt (so the model knows what skills exist without paying for their bodies), and the FULL instructions are lazy-loaded on demand via a model-invoked `read_skill` tool. This is the CC lazy-load loop: **advertise cheap → model self-selects → `read_skill(name)` → follow the loaded instructions.**

Verified end-to-end through chat-v2 with a real Azure LLM (§3 + §drive-through). System-bundled only (no per-tenant catalogs); two real skills ship (`code-review`, `summarize`).

## 2. Decision Matrix

**The invocation model** (user scope decision 2026-06-13, AskUserQuestion):

| Option | Mechanism | CC-faithful? | Agentic? | FE work | Verdict |
|--------|-----------|--------------|----------|---------|---------|
| **A — Model-invoked lazy-load** ✅ | cheap name+desc list in system prompt + a `read_skill` tool the model calls on-demand | **Yes** (cc-parity row 9 "lazy load") | **Yes** (model self-selects) | none (chat-v2 renders tool calls) | **CHOSEN** — the CC-faithful core + thinnest agentic vertical |
| B — System auto-match injection | a pre-loop matcher injects the best skill's full instructions | No (model doesn't self-select) | No | none | Rejected — less agentic, less faithful |
| C — User `/skill` slash command | UI `/skill-name` loads the skill | partial (`commands/skills/`) | No (human-triggered) | FE slash plumbing | Deferred — a later epic slice; the model-invoked core ships first |

**Sub-decisions**:

| Decision | Choice | Rationale (file:line) |
|----------|--------|-----------------------|
| Where the catalog block is injected | Append to the resolved `system_prompt` at `build_real_llm_handler` (rides the persona seam) | The loop prepends `system_prompt` as the system message (`loop.py:1899-1900`); persona provably reaches the LLM via this seam, so the block does too. Avoids rewiring the PromptBuilder internals. |
| How `read_skill` is permitted by Cat 9 | Nothing — auto-PASS | The chat path derives the tool-permission matrix from the live registry (`handler.py:555-563` `tool_rules = {spec.name: PermissionRule(...) for spec in registry.list()}`), so a registered tool auto-gets a PASS rule. No `capability_matrix.yaml` edit. |
| Frontmatter parsing | `yaml.safe_load` on the `---`-delimited block (`maxsplit=2`) | Matches the `capability_matrix.from_yaml` convention (`capability_matrix.py:135`); robust for descriptions containing `:`. No new dep beyond declaring the transitive `PyYAML`. |
| Bundled dir location | `agent_harness/skills/bundled/` (co-located) | `Path(__file__).parent/"bundled"` (`registry.py`) — no CWD/layout dependence, packaged with the code, matches CC's `skills/bundled/`. |
| New SSE wire event? | No | `read_skill` streams via the existing Cat 2 tool rendering; wire count stays 24, zero codegen. |

## 3. Verified Invariants (file:line + how verified)

1. **A skill loads from frontmatter+body** — `SkillRegistry.from_dir` (`backend/src/agent_harness/skills/registry.py`) parses `---\n<yaml>\n---\n<body>` → `Skill(name, description, instructions)`. Verified: `tests/unit/agent_harness/skills/test_skills_registry.py::test_from_dir_parses_valid_skill`.
2. **A malformed bundled file is skipped, not fatal** — `from_dir` logs a warning + continues (no raise). Verified: `test_from_dir_skips_malformed_without_crashing`.
3. **The two bundled skills load in the server runtime** — `get_default_skill_registry()` → `['code-review','summarize']`. Verified: `test_bundled_skills_load` + runtime probe (progress.md Day 3 — CR 1179 / SUM 740 chars; confirms `Path(__file__).parent/"bundled"` resolves under uvicorn).
4. **The cheap discovery block renders** — `render_catalog_block(skills)` → "## Available Skills" + the `read_skill(name)` instruction + `- name: description` lines; `""` when empty. Verified: `test_render_catalog_block_*`.
5. **`read_skill` returns the framed full instructions** — `make_read_skill_handler` (`tool.py`) → `# Skill: {name}\n\n{instructions}\n\nFollow these instructions…`; unknown name → recoverable message (no raise). Verified: `tests/unit/agent_harness/skills/test_skills_tool.py`.
6. **The opt-in registers `read_skill` into the live tool registry** — `make_default_executor(skill_registry=reg)` (`backend/src/business_domain/_register_all.py`) registers `READ_SKILL_TOOL_SPEC` + the handler; absent without a registry. Verified: `tests/integration/api/test_skills_wiring.py::test_make_default_executor_registers_read_skill_when_given` (+ negative guard).
7. **The catalog block reaches the loop's system prompt** — `build_handler(skill_registry=reg)` → `loop._system_prompt` contains "## Available Skills" + both skill names; `build_handler` with no registry → `loop._system_prompt == DEMO_SYSTEM_PROMPT` (regression-safe). Verified: `test_build_handler_appends_skills_block_to_system_prompt` + `test_build_handler_no_block_without_registry`.
8. **`read_skill` executes on the live chat SSE flow** — a scripted `read_skill` tool call → `ToolCallExecuted.result_content` carries the framed instructions. Verified: `test_chat_path_read_skill_executes` (MockChatClient, Azure-call-free).

**Verification commands**:
```
cd backend
python -m pytest tests/unit/agent_harness/skills tests/integration/api/test_skills_wiring.py -q   # 20 tests
mypy src   # 0/366
python ../scripts/lint/run_all.py   # 10/10 (count 24)
```

**Real-LLM drive-through** (Sprint 57.113 Day 3 — real chat-v2 :3007 + real Azure, dev-login jamie@acme.com): Leg A `read_skill("code-review")` → Summary/Risks-table/Fixes; Leg B `read_skill("summarize")` → Decisions/Action Items(owner—task)/Open Questions; Leg C "2+2" → no read_skill. Screenshots `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-113/artifacts/dt57113-{A,B,C}-*.png`. The output shapes distinctly followed the loaded skills (load+follow proven, not generic).

## 4. Cross-Category Contracts

No NEW cross-category contract (17.md unchanged). `read_skill` is an ordinary Cat 2 `ToolSpec` (`_contracts/tools.py` ToolSpec — registered like any built-in via `make_default_executor`); the catalog block is plain text appended to the Cat 1 loop's `system_prompt` param (`loop.py` `AgentLoopImpl(system_prompt=)`). The Cat 5 `agent_harness/skills/` module imports only `_contracts` (the shared bottom layer) — `check_cross_category_import` green. Per the identity/MFA precedent (Sprint 57.105/112), a feature wired through existing contracts adds no 17.md entry.

## 5. Open Invariants (NOT verified this spike — deferred)

- **Per-tenant / DB-backed custom skill catalogs** (`AD-Skills-Per-Tenant-Catalog`) — the registry is system-bundled (no tenant_id, no DB). A per-tenant overlay would resolve like `resolve_session_persona` and merge tenant skills over the bundled set.
- **A `/skill` slash command** (`AD-Skills-Slash-Command`) — Option C; needs FE slash plumbing + a force-load path.
- **A dedicated SSE wire event + Inspector "skill loaded" affordance** (`AD-Skills-Inspector-Affordance`) — currently the `read_skill` call rides the generic tool stream.
- **Skill versioning / hot-reload / authoring UI** (`AD-Skills-Authoring-UI`) — the registry loads once at first access; no reload.
- **Bundled executable scripts/resources inside a skill** (`AD-Skills-Bundled-Scripts`) — CC skills can bundle tools; this spike is instructions-only.
- **Skill-aware prompt caching boundary** — the block is appended to the (cache-stable) persona prefix; a dedicated cache breakpoint for the skills block was not measured.

## 6. Rollback

Fully reversible, low blast radius (no DB / no migration / no wire / no FE):
- Revert the 3 wiring edits (`_register_all.py` opt-in, `handler.py` param+append, `router.py` arg) → `read_skill` is never registered + no block is appended → the chat path is byte-identical to pre-57.113 (the no-registry regression test pins this).
- Delete `agent_harness/skills/` + its tests + `requirements.txt` PyYAML line.
- Estimated effort: < 1 hr. No data migration. The `skill_registry` params default to `None`, so any caller not passing a registry is unaffected.

## 7. References

- `claudedocs/5-status/agent-harness-cc-parity-20260607.md` row 9 — the cc-parity gap (source).
- `01-eleven-categories-spec.md` §範疇5 (Prompt Construction) + §範疇2 (Tool Layer).
- `backend/src/agent_harness/skills/{registry,tool}.py` + `bundled/{code-review,summarize}.md` — the shipped module.
- `backend/src/api/v1/chat/handler.py` (`build_real_llm_handler` append + `build_handler` thread) + `router.py` (registry pass) + `business_domain/_register_all.py` (`make_default_executor` opt-in) — the wiring.
- `claudedocs/4-changes/feature-changes/CHANGE-080-skills-system-spike.md` — the change record.
- Sprint 57.113 plan / checklist / progress / retrospective.
