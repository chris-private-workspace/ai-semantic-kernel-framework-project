# Redis 使用示例和最佳實踐

## 1. 基本設置和初始化

### 1.1 應用啟動時連接 Redis

```python
# main.py
from fastapi import FastAPI
from src.infrastructure.cache import redis_manager

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """應用啟動時連接 Redis"""
    try:
        redis_manager.connect()
        print("✅ Redis connected successfully")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時斷開 Redis"""
    redis_manager.disconnect()
    print("✅ Redis disconnected")
```

### 1.2 健康檢查端點

```python
# src/api/v1/health.py
from fastapi import APIRouter
from src.infrastructure.cache import redis_manager

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint with Redis status"""
    redis_health = redis_manager.health_check()

    return {
        "status": "healthy" if redis_health["status"] == "healthy" else "degraded",
        "components": {
            "api": "healthy",
            "redis": redis_health
        }
    }
```

## 2. Cache Service 使用示例

### 2.1 基本緩存操作

```python
from src.infrastructure.cache import CacheService

cache = CacheService(namespace="workflows")

# 設置緩存（TTL 1 小時）
workflow_data = {"id": "123", "name": "Data Processing"}
cache.set("workflow:123", workflow_data, ttl=3600)

# 獲取緩存
cached_workflow = cache.get("workflow:123")
if cached_workflow:
    print(f"Cache hit: {cached_workflow}")
else:
    print("Cache miss")

# 刪除緩存
cache.delete("workflow:123")

# 檢查鍵是否存在
if cache.exists("workflow:123"):
    print("Key exists")
```

### 2.2 Cache-Aside Pattern（旁路緩存）

```python
from src.infrastructure.cache import CacheService
from src.infrastructure.database.repositories import WorkflowRepository

cache = CacheService(namespace="workflows")
workflow_repo = WorkflowRepository(db_session)

def get_workflow(workflow_id: str):
    """Get workflow with cache-aside pattern"""
    # 1. 嘗試從緩存獲取
    cached = cache.get(f"workflow:{workflow_id}")
    if cached:
        return cached

    # 2. 緩存未命中，從數據庫查詢
    workflow = workflow_repo.get_by_id(workflow_id)
    if not workflow:
        return None

    # 3. 寫入緩存
    cache.set(
        f"workflow:{workflow_id}",
        workflow.to_dict(),
        ttl=3600  # 1 hour
    )

    return workflow
```

### 2.3 使用 get_or_set 簡化代碼

```python
from src.infrastructure.cache import CacheService

cache = CacheService(namespace="workflows")

def get_workflow(workflow_id: str):
    """Simplified cache-aside using get_or_set"""
    return cache.get_or_set(
        key=f"workflow:{workflow_id}",
        factory=lambda: workflow_repo.get_by_id(workflow_id).to_dict(),
        ttl=3600
    )
```

### 2.4 Write-Through Pattern（寫穿）

```python
def update_workflow(workflow_id: str, data: dict):
    """Update workflow with write-through caching"""
    # 1. 更新數據庫
    updated_workflow = workflow_repo.update(workflow_id, data)

    # 2. 同時更新緩存
    cache.set(
        f"workflow:{workflow_id}",
        updated_workflow.to_dict(),
        ttl=3600
    )

    # 3. 失效相關緩存（如列表緩存）
    cache.invalidate_pattern("workflow:list:*")

    return updated_workflow
```

### 2.5 使用 @cached 裝飾器

```python
from src.infrastructure.cache import cached

@cached(ttl=3600, namespace="workflows")
def get_workflow_by_id(workflow_id: str):
    """Automatically cached function"""
    return workflow_repo.get_by_id(workflow_id).to_dict()

@cached(
    ttl=300,
    key_func=lambda user_id: f"user:{user_id}:workflows"
)
def get_user_workflows(user_id: str):
    """Custom cache key generation"""
    return workflow_repo.get_by_user(user_id)
```

### 2.6 計數器操作

```python
from src.infrastructure.cache import CacheService

cache = CacheService(namespace="stats")

# 增加計數
execution_count = cache.increment(f"execution:{workflow_id}:count")

# 減少計數
remaining_quota = cache.decrement(f"user:{user_id}:quota")

# 初始化計數器並設置過期時間
cache.set(f"daily:api:calls", 0, ttl=86400)  # 24 小時
cache.increment(f"daily:api:calls")
```

## 3. 分佈式鎖使用示例

### 3.1 基本鎖操作

```python
from src.infrastructure.cache import DistributedLock

lock = DistributedLock("workflow:123:edit", ttl=30)

# 手動獲取和釋放
if lock.acquire(blocking=True, timeout=10):
    try:
        # 執行臨界區操作
        edit_workflow(workflow_id="123")
    finally:
        lock.release()
else:
    raise Exception("Failed to acquire lock")
```

### 3.2 使用 Context Manager

```python
from src.infrastructure.cache import DistributedLock

lock = DistributedLock("workflow:123:edit", ttl=30)

with lock():
    # 自動獲取和釋放鎖
    edit_workflow(workflow_id="123")
```

### 3.3 使用 distributed_lock 函數

```python
from src.infrastructure.cache import distributed_lock

with distributed_lock("workflow:123:edit", ttl=30, timeout=10):
    # 臨界區
    edit_workflow(workflow_id="123")
```

### 3.4 防止重複執行

```python
from src.infrastructure.cache import distributed_lock
from fastapi import HTTPException

def execute_workflow(workflow_id: str, execution_id: str):
    """Prevent duplicate workflow execution"""
    lock_key = f"execution:{execution_id}:lock"

    try:
        with distributed_lock(lock_key, ttl=300, blocking=False):
            # 執行工作流
            result = perform_execution(workflow_id, execution_id)
            return result
    except RuntimeError:
        # 鎖已被其他進程持有
        raise HTTPException(
            status_code=409,
            detail="Execution already in progress"
        )
```

### 3.5 長時間操作的鎖續期

```python
from src.infrastructure.cache import DistributedLock
import time

lock = DistributedLock("long-running-task", ttl=30)

with lock():
    for i in range(10):
        # 執行操作
        process_batch(i)

        # 每次迭代延長鎖
        if i < 9:  # 最後一次不需要延長
            lock.extend(additional_time=30)

        time.sleep(5)
```

## 4. 速率限制使用示例

### 4.1 基本速率限制

```python
from src.infrastructure.cache import RateLimiter, RateLimitStrategy, RateLimitExceeded

limiter = RateLimiter()

def api_endpoint(user_id: str):
    """API endpoint with rate limiting"""
    try:
        # 檢查速率限制：每分鐘最多 60 次請求
        allowed, count, retry_after = limiter.check_rate_limit(
            identifier=user_id,
            max_requests=60,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW
        )

        if not allowed:
            raise RateLimitExceeded(
                f"Rate limit exceeded. Retry after {retry_after} seconds.",
                retry_after=retry_after
            )

        # 執行 API 操作
        return {"status": "ok", "requests_remaining": 60 - count}

    except RateLimitExceeded as e:
        return {
            "error": str(e),
            "retry_after": e.retry_after
        }
```

### 4.2 使用滑動窗口（更精確）

```python
from src.infrastructure.cache import RateLimiter, RateLimitStrategy

limiter = RateLimiter()

# 滑動窗口：每小時最多 1000 次請求
allowed, count, retry_after = limiter.check_rate_limit(
    identifier=f"api:{client_ip}",
    max_requests=1000,
    window_seconds=3600,
    strategy=RateLimitStrategy.SLIDING_WINDOW
)
```

### 4.3 使用 @rate_limit 裝飾器

```python
from src.infrastructure.cache import rate_limit, RateLimitStrategy

@rate_limit(max_requests=10, window_seconds=60)
def api_endpoint(user_id: str):
    """Automatically rate limited (identifier = first arg)"""
    return {"data": "..."}

@rate_limit(
    max_requests=100,
    window_seconds=3600,
    strategy=RateLimitStrategy.SLIDING_WINDOW,
    identifier_func=lambda request: request.client.host
)
def handle_request(request):
    """Rate limit by IP address"""
    return {"status": "ok"}
```

### 4.4 FastAPI 中間件集成

```python
from fastapi import FastAPI, Request, HTTPException
from src.infrastructure.cache import RateLimiter, RateLimitStrategy

app = FastAPI()
limiter = RateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Global rate limiting middleware"""
    # 獲取客戶端標識（IP 或用戶 ID）
    client_id = request.client.host
    if hasattr(request.state, "user"):
        client_id = request.state.user.id

    # 檢查速率限制
    allowed, count, retry_after = limiter.check_rate_limit(
        identifier=client_id,
        max_requests=100,
        window_seconds=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    # 添加速率限制頭
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = str(100 - count)
    response.headers["X-RateLimit-Reset"] = str(retry_after)

    return response
```

### 4.5 不同端點不同限制

```python
from fastapi import APIRouter, Depends
from src.infrastructure.cache import RateLimiter, RateLimitStrategy

router = APIRouter()
limiter = RateLimiter()

def check_rate_limit(max_requests: int, window: int):
    """Dependency for rate limiting"""
    async def _check(request: Request):
        user_id = request.state.user.id
        allowed, _, retry_after = limiter.check_rate_limit(
            identifier=user_id,
            max_requests=max_requests,
            window_seconds=window,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry after {retry_after}s"
            )
    return _check

# 一般端點：每分鐘 60 次
@router.get("/workflows", dependencies=[Depends(check_rate_limit(60, 60))])
async def list_workflows():
    return {"workflows": []}

# 消耗資源的端點：每分鐘 10 次
@router.post("/executions", dependencies=[Depends(check_rate_limit(10, 60))])
async def create_execution():
    return {"execution_id": "..."}
```

## 5. 會話管理使用示例

### 5.1 創建會話

```python
from src.infrastructure.cache import CacheService
from datetime import datetime
import secrets

cache = CacheService(namespace="session")

def create_session(user_id: str, user_data: dict) -> str:
    """Create user session"""
    session_id = secrets.token_urlsafe(32)

    session_data = {
        "user_id": user_id,
        "username": user_data["username"],
        "is_superuser": user_data.get("is_superuser", False),
        "permissions": user_data.get("permissions", []),
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat()
    }

    # 存儲會話（TTL 24 小時）
    cache.set(
        f"user:{session_id}",
        session_data,
        ttl=86400
    )

    return session_id
```

### 5.2 獲取會話

```python
def get_session(session_id: str) -> dict | None:
    """Get session data and renew expiration"""
    session_data = cache.get(f"user:{session_id}")

    if session_data:
        # 更新最後活動時間
        session_data["last_activity"] = datetime.utcnow().isoformat()

        # 續期會話
        cache.expire(f"user:{session_id}", ttl=86400)

    return session_data
```

### 5.3 FastAPI 依賴注入

```python
from fastapi import Cookie, HTTPException, Depends
from typing import Optional

async def get_current_user(
    session_id: Optional[str] = Cookie(None, alias="session_id")
) -> dict:
    """FastAPI dependency for session authentication"""
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return session_data

@router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Protected endpoint requiring authentication"""
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"]
    }
```

## 6. 工作流執行狀態緩存

### 6.1 緩存執行狀態

```python
from src.infrastructure.cache import CacheService

cache = CacheService(namespace="execution")

def cache_execution_status(execution_id: str, status_data: dict):
    """Cache execution status for real-time updates"""
    cache.set(
        f"status:{execution_id}",
        status_data,
        ttl=1800  # 30 minutes
    )

def get_execution_status(execution_id: str) -> dict | None:
    """Get cached execution status"""
    return cache.get(f"status:{execution_id}")

def update_execution_progress(execution_id: str, current_step: int, total_steps: int):
    """Update execution progress"""
    status = get_execution_status(execution_id)
    if status:
        status["current_step"] = current_step
        status["progress"] = current_step / total_steps
        cache_execution_status(execution_id, status)
```

### 6.2 使用 Redis Pub/Sub 推送狀態更新

```python
from src.infrastructure.cache import get_redis
import json

redis = get_redis()

def publish_execution_update(execution_id: str, event_type: str, data: dict):
    """Publish execution status update"""
    message = {
        "execution_id": execution_id,
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

    channel = f"execution:{execution_id}:updates"
    redis.publish(channel, json.dumps(message))

# 訂閱者
def subscribe_execution_updates(execution_id: str):
    """Subscribe to execution updates"""
    pubsub = redis.pubsub()
    channel = f"execution:{execution_id}:updates"
    pubsub.subscribe(channel)

    for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            yield data
```

## 7. 性能優化最佳實踐

### 7.1 批量操作使用 Pipeline

```python
from src.infrastructure.cache import get_redis

redis = get_redis()

def cache_multiple_workflows(workflows: list[dict]):
    """Batch cache multiple workflows using pipeline"""
    pipe = redis.pipeline()

    for workflow in workflows:
        key = f"cache:workflow:{workflow['id']}"
        pipe.setex(key, 3600, json.dumps(workflow))

    # 一次執行所有命令
    results = pipe.execute()
    return results

def get_multiple_workflows(workflow_ids: list[str]) -> list[dict]:
    """Batch get multiple workflows"""
    keys = [f"cache:workflow:{wf_id}" for wf_id in workflow_ids]

    # 使用 MGET 一次獲取多個鍵
    values = redis.mget(keys)

    return [
        json.loads(v) if v else None
        for v in values
    ]
```

### 7.2 避免緩存穿透

```python
def get_workflow_safe(workflow_id: str):
    """Prevent cache penetration with NULL caching"""
    # 嘗試從緩存獲取
    cached = cache.get(f"workflow:{workflow_id}")

    # 檢查是否為空值標記
    if cached == "NULL":
        return None

    if cached:
        return cached

    # 從數據庫查詢
    workflow = workflow_repo.get_by_id(workflow_id)

    if workflow:
        # 正常緩存
        cache.set(f"workflow:{workflow_id}", workflow, ttl=3600)
        return workflow
    else:
        # 緩存空值標記（短期）
        cache.set(f"workflow:{workflow_id}", "NULL", ttl=60)
        return None
```

### 7.3 防止緩存雪崩

```python
import random

def cache_with_jitter(key: str, value: any, base_ttl: int):
    """Add random jitter to TTL to prevent cache avalanche"""
    # 添加 ±10% 的隨機抖動
    jitter = random.randint(-base_ttl // 10, base_ttl // 10)
    actual_ttl = base_ttl + jitter

    cache.set(key, value, ttl=actual_ttl)
```

### 7.4 使用布隆過濾器（Bloom Filter）

```python
# 需要安裝 redis-py-bloom
# pip install redis-py-bloom

from redisbloom.client import Client

rb = Client(host='localhost', port=6379)

# 創建布隆過濾器
rb.bfCreate("workflow:exists", 0.01, 10000)

# 添加元素
rb.bfAdd("workflow:exists", workflow_id)

# 檢查元素是否存在
exists = rb.bfExists("workflow:exists", workflow_id)
if not exists:
    return None  # 100% 確定不存在
```

## 8. 監控和調試

### 8.1 緩存命中率統計

```python
from src.infrastructure.cache import CacheService

class MonitoredCacheService(CacheService):
    """Cache service with hit rate monitoring"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hits = 0
        self._misses = 0

    def get(self, key: str, namespace: str = None):
        value = super().get(key, namespace)

        if value is not None:
            self._hits += 1
        else:
            self._misses += 1

        return value

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def reset_stats(self):
        """Reset statistics"""
        self._hits = 0
        self._misses = 0
```

### 8.2 慢操作日誌

```python
import time
import logging

logger = logging.getLogger(__name__)

class TimedCacheService(CacheService):
    """Cache service with operation timing"""

    def get(self, key: str, namespace: str = None):
        start = time.time()
        value = super().get(key, namespace)
        elapsed = (time.time() - start) * 1000  # ms

        if elapsed > 10:  # 超過 10ms 記錄
            logger.warning(f"Slow cache GET: {key} took {elapsed:.2f}ms")

        return value
```

## 9. 測試

### 9.1 使用 fakeredis 進行單元測試

```python
import pytest
import fakeredis
from src.infrastructure.cache import CacheService

@pytest.fixture
def redis_client():
    """Fake Redis client for testing"""
    return fakeredis.FakeRedis(decode_responses=True)

@pytest.fixture
def cache_service(redis_client):
    """Cache service with fake Redis"""
    return CacheService(redis_client=redis_client)

def test_cache_set_get(cache_service):
    """Test basic cache operations"""
    # Set value
    cache_service.set("test_key", {"data": "value"}, ttl=60)

    # Get value
    result = cache_service.get("test_key")
    assert result == {"data": "value"}

    # Check TTL
    ttl = cache_service.get_ttl("test_key")
    assert 0 < ttl <= 60

def test_cache_expiration(cache_service, redis_client):
    """Test cache expiration"""
    cache_service.set("test_key", "value", ttl=1)

    # Manually expire in fake redis
    redis_client.expire("cache:test_key", -1)

    result = cache_service.get("test_key")
    assert result is None
```

### 9.2 集成測試

```python
import pytest
from src.infrastructure.cache import redis_manager

@pytest.fixture(scope="session")
def redis():
    """Real Redis connection for integration tests"""
    redis_manager.connect()
    yield redis_manager.get_client()
    redis_manager.disconnect()

def test_distributed_lock_integration(redis):
    """Test distributed lock with real Redis"""
    from src.infrastructure.cache import DistributedLock

    lock = DistributedLock("test:lock", ttl=5, redis_client=redis)

    # Acquire lock
    assert lock.acquire()
    assert lock.is_locked()
    assert lock.is_owned()

    # Release lock
    assert lock.release()
    assert not lock.is_locked()
```

## 10. 故障排除

### 10.1 常見問題

**問題：連接被拒絕**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```
解決：
- 檢查 Redis 是否運行：`docker ps | grep redis`
- 檢查端口映射：`docker port ai-framework-redis`
- 檢查防火牆設置

**問題：認證失敗**
```
redis.exceptions.AuthenticationError: Authentication required
```
解決：
- 檢查 `.env` 中的 `REDIS_PASSWORD` 配置
- 確認 Docker Compose 中的密碼設置

**問題：內存不足**
```
OOM command not allowed when used memory > 'maxmemory'
```
解決：
- 增加 Redis 內存限制
- 實施驅逐策略（LRU）
- 減少緩存 TTL

### 10.2 調試技巧

```python
# 查看所有鍵
redis = get_redis()
keys = list(redis.scan_iter(match="cache:*", count=100))
print(f"Total keys: {len(keys)}")

# 查看內存使用
info = redis.info("memory")
print(f"Used memory: {info['used_memory_human']}")

# 查看慢查詢
slowlog = redis.slowlog_get(10)
for entry in slowlog:
    print(f"Duration: {entry['duration']}μs, Command: {entry['command']}")
```

這份文檔涵蓋了 Redis 在項目中的所有主要使用場景和最佳實踐。
