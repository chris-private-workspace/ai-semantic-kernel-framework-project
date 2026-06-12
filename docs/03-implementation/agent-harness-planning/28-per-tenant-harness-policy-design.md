# 28 — Per-tenant Harness Policy + Risky-Action Detector (Config Tiering, C3)

**Purpose**: Extract the verified invariants of the per-tenant harness-policy slice (Sprint 57.106) — the chat handler's hardcoded Cat 9/10 governance knobs become tenant-governable, plus a new Cat 9 `RiskyActionDetector` (the server-side equivalent of Claude Code's bashSecurity screen).
**Category / Scope**: platform_layer.governance + 範疇 9 / harness-deepening Workflow C slice C3 / Phase 57.106
**Created**: 2026-06-12
**Status**: Active (extracted from shipped + drive-through-proven implementation)
**Closes**: harness-deepening proposal §3.4 C3 (escalate/verification policy 面 + risky-action detector)

> **Modification History**
> - 2026-06-12: Initial creation — extracted from Sprint 57.106 shipped impl

---

## 1. Spike Summary — "C3: make the chat handler's hardcoded governance knobs tenant-governable + add a risky-action screen"

A tenant governs its own escalate phrases (3 guardrail chains), escalate-tool list, and
verification mode/template/escalate-on-max via `tenant.meta_data["harness_policy"]` (sparse
JSONB, mirror of C1's model-policy). A new `RiskyActionDetector` (Cat 9 TOOL chain) screens
`python_sandbox` code + tenant regex patterns into the existing HITL approval flow, per-tenant
switchable. Shipped: `HarnessPolicy` value object + TTL resolver
(`platform_layer/governance/harness_policy.py`), the detector
(`agent_harness/guardrails/tool/risky_action_detector.py:78` `RiskyActionDetector`), the
handler wiring (`api/v1/chat/handler.py` resolved-values block), admin
`PUT`/`GET /api/v1/admin/tenants/{id}/harness-policy` (`api/v1/admin/tenants.py`), and a
tenant-settings "Harness Policy" tab.

## 2. Decision Matrix

| # | Decision | Options | Chosen | Why (rejected the rest) |
|---|----------|---------|--------|------------------------|
| D1 | Storage | (a) `meta_data["harness_policy"]` JSONB / (b) dedicated `tenant_policies` table / (c) feature_flags registry | **(a)** | C1 precedent; zero migration; `append_audit` reuse. (b) = migration + larger surface (evaluated §5, not built); (c) is per-key cross-tenant — wrong shape for per-tenant policy. |
| D2 | Sparse tri-state | (a) `None`-only / (b) `None` vs `()` distinct | **(b)** | `escalate_tools=[]` is a real "off" override (turn the default escalate list OFF), distinct from omitted=use-default. `HarnessPolicy` tuple fields + `risky_action_enabled` tri-state encode this. |
| D3 | Detector action | (a) BLOCK / (b) ESCALATE | **(b) ESCALATE** | BLOCK is a silent denial the user can't appeal; ESCALATE routes into the existing Cat 9 HITL approval (a human decides). `risky_action_detector.py:127` returns `GuardrailAction.ESCALATE`. |
| D4 | Detector off-switch | (a) registered-but-noop / (b) not-registered | **(b)** | Zero-cost off: `handler.py` registers the detector only when `policy.risky_action_enabled is not False`. |
| D5 | Verification template override | (a) raw template upload / (b) NAME from shipped set | **(b) NAME-only** | Raw upload = prompt-injection + unbounded-size risk. `list_templates()` (`verification/templates/__init__.py`) is the single-source allow-list; PUT rejects unknown name 422; handler falls back to env default on a hand-edited bad name (no `load_template` crash). |
| D6 | Frozenset rename | (a) `_DEFAULT_*` rename / (b) keep names as defaults | **(b) keep** | The 4 `CHAT_HITL_ESCALATE_*` frozensets are referenced BY NAME in `note_tool.py:9` + `_register_all.py:247` comments; renaming churns unrelated files (surgical-changes). They ARE the defaults; the resolved-values block reads `frozenset(policy.X) if policy.X is not None else <NAME>`. |
| D7 | Resolve boundary | (a) per-request DB / (b) TTL cache | **(b)** | Hot-path cost — `_HarnessPolicyCache` (TTL 60s, injectable clock) mirrors `_ModelPolicyCache`; the admin PUT calls `invalidate_tenant_harness_policy`. |

## 3. Verified Invariants (drive-through + gate proven)

- **No-policy tenant byte-identical**: `harness_policy or HarnessPolicy()` → every field falls
  back to the module default; chat handler/router + guardrail suites 506 passed UNCHANGED.
  Verify: `pytest tests/unit/api/v1/chat/test_handler.py tests/unit/api/v1/chat/test_router.py tests/unit/agent_harness/guardrails -q`.
- **Escalate phrase is tenant-governed**: setting `escalate_input_phrases=["wire transfer"]`
  makes a real chat "…wire transfer…" ESCALATE at turn 0 (`loop_end stop=awaiting_approval
  turns=0`); clearing it (PUT invalidates cache) → same message `stop=end_turn`, no pause.
  "wire transfer" is provably not a default (defaults: approval required / checkpoint /
  confidential). Drive-through screenshots `dt57106-escalate-phrase-pause.png` +
  `dt57106-no-phrase-no-pause.png`.
- **RiskyActionDetector ESCALATES sandbox code + per-tenant off works**: a real
  `python_sandbox` call with `os.system(...)` ESCALATES with `risky_action_enabled=On`
  (`dt57106-risky-detector-escalate.png`) and executes through with `=Off`
  (`dt57106-risky-off-passthrough.png`). python_sandbox is `hitl_policy=AUTO` + has a PASS
  ToolGuardrail rule, so the detector (priority 8) is the only escalation source. Verify
  units: `pytest tests/unit/agent_harness/guardrails/test_risky_action_detector.py -q` (16).
- **Admin write governance**: `PUT /{id}/harness-policy` validates (422 on bad mode / unknown
  template / non-compiling regex / >20 patterns / >200-char), writes sparse JSONB, audits
  (`tenant_harness_policy_upsert`), invalidates the cache. `require_admin_platform_role` gate
  → role-less JWT 403 (drive-through). Verify: `pytest
  tests/integration/api/test_admin_tenant_harness_policy.py -q` (17).
- **Detector near-miss safety**: `\b` + `(` anchoring means `evaluate(` / `execute_query(` /
  `list.remove` do NOT fire (only the real builtins do). Verify in
  `test_risky_action_detector.py::test_clean_code_passes`.

## 4. Cross-Category Contracts (→ 17.md single-source)

- `HarnessPolicy` is a `platform_layer.governance` value object — **N/A to 17.md** (the 17.md
  registry is the 11+1 agent-harness categories; identity/governance platform surfaces are
  out, per the 57.84-87 + 57.105 D12 precedent). Contract lives in this note + the module
  docstring + CHANGE-073.
- `RiskyActionDetector` is a Cat 9 `Guardrail` — it rides the EXISTING `Guardrail` ABC row in
  17.md §2.1 (no new ABC). It emits the EXISTING `GuardrailTriggered` event (no new event
  type; `check_event_schema_sync` count unchanged).

## 5. Open Invariants (NOT verified this spike — deferred)

- **`AD-HITL-Policy-ReadSide-Potemkin-Phase58`** (NEW) — `DBHITLPolicyStore.get_policy()`
  (Sprint 57.54 write-side) is NOT consumed at tool execution; `ToolGuardrail` Stage 3
  hardcodes `requires_approval` (does not read `auto_approve_max_risk` /
  `require_approval_min_risk`). Risk-threshold semantics = own slice.
- **`AD-ChatV2-HITL-Card-Tool-Name`** (NEW) — the chat-v2 HITL card renders `tool: —` for an
  `approval_requested` event (the tool name/reason isn't wired to the card). FE wiring gap.
- **Dedicated `tenant_policies` table** — evaluated NOT built: the JSONB-on-meta_data shape is
  schema-less; when the policy 面 matures (typed + RLS + versioning) it graduates to a table
  (the `rate_limit_configs` 0019 precedent). Trigger: when ≥2 more policy concerns land on
  meta_data OR a typed-query need arises.
- capability_matrix per-tenant role/scope/max_calls override; raw verification-template upload;
  per-tenant injection policy (B-family); C2 compaction cheap tier (next C slice).

## 6. Rollback / Fallback

Low-risk, additive. To revert: drop the `harness_policy` param from `build_real_llm_handler` +
`build_handler` (the resolved-values block falls back to the frozenset defaults), remove the
detector registration + the `RiskyActionDetector` file + `tool/__init__.py` export, remove the
router `resolve_tenant_harness_policy` call, delete the admin PUT/GET + the FE tab. No
migration / no schema change → no DB rollback. Any stored `meta_data["harness_policy"]` becomes
inert (ignored by the resolver if the resolver is removed). Est. < 30 min.

## 7. References

- `sprint-57-106-plan.md` / `-checklist.md` — sprint contract
- `27-per-tenant-model-policy-design.md` — the C1 pattern this mirrors
- `platform_layer/billing/model_policy.py` — the byte-pattern-mirror resolver
- `claudedocs/1-planning/harness-deepening-proposal-20260610.md` §3.4 — C3 scope
- `CHANGE-073-per-tenant-harness-policy.md` — change record

## 8. 8-Point Quality Gate (self-review)

1. ✅ Section header maps to the spike (C3 governance knobs + detector)
2. ✅ Each claim has file:line (`risky_action_detector.py:78/:127`, `handler.py` block, etc.)
3. ✅ Decision matrix with options + rejected reasons (D1-D7)
4. ✅ Verification commands (3 pytest invocations + drive-through screenshots)
5. ✅ Test fixtures referenced (`test_harness_policy.py` / `test_risky_action_detector.py` / `test_admin_tenant_harness_policy.py`)
6. ✅ Open invariants explicitly separated (§5; AD-HITL-ReadSide / table / card-tool-name)
7. ✅ Rollback path (§6, < 30 min, additive)
8. ✅ 17.md cross-ref (§4 — N/A by precedent for the value object; detector rides existing Guardrail ABC + GuardrailTriggered)
