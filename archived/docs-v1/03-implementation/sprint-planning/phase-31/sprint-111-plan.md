# Sprint 111: Quick Wins + Auth Foundation

## 概述

Sprint 111 是 Phase 31 的第一個 Sprint，專注於立即修復已知的安全速效問題（CORS、Vite proxy、JWT、console.log、Docker 憑證），並建立全局 Auth Middleware 作為後續安全工作的基礎。

## 目標

1. 修復 CORS origin 端口不匹配 (3000→3005)
2. 修復 Vite proxy target 端口不匹配 (8010→8000)
3. JWT Secret 從硬編碼改為環境變量
4. 清理 authStore PII 洩漏的 console.log
5. Docker 預設憑證環境變量化
6. Uvicorn reload 設定環境感知
7. 全局 Auth Middleware 覆蓋全部 528 端點
8. Sessions 偽認證修復
9. Rate Limiting 基礎設施

## Story Points: 40 點

## 前置條件

- ✅ Phase 29 完成 (Agent Swarm 可視化)
- ✅ 6 位領域專家分析報告完成
- ✅ IPA Platform 統一改善方案建議書完成

## 任務分解

### Story 111-1: CORS Origin 修復 (0.5h, P0)

**目標**: 修復後端 CORS 允許來源端口，從 3000 改為 3005（前端實際端口）

**交付物**:
- 修改 `backend/src/core/config.py`

**修改方式**:

找到 `CORS_ORIGINS` 配置，將 `http://localhost:3000` 修改為 `http://localhost:3005`。如果是列表形式，同時確認包含 `http://localhost:3005`。同步檢查是否有其他文件引用 port 3000 的 CORS 配置。

```python
# Before
CORS_ORIGINS = ["http://localhost:3000", ...]

# After
CORS_ORIGINS = ["http://localhost:3005", ...]
```

**驗收標準**:
- [ ] CORS_ORIGINS 包含 http://localhost:3005
- [ ] 不再包含 http://localhost:3000
- [ ] 前端請求不再出現 CORS 錯誤

### Story 111-2: Vite Proxy 修復 (0.5h, P0)

**目標**: 修復前端 Vite 開發伺服器的 proxy target 端口，從 8010 改為 8000（後端實際端口）

**交付物**:
- 修改 `frontend/vite.config.ts`

**修改方式**:

找到 proxy 配置中 target 為 `http://localhost:8010` 的部分，修改為 `http://localhost:8000`。

```typescript
// Before
proxy: {
  '/api': {
    target: 'http://localhost:8010',
    ...
  }
}

// After
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    ...
  }
}
```

**驗收標準**:
- [ ] Vite proxy target 指向 http://localhost:8000
- [ ] 前端 API 請求可正確代理到後端

### Story 111-3: JWT Secret 環境變量化 (2h, P0)

**目標**: 找出 3 處硬編碼 JWT Secret 的位置，全部改為從環境變量讀取，並在啟動時驗證不安全值

**交付物**:
- 修改 JWT Secret 相關的 3 個文件（需先搜索確認位置）
- 新增/修改 `backend/src/core/config.py` 中的 JWT_SECRET 環境變量讀取
- 新增啟動時不安全值警告邏輯

**修改方式**:

1. 搜索 `backend/` 下所有硬編碼 JWT secret 字串（如 `"secret"`, `"your-secret-key"` 等）
2. 統一改為從 `settings.JWT_SECRET` 或 `os.environ["JWT_SECRET"]` 讀取
3. 在應用啟動時檢查 JWT_SECRET 值，若為常見不安全值（"secret", "your-secret-key", "changeme" 等）則記錄 WARNING

```python
# config.py
JWT_SECRET: str = os.environ.get("JWT_SECRET", "")

# startup validation
UNSAFE_SECRETS = {"secret", "your-secret-key", "changeme", "jwt-secret", ""}
if settings.JWT_SECRET in UNSAFE_SECRETS:
    logger.warning("JWT_SECRET is set to an unsafe value! Change it in production.")
```

**驗收標準**:
- [ ] 0 處硬編碼 JWT Secret
- [ ] JWT_SECRET 從環境變量讀取
- [ ] 不安全值啟動時 WARNING 日誌
- [ ] .env.example 中包含 JWT_SECRET 配置說明

### Story 111-4: authStore console.log 清理 (0.5h, P0)

**目標**: 移除 `frontend/src/stores/authStore.ts` 中的 5 個 console.log 語句，防止 PII（個人可識別資訊）洩漏到瀏覽器控制台

**交付物**:
- 修改 `frontend/src/stores/authStore.ts`

**修改方式**:

搜索 `authStore.ts` 中所有 `console.log` 語句，全部移除或替換為條件化的 debug 輸出（僅在 development 環境）。注意不要移除 `console.error` — 錯誤日誌應保留。

```typescript
// Before
console.log('User logged in:', userData);

// After (移除，不替換)
// 或替換為安全版本：
if (import.meta.env.DEV) {
  console.debug('[AuthStore] Login event');  // 不含用戶資料
}
```

**驗收標準**:
- [ ] authStore.ts 中 0 個 console.log 語句
- [ ] 不洩漏用戶資料到控制台
- [ ] console.error 保留（錯誤處理不受影響）

### Story 111-5: Docker 預設憑證修復 (0.25h, P0)

**目標**: 移除 docker-compose 中 n8n 和 Grafana 的預設弱密碼 `admin/admin123`

**交付物**:
- 修改 `docker-compose.yml`（及 override 文件若存在）

**修改方式**:

將 n8n 和 Grafana 的 admin 密碼從硬編碼值改為環境變量引用：

```yaml
# Before
environment:
  - GF_SECURITY_ADMIN_PASSWORD=admin123

# After
environment:
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-please-change-me}
```

在 `.env.example` 中添加對應的環境變量模板。

**驗收標準**:
- [ ] docker-compose 中無硬編碼 admin/admin123
- [ ] 密碼從環境變量讀取
- [ ] .env.example 包含密碼模板

### Story 111-6: Uvicorn reload 環境感知 (0.5h, P0)

**目標**: 將 Uvicorn 的 `reload=True` 從硬編碼改為環境感知，僅在 development 環境啟用

**交付物**:
- 修改 `backend/main.py` 或 Uvicorn 啟動配置

**修改方式**:

```python
# Before
uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)

# After
import os
env = os.environ.get("ENVIRONMENT", "development")
uvicorn.run(
    "main:app",
    reload=(env == "development"),
    host="0.0.0.0",
    port=8000,
    workers=1 if env == "development" else 4
)
```

**驗收標準**:
- [ ] reload 僅在 development 環境為 True
- [ ] production 環境 reload=False
- [ ] 環境判斷基於 ENVIRONMENT 環境變量

### Story 111-7: 全局 Auth Middleware (3-4 天, P0)

**目標**: 實現基於 FastAPI Depends 的 JWT Auth Middleware，應用到所有 528 個端點，將 Auth 覆蓋率從 7% 提升到 100%

**交付物**:
- 新增/修改 `backend/src/core/auth.py` — 核心 JWT 驗證邏輯
- 修改 `backend/src/api/v1/__init__.py` — 全局 Depends 注入
- 修改各 router 模組（39 個 route 模組）

**修改方式**:

**Phase 1: 建立核心驗證函數**

```python
# backend/src/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """JWT Token 驗證，提取用戶資訊"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        return {"user_id": user_id, "email": payload.get("email"), **payload}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
```

**Phase 2: 全局注入策略**

在主 router 或 `api/v1/__init__.py` 中，對所有子路由統一注入 `dependencies=[Depends(get_current_user)]`。白名單路由（health check、登入、文檔）使用 `tags` 或獨立 router 排除。

```python
# backend/src/api/v1/__init__.py
from backend.src.core.auth import get_current_user

# 受保護的 router（所有業務端點）
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

# 公開的 router（health check, login, docs）
public_router = APIRouter()
```

**Phase 3: 白名單路由定義**

```python
# 無需認證的路由
PUBLIC_ROUTES = [
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/docs",
    "/redoc",
    "/openapi.json",
]
```

**驗收標準**:
- [ ] get_current_user 驗證函數完整實現
- [ ] 全部 528 端點（除白名單外）需要 JWT Token
- [ ] 未帶 Token 的請求返回 401
- [ ] Token 過期返回 401
- [ ] Health check、login、docs 無需認證
- [ ] 現有 38 個已有 auth 的端點仍正常運作
- [ ] 前端請求自動帶 Authorization header

### Story 111-8: Sessions 偽認證修復 (1 天, P0)

**目標**: 移除 `get_current_user_id()` 返回的硬編碼 UUID，改為從 JWT Token 中提取真實用戶 ID

**交付物**:
- 修改 Sessions 相關的 `get_current_user_id()` 函數
- 修改依賴該函數的所有端點

**修改方式**:

搜索 `get_current_user_id` 函數定義位置，替換為從 Story 111-7 建立的 `get_current_user` 中提取 `user_id`：

```python
# Before
def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000000"  # 硬編碼 UUID

# After
async def get_current_user_id(
    current_user: dict = Depends(get_current_user)
) -> str:
    return current_user["user_id"]
```

**驗收標準**:
- [ ] 無硬編碼 UUID
- [ ] user_id 從 JWT Token 提取
- [ ] 不同用戶的 session 數據隔離
- [ ] 依賴 get_current_user_id 的端點全部正常

### Story 111-9: Rate Limiting (0.5 天, P1)

**目標**: 使用 slowapi 添加全局 API Rate Limiting，防止 API 濫用

**交付物**:
- 新增 `slowapi` 到 `requirements.txt`
- 新增 `backend/src/middleware/rate_limit.py`
- 修改 `backend/main.py` 掛載 middleware

**修改方式**:

```python
# backend/src/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

def setup_rate_limiting(app):
    """設定 Rate Limiting middleware"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

```python
# main.py
from backend.src.middleware.rate_limit import setup_rate_limiting

app = FastAPI(...)
setup_rate_limiting(app)
```

預設限制：
- 全局：100 requests/minute per IP
- 登入端點：10 requests/minute per IP
- 敏感操作：30 requests/minute per IP
- Development 環境：放寬或停用

**驗收標準**:
- [ ] slowapi 正確安裝
- [ ] 全局 Rate Limiting 生效
- [ ] 超過限制返回 429 Too Many Requests
- [ ] Development 環境限制放寬
- [ ] 登入端點有更嚴格限制

## 技術設計

### 目錄結構變更

```
backend/src/
├── core/
│   ├── config.py            # 修改: CORS origin, JWT_SECRET
│   ├── auth.py              # 新增/修改: get_current_user, JWT 驗證
│   └── security.py          # 修改: JWT Secret 環境變量化
├── middleware/
│   └── rate_limit.py        # 新增: slowapi Rate Limiting
├── api/v1/
│   └── __init__.py          # 修改: 全局 Depends 注入
└── main.py                  # 修改: reload 環境感知, rate limiting

frontend/src/
├── stores/
│   └── authStore.ts         # 修改: 移除 console.log
└── vite.config.ts           # 修改: proxy target port

docker-compose.yml            # 修改: 預設憑證環境變量化
```

### 依賴

```
# 新增依賴
slowapi>=0.1.9
python-jose[cryptography]>=3.3.0  # 確認已存在
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| 全局 Auth 導致前端全部 401 | 確保前端 AuthInterceptor 正確帶 Token；白名單路由不受影響 |
| JWT_SECRET 環境變量未設定 | 啟動時 WARNING 並使用 fallback（僅限 development） |
| Rate Limiting 影響自動化測試 | 測試環境停用或大幅放寬 |

## 完成標準

- [ ] 所有速效修復完成（CORS, Vite, JWT, console.log, Docker, reload）
- [ ] Auth 覆蓋率 100%
- [ ] Sessions 使用真實用戶 ID
- [ ] Rate Limiting 生效
- [ ] 所有現有測試仍通過
- [ ] 前端→後端 端到端通訊正常

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: TBD
