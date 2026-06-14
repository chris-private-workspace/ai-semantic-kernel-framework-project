# CHANGE-082: Skills Slash-Command (`/skill-name` force-load)

**Date**: 2026-06-14
**Sprint**: 57.115
**Scope**: 範疇 5 (Prompt Construction) + 範疇 2 (Tool Layer) + api/v1/chat + frontend chat_v2

## Problem

The Skills System (57.113 bundled lazy-load + 57.114 per-tenant overlay) was **model-invoked only** — the model decided whether to call `read_skill`. A user had no way to **explicitly** activate a skill. `AD-Skills-Slash-Command` ("Option C: a `/skill-name` UI slash command + FE plumbing + a force-load path") was the deferred user-invoked half.

## Root Cause

By design, 57.113/57.114 shipped the CC-faithful model-self-selection core first and deferred the user-invoked path. No request field, no chat-user-facing skills list endpoint, no composer affordance existed.

## Solution

A **deterministic force-load** path + a greenfield composer picker (closes `AD-Skills-Slash-Command`):

- **Force-load primitive** (Cat 5/handler): a shared `render_skill_instructions(skill)` helper (`registry.py`, DRY with the `read_skill` tool — output byte-identical); `build_handler`/`build_real_llm_handler` gain `force_load_skill: str | None` → when set + present in the registry, a `## Active Skill` section appends the skill's FULL instructions to the system prompt AFTER the catalog block. The model loads the skill WITHOUT calling `read_skill` (deterministic).
- **Picker list endpoint** (主流量): `GET /api/v1/chat/skills` — non-admin, `current_tenant`-scoped, resolves `resolve_tenant_skill_registry`, returns `{name, description}` ONLY (no `instructions` body — never leaks to a list).
- **Request field + router**: `ChatRequest.force_load_skill` (kebab, optional); the chat POST validates it against the resolved registry (unknown → `None`, graceful) and threads it to `build_handler`.
- **FE picker** (greenfield): `SkillSlashMenu.tsx` (filtered dropdown, keyboard ↑/↓/Enter/Esc) + `InputBar.tsx` `/`-trigger (gated `!isRunning && real_llm`) + leading-token parse (KNOWN skill only → `force_load_skill` + strip from the message) + `useChatSkills` (TanStack) + `useLoopEventStream.send(message, {forceLoadSkill})`.

**NOT changed**: `make_default_executor` / `loop.py` / `read_skill`'s self-select behavior / the wire schema (count 24) / any codegen / any migration. `read_skill` stays available for model self-selection of OTHER skills.

Code: `backend/src/agent_harness/skills/{registry,tool,__init__}.py` · `backend/src/api/v1/chat/{handler,schemas,router}.py` · `frontend/src/features/chat_v2/{services/chatService,hooks/useChatSkills,hooks/useLoopEventStream,components/SkillSlashMenu,components/InputBar}.tsx`. PR (Sprint 57.115).

## Verification

- **Gates**: mypy `src` 0/370 · `run_all.py` 10/10 (wire 24, no codegen) · backend pytest **2616+5skip (+14, 0 del)** · FE lint 0 · build · Vitest **863 (+12)** · mockup-fidelity **51** (shadow `oklch` literal → `var(--shadow)` token; baseline held).
- **Drive-through (real chat-v2 :3007 + real Azure gpt-5.2, tenant acme-skills)** — ALL 3 legs PASS:
  - **A** force-load determinism: `/release-notes` + a generic task → output followed `## Summary/## Highlights/## Upgrade steps` EXACTLY + Loop trace `llm_response: 0 tool calls` (`read_skill` **0×** — force-injected) + the `/release-notes` token stripped from the user turn; verification 0.98.
  - **B** picker: `/` listed all 3; `/re` filtered (summarize dropped); Enter selected.
  - **C** graceful unknown: `/nonexistent …` → no menu, literal token (plain text), agent answered "OK", verification 0.99, no error.
  - Screenshots: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-115/artifacts/leg{A,B,C}-*.png`.

## Impact

Full-stack (backend force-load + new GET endpoint + greenfield FE picker). The user-invoked half of the Skills epic; `AD-Skills-Slash-Command` closed. Inspector "skill force-loaded" affordance, multi-skill commands, and a rich authoring UI stay deferred (see `next-phase-candidates.md`). Design note `33-skills-slash-command.md`.
