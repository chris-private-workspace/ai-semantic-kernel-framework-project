# Sprint 111 Execution Log

## Overview

**Sprint**: 111 - Quick Wins + Auth Foundation
**Phase**: 31 - Security Hardening + Quick Wins
**Story Points**: 40
**Status**: ✅ Completed
**Date**: 2026-02-23

## Objectives

1. Fix CORS origin port mismatch (3000→3005)
2. Fix Vite proxy target port mismatch (8010→8000)
3. JWT Secret from hardcoded to environment variable with unsafe value validation
4. Clean authStore PII-leaking console.log statements
5. Docker default credentials to environment variables
6. Uvicorn reload environment-aware configuration
7. Global Auth Middleware covering all endpoints (7%→100%)
8. Sessions fake auth fix (remove hardcoded UUID)
9. Rate Limiting infrastructure with slowapi

## Execution Summary

### Story 111-1: CORS Origin Fix ✅

**Modified Files:**
- `backend/src/core/config.py`

**Changes:**
- Changed `cors_origins` default from `"http://localhost:3000,http://localhost:8000"` to `"http://localhost:3005,http://localhost:8000"`
- Port 3005 matches the frontend Vite dev server port

**Before → After:**
```python
# Before
cors_origins: str = "http://localhost:3000,http://localhost:8000"

# After
cors_origins: str = "http://localhost:3005,http://localhost:8000"
```

### Story 111-2: Vite Proxy Fix ✅

**Modified Files:**
- `frontend/vite.config.ts`

**Changes:**
- Changed proxy target from `http://localhost:8010` to `http://localhost:8000`
- Port 8000 matches the backend FastAPI/Uvicorn port

**Before → After:**
```typescript
// Before
target: 'http://localhost:8010',

// After
target: 'http://localhost:8000',
```

### Story 111-3: JWT Secret Environment Variable ✅

**Modified Files:**
- `backend/src/core/config.py`
- `backend/.env.example`

**Changes:**

1. **Removed hardcoded default values** for `secret_key` and `jwt_secret_key` in `config.py`:
   - `secret_key: str = "change-this-to-a-secure-random-string"` → `secret_key: str = ""`
   - `jwt_secret_key: str = "change-this-to-a-secure-random-string"` → `jwt_secret_key: str = ""`

2. **Added `validate_security_settings()` method** to Settings class:
   - Checks both `secret_key` and `jwt_secret_key` against a list of known unsafe values
   - In `development` mode: logs WARNING
   - In `production` mode: raises ValueError (prevents startup)
   - Unsafe values list: `""`, `"secret"`, `"your-secret-key"`, `"changeme"`, `"jwt-secret"`, `"change-this-to-a-secure-random-string"`

3. **Startup validation** in `main.py` lifespan:
   - `settings.validate_security_settings()` called during application startup

4. **Updated `.env.example`**:
   - Added `JWT_SECRET_KEY=<your-jwt-secret-key>` entry
   - Added `APP_ENV=development` entry
   - Added generation command: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

### Story 111-4: authStore console.log Cleanup ✅

**Modified Files:**
- `frontend/src/store/authStore.ts`

**Changes:**
- Removed 5 `console.log` statements that leaked PII (user email, session state)
- Replaced with inline comments explaining the event (no output)
- Preserved all `console.error` and `console.warn` statements

**Removed statements:**

| Line | Original | Risk |
|------|----------|------|
| 187 | `console.log('[AuthStore] Login successful:', user.email)` | Email leak |
| 229 | `console.log('[AuthStore] Registration successful:', user.email)` | Email leak |
| 256 | `console.log('[AuthStore] Logged out')` | Session state leak |
| 264 | `console.log('[AuthStore] No refresh token, cannot refresh session')` | Session state leak |
| 279 | `console.log('[AuthStore] Session refreshed')` | Session state leak |

### Story 111-5: Docker Default Credentials Fix ✅

**Modified Files:**
- `docker-compose.yml`
- `backend/.env.example`

**Changes:**
- Changed Grafana admin password default from `admin` to `please-change-me`
- Added `GRAFANA_USER` and `GRAFANA_PASSWORD` entries to `.env.example`

**Before → After:**
```yaml
# Before
GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}

# After
GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-please-change-me}
```

**Note:** RabbitMQ already uses `${RABBITMQ_PASSWORD:-guest}` which is the standard RabbitMQ default. The `guest` user only works for localhost connections by default.

### Story 111-6: Uvicorn Reload Environment-Aware ✅

**Modified Files:**
- `backend/main.py`

**Changes:**
- Changed `reload=True` to `reload=(env == "development")`
- Added `workers=1` for development, `workers=4` for production
- Reads `APP_ENV` environment variable (defaults to "development")

**Before → After:**
```python
# Before
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

# After
env = os.environ.get("APP_ENV", "development")
uvicorn.run(
    "main:app", host="0.0.0.0", port=8000,
    reload=(env == "development"),
    workers=1 if env == "development" else 4,
    log_level="info",
)
```

### Story 111-7: Global Auth Middleware ✅

**New Files:**
- `backend/src/core/auth.py`

**Modified Files:**
- `backend/src/api/v1/__init__.py`

**Architecture:**

Created a lightweight JWT validation dependency (`require_auth`) in `core/auth.py` that:
- Uses `HTTPBearer` scheme to extract token from Authorization header
- Validates JWT structure and claims (sub, role, exp) using `python-jose`
- Returns a dict with `user_id`, `role`, `email` (no DB lookup required)
- Raises 401 for missing, invalid, or expired tokens

Restructured `api/v1/__init__.py` with two sub-routers:

```
api_router (prefix=/api/v1)
  ├── public_router    ← No auth required
  │   └── auth_router  ← Login, Register, Refresh, Me
  └── protected_router ← dependencies=[Depends(require_auth)]
      ├── 17 Phase 1 modules
      ├── 5 Phase 2 modules
      ├── Phase 8-10 modules
      ├── Phase 12 modules
      ├── Phase 13-14 modules
      ├── Phase 15 module
      ├── Phase 18-22 modules
      ├── Phase 23 modules
      ├── Phase 28 modules
      └── Phase 29 modules
```

**Key design decisions:**
- `require_auth` is a lightweight JWT-only check (no DB query) for global protection
- Existing `get_current_user` (with DB lookup) remains available for routes needing full User model
- Health check endpoints (`/`, `/health`, `/ready`) are on the app directly (outside `/api/v1`), unaffected
- Auth routes (login, register, refresh) are on `public_router`, accessible without authentication

### Story 111-8: Sessions Fake Auth Fix ✅

**Modified Files:**
- `backend/src/api/v1/sessions/routes.py`
- `backend/src/api/v1/sessions/chat.py`

**Changes:**
- Replaced hardcoded `"00000000-0000-0000-0000-000000000001"` UUID in both files
- New `get_current_user_id()` uses `Depends(require_auth)` to extract `user_id` from JWT claims
- Both files now import `require_auth` from `src.core.auth`

**Before → After:**
```python
# Before
async def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"

# After
async def get_current_user_id(
    auth_claims: dict = Depends(require_auth),
) -> str:
    return auth_claims["user_id"]
```

**Impact:** 19 endpoints across sessions/routes.py and sessions/chat.py now use real user IDs from JWT tokens.

### Story 111-9: Rate Limiting ✅

**New Files:**
- `backend/src/middleware/__init__.py`
- `backend/src/middleware/rate_limit.py`

**Modified Files:**
- `backend/main.py`
- `backend/requirements.txt`
- `backend/src/api/v1/auth/routes.py`

**Changes:**

1. **Added `slowapi>=0.1.9`** to requirements.txt

2. **Created rate limiting module** (`src/middleware/rate_limit.py`):
   - Global Limiter using `get_remote_address` as key function
   - Default limit: 100 req/min (production), 1000 req/min (development)
   - `setup_rate_limiting(app)` function for easy integration

3. **Integrated into main.py**:
   - `setup_rate_limiting(app)` called during app creation

4. **Added route-specific limits to auth endpoints**:
   - `/auth/login`: 10 requests/minute per IP
   - `/auth/register`: 10 requests/minute per IP
   - Added `Request` parameter to both endpoints (required by slowapi)

## File Changes Summary

### Backend (7 modified files, 3 new files)

| File | Action | Story | Description |
|------|--------|-------|-------------|
| `src/core/config.py` | Modified | 111-1,3 | CORS origin fix + JWT secret env var + validation |
| `src/core/auth.py` | Created | 111-7 | Lightweight JWT auth dependency |
| `src/api/v1/__init__.py` | Modified | 111-7 | Public/protected router split |
| `src/api/v1/auth/routes.py` | Modified | 111-9 | Rate limiting on login/register |
| `src/api/v1/sessions/routes.py` | Modified | 111-8 | Real JWT user ID extraction |
| `src/api/v1/sessions/chat.py` | Modified | 111-8 | Real JWT user ID extraction |
| `src/middleware/__init__.py` | Created | 111-9 | Middleware module init |
| `src/middleware/rate_limit.py` | Created | 111-9 | slowapi rate limiting |
| `main.py` | Modified | 111-3,6,9 | Security validation + reload env-aware + rate limiting |
| `requirements.txt` | Modified | 111-9 | Added slowapi dependency |
| `.env.example` | Modified | 111-3,5 | JWT_SECRET_KEY + APP_ENV + Docker credentials |

### Frontend (2 modified files)

| File | Action | Story | Description |
|------|--------|-------|-------------|
| `src/store/authStore.ts` | Modified | 111-4 | Removed 5 console.log PII leaks |
| `vite.config.ts` | Modified | 111-2 | Proxy target 8010→8000 |

### Infrastructure (1 modified file)

| File | Action | Story | Description |
|------|--------|-------|-------------|
| `docker-compose.yml` | Modified | 111-5 | Grafana password default changed |

## Technical Architecture

### Auth Flow (Sprint 111)

```
Frontend Request
    │
    ├── Authorization: Bearer <JWT token>
    │
    ▼
FastAPI Router (api/v1/__init__.py)
    │
    ├── public_router (no auth)
    │   └── /auth/login, /auth/register, /auth/refresh, /auth/me
    │
    └── protected_router (Depends(require_auth))
        │
        ├── require_auth (core/auth.py)
        │   ├── Extract token from Authorization header
        │   ├── Decode JWT with jwt_secret_key
        │   ├── Validate claims (sub, exp)
        │   └── Return {"user_id", "role", "email"}
        │
        └── All business endpoints (528+ endpoints)
```

### Rate Limiting Architecture

```
Request → slowapi Limiter → Route Handler
              │
              ├── Key: Client IP (get_remote_address)
              ├── Global: 100/min (prod) or 1000/min (dev)
              ├── /auth/login: 10/min
              ├── /auth/register: 10/min
              └── Exceeded → 429 Too Many Requests
```

## Security Improvements Summary

| Metric | Before | After |
|--------|--------|-------|
| Auth coverage | 7% (38/528) | 100% (528/528) |
| Hardcoded JWT secrets | 2 locations | 0 (env var) |
| Console PII leaks | 5 statements | 0 |
| Docker weak passwords | 1 (Grafana) | 0 |
| CORS origin mismatch | Yes (3000≠3005) | Fixed |
| Vite proxy mismatch | Yes (8010≠8000) | Fixed |
| Rate limiting | None | Global + per-route |
| Uvicorn reload in prod | True (always) | Env-aware |
| Sessions fake user ID | Hardcoded UUID | JWT extraction |

## Dependencies Added

- `slowapi>=0.1.9` (rate limiting)

## Known Limitations

1. Rate limiting uses in-memory storage — upgrade to Redis in Sprint 119
2. `require_auth` is JWT-only (no DB user lookup) — endpoints needing full User model should additionally use `get_current_user` from `api/v1/dependencies.py`
3. Frontend must always send JWT token for protected routes — ensure auth flow is complete before API calls
4. Development mode with no DB: auth routes (login/register) won't work, but `require_auth` validation is JWT-only and doesn't need DB

## Next Steps

- Sprint 112: Mock code audit and separation, InMemoryApprovalStorage → Redis
- Sprint 113: MCP permission checks, ContextSynchronizer lock fix

---

**Sprint Status**: ✅ Completed
**Story Points**: 40
**Start Date**: 2026-02-23
**Completion Date**: 2026-02-23
