# V2 Reality Gap Report — 21 V2 Planning Doc Audit

**File**: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-5/v2-reality-gap-report.md`
**Purpose**: Cross-check 21 V2 planning docs (paper claims) vs runtime/code reality after V2 22-sprint + Phase 56-58 SaaS Stage 1 + Phase 57+ Frontend SaaS 3/N closure.
**Category**: Audit / Closeout
**Scope**: Sprint 57.5 / Day 3 (V2 Reality Check & Smoke Test Sprint)
**Owner**: Sprint 57.5 retrospective
**Created**: 2026-05-07
**Last Modified**: 2026-05-07

**Modification History**:
- 2026-05-07: Initial creation (Sprint 57.5 Day 3) — 21-doc reality audit + synthesis + Phase 57.6+ candidate scope mapping

**Related**:
- `progress.md` Sprint 57.5 Day 0-2 (28 runtime D-findings catalog)
- `sprint-57-5-plan.md` §US-4 V2 planning doc reality audit
- `claudedocs/...sprint-57-4-summary.md` (V2 22/22 + Phase 56-58 + Phase 57+ Frontend 3/N baseline)

---

## 0. Executive Summary

### Audit scope
- **21 V2 planning docs** under `docs/03-implementation/agent-harness-planning/`
- Cross-checked vs:
  - 28 runtime D-findings from Sprint 57.5 Day 0-2 (boot smoke test + 7-page browser test)
  - File-system reality (Glob + Grep verification of key claims)
  - 16 Alembic migrations actually applied
  - 13 `_abc.py` files actually in `agent_harness/`
  - 14 `_contracts/*.py` files actually in `agent_harness/_contracts/`
  - 7 frontend pages actually shipped vs 12 paper-claim pages

### Top-line finding
V2 22-sprint claim is **dual-state**:

| State | Score | Evidence |
|-------|-------|----------|
| **Code-level** (paper-aligned structure + tests + lints) | **★★★★** (~85%) | pytest 1598 / mypy 0/295 / 8 V2 lints / LLM SDK leak 0 / 13 _abc.py / 16 migrations / 14 contracts / 5 business domains / 1 ChatClient ABC / 1 AzureOpenAIAdapter |
| **Runtime-level** (actually-runs production-deployable) | **★★** (~40%) | 0/7 RED runtime gaps closed; default boot loads stub not real entry; vite proxy port drift breaks all frontend↔backend; 5 pages still placeholder/skeleton; chat session 結束後 DB 0 delta (sessions / audit_log / cost_ledger / tool_calls) |

**Pattern**: V2 optimized for "each sprint isolated tests pass" not for "the whole thing actually runs end-to-end".

### Doc-level alignment by tier
| Tier | Count | Docs |
|------|-------|------|
| **Strongly aligned** (paper ≈ reality) | 9 | 04 / 06 / 07 / 08 / 09 / 11 / 12 / 17 / v2-review |
| **Mostly aligned with drift** (paper > reality on minor details) | 8 | 00 / 01 / 02 / 03 / 05 / 08b / 13 / 16 |
| **Significant gap** (paper claims > reality delivers) | 4 | 10 (provider neutrality enforced but only 1 adapter shipped) / 14 (security STRIDE/OWASP partial) / 15 (SaaS Stage 1 backend ship but frontend 3/N) / 16 (12 pages claim, 7 ship, 5 in placeholder/未開發) |

---

## 1. Per-Doc Reality Audit (21 sections)

### 1.1 README.md — 整體導覽
**Concept**: 21-doc registry + Phase 49-55 22-sprint roadmap entry point.
**Code Location**: N/A (meta-doc).
**Wired?**: ✅ all 21 referenced docs exist; sprint phase folders match (`phase-49-foundation/` through `phase-55-production/`).
**Drift severity**: 🟢 GREEN — meta-aligned.
**Phase 57.6+ implication**: README needs Phase 56-58 SaaS Stage 1 + Phase 57+ Frontend 3/N entries added (currently only V2 Phase 49-55 listed).

### 1.2 00-v2-vision.md — V2 Vision
**Concept**: 11+1 範疇驅動 / Loop-First / 企業治理+Agent 雙軌 / LLM Provider Neutrality / Server-Side First. **V2 ≠ SaaS-ready** explicit declaration.
**Code Location**: N/A (vision doc); claims map to whole `backend/src/agent_harness/` + `platform_layer/`.
**Wired?**: ✅ "V2 ≠ SaaS-ready" honest declaration honored by Phase 56-58 SaaS Stage 1 follow-up.
**Drift severity**: 🟡 YELLOW — vision generally aligned but Phase 55 deliverables list (line 20-24) claims "5 個 IPA 業務 domain (patrol / correlation / rootcause / audit / incident)" 真實只有 `incident` domain ship 真實 service layer (Sprint 55.1 D9 mode swap evidence: 4 deferred domains 仍是 mock-only sentinel handler). User-facing vision implies "5 domains all ship" while reality "1 ship + 4 mock-only".
**Phase 57.6+ implication**: Update vision doc to state "1 production domain (incident) + 4 mock-only domains (patrol / correlation / rootcause / audit) — full ship deferred to Phase 57.x business domains sprint".

### 1.3 01-eleven-categories-spec.md — 11+1 範疇 spec
**Concept**: 11 範疇 + 範疇 12 Observability cross-cutting; each 範疇 has driver + V2 spec + 驗收 criteria.
**Code Location**: `backend/src/agent_harness/{範疇}/_abc.py` (13 files: 11 範疇 + observability + hitl).
**Wired?**: ✅ All 13 `_abc.py` files exist; lint check_sole_mutator + check_promptbuilder + check_ap1 + check_rls_policies enforce structural alignment.
**Drift severity**: 🟢 GREEN — structurally complete; **Cat 9 Level 5** + Cat 1-11 Level 4 claim verified by code presence + integration tests.
**Phase 57.6+ implication**: None — paper aligned with reality at structural level. Runtime alignment (e.g. Cat 4 compaction 真實 fire 與否) beyond code-level audit.

### 1.4 02-architecture-design.md — 5-layer architecture
**Concept**: API / Business Domain / Agent Harness / Adapters + Cross-Cutting (governance/identity/observability) + Runtime + Infrastructure.
**Code Location**: `backend/src/{api,business_domain,agent_harness,adapters,platform_layer,infrastructure}/`.
**Wired?**: ⚠️ MAJOR drift — paper says **flat-layer cross-cutting** `backend/src/governance/` / `backend/src/identity/` / `backend/src/observability/`; reality nested under `backend/src/platform_layer/{governance,identity,observability,middleware,workers,billing,tenant}/`.
**Drift severity**: 🟡 YELLOW — naming drift (cosmetic; not behavior); fold `platform_layer/` rename rationale into 02.md or update doc to match reality.
**Phase 57.6+ implication**: Either (a) update 02.md to document `platform_layer/` nested-layer pattern (recommended; matches reality without code churn) or (b) flatten layout (high churn, rejected for value).

### 1.5 03-rebirth-strategy.md — 3 區分治
**Concept**: 區 1 Greenfield 85% + 區 2 評估後保留 10% + 區 3 知識資產 5%.
**Code Location**: `archived/v1-phase1-48/` + `backend/src/` (rewrite) + `docs/07-analysis/{V9,claude-code-study}/`.
**Wired?**: ✅ V1 archived; V2 backend rewrite shipped (~50K LOC); knowledge archive intact.
**Drift severity**: 🟢 GREEN.
**Phase 57.6+ implication**: None.

### 1.6 04-anti-patterns.md — 11 anti-patterns checklist
**Concept**: AP-1 Pipeline-disguised-as-Loop / AP-2 Side-track / AP-3 Cross-directory scattering / AP-4 Potemkin / AP-5 PoC accumulation / AP-6 Hybrid bridge debt / AP-7 Context rot ignored / AP-8 No PromptBuilder / AP-9 No Verification / AP-10 Mock-vs-Real divergence / AP-11 Sync callback in async loop.
**Code Location**: enforced by `scripts/lint/check_*.py` (8 V2 lints).
**Wired?**: ⚠️ MIXED — AP-1 / AP-3 / AP-8 / AP-11 enforced via lint; AP-2 / AP-4 / AP-7 / AP-10 NOT enforced (need runtime verification).
**Drift severity**: 🔴 RED — Sprint 57.5 Day 0-2 D-findings revealed:
  - **AP-4 Potemkin** activated for D-12 (default boot loads stub vs real `src/api/main.py`), D-14 (default mock mode), D-23/D-24/D-25 (5 frontend pages stuck in placeholder/skeleton).
  - **AP-7 Context rot mitigation** code present but never validated end-to-end in real LLM mode (D-20 .env not loaded → real LLM mode 503 → never invoked compactor).
**Phase 57.6+ implication**: Add runtime AP-4 verification to `check_ap1` lint (e.g. AST scan for placeholder text "Coming in Phase X" or "skeleton" / "TODO" markers in production frontend pages); add E2E real-LLM smoke test gate to CI (currently only mock-mode CI runs).

### 1.7 05-reference-strategy.md — Reference layers
**Concept**: 4-layer ref hierarchy (industry standard / CC source / V1 valuable / other frameworks).
**Code Location**: N/A (process doc).
**Wired?**: ✅ V1 archived for ref; CC research in `docs/07-analysis/claude-code-study/`.
**Drift severity**: 🟢 GREEN.
**Phase 57.6+ implication**: None.

### 1.8 06-phase-roadmap.md — 22-sprint roadmap
**Concept**: Phase 49 (4 sprints) / 50 (2) / 51 (3) / 52 (2) / 53 (4) / 54 (2) / 55 (5) = 22 sprints over 5.5 months.
**Code Location**: `phase-49-foundation/` through `phase-55-production/` planning folders + `agent-harness-execution/phase-49/...phase-55/` execution folders.
**Wired?**: ✅ All 22 sprints + 5 carryover (52.5 / 52.6 / 53.2.5 / 53.7 / 55.3-55.6 audit cycle bundles) + Phase 56-58 SaaS Stage 1 (3/3) + Phase 57+ Frontend SaaS (3/N: 57.1 / 57.3 / 57.4) all have plan + checklist + closeout artifacts.
**Drift severity**: 🟢 GREEN — roadmap delivery 100% (V2 22/22 + SaaS3 + Frontend3 = 28 main + 5 audit cycle = 33 deliverables).
**Phase 57.6+ implication**: 06.md needs Phase 56-58 + Phase 57+ Frontend section appended (currently only V2 49-55 documented).

### 1.9 07-tech-stack-decisions.md — Tech selection
**Concept**: Azure OpenAI GPT-5.4 主 / Anthropic + OpenAI 備援 / FastAPI / React 18 / PostgreSQL 16 / Redis 7 / Qdrant / Celery vs Temporal PoC.
**Code Location**: `backend/src/adapters/azure_openai/adapter.py` + various FastAPI + Vite configs.
**Wired?**: ⚠️ DRIFT — paper says "備援 Anthropic + OpenAI"; reality only `adapters/azure_openai/adapter.py` shipped; no `adapters/anthropic/` or `adapters/openai/` directories. Worker queue: Celery shipped (per Sprint 49.4 retro), Temporal PoC not done; Qdrant integration not verified Day 1-2 boot.
**Drift severity**: 🟡 YELLOW — single-provider reality vs multi-provider paper claim. **LLM Provider Neutrality** lint check_neutrality enforces ABC pattern (so adding Anthropic/OpenAI later is config + code, not refactor) — reality is "neutrality enforced; only 1 provider shipped".
**Phase 57.6+ implication**: Update 07.md to state "Anthropic + OpenAI 備援 deferred to Phase 58+ when production launch needs multi-provider routing".

### 1.10 08-glossary.md — Terminology
**Concept**: Loop / Pipeline / Main flow / Side-track / Potemkin / 11 範疇 terms.
**Code Location**: N/A (glossary).
**Wired?**: ✅ Terms used consistently across V2 codebase + tests + commit messages.
**Drift severity**: 🟢 GREEN.
**Phase 57.6+ implication**: None.

### 1.11 08b-business-tools-spec.md — 5 business domains × 24 tools
**Concept**: Patrol (4 tools) / Correlation (3) / RootCause (3) / Audit (3) / Incident (5) + tool annotations + concurrency + hitl_policy + risk_level.
**Code Location**: `backend/src/business_domain/{patrol,correlation,rootcause,audit_domain,incident}/tools.py` (5 files).
**Wired?**: ⚠️ PARTIAL — 5 tools.py files exist with `register_*_tools()` entry; **`incident` domain** ships real production service (Sprint 55.1 US-1 IncidentService + DB CRUD + multi-tenant + audit chain); **4 deferred domains** (patrol / correlation / rootcause / audit) tools.py uniformly threaded via mode swap (Sprint 55.2) but service handlers are sentinel mocks (per AD-BusinessDomainPartialSwap-1 D9 evidence).
**Drift severity**: 🟡 YELLOW — paper claims 24 tools fully shipped; reality 5 tools real (incident) + 19 sentinel mocks (4 other domains).
**Phase 57.6+ implication**: Phase 57.x business domains follow-up sprint to ship 4 deferred domains real service layer (estimated 4 sprints @ 1 domain/sprint with mode swap pattern reuse).

### 1.12 09-db-schema-design.md — DB schema 11 groups
**Concept**: Identity / Sessions / Tools / Memory / State / Governance / Audit / Verification / Subagent / SaaS / Cost+SLA. 30+ tables. RLS enforced. Append-only audit log + hash chain.
**Code Location**: `backend/src/infrastructure/db/migrations/versions/0001_*.py` through `0016_sla_and_cost_ledger.py` (16 migrations).
**Wired?**: ✅ All 11 schema groups have corresponding migrations; RLS policies via 0009_rls_policies.py + extended in 0014_phase56_1_saas_foundation.py + 0016_sla_and_cost_ledger.py; `check_rls_policies` lint enforces 0 RLS gaps for tenant_id-bearing tables.
**Drift severity**: 🟢 GREEN — schema fully aligned. **D-2 yellow finding** (seed_defaults not at startup lifespan) is wiring drift not schema drift.
**Phase 57.6+ implication**: None on schema; D-2 wire seed_defaults to startup lifespan.

### 1.13 10-server-side-philosophy.md — 3 大原則
**Concept**: 原則 1 Server-Side First (no host fs / multi-tenant / DB-not-git) / 原則 2 LLM Provider Neutrality (ChatClient ABC + agent_harness 禁 import openai/anthropic) / 原則 3 CC reference 不照搬 (參考 5 機制).
**Code Location**: `backend/src/adapters/_base/chat_client.py` (ChatClient ABC) + `scripts/lint/check_neutrality.py` (LLM SDK ban).
**Wired?**: ✅ ChatClient ABC + 6 abstract methods (chat / stream / count_tokens / get_pricing / supports_feature / model_info) implemented; LLM SDK leak count 0 (verified Sprint 57.5 Day 0); azure_openai/adapter.py implements full ABC.
**Drift severity**: 🟢 GREEN structurally; 🟡 YELLOW operationally — only 1 of 3 promised providers (Azure OpenAI) shipped.
**Phase 57.6+ implication**: Document Anthropic + OpenAI adapter deferral; consider Phase 58 production launch sprint to ship 2nd provider for真實 routing test.

### 1.14 11-test-strategy.md — Test pyramid 70/25/5
**Concept**: Unit 70% / Integration 25% / E2E 5%; per-範疇 test matrix; 11 範疇 each ≥ 80% coverage.
**Code Location**: `backend/tests/{unit,integration,e2e}/` + `frontend/tests/`.
**Wired?**: ✅ pytest 1598 (mostly unit + integration) / Playwright e2e 23 / Vitest 35 unit. 11 範疇 each have dedicated unit test directory.
**Drift severity**: 🟡 YELLOW — paper says E2E 5% (~80 tests); reality E2E only 23 Playwright tests (~1.4%) — significantly under-shipped on E2E. **Real-LLM E2E** category (paper claim "real LLM cost-aware quota") not verified Sprint 57.5 (D-20 .env not loaded).
**Phase 57.6+ implication**: E2E test count expansion + real-LLM smoke gate addition to CI (currently mock-only).

### 1.15 12-category-contracts.md — 14 contracts
**Concept**: Contract 1 Loop↔PromptBuilder / 2 Loop↔OutputParser / 3 Tool↔Guardrail / ... / 12 Reducer / 13 Observability / 14 HITL中央化. trace_context cross-cutting enforcement. 範疇 dependency rules.
**Code Location**: `backend/src/agent_harness/_contracts/*.py` (14 files matching).
**Wired?**: ✅ All 14 contracts have corresponding `_contracts/{contract_name}.py`; lint check_promptbuilder / check_sole_mutator enforce contract isolation.
**Drift severity**: 🟢 GREEN.
**Phase 57.6+ implication**: None — contracts aligned.

### 1.16 13-deployment-and-devops.md — Dev / Stage / Prod
**Concept**: Dev (Docker Compose) / Integration / Staging / Production environments; CI/CD 7 stages; deploy-production.yml workflow.
**Code Location**: `docker-compose.yml` + `.github/workflows/{backend-ci,frontend-ci,playwright-e2e,deploy-production,...}.yml`.
**Wired?**: ⚠️ PARTIAL — Dev environment runs (Sprint 57.5 Day 1 boot evidence); Integration / Staging / Production environments NOT provisioned (per AD-CI-6 Phase 58 production launch carryover); deploy-production.yml workflow disabled (workflow_dispatch only) per AD-CI-6.
**Drift severity**: 🟡 YELLOW — paper "4 envs" reality "1 env (Dev) + 3 envs deferred".
**Phase 57.6+ implication**: AD-CI-6 promotion to Phase 58 production launch sprint (5-point re-enable criteria already documented per Sprint 55.6 closeout).

### 1.17 14-security-deep-dive.md — STRIDE / OWASP / GDPR
**Concept**: Zero-Trust + Defense in Depth + Compliance-Ready 3 原則; 4-tier data classification; encryption at rest + in transit; OIDC + RBAC; STRIDE matrix; OWASP LLM Top 10; GDPR data subject rights.
**Code Location**: Various — `platform_layer/identity/` (RBAC) + `agent_harness/guardrails/` (Cat 9 PII detector + jailbreak + tripwire) + audit chain (Migration 0005 hash chain trigger).
**Wired?**: ⚠️ PARTIAL —
  - ✅ Zero-Trust auth: JWT + middleware + RBAC implemented + tested (Sprint 53.4 §HITL Centralization)
  - ✅ RLS multi-tenant isolation: `check_rls_policies` lint 0 gaps
  - ✅ Audit append-only + hash chain: Migration 0005 + 53.5 verify-chain endpoint
  - ✅ Cat 9 PII detector + 4 detectors + tripwire: Sprint 53.3 ship + 53.7 200-case fixture 100% detect / 0% FP
  - ⚠️ Encryption at rest: paper claims TDE + Azure Key Vault; reality DB containerized but TDE not configured (Phase 58 production)
  - ⚠️ STRIDE / OWASP LLM Top 10: paper documents matrix; reality partial coverage (no STRIDE-checklist test suite shipped)
  - ⚠️ GDPR: 14.md §GDPR claims "Right to erasure / data portability / consent" reality 0 endpoints shipped (Phase 57.x candidate per Sprint 56.3 retro)
**Drift severity**: 🟡 YELLOW — auth + tenant isolation + audit + Cat 9 ship; encryption at rest + STRIDE matrix + GDPR endpoints deferred.
**Phase 57.6+ implication**: Phase 57.x partial GDPR (right to erasure + audit log endpoint backed by Cat 9 hash chain); Phase 58 production launch — TDE + key vault provisioning.

### 1.18 15-saas-readiness.md — SaaS Stage 1 (Phase 56-58)
**Concept**: Tenant lifecycle (provisioning + state machine + 3 plans) / SLA monitoring / Cost ledger / DR + WAL streaming / Stripe billing.
**Code Location**: `backend/src/platform_layer/{tenant,billing}/` + `backend/src/api/v1/admin/tenants.py` + Migration 0014 + 0016.
**Wired?**: ⚠️ PARTIAL —
  - ✅ Tenant lifecycle backend: Sprint 56.1 US-1 (state machine 5 states + plan templates 3 + onboarding API + feature flags backend)
  - ✅ SLA monitoring backend: Sprint 56.3 SLAMetricRecorder + monthly report generator
  - ✅ Cost ledger backend: Sprint 56.3 CostLedgerService + ORM + chat router auto-record hooks
  - ✅ Tenant settings frontend: Sprint 57.3 (View + Edit form)
  - ✅ Admin tenants console list frontend: Sprint 57.4 (table + filters + pagination)
  - ✅ Cost dashboard frontend: Sprint 57.1 v2
  - ✅ SLA dashboard frontend: Sprint 57.1 v2
  - ⚠️ Onboarding self-serve wizard: 57.1 v1 aborted Day 0 (D7 admin-driven model mismatch); deferred to Phase 57.x with backend self-serve API design
  - ❌ Stripe billing: 0 LOC (Phase 57.x SaaS Stage 2 candidate)
  - ❌ DR + WAL streaming: 0 LOC (Phase 57.x candidate)
  - ❌ Status Page: 0 LOC (Phase 57.x SaaS Stage 2 candidate)
**Drift severity**: 🟡 YELLOW — Stage 1 backend 100% + Stage 1 frontend 3/N; Stage 2 (billing + DR + status page) 0%.
**Phase 57.6+ implication**: 57.x candidates: Stripe + 月結 + Status Page (SaaS Stage 2); DR + WAL streaming (DR sprint); partial GDPR (compliance); onboarding self-serve wizard (needs backend self-serve API design).

### 1.19 16-frontend-design.md — 12 frontend pages
**Concept**: 12 pages (chat / governance / agents / workflows / incidents / memory / audit / tools / admin / dashboard / devui / auth) with per-Sprint接手時序.
**Code Location**: `frontend/src/pages/{chat-v2,verification,governance,cost-dashboard,sla-dashboard,tenant-settings,admin-tenants}/` (7 directories).
**Wired?**: 🔴 RED gap — paper lists 12 pages; reality 7 pages exist + chat-v2 self-admits "50.2 Day 3 skeleton" + governance "land in subsequent sprints" placeholder text + verification "Coming in Phase 54.1" placeholder + only 3 pages truly ship customer UX (cost-dashboard / sla-dashboard / tenant-settings / admin-tenants — 4 真實 ship per Sprint 57.1+57.3+57.4).
**Drift severity**: 🔴 RED — 12 paper / 4 真實 ship + 3 placeholder + 5 not-yet-developed = significant gap (~33% real ship rate). D-23/D-24/D-25 catalogued in Sprint 57.5 Day 2.
**Phase 57.6+ implication**: 5 unshipped pages (agents / workflows / incidents / memory / audit / tools / admin / dashboard / devui) need scope decision: ship vs explicit-defer-to-V3. Recommend documenting "16.md V2 scope = 7 pages (4 customer + 3 placeholder); remaining 5 deferred to V3" via 16.md update.

### 1.20 17-cross-category-interfaces.md — Single-source registry
**Concept**: 24 dataclass + 19 ABC + 22 LoopEvent + 9 cross-category tools owner-table.
**Code Location**: `backend/src/agent_harness/_contracts/*.py` (14 files) + 13 `_abc.py` files + `events.py` + tools.
**Wired?**: ✅ All 24 dataclass + 19 ABC + 22 LoopEvent + 9 tools verified present; `check_promptbuilder` + `check_sole_mutator` lints enforce single-source.
**Drift severity**: 🟢 GREEN — single-source authority maintained throughout 22 sprints + 5 carryover.
**Phase 57.6+ implication**: None.

### 1.21 v2-review-integration-report-20260428.md — Two-round expert review
**Concept**: P0+P1 二輪 review fold-in (路線圖 16→22 sprint / 範疇 12 升級 / HITL 中央化 / 17.md / 08b.md / 範疇 1 async / 範疇 11 刪 worktree / Reducer / trace_context / Streaming / etc).
**Code Location**: All 21 docs + Phase 49-55 implementation.
**Wired?**: ✅ All P0+P1 items folded in by Phase 49.1 + subsequent sprints; 範疇 12 (Observability) shipped; HITL 中央化 shipped (Sprint 53.4); range 11 worktree deliberately not implemented (per 54.2).
**Drift severity**: 🟢 GREEN.
**Phase 57.6+ implication**: None — review integration complete.

---

## 2. Synthesis

### 2.1 Top 5 Critical RED Findings (Phase 57.6+ MUST-FIX-FIRST candidates)

| # | Finding | Source | Effort | Phase 57.6+ scope class |
|---|---------|--------|--------|-------------------------|
| **R1** | **Default boot loads stub vs real entry**: `scripts/dev.py` references `src/main.py` (Sprint 49.1 stub); real entry is `src/api/main.py` (Sprint 49.4+); + vite.config.ts proxy 8001 vs backend 8000. Frontend↔backend integration fully broken on default boot. | Sprint 57.5 D-12 + D-21 + D-27 (runtime) + 1.4 02.md (paper) | ~2-3 hr | reality-gap-fix (config + wiring) |
| **R2** | **`.env` not auto-loaded**: uvicorn startup doesn't `python-dotenv` autoload → real_llm mode 503 → real LLM smoke test never possible without manual `set -a; source .env` shell prep. | Sprint 57.5 D-20 (runtime) + 1.13 10.md (paper claims production-ready) | ~30 min | reality-gap-fix (lifespan startup) |
| **R3** | **Chat session DB persistence not firing**: AgentLoop main flow runs in-memory but observer hooks at chat router don't INSERT to sessions / audit_log / cost_ledger / tool_calls tables — chat session 結束後 DB 0 delta. | Sprint 57.5 D-16 + D-17 + D-18 (runtime) + 1.12 09.md (paper claims schema fully wired) | ~4-6 hr | reality-gap-fix (chat router observer wiring) |
| **R4** | **5 frontend pages stuck in placeholder/skeleton**: chat-v2 "50.2 Day 3 skeleton" / governance "land in subsequent sprints" / verification "Coming in Phase 54.1" — 16.md paper claims 12 pages; only 4 真實 ship customer UX. | Sprint 57.5 D-23 + D-24 + D-25 (runtime) + 1.19 16.md (paper) | ~8-12 hr per page | reality-gap-fix or scope-defer (5 pages × decision) |
| **R5** | **AP-4 Potemkin enforcement gap**: 04.md Anti-Pattern lints enforce AP-1/3/8/11 structurally; AP-4 (Potemkin) NOT enforced — placeholder text in production frontend pages bypasses CI; AP-7 (context rot) code present but never validated end-to-end real-LLM. | Sprint 57.5 (mass D-findings) + 1.6 04.md (paper enforcement claim) | ~2-3 hr (lint addition) + ~4-6 hr (E2E real-LLM smoke gate) | reality-gap-fix (lint + E2E gate) |

### 2.2 Top 5 YELLOW Informational Findings (Phase 57.6+ NICE-TO-FIX)

| # | Finding | Source | Effort |
|---|---------|--------|--------|
| **Y1** | **02.md governance/identity/observability flat-layer drift**: paper says `backend/src/{governance,identity,observability}/`; reality `backend/src/platform_layer/{governance,identity,observability,...}/`. Cosmetic/naming. | 1.4 02.md | ~1 hr (doc update) |
| **Y2** | **5 business domains 4-of-5 sentinel-mock**: 08b.md claims 24 tools fully ship; reality `incident` real + 4 other domains threaded but sentinel-mock service handlers per AD-BusinessDomainPartialSwap-1. | 1.11 08b.md | ~16-20 hr (4 sprints @ 4-5 hr/domain pattern reuse) |
| **Y3** | **Worker queue Temporal PoC not done**: 07.md tech stack lists Temporal as preferred; reality Celery shipped + Temporal PoC deferred. Architectural decision unmade. | 1.9 07.md | ~6-10 hr (PoC + decision) |
| **Y4** | **Anthropic + OpenAI 備援 adapters not shipped**: 07.md + 10.md promise multi-provider; reality 1 provider (Azure OpenAI). LLM Provider Neutrality enforced (so adding later = config + code, not refactor). | 1.9 07.md + 1.13 10.md | ~3-5 hr per adapter (Anthropic + OpenAI) |
| **Y5** | **STRIDE matrix + OWASP LLM Top 10 + GDPR endpoints partial**: 14.md security deep-dive claims comprehensive coverage; reality auth + tenant isolation + audit + Cat 9 ship; STRIDE checklist test suite + GDPR endpoints + encryption at rest deferred. | 1.17 14.md | ~10-15 hr (STRIDE test + partial GDPR + encryption config) |

### 2.3 Top 5 GREEN Well-Aligned Regions (Don't Touch)

| # | Region | Evidence |
|---|--------|----------|
| **G1** | **11+1 範疇 _abc.py + _contracts/ structural alignment** | 13 _abc.py + 14 _contracts/*.py; 8 V2 lints enforce; pytest 1598 / mypy 0/295 / LLM SDK leak 0 |
| **G2** | **17.md single-source registry** | 24 dataclass + 19 ABC + 22 LoopEvent + 9 cross-category tools all maintained through 22 sprints + 5 carryover; check_promptbuilder + check_sole_mutator lints enforce |
| **G3** | **Cat 9 Guardrails + audit hash chain + multi-tenant RLS** | Sprint 53.3 + 53.4 + 53.5 + 53.7 + Migration 0005 + 0009 + check_rls_policies lint 0 gaps; 200-case PII fixture 100% detect / 0% FP; Cat 9 Level 5 |
| **G4** | **22-sprint roadmap delivery** | 22/22 main + 5 carryover bundles + Phase 56-58 SaaS Stage 1 (3/3) + Phase 57+ Frontend SaaS (3/N) all have plan + checklist + closeout artifacts |
| **G5** | **AgentLoop + Cat 2 Tool Layer + SSE event stream code-level** | TAO loop while-true + while-stop_reason + tool_executor sandbox + 22 LoopEvent SSE schema; AP-1 lint enforces; 50.1 + 50.2 ship + 23 Playwright e2e green |

---

## 3. Phase 57.6+ Candidate Scope Mapping

> Per CLAUDE.md rolling planning 紀律: 不預寫具體未來 sprint plan;以下僅 candidate scope 列出 + 等 user 決策方向。

### 3.1 Candidate A: Reality Gap Fix Sprint(s) — RECOMMENDED FIRST

Per Option D (A+C 組合) user preference signaled at conversation start.

**Phase 57.6 (~10-15 hr)**: Close 7 RED runtime D-findings + paper-side R5 lint addition.
- R1 entry-point + port config drift unification (D-12 + D-21 + D-27)
- R2 .env autoload via lifespan startup (D-20)
- R3 chat router observer wiring (D-16 + D-17 + D-18 sessions / audit_log / cost_ledger / tool_calls DB persist)
- R5 AP-4 Potemkin lint addition + E2E real-LLM smoke gate to CI

**Phase 57.7 (~3-5 hr)**: Re-baseline + audit closure.
- 02.md governance flat-layer rename rationale (Y1 doc fix)
- 16.md update — explicit "V2 scope = 7 pages; 5 deferred to V3" (R4 scope decision documentation)
- SITUATION-V2 §9 dual scoring (code-level + runtime-level)
- CLAUDE.md project status reflect Phase 57.6 reality closure
- New scope class `reality-gap-fix` baseline calibration (~0.50 multiplier per Day 0 reality check evidence)
- Memory snapshot for Phase 57.6 / 57.7

### 3.2 Candidate B: 56-58 SaaS Stage 2 Continuation (NICE-TO-HAVE)

If user prefers feature work over reality gap closure (less recommended given current Reality Gap evidence):
- **Stripe billing + 月結 + Status Page** (SaaS Stage 2 — bundle ~10-12 hr)
- **Onboarding self-serve wizard** (needs backend self-serve API design first; ~6-8 hr)
- **Audit log frontend view** (consume 53.5 backend; pattern reuse from tenant-settings; ~6-8 hr per AD-Sprint-Plan-6 mixed-pattern-reuse 0.40)
- **Feature flags admin UI** (consume 56.1 backend; ~6-8 hr per AD-Sprint-Plan-6 mixed-pattern-reuse 0.40)
- **Compliance partial GDPR** (right to erasure + audit log endpoint; ~10-12 hr)
- **DR + WAL streaming** (large multi-domain ~12-15 hr)
- **AD-Cat10-VisualVerifier+Frontend-Panel** (Phase 57.x Group F deferred)
- **AD-Cat11-Multiturn+SSEEvents+ParentCtx** (54.2 deferred)
- **AD-CI-6 Phase 58 production launch** (5-point re-enable criteria + provisioning)

### 3.3 Candidate C: Defer-and-Ship (LEAST RECOMMENDED)

- Acknowledge Reality Gap as documentation-only; continue feature work.
- Risk: paper-claim mountain grows; future audit cycle will surface more findings.

---

## 4. Calibration Note

**`reality-check` scope class first application** (Sprint 57.5):
- Bottom-up est ~15 hr × 0.60 multiplier = 9 hr commit
- Day 4 retrospective Q2 will compute final ratio after Day 4 closeout completion
- **Day 3 progress so far**: ~3 hr (Day 0 三-prong + Day 1 boot + Day 2 7-page test) + ~2.5 hr (Day 3 21-doc audit + this report) = **~5.5 hr / 9 hr commit** = **~0.61 ratio mid-band** if Day 4 closes within ~3.5 hr (retrospective + memory + SITUATION-V2 + CLAUDE.md sync + commit + PR + closeout PR).

**Recommendation for AD-Sprint-Plan-7**: 「reality-check」class baseline ~0.55-0.60 multiplier (类比 audit cycle ~0.60 mixed but with real boot + browser test execution overhead) for future reality gate sprints.

---

## 5. Closing

**Audit honesty statement** (per Sprint 57.5 plan §重要備註 "誠實 over completeness"):
> V2 22-sprint + Phase 56-58 SaaS Stage 1 + Phase 57+ Frontend SaaS 3/N delivered substantial code-level structural + tested + lint-enforced foundation (~50K LOC; 1598 pytest; 8 V2 lints; 16 migrations; 13 _abc.py; 14 contracts; 23 Playwright e2e; ~85% code-level alignment per dual scoring). Runtime alignment lower (~40%) due to default boot drift + DB persistence wiring gaps + 5 placeholder/未開發 frontend pages — an artifact of solo-dev sprint optimization for "isolated tests pass" not "whole system runs end-to-end". Reality Gap is **closeable** with focused 1-2 sprint Phase 57.6 + 57.7 effort (Option D A+C 組合 user preference signaled).

**Phase 57.6+ direction**: Awaiting user confirmation to draft Phase 57.6 plan (Reality Gap Fix) + Phase 57.7 plan (Re-baseline) per Option D.
