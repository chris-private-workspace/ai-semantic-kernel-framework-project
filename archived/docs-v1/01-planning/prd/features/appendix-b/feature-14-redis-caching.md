# Feature 14: Redis 快取

**版本**: 1.0  
**日期**: 2025-11-19  
**狀態**: 草稿

---

## 📑 導航

- [← 返回附錄 B 索引](../../prd-appendix-b-features-8-14.md)
- [← 上一個: Feature 13 - 現代 Web UI](./feature-13-modern-web-ui.md)
- [→ 下一個: 附錄 C - API 規範](../../prd-appendix-c-api-specs.md)

---

## <a id="f14-redis-caching"></a>F14. Redis 緩存

**功能類別**: Performance (性能優化)  
**優先級**: P0 (必須擁有)  
**估計開發時間**: 1 週  
**複雜度**: ⭐⭐⭐

---

### 14.1 功能概述

**定義**:
F14（Redis 緩存系統）提供**分佈式內存緩存**來加速頻繁訪問的數據（Workflow 定義、Agent 配置、Prompt 模板），並支持**會話管理、分佈式鎖、速率限制**等高級功能。通過 Redis 減少數據庫查詢，將 API 響應時間從 500ms 降至 50ms。

**為什麼重要**:
- **性能提升**: 緩存熱點數據，減少 90% 數據庫查詢
- **可擴展性**: 支持水平擴展的分佈式緩存
- **一致性**: 使用 Redis 分佈式鎖保證數據一致性
- **彈性**: API 速率限制防止濫用和 DDoS 攻擊

**核心能力**:
1. **數據緩存**: Workflow 定義、Agent 配置、Prompt 模板、用戶會話
2. **緩存失效策略**: TTL（過期時間）、LRU（最少使用淘汰）、主動失效（數據更新時）
3. **分佈式鎖**: 保證多實例環境下的操作原子性（如 Workflow 發布）
4. **速率限制**: API 調用頻率限制（按用戶/IP）
5. **會話管理**: 用戶登入狀態、權限緩存
6. **緩存預熱**: 系統啟動時加載常用數據

**業務價值**:
- **用戶體驗**: API 響應時間從 500ms 降至 50ms（10 倍提升）
- **成本節省**: 減少數據庫負載 80%，延遲數據庫擴容
- **高可用**: Redis Sentinel/Cluster 提供 99.9% 可用性

**技術棧**:
- **Redis 版本**: Redis 7.0+（支持 JSON 數據類型）
- **Python 客戶端**: redis-py + aioredis（異步支持）
- **高可用**: Redis Sentinel（自動故障轉移）
- **持久化**: AOF（追加日誌）+ RDB（快照）混合持久化
- **監控**: redis_exporter + Prometheus

**現實世界示例**:

**場景**: "ServiceNow 票務查詢" Workflow 的性能優化

**無緩存（首次查詢）**:
```
用戶請求 → API → 數據庫查詢 Workflow 定義（200ms） 
         → 數據庫查詢 Agent 配置（150ms）
         → 數據庫查詢 Prompt 模板（100ms）
         → 執行 Workflow（500ms）
總耗時: 950ms
```

**有緩存（後續查詢）**:
```
用戶請求 → API → Redis 獲取 Workflow 定義（5ms）
         → Redis 獲取 Agent 配置（5ms）
         → Redis 獲取 Prompt 模板（5ms）
         → 執行 Workflow（500ms）
總耗時: 515ms（減少 45%）
```

**緩存命中率**: 95%（熱門 Workflow）

---

### 14.2 用戶故事

#### **US-F14-001: Workflow 和 Agent 配置緩存**

**User Story**:  
作為系統架構師，我希望緩存 Workflow 定義和 Agent 配置，以便減少數據庫查詢並加速 Workflow 執行。

**場景描述**:

- 用戶觸發 Workflow 執行
- 系統首先查詢 Redis 緩存
- 如果緩存命中，直接使用緩存數據
- 如果緩存未命中，從數據庫加載並寫入 Redis
- 當 Workflow 或 Agent 配置更新時，主動失效緩存

**Acceptance Criteria**:

1. ✅ Workflow 定義緩存 TTL = 1 小時（可配置）
2. ✅ Agent 配置緩存 TTL = 30 分鐘
3. ✅ 緩存命中率 >90%（監控指標）
4. ✅ 數據更新時自動失效緩存（通過事件機制）
5. ✅ 支持緩存預熱（系統啟動時加載 Top 100 熱門 Workflow）
6. ✅ 緩存 Key 命名規範：`workflow:{workflow_id}`, `agent:{agent_id}`
7. ✅ 使用 Redis JSON 存儲複雜對象

**技術實現**:

```python
# core/cache.py
import redis.asyncio as redis
from redis.commands.json.path import Path
import json
from typing import Optional, Any
from datetime import timedelta

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def get_workflow(self, workflow_id: str) -> Optional[dict]:
        """獲取 Workflow 定義（優先從緩存）"""
        cache_key = f"workflow:{workflow_id}"
        
        # Try cache first
        cached = await self.redis.json().get(cache_key)
        if cached:
            print(f"✅ Cache hit: {cache_key}")
            return cached
        
        # Cache miss - load from DB
        print(f"❌ Cache miss: {cache_key}")
        workflow = await self._load_workflow_from_db(workflow_id)
        if workflow:
            # Write to cache with TTL
            await self.redis.json().set(cache_key, Path.root_path(), workflow)
            await self.redis.expire(cache_key, timedelta(hours=1))
        
        return workflow
    
    async def get_agent(self, agent_id: str) -> Optional[dict]:
        """獲取 Agent 配置（優先從緩存）"""
        cache_key = f"agent:{agent_id}"
        
        cached = await self.redis.json().get(cache_key)
        if cached:
            return cached
        
        agent = await self._load_agent_from_db(agent_id)
        if agent:
            await self.redis.json().set(cache_key, Path.root_path(), agent)
            await self.redis.expire(cache_key, timedelta(minutes=30))
        
        return agent
    
    async def invalidate_workflow(self, workflow_id: str):
        """主動失效 Workflow 緩存（當數據更新時）"""
        cache_key = f"workflow:{workflow_id}"
        await self.redis.delete(cache_key)
        print(f"🗑️ Invalidated cache: {cache_key}")
    
    async def invalidate_agent(self, agent_id: str):
        """主動失效 Agent 緩存"""
        cache_key = f"agent:{agent_id}"
        await self.redis.delete(cache_key)
    
    async def warm_up_cache(self):
        """緩存預熱：加載 Top 100 熱門 Workflow"""
        top_workflows = await self._get_top_workflows(limit=100)
        for workflow in top_workflows:
            cache_key = f"workflow:{workflow['id']}"
            await self.redis.json().set(cache_key, Path.root_path(), workflow)
            await self.redis.expire(cache_key, timedelta(hours=1))
        print(f"🔥 Warmed up {len(top_workflows)} workflows")
    
    async def _load_workflow_from_db(self, workflow_id: str) -> Optional[dict]:
        # Database query implementation
        pass
    
    async def _load_agent_from_db(self, agent_id: str) -> Optional[dict]:
        # Database query implementation
        pass
    
    async def _get_top_workflows(self, limit: int = 100) -> list:
        # Query top workflows by execution count
        pass

# 使用示例
cache = RedisCache()

# 執行 Workflow 時使用緩存
async def execute_workflow(workflow_id: str, input_data: dict):
    workflow = await cache.get_workflow(workflow_id)
    if not workflow:
        raise ValueError(f"Workflow {workflow_id} not found")
    
    # Execute workflow steps
    for step in workflow['steps']:
        agent = await cache.get_agent(step['agent_id'])
        # ... execute step
```

**緩存失效事件處理**:

```python
# api/workflow.py
from fastapi import APIRouter, Depends
from core.cache import RedisCache

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
cache = RedisCache()

@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, workflow_data: dict, db: Session = Depends(get_db)):
    """更新 Workflow 並失效緩存"""
    # Update database
    db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    db_workflow.definition = workflow_data['definition']
    db.commit()
    
    # Invalidate cache
    await cache.invalidate_workflow(workflow_id)
    
    return {"status": "updated", "workflow_id": workflow_id}
```

**緩存監控指標**:

```python
# core/metrics.py
from prometheus_client import Counter, Histogram

cache_hits = Counter('redis_cache_hits_total', 'Total cache hits', ['cache_type'])
cache_misses = Counter('redis_cache_misses_total', 'Total cache misses', ['cache_type'])
cache_latency = Histogram('redis_cache_latency_seconds', 'Cache operation latency', ['operation'])

async def get_workflow_with_metrics(workflow_id: str):
    with cache_latency.labels(operation='get_workflow').time():
        workflow = await cache.get_workflow(workflow_id)
        if workflow:
            cache_hits.labels(cache_type='workflow').inc()
        else:
            cache_misses.labels(cache_type='workflow').inc()
        return workflow
```

**測試策略**:

1. 單元測試：測試緩存命中、未命中、失效邏輯
2. 集成測試：測試數據庫與 Redis 數據一致性
3. 性能測試：對比有/無緩存的 API 響應時間
4. 負載測試：測試高並發下的緩存性能

---

#### **US-F14-002: Prompt 模板緩存與熱重載**

**User Story**:  
作為提示工程師，我希望 Prompt 模板自動緩存並支持熱重載，以便模板更新後 5 秒內生效。

**場景描述**:

- Prompt 模板存儲在 Git 倉庫（YAML 文件）
- 系統啟動時加載所有 Prompt 到 Redis
- 每 5 秒檢查 Git 倉庫變更（Webhook 或輪詢）
- 檢測到變更時，重新加載並更新 Redis 緩存
- Agent 執行時從 Redis 獲取最新 Prompt

**Acceptance Criteria**:

1. ✅ Prompt 模板緩存 Key：`prompt:{prompt_name}:{version}`
2. ✅ 支持多版本 Prompt 共存（用於 A/B 測試）
3. ✅ Git 倉庫變更後 5 秒內自動更新緩存
4. ✅ 提供手動刷新 API（`POST /api/prompts/reload`）
5. ✅ 緩存預熱：系統啟動時加載所有 Prompt
6. ✅ Prompt 模板包含元數據：版本號、更新時間、作者

**技術實現**:

```python
# core/prompt_cache.py
import asyncio
import aiofiles
import yaml
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from core.cache import RedisCache

class PromptCacheManager:
    def __init__(self, prompts_dir: str = "./prompts", redis_cache: RedisCache = None):
        self.prompts_dir = Path(prompts_dir)
        self.cache = redis_cache or RedisCache()
        self.last_sync_time = None
    
    async def load_all_prompts(self):
        """加載所有 Prompt 模板到 Redis"""
        prompt_files = list(self.prompts_dir.glob("**/*.yaml"))
        print(f"📂 Loading {len(prompt_files)} prompt templates...")
        
        for prompt_file in prompt_files:
            await self._load_prompt_file(prompt_file)
        
        self.last_sync_time = datetime.now()
        print(f"✅ Loaded all prompts at {self.last_sync_time}")
    
    async def _load_prompt_file(self, prompt_file: Path):
        """加載單個 Prompt 文件"""
        async with aiofiles.open(prompt_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            prompt_data = yaml.safe_load(content)
        
        prompt_name = prompt_data.get('name')
        version = prompt_data.get('version', 'latest')
        
        # Store in Redis with metadata
        cache_key = f"prompt:{prompt_name}:{version}"
        prompt_with_metadata = {
            "name": prompt_name,
            "version": version,
            "template": prompt_data.get('template'),
            "variables": prompt_data.get('variables', []),
            "description": prompt_data.get('description', ''),
            "author": prompt_data.get('author', 'unknown'),
            "updated_at": datetime.now().isoformat(),
            "file_path": str(prompt_file)
        }
        
        await self.cache.redis.json().set(cache_key, Path.root_path(), prompt_with_metadata)
        
        # Also store under 'latest' alias
        latest_key = f"prompt:{prompt_name}:latest"
        await self.cache.redis.json().set(latest_key, Path.root_path(), prompt_with_metadata)
        
        print(f"📝 Cached prompt: {cache_key}")
    
    async def get_prompt(self, prompt_name: str, version: str = "latest") -> Optional[dict]:
        """獲取 Prompt 模板"""
        cache_key = f"prompt:{prompt_name}:{version}"
        return await self.cache.redis.json().get(cache_key)
    
    async def watch_for_changes(self):
        """監控 Git 倉庫變更並自動重載"""
        while True:
            try:
                # Check for changes (simplified - in production use Git hooks)
                current_mtime = max(f.stat().st_mtime for f in self.prompts_dir.glob("**/*.yaml"))
                
                if self.last_sync_time is None or current_mtime > self.last_sync_time.timestamp():
                    print(f"🔄 Detected prompt changes, reloading...")
                    await self.load_all_prompts()
                
            except Exception as e:
                print(f"❌ Error watching prompts: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def reload_prompts(self):
        """手動重載所有 Prompt"""
        await self.load_all_prompts()
        return {"status": "reloaded", "timestamp": self.last_sync_time.isoformat()}

# 初始化
prompt_manager = PromptCacheManager()

# 系統啟動時加載
@app.on_event("startup")
async def startup():
    await prompt_manager.load_all_prompts()
    # Start background watcher
    asyncio.create_task(prompt_manager.watch_for_changes())

# API endpoint
@router.post("/api/prompts/reload")
async def reload_prompts():
    """手動重載 Prompt"""
    result = await prompt_manager.reload_prompts()
    return result
```

**Prompt 模板示例**:

```yaml
# prompts/customer_service/ticket_summary.yaml
name: ticket_summary
version: v1.2
author: john.doe@company.com
description: Summarize customer support tickets
template: |
  You are a customer service analyst. Summarize the following ticket:
  
  Ticket ID: {ticket_id}
  Customer: {customer_name}
  Issue: {issue_description}
  Priority: {priority}
  
  Provide a concise summary in 2-3 sentences, focusing on:
  1. Main problem
  2. Customer impact
  3. Suggested action
variables:
  - ticket_id
  - customer_name
  - issue_description
  - priority
```

**使用緩存的 Prompt**:

```python
# agents/customer_service_agent.py
async def execute_ticket_summary(ticket_data: dict):
    # Get prompt from cache
    prompt_template = await prompt_manager.get_prompt("ticket_summary", version="latest")
    
    if not prompt_template:
        raise ValueError("Prompt template not found")
    
    # Render prompt with variables
    from jinja2 import Template
    template = Template(prompt_template['template'])
    rendered_prompt = template.render(**ticket_data)
    
    # Call LLM
    response = await call_llm(rendered_prompt)
    return response
```

**測試策略**:

1. 單元測試：測試 Prompt 加載、緩存、版本管理
2. 集成測試：測試 Git 倉庫變更觸發熱重載
3. 性能測試：測試 Prompt 緩存命中率和響應時間
4. 版本測試：測試多版本 Prompt 共存和切換

---

#### **US-F14-003: 分佈式鎖與速率限制**

**User Story**:  
作為系統管理員，我希望使用 Redis 分佈式鎖保證操作原子性，並實現 API 速率限制防止濫用。

**場景描述（分佈式鎖）**:

- 多個實例同時嘗試發布 Workflow
- 使用 Redis 分佈式鎖保證只有一個實例成功
- 鎖自動過期（防止死鎖）
- 鎖釋放後其他實例可繼續嘗試

**場景描述（速率限制）**:

- 用戶/IP 調用 API 頻率過高
- Redis 記錄每個用戶的請求計數（滑動窗口）
- 超過限制時返回 429 Too Many Requests
- 1 分鐘後自動重置計數器

**Acceptance Criteria（分佈式鎖）**:

1. ✅ 支持可重入鎖（同一線程可多次獲取）
2. ✅ 鎖自動過期時間 30 秒（可配置）
3. ✅ 鎖釋放使用 Lua 腳本保證原子性
4. ✅ 獲取鎖失敗時支持重試（指數退避）
5. ✅ 監控指標：鎖競爭次數、鎖持有時間

**Acceptance Criteria（速率限制）**:

1. ✅ 默認速率限制：100 請求/分鐘（按用戶 ID）
2. ✅ IP 速率限制：500 請求/分鐘（防止未認證濫用）
3. ✅ 白名單：管理員和系統賬號不受限制
4. ✅ 響應頭包含：`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
5. ✅ 超限時返回 429 狀態碼和重試時間

**技術實現（分佈式鎖）**:

```python
# core/distributed_lock.py
import asyncio
import uuid
from typing import Optional
from redis.asyncio import Redis

class DistributedLock:
    def __init__(self, redis: Redis, lock_name: str, timeout: int = 30):
        self.redis = redis
        self.lock_name = f"lock:{lock_name}"
        self.timeout = timeout
        self.token = str(uuid.uuid4())  # Unique token for this lock holder
    
    async def acquire(self, blocking: bool = True, retry_delay: float = 0.1) -> bool:
        """獲取分佈式鎖"""
        while True:
            # Try to set lock with NX (only if not exists) and EX (expiration)
            acquired = await self.redis.set(
                self.lock_name,
                self.token,
                nx=True,  # Only set if key doesn't exist
                ex=self.timeout  # Auto-expire after timeout
            )
            
            if acquired:
                print(f"🔒 Acquired lock: {self.lock_name}")
                return True
            
            if not blocking:
                return False
            
            # Exponential backoff
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 1.0)  # Max 1 second
    
    async def release(self):
        """釋放分佈式鎖（使用 Lua 腳本保證原子性）"""
        # Lua script to check token and delete atomically
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        released = await self.redis.eval(lua_script, 1, self.lock_name, self.token)
        
        if released:
            print(f"🔓 Released lock: {self.lock_name}")
        else:
            print(f"⚠️ Lock already released or expired: {self.lock_name}")
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()

# 使用示例
from core.cache import RedisCache

cache = RedisCache()

async def publish_workflow(workflow_id: str):
    """發布 Workflow（使用分佈式鎖保證只有一個實例執行）"""
    lock = DistributedLock(cache.redis, f"publish_workflow:{workflow_id}", timeout=30)
    
    async with lock:
        # Critical section - only one instance can execute this
        workflow = await load_workflow_from_db(workflow_id)
        workflow['status'] = 'published'
        workflow['published_at'] = datetime.now()
        await save_workflow_to_db(workflow)
        
        # Invalidate cache
        await cache.invalidate_workflow(workflow_id)
        
        print(f"✅ Published workflow: {workflow_id}")
```

**技術實現（速率限制）**:

```python
# core/rate_limiter.py
from typing import Optional
from redis.asyncio import Redis
from datetime import datetime

class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int = 100,
        window: int = 60
    ) -> dict:
        """
        檢查速率限制（滑動窗口算法）
        
        Args:
            key: 用戶 ID 或 IP 地址
            limit: 允許的最大請求數
            window: 時間窗口（秒）
        
        Returns:
            {
                "allowed": bool,
                "limit": int,
                "remaining": int,
                "reset": int (timestamp)
            }
        """
        now = datetime.now().timestamp()
        window_start = now - window
        
        cache_key = f"rate_limit:{key}"
        
        # Use Redis sorted set to track requests with timestamps
        pipe = self.redis.pipeline()
        
        # Remove old requests outside the window
        pipe.zremrangebyscore(cache_key, 0, window_start)
        
        # Count requests in current window
        pipe.zcard(cache_key)
        
        # Add current request
        pipe.zadd(cache_key, {str(now): now})
        
        # Set expiration
        pipe.expire(cache_key, window)
        
        results = await pipe.execute()
        request_count = results[1]
        
        allowed = request_count < limit
        remaining = max(0, limit - request_count - 1)
        reset = int(now + window)
        
        return {
            "allowed": allowed,
            "limit": limit,
            "remaining": remaining,
            "reset": reset,
            "current_count": request_count
        }

# FastAPI middleware
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis: Redis):
        super().__init__(app)
        self.rate_limiter = RateLimiter(redis)
        self.whitelist = ["admin@company.com", "system@company.com"]
    
    async def dispatch(self, request: Request, call_next):
        # Get user ID or IP
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
        ip_address = request.client.host
        
        # Check whitelist
        if user_id in self.whitelist:
            return await call_next(request)
        
        # Check rate limit (prefer user_id, fallback to IP)
        key = user_id or ip_address
        limit_result = await self.rate_limiter.check_rate_limit(
            key=key,
            limit=100 if user_id else 500,  # Higher limit for authenticated users
            window=60
        )
        
        # Add headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit_result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(limit_result["reset"])
        
        if not limit_result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {limit_result['reset'] - int(datetime.now().timestamp())} seconds"
            )
        
        return response

# 應用 middleware
from fastapi import FastAPI
app = FastAPI()
app.add_middleware(RateLimitMiddleware, redis=cache.redis)
```

**監控指標**:

```python
# core/metrics.py
from prometheus_client import Counter, Histogram

lock_acquisitions = Counter('redis_lock_acquisitions_total', 'Total lock acquisitions', ['lock_name'])
lock_contentions = Counter('redis_lock_contentions_total', 'Lock contention events', ['lock_name'])
lock_hold_time = Histogram('redis_lock_hold_seconds', 'Lock hold duration', ['lock_name'])

rate_limit_hits = Counter('rate_limit_hits_total', 'Rate limit exceeded', ['endpoint', 'user_type'])
rate_limit_requests = Counter('rate_limit_requests_total', 'Total rate-limited requests', ['endpoint'])
```

**測試策略**:

1. 並發測試：使用 asyncio 模擬多實例競爭鎖
2. 壓力測試：測試高並發下的速率限制準確性
3. 故障測試：測試 Redis 不可用時的降級行為
4. 性能測試：測試分佈式鎖對 API 延遲的影響

---

#### **US-F14-004: 會話管理與緩存監控**

**User Story**:  
作為系統管理員，我希望使用 Redis 管理用戶會話並監控緩存性能，以便優化系統資源使用。

**場景描述（會話管理）**:

- 用戶登入後生成會話 Token
- 會話信息存儲在 Redis（用戶 ID、權限、過期時間）
- 每次 API 請求驗證會話有效性
- 會話過期後自動清理

**場景描述（緩存監控）**:

- 實時監控緩存命中率、未命中率
- 監控 Redis 內存使用、連接數
- 監控熱點 Key（最常訪問的數據）
- 告警：緩存命中率 <80% 或內存使用 >90%

**Acceptance Criteria（會話管理）**:

1. ✅ 會話 TTL = 24 小時（可配置）
2. ✅ 支持會話續期（用戶活動時自動延長）
3. ✅ 支持單點登出（刪除 Redis 會話）
4. ✅ 支持多設備登入（每個設備獨立會話）
5. ✅ 會話信息包含：用戶 ID、角色、權限列表、設備信息

**Acceptance Criteria（緩存監控）**:

1. ✅ Dashboard 顯示：命中率、未命中率、平均響應時間
2. ✅ 顯示 Top 10 熱點 Key
3. ✅ Redis INFO 指標：內存使用、連接數、鍵數量
4. ✅ 告警規則：命中率 <80% 或內存使用 >90%
5. ✅ 支持手動清理過期緩存（`POST /api/cache/cleanup`）

**技術實現（會話管理）**:

```python
# core/session_manager.py
import json
from typing import Optional
from datetime import timedelta
from redis.asyncio import Redis

class SessionManager:
    def __init__(self, redis: Redis, session_ttl: int = 86400):
        self.redis = redis
        self.session_ttl = session_ttl  # 24 hours
    
    async def create_session(self, user_id: str, user_data: dict, device_id: str) -> str:
        """創建新會話"""
        import secrets
        session_token = secrets.token_urlsafe(32)
        
        session_key = f"session:{session_token}"
        session_data = {
            "user_id": user_id,
            "roles": user_data.get("roles", []),
            "permissions": user_data.get("permissions", []),
            "device_id": device_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        await self.redis.setex(
            session_key,
            self.session_ttl,
            json.dumps(session_data)
        )
        
        # Track user's active sessions
        user_sessions_key = f"user_sessions:{user_id}"
        await self.redis.sadd(user_sessions_key, session_token)
        await self.redis.expire(user_sessions_key, self.session_ttl)
        
        print(f"✅ Created session for user {user_id}: {session_token[:10]}...")
        return session_token
    
    async def get_session(self, session_token: str) -> Optional[dict]:
        """獲取會話信息"""
        session_key = f"session:{session_token}"
        session_data = await self.redis.get(session_key)
        
        if not session_data:
            return None
        
        return json.loads(session_data)
    
    async def refresh_session(self, session_token: str):
        """續期會話（用戶活動時調用）"""
        session_key = f"session:{session_token}"
        session_data = await self.get_session(session_token)
        
        if session_data:
            session_data["last_activity"] = datetime.now().isoformat()
            await self.redis.setex(
                session_key,
                self.session_ttl,
                json.dumps(session_data)
            )
    
    async def delete_session(self, session_token: str):
        """登出（刪除會話）"""
        session_data = await self.get_session(session_token)
        if session_data:
            user_id = session_data["user_id"]
            
            # Remove session
            session_key = f"session:{session_token}"
            await self.redis.delete(session_key)
            
            # Remove from user's active sessions
            user_sessions_key = f"user_sessions:{user_id}"
            await self.redis.srem(user_sessions_key, session_token)
            
            print(f"🚪 Logged out user {user_id}")
    
    async def get_user_sessions(self, user_id: str) -> list:
        """獲取用戶的所有活躍會話"""
        user_sessions_key = f"user_sessions:{user_id}"
        session_tokens = await self.redis.smembers(user_sessions_key)
        
        sessions = []
        for token in session_tokens:
            session_data = await self.get_session(token)
            if session_data:
                sessions.append({
                    "token": token[:10] + "...",
                    "device_id": session_data.get("device_id"),
                    "last_activity": session_data.get("last_activity")
                })
        
        return sessions

# FastAPI 集成
from fastapi import Request, HTTPException, Depends

async def get_current_user(request: Request, session_manager: SessionManager = Depends()):
    """驗證會話並獲取當前用戶"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    session_token = auth_header.split(" ")[1]
    session_data = await session_manager.get_session(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Refresh session on activity
    await session_manager.refresh_session(session_token)
    
    return session_data

# API endpoints
@router.post("/api/auth/login")
async def login(username: str, password: str, device_id: str, session_manager: SessionManager = Depends()):
    # Authenticate user (omitted)
    user_data = authenticate_user(username, password)
    
    # Create session
    session_token = await session_manager.create_session(
        user_id=user_data["user_id"],
        user_data=user_data,
        device_id=device_id
    )
    
    return {"access_token": session_token, "token_type": "bearer"}

@router.post("/api/auth/logout")
async def logout(session_token: str, session_manager: SessionManager = Depends()):
    await session_manager.delete_session(session_token)
    return {"status": "logged_out"}
```

**技術實現（緩存監控）**:

```python
# core/cache_monitor.py
from typing import Dict, List
from redis.asyncio import Redis

class CacheMonitor:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get_cache_stats(self) -> Dict:
        """獲取緩存統計信息"""
        info = await self.redis.info()
        
        # Calculate hit rate
        keyspace_hits = info.get('keyspace_hits', 0)
        keyspace_misses = info.get('keyspace_misses', 0)
        total_requests = keyspace_hits + keyspace_misses
        hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_rate": round(hit_rate, 2),
            "total_hits": keyspace_hits,
            "total_misses": keyspace_misses,
            "memory_used_mb": info.get('used_memory', 0) / 1024 / 1024,
            "memory_peak_mb": info.get('used_memory_peak', 0) / 1024 / 1024,
            "total_keys": info.get('db0', {}).get('keys', 0),
            "connected_clients": info.get('connected_clients', 0),
            "uptime_days": info.get('uptime_in_days', 0)
        }
    
    async def get_hot_keys(self, limit: int = 10) -> List[Dict]:
        """獲取熱點 Key（需要 Redis 4.0+ 的 OBJECT FREQ 命令）"""
        # This is a simplified version - in production use Redis's built-in tracking
        all_keys = await self.redis.keys("*")
        
        hot_keys = []
        for key in all_keys[:100]:  # Sample first 100 keys
            ttl = await self.redis.ttl(key)
            memory = await self.redis.memory_usage(key) or 0
            
            hot_keys.append({
                "key": key,
                "ttl": ttl,
                "memory_bytes": memory
            })
        
        # Sort by memory usage (proxy for access frequency)
        hot_keys.sort(key=lambda x: x['memory_bytes'], reverse=True)
        return hot_keys[:limit]
    
    async def cleanup_expired_keys(self) -> int:
        """手動清理過期 Key（Redis 自動清理，這是補充）"""
        # Get all keys with TTL
        all_keys = await self.redis.keys("*")
        deleted = 0
        
        for key in all_keys:
            ttl = await self.redis.ttl(key)
            if ttl == -1:  # No expiration set
                # Optionally set default expiration
                pass
        
        return deleted

# API endpoints
@router.get("/api/cache/stats")
async def get_cache_stats(monitor: CacheMonitor = Depends()):
    """獲取緩存統計"""
    return await monitor.get_cache_stats()

@router.get("/api/cache/hot-keys")
async def get_hot_keys(limit: int = 10, monitor: CacheMonitor = Depends()):
    """獲取熱點 Key"""
    return await monitor.get_hot_keys(limit)

@router.post("/api/cache/cleanup")
async def cleanup_cache(monitor: CacheMonitor = Depends()):
    """手動清理過期緩存"""
    deleted = await monitor.cleanup_expired_keys()
    return {"deleted_keys": deleted}
```

**Grafana Dashboard 配置**:

```yaml
# grafana/dashboards/redis-cache.json
{
  "dashboard": {
    "title": "Redis Cache Performance",
    "panels": [
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "redis_memory_used_bytes / 1024 / 1024"
          }
        ]
      },
      {
        "title": "Connected Clients",
        "targets": [
          {
            "expr": "redis_connected_clients"
          }
        ]
      }
    ]
  }
}
```

**測試策略**:

1. 會話測試：測試登入、登出、會話過期、多設備登入
2. 監控測試：驗證緩存統計指標準確性
3. 性能測試：測試高並發下的會話驗證性能
4. 安全測試：測試會話劫持防護、Token 泄露風險

---

### 14.3 數據庫架構（Redis 數據結構）

```text
# Redis Key 命名規範
workflow:{workflow_id}              -> JSON (Workflow 定義)
agent:{agent_id}                    -> JSON (Agent 配置)
prompt:{prompt_name}:{version}      -> JSON (Prompt 模板)
session:{session_token}             -> JSON (用戶會話)
user_sessions:{user_id}             -> SET (用戶的活躍會話列表)
lock:{resource_name}                -> STRING (分佈式鎖)
rate_limit:{user_id_or_ip}          -> SORTED SET (速率限制請求記錄)

# TTL 設置
workflow:*                          -> 1 hour
agent:*                             -> 30 minutes
prompt:*                            -> No expiration (手動失效)
session:*                           -> 24 hours
lock:*                              -> 30 seconds (自動過期)
rate_limit:*                        -> 60 seconds (滑動窗口)

# 示例數據
SET workflow:wf-001 '{"id": "wf-001", "name": "ServiceNow Ticket", ...}' EX 3600
SET session:abc123 '{"user_id": "u-001", "roles": ["admin"], ...}' EX 86400
ZADD rate_limit:u-001 1700000000.123 "1700000000.123"
```

---

### 14.4 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **性能** | 緩存命中率 | >90% | Prometheus 監控 |
| | Redis 響應時間 | <5ms (P95) | redis_exporter |
| | API 響應時間提升 | 減少 80% | APM 對比測試 |
| **可靠性** | Redis 可用性 | 99.9% | Sentinel 高可用 |
| | 數據持久化 | AOF + RDB 混合 | 定期備份驗證 |
| **可擴展性** | 支持併發連接數 | 10000+ | 負載測試 |
| | 內存使用 | <16 GB | Redis INFO 監控 |
| **安全性** | 速率限制準確性 | >99% | 壓力測試驗證 |
| | 會話劫持防護 | Token 綁定 IP/Device | 安全審計 |

---

### 14.5 測試策略

**單元測試**:

- 測試緩存讀寫、失效邏輯
- 測試分佈式鎖獲取/釋放
- 測試速率限制計數器
- 測試會話創建/驗證/過期

**集成測試**:

- 測試 Redis 與數據庫數據一致性
- 測試多實例環境下的分佈式鎖
- 測試緩存失效觸發機制

**性能測試**:

- 基準測試：對比有/無緩存的 API 響應時間
- 負載測試：測試 10000 併發請求的緩存性能
- 壓力測試：測試 Redis 內存不足時的降級行為

**故障測試**:

- 測試 Redis 不可用時的降級（直接查詢數據庫）
- 測試 Redis 內存滿時的 LRU 淘汰策略
- 測試網絡分區時的 Sentinel 故障轉移

---

### 14.6 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| Redis 單點故障 | 中 | 高 | Redis Sentinel 3 節點高可用 |
| 緩存雪崩（大量 Key 同時過期） | 中 | 高 | 隨機 TTL + 緩存預熱 |
| 緩存穿透（惡意查詢不存在的數據） | 低 | 中 | 布隆過濾器 + 空值緩存 |
| 內存溢出 | 中 | 高 | LRU 淘汰策略 + 監控告警 |
| 熱點 Key 性能瓶頸 | 低 | 中 | 本地緩存（Caffeine）+ Redis |

---

### 14.7 未來增強（MVP 後）

1. **Redis Cluster**: 支持數據分片和水平擴展
2. **多級緩存**: 本地緩存（L1）+ Redis（L2）+ DB（L3）
3. **緩存預測**: 使用 ML 預測熱點數據並預加載
4. **智能淘汰**: 根據業務價值（而非訪問頻率）淘汰數據
5. **跨區域同步**: Redis 跨數據中心同步（Geo-Replication）

---

**✅ F14 完成**：Redis 緩存系統功能規範已完整編寫（4 個用戶故事、數據結構設計、NFR、測試策略）。

---
