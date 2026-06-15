# Sprint 57.122 Plan — HITL policy read-side load-bearing (`AD-HITL-Policy-ReadSide-Potemkin-Phase58`): The per-tenant HITL policy (`HITLPolicy.auto_approve_max_risk` / `require_approval_min_risk`, write-side shipped Sprint 55.3/57.54: DB store + admin GET/PUT) WORKS but is NEVER consumed at tool execution — the agent loop's Cat 9 HITL branch hardcodes `if rule.requires_approval: ESCALATE` (`tool_guardrail.py:151-160`) and then a flat `RiskLevel.HIGH` (`loop.py:1007`), reading NEITHER threshold. So the whole per-tenant approval-threshold feature is structurally complete (write path + DB + admin UI) but **load-bearing-empty** (the runtime never reads it). This sprint makes the thresholds load-bearing: the loop reads `hitl_manager.get_policy(tenant_id)` (the production manager is ALREADY wired with `DBHITLPolicyStore` — `service_factory.py:124/134`) and applies a **two-threshold decision** (user-approved 2026-06-15: both thresholds bear load; tool-call risk from `ToolSpec.risk_level`, no schema change) so the tenant's policy actually decides escalate-vs-auto-approve, and escalations carry the REAL risk (so reviewer routing + SLA become live too). Pure backend; NO migration / wire / codegen / frontend. CHANGE-089 + design note 35 (the risk-threshold semantics).

**Status**: Approved-to-execute (user 2026-06-15: "先執行 HITL 載重 gap（旗艦、企業安全剛需、純後端接線）"; semantics resolved via AskUserQuestion 2026-06-15 — **雙門檻皆生效** + **ToolSpec.risk_level (no schema change)**).
**Branch**: `feature/sprint-57-122-hitl-policy-readside`
**Base**: `main` HEAD `f57135ef` (post-#296 — Sprint 57.121 Skills slash-menu mockup; the Skills epic is COMPLETE).
**Slice**: `AD-HITL-Policy-ReadSide-Potemkin-Phase58` (flagged from the Sprint 57.106 Day-0 Explore; the highest-value of the "C. 主流量 Potemkin / 載重 gap" class). Establishes NEW risk-threshold decision semantics → a **spike-extract design note (35)** is warranted (per `.claude/rules/sprint-workflow.md` §5.5 — new decision semantics, not a pure pattern-reuse continuation). CHANGE-089.
**Scope decisions** (per the AskUserQuestion + the load-bearing-gap framing): (a) **Two thresholds both load-bearing** — `risk ≤ auto_approve_max_risk` → auto-approve (PASS), even for a per-rule-flagged tool; `risk ≥ require_approval_min_risk` → ESCALATE; the gray band → the per-rule `requires_approval` bool decides. Safety-first ordering (escalate-check FIRST) so a misconfigured overlapping policy errs to ESCALATE. (b) **Tool-call risk from `ToolSpec.risk_level`** — no per-rule `risk_level` added to the capability matrix (no schema / YAML change); a flagged tool with no declared risk defaults MEDIUM, an unflagged tool with no declared risk defaults LOW. (c) **Integration point = the loop** (`_cat9_tool_check` / `_cat9_hitl_branch`), NOT the guardrail — `ToolGuardrail` stays a stateless, DB-free Cat 9 rule-checker (no policy-store dependency injected into it); the loop already holds `hitl_manager` + `tenant_id`. (d) **Escalations carry the REAL risk** — replace the hardcoded `RiskLevel.HIGH` (`loop.py:1007`) with the resolved tool risk so `reviewer_groups_by_risk` / `sla_seconds_by_risk` routing become correct. (e) **NO manager-construction change** (the crux wiring `policy_store=DBHITLPolicyStore` is ALREADY done — `service_factory.py:134-137`), **NO migration** (`hitl_policies` table exists, migration 0013), **NO new wire event / codegen / frontend**.

---

## 0. Background

The platform ships a per-tenant HITL (human-in-the-loop) approval policy:

- **Model** (`backend/src/agent_harness/_contracts/hitl.py:80-87`): `HITLPolicy(tenant_id, auto_approve_max_risk: RiskLevel = LOW, require_approval_min_risk: RiskLevel = MEDIUM, reviewer_groups_by_risk, sla_seconds_by_risk)`. `RiskLevel` (`:37-43`) = `LOW / MEDIUM / HIGH / CRITICAL`.
- **Store** (`backend/src/platform_layer/governance/hitl/policy_store.py:55-146`): `DBHITLPolicyStore.get(tenant_id) -> HITLPolicy | None` / `.put(...)` over the `hitl_policies` table (migration 0013, RLS `tenant_id = current_setting('app.tenant_id')`).
- **Manager** (`backend/src/platform_layer/governance/hitl/manager.py:271-291`): `DefaultHITLManager.get_policy(tenant_id) -> HITLPolicy` — resolution order DB store → construction `default_policy` → hardcoded minimal (LOW / MEDIUM).
- **Production wiring (the crux — ALREADY DONE)**: `service_factory.py:124` builds `DBHITLPolicyStore`; `:134-137` builds `DefaultHITLManager(..., policy_store=self.get_hitl_policy_store())`. The chat handler builds the loop with `hitl_manager=service_factory.get_hitl_manager()` (`handler.py:267/705/768-778`). So `hitl_manager.get_policy(tenant_id)` **does read the real DB policy** for a real tenant.
- **Admin write-side (already works)**: `GET /admin/tenants/{tenant_id}/hitl-policies` (`tenants.py:932-957`) + `PUT` (`:1010-1042`, `HITLPolicyUpsertRequest`). An operator can already set a tenant's thresholds.

**The gap**: NONE of the runtime reads those thresholds at tool execution. The Cat 9 tool path:
1. `loop._cat9_tool_check()` (`loop.py:859-941`) → `guardrail_engine.check_tool_call(tc, trace_context=ctx)`.
2. `ToolGuardrail.check()` (`tool_guardrail.py:83-162`) Stage 3 hardcodes `if rule.requires_approval: return GuardrailResult(action=ESCALATE, risk_level="MEDIUM")` (`:151-160`) — reads the per-rule `PermissionRule.requires_approval` bool only; never the tenant policy (even though `trace_context.tenant_id` is in hand at `:116-122`).
3. On ESCALATE, `loop._cat9_hitl_branch()` (`:943-1008`) hardcodes `risk_level = RiskLevel.HIGH` (`:1007`) for EVERY escalation, then `hitl_manager.request_approval(req)`.

⇒ `auto_approve_max_risk` and `require_approval_min_risk` are **decorative**: a tenant can set them via the admin UI, the DB stores them, but a tool call's escalate/auto-approve decision is identical for every tenant. This is the flagship **載重 gap** (load-bearing gap): write-side齊全、執行端零承重.

### Design decision (read `hitl_manager.get_policy(tenant_id)` in the loop Cat 9 path → resolve the tool-call risk from `ToolSpec.risk_level` → apply a pure two-threshold decision → escalate / auto-approve accordingly + carry the real risk into the `ApprovalRequest`; ToolGuardrail stays stateless; NO migration / wire / codegen / frontend)

The decision is a pure function (provider-neutral, DB-free, table-testable) living in the Cat 9 contract layer (`_contracts/hitl.py`):

```
# RiskLevel ordering: LOW(0) < MEDIUM(1) < HIGH(2) < CRITICAL(3)
def decide_tool_hitl(risk, policy, *, rule_requires_approval) -> bool:   # True = ESCALATE (HITL), False = auto-approve
    if risk >= policy.require_approval_min_risk:   # safety-first: escalate-threshold wins on overlap
        return True
    if risk <= policy.auto_approve_max_risk:        # auto-approve up to the tenant's trust ceiling (even if flagged)
        return False
    return rule_requires_approval                   # gray band → the per-rule bool decides

def resolve_tool_risk(spec_risk: RiskLevel | None, *, rule_requires_approval) -> RiskLevel:
    if spec_risk is not None:
        return spec_risk
    return RiskLevel.MEDIUM if rule_requires_approval else RiskLevel.LOW
```

- **US-1**: `decide_tool_hitl` + `resolve_tool_risk` + a `RISK_ORDER` ordering helper in `_contracts/hitl.py` (pure, no DB, unit-tested table-driven across risk × policy × flag).
- **US-2**: the loop (`_cat9_tool_check`) resolves the tenant policy ONCE per run (lazy + cached on the loop instance; fail-open to the manager's own LOW/MEDIUM default on a store error), computes the tool-call risk via `resolve_tool_risk`, and applies `decide_tool_hitl` to BOTH the guardrail-PASS case (new escalation trigger: a high-risk unflagged tool now escalates) AND the guardrail-ESCALATE case (auto-approve override: a flagged low-risk tool now auto-approves per the tenant's threshold). `flagged = (guardrail action == ESCALATE)`. BLOCK / SANITIZE short-circuit FIRST (not subject to the HITL policy).
- **US-3**: `_cat9_hitl_branch` uses the resolved tool risk for the `ApprovalRequest` (replace the hardcoded `RiskLevel.HIGH` at `:1007`) → `reviewer_groups_by_risk` / `sla_seconds_by_risk` routing become correct.
- **US-4**: tests — unit (the pure functions) + integration (the loop path: auto-approve / escalate-by-threshold / escalate-by-flag / gray-band) + **multi-tenant** (two tenants, different policies, SAME tool → different decisions = the load-bearing proof).
- **US-5**: drive-through (real chat-v2 + real backend + real LLM): set a tenant's policy via admin PUT to a NON-default threshold, then drive a tool call and observe the HITL behavior change vs. a default-policy tenant (the same tool escalates for one tenant, auto-approves for the other).
- **US-6**: design note 35 (the risk-threshold semantics — the two-threshold rule, the precedence ordering, the risk-resolution defaults, the gray-band) + CHANGE-089.
- **Rejected / deferred**: injecting the policy store into `ToolGuardrail` (keeps Cat 9 DB-free — the loop is the integration point); adding a per-rule `risk_level` to the capability matrix YAML (the AskUserQuestion chose `ToolSpec.risk_level`, no schema change); the "platform-ceiling hybrid" precedence (the AskUserQuestion chose two-thresholds-both-load-bearing); admin-PUT validation that `auto_approve_max_risk < require_approval_min_risk` (a separate hardening slice — the runtime is safe via escalate-first ordering); a `tenant_policies` dedicated typed table (the JSONB/columns shape is sufficient; graduate later).

### Ground truth (Day-0 head-start — direct reads on `main` HEAD `f57135ef` + the Sprint 57.106 Explore; ALL re-verified in the formal Day-0 三-prong §checklist 0.1)

**Read-side wiring (CRUX — confirmed wired):**
- `service_factory.py:124` `self._hitl_policy_store = DBHITLPolicyStore(...)`; `:134-137` `DefaultHITLManager(..., policy_store=self.get_hitl_policy_store())`. → `get_policy(tenant_id)` reads the DB for real tenants. (Day-0: re-confirm the loop's `hitl_manager` is this factory instance via `handler.py:267/705/768`.)
- `manager.py:271-291` `get_policy(self, tenant_id, *, trace_context=None) -> HITLPolicy` — DB → default_policy → hardcoded LOW/MEDIUM. (Day-0: confirm it does NOT raise on a store exception, OR wrap the loop call in try/except → fail-open to a default `HITLPolicy`.)

**The gap (to change):**
- `tool_guardrail.py:151-160` Stage 3 hardcoded `if rule.requires_approval: ESCALATE risk_level="MEDIUM"` — leave the ESCALATE signal (it = "this rule is flagged"); the loop reinterprets it through the policy. (Day-0: confirm `GuardrailResult.action` / the `GuardrailAction` enum `_abc.py:47-54`.)
- `loop.py:859-941` `_cat9_tool_check` (the guardrail call + the `if action == ESCALATE and hitl_manager: _cat9_hitl_branch`); `:943-1008` `_cat9_hitl_branch`; `:1007` hardcoded `RiskLevel.HIGH`; `:492` `self._hitl_manager`; `:987` `tenant_id = self._tenant_id or ctx.tenant_id`. (Day-0: confirm how the loop maps `tc.tool_name → ToolSpec` to read `.risk_level` — the tool registry / spec list the loop already holds for prompt-building; confirm `ToolSpec.risk_level` is `RiskLevel | None` vs always-set.)

**The contract (to extend):**
- `_contracts/hitl.py:37-43` `RiskLevel` (str Enum, NOT ordered — needs a `RISK_ORDER` map or comparison helper); `:80-87` `HITLPolicy`. (Day-0: confirm `RiskLevel` is a plain `Enum` (add ordering) vs already comparable.)

**Baselines (57.121 closeout)**: full pytest **2648+5skip** · wire **24** · FE Vitest **888** · mockup-fidelity **51** · mypy `src` **0/371** · run_all **10/10**. Re-verify Day-0.
- **Backend-only. NO migration. NO wire / codegen (count 24). NO frontend.** Design note **35** (next free) + **CHANGE-089** (088 = 57.121).

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

(1) **Prong-1 path**: `_contracts/hitl.py` / `tool_guardrail.py` / `loop.py` / `manager.py` / `service_factory.py` / `policy_store.py` exist as above; no NEW file needed except tests + the design note + CHANGE. (2) **Prong-2 content**: the loop's `tc.tool_name → ToolSpec` mapping (how to read `.risk_level`); whether `ToolSpec.risk_level` is `Optional`; whether `RiskLevel` is plain `Enum` (needs ordering); whether `_cat9_hitl_branch`'s `ApprovalRequest` already routes by risk in the manager (so passing real risk is sufficient); whether `get_policy` raises on a store error (→ decide fail-open wrap). (3) **Prong-2 existing tests**: find the existing loop Cat 9 / HITL / guardrail tests to EXTEND (not duplicate); find the existing `DBHITLPolicyStore` / `manager.get_policy` tests. (4) **Prong-3 schema**: N/A — no new table / migration (`hitl_policies` 0013 exists; re-confirm its columns match `HITLPolicy` per the Sprint 55.3 D6 correction). (5) 17.md: does the HITL/Cat 9 contract section need the `decide_tool_hitl` semantics registered? (single-source). (6) Baselines re-verify (pytest 2648+5skip / wire 24 / Vitest 888 / mockup 51 / mypy 0/371 / run_all 10/10).

## 1. Sprint Goal

The agent loop's Cat 9 HITL branch becomes policy-aware: it reads `hitl_manager.get_policy(tenant_id)` and applies a pure two-threshold decision (`risk ≤ auto_approve_max_risk` → auto-approve; `risk ≥ require_approval_min_risk` → escalate; gray band → per-rule bool) using the tool-call risk resolved from `ToolSpec.risk_level`, and escalations carry the real risk into the `ApprovalRequest`. The per-tenant HITL thresholds (write-side shipped 55.3/57.54) become **load-bearing** — the SAME tool call escalates for one tenant and auto-approves for another, per their policy. Closes `AD-HITL-Policy-ReadSide-Potemkin-Phase58` (the flagship 載重 gap). Proven by a real chat-v2 + real-LLM drive-through showing the per-tenant behavior delta. Pure backend; NO migration / wire (count 24) / codegen / frontend. Design note 35 + CHANGE-089.

## 2. User Stories

- **US-1**: 作為 platform，我希望有一個純決策函式（`decide_tool_hitl` + `resolve_tool_risk` + `RISK_ORDER`，置於 `_contracts/hitl.py`，無 DB 依賴）把「兩門檻 + per-rule bool + 工具風險」轉成 escalate/auto-approve 布林，以便決策可 table-test、可被 loop 重用、且 provider-neutral。
- **US-2**: 作為 agent loop，我希望 Cat 9 tool 路徑讀租戶 policy（`hitl_manager.get_policy(tenant_id)`，每 run cache 一次、store 例外 fail-open 至預設 policy）並套 `decide_tool_hitl`——對 guardrail-PASS（新增升審觸發：高風險未標工具）與 guardrail-ESCALATE（自動核准覆寫：被標低風險工具）皆生效，BLOCK/SANITIZE 先短路——以便租戶門檻真正決定 escalate-vs-auto-approve。
- **US-3**: 作為 reviewer routing，我希望升審帶真實風險：`_cat9_hitl_branch` 用 `resolve_tool_risk` 的結果建 `ApprovalRequest`（取代寫死的 `RiskLevel.HIGH`），以便 `reviewer_groups_by_risk` / `sla_seconds_by_risk` 路由正確。
- **US-4**: 作為 platform，我希望測試守住：unit（純函式 table：risk × policy × flag 全組合）+ integration（loop 路徑 auto-approve / escalate-by-threshold / escalate-by-flag / gray-band）+ **multi-tenant**（兩租戶不同 policy、同工具 → 不同決策 = 載重證明），以便回歸受保護。
- **US-5**: 作為 reviewer，我希望真 drive-through（真 chat-v2 + 真 backend + 真 LLM）：用 admin PUT 把某租戶 policy 設成非預設門檻，驅動一個工具呼叫，觀察其 HITL 行為與預設租戶不同（同工具一個升審、一個自動核准）；截圖 + observed-vs-intended。
- **US-6**: 作為 future dev，我希望 design note 35 記錄風險門檻語意（兩門檻規則、precedence 排序、風險解析預設、gray band），以便後續可理解/可 rollback；CHANGE-089。

## 3. Technical Specifications

### 3.0 Architecture (loop reads `get_policy` → resolve risk from `ToolSpec.risk_level` → pure two-threshold decision → escalate/auto-approve + real-risk `ApprovalRequest`; ToolGuardrail stateless; NO migration / wire / codegen / frontend)

```
_contracts/hitl.py (EDIT): + RISK_ORDER + risk comparison + decide_tool_hitl(...) + resolve_tool_risk(...)   [pure, no DB]
orchestrator_loop/loop.py (EDIT): _cat9_tool_check resolves+caches policy, computes risk, applies decision
                                  (re-eval PASS for high-risk-unflagged + auto-approve flagged-low-risk);
                                  _cat9_hitl_branch builds ApprovalRequest with the real risk (drop hardcoded HIGH)
tests: unit (decide_tool_hitl table) + integration (loop path) + multi-tenant (two policies, same tool)
docs: design note 35 (risk-threshold semantics) + CHANGE-089
tool_guardrail.py / capability_matrix.py / service_factory.py / manager.py / policy_store.py / migrations / events / sse / frontend: UNTOUCHED (or read-only)
```

### 3.1 Pure decision contract (US-1) — `_contracts/hitl.py`

Add (provider-neutral, no DB import):
- `RISK_ORDER: dict[RiskLevel, int]` = `{LOW:0, MEDIUM:1, HIGH:2, CRITICAL:3}` + a `_rank(level) -> int` / comparison helpers (`risk_ge`, `risk_le`) — `RiskLevel` is a string `Enum`, NOT orderable as-is.
- `decide_tool_hitl(risk: RiskLevel, policy: HITLPolicy, *, rule_requires_approval: bool) -> bool` — `True` = needs HITL (ESCALATE), `False` = auto-approve. Logic: escalate-first (`risk >= require_approval_min_risk → True`), then auto-approve (`risk <= auto_approve_max_risk → False`), then gray band (`return rule_requires_approval`).
- `resolve_tool_risk(spec_risk: RiskLevel | None, *, rule_requires_approval: bool) -> RiskLevel` — `spec_risk` if set, else `MEDIUM if rule_requires_approval else LOW`.

Docstrings cite the design note + the AskUserQuestion decision (two-thresholds-both-load-bearing + ToolSpec-risk + safety-first ordering).

### 3.2 Loop integration (US-2/US-3) — `loop.py`

- **Policy resolution + cache**: add `self._hitl_policy: HITLPolicy | None = None` (or a small `_resolve_hitl_policy()` coroutine) — on first Cat 9 tool check of a run, `try: policy = await self._hitl_manager.get_policy(tenant_id) except Exception: policy = <conservative default HITLPolicy(LOW, MEDIUM)>`; cache for the run (tenant_id is stable). (If `hitl_manager is None` → keep today's behavior: flagged-only escalate.)
- **`_cat9_tool_check`** (`:859-941`): after the guardrail verdict — if `action in (BLOCK, SANITIZE, REROLL)` short-circuit as today; else (PASS / ESCALATE) resolve the tool's risk (`spec = <tool registry>[tc.tool_name]`; `R = resolve_tool_risk(spec.risk_level, rule_requires_approval=(action==ESCALATE))`), resolve the policy (cached), and `if decide_tool_hitl(R, policy, rule_requires_approval=(action==ESCALATE)) and hitl_manager: _cat9_hitl_branch(..., risk=R)` else proceed (auto-approve / pass). This adds the new escalation trigger (high-risk unflagged) AND the auto-approve override (flagged low-risk).
- **`_cat9_hitl_branch`** (`:943-1008`): accept the resolved `risk` param; build the `ApprovalRequest` with it (replace the hardcoded `RiskLevel.HIGH` at `:1007`). Everything downstream (`request_approval`, reviewer routing, SLA, the `approval_requested` SSE) flows from the real risk.
- Emit an observability detail (existing Cat 12 span/log) noting the policy-driven decision (auto-approve vs escalate + the resolved risk + the thresholds) — reuse the existing Cat 9 span; no new event.

### 3.3 What stays stateless / untouched

`ToolGuardrail` keeps its Stage 3 ESCALATE-on-`requires_approval` signal (no policy store injected — Cat 9 stays DB-free); the loop reinterprets it. `capability_matrix.py` unchanged (no per-rule `risk_level`). `service_factory.py` / `manager.py` / `policy_store.py` unchanged (the crux wiring + `get_policy` already exist). No migration (table 0013 exists). No new SSE event / codegen (count 24). No frontend.

### 3.4 Drive-through (US-5) — real chat-v2 + real backend + real LLM

1. Real backend (:8000) + Vite (:3007) + dev-login. Pick a tool whose `ToolSpec.risk_level` lands in a band the policy can flip (Day-0/drive-through: identify a concrete MEDIUM-or-higher tool reachable from chat-v2, e.g. a business tool or `request_approval`).
2. **Tenant A (default policy)**: drive the tool → observe today's behavior (escalate or not) as the baseline.
3. **Tenant B**: `PUT /admin/tenants/{B}/hitl-policies` to a NON-default threshold (e.g. `auto_approve_max_risk=HIGH` to auto-approve the tool that escalates for A, OR `require_approval_min_risk=LOW` to escalate a tool that A auto-approves). Drive the SAME tool → observe the DIFFERENT HITL behavior. This is the load-bearing proof: the runtime now reads the tenant's policy.
4. Screenshots + observed-vs-intended (the per-tenant delta) in progress.md.

> If a clean two-tenant chat-v2 drive-through proves impractical (tool reachability / approval-card UX), fall back to a same-tenant before/after: drive → PUT a new policy → re-drive → observe the flip. Either way the proof is "the runtime decision changed because the DB policy changed" — NOT a gate-only claim.

### 3.5 What is explicitly NOT done

A per-rule `risk_level` in the capability matrix YAML (chose `ToolSpec.risk_level`); the platform-ceiling-hybrid precedence (chose two-thresholds-both-load-bearing); injecting the policy store into `ToolGuardrail`; admin-PUT validation of `auto_approve_max_risk < require_approval_min_risk` (a separate hardening AD — the runtime is safe via escalate-first ordering); a dedicated `tenant_policies` typed table; the `AD-ChatV2-HITL-Card-Tool-Name` FE polish (separate chat-v2 slice); the FE-tenant-display fixture (`AD-FE-Tenant-Display-Fixture-Phase58`, a separate C-class item); any migration / wire / codegen / frontend.

### 3.6 Validation (US-1..US-6)

Gates: mypy strict `src` **0** (re-baseline the count after the new contract helpers — may rise from 371) · run_all **10/10** (count 24) · full pytest **2648+5skip + N** (new unit + integration + multi-tenant) · Vitest **888 UNCHANGED** (no frontend) · mockup-fidelity **51 UNCHANGED** · `tool_guardrail.py` / `capability_matrix.py` / `service_factory.py` / `manager.py` / `policy_store.py` / migrations / events / sse / codegen / frontend **UNTOUCHED**. Plus: the unit table covers every risk × {default policy, auto=HIGH policy, require=LOW policy} × {flagged, unflagged}; the multi-tenant integration proves the same tool → different decision; the drive-through proves the per-tenant runtime delta (NOT gate-only).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/_contracts/hitl.py` | EDIT — add `RISK_ORDER` + risk comparison helpers + `decide_tool_hitl(...)` + `resolve_tool_risk(...)` (pure, no DB) |
| 2 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT — `_cat9_tool_check` resolve+cache policy + compute risk + apply `decide_tool_hitl`; `_cat9_hitl_branch` build `ApprovalRequest` with the real risk (drop hardcoded `RiskLevel.HIGH`) |
| 3 | `backend/tests/unit/agent_harness/.../test_hitl_decision.py` | NEW — table-driven `decide_tool_hitl` + `resolve_tool_risk` + `RISK_ORDER` (path confirmed Day-0) |
| 4 | `backend/tests/integration/.../test_loop_hitl_policy.py` (or EXTEND an existing loop-HITL test) | NEW/EDIT — loop path auto-approve / escalate-by-threshold / escalate-by-flag / gray-band + multi-tenant (two policies, same tool) |
| 5 | `docs/03-implementation/agent-harness-planning/35-hitl-risk-threshold-semantics.md` | NEW — design note 35 (the risk-threshold decision semantics; 8-point quality gate) |
| 6 | `claudedocs/4-changes/feature-changes/CHANGE-089-hitl-policy-readside-loadbearing.md` | NEW — change record (incl. the drive-through delta) |
| — | `tool_guardrail.py` / `capability_matrix.py` / `service_factory.py` / `manager.py` / `policy_store.py` / migrations / `events.py` / `sse.py` / codegen / frontend | **UNTOUCHED / NONE** |

(Exact test paths confirmed in Day-0 Prong-2 by locating the existing loop-Cat9 / HITL / guardrail test homes.)

## 5. Acceptance Criteria

1. `_contracts/hitl.py` exposes `decide_tool_hitl` + `resolve_tool_risk` + `RISK_ORDER` (pure, no DB import), implementing the two-threshold escalate-first semantics + the risk-resolution defaults (flagged→MEDIUM / unflagged→LOW).
2. The loop's `_cat9_tool_check` reads `hitl_manager.get_policy(tenant_id)` (cached per run, fail-open to a conservative default on a store error) and applies `decide_tool_hitl` to both the guardrail-PASS and guardrail-ESCALATE cases; BLOCK / SANITIZE short-circuit first.
3. `_cat9_hitl_branch` builds the `ApprovalRequest` with the resolved tool risk (the hardcoded `RiskLevel.HIGH` is gone); reviewer routing + SLA flow from the real risk.
4. Unit table covers risk × policy × flag; multi-tenant integration proves the SAME tool → DIFFERENT decision under two tenants' policies.
5. Gates: mypy 0 (re-baselined) · run_all 10/10 (count 24) · pytest 2648+5skip + N · Vitest 888 unchanged · mockup 51 unchanged · `tool_guardrail.py`/`capability_matrix.py`/`service_factory.py`/`manager.py`/migrations/events/sse/codegen/frontend UNTOUCHED.
6. Real drive-through PASS: a tenant with a non-default HITL policy drives the SAME tool to a DIFFERENT HITL outcome than a default-policy tenant (or a same-tenant before/after PUT flip); screenshots + observed-vs-intended (live — the runtime read the DB policy, NOT gate-only).
7. `AD-HITL-Policy-ReadSide-Potemkin-Phase58` shipped (the flagship 載重 gap closed); design note 35 (8-point quality gate passed); CHANGE-089; calibration recorded; 17.md HITL/Cat 9 section updated if a contract registration is needed.

## 6. Deliverables

- [ ] US-1 `_contracts/hitl.py` pure helpers (`RISK_ORDER` + `decide_tool_hitl` + `resolve_tool_risk`)
- [ ] US-2 loop `_cat9_tool_check` policy-aware decision (resolve+cache policy, compute risk, apply decision, BLOCK/SANITIZE short-circuit)
- [ ] US-3 loop `_cat9_hitl_branch` real-risk `ApprovalRequest` (drop hardcoded HIGH)
- [ ] US-4 tests (unit table + integration loop path + multi-tenant same-tool-different-decision)
- [ ] US-5 drive-through PASS (per-tenant HITL delta; screenshots + observed-vs-intended)
- [ ] US-6 design note 35 (risk-threshold semantics, 8-point gate) + CHANGE-089 + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates: `AD-HITL-Policy-ReadSide-Potemkin-Phase58` shipped; 17.md HITL/Cat 9 registration if needed)

## 7. Workload Calibration

- Scope class **`harness-loadbearing-gap-fix` 0.60** (NEW, 1st data point; pending 2-3 sprint validation). Shape: make an existing write-side feature's read-side load-bearing — a pure decision contract + a bounded loop-integration (read an already-wired manager + apply the decision) + multi-tenant tests + a per-tenant-delta drive-through + a semantics design note. More than `reality-gap-fix` 0.50 (it establishes NEW decision semantics + a design note + multi-tenant proof, not a one-line wire) but less than `medium-backend` 0.80 (the crux wiring is ALREADY done — no manager/migration/schema change; the surface is one contract file + one loop file + tests). Set 0.60 (kin to `subagent-child-loop-spike` 0.60 / `config-tiering-model-policy-spike` 0.60 — a contained backend slice over proven plumbing). If the 1st point lands > 1.20, re-point toward 0.80; if < 0.7, toward 0.50.
- **Agent-delegated: no** (parent-direct; the decision semantics + the loop integration + the live per-tenant drive-through need careful hand-authoring + verification). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~6.5 hr (contract helpers + unit table ~1.0 · loop integration ~1.5 · integration + multi-tenant tests ~1.25 · drive-through ~1.0 · design note 35 ~0.9 · CHANGE-089 + closeout ~0.85) → class-calibrated commit ~3.9 hr (mult 0.60). Day-4 retro Q2 verifies (1st `harness-loadbearing-gap-fix` data point).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **The production `hitl_manager` is NOT actually wired with the DB store** → even after the loop change, `get_policy` returns the in-memory default → still Potemkin | **Pre-verified** (`service_factory.py:124/134-137` wires `policy_store=DBHITLPolicyStore`); Day-0 re-confirm the loop's `hitl_manager` IS the factory instance (`handler.py:267/705/768`). If a code path builds the loop with a store-less manager, wire it (in scope). |
| `RiskLevel` is a plain `str Enum`, NOT orderable → naive `>=` comparison fails | add an explicit `RISK_ORDER` map + `risk_ge`/`risk_le` helpers; never compare the enums directly; unit-test the ordering |
| `ToolSpec.risk_level` is `Optional` / some tools have no declared risk → `None` risk | `resolve_tool_risk` defaults `flagged→MEDIUM` / `unflagged→LOW` (the AskUserQuestion decision); Day-0 confirm the field's type + how the loop maps `tool_name → ToolSpec` |
| `get_policy` raises on a DB/store error → the tool check crashes mid-loop | wrap the loop's `get_policy` call in try/except → fail-open to a conservative `HITLPolicy(auto_approve_max_risk=LOW, require_approval_min_risk=MEDIUM)` (= today's effective behavior); log the fallback (Cat 12) |
| Resolving the policy per tool call hits the DB repeatedly | resolve ONCE per loop run + cache on the loop instance (tenant_id stable); mirrors the `resolve_tenant_model_policy` / `resolve_tenant_skill_registry` TTL precedent (here a per-run cache suffices) |
| The new auto-approve path silently SUPPRESSES an approval an admin intended (a flagged tool now auto-approves under a permissive tenant threshold) | this is the user-chosen semantics (two-thresholds-both-load-bearing); document it prominently in design note 35 + CHANGE-089 + the `decide_tool_hitl` docstring; the safety-first ordering ensures `require_approval_min_risk` still wins on a misconfigured overlap; the drive-through demonstrates it intentionally |
| Test isolation — a module-level `service_factory` / HITL manager singleton across test event loops (Risk Class C) | use the established autouse `reset_*` fixture pattern (`.claude/rules/testing.md` §Module-level Singleton Reset); resolve the policy via an injected manager in the integration test, not the global factory |
| Risk Class E — a stale `--reload` backend serves old loop code at the drive-through (this sprint DOES change `.py`) | clean restart before the drive-through (kill ALL stale uvicorn reloader+worker PIDs / `Win32_Process` PID/PPID/StartTime sweep), confirm the fresh PID is the sole :8000 owner, capture a startup log line; the policy read is per-request so no startup-only concern, but the loop code change requires the new process |
| `mypy --strict` cross-platform `unused-ignore` on the new helpers | follow `.claude/rules/code-quality.md` dual-ignore pattern if needed |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **Per-rule `risk_level` in the capability matrix YAML** (chose `ToolSpec.risk_level`; revisit if per-tool granularity proves insufficient).
- **Admin-PUT validation** that `auto_approve_max_risk < require_approval_min_risk` (a hardening AD; the runtime is safe via escalate-first ordering — a future `AD-HITL-Policy-Threshold-Validation`).
- **The `AD-ChatV2-HITL-Card-Tool-Name`** FE polish (the chat-v2 approval card renders `tool: —`) — a separate chat-v2 slice.
- **`AD-FE-Tenant-Display-Fixture-Phase58`** (sidebar/header fixture tenant) — the next C-class 主流量 Potemkin item.
- **`AD-HITL-Policy-Threshold-Semantics` for the gray-band beyond per-rule bool** (e.g. an explicit "ask-once" tier the admin GET projects) — deferred; the per-rule bool tiebreaker is sufficient now.
- A dedicated `tenant_policies` typed/RLS/versioned table (the JSONB/columns shape is sufficient; graduate when ≥2 more policy concerns land or a typed-query need arises — the `rate_limit_configs` 0019 precedent).
- Any migration / wire / codegen / SSE / frontend change (count 24 unchanged).
