# FIX-019: 匯出空白 Excel - 認證重導向問題

## 問題摘要

| 項目 | 說明 |
|------|------|
| **發現日期** | 2026-01-05 |
| **影響範圍** | 歷史數據頁面的階層式術語匯出功能 |
| **嚴重程度** | 高（功能無法使用） |
| **根本原因** | 認證失敗時 fetch 自動跟隨重導向，下載 HTML 而非 Excel |

---

## 問題描述

### 症狀
- 用戶在 `/admin/historical-data` 頁面點擊「匯出術語」按鈕
- UI 顯示「匯出成功」並下載了 .xlsx 檔案
- 但檔案內容為空或無法開啟

### 調查過程

1. **後端服務驗證** ✅
   - `hierarchical-term-aggregation.service.ts` 正確產生資料
   - 測試腳本顯示：56 家公司，335 個術語，463 次出現

2. **API 端點測試** ❌
   - 直接呼叫 API 返回 HTML（登入頁面）而非 Excel
   - 伺服器日誌顯示重導向：
     ```
     GET /auth/login?callbackUrl=http%3A%2F%2Flocalhost%3A3010%2Fapi%2Fv1%2Fbatches%2F...
     ```

3. **認證配置確認**
   - `src/lib/auth.config.ts` 第 134, 144-146 行
   - `/api/v1/*` 路由需要認證

---

## 根本原因

### 問題流程
```
1. 用戶點擊匯出按鈕
2. fetch 發送到 /api/v1/batches/${batchId}/hierarchical-terms/export
3. Middleware 檢測到未認證（session 過期或 cookie 未傳送）
4. Middleware 返回 302 重導向到 /auth/login
5. fetch 自動跟隨重導向（預設行為）
6. Response 變成登入頁面 HTML，狀態碼 200
7. response.ok === true（因為是 200）
8. 前端沒有檢查 Content-Type
9. response.blob() 將 HTML 轉為 blob
10. 下載的檔案實際上是 HTML，但副檔名是 .xlsx
```

### 問題代碼
```typescript
// HierarchicalTermsExportButton.tsx（修復前）
const response = await fetch(
  `/api/v1/batches/${batchId}/hierarchical-terms/export`,
  { method: 'GET' }  // 沒有 credentials，沒有 Content-Type 驗證
)

if (!response.ok) {  // 這裡 response.ok === true（因為重導向後是 200）
  // ...
}

const blob = await response.blob()  // 將 HTML 轉為 blob
```

---

## 修復方案

### 修改檔案
`src/components/features/historical-data/HierarchicalTermsExportButton.tsx`

### 修復內容

1. **添加 `credentials: 'include'`** - 確保認證 cookies 被發送
2. **添加 Content-Type 驗證** - 確保返回的是 Excel 格式

```typescript
// 修復後
const response = await fetch(
  `/api/v1/batches/${batchId}/hierarchical-terms/export`,
  {
    method: 'GET',
    credentials: 'include', // 確保認證 cookies 被發送
  }
)

if (!response.ok) {
  const errorData = await response.json()
  throw new Error(errorData.error || '匯出失敗')
}

// 檢查 Content-Type 確保是 Excel 格式
const contentType = response.headers.get('Content-Type') || ''
if (!contentType.includes('spreadsheetml') && !contentType.includes('application/octet-stream')) {
  // 可能是被重導向到登入頁面
  console.error('[Export] Unexpected content type:', contentType)
  throw new Error('認證已過期，請重新登入後再試')
}
```

---

## 驗證步驟

### 測試場景 1：正常匯出
1. 登入系統
2. 導航到 `/admin/historical-data`
3. 選擇一個 COMPLETED 狀態的批次
4. 點擊「匯出術語」按鈕
5. **預期結果**: 下載有效的 Excel 檔案

### 測試場景 2：認證過期
1. 登入系統
2. 導航到 `/admin/historical-data`
3. 在另一個分頁登出或等待 session 過期
4. 點擊「匯出術語」按鈕
5. **預期結果**: 顯示錯誤提示「認證已過期，請重新登入後再試」

---

## 相關檔案

| 檔案 | 變更 |
|------|------|
| `src/components/features/historical-data/HierarchicalTermsExportButton.tsx` | 添加 credentials 和 Content-Type 驗證 |
| `src/lib/auth.config.ts` | 無變更（僅供參考） |
| `src/middleware.ts` | 無變更（僅供參考） |

---

## 經驗教訓

1. **所有下載 API 調用都應檢查 Content-Type** - 確保返回的是預期格式
2. **fetch 預設會跟隨重導向** - 需要特別注意認證相關的 API
3. **認證過期的錯誤處理** - 應該給用戶清楚的提示，而非靜默失敗

---

**修復者**: Claude Code
**修復日期**: 2026-01-05
**狀態**: ✅ 已修復
