# Sprint 57.122 — Checklist (HITL policy read-side load-bearing: the per-tenant `HITLPolicy.auto_approve_max_risk`/`require_approval_min_risk` (write-side shipped 55.3/57.54: DB store + admin GET/PUT) is NEVER read at tool execution — the loop's Cat 9 HITL branch hardcodes `if rule.requires_approval: ESCALATE` (`tool_guardrail.py:151-160`) + a flat `RiskLevel.HIGH` (`loop.py:1007`). This makes the thresholds load-bearing: the loop reads `hitl_manager.get_policy(tenant_id)` (production manager ALREADY wired with `DBHITLPolicyStore`) + applies a pure two-threshold decision (risk from `ToolSpec.risk_level`, no schema change) + carries the real risk into the `ApprovalRequest`. Backend-only; NO migration/wire/codegen/frontend. CHANGE-089 + design note 35)

[Plan](./sprint-57-122-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong; Prong-3 schema: confirm `hitl_policies` table exists, NO new table/migration) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `f57135ef`) — catalogue in progress.md
- [x] **Prong 1 — path verify**: `_contracts/hitl.py` · `orchestrator_loop/loop.py` · `guardrails/tool/tool_guardrail.py` · `platform_layer/governance/hitl/manager.py` · `.../hitl/policy_store.py` · `platform_layer/governance/service_factory.py` present; `CHANGE-089-*.md` free; `docs/.../35-*.md` design-note free; locate the existing loop-Cat9 / HITL / guardrail test homes (for US-4 placement)
- [x] **Prong 2 — content verify** (drift findings → progress.md):
  - [x] **D-manager-wired** (CRUX): `service_factory.py:124/134-137` builds `DefaultHITLManager(policy_store=DBHITLPolicyStore)`; the loop's `hitl_manager` IS the factory instance (`handler.py:267/705/768`) → `get_policy(tenant_id)` reads DB. If any path builds a store-less manager → note as in-scope wiring
  - [x] **D-getpolicy-shape**: `manager.py:271-291` `get_policy(tenant_id, *, trace_context=None) -> HITLPolicy`; resolution DB→default→hardcoded LOW/MEDIUM; **does it raise on a store exception?** → decide the loop fail-open wrap
  - [x] **D-risklevel-order**: `_contracts/hitl.py:37-43` `RiskLevel` — plain `str Enum` (NOT orderable) → confirm a `RISK_ORDER` map is needed (vs already comparable)
  - [x] **D-toolspec-risk**: how the loop maps `tc.tool_name → ToolSpec` (the tool registry / spec list held for prompt-building); is `ToolSpec.risk_level` `RiskLevel | None` or always-set? → shapes `resolve_tool_risk`
  - [x] **D-cat9-anchors**: `loop.py:859-941` `_cat9_tool_check` (guardrail call + `if action==ESCALATE and hitl_manager: _cat9_hitl_branch`); `:943-1008` `_cat9_hitl_branch`; `:1007` hardcoded `RiskLevel.HIGH`; `:987` `tenant_id`; `:492` `self._hitl_manager`. Confirm `GuardrailAction` enum (`_abc.py:47-54`) + does `_cat9_hitl_branch`'s manager already route by risk (so passing real risk suffices)
- [x] **Prong 3 — schema**: `hitl_policies` table (migration 0013) exists with columns mirroring `HITLPolicy` (Sprint 55.3 D6 correction); **NO new table / migration this sprint** — confirm only
- [x] **D-baselines**: full pytest **2648+5skip** · wire **24** · Vitest **888** · mockup **51** · mypy `src` **0/371** · run_all **10/10** (re-run to capture real baseline at HEAD)
- [x] **Catalog drift**: anchors confirmed / scope shift noted in plan §8 (do NOT silently edit §3)
- [x] **Go/no-go**: scope shift ≤20% → GO; 20-50% → revise §Acceptance + §Workload; >50% → abort+redraft

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-122-hitl-policy-readside` (from `main` `f57135ef`)

---

## Day 1 — Pure decision contract (US-1) — `_contracts/hitl.py`

### 1.1 `RISK_ORDER` + comparison helpers
- [x] **`backend/src/agent_harness/_contracts/hitl.py`** (EDIT): add `RISK_ORDER: dict[RiskLevel, int]` = `{LOW:0, MEDIUM:1, HIGH:2, CRITICAL:3}` + `risk_ge(a, b)` / `risk_le(a, b)` helpers (never compare the enums directly). MHist + Last Modified
  - DoD: `RISK_ORDER` covers all 4 levels; helpers are total order

### 1.2 `decide_tool_hitl` + `resolve_tool_risk`
- [x] **`decide_tool_hitl(risk, policy, *, rule_requires_approval) -> bool`**: escalate-first (`risk_ge(risk, policy.require_approval_min_risk) → True`), then auto-approve (`risk_le(risk, policy.auto_approve_max_risk) → False`), then gray band (`return rule_requires_approval`). Docstring cites design note 35 + the two-thresholds-both-load-bearing decision
- [x] **`resolve_tool_risk(spec_risk: RiskLevel | None, *, rule_requires_approval) -> RiskLevel`**: `spec_risk` if set else `MEDIUM if rule_requires_approval else LOW`
  - DoD: both pure, no DB import; provider-neutral (no openai/anthropic)

### 1.3 Unit table (US-4 first half)
- [x] **`backend/tests/unit/.../test_hitl_decision.py`** (NEW; path confirmed Day-0): table across `risk ∈ {LOW,MEDIUM,HIGH,CRITICAL}` × `policy ∈ {default(LOW,MEDIUM), permissive(HIGH,CRITICAL), strict(LOW,LOW)}` × `flagged ∈ {T,F}` → assert escalate/auto-approve; `resolve_tool_risk` cases (set / flagged-none→MEDIUM / unflagged-none→LOW); `RISK_ORDER` ordering; misconfigured-overlap (auto≥require) → escalate-first wins (safe)
  - Verify: `pytest backend/tests/unit/.../test_hitl_decision.py -q`

---

## Day 2 — Loop integration (US-2, US-3) + integration/multi-tenant tests (US-4 second half)

### 2.1 Policy resolution + cache (US-2)
- [x] **`loop.py`** (EDIT): add `self._hitl_policy` cache (resolve ONCE per run, lazy on first Cat 9 tool check) — `try: policy = await self._hitl_manager.get_policy(tenant_id) except Exception: policy = HITLPolicy(auto_approve_max_risk=LOW, require_approval_min_risk=MEDIUM)` (fail-open = today's behavior; log Cat 12). `hitl_manager is None` → keep today's flagged-only escalate
  - DoD: one DB read per run (not per tool call); fail-open verified

### 2.2 Decision in `_cat9_tool_check` (US-2)
- [x] **`_cat9_tool_check`** (`:859-941`, EDIT): after the guardrail verdict — `BLOCK/SANITIZE/REROLL` short-circuit first (as today); else (PASS/ESCALATE) resolve risk (`R = resolve_tool_risk(<spec>.risk_level, rule_requires_approval=(action==ESCALATE))`) + policy (cached) + `if decide_tool_hitl(R, policy, rule_requires_approval=(action==ESCALATE)) and hitl_manager: _cat9_hitl_branch(..., risk=R)` else proceed. Adds the new escalation trigger (high-risk unflagged) + auto-approve override (flagged low-risk)
  - DoD: BLOCK/SANITIZE unaffected; the two new behaviors wired

### 2.3 Real risk into `ApprovalRequest` (US-3)
- [x] **`_cat9_hitl_branch`** (`:943-1008`, EDIT): accept the resolved `risk` param; build `ApprovalRequest` with it (drop the hardcoded `RiskLevel.HIGH` at `:1007`); reviewer routing + SLA flow from the real risk. MHist + Last Modified on `loop.py`
  - DoD: `grep RiskLevel.HIGH loop.py` → the hardcoded escalation default is gone

### 2.4 Integration + multi-tenant tests (US-4)
- [x] **`backend/tests/integration/.../test_loop_hitl_policy.py`** (NEW/EXTEND; path confirmed Day-0): loop path — auto-approve (risk ≤ auto_max), escalate-by-threshold (risk ≥ require_min, unflagged), escalate-by-flag (gray band + flagged), gray-band-unflagged → pass; **multi-tenant**: two tenants, different policies, SAME tool → DIFFERENT decision (the load-bearing proof); Risk Class C — autouse `reset_*` singleton fixture / injected manager
  - Verify: `pytest backend/tests/integration/.../test_loop_hitl_policy.py -q`

### 2.5 Gate sweep
- [x] mypy `src` **0** (re-baseline count — may rise from 371 with new helpers) · `run_all` **10/10** (count 24) · full pytest **2648+5skip + N** · Vitest **888 UNCHANGED** (no FE) · mockup **51 UNCHANGED** · `tool_guardrail.py`/`capability_matrix.py`/`service_factory.py`/`manager.py`/`policy_store.py`/migrations/events/sse/codegen/frontend UNTOUCHED
  - Verify: `black/isort/flake8/mypy` · `python scripts/lint/run_all.py` · `pytest`

---

## Day 3 — Drive-through (US-5) — real chat-v2 + real backend + real LLM

### 3.1 Clean restart / probe (Risk Class E — `.py` changed)
- [x] Kill ALL stale uvicorn reloader+worker PIDs (`Win32_Process` PID/PPID/StartTime sweep); confirm the fresh PID is the sole :8000 owner (no Errno 10048); capture a startup log line. Vite :3007 + dev-login (acme-prod)
  - DoD: the running backend serves the NEW loop code (not a stale `--reload` worker)

### 3.2 Drive-through (per-tenant HITL delta)
- [x] Identify a concrete tool reachable from chat-v2 whose `ToolSpec.risk_level` a policy can flip (business tool / `request_approval`); document the choice
- [x] **Tenant A (default policy)**: drive the tool → observe baseline (escalate or not)
- [x] **Tenant B**: `PUT /admin/tenants/{B}/hitl-policies` to a non-default threshold (e.g. `auto_approve_max_risk=HIGH` or `require_approval_min_risk=LOW`) → drive the SAME tool → observe the DIFFERENT HITL outcome. (Fallback: same-tenant before/after PUT flip.)
- [x] Each step driven (real render, not fixture): observed-vs-intended (the per-tenant delta) + screenshots in progress.md. **AP-4 clear** — the runtime read the DB policy
  - DoD: the SAME tool → DIFFERENT HITL outcome per the DB policy (load-bearing proven LIVE, NOT gate-only)

---

## Day 4 — Design note 35 + CHANGE-089 + closeout

### 4.1 Design note 35 (US-6)
- [x] **`docs/03-implementation/agent-harness-planning/35-hitl-risk-threshold-semantics.md`** (NEW): the two-threshold rule + escalate-first precedence + risk-resolution defaults + the gray band + the auto-approve-suppresses-flagged trade-off; 8-point quality gate (file:line, decision matrix, verification command, etc.)
  - DoD: 8-point gate passed (record in retrospective.md)

### 4.2 CHANGE-089
- [x] **`claudedocs/4-changes/feature-changes/CHANGE-089-hitl-policy-readside-loadbearing.md`** (1-page, incl. the per-tenant drive-through delta)

### 4.3 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`harness-loadbearing-gap-fix` 0.60 1st pt) + progress.md final
- [x] Final gate sweep: mypy **0** · run_all **10/10** (count 24) · full pytest **2648+5skip + N** · Vitest **888** · mockup **51**
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + memory subfile `project_phase57_122_hitl_policy_readside.md` · next-phase-candidates (`AD-HITL-Policy-ReadSide-Potemkin-Phase58` SHIPPED; the spun-off `AD-HITL-Policy-Threshold-Validation` logged) · sprint-workflow matrix `harness-loadbearing-gap-fix` 0.60 1st-point · 17.md HITL/Cat 9 registration if a contract needs single-source
- [x] **Anti-pattern self-check** (retro Q5): AP-4 (per-tenant delta live — drive-through) / AP-1 / AP-2 / AP-3 / AP-6 → 0 violations
- [x] PR (push + open — user authorized the slice); CI → merge on green (gh-verified MERGED before main sync)
