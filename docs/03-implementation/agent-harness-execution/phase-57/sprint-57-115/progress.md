# Sprint 57.115 Progress — Skills Slash-Command (`/skill-name` force-load)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-115-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-115-checklist.md)

---

## Day 0 — 2026-06-14 — Plan-vs-Repo Verify (三-prong) + Branch

**Branch**: `feature/sprint-57-115-skills-slash-command` (from `main` `706de5b3`) ✅

### Prong 1 — path verify
- **NEW absent (Glob-0)** ✅: `SkillSlashMenu.tsx`, `useChatSkills.ts` — both 0 results. Design note 33 / CHANGE-082 free.
- **EDIT present** ✅: `registry.py` / `tool.py` / `handler.py` / `schemas.py` / `router.py` (all read/grepped) · `chatService.ts` / `useLoopEventStream.ts` (read) · `InputBar.tsx` (exists, read deferred to Day 3).
- **Test paths** ✅: FE tests → `frontend/tests/unit/chat_v2/` (EXISTS: `InputBar.test.tsx` + `HITLTurn.resume.test.tsx`) → new `InputBar.slash.test.tsx` + `SkillSlashMenu.test.tsx` basenames unique (no collision w/ existing `InputBar.test.tsx`; 57.109 unique-basename rule). Backend skills tests → `backend/tests/unit/agent_harness/skills/` (EXISTS: registry/tool/overlay) → `test_render_skill_instructions.py` unique.

### Prong 2 — content verify (drift findings)
- **D-build-handler-systemprompt** 🟢 CONFIRMED: TWO builders — `build_real_llm_handler` (`handler.py:272`) does the catalog append at `:489-492` (`system_prompt = f"{system_prompt}\n\n{skills_block}"`, local string) → passed to the loop ctor at `:684`. `build_handler` (`:713`) DELEGATES to `build_real_llm_handler` for `real_llm` (`:756-784`, threads `skill_registry=`), echo path (`:749-755`) gets NO registry. → add `force_load_skill: str | None = None` to BOTH; the `## Active Skill` append goes right after `:492`; `build_handler` threads it to the `build_real_llm_handler(...)` call. Echo path never receives it → force-load no-ops on echo (the D-echo-path concern resolves itself).
- **D-read-skill-string** 🟢 CONFIRMED: exact return (`tool.py:90-94`) = `f"# Skill: {skill.name}\n\n{skill.instructions}\n\nFollow these instructions for the current task."` → `render_skill_instructions(skill) = f"# Skill: {skill.name}\n\n{skill.instructions}"`; the tool appends `"\n\nFollow these instructions for the current task."` → byte-identical. The existing `test_skills_tool.py` asserts this string → stays green after the DRY refactor (Never-Delete: no conversion needed).
- **D-chat-deps** 🟢 CONFIRMED: chat POST `@router.post("/")` (`router.py:164`); `current_tenant: UUID = Depends(get_current_tenant)` (`:167`) + `db`; `from platform_layer.skills import resolve_tenant_skill_registry` (`:136`); resolved `:264`; `build_handler(` `:282`. `get_current_tenant` from `platform_layer.identity` — the NON-admin chat gate (reuse for `GET /skills`).
- **D-route-collision** 🟢 CONFIRMED: chat router GET routes = only `GET /sessions/{session_id}` (`:973`); param POSTs are `/{session_id}/inject` `/{session_id}/resume` `/{session_id}/cancel`. NO `GET /{param}` catch-all at the root → `GET /skills` (static segment) is collision-free. (The 57.107 session-LIST `GET /api/v1/sessions` lives on a DIFFERENT router, not under `/chat`.)
- **D-chatrequest-config** 🟢 CONFIRMED: `ChatRequest` (`schemas.py:41-46`) = `{message, session_id, mode}`, NO `model_config` (so no `extra="forbid"`); `Field` already imported → add `force_load_skill: str | None = Field(default=None, max_length=128, pattern=r"^[a-z0-9-]+$")` safely.
- **D-fe-send-sig** 🟢 CONFIRMED: `useLoopEventStream.send: (message: string) => Promise<void>` (`:44`, body `:62-94`) → single-arg today; add `opts?: { forceLoadSkill?: string }` + thread into the `streamChat({ message, mode, ...session_id, ...force_load_skill })` body. `chatService.ChatRequestBody = {message, mode, session_id?}` (`:52-56`); `streamChat(body, opts)` POSTs `JSON.stringify(body)` to `/api/v1/chat/` (`:99-127`). The new GET mirrors `listSessions` (`:81-89`): `fetchWithAuth("/api/v1/chat/skills", {method:"GET"})` → check ok → parse json.
- **D-echo-path** 🟢 RESOLVED (see D-build-handler): echo `build_handler` branch passes NO registry/force_load → force-load is a structural no-op on echo (no extra guard needed).
- **D-fe-tree (Prong-2.5)** ⏳ DEFERRED to Day-3 start: read `InputBar.tsx` + composer chrome for shadcn-utility residue before editing; `SkillSlashMenu` is net-new (no vintage drift). Will style with `styles-mockup.css` tokens.

### Prong 3 — N/A (no new table / migration / ORM this sprint).

### Go/no-go: 🟢 **GO**
Design fully confirmed against the real repo — no scope shift > 20%. The 3 backend touch points (DRY helper + `build_handler` append + `GET /skills` + `force_load_skill` field/router) are all light mirrors of existing machinery; the greenfield FE picker is the main net-new surface. Refinement adopted from Day-0: force-load param goes on BOTH `build_real_llm_handler` (the append site) AND `build_handler` (the delegating entry the router calls).

### Baselines to re-verify at Day-2/Day-3 gate
pytest 2602+5skip · wire 24 · Vitest 851 · mockup-fidelity 51 · mypy `src` 0/366 · run_all 10/10.

---

## Day 1 — 2026-06-14 — Backend force-load primitive (US-1 + US-3 schema half)

**Done (1.1 + 1.2 + 1.3)**:
- `registry.py`: NEW `render_skill_instructions(skill) -> "# Skill: {name}\n\n{instructions}"` (DRY body) + re-exported from `skills/__init__.py`.
- `tool.py`: `make_read_skill_handler` now calls `render_skill_instructions` + its trailing directive → **output byte-identical** (the existing `test_skills_tool.py` 3 tests stay green, no conversion needed — Never-Delete satisfied).
- `handler.py`: `build_real_llm_handler` + `build_handler` both gain `force_load_skill: str | None = None`; after the catalog block, a `## Active Skill` section appends the picked skill's full instructions deterministically (the model does NOT need read_skill). `build_handler` threads it to the real_llm builder; echo path never receives it (structural no-op).
- `schemas.py`: `ChatRequest.force_load_skill: str | None` (kebab pattern, max 128, default None) + `ChatSkillItem`/`ChatSkillsResponse` (Day-2 GET schemas, done early for file cohesion).

**Plan-vs-repo adjustment (Day 1)**: the checklist named a NEW `tests/unit/api/v1/chat/test_build_handler_force_load.py`, but `tests/integration/api/test_skills_wiring.py` (57.113) ALREADY carries the exact harness I need (`_set_fake_azure` monkeypatch → Azure-call-free `build_handler` + `loop._system_prompt` inspection). Per "check existing before building" + DRY, the 3 force-load tests were **added to that file** instead of duplicating the fixture harness in a new unit file. No new test file for 1.2.

**Tests/gate (Day-1 focused)**: `pytest test_render_skill_instructions.py test_skills_tool.py test_skills_wiring.py` → **16/16 pass** (3 new helper + 3 existing read_skill byte-identical + 3 new force-load + 7 existing wiring). `flake8` 0 (fixed a registry.py:30 MHist E501 — shortened) · `mypy` 0/5 changed modules.

**Touch points**: `registry.py` · `tool.py` · `skills/__init__.py` · `handler.py` · `schemas.py` (5 src) + `test_render_skill_instructions.py` (NEW) + `test_skills_wiring.py` (EDIT). `make_default_executor`/`loop.py`/`read_skill` behavior/wire schema UNTOUCHED.

---
