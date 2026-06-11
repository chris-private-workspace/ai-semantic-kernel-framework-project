# Sprint 24 Checklist: Planning & Multi-turn 整合

## ⏳ Sprint 狀態 - 待開始

> **狀態**: 待開始
> **點數**: 0/30 pts (0%)
> **目標**: 動態規劃和多輪對話整合

---

## Quick Verification Commands

```bash
# 驗證 API 層不再使用 domain 層
cd backend
grep -r "from domain.orchestration.planning" src/api/
grep -r "from domain.orchestration.multiturn" src/api/

# 運行相關測試
pytest tests/unit/test_planning*.py tests/unit/test_multiturn*.py -v

# 官方 API 使用驗證
python scripts/verify_official_api_usage.py
```

---

## Story Breakdown

### S24-1: 評估 Planning 模組 (5 points) ⏳

**產出**: `docs/03-implementation/sprint-execution/sprint-24/planning-analysis.md`

#### 任務清單

- [ ] 分析 `DynamicPlanner` 組件
  - [ ] 代碼行數統計
  - [ ] 功能列表
  - [ ] 官方 API 對應關係
  - [ ] 遷移決策
- [ ] 分析 `TaskDecomposer` 組件
  - [ ] 代碼行數統計
  - [ ] 功能列表
  - [ ] 是否有官方 API 對應
  - [ ] 保留/遷移決策
- [ ] 分析 `DecisionEngine` 組件
  - [ ] 代碼行數統計
  - [ ] 功能列表
  - [ ] 是否有官方 API 對應
  - [ ] 保留/遷移決策
- [ ] 分析 `TrialErrorHandler` 組件
- [ ] 分析 `PlanOptimizer` 組件
- [ ] 產出分析文檔

#### 驗證

- [ ] 分析文檔完成
- [ ] 所有組件決策明確
- [ ] 文檔審查通過

---

### S24-2: 創建 PlanningAdapter (10 points) ⏳

**文件**: 新建 `backend/src/integrations/agent_framework/builders/planning.py`

#### 任務清單

- [ ] 創建 `planning.py` 文件
- [ ] 定義 `DecompositionStrategy` 枚舉
  ```python
  class DecompositionStrategy(Enum):
      SEQUENTIAL = "sequential"
      HIERARCHICAL = "hierarchical"
      PARALLEL = "parallel"
  ```
- [ ] 定義 `DecisionRule` 類
- [ ] 實現 `PlanningAdapter` 類
  - [ ] `__init__()` 方法
  - [ ] 創建 `MagenticBuilder` 實例
- [ ] 實現 `with_task_decomposition()` 方法
- [ ] 實現 `with_decision_engine()` 方法
- [ ] 實現 `build()` 方法
- [ ] 實現 `run()` 方法
  - [ ] 任務分解邏輯
  - [ ] 決策引擎邏輯
  - [ ] 結果聚合邏輯
- [ ] 實現 `_aggregate_results()` 方法
- [ ] 更新 `__init__.py` 導出

#### 驗證

- [ ] 使用官方 `MagenticBuilder`
- [ ] 任務分解功能測試通過
- [ ] 決策引擎功能測試通過
- [ ] 完整流程測試通過

---

### S24-3: 遷移 Multi-turn 到 Checkpoint (8 points) ⏳

**文件**:
- 新建 `backend/src/integrations/agent_framework/multiturn/__init__.py`
- 新建 `backend/src/integrations/agent_framework/multiturn/adapter.py`
- 新建 `backend/src/integrations/agent_framework/multiturn/checkpoint_storage.py`

#### 任務清單

- [ ] 創建 `multiturn/` 目錄結構
- [ ] 創建 `MultiTurnAdapter` 類
  - [ ] `__init__()` 方法
  - [ ] 整合 `CheckpointStorage`
  - [ ] 整合 `SessionManager`
- [ ] 實現 `add_turn()` 方法
  - [ ] 從 Checkpoint 恢復狀態
  - [ ] 處理對話
  - [ ] 保存 Checkpoint
- [ ] 實現 `get_history()` 方法
- [ ] 實現 `clear_session()` 方法
- [ ] 創建 `RedisCheckpointStorage` 類
  - [ ] 實現 `save()` 方法
  - [ ] 實現 `load()` 方法
  - [ ] 實現 `delete()` 方法
- [ ] 更新 `__init__.py` 導出

#### 驗證

- [ ] 使用官方 `CheckpointStorage` 接口
- [ ] 狀態保存測試通過
- [ ] 狀態恢復測試通過
- [ ] 會話清除測試通過

---

### S24-4: 更新 API 路由 (4 points) ⏳

**文件**:
- `backend/src/api/v1/planning/routes.py`
- `backend/src/api/v1/conversations/routes.py` 或相關路由

#### 任務清單

- [ ] 識別所有使用 domain 層的代碼
- [ ] 修改 Planning API import
  ```python
  # BEFORE
  from domain.orchestration.planning.dynamic_planner import DynamicPlanner

  # AFTER
  from integrations.agent_framework.builders.planning import PlanningAdapter
  ```
- [ ] 修改 Multi-turn API import
  ```python
  # BEFORE
  from domain.orchestration.multiturn.session_manager import SessionManager

  # AFTER
  from integrations.agent_framework.multiturn.adapter import MultiTurnAdapter
  ```
- [ ] 重構相關端點
- [ ] 保持 API 響應格式不變
- [ ] 更新 API 文檔

#### 驗證

- [ ] `grep "from domain.orchestration.planning" api/` 返回 0 結果
- [ ] `grep "from domain.orchestration.multiturn" api/` 返回 0 結果
- [ ] 所有 API 端點正常工作
- [ ] 集成測試通過

---

### S24-5: 測試和文檔 (3 points) ⏳

**文件**:
- 新建 `backend/tests/unit/test_planning_adapter.py`
- 新建 `backend/tests/unit/test_multiturn_adapter.py`
- 新建 `backend/tests/unit/test_checkpoint_storage.py`
- 新建 `docs/03-implementation/migration/planning-migration.md`
- 新建 `docs/03-implementation/migration/multiturn-migration.md`

#### 任務清單

- [ ] 創建 `test_planning_adapter.py`
  - [ ] 測試基本創建
  - [ ] 測試任務分解
  - [ ] 測試決策引擎
  - [ ] 測試完整流程
- [ ] 創建 `test_multiturn_adapter.py`
  - [ ] 測試添加對話
  - [ ] 測試獲取歷史
  - [ ] 測試清除會話
  - [ ] 測試狀態恢復
- [ ] 創建 `test_checkpoint_storage.py`
  - [ ] 測試 Redis 存儲
  - [ ] 測試保存/加載
- [ ] 創建遷移指南文檔
- [ ] 運行覆蓋率報告

#### 驗證

- [ ] 所有測試通過
- [ ] 測試覆蓋率 > 80%
- [ ] 遷移指南完成

---

## Sprint Completion Criteria

### 必須達成項目

- [ ] PlanningAdapter 使用官方 `MagenticBuilder`
- [ ] 多輪對話使用官方 `Checkpoint` API
- [ ] 保留 Phase 2 的擴展功能
- [ ] 測試覆蓋完整

### 代碼審查重點

- [ ] 適配器正確使用官方 API
- [ ] 擴展功能整合正確
- [ ] 狀態管理可靠
- [ ] 錯誤處理完善

---

## Final Checklist

- [ ] S24-1: Planning 模組評估 ⏳
- [ ] S24-2: PlanningAdapter 創建 ⏳
- [ ] S24-3: Multi-turn 遷移 ⏳
- [ ] S24-4: API 路由更新 ⏳
- [ ] S24-5: 測試和文檔 ⏳
- [ ] 官方 API 驗證通過
- [ ] 所有測試通過
- [ ] 代碼審查完成
- [ ] 更新 bmm-workflow-status.yaml
- [ ] 更新 progress.md

---

## Post-Sprint Actions

1. **更新 bmm-workflow-status.yaml** - 記錄 Sprint 24 完成
2. **標記舊代碼** - 標記相關 domain 模組為 deprecated
3. **Git Commit** - 提交所有變更
4. **準備 Sprint 25** - 確認清理工作依賴項就緒

---

**創建日期**: 2025-12-06
**最後更新**: 2025-12-06
**版本**: 1.0
