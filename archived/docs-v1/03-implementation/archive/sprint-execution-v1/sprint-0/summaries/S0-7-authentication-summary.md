# S0-7: Authentication Framework 完成總結

**Story ID**: S0-7
**Story Points**: 8
**完成日期**: 2025-11-20
**負責人**: Backend Team

---

## 📋 目標達成情況

✅ **主要目標**: 實現完整的 JWT 認證系統，包含用戶註冊、登入、Token 管理、權限控制

### 已完成項目

| 項目 | 狀態 | 說明 |
|-----|------|------|
| JWT Token 管理器 | ✅ | Access Token (30分鐘) + Refresh Token (7天) |
| 密碼安全管理 | ✅ | Bcrypt 哈希 (12 rounds) + 密碼強度驗證 |
| User Repository | ✅ | 完整的用戶數據持久化操作 |
| Authentication Service | ✅ | 註冊、登入、Token 刷新、登出、密碼修改 |
| FastAPI 依賴注入 | ✅ | `get_current_user`, `require_permission` 等 |
| API Endpoints | ✅ | 10 個完整的認證端點 |
| Rate Limiting | ✅ | 登入失敗限制 (Redis) |
| Token Revocation | ✅ | 登出時撤銷 Token (Redis) |
| 架構設計文檔 | ✅ | 完整的技術設計文檔 |
| 使用指南 | ✅ | 詳細的 API 使用文檔 |

---

## 📁 新增文件

### 核心實現文件

1. **JWT Token 管理** (`backend/src/infrastructure/auth/`)
   - `jwt_manager.py` (353 行) - JWT Token 創建、驗證、刷新
   - `password.py` (172 行) - 密碼哈希和強度驗證

2. **數據持久化** (`backend/src/infrastructure/database/repositories/`)
   - `user_repository.py` (195 行) - 用戶 CRUD 操作

3. **業務邏輯** (`backend/src/domain/auth/`)
   - `auth_service.py` (384 行) - 完整的認證業務邏輯
   - `schemas.py` (55 行) - Pydantic 數據模型

4. **API 層** (`backend/src/api/`)
   - `dependencies/auth.py` (167 行) - FastAPI 依賴注入
   - `v1/auth/routes.py` (318 行) - 10 個 API 端點

### 文檔文件

1. **架構設計**: `docs/03-implementation/authentication-design.md` (完整技術設計)
2. **使用指南**: `docs/04-usage/authentication-guide.md` (API 使用文檔)
3. **實現總結**: `docs/03-implementation/S0-7-authentication-summary.md` (本文檔)

### 配置更新

1. **配置文件**: `backend/src/core/config.py` (+7 行 JWT 配置)
2. **主應用**: `backend/main.py` (集成認證路由)

---

## 🔧 技術實現細節

### 1. JWT Token 設計

#### Access Token (30 分鐘)
```json
{
  "sub": "user_id (UUID)",
  "username": "johndoe",
  "is_superuser": false,
  "permissions": ["workflow:read", "workflow:create"],
  "exp": 1700000000,
  "iat": 1699998200,
  "type": "access",
  "jti": "unique-token-id"
}
```

#### Refresh Token (7 天)
```json
{
  "sub": "user_id (UUID)",
  "exp": 1700604800,
  "iat": 1699998200,
  "type": "refresh",
  "jti": "unique-token-id"
}
```

**關鍵特性**:
- ✅ 使用 `python-jose` 進行 Token 簽名和驗證
- ✅ HS256 算法 (可配置)
- ✅ JTI (JWT ID) 用於 Token 撤銷追蹤
- ✅ 分離的 Access 和 Refresh Token 過期時間

---

### 2. 密碼安全

```python
# Bcrypt 配置
DEFAULT_ROUNDS = 12  # 2^12 次迭代
MIN_LENGTH = 8       # 最短密碼長度

# 密碼強度要求
- 至少 8 個字符
- 至少 1 個大寫字母
- 至少 1 個小寫字母
- 至少 1 個數字
- 不能包含用戶名
```

**安全機制**:
- ✅ Bcrypt 自適應哈希 (可調整成本因子)
- ✅ 自動密碼強度驗證
- ✅ 密碼重哈希檢測 (當成本因子增加時)
- ✅ 防止明文密碼洩漏

---

### 3. 認證流程

#### 用戶註冊
```
Client → API → AuthService
        ↓
    驗證郵箱/用戶名唯一性
        ↓
    驗證密碼強度
        ↓
    Bcrypt 哈希密碼
        ↓
    創建用戶記錄 (Database)
        ↓
    返回用戶信息
```

#### 登入流程
```
Client → API → AuthService
        ↓
    檢查速率限制 (Redis)
        ↓
    查詢用戶 (Database)
        ↓
    驗證密碼 (Bcrypt)
        ↓
    創建 Token 對 (JWT)
        ↓
    更新最後登入時間
        ↓
    清除失敗登入記錄 (Redis)
        ↓
    返回 Access + Refresh Token
```

#### Token 刷新
```
Client → API → AuthService
        ↓
    檢查 Token 是否撤銷 (Redis)
        ↓
    驗證 Refresh Token (JWT)
        ↓
    查詢用戶狀態 (Database)
        ↓
    創建新 Access Token
        ↓
    返回新 Access Token
```

---

### 4. 權限系統

#### 權限格式
```
resource:action

例如:
- workflow:read        # 讀取工作流
- workflow:create      # 創建工作流
- workflow:*           # 工作流所有權限
- *:*                  # 所有權限 (Superuser)
```

#### FastAPI 集成
```python
# 方法 1: Dependency
@router.get(
    "/workflows",
    dependencies=[Depends(require_permission("workflow:read"))]
)

# 方法 2: 手動檢查
current_user = Depends(get_current_active_user)
if not user.is_superuser and "workflow:read" not in permissions:
    raise HTTPException(403)
```

---

### 5. 安全特性

#### Rate Limiting (Redis)
```python
MAX_LOGIN_ATTEMPTS = 5           # 最多失敗次數
LOGIN_ATTEMPT_WINDOW = 900       # 15 分鐘窗口
ACCOUNT_LOCKOUT_DURATION = 1800  # 鎖定 30 分鐘
```

**實現**:
- 每次登入失敗: `INCR login_attempts:username`
- 設置過期時間: `EXPIRE 900` (15 分鐘)
- 達到限制: 返回 429 Too Many Requests
- 登入成功: 清除計數器

#### Token Revocation (Redis)
```python
# 登出時撤銷 Token
key = f"revoked_token:{jti}"
ttl = (expires_at - now).total_seconds()
redis.set(key, "1", ex=ttl)

# 驗證時檢查
if redis.exists(f"revoked_token:{jti}"):
    raise TokenRevokedError()
```

---

## 🌐 API 端點

### 公開端點

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 註冊新用戶 |
| POST | `/api/v1/auth/login` | 登入 (OAuth2 form) |
| POST | `/api/v1/auth/login/json` | 登入 (JSON body) |
| POST | `/api/v1/auth/refresh` | 刷新 Access Token |

### 受保護端點 (需要認證)

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/v1/auth/me` | 獲取當前用戶信息 |
| POST | `/api/v1/auth/logout` | 登出 (撤銷 Token) |
| POST | `/api/v1/auth/change-password` | 修改密碼 |

### 管理員端點 (需要 Superuser)

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/v1/auth/users/{user_id}` | 獲取用戶資料 |
| PATCH | `/api/v1/auth/users/{user_id}/deactivate` | 停用用戶 |
| PATCH | `/api/v1/auth/users/{user_id}/activate` | 啟用用戶 |

---

## 📊 代碼統計

### 新增代碼量

| 類別 | 文件數 | 代碼行數 |
|------|--------|----------|
| 基礎設施層 | 2 | 525 |
| 數據持久化層 | 1 | 195 |
| 業務邏輯層 | 2 | 439 |
| API 層 | 2 | 485 |
| **總計** | **7** | **1,644** |

### 文檔

| 類別 | 文件數 | 字數 (估計) |
|------|--------|--------------|
| 架構設計 | 1 | ~5,000 |
| 使用指南 | 1 | ~8,000 |
| 實現總結 | 1 | ~2,500 |
| **總計** | **3** | **~15,500** |

---

## 🧪 測試建議

### 單元測試 (待實現)

```python
# tests/infrastructure/auth/test_jwt_manager.py
def test_create_access_token():
    """測試創建 Access Token"""
    pass

def test_verify_token():
    """測試驗證 Token"""
    pass

def test_expired_token():
    """測試過期 Token"""
    pass

# tests/infrastructure/auth/test_password.py
def test_hash_password():
    """測試密碼哈希"""
    pass

def test_verify_password():
    """測試密碼驗證"""
    pass

def test_password_strength_validation():
    """測試密碼強度驗證"""
    pass

# tests/domain/auth/test_auth_service.py
def test_register_user():
    """測試用戶註冊"""
    pass

def test_login():
    """測試登入"""
    pass

def test_rate_limiting():
    """測試速率限制"""
    pass

def test_token_revocation():
    """測試 Token 撤銷"""
    pass
```

### 集成測試 (待實現)

```python
# tests/api/v1/test_auth.py
async def test_register_endpoint():
    """測試註冊端點"""
    pass

async def test_login_endpoint():
    """測試登入端點"""
    pass

async def test_protected_endpoint():
    """測試受保護端點"""
    pass

async def test_permission_check():
    """測試權限檢查"""
    pass
```

---

## 🔄 與其他 Stories 的集成

### 依賴關係

| Story | 關係 | 說明 |
|-------|------|------|
| S0-4 (Database) | ✅ 已完成 | 使用 User 模型和數據庫會話 |
| S0-5 (Redis) | ✅ 已完成 | 用於速率限制和 Token 撤銷 |

### 被依賴

| Story | 如何使用 | 說明 |
|-------|---------|------|
| S1-1 (Workflow API) | 需要認證 | 使用 `get_current_user` 依賴 |
| S1-2 (Agent API) | 需要認證 | 使用權限檢查 `require_permission` |
| 所有 API 端點 | 需要認證 | 統一的認證機制 |

---

## 📝 使用範例

### Python 客戶端

```python
import httpx

API_BASE = "http://localhost:8000/api/v1"

async def authenticate():
    # 1. 註冊
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/auth/register",
            json={
                "email": "user@example.com",
                "username": "johndoe",
                "password": "SecureP@ss123",
                "full_name": "John Doe"
            }
        )
        user = response.json()

    # 2. 登入
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/auth/login/json",
            json={
                "username": "johndoe",
                "password": "SecureP@ss123"
            }
        )
        tokens = response.json()
        access_token = tokens["access_token"]

    # 3. 訪問受保護資源
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        current_user = response.json()

    return current_user
```

### JavaScript/TypeScript

```typescript
// 登入並存儲 Token
async function login(username: string, password: string) {
  const response = await fetch(`${API_BASE}/auth/login/json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
}

// 自動刷新 Token 的 Fetch 包裝器
async function authenticatedFetch(url: string, options: RequestInit = {}) {
  let token = localStorage.getItem('access_token');

  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };

  let response = await fetch(url, options);

  // Token 過期，嘗試刷新
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    const data = await refreshResponse.json();
    token = data.access_token;
    localStorage.setItem('access_token', token);

    // 重試原始請求
    options.headers['Authorization'] = `Bearer ${token}`;
    response = await fetch(url, options);
  }

  return response;
}
```

---

## 🚀 部署注意事項

### 環境變量 (必須修改)

```bash
# ⚠️ 生產環境必須修改
SECRET_KEY=$(openssl rand -hex 32)  # 生成 64 字符的隨機密鑰

# Token 過期時間 (可選)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# JWT 算法
JWT_ALGORITHM=HS256
```

### 安全清單

- [ ] 修改 `SECRET_KEY` 為隨機生成的密鑰
- [ ] 啟用 HTTPS (生產環境)
- [ ] 設置 `SESSION_COOKIE_SECURE=true`
- [ ] 設置 `SESSION_COOKIE_SAMESITE=strict`
- [ ] 配置 Redis 密碼保護
- [ ] 配置 CORS 白名單 (不使用 `*`)
- [ ] 啟用速率限制
- [ ] 監控失敗登入嘗試
- [ ] 定期輪換 SECRET_KEY (建議)

---

## 🎯 未來增強功能

以下功能可在後續 Sprint 中實現:

### Phase 2 增強

1. **密碼重置**
   - 電郵驗證碼
   - 安全的重置 Token
   - 過期機制

2. **雙因素認證 (2FA)**
   - TOTP (Google Authenticator)
   - SMS 驗證碼
   - 備份碼

3. **會話管理**
   - 多設備登入追蹤
   - 查看活躍會話
   - 強制登出所有會話

### Phase 3 增強

4. **Azure AD 整合**
   - 企業 SSO
   - OAuth2 Provider
   - SAML 支援

5. **審計日誌**
   - 登入歷史
   - 操作追蹤
   - 異常檢測

6. **進階權限**
   - 細粒度 RBAC
   - 動態權限分配
   - 權限繼承

---

## 📖 相關文檔

- [認證架構設計](./authentication-design.md)
- [API 使用指南](../04-usage/authentication-guide.md)
- [Sprint Status](./sprint-status.yaml)
- [Swagger 文檔](http://localhost:8000/docs)

---

## ✅ 驗收標準

| 標準 | 狀態 | 說明 |
|------|------|------|
| JWT Token 生成和驗證 | ✅ | Access + Refresh Token |
| 用戶註冊流程 | ✅ | 包含密碼強度驗證 |
| 用戶登入流程 | ✅ | OAuth2 + JSON 兩種方式 |
| Token 刷新機制 | ✅ | 使用 Refresh Token |
| 登出和 Token 撤銷 | ✅ | Redis 黑名單 |
| 密碼安全 (Bcrypt) | ✅ | 12 rounds |
| 速率限制 | ✅ | Redis 實現 |
| 權限檢查 | ✅ | Dependency 注入 |
| API 文檔 | ✅ | Swagger + 使用指南 |
| 架構設計文檔 | ✅ | 完整技術文檔 |

---

**狀態**: ✅ **已完成**
**完成時間**: 2025-11-20
**總代碼量**: 1,644 行
**總文檔量**: ~15,500 字

---

**下一步**: S0-8 (Monitoring Setup) 或 S0-9 (Application Insights Logging)
