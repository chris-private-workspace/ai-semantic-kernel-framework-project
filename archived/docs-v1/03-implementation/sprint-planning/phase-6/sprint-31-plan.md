# Sprint 31: Planning API 完整遷移

**Sprint 目標**: 解決所有 P0 級別架構問題，確保核心 API 路由 100% 使用適配器
**總點數**: 25 Story Points
**優先級**: 🔴 CRITICAL

---

## 問題背景

根據 Phase 1-5 架構審計，發現以下 P0 級別問題：

### 問題 1: Planning API 直接使用棄用代碼

```python
# 當前問題代碼 (backend/src/api/v1/planning/routes.py)
from src.domain.orchestration.planning import (
    TaskDecomposer,           # ❌ 已棄用
    DynamicPlanner,           # ❌ 已棄用
    AutonomousDecisionEngine, # ❌ 已棄用
    TrialAndErrorEngine,      # ❌ 已棄用
)

# 應該使用
from src.integrations.agent_framework.builders import PlanningAdapter
```

### 問題 2: domain/agents/service.py 官方 API 位置

```python
# 當前問題代碼 (backend/src/domain/agents/service.py:218)
def _build_agent_executor(...):
    try:
        from agent_framework import AgentExecutor, ChatMessage, Role
        # ⚠️ 官方 API 導入應該在適配器層
```

### 問題 3: Concurrent API 使用 domain.workflows.executors

```python
# 當前問題代碼 (backend/src/api/v1/concurrent/routes.py)
from src.domain.workflows.executors import (
    ConcurrentExecutor,  # ❌ 已棄用
    ...
)
```

---

## Story 清單

### S31-1: Planning API 路由遷移至 PlanningAdapter (8 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 重構
**影響範圍**: `backend/src/api/v1/planning/routes.py`

#### 任務清單

1. **分析現有 Planning API 路由**
   - 識別所有使用 `domain.orchestration.planning` 的端點
   - 統計影響的 API 路由數量 (預計 46 個路由)
   - 確認 PlanningAdapter 已有的功能

2. **重構 Planning 路由導入**
   ```python
   # 移除
   from src.domain.orchestration.planning import (
       TaskDecomposer,
       DynamicPlanner,
       AutonomousDecisionEngine,
       TrialAndErrorEngine,
       # ... 其他類
   )

   # 添加
   from src.integrations.agent_framework.builders import PlanningAdapter
   from src.integrations.agent_framework.builders.planning import (
       TaskDecomposerAdapter,
       DynamicPlannerAdapter,
       # ... 其他適配器
   )
   ```

3. **更新 API 端點實現**
   - `/api/v1/planning/decompose` → 使用 TaskDecomposerAdapter
   - `/api/v1/planning/plan` → 使用 DynamicPlannerAdapter
   - `/api/v1/planning/decide` → 使用 PlanningAdapter.decide()
   - `/api/v1/planning/trial` → 使用 PlanningAdapter.trial_run()

4. **驗證功能等價性**
   - 運行現有測試
   - 確認 API 響應格式不變

#### 驗收標準
- [ ] Planning routes.py 無 `domain.orchestration.planning` 導入
- [ ] 所有 46 個 Planning API 路由正常工作
- [ ] 現有測試通過 (test_planning_api.py: 22 tests)

---

### S31-2: AgentExecutor 適配器創建 (5 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/agent_framework/builders/`

#### 任務清單

1. **創建 AgentExecutorAdapter**
   ```python
   # 新文件: backend/src/integrations/agent_framework/builders/agent_executor.py

   from agent_framework import AgentExecutor, ChatMessage, Role

   class AgentExecutorAdapter:
       """Agent 執行器適配器 - 包裝官方 AgentExecutor API"""

       def __init__(self, agent_config: dict):
           self._executor = AgentExecutor()
           # ...

       async def execute(self, messages: List[ChatMessage]) -> str:
           return await self._executor.run(messages)
   ```

2. **遷移 domain/agents/service.py 邏輯**
   - 將 `_build_agent_executor` 遷移到適配器
   - 更新 service.py 使用適配器

3. **更新 builders/__init__.py 導出**
   ```python
   from .agent_executor import AgentExecutorAdapter

   __all__ = [
       # ... 現有導出
       "AgentExecutorAdapter",
   ]
   ```

#### 驗收標準
- [ ] AgentExecutorAdapter 創建完成
- [ ] domain/agents/service.py 使用適配器
- [ ] 官方 API 導入集中度提升至 83%+

---

### S31-3: Concurrent API 路由修復 (5 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 重構
**影響範圍**: `backend/src/api/v1/concurrent/routes.py`, `websocket.py`

#### 任務清單

1. **分析 Concurrent API 當前導入**
   ```python
   # 當前問題
   from src.domain.workflows.executors import (
       ConcurrentExecutor,
       ConcurrentMode,
       ...
   )
   from src.domain.workflows.deadlock_detector import (...)
   ```

2. **重構為適配器導入**
   ```python
   # 目標
   from src.integrations.agent_framework.builders import (
       ConcurrentBuilderAdapter,
       ConcurrentExecutorAdapter,
   )
   from src.api.v1.concurrent.adapter_service import ConcurrentAPIService
   ```

3. **更新 WebSocket 處理**
   - concurrent/websocket.py 同步更新

#### 驗收標準
- [ ] Concurrent routes.py 無 domain.workflows.executors 導入
- [ ] 13 個 Concurrent API 路由正常工作
- [ ] WebSocket 功能正常

---

### S31-4: 棄用代碼清理和警告更新 (4 pts)

**優先級**: 🟡 P1 - HIGH
**類型**: 清理
**影響範圍**: `backend/src/domain/orchestration/`

#### 任務清單

1. **更新棄用警告訊息**
   - 確保所有棄用模組有清晰的遷移指引
   - 更新 deprecated-modules.md 文檔

2. **清理未使用的導入**
   - 掃描所有 API 路由文件
   - 移除未使用的 domain 導入

3. **驗證棄用警告生效**
   ```python
   import warnings
   warnings.filterwarnings('error', category=DeprecationWarning)
   # 確保正常流程不觸發
   ```

#### 驗收標準
- [ ] 所有棄用模組有 DeprecationWarning
- [ ] deprecated-modules.md 更新完成
- [ ] 正常使用流程無 DeprecationWarning

---

### S31-5: 單元測試驗證 (3 pts)

**優先級**: 🟡 P1 - HIGH
**類型**: 測試
**影響範圍**: `backend/tests/`

#### 任務清單

1. **運行現有測試套件**
   ```bash
   pytest tests/unit/ -v --tb=short
   pytest tests/integration/ -v --tb=short
   ```

2. **新增適配器測試**
   - test_agent_executor_adapter.py
   - 更新 test_planning_api.py

3. **驗證無回歸**
   - 所有 3,439+ 測試通過
   - 無新增 DeprecationWarning

#### 驗收標準
- [ ] 所有現有測試通過
- [ ] 新增 AgentExecutorAdapter 測試
- [ ] 測試覆蓋率維持 85%+

---

## 技術規範

### 導入規範

```python
# ✅ 正確 - 使用適配器
from src.integrations.agent_framework.builders import (
    PlanningAdapter,
    ConcurrentBuilderAdapter,
    AgentExecutorAdapter,
)

# ❌ 錯誤 - 直接使用棄用代碼
from src.domain.orchestration.planning import TaskDecomposer
from src.domain.workflows.executors import ConcurrentExecutor
```

### 適配器設計規範

```python
class XxxAdapter:
    """適配器應遵循的模式"""

    def __init__(self, config: dict):
        # 1. 導入官方 API
        from agent_framework import OfficialClass

        # 2. 創建官方實例
        self._official = OfficialClass()

    def build(self) -> Result:
        # 3. 調用官方 API
        return self._official.build()
```

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| Planning 遷移破壞現有功能 | 中 | 高 | 完整測試，回滾分支 |
| API 響應格式變化 | 低 | 高 | 保持接口兼容 |
| 遺漏部分導入 | 中 | 中 | 使用 grep 全面掃描 |

---

## 驗證命令

```bash
# 驗證無棄用導入
grep -r "from src.domain.orchestration.planning" backend/src/api/

# 驗證官方 API 使用
cd backend && python scripts/verify_official_api_usage.py

# 運行測試
pytest tests/ -v --tb=short

# 檢查 DeprecationWarning
python -W error::DeprecationWarning -c "from src.api.v1.planning import routes"
```

---

## 完成定義

- [ ] 所有 S31 Story 完成
- [ ] Planning/Concurrent API 100% 使用適配器
- [ ] 官方 API 導入集中度 > 85%
- [ ] 所有測試通過
- [ ] 代碼審查完成
