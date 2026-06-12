# CHANGE-073: Per-tenant harness policy + risky-action detector (C3)

**Date**: 2026-06-12
**Sprint**: 57.106
**Scope**: platform_layer.governance + 範疇 9 (Guardrails) × api/v1/chat × api/v1/admin × frontend
**Slice**: harness-deepening Workflow C slice C3

## Problem

The chat handler hardcoded its governance knobs — escalate keyword phrases for 3
guardrail chains (`{"approval required"}` / `{"checkpoint"}` / `{"confidential"}`),
the escalate-tool list (`{"echo_tool"}`), and the verification mode / judge template /
escalate-on-max (env settings) — so every tenant got identical behavior. Two
self-describing "deferred per-tenant policy" comments (`handler.py:160`, `:171-172`)
flagged this. Separately, `python_sandbox` executes arbitrary code with
`hitl_policy=AUTO` (zero approval) — no server-side equivalent of Claude Code's
bashSecurity screen existed.

## Design (one sparse JSONB key; detector ESCALATEs, never BLOCKs)

Mirror the C1 (Sprint 57.104) config-tiering pattern: `tenant.meta_data["harness_policy"]`
sparse JSONB + a TTL-cached resolver + a pricing-style admin PUT/GET + a tenant-settings
tab. Each policy field falls back to the system default when unset (a tenant with no
policy is byte-identical to pre-57.106).

- **`HarnessPolicy` value object** (`platform_layer/governance/harness_policy.py`): 9 sparse
  fields with a deliberate tri-state — `None` = not-set (use default) vs `()`/value =
  explicit override (e.g. `escalate_tools=[]` turns the default escalate list OFF).
- **`resolve_tenant_harness_policy`** (TTL 60s, injectable clock, fail-open) — resolved in
  the router pre-handler (mirror `resolve_tenant_model_policy`) + threaded through
  `build_handler` → `build_real_llm_handler`.
- **`RiskyActionDetector`** (`agent_harness/guardrails/tool/risky_action_detector.py`, Cat 9
  TOOL chain, priority 8): screens `python_sandbox` `code` against a 9-pattern word-bounded
  builtin deny-list (`os.system`/`os.remove|unlink|rmdir|removedirs`/`subprocess`/
  `shutil.rmtree`/`eval(`/`exec(`/`__import__`/`socket`/`ctypes`) + tenant `extra_patterns`
  over any tool's serialized args → **ESCALATE** (never BLOCK — routes into the existing
  Cat 9 HITL approval flow; a human decides). Default ON; `risky_action_enabled=False` →
  not registered (zero-cost off).
- **Verification template override is NAME-only**: must be one of the 5 shipped
  `verification/templates/*.txt` (single-source `list_templates()`); raw-template upload is
  rejected (prompt-injection + unbounded-size risk). A hand-edited bad name falls back to
  the env default rather than crashing `load_template`.

**Rejected**: per-request DB read (hot-path cost — TTL cache per C1); folding the
`hitl_policies` read-side Potemkin fix (own AD — see Open); per-tenant capability_matrix
role/scope/max_calls overrides (only the escalate dimension is in scope); a dedicated
`tenant_policies` table (evaluated in design note 28, not built); `_DEFAULT_*` rename of the
4 frozensets (they're referenced by name in 2 unrelated modules' comments — surgical-changes
rule; they ARE the defaults).

## Solution

| File | Change |
|------|--------|
| `platform_layer/governance/harness_policy.py` | NEW — value object + TTL resolver + invalidate + reset |
| `agent_harness/guardrails/tool/risky_action_detector.py` | NEW — Cat 9 TOOL guardrail (+ `tool/__init__.py` export) |
| `agent_harness/verification/templates/__init__.py` | + `list_templates()` single-source allow-list |
| `api/v1/chat/handler.py` | `harness_policy` param + resolved-values block + detector registration; frozensets KEPT as defaults |
| `api/v1/chat/router.py` | resolve + thread (1 call site, mirror C1 line 238) |
| `api/v1/admin/tenants.py` | `PUT`/`GET /{id}/harness-policy` + `_validate_harness_policy` (422 mode/template/regex/caps) + audit + invalidate |
| `frontend/.../tabs/HarnessPolicyTab.tsx` + hooks + service + types + `TAB_ITEMS` 7→8 | NEW tab (mirror ModelPolicyTab) |
| `tests/integration/api/conftest.py` | `HARNESSPOL_PUT_%` sweep + `reset_harness_policy_cache` (Risk Class C) |

`loop.py` / DB models / migrations / `event_wire_schema` UNTOUCHED.

## Verification

- **Unit**: `test_harness_policy.py` 22 (value-object tri-state + TTL + resolver fail-open) +
  `test_risky_action_detector.py` 16 (each builtin pattern + near-miss cleans + extra-pattern
  + disabled + defensive).
- **Integration**: `test_admin_tenant_harness_policy.py` 17 (auth/404 · create/composite-
  replace/`[]`-off/clear · 5 validation poles · isolation 鐵律 · audit · GET).
- **Byte-identical**: chat handler/router + guardrail suites 506 passed UNCHANGED (no-policy
  tenant). Gates: mypy 0/359 · run_all 10/10 (event count unchanged) · full pytest 2438+4skip
  (1 pre-existing incident ordering-flake, passes isolated) · FE Vitest 206 · mockup-fidelity 53.
- **Drive-through PASS** (real UI + fresh no-reload backend + real LLM, NO dev-login):
  Harness Policy tab PUT 200 → escalate phrase "wire transfer" pauses (turn-0 input
  ESCALATE) WITH the policy / no pause WITHOUT (cache invalidation) → risky `os.system`
  sandbox call ESCALATES with risky=On / passes through with risky=Off → role-less JWT 403 →
  policy cleared. Screenshots `sprint-57-106/artifacts/dt57106-*.png`.

## Open (deferred — own slices/ADs)

- `AD-HITL-Policy-ReadSide-Potemkin-Phase58` (NEW) — `DBHITLPolicyStore.get_policy()` write-side
  works but is never consumed at tool execution (`ToolGuardrail` Stage 3 hardcodes
  `requires_approval`); risk-threshold semantics redesign = own slice.
- capability_matrix per-tenant role/scope/max_calls override; raw template upload;
  `tenant_policies` dedicated table (note 28 evaluation only); C2 compaction cheap tier (next C).
- `AD-ChatV2-HITL-Card-Tool-Name` (NEW) — the chat-v2 HITL card renders `tool: —` for an
  `approval_requested` event (pre-existing FE wiring gap surfaced by the drive-through).

## Impact

Backend (6 files) + frontend (1 tab + hooks/service/types/view). No migration, no new event,
`loop.py` diff 0. A tenant with no policy is byte-identical to pre-57.106.
