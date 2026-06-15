# CHANGE-085: Skills bundled scripts — system-bundled `run_skill_script`

**Date**: 2026-06-15
**Sprint**: 57.118
**Scope**: 範疇 5 (Prompt Construction — `Skill.script` + loader) + 範疇 2 (Tool Layer — `run_skill_script` + `SandboxBackend` reuse) + business_domain wiring
**AD**: closes the system-bundled leg of `AD-Skills-Bundled-Scripts` (4th Skills System slice)

## Problem / Motivation

The Skills System (57.113–57.117) could only inject TEXT instructions. CC's skills can ship executable scripts that run in a sandbox; the harness had no way for a bundled skill to carry a script the model can run. This is cc-parity row 9's remaining executable half.

## Solution

A SYSTEM-BUNDLED skill may now ship a sibling `<stem>.py` next to its `SKILL.md`; the model runs it on demand via a new Cat-2 tool, through the existing sandbox.

- **`Skill.script` field** (`agent_harness/skills/registry.py:54-68`) — `frozen` dataclass gains `script: str | None = None` (keyword-defaulted last; overlay/no-sibling skills stay `None`).
- **Sibling loader** (`registry.py:130-160`) — `from_dir` reads a sibling `md_path.with_suffix(".py")` (`is_file()` guard; `OSError` → warn + `None`) into `Skill.script`. Glob stays `*.md` (a lone `.py` never registers).
- **`run_skill_script` tool** (`agent_harness/skills/tool.py:114-202`) — `RUN_SKILL_SCRIPT_TOOL_SPEC` (input `{skill_name}` only; `read_only=False` / `risk_level=MEDIUM` / `tags=("skills","exec")`) + `make_run_skill_script_handler(registry, sandbox=None)`: unknown / no-script → recoverable message; else `backend.execute(skill.script, timeout_seconds=10.0, memory_mb=256, network_blocked=True)` → JSON `{stdout,stderr,exit_code,duration_seconds,killed_by_timeout}`. The source is `Skill.script` (server-loaded), never an LLM arg. A process-wide `_get_default_sandbox()` lazy singleton (`tool.py:153-161`) probes Docker once.
- **Chat wiring (opt-in)** (`business_domain/_register_all.py:306-310`) — the `skill_registry` opt-in now also registers `run_skill_script`; the registry-derived risk-blind permission matrix (`api/v1/chat/handler.py:588-592`) auto-PASSes it. NO per-request Docker probe (sandbox=None → lazy singleton).
- **Demo skill** (`agent_harness/skills/bundled/digest.{md,py}`) — `digest.py` prints `hashlib.sha256(b"agent-harness-bundled-skill").hexdigest()` (a RUNTIME value the LLM cannot fabricate — the execution proof).

Trust model: **supply-chain-at-authorship (git + review) + isolation-at-runtime (sandbox)**. Tenant-authored scripts, multi-file resources, script args, and an authoring UI are deferred (design note 34 §5).

NO DB / migration / wire event (count 24) / codegen / frontend this sprint.

## Verification

- **Gate**: mypy `src` 0/371 (+1 `digest.py`) · black/isort/flake8 0 · `python scripts/lint/run_all.py` 10/10 (count 24, `check_cross_category_import` green — skills→tools is Cat2→Cat2) · backend pytest **2644 passed, 5 skipped** (+14, 0 del) vs 2630 · Vitest 873 / mockup 51 unchanged (no frontend) · `loop.py`/`events.py`/`sse.py`/`event_wire_schema` UNTOUCHED.
- **Test-layer real execution**: `test_skills_wiring.py::test_run_skill_script_runs_bundled_digest_in_real_sandbox` runs the bundled `digest` script in a real injected `SubprocessSandbox()` → stdout == local sha256.
- **Drive-through (real chat-v2 :3007 + Azure gpt-5.2 + REAL DockerSandbox 29.5.2, tenant acme-skills)** — model self-selected the digest skill: `read_skill` → `run_skill_script("digest")` (span 546 ms, exit_code 0) → final answer `039e824cfd166d0c491ca12b290e28b6da2d89b0eaceca4b33a57231517b8b1e` == local ground truth byte-for-byte, verification 0.99. **First main-flow proof of sandboxed execution.** Screenshot `…/sprint-57-118/artifacts/sprint-57-118-drivethrough-digest.png`.

## Impact

Backend-only (Cat 5 + Cat 2 + business_domain wiring); additive + opt-in. No DB/migration/wire/frontend. Existing skills (no sibling `.py`) and tenant-overlay skills are unaffected (`script=None`). Reverting commits `2cedace8` + `5de95ef5` restores the exact 57.117 state. Design note: `docs/03-implementation/agent-harness-planning/34-skills-bundled-scripts.md`.
