# Phase 3 Migration Guide: Agent Framework Integration

## Overview

本文檔說明如何將 IPA Platform 的 Phase 2 自定義實現遷移至 Microsoft Agent Framework 官方 API。

### 遷移目標

- 將自定義實現替換為官方 API
- 保持現有 API 端點向後兼容
- 確保性能不低於原有實現
- 簡化維護和未來升級

### 影響範圍

| 組件 | 原實現 | 目標 API | 影響程度 |
|------|--------|----------|----------|
| 並行執行 | ConcurrentExecutor | ConcurrentBuilder | 高 |
| Agent Handoff | HandoffController | HandoffBuilder | 高 |
| 群組聊天 | GroupChatManager | GroupChatBuilder | 高 |
| 動態規劃 | DynamicPlanner | MagenticBuilder | 高 |
| 嵌套工作流 | NestedWorkflowManager | WorkflowExecutor | 中 |

---

## 遷移時間線

### Sprint 13: 基礎設施準備 (Week 27-28)
- 建立 Agent Framework API wrapper 層
- 整合 WorkflowBuilder 基礎設施
- 實現 CheckpointStorage 適配器
- 建立測試框架和 mock 工具

### Sprint 14: ConcurrentBuilder 重構 (Week 29-30)
- 將 ConcurrentExecutor 遷移至 ConcurrentBuilder
- 支持 FanOut/FanIn 邊類型
- 更新相關 API 端點

### Sprint 15: HandoffBuilder 重構 (Week 31-32)
- 將 HandoffController 遷移至 HandoffBuilder
- 整合 HandoffUserInputRequest
- 更新相關 API 端點

### Sprint 16: GroupChatBuilder 重構 (Week 33-34)
- 將 GroupChatManager 遷移至 GroupChatBuilder
- 整合 GroupChatOrchestratorExecutor
- 更新相關 API 端點

### Sprint 17: MagenticBuilder 重構 (Week 35-36)
- 將 DynamicPlanner 遷移至 MagenticBuilder
- 整合 Task/Progress Ledger
- 整合 Human Intervention

### Sprint 18: WorkflowExecutor 和整合 (Week 37-38)
- 將 NestedWorkflowManager 遷移至 WorkflowExecutor
- 完成整合測試
- 性能測試和優化
- 清理舊代碼

---

## 架構變更

### 當前架構 (Phase 2)

```
┌─────────────────────────────────────────────────────────────────┐
│                    IPA Platform 應用層                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │               自定義實現 (Phase 2)                          ││
│  │  - ConcurrentExecutor (619 行)                              ││
│  │  - HandoffController (500 行)                               ││
│  │  - GroupChatManager (1140 行)                               ││
│  │  - DynamicPlanner (600 行)                                  ││
│  │  - NestedWorkflowManager (500 行)                           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 目標架構 (Phase 3)

```
┌─────────────────────────────────────────────────────────────────┐
│                    IPA Platform 應用層                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │               Adapter Layer (新建)                          ││
│  │  - ConcurrentBuilderAdapter                                 ││
│  │  - HandoffBuilderAdapter                                    ││
│  │  - GroupChatBuilderAdapter                                  ││
│  │  - MagenticBuilderAdapter                                   ││
│  │  - WorkflowExecutorAdapter                                  ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Agent Framework Core API                       ││
│  │  ConcurrentBuilder, GroupChatBuilder, HandoffBuilder,       ││
│  │  MagenticBuilder, WorkflowExecutor, CheckpointStorage       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 逐步遷移指南

### Step 1: 準備工作

1. **安裝 Agent Framework**
   ```bash
   pip install agent-framework
   ```

2. **導入新模組**
   ```python
   from src.integrations.agent_framework import (
       WorkflowAdapter,
       WorkflowConfig,
       CheckpointStorageAdapter,
   )
   ```

### Step 2: 創建適配器

使用新的適配器替換直接的 Agent Framework 調用：

```python
# 舊代碼
from domain.workflows.executors.concurrent import ConcurrentExecutor

executor = ConcurrentExecutor(
    mode=ConcurrentMode.ALL,
    tasks=[task1, task2, task3],
)
result = await executor.execute(input_data)

# 新代碼
from src.integrations.agent_framework.builders import ConcurrentBuilderAdapter

adapter = ConcurrentBuilderAdapter(
    id="parallel-tasks",
    executors=[exec1, exec2, exec3],
    completion_condition=CompleteAll(),
)
workflow = adapter.build()
result = await adapter.run(input_data)
```

### Step 3: 更新 API 端點

API 端點保持向後兼容，內部使用新的適配器：

```python
# API 路由 (保持不變)
@router.post("/concurrent/execute")
async def execute_concurrent(request: ConcurrentRequest):
    # 內部使用新適配器
    adapter = ConcurrentBuilderAdapter(...)
    result = await adapter.run(request.input)
    return result
```

### Step 4: 測試和驗證

1. **單元測試**
   ```bash
   pytest tests/unit/test_agent_framework*.py -v
   ```

2. **整合測試**
   ```bash
   pytest tests/integration/test_workflow_integration.py -v
   ```

3. **性能測試**
   ```bash
   pytest tests/performance/test_concurrent_perf.py -v
   ```

---

## API 向後兼容性

### 保持的 API 端點

所有現有 API 端點保持不變：

| 端點 | 方法 | 狀態 |
|------|------|------|
| `/api/v1/concurrent/execute` | POST | 保持 |
| `/api/v1/handoff/trigger` | POST | 保持 |
| `/api/v1/groupchat/start` | POST | 保持 |
| `/api/v1/planning/create` | POST | 保持 |
| `/api/v1/workflow/nested/execute` | POST | 保持 |

### 請求/響應格式

請求和響應格式保持向後兼容。內部數據結構可能會改變，但對外介面不變。

---

## 常見問題

### Q1: 遷移後性能會受影響嗎？

Phase 3 的目標是確保性能不低於原有實現。Agent Framework 提供了更優化的底層實現，某些場景可能會有性能提升。

### Q2: 現有的測試需要修改嗎？

單元測試需要更新以使用新的 Mock 工具。整合測試和 E2E 測試應該保持不變，因為 API 介面保持向後兼容。

### Q3: 如果 Agent Framework 有 breaking change 怎麼辦？

適配層的設計目的就是隔離這種變更。當 Agent Framework 更新時，只需要修改適配器實現，不需要修改上層應用代碼。

### Q4: 遷移過程中如何保持系統穩定？

建議使用功能開關（Feature Flag）來控制新舊實現的切換，在充分測試後再完全切換到新實現。

---

## 風險評估

### 高風險
- Agent Framework API 變更
- 性能回退

### 中風險
- 測試覆蓋不足
- 文檔同步問題

### 低風險
- 開發延遲
- 學習曲線

### 緩解措施
1. 保持與 Agent Framework 團隊的溝通
2. 建立完整的測試套件
3. 保留舊實現作為 fallback
4. 增量式遷移

---

## 相關文檔

- [API 映射表](./api-mapping.md)
- [Phase 3 Overview](../03-implementation/sprint-planning/phase-3/README.md)
- [Phase 2 架構審查](../../claudedocs/PHASE2-ARCHITECTURE-REVIEW.md)
