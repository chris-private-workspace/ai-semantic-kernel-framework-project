# Redis Cache 設計文檔

## 1. 概述

### 1.1 目的
Redis 作為高性能內存數據庫，在系統中主要用於：
- 會話管理（Session Management）
- API 響應緩存（Response Caching）
- 工作流執行狀態緩存（Execution State Caching）
- 分佈式鎖（Distributed Locks）
- 速率限制（Rate Limiting）
- 消息隊列（Message Queue - 簡單場景）

### 1.2 部署架構

**本地開發環境**：
- Docker Compose 運行單節點 Redis 7
- 無持久化（開發測試用）
- 端口：6379

**Azure 生產環境**：
- Azure Cache for Redis
- Staging: C1 (1GB, 共享)
- Production: P1 (6GB, 專用) 或 P2 (13GB, 專用)
- 啟用 AOF 持久化
- 啟用 Redis 6.0+ ACL

## 2. 緩存策略設計

### 2.1 緩存鍵命名規範

```
{namespace}:{resource}:{identifier}[:{sub_resource}]

範例：
- session:user:550e8400-e29b-41d4-a716-446655440000
- cache:workflow:550e8400-e29b-41d4-a716-446655440000:definition
- cache:execution:550e8400-e29b-41d4-a716-446655440000:status
- lock:workflow:550e8400-e29b-41d4-a716-446655440000:edit
- ratelimit:api:192.168.1.1:60s
```

### 2.2 過期策略（TTL）

| 資源類型 | TTL | 說明 |
|---------|-----|------|
| User Session | 24h | 用戶會話，可續期 |
| Workflow Definition | 1h | 工作流定義緩存 |
| Execution Status | 30min | 執行狀態，頻繁更新 |
| API Response | 5-15min | 根據數據變化頻率調整 |
| Distributed Lock | 30s-5min | 避免死鎖 |
| Rate Limit Counter | 60s-3600s | 根據限流窗口 |

### 2.3 緩存失效策略

**Write-Through（寫穿）**：
```python
def update_workflow(workflow_id, data):
    # 1. 更新數據庫
    db.update(workflow_id, data)
    # 2. 更新緩存
    cache.set(f"cache:workflow:{workflow_id}", data, ttl=3600)
    # 3. 發布失效事件（可選）
    cache.publish(f"invalidate:workflow:{workflow_id}", workflow_id)
```

**Cache-Aside（旁路緩存）**：
```python
def get_workflow(workflow_id):
    # 1. 嘗試從緩存讀取
    data = cache.get(f"cache:workflow:{workflow_id}")
    if data:
        return data
    # 2. 緩存未命中，從數據庫讀取
    data = db.query(workflow_id)
    # 3. 寫入緩存
    cache.set(f"cache:workflow:{workflow_id}", data, ttl=3600)
    return data
```

**Write-Behind（寫回）**：
- 不適用於本系統（需要高數據一致性）

## 3. 功能設計

### 3.1 會話管理

**會話數據結構**：
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user@example.com",
  "is_superuser": false,
  "created_at": "2025-11-20T10:00:00Z",
  "last_activity": "2025-11-20T10:30:00Z",
  "permissions": ["workflow:read", "workflow:create"]
}
```

**操作**：
- `SETEX session:user:{session_id} 86400 {json_data}` - 創建會話
- `GET session:user:{session_id}` - 獲取會話
- `EXPIRE session:user:{session_id} 86400` - 續期
- `DEL session:user:{session_id}` - 登出

### 3.2 分佈式鎖

**使用場景**：
- 工作流編輯鎖（防止並發編輯）
- 執行實例創建鎖（防止重複執行）
- 配置更新鎖

**實現（Redlock 算法）**：
```python
# 獲取鎖
SET lock:workflow:{id}:edit {token} NX EX 30

# 釋放鎖（使用 Lua 腳本保證原子性）
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
```

### 3.3 速率限制

**Fixed Window（固定窗口）**：
```python
# 每分鐘最多 60 次請求
key = f"ratelimit:api:{client_ip}:60s"
current = INCR key
if current == 1:
    EXPIRE key 60
if current > 60:
    raise RateLimitExceeded
```

**Sliding Window（滑動窗口）**：
```python
# 使用 Sorted Set 實現更精確的滑動窗口
key = f"ratelimit:api:{client_ip}:sliding"
now = time.time()
ZADD key now now  # score 和 member 都是時間戳
ZREMRANGEBYSCORE key 0 (now - 60)  # 移除 60 秒前的記錄
count = ZCARD key
if count > 60:
    raise RateLimitExceeded
EXPIRE key 60
```

### 3.4 執行狀態緩存

**狀態數據結構**：
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "running",
  "current_step": 3,
  "total_steps": 10,
  "started_at": "2025-11-20T10:00:00Z",
  "progress": 0.3
}
```

**實時更新**：
- 使用 Redis Pub/Sub 推送狀態變更
- 使用 Redis Streams 記錄執行日誌流

## 4. 數據結構選擇

### 4.1 String
**用途**：簡單鍵值對、Session、緩存
```redis
SET cache:workflow:123 '{"name": "..."}'
GET cache:workflow:123
```

### 4.2 Hash
**用途**：存儲對象屬性、用戶資料
```redis
HSET user:123 username "john" email "john@example.com"
HGETALL user:123
```

### 4.3 List
**用途**：執行歷史、日誌隊列
```redis
LPUSH execution:123:logs "Step 1 completed"
LRANGE execution:123:logs 0 -1
```

### 4.4 Set
**用途**：標籤、權限集合
```redis
SADD workflow:123:tags "production" "critical"
SMEMBERS workflow:123:tags
```

### 4.5 Sorted Set
**用途**：排行榜、滑動窗口、優先級隊列
```redis
ZADD workflow:executions:recent 1700000000 "exec123"
ZRANGE workflow:executions:recent 0 -1 WITHSCORES
```

### 4.6 Stream
**用途**：執行日誌流、事件溯源
```redis
XADD execution:123:stream * level INFO message "Step completed"
XREAD STREAMS execution:123:stream 0
```

## 5. 連接管理

### 5.1 連接池配置

**開發環境**：
```python
redis_config = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "decode_responses": True,
    "max_connections": 50,
    "socket_keepalive": True,
    "socket_keepalive_options": {
        socket.TCP_KEEPIDLE: 60,
        socket.TCP_KEEPINTVL: 10,
        socket.TCP_KEEPCNT: 3
    },
    "health_check_interval": 30,
    "retry_on_timeout": True,
    "socket_connect_timeout": 5,
    "socket_timeout": 5
}
```

**Azure 生產環境**：
```python
redis_config = {
    "host": "{cache-name}.redis.cache.windows.net",
    "port": 6380,
    "password": "{access-key}",
    "ssl": True,
    "ssl_cert_reqs": "required",
    "db": 0,
    "decode_responses": True,
    "max_connections": 100,
    "socket_keepalive": True,
    "health_check_interval": 30,
    "retry_on_timeout": True,
    "socket_connect_timeout": 10,
    "socket_timeout": 10
}
```

### 5.2 連接重試策略

**指數退避重試**：
```python
from redis.retry import Retry
from redis.backoff import ExponentialBackoff

retry = Retry(
    backoff=ExponentialBackoff(base=0.1, cap=2.0),
    retries=3
)
```

### 5.3 健康檢查

```python
def health_check():
    try:
        redis_client.ping()
        info = redis_client.info("server")
        return {
            "status": "healthy",
            "redis_version": info["redis_version"],
            "uptime_seconds": info["uptime_in_seconds"],
            "connected_clients": info["connected_clients"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## 6. 安全性設計

### 6.1 認證授權

**本地開發**：
- 無密碼（Docker 內網訪問）

**Azure 生產**：
- Redis 訪問密鑰（Primary/Secondary）
- SSL/TLS 加密傳輸
- ACL（Access Control List）

### 6.2 數據加密

**傳輸加密**：
- 使用 SSL/TLS（Azure 強制 6380 端口）
- 證書驗證

**敏感數據加密**：
```python
def encrypt_session_data(data: dict) -> str:
    """加密敏感會話數據"""
    encrypted = fernet.encrypt(json.dumps(data).encode())
    return base64.b64encode(encrypted).decode()

def decrypt_session_data(encrypted: str) -> dict:
    """解密會話數據"""
    decoded = base64.b64decode(encrypted.encode())
    decrypted = fernet.decrypt(decoded)
    return json.loads(decrypted.decode())
```

### 6.3 防止緩存穿透/雪崩

**緩存穿透（查詢不存在的數據）**：
```python
# 使用空值緩存
if data is None:
    cache.set(key, "NULL", ttl=60)  # 短期緩存空值
```

**緩存雪崩（大量緩存同時過期）**：
```python
# TTL 加隨機值
import random
ttl = base_ttl + random.randint(0, 300)  # 3600 ± 5min
cache.set(key, data, ttl=ttl)
```

**緩存擊穿（熱點數據過期）**：
```python
# 使用分佈式鎖
lock_key = f"lock:rebuild:{key}"
if cache.set(lock_key, "1", nx=True, ex=10):
    try:
        data = db.query(...)
        cache.set(key, data, ttl=3600)
    finally:
        cache.delete(lock_key)
else:
    time.sleep(0.1)
    return cache.get(key)  # 等待其他進程重建緩存
```

## 7. 監控與運維

### 7.1 關鍵指標

**性能指標**：
- `hit_rate` - 緩存命中率（目標 >80%）
- `evicted_keys` - 驅逐鍵數量
- `expired_keys` - 過期鍵數量
- `connected_clients` - 連接客戶端數
- `used_memory` - 內存使用量
- `ops_per_sec` - 每秒操作數

**可用性指標**：
- `uptime` - 運行時間
- `rejected_connections` - 拒絕連接數
- `sync_partial_ok/err` - 主從同步狀態

### 7.2 慢查詢日誌

```redis
# 配置慢查詢閾值（微秒）
CONFIG SET slowlog-log-slower-than 10000  # 10ms

# 查看慢查詢
SLOWLOG GET 10
```

### 7.3 Azure Monitor 集成

**診斷設置**：
- 啟用 Redis 慢查詢日誌
- 啟用連接日誌
- 配置 Log Analytics 工作區

**告警規則**：
- 緩存命中率 < 70%
- 內存使用率 > 90%
- 連接數 > 閾值
- 錯誤率 > 1%

## 8. 最佳實踐

### 8.1 Key 設計原則

1. **使用有意義的命名空間**
2. **避免過長的 Key（<256 bytes）**
3. **使用一致的分隔符（:）**
4. **包含版本號（如需要）**：`cache:v2:workflow:123`

### 8.2 值大小限制

- **單個值 < 512MB**（理論上限）
- **實踐建議 < 100KB**（避免大 Key）
- **使用壓縮**（gzip/lz4）處理大值

### 8.3 批量操作

**使用 Pipeline 減少 RTT**：
```python
pipe = redis.pipeline()
pipe.set("key1", "value1")
pipe.set("key2", "value2")
pipe.set("key3", "value3")
results = pipe.execute()
```

**使用 MGET/MSET**：
```python
# 一次獲取多個鍵
values = redis.mget(["key1", "key2", "key3"])

# 一次設置多個鍵
redis.mset({"key1": "value1", "key2": "value2"})
```

### 8.4 避免阻塞操作

**避免**：
- `KEYS *`（掃描所有鍵，O(n)）
- `FLUSHALL/FLUSHDB`（生產環境）
- `SAVE`（同步持久化，阻塞）

**推薦**：
- `SCAN`（遊標迭代）
- `BGSAVE`（後台持久化）
- 使用 TTL 自動過期

### 8.5 Lua 腳本

**原子操作示例**：
```lua
-- 分佈式鎖釋放腳本
local key = KEYS[1]
local token = ARGV[1]
if redis.call("get", key) == token then
    return redis.call("del", key)
else
    return 0
end
```

## 9. 容量規劃

### 9.1 內存估算

**估算公式**：
```
Total Memory = (Key Size + Value Size + Overhead) × Key Count × Safety Factor

Overhead ≈ 90 bytes per key (Redis 7)
Safety Factor = 1.5-2.0（預留增長空間）
```

**示例**：
- 100,000 個用戶會話
- 每個會話 2KB
- Overhead: 90 bytes/key
- 總計: (90 + 2048) × 100,000 × 1.5 ≈ 320MB

### 9.2 Azure Cache for Redis SKU 選擇

| SKU | 內存 | 連接數 | 吞吐量 | 適用場景 |
|-----|------|--------|--------|----------|
| C0 | 250MB | 256 | 低 | 開發測試 |
| C1 | 1GB | 1000 | 低 | Staging |
| C2 | 2.5GB | 2000 | 中 | 小型生產 |
| P1 | 6GB | 7500 | 高 | 生產環境 |
| P2 | 13GB | 7500 | 高 | 大型生產 |

## 10. 故障恢復

### 10.1 持久化策略

**RDB（快照）**：
- 定期生成數據快照
- 恢復速度快
- 可能丟失最後一次快照後的數據

**AOF（追加文件）**：
- 記錄每個寫操作
- 數據安全性高
- 文件較大，恢復較慢

**Azure 推薦**：
- 啟用 AOF
- 定期備份到 Storage Account

### 10.2 災難恢復計劃

**備份策略**：
- 每日自動備份（保留 7 天）
- 每週備份（保留 4 週）
- 手動備份（重大變更前）

**恢復流程**：
1. 創建新 Redis 實例
2. 從備份恢復數據
3. 更新應用配置
4. 驗證數據完整性
5. 切換流量

## 11. 開發測試指南

### 11.1 本地開發環境

**啟動 Redis**：
```bash
docker-compose up -d redis
```

**連接測試**：
```bash
docker exec -it redis redis-cli
> PING
PONG
> SET test "Hello Redis"
OK
> GET test
"Hello Redis"
```

### 11.2 單元測試

**使用 fakeredis 進行測試**：
```python
import fakeredis
import pytest

@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)

def test_cache_set_get(redis_client):
    redis_client.set("test", "value", ex=60)
    assert redis_client.get("test") == "value"
    assert redis_client.ttl("test") > 0
```

### 11.3 性能測試

**使用 redis-benchmark**：
```bash
# 測試 10000 次 SET 操作
redis-benchmark -t set -n 10000 -q

# 測試 Pipeline 性能
redis-benchmark -t set,get -n 100000 -P 16 -q
```

## 12. 遷移計劃

### 12.1 從無緩存到 Redis

**階段 1：基礎設施**
- 部署 Redis（本地 Docker）
- 配置連接池
- 實現基礎 Cache Service

**階段 2：會話管理**
- 遷移 Session 到 Redis
- 實現 Session 中間件

**階段 3：API 緩存**
- 識別緩存候選 API
- 實現 Cache 裝飾器
- 逐步啟用緩存

**階段 4：高級功能**
- 分佈式鎖
- 速率限制
- 執行狀態緩存

### 12.2 數據遷移

**Session 遷移**：
```python
# 從舊存儲讀取 Session
old_sessions = old_storage.get_all_sessions()

# 批量寫入 Redis
pipe = redis.pipeline()
for session_id, session_data in old_sessions.items():
    key = f"session:user:{session_id}"
    pipe.setex(key, 86400, json.dumps(session_data))
pipe.execute()
```

## 13. 參考資料

- [Redis 官方文檔](https://redis.io/docs/)
- [Azure Cache for Redis 文檔](https://docs.microsoft.com/azure/azure-cache-for-redis/)
- [Redis Python Client (redis-py)](https://redis-py.readthedocs.io/)
- [Redis 最佳實踐](https://redis.io/docs/manual/patterns/)
