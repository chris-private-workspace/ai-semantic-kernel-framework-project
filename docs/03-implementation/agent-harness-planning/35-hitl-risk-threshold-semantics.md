# 35 — HITL Risk-Threshold Decision Semantics (per-tenant, load-bearing)

**Purpose**: Define the runtime semantics by which the per-tenant `HITLPolicy` risk thresholds decide whether a tool call escalates to human approval or auto-approves — the read-side that Sprint 57.122 made load-bearing.
**Category / Scope**: 範疇 9 (Guardrails / HITL Centralization) × 範疇 1 (Orchestrator Loop) / Phase 57 / Sprint 57.122
**Created**: 2026-06-15
**Last Modified**: 2026-06-15
**Status**: Active
**Slice**: `AD-HITL-Policy-ReadSide-Potemkin-Phase58`

> **Modification History**
> - 2026-06-15: Initial extract from Sprint 57.122 implementation

---

## 1. Spike Summary — US-2/US-3: per-tenant risk thresholds decide tool HITL, as wired in Sprint 57.122

The per-tenant `HITLPolicy` (`backend/src/agent_harness/_contracts/hitl.py:79-87`) carries two risk thresholds — `auto_approve_max_risk` (default LOW) and `require_approval_min_risk` (default MEDIUM). The write-side shipped earlier (Sprint 55.3 DB-backed `get_policy`; Sprint 57.48/57.54 admin GET/PUT at `backend/src/api/v1/admin/tenants.py:932-957` / `:1010-1042`), and the production HITL manager is wired with the DB store (`backend/src/platform_layer/governance/service_factory.py:124` + `:134-137`).

**The gap (Potemkin / 載重)**: neither threshold was read at tool execution. `ToolGuardrail` Stage 3 (`backend/src/agent_harness/guardrails/tool/tool_guardrail.py:151-160`) escalated on the per-rule `requires_approval` bool with a hardcoded `risk_level="MEDIUM"`, and the loop's `_cat9_hitl_branch` then hardcoded `RiskLevel.HIGH` for every escalation (pre-57.122 `loop.py:1007`). Every tenant got the identical decision regardless of their stored thresholds.

**This spike** wired the loop's Cat 9 tool path to read `hitl_manager.get_policy(tenant_id)` and apply a pure two-threshold decision (`decide_tool_hitl`) using the tool's `ToolSpec.risk_level`, and to carry the resolved risk into the `ApprovalRequest`. `ToolGuardrail` stays a stateless, DB-free Cat 9 rule-checker; the loop is the integration point.

## 2. Decision Matrix

### 2.1 Where the risk-source decision was made (user, 2026-06-15)

| Option | Risk source | Schema change | Decision |
|--------|-------------|---------------|----------|
| **A (chosen)** | `ToolSpec.risk_level` (`_contracts/tools.py:95`, always-set, default LOW) | none | ✅ Chosen — no migration / no YAML edit; the spec already carries `risk_level` (reuses the single-source `RiskLevel` from `_contracts.hitl`) |
| B | new per-rule `risk_level` in `capability_matrix.yaml` | config schema + all YAML rules | ❌ Rejected — out of "pure backend wiring" scope; revisit only if per-tool granularity proves insufficient |

### 2.2 Where the precedence decision was made (user, 2026-06-15)

| Option | Semantics | Decision |
|--------|-----------|----------|
| **Two thresholds both load-bearing (chosen)** | `auto_approve_max_risk` can auto-approve a per-rule-flagged tool; `require_approval_min_risk` escalates any tool at/above it; gray band → per-rule bool | ✅ Chosen — both fields bear load (closes the Potemkin fully) |
| Safety floor (per-rule = hard floor) | flagged tools always escalate; thresholds only ADD escalation | ❌ Rejected — makes `auto_approve_max_risk` near-inert (a partial fix) |
| Platform-ceiling hybrid | per-rule floor + tenant auto-approve up to a platform max | ❌ Rejected — needs extra `platform_max` config; AP-6 over-design (YAGNI) |

### 2.3 Implementation-time refinement — the per-rule flag as a MEDIUM risk floor

Because `ToolSpec.risk_level` defaults LOW, a capability-matrix-flagged tool (`requires_approval=True`) with the default LOW spec would have AUTO-APPROVED under the DEFAULT policy — a **silent safety relaxation** for tenants who never set a custom policy. To avoid this regression (the user's motivation was 企業安全剛需 = tighter enforcement), `resolve_tool_risk` treats the flag as a **risk floor of MEDIUM**: a flagged tool's effective risk is `max(spec_risk, MEDIUM)`. This keeps flagged tools escalating under the DEFAULT policy (backward-compatible) while letting a permissive tenant (`auto_approve_max_risk >= MEDIUM`) still auto-approve them (the load-bearing part).

## 3. Verified Invariants

The semantics are two pure functions in `backend/src/agent_harness/_contracts/hitl.py` (DB-free, provider-neutral):

- **`RISK_ORDER` + `risk_ge`/`risk_le`** (`hitl.py:111-133`) — `RiskLevel` is a plain `str` Enum (`hitl.py:37-43`), NOT orderable; compare only via `RISK_ORDER` (`{LOW:0, MEDIUM:1, HIGH:2, CRITICAL:3}`).
- **`resolve_tool_risk(spec_risk, *, rule_requires_approval)`** (`hitl.py:136-160`) — `spec_risk` when present, else LOW; flagged → floored to MEDIUM (`max(base, MEDIUM)`).
- **`decide_tool_hitl(risk, policy, *, rule_requires_approval) -> bool`** (`hitl.py:163-196`) — escalate-first precedence:
  1. `risk >= require_approval_min_risk` → **ESCALATE** (safety-first: wins on a misconfigured overlap `auto >= require`)
  2. `risk <= auto_approve_max_risk` → **auto-approve** (even a per-rule-flagged tool)
  3. gray band → `rule_requires_approval` (the platform baseline tiebreaker)

Loop integration (`backend/src/agent_harness/orchestrator_loop/loop.py`):
- `_resolve_hitl_policy(ctx)` — reads `hitl_manager.get_policy(tenant_id)` (the manager does NOT catch store errors — `manager.py:286-289`), **try/except fail-open** to a conservative DEFAULT policy, cached once per run.
- `_resolve_tool_call_risk(tool_name, *, flagged)` — `self._tool_registry.get(name).risk_level` (`tools/registry.py:66`) → `resolve_tool_risk`.
- `_cat9_tool_check` — BLOCK/SANITIZE/REROLL short-circuit (unchanged); PASS/ESCALATE → `decide_tool_hitl` → `_cat9_hitl_branch(..., risk=R)` or fall-through; ESCALATE-without-manager preserves the pre-57.122 fail-closed soft-block.
- `_cat9_hitl_branch` — `ApprovalRequest.risk_level = risk` (the hardcoded `RiskLevel.HIGH` is dropped).

**Scope boundary** (deliberate): only the **tool path** (`_cat9_hitl_branch`) is policy-aware. The 5 other hardcoded `RiskLevel.HIGH` sites in `loop.py` (input / output / between-turns content-guardrail escalations) are UNCHANGED — a tenant must not be able to auto-approve a jailbreak / PII leak via a risk threshold.

**Verification commands**:
- `pytest backend/tests/unit/agent_harness/guardrails/test_hitl_decision.py -q` → 38 passed (table across risk × {DEFAULT, PERMISSIVE, STRICT, WIDE-grayband, OVERLAP-misconfigured} × flag + floor cases + backward-compat guard + permissive-auto-approve proof).
- `pytest backend/tests/integration/agent_harness/governance/test_loop_hitl_policy.py -q` → 9 passed (loop path: escalate-by-flag / auto-approve-override / escalate-by-threshold / gray-band / **same tool → different decision per tenant** / resolved-risk-on-ApprovalRequest / policy-resolved-once-cached).
- **Drive-through (real chat-v2 + real backend + gpt-5.2)**: the IDENTICAL `python_sandbox(print(6*7))` call auto-approved under a permissive policy (`TOOL_EXEC`) but escalated (`approval_requested risk=MEDIUM` → `awaiting_approval`) under a strict policy set via admin PUT — the runtime read the per-tenant DB policy. See `agent-harness-execution/phase-57/sprint-57-122/progress.md` Day 3 + 3 screenshots.

## 4. Cross-Category Contracts

No NEW cross-category ABC. The decision functions are pure helpers in the existing single-source HITL contract file (`_contracts/hitl.py`, owned by §HITL Centralization per `17-cross-category-interfaces.md §1.1 / §5`). The loop consumes `HITLManager.get_policy` (an existing method, `manager.py:271`) and `ToolRegistry.get` (existing, `registry.py:66`). No 17.md contract addition required (the helpers extend an existing contract type, they don't define a new inter-category interface).

## 5. Open Invariants (NOT verified / deferred to later slices)

- **Admin-PUT validation** that `auto_approve_max_risk < require_approval_min_risk` — NOT enforced; the runtime is safe via escalate-first ordering, but a misconfigured overlap silently means "escalate". Deferred → `AD-HITL-Policy-Threshold-Validation`.
- **The per-rule `requires_approval` flag is double-used** (a MEDIUM floor in `resolve_tool_risk` AND a gray-band tiebreaker in `decide_tool_hitl`) — verified consistent (both push toward escalate, the safe direction) but the interaction is subtle; documented here as the canonical reference.
- **`ToolSpec.hitl_policy` (AUTO/ASK_ONCE/ALWAYS_ASK) + the Sprint 51.1 `PermissionChecker`** are a PARALLEL HITL abstraction NOT wired into the loop (the live path is `guardrail_engine.check_tool_call` → `ToolGuardrail`). NOT touched by this spike; possible separate Potemkin to audit later.
- **Content-guardrail escalations** (input / output / between-turns) still hardcode `RiskLevel.HIGH` — intentional (out of scope; safety-driven, not tool-risk-driven).
- **A dedicated `tenant_policies` typed/RLS/versioned table** — the existing `hitl_policies` columns suffice; graduate later.

## 6. Rollback

The change is contained to `_contracts/hitl.py` (additive pure functions) + `loop.py` (`_cat9_tool_check` restructure + `_cat9_hitl_branch` `risk` param). To revert: restore `_cat9_tool_check`'s original `if g_result.action != PASS` block and the hardcoded `risk_level = RiskLevel.HIGH` at the `_cat9_hitl_branch` `ApprovalRequest`; the pure helpers can stay (unused) or be removed. No migration / schema / wire to undo. Estimated 1-2 hr. The `agent_factor`-free, DB-store-already-wired nature means no infra rollback.

## 7. References

- `04-anti-patterns.md` §AP-4 (Potemkin — this slice closes one) / §AP-6 (rejected the platform-ceiling-hybrid as over-design)
- `17-cross-category-interfaces.md §1.1 / §5` — HITL single-source contract ownership
- `.claude/rules/multi-tenant-data.md` — `get_policy` is tenant-scoped (RLS on `hitl_policies`, migration 0013)
- `claudedocs/4-changes/feature-changes/CHANGE-089-hitl-policy-readside-loadbearing.md` — the change record
- `claudedocs/1-planning/next-phase-candidates.md` — `AD-HITL-Policy-ReadSide-Potemkin-Phase58` (this) + the spun-off `AD-HITL-Policy-Threshold-Validation`
- Sprint 57.122 plan / checklist / progress / retrospective under `docs/03-implementation/`
