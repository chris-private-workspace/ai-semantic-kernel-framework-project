# Phase 44: Magentic Orchestrator Agent — 多模型動態選擇 + Manager 升級

## 概述

Phase 42-43 完成了 E2E Pipeline Deep Integration 和 Swarm Core Engine，
但 MagenticBuilderAdapter 的 Manager Agent 仍然是 `StandardMagenticManager()` 預設配置，
無法根據任務風險和複雜度動態選擇最佳模型。本 Phase 的目標是實現
**ManagerModelRegistry + ManagerModelSelector 雙層架構**，支持 Anthropic 和 Azure OpenAI
多模型 YAML 零代碼切換，並修復 `build()` 方法正確轉發 manager 配置到官方 MagenticBuilder API。

> **Status**: 📋 規劃中 — 2 Sprints (151-152), ~16 SP

## 核心問題（4 個關鍵差距）

| # | 差距 | 現狀 | 目標 |
|---|------|------|------|
| 1 | **Manager 模型不可配置** | `StandardMagenticManager()` 無參數預設 | YAML 配置 + 按風險自動選擇 Opus/Sonnet/Haiku/GPT |
| 2 | **只有 Azure OpenAI** | `LLMServiceFactory` 只支援 azure/mock | 新增 Anthropic provider（AnthropicChatClient） |
| 3 | **build() 未傳 manager** | `MagenticBuilder(participants=...).build()` 跳過 manager 配置 | 構造時傳入 `manager_agent=` 參數（PoC 已驗證） |
| 4 | **風險等級未傳到 Builder** | FrameworkSelector 的 routing_decision 不傳遞到 MagenticBuilderAdapter | risk_level 經 ManagerModelSelector 驅動模型選擇 |

### 現有基礎設施盤點

**已完成（可重用）：**
- ✅ `anthropic>=0.84.0` — 已安裝，`claude_sdk/client.py` 已有 AsyncAnthropic 使用經驗
- ✅ `BaseChatClient` — MAF 核心套件的抽象基類，設計上預期被擴展
- ✅ `MagenticBuilderAdapter` — 已有 `with_manager()`, `with_plan_review()` 方法
- ✅ `MagenticBuilder` 構造函數接受 `manager_agent=` 參數（PoC 已驗證）
- ✅ `RiskLevel` enum — CRITICAL/HIGH/MEDIUM/LOW（`orchestration/intent_router/models.py`）
- ✅ `FrameworkSelector.select_framework()` — 接受 `routing_decision` 含 risk_level
- ✅ `LLMServiceProtocol` — generate + generate_structured + chat_with_tools（可選）
- ✅ `StandardMagenticManager` — MAF 官方 Manager，接受 `agent_executor` 等參數

**需要新建：**
- ❌ `AnthropicChatClient(BaseChatClient)` — 包裝 AsyncAnthropic 為 MAF ChatClient
- ❌ `ManagerModelRegistry` — YAML 配置管理多個 provider/model
- ❌ `ManagerModelSelector` — 根據 risk_level + complexity 自動選模型
- ❌ `config/manager_models.yaml` — 模型定義 + 選擇策略
- ❌ `manager_model_routes.py` — API 端點（列出模型/測試連線/自動選擇）

**需要修改：**
- ⚠️ `MagenticBuilderAdapter.build()` — 修復：構造 `MagenticBuilder` 時傳入 `manager_agent=`
- ⚠️ `FrameworkSelector` / ExecutionHandler — 傳遞 risk_level 到 Builder

## 架構設計

### 完整數據流

```
用戶輸入 + 手動模式選擇（Chat/Workflow/Swarm）
    ↓
[L4] BusinessIntentRouter.route(user_input)
    → RoutingDecision {intent_category: INCIDENT, confidence: 0.95}
    （三層瀑布：PatternMatcher → SemanticRouter → LLMClassifier）
    ↓
[L4] RiskAssessor.assess(routing_decision)
    → RiskLevel.CRITICAL
    （路徑：orchestration/risk_assessor/assessor.py，7 維度條件性評分）
    ↓
[L4] HITLController.check(risk_level)
    → Approved ✅
    ↓
[L5] FrameworkSelector.select_framework(user_input, routing_decision=routing_decision)
    → IntentAnalysis {mode: ExecutionMode.SWARM_MODE, framework: SuggestedFramework.MAF}
    （路徑：hybrid/intent/router.py）
    ↓
[L5→L6] ManagerModelSelector.select_model(risk_level=CRITICAL, complexity="VERY_HIGH")
    → "claude-opus-4-6"                                    ← 新增
    ↓
[L6] MagenticBuilderAdapter.build_with_model_selection(risk_level=CRITICAL)
    → client = AnthropicChatClient(model="claude-opus-4-6", thinking=10K)   ← 新增
    → manager = Agent(client, name="Manager", instructions="...")           ← PoC 驗證
    → workflow = MagenticBuilder(participants=..., manager_agent=manager)   ← 構造函數注入
    → workflow = builder.build()
    ↓
[L6] workflow.run(task="APAC Glider ETL Pipeline 連續失敗")
    → Manager(Claude Opus): Task Ledger → 分解為 3 子任務
    → Worker 1-N 並行執行 → Progress Ledger → 綜合結果
```

### 模型選擇策略

| 風險等級 | Manager 模型 | 場景 |
|---------|-------------|------|
| 🔴 CRITICAL | claude-opus-4-6 + Extended Thinking 10K | 系統全面崩潰、ERP 遷移 |
| 🟠 HIGH | claude-sonnet-4-6 + Extended Thinking 5K | 安全事件、部署失敗 |
| 🟡 MEDIUM | gpt-4o | 常規變更管理、服務請求 |
| 🟢 LOW | claude-haiku-4-5 | 資訊查詢、狀態檢查 |
| ⚙️ USER_OVERRIDE | 任何已註冊模型 | 開發測試、手動指定 |

## Sprint 規劃

| Sprint | 名稱 | Story Points | 重點 |
|--------|------|-------------|------|
| [Sprint 151](./sprint-151-plan.md) | Foundation — AnthropicChatClient + Registry + Selector + build() 修復 | ~9 | 新增 3 模組 + YAML 配置 + 修復 build() 轉發 |
| [Sprint 152](./sprint-152-plan.md) | Integration — Builder 整合 + API 端點 + E2E 驗證 | ~7 | MagenticBuilderAdapter 整合 + FrameworkSelector 傳遞 + 測試 |

**總計**: ~16 Story Points (2 Sprints)

## 設計原則

1. **最小改動** — L1-L4、L7-L11 全部不動，只改 L5（FrameworkSelector 傳遞）和 L6（Builder 整合）
2. **YAML 零代碼配置** — 運維人員直接修改 `config/manager_models.yaml` 切換模型
3. **自動 Fallback** — Claude API 不可用時，ManagerModelSelector 自動降級到 Azure OpenAI
4. **Adapter 模式** — AnthropicChatClient 實作 MAF `BaseChatClient`，不是 hack
5. **先修後建** — Step 0 修復 build() 轉發問題，確保基礎正確再疊加功能

## 前置條件

- ✅ Phase 42 — SSE 串流端點、Mode Selector、HITL 審批
- ✅ Phase 43 — Swarm Core Engine（TaskDecomposer + SwarmWorkerExecutor）
- ✅ REFACTOR-001 — LLMServiceProtocol.chat_with_tools()
- ✅ `anthropic>=0.84.0` 已安裝
- ✅ `agent-framework>=1.0.0rc4` 已安裝
- ✅ `BaseChatClient` 抽象基類可用（MAF 擴展點）

## 風險與緩解

| 風險 | 影響 | 緩解 |
|------|------|------|
| build() 修復可能影響現有功能 | 高 | 先確認 E2E 測試通過，修復後逐步驗證 |
| AnthropicChatClient 格式轉換不完整 | 中 | 先用簡單 prompt 測試，逐步增加複雜度 |
| MAF GA 後 BaseChatClient 介面變更 | 中 | Adapter 模式隔離，GA 時改動量小 |
| 成本失控（Opus 比 GPT-4o 貴） | 低 | max_cost_per_task 上限 + 自動降級策略 |

## 檔案清單

| 操作 | 檔案路徑 | LOC |
|------|---------|-----|
| 新增 | `backend/config/manager_models.yaml` | ~80 |
| 新增 | `backend/src/integrations/agent_framework/clients/anthropic_chat_client.py` | ~150 |
| 新增 | `backend/src/integrations/hybrid/orchestrator/manager_model_registry.py` | ~120 |
| 新增 | `backend/src/integrations/hybrid/orchestrator/manager_model_selector.py` | ~60 |
| 新增 | `backend/src/api/v1/orchestration/manager_model_routes.py` | ~50 |
| 修改 | `backend/src/integrations/agent_framework/builders/magentic.py` | ~30 行 |
| 修改 | `backend/src/integrations/hybrid/intent/router.py` | ~15 行 |
| **合計** | **5 新增 + 2 修改** | **~430 LOC 新增 + ~45 行修改** |

---

**Phase 44 前置**: Phase 42-43 (E2E Pipeline + Swarm Core Engine)
**總 Story Points**: ~16 pts
**Sprint 範圍**: Sprint 151-152
**核心目標**: Manager Agent 從固定預設 → 多模型動態選擇
**詳細設計**: [magentic-orchestrator-upgrade-plan.md](../../../07-analysis/claude-agent-study/magentic-orchestrator-upgrade-plan.md)
**PoC 驗證**: [poc-findings.md](../../../07-analysis/claude-agent-study/poc-findings.md) — 全部 5 步通過，API 差異已記錄
