# Sprint 72 Progress: Session Integration + Guest Migration

> **Phase 18**: Authentication System
> **Sprint 目標**: User-Session 關聯、Guest 數據遷移

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 72 |
| 計劃點數 | 8 Story Points |
| 完成點數 | 8 Story Points |
| 開始日期 | 2026-01-08 |
| 完成日期 | 2026-01-08 |
| Phase | 18 - Authentication System |
| 前置條件 | Sprint 70-71 完成（認證系統） |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S72-1 | Session User Association | 3 | ✅ 完成 | 100% |
| S72-2 | Guest Data Migration API | 3 | ✅ 完成 | 100% |
| S72-3 | Frontend Migration Flow | 2 | ✅ 完成 | 100% |

**整體進度**: 8/8 pts (100%) ✅

---

## 詳細進度記錄

### S72-1: Session User Association (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 修改 user_id 為 nullable（支持 guest sessions）
- [x] 添加 ForeignKey 到 users 表
- [x] 添加 guest_user_id 欄位
- [x] 添加 User relationship
- [x] 在 User model 添加 sessions relationship
- [x] 創建 get_user_id_or_guest 依賴函數
- [x] 創建 get_user_and_guest_id 依賴函數

**修改檔案**:
- [x] `backend/src/infrastructure/database/models/session.py`
- [x] `backend/src/infrastructure/database/models/user.py`
- [x] `backend/src/api/v1/ag_ui/dependencies.py`

**Model 變更**:
```python
# SessionModel
user_id: Mapped[Optional[uuid4]] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("users.id", ondelete="SET NULL"),
    nullable=True,  # Allow guest sessions
    index=True,
)

guest_user_id: Mapped[Optional[str]] = mapped_column(
    String(100),
    nullable=True,
    index=True,
)

user: Mapped[Optional["User"]] = relationship(
    "User",
    back_populates="sessions",
)
```

---

### S72-2: Guest Data Migration API (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 migration.py router
- [x] 實現 POST /auth/migrate-guest 端點
- [x] 實現 session 遷移邏輯
- [x] 實現 sandbox 目錄遷移
- [x] 處理 name conflicts
- [x] 返回遷移摘要

**新增檔案**:
- [x] `backend/src/api/v1/auth/migration.py`

**修改檔案**:
- [x] `backend/src/api/v1/auth/__init__.py`

**API 端點**:
```
POST /api/v1/auth/migrate-guest
Body: { "guest_id": "guest-xxx-xxx" }
Response: {
    "success": true,
    "sessions_migrated": 5,
    "directories_migrated": ["uploads", "sandbox"],
    "message": "Successfully migrated data from guest guest-xxx"
}
```

**遷移邏輯**:
1. 更新 sessions 的 user_id 並清除 guest_user_id
2. 移動 uploads/{guest_id}/* → uploads/{user_id}/
3. 移動 sandbox/{guest_id}/* → sandbox/{user_id}/
4. 移動 outputs/{guest_id}/* → outputs/{user_id}/
5. 清理空的 guest 目錄

---

### S72-3: Frontend Migration Flow (2 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] migrateGuestData() 函數（已存在於 guestUser.ts）
- [x] 調用 API 傳送 guest_id
- [x] 成功後清除 guest_id
- [x] 在 login action 中調用（已在 S71-1 實現）
- [x] 優雅處理遷移失敗（non-blocking）

**已存在檔案（無需修改）**:
- `frontend/src/utils/guestUser.ts` - migrateGuestData() 已完整實現
- `frontend/src/store/authStore.ts` - login() 已調用 migrateGuestData()

**前端遷移流程**:
```typescript
// authStore.ts login action 中
migrateGuestData(tokenResponse.access_token).catch((err) => {
  console.warn('[AuthStore] Guest data migration failed:', err);
});
```

---

## 技術備註

### 完整遷移流程

```
[Guest User]
     │
     ├── 使用 guest-xxx-xxx ID
     ├── 創建 Sessions (guest_user_id = guest-xxx)
     └── 上傳文件 (data/uploads/guest-xxx/)
           │
           ▼ [用戶登入]
           │
[Frontend] authStore.login()
     │
     ├── POST /api/v1/auth/login → 獲取 token
     ├── GET /api/v1/auth/me → 獲取用戶資訊
     └── POST /api/v1/auth/migrate-guest (non-blocking)
           │
           ▼
[Backend] migrate_guest_data()
     │
     ├── UPDATE sessions SET user_id=:user, guest_user_id=NULL
     ├── MOVE uploads/{guest}/* → uploads/{user}/
     ├── MOVE sandbox/{guest}/* → sandbox/{user}/
     └── MOVE outputs/{guest}/* → outputs/{user}/
           │
           ▼
[Frontend] clearGuestUserId()
     │
     └── localStorage.removeItem('ipa_guest_user_id')
```

### 錯誤處理

| 場景 | 行為 |
|------|------|
| 無 guest_id | 跳過遷移 |
| API 調用失敗 | 記錄警告，繼續登入 |
| 目錄移動失敗 | 繼續其他目錄 |
| 同名文件衝突 | 添加數字後綴 |

---

## 新增/修改檔案總覽

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `backend/src/api/v1/auth/migration.py` | Guest 數據遷移 API |

### 修改檔案

| 檔案 | 說明 |
|------|------|
| `backend/src/infrastructure/database/models/session.py` | 添加 user FK + guest_user_id |
| `backend/src/infrastructure/database/models/user.py` | 添加 sessions relationship |
| `backend/src/api/v1/ag_ui/dependencies.py` | 添加 get_user_id_or_guest |
| `backend/src/api/v1/auth/__init__.py` | 註冊 migration router |

---

## Phase 18 完成總結

| Sprint | Focus | Points | Status |
|--------|-------|--------|--------|
| Sprint 70 | Backend Core Auth | 13 pts | ✅ |
| Sprint 71 | Frontend Auth | 13 pts | ✅ |
| Sprint 72 | Session + Migration | 8 pts | ✅ |
| **Total** | | **34 pts** | ✅ |

### Phase 18 功能清單

| 功能 | 狀態 |
|------|------|
| JWT Authentication | ✅ |
| Password Hashing (bcrypt) | ✅ |
| Auth API Routes | ✅ |
| Auth Dependencies | ✅ |
| Frontend Auth Store | ✅ |
| Login/Signup Pages | ✅ |
| Protected Routes | ✅ |
| API Token Interceptor | ✅ |
| Session-User Association | ✅ |
| Guest Data Migration | ✅ |

---

**更新日期**: 2026-01-08
**Sprint 狀態**: ✅ 完成
**Phase 18 狀態**: ✅ 完成
