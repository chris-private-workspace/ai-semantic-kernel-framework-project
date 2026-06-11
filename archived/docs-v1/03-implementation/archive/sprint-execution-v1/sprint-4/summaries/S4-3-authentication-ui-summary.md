# S4-3: Authentication UI - 實現摘要

**Story ID**: S4-3
**標題**: Authentication UI
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-26

---

## 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| 登錄頁面 UI | ✅ | 使用 Design System 組件 |
| OAuth 2.0 登錄流程 | ✅ | Azure AD OAuth 準備就緒 |
| JWT token 管理 | ✅ | 完整的 token 存儲和管理 |
| 自動刷新 token | ✅ | 每分鐘檢查，提前 5 分鐘刷新 |
| 登出功能 | ✅ | 清除 token 和狀態 |

---

## 技術實現

### 主要組件

| 組件/檔案 | 用途 |
|----------|------|
| `LoginPage.tsx` | 登錄頁面 UI（使用 Design System） |
| `AuthCallbackPage.tsx` | OAuth 回調處理頁面 |
| `useAuth.ts` | 認證邏輯 hook（登錄、登出、token 刷新） |
| `auth.ts` | 認證 API 服務 |

### 關鍵代碼

```typescript
// src/api/auth.ts - Token 管理
export function saveTokens(
  accessToken: string,
  refreshToken: string,
  expiresIn: number
): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  const expiryTime = Date.now() + expiresIn * 1000
  localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString())
}

export function shouldRefreshToken(): boolean {
  const expiry = getTokenExpiry()
  if (!expiry) return false
  // Refresh token 5 minutes before expiry
  return Date.now() >= expiry - 5 * 60 * 1000
}
```

```typescript
// src/hooks/useAuth.ts - 自動 Token 刷新
const setupRefreshTimer = useCallback(() => {
  refreshTimerRef.current = window.setInterval(async () => {
    if (shouldRefreshToken()) {
      const refreshTokenValue = getRefreshToken()
      if (refreshTokenValue) {
        const response = await apiRefreshToken(refreshTokenValue)
        saveTokens(response.access_token, refreshTokenValue, response.expires_in)
      }
    }
  }, 60000) // Check every minute
}, [])
```

```typescript
// src/features/auth/LoginPage.tsx - 使用 Design System 組件
<Card className="w-full max-w-md">
  <CardHeader className="text-center">
    <CardTitle className="text-2xl">IPA Platform</CardTitle>
    <CardDescription>Intelligent Process Automation</CardDescription>
  </CardHeader>
  <CardContent>
    <form onSubmit={handleSubmit}>
      <Label htmlFor="email">Email</Label>
      <Input id="email" type="email" ... />
      <Button type="submit" disabled={loading}>
        {loading ? <Spinner /> : 'Login'}
      </Button>
    </form>
    <Button variant="outline" onClick={handleAzureAdLogin}>
      Login with Microsoft
    </Button>
  </CardContent>
</Card>
```

### 認證流程

```
1. Email/Password 登錄:
   User → LoginPage → useAuth.login() → apiLogin() → saveTokens() → Navigate

2. Azure AD OAuth:
   User → LoginPage → initiateAzureAdLogin() → Redirect to Azure AD
   Azure AD → /auth/callback → handleOAuthCallback() → saveTokens() → Navigate

3. Token 刷新:
   Timer (每分鐘) → shouldRefreshToken() → apiRefreshToken() → saveTokens()

4. 登出:
   User → useAuth.logout() → apiLogout() → clearTokens() → Navigate to /login
```

---

## 代碼位置

```
frontend/src/
├── api/
│   └── auth.ts              # 認證 API 服務
├── hooks/
│   ├── index.ts             # Hooks 導出
│   └── useAuth.ts           # 認證 hook
└── features/
    └── auth/
        ├── index.ts         # Feature 導出
        ├── LoginPage.tsx    # 登錄頁面
        └── AuthCallbackPage.tsx  # OAuth 回調頁面
```

---

## 測試覆蓋

| 測試文件 | 測試數量 | 狀態 |
|---------|---------|------|
| 單元測試 | 待 S4-10 | ⏳ |
| E2E 測試 | 待 S4-10 | ⏳ |

### 構建驗證
- ✅ `npm run build` 成功
- ✅ TypeScript 編譯無錯誤
- ✅ 產出文件大小：
  - CSS: 23.06 kB (gzip: 5.19 kB)
  - JS: 427.49 kB (gzip: 139.01 kB)

---

## 備註

### 開發模式 Mock Auth
- 環境變量 `VITE_ENABLE_MOCK_AUTH=true` 啟用 mock 認證
- 無需後端即可進行前端開發
- Mock token 有效期 1 小時

### Azure AD OAuth
- OAuth 流程使用後端代理 (`/api/v1/auth/azure/login`)
- 回調 URL: `/auth/callback`
- 需要後端配置 Azure AD 應用程序

### Token 管理策略
- Access Token 存儲在 localStorage
- Refresh Token 存儲在 localStorage
- Token 過期前 5 分鐘自動刷新
- 刷新失敗時自動登出

### 路由保護
- `ProtectedRoute` 組件檢查認證狀態
- 未認證用戶重定向到 `/login`
- 登錄後重定向回原始頁面

---

## 相關文檔

- [Sprint 規劃](../../sprint-planning/sprint-4-ui-frontend.md)
- [S4-2 Design System 摘要](./S4-2-design-system-summary.md)
- [Frontend README](../../../../frontend/README.md)

---

**生成日期**: 2025-11-26
