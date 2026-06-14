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

## Day 2 — 2026-06-14 — `GET /chat/skills` + router force-load validate-and-pass (US-2 + US-3 router half)

**Done (2.1 + 2.2)**:
- `router.py`: NEW `GET /skills` (`list_chat_skills`) — `Depends(get_current_tenant)` (non-admin) + `get_db_session`, `resolve_tenant_skill_registry` → `ChatSkillsResponse(name+description)`. Chat POST: `forced_skill = req.force_load_skill if (req.force_load_skill and skill_registry.get(...)) else None` → `build_handler(force_load_skill=forced_skill)`. + MHist.
- `schemas.py`: `ChatSkillItem`/`ChatSkillsResponse` (added Day-1).

**Bug caught + fixed (router prefix)**: the GET tests 404'd — the chat `router` carries an internal `prefix="/chat"`, so the real app mounts it at `/api/v1` (→ `/api/v1/chat/...`). My test app initially used `include_router(prefix="/api/v1/chat")` → double `/chat/chat/skills`. Fixed to `prefix="/api/v1"`. (Route inventory confirmed: `GET /chat/skills` registered, no `GET /{param}` catch-all to shadow it.)

**Plan-vs-repo adjustment (Day 2)**: same DRY principle as Day-1 — the force-load **per-tenant** tests went into a focused NEW `test_chat_force_load_skill.py` (custom body / override body / unknown-graceful, reusing the per-tenant resolver harness); the build-level present/absent/unknown cases stayed in `test_skills_wiring.py` (Day-1). The plan's "stubbed-LLM read_skill-not-auto-called" assertion is deferred to the Day-4 drive-through (the real-LLM read_skill 0× proof) — a scripted MockChatClient can't meaningfully prove "the model didn't NEED read_skill".

**Tests/gate (Day-2)**: new GET ×5 + force-load ×3 → 11/11 with the per-tenant regression; chat+skills sweep **204 passed**; `mypy src` **0/370** (+4 files); `flake8` 0 (fixed a docstring E501); `run_all.py` **10/10** (wire count 24 unchanged, sdk-leak green); full pytest running (background).

**Touch points**: `router.py` (EDIT) + `test_chat_skills_list.py` (NEW) + `test_chat_force_load_skill.py` (NEW). `loop.py`/`make_default_executor`/wire/codegen/migration UNTOUCHED.

---

## Day 3 — 2026-06-14 — Frontend `/skill-name` picker + plumbing (US-4 + US-5)

**Prong-2.5 (deferred from Day-0)**: `InputBar.tsx` + composer chrome use mockup classes + inline mockup-token styles — NO shadcn-utility residue. GREEN.

**Done (3.1 + 3.2 + 3.3)**:
- `chatService.ts`: `ChatRequestBody += force_load_skill?`; `ChatSkill`/`ChatSkillsResponse`; `fetchChatSkills()` (GET, mirrors listSessions).
- `useChatSkills.ts` (NEW): TanStack `useQuery(["chat-v2","skills"], enabled, staleTime 60s)`.
- `useLoopEventStream.ts`: `send(message, opts?: {forceLoadSkill?})` → threads into the streamChat body.
- `SkillSlashMenu.tsx` (NEW): presentational dropdown (mockup tokens + `var(--shadow)` + file-level eslint-disable; `aria-selected`/`tabIndex=-1`).
- `InputBar.tsx`: `/`-trigger (gated `!isRunning && real_llm`), filter, keyboard ↑/↓/Enter/Esc, `matchForceLoad` (leading KNOWN-skill token → forceLoadSkill + strip), conditional `send`.

**Bugs caught + fixed**:
- a11y lint `interactive-supports-focus` (role="option" needs focusable) → `tabIndex={-1}`.
- mockup-fidelity FAIL — my `SkillSlashMenu` shadow `oklch(0 0 0 / 0.3)` was a NEW colour literal (51→52) → switched to the `var(--shadow)` token (no literal; baseline 51 holds). The Day-0 silent-constraint-delta drift class in action.
- existing `InputBar.test.tsx` would break (InputBar now imports `useChatSkills` → `useQuery` needs a provider) → added a `useChatSkills` mock there (`{data:[]}`); also made `onSend` pass 1-arg `send(msg)` when no force-load so the existing `toHaveBeenCalledWith("hello")` stays green (Never-Delete: mock added, no test removed).

**Plan-vs-repo adjustment**: the `useChatSkills` mock in the existing `InputBar.test.tsx` is a Never-Delete-safe addition (the 57.101 inject tests stay green, unchanged assertions).

**Tests/gate (Day-3)**: chat_v2 Vitest 15/15 (4 menu + 8 slash + 3 existing) → full Vitest **863 passed (+12 vs 851)**; `npm run lint` 0 (no `--silent`); `npm run build` clean; `npm run check:mockup-fidelity` **51** holds.

**Touch points**: `chatService.ts` · `useLoopEventStream.ts` · `InputBar.tsx` (EDIT) + `useChatSkills.ts` · `SkillSlashMenu.tsx` (NEW) + 2 NEW Vitest + `InputBar.test.tsx` (mock add). `chatStore`/wire/codegen UNTOUCHED.

---

## Day 4 — 2026-06-14 — Drive-through (ALL 3 legs PASS) + closeout

**Clean restart (Risk Class E)**: killed stale backend PID 38756 (57.114 code) + a transient PID 6716 (started from `backend/` CWD → `.env` not found → no Azure); ZERO python orphans confirmed; restarted from **repo-root** with `--env-file .env` + `PYTHONPATH=backend/src` (the `env_file=".env"` is CWD-relative + `.env` lives at repo root) → fresh PID, startup complete, pricing/SLA/billing wired, Azure loaded. Frontend :3007 (node, HMR serves the new FE). Reused dev tenant **acme-skills** (jamie@acme.com via dev-login cookie) — its 57.114 overlay `release-notes` + bundled `code-review`/`summarize` persisted.

**Endpoint live-probe**: `GET /api/v1/chat/skills` → **200** `{code-review, summarize, release-notes}` name+description, **NO `instructions`** (no-leak confirmed live).

**Leg A (force-load determinism) PASS** — real chat-v2 + real Azure gpt-5.2:
- Picker `/release-notes` → Enter selects → typed a generic task → Send.
- User turn shows the CLEAN message ("We shipped dark mode and fixed two login crashes this week.") — **the `/release-notes` token was stripped**.
- Agent output followed the release-notes skill EXACTLY: `## Summary` / `## Highlights` (bullets) / `## Upgrade steps` (numbered).
- **`read_skill` called 0×** — the Loop trace shows `llm_response: 0 tool calls`, NO `read_skill` event (the instructions were force-injected into the `## Active Skill` system-prompt block; input 3495 est / 2425 actual tokens). Verification 0.98 PASS. → deterministic injection PROVEN distinct from model-invoked. Screenshot `legA-forceload-output-follows-readskill-0x.png`.

**Leg B (picker discoverability + filter) PASS**:
- `/` → the picker lists all 3 (`/code-review`, `/summarize`, `/release-notes` overlay). Screenshot `legB-picker-open-all-skills.png`.
- `/re` → filtered to code-review + release-notes (both contain "re" substring); `summarize` correctly dropped. Keyboard select (Enter) inserted `/release-notes ` + closed the menu.

**Leg C (graceful unknown) PASS**:
- `/nonexistent reply with exactly: OK` → NO menu (empty filter, no dead control) → Send enabled.
- User turn shows the LITERAL `/nonexistent reply with exactly: OK` (NOT stripped — unmatched token = plain text) → agent answered **"OK"** normally, verification 0.99, no error. Screenshot `legC-unknown-token-graceful-plain-text.png`.

**Drive-Through-Acceptance**: the picker DRIVES the request (force-load changes the output + read_skill 0×, not a cosmetic menu); all controls live (type/filter/keyboard-select/send); no fixture, no dead control, no mislabeled output (AP-4 guard satisfied). OTel "Failed to detach context" log noise is pre-existing async-tracer teardown (not a functional failure; both legs verified 0.98/0.99).

---
