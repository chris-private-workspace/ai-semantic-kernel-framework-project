# CHANGE-080: Skills System (thin vertical, model-invoked lazy-load)

**Date**: 2026-06-13
**Sprint**: 57.113
**Scope**: 範疇 5 (Prompt Construction) + 範疇 2 (Tool Layer — `read_skill`); cross-cutting into the chat main flow (api/v1/chat)

## Problem

The cc-parity analysis (`claudedocs/5-status/agent-harness-cc-parity-20260607.md` row 9) flagged "Skills System (lazy load)" as the last systematic Claude-Code-parity gap: CC ships a `skills/bundled/` capability where each skill is a markdown instruction file whose name+description is always visible cheaply and whose full instructions load on demand, letting the agent self-select a relevant skill. This platform had ZERO skills code (the cc-parity "有痕跡" was disproven at Day-0 — only an unrelated `capability_matrix` existed).

## Root Cause

New domain — no prior implementation. Per the rolling-planning discipline, opened the epic with a thin vertical spike (not a batch of planning docs).

## Solution

**Model-invoked lazy-load** (user scope decision — Option A): the CC-faithful core.

- **`agent_harness/skills/`** (NEW, Cat 5): `Skill` frozen dataclass + `SkillRegistry` (register/get/list + `from_dir` markdown/frontmatter loader using `yaml.safe_load`, skips malformed files without crashing) + `get_default_skill_registry()` module singleton (loads `agent_harness/skills/bundled/` via `Path(__file__).parent/"bundled"`) + `render_catalog_block()` (the cheap "## Available Skills" name+description block; `""` when empty). Two REAL bundled skills: `code-review.md` (Summary / Risks table w/ severity / Fixes) + `summarize.md` (Decisions / Action Items / Open Questions).
- **`agent_harness/skills/tool.py`** (NEW, Cat 2): `READ_SKILL_TOOL_SPEC` (read-only) + `make_read_skill_handler(registry)` — returns the named skill's full instructions framed as a directive (unknown name → recoverable message, not an exception).
- **Wiring**: `make_default_executor(skill_registry=None)` opt-in registers `read_skill` (mirrors the echo + handoff opt-in); `build_real_llm_handler` appends `render_catalog_block` to the resolved `system_prompt` (rides the proven persona seam — `loop.py:1899` prepends `system_prompt` as the system message) AND passes the registry to the executor; `build_handler` threads `skill_registry` through; the chat `router` passes `get_default_skill_registry()`.
- **No DB, no migration, no new SSE wire event** (the `read_skill` call streams via the existing Cat 2 tool rendering; wire count 24 unchanged), no frontend change (chat-v2 already renders tool calls + assistant output). `PyYAML` added to `requirements.txt` (the loader needs `yaml.safe_load`; previously transitive-only). The chat path derives the tool-permission matrix from the live registry (`handler.py:555-563`), so `read_skill` auto-gets a PASS rule once registered — no `capability_matrix.yaml` edit.

System-bundled only this spike (no per-tenant catalogs); rejected: auto-match injection (less agentic), a `/skill` slash command (FE plumbing — later), placeholder skills (AP-4).

## Verification

- Unit (`tests/unit/agent_harness/skills/test_skills_{registry,tool}.py`, 14): loader parse / skip-malformed / register-dup / get / list-order / bundled-load / catalog-block render / singleton; read_skill framed-instructions / recoverable-miss / spec-valid-schema.
- Integration (`tests/integration/api/test_skills_wiring.py`, 6): executor opt-in registers `read_skill` (+ negative guard) / read_skill executes through `executor.execute` / `build_handler(skill_registry=reg)` appends the block to `loop._system_prompt` / no-registry regression (`== DEMO_SYSTEM_PROMPT`) / scripted-LLM `read_skill` tool call → `ToolCallExecuted` carries the framed instructions on the SSE flow.
- Gates: mypy `src` 0/366 · run_all 10/10 (count 24) · full pytest 2566+5skip (+20, 0 del) · Vitest/mockup-fidelity unchanged (zero FE).
- **Drive-through PASS (real chat-v2 + real Azure LLM, dev-login jamie@acme.com)**: Leg A code-review → `read_skill("code-review")` → structured Summary/Risks-table/Fixes; Leg B summarize → `read_skill("summarize")` → Decisions/Action Items (owner — task)/Open Questions; Leg C "2+2" → NO read_skill, direct answer. Screenshots `artifacts/dt57113-{A,B,C}-*.png`. Output shapes distinctly followed the loaded skills (load+follow proven, not generic).

## Impact

Backend + bundled-content only; no DB / no migration / no wire / no FE. Opens the Skills System epic; deferred: per-tenant catalogs (`AD-Skills-Per-Tenant-Catalog`), `/skill` slash command (`AD-Skills-Slash-Command`), a dedicated Inspector affordance (`AD-Skills-Inspector-Affordance`), an authoring UI (`AD-Skills-Authoring-UI`), bundled executable scripts (`AD-Skills-Bundled-Scripts`).
