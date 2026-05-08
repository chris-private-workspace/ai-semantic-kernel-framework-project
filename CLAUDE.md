# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **2026-04-28 更新**：本專案進入 **V2 重構（Phase 49+）**，不再以 Microsoft Agent Framework 為主架構。V1 內容已歸檔至 `CLAUDE.backup.md`。

---

## ⚠️ 最關鍵閱讀順序（每次 session 必讀）

1. **本檔案**（CLAUDE.md）— 高層導航
2. **`docs/03-implementation/agent-harness-planning/README.md`** — V2 規劃權威入口
3. **`docs/03-implementation/agent-harness-planning/10-server-side-philosophy.md`** — 3 大最高指導原則（必讀）
4. **`docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md`** — Single-source 介面權威表
5. 🆕 **`claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md`** — Phase 57.7-57.9 active reference（識別 Top 10 critical gaps + Adjusted Roadmap + Buy-vs-Build 9 條決策；Phase 58.0+ 進入 Tier 1 後可降為條件性 reference）

> **權威排序**：`agent-harness-planning/` 21 份 V2 文件（20 規劃 + 1 review）> 本 CLAUDE.md > 任何 V1 文件 / 既有代碼。
> 衝突時以 V2 規劃為準。

---

## AI Assistant Notes

- **Project Location**: Windows (`C:\Users\Chris\Downloads\ai-semantic-kernel-framework-project`)
- **Server Startup**: Use `cmd /c` or direct terminal execution, NOT `start /D` or `start /B`

```bash
# Recommended (Windows)
cmd /c "cd /d <project_path>\backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
```

> **注意**：V1 backend / frontend 已封存於 `archived/v1-phase1-48/`（Sprint 49.1 完成）。啟動命令對應新 V2 backend 結構。

---

## Core Vision & Design Philosophy

> **本節定義專案根本方向。所有設計決策、建議、實作必須對齊。**

### Mission

Build enterprise AI agent teams that work like **human professional teams** — 不只是用既有框架，而是設計**業界第一個「企業級治理 + Claude Code 級閉環」混合 agent 平台**。

### Agent Team Design Principles

平台交付的 agent 必須是：
1. **Professional** — 領域專長，不是通用聊天
2. **Planned** — 結構化，不是 ad-hoc
3. **Memory-equipped** — 記得過去互動、決策、上下文
4. **Autonomous** — 自我組織、規劃、執行、重試
5. **Controllable** — 隨時可由人介入
6. **Transparent** — 所有過程與決策可審計
7. **Security-compliant** — 遵循企業合規
8. **Multi-intelligent** — 多專業 agent 協作
9. **Knowledge-aware** — RAG / 企業知識
10. **Action-capable** — 真實工具執行，不只對話

### Development Philosophy

- MAF / Claude SDK / AG-UI / Claude Code 是**靈感與參考**，**不是設計邊界**
- 許多企業需求需要**自研架構**，沒有單一框架完整提供
- **不要**「MAF 已經有 X，用 MAF 的」 — 要問「需要什麼效果」再 co-design
- Hybrid orchestrator（code-enforced steps + LLM routing）是**有意設計**，不是 workaround
- **使用者出構想，AI 助手執行協調** — 一起設計尚未存在的東西

---

## V2 Refactor Status（Phase 49+）

| Attribute | Value |
|-----------|-------|
| **Phase** | **🎉 V2 重構完成 — 22/22 sprint** + **🎉 Phase 56-58 SaaS Stage 1 完成 — 3/3 backend stack** + **🎉 Phase 57+ SaaS Frontend 推進 — 4/N**(57.1 Cost+SLA dashboards / 57.3 Tenant Settings / 57.4 Admin Tenants Console list / 57.7 cost-dashboard AppShell-compliant)|
| **Latest Sprint** | **57.7** ✅ COMPLETE 2026-05-10（IAM Foundation + Frontend Foundation 1/N spike;PR pending squash merge from branch `feature/sprint-57-7-iam-frontend-foundation` 7 commits ahead of main `d485b42d`;7 USs all delivered: US-A1 IAM 4-vendor matrix → **WorkOS chosen** (B2B SCIM + APAC + cost-predictable per-conn $125→$65 volume / Clerk Auth0 Supabase rejected with 3 specific rationale each per AP-2);US-A2 OIDC backend (oidc.py WorkOSOIDCFlow + AsyncWorkOSClient.user_management API + HS256 internal JWT Path 1) + frontend (login + callback skeleton + authService.ts);US-A3 DB-backed RBAC (rbac.py RBACManager.has_role_code SQL JOIN + auth.py hybrid path opt-in via Settings.rbac_db_backed_fallback default OFF preserves 100+ test fixtures;closes Tier 0 #5);US-B1 Frontend foundation install (Tailwind 4 + shadcn/ui + TanStack Query 5 + RHF + Zod + Sonner + react-error-boundary + lucide-react + 12 deps + components.json + index.css shadcn vars + cn() helper);US-B2 AppShell + ThemeProvider + AppErrorBoundary (3 NEW components + main.tsx 4 providers wrap);US-B3 cost-dashboard CostOverview migrate (9 inline style→Tailwind + AppShell wrap + Zustand preserve per surgical D23);US-R1 sessions/tool_calls observer wire (D19 critical: AD-Reality-3a "blocked by missing user_id infra" was wrong — TenantContextMiddleware since 49.3 + get_current_user_id since 52.5 already populate request.state.user_id → single Depends() fix saved ~3-5 hr feared scope;NEW SessionRepository + ToolCallRepository DAOs;chat router 2 observers SAVEPOINT + env flags SESSIONS_CHAT_OBSERVER + TOOL_CALLS_CHAT_OBSERVER;closes AD-Reality-3a + 3b);Day 4 closeout: design note `20-iam-deep-dive.md` 8-Point Quality Gate ≥95% verified ratio + retrospective.md Q1-Q7 + memory snapshot + 4 doc syncs (sprint-workflow.md calibration matrix +1 row `iam-frontend-spike` 0.60 + CLAUDE.md (this) + SITUATION-V2 §9 + 16.md frontend ship 4/N);pytest 1602→**1622** (+20: 7 oidc/auth + 6 repos + 7 RBAC);Vitest 35→**41** (+6 ⏫20% target +5);Playwright 23/23 no regression sentinel;mypy 0/300 strict (+6 source);9/9 V2 lints;LLM SDK leak 0;Vite build 75→132 modules / 209→273 kB JS (+29% under +50% Risk D);**calibration `iam-frontend-spike` HYBRID 0.60 1st app** weighted blend (IAM × 0.60 + Frontend × 0.65 + Reality × 0.50 + closeout × 0.80);bottom-up est ~26-33 hr / committed 18 hr / actual ~16.5 hr → ratio **~0.92 ✅ in [0.85, 1.20] band** at lower edge;KEEP 0.60 baseline per `When to adjust` 3-sprint window rule;25 cumulative D-findings (D1-D25: 9 RED resolved + 12 YELLOW informational + 4 GREEN);AD closures: AD-Reality-3a (sessions row INSERT) + AD-Reality-3b (tool_calls row INSERT) + AD-Plan-5 (constraint-level schema verify Prong 3 first application D8) + Tier 0 #5 (DB-backed RBAC);**13 NEW carryover ADs**: AD-Reality-3c guardrail_audit + 3d verification_audit ~2-3 hr each Phase 58+ / AD-IAM-{SAML, MFA, RefreshToken, SCIM} ~3-8 hr each Phase 58+ / AD-Frontend-{AuthUX, Sentry} Phase 58.2+ / AD-RBAC-FullDBOnly ~5-8 hr (100+ test fixture retrofit) / AD-Frontend-Tsconfig D24 TS6310 ~30 min / AD-Cost-Dashboard-{UseQuery D23, ChildrenTailwind D25} Phase 58.2+ batch / AD-Plan-3-Test-Fixture-Grep meta-rule iteration;**V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged** (Sprint 57.7 advances Phase 57+ Frontend SaaS 3/N → 4/N — cost-dashboard now AppShell-compliant counts as 4th frontend ship — NOT main V2 progress);Phase 57.8+ direction per Q5 retro 5 candidates pending user instruct per rolling planning 紀律: (a) SOC 2 + SBOM Block C+D (EU CRA 2026 Sep deadline) ~12-15 hr / (b) Status Page + APAC Compliance Block E+F ~10-12 hr / (c) Tier 1 IaC + DR drill ~15-20 hr / (d) chat-v2 / governance / verification real ship now that auth working / (e) Frontend Pages 11 batch (Phase 58.2+ User Profile / MFA / Billing / Onboarding wizard))| Previous Sprint **57.6** ✅ COMPLETE 2026-05-08（Reality Gap Fix Sprint + 5 doc updates merged per Decision 4 (b);PR #114 merged main `799ce14e`;5 USs all closed: US-1 entry-point + port drift fix (scripts/dev.py L435 `main:app`→`api.main:app` + `--app-dir src` / scripts/dev_server.py L246 same fix Day 1 NEW finding via grep / vite.config.ts L22 `8001`→`8000` / backend/src/main.py 49.1 stub `git rm` no external imports per pre-removal grep / closes 57.5 D-12+D-21+D-27 + AD-Reality-1) / US-2 dotenv lifespan autoload (api/main.py existing `_lifespan()` ADD `load_dotenv()` first line + `from dotenv import load_dotenv` import per Day 0 D-1.9 plan adjustment NOT new lifespan / requirements.txt ADD `python-dotenv>=1.0,<2.0` / 1 unit test test_main_lifespan.py / closes 57.5 D-20 + AD-Reality-2) / US-3 audit_log observer NARROW SCOPE (Day 2 探勘 critical finding: cost_ledger LLM + tool already wired via Sprint 56.3 + 57.2 closure;sessions/tool_calls BLOCKED by missing user_id JWT extraction infra — Session.user_id NOT NULLABLE FK to users.id + chat router only extracts current_tenant;**AD-Reality-3 split into 5 sub-ADs**: 3-audit_log closed Day 2 (append_audit at LoopCompleted via existing infrastructure/db/audit_helper.py:90 + 3 unit tests + best-effort try/except) + 3a-sessions deferred Phase 57.7+ ~3-5 hr + 3b-tool_calls deferred Phase 57.7+ ~2-3 hr after 3a + 3c-guardrail_audit deferred ~2-3 hr + 3d-verification_audit deferred ~2-3 hr / closes 57.5 D-17 + AD-Reality-3-audit_log) / US-4 16.md V2 Ship Timeline section (4 已 ship table + 3 priority Phase 57.7-57.9 ~10-12 hr each: chat-v2 / governance / verification + 5 deferred Phase 57.10+ + Sprint slot mapping + explicit "NOT V3 defer" 聲明 / closes 57.5 D-22 + R4 + AD-Reality-4-partial + AD-Reality-7) / US-5 NEW V2 lint #9 check_ap4_frontend_placeholder.py + E2E real-LLM workflow (9 forbidden patterns + comment masking JSX block + JS line + JS block + `--exclude` default 3 ship-pending dirs + 2 iterations to address 5 false positives → 9/9 V2 lints green / .github/workflows/e2e-real-llm-smoke.yml workflow_dispatch + cron schedule commented out per AD-CI-6 Phase 58 secrets dependency + cost guard `max_tokens=100` ~$0.005/run × 30/month = <$0.15 negligible / closes 57.5 D-19 + AD-Reality-5);Day 4 closeout 5 doc updates merged: AD-Reality-6 02-architecture-design.md flat-layer drift fold-in + AD-Reality-8 SITUATION-V2 §9 dual scoring format + §11 NEW entry + AD-Reality-9 CLAUDE.md sync (this) + AD-Reality-10 sprint-workflow.md Calibration matrix +2 rows (`reality-gap-fix` 0.50 + `reality-check` 0.85);pytest 1598 → **1602** (+4 = 1 lifespan + 3 audit_log observer);8 V2 lints → **9 V2 lints 9/9 green**;mypy 0/295 unchanged;LLM SDK leak 0;Vitest 35 unchanged (no frontend code change Sprint 57.6);Playwright 23 unchanged;**calibration `reality-gap-fix` 0.50 NEW class 1st app ratio 0.54 below [0.85, 1.20] band by 0.31** → AD-Sprint-Plan-8 propose pending 2-3 sprint validation (potentially adjust to 0.35 if pattern holds);17 cumulative D-findings (11 Day 0 + 1 Day 1 + 3 Day 2 + 3 Day 3);Phase 57.7+ direction per Q5 retrospective 5 candidates: (a) chat-v2 real ship ~10-12 hr / (b) governance real ship ~10-12 hr / (c) verification real ship ~10-12 hr / (d) AD-Reality-3a sessions infra ~3-5 hr / (e) Other Phase 57.x candidate;**V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 + Phase 57+ Frontend SaaS 3/N unchanged** (Sprint 57.6 is reality-gap-fix verification gate per checklist L291-292, NOT main progress)）|
| **Last main-progress Sprint** | **57.4** ✅ COMPLETE 2026-05-07（Admin Tenants Console List Bundle — backend list endpoint + frontend admin-tenants page）|
| **main HEAD** | `799ce14e` (2026-05-08 — Sprint 57.6 merged) — Sprint 57.7 PR pending squash merge from `feature/sprint-57-7-iam-frontend-foundation` (7 commits ahead) |
| **Next Phase** | **Phase 57.7+ candidates (per Sprint 57.6 retrospective Q5; user instruct each sprint scope)**: (a) **chat-v2 real ship** ~10-12 hr (backend complete via 50.2 + Cat 1+2+9+10+12 — replace skeleton with real chat UX wired to chat router SSE + ApprovalCard + verification panel) / (b) **governance real ship** ~10-12 hr (backend complete via 53.5 — replace placeholder with approver queue + audit log frontend) / (c) **verification real ship** ~10-12 hr (backend complete via 54.1+54.2 — replace placeholder with verifier output + correction loop) / (d) **AD-Reality-3a sessions infra** ~3-5 hr (JWT user_id extraction + sessions row INSERT;unblocks 3b tool_calls ~2-3 hr) / (e) **Other Phase 57.x candidate**: Onboarding self-serve / Audit log frontend / Feature flags admin UI / Compliance partial GDPR / DR + WAL streaming / SaaS Stage 2 (Stripe / 月結 / Status Page) / AD-Cat10-VisualVerifier+Frontend-Panel / AD-Cat11-Multiturn+SSEEvents+ParentCtx / AD-CI-6 Phase 58 production launch;Per rolling planning 紀律 — Phase 57.7 plan/checklist 待 user 明確選定 scope 才起草 |
| **Roadmap** | Phase 49-55 V2 ✅，Phase 56-58 SaaS Stage 1 **3/3 ✅ CLOSED**，Phase 57+ SaaS Frontend **4/N opened**(57.1 + 57.3 + 57.4 + 57.7 cost-dashboard AppShell-compliant) |
| **Tech Stack** | FastAPI + React 18 + PostgreSQL + Redis（V1 沿用）|
| **Architecture** | TAO/ReAct loop + 11+1 範疇 全 Level 4（Cat 9 L5）+ LLM Provider 中性（CI-enforced）+ Multi-tenant 3 鐵律 |
| **Branch Protection** | enforce_admins=true / **review_count=0**（solo-dev policy 永久，2026-05-03 Sprint 53.2 起）/ 5 active required CI checks |

詳見 `docs/03-implementation/agent-harness-planning/06-phase-roadmap.md`。

### V2 不是「修補 V1」也不是「全部砍掉」

- ❌ **不是修補 V1**：V1 真實對齊度 27%，11 範疇 8 個處於 Level 0-2
- ❌ **不是全部砍掉**：保留 V9 分析 / CC 30-wave 研究 / V1 教訓 / 部分 infrastructure 設計
- ❌ **也不是「再寫一批新規劃文件」**（2026-05-08 加入）：V2 22/22 完成後，新領域（IAM / SaaS Stage 2 / Public API / SOC 2 / EU CRA / EU AI Act / APAC PDPA）的 doc 必須**先 thin spike → retrospective → extract design note**，禁止因 gap analysis 結果預寫多份新文件（doc-level 同 sprint-level rolling 紀律；前車：21 docs : 22 sprints 1:1 比例下 dual scoring code 85% / runtime 40%）
- ✅ **是 11+1 範疇導向重新出發**

### V2 完成 ≠ SaaS-ready ⚠️

V2（Phase 55）達成「核心能力 + 業務領域 + canary」；SaaS Stage 1（多租戶內部 SaaS / billing / SLA / DR）在 Phase 56-58。
詳見 `agent-harness-planning/00-v2-vision.md`。

---

## V2 11+1 範疇

V2 嚴格按以下範疇組織代碼，**禁止跨範疇雜湊**：

| # | 範疇 | Phase |
|---|------|-------|
| 1 | Orchestrator Layer (TAO/ReAct) | 50.1 |
| 2 | Tool Layer | 51.1 |
| 3 | Memory（雙軸：5 scope × 3 time scale） | 51.2 |
| 4 | Context Mgmt（含 Prompt Caching） | 52.1 |
| 5 | Prompt Construction | 52.2 |
| 6 | Output Parsing | 50.1 |
| 7 | State Mgmt（含 Reducer + transient/durable） | 53.1 |
| 8 | Error Handling | 53.2 |
| 9 | Guardrails & Safety | 53.3 + 53.4 |
| 10 | Verification Loops | 54.1 |
| 11 | Subagent Orchestration（4 模式，**無 worktree**） | 54.2 |
| **12** | **Observability / Tracing**（cross-cutting） | 49.4 滲透所有 |

完整定義見 `agent-harness-planning/01-eleven-categories-spec.md`。

---

## V2 五大核心約束（必守）

### 約束 1：單一範疇歸屬原則
任何代碼必須明確歸屬於 11 範疇之一（或 platform / business_domain / infrastructure / adapters）。

### 約束 2：主流量驗證原則
任何功能必須能在 UnifiedChat-V2 → API → Agent Loop 主流量中驗證。**禁止 Potemkin Feature**。

### 約束 3：LLM Provider Neutrality（中性）⭐⭐⭐
- ❌ `agent_harness/**` 任何檔案禁止 `import openai` / `import anthropic`
- ❌ 工具定義禁止用 OpenAI / Anthropic 原生 schema
- ✅ 全透過 `adapters/_base/` 的 `ChatClient` ABC + 中性 `ToolSpec` + 中性 `Message`
- ✅ CI 強制 lint 檢查
- **驗收**：30 分鐘換 provider 不改代碼

### 約束 4：Anti-Pattern 檢查原則
每個 PR 必須通過 `04-anti-patterns.md` 11 條檢查清單。

### 約束 5：測試優先原則
- 範疇單元測試 ≥ 80%
- 範疇整合測試 ≥ 60%
- 端到端閉環測試 ≥ 1 個關鍵案例

---

## 「Check Existing Before Building」— V2 版

建任何新 infra 前，**權威排序**：

1. **`agent-harness-planning/` 21 份 V2 規劃**（20 規劃 + 1 review；最高權威）
2. **Sprint 49.1+ plan/checklist** — 當前迭代決定
3. **PoC worktrees 驗證模式** — poc-tools / intent-classifier / memory-system / subagent-control / KB enterprise
4. **Phase 48 LLM-native orchestrator + 7 YAML configs**（已落地新基礎）
5. **既有 V2 代碼**（archive 範圍外的部分）

### ⛔ 禁止反模式

- ❌ 「MAF 已經有 X」— MAF 已封存於 `archived/v1-phase1-48/`，V2 不再以 MAF 為核心
- ❌ 翻 `reference/agent-framework/` 找實作 — 該目錄為 MAF upstream 鏡像，僅作歷史參考，禁止用於 V2 設計
- ❌ 擴充 `backend/src/integrations/agent_framework/` — 該目錄已不存在（隨 V1 一併封存到 archived/）
- ❌ **「先寫一批新規劃文件再實作」**（2026-05-08 加入）— Sprint 57.5 reality check 已揭示 V2 21 docs : 22 sprints 1:1 比例下 paper-vs-runtime drift 普遍存在（code 85% / runtime 40%）。新規劃文件**必須**從 1 個 thin vertical spike 的 retrospective extract，禁止因 gap analysis 結果預寫多份新文件（doc-level 同 sprint-level rolling 紀律）。詳見 `claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md` §3 + SITUATION-V2-SESSION-START.md §6.5

---

## V2 規劃文件導航（21 份）

| 文件 | 用途 |
|------|------|
| `agent-harness-planning/README.md` | 整體導覽 |
| `00-v2-vision.md` | V2 願景（含 V2 ≠ SaaS-ready 聲明）|
| `01-eleven-categories-spec.md` | 11 範疇 + 範疇 12 完整定義 |
| `02-architecture-design.md` | 5 層架構 + 範疇 12 cross-cutting |
| `03-rebirth-strategy.md` | 重生策略（3 區分治、archive 處理）|
| `04-anti-patterns.md` | V1 教訓 11 條反模式 |
| `05-reference-strategy.md` | 參考資料策略 |
| `06-phase-roadmap.md` | **22 sprint 路線圖（5.5 個月）** |
| `07-tech-stack-decisions.md` | 技術選型 |
| `08-glossary.md` | 術語表 |
| `08b-business-tools-spec.md` | 業務領域工具 spec（5 domain × 24 工具）|
| `09-db-schema-design.md` | DB Schema |
| `10-server-side-philosophy.md` | ⭐ **3 大最高指導原則（必讀）**|
| `11-test-strategy.md` | 測試策略 |
| `12-category-contracts.md` | 範疇間整合契約 |
| `13-deployment-and-devops.md` | 部署 + CI/CD + Docker + DR |
| `14-security-deep-dive.md` | STRIDE / OWASP / GDPR |
| `15-saas-readiness.md` | SaaS Stage 1 規劃 |
| `16-frontend-design.md` | 前端 12 頁 sprint 對應 |
| `17-cross-category-interfaces.md` | ⭐ **跨範疇接口 single-source registry** |
| `v2-review-integration-report-20260428.md` | 兩輪 expert review 整合報告 |

---

## V1 歷史資產（保留參考）

V1 雖被 V2 取代，但下列資產持續保留作為**設計知識**：

| 資產 | 位置 | 用途 |
|------|------|------|
| V9 Codebase Analysis | `docs/07-analysis/V9/00-index.md` | V1 baseline（Phase 1-44，1028 files） |
| Claude Code Source Study | `docs/07-analysis/claude-code-study/` | V2 設計藍本（30 waves） |
| V8 Analysis | `docs/07-analysis/Overview/full-codebase-analysis/` | 歷史對比 |
| ClaudeDocs | `claudedocs/` | 持續使用（V2 新文件繼續寫入）|

> **使用準則**：V9 是 V1 的真相快照；引用時要標註「V1 baseline」，不能當作 V2 架構描述。

---

## Development Commands

> Sprint 49.1 已完成 backend / frontend 遷移；以下命令對應 V2 結構。

### Unified Dev Environment

```bash
# View status
python scripts/dev.py status

# Start services
python scripts/dev.py start              # All
python scripts/dev.py start backend
python scripts/dev.py start frontend

# Stop / Restart / Logs
python scripts/dev.py stop [service]
python scripts/dev.py restart [service]
python scripts/dev.py logs docker -f
```

### Service Ports

| Service | Port |
|---------|------|
| Backend | 8000 |
| Frontend | 3005 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| RabbitMQ | 5672 / 15672 |

---

## Code Standards

完整規則在 `.claude/rules/`：

| Rule File | Scope |
|-----------|-------|
| `backend-python.md` | Python backend |
| `frontend-react.md` | React/TypeScript |
| `git-workflow.md` | Git commits / branches |
| `code-quality.md` | Black / ESLint / mypy |
| `testing.md` | 測試標準（≥ 80% coverage） |
| `adapters-layer.md` | LLM adapter 設計 + Azure OpenAI 細節（吸收原 azure-openai-api.md + agent-framework.md） |
| `category-boundaries.md` | 11+1 範疇邊界與跨範疇 import 紀律 |
| `llm-provider-neutrality.md` | `agent_harness/**` 禁 import LLM SDK；CI lint |
| `anti-patterns-checklist.md` | 11 條反模式 PR 自檢清單 |
| `multi-tenant-data.md` | tenant_id / RLS / GDPR / PII |
| `observability-instrumentation.md` | 範疇 12 cross-cutting 埋點規範 |
| `sprint-workflow.md` | 5 步 sprint 強制流程 |
| `file-header-convention.md` | File header + Modification History |

> 詳細索引見 [.claude/rules/README.md](.claude/rules/README.md)。

### Quick Commands

```bash
# Backend
cd backend && black . && isort . && flake8 . && mypy . && pytest

# Frontend
cd frontend && npm run lint && npm run build
```

---

## Environment Setup

複製 `.env.example` 到 `.env`。關鍵變數：

```bash
# Database / Redis / RabbitMQ
DB_NAME=ipa_platform
DB_USER=ipa_user
DB_PASSWORD=ipa_password
REDIS_HOST=localhost
RABBITMQ_HOST=localhost

# Azure OpenAI（V2 主供應商）
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional adapters（V2 透過 adapter 層支援）
# ANTHROPIC_API_KEY=<key>
# OPENAI_API_KEY=<key>
```

---

## ClaudeDocs — AI Assistant Execution Docs

`claudedocs/` 是 AI 助手與開發者協作的動態執行紀錄，獨立於 `docs/`。

### Directory Structure

```
claudedocs/
├── 1-planning/          # 整體規劃
├── 2-sprints/           # Sprint 執行
├── 3-progress/          # 進度（daily / weekly / milestone）
├── 4-changes/           # 變更紀錄（bug-fixes / feature-changes）
├── 5-status/            # 狀態報告
├── 6-ai-assistant/      # AI 助手相關（prompts / analysis）
├── 7-archive/           # 歷史封存
├── CLAUDE.md            # 詳細索引
└── README.md            # 快速導覽
```

### AI Assistant Situation Prompts

依當前情境使用對應 prompt 模板：

| Situation | 文件 | 何時使用 |
|-----------|------|---------|
| **SITUATION-1** | `6-ai-assistant/prompts/SITUATION-1-PROJECT-ONBOARDING.md` | 專案初次接觸 |
| **SITUATION-2** | `SITUATION-2-FEATURE-DEV-PREP.md` | 功能開發準備 |
| **SITUATION-3** | `SITUATION-3-FEATURE-ENHANCEMENT.md` | 功能增強或修復 |
| **SITUATION-4** | `SITUATION-4-NEW-FEATURE-DEV.md` | 新功能開發執行 |
| **SITUATION-5** | `SITUATION-5-SAVE-PROGRESS.md` | 儲存進度、結束 session |
| **SITUATION-6** | `SITUATION-6-SERVICE-STARTUP.md` | 服務啟動、環境檢查 |
| **SITUATION-7** | `SITUATION-7-NEW-ENV-SETUP.md` | 新開發環境設置 |

### Change Record Conventions

修 bug 或實作變更時，於 `claudedocs/4-changes/` 建立對應文件：

| Type | Directory | Naming |
|------|-----------|--------|
| Bug Fix | `4-changes/bug-fixes/` | `FIX-XXX-description.md` |
| Feature Change | `4-changes/feature-changes/` | `CHANGE-XXX-description.md` |
| Refactoring | `4-changes/refactoring/` | `REFACTOR-XXX-description.md` |

### Daily Workflow

1. **開工前**：看 `claudedocs/3-progress/daily/` 最新 log
2. **修 bug**：在 `4-changes/bug-fixes/` 建 FIX
3. **功能變更**：在 `4-changes/feature-changes/` 建 CHANGE
4. **下班前**：用 SITUATION-5 儲存進度

---

## Developer Preferences

### Communication
- **Language**: 用戶溝通用繁體中文
- **Documentation**: CLAUDE.md / 設計文件用英文
- **Detail**: 詳細解釋並附理由
- **Confirmation**: 破壞性操作前必問

### Code Style
- **Comments**: 程式碼註解用英文
- **Git Commit**: 功能完成才 commit
- **Testing**: 新功能必須附單元測試

### Behavior Rules
- **Proactive Assistance**: 主動參與開發
- **Ask Before Acting**: 不確定時必先問
- **Deep Error Analysis**: 找根因，不貼膏藥
- **Never Delete Tests**: 不刪測試 / 不關測試 / 不跳測試
- **Never Delete Docs**: 未授權不刪文件
- **Never Delete Checklist Items**: 只能 `[ ]` → `[x]`，不能刪除未勾選項（Phase 42 Sprint 147 違規前車之鑑）
- **Check Existing Before Building**: 建新 infra 前，先查 V2 21 份規劃 + Sprint plan + PoC worktrees（**不是查 MAF/AG-UI/SDK** — 它們已封存於 archived/）

---

## Karpathy Coding Guidelines

> 減少常見 LLM coding 錯誤的行為守則。Source: [Andrej Karpathy](https://x.com/karpathy/status/2015883857489522876)

### 1. Think Before Coding
- 明說假設；不確定就問
- 多種解讀並陳，不要私下選一個
- 有更簡單方案就說；該 push back 就 push back
- 不清楚就停下、命名困惑、發問

### 2. Simplicity First
- 最少代碼解決問題
- 不寫沒被問的功能 / 不為單次使用造抽象 / 不加未要求的「彈性」
- 不為不可能的情境寫 error handling
- 200 行能變 50 行就重寫

### 3. Surgical Changes
- 只動必要的；不順手「改善」相鄰代碼
- 不重構沒壞的東西；配合既有風格即使你會做不同
- 看到無關的 dead code 就提一下，不刪
- 你的改動產生的 orphan 才清；既有的 dead code 不關你事

### 4. Goal-Driven Execution
- 任務轉成可驗證目標：「Add validation」→「寫無效輸入測試 → 通過」
- 多步任務先給簡短 plan：每步 + verify
- 強成功標準才能獨立 loop；弱標準需要不斷澄清

---

## File Header & Modification Convention

> 完整規範：[`.claude/rules/file-header-convention.md`](.claude/rules/file-header-convention.md)

### 三大原則

- ✅ **要寫**：檔案開頭 docstring（Purpose / Category / Created / Modification History）
- ✅ **要寫**：重要區塊開頭的 WHY 說明（含 Alternative considered）
- ❌ **不寫**：行內每行 `# this assigns x to y` 噪音
- ❌ **不寫**：「used by X」「added for Y」git log 已記錄的內容

### Python File Header 速查範本

```python
"""
File: <relative path>
Purpose: <一句話>
Category: <11+1 範疇之一>
Scope: <Sprint XX.Y / Phase ZZ>

Description:
    <2-5 行：做什麼、為何存在、與哪些範疇互動>

Key Components:
    - ClassA: <用途>
    - function_b(): <用途>

Created: YYYY-MM-DD (Sprint XX.Y)
Last Modified: YYYY-MM-DD

Modification History (newest-first):
    - YYYY-MM-DD: Initial creation (Sprint XX.Y) - <reason>

Related:
    - 01-eleven-categories-spec.md §<section>
    - 17-cross-category-interfaces.md Contract <N>
"""
```

> TypeScript / Markdown 範本見獨立 rule 檔。

### 三層級修改對應

| 改動類型 | 範例 | 文件處理 |
|---------|------|---------|
| **Trivial** | typo / format / rename 變數 | git log 即可，**不更新** Modification History |
| **Behavioral** | 修 bug / 新功能 / 重構邏輯 | ✅ 更新 Last Modified + 加 Modification History + 建 `claudedocs/4-changes/FIX-XXX` |
| **Structural** | 拆檔 / 範疇遷移 / 介面變更 | ✅ 上述全做 + 更新 Sprint progress + 視情況更新 17.md |

### 核心禁止

- ❌ 行內歷史註解（git blame 已有）
- ❌ 保留 dead code 註解（直接刪）
- ❌ Commit message 寫「update / fix / changes」（必須具體 type + scope + why）
- ❌ 行為變更跳過 `claudedocs/4-changes/`

> 例外（生成檔 / vendor / 空 `__init__.py` / 測試檔簡化）與完整禁止項見 [`file-header-convention.md`](.claude/rules/file-header-convention.md)。

---

## CRITICAL: Sprint Execution Workflow

> **強制流程。Phase 35-38（Sprint 107-120）違規前車之鑑，永不重蹈。**

每個 sprint 必須按以下順序：

### Step 1: Create Plan File
寫 code 前，建 `docs/03-implementation/agent-harness-planning/phase-XX-*/sprint-XXX-plan.md`：
- User Stories（作為 / 我希望 / 以便）
- Technical specifications
- File change list
- Acceptance criteria

> **🔴 格式一致性鐵律**：起草前必先讀**最近一個 completed sprint 的 plan**（不是 49.1 / 50.1 等舊樣板，是最新 closed 的）作為模板。
> 章節編號 / 章節命名 / Day 結構 / 每 task 細節水平**必須一致**。
> Sprint scope 差異透過**內容**調整（更多 stories / 更多 file），**不是透過結構**調整（多加章節 / 改 Day 數）。
> 例：51.2 plan 9 sections（0-9）→ 52.1 plan 必須也 9 sections + 命名一致；違反 = 用戶矯正成本（前車：52.1 v1→v3 三輪重寫）。

### Step 2: Create Checklist File
建 `phase-XX-*/sprint-XXX-checklist.md`：
- `- [ ]` 列出每個交付項
- 驗證標準
- 連結 plan

> **🔴 格式一致性鐵律**：同 Step 1 — 必讀最近 completed sprint checklist 為模板。
> Day 數預設 5（Day 0-4，與 V2 累計 sprint 一致）；Day 4 含 retro + closeout。
> 每 task 含：bold task 描述 / 3-6 sub-bullets（具體 case / 配置 / DoD）/ Verify command。
> 細節水平：同等 scope sprint，checklist 行數 ±20% 內。

### Step 3: Implement Code
plan + checklist 都有了才開始 code。

### Step 4: Update Checklist
進度推進時，將 `[ ]` 改 `[x]`。**禁止刪除未勾選項**。

### Step 5: Create Progress Doc
建 `docs/03-implementation/agent-harness-execution/sprint-XXX/progress.md`。

### 正確流程
```
Phase README → Sprint Plan → Sprint Checklist → Code → Update Checklist → Progress Doc
```

### 錯誤流程（Phase 35-38 發生過）
```
Phase README → Code → Progress Doc  ❌ 跳過 plan + checklist
```

參考範例：`agent-harness-planning/phase-49-foundation/sprint-49-1-plan.md` + `sprint-49-1-checklist.md`

---

## Important Notes

1. **Target Market**: 台灣 / 香港。技術詞英文，使用者面向繁體中文。
2. **BMAD Methodology**: 沿用 BMad Agile workflow。狀態追蹤於 `docs/bmm-workflow-status.yaml`。
3. **MAF Status**: V1 整合的 Microsoft Agent Framework 已於 Sprint 49.1 完成封存到 `archived/v1-phase1-48/`。V2 不再以 MAF 為核心；如需 multi-agent builder 才有條件保留 adapter。

---

## graphify

This project has a graphify knowledge graph at `graphify-out/`.

### Navigation rules
- 回答架構或代碼問題前，讀 `graphify-out/GRAPH_REPORT.md`（god nodes + community structure）
- 若 `graphify-out/wiki/index.md` 存在，優先用而非讀原始檔案
- 最佳閱讀順序：L1–10（summary）→ L2184–2322（god nodes + surprising connections + hyperedges）。用 Grep 跳到特定 community 在 L2323+

### Confidence handling（CRITICAL）
當前 graph 約 25% EXTRACTED / 75% INFERRED。
- **God Nodes 與 Community structure** — 高信任，可直接用
- **Surprising Connections** — 多為 INFERRED，當作假說，引用前用 Read/Grep 驗證
- **架構理由引用** — 用 `/graphify explain <node>` 確認支撐 edge 是 EXTRACTED（已驗證）還是 INFERRED（LLM 猜的）。若只有 INFERRED 支撐，回答時必須明示

### ⚠️ Scope Control
**`.graphifyignore` 必須存在於專案根**。`graphify update .` 不會記住初次 build 排除哪些目錄；缺少 `.graphifyignore` 會把 `reference/`（2,213 files）、`claudedocs sample/`（217 files）、debug PNG（~124 files）全納入。

驗證 scope：
```bash
python -c "from graphify.detect import detect; from pathlib import Path; r = detect(Path('.')); print(f'{r[\"total_files\"]} files, {r[\"graphifyignore_patterns\"]} ignore patterns')"
# 預期：~3,300 files、30 ignore patterns
```

若 >5,000 files，停下修 `.graphifyignore` 再繼續。

### Maintenance

| Command | When | Cost |
|---------|------|------|
| `graphify update .` | 代碼變更（.py / .ts / .tsx）| Free |
| `/graphify --update` | docs / markdown / PDF / image | Paid (LLM) |
| `/graphify .` | 全重建（罕用） | Paid (LLM) |

預設：每次 code commit 後跑 `graphify update .` — 它用 manifest.json diff，小變更幾乎瞬間完成。

---

## V1 Backup

V1 完整 CLAUDE.md 已保留於 `CLAUDE.backup.md`。如需查閱 V1 架構（MAF + Claude SDK + AG-UI）細節請參考。

---

**Last Updated**: 2026-05-10 (Sprint 57.7 closeout — **IAM Foundation + Frontend Foundation 1/N spike**;PR pending squash merge from `feature/sprint-57-7-iam-frontend-foundation` 7 commits ahead of main `d485b42d`;7 USs all delivered (A1 IAM 4-vendor matrix → WorkOS chosen + 3 specific rejection rationale Clerk/Auth0/Supabase / A2 OIDC backend with real workos.AsyncWorkOSClient.user_management API + HS256 internal JWT Path 1 + frontend login/callback skeleton + DB user upsert via composite (tenant_id, external_id) key per Multi-tenant 鐵律 #2 / A3 DB-backed RBAC RBACManager + auth.py hybrid path opt-in via Settings.rbac_db_backed_fallback default OFF preserves 100+ test fixtures;closes Tier 0 #5 / B1 Frontend foundation install Tailwind 4 + shadcn/ui + TanStack Query 5 + RHF + Zod + Sonner + react-error-boundary + lucide-react + 12 deps + index.css shadcn vars + cn() helper / B2 AppShell + ThemeProvider + AppErrorBoundary 3 NEW components + main.tsx 4 providers wrap / B3 cost-dashboard CostOverview 9 inline style→Tailwind + AppShell wrap + Zustand preserve per surgical D23 / R1 sessions/tool_calls observer wire — D19 critical AD-Reality-3a "blocked by missing user_id infra" was wrong (TenantContextMiddleware since 49.3 + get_current_user_id since 52.5 already populate request.state.user_id) → single Depends() fix saved ~3-5 hr feared scope;NEW SessionRepository + ToolCallRepository DAOs;chat router 2 observers SAVEPOINT + env flags;closes AD-Reality-3a + 3b);Day 4 closeout per checklist 4.1-4.6: design note `20-iam-deep-dive.md` 8-Point Quality Gate ≥95% verified ratio + retrospective.md Q1-Q7 + memory snapshot `project_phase57_7_iam_frontend_foundation.md` + 4 doc syncs (sprint-workflow.md calibration matrix +1 row `iam-frontend-spike` 0.60 + CLAUDE.md (this) + SITUATION-V2 §9 + 16.md frontend ship 4/N);pytest 1602→**1622** (+20: 7 oidc/auth + 6 repos + 7 RBAC);Vitest 35→**41** (+6 ⏫20% target +5);Playwright 23/23 no regression sentinel;mypy 0/300 strict (+6 source);9/9 V2 lints;LLM SDK leak 0;Vite build 75→132 modules / 209→273 kB JS (+29% under +50% Risk D);**calibration `iam-frontend-spike` HYBRID 0.60 1st app NEW class** weighted blend (IAM × 0.60 + Frontend × 0.65 + Reality × 0.50 + closeout × 0.80);bottom-up est ~26-33 hr / committed 18 hr / actual ~16.5 hr → ratio **~0.92 ✅ in [0.85, 1.20] band** at lower edge;KEEP 0.60 baseline per `When to adjust` 3-sprint window rule;1-data-point baseline opens (closes AD-Sprint-Plan-9);25 cumulative D-findings (D1-D25: 9 RED resolved + 12 YELLOW informational + 4 GREEN);AD closures: AD-Reality-3a + 3b + AD-Plan-5 + Tier 0 #5;**13 NEW carryover ADs Phase 57.8+ / 58+**: AD-Reality-3c guardrail_audit + 3d verification_audit ~2-3 hr each / AD-IAM-{SAML, MFA, RefreshToken, SCIM} ~3-8 hr each / AD-Frontend-{AuthUX, Sentry} Phase 58.2+ / AD-RBAC-FullDBOnly ~5-8 hr / AD-Frontend-Tsconfig D24 TS6310 ~30 min / AD-Cost-Dashboard-{UseQuery D23, ChildrenTailwind D25} batch / AD-Plan-3-Test-Fixture-Grep meta-rule;**V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged** (Sprint 57.7 advances Phase 57+ Frontend SaaS 3/N → 4/N — cost-dashboard now AppShell-compliant counts as 4th frontend ship);Phase 57.8+ direction per Q5 retro 5 candidates pending user instruct per rolling planning 紀律: (a) SOC 2 + SBOM Block C+D (EU CRA 2026 Sep deadline) ~12-15 hr / (b) Status Page + APAC Compliance Block E+F ~10-12 hr / (c) Tier 1 IaC + DR drill ~15-20 hr / (d) chat-v2 / governance / verification real ship now that auth working / (e) Frontend Pages 11 batch Phase 58.2+).
> Previous: 2026-05-08 (Sprint 57.6 closeout — **Reality Gap Fix Sprint** + 5 doc updates merged per Decision 4 (b);PR #114 merged main `799ce14e`;5 USs all closed (US-1 entry-point + port drift fix scripts/dev.py L435 `main:app`→`api.main:app` + `--app-dir src` + scripts/dev_server.py L246 same fix Day 1 NEW finding via grep + vite.config.ts L22 `8001`→`8000` + backend/src/main.py 49.1 stub `git rm` no external imports per pre-removal grep / closes 57.5 D-12+D-21+D-27 + AD-Reality-1; US-2 dotenv lifespan autoload api/main.py existing `_lifespan()` ADD `load_dotenv()` first line + `from dotenv import load_dotenv` import per Day 0 D-1.9 plan adjustment NOT new lifespan + requirements.txt ADD `python-dotenv>=1.0,<2.0` + 1 unit test test_main_lifespan.py / closes 57.5 D-20 + AD-Reality-2; US-3 audit_log observer NARROW SCOPE — Day 2 探勘 critical finding cost_ledger LLM + tool already wired via Sprint 56.3 + 57.2 closure;sessions/tool_calls BLOCKED by missing user_id JWT extraction infra Session.user_id NOT NULLABLE FK to users.id + chat router only extracts current_tenant;**AD-Reality-3 split into 5 sub-ADs**: 3-audit_log closed Day 2 append_audit at LoopCompleted via existing infrastructure/db/audit_helper.py:90 + 3 unit tests + best-effort try/except + 3a-sessions deferred Phase 57.7+ ~3-5 hr + 3b-tool_calls deferred ~2-3 hr after 3a + 3c-guardrail_audit deferred ~2-3 hr + 3d-verification_audit deferred ~2-3 hr / closes 57.5 D-17 + AD-Reality-3-audit_log; US-4 16.md V2 Ship Timeline section — 4 已 ship table + 3 priority Phase 57.7-57.9 ~10-12 hr each chat-v2 / governance / verification + 5 deferred Phase 57.10+ + Sprint slot mapping + explicit "NOT V3 defer" 聲明 / closes 57.5 D-22 + R4 + AD-Reality-4-partial + AD-Reality-7; US-5 NEW V2 lint #9 check_ap4_frontend_placeholder.py + E2E real-LLM workflow — 9 forbidden patterns + comment masking JSX block + JS line + JS block + `--exclude` default 3 ship-pending dirs + 2 iterations to address 5 false positives → 9/9 V2 lints green + .github/workflows/e2e-real-llm-smoke.yml workflow_dispatch + cron schedule commented out per AD-CI-6 Phase 58 secrets dependency + cost guard `max_tokens=100` ~$0.005/run × 30/month = <$0.15 negligible / closes 57.5 D-19 + AD-Reality-5);Day 4 closeout 5 doc updates merged per Decision 4 (b): AD-Reality-6 02-architecture-design.md flat-layer drift fold-in + AD-Reality-8 SITUATION-V2 §9 dual scoring format + §11 NEW entry + AD-Reality-9 CLAUDE.md sync (this) + AD-Reality-10 sprint-workflow.md Calibration matrix +2 rows (`reality-gap-fix` 0.50 + `reality-check` 0.85);pytest 1598 → **1602** (+4 = 1 lifespan + 3 audit_log observer);**8 V2 lints → 9 V2 lints 9/9 green** (NEW check_ap4_frontend_placeholder.py 9th lint with comment masking + ship-pending dir exclusion);mypy 0/295 unchanged (no new source modules);LLM SDK leak 0;Vitest 35 unchanged (no frontend code change Sprint 57.6);Playwright 23 unchanged;**calibration `reality-gap-fix` 0.50 NEW class 1st app ratio 0.54 below [0.85, 1.20] band by 0.31** → AD-Sprint-Plan-8 (NEW) propose pending 2-3 sprint validation (potentially adjust to 0.35 if pattern holds — 1-data-point baseline insufficient for adjustment per `When to adjust` rule);17 cumulative D-findings (11 Day 0 + 1 Day 1 + 3 Day 2 + 3 Day 3);**5 NEW deferred ADs Phase 57.7+**: AD-Reality-3a sessions infra ~3-5 hr (JWT user_id extraction + sessions row INSERT) + AD-Reality-3b tool_calls ~2-3 hr after 3a + AD-Reality-3c guardrail_audit ~2-3 hr + AD-Reality-3d verification_audit ~2-3 hr + AD-Plan-5 constraint-level schema verify (NOT NULL + FK constraint review) Prong 3 fold-in;Phase 57.7+ direction per Q5 retrospective 5 candidates: (a) chat-v2 real ship ~10-12 hr / (b) governance real ship ~10-12 hr / (c) verification real ship ~10-12 hr / (d) AD-Reality-3a sessions infra ~3-5 hr unblocks 3b / (e) Other Phase 57.x candidate Onboarding self-serve / Audit log frontend / Compliance partial GDPR / DR + WAL streaming / SaaS Stage 2;**V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 + Phase 57+ Frontend SaaS 3/N unchanged** (Sprint 57.6 is reality-gap-fix verification gate per checklist L291-292, NOT main progress);Day 0+1+2+3+4 cumulative ~7-8 hr / ~13-15 hr calibrated budget = ~50-55% used;**Day 0 三-prong full application** (Path 10 checks + Content 7 checks + Schema 4 checks → 11 D-findings catalogued before Day 1) ROI ~10-14× (~30 min Day-0 cost prevented ~5-7 hr Day 1+ rework).)
> Previous: 2026-05-07 (Sprint 57.5 closeout — **V2 Reality Check & Smoke Test Sprint** non-feature reality verification gate (0 source code change);PR #112 merged main `c1139fcc`;first-of-kind sprint type;pivot from Feature Flags Admin UI Day 0 (renamed deferred candidate per rolling planning 紀律);5 USs all closed (US-1 Day 0 三-prong + Path C boot + US-2 Day 1 backend smoke 20 D-findings + US-3 Day 2 frontend Playwright 7-page 8 NEW D-findings = **28 cumulative** (7 RED + 13 YELLOW + 8 GREEN) + US-4 Day 3 21-doc reality audit + **315-line v2-reality-gap-report.md** + US-5 Day 4 closeout **250-line retrospective.md** + memory + sync PR);**0 source code change** (pytest 1598 / mypy 0/295 / 8 V2 lints 8/8 / Vitest 35 / Playwright 23 — all unchanged from 57.4 baseline);**dual scoring framework introduced**: code-level ★★★★ ~85% (paper-aligned structure + tests + lints) vs runtime-level ★★ ~40% (default boot stub vs real entry / vite proxy port drift / chat session DB 0 delta / 5 placeholder pages) — pattern: V2 optimized for "each sprint isolated tests pass" not for "the whole thing actually runs end-to-end" (artifact of solo-dev sprint optimization);21-doc audit alignment 9 strongly aligned (04/06/07/08/09/11/12/17/v2-review) + 8 mostly w/ drift (00/01/02/03/05/08b/13/16) + 4 significant gap (10 provider neutrality enforced 但 1 adapter only / 14 security STRIDE/OWASP partial / 15 SaaS Stage 1 backend ship + frontend 3/N partial / 16 12-page claim vs 4 真實 ship + 3 placeholder + 5 not-developed);28 D-findings (7 RED critical + 13 YELLOW informational + 8 GREEN well-aligned);**calibration `reality-check` NEW scope class 1st application** ratio **~1.04 ✅** in [0.85, 1.20] band (bottom-up est ~15 hr × 0.60 multiplier = 9 hr commit; Day 0-3 ~6.5 hr + Day 4 ~3 hr = ~9.4 hr actual);Day 0 三-prong over-pessimistic prediction (~0.40-0.60 audit-cycle類比) wrong — bottom-up est approximately accurate → **AD-Sprint-Plan-7 (NEW) propose `reality-check` baseline ~0.85 multiplier** (1-data-point baseline; pending 2-3 sprint window evidence);Top 5 RED findings (Phase 57.6+ MUST-FIX-FIRST per gap report §2.1): R1 scripts/dev.py + vite.config.ts + src/main.py drift unification (D-12+21+27) ~2-3 hr / R2 uvicorn .env autoload via lifespan startup (D-20) ~30 min / R3 chat router observer wiring sessions/audit_log/cost_ledger/tool_calls (D-16+17+18) ~4-6 hr / R4 5 placeholder/未開發 frontend pages scope decision per page / R5 AP-4 Potemkin lint extension + E2E real-LLM smoke gate addition to CI ~6-9 hr;**10 NEW carryover ADs** + 1 calibration AD: AD-Reality-1 to AD-Reality-5 (Phase 57.6 Reality Gap Fix Sprint scope ~10-15 hr) + AD-Reality-6 to AD-Reality-10 (Phase 57.7 Re-baseline Sprint scope ~3-5 hr — all doc updates) + AD-Sprint-Plan-7 (calibration class proposal `reality-check` 0.85 baseline);Phase 57.6+ direction per Option D (A+C 組合) user preference signaled at Day 3 start: Phase 57.6 Reality Gap Fix Sprint then Phase 57.7 Re-baseline Sprint then Phase 57.8+ feature work resumption from honest foundation;5 user decision points pending Day 4.5 closeout interaction (Phase 57.6 scope confirm / AD-Reality-4 partial vs full / 5 frontend pages future ship vs V3 defer / Phase 57.7 doc-only scope confirm / calibration baselines reality-gap-fix 0.50 + reality-check 0.85 acceptable);**V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 + Phase 57+ Frontend SaaS 3/N unchanged** (reality check verification gate, NOT main progress))
> Previous: 2026-05-07 (Sprint 57.4 closeout — **Phase 57+ SaaS Frontend 3/N — Admin Tenants Console List Bundle**;PR #110 merged `ca8c43c7`;closes plan-time D1 RED (backend admin tenants.py 缺 GET `""` list endpoint) via Option A pre-emptive bundle;5 USs (US-1 backend list endpoint TenantListItem + TenantListResponse + state/plan/search/limit/offset Query + ORDER BY (created_at DESC, id DESC) + 9 integration tests / US-2 admin-tenants infra types/service/store re-export TenantState+TenantPlan + buildListSearchParams URLSearchParams omit-undefined + setFilter resets offset Zustand + 7 Vitest / US-3 TenantListTable+TenantListFilters 5 Vitest no debounce per AP-6 → AD-AdminTenants-DebouncedSearch deferred / US-4 TenantListPagination+page layout URL query sync deferred per AP-6 → AD-AdminTenants-URL-QuerySync / US-5 App.tsx route + Home Link + 4 Playwright e2e);pytest 1589→**1598** (+9 plan target +6 ⏫150%);mypy 0/295 unchanged (modify existing tenants.py only);8 V2 lints 8/8;LLM SDK leak 0;Vitest 23→**35** (+12 plan target +6 ⏫200%);Playwright e2e 19→**23** (+4);Vite build 69→**75** modules (+6 wire-up post Day 4 App.tsx import) / 203.02→**209.11** kB (+6.09 kB);calibration `mixed` 0.60 mid-band 4th app ratio **0.42** under [0.85, 1.20] band lower edge by 0.43;4-data-point `mixed` window 53.7=1.01 + 56.2=1.17 + 57.3=0.57 + 57.4=0.42 = mean **0.79 ⬇️ below band** — pattern reuse from 57.3 tenant-settings drove 60-70% velocity boost vs greenfield;**AD-Sprint-Plan-6** logged proposing scope-class refinement split `mixed` into `mixed-greenfield` (0.60) vs `mixed-pattern-reuse` (~0.40) per pattern reuse acceleration evidence;**15-sprint cumulative window** in-band 8/15 (53%) further dropped below 60% threshold for second consecutive sprint after 57.3 first dip;8 D-findings cumulative (1 🔴 RED backend gap closed by Option A pre-emptive bundle + 5 🟢 GREEN + 2 🟠 YELLOW including D9 pagination stability fix endpoint adds (created_at DESC, id DESC) + D14 Playwright strict-mode selector fix);2 CI fix commits (D14 black formatting Linux 2 files + D15 flake8 E501 MHist trim per AD-Lint-MHist-Verbosity);**Day 0 三-prong second fully-applied sprint** (Path 8 checks 0 drift + Content 6 checks 1 RED + 5 GREEN + Schema N/A this sprint;ROI ≈ 16-24× — 30 min cost prevented 8-12 hr Day 1+ rework);D1 RED finding plan-time closed (backend admin tenants.py R surface complete: list + per-tenant detail + create + update + onboarding-status + onboarding-step);**3 NEW carryover ADs**: AD-Sprint-Plan-6 (scope-class refinement Sprint 57.5+) + AD-AdminTenants-URL-QuerySync (Phase 57.x or 58 when share-URL real need) + AD-AdminTenants-DebouncedSearch (Phase 58+ when tenant count > 500);Phase 57.5 candidates per Q5 retrospective (Onboarding self-serve wizard 需 backend self-serve API design / Feature flags admin UI / Audit log frontend view / Compliance partial GDPR / DR + WAL streaming / SaaS Stage 2 Stripe + 月結 + Status Page / AD-Cat10-VisualVerifier+Frontend-Panel 55.5 deferred / AD-Cat11-Multiturn+SSEEvents+ParentCtx 54.2 deferred / AD-CI-6 Phase 58 production launch) 待 user approve per rolling planning 紀律)
> Previous: 2026-05-07 (Sprint 57.3 closeout — **Phase 57+ SaaS Frontend 2/N — Tenant Settings Bundle**;PR #108 merged `5c893e5b`;closes Day 0 D1 RED finding (backend admin tenants.py 缺 GET/PUT/PATCH for tenant entity → user-confirmed Option B pivot);5 USs (US-1 GET 6 tests + US-2 PATCH+audit chain 9 tests + US-3 frontend infra + US-4 View+EditForm + US-5 routing + 4 Playwright e2e);pytest 1574→**1589** (+15 ⏫150%);mypy 0/295 unchanged;8 V2 lints 8/8;Vitest 15→**23** (+8 ⏫133%);Playwright 11→**15** (+4);Vite build 63→**69** modules / 196.55→203.02 kB;calibration `mixed` 0.60 mid-band 3rd app ratio **0.57** under band 0.28;3-data-point `mixed` mean **0.92 ✅** in band → KEEP 0.60;**14-sprint window 8/14 (57%)** in-band slipped below 60% threshold first time;13 D-findings (1 RED + 8 GREEN + 4 YELLOW);1 CI fix (D14 flake8 E501);**Day 0 三-prong first fully-applied sprint** ROI ≈ 12-18×;V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged + **Phase 57+ Frontend 1/N → 2/N** ↑)
**Project Start**: 2025-11-14
**Current Phase**: 🎉 **V2 重構完成（22/22）** + 🎉 **Phase 56-58 SaaS Stage 1 完成（3/3 backend stack）** + 🎉 **Phase 57+ SaaS Frontend 推進（4/N opens — cost-dashboard now AppShell-compliant per Sprint 57.7）** + 🔐 **Sprint 57.7 IAM Foundation + Frontend Foundation 1/N spike COMPLETE** — Sprint 57.7 ✅ delivered 7 USs (A1 IAM 4-vendor matrix → WorkOS chosen + 3 specific rejection rationale Clerk/Auth0/Supabase / A2 OIDC backend with workos.AsyncWorkOSClient.user_management API + HS256 internal JWT Path 1 + frontend skeleton + DB user upsert via composite (tenant_id, external_id) Multi-tenant 鐵律 #2 / A3 DB-backed RBAC + hybrid path opt-in default OFF preserves 100+ test fixtures closes Tier 0 #5 / B1 Tailwind 4 + shadcn/ui + TanStack Query 5 + 12 deps install / B2 AppShell + ThemeProvider + AppErrorBoundary 3 NEW components / B3 cost-dashboard CostOverview migrate Tailwind + AppShell wrap surgical D23 / R1 sessions+tool_calls observer wire D19 critical AD-Reality-3a infra "blocked" assumption was wrong — middleware since 49.3 already populated request.state.user_id → single Depends() saved ~3-5 hr feared scope; closes AD-Reality-3a + 3b);Day 4 closeout: design note `20-iam-deep-dive.md` 8-Point Quality Gate ≥95% verified ratio + retrospective.md Q1-Q7 + memory snapshot + 4 doc syncs (sprint-workflow.md calibration matrix +1 row `iam-frontend-spike` 0.60 + CLAUDE.md (this) + SITUATION-V2 §9 + 16.md frontend ship 4/N);pytest 1602→**1622** (+20);Vitest 35→**41** (+6 ⏫20%);Playwright 23/23 no regression;mypy 0/300 strict (+6 source);9/9 V2 lints;LLM SDK leak 0;Vite 75→132 modules / 209→273 kB JS (+29% under +50% Risk D);**calibration `iam-frontend-spike` HYBRID 0.60 1st app NEW class** weighted blend → ratio **~0.92 ✅ in [0.85, 1.20] band** at lower edge;KEEP 0.60 baseline 1-data-point opens (closes AD-Sprint-Plan-9);25 cumulative D-findings;AD closures: AD-Reality-3a + 3b + AD-Plan-5 + Tier 0 #5;**13 NEW carryover ADs Phase 57.8+ / 58+** (3c/3d guardrail+verification observer / IAM SAML+MFA+RefreshToken+SCIM / Frontend AuthUX+Sentry / RBAC FullDBOnly / Tsconfig D24 / Cost-Dashboard UseQuery+ChildrenTailwind / AD-Plan-3-Test-Fixture-Grep meta-rule);**V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged** (Sprint 57.7 advances Phase 57+ Frontend SaaS 3/N → 4/N — cost-dashboard now AppShell-compliant counts as 4th frontend ship);Phase 57.8+ direction per Q5 retro 5 candidates pending user instruct (a SOC 2 + SBOM Block C+D EU CRA 2026 Sep deadline ~12-15 hr / b Status Page + APAC Compliance Block E+F ~10-12 hr / c Tier 1 IaC + DR drill ~15-20 hr / d chat-v2/governance/verification real ship now that auth working / e Frontend Pages 11 batch Phase 58.2+);Previous Sprint 57.6 ✅ delivered 5 USs closing top 5 RED 57.5 reality findings (US-1 entry-point + port drift fix scripts/dev.py + scripts/dev_server.py + vite.config.ts + 49.1 stub removed / US-2 dotenv lifespan autoload api/main.py + python-dotenv dep / US-3 audit_log observer NARROW SCOPE only — sessions/tool_calls/guardrail/verification deferred AD-Reality-3a/b/c/d Phase 57.7+ blocked by missing user_id JWT extraction infra / US-4 16.md V2 Ship Timeline section 4 ship + 3 priority + 5 deferred + NOT V3 defer 聲明 / US-5 NEW V2 lint #9 check_ap4_frontend_placeholder.py + E2E real-LLM smoke workflow); 8 V2 lints → **9 V2 lints 9/9 green**; pytest 1598 → 1602 (+4); calibration `reality-gap-fix` 0.50 NEW class 1st app ratio 0.54 below [0.85, 1.20] band by 0.31 → AD-Sprint-Plan-8 propose pending 2-3 sprint validation; 17 cumulative D-findings; 5 NEW AD deferred Phase 57.7+ (3a/b/c/d + AD-Plan-5); Day 4 closeout 5 doc updates merged per Decision 4 (b) (AD-Reality-6 02.md drift / AD-Reality-8 SITUATION-V2 §9 dual scoring + §11 / AD-Reality-9 CLAUDE.md / AD-Reality-10 sprint-workflow.md calibration matrix +2 rows); V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 + Phase 57+ Frontend SaaS 3/N **unchanged** (reality-gap-fix verification gate per checklist L291-292, NOT main progress); Phase 57.7+ direction per Q5 retro 5 candidates pending user instruct; Previous Sprint 57.5 ✅ delivered first-of-kind reality verification gate (PR #112 `c1139fcc`); non-feature sprint (0 source code change); 28 runtime D-findings (7 RED + 13 YELLOW + 8 GREEN) + 21-doc paper audit + 315-line v2-reality-gap-report.md + 250-line retrospective; **dual scoring framework introduced**: code-level ★★★★ ~85% vs runtime-level ★★ ~40%; **calibration `reality-check` NEW class 1st app ratio ~1.04 ✅ in band** → AD-Sprint-Plan-7 propose 0.85 baseline; Top 5 RED (Phase 57.6+ MUST-FIX-FIRST): R1 entry-point + port drift / R2 .env autoload / R3 chat router DB persist / R4 5 placeholder pages scope decision / R5 AP-4 lint + E2E real-LLM gate; **10 NEW AD-Reality-N + AD-Sprint-Plan-7** carryover; Phase 57.6+ direction per Option D (A+C 組合): Phase 57.6 Reality Gap Fix Sprint ~10-15 hr + Phase 57.7 Re-baseline Sprint ~3-5 hr + Phase 57.8+ feature work resumption; 5 user decision points pending Day 4.5; V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 + Phase 57+ Frontend SaaS 3/N **unchanged** (reality check verification gate, NOT main progress); Previous Sprint 57.4 ✅ delivered Admin Tenants Console List Bundle (PR #110 `ca8c43c7`): closes plan-time D1 RED finding (backend admin tenants.py 缺 GET `""` list endpoint → user-approved Option A pre-emptive bundle 2026-05-07); 5 USs (US-1 Backend GET /admin/tenants list endpoint with TenantListItem 7 fields + TenantListResponse paginated wrapper + state/plan/search/limit/offset Query params + ORDER BY (created_at DESC, id DESC) deterministic pagination + require_admin_platform_role RBAC + 9 integration tests; US-2 Frontend features/admin-tenants/{types,services,store} infra mirroring 57.3 tenant-settings pattern with TenantState+TenantPlan re-exported (no duplicate enum) + buildListSearchParams URLSearchParams omit-undefined helper + setFilter resets offset Zustand pattern + 7 Vitest unit tests; US-3 Frontend TenantListTable with state/plan badges + View button navigate to /tenant-settings/?tenant_id=... + empty state with Reset Filters button + 5-row loading skeleton + TenantListFilters with state/plan dropdowns + search input + Apply/Reset buttons no debounce per AP-6 → AD-AdminTenants-DebouncedSearch deferred to Phase 58+ when tenant count > 500 + 5 Vitest unit tests; US-4 Frontend TenantListPagination with Prev/Next + range indicator + edge-disable logic + pages/admin-tenants/index.tsx layout combining Filters+Table+Pagination + auto-load on mount + error retry UX + URL query sync deferred per AP-6 → AD-AdminTenants-URL-QuerySync to Phase 57.x or 58; US-5 App.tsx route /admin-tenants + Home Link always visible per 57.1 D10 Option C + 4 Playwright e2e (happy path mocked rows + filter state=active + click View navigates to /tenant-settings/{id} + empty state with Reset Filters button)); pytest 1589 → **1598** (+9 plan target +6 ⏫150%); mypy 0/295 source files unchanged (modify existing tenants.py only — no new source files for backend); 8 V2 lints 8/8 green; LLM SDK leak 0; Vitest 23 → **35** (+12 plan target +6 ⏫200%); Playwright e2e 19 → **23** (+4); Vite build 69 → **75** modules (+6 wire-up after Day 4 App.tsx import) / 203.02 → **209.11** kB (+6.09 kB); calibration `mixed` 0.60 mid-band **4th application** ratio **0.42** (5-day actual ~3.5 hr / committed 8.4 hr; under [0.85, 1.20] band lower edge by 0.43); **4-data-point `mixed` window** 53.7=1.01 + 56.2=1.17 + 57.3=0.57 + 57.4=0.42 = mean **0.79 ⬇️ below band** — pattern reuse from 57.3 tenant-settings drove dramatic acceleration (60-70% velocity boost vs greenfield); **AD-Sprint-Plan-6** logged proposing scope-class refinement split `mixed` into `mixed-greenfield` (0.60 retained for novel scope) vs `mixed-pattern-reuse` (~0.40 starting baseline for sprints extending established frontend feature folder); **15-sprint cumulative window** in-band 8/15 (53%) further dropped below 60% threshold for second consecutive sprint after 57.3 first dip; 8 D-findings catalogued (D1 🔴 RED plan-time backend gap closed by Option A pre-emptive bundle + D2-D5 informational + D6 RLS not applicable to tenants table per 56.1 baseline + D7 store pattern reusable + D8 URL query sync deferred + D9 pagination stability fix endpoint adds (created_at DESC, id DESC) secondary sort key + D14 Playwright strict-mode selector fix mid-Day-4 getByText("active") 2 matches → .locator("td span").filter() + getByRole("heading")); 2 CI fix commits (D14 black formatting on Linux runner 2 files + D15 flake8 E501 MHist trim per AD-Lint-MHist-Verbosity char-count guidance); **Day 0 三-prong second fully-applied sprint** (Prong 1 Path 8 checks 0 drift + Prong 2 Content 6 checks 1 RED + 5 GREEN + Prong 3 Schema N/A this sprint but attempt 完成 per fold-in spirit); ROI ≈ 16-24× (~30 min Day-0 cost prevented 8-12 hr Day 1+ rework matching 57.3 first application evidence); D1 RED finding plan-time closed (backend admin tenants.py R surface now complete: GET "" list + GET /{id} per-tenant detail + POST "" create + PATCH /{id} update + GET /{id}/onboarding-status + POST /{id}/onboarding/{step}); **3 NEW carryover ADs**: AD-Sprint-Plan-6 (scope-class refinement target Sprint 57.5+) + AD-AdminTenants-URL-QuerySync (Phase 57.x or 58 when admin team raises actual share-URL request) + AD-AdminTenants-DebouncedSearch (Phase 58+ when tenant count > ~500 in production); Phase 57.5 candidates per Q5 retrospective待 user approve per rolling planning 紀律 (Onboarding self-serve wizard 需 backend self-serve API design / Feature flags admin UI consume 56.1 backend × `mixed-pattern-reuse` ~0.40 fast ROI / Audit log frontend view consume 53.5/53.6 backend × `mixed-pattern-reuse` ~0.40 fast ROI / Compliance partial GDPR medium-backend / DR + WAL streaming large multi-domain / SaaS Stage 2 Stripe + 月結 + Status Page / AD-Cat10-VisualVerifier+Frontend-Panel Phase 57.x Group F / AD-Cat11-Multiturn+SSEEvents+ParentCtx 54.2 deferred / AD-CI-6 Phase 58 production launch needs Azure provisioning): closes Day 0 D1 RED finding (backend admin tenants.py 缺 GET/PUT/PATCH for tenant entity → user-confirmed Option B pivot bundle backend + frontend 2026-05-07); 5 USs (US-1 Backend GET TenantResponse 10 fields + 6 integration tests / US-2 Backend PATCH TenantUpdateRequest extra="forbid" + audit chain entry on actual change + 9 integration tests / US-3 Frontend infra features/tenant-settings/{types,services,store} skeleton mirror cost-dashboard pattern + 5 Vitest / US-4 TenantSettingsView read view with State+Plan badges + TenantSettingsEditForm display_name+meta_data JSON validate + 3 Vitest / US-5 App.tsx /tenant-settings/* route + Home Link + 4 Playwright e2e); pytest 1574 → **1589** (+15 plan target +10 ⏫150%); mypy 0/295 unchanged (modify existing tenants.py only); 8 V2 lints 8/8; LLM SDK leak 0; Vitest 15 → **23** (+8 plan target +6 ⏫133%); Playwright e2e 11 → **15** (+4); Vite build 63 → **69** modules (+6 wire-up) / 196.55 → 203.02 kB; calibration `mixed` 0.60 mid-band **3rd application** ratio **0.57** under [0.85, 1.20] band lower edge by 0.28; 3-data-point `mixed` window 53.7=1.01 + 56.2=1.17 + 57.3=0.57 = mean **0.92 ✅** in band → KEEP 0.60 mid-band per AD-Sprint-Plan-4 matrix discipline; **14-sprint cumulative window 8/14 (57%)** in-band slipped below 60% threshold for first time after 3 consecutive sprints in-band; 13 D-findings cumulative (D1 🔴 RED backend gap closed by Option B pivot + D2-D8 informational + D9 test path 56.x flat convention + D10 TenantState default REQUESTED + D11 append_audit signature + D12 build modules tree-shaken + D13 Playwright API surface + D14 flake8 E501 file header); 1 CI fix commit (Day 4 D14 flake8 E501 file header lines 3/5/49 wrapping); **Day 0 三-prong first fully-applied sprint** (Path 8 checks 0 drift + Content 7 checks 1 RED + 5 GREEN + 2 YELLOW + Schema N/A this sprint); ROI ≈ 12-18× (40 min cost prevented 8-12 hr 57.1 v1-style abort rework); D1 RED finding fully closed (backend admin tenants.py R+U complete: create + read + update + onboarding); Phase 57.x next-sprint candidates per Q5 retrospective (10 candidates: Admin tenant console list view extends 57.3 pattern / Onboarding self-serve wizard 需 backend self-serve API design / Feature flags admin UI / Audit log frontend view / DR + WAL streaming / Compliance partial GDPR / SaaS Stage 2 Stripe + 月結 + Status Page / AD-Cat10-VisualVerifier+Frontend-Panel / AD-Cat11-Multiturn+SSEEvents+ParentCtx / AD-CI-6 Phase 58) 待 user approve per rolling planning 紀律: v1 onboarding wizard plan aborted Day 0 due to D7 backend admin-driven model mismatch (super-admin POST /admin/tenants/{id}/onboarding/{step} 模型 vs plan 假設 self-serve POST /onboarding/start), user redirected Option D dual dashboard bundle 2026-05-06; 5 USs closed (US-1 shared infra + Vitest setup per D11 first frontend test infra / US-2 Cost Dashboard consumes 56.3 cost-summary endpoint with nested 2-level by_type per D9 / US-3 SLA Dashboard with 6 metric cards + violations badge + Standard 99.5% threshold fallback per D10 (frontend has no tenant.plan accessible) / US-4 routing + Home nav + admin gate skipped per D10 Option C / US-5 Playwright e2e + closeout); 4 e2e (2 happy + 2 error) + 15 Vitest unit tests; D20 selector fix (getByText 匹配內層 strong → split assertion); Vitest config via vitest/config defineConfig per D15 fix; calibration ratio 0.85 ✅ (`medium-frontend` 0.65 mid-band 1st app — KEEP 0.65 multiplier 1-data-point baseline opens); 12-sprint window in-band **8/12 (67%)** sustained ≥ 60% threshold for 3rd consecutive sprint; 20 D-findings cumulative (D1-D7 v1 carry-forward + D8-D14 Day 0 兩-prong v2 + D15 vitest config + D16-D17 bonus coverage + D18 SLA tier fallback + D19 Playwright page.route mock + D20 e2e selector); AD-Plan-4-Schema-Grep **folded** to sprint-workflow.md §Step 2.5 Prong 3 formal section (closes 55.6 promotion + 56.3 3rd evidence; +35 lines, 5-row drift class table, ROI evidence sub-table); v1 abort lesson captured retro Q1 (跨域 plan-time grep 應加重 — memory 對 frontend 細節零基礎, 標準 SaaS lens 假設 self-serve 在 enterprise admin-driven 不適用, AD-Plan-3 兩-prong Day 0 catch ROI 顯著 1 hr cost vs Day 2 catch 8-10 hr cost rework); pytest 1557 unchanged (frontend-only sprint); mypy 0/293; 8 V2 lints 8/8; LLM SDK leak 0; Phase 57+ next-sprint candidates (Tenant Settings / Admin tenant console / Onboarding self-serve wizard 需 backend self-serve API design / DR + WAL streaming / Compliance partial GDPR / SaaS Stage 2 Stripe + 月結 + Status Page) 待 user approve per rolling planning 紀律
**main HEAD**: `799ce14e` (Sprint 57.6 Reality Gap Fix Sprint merged via PR #114, 2026-05-08) — Sprint 57.7 PR pending squash merge from `feature/sprint-57-7-iam-frontend-foundation` (7 commits ahead)
**V2 Authority**: `docs/03-implementation/agent-harness-planning/` (21 docs — 20 規劃 + 1 review)
**V1 Reference**: `CLAUDE.backup.md` + `docs/07-analysis/V9/00-index.md`
