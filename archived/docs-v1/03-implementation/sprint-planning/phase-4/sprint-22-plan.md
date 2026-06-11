# Sprint 22: Concurrent & Memory 遷移

## Sprint Overview

| Property | Value |
|----------|-------|
| **Sprint** | 22 |
| **Phase** | 4 - 完整重構 |
| **Focus** | 並行執行器和記憶體系統遷移 |
| **Duration** | 2 週 |
| **Total Story Points** | 28 |

## Sprint Goal

將 `domain/workflows/executors/` 並行執行功能和 `domain/orchestration/memory/` 記憶體系統遷移到官方 API，確保所有並行操作使用 `ConcurrentBuilderAdapter`，記憶體使用官方 Memory API 接口。

---

## 問題分析

### 當前狀態

| 模組 | 行數 | 問題 |
|------|------|------|
| `domain/workflows/executors/concurrent.py` | ~500 | 自行實現並行執行 |
| `domain/workflows/executors/parallel_gateway.py` | ~600 | 自行實現並行網關 |
| `domain/orchestration/memory/` | 2,017 | 自行實現記憶體存儲 |

### 目標架構

```
並行執行:
API Layer → ConcurrentBuilderAdapter → Official ConcurrentBuilder

記憶體:
API Layer → Memory API → RedisMemoryStorage (自定義後端)
```

---

## User Stories

### S22-1: 重構 Concurrent 執行器 (8 pts)

**目標**: 將所有並行執行遷移到 `ConcurrentBuilderAdapter`

**範圍**:
- `api/v1/workflows/routes.py` (並行執行相關)
- `domain/workflows/executors/concurrent.py`

**修改前**:
```python
from domain.workflows.executors.concurrent import ConcurrentExecutor

executor = ConcurrentExecutor(tasks=[task1, task2, task3])
results = await executor.execute_parallel()
```

**修改後**:
```python
from integrations.agent_framework.builders.concurrent import ConcurrentBuilderAdapter

adapter = ConcurrentBuilderAdapter(
    id="concurrent-001",
    executors=[executor1, executor2, executor3],
)
adapter.with_aggregator(lambda results: merge_results(results))
workflow = adapter.build()
results = await adapter.run(input_data)
```

**驗收標準**:
- [ ] 所有並行執行使用 `ConcurrentBuilderAdapter`
- [ ] API 層不再直接使用 `domain/workflows/executors/concurrent.py`
- [ ] 並行執行性能無明顯下降
- [ ] 測試通過

---

### S22-2: 整合 ParallelGateway (6 pts)

**目標**: 將並行網關功能整合到 `ConcurrentBuilderAdapter`

**範圍**: `integrations/agent_framework/builders/concurrent.py`

**網關類型**:
1. `PARALLEL_SPLIT` - 並行分割（同時執行多個分支）
2. `PARALLEL_JOIN` - 並行合併（等待所有分支完成）
3. `INCLUSIVE_GATEWAY` - 包含網關（根據條件選擇分支）

**Join 條件**:
1. `ALL` - 等待所有完成
2. `ANY` - 任一完成即可
3. `FIRST` - 第一個完成即可
4. `N_OF_M` - N 個完成即可

**實現方式**:
```python
class ConcurrentBuilderAdapter:
    def with_gateway_config(
        self,
        gateway_type: GatewayType = GatewayType.PARALLEL_SPLIT,
        join_condition: JoinCondition = JoinCondition.ALL,
        timeout: Optional[float] = None,
    ) -> "ConcurrentBuilderAdapter":
        """
        配置並行網關。

        使用官方 ConcurrentBuilder 實現，保留 Phase 2 的網關語義。
        """
        self._gateway_type = gateway_type
        self._join_condition = join_condition
        self._timeout = timeout

        # 根據 join_condition 設置官方 API 的 aggregator
        if join_condition == JoinCondition.ALL:
            self._aggregator = lambda results: {"all": results, "completed": len(results)}
        elif join_condition == JoinCondition.ANY:
            self._aggregator = lambda results: {"first": results[0]} if results else None
        elif join_condition == JoinCondition.FIRST:
            self._aggregator = lambda results: results[0] if results else None

        return self
```

**驗收標準**:
- [ ] 所有網關類型正常工作
- [ ] Join 條件正確執行
- [ ] 超時處理正確
- [ ] 測試通過

---

### S22-3: 遷移 Memory 系統 (8 pts)

**目標**: 使用官方 Memory API 接口，保留自定義後端實現

**範圍**:
- `domain/orchestration/memory/redis_store.py`
- `domain/orchestration/memory/postgres_store.py`

**官方 API 接口**:
```python
from agent_framework import Memory, MemoryStorage

class MemoryStorage(Protocol):
    """官方定義的記憶體存儲接口"""

    async def store(self, key: str, value: Any) -> None:
        """存儲數據"""
        ...

    async def retrieve(self, key: str) -> Optional[Any]:
        """檢索數據"""
        ...

    async def search(self, query: str, limit: int = 10) -> List[Any]:
        """搜索數據"""
        ...

    async def delete(self, key: str) -> bool:
        """刪除數據"""
        ...
```

**自定義後端實現**:
```python
# integrations/agent_framework/memory/redis_storage.py

from agent_framework import MemoryStorage
from typing import Any, Optional, List
import json

class RedisMemoryStorage(MemoryStorage):
    """使用官方 MemoryStorage 接口，保留 Redis 後端"""

    def __init__(self, redis_client):
        self._redis = redis_client

    async def store(self, key: str, value: Any) -> None:
        await self._redis.set(key, json.dumps(value))

    async def retrieve(self, key: str) -> Optional[Any]:
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def search(self, query: str, limit: int = 10) -> List[Any]:
        # 實現向量搜索或關鍵詞搜索
        # 使用 Phase 2 的搜索邏輯
        from domain.orchestration.memory.search import MemorySearcher
        searcher = MemorySearcher(self._redis)
        return await searcher.search(query, limit)

    async def delete(self, key: str) -> bool:
        return await self._redis.delete(key) > 0

# 創建 Memory 實例
memory = Memory(storage=RedisMemoryStorage(redis_client))
```

**驗收標準**:
- [ ] `RedisMemoryStorage` 實現官方 `MemoryStorage` 接口
- [ ] `PostgresMemoryStorage` 實現官方 `MemoryStorage` 接口
- [ ] 現有功能保留（CRUD、搜索）
- [ ] 測試通過

---

### S22-4: 測試和文檔 (6 pts)

**測試文件**:
- 新建 `tests/unit/test_concurrent_adapter.py`
- 新建 `tests/unit/test_memory_storage.py`
- 更新 `tests/integration/test_concurrent_api.py`

**測試清單**:
- [ ] 並行執行基本功能
- [ ] 網關類型測試
- [ ] Join 條件測試
- [ ] 超時處理測試
- [ ] Redis 記憶體存儲測試
- [ ] Postgres 記憶體存儲測試
- [ ] 記憶體搜索測試
- [ ] API 集成測試

**文檔更新**:
- [ ] 創建 `docs/03-implementation/migration/concurrent-migration.md`
- [ ] 創建 `docs/03-implementation/migration/memory-migration.md`

**驗收標準**:
- [ ] 所有測試通過
- [ ] 測試覆蓋率 > 80%
- [ ] 遷移指南完成

---

## Sprint 完成標準 (Definition of Done)

### 代碼驗證

```bash
# 1. 檢查並行執行不再直接使用 domain 層
cd backend
grep -r "from domain.workflows.executors.concurrent" src/api/
# 預期: 返回 0 結果

# 2. 檢查記憶體不再直接使用 domain 層
grep -r "from domain.orchestration.memory" src/api/
# 預期: 返回 0 結果

# 3. 運行所有測試
pytest tests/unit/test_concurrent*.py tests/unit/test_memory*.py -v
# 預期: 所有測試通過
```

### 完成確認清單

- [ ] S22-1: Concurrent 執行器重構完成
- [ ] S22-2: ParallelGateway 整合完成
- [ ] S22-3: Memory 系統遷移完成
- [ ] S22-4: 測試和文檔完成
- [ ] 所有測試通過
- [ ] 代碼審查完成
- [ ] 更新 bmm-workflow-status.yaml

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 並行執行性能下降 | 低 | 中 | 性能基準測試對比 |
| 記憶體數據遷移 | 中 | 高 | 數據備份和驗證 |
| 搜索功能差異 | 中 | 中 | 保留原有搜索邏輯 |

---

## 依賴關係

| 依賴項 | 狀態 | 說明 |
|--------|------|------|
| Sprint 21 | 待完成 | Handoff 遷移 |
| `ConcurrentBuilderAdapter` | ✅ 存在 | 需要擴展網關功能 |
| 官方 `ConcurrentBuilder` | ✅ 可用 | `from agent_framework import ConcurrentBuilder` |
| 官方 `Memory` | ✅ 可用 | `from agent_framework import Memory` |

---

## 時間規劃

| Story | Points | 建議順序 | 依賴 |
|-------|--------|----------|------|
| S22-1: Concurrent 執行器 | 8 | 1 | 無 |
| S22-2: ParallelGateway | 6 | 2 | S22-1 |
| S22-3: Memory 系統 | 8 | 3 | 無（可並行） |
| S22-4: 測試和文檔 | 6 | 4 | S22-1, S22-2, S22-3 |

---

**創建日期**: 2025-12-06
**最後更新**: 2025-12-06
**版本**: 1.0
