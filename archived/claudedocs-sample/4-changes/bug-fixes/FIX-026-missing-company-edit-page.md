# FIX-026: 公司編輯頁面路由缺失

> **狀態**: ✅ 已修復
> **發現日期**: 2026-01-13
> **修復日期**: 2026-01-13
> **影響範圍**: 公司列表頁面、公司詳情頁面
> **相關 Story**: Epic 5 - Story 5.5 (新增/停用公司配置)

---

## 問題描述

用戶從公司列表頁面點擊「編輯」按鈕後，瀏覽器導航到 `/companies/[id]/edit`，但該路由返回 404 錯誤。

**錯誤 URL 範例**:
```
http://localhost:3000/companies/2036fa82-efee-4fe8-9bc9-300dfbb3412b/edit
```

**影響頁面**:
- `/companies` - 公司列表頁面（編輯按鈕無法使用）

---

## 重現步驟

1. 進入 `/companies` 公司列表頁面
2. 點擊任意公司的「編輯」按鈕
3. 系統導航到 `/companies/[id]/edit`
4. 頁面顯示 404 錯誤

---

## 根本原因

`ForwarderList.tsx` 第 138-142 行的 `handleEdit` 函數會導航到 `/companies/${id}/edit`：

```typescript
const handleEdit = useCallback(
  (id: string) => {
    router.push(`/companies/${id}/edit`)
  },
  [router]
)
```

但是 `src/app/(dashboard)/companies/[id]/edit/page.tsx` 路由頁面**從未被創建**。

**相關組件狀態**:
- ✅ `ForwarderForm` 組件已支援編輯模式（接受 `initialData` prop）
- ✅ `/companies/new` 新增頁面存在且運作正常
- ❌ `/companies/[id]/edit` 編輯頁面不存在

---

## 解決方案

創建 `src/app/(dashboard)/companies/[id]/edit/page.tsx` 編輯頁面：

1. **伺服器端權限檢查** - 驗證 FORWARDER_MANAGE 權限
2. **獲取現有公司資料** - 使用 `getCompanyById` 服務
3. **渲染編輯表單** - 使用現有的 `ForwarderForm` 組件（傳入 `initialData`）

---

## 修改的檔案

| 文件 | 修改類型 | 說明 |
|------|----------|------|
| `src/app/(dashboard)/companies/[id]/edit/page.tsx` | 新增 | 公司編輯頁面 |

---

## 新增文件內容

### `src/app/(dashboard)/companies/[id]/edit/page.tsx`

```typescript
/**
 * @fileoverview 編輯公司頁面
 * @module src/app/(dashboard)/companies/[id]/edit/page
 * @since Epic 5 - Story 5.5
 */

import { redirect, notFound } from 'next/navigation'
import { auth } from '@/lib/auth'
import { hasPermission } from '@/lib/auth/city-permission'
import { PERMISSIONS } from '@/types/permissions'
import { getCompanyById } from '@/services/company.service'
import { ForwarderForm } from '@/components/features/forwarders'

export default async function EditCompanyPage({ params }: PageProps) {
  const resolvedParams = await params
  const companyId = resolvedParams.id

  // 1. 驗證認證狀態
  const session = await auth()
  if (!session?.user) {
    redirect('/auth/login')
  }

  // 2. 檢查權限
  const hasManagePermission = hasPermission(session.user, PERMISSIONS.FORWARDER_MANAGE)
  if (!hasManagePermission) {
    redirect(`/companies/${companyId}?error=access_denied`)
  }

  // 3. 獲取公司資料
  const company = await getCompanyById(companyId)
  if (!company) {
    notFound()
  }

  // 4. 準備初始資料並渲染表單
  const initialData = {
    id: company.id,
    name: company.name,
    code: company.code ?? '',
    description: company.description,
    contactEmail: company.contactEmail,
    defaultConfidence: company.defaultConfidence,
    logoUrl: company.logoUrl,
  }

  return (
    <ForwarderForm
      initialData={initialData}
      title="公司資訊"
      description="修改公司基本資訊"
      submitLabel="儲存變更"
    />
  )
}
```

---

## 測試驗證

1. **訪問編輯頁面**
   - 從公司列表點擊編輯按鈕
   - 確認頁面正常載入（無 404 錯誤）

2. **權限檢查**
   - 無權限用戶應被重定向到公司詳情頁面

3. **表單功能**
   - 現有資料正確顯示
   - 代碼欄位為唯讀（編輯模式）
   - 修改後提交成功

4. **導航功能**
   - 返回按鈕導向公司詳情頁
   - 取消按鈕返回上一頁
   - 成功提交後導向公司列表

---

## 技術備註

- **類型處理**: `code` 欄位在資料庫可能為 `null`，使用 `?? ''` 轉換為空字串以符合表單要求
- **組件複用**: 直接使用現有的 `ForwarderForm` 組件，無需創建新表單

---

**維護者**: Claude Code
**最後更新**: 2026-01-13
