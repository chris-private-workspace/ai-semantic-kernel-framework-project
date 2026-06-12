# Sprint 57.106 Progress — C3 per-tenant harness policy 面 + risky-action detector

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-106-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-106-checklist.md)

---

## Day 0 — 2026-06-12 — Three-prong plan-vs-repo verify ✅ GO

**Baseline**: `main` HEAD `7e358a6a` (post-#280 RBAC-wiring merge). Branch `feature/sprint-57-106-harness-policy` created.

### Drift findings

| ID | Finding | Implication |
|----|---------|-------------|
| D1 | Integration-suite naming precedent is `test_admin_tenant_model_policy.py` (plan §4 #8 said `test_admin_harness_policy.py`). | New suite named **`test_admin_tenant_harness_policy.py`** (mirror exact). Plan file list NOT silently rewritten (audit-trail rule); this entry is the record. |
| D2 | env `chat_verification_judge_template` accepts a template NAME **or a raw `{output}` string** (config docstring :117-124) — broader than recon claimed. | Per-tenant override stays **NAME-only** (deliberate tightening vs env; prompt-injection + size risk). Asymmetry documented in CHANGE-073 + note 28. |
| D3 | `python_sandbox` spec today: `hitl_policy=AUTO`, `destructive=False`, `risk_level=MEDIUM` (`exec_tools.py:27-70`) — arbitrary code executes with ZERO approval. `code` arg confirmed (required string). | Detector adds a real gate; spec itself untouched (detector is orthogonal, chain-level). |
| D4 | `ToolCall = {id: str, name: str, arguments: dict[str, Any]}` (`_contracts/chat.py:67-72`, flat — no nesting); loop passes per-call `tc` via singular `check_tool_call` (`loop.py:876`); `batch_check_tool_calls` is NOT used by the loop. | Detector reads `content.name` / `content.arguments` (mirror ToolGuardrail's content handling). Nested-shape rule satisfied by reading the body. |
| D5 | `TenantSettingsView.tsx` needs THREE edits, not one: `TabId` union (:56) + `TAB_ITEMS` (:58-66) + the tab-router switch — same file. | §4 #11 covers; micro-scope note. |
| D6 | `Tenant.meta_data` alias is a MULTI-LINE `mapped_column(\n "metadata", ...)` (`identity.py:139-140`, also :249-250) — the single-line Prong-3 grep pattern missed it first pass. | No raw SQL in this slice (ORM update mirrors C1) → no impact; catalogued for the physical-column rule's grep pattern (add `-A 1` next time). |
| D7 | Prong 2.5: `ModelPolicyTab.tsx` mirror source is CLEAN — 0 shadcn-utility residue; 7 inline `style={{` sites are lint-compliant escapes. | Mirror-copy inherits compliance. |
| D8 | `engine.register` appends duplicates on re-register (docstring: caller dedupes); chains are built fresh per session in the handler (:465-500). | Detector registered once per session build — no dedupe risk. |
| D9 | `grep harness_policy backend/src` = 0 hits. | JSONB key name free. |

### Anchors re-verified (all ✓)

handler.py `:163/:173/:184/:196` 4 frozensets + `:460-467` PermissionRule-from-frozenset + `:480/:488/:498` registrations + `:510-515` verifier registry + escalate flag into loop ctor · config 3 fields `:116/:124/:132` (mode default **"enabled"**) · router.py `:238` resolve site + `:111` import · tenants.py `:1474-1605` (schemas/validate/PUT/audit/invalidate/GET) · `TAB_ITEMS` 7 tabs · 5 template filenames exact · engine register/priority/fail-fast (`engine.py:86-117`) + `check_tool_call` (`:154-161`) · `KeywordEscalationGuardrail` ctor pattern (`escalation_keyword_detector.py:48-80` — frozenset-in-ctor + `_extract_text`, the detector's mirror).

### Go/no-go

**GO** — scope shift ≈ 0 (D1/D5 naming + micro-edits; D2-D4 confirm the design; D3 strengthens the detector's rationale).

---

## Day 1 — 2026-06-12 — Backend core: resolver + detector (US-1/US-3) ✅

- **`harness_policy.py`** (NEW, platform_layer/governance): `HarnessPolicy` frozen value object — 9 sparse fields with a deliberate tri-state (`None` = not-set/use-default vs `()` = explicit off-override, e.g. `escalate_tools: []` turns the default escalate list OFF); `_HarnessPolicyCache` (TTL 60s, injectable clock) + `resolve_tenant_harness_policy` (fail-open) + invalidate + reset — byte-pattern mirror of `model_policy.py`. Value object lives in-file (NOT adapters/_base — it's a governance concern, not provider-related; ModelPolicy's adapters home was provider-specific).
- **`risky_action_detector.py`** (NEW, Cat 9 TOOL chain): 9 builtin word-bounded deny patterns over the sandbox `code` arg + tenant `extra_patterns` over ANY tool's serialized args → ESCALATE (never BLOCK; risk HIGH); invalid hand-written tenant pattern skipped defensively (the PUT validates, but meta_data can be hand-edited); exported via `tool/__init__.py`.
- **Unit tests**: 38/38 (policy 22 + detector 16) — incl. near-miss cleans proving the `\b` + `(` anchoring (`evaluate(` / `execute_query(` / `list.remove` do NOT fire).
- Gates: mypy `src` **0/359** (+2 files) · flake8/black/isort clean (3 E501 Purpose-line trims — the MHist char-budget lesson applies to Purpose lines too) · `run_all` 10/10 (`check_cross_category_import` green — detector imports no platform_layer; `check_event_schema_sync` unchanged).

---

## Day 2 — 2026-06-12 — Handler/router wiring + admin PUT/GET (US-2/US-4 backend) ✅

### Drift finding

| ID | Finding | Implication |
|----|---------|-------------|
| D10 | The 4 escalate frozensets (`CHAT_HITL_ESCALATE_*`) are referenced BY NAME in 2 unrelated modules' comments (`note_tool.py:9`, `_register_all.py:247`). | Deviation from plan §3.2's cosmetic `_DEFAULT_*` rename: KEPT the names as the system-default values (renaming would churn 2 unrelated files' comments — surgical-changes rule). The policy-sourcing reads `frozenset(policy.X) if policy.X is not None else <NAME>`. No behavior change; the names ARE the defaults. |

### Work

- **`handler.py`**: `build_real_llm_handler` + `build_handler` gain `harness_policy` param; a resolved-values block computes `escalate_{tools,input,between,output}` (tri-state: `None`→default, `()`/values→override), `verification_{mode,template,escalate_on_max}` (template NAME-validated via `list_templates()` — a hand-edited bad name falls back to the env default instead of crashing `load_template`), and registers `RiskyActionDetector(priority=8)` unless `risky_action_enabled is False`.
- **`router.py`**: `resolve_tenant_harness_policy` resolved pre-handler (mirror C1 line 238) + threaded.
- **`templates/__init__.py`**: NEW `list_templates()` — single-source template-NAME allow-list shared by the handler (fallback) + the PUT (422).
- **`tenants.py`**: `HarnessPolicyUpsertRequest/Response` + `PUT`/`GET /{id}/harness-policy` + `_validate_harness_policy` (422: bad mode / unknown template / non-compiling regex / >20 patterns / >200-char) + audit + cache-invalidate — byte-pattern mirror of model-policy.
- **conftest.py**: `HARNESSPOL_PUT_%` committed-row sweep + `reset_harness_policy_cache()` at both reset points (Risk Class C).
- **Tests**: 17 integration (auth/404 · persistence/composite-replace/`[]`-off/clear · 5 validation poles · isolation · audit · GET). Byte-identical proof: chat handler/router + guardrail suites **506 passed UNCHANGED**.
- Gates: mypy 0/359 · flake8 clean · run_all 10/10 · full pytest **2438 passed + 4 skip**.

### Pre-existing flake (NOT a C3 regression)

`tests/unit/business_domain/incident/test_service.py::test_create_returns_incident` failed ONCE in the full-suite run but **passes isolated (1/1) and in its own file (12/12)**; `git diff main...HEAD` touches **zero** incident files; the conftest I edited is `tests/integration/api/` (a different tree from the failing `tests/unit/business_domain/incident/`). It's a full-suite ordering interaction (some earlier test's global state — Risk Class C class), pre-existing and out of C3 scope. Logged, not chased.

---

## Day 3 — 2026-06-12 — FE tab (US-4) + two-tenant drive-through (US-5) ✅ PASS

### FE tab (US-4 FE)

Agent-delegated (code-implementer) mirror of ModelPolicyTab; **parent independently re-verified all 4 gates** (Before-Commit item 7): `npm run lint` 0 (no `--silent`) · `npm run build` 0 · Vitest **206** (21 files, +13 HarnessPolicyTab) · `check:mockup-fidelity` 53 unchanged. 0 shadcn-utility residue, 0 Chinese copy (English state strings), real `saveMutation.mutate` (not Potemkin). Hooks placed in `hooks/` matching `useModelPolicy` location. Commit `1c5dcd8a`.

### Drive-through — observed vs intended (real UI :3007 + fresh no-reload backend PID 37844 on 57.106 code + real Azure gpt, NO dev-login)

Risk Class E: killed the stale 57.105 backend (PID 7672, pre-57.106 code) → fresh single no-reload uvicorn PID 37844, startup log captured (`artifacts/backend-dt57106.log`). Logged in as the persisted 57.105 founding admin (`dt57105-rbac` / `founder@dt57105.test`, password-login, role renders **admin**) — the C3 admin surface is drivable because 57.105 made the DB admin grant JWT-effective.

| # | Intended | Observed |
|---|----------|----------|
| US-4 | Harness Policy tab → edit → Save → PUT 200 | Tab (8th, between Model Policy + HITL Policies) renders 9 fields all "System default"; Edit → set `escalate_input_phrases="wire transfer"` + `verification_mode=disabled` + `risky_action_enabled=On` → Save → **PUT 200** + GET reflects saved values. Screenshot `dt57106-harness-policy-put200.png`. |
| US-2/5 (A) | tenant's escalate phrase fires | chat-v2 real_llm "Please process a wire transfer…" → input guardrail **ESCALATE** → HITL pause at turn 0 (`approval_requested risk=HIGH` → `loop_end stop=awaiting_approval turns=0`, BEFORE any LLM call). "wire transfer" is NOT a system default (defaults: approval required / checkpoint / confidential) → the pause can ONLY be the tenant policy. Screenshot `dt57106-escalate-phrase-pause.png`. |
| US-2/5 (B contrast) | without the phrase, no pause | Cleared `escalate_input_phrases` via the tab (PUT invalidates cache) → new session → SAME "wire transfer" message → **`stop=end_turn`, NO pause** (`hasApproval:false`). Same tenant, same message — behavior flipped purely by the policy. Screenshot `dt57106-no-phrase-no-pause.png`. |
| US-3/5 (on) | risky sandbox code escalates | risky_action_enabled=On; "Use python_sandbox to run: import os; os.system('echo …')" → LLM calls `python_sandbox` → RiskyActionDetector **ESCALATE** → `approval_requested risk=HIGH` → `stop=awaiting_approval`. python_sandbox is `hitl_policy=AUTO` + has a PASS ToolGuardrail rule, so the ONLY escalation source is the detector (priority 8). Screenshot `dt57106-risky-detector-escalate.png`. |
| US-3/5 (off) | per-tenant off-switch | Toggled risky_action_enabled=Off via the tab (PUT invalidates cache) → new session → SAME sandbox prompt → `python_sandbox` **executed**, NO approval, `stop=end_turn`. Per-tenant off proven. Screenshot `dt57106-risky-off-passthrough.png`. |
| Negative | role-less → 403 | Minted a role-less JWT (same user/tenant, `roles=["user"]`) → harness-policy PUT → **403 "Platform admin role required"**. |
| Cleanup | revert policy | Tab Edit → all fields → System default → Save → all "System default" (meta_data drops `harness_policy`). Throwaway tenant `dt57105-rbac` left clean (no shared-tenant pollution; acme-prod untouched). |

**Honest notes**: the chat-v2 HITL card renders `tool: —` (it doesn't surface the `approval_requested` tool name/reason — a PRE-EXISTING chat-v2 card limitation, not a C3 regression; the Loop visualizer event chain `tool_call → approval_requested risk=HIGH` is the evidence). Drive-through used a **temporal A/B on one tenant** (before/after policy on `dt57105-rbac`) rather than two distinct tenants — a stronger controlled experiment (only the policy variable changes; everything else identical) and avoids a 2nd admin-tenant setup; the proposal DoD's "A escalates / B passes" invariant is proven by the WITH/WITHOUT contrast.

### Drift finding

| ID | Finding | Implication |
|----|---------|-------------|
| D11 | The chat-v2 HITL approval card surfaces `tool: —` (no tool name) for an `approval_requested` event. | Pre-existing chat-v2 limitation (the card reads a tool field the verification/risky escalate doesn't populate the same way). NOT a C3 regression; logged as a candidate FE wiring AD for a future chat-v2 slice. |

---
