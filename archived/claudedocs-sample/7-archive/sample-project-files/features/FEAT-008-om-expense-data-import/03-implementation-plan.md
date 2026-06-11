# FEAT-008: 實施計劃

> **建立日期**: 2025-12-09
> **最後更新**: 2025-12-09
> **預估工時**: 6-8 小時

---

## 1. 開發階段

### Phase 1: 準備工作 (1 小時)

- [ ] 確認現有 ExpenseCategory 資料（9 個類別）
- [ ] 確認現有 OperatingCompany 資料
- [ ] 準備導入資料 JSON 檔案（從 Excel 轉換）
- [ ] **Schema Migration**: 新增 OMExpenseItem.lastFYActualExpense 欄位
  - [ ] 修改 packages/db/prisma/schema.prisma
  - [ ] 執行 `pnpm db:migrate`
  - [ ] 執行 `pnpm db:generate`

### Phase 2: 後端 API 開發 (2-3 小時)

- [ ] 設計 Zod Schema（importOMExpenseDataSchema）
- [ ] 實作 `importData` procedure
  - [ ] OpCo 處理邏輯（查詢現有 + 建立缺失）
  - [ ] Header 處理邏輯（查詢現有 + 建立缺失）
  - [ ] Item 建立邏輯（含唯一性檢查 + lastFYActualExpense）
  - [ ] Monthly 記錄建立（12 個月）
  - [ ] Prisma Transaction（全部 Rollback 策略）
- [ ] 實作導入結果報告
- [ ] **更新現有 API**: `addItem`, `updateItem` 支援 lastFYActualExpense 欄位

### Phase 3: 前端頁面開發 (2-3 小時)

- [ ] 建立 `/data-import` 頁面
- [ ] 建立 `DataImportForm` 組件
  - [ ] 檔案上傳區域（拖放 + 選擇）
  - [ ] Financial Year 選擇
  - [ ] 導入按鈕
- [ ] 建立 `ImportResult` 組件
  - [ ] 成功結果顯示
  - [ ] 錯誤結果顯示
- [ ] 建立 `ImportProgress` 組件（Loading 狀態）
- [ ] 新增 i18n 翻譯（en.json, zh-TW.json）
- [ ] 修改 Sidebar 新增導航項目
- [ ] **更新 OMExpenseItemForm 組件**
  - [ ] 新增 "Last year actual expense" 輸入欄位
  - [ ] 欄位類型：數字輸入框（可為空）
  - [ ] 位置：放在 Budget Amount 欄位附近

### Phase 4: 資料準備 (1 小時)

- [ ] 建立 Excel → JSON 轉換腳本
- [ ] 驗證轉換後的 JSON 資料格式
- [ ] 確認 500 筆資料正確轉換

### Phase 5: 測試 (1-2 小時)

- [ ] 使用 Prisma Studio 確認現有資料
- [ ] 執行小批量測試（10 筆）
- [ ] 執行完整導入測試（500 筆）
- [ ] 測試重複導入（確認 Rollback）
- [ ] 驗證導入結果

---

## 2. 任務分解

### Task 2.1: 後端 - 新增 Zod Schema

```typescript
// 在 packages/api/src/routers/omExpense.ts 中新增
const importOMExpenseItemSchema = z.object({...});
const importOMExpenseDataSchema = z.object({...});
```

### Task 2.2: 後端 - 實作 importData Procedure

```typescript
importData: protectedProcedure
  .input(importOMExpenseDataSchema)
  .mutation(async ({ ctx, input }) => {
    // 使用 Prisma Transaction
    return await ctx.prisma.$transaction(async (tx) => {
      // Step 1-7 實作
    });
  }),
```

### Task 2.3: 前端 - 建立 Data Import 頁面

```
apps/web/src/app/[locale]/data-import/
├── page.tsx
└── components/
    ├── DataImportForm.tsx
    ├── ImportResult.tsx
    └── ImportProgress.tsx
```

### Task 2.4: 前端 - 新增 i18n 翻譯

```json
// en.json & zh-TW.json
{
  "dataImport": {
    "title": "Data Import / 資料導入",
    "description": "...",
    "uploadFile": "...",
    "importButton": "...",
    "success": "...",
    "error": "..."
  }
}
```

### Task 2.5: 前端 - 修改 Sidebar

```typescript
// 在 Sidebar.tsx 中新增導航項目
{
  href: '/data-import',
  icon: Upload,
  label: t('dataImport'),
}
```

### Task 2.6: 建立 Excel 轉 JSON 腳本

```python
# scripts/convert-import-excel-to-json.py
# 讀取 Excel，輸出 JSON 格式
```

---

## 3. 依賴關係

```
Phase 1 (準備) ──────────────────┐
                                 │
Phase 2 (後端 API) ←─────────────┤
                                 │
Phase 3 (前端頁面) ←─────────────┤ (Phase 2 完成後可開始)
                                 │
Phase 4 (資料準備) ←─────────────┤ (可與 Phase 2, 3 並行)
                                 │
Phase 5 (測試) ←─────────────────┘ (依賴 Phase 2, 3, 4)
```

---

## 4. 風險評估

### 風險 1: OpCo 命名不一致

**風險**: Excel 中有多種寫法（如 `R.IT` vs `RIT`）
**緩解**: 保留原始名稱，由用戶日後在 UI 中合併管理

### 風險 2: 大量資料導入效能

**風險**: 500 筆資料可能導致超時
**緩解**:
- 使用 Prisma Transaction 批次處理
- 設定適當的 Transaction timeout
- 優化查詢效能（使用 Map 緩存）

### 風險 3: Transaction Rollback 時間

**風險**: 全部 Rollback 策略可能導致長時間等待
**緩解**: 在處理前進行完整的驗證檢查，減少中途失敗機會

### 風險 4: 重複導入

**風險**: 用戶可能不小心重複導入
**緩解**:
- 唯一性檢查會觸發 Rollback
- 前端顯示清晰的錯誤訊息

---

## 5. 驗收測試

### Test Case 1: 小批量導入

```bash
# 導入 10 筆資料，驗證：
# - OpCo 正確建立
# - Header 正確建立
# - Item 正確建立
# - Monthly 記錄正確建立（每 Item 12 筆）
```

### Test Case 2: 完整導入

```bash
# 導入 500 筆資料，驗證：
# - 導入統計正確
# - 無重複記錄
# - 資料完整性
# - Monthly 記錄總數 = 500 * 12 = 6000 筆
```

### Test Case 3: 重複導入

```bash
# 再次執行導入，驗證：
# - 觸發唯一性錯誤
# - 顯示錯誤訊息（包含重複的 Header, Item, OpCo）
# - 所有資料 Rollback
# - 資料庫無任何變更
```

### Test Case 4: 前端測試

```bash
# 測試前端頁面：
# - 檔案上傳功能正常
# - 處理中狀態顯示正確
# - 成功結果顯示統計摘要
# - 錯誤結果顯示詳細資訊
```

---

## 6. 文件變更清單

### 新增文件

| 文件 | 說明 |
|------|------|
| `apps/web/src/app/[locale]/data-import/page.tsx` | Data Import 頁面 |
| `apps/web/src/app/[locale]/data-import/components/DataImportForm.tsx` | 上傳表單組件 |
| `apps/web/src/app/[locale]/data-import/components/ImportResult.tsx` | 結果顯示組件 |
| `apps/web/src/app/[locale]/data-import/components/ImportProgress.tsx` | 進度顯示組件 |
| `scripts/convert-import-excel-to-json.py` | Excel 轉 JSON 腳本 |

### 修改文件

| 文件 | 變更說明 |
|------|---------|
| `packages/db/prisma/schema.prisma` | OMExpenseItem 新增 lastFYActualExpense 欄位 |
| `packages/api/src/routers/omExpense.ts` | 新增 `importData` procedure，更新 addItem/updateItem |
| `apps/web/src/components/om-expense/OMExpenseItemForm.tsx` | 新增 "Last year actual expense" 輸入欄位 |
| `apps/web/src/components/layout/Sidebar.tsx` | 新增 Data Import 導航 |
| `apps/web/src/messages/en.json` | 新增 dataImport 翻譯，更新 omExpense 翻譯 |
| `apps/web/src/messages/zh-TW.json` | 新增 dataImport 翻譯，更新 omExpense 翻譯 |

---

## 7. 相關文檔

- `01-requirements.md` - 需求規格
- `02-technical-design.md` - 技術設計
- `04-progress.md` - 進度追蹤
