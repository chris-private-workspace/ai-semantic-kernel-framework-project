# Sprint 112: Mock Separation + Redis Storage

## 概述

Sprint 112 專注於將 18 個 Mock 類從生產代碼中分離到測試目錄，建立環境感知的 Factory Pattern，並將 HITL 預設的 InMemoryApprovalStorage 遷移到 Redis 持久化存儲。此 Sprint 消除生產環境中的不確定性，確保運行時行為可預測。

## 目標

1. 審計並記錄所有 18 個 Mock 類的位置和依賴關係
2. 設計環境感知 Factory Pattern
3. 將 18 個 Mock 類遷移到 `backend/tests/mocks/`
4. InMemoryApprovalStorage 替換為 Redis 實現
5. LLMServiceFactory 移除靜默 fallback 到 Mock 的行為

## Story Points: 45 點

## 前置條件

- ✅ Sprint 111 完成 (Auth Middleware + Quick Wins)
- ✅ Redis 服務可用 (docker-compose)
- ✅ 全局 Auth 已啟用

## 任務分解

### Story 112-1: Mock 代碼審計 (0.5 天, P0)

**目標**: 完整記錄所有 18 個 Mock 類的位置、用途、被匯入的位置和依賴關係

**交付物**:
- Mock 審計報告（作為本文件的附錄或內部文檔）

**審計範圍**:

根據 V7 架構分析報告，18 個 Mock 類分布為：
- `backend/src/integrations/orchestration/` — 17 個 Mock 類
- `backend/src/integrations/llm/` — 1 個 Mock 類

**審計方式**:

```bash
# 搜索所有 Mock 類定義
grep -rn "class Mock" backend/src/integrations/orchestration/
grep -rn "class Mock" backend/src/integrations/llm/

# 搜索所有 Mock 類匯出 (__init__.py)
grep -rn "Mock" backend/src/integrations/orchestration/__init__.py

# 搜索所有 Mock 類被引用的位置
grep -rn "from.*orchestration.*import.*Mock" backend/src/
grep -rn "from.*llm.*import.*Mock" backend/src/
```

對每個 Mock 類記錄：
1. 類名和定義文件
2. 對應的真實實現類
3. 被匯入的位置（生產代碼 vs 測試代碼）
4. 是否通過 `__init__.py` 匯出
5. 遷移風險等級 (Low/Medium/High)

**驗收標準**:
- [ ] 18 個 Mock 類全部定位
- [ ] 每個 Mock 的匯入鏈記錄完整
- [ ] 9 個通過 `__init__.py` 匯出的 Mock 已標記
- [ ] 遷移順序和風險等級已評估

### Story 112-2: Factory Pattern 設計 (0.5 天, P0)

**目標**: 設計環境感知的 Factory Pattern，根據運行環境（production/development/testing）自動選擇真實或 Mock 實現

**交付物**:
- 新增 `backend/src/core/factories.py`

**設計方案**:

```python
# backend/src/core/factories.py
import os
from typing import TypeVar, Type

T = TypeVar("T")

class ServiceFactory:
    """環境感知的服務工廠

    根據 ENVIRONMENT 環境變量決定使用真實實現或 Mock 實現。
    production/staging: 僅使用真實實現，缺少依賴時拋出異常
    development: 使用真實實現，缺少依賴時 WARNING 並 fallback
    testing: 使用 Mock 實現
    """

    _registry: dict[str, dict[str, type]] = {}

    @classmethod
    def register(cls, service_name: str, real_cls: type, mock_cls: type | None = None):
        """註冊服務的真實和 Mock 實現"""
        cls._registry[service_name] = {
            "real": real_cls,
            "mock": mock_cls,
        }

    @classmethod
    def create(cls, service_name: str, **kwargs) -> object:
        """根據環境創建服務實例"""
        env = os.environ.get("ENVIRONMENT", "development")
        entry = cls._registry.get(service_name)
        if entry is None:
            raise ValueError(f"Unknown service: {service_name}")

        if env == "testing" and entry["mock"] is not None:
            return entry["mock"](**kwargs)

        try:
            return entry["real"](**kwargs)
        except Exception as e:
            if env == "production":
                raise RuntimeError(
                    f"Failed to create {service_name} in production: {e}"
                ) from e
            # development fallback
            if entry["mock"] is not None:
                logger.warning(
                    f"Failed to create real {service_name}, "
                    f"falling back to mock in {env}: {e}"
                )
                return entry["mock"](**kwargs)
            raise
```

**驗收標準**:
- [ ] ServiceFactory 類設計完成
- [ ] 支持 production/development/testing 三種環境
- [ ] production 環境不 fallback 到 Mock
- [ ] development 環境 fallback 時有 WARNING 日誌
- [ ] testing 環境直接使用 Mock
- [ ] Factory 設計文檔完成

### Story 112-3: Mock 遷移 (2.5 天, P0)

**目標**: 將 18 個 Mock 類從生產代碼遷移到 `backend/tests/mocks/`，更新所有匯入路徑

**交付物**:
- 新增 `backend/tests/mocks/` 目錄及子目錄
- 新增 `backend/tests/mocks/__init__.py`
- 新增 `backend/tests/mocks/orchestration.py` — 17 個 Mock 類
- 新增 `backend/tests/mocks/llm.py` — 1 個 Mock 類
- 修改 `backend/src/integrations/orchestration/` — 移除 Mock 類定義
- 修改 `backend/src/integrations/orchestration/__init__.py` — 移除 Mock 匯出
- 修改 `backend/src/integrations/llm/` — 移除 Mock 類定義
- 修改所有匯入 Mock 的文件

**遷移步驟**:

1. **建立目標目錄結構**:
```
backend/tests/mocks/
├── __init__.py
├── orchestration.py     # 17 個 Mock 類
└── llm.py               # 1 個 Mock 類
```

2. **逐批遷移**（每批遷移後跑測試）:
   - Batch 1: 未被生產代碼直接引用的 Mock（低風險）
   - Batch 2: 被生產代碼引用但可替換為 Factory 的 Mock
   - Batch 3: 通過 `__init__.py` 匯出的 9 個 Mock（高風險）

3. **每個 Mock 類的遷移流程**:
   - 複製類定義到 `tests/mocks/`
   - 更新測試文件中的匯入路徑
   - 更新 Factory 註冊（若需要）
   - 從原始文件刪除類定義
   - 從 `__init__.py` 移除匯出
   - 跑測試確認無回歸

4. **匯入路徑更新規則**:
```python
# Before (生產代碼中)
from backend.src.integrations.orchestration import MockRouter

# After (測試代碼中)
from backend.tests.mocks.orchestration import MockRouter

# After (生產代碼中 — 使用 Factory)
router = ServiceFactory.create("router")
```

**驗收標準**:
- [ ] `backend/src/integrations/orchestration/` 中 0 個 Mock 類定義
- [ ] `backend/src/integrations/llm/` 中 0 個 Mock 類定義
- [ ] `backend/src/integrations/orchestration/__init__.py` 中 0 個 Mock 匯出
- [ ] 所有 18 個 Mock 類在 `backend/tests/mocks/` 中
- [ ] 生產代碼中 0 處直接匯入 Mock 類
- [ ] 所有測試通過
- [ ] Factory Pattern 正確運作

### Story 112-4: InMemoryApprovalStorage → Redis (2 天, P0)

**目標**: 將 HITL 預設的 InMemoryApprovalStorage 替換為 Redis 持久化實現，確保審批資料在重啟後不丟失

**交付物**:
- 新增 `backend/src/infrastructure/storage/redis_approval_storage.py`
- 修改 ApprovalStorage 的預設實現配置
- 新增 Redis 連接健康檢查

**設計方案**:

```python
# backend/src/infrastructure/storage/redis_approval_storage.py
import json
from typing import Optional, List
from redis.asyncio import Redis

class RedisApprovalStorage:
    """Redis-backed 審批存儲

    Key 結構:
    - approval:{approval_id} → JSON(ApprovalRequest)
    - approval:pending → Set of pending approval_ids
    - approval:user:{user_id} → Set of user's approval_ids

    TTL: 7 天（可配置）
    """

    def __init__(self, redis: Redis, ttl_seconds: int = 604800):
        self._redis = redis
        self._ttl = ttl_seconds

    async def store_approval(self, approval_id: str, data: dict) -> None:
        """存儲審批請求"""
        key = f"approval:{approval_id}"
        await self._redis.set(key, json.dumps(data), ex=self._ttl)
        await self._redis.sadd("approval:pending", approval_id)
        if "user_id" in data:
            await self._redis.sadd(f"approval:user:{data['user_id']}", approval_id)

    async def get_approval(self, approval_id: str) -> Optional[dict]:
        """讀取審批請求"""
        key = f"approval:{approval_id}"
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def update_approval(self, approval_id: str, data: dict) -> None:
        """更新審批狀態"""
        key = f"approval:{approval_id}"
        await self._redis.set(key, json.dumps(data), ex=self._ttl)
        # 若已完成，從 pending 集合移除
        if data.get("status") in ("approved", "rejected"):
            await self._redis.srem("approval:pending", approval_id)

    async def list_pending(self) -> List[dict]:
        """列出所有待處理的審批"""
        pending_ids = await self._redis.smembers("approval:pending")
        results = []
        for aid in pending_ids:
            data = await self.get_approval(aid.decode() if isinstance(aid, bytes) else aid)
            if data:
                results.append(data)
        return results

    async def delete_approval(self, approval_id: str) -> None:
        """刪除審批記錄"""
        key = f"approval:{approval_id}"
        await self._redis.delete(key)
        await self._redis.srem("approval:pending", approval_id)
```

**替換策略**:

1. 找到 InMemoryApprovalStorage 的使用位置
2. 建立 RedisApprovalStorage 並保持相同介面
3. 使用 Factory Pattern 根據環境選擇實現
4. Development 環境 Redis 不可用時 fallback 到 InMemory（帶 WARNING）
5. Production 環境 Redis 不可用時拋出異常

**驗收標準**:
- [ ] RedisApprovalStorage 完整實現
- [ ] 介面與 InMemoryApprovalStorage 相容
- [ ] 審批資料在 Redis 重啟後可恢復（TTL 內）
- [ ] 健康檢查 endpoint 包含 Redis 連接狀態
- [ ] 單元測試覆蓋率 > 90%
- [ ] 整合測試驗證 Redis 讀寫正確
- [ ] Production 環境 Redis 不可用時拋出明確異常

### Story 112-5: LLMServiceFactory 靜默 Fallback 移除 (0.5 天, P1)

**目標**: 移除 LLMServiceFactory 在真實 LLM 不可用時靜默 fallback 到 Mock 的行為，改為明確失敗

**交付物**:
- 修改 `backend/src/integrations/llm/` 中的 LLMServiceFactory

**修改方式**:

找到 LLMServiceFactory 中的 fallback 邏輯：

```python
# Before (靜默 fallback)
try:
    return RealLLMService(...)
except Exception:
    return MockLLMService()  # 用戶不知道正在使用 Mock

# After (明確失敗)
try:
    return RealLLMService(...)
except Exception as e:
    env = os.environ.get("ENVIRONMENT", "development")
    if env == "production":
        raise RuntimeError(
            f"LLM service unavailable in production: {e}. "
            f"Check AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY."
        ) from e
    logger.warning(
        f"LLM service unavailable in {env}, using mock. "
        f"This is NOT acceptable in production. Error: {e}"
    )
    return MockLLMService()
```

**驗收標準**:
- [ ] Production 環境 LLM 不可用時拋出異常（而非靜默 fallback）
- [ ] Development 環境 fallback 時有明確 WARNING 日誌
- [ ] WARNING 日誌包含「NOT acceptable in production」提示
- [ ] 錯誤訊息包含環境變量提示 (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY)
- [ ] 單元測試驗證不同環境的行為

## 技術設計

### 目錄結構變更

```
backend/
├── src/
│   ├── core/
│   │   └── factories.py                    # 新增: ServiceFactory
│   ├── infrastructure/storage/
│   │   └── redis_approval_storage.py       # 新增: Redis 審批存儲
│   └── integrations/
│       ├── orchestration/
│       │   ├── *.py                        # 修改: 移除 Mock 類定義
│       │   └── __init__.py                 # 修改: 移除 Mock 匯出
│       └── llm/
│           └── *.py                        # 修改: 移除 Mock, 修改 Factory
└── tests/
    └── mocks/                              # 新增: Mock 目錄
        ├── __init__.py
        ├── orchestration.py                # 17 個 Mock 類
        └── llm.py                          # 1 個 Mock 類
```

### 依賴

```
# 確認已存在
redis>=5.0.0
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| Mock 遷移導致匯入錯誤 | 逐批遷移，每批跑完整測試；先 Batch 1（低風險），再 Batch 3（高風險） |
| Redis 連接失敗影響 HITL | 健康檢查 + development 環境 fallback（帶 WARNING） |
| Factory Pattern 引入複雜度 | 保持簡單設計，僅 register/create 兩個方法 |
| LLM fallback 移除後開發不便 | Development 環境仍允許 fallback，但帶明確警告 |

## 完成標準

- [ ] 18 Mock 類全部遷移到 tests/mocks/
- [ ] 生產代碼中 0 個 Mock 類定義
- [ ] ServiceFactory 正確運作
- [ ] RedisApprovalStorage 正常運作
- [ ] LLMServiceFactory 無靜默 fallback
- [ ] 所有測試通過
- [ ] Redis 健康檢查通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: TBD
