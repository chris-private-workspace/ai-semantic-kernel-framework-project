# IPA Platform 完整目錄審計 + 11 範疇映射

**建立日期**：2026-04-23
**目的**：在決定架構重組前，先全面釐清現有目錄結構與功用，並映射到 agent harness 11 範疇
**驗證**：codebase-researcher 子代理深度掃描

---

## 圖例

| 標記 | 意義 |
|------|------|
| ✅ 生產 | 在主流量運行 |
| 🟡 部分 | 接入但不完整 / 部分流量 |
| ⚠️ PoC | 實驗性，未必接入主流量 |
| ❌ 僵屍 | 代碼存在但不運行 |
| 不屬於 | 不對應 11 範疇（基礎設施 / 業務領域） |

---

## 1. 頂層目錄

| 目錄 | 用途 | 對應範疇 | 狀況 | 建議 |
|------|-----|---------|------|------|
| `backend/` | FastAPI 後端 | 跨範疇 | ✅ 生產 | 保留 |
| `frontend/` | React 18 前端 | 不屬於 | ✅ 生產 | 保留 |
| `docs/` | 設計文件（含 V9 分析） | 不屬於 | ✅ 生產 | 保留 |
| `claudedocs/` | AI 協作執行文件 | 不屬於 | ✅ 生產 | 保留 |
| `claudedocs sample/` | 範本樣本（已被 .graphifyignore 排除） | 不屬於 | ❌ 僵屍 | **移除** |
| `archive/` | 歷史封存 | 不屬於 | ❌ 僵屍 | 維持原狀 |
| `tests/` | 後端測試（少量） | 跨範疇 | 🟡 部分 | **重組**（合併到 backend/tests） |
| `scripts/` | dev.py 等運維腳本 | 不屬於 | ✅ 生產 | 保留 |
| `infra/` + `infrastructure/` + `deploy/` | 部署設定（**3 個重複目錄**） | 不屬於 | 🟡 部分 | **整併為單一** |
| `monitoring/` | 監控設定 | 不屬於 | 🟡 部分 | 保留 |
| `data/` | 資料快取 | 不屬於 | ⚠️ PoC | 維持 |
| `reference/` | MAF/Claude SDK 原始碼參考 | 不屬於 | ✅ 生產 | 保留（已 graphify-ignore） |
| `graphify-out/` | 知識圖譜輸出（52K 節點） | 不屬於 | ✅ 生產 | 保留 |

---

## 2. backend/src/ 一級目錄

| 目錄 | 用途 | 對應範疇 | 狀況 | 建議 |
|------|-----|---------|------|------|
| `api/v1/` | 41 路由模組，591 endpoints | 跨範疇（業務介面層） | ✅ 生產 | 保留 |
| `core/` | logging / observability / performance / sandbox / security | 範疇 8（Error）+ 9（Guardrails） | ✅ 生產 | 保留（未來可拆 guardrails 子層） |
| `domain/` | 21 業務模組（agents / workflows / executions / sessions / prompts / routing / learning / audit…） | 範疇 7（State）+ 5（Prompts 部分） | ✅ 生產 | **重組** — `prompts`、`routing` 應對應到 11 範疇 |
| `infrastructure/` | cache / database / messaging / storage / workers / distributed_lock / checkpoint | 不屬於（基礎設施） | ✅ 生產 | 保留 |
| `middleware/` | FastAPI 中介層 | 不屬於 | ✅ 生產 | 保留 |
| `integrations/` | **21 子模組（最重要，下面詳列）** | 跨範疇 | 混合 | **重組重點區** |

---

## 3. backend/src/integrations/ 詳細映射（**核心重組區**）

### 3.1 agent_framework/ — MAF 包裝層

| 子目錄 | 用途 | 對應範疇 | 狀況 |
|--------|------|---------|------|
| `acl/` | 權限適配 | 範疇 9 | ✅ |
| `assistant/` | Assistant API 整合 | 範疇 1 | 🟡 |
| `builders/` | **30+ 官方 Builder 包裝** | 範疇 11（Subagent Orch） | ✅ 生產 |
| `clients/` | Anthropic + Azure 客戶端 | 範疇 5（Prompt 觸達 LLM） | ✅ 生產 |
| `core/` | workflow / executor / edge / events / approval | 範疇 1 + 7 | ✅ 生產 |
| `memory/` | MAF Memory 整合 | 範疇 3 | ✅ 生產 |
| `multiturn/` | 多輪對話適配 + checkpoint | 範疇 4（Context Mgmt） | ✅ 生產 |
| `tools/` | MAF function tools | 範疇 2 | ✅ 生產 |

### 3.2 claude_sdk/ — Claude Agent SDK 整合（**側翼實驗**）

| 子目錄 | 用途 | 對應範疇 | 狀況 |
|--------|------|---------|------|
| `autonomous/` | 自主執行（planner / verifier / retry / fallback） | 範疇 10 + 8 | ⚠️ PoC（**不在主流量**） |
| `hooks/` | Approval / Audit / RateLimit / Sandbox 鉤鏈 | 範疇 9 | ⚠️ **不在主流量** |
| `hybrid/` | MAF+SDK 同步器 | 範疇 4 | 🟡 部分 |
| `mcp/` | SDK 端 MCP 整合 | 範疇 2 | 🟡 |
| `orchestrator/` | coordinator (522 LOC) | 範疇 1 | ⚠️ PoC |
| `tools/` | SDK 工具註冊 | 範疇 2 | ⚠️ PoC |

### 3.3 orchestration/ — Phase 48 LLM-native（**主流量重點**）

| 子目錄 | 用途 | 對應範疇 | 狀況 |
|--------|------|---------|------|
| `intent_router/` | completeness / llm_classifier / pattern_matcher / semantic_router | 範疇 1 + 5 | ✅ 生產 |
| `dispatch/executors/` | **3 routes**: direct_answer / subagent / team | 範疇 11 | ✅ 生產 |
| `pipeline/steps/` | 8-step pipeline | 範疇 1（但非 loop） | ✅ 生產 |
| `risk_assessor/` | 政策化風險評估（639 LOC） | 範疇 9 | ✅ 生產 |
| `hitl/` + `approval/` | Human-in-the-loop（788 LOC） | 範疇 9 | ✅ 生產 |
| `experts/` | 預定義 agent registry | 範疇 11 | 🟡 部分 |
| `transcript/` | 執行記錄 | 範疇 7 | ✅ 生產 |
| `audit/` | 稽核日誌 | 範疇 9 + 7 | ✅ 生產 |
| `guided_dialog/` | 引導式補資料 | 範疇 5 | ✅ 生產 |
| `resume/` | Checkpoint resume | 範疇 7 | 🟡 接入但少測試 |
| `input_gateway/` + `input/` | 輸入閘道 | 範疇 6（反向） | ✅ 生產 |
| `metrics/` | 指標收集 | 不屬於 | ✅ 生產 |

### 3.4 其他 integrations/

| 子目錄 | 用途 | 對應範疇 | 狀況 | 建議 |
|--------|------|---------|------|------|
| `memory/` | 多層記憶（短/長/共享 + mem0） | 範疇 3 | ✅ 生產 | 保留 |
| `mcp/` | MCP servers（Azure / Filesystem / LDAP / Shell / SSH） | 範疇 2 | ✅ 生產 | 保留 |
| `hybrid/` | MAF+SDK 切換（context / intent / risk） | 範疇 1 | 🟡 部分 | **重組**（被 orchestration 取代，Sprint 181 移除） |
| `swarm/` | Phase 29 Agent Swarm | 範疇 11 | ⚠️ PoC | **整併到 orchestration** |
| `ag_ui/` | AG-UI Protocol（SSE / Events / Handlers） | 不屬於 | ✅ 生產 | 保留 |
| `a2a/` | Agent-to-Agent | 範疇 11 | 🟡 部分 | **整併到 orchestration** |
| `learning/` | 學習回饋 | 範疇 10 | 🟡 部分 | 保留並補強 |
| `llm/` | LLM client 抽象 | 範疇 5 | ✅ 生產 | 保留 |
| `knowledge/` | RAG / KB | 範疇 3（Memory-RAG） | 🟡 部分 | 保留（KB worktree 進行中） |
| `patrol/` | IPA 巡檢業務 | 不屬於（業務） | ✅ 生產 | 保留 |
| `correlation/` | 關聯分析業務 | 不屬於（業務） | ✅ 生產 | 保留 |
| `rootcause/` | 根因分析業務 | 不屬於（業務） | ✅ 生產 | 保留 |
| `audit/` | 稽核業務 | 不屬於（業務） | ✅ 生產 | 保留 |
| `incident/` | 事件管理 | 不屬於（業務） | 🟡 | 維持 |
| `n8n/` | n8n 整合 | 範疇 2 | 🟡 | 維持 |
| `contracts/`, `shared/` | 雜項 | 不屬於 | 🟡 | 維持 |
| `poc/` | 實驗性原型 | 跨範疇 | ⚠️ PoC | **整理**（評估保留 / 淘汰） |

---

## 4. frontend/src/

| 目錄 | 用途 | 狀況 | 建議 |
|------|------|------|------|
| `pages/` | 頁面組件（agents / workflows / dashboard / DevUI） | ✅ 生產 | 保留 |
| `components/` | UI 組件（unified-chat 27+ / agent-swarm 15+ / ag-ui / DevUI 15 / ui shadcn） | ✅ 生產 | 保留 |
| `hooks/` | 17 個 React hooks | ✅ 生產 | 保留 |
| `api/` | Fetch API client（非 Axios） | ✅ 生產 | 保留 |
| `store/` + `stores/` | Zustand 狀態（**2 個重複目錄**） | 🟡 部分 | **合併** |
| `types/`, `utils/`, `lib/`, `test/` | 標準工具 | ✅ 生產 | 保留 |

---

## 5. docs/ 主要分類

| 目錄 | 用途 | 狀況 | 建議 |
|------|------|------|------|
| `01-planning/` | PRD / Epic | ✅ | 保留 |
| `02-architecture/` | 技術架構 | ✅ | 保留 |
| `03-implementation/` | Sprint 規劃 | ✅ | 保留 |
| `07-analysis/` | **V9 分析（權威）+ Claude Code 研究** | ✅ | 保留 |
| `08-development-log/` | PoC1-9 開發日誌 | ✅ | 保留 |
| `09-git-worktree-working-folder/` | 各 worktree 研究文件 | ✅ | 保留 |
| `04-review/`, `04-usage/`, `phase-2/`, `migration/`, `admin-guide/`, `user-guide/` | 部分重複目錄 | 🟡 部分 | **整併** |

---

## 6. claudedocs/ 主要分類

| 目錄 | 用途 | 狀況 | 建議 |
|------|------|------|------|
| `1-planning/` ~ `7-archive/` | 主結構（整齊） | ✅ | 保留 |
| `8-conversation-log/` + `code-review/` + `prompts/` + `session-logs/` + `session-summaries/` + `sprint-reports/` + `testing/` + `uat/` | **多目錄並存** | 🟡 部分 | **整併到 1-7 主結構** |

---

## 7. tests/

| 目錄 | 狀況 | 建議 |
|------|------|------|
| `tests/unit/` | 唯一存在的測試目錄 | 🟡 部分 | **重組**（補上 integration / e2e，或合併到 backend/tests） |

---

## 8. 11 範疇主要落點總表

| 範疇 | 主要散落位置 | 整併狀態 |
|------|-------------|---------|
| **1 Orchestrator Loop** | `orchestration/pipeline`, `orchestration/intent_router`, `claude_sdk/orchestrator`, `hybrid/orchestrator`, `agent_framework/assistant` | **5 處散落，需整併** |
| **2 Tool Layer** | `agent_framework/tools`, `claude_sdk/tools`, `mcp/`, `n8n/` | **4 處散落，統一介面待建** |
| **3 Memory** | `memory/`, `knowledge/`, `agent_framework/memory` | **3 處散落，整併進度中** |
| **4 Context Mgmt** | `agent_framework/multiturn`, `claude_sdk/hybrid` | **2 處，需補強** |
| **5 Prompt Construction** | `domain/prompts`, `llm/`, `orchestration/guided_dialog`, `orchestration/intent_router/llm_classifier` | **4 處散落，無集中構建器** |
| **6 Output Parsing** | `orchestration/input_gateway`（反向） | **缺正向實作** |
| **7 State Mgmt** | `orchestration/transcript`, `orchestration/resume`, `infrastructure/checkpoint`, `agent_framework/checkpoint` | **4 處散落** |
| **8 Error Handling** | `core/observability`, `claude_sdk/autonomous/retry` | **缺集中模組** |
| **9 Guardrails** | `core/security`, `orchestration/hitl`, `orchestration/risk_assessor`, `orchestration/audit`, `claude_sdk/hooks`, `agent_framework/acl` | **6 處散落，最分散** |
| **10 Verification** | `claude_sdk/autonomous/verifier`, `learning/` | **2 處，主流量缺失** |
| **11 Subagent Orch** | `orchestration/dispatch`, `orchestration/experts`, `swarm/`, `a2a/`, `agent_framework/builders` | **5 處散落** |

---

## 9. 三大關鍵發現

### 發現 1：嚴重的「跨目錄散落」問題
**11 個範疇平均散落在 4 個目錄**（最多的 Guardrails 散落在 6 處）。這就是為什麼之前審計給高分而實際對齊度低 — 代碼存在但不集中、互相不知對方存在。

### 發現 2：**3 處重複目錄**
- 根目錄：`infra/` + `infrastructure/` + `deploy/`
- 前端：`store/` + `stores/`
- 文件：`docs/04-review/` + `docs/04-usage/` 等

這些是**歷史演進的遺跡**，需在重組時清理。

### 發現 3：**3 套並存的 orchestrator 實作**
- `orchestration/` （Phase 48 主流量）
- `hybrid/orchestrator*`（被取代但未移除）
- `claude_sdk/orchestrator/`（PoC 不在主流量）

這是 Sprint 181 待清理項目。

---

## 10. 建議重組策略（決策點）

### 選項 A：**激進物理重組**
完全按 11 範疇建立 `backend/src/agent_harness/01_orchestrator_loop/...` 目錄樹，所有相關代碼搬遷到對應範疇。

- ✅ 最清晰
- ❌ 改動巨大，破壞 git 歷史，影響所有 import

### 選項 B：**邏輯重組（推薦）**
保留現有目錄不動，新建 `backend/src/agent_harness/` 作為 **facade 層**，每個範疇下用 `__init__.py` re-export 自原目錄。

- ✅ 不破壞現有代碼
- ✅ 新代碼明確按範疇歸屬
- ✅ 可漸進遷移
- ⚠️ 需嚴格 import 規範

### 選項 C：**僅整併已知重複**
只清理 3 處重複目錄、合併散落的 Guardrails、整併被取代的 hybrid，不做 11 範疇重組。

- ✅ 最低風險
- ❌ 不解決根本問題（11 範疇散落）

---

## 11. 我的建議

**採用選項 B（邏輯重組）+ 選項 C（清理重複）並行**：

1. **立即做（1 sprint）**：
   - 清理 3 處重複目錄（infra / store / docs）
   - 移除 Sprint 181 的 hybrid 殘留
   - 整併 Agent Team 散落

2. **短期做（2 sprint）**：
   - 建立 `backend/src/agent_harness/` facade 層
   - 11 個子目錄各放 README + ABC + re-export
   - 每範疇標記當前 Level / %（27% baseline）

3. **中期做（隨 Phase 49+ 推進）**：
   - 各範疇補強時，新代碼直接放 `agent_harness/` 對應目錄
   - 舊代碼透過 re-export 逐步遷移

4. **長期目標**：
   - Phase 50+ 後評估是否做激進物理重組

---

## 12. 下一步討論議題

1. 你傾向選項 A / B / C 哪一個？
2. 是否同意「先建 facade 層、後物理遷移」漸進策略？
3. `claude_sdk/` 是否要降級為 `reference/` 等級（只保留設計參考，不在主流量）？
4. `swarm/`、`a2a/`、`hybrid/` 是否一次性整併進 `orchestration/`？
5. 業務領域（patrol / correlation / rootcause / audit）是否獨立成 `business_domain/` 目錄？

**這份報告作為架構重組討論的 baseline。請逐項確認後再進入正式重組計畫**。
