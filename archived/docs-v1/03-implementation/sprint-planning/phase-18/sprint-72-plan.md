# Sprint 72: Session Integration + Guest Migration

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 72 |
| **Phase** | 18 - Authentication System |
| **Duration** | 1-2 days |
| **Total Points** | 8 |
| **Focus** | User-Session association, Guest data migration |

## Sprint Goals

1. Associate Sessions with Users
2. Implement Guest data migration API
3. Frontend migration flow on first login

## Prerequisites

- Sprint 70-71 completed
- Backend auth working
- Frontend auth working

---

## Stories

### S72-1: Session User Association (3 pts)

**Description**: Associate Sessions and Threads with authenticated Users.

**Acceptance Criteria**:
- [ ] Add user_id to Session model (optional FK)
- [ ] Update session creation to use current user
- [ ] Filter sessions by user in queries
- [ ] Support both guest and auth users

**Technical Details**:
```python
# backend/src/domain/sessions/models.py - Update
class SessionModel(Base):
    ...
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # Allow guest sessions
        index=True,
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="sessions")
```

```python
# backend/src/api/v1/ag_ui/dependencies.py - Update
async def get_user_id_or_guest(
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_guest_id: Optional[str] = Header(None),
) -> str:
    """Get user ID from auth or guest header."""
    if current_user:
        return str(current_user.id)
    if x_guest_id:
        return x_guest_id
    raise HTTPException(status_code=401, detail="User identification required")
```

**Files to Modify**:
- `backend/src/domain/sessions/models.py` - Add user_id
- `backend/src/domain/sessions/service.py` - User filtering
- `backend/src/api/v1/ag_ui/dependencies.py` - Unified user ID

---

### S72-2: Guest Data Migration API (3 pts)

**Description**: Implement API to migrate Guest data to authenticated User.

**Acceptance Criteria**:
- [ ] Create POST /auth/migrate-guest endpoint
- [ ] Migrate sessions from guest_id to user_id
- [ ] Migrate sandbox directories
- [ ] Return migration summary
- [ ] Handle already-migrated data

**Technical Details**:
```python
# backend/src/api/v1/auth/migration.py
from fastapi import APIRouter, Depends
from src.domain.sessions.service import SessionService
from src.core.sandbox_config import SandboxConfig
import shutil

router = APIRouter()

@router.post("/migrate-guest")
async def migrate_guest_data(
    guest_id: str,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
) -> dict:
    """Migrate guest data to authenticated user."""
    user_id = str(current_user.id)

    # 1. Migrate sessions
    sessions_migrated = await session_service.migrate_user_sessions(
        from_user_id=guest_id,
        to_user_id=user_id,
    )

    # 2. Migrate sandbox directories
    dirs_migrated = []
    for dir_type in ["uploads", "sandbox", "outputs"]:
        guest_dir = SandboxConfig.get_user_dir(guest_id, dir_type)
        user_dir = SandboxConfig.get_user_dir(user_id, dir_type)

        if guest_dir.exists():
            user_dir.mkdir(parents=True, exist_ok=True)
            # Move files from guest to user
            for item in guest_dir.iterdir():
                shutil.move(str(item), str(user_dir / item.name))
            guest_dir.rmdir()
            dirs_migrated.append(dir_type)

    return {
        "success": True,
        "sessions_migrated": sessions_migrated,
        "directories_migrated": dirs_migrated,
    }
```

**Files to Create**:
- `backend/src/api/v1/auth/migration.py`

**Files to Modify**:
- `backend/src/domain/sessions/service.py` - Add migrate_user_sessions

---

### S72-3: Frontend Migration Flow (2 pts)

**Description**: Trigger guest migration on first login.

**Acceptance Criteria**:
- [ ] Check for guest_id on login success
- [ ] Call migrate-guest API
- [ ] Clear guest_id after migration
- [ ] Show migration success message (optional)

**Technical Details**:
```typescript
// frontend/src/utils/guestUser.ts - Update
export async function migrateGuestData(authToken: string): Promise<void> {
  const guestId = localStorage.getItem(GUEST_USER_KEY);
  if (!guestId) return;

  try {
    const response = await fetch('/api/v1/auth/migrate-guest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
      body: JSON.stringify({ guest_id: guestId }),
    });

    if (response.ok) {
      localStorage.removeItem(GUEST_USER_KEY);
      console.log('Guest data migrated successfully');
    }
  } catch (error) {
    console.error('Failed to migrate guest data:', error);
    // Non-critical - guest data remains, user can continue
  }
}
```

```typescript
// frontend/src/store/authStore.ts - Update login action
login: async (email, password) => {
  // ... existing login code ...

  // After successful login, migrate guest data
  const guestId = localStorage.getItem('ipa_guest_user_id');
  if (guestId) {
    await migrateGuestData(access_token);
  }
}
```

**Files to Modify**:
- `frontend/src/utils/guestUser.ts`
- `frontend/src/store/authStore.ts`

---

## Definition of Done

- [ ] All 3 stories completed and tested
- [ ] Sessions associated with users
- [ ] Guest migration works end-to-end
- [ ] Data properly transferred

---

## Phase 18 Completion Summary

After Sprint 72:

| Feature | Status |
|---------|--------|
| JWT Authentication | ✅ Sprint 70 |
| Auth API Routes | ✅ Sprint 70 |
| Frontend Auth Store | ✅ Sprint 71 |
| Login/Signup Pages | ✅ Sprint 71 |
| Protected Routes | ✅ Sprint 71 |
| Session-User Association | ✅ Sprint 72 |
| Guest Migration | ✅ Sprint 72 |

**Total Points**: 34 pts (13 + 13 + 8)

---

## Sprint Velocity Reference

Integration and migration work.
Expected completion: 1-2 days for 8 pts
