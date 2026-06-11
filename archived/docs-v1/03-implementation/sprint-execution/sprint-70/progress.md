# Sprint 70 Progress: Backend Core Authentication

> **Phase 18**: Authentication System
> **Sprint 目標**: JWT 工具、密碼哈希、AuthService、認證 API

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 70 |
| 計劃點數 | 13 Story Points |
| 完成點數 | 13 Story Points |
| 開始日期 | 2026-01-08 |
| 完成日期 | 2026-01-08 |
| Phase | 18 - Authentication System |
| 前置條件 | Phase 17 完成、User Model 存在 |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S70-1 | JWT Utilities | 3 | ✅ 完成 | 100% |
| S70-2 | UserRepository + AuthService | 5 | ✅ 完成 | 100% |
| S70-3 | Auth API Routes | 3 | ✅ 完成 | 100% |
| S70-4 | Auth Dependency Injection | 2 | ✅ 完成 | 100% |

**整體進度**: 13/13 pts (100%) ✅

---

## 詳細進度記錄

### S70-1: JWT Utilities (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `security/` 目錄結構
- [x] 實現 `create_access_token()`
- [x] 實現 `decode_token()`
- [x] 實現 `create_refresh_token()`
- [x] 實現 `hash_password()`
- [x] 實現 `verify_password()`
- [x] 使用 config 中的 JWT 設定

**新增檔案**:
- [x] `backend/src/core/security/__init__.py`
- [x] `backend/src/core/security/jwt.py`
- [x] `backend/src/core/security/password.py`

**代碼模式**:
```python
# JWT Token 結構
{
  "sub": "user_id",
  "role": "viewer",
  "exp": 1736345678,
  "iat": 1736343878
}

# 密碼哈希
hashed = hash_password("plain_password")
is_valid = verify_password("plain_password", hashed)
```

---

### S70-2: UserRepository + AuthService (5 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `UserRepository` 類
- [x] 實現 `get_by_email()`
- [x] 實現 `get_active_by_email()`
- [x] 實現 `email_exists()`
- [x] 創建 `AuthService` 類
- [x] 實現 `register()`
- [x] 實現 `authenticate()`
- [x] 實現 `get_user_from_token()`
- [x] 實現 `refresh_access_token()`
- [x] 實現 `change_password()`
- [x] 創建 auth schemas (UserCreate, TokenResponse, etc.)

**新增檔案**:
- [x] `backend/src/infrastructure/database/repositories/user.py`
- [x] `backend/src/domain/auth/__init__.py`
- [x] `backend/src/domain/auth/service.py`
- [x] `backend/src/domain/auth/schemas.py`

**認證流程**:
```
POST /register
     │
     ├── Check email uniqueness
     ├── Hash password (bcrypt)
     ├── Create User
     └── Generate JWT token
           │
           ▼
      Return token

POST /login
     │
     ├── Get user by email
     ├── Verify password
     ├── Update last_login
     └── Generate tokens (access + refresh)
           │
           ▼
      Return tokens
```

---

### S70-3: Auth API Routes (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `auth/` router
- [x] 實現 POST /register
- [x] 實現 POST /login (OAuth2PasswordRequestForm)
- [x] 實現 POST /refresh
- [x] 實現 GET /me
- [x] 註冊 router 至 api_router

**新增檔案**:
- [x] `backend/src/api/v1/auth/__init__.py`
- [x] `backend/src/api/v1/auth/routes.py`

**修改檔案**:
- [x] `backend/src/api/v1/__init__.py` - 添加 auth_router

**API 端點**:
| Method | Route | 說明 |
|--------|-------|------|
| POST | `/api/v1/auth/register` | 註冊新用戶 |
| POST | `/api/v1/auth/login` | 用戶登入 (OAuth2 form) |
| POST | `/api/v1/auth/refresh` | 刷新 token |
| GET | `/api/v1/auth/me` | 獲取當前用戶 |

---

### S70-4: Auth Dependency Injection (2 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `OAuth2PasswordBearer` scheme
- [x] 創建 `oauth2_scheme_optional`
- [x] 實現 `get_current_user()`
- [x] 實現 `get_current_user_optional()`
- [x] 實現 `get_current_active_admin()`
- [x] 實現 `get_current_operator_or_admin()`
- [x] 處理無效/過期 tokens

**新增檔案**:
- [x] `backend/src/api/v1/dependencies.py`

**使用方式**:
```python
from src.api.v1.dependencies import get_current_user, get_current_active_admin

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    return {"user": current_user.email}

@router.delete("/admin-only/{id}")
async def admin_route(
    admin: User = Depends(get_current_active_admin)
):
    # Only admins can access
    ...
```

---

## 技術備註

### JWT 設定 (已存在於 config.py)

```python
# settings from config.py
jwt_secret_key: str = "change-this-to-a-secure-random-string"
jwt_algorithm: str = "HS256"
jwt_access_token_expire_minutes: int = 60
```

### 安全考量

| 項目 | 實現 |
|------|------|
| 密碼哈希 | bcrypt (passlib) |
| Token 演算法 | HS256 |
| Access Token 有效期 | 60 分鐘 (可配置) |
| Refresh Token 有效期 | 7 天 |
| 無效 Token | 返回 401 |
| 非活躍用戶 | 返回 401 |
| 非 Admin 用戶 | 返回 403 (admin 路由) |

### 依賴已存在

以下依賴已在 requirements.txt 中：
- `python-jose[cryptography]>=3.3.0`
- `passlib[bcrypt]>=1.7.4`

---

## 新增/修改檔案總覽

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `backend/src/core/security/__init__.py` | Security 模組入口 |
| `backend/src/core/security/jwt.py` | JWT token 工具 |
| `backend/src/core/security/password.py` | 密碼哈希工具 |
| `backend/src/infrastructure/database/repositories/user.py` | UserRepository |
| `backend/src/domain/auth/__init__.py` | Auth domain 入口 |
| `backend/src/domain/auth/service.py` | AuthService |
| `backend/src/domain/auth/schemas.py` | Auth Pydantic schemas |
| `backend/src/api/v1/auth/__init__.py` | Auth API 入口 |
| `backend/src/api/v1/auth/routes.py` | Auth API routes |
| `backend/src/api/v1/dependencies.py` | 認證依賴注入 |

### 修改檔案

| 檔案 | 說明 |
|------|------|
| `backend/src/api/v1/__init__.py` | 添加 auth_router |

---

## 下一步：Sprint 71

Sprint 71 將實現前端認證：
- Auth Store (Zustand)
- Login/Signup 頁面
- ProtectedRoute 組件
- API Client 攔截器

---

**更新日期**: 2026-01-08
**Sprint 狀態**: ✅ 完成
