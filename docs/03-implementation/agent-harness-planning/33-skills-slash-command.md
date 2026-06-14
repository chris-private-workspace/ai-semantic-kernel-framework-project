# 33 — Skills Slash-Command (`/skill-name` force-load)

**Purpose**: Design note extracted from Sprint 57.115 — the user-invoked force-load path of the Skills System (a `/skill-name` composer picker + deterministic system-prompt injection), closing `AD-Skills-Slash-Command`.
**Category / Scope**: 範疇 5 (Prompt Construction) + 範疇 2 (Tool Layer) + api/v1/chat + frontend chat_v2 / Sprint 57.115
**Created**: 2026-06-14
**Last Modified**: 2026-06-14
**Status**: Active (spike-extract; verified ratio ~96%)

> **Modification History**
> - 2026-06-14: Initial creation (Sprint 57.115) — slash-command force-load (3rd Skills slice)

> **Epic chain**: `31-skills-system-spike.md` (bundled model-invoked lazy-load) → `32-skills-per-tenant-catalog.md` (per-tenant overlay) → **this** (user-invoked force-load).

---

## 1. Spike Summary (US-1..US-6 as wired in Sprint 57.115)

The Skills System gains a **user-invoked** path alongside the 57.113 model-invoked one. A chat user types `/` in the chat-v2 composer → a `SkillSlashMenu` lists the tenant's effective skills (`GET /api/v1/chat/skills`) → selecting one (or typing `/skill-name`) sets `ChatRequest.force_load_skill` → the chat router validates it and `build_handler` appends the skill's FULL instructions to the turn's system prompt under a `## Active Skill` header — so the skill loads **deterministically, without the model calling `read_skill`**.

## 2. Decision Matrix — force-load mechanism

| Option | How | Pros | Cons | Decision |
|--------|-----|------|------|----------|
| **A. Deterministic system-prompt injection** | `build_handler` appends `## Active Skill` + the full instructions to `system_prompt` when `force_load_skill` is set | Guaranteed load (model-independent); provable via `read_skill` 0×; rides the existing 57.113 catalog seam (1 append) | The forced body inflates the per-turn system prompt (acceptable — it's per-request) | ✅ **CHOSEN** (user-confirmed 2026-06-14) |
| B. Force a `read_skill` tool CALL | Pre-seed a synthetic `read_skill(name)` tool call/result | Visible in the Inspector tool stream | Indirect; the model may still ignore the loaded body; harder to prove; needs a synthetic tool-result injection point | ❌ rejected |
| C. Message-text directive | Prepend "use the X skill" to the user message | No schema change | Fragile; the model may ignore; pollutes the user message; the model sees the directive | ❌ rejected |

| Sub-decision | Choice | Rationale |
|--------------|--------|-----------|
| Skills per command | **single** `force_load_skill: str` | `/skill-name` = one skill; multi-skill is additive later (YAGNI) |
| Picker list endpoint | **NEW non-admin `GET /chat/skills`** (name+description only) | The admin CRUD `/admin/tenants/{id}/skills` needs admin role; a chat user can't use it; instructions body never leaks to a list |
| Picker UI | greenfield `SkillSlashMenu` (custom dropdown) | `CommandPalette` (cmdk ⌘K) is global navigation, not anchorable to a textarea `/` trigger |
| Composer→backend signal | a **request field** (`force_load_skill`), token stripped FE-side | the model never sees the `/token`; mirrors the `session_id?` pattern |

## 3. Verified Invariants (file:line; gate + drive-through proven)

- **DRY body helper** — `render_skill_instructions(skill) -> "# Skill: {name}\n\n{instructions}"` `backend/src/agent_harness/skills/registry.py` (re-exported `skills/__init__.py`). The `read_skill` tool `tool.py:make_read_skill_handler` calls it + appends its trailing directive → output **byte-identical** to pre-refactor (asserted `test_render_skill_instructions.py` + existing `test_skills_tool.py` stays green).
- **`## Active Skill` injection** — `build_real_llm_handler` (`handler.py`, after the catalog append `~:489-492`) + `build_handler` (delegates, threads `force_load_skill`). When `force_load_skill` + registry + `skill_registry.get(name)`, appends the `## Active Skill` section; absent/unknown → no block (byte-identical). Echo path never receives a registry → structural no-op. Verified `test_skills_wiring.py` (3 build-level) + `test_chat_force_load_skill.py` (3 per-tenant: custom body / override body / unknown-graceful).
- **`GET /api/v1/chat/skills`** — `router.py:list_chat_skills`, `Depends(get_current_tenant)` (NON-admin) + `get_db_session`, `resolve_tenant_skill_registry` → `ChatSkillsResponse{name, description}` (NO `instructions`). Registered after the chat POST (router internal prefix `/chat`; no `GET /{param}` catch-all to shadow). Verified `test_chat_skills_list.py` (5: bundled / overlay / no-instructions / tenant-scoped / 401). Live-probed in the drive-through (200, no instructions key).
- **Request field + router validate-and-pass** — `ChatRequest.force_load_skill: str | None = Field(pattern=r"^[a-z0-9-]+$", max_length=128)` (`schemas.py`); chat POST `forced_skill = req.force_load_skill if (… and skill_registry.get(…)) else None` (`router.py`, after `:264`) → `build_handler(force_load_skill=forced_skill)`. Unknown name → graceful `None`.
- **FE force-load wiring** — `chatService.ChatRequestBody += force_load_skill?` + `fetchChatSkills()`; `useChatSkills` (TanStack, gated real_llm); `useLoopEventStream.send(message, {forceLoadSkill})`; `SkillSlashMenu.tsx` (presentational, `aria-selected`/`tabIndex=-1`, `var(--shadow)` token); `InputBar.tsx` `/`-trigger + `matchForceLoad` (leading KNOWN-skill token → strip + `forceLoadSkill`). Verified `SkillSlashMenu.test.tsx` (4) + `InputBar.slash.test.tsx` (8).
- **Drive-through (real chat-v2 + Azure gpt-5.2, tenant acme-skills)** — Leg A: `/release-notes` + generic task → output followed `## Summary/## Highlights/## Upgrade steps` + Loop trace `llm_response: 0 tool calls` (**`read_skill` 0×** — deterministic injection proven) + token stripped, verification 0.98. Leg B: `/` lists 3, `/re` filters. Leg C: `/nonexistent` → literal plain text, agent "OK", 0.99, no error. Screenshots in `…/sprint-57-115/artifacts/`.

## 4. Cross-Category Contracts (17.md)

**Decision: NO new contract in 17.md.** `force_load_skill` is an additive optional field on the existing `ChatRequest` (api-level HTTP contract, not an agent_harness cross-category ABC); `render_skill_instructions` is an intra-Cat-5 helper; `GET /chat/skills` is an api endpoint. This mirrors the 57.113/57.114 precedent (the Skills registry seam was not registered as a 17.md contract — it rides the existing `build_handler(skill_registry=)` parameter). No new ABC, no provider-neutral type change.

## 5. Open Invariants (deferred — NOT verified here)

- **Inspector "skill force-loaded" affordance** (`AD-Skills-Inspector-Affordance`) — force-load is invisible in the timeline after send (the `/token` is stripped); a dedicated SSE wire event / a "skill: X active" chip on the user turn is deferred (wire count stays 24).
- **Multi-skill per command** — single `force_load_skill`; `force_load_skills: list` is additive (YAGNI).
- **Echo-mode force-load** — gated OFF (the echo mock ignores `force_load_skill`); no behavior in echo.
- **Picker for a stale/renamed skill** — the FE only force-loads a name present in `useChatSkills`; a renamed skill mid-session would need a refetch (TanStack staleTime 60s).

## 6. Rollback / Fallback

- The feature is purely additive + opt-in: `force_load_skill` defaults `None` (no `## Active Skill`); the picker is gated `!isRunning && real_llm`. Reverting the 3 commits restores the 57.114 state (model-invoked only) with zero schema/migration to undo.
- `GET /chat/skills` is a new read endpoint (no state); removing it only breaks the picker fetch (the composer falls back to no menu).
- The `render_skill_instructions` DRY refactor is byte-identical — reverting it is safe (the tool output is unchanged either way).

## 7. References

- `31-skills-system-spike.md` (model-invoked core) · `32-skills-per-tenant-catalog.md` (per-tenant overlay)
- `claudedocs/5-status/agent-harness-cc-parity-20260607.md` row 9 (Skills System cc-parity gap)
- `CHANGE-082-skills-slash-command.md` · `.../sprint-57-115/{plan,checklist,progress,retrospective}.md`
- `.claude/rules/sprint-workflow.md` §Drive-Through Acceptance + §Scope-class matrix (NEW `skills-slash-command-fullstack` 0.55)

## 8. Modification History

- 2026-06-14: Initial creation (Sprint 57.115)
