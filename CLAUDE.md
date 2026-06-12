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
| **Phase** | V2 22/22 ✅ + SaaS Stage 1 3/3 ✅ + SaaS Frontend ongoing (Phase 57+) |
| **Current Sprint** | Sprint 57.108 (PR-pending) — **UX slice: chat-v2 HITL card real tool/reason + Inspector turn metadata wire — SHIPPED + drive-through ALL legs PASS** (closes `AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire`/ISSUE-5). Additive wire fields only: `approval_requested` +`tool_name`/`reason` (all 5 escalate yield sites; tool site carries `tc.name`) + `llm_response` +token actuals — event count 24 UNCHANGED, codegen regen; chatStore 4 captures with **ZERO component edits** (HITLTurn/InspectorTurn store-driven); `cost`/`tokens.thinking` stay honest "—" by documented design (post-loop cost_ledger). D9 load-bearing: `SpanStarted(TURN)` precedes `TurnStarted` → span linkage lives in the `turn_start` handler. Gate: mypy 0/359 · run_all 10/10 · full pytest 2462+4skip (0 del) · FE Vitest 836 / mockup-fidelity 51==51 · `loop.py` diff = 5 yield kwargs. Drive-through (zero dev-login, real Azure): card shows `python_sandbox` + detector rationale (LLM refused → verifier coached → `subprocess` detour caught live) → Approve resumes; non-tool kind falls back "—" with real reason; Inspector tokens.in 2,301 / tokens.out 75 / trace+span real / duration on TURN span_ended. Detail: `memory/project_phase57_108_chatv2_hitl_inspector_wire.md` + CHANGE-075. Next: `claudedocs/1-planning/next-phase-candidates.md` (C2 per interleave). |
| **Sprint History** | See [`memory/MEMORY.md`](memory/MEMORY.md) §Recent Sprints + per-sprint subfile `memory/project_phase57_XX_*.md` + retrospective.md under `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-XX/` |
| **Pending / Next Phase** | See [`claudedocs/1-planning/next-phase-candidates.md`](claudedocs/1-planning/next-phase-candidates.md) |
| **Roadmap** | Phase 49-55 V2 ✅ / Phase 56-58 SaaS Stage 1 3/3 ✅ / Phase 57+ Frontend ongoing |
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

## Frontend Mockup-Fidelity Hard Constraint（必守）⭐⭐⭐

> 所有 frontend 頁面的 UI / UX 視覺必須**完全跟隨** `reference/design-mockups/`。
> **🔴 2026-05-22 重大修正**：本節原本（2026-05-17 起）規定的「翻譯 mockup 樣式 / Tailwind escape-hatch」方法，正是 Sprint 57.18-57.27 連續 10 個 sprint drift 的**根源**。已驗證的正確方法見下。完整根因 + PoC 證據：`claudedocs/5-status/v2-investigation-20260522/03-mockup-consistency-rootcause.md`。

### 核心方法：mockup 是兩層，處理方式相反

| mockup 的層 | 檔案 | 處理 |
|------------|------|------|
| **視覺層 / CSS** | `reference/design-mockups/styles.css`（oklch，251 class）| ✅ **逐字複製** → `frontend/src/styles-mockup.css`（byte-identical）；**永不翻譯** |
| **組件邏輯層** | `reference/design-mockups/page-*.jsx` | 重寫成 typed `.tsx`（`window` 全域 → hooks、接 API、i18n）|

頁面組件**直接消費 mockup class 名**（`className="card"`），色彩**全程 oklch**。「重寫」**只**套組件邏輯層 —— CSS 是「複製」不是「重寫」。混淆兩層 = 10-sprint drift 根因。

> **詳細 4-layer 同步協定 + 7 鐵律 + DoD**：[`docs/rules-on-demand/frontend-mockup-fidelity.md`](docs/rules-on-demand/frontend-mockup-fidelity.md) —— **每個 frontend sprint 必讀**。

### 唯一視覺真相來源

| 來源 | 角色 |
|------|------|
| **`reference/design-mockups/`** | ⭐ canonical visual source of truth；`styles.css` 逐字複製、`page-*.jsx` 重寫 |
| `design/operator-portal/` | Sprint 57.18 cp 快照；權威性低於 `reference/design-mockups/` |
| `frontend/src/styles-mockup.css` | Layer 2 —— `styles.css` 的 byte-identical 複製（`diff` 必須為空）|

### 禁止項（10-sprint drift 來源）

- ❌ **翻譯 CSS** —— 讀 mockup 樣式再手工拼成 Tailwind utility
- ❌ **oklch→HSL 近似** —— Tailwind v4 原生支援 oklch，轉 HSL 是有損的 unforced error
- ❌ 用 shadcn `Card`/`Badge`/`Button` **預設值**替代 mockup 樣式（shadcn 只作 interaction primitive，不作樣式替代層）
- ❌ 用「production 簡化版」名義裁剪 mockup widget / 改 layout
- ❌ 自創 i18n copy 不對照 mockup `reference/design-mockups/i18n.jsx`
- ❌ 把 mockup 當成不可分割的整體（它是兩層）

### 後端 / 功能差距處理

- 後端尚未支援的 widget → **仍依 mockup 視覺實作**，data 用 fixture；後續 sprint 加 backend API
- 不允許因後端沒有就改 mockup widget layout / 刪 widget

### Mockup-Fidelity DoD（每個 frontend 頁面 task）

1. `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → 必須為空
2. Playwright 截圖 mockup（`python -m http.server`）vs production，1440×900
3. **computed-style 量測**：代表元素 + 版面尺寸逐項對比（drift 偵測在量測層做，非用眼）
4. drift 分類 + parity verdict 記入 progress.md / DRIFT-REPORT.md
5. fundamental drift → **先換方法再重建**，不用會 drift 的方法 redo

### 既有頁面 drift 狀態

57.18-57.27 epic 已重建約 10 頁宣稱 parity（auth / cost / sla / overview），但多為「眼湊 HSL 翻譯」版，仍需依新方法 re-point；其餘 ~25 頁待依新方法重建。詳見 `claudedocs/5-status/v2-investigation-20260522/02-frontend-status.md`。

---

## Drive-Through Acceptance Hard Constraint（必守）⭐⭐⭐

> 本項目的開發**不能只看字面上的數據**。gate 全綠（mypy / pytest / Vitest / lint / mockup-fidelity）只證明「零件對」與「API 會回應」，**不證明「人能真的用」**。
> 任何 user-facing feature 在標 done 前，必須有人**實際開著真 UI + 真後端 + 真 LLM 走完流程**，並比對「實際發生 vs 預期流程」。完整根因 + chat-v2 五個 Potemkin 證據：[`memory/feedback_drive_through_over_paper_metrics.md`](memory/feedback_drive_through_over_paper_metrics.md)。

### 「驗證」有三層，gate 只覆蓋前兩層

| 層級 | 證明的事 | 工具 |
|------|---------|------|
| **Gate 層** | 零件正確 | mypy / pytest / Vitest / lint / mockup byte-identical |
| **Curl/probe 層** | API 會回應 | curl / httpx probe / e2e against API |
| **Drive-Through 層** ⭐ | **整台車能開、體驗符合預期** | 真 UI（Playwright/browser MCP 或人）+ 真後端 + 真 LLM，截圖 + 行為對照 |

「主流量驗證原則」（約束 2）要求的是第 3 層；「**能**驗證」**不等於**「**已**驅動驗證」。

### 禁止項（紙上談兵來源）

- ❌ gate 過了就標「verified / ~X% working」——drive-through 沒做一律寫「未驗證 (gate-only)」
- ❌ 用 curl/probe 通過 API 當「功能能用」
- ❌ 死控件（無 onClick）/ fixture 假資料 / 寫死或誤導標籤 / 結果不渲染——全是 AP-4 Potemkin
- ❌ 後端沒接就用假資料但**不標示** demo（要嘛標 DEMO，要嘛留白，不可假裝真）

### Drive-Through DoD（每個 user-facing feature task）

1. 開真 UI（dev server）+ 真後端 + 真 LLM（非 echo/mock），走完該 feature 主路徑
2. 逐控件確認：可點、有效果、標籤真實、結果真的渲染
3. 截圖 +「實際發生 vs 預期流程」對照記入 progress.md / CHANGE 紀錄
4. 發現 Potemkin（死控件 / 假資料 / 誤導標籤 / 不渲染）→ 修到能用才算 done
5. 強制 gate：見 [`.claude/rules/sprint-workflow.md`](.claude/rules/sprint-workflow.md) §Before Commit Checklist item 8（AD-Drive-Through-Acceptance）

---

## 「Check Existing Before Building」— V2 版

建任何新 infra 前，**權威排序**：

1. **`agent-harness-planning/` 21 份 V2 規劃**（20 規劃 + 1 review；最高權威）
2. **Sprint 49.1+ plan/checklist** — 當前迭代決定
3. **Phase 48 LLM-native orchestrator + 7 YAML configs**（已落地新基礎）
4. **既有 V2 代碼**（archive 範圍外的部分）

> **註（2026-06-07）**：V1 末期的 PoC 驗證 worktrees（poc-tools / intent-classifier / memory-system / subagent-control / KB enterprise）已移除（皆為 pre-V2 / V1 相關）；其驗證的模式已落地 V2（Cat 2 Tool / Cat 3 Memory / Cat 11 Subagent），findings 仍保存於 `docs/07-analysis/poc-agent-team/` 與 `docs/07-analysis/claude-agent-study/`。

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

規則目錄 Hybrid 載入（2026-05-09 起）：

**🔴 Always-loaded（4 條 critical，自動進每個 session）**

| Rule | Scope |
|------|-------|
| `.claude/rules/sprint-workflow.md` | 5 步 sprint 流程 + Day 0 三-prong + calibration matrix |
| `.claude/rules/file-header-convention.md` | File header + MHist 1-line max |
| `.claude/rules/multi-tenant-data.md` | tenant_id 鐵律 + RLS + GDPR / PII |
| `.claude/rules/anti-patterns-checklist.md` | 11 條 PR 自檢 |

**📋 On-demand（9 條，需要時主動 Read `docs/rules-on-demand/X.md`）**

| Rule | Trigger |
|------|---------|
| `category-boundaries.md` | 新建檔案 / 跨範疇 import |
| `llm-provider-neutrality.md` | 動 LLM 呼叫 / 新 adapter |
| `adapters-layer.md` | 修改 `adapters/` |
| `observability-instrumentation.md` | 新增埋點 / Cat 12 |
| `code-quality.md` | mypy strict / 跨平台 lint 問題 |
| `testing.md` | Contract test / multi-tenant test |
| `git-workflow.md` | Commit message / branch naming |
| `backend-python.md` | Python backend 通用約定 |
| `frontend-react.md` | React/TS 通用約定 |

> 完整 trigger 表 + 任務情境配對見 [`.claude/rules/README.md`](.claude/rules/README.md)。

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
- **Confirmation on Destructive Only**: `git push` / `git reset --hard` / `git push --force` / 刪 production code / 改 shared infra / 改 CI/CD pipeline / 發外部訊息（Slack / email / PR comments）/ 上傳第三方 tool 前必問。**NOT destructive**: Write / Edit / Read 在已對齊 scope 內 / TaskCreate / Glob / Grep / Bash read-only 命令 / 創建 plan §File Change List 內預期的新檔。詳見 [`memory/feedback_tool_result_is_not_turn_boundary.md`](memory/feedback_tool_result_is_not_turn_boundary.md)。

### Code Style
- **Comments**: 程式碼註解用英文
- **Git Commit**: 功能完成才 commit
- **Testing**: 新功能必須附單元測試

### Behavior Rules
- **Proactive Assistance**: 主動參與開發
- **Ask Before Acting on STRATEGY**: 範圍模糊 / 多個有效方法 / 用戶意圖不明 / 新 sprint 方向時必先問。**NOT trigger**: tool result return / Write/Edit/Read 在已對齊的 scope 內 / sprint plan 內的下一步 / batch parallel tool calls。Karpathy §1「不清楚就停下」仍適用但限真 ambiguous decision，**不適用** tool chaining within aligned scope。詳見 [`memory/feedback_tool_result_is_not_turn_boundary.md`](memory/feedback_tool_result_is_not_turn_boundary.md)。
- **Deep Error Analysis**: 找根因，不貼膏藥
- **Never Delete Tests**: 不刪測試 / 不關測試 / 不跳測試
- **Never Delete Docs**: 未授權不刪文件
- **Never Delete Checklist Items**: 只能 `[ ]` → `[x]`，不能刪除未勾選項（Phase 42 Sprint 147 違規前車之鑑）
- **Check Existing Before Building**: 建新 infra 前，先查 V2 21 份規劃 + Sprint plan（**不是查 MAF/AG-UI/SDK** — 它們已封存於 archived/；V1 末期 PoC 驗證 worktrees 已於 2026-06-07 移除，模式已落地 V2）

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

## V1 Backup

V1 完整 CLAUDE.md 已保留於 `CLAUDE.backup.md`。如需查閱 V1 架構（MAF + Claude SDK + AG-UI）細節請參考。

---

**Last Updated**: 2026-06-12 (Sprint 57.108 — chat-v2 HITL card real tool/reason + Inspector turn metadata wire SHIPPED, drive-through ALL legs PASS; CHANGE-075); see `memory/` for sprint history
**Project Start**: 2025-11-14
**V2 Authority**: `docs/03-implementation/agent-harness-planning/` (21 docs — 20 規劃 + 1 review)
**V1 Reference**: `CLAUDE.backup.md` + `docs/07-analysis/V9/00-index.md`
