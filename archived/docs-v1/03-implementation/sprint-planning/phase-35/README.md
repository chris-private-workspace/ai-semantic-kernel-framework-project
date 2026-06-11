# Phase 35: E2E Assembly A0 — 核心假設驗證

## 概述

Phase 35 是 IPA Platform **E2E Assembly 計劃**的第一個階段，對應 **Phase A0: Core Hypothesis Validation（核心假設驗證）**。

IPA Platform 歷經 29 個 Phase、106 個 Sprint、累計 ~2379 Story Points，已建構 70+ 功能與 280K+ LOC。然而，平台從未端到端跑通一套完整流程。本 Phase 的核心使命是：**用最小投入驗證最關鍵的技術假設 — Orchestrator Agent 能否成功接通並真正使用 LLM 回應用戶。**

本計劃基於三份專家分析報告的共識：必須先做最小驗證環（Minimum Viable Loop），確認核心技術路徑可行，再逐步擴展。Phase 31-34 之前的改善計劃已被本 E2E Assembly 計劃取代。

## 目標

1. **Hybrid Orchestrator Agent 原型** - 建立保留 OrchestratorMediator 架構的 AgentHandler LLM 決策引擎
2. **最短路徑端到端接通** - 從 Chat UI 到 LLM 回應的完整資料流
3. **三層意圖路由啟用** - 至少 L1 PatternMatcher + L3 LLMClassifier 真正工作
4. **零 Mock 驗證** - 全程使用真實 Azure OpenAI API，不使用任何模擬
5. **安全前提修復** - 修復 C-07 SQL Injection 問題作為端到端接通的安全基礎

## 前置條件

- ✅ Phase 29 完成 (Agent Swarm 可視化介面)
- ✅ MAF RC4 升級完成 + V8.1 分析報告更新
- ✅ E2E Blueprint 三方專家分析完成
- ⏸️ Phase 31-34 計劃被本 E2E Assembly 計劃取代

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 107](./sprint-107-plan.md) | Orchestrator Agent 原型 | ~8 點 | ✅ 完成 |
| [Sprint 108](./sprint-108-plan.md) | 最短路徑端到端接通 | ~7 點 | ✅ 完成 |

**總計**: ~15 Story Points (2 Sprints)
**預估時程**: 1.5 週

## 架構概覽

```
┌──────────────────────────────────────────────────────────────────────────────┐
│              Phase 35: E2E Assembly A0 — 核心假設驗證架構                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        Frontend (React 18)                             │  │
│  │                                                                        │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │                    Chat UI (unified-chat)                     │    │  │
│  │   │   用戶輸入:「ETL Pipeline 今天跑失敗了」                        │    │  │
│  │   └──────────────────────┬───────────────────────────────────────┘    │  │
│  │                          │ HTTP POST                                   │  │
│  └──────────────────────────┼────────────────────────────────────────────┘  │
│                             ↓                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        Backend (FastAPI)                                │  │
│  │                                                                        │  │
│  │   ┌──────────────────┐                                                │  │
│  │   │  AG-UI Chat      │  /api/v1/ag-ui/chat                           │  │
│  │   │  Endpoint        │  (SSE 串流回應)                                │  │
│  │   └────────┬─────────┘                                                │  │
│  │            │ 斷點 #1 修復                                              │  │
│  │            ↓                                                           │  │
│  │   ┌──────────────────┐                                                │  │
│  │   │  InputGateway    │  輸入驗證 + 安全檢查                            │  │
│  │   │                  │  (C-07 SQL Injection 修復)                      │  │
│  │   └────────┬─────────┘                                                │  │
│  │            │ 斷點 #2 修復                                              │  │
│  │            ↓                                                           │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │              OrchestratorMediator (保留現有架構)                │    │  │
│  │   │                                                                │    │  │
│  │   │   ┌─────────────────────────────────────────────────────┐    │    │  │
│  │   │   │           三層意圖路由 (確定性邏輯)                    │    │    │  │
│  │   │   │                                                      │    │    │  │
│  │   │   │   L1: PatternMatcher ──→ 快速模式匹配               │    │    │  │
│  │   │   │   L2: (本 Phase 略過)                                │    │    │  │
│  │   │   │   L3: LLMClassifier ──→ LLM 語義分類                │    │    │  │
│  │   │   │                                                      │    │    │  │
│  │   │   │   輸出: IntentResult { intent: INCIDENT, ... }       │    │    │  │
│  │   │   └─────────────────────────────────────────────────────┘    │    │  │
│  │   │                          │                                    │    │  │
│  │   │                          ↓                                    │    │  │
│  │   │   ┌─────────────────────────────────────────────────────┐    │    │  │
│  │   │   │           AgentHandler (🆕 新增)                      │    │    │  │
│  │   │   │                                                      │    │    │  │
│  │   │   │   • System Prompt: IT 運維助手 (繁體中文)             │    │    │  │
│  │   │   │   • Function Tools:                                  │    │    │  │
│  │   │   │     - route_intent()    → 意圖路由結果               │    │    │  │
│  │   │   │     - respond_to_user() → 生成回應                   │    │    │  │
│  │   │   │   • FrameworkSelector → 選擇 LLM 供應商              │    │    │  │
│  │   │   └──────────────────────┬──────────────────────────────┘    │    │  │
│  │   │                          │                                    │    │  │
│  │   └──────────────────────────┼────────────────────────────────────┘    │  │
│  │                              ↓                                         │  │
│  │   ┌──────────────────────────────────────────────────────────────┐    │  │
│  │   │              FrameworkSelector                                │    │  │
│  │   │                                                                │    │  │
│  │   │   Azure OpenAI (gpt-4o)  ←──  預設選擇                       │    │  │
│  │   │   Claude (備選)          ←──  供應商靈活性                     │    │  │
│  │   └──────────────────────────────────────────────────────────────┘    │  │
│  │                              │                                         │  │
│  │                              ↓                                         │  │
│  │              LLM 回應 → SSE 串流 → Chat UI 顯示                       │  │
│  │                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    跨模組合約介面 (🆕 新增)                              │  │
│  │                                                                        │  │
│  │   orchestration/ ←──合約──→ hybrid/                                    │  │
│  │                                                                        │  │
│  │   IntentResult    : 意圖分類結果                                       │  │
│  │   AgentRequest    : Agent 處理請求                                     │  │
│  │   AgentResponse   : Agent 處理回應                                     │  │
│  │   OrchestratorConfig : Orchestrator 配置                               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Sprint 詳細規劃

### Sprint 107 (~8 SP): Orchestrator Agent 原型

| # | 任務 | SP | 說明 |
|---|------|----|------|
| 1 | 建立 AgentHandler 類別 | 2 | 在 `integrations/hybrid/` 下新增 AgentHandler，作為 LLM 決策引擎 |
| 2 | 實作 Function Tools | 2 | 定義 `route_intent()` 和 `respond_to_user()` 兩個 function tools |
| 3 | System Prompt 設計 | 1 | 定義 IT 運維助手角色的 system prompt（繁體中文） |
| 4 | 配置 Azure OpenAI 連接 | 1 | 使用真實 API Key，通過 FrameworkSelector 接入 |
| 5 | 三層意圖路由啟用 | 2 | 確保 L1 PatternMatcher + L3 LLMClassifier 真正工作 |

**Sprint 107 交付物**：
- AgentHandler 能接收用戶輸入、調用 LLM、返回結構化回應
- 意圖路由能正確分類至少 3 種意圖（INCIDENT、QUERY、REQUEST）
- 單元測試通過（使用真實 LLM，非 Mock）

### Sprint 108 (~7 SP): 最短路徑端到端接通

| # | 任務 | SP | 說明 |
|---|------|----|------|
| 1 | 修復斷點 #1: AG-UI → InputGateway | 2 | 接通 AG-UI chat endpoint 到 InputGateway 的資料流 |
| 2 | 修復斷點 #2: InputGateway → Mediator | 2 | 接通 InputGateway 到 OrchestratorMediator 的資料流 |
| 3 | 定義跨模組合約介面 | 1 | 定義 `orchestration/` 與 `hybrid/` 之間的合約型別 |
| 4 | 修復 C-07 SQL Injection | 1 | 安全前提：修復已知的 SQL injection 風險 |
| 5 | 端到端整合測試 + 演示 | 1 | 完整流程演示與驗證 |

**Sprint 108 交付物**：
- 完整端到端流程：Chat UI → AG-UI → InputGateway → Mediator → AgentHandler → LLM → 回應
- 跨模組合約介面定義完成
- C-07 安全漏洞修復
- 端到端演示影片/截圖

## 關鍵架構決策

| # | 決策 | 理由 |
|---|------|------|
| AD-1 | Orchestrator 採用 Hybrid 方案（保留 Mediator + 新增 AgentHandler） | 不是純 ClaudeAgent，保留現有確定性邏輯的投資，同時引入 LLM 能力 |
| AD-2 | AgentHandler 透過 FrameworkSelector 選擇 LLM | 保持供應商靈活性，不綁定單一 LLM 供應商（Azure OpenAI 或 Claude） |
| AD-3 | 確定性邏輯保持在 Mediator Handler 中 | 意圖路由、風險計算等確定性邏輯不使用 LLM function calling，確保可預測性 |
| AD-4 | 最小 Function Tools 設計 | Agent 只需 2 個 tools（route_intent + respond_to_user），避免過度設計 |
| AD-5 | L2 意圖路由本 Phase 略過 | 先驗證 L1 + L3 的核心路徑，L2 在後續 Phase 補齊 |

## 技術要點

### 新增組件

| 組件 | 位置 | 說明 |
|------|------|------|
| AgentHandler | `backend/src/integrations/hybrid/agent_handler.py` | LLM 決策引擎，Mediator 的 Agent 後端 |
| 跨模組合約 | `backend/src/integrations/orchestration/contracts.py` | orchestration/ 與 hybrid/ 之間的介面定義 |
| System Prompt | `backend/src/integrations/hybrid/prompts/orchestrator.py` | IT 運維助手角色定義 |

### 修改組件

| 組件 | 位置 | 修改內容 |
|------|------|----------|
| AG-UI Chat Endpoint | `backend/src/api/v1/ag_ui/` | 修復 → InputGateway 的接通 |
| InputGateway | `backend/src/integrations/orchestration/` | 修復 → OrchestratorMediator 的接通 |
| OrchestratorMediator | `backend/src/integrations/hybrid/` | 整合 AgentHandler |
| IntentRouter | `backend/src/integrations/orchestration/` | 啟用 L1 + L3 路由 |

### 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.100+ | 後端框架 |
| Azure OpenAI | gpt-4o | LLM 供應商 |
| Pydantic | 2.0+ | 數據驗證與合約介面 |
| React | 18.2+ | 前端框架（Chat UI） |
| AG-UI Protocol | - | SSE 串流通訊 |

## 風險與降級策略

| 風險 | 影響 | 機率 | 降級策略 |
|------|------|------|----------|
| Azure OpenAI API Key 無效或配額不足 | 無法驗證核心假設 | 中 | 備選 Claude API；確認配額前先用最小請求測試 |
| 斷點修復牽涉大量重構 | Sprint 延遲 | 中 | 如重構量 > 3 個檔案，先建最小 bypass 路徑驗證可行性 |
| 三層意圖路由複雜度高於預期 | 無法在 Sprint 107 完成 | 低 | 降級為僅 L1 PatternMatcher，L3 延至 Sprint 108 |
| 跨模組合約定義分歧 | 整合困難 | 低 | 先用最小 TypedDict 定義，後續迭代完善 |
| C-07 SQL Injection 修復影響現有功能 | 回歸問題 | 低 | 修復範圍限定於 InputGateway，加入回歸測試 |

## 驗收標準

### 必須達成（Pass/Fail）

- [ ] 一個真實的繁中 IT 問題（如「ETL Pipeline 今天跑失敗了」）→ Orchestrator 正確識別意圖為 INCIDENT → 給出合理的處理建議
- [ ] 端到端延遲 < 5 秒（從用戶送出到收到第一個回應 token）
- [ ] 全程未使用任何 Mock / 模擬 / 假資料
- [ ] C-07 SQL Injection 漏洞已修復並有測試覆蓋

### 品質指標

- [ ] AgentHandler 單元測試覆蓋率 > 80%
- [ ] 跨模組合約介面有完整的 Pydantic 型別定義
- [ ] 意圖路由能正確分類至少 3 種意圖（INCIDENT、QUERY、REQUEST）
- [ ] 端到端流程有整合測試

### 失敗處理

> **如果 Phase 35 核心假設驗證失敗**（Orchestrator 無法成功接通 LLM 並回應），將在 Phase 36 開始前重新評估整個架構方案，考慮是否需要更根本性的架構調整。

## 分析報告參考

| 報告 | 路徑 |
|------|------|
| E2E Blueprint 架構審查 | `claudedocs/6-ai-assistant/analysis/IPA-E2E-Blueprint-Architecture-Review.md` |
| Use Case 計劃驗證報告 | `claudedocs/6-ai-assistant/analysis/usecase-plan-verification-report.md` |
| Business Panel 分析 | `docs/07-analysis/.../ipa-usecase-plan-business-panel-analysis.md` |
| 期望 Use Case 計劃 | `docs/07-analysis/.../ipa-desired-usecase-plan.md` |

---

**Phase 35 開始時間**: 2026-03-19
**預估完成時間**: 1.5 週 (2 Sprints)
**總 Story Points**: ~15 pts
**E2E Assembly 計劃階段**: A0 — 核心假設驗證
