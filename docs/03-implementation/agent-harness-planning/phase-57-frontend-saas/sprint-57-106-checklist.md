# Sprint 57.106 — Checklist (C3 per-tenant harness policy 面 + risky-action detector: `meta_data["harness_policy"]` + TTL resolver + handler wiring + `RiskyActionDetector` + admin PUT/GET + "Harness Policy" tab → two-tenant drive-through)

[Plan](./sprint-57-106-plan.md)

**Status**: 🚧 Day 0 ✅ GO — Day 1 next
**Branch**: `feature/sprint-57-106-harness-policy`

---

## Day 0 — Plan-vs-Repo Verify + Branch ✅

### 0.1 Three-prong Day-0 verify (against `main` HEAD `7e358a6a`) — DONE, catalogued in progress.md D1-D9
- [x] **Prong 1 — path verify**: NEW files all Glob-0; EDIT files Glob-1; suites pinned — integration naming precedent `test_admin_tenant_model_policy.py` → mine `test_admin_tenant_harness_policy.py` (D1); unit dirs `tests/unit/platform_layer/governance/` + `tests/unit/agent_harness/guardrails/` exist
- [x] **Prong 2 — content verify**: ALL §0 STALE anchors ✓ — handler 4 frozensets `:163/:173/:184/:196` + registrations `:480/:488/:498` + verifier wiring `:510-515` + escalate flag; config 3 fields (mode default "enabled"); router `:238`; tenants.py `:1474-1605`; `TAB_ITEMS` 7; `exec_tools.py:27-70` `code` arg + AUTO/MEDIUM (D3); engine register/priority/fail-fast + `check_tool_call(content)` + loop `:876` singular call (D4); 5 templates exact; **`ToolCall` BODY read**: flat `{id, name, arguments: dict}` (D4); `harness_policy` grep-0 (D9); env judge_template also takes raw string → per-tenant NAME-only is deliberate tightening (D2)
- [x] **Prong 2.5 — FE tree audit**: ModelPolicyTab mirror source CLEAN (0 shadcn residue; 7 lint-compliant inline-style escapes — D7); `TabId` union + tab-router switch need edits too (D5)
- [x] **Prong 3 — schema verify**: no migration; `meta_data` alias confirmed MULTI-LINE `mapped_column("metadata", ...)` `identity.py:139-140/:249-250` (D6 — single-line grep misses; no raw SQL in scope)
- [x] **Catalog drift** in progress.md Day 0 (D1-D9 + implications)
- [x] **Go/no-go**: GO — scope shift ≈ 0

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-106-harness-policy` (from `main` `7e358a6a`)

---

## Day 1 — Backend core: resolver + detector (US-1 / US-3) ✅

### 1.1 HarnessPolicy value object + resolver (US-1)
- [x] **`platform_layer/governance/harness_policy.py`**: frozen `HarnessPolicy` (9 sparse fields; tuple `()` = explicit-off vs `None` = not-set tri-state) + `_HarnessPolicyCache` (TTL 60s, injectable clock) + `resolve_tenant_harness_policy` (fail-open) + `invalidate_tenant_harness_policy` + `reset_harness_policy_cache`
  - Mirror `model_policy.py` byte-pattern ✓; value object lives in-file (not adapters — non-provider concern)
  - DoD: mypy 0/359 ✓; unit tests green ✓
- [x] **Risk Class C guard**: autouse `_reset_cache` fixture in the unit suite (integration conftest extension lands with Day 2 suite)

### 1.2 RiskyActionDetector (US-3)
- [x] **`agent_harness/guardrails/tool/risky_action_detector.py`**: `guardrail_type=TOOL`; 9-pattern builtin deny-list (`os.system`/`os.remove|unlink|rmdir|removedirs`/`subprocess`/`shutil.rmtree`/`eval(`/`exec(`/`__import__`/`socket`/`ctypes`) over sandbox `code` + any-tool `extra_patterns` over serialized args → ESCALATE (risk HIGH); invalid tenant pattern skipped defensively; exported via `tool/__init__.py`
  - DoD: existing `GuardrailTriggered` path only ✓; `check_cross_category_import` green (no platform_layer import) ✓
- [x] (handler-level `enabled=False` → not-registered lands with Day 2 wiring)

### 1.3 Unit tests
- [x] **`test_harness_policy.py`** (22): TTL hit/expiry/invalidate · resolver fail-open/cache/invalidate-reread · from_dict all types / wrong-types-not-set / `[]`-off-override / round-trip
- [x] **`test_risky_action_detector.py`** (16): each builtin pattern hit (9) + near-miss cleans (`evaluate(`/`execute_query(`/`list.remove`) + extra-pattern any-tool hit/clean + invalid-pattern skip + non-tool-content/missing-code defensive
  - DoD: 38/38 green ✓; flake8 clean ✓; run_all 10/10 ✓

---

## Day 2 — Wiring + admin write/read (US-2 / US-4 backend) ✅

### 2.1 Handler/router wiring (US-2)
- [x] **`handler.py`**: 4 frozensets KEPT as the system defaults (deviation from plan §3.2 cosmetic `_DEFAULT_*` rename — they're referenced by name in note_tool.py + _register_all.py comments; renaming churns unrelated files per surgical-changes; recorded D10); `build_real_llm_handler(harness_policy=None)` + `build_handler` forward; phrases/tools sourced `frozenset(policy.X) if not None else DEFAULT`; verification mode/template(NAME-validated via `list_templates()`)/escalate_on_max sourced policy-or-settings; `RiskyActionDetector` registered priority 8 when `risky_action_enabled is not False`
  - DoD: NO-policy tenant byte-identical — chat handler/router + guardrail suites **506 passed** UNCHANGED ✓
- [x] **`router.py`**: `resolve_tenant_harness_policy` pre-handler (mirror C1 `:238`) + thread through build_handler; echo path untouched
- [x] **`templates/__init__.py`**: `list_templates()` single-source allow-list (shared by handler validation + PUT 422)

### 2.2 Admin PUT/GET (US-4 backend)
- [x] **`tenants.py`**: `HarnessPolicyUpsertRequest/Response` (`extra='forbid'`) + `PUT`/`GET /{tenant_id}/harness-policy` — composite-replace + `[]`-off-override kept; 422 poles (unknown template / non-compiling regex / >20 patterns / >200-char / bad mode); `append_audit("tenant_harness_policy_upsert")` + `invalidate_tenant_harness_policy`; `require_admin_platform_role`
- [x] **`test_admin_tenant_harness_policy.py`** (17, mirror model-policy + D1 naming): auth/404 · create/composite-replace/`[]`-off/clear · 5 validation poles · isolation 鐵律 · audit chain · GET round-trip
- [x] **conftest.py**: `HARNESSPOL_PUT_%` sweep + `reset_harness_policy_cache()` (Risk Class C)
  - DoD: 17/17 green; mypy 0/359; run_all 10/10; full pytest **2438 passed + 4 skip** (1 pre-existing incident ordering-flake, passes isolated + 0 incident files in branch diff — NOT a C3 regression)

---

## Day 3 — FE tab + full gates + drive-through (US-4 FE / US-5) + CHANGE-073 + note 28

### 3.1 FE tab (US-4) ✅
- [x] **`HarnessPolicyTab.tsx`** mirror ModelPolicyTab (view/edit/Save/Cancel + 422 inline `harness-policy-save-error`); 5 list fields comma/newline-separated; verification_mode + template + 2 bools as tri-state selects (""=System default); `hooks/useHarnessPolicy.ts` + `useHarnessPolicySave.ts` (mirror useModelPolicy location); service get/put + camel↔snake mappers; `types.ts` unions; `TAB_ITEMS` 7→8 (4 wiring points)
  - Agent-delegated (code-implementer) → **parent independently re-verified all 4 gates** (Before-Commit item 7): 0 shadcn residue · 0 Chinese copy (English state strings) · real save mutation (not Potemkin)
- [x] FE Vitest **206 passed** (21 files, +13 HarnessPolicyTab); `npm run lint` exit 0 (no `--silent`) · `npm run build` exit 0 · `npm run check:mockup-fidelity` 53 unchanged

### 3.2 Full gate sweep ✅
- [x] `black/isort/flake8` clean · `mypy src` 0/359 · `python scripts/lint/run_all.py` 10/10 (event count UNCHANGED)
- [x] full `pytest` 2438 passed + 4 skip (0 deletions; 1 pre-existing incident ordering-flake, passes isolated) · FE Vitest 206 · mockup-fidelity 53
- [x] `loop.py` / DB / migration / wire schema diff = 0 (none touched)

### 3.3 Drive-through (US-5 — NO dev-login) — ✅ PASS
- [x] Clean restart (Risk Class E): killed stale 57.105 backend PID 7672 (pre-57.106 code) → fresh no-reload uvicorn PID 37844 sole :8000 + startup log; Vite :3007 serves source live
- [x] US-4: Harness Policy tab (founder admin, password-login, role=admin) → set `escalate_input_phrases="wire transfer"` + `verification_mode=disabled` + `risky_action_enabled=On` → **PUT 200** + GET reflects
- [x] US-2/5 (A): chat "wire transfer" → input ESCALATE → HITL pause `stop=awaiting_approval turns=0`; (B contrast) cleared phrase → same message `stop=end_turn` no pause (cache invalidation) — same-tenant temporal A/B (stronger controlled experiment; noted)
- [x] US-3/5: python_sandbox `os.system` → **ESCALATE** with risky=On; toggled risky=Off → same payload **執行直通** (per-tenant off + cache invalidation proven)
- [x] Screenshots (`artifacts/dt57106-{harness-policy-put200,escalate-phrase-pause,no-phrase-no-pause,risky-detector-escalate,risky-off-passthrough}.png`) + observed-vs-intended table in progress.md; cleanup: policy cleared (all System default)
- [x] (negative) role-less JWT (same user/tenant) → harness-policy PUT **403 "Platform admin role required"**

### 3.4 CHANGE-073 + docs ✅
- [x] `CHANGE-073-per-tenant-harness-policy.md`
- [x] design note **28-per-tenant-harness-policy-design.md** (8-point gate; incl. 專表畢業 evaluation ¶ §5 + detector deny-list rationale §2 D3/D5)
- [x] 17.md decision recorded (in note 28 §4): `HarnessPolicy` platform_layer → **N/A per 57.105 D12 precedent**; `RiskyActionDetector` rides the EXISTING Guardrail ABC row + emits EXISTING `GuardrailTriggered` (no new ABC, no new event — confirmed `check_event_schema_sync` count unchanged)

---

## Day 4 — Closeout

### 4.1 Closeout
- [ ] progress.md Day 0-3 complete (drift catalog + drive-through table)
- [ ] retrospective.md Q1-Q7 (Q2: `config-tiering-model-policy-spike` 0.60 2nd-validation ratio → window)
- [ ] CLAUDE.md Current Sprint + Last Updated (lean) · MEMORY.md pointer + `project_phase57_106_harness_policy.md` subfile (auto-memory dir)
- [ ] next-phase-candidates.md: C3 ✅ + 🆕 `AD-HITL-Policy-ReadSide-Potemkin-Phase58` + next slice **B3** per interleave
- [ ] sprint-workflow.md calibration row update (`config-tiering-model-policy-spike` 2 pt)
- [ ] all checklist items `[x]` or annotated 🚧 (never delete unchecked)
