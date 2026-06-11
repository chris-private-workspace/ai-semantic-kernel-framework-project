# Sprint 3: Security & Observability - 詳細規劃

> ℹ️ **開發策略**: 本 Sprint 完成**本地開發階段** (Phase 1)  
> 🔐 **認證方式**: Mock Auth (開發) → Azure AD 準備 (Phase 2)  
> 📊 **監控方案**: Console Logging + 簡單 Metrics (Phase 1)  
> 🔒 **Secrets 管理**: .env 文件 (Phase 1) → Azure Key Vault (Phase 2)  
> 💰 **成本**: $0 Azure 費用

**版本**: 1.1 (Local-First)  
**創建日期**: 2025-11-19  
**更新日期**: 2025-11-20  
**Sprint 期間**: 2026-01-06 至 2026-01-17 (2週)  
**團隊規模**: 8人

---

## 📋 Sprint 目標

實現完整的安全強化和可觀測性系統，確保平台符合企業級安全標準。

### 核心目標
1. ✅ 實現 RBAC 權限系統
2. ✅ API 安全強化（防注入、限流）
3. ✅ 數據加密（靜態 + 傳輸中）
4. ✅ Secrets 管理（Azure Key Vault）
5. ✅ 分佈式追蹤和性能監控
6. ✅ 安全滲透測試

### 成功標準
- 所有 API 受 RBAC 保護
- 敏感數據加密存儲
- 無 P0/P1 安全漏洞
- 分佈式追蹤覆蓋所有服務
- 安全審計 Dashboard 可用

---

## 📊 Story Points 分配

**總計劃點數**: 38

**按優先級分配**:
- P0 (Critical): 28 點 (74%)
- P1 (High): 10 點 (26%)

---

## 🎯 Sprint Backlog

### S3-1: RBAC Permission System
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 1  
**依賴**: S0-7 (Authentication Framework)

#### 描述

實現基於角色的訪問控制系統，支持細粒度權限管理。

#### 驗收標準
- [ ] 定義 4 個角色：Admin、PowerUser、User、Viewer
- [ ] 每個 API endpoint 有權限檢查
- [ ] 用戶可以分配多個角色
- [ ] 權限繼承正確（Admin > PowerUser > User > Viewer）
- [ ] 提供權限檢查裝飾器

#### 技術實現細節

**1. 角色和權限數據模型**

```python
# app/models/rbac.py
from sqlalchemy import Column, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
import uuid

# 多對多關係表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    priority = Column(Integer, nullable=False)  # 數字越大權限越高
    is_system = Column(Boolean, default=False)  # 系統角色不可刪除
    
    # 關係
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)  # 例如: "workflow:create"
    resource = Column(String(50), nullable=False, index=True)  # workflow, execution, agent
    action = Column(String(50), nullable=False, index=True)  # create, read, update, delete, execute
    description = Column(String(255))
    
    # 關係
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

# 更新 User 模型
class User(Base):
    # ... 現有字段 ...
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    def has_permission(self, resource: str, action: str) -> bool:
        """檢查用戶是否有特定權限"""
        for role in self.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """檢查用戶是否有特定角色"""
        return any(role.name == role_name for role in self.roles)
    
    @property
    def is_admin(self) -> bool:
        return self.has_role("Admin")
```

**2. 初始化角色和權限**

```python
# app/db/init_rbac.py
from sqlalchemy.orm import Session
from app.models.rbac import Role, Permission

def init_rbac(db: Session):
    """初始化 RBAC 角色和權限"""
    
    # 定義權限
    permissions = [
        # Workflow 權限
        {"name": "workflow:create", "resource": "workflow", "action": "create"},
        {"name": "workflow:read", "resource": "workflow", "action": "read"},
        {"name": "workflow:update", "resource": "workflow", "action": "update"},
        {"name": "workflow:delete", "resource": "workflow", "action": "delete"},
        
        # Execution 權限
        {"name": "execution:create", "resource": "execution", "action": "create"},
        {"name": "execution:read", "resource": "execution", "action": "read"},
        {"name": "execution:cancel", "resource": "execution", "action": "cancel"},
        
        # Agent 權限
        {"name": "agent:create", "resource": "agent", "action": "create"},
        {"name": "agent:read", "resource": "agent", "action": "read"},
        {"name": "agent:update", "resource": "agent", "action": "update"},
        {"name": "agent:delete", "resource": "agent", "action": "delete"},
        
        # User 權限
        {"name": "user:read", "resource": "user", "action": "read"},
        {"name": "user:create", "resource": "user", "action": "create"},
        {"name": "user:update", "resource": "user", "action": "update"},
        {"name": "user:delete", "resource": "user", "action": "delete"},
        
        # Admin 權限
        {"name": "admin:access", "resource": "admin", "action": "access"},
        {"name": "audit:read", "resource": "audit", "action": "read"},
    ]
    
    # 創建權限
    permission_objects = {}
    for perm_data in permissions:
        perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not perm:
            perm = Permission(**perm_data)
            db.add(perm)
            db.flush()
        permission_objects[perm_data["name"]] = perm
    
    # 定義角色及其權限
    roles_config = [
        {
            "name": "Admin",
            "description": "管理員，擁有所有權限",
            "priority": 100,
            "is_system": True,
            "permissions": list(permission_objects.keys())  # 所有權限
        },
        {
            "name": "PowerUser",
            "description": "高級用戶，可以管理工作流和執行",
            "priority": 75,
            "is_system": True,
            "permissions": [
                "workflow:create", "workflow:read", "workflow:update", "workflow:delete",
                "execution:create", "execution:read", "execution:cancel",
                "agent:create", "agent:read", "agent:update",
                "user:read"
            ]
        },
        {
            "name": "User",
            "description": "普通用戶，可以創建和執行自己的工作流",
            "priority": 50,
            "is_system": True,
            "permissions": [
                "workflow:create", "workflow:read", "workflow:update",
                "execution:create", "execution:read",
                "agent:read",
                "user:read"
            ]
        },
        {
            "name": "Viewer",
            "description": "只讀用戶，只能查看",
            "priority": 25,
            "is_system": True,
            "permissions": [
                "workflow:read",
                "execution:read",
                "agent:read",
                "user:read"
            ]
        }
    ]
    
    # 創建角色
    for role_data in roles_config:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                priority=role_data["priority"],
                is_system=role_data["is_system"]
            )
            db.add(role)
            db.flush()
        
        # 分配權限
        role.permissions = [
            permission_objects[perm_name] 
            for perm_name in role_data["permissions"]
        ]
    
    db.commit()
    print("RBAC initialized successfully")
```

**3. 權限檢查裝飾器**

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from functools import wraps

def require_permission(resource: str, action: str):
    """權限檢查裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            if not current_user.has_permission(resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {resource}:{action}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role_name: str):
    """角色檢查裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            if not current_user.has_role(role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role_name}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 便捷方法
def require_admin(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

**4. 應用到 API**

```python
# app/api/v1/workflows.py
from app.api.deps import require_permission, get_current_user

@router.post("/api/workflows/")
@require_permission("workflow", "create")
async def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 創建工作流邏輯
    pass

@router.delete("/api/workflows/{workflow_id}")
@require_permission("workflow", "delete")
async def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 刪除工作流邏輯
    pass
```

**5. 用戶角色管理 API**

```python
# app/api/v1/roles.py
from fastapi import APIRouter, Depends
from app.api.deps import require_admin

router = APIRouter()

@router.post("/api/users/{user_id}/roles/{role_id}")
async def assign_role(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not user or not role:
        raise HTTPException(status_code=404, detail="User or Role not found")
    
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
    
    return {"message": f"Role {role.name} assigned to user {user.email}"}

@router.delete("/api/users/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not user or not role:
        raise HTTPException(status_code=404, detail="User or Role not found")
    
    if role in user.roles:
        user.roles.remove(role)
        db.commit()
    
    return {"message": f"Role {role.name} removed from user {user.email}"}
```

#### 子任務

1. [ ] 創建 RBAC 數據模型和遷移
2. [ ] 實現初始化腳本（角色和權限）
3. [ ] 創建權限檢查裝飾器
4. [ ] 更新所有 API 添加權限檢查
5. [ ] 實現角色管理 API
6. [ ] 編寫單元測試
7. [ ] 編寫集成測試

#### 測試計劃

```python
# tests/test_rbac.py
def test_user_has_permission():
    user = User(email="test@example.com")
    role = Role(name="User", priority=50)
    permission = Permission(name="workflow:create", resource="workflow", action="create")
    
    role.permissions.append(permission)
    user.roles.append(role)
    
    assert user.has_permission("workflow", "create") == True
    assert user.has_permission("workflow", "delete") == False

def test_admin_can_delete_workflow(client, admin_user):
    response = client.delete(
        f"/api/workflows/{workflow_id}",
        headers={"Authorization": f"Bearer {admin_user.token}"}
    )
    assert response.status_code == 200

def test_viewer_cannot_delete_workflow(client, viewer_user):
    response = client.delete(
        f"/api/workflows/{workflow_id}",
        headers={"Authorization": f"Bearer {viewer_user.token}"}
    )
    assert response.status_code == 403
```

---

### S3-2: API Security Hardening
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 2  
**依賴**: S1-8 (API Gateway)

#### 描述

強化 API 安全性，防止常見攻擊（SQL 注入、XSS、CSRF），實現限流和輸入驗證。

#### 驗收標準
- [ ] 所有輸入經過驗證和清理
- [ ] SQL 注入防護（使用 ORM）
- [ ] API 限流（每分鐘 60 次）
- [ ] CORS 配置正確
- [ ] 安全 headers（HSTS、CSP、X-Frame-Options）

#### 技術實現細節

**1. 輸入驗證和清理**

```python
# app/core/security.py
import bleach
from pydantic import validator

class WorkflowCreate(BaseModel):
    name: str
    description: str = None
    
    @validator('name')
    def validate_name(cls, v):
        # 移除 HTML 標籤
        v = bleach.clean(v, tags=[], strip=True)
        
        # 檢查長度
        if len(v) < 3 or len(v) > 100:
            raise ValueError('Name must be between 3 and 100 characters')
        
        # 檢查非法字符
        if not v.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            raise ValueError('Name contains invalid characters')
        
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v:
            # 允許部分 HTML 標籤但清理危險內容
            v = bleach.clean(
                v,
                tags=['b', 'i', 'u', 'p', 'br'],
                attributes={},
                strip=True
            )
        return v
```

**2. SQL 注入防護**

```python
# ✅ 正確：使用 ORM 參數化查詢
workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

# ✅ 正確：使用參數綁定
query = text("SELECT * FROM workflows WHERE name = :name")
result = db.execute(query, {"name": user_input})

# ❌ 錯誤：字符串拼接（永遠不要這樣做）
# query = f"SELECT * FROM workflows WHERE name = '{user_input}'"
```

**3. API 限流（使用 FastAPI-Limiter）**

```python
# app/core/rate_limit.py
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

async def init_rate_limiter():
    redis_client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    await FastAPILimiter.init(redis_client)

# 在 API 中應用限流
@router.post("/api/workflows/")
@limiter.limit("60/minute")  # 每分鐘 60 次
async def create_workflow(
    request: Request,
    workflow: WorkflowCreate,
    db: Session = Depends(get_db)
):
    # 創建工作流
    pass

# 針對不同用戶的限流
@router.post("/api/executions/")
async def create_execution(
    request: Request,
    execution: ExecutionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _rate_limit = Depends(RateLimiter(times=100, seconds=60))  # VIP 用戶更高限額
):
    pass
```

**4. CORS 配置**

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ipa-platform.example.com",  # 生產環境
        "https://staging.ipa-platform.example.com",  # Staging
        "http://localhost:3000",  # 本地開發
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
    max_age=600,  # 預檢請求緩存 10 分鐘
)
```

**5. 安全 Headers Middleware**

```python
# app/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # HTTP Strict Transport Security
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.example.com"
        )
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

# 在 main.py 中註冊
app.add_middleware(SecurityHeadersMiddleware)
```

**6. CSRF 保護（API Token 模式）**

```python
# app/core/csrf.py
from fastapi import Header, HTTPException
import hmac
import hashlib
import time

def generate_csrf_token(user_id: str, secret: str) -> str:
    """生成 CSRF token"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{timestamp}"
    signature = hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{data}:{signature}"

def verify_csrf_token(token: str, user_id: str, secret: str, max_age: int = 3600) -> bool:
    """驗證 CSRF token"""
    try:
        data, signature = token.rsplit(":", 1)
        token_user_id, timestamp = data.split(":")
        
        # 驗證用戶
        if token_user_id != user_id:
            return False
        
        # 驗證時間
        if int(time.time()) - int(timestamp) > max_age:
            return False
        
        # 驗證簽名
        expected_signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except:
        return False

# 在需要 CSRF 保護的 endpoint 使用
@router.post("/api/workflows/{workflow_id}/delete")
async def delete_workflow(
    workflow_id: str,
    csrf_token: str = Header(None, alias="X-CSRF-Token"),
    current_user = Depends(get_current_user)
):
    if not verify_csrf_token(csrf_token, current_user.id, settings.SECRET_KEY):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    
    # 刪除邏輯
    pass
```

#### 子任務

1. [ ] 實現輸入驗證（Pydantic validators）
2. [ ] 審查所有 ORM 查詢（防 SQL 注入）
3. [ ] 配置 API 限流
4. [ ] 配置 CORS
5. [ ] 實現安全 headers middleware
6. [ ] 配置 CSRF 保護
7. [ ] 安全測試（OWASP ZAP 掃描）

#### 測試計劃

```python
# tests/test_security.py
def test_input_validation_rejects_html():
    with pytest.raises(ValueError):
        WorkflowCreate(name="<script>alert('xss')</script>")

def test_rate_limiting(client):
    for _ in range(61):
        response = client.post("/api/workflows/", json={"name": "Test"})
    
    assert response.status_code == 429  # Too Many Requests

def test_security_headers(client):
    response = client.get("/api/workflows/")
    assert "Strict-Transport-Security" in response.headers
    assert "X-Frame-Options" in response.headers
```

---

### S3-3: Data Encryption at Rest
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 1  
**依賴**: S0-4 (Database Infrastructure)

#### 描述

實現敏感數據的靜態加密，包括數據庫字段加密和文件存儲加密。

#### 驗收標準
- [ ] 敏感字段（密碼、API keys、tokens）加密存儲
- [ ] 使用 AES-256-GCM 加密算法
- [ ] 加密密鑰通過 Azure Key Vault 管理
- [ ] 提供透明的加密/解密層
- [ ] 數據庫連接使用 SSL/TLS

#### 技術實現細節

**1. 加密服務**

```python
# app/core/encryption.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import os
import base64

class EncryptionService:
    def __init__(self, key: bytes = None):
        """
        初始化加密服務
        key: 32 字節密鑰（從 Azure Key Vault 獲取）
        """
        if key is None:
            # 從環境變量讀取（生產環境應從 Key Vault 讀取）
            key = base64.b64decode(os.getenv("ENCRYPTION_KEY"))
        
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        
        self.cipher = AESGCM(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串
        返回: base64 編碼的 nonce + ciphertext
        """
        if not plaintext:
            return None
        
        # 生成隨機 nonce
        nonce = os.urandom(12)
        
        # 加密
        ciphertext = self.cipher.encrypt(
            nonce,
            plaintext.encode('utf-8'),
            None  # additional authenticated data
        )
        
        # 合併 nonce 和 ciphertext，然後 base64 編碼
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密字符串
        encrypted_data: base64 編碼的 nonce + ciphertext
        """
        if not encrypted_data:
            return None
        
        # Base64 解碼
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # 分離 nonce 和 ciphertext
        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]
        
        # 解密
        plaintext = self.cipher.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')

# 全局實例
encryption_service = EncryptionService()
```

**2. SQLAlchemy 加密列類型**

```python
# app/db/encrypted_type.py
from sqlalchemy.types import TypeDecorator, String
from app.core.encryption import encryption_service

class EncryptedString(TypeDecorator):
    """自動加密/解密的字符串列類型"""
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """寫入數據庫前加密"""
        if value is not None:
            return encryption_service.encrypt(value)
        return value
    
    def process_result_value(self, value, dialect):
        """從數據庫讀取後解密"""
        if value is not None:
            return encryption_service.decrypt(value)
        return value
```

**3. 應用到敏感字段**

```python
# app/models/integration.py
from app.db.encrypted_type import EncryptedString

class N8nIntegration(Base):
    __tablename__ = "n8n_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    
    # 加密字段
    api_key = Column(EncryptedString(500), nullable=False)  # 自動加密
    webhook_secret = Column(EncryptedString(500), nullable=False)
    
    # 普通字段
    webhook_url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)

class TeamsIntegration(Base):
    __tablename__ = "teams_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    
    # 加密字段
    webhook_url = Column(EncryptedString(1000), nullable=False)  # Webhook URL 包含敏感 token
    
    is_active = Column(Boolean, default=True)
```

**4. 數據庫連接 SSL/TLS**

```python
# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    
    @property
    def database_url_with_ssl(self) -> str:
        """添加 SSL 參數"""
        if "?" in self.DATABASE_URL:
            return f"{self.DATABASE_URL}&sslmode=require&sslrootcert=/app/certs/ca-certificate.crt"
        else:
            return f"{self.DATABASE_URL}?sslmode=require&sslrootcert=/app/certs/ca-certificate.crt"

settings = Settings()

# 創建 engine
engine = create_engine(
    settings.database_url_with_ssl,
    pool_pre_ping=True,
    echo=False
)
```

**5. PostgreSQL 加密配置**

```yaml
# k8s/database/postgresql-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgresql-config
data:
  postgresql.conf: |
    # SSL 配置
    ssl = on
    ssl_cert_file = '/var/lib/postgresql/certs/server.crt'
    ssl_key_file = '/var/lib/postgresql/certs/server.key'
    ssl_ca_file = '/var/lib/postgresql/certs/ca.crt'
    
    # 強制 SSL 連接
    ssl_min_protocol_version = 'TLSv1.2'
    ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
    
    # 加密傳輸中數據
    password_encryption = scram-sha-256
```

#### 子任務

1. [ ] 實現 EncryptionService
2. [ ] 創建 EncryptedString 列類型
3. [ ] 識別並遷移敏感字段
4. [ ] 配置數據庫 SSL/TLS
5. [ ] 集成 Azure Key Vault（S3-4）
6. [ ] 編寫加密/解密測試
7. [ ] 性能測試（加密開銷）

#### 測試計劃

```python
# tests/test_encryption.py
def test_encryption_decryption():
    service = EncryptionService()
    plaintext = "my-secret-api-key"
    
    encrypted = service.encrypt(plaintext)
    assert encrypted != plaintext
    
    decrypted = service.decrypt(encrypted)
    assert decrypted == plaintext

def test_encrypted_column(db):
    integration = N8nIntegration(
        name="Test Integration",
        api_key="super-secret-key",
        webhook_secret="webhook-secret-123"
    )
    db.add(integration)
    db.commit()
    
    # 驗證數據庫中存儲的是加密值
    result = db.execute(text("SELECT api_key FROM n8n_integrations WHERE name='Test Integration'"))
    raw_value = result.scalar()
    assert raw_value != "super-secret-key"
    
    # 驗證 ORM 讀取時自動解密
    loaded = db.query(N8nIntegration).filter_by(name="Test Integration").first()
    assert loaded.api_key == "super-secret-key"
```

---

### S3-4: Secrets Management (Azure Key Vault)
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: DevOps Engineer  
**依賴**: S0-2 (Kubernetes Cluster)

#### 描述

集成 Azure Key Vault 管理所有敏感配置，包括數據庫密碼、API keys、加密密鑰等。

#### 驗收標準
- [ ] Azure Key Vault 配置完成
- [ ] 所有敏感配置從 Key Vault 讀取
- [ ] 使用 Managed Identity 驗證
- [ ] Secrets 自動輪轉機制
- [ ] 無硬編碼的敏感信息

#### 技術實現細節

**1. Azure Key Vault 設置**

```bash
# 創建 Key Vault
az keyvault create \
  --name ipa-platform-kv \
  --resource-group ipa-platform-rg \
  --location eastus \
  --enable-rbac-authorization true

# 創建 Managed Identity
az identity create \
  --name ipa-platform-identity \
  --resource-group ipa-platform-rg

# 授予 AKS 訪問 Key Vault 的權限
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee <managed-identity-client-id> \
  --scope /subscriptions/<subscription-id>/resourceGroups/ipa-platform-rg/providers/Microsoft.KeyVault/vaults/ipa-platform-kv

# 添加 secrets
az keyvault secret set --vault-name ipa-platform-kv --name "database-password" --value "your-db-password"
az keyvault secret set --vault-name ipa-platform-kv --name "encryption-key" --value "your-32-byte-key"
az keyvault secret set --vault-name ipa-platform-kv --name "jwt-secret" --value "your-jwt-secret"
```

**2. Python 集成（使用 azure-identity 和 azure-keyvault-secrets）**

```python
# app/core/secrets.py
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
import os

class SecretsManager:
    def __init__(self):
        vault_url = os.getenv("AZURE_KEY_VAULT_URL", "https://ipa-platform-kv.vault.azure.net/")
        
        # 生產環境使用 Managed Identity，本地使用 DefaultAzureCredential
        if os.getenv("ENVIRONMENT") == "production":
            credential = ManagedIdentityCredential()
        else:
            credential = DefaultAzureCredential()
        
        self.client = SecretClient(vault_url=vault_url, credential=credential)
        self._cache = {}
    
    def get_secret(self, secret_name: str, use_cache: bool = True) -> str:
        """獲取 secret"""
        if use_cache and secret_name in self._cache:
            return self._cache[secret_name]
        
        try:
            secret = self.client.get_secret(secret_name)
            self._cache[secret_name] = secret.value
            return secret.value
        except Exception as e:
            # 如果 Key Vault 不可用，回退到環境變量
            fallback = os.getenv(secret_name.upper().replace("-", "_"))
            if fallback:
                return fallback
            raise Exception(f"Failed to get secret {secret_name}: {str(e)}")
    
    def set_secret(self, secret_name: str, secret_value: str):
        """設置 secret"""
        self.client.set_secret(secret_name, secret_value)
        self._cache[secret_name] = secret_value

# 全局實例
secrets_manager = SecretsManager()
```

**3. 更新配置讀取邏輯**

```python
# app/core/config.py
from app.core.secrets import secrets_manager

class Settings(BaseSettings):
    # 公開配置
    PROJECT_NAME: str = "IPA Platform"
    API_VERSION: str = "v1"
    ENVIRONMENT: str = "development"
    
    # 敏感配置（從 Key Vault 讀取）
    @property
    def database_password(self) -> str:
        return secrets_manager.get_secret("database-password")
    
    @property
    def encryption_key(self) -> str:
        return secrets_manager.get_secret("encryption-key")
    
    @property
    def jwt_secret(self) -> str:
        return secrets_manager.get_secret("jwt-secret")
    
    @property
    def azure_openai_api_key(self) -> str:
        return secrets_manager.get_secret("azure-openai-api-key")
    
    @property
    def database_url(self) -> str:
        username = os.getenv("DB_USERNAME", "postgres")
        password = self.database_password
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME", "ipa_platform")
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

settings = Settings()
```

**4. Kubernetes 集成（使用 Azure Key Vault Provider for Secrets Store CSI Driver）**

```yaml
# k8s/secrets/secret-provider-class.yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: ipa-platform-secrets
  namespace: default
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<managed-identity-client-id>"
    keyvaultName: "ipa-platform-kv"
    tenantId: "<tenant-id>"
    objects: |
      array:
        - |
          objectName: database-password
          objectType: secret
        - |
          objectName: encryption-key
          objectType: secret
        - |
          objectName: jwt-secret
          objectType: secret
        - |
          objectName: azure-openai-api-key
          objectType: secret
  secretObjects:
    - secretName: ipa-platform-secrets
      type: Opaque
      data:
        - objectName: database-password
          key: DATABASE_PASSWORD
        - objectName: encryption-key
          key: ENCRYPTION_KEY
        - objectName: jwt-secret
          key: JWT_SECRET
        - objectName: azure-openai-api-key
          key: AZURE_OPENAI_API_KEY
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ipa-platform-backend
spec:
  template:
    spec:
      containers:
        - name: backend
          image: ipa-platform-backend:latest
          env:
            - name: AZURE_KEY_VAULT_URL
              value: "https://ipa-platform-kv.vault.azure.net/"
            - name: DATABASE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: ipa-platform-secrets
                  key: DATABASE_PASSWORD
          volumeMounts:
            - name: secrets-store
              mountPath: "/mnt/secrets-store"
              readOnly: true
      volumes:
        - name: secrets-store
          csi:
            driver: secrets-store.csi.k8s.io
            readOnly: true
            volumeAttributes:
              secretProviderClass: "ipa-platform-secrets"
```

**5. Secret 輪轉策略**

```python
# scripts/rotate_secrets.py
from app.core.secrets import secrets_manager
import secrets as py_secrets
import base64

def rotate_encryption_key():
    """輪轉加密密鑰"""
    # 生成新的 32 字節密鑰
    new_key = py_secrets.token_bytes(32)
    new_key_b64 = base64.b64encode(new_key).decode('utf-8')
    
    # 保存舊密鑰
    old_key = secrets_manager.get_secret("encryption-key")
    secrets_manager.set_secret("encryption-key-old", old_key)
    
    # 設置新密鑰
    secrets_manager.set_secret("encryption-key", new_key_b64)
    
    print("Encryption key rotated successfully")
    print("IMPORTANT: Re-encrypt all encrypted data with new key!")

def rotate_jwt_secret():
    """輪轉 JWT secret"""
    new_secret = py_secrets.token_urlsafe(64)
    
    old_secret = secrets_manager.get_secret("jwt-secret")
    secrets_manager.set_secret("jwt-secret-old", old_secret)
    
    secrets_manager.set_secret("jwt-secret", new_secret)
    
    print("JWT secret rotated successfully")
    print("IMPORTANT: All existing tokens will be invalidated!")

if __name__ == "__main__":
    rotate_encryption_key()
    rotate_jwt_secret()
```

#### 子任務

1. [ ] 創建 Azure Key Vault
2. [ ] 配置 Managed Identity
3. [ ] 實現 SecretsManager 類
4. [ ] 更新所有配置讀取邏輯
5. [ ] 配置 CSI Driver（Kubernetes）
6. [ ] 實現 secret 輪轉腳本
7. [ ] 測試 Key Vault 集成

---

### S3-5: Security Audit Dashboard
**Story Points**: 3  
**優先級**: P1 - High  
**負責人**: DevOps Engineer  
**依賴**: S2-7 (Audit Log Service), S0-8 (Monitoring Stack)

#### 描述

創建 Grafana Dashboard 顯示安全事件、審計日誌、異常登錄等。

#### 驗收標準
- [ ] Dashboard 顯示過去 24 小時安全事件
- [ ] 可視化失敗登錄嘗試
- [ ] 顯示權限變更歷史
- [ ] 異常活動告警（多次失敗登錄）
- [ ] 可按用戶/資源/時間篩選

#### 技術實現細節

**1. Grafana Dashboard JSON**

```json
{
  "dashboard": {
    "title": "Security Audit Dashboard",
    "panels": [
      {
        "id": 1,
        "title": "Failed Login Attempts (24h)",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(auth_login_failures_total[24h]))",
            "legendFormat": "Failed Logins"
          }
        ]
      },
      {
        "id": 2,
        "title": "Login Attempts by Status",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (status) (increase(auth_login_attempts_total[24h]))"
          }
        ]
      },
      {
        "id": 3,
        "title": "Permission Changes Timeline",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(audit_log_permission_changes_total[5m])"
          }
        ]
      },
      {
        "id": 4,
        "title": "Top Failed Login Users",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, sum by (user_email) (increase(auth_login_failures_total[24h])))"
          }
        ]
      },
      {
        "id": 5,
        "title": "Security Events by Type",
        "type": "graph",
        "targets": [
          {
            "expr": "sum by (event_type) (increase(security_events_total[5m]))"
          }
        ]
      }
    ]
  }
}
```

**2. 記錄安全指標**

```python
# app/core/security_metrics.py
from prometheus_client import Counter, Histogram

# 登錄指標
login_attempts = Counter(
    'auth_login_attempts_total',
    'Total login attempts',
    ['status', 'method']
)

login_failures = Counter(
    'auth_login_failures_total',
    'Failed login attempts',
    ['user_email', 'reason']
)

# 權限變更
permission_changes = Counter(
    'audit_log_permission_changes_total',
    'Permission changes',
    ['user_id', 'action']
)

# 安全事件
security_events = Counter(
    'security_events_total',
    'Security events',
    ['event_type', 'severity']
)

# 在登錄處理中使用
@router.post("/api/auth/login")
async def login(credentials: LoginCredentials):
    try:
        user = await authenticate_user(credentials.email, credentials.password)
        login_attempts.labels(status='success', method='password').inc()
        return {"access_token": create_access_token(user)}
    except AuthenticationError as e:
        login_failures.labels(user_email=credentials.email, reason=str(e)).inc()
        login_attempts.labels(status='failure', method='password').inc()
        raise HTTPException(status_code=401, detail="Authentication failed")
```

#### 子任務

1. [ ] 設計 Dashboard 佈局
2. [ ] 創建 Grafana Dashboard JSON
3. [ ] 添加安全事件指標
4. [ ] 配置告警規則（異常登錄）
5. [ ] 測試 Dashboard 數據

---

### S3-6: Distributed Tracing (Jaeger)
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: Backend Engineer 2  
**依賴**: S2-5 (Monitoring Integration)

#### 描述

部署 Jaeger 分佈式追蹤系統，實現跨服務請求追蹤。

#### 驗收標準
- [ ] Jaeger 部署並運行
- [ ] 所有服務集成 OpenTelemetry
- [ ] 追蹤上下文在服務間傳播
- [ ] Jaeger UI 顯示完整調用鏈
- [ ] 追蹤數據保留 7 天

#### 技術實現細節

**1. Jaeger 部署（Kubernetes）**

```yaml
# k8s/monitoring/jaeger.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
        - name: jaeger
          image: jaegertracing/all-in-one:1.50
          ports:
            - containerPort: 5775
              name: zipkin-compact
            - containerPort: 6831
              name: jaeger-compact
            - containerPort: 6832
              name: jaeger-binary
            - containerPort: 5778
              name: config-rest
            - containerPort: 16686
              name: ui
            - containerPort: 14268
              name: jaeger-http
            - containerPort: 14250
              name: grpc
          env:
            - name: COLLECTOR_ZIPKIN_HOST_PORT
              value: ":9411"
            - name: SPAN_STORAGE_TYPE
              value: "elasticsearch"
            - name: ES_SERVER_URLS
              value: "http://elasticsearch:9200"
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger
  namespace: monitoring
spec:
  selector:
    app: jaeger
  ports:
    - name: ui
      port: 16686
      targetPort: 16686
    - name: grpc
      port: 14250
      targetPort: 14250
```

**2. 應用追蹤（已在 S2-5 實現基礎）**

```python
# 補充：跨服務追蹤上下文傳播
import httpx
from opentelemetry import trace
from opentelemetry.propagate import inject

tracer = trace.get_tracer(__name__)

class ServiceClient:
    async def call_another_service(self, endpoint: str, data: dict):
        with tracer.start_as_current_span("call_external_service") as span:
            span.set_attribute("http.url", endpoint)
            
            # 創建 headers 並注入追蹤上下文
            headers = {}
            inject(headers)  # 自動添加 traceparent header
            
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=data, headers=headers)
                span.set_attribute("http.status_code", response.status_code)
                
                if response.status_code >= 400:
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                
                return response.json()
```

#### 子任務

1. [ ] 部署 Jaeger
2. [ ] 配置 Elasticsearch 存儲
3. [ ] 驗證追蹤上下文傳播
4. [ ] 配置數據保留策略
5. [ ] 測試 Jaeger UI

---

### S3-7: Custom Business Metrics
**Story Points**: 3  
**優先級**: P1 - High  
**負責人**: Backend Engineer 1  
**依賴**: S0-8 (Monitoring Stack)

#### 描述

實現自定義業務指標，監控平台使用情況和業務 KPI。

#### 驗收標準
- [ ] 記錄工作流創建/執行/失敗數量
- [ ] LLM Token 使用量和成本
- [ ] 平均執行時長
- [ ] 活躍用戶數
- [ ] Prometheus 可抓取指標

#### 技術實現細節

（已在 S2-5 中實現 MetricsService，這裡補充業務指標）

```python
# app/services/metrics_service.py (補充)
class MetricsService:
    def __init__(self):
        meter = metrics.get_meter(__name__)
        
        # 新增業務指標
        self.active_users = meter.create_up_down_counter(
            name="active_users_total",
            description="Number of active users",
            unit="users"
        )
        
        self.workflow_success_rate = meter.create_observable_gauge(
            name="workflow_success_rate",
            description="Workflow success rate",
            unit="percentage",
            callbacks=[self._get_success_rate]
        )
    
    def _get_success_rate(self, options):
        """計算成功率（回調函數）"""
        # 從數據庫查詢最近 1 小時的成功率
        total = db.query(func.count(Execution.id)).filter(
            Execution.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).scalar()
        
        successful = db.query(func.count(Execution.id)).filter(
            Execution.created_at >= datetime.utcnow() - timedelta(hours=1),
            Execution.status == "completed"
        ).scalar()
        
        rate = (successful / total * 100) if total > 0 else 0
        yield Observation(value=rate)
```

#### 子任務

1. [ ] 定義業務指標
2. [ ] 實現指標收集邏輯
3. [ ] 驗證 Prometheus 抓取
4. [ ] 創建業務 Dashboard

---

### S3-8: Performance Monitoring Dashboard
**Story Points**: 3  
**優先級**: P1 - High  
**負責人**: DevOps Engineer  
**依賴**: S3-7 (Custom Metrics)

#### 描述

創建性能監控 Dashboard，顯示 API 延遲、吞吐量、資源使用等。

#### 驗收標準
- [ ] 顯示 API P95/P99 延遲
- [ ] 顯示每秒請求數（RPS）
- [ ] 顯示錯誤率
- [ ] CPU/內存使用率
- [ ] 數據庫連接池狀態

（Grafana Dashboard 配置省略，類似 S3-5）

---

### S3-9: Security Penetration Testing
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: QA Engineer  
**依賴**: S3-1, S3-2, S3-3 (所有安全功能)

#### 描述

進行全面的安全滲透測試，發現並修復漏洞。

#### 驗收標準
- [ ] OWASP Top 10 檢查通過
- [ ] SQL 注入測試通過
- [ ] XSS 測試通過
- [ ] CSRF 測試通過
- [ ] 無 P0/P1 安全漏洞

#### 技術實現細節

**1. 自動化掃描（OWASP ZAP）**

```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  zap-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run OWASP ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.7.0
        with:
          target: 'http://staging.ipa-platform.example.com'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a'
      
      - name: Upload ZAP Report
        uses: actions/upload-artifact@v3
        with:
          name: zap-report
          path: report_html.html
```

**2. 滲透測試清單**

```markdown
## Security Testing Checklist

### Authentication & Authorization
- [ ] 測試弱密碼策略
- [ ] 測試會話固定攻擊
- [ ] 測試 JWT token 篡改
- [ ] 測試權限提升（普通用戶訪問管理員 API）
- [ ] 測試橫向越權（訪問其他用戶資源）

### Injection Attacks
- [ ] SQL 注入（使用 SQLMap）
- [ ] NoSQL 注入
- [ ] Command 注入
- [ ] LDAP 注入
- [ ] XML 注入

### XSS & CSRF
- [ ] 反射型 XSS
- [ ] 存儲型 XSS
- [ ] DOM-based XSS
- [ ] CSRF 攻擊

### Data Exposure
- [ ] 敏感數據明文傳輸
- [ ] 敏感數據明文存儲
- [ ] 錯誤信息泄露
- [ ] 目錄遍歷

### API Security
- [ ] API 限流繞過
- [ ] Mass Assignment
- [ ] API 版本泄露
- [ ] GraphQL 查詢深度攻擊

### Infrastructure
- [ ] TLS/SSL 配置測試
- [ ] HTTP headers 安全性
- [ ] CORS 配置錯誤
- [ ] 容器逃逸測試
```

#### 子任務

1. [ ] 設置測試環境
2. [ ] 運行 OWASP ZAP 掃描
3. [ ] 手動滲透測試（按清單）
4. [ ] 記錄發現的漏洞
5. [ ] 修復 P0/P1 漏洞
6. [ ] 重新測試驗證修復
7. [ ] 生成安全測試報告

---

## 📈 Sprint 3 Metrics

### Velocity Tracking
- **計劃點數**: 38
- **關鍵任務**: S3-1 (RBAC), S3-2 (API Security), S3-3 (Encryption), S3-9 (Pen Testing)

### Risk Register
- 🔴 滲透測試可能發現大量漏洞需要修復
- 🟡 Azure Key Vault 配置複雜度
- 🟡 加密可能影響性能

### Definition of Done
- [ ] 所有代碼已合併到 main
- [ ] 安全測試通過（無 P0/P1 漏洞）
- [ ] RBAC 應用到所有 API
- [ ] 敏感數據已加密
- [ ] Key Vault 集成完成
- [ ] 分佈式追蹤正常工作

---

**文檔狀態**: ✅ 已完成  
**上次更新**: 2025-11-19  
**下次審查**: Sprint 3 開始前 (2026-01-06)
