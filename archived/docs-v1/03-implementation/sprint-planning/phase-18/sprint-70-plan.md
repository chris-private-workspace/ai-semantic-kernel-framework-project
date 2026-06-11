# Sprint 70: Backend Core Authentication

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 70 |
| **Phase** | 18 - Authentication System |
| **Duration** | 2-3 days |
| **Total Points** | 13 |
| **Focus** | JWT utilities, AuthService, Auth API routes |

## Sprint Goals

1. Implement JWT token generation and validation
2. Implement password hashing with bcrypt
3. Create AuthService with register/login/validate
4. Create auth API endpoints
5. Create get_current_user dependency

## Prerequisites

- Phase 17 completed
- User Model exists
- Secret key configured in settings

---

## Stories

### S70-1: JWT Utilities (3 pts)

**Description**: Implement JWT token generation and validation utilities.

**Acceptance Criteria**:
- [ ] Create `create_access_token()` function
- [ ] Create `decode_token()` function
- [ ] Support token expiration
- [ ] Include user_id and role in payload
- [ ] Handle JWTError exceptions

**Technical Details**:
```python
# backend/src/core/security/jwt.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from src.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")
```

```python
# backend/src/core/security/password.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

**Files to Create**:
- `backend/src/core/security/__init__.py`
- `backend/src/core/security/jwt.py`
- `backend/src/core/security/password.py`

---

### S70-2: UserRepository + AuthService (5 pts)

**Description**: Implement user repository and authentication service.

**Acceptance Criteria**:
- [ ] Create UserRepository with get_by_email
- [ ] Create AuthService with register/authenticate/get_current_user
- [ ] Validate email uniqueness on register
- [ ] Verify password on login
- [ ] Return JWT token on success

**Technical Details**:
```python
# backend/src/infrastructure/database/repositories/user.py
from sqlalchemy import select
from src.infrastructure.database.models import User
from src.infrastructure.database.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.email == email,
                User.is_active == True
            )
        )
        return result.scalar_one_or_none()
```

```python
# backend/src/domain/auth/service.py
from src.core.security import hash_password, verify_password, create_access_token
from src.infrastructure.database.repositories.user import UserRepository

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(
        self, email: str, password: str, full_name: str
    ) -> tuple[User, str]:
        # Check if email exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        await self.user_repo.create(user)

        # Generate token
        token = create_access_token(str(user.id), user.role)
        return user, token

    async def authenticate(self, email: str, password: str) -> str:
        user = await self.user_repo.get_active_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        # Update last_login
        user.last_login = datetime.utcnow()
        await self.user_repo.update(user)

        return create_access_token(str(user.id), user.role)
```

**Files to Create**:
- `backend/src/infrastructure/database/repositories/user.py`
- `backend/src/domain/auth/__init__.py`
- `backend/src/domain/auth/service.py`
- `backend/src/domain/auth/schemas.py`

---

### S70-3: Auth API Routes (3 pts)

**Description**: Create authentication API endpoints.

**Acceptance Criteria**:
- [ ] POST /auth/register - Create new user
- [ ] POST /auth/login - Authenticate and return token
- [ ] POST /auth/refresh - Refresh token
- [ ] GET /auth/me - Get current user info

**Technical Details**:
```python
# backend/src/api/v1/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from src.domain.auth.service import AuthService
from src.domain.auth.schemas import UserCreate, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user, token = await auth_service.register(
            data.email, data.password, data.full_name
        )
        return TokenResponse(access_token=token, token_type="bearer")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        token = await auth_service.authenticate(
            form_data.username, form_data.password
        )
        return TokenResponse(access_token=token, token_type="bearer")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

**Files to Create**:
- `backend/src/api/v1/auth/__init__.py`
- `backend/src/api/v1/auth/routes.py`

**Files to Modify**:
- `backend/src/main.py` - Register auth router

---

### S70-4: Auth Dependency Injection (2 pts)

**Description**: Create get_current_user dependency for route protection.

**Acceptance Criteria**:
- [ ] Create OAuth2PasswordBearer scheme
- [ ] Create get_current_user dependency
- [ ] Create get_current_user_optional for mixed routes
- [ ] Handle invalid/expired tokens

**Technical Details**:
```python
# backend/src/api/v1/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.core.security import decode_token
from src.infrastructure.database.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user

async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_session),
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
```

**Files to Modify**:
- `backend/src/api/v1/dependencies.py`

---

## Dependencies

### New Python Packages
```
python-jose[cryptography]
passlib[bcrypt]
```

---

## Definition of Done

- [ ] All 4 stories completed and tested
- [ ] JWT tokens generated and validated correctly
- [ ] Passwords hashed with bcrypt
- [ ] Register/Login endpoints work
- [ ] get_current_user protects routes
- [ ] Unit tests for AuthService

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Token security | High | Use strong secret, short expiration |
| Password storage | High | bcrypt with proper cost factor |
| Rate limiting | Medium | Add per-IP rate limit on auth routes |

---

## Sprint Velocity Reference

Backend authentication foundation.
Expected completion: 2-3 days for 13 pts
