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
  - [x] **D-fe-tree (Prong-2.5)** 🟢 (done Day-3 start): `InputBar.tsx` + composer chrome use mockup classes (`.composer`/`.composer-input`/`.btn primary`) + inline mockup-token styles (`var(--border)`/`var(--bg)`/`var(--primary)`) — NO shadcn-utility residue to inherit; `SkillSlashMenu` net-new (mockup tokens + file-level eslint-disable, InputBar precedent)
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

### 3.1 Service + hook + types (US-5) ✅
- [x] **`features/chat_v2/services/chatService.ts`** (EDIT): `ChatRequestBody` += `force_load_skill?: string` (snake_case); `ChatSkill`/`ChatSkillsResponse` types; `fetchChatSkills(signal?)` (`GET /api/v1/chat/skills`, mirrors `listSessions`); `streamChat` forwards `force_load_skill` (threaded from the hook)
- [x] **`features/chat_v2/hooks/useChatSkills.ts`** (NEW): `useQuery` (`["chat-v2","skills"]`, `fetchChatSkills`, `enabled` param, `staleTime` 60s) — gated to real_llm by the InputBar
- [x] **`features/chat_v2/hooks/useLoopEventStream.ts`** (EDIT): `send(message, opts?: {forceLoadSkill?})` → threads `opts.forceLoadSkill` into the `streamChat` body (`force_load_skill`); existing single-arg callers stay valid

### 3.2 `SkillSlashMenu` + InputBar wiring (US-4) ✅
- [x] **`features/chat_v2/components/SkillSlashMenu.tsx`** (NEW): presentational filtered dropdown anchored above the composer (`/name` + muted description; `activeIndex` highlight via `aria-selected`; "No matching skills" empty row); mockup tokens (`var(--bg-2)`/`var(--border)`/`var(--primary)`/`var(--shadow)` — NOT a colour literal) + file-level eslint-disable (InputBar precedent); `data-testid` per row; `tabIndex=-1` a11y (keyboard lives on the textarea)
- [x] **`features/chat_v2/components/InputBar.tsx`** (EDIT): `slashEnabled = !isRunning && mode==="real_llm"` (no dead control in echo/mid-run); `slashActive` = leading `/` no-space; filter + `showMenu`; keyboard (menu open: ↓/↑/Enter-select→`/{name} `/Esc-dismiss; closed: Enter send); `matchForceLoad` parses leading `/skill` (KNOWN skill only) → `forceLoadSkill` + strip; `send(msg)` or `send(msg, {forceLoadSkill})`; `freshSendDisabled = showMenu || empty-after-strip`
  - DoD: ✅ `npm run build` clean; menu opens on `/`, select force-loads
- [x] **`features/chat_v2/components/Composer.tsx`** — N/A: `InputBar` IS the sole production send path (Composer.tsx is disabled scaffolding); menu anchored to `.composer-inner` (`position: relative` inline)

### 3.3 Vitest + FE gates ✅
- [x] **`tests/unit/chat_v2/SkillSlashMenu.test.tsx`** (NEW ×4): renders `/name`+description · `aria-selected` on activeIndex · click → `onSelect` · empty-state row
- [x] **`tests/unit/chat_v2/InputBar.slash.test.tsx`** (NEW ×8): `/` opens menu · prefix filter · Enter selects (`/name `, no send) · ArrowDown+Enter · Escape dismiss · leading `/skill` → `send("task", {forceLoadSkill})` + strip · unmatched `/foo` plain · non-leading `/` plain. **+ existing `InputBar.test.tsx` (3) given a `useChatSkills` mock** (it now imports the TanStack hook; mock returns `{data:[]}` → no menu; the 57.101 inject coverage stays green)
- [x] FE gates: `npm run lint` (NO `--silent`) **0 error** (fixed a11y `interactive-supports-focus` → `tabIndex=-1`) · `npm run build` clean · `npm run test` Vitest **863 (+12 vs 851)** · `npm run check:mockup-fidelity` **51** holds (fixed: shadow `oklch` literal → `var(--shadow)` token)
  - Verify: ✅ `cd frontend && npm run lint && npm run build && npm run test && npm run check:mockup-fidelity`

---

## Day 4 — Drive-through (US-6) + CHANGE-082 + design note 33 + closeout

### 4.1 Drive-through (real chat-v2 :3007 + fresh single-process backend + real Azure LLM; Risk Class E clean restart) ✅
- [x] **Clean restart + probe**: killed stale PID 38756 (57.114 code) + transient PID 6716 (CWD `.env` miss → no Azure); ZERO python orphans; restarted from **repo-root** with `--env-file .env` + `PYTHONPATH=backend/src` (env_file CWD-relative, `.env` at root) → startup complete + Azure loaded; `GET /api/v1/chat/skills` **200** (name+desc only, no instructions). Reused dev tenant `acme-skills` (jamie@acme.com, cookie) with persisted overlay `release-notes`
- [x] **Leg A (force-load determinism) PASS**: `/release-notes` picker→Enter→task→Send → user turn shows the STRIPPED message → output followed `## Summary/## Highlights/## Upgrade steps` EXACTLY → Loop trace `llm_response: 0 tool calls` (**`read_skill` 0×**, force-injected into `## Active Skill`) → verification 0.98. `legA-forceload-output-follows-readskill-0x.png`
- [x] **Leg B (picker discoverability + filter) PASS**: `/` lists all 3 (`/code-review`/`/summarize`/`/release-notes`) · `/re` filtered (summarize dropped; substring `includes`) · Enter inserts `/release-notes ` + closes. `legB-picker-open-all-skills.png`
- [x] **Leg C (graceful unknown) PASS**: `/nonexistent reply with exactly: OK` → NO menu (empty filter, no dead control) → user turn shows the LITERAL token (unmatched = plain text) → agent answered "OK" normally, verification 0.99, no error. `legC-unknown-token-graceful-plain-text.png`. (Overlay-aware force-load already proven by Leg A — `release-notes` IS acme's overlay skill.)
- [x] Each control driven (no dead control / no fixture / real LLM): the picker DRIVES the request (output changes + `read_skill` 0×, not cosmetic); Drive-Through-Acceptance + AP-4 guard satisfied
  - DoD: ✅ ALL 3 legs PASS + the picker drives the request

### 4.2 CHANGE-082 + design note 33 ✅
- [x] **`claudedocs/4-changes/feature-changes/CHANGE-082-skills-slash-command.md`** (1-page, incl. the 3-leg drive-through)
- [x] **Design note `33-skills-slash-command.md`** (8-point quality gate ALL pass — decision matrix A/B/C system-prompt-injection vs forced-tool-call; file:line anchors; verified ratio ~96%; 17.md decision: NO new contract)

### 4.3 Closeout ✅
- [x] retrospective.md Q1-Q7 + calibration (NEW `skills-slash-command-fullstack` 0.55 1st data point — ratio ~1.0 IN band → KEEP; **parent-direct** agent_factor 1.0, NOT the planned partial) + progress.md final
- [x] Navigators: CLAUDE.md Current-Sprint row + Last-Updated (minimal touch); MEMORY.md quality pointer + memory subfile `project_phase57_115_skills_slash_command.md`; next-phase-candidates — `AD-Skills-Slash-Command` CLOSED + 57.115 carryover block + remaining Skills ADs carried; sprint-workflow matrix NEW `skills-slash-command-fullstack` 0.55; 17.md — **decision: NO new contract** (additive ChatRequest field + intra-Cat-5 helper + api endpoint; mirrors 57.113/114 — noted in design note §4)
- [x] **Anti-pattern self-check** (retro Q5/Q7): AP-4 (drive-through proves force-load changes output + `read_skill` 0×) · AP-2 (composer→router→build_handler main flow) · AP-3 (helper Cat 5 / endpoint+field chat api / picker chat_v2) · AP-6 (single skill)
- [ ] PR (push + open on user authorization)
