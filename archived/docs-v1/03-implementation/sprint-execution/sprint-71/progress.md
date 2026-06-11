# Sprint 71 Progress: Frontend Authentication + Protected Routes

> **Phase 18**: Authentication System
> **Sprint 目標**: Auth Store、Login/Signup 頁面、路由保護

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 71 |
| 計劃點數 | 13 Story Points |
| 完成點數 | 13 Story Points |
| 開始日期 | 2026-01-08 |
| 完成日期 | 2026-01-08 |
| Phase | 18 - Authentication System |
| 前置條件 | Sprint 70 完成（後端認證 API） |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S71-1 | Auth Store (Zustand) | 3 | ✅ 完成 | 100% |
| S71-2 | Login/Signup Pages | 5 | ✅ 完成 | 100% |
| S71-3 | ProtectedRoute Component | 3 | ✅ 完成 | 100% |
| S71-4 | API Client Token Interceptor | 2 | ✅ 完成 | 100% |

**整體進度**: 13/13 pts (100%) ✅

---

## 詳細進度記錄

### S71-1: Auth Store (Zustand) (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `authStore.ts`
- [x] 定義 User 和 AuthState 介面
- [x] 實現 `login()` action
- [x] 實現 `register()` action
- [x] 實現 `logout()` action
- [x] 添加 persist middleware
- [x] 實現 session restore (refreshSession)
- [x] 登入時調用 migrateGuestData

**新增檔案**:
- [x] `frontend/src/store/authStore.ts`

**代碼模式**:
```typescript
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: async (email, password) => {
        const tokenResponse = await apiLogin(email, password);
        const user = await apiGetMe(tokenResponse.access_token);
        set({ token: tokenResponse.access_token, user, isAuthenticated: true });
        migrateGuestData(tokenResponse.access_token);
        return true;
      },
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
        clearGuestUserId();
      },
    }),
    { name: 'ipa-auth-storage' }
  )
);
```

---

### S71-2: Login/Signup Pages (5 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `LoginPage.tsx`
- [x] 創建 `SignupPage.tsx`
- [x] 表單驗證（email、密碼長度）
- [x] 錯誤訊息顯示
- [x] 載入狀態
- [x] 成功後重導向
- [x] 更新 App.tsx 路由

**新增檔案**:
- [x] `frontend/src/pages/auth/LoginPage.tsx`
- [x] `frontend/src/pages/auth/SignupPage.tsx`

**修改檔案**:
- [x] `frontend/src/App.tsx` - 添加 /login 和 /signup 路由

**表單驗證規則**:
| 欄位 | 驗證規則 |
|------|----------|
| Email | 必填、有效格式 |
| 密碼 | 必填、最少 8 字元 |
| 確認密碼 | 與密碼一致（註冊） |
| 姓名 | 選填、最多 100 字元 |

---

### S71-3: ProtectedRoute Component (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `ProtectedRoute.tsx`
- [x] 檢查 isAuthenticated
- [x] 載入時顯示 spinner
- [x] 未認證重導向至 /login
- [x] 支援 requiredRoles 參數
- [x] 更新 App.tsx 路由包裝

**新增檔案**:
- [x] `frontend/src/components/auth/ProtectedRoute.tsx`

**修改檔案**:
- [x] `frontend/src/App.tsx` - 使用 ProtectedRoute 包裝 AppLayout

**使用方式**:
```tsx
// 基本保護
<ProtectedRoute>
  <AppLayout />
</ProtectedRoute>

// 角色限制
<ProtectedRoute requiredRoles={['admin']}>
  <AdminPanel />
</ProtectedRoute>
```

---

### S71-4: API Client Token Interceptor (2 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 更新 getAuthToken() 從 authStore 讀取
- [x] 添加 Authorization header
- [x] 處理 401 回應
- [x] 觸發 logout 並重導向

**修改檔案**:
- [x] `frontend/src/api/client.ts`

**401 處理流程**:
```
API 回應 401
    │
    ├── 調用 handleUnauthorized()
    │     ├── authStore.logout()
    │     └── window.location.href = '/login'
    │
    └── 拋出 ApiError('Unauthorized', 401)
```

---

## 技術備註

### 認證流程

```
User → LoginPage
         │
         ▼
    authStore.login()
         │
         ├── POST /api/v1/auth/login
         ├── GET /api/v1/auth/me
         ├── Store token + user
         └── migrateGuestData()
               │
               ▼
         Navigate to Dashboard
```

### 路由保護架構

```
App.tsx
├── /login (獨立頁面)
├── /signup (獨立頁面)
└── / (ProtectedRoute 包裝)
    └── AppLayout
        ├── /dashboard
        ├── /chat
        ├── /workflows/*
        ├── /agents/*
        └── ...
```

### 狀態持久化

| 項目 | 儲存位置 | Key |
|------|----------|-----|
| Auth State | localStorage | `ipa-auth-storage` |
| Token | (包含在 Auth State) | - |
| User | (包含在 Auth State) | - |

---

## 新增/修改檔案總覽

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `frontend/src/store/authStore.ts` | Zustand 認證狀態管理 |
| `frontend/src/pages/auth/LoginPage.tsx` | 登入頁面 |
| `frontend/src/pages/auth/SignupPage.tsx` | 註冊頁面 |
| `frontend/src/components/auth/ProtectedRoute.tsx` | 路由保護組件 |

### 修改檔案

| 檔案 | 說明 |
|------|------|
| `frontend/src/App.tsx` | 添加 auth 路由 + ProtectedRoute |
| `frontend/src/api/client.ts` | Token 攔截器 + 401 處理 |

---

## 下一步：Sprint 72

Sprint 72 將完成 Session 整合和 Guest 遷移：
- Session User 關聯
- Guest 數據遷移 API
- 前端遷移流程

---

**更新日期**: 2026-01-08
**Sprint 狀態**: ✅ 完成
