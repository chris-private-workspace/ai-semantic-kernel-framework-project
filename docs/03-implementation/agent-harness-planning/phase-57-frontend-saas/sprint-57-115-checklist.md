# Sprint 57.115 — Checklist (Skills Slash-Command: a DRY `render_skill_instructions` helper + a `build_handler` `## Active Skill` deterministic force-load + a non-admin `GET /chat/skills` list + a `ChatRequest.force_load_skill` field + router validate-and-pass + a greenfield composer `SkillSlashMenu` (/ -trigger + keyboard + leading-token parse) — the third slice of the Skills System epic, closes `AD-Skills-Slash-Command`; Inspector affordance / multi-skill / authoring deferred)

[Plan](./sprint-57-115-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong; no Prong-3 schema — no new table) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `706de5b3`) — catalogued in progress.md ✅
- [x] **Prong 1 — path verify**: NEW absent (Glob-0) — `SkillSlashMenu.tsx` / `useChatSkills.ts` confirmed 0; EDIT present confirmed; design note 33 / CHANGE 082 free; FE tests → `frontend/tests/unit/chat_v2/` (basenames unique vs existing `InputBar.test.tsx`)
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-build-handler-systemprompt (CRITICAL)** 🟢: `build_real_llm_handler:272` appends the catalog at `:489-492` (local `system_prompt`) → loop ctor `:684`; `build_handler:713` delegates to it for `real_llm` (echo gets NO registry) → force-load param on BOTH; append after `:492`
  - [x] **D-read-skill-string** 🟢: exact string `tool.py:90-94` confirmed → `render_skill_instructions` + the trailing line byte-identical (existing `test_skills_tool.py` stays green)
  - [x] **D-chat-deps** 🟢: `current_tenant = Depends(get_current_tenant)` (`router.py:167`) + db; `resolve_tenant_skill_registry` imported `:136` + called `:264`; `build_handler(` `:282`
  - [x] **D-route-collision** 🟢: only `GET /sessions/{session_id}` (`:973`); no `GET /{param}` catch-all → `GET /skills` static-segment safe
  - [x] **D-chatrequest-config** 🟢: `ChatRequest` no `model_config` (no `extra=forbid`); `Field` already imported
  - [x] **D-fe-send-sig** 🟢: `send: (message)=>` single-arg (`useLoopEventStream:44`) → add opts; `ChatRequestBody{message,mode,session_id?}`; new GET mirrors `listSessions` `fetchWithAuth` pattern
  - [ ] **D-fe-tree (Prong-2.5)** — DEFERRED to Day-3 start (read `InputBar.tsx` before editing)
  - [x] **D-echo-path** 🟢 RESOLVED: echo `build_handler` branch passes NO registry/force_load → force-load structural no-op
- [x] **Prong 3 — N/A** (no new table / migration / ORM this sprint)
- [x] **Catalog drift** findings in progress.md Day 0
- [x] **Go/no-go**: 🟢 GO — design confirmed, no scope shift > 20%

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-115-skills-slash-command` (from `main` `706de5b3`) ✅

---

## Day 1 — Backend: `render_skill_instructions` (DRY) + `build_handler` force-load + force-load field (US-1, US-3 backend half)

### 1.1 `render_skill_instructions` (Cat 5, DRY) + `read_skill` refactor ✅
- [x] **`agent_harness/skills/registry.py`** (EDIT): `render_skill_instructions(skill) -> str` = `f"# Skill: {skill.name}\n\n{skill.instructions}"`; WHY block + MHist; re-exported from `skills/__init__.py`
- [x] **`agent_harness/skills/tool.py`** (EDIT): `make_read_skill_handler` uses `render_skill_instructions` + the trailing directive (byte-identical)
- [x] **`tests/unit/agent_harness/skills/test_render_skill_instructions.py`** (NEW ×3): helper shape · no-trailing-directive · `read_skill` output byte-identical to the exact pre-refactor literal
  - DoD: ✅ 16/16 pass (incl. existing `test_skills_tool.py` green); mypy 0

### 1.2 `build_handler` `## Active Skill` force-load (US-1) ✅
- [x] **`api/v1/chat/handler.py`** (EDIT): `build_real_llm_handler` + `build_handler` both += `force_load_skill: str | None = None`; after the catalog append, when `force_load_skill` + registry + `(forced := skill_registry.get(name))`, append the `## Active Skill` section (`render_skill_instructions`); `build_handler` threads it to the real_llm call; echo path unaffected
- [x] **`tests/integration/api/test_skills_wiring.py`** (EDIT — NOT a new file; +3 tests): **Day-1 plan-vs-repo adjustment** — the existing wiring test ALREADY has the exact `_set_fake_azure` + `loop._system_prompt` harness → extend it (DRY) rather than duplicate the harness in a new `test_build_handler_force_load.py`. force_load present → `## Active Skill` + instructions + catalog still present · None → no active block · unknown name → graceful no block
  - DoD: ✅ tests pass; `make_default_executor`/`loop.py` UNTOUCHED

### 1.3 `ChatRequest.force_load_skill` field (US-3 schema half) ✅
- [x] **`api/v1/chat/schemas.py`** (EDIT): `ChatRequest` += `force_load_skill: str | None = Field(default=None, max_length=128, pattern=r"^[a-z0-9-]+$")`; ALSO added `ChatSkillItem{name,description}` + `ChatSkillsResponse{skills}` (Day-2 GET schemas, done early for cohesion)
  - DoD: ✅ mypy 0; flake8 0; bad pattern rejected by Pydantic

---

## Day 2 — Backend: `GET /chat/skills` + router validate-and-pass + tests (US-2, US-3 router half)

### 2.1 `GET /api/v1/chat/skills` list endpoint (US-2) ✅
- [x] **`api/v1/chat/schemas.py`** (EDIT): `ChatSkillItem{name, description}` + `ChatSkillsResponse{skills}` (NO `instructions`) — done Day-1 (file cohesion)
- [x] **`api/v1/chat/router.py`** (EDIT): `GET /skills` — `Depends(get_current_tenant)` (NON-admin) + `get_db_session`, `resolve_tenant_skill_registry` → `ChatSkillsResponse` name+description; placed right after the chat POST (router internal prefix `/chat` → effective `/api/v1/chat/skills`; no `GET /{param}` catch-all to shadow it)
- [x] **`tests/integration/api/test_chat_skills_list.py`** (NEW ×5): bundled-only tenant · overlay tenant (bundled+overlay) · NO `instructions` key + body never in payload · tenant-scoped (B never sees A's overlay) · unauthed → **401**
  - DoD: ✅ 5/5 pass (caught + fixed the router's internal `/chat` prefix → mount at `/api/v1` not `/api/v1/chat`)

### 2.2 Chat POST validate-and-pass `force_load_skill` (US-3) ✅
- [x] **`api/v1/chat/router.py`** (EDIT): after `skill_registry = ...` (`:264`), `forced_skill = req.force_load_skill if (req.force_load_skill and skill_registry.get(...) is not None) else None`; pass `force_load_skill=forced_skill` to `build_handler(...)`; comment + MHist
- [x] **`tests/integration/api/test_chat_force_load_skill.py`** (NEW ×3): a tenant-custom skill → `## Active Skill` carries the per-tenant body · a tenant override → the OVERRIDDEN body (force-load respects the 57.114 overlay) · an unknown name → graceful (no block). (The build-level present/absent/unknown + the bundled path are in `test_skills_wiring.py` from Day-1; the chat-POST unknown-graceful at the router is exercised end-to-end in the Day-4 drive-through.)
  - DoD: ✅ tests pass; `handler.py` force-load reached from the 主流量 router (`force_load_skill=forced_skill`)

### 2.3 Backend gate sweep ✅
- [x] mypy `src` **0/370** (+4 files) · black/isort/flake8 0 · `python scripts/lint/run_all.py` **10/10** (count 24, no codegen diff) · `make_default_executor`/`loop.py`/wire/codegen UNTOUCHED · no migration
- [x] full pytest **2616 passed + 5 skip (+14, 0 del)** vs 2602 (123s) ✅
  - Verify: `cd backend && python -m mypy src` ✅ · `python scripts/lint/run_all.py` ✅ (from repo root) · `python -m pytest -q` ✅

---

## Day 3 — Frontend: `SkillSlashMenu` + InputBar `/`-trigger + service/hook/send plumbing (US-4, US-5)

### 3.1 Service + hook + types (US-5)
- [ ] **`features/chat_v2/services/chatService.ts`** (EDIT): `ChatRequestBody` += `force_load_skill?: string` (snake_case, mirroring `session_id`); `type ChatSkill = {name; description}` + `type ChatSkillsResponse = {skills: ChatSkill[]}`; `fetchChatSkills(signal?)` (`GET /api/v1/chat/skills` via the chat service idiom); `streamChat` includes `force_load_skill` when set
- [ ] **`features/chat_v2/hooks/useChatSkills.ts`** (NEW): `useQuery` (`["chat-v2","skills"]`, `fetchChatSkills`) feeding the picker
- [ ] **`features/chat_v2/hooks/useLoopEventStream.ts`** (EDIT): `send(message, opts?: {forceLoadSkill?})` → threads `opts?.forceLoadSkill` into `streamChat` (existing single-arg callers stay valid)

### 3.2 `SkillSlashMenu` + InputBar wiring (US-4)
- [ ] **`features/chat_v2/components/SkillSlashMenu.tsx`** (NEW): filtered dropdown anchored above the composer (name + muted description per row; `activeIndex` highlight; "No matching skills" empty row); `styles-mockup.css` tokens only (`var(--card)`/`var(--border)`/`var(--muted-foreground)`); `data-testid="skill-slash-menu"` + `skill-slash-item-{name}`
- [ ] **`features/chat_v2/components/InputBar.tsx`** (EDIT): `slashActive = text.startsWith("/")` + `slashQuery`; render `<SkillSlashMenu>` when active+matches; keyboard (menu open: ↓/↑ move, Enter select→insert `/{name} `, Esc close; menu closed: Enter send); `onSend` parses `^\/([a-z0-9-]+)\s*` → if it matches an available skill: `forceLoadSkill`+strip, else plain text; `send(message, {forceLoadSkill})`; empty-after-strip → send stays disabled
  - DoD: `npm run build` clean; the menu opens on `/` + selecting force-loads
- [ ] **`features/chat_v2/components/Composer.tsx`** (EDIT — only if the production composer wraps `InputBar` + needs the menu's positioning container; else N/A) — Day-3 confirms `InputBar` is the sole production path

### 3.3 Vitest + FE gates
- [ ] **`tests/unit/chat_v2/SkillSlashMenu.test.tsx`** (NEW): renders the list · filters by query · highlights `activeIndex` · click/Enter calls `onSelect` · empty-filter row
- [ ] **`tests/unit/chat_v2/InputBar.slash.test.tsx`** (NEW): `/` opens the menu · ↑/↓/Enter/Esc behavior · a leading `/skill-name` sets `forceLoadSkill` + strips it · an unmatched `/foo` stays plain text · a mid-message `/` stays plain text · `send` called with `{forceLoadSkill}`
- [ ] FE gates: `npm run lint` (NO `--silent`) 0 error · `npm run build` clean · `npm run test` Vitest **+M vs 851** · `npm run check:mockup-fidelity` **51** holds
  - Verify: `cd frontend && npm run lint && npm run build && npm run test && npm run check:mockup-fidelity`

---

## Day 4 — Drive-through (US-6) + CHANGE-082 + design note 33 + closeout

### 4.1 Drive-through (real chat-v2 :3007 + fresh single-process backend + real Azure LLM; Risk Class E clean restart)
- [ ] **Clean restart + probe**: orphan sweep (`Win32_Process` PID/PPID/StartTime) → ZERO python.exe orphans, :8000 free → fresh no-reload backend sole owner (startup probe + `GET /chat/skills` 200); a dev tenant with a custom skill (reuse 57.114 `acme-skills`, or add `release-notes` via the Skills admin tab)
- [ ] **Leg A (force-load determinism) PASS**: chat-v2 real_llm → `/` → pick `release-notes` (or type `/release-notes`) + a generic task → Send → Inspector shows `read_skill` **0×** yet the output follows the `release-notes` shape → screenshots (picker + answer + Inspector-no-read_skill)
- [ ] **Leg B (picker discoverability + filter) PASS**: `/` lists the tenant's effective skills (bundled `code-review`/`summarize` + overlay) · `/re` filters to `release-notes` · ↓/↑ highlight · Esc dismiss · Enter inserts `/{name} ` → screenshots (open + filtered)
- [ ] **Leg C (graceful + overlay-aware) PASS**: `/nonexistent <task>` → no force-load, chat answers normally (no error) · force-load a tenant-overridden `code-review` → the `## Active Skill` carries the OVERRIDDEN body → output follows the override → screenshots
- [ ] Each control driven (no dead control / no fixture / real LLM): the picker actually changes the output (force-load follows + `read_skill` 0×); Drive-Through-Acceptance (load+follow + graceful + overlay, AP-4 guard)
  - DoD: ALL 3 legs PASS + the picker drives the request

### 4.2 CHANGE-082 + design note 33
- [ ] **`claudedocs/4-changes/feature-changes/CHANGE-082-skills-slash-command.md`** (1-page, incl. the 3-leg drive-through)
- [ ] **Design note `33-skills-slash-command.md`** (8-point quality gate — the FIRST user-invoked force-load + the FIRST chat-user-facing skills endpoint + the greenfield composer picker; file:line anchors; decision: system-prompt injection vs forced-tool-call; verified ratio target ~95%)

### 4.3 Closeout
- [ ] retrospective.md Q1-Q7 + calibration (NEW `skills-slash-command-fullstack` 0.55 1st data point — record ratio vs ~9.5 hr commit; agent-delegated partial/parent-direct as executed) + progress.md final
- [ ] Navigators: CLAUDE.md Current-Sprint row + Last-Updated (minimal touch); MEMORY.md quality pointer + memory subfile `project_phase57_115_skills_slash_command.md`; next-phase-candidates — `AD-Skills-Slash-Command` CLOSED + remaining Skills ADs carried; sprint-workflow matrix NEW `skills-slash-command-fullstack` 0.55 1st data point; 17.md — decision (NO new contract vs a documented `force_load_skill` seam)
- [ ] **Anti-pattern self-check** (retro Q5/Q7): AP-4 (drive-through proves force-load changes output + `read_skill` 0×, not a cosmetic menu) · AP-2 (reachable from the composer→router→build_handler main flow) · AP-3 (helper in Cat 5 / endpoint+field in chat api / picker in chat_v2 — no scattering) · AP-6 (single skill, no speculative multi-skill list)
- [ ] PR (push + open on user authorization)
