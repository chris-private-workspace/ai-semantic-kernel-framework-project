# FIX-030: 生產模式認證與 Session 同步問題

## 問題描述

### 問題 1: 生產模式 API 返回 403 Forbidden
- **症狀**: `/api/dashboard/statistics` 等 API 在生產模式下返回 403
- **根本原因**: `auth.ts` 中的 `isDevelopmentMode` 邏輯錯誤，使用 `&&` 而非 `||`

### 問題 2: 登錄後用戶信息不顯示
- **症狀**: 登錄成功後，右上角用戶信息需要重新整理頁面才能看到
- **根本原因**: Server Action 的 `signIn` 設置 cookie 後，客戶端 SessionProvider 沒有立即讀取到新 session

### 問題 3: Global View 頁面被重定向回 Dashboard
- **症狀**: 登錄後訪問 Global View 頁面時被重定向回 dashboard
- **根本原因**: `session.user.isGlobalAdmin` 為 `undefined` 時被視為 falsy 值

## 修復方案

### 修改 1: auth.ts - 開發模式判斷邏輯

**問題代碼**:
```typescript
// 錯誤：使用 && 導致只有同時滿足兩個條件才啟用開發模式
const isDevelopmentMode = process.env.NODE_ENV === 'development' && !isAzureADConfigured()
```

**修復代碼**:
```typescript
// 正確：改為函數，運行時計算，使用 || 確保任一條件成立即啟用
function isDevelopmentMode(): boolean {
  return process.env.NODE_ENV === 'development' || !isAzureADConfigured()
}
```

**關鍵點**:
- 從常數改為函數，避免構建時烘焙
- 使用 `||` 確保 Azure AD 未配置時也能使用開發模式認證

### 修改 2: 新建 DevLoginForm 客戶端組件

**文件**: `src/components/features/auth/DevLoginForm.tsx`

**解決方案**:
```typescript
'use client'

import { signIn } from 'next-auth/react'
import { useRouter } from 'next/navigation'

export function DevLoginForm({ callbackUrl }: DevLoginFormProps) {
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    const result = await signIn('credentials', {
      email,
      password: 'dev',
      redirect: false,  // 不自動重定向
    })

    if (result?.ok) {
      router.push(callbackUrl ?? '/dashboard')
      router.refresh()  // 強制刷新頁面數據
    }
  }
}
```

**關鍵點**:
- 使用客戶端 `signIn` 而非 Server Action
- `redirect: false` 後手動 `router.push` + `router.refresh`
- 確保 SessionProvider 正確同步

### 修改 3: Global Page Session 檢查

**文件**: `src/app/[locale]/(dashboard)/global/page.tsx`

**問題代碼**:
```typescript
if (!session.user.isGlobalAdmin) {
  redirect('/dashboard')  // undefined 也會觸發重定向
}
```

**修復代碼**:
```typescript
// 首次加載時，強制刷新 session
useEffect(() => {
  const checkSession = async () => {
    if (status === 'authenticated' && session?.user) {
      if (session.user.isGlobalAdmin === undefined) {
        await update()  // 強制刷新 session
      }
      setIsChecking(false)
    }
  }
  checkSession()
}, [status, session, update])

// 明確檢查 false，避免 undefined 導致錯誤重定向
if (session.user.isGlobalAdmin === false) {
  redirect('/dashboard')
}
```

### 修改 4: AuthProvider 配置

**文件**: `src/providers/AuthProvider.tsx`

```typescript
<SessionProvider
  refetchOnWindowFocus={true}   // 窗口獲得焦點時重新獲取 session
  refetchWhenOffline={false}
>
```

## 修改的文件清單

| 文件 | 修改類型 | 說明 |
|------|----------|------|
| `src/lib/auth.ts` | 修改 | `isDevelopmentMode` 改為函數，`&&` → `\|\|` |
| `src/lib/auth.config.ts` | 修改 | 添加同步提示註釋 |
| `src/components/features/auth/DevLoginForm.tsx` | 新建 | 客戶端登錄組件 |
| `src/app/[locale]/(auth)/auth/login/page.tsx` | 修改 | 使用客戶端登錄組件 |
| `src/app/[locale]/(dashboard)/global/page.tsx` | 修改 | 添加 session 刷新機制 |
| `src/providers/AuthProvider.tsx` | 修改 | 添加 `refetchOnWindowFocus` |

## 測試驗證

### 測試環境
- 生產模式 (`npm run build && npm start`)
- Port: 3200

### 測試結果
- ✅ 登錄後用戶信息 "admin admin@example.com" 立即顯示
- ✅ "Global Admin" 標籤正確顯示
- ✅ Global View 頁面可正常訪問
- ✅ Dashboard API 正常返回數據

## 根本原因分析

```
問題根源
    │
    ├── auth.ts isDevelopmentMode 邏輯錯誤
    │   └── && 導致生產環境即使 Azure AD 未配置也不啟用開發模式
    │
    ├── Server Action signIn 的 session 同步問題
    │   └── 服務端設置 cookie，客戶端 SessionProvider 不會自動刷新
    │
    └── isGlobalAdmin undefined 處理不當
        └── JavaScript falsy 檢查將 undefined 視為 false
```

## 教訓與最佳實踐

1. **環境變數判斷應使用函數**: 避免構建時烘焙，確保運行時正確計算
2. **NextAuth 登錄後 session 同步**: 使用客戶端 `signIn` + `router.refresh()` 確保同步
3. **布林值檢查要明確**: 使用 `=== false` 而非 `!value` 避免 undefined 問題
4. **auth.ts 和 auth.config.ts 邏輯必須一致**: 兩個文件的開發模式判斷必須同步

---

**修復日期**: 2026-01-18
**修復者**: Claude AI Assistant
**相關 Epic**: Epic 17 - 國際化 (i18n)
