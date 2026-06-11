# FIX-024: Hooks API Path Errors

> **狀態**: ✅ 已修復
> **發現日期**: 2026-01-07
> **修復日期**: 2026-01-07
> **影響範圍**: Field Mapping Configs 後台頁面、Prompt Configs 編輯頁面
> **相關 Story**: Story 13-7, Story 14-1

---

## 問題描述

### 問題 1: Companies API 路徑錯誤 (404)

**錯誤訊息**:
```
GET http://localhost:3500/api/v1/companies?limit=100&sortBy=name 404 (Not Found)
```

**影響頁面**:
- `/admin/field-mapping-configs`
- `/admin/prompt-configs/[id]`

**根因**: Hooks 使用錯誤的 API 路徑 `/api/v1/companies`，實際端點為 `/api/companies`

---

### 問題 2: Document Formats API 路徑錯誤 (404)

**錯誤訊息**:
```
GET http://localhost:3500/api/v1/document-formats?limit=100&sortBy=name 404 (Not Found)
```

**影響頁面**:
- `/admin/field-mapping-configs`
- `/admin/prompt-configs/[id]`

**根因**: Hooks 使用錯誤的 API 路徑 `/api/v1/document-formats`，實際端點為 `/api/v1/formats`

---

### 問題 3: Formats API 響應結構解析錯誤 (TypeError)

**錯誤訊息**:
```
TypeError: documentFormats.map is not a function
```

**影響頁面**:
- `/admin/field-mapping-configs`

**根因**: `/api/v1/formats` 返回結構為 `{ data: { formats: [...], pagination: {...} } }`，但 hooks 只取 `data.data`（物件），應取 `data.data?.formats`（陣列）

---

## 修復方案

### 修改文件

| 文件 | 修改內容 |
|------|----------|
| `src/hooks/use-field-mapping-configs.ts` | 修正 API 路徑和響應解析 |
| `src/hooks/use-prompt-configs.ts` | 修正 API 路徑和響應解析 |

### 修改詳情

#### 1. useCompaniesForFieldMapping / useCompaniesForPromptConfig

```typescript
// 修改前
const res = await fetch('/api/v1/companies?limit=100&sortBy=name');

// 修改後
const res = await fetch('/api/companies?limit=100&sortBy=name');
```

#### 2. useDocumentFormatsForFieldMapping / useDocumentFormatsForPromptConfig

```typescript
// 修改前
const res = await fetch(`/api/v1/document-formats?${params}`);
const data = await res.json();
return data.data || [];

// 修改後
const res = await fetch(`/api/v1/formats?${params}`);
const data = await res.json();
// API 返回 { data: { formats: [...], pagination: {...} } }
return data.data?.formats || [];
```

---

## Git Commits

| Commit Hash | 說明 |
|-------------|------|
| `0f4a6e1` | fix(hooks): correct companies API path from /api/v1/companies to /api/companies |
| `31e0d40` | fix(hooks): correct document-formats API path to /api/v1/formats |
| `7ced2e0` | fix(hooks): extract formats array from API response structure |

---

## API 路徑參考

| 資源 | 正確路徑 | 備註 |
|------|----------|------|
| Companies | `/api/companies` | 無 v1 前綴 |
| Formats | `/api/v1/formats` | 有 v1 前綴 |
| Field Mapping Configs | `/api/v1/field-mapping-configs` | 有 v1 前綴 |
| Prompt Configs | `/api/v1/prompt-configs` | 有 v1 前綴 |

---

## 驗證步驟

1. 開啟 `/admin/field-mapping-configs` 頁面
2. 確認無 404 錯誤，下拉選單正常載入公司和格式列表
3. 開啟 `/admin/prompt-configs/[id]` 編輯頁面
4. 確認無 404 錯誤，下拉選單正常載入

---

## 經驗教訓

1. **API 路徑一致性**: 項目中部分 API 有 `/v1/` 前綴，部分沒有，容易混淆
2. **API 響應結構**: 不同 API 的響應結構可能不同，需要仔細對照
3. **建議**: 考慮統一所有 API 路徑前綴規範，或建立 API 路徑常數檔案

---

**維護者**: Claude Code
**最後更新**: 2026-01-07
