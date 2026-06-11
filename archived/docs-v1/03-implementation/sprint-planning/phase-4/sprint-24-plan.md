# Sprint 24: Planning & Multi-turn 整合

## Sprint Overview

| Property | Value |
|----------|-------|
| **Sprint** | 24 |
| **Phase** | 4 - 完整重構 |
| **Focus** | 動態規劃和多輪對話整合 |
| **Duration** | 2 週 |
| **Total Story Points** | 30 |

## Sprint Goal

評估並整合動態規劃和多輪對話功能，使用官方 `MagenticBuilder` 作為規劃核心，使用官方 `Checkpoint` API 管理多輪對話狀態，同時保留 Phase 2 的擴展功能（任務分解、決策引擎、會話管理）。

---

## 問題分析

### 當前狀態

| 模組 | 行數 | 問題 |
|------|------|------|
| `domain/orchestration/planning/` | 3,156 | 自行實現規劃功能 |
| `domain/orchestration/multiturn/` | 1,842 | 自行實現會話管理 |

### 官方 API 對應

| Phase 2 功能 | 官方 API | 建議 |
|-------------|----------|------|
| DynamicPlanner | `MagenticBuilder` | 使用官方 API |
| TaskDecomposer | 無直接對應 | 保留為擴展 |
| DecisionEngine | 無直接對應 | 保留為擴展 |
| SessionManager | `CheckpointStorage` | 使用官方 API |
| ConversationState | `Checkpoint` | 使用官方 API |

---

## User Stories

### S24-1: 評估 Planning 模組 (5 pts)

**目標**: 分析 `domain/orchestration/planning/` 各功能與官方 API 的對應關係

**評估項目**:

| 組件 | 行數 | 官方 API | 決策 |
|------|------|----------|------|
| `DynamicPlanner` | ~800 | `MagenticBuilder` | 遷移 |
| `TaskDecomposer` | ~600 | 無 | 保留為擴展 |
| `DecisionEngine` | ~700 | 無 | 保留為擴展 |
| `TrialErrorHandler` | ~500 | 無 | 保留為擴展 |
| `PlanOptimizer` | ~400 | 無 | 保留為擴展 |

**產出文檔**:
- `docs/03-implementation/sprint-execution/sprint-24/planning-analysis.md`

**驗收標準**:
- [ ] 完成所有組件的對應分析
- [ ] 確定保留/遷移決策
- [ ] 產出分析文檔

---

### S24-2: 創建 PlanningAdapter (10 pts)

**目標**: 創建動態規劃適配器

**範圍**: 新建 `integrations/agent_framework/builders/planning.py`

**架構設計**:
```python
from agent_framework import MagenticBuilder
from typing import List, Any, Optional, Dict
from domain.orchestration.planning.task_decomposer import TaskDecomposer
from domain.orchestration.planning.decision_engine import DecisionEngine

class PlanningAdapter:
    """
    動態規劃適配器。

    使用官方 MagenticBuilder 作為核心規劃引擎，
    擴展 Phase 2 的任務分解和決策引擎功能。
    """

    def __init__(self, id: str):
        self._id = id
        self._magentic_builder = MagenticBuilder()

        # Phase 2 擴展功能
        self._task_decomposer: Optional[TaskDecomposer] = None
        self._decision_engine: Optional[DecisionEngine] = None

    def with_task_decomposition(
        self,
        decomposition_strategy: DecompositionStrategy,
        max_subtasks: int = 10,
    ) -> "PlanningAdapter":
        """啟用任務分解功能"""
        self._task_decomposer = TaskDecomposer(
            strategy=decomposition_strategy,
            max_subtasks=max_subtasks,
        )
        return self

    def with_decision_engine(
        self,
        decision_rules: List[DecisionRule],
        fallback_strategy: Optional[str] = None,
    ) -> "PlanningAdapter":
        """啟用決策引擎"""
        self._decision_engine = DecisionEngine(
            rules=decision_rules,
            fallback=fallback_strategy,
        )
        return self

    def build(self) -> Workflow:
        """構建規劃工作流"""
        return self._magentic_builder.build()

    async def run(self, task: str) -> Any:
        """執行動態規劃"""
        # 1. 任務分解
        if self._task_decomposer:
            subtasks = await self._task_decomposer.decompose(task)
        else:
            subtasks = [task]

        # 2. 使用官方 MagenticBuilder 執行
        workflow = self.build()
        results = []

        for subtask in subtasks:
            # 3. 決策引擎選擇策略
            if self._decision_engine:
                strategy = await self._decision_engine.decide(subtask)
                result = await workflow.run(subtask, strategy=strategy)
            else:
                result = await workflow.run(subtask)

            results.append(result)

        return self._aggregate_results(results)
```

**驗收標準**:
- [ ] `PlanningAdapter` 使用官方 `MagenticBuilder`
- [ ] 任務分解功能正常工作
- [ ] 決策引擎功能正常工作
- [ ] 測試通過

---

### S24-3: 遷移 Multi-turn 到 Checkpoint (8 pts)

**目標**: 使用官方 Checkpoint API 管理多輪對話狀態

**範圍**:
- 新建 `integrations/agent_framework/multiturn/adapter.py`
- 新建 `integrations/agent_framework/multiturn/checkpoint_storage.py`

**架構設計**:
```python
from agent_framework import CheckpointStorage, InMemoryCheckpointStorage
from typing import Optional, Any
from domain.orchestration.multiturn.session_manager import SessionManager

class MultiTurnAdapter:
    """
    多輪對話適配器。

    使用官方 Checkpoint API 管理對話狀態，
    保留 Phase 2 的會話管理語義。
    """

    def __init__(
        self,
        session_id: str,
        checkpoint_storage: Optional[CheckpointStorage] = None,
    ):
        self._session_id = session_id
        self._checkpoint_storage = checkpoint_storage or InMemoryCheckpointStorage()

        # 從 Phase 2 遷移的會話追蹤
        self._session_manager = SessionManager(session_id)

    async def add_turn(self, message: str) -> str:
        """添加一輪對話"""
        # 從 Checkpoint 恢復狀態
        state = await self._checkpoint_storage.load(self._session_id)

        if state:
            self._session_manager.restore(state)

        # 處理對話
        response = await self._session_manager.process_turn(message)

        # 保存 Checkpoint
        await self._checkpoint_storage.save(
            self._session_id,
            self._session_manager.get_state(),
        )

        return response

    async def get_history(self) -> List[Dict]:
        """獲取對話歷史"""
        state = await self._checkpoint_storage.load(self._session_id)
        if state:
            return state.get("history", [])
        return []

    async def clear_session(self) -> bool:
        """清除會話"""
        return await self._checkpoint_storage.delete(self._session_id)
```

**自定義 Checkpoint 存儲**:
```python
# integrations/agent_framework/multiturn/checkpoint_storage.py

from agent_framework import CheckpointStorage
from typing import Any, Optional

class RedisCheckpointStorage(CheckpointStorage):
    """使用 Redis 的 Checkpoint 存儲"""

    def __init__(self, redis_client):
        self._redis = redis_client

    async def save(self, session_id: str, state: Any) -> None:
        await self._redis.set(f"checkpoint:{session_id}", json.dumps(state))

    async def load(self, session_id: str) -> Optional[Any]:
        data = await self._redis.get(f"checkpoint:{session_id}")
        return json.loads(data) if data else None

    async def delete(self, session_id: str) -> bool:
        return await self._redis.delete(f"checkpoint:{session_id}") > 0
```

**驗收標準**:
- [ ] `MultiTurnAdapter` 使用官方 `CheckpointStorage` 接口
- [ ] `RedisCheckpointStorage` 實現完成
- [ ] 會話狀態正確保存和恢復
- [ ] 測試通過

---

### S24-4: 更新 API 路由 (4 pts)

**目標**: 修改 API 層使用新的適配器

**範圍**:
- `api/v1/planning/routes.py`
- `api/v1/conversations/routes.py` 或相關路由

**規劃 API 重構**:
```python
# BEFORE
from domain.orchestration.planning.dynamic_planner import DynamicPlanner

# AFTER
from integrations.agent_framework.builders.planning import PlanningAdapter
```

**多輪對話 API 重構**:
```python
# BEFORE
from domain.orchestration.multiturn.session_manager import SessionManager

# AFTER
from integrations.agent_framework.multiturn.adapter import MultiTurnAdapter
```

**驗收標準**:
- [ ] API 層使用新的適配器
- [ ] API 響應格式保持不變
- [ ] 集成測試通過

---

### S24-5: 測試和文檔 (3 pts)

**測試文件**:
- 新建 `tests/unit/test_planning_adapter.py`
- 新建 `tests/unit/test_multiturn_adapter.py`
- 新建 `tests/unit/test_checkpoint_storage.py`

**測試清單**:
- [ ] PlanningAdapter 基本功能
- [ ] 任務分解測試
- [ ] 決策引擎測試
- [ ] MultiTurnAdapter 基本功能
- [ ] Checkpoint 存儲測試
- [ ] 會話恢復測試
- [ ] API 集成測試

**文檔更新**:
- [ ] 創建 `docs/03-implementation/migration/planning-migration.md`
- [ ] 創建 `docs/03-implementation/migration/multiturn-migration.md`

**驗收標準**:
- [ ] 所有測試通過
- [ ] 測試覆蓋率 > 80%
- [ ] 遷移指南完成

---

## Sprint 完成標準 (Definition of Done)

### 代碼驗證

```bash
# 1. 檢查 API 層不再直接使用 domain 層
cd backend
grep -r "from domain.orchestration.planning" src/api/
grep -r "from domain.orchestration.multiturn" src/api/
# 預期: 返回 0 結果

# 2. 運行所有測試
pytest tests/unit/test_planning*.py tests/unit/test_multiturn*.py -v
# 預期: 所有測試通過
```

### 完成確認清單

- [ ] S24-1: Planning 模組評估完成
- [ ] S24-2: PlanningAdapter 創建完成
- [ ] S24-3: Multi-turn 遷移完成
- [ ] S24-4: API 路由更新完成
- [ ] S24-5: 測試和文檔完成
- [ ] 所有測試通過
- [ ] 代碼審查完成
- [ ] 更新 bmm-workflow-status.yaml

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 規劃功能不兼容 | 中 | 高 | 保留擴展機制 |
| 會話狀態丟失 | 低 | 高 | 完整測試狀態恢復 |
| API 行為變更 | 中 | 中 | 保持接口兼容 |

---

## 依賴關係

| 依賴項 | 狀態 | 說明 |
|--------|------|------|
| Sprint 23 | 待完成 | Nested Workflow 重構 |
| 官方 `MagenticBuilder` | ✅ 可用 | 規劃核心 |
| 官方 `CheckpointStorage` | ✅ 可用 | 狀態管理 |

---

## 時間規劃

| Story | Points | 建議順序 | 依賴 |
|-------|--------|----------|------|
| S24-1: 評估 Planning | 5 | 1 | 無 |
| S24-2: PlanningAdapter | 10 | 2 | S24-1 |
| S24-3: Multi-turn 遷移 | 8 | 3 | 無（可並行） |
| S24-4: API 路由更新 | 4 | 4 | S24-2, S24-3 |
| S24-5: 測試和文檔 | 3 | 5 | S24-4 |

---

**創建日期**: 2025-12-06
**最後更新**: 2025-12-06
**版本**: 1.0
