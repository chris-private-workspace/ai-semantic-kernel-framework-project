# Phase 3: 完整重構計劃 - 遷移至 Microsoft Agent Framework 官方 API

**生成日期**: 2025-12-05
**計劃範圍**: 將 Phase 2 所有自定義實現替換為 Agent Framework 官方 API
**估計工作量**: 6 個 Sprint (Sprint 13-18)

---

## 1. API 對比分析

### 1.1 ConcurrentBuilder vs 自定義 ConcurrentExecutor

| 面向 | 我們的實現 | Agent Framework 官方 API |
|------|-----------|------------------------|
| **位置** | `backend/src/domain/workflows/executors/concurrent.py` | `agent_framework.ConcurrentBuilder` |
| **行數** | ~619 行 | ~336 行 |
| **架構** | 獨立執行器，不與 Workflow 系統整合 | 與 Workflow、CheckpointStorage 深度整合 |

#### 主要差異

**我們的實現特點**:
- `ConcurrentMode` enum: ALL, ANY, MAJORITY, FIRST_SUCCESS
- 自定義 `ConcurrentTask` 和 `ConcurrentResult` dataclass
- 手動 semaphore 控制並發
- 不支持 checkpointing

**官方 API 特點**:
- Fluent Builder API: `ConcurrentBuilder().participants([]).with_aggregator().build()`
- 使用 `WorkflowBuilder` 底層，自動處理 fan-out/fan-in edges
- 內建 `CheckpointStorage` 支持
- 與 `AgentExecutor` 無縫整合
- 支持自定義聚合器 (callback 或 Executor)

#### 重構工作量: 中等 (21 點)
- 重新設計 API 介面以使用 Builder pattern
- 整合 WorkflowBuilder 和 edge routing
- 實現與現有 Agent Service 的適配

---

### 1.2 GroupChatBuilder vs 自定義 GroupChatManager

| 面向 | 我們的實現 | Agent Framework 官方 API |
|------|-----------|------------------------|
| **位置** | `backend/src/domain/orchestration/groupchat/manager.py` | `agent_framework.GroupChatBuilder` |
| **行數** | ~1140 行 | ~1877 行 |
| **架構** | 狀態機管理器 | Orchestrator + Builder pattern |

#### 主要差異

**我們的實現特點**:
- `SpeakerSelectionMethod`: AUTO, ROUND_ROBIN, RANDOM, MANUAL, PRIORITY, EXPERTISE
- 自定義 `GroupMessage`, `GroupChatConfig`, `GroupChatState` dataclass
- 手動 asyncio.Lock 管理
- 事件處理系統 (`on_message`, `on_event`)
- 簡單的 LLM 選擇整合

**官方 API 特點**:
- `GroupChatBuilder` 流暢 API
- `set_manager()` 或 `set_select_speakers_func()` 選擇發言者
- `GroupChatOrchestratorExecutor` 核心狀態機
- `ManagerSelectionRequest/Response` 結構化選擇
- 內建 termination condition 和 max_rounds
- Workflow 深度整合，支持 checkpointing
- `GroupChatStateSnapshot` 用於 manager 決策

#### 重構工作量: 高 (34 點)
- 完全重新設計為 Builder pattern
- 實現 `GroupChatOrchestratorExecutor` 等效
- 整合 `ManagerSelectionResponse` 結構化輸出
- 遷移發言者選擇邏輯
- 保持向後兼容的 API wrapper

---

### 1.3 HandoffBuilder vs 自定義 HandoffController

| 面向 | 我們的實現 | Agent Framework 官方 API |
|------|-----------|------------------------|
| **位置** | `backend/src/domain/orchestration/handoff/controller.py` | `agent_framework.HandoffBuilder` |
| **行數** | ~500 行 (估計) | ~1600 行 |
| **架構** | 控制器模式 | Builder + Coordinator pattern |

#### 主要差異

**我們的實現特點**:
- `HandoffPolicy`: IMMEDIATE, GRACEFUL, CONDITIONAL
- `HandoffStatus`, `HandoffContext`, `HandoffRequest`, `HandoffResult`
- 手動 handoff 執行邏輯

**官方 API 特點**:
- `HandoffBuilder` 流暢 API
- `participants()` 註冊 agents
- `set_coordinator()` 指定協調者
- `add_handoff()` 配置 handoff routing
- `with_interaction_mode()`: human_in_loop, autonomous
- `enable_return_to_previous()` 路由控制
- `HandoffUserInputRequest` 人機互動
- 內建 checkpointing 支持

#### 重構工作量: 高 (34 點)
- 實現 Builder pattern
- 整合 coordinator/participant 模型
- 實現 `HandoffUserInputRequest` 人機互動
- 遷移 handoff routing 邏輯

---

### 1.4 MagenticBuilder vs 自定義 DynamicPlanner

| 面向 | 我們的實現 | Agent Framework 官方 API |
|------|-----------|------------------------|
| **位置** | `backend/src/domain/orchestration/planning/dynamic_planner.py` | `agent_framework.MagenticBuilder` |
| **行數** | ~600 行 (估計) | ~2200+ 行 |
| **架構** | 獨立規劃器 | Magentic One 完整模式 |

#### 主要差異

**我們的實現特點**:
- `PlanStatus`, `PlanEvent`, `PlanAdjustment`
- `ExecutionPlan`, `DynamicPlanner`
- 簡單的動態規劃邏輯

**官方 API 特點**:
- `MagenticBuilder` 流暢 API
- `StandardMagenticManager` 或自定義 `MagenticManagerBase`
- 完整的 Task Ledger 系統 (facts, plan)
- Progress Ledger 追蹤 (is_satisfied, is_in_loop, is_progress_made)
- Human intervention 支持 (PLAN_REVIEW, TOOL_APPROVAL, STALL)
- 自動 reset 和 replan 邏輯
- 內建 prompts 模板
- 與 `MagenticAgentExecutor` 整合

#### 重構工作量: 很高 (42 點)
- 實現完整 Magentic One pattern
- 整合 Task Ledger 和 Progress Ledger
- 實現 `MagenticManagerBase` 子類
- 遷移 human intervention 邏輯
- 整合 streaming 和 event 系統

---

### 1.5 WorkflowExecutor vs 自定義 NestedWorkflowManager

| 面向 | 我們的實現 | Agent Framework 官方 API |
|------|-----------|------------------------|
| **位置** | `backend/src/domain/orchestration/nested/workflow_manager.py` | `agent_framework.WorkflowExecutor` |
| **行數** | ~500 行 (估計) | ~600 行 |
| **架構** | 獨立管理器 | Executor 包裝 Workflow |

#### 主要差異

**我們的實現特點**:
- `NestedWorkflowType`, `WorkflowScope`
- `NestedWorkflowConfig`, `SubWorkflowReference`
- `NestedExecutionContext`, `NestedWorkflowManager`

**官方 API 特點**:
- `WorkflowExecutor` 包裝任何 Workflow
- `SubWorkflowRequestMessage` / `SubWorkflowResponseMessage` 通訊
- 自動處理子工作流生命週期
- 並發執行支持 (per-execution state isolation)
- Checkpointing 整合
- 事件傳播 (outputs, requests)

#### 重構工作量: 中等 (26 點)
- 實現 WorkflowExecutor wrapper
- 整合 SubWorkflow request/response 機制
- 遷移嵌套執行邏輯
- 處理並發隔離

---

## 2. Sprint 規劃 (Phase 3: Sprint 13-18)

### Sprint 13: 基礎設施準備 (34 點)

| Story | 描述 | 點數 |
|-------|------|------|
| S13-1 | 建立 Agent Framework API wrapper 層 | 8 |
| S13-2 | 整合 WorkflowBuilder 基礎設施 | 8 |
| S13-3 | 實現 CheckpointStorage 適配器 | 8 |
| S13-4 | 建立測試框架和 mock | 5 |
| S13-5 | 文檔和遷移指南 | 5 |

**Sprint 目標**: 建立重構所需的基礎設施和適配層

---

### Sprint 14: ConcurrentBuilder 重構 (34 點)

| Story | 描述 | 點數 |
|-------|------|------|
| S14-1 | 實現 ConcurrentBuilder 適配器 | 8 |
| S14-2 | 遷移 ConcurrentExecutor 功能 | 8 |
| S14-3 | 整合 fan-out/fan-in edge routing | 8 |
| S14-4 | 更新 API 端點和 schema | 5 |
| S14-5 | 單元測試和整合測試 | 5 |

**Sprint 目標**: 完成並行執行功能的重構

---

### Sprint 15: HandoffBuilder 重構 (34 點)

| Story | 描述 | 點數 |
|-------|------|------|
| S15-1 | 實現 HandoffBuilder 適配器 | 8 |
| S15-2 | 遷移 HandoffController 功能 | 8 |
| S15-3 | 實現 HandoffUserInputRequest HITL | 8 |
| S15-4 | 更新 API 端點和 schema | 5 |
| S15-5 | 單元測試和整合測試 | 5 |

**Sprint 目標**: 完成 Agent Handoff 功能的重構

---

### Sprint 16: GroupChatBuilder 重構 (42 點)

| Story | 描述 | 點數 |
|-------|------|------|
| S16-1 | 實現 GroupChatBuilder 適配器 | 8 |
| S16-2 | 遷移 GroupChatManager 核心功能 | 8 |
| S16-3 | 實現 GroupChatOrchestratorExecutor | 8 |
| S16-4 | 整合 ManagerSelectionResponse | 8 |
| S16-5 | 更新 API 端點和 schema | 5 |
| S16-6 | 單元測試和整合測試 | 5 |

**Sprint 目標**: 完成群組聊天功能的重構

---

### Sprint 17: MagenticBuilder 重構 (42 點)

| Story | 描述 | 點數 |
|-------|------|------|
| S17-1 | 實現 MagenticBuilder 適配器 | 8 |
| S17-2 | 實現 StandardMagenticManager | 8 |
| S17-3 | 整合 Task/Progress Ledger | 8 |
| S17-4 | 實現 Human Intervention 系統 | 8 |
| S17-5 | 更新 API 端點和 schema | 5 |
| S17-6 | 單元測試和整合測試 | 5 |

**Sprint 目標**: 完成動態規劃功能的重構

---

### Sprint 18: WorkflowExecutor 和整合 (36 點)

| Story | 描述 | 點數 |
|-------|------|------|
| S18-1 | 實現 WorkflowExecutor 適配器 | 8 |
| S18-2 | 遷移 NestedWorkflowManager 功能 | 8 |
| S18-3 | 整合測試 - 所有功能 | 8 |
| S18-4 | 性能測試和優化 | 5 |
| S18-5 | 文檔更新和遷移完成 | 5 |
| S18-6 | 清理舊代碼和技術債務 | 2 |

**Sprint 目標**: 完成嵌套工作流重構和全面整合測試

---

## 3. 總結

### Phase 3 總計

| Sprint | 名稱 | 點數 |
|--------|------|------|
| Sprint 13 | 基礎設施準備 | 34 |
| Sprint 14 | ConcurrentBuilder 重構 | 34 |
| Sprint 15 | HandoffBuilder 重構 | 34 |
| Sprint 16 | GroupChatBuilder 重構 | 42 |
| Sprint 17 | MagenticBuilder 重構 | 42 |
| Sprint 18 | WorkflowExecutor 和整合 | 36 |
| **總計** | | **222 點** |

### 重構優先級

1. **Sprint 13** - 基礎設施 (必須先完成)
2. **Sprint 14** - ConcurrentBuilder (最簡單，建立信心)
3. **Sprint 15** - HandoffBuilder (核心功能)
4. **Sprint 16** - GroupChatBuilder (複雜但重要)
5. **Sprint 17** - MagenticBuilder (最複雜)
6. **Sprint 18** - WorkflowExecutor 和清理

### 風險和注意事項

1. **API 穩定性**: Agent Framework 仍在 Preview，API 可能變更
2. **向後兼容**: 需要維護適配層確保現有 API 不中斷
3. **測試覆蓋**: 每個 Sprint 需要完整的測試覆蓋
4. **文檔**: 需要同步更新 API 文檔和範例

### 成功標準

- [ ] 所有 Phase 2 功能通過官方 API 實現
- [ ] 現有 API 端點向後兼容
- [ ] 測試覆蓋率 >= 80%
- [ ] 性能不低於原有實現
- [ ] 與 Agent Framework 版本升級兼容

---

**報告生成者**: Claude Code
**方法**: 靜態代碼分析、API 對比
**下一步**: 創建 Sprint 13-18 詳細規劃文件
