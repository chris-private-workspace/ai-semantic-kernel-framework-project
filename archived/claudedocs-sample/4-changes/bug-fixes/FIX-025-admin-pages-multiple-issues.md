# FIX-025: Admin Pages Multiple Issues

> **狀態**: ✅ 已修復
> **發現日期**: 2026-01-07
> **修復日期**: 2026-01-07
> **影響範圍**: Term Analysis 頁面、Prompt Configs 編輯頁面
> **相關 Story**: Epic 0 (Term Analysis), Epic 14 (Prompt Configs)

---

## 問題列表

### 問題 1: Prompt 測試 API 405 錯誤

**錯誤訊息**:
```
POST http://localhost:3500/api/v1/prompt-configs/test 405 (Method Not Allowed)
```

**影響頁面**: `/admin/prompt-configs/[id]`

**根因**: API 端點 `/api/v1/prompt-configs/test` 不存在

**解決方案**: 創建新的 API 端點

---

### 問題 2: Prompt 類型和適用範圍不能修改（設計決定）

**影響頁面**: `/admin/prompt-configs/[id]`

**表現**: 在編輯頁面中，「Prompt 類型」和「適用範圍」兩個欄位被禁用

**根因**: 這是**設計決定**，不是 Bug

**說明**:
- `PromptConfigForm.tsx:217`: `disabled={isEditMode}` - Prompt 類型禁用
- `PromptConfigForm.tsx:250`: `disabled={isEditMode}` - 適用範圍禁用
- **原因**: 這些欄位組成唯一約束 `(promptType + scope + companyId + documentFormatId)`
- 編輯時修改可能導致與現有配置衝突
- 若需修改這些欄位，應刪除配置後重新創建

---

### 問題 3: Term Analysis 頁面 SelectItem 空值錯誤

**錯誤訊息**:
```
A <Select.Item /> must have a value prop that is not an empty string.
```

**影響頁面**: `/admin/term-analysis`

**根因**: `TermFilters.tsx` 中使用了 `<SelectItem value="">` 空字串作為值

**受影響位置**:
- 第 114 行: `<SelectItem value="">All batches</SelectItem>`
- 第 135 行: `<SelectItem value="">All companies</SelectItem>`
- 第 176 行: `<SelectItem value="">500 (default)</SelectItem>`

**解決方案**: 使用 `"__all__"` 作為代表「全部」的值

---

## 修復詳情

### 修改文件

| 文件 | 修改內容 |
|------|----------|
| `src/components/features/term-analysis/TermFilters.tsx` | 將空字串值改為 `"__all__"` |
| `src/app/api/v1/prompt-configs/test/route.ts` | 新建 - Prompt 測試 API 端點 |

### TermFilters.tsx 修改

```typescript
// 修改前
<SelectItem value="">All batches</SelectItem>

// 修改後
<SelectItem value="__all__">All batches</SelectItem>

// handleFilterChange 也需處理 "__all__"
[key]: value === '' || value === '__all__' ? undefined : value,
```

### Prompt Test API 實現

創建 `src/app/api/v1/prompt-configs/test/route.ts`:

- 接收 FormData（configId + file）
- 載入配置並解析變數
- 返回模擬測試結果（TODO: 整合實際 GPT Vision 服務）

---

## Git Commits

| Commit Hash | 說明 |
|-------------|------|
| `f7cf459` | fix(term-analysis): replace empty string SelectItem values with '__all__' |
| `633f95f` | feat(prompt-configs): add test API endpoint (mock mode) |

---

## 待辦事項

- [x] **Prompt Test API**: 整合實際 GPT Vision 服務進行真實測試 ✅ (2026-01-07)
  - 已整合 Azure OpenAI GPT-5.2 Vision 服務
  - 支援 PDF 和圖片文件測試
  - 返回真實的提取結果、Token 使用量、執行時間

---

## 驗證步驟

1. 開啟 `/admin/term-analysis` 頁面
   - 確認無 SelectItem 錯誤
   - 確認篩選器正常運作

2. 開啟 `/admin/prompt-configs/[id]` 編輯頁面
   - 測試功能應返回模擬結果（而非 405 錯誤）
   - Prompt 類型和適用範圍為唯讀（設計如此）

---

**維護者**: Claude Code
**最後更新**: 2026-01-07
