# Sprint 119: InMemory Storage 遷移（前 4 個關鍵存儲）

## 概述

Sprint 119 是 Phase 33 的第一個 Sprint，專注於將平台中最關鍵的 4 個 InMemory 存儲類遷移到 Redis/PostgreSQL，同時將 ContextSynchronizer 的最小修復升級為 Redis Distributed Lock。

平台目前有 9 個 InMemory 存儲類散佈在 8 個檔案中，本 Sprint 優先處理影響最大的前 4 個。

## 目標

1. 替換 4 個最關鍵的 InMemory 存儲類為 Redis/PostgreSQL 持久化方案
2. 將 ContextSynchronizer 的 asyncio.Lock 升級為 Redis Distributed Lock

## Story Points: 45 點

## 前置條件

- ⬜ Phase 32 完成
- ⬜ Redis 服務可用（本地 Docker 或 Azure Cache for Redis）
- ⬜ PostgreSQL 服務可用
- ⬜ Phase 31 的 asyncio.Lock 最小修復已上線

## 任務分解

### Story 119-1: 替換前 4 個關鍵 InMemory 存儲類 (4 天, P0)

**目標**: 將 ApprovalStorage、SessionStorage、StateStorage、CacheStorage 從 InMemory 遷移到 Redis/PostgreSQL

**交付物**:
- 修改 `backend/src/integrations/` 中相關存儲模組
- 新增 Redis/PostgreSQL 存儲實現
- 遷移腳本（如需要）

**優先順序**:

| # | 存儲類 | 目標存儲 | 理由 |
|---|--------|---------|------|
| 1 | InMemoryApprovalStorage | Redis | HITL 審批預設存儲，丟失 = 審批中斷（若 Phase 31 未完成則此處完成） |
| 2 | SessionStorage | Redis | 用戶 Session 在 dict 中存儲，記憶體洩漏風險 |
| 3 | StateStorage | Redis + PostgreSQL | Agent 執行狀態，重啟丟失 = 任務中斷 |
| 4 | CacheStorage | Redis | 快取資料，遷移到原生 Redis 快取 |

**實現方式**:

```python
# Storage Protocol 定義（統一介面）
from typing import Protocol, Optional, Any

class StorageBackend(Protocol):
    """統一存儲後端協議"""

    async def get(self, key: str) -> Optional[Any]:
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def exists(self, key: str) -> bool:
        ...


class RedisStorageBackend:
    """Redis 存儲後端實現"""

    def __init__(self, redis_client, prefix: str = ""):
        self._redis = redis_client
        self._prefix = prefix

    async def get(self, key: str) -> Optional[Any]:
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ...
```

**驗收標準**:
- [ ] 4 個 InMemory 存儲類全部替換完成
- [ ] StorageBackend Protocol 定義完整
- [ ] RedisStorageBackend 實現完整
- [ ] 所有現有功能不受影響（向後兼容）
- [ ] 重啟服務後資料不丟失
- [ ] 單元測試覆蓋率 > 85%

### Story 119-2: ContextSynchronizer 升級為 Redis Distributed Lock (2 天, P0)

**目標**: 將 ContextSynchronizer 的 asyncio.Lock 最小修復升級為 Redis Distributed Lock，確保多 Worker 環境下的並發安全

**交付物**:
- 修改 `backend/src/integrations/hybrid/context_synchronizer.py`（或相關檔案，平台有 2 份 ContextSynchronizer 實現）
- 新增 Redis Distributed Lock 工具模組

**背景**:
- Phase 31 使用 asyncio.Lock 作為最小修復（單 Worker 足夠）
- Phase 33 準備 Multi-Worker 部署，asyncio.Lock 無法跨進程
- 需要升級為 Redis-based Distributed Lock

**實現方式**:

```python
import redis.asyncio as redis
from contextlib import asynccontextmanager

class RedisDistributedLock:
    """Redis 分散式鎖"""

    def __init__(self, redis_client: redis.Redis, lock_name: str, timeout: int = 30):
        self._redis = redis_client
        self._lock_name = lock_name
        self._timeout = timeout

    @asynccontextmanager
    async def acquire(self):
        lock = self._redis.lock(self._lock_name, timeout=self._timeout)
        acquired = await lock.acquire(blocking=True, blocking_timeout=10)
        if not acquired:
            raise TimeoutError(f"Failed to acquire lock: {self._lock_name}")
        try:
            yield
        finally:
            await lock.release()


class ContextSynchronizer:
    """升級後的 ContextSynchronizer（Redis Distributed Lock）"""

    def __init__(self, redis_client: redis.Redis):
        self._lock = RedisDistributedLock(redis_client, "context_sync_lock")

    async def synchronize(self, context_id: str, operation):
        async with self._lock.acquire():
            return await operation()
```

**驗收標準**:
- [ ] 2 份 ContextSynchronizer 實現統一為 1 份
- [ ] 使用 Redis Distributed Lock 取代 asyncio.Lock
- [ ] 支持 lock timeout 和 blocking timeout 配置
- [ ] 處理 lock 取得失敗的情況（TimeoutError）
- [ ] 多進程環境下並發測試通過
- [ ] 向後兼容（如 Redis 不可用時降級為 asyncio.Lock）
- [ ] 單元測試覆蓋率 > 85%

## 技術設計

### 目錄結構變更

```
backend/src/
├── infrastructure/
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── protocol.py          # StorageBackend Protocol
│   │   ├── redis_backend.py     # Redis 存儲實現
│   │   └── postgres_backend.py  # PostgreSQL 存儲實現（如需要）
│   └── distributed_lock/
│       ├── __init__.py
│       └── redis_lock.py        # Redis Distributed Lock
```

### 遷移策略

1. **定義統一 Protocol** - StorageBackend 介面
2. **實現 Redis Backend** - RedisStorageBackend
3. **逐一替換** - 每個存儲類獨立遷移、獨立測試
4. **環境感知** - 支持透過環境變量切換 InMemory/Redis
5. **降級機制** - Redis 不可用時自動降級為 InMemory + 告警

## 依賴

```
# 新增依賴
redis[hiredis]>=5.0      # Redis 異步客戶端
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| Redis 序列化複雜物件失敗 | 使用 JSON 序列化 + 自定義 encoder/decoder |
| 遷移過程中資料遺失 | 漸進式遷移，新舊並行一段時間 |
| Redis 連線不穩定 | 連線池 + 重試機制 + InMemory 降級 |
| 2 份 ContextSynchronizer 行為不一致 | 先理解兩份的差異，統一後充分測試 |

## 完成標準

- [ ] 4 個 InMemory 存儲類成功遷移到 Redis/PostgreSQL
- [ ] ContextSynchronizer 統一為 1 份，使用 Redis Distributed Lock
- [ ] 所有現有 API 端點行為不變
- [ ] 重啟後資料持久化驗證通過
- [ ] 單元測試與整合測試全部通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: 待定
