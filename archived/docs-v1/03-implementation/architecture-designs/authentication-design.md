# Authentication Framework 設計文檔

## 1. 概述

### 1.1 目的

認證框架為系統提供：
- **用戶認證**：用戶名/密碼登錄、JWT Token 驗證
- **授權控制**：基於角色的訪問控制（RBAC）
- **會話管理**：JWT Token 生命週期管理、刷新 Token
- **Azure AD 集成**：企業級單點登錄（SSO）準備
- **安全性**：密碼哈希、Token 簽名、防暴力破解

### 1.2 技術選型

**核心技術**：
- **JWT (JSON Web Tokens)**: 無狀態認證
- **OAuth 2.0**: 授權框架標準
- **Passlib + Bcrypt**: 密碼哈希
- **Python-JOSE**: JWT 編碼/解碼
- **FastAPI Security**: OAuth2PasswordBearer

**Azure 集成（可選）**：
- **MSAL (Microsoft Authentication Library)**: Azure AD 集成
- **Azure AD B2C**: 消費者身份管理

### 1.3 認證流程

**密碼登錄流程**：
```
1. Client POST /auth/login {username, password}
2. Server 驗證用戶名和密碼哈希
3. Server 生成 Access Token (30min) + Refresh Token (7 days)
4. Server 返回 tokens + user info
5. Client 存儲 tokens (localStorage/cookie)
6. Client 使用 Access Token 訪問 API (Authorization: Bearer {token})
7. Access Token 過期時，使用 Refresh Token 獲取新 Access Token
```

**Token 刷新流程**：
```
1. Client POST /auth/refresh {refresh_token}
2. Server 驗證 Refresh Token
3. Server 生成新 Access Token
4. Server 返回新 Access Token
```

**Azure AD 登錄流程（未來）**：
```
1. Client 重定向到 Azure AD 登錄頁
2. 用戶在 Azure AD 登錄
3. Azure AD 重定向回應用，帶 authorization code
4. Server 用 code 換取 Azure AD token
5. Server 創建本地用戶會話並返回 JWT
```

## 2. JWT Token 設計

### 2.1 Access Token

**用途**: 短期有效，用於 API 訪問授權

**Payload 結構**：
```json
{
  "sub": "user_id (UUID)",
  "username": "user@example.com",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_superuser": false,
  "permissions": ["workflow:read", "workflow:create"],
  "exp": 1700000000,
  "iat": 1699998000,
  "jti": "token_id (UUID)",
  "type": "access"
}
```

**配置**：
- **有效期**: 30 分鐘（可配置）
- **算法**: HS256（HMAC with SHA-256）
- **密鑰**: 從環境變量讀取 SECRET_KEY

### 2.2 Refresh Token

**用途**: 長期有效，用於獲取新 Access Token

**Payload 結構**：
```json
{
  "sub": "user_id (UUID)",
  "exp": 1700604800,
  "iat": 1699998000,
  "jti": "token_id (UUID)",
  "type": "refresh"
}
```

**配置**：
- **有效期**: 7 天（可配置）
- **算法**: HS256
- **存儲**: Redis 黑名單機制（撤銷）

### 2.3 Token 安全性

**密鑰管理**：
```python
# 開發環境：固定密鑰（不安全，僅用於開發）
SECRET_KEY = "development-secret-key"

# 生產環境：強密鑰（從 Azure Key Vault 獲取）
SECRET_KEY = os.environ.get("SECRET_KEY")  # 至少 32 字符

# 生成強密鑰
import secrets
SECRET_KEY = secrets.token_urlsafe(32)
```

**Token 撤銷**：
```python
# 使用 Redis 存儲撤銷的 token JTI
await redis.setex(
    f"revoked:token:{jti}",
    ttl=token_expiry,
    value="1"
)

# 驗證時檢查
is_revoked = await redis.exists(f"revoked:token:{jti}")
if is_revoked:
    raise TokenRevokedError()
```

**防重放攻擊**：
- JTI (JWT ID) 唯一標識每個 token
- Token 綁定到特定用戶會話
- 短期 Access Token 減少風險

## 3. 密碼安全

### 3.1 密碼哈希

**算法**: Bcrypt（自適應成本因子）

**實現**：
```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # 成本因子（2^12 次迭代）
)

# 哈希密碼
hashed = pwd_context.hash("plain_password")

# 驗證密碼
is_valid = pwd_context.verify("plain_password", hashed)
```

**成本因子選擇**：
- **12 rounds**: 平衡安全性和性能（推薦）
- **14 rounds**: 更高安全性（慢約 4 倍）
- **10 rounds**: 較快但安全性降低（不推薦）

### 3.2 密碼策略

**最小要求**：
- 長度 ≥ 8 字符
- 至少包含 1 個大寫字母
- 至少包含 1 個小寫字母
- 至少包含 1 個數字
- 至少包含 1 個特殊字符（可選）

**實現**：
```python
import re

def validate_password(password: str) -> bool:
    """驗證密碼強度"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True
```

**密碼重置**：
- 生成隨機重置 token（有效期 1 小時）
- 通過郵件發送重置鏈接
- 驗證 token 後允許設置新密碼

### 3.3 防暴力破解

**速率限制**：
```python
# 使用 Redis 限制登錄嘗試
key = f"login:attempts:{username}"
attempts = await redis.incr(key)

if attempts == 1:
    await redis.expire(key, 900)  # 15 分鐘窗口

if attempts > 5:
    raise TooManyLoginAttemptsError("請 15 分鐘後再試")
```

**賬戶鎖定**：
```python
# 連續失敗 5 次後鎖定賬戶
if user.failed_login_attempts >= 5:
    if not user.locked_until or user.locked_until < datetime.utcnow():
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        await user_repo.update(user)
    raise AccountLockedError("賬戶已鎖定 30 分鐘")
```

## 4. 用戶模型

### 4.1 User 表結構

（已在 S0-4 定義）

```python
class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True))

    # 安全相關
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
```

### 4.2 Pydantic 模型

**用戶註冊**：
```python
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: str = Field(min_length=8)

    @validator("password")
    def validate_password_strength(cls, v):
        if not validate_password(v):
            raise ValueError("密碼不符合安全要求")
        return v
```

**用戶登錄**：
```python
class UserLogin(BaseModel):
    username: str  # 可以是 username 或 email
    password: str
```

**Token 響應**：
```python
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒

class TokenPayload(BaseModel):
    sub: str  # user_id
    username: str
    email: str
    full_name: Optional[str]
    is_superuser: bool
    permissions: List[str]
    exp: int
    iat: int
    jti: str
    type: str  # "access" or "refresh"
```

**用戶信息**：
```python
class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True
```

## 5. 權限系統

### 5.1 權限模型

**權限格式**: `resource:action`

**資源類型**：
- `workflow` - 工作流
- `execution` - 執行實例
- `agent` - AI Agent
- `user` - 用戶管理
- `system` - 系統配置

**操作類型**：
- `read` - 讀取
- `create` - 創建
- `update` - 更新
- `delete` - 刪除
- `execute` - 執行

**示例權限**：
```python
permissions = [
    "workflow:read",
    "workflow:create",
    "workflow:update",
    "workflow:delete",
    "execution:read",
    "execution:execute",
    "agent:read",
]
```

### 5.2 角色定義

**預定義角色**：
```python
class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"

ROLE_PERMISSIONS = {
    Role.ADMIN: ["*:*"],  # 所有權限

    Role.DEVELOPER: [
        "workflow:*",
        "execution:*",
        "agent:*",
    ],

    Role.OPERATOR: [
        "workflow:read",
        "execution:*",
        "agent:read",
    ],

    Role.VIEWER: [
        "workflow:read",
        "execution:read",
        "agent:read",
    ]
}
```

### 5.3 權限檢查

**依賴注入檢查**：
```python
from fastapi import Depends, HTTPException

def require_permission(permission: str):
    """權限檢查裝飾器"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        if current_user.is_superuser:
            return current_user

        user_permissions = get_user_permissions(current_user)
        if permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"需要權限: {permission}"
            )
        return current_user

    return permission_checker

# 使用
@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    current_user: User = Depends(require_permission("workflow:delete"))
):
    # 只有擁有 workflow:delete 權限的用戶可以訪問
    pass
```

## 6. FastAPI 集成

### 6.1 OAuth2 配置

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT"
)
```

### 6.2 依賴注入

**獲取當前用戶**：
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> User:
    """從 JWT token 獲取當前用戶"""
    try:
        # 解碼 token
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        # 驗證 token 類型
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")

        # 檢查 token 是否被撤銷
        jti = payload.get("jti")
        is_revoked = await redis.exists(f"revoked:token:{jti}")
        if is_revoked:
            raise TokenRevokedError("Token has been revoked")

        # 獲取用戶
        user_id = UUID(payload.get("sub"))
        user = await user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundError("User not found")

        return user

    except JWTError as e:
        raise InvalidTokenError(str(e))

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """獲取當前活躍用戶"""
    if not current_user.is_active:
        raise InactiveUserError("User is inactive")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """獲取當前超級用戶"""
    if not current_user.is_superuser:
        raise PermissionDeniedError("Superuser access required")
    return current_user
```

### 6.3 中間件

**日誌中間件**：
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """記錄所有請求"""
    start_time = time.time()

    # 獲取用戶信息（如果已認證）
    user_id = None
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id = payload.get("sub")
    except:
        pass

    # 處理請求
    response = await call_next(request)

    # 記錄
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"user={user_id} status={response.status_code} "
        f"duration={process_time:.3f}s"
    )

    return response
```

## 7. API Endpoints

### 7.1 認證端點

**POST /api/v1/auth/register**
```python
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用戶註冊"""
    # 檢查用戶名和郵箱是否已存在
    if await user_repo.get_by_email(user_in.email):
        raise HTTPException(400, "郵箱已被使用")
    if await user_repo.get_by_username(user_in.username):
        raise HTTPException(400, "用戶名已被使用")

    # 哈希密碼
    hashed_password = pwd_context.hash(user_in.password)

    # 創建用戶
    user = await user_repo.create({
        "email": user_in.email,
        "username": user_in.username,
        "full_name": user_in.full_name,
        "hashed_password": hashed_password
    })

    return user
```

**POST /api/v1/auth/login**
```python
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """用戶登錄"""
    # 檢查速率限制
    await check_rate_limit(redis, form_data.username)

    # 查找用戶（支持 username 或 email）
    user = await user_repo.get_by_username_or_email(form_data.username)

    if not user:
        await record_failed_attempt(redis, form_data.username)
        raise HTTPException(401, "用戶名或密碼錯誤")

    # 檢查賬戶鎖定
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(403, "賬戶已鎖定")

    # 驗證密碼
    if not pwd_context.verify(form_data.password, user.hashed_password):
        await record_failed_attempt(redis, form_data.username)
        await user_repo.increment_failed_attempts(user.id)
        raise HTTPException(401, "用戶名或密碼錯誤")

    # 重置失敗次數
    await user_repo.reset_failed_attempts(user.id)
    await redis.delete(f"login:attempts:{form_data.username}")

    # 更新最後登錄時間
    await user_repo.update_last_login(user.id)

    # 生成 tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }
```

**POST /api/v1/auth/refresh**
```python
@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """刷新 Access Token"""
    try:
        # 解碼 refresh token
        payload = jwt.decode(
            refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        # 驗證 token 類型
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token type")

        # 檢查是否被撤銷
        jti = payload.get("jti")
        is_revoked = await redis.exists(f"revoked:token:{jti}")
        if is_revoked:
            raise HTTPException(401, "Token has been revoked")

        # 獲取用戶
        user_id = UUID(payload.get("sub"))
        user = await user_repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(401, "User not found or inactive")

        # 生成新 access token
        new_access_token = create_access_token(user)

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,  # 保持原 refresh token
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }

    except JWTError:
        raise HTTPException(401, "Invalid refresh token")
```

**POST /api/v1/auth/logout**
```python
@router.post("/logout", status_code=204)
async def logout(
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis)
):
    """用戶登出（撤銷 token）"""
    try:
        # 解碼 token 獲取 JTI
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        jti = payload.get("jti")
        exp = payload.get("exp")

        # 將 token 加入撤銷列表
        ttl = exp - int(time.time())
        if ttl > 0:
            await redis.setex(
                f"revoked:token:{jti}",
                ttl,
                "1"
            )

    except JWTError:
        pass  # Token 無效也視為登出成功
```

**GET /api/v1/auth/me**
```python
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """獲取當前用戶信息"""
    return current_user
```

### 7.2 用戶管理端點（需要 admin 權限）

**GET /api/v1/users**
```python
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """列出所有用戶"""
    users = await user_repo.list(skip=skip, limit=limit)
    return users
```

**GET /api/v1/users/{user_id}**
```python
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """獲取用戶詳情"""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

**PUT /api/v1/users/{user_id}**
```python
@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """更新用戶信息"""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    updated_user = await user_repo.update(user_id, user_update.dict(exclude_unset=True))
    return updated_user
```

**DELETE /api/v1/users/{user_id}**
```python
@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """刪除用戶（軟刪除）"""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # 軟刪除：設置 is_active = False
    await user_repo.update(user_id, {"is_active": False})
```

## 8. 測試策略

### 8.1 單元測試

**密碼哈希測試**：
```python
def test_password_hashing():
    """測試密碼哈希和驗證"""
    password = "TestPassword123"
    hashed = pwd_context.hash(password)

    assert hashed != password
    assert pwd_context.verify(password, hashed)
    assert not pwd_context.verify("WrongPassword", hashed)
```

**JWT 生成和驗證**：
```python
def test_jwt_creation_and_validation():
    """測試 JWT 創建和驗證"""
    user = User(id=uuid4(), username="testuser", email="test@example.com")

    token = create_access_token(user)
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    assert payload["sub"] == str(user.id)
    assert payload["username"] == user.username
    assert payload["type"] == "access"
```

### 8.2 集成測試

**登錄流程測試**：
```python
@pytest.mark.asyncio
async def test_login_flow(client: AsyncClient, test_user):
    """測試完整登錄流程"""
    # 登錄
    response = await client.post("/api/v1/auth/login", data={
        "username": test_user.username,
        "password": "TestPassword123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # 使用 token 訪問保護端點
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == test_user.username
```

**權限測試**：
```python
@pytest.mark.asyncio
async def test_permission_check(client: AsyncClient, regular_user_token, admin_user_token):
    """測試權限檢查"""
    # 普通用戶無法訪問管理端點
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    response = await client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403

    # 管理員可以訪問
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = await client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200
```

### 8.3 安全測試

**防暴力破解測試**：
```python
@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient):
    """測試登錄速率限制"""
    # 嘗試登錄 6 次
    for i in range(6):
        response = await client.post("/api/v1/auth/login", data={
            "username": "testuser",
            "password": "WrongPassword"
        })

        if i < 5:
            assert response.status_code in [401, 429]
        else:
            # 第 6 次應該被速率限制
            assert response.status_code == 429
```

## 9. Azure AD 集成（未來擴展）

### 9.1 MSAL 配置

```python
from msal import ConfidentialClientApplication

msal_app = ConfidentialClientApplication(
    client_id=settings.azure_ad_client_id,
    client_credential=settings.azure_ad_client_secret,
    authority=f"https://login.microsoftonline.com/{settings.azure_ad_tenant_id}"
)
```

### 9.2 Azure AD 登錄端點

```python
@router.get("/auth/azure/login")
async def azure_login():
    """重定向到 Azure AD 登錄"""
    auth_url = msal_app.get_authorization_request_url(
        scopes=["User.Read"],
        redirect_uri=settings.azure_ad_redirect_uri
    )
    return RedirectResponse(auth_url)

@router.get("/auth/azure/callback")
async def azure_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Azure AD 回調處理"""
    # 用 code 換取 token
    result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=["User.Read"],
        redirect_uri=settings.azure_ad_redirect_uri
    )

    if "error" in result:
        raise HTTPException(400, result["error_description"])

    # 獲取用戶信息
    azure_user = result.get("id_token_claims")

    # 創建或更新本地用戶
    user = await user_repo.get_by_email(azure_user["email"])
    if not user:
        user = await user_repo.create({
            "email": azure_user["email"],
            "username": azure_user["preferred_username"],
            "full_name": azure_user.get("name"),
            "hashed_password": "",  # Azure AD 用戶無密碼
        })

    # 生成本地 JWT
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
```

## 10. 部署和配置

### 10.1 環境變量

```env
# JWT Configuration
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=false

# Rate Limiting
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_DURATION=900  # 15 minutes

# Azure AD (Optional)
AZURE_AD_TENANT_ID=
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=
AZURE_AD_REDIRECT_URI=http://localhost:8000/api/v1/auth/azure/callback
```

### 10.2 生產環境安全

**密鑰管理**：
```python
# 從 Azure Key Vault 獲取密鑰
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url=f"https://{settings.key_vault_name}.vault.azure.net/",
    credential=credential
)

SECRET_KEY = client.get_secret("jwt-secret-key").value
```

**HTTPS 強制**：
```python
@app.middleware("http")
async def force_https(request: Request, call_next):
    """強制 HTTPS"""
    if not request.url.scheme == "https" and settings.is_production:
        url = request.url.replace(scheme="https")
        return RedirectResponse(url)
    return await call_next(request)
```

**安全頭**：
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """添加安全頭"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## 11. 監控和審計

### 11.1 審計日誌

```python
# 記錄所有認證事件到 audit_logs 表
await audit_repo.create({
    "user_id": user.id,
    "action": AuditAction.LOGIN,
    "resource_type": "auth",
    "ip_address": request.client.host,
    "user_agent": request.headers.get("user-agent"),
    "changes": {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    }
})
```

### 11.2 關鍵指標

- `login_success_total` - 成功登錄次數
- `login_failure_total` - 失敗登錄次數
- `token_issued_total` - 發行 token 數量
- `token_revoked_total` - 撤銷 token 數量
- `active_sessions` - 活躍會話數
- `login_duration_seconds` - 登錄處理時長

## 12. 最佳實踐

### 12.1 Token 管理

1. **使用短期 Access Token**：30 分鐘有效期
2. **實現 Refresh Token 輪換**：每次刷新時發行新 refresh token
3. **存儲 Refresh Token 黑名單**：允許撤銷
4. **不在 URL 中傳遞 Token**：使用 Authorization header

### 12.2 密碼管理

1. **使用強密碼策略**：最小長度、複雜度要求
2. **密碼歷史**：防止重複使用舊密碼
3. **密碼過期**：定期強制更改密碼（可選）
4. **安全的密碼重置**：郵件驗證、短期 token

### 12.3 會話管理

1. **限制併發會話**：每個用戶最多 N 個活躍 token
2. **記錄設備信息**：追蹤登錄設備
3. **異常檢測**：檢測異地登錄、可疑活動
4. **提供會話管理UI**：讓用戶查看和撤銷活躍會話

## 13. 參考資料

- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [JWT RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Azure AD Authentication](https://docs.microsoft.com/azure/active-directory/develop/)
