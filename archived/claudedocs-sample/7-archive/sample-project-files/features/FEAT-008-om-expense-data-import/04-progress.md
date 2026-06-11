# FEAT-008: OM Expense 資料導入 - 開發進度

> **建立日期**: 2025-12-09
> **最後更新**: 2025-12-11
> **狀態**: ✅ v1.3 開發完成 (含 CHANGE-010, CHANGE-011 增強)

---

## 📊 整體進度

### v1.0 基本功能 (已完成)
- [x] Phase 0: 規劃準備
- [x] Phase 1: 準備工作 (Schema Migration)
- [x] Phase 2: 後端 API 開發 (importData procedure)
- [x] Phase 3: 前端頁面開發 (/data-import + i18n)
- [x] Phase 4: 資料準備 (Excel → JSON 轉換)
- [x] Phase 5: 測試驗證 (Dev server 測試通過)

### v1.1 改進功能 (已完成)
- [x] Phase 6: 補充英文翻譯 (60+ 個翻譯鍵)
- [x] Phase 7: 預覽確認機制 (詳細資料預覽 + 確認流程)

### v1.2 重複檢測修復 (已完成)
- [x] Phase 8: 後端重複檢測邏輯修正 (6 欄位完整唯一鍵)
- [x] Phase 9: 前端註解同步更新
- [x] Phase 10: Transaction 超時修復 (5 秒 → 5 分鐘)

### v1.3 CHANGE-010/011 增強 (已完成)
- [x] Phase 11: 日期驗證增強 (CHANGE-010)
- [x] Phase 12: isOngoing 欄位支援 (CHANGE-011)
- [x] Phase 13: lastFYActualExpense 欄位映射修正
- [x] Phase 14: Date 對象格式解析支援

---

## 📝 開發日誌

### 2025-12-09 (v1.0 完成)

**完成項目:**

#### Phase 1: Schema Migration ✅
- 修改 `packages/db/prisma/schema.prisma`
- 新增 `OMExpenseItem.lastFYActualExpense` 欄位 (Float?)
- 執行 `pnpm db:migrate` 成功
- 執行 `pnpm db:generate` 成功

#### Phase 2: 後端 API 開發 ✅
- 在 `packages/api/src/routers/omExpense.ts` 新增 `importData` procedure
- 實作完整功能：
  - Zod Schema 驗證
  - OpCo 自動建立邏輯
  - Header 自動建立邏輯
  - Item + 12 個 Monthly 記錄建立
  - 唯一性檢查 (Header + Item + OpCo)
  - Prisma Transaction 全部 Rollback 策略
  - 詳細統計資訊回傳

#### Phase 3: 前端頁面開發 ✅
- 建立 `/data-import` 頁面
- 支援直接 Excel 上傳 (使用 xlsx/SheetJS 函式庫)
- 支援 JSON 格式輸入
- 拖放上傳功能
- 客戶端 Excel 解析和驗證
- 重複資料自動檢測和移除
- i18n 翻譯支援 (en.json + zh-TW.json)
- Sidebar 導航項目新增

#### Phase 4: 資料準備 ✅
- 建立 `scripts/convert-excel-to-import-json.py` 腳本 (備用)
- 支援直接 Excel 上傳後改為客戶端解析

#### Phase 5: 測試驗證 ✅
- Dev server 啟動成功 (port 3001)
- 頁面編譯成功，無 TypeScript 錯誤
- HTTP 200 響應正常

**TypeScript 錯誤修復:**
- Line 169: `date.toISOString().split('T')[0]` 返回 undefined 問題
- Line 204: `workbook.SheetNames[0]` 可能 undefined 問題
- Line 212: `workbook.Sheets[sheetName]` 可能 undefined 問題

---

### 2025-12-09 (v1.1 規劃)

**發現的問題:**

1. **英文翻譯不完整**: 頁面中有 50+ 處硬編碼中文，在 `/en/data-import` 頁面顯示中文
2. **預覽確認機制不足**: 用戶希望上傳後先顯示詳細預覽，確認後再執行導入

**改進需求 (Phase 6-7):**
- 詳見 `05-enhancements.md`

### 2025-12-09 (v1.1 完成)

**Phase 6: 補充英文翻譯 ✅**
- 新增 60+ 個翻譯鍵到 `en.json` 和 `zh-TW.json`
- 涵蓋：tabs, form, excel upload, actions, errors, messages, preview, statistics, excelFormat, notes
- 執行 `pnpm validate:i18n` 驗證通過 (2249 個鍵結構一致)

**Phase 7: 預覽確認機制 ✅**
- 重構 `page.tsx` 實作三步驟流程 (upload → preview → result)
- 新增資料結構：`ErrorRow`, `DuplicateRow`, `HeaderPreview`, `ItemPreview`, `ParseResult`
- 統計摘要顯示 8 個指標：totalRows, validItems, skippedRows, errorRows, duplicateRows, uniqueHeaders, uniqueOpCos, uniqueCategories
- OM Expense Headers 預覽表格（含展開/收合功能）
- OM Expense Items 詳細預覽表格（支援載入更多）
- 有問題數據行表格（行號、問題欄位、原因、原始值）
- 重複數據行表格（行號、重複的組合）
- 「確認導入」按鈕顯示導入筆數
- Dev server 編譯成功，頁面正常運作

---

### 2025-12-10 (v1.2 完成)

**問題發現:**

1. **Excel 行數顯示**: 388 行 vs 387 顯示 → 正常行為（排除標題行）
2. **部分記錄導入後消失**: Excel Row 34 和 Row 35 有相同的 Header + ItemName + OpCo，但有不同的 Description 和 Budget
   - 前端使用 6 欄位唯一鍵：`headerName|itemName|itemDescription|category|opCoName|budgetAmount`
   - 後端只使用 3 欄位唯一鍵：`header + itemName + opCo`
   - 導致前端 Preview 通過的記錄在後端被判定為重複而跳過

**Phase 8: 後端重複檢測修正 ✅**
- 修改 `packages/api/src/routers/omExpense.ts` 中的 `importData` procedure
- 將後端唯一性檢查從 3 欄位擴展為 6 欄位：
  1. headerName (via omExpenseId)
  2. itemName
  3. itemDescription
  4. category (via omExpenseId)
  5. opCoName (via opCoId)
  6. budgetAmount
- 新增 Prisma 查詢條件：`description` 和 `budgetAmount`

**Phase 9: 前端註解同步 ✅**
- 更新 `apps/web/src/app/[locale]/data-import/page.tsx` 中的重複檢測註解
- 明確記錄 6 欄位唯一鍵邏輯，確保前後端保持一致

**Phase 10: Transaction 超時修復 ✅**
- 問題：Prisma Transaction 預設超時 5 秒，導入 387 筆資料時超時
- 錯誤訊息：`Transaction already closed: A query cannot be executed on an expired transaction`
- 修復：增加 transaction 超時設定
  ```typescript
  ctx.prisma.$transaction(async (tx) => { ... }, {
    maxWait: 10000,   // 10 秒等待連接
    timeout: 300000,  // 5 分鐘執行超時
  });
  ```

**驗證結果:**
- ✅ TypeScript 編譯通過
- ✅ ESLint 檢查通過 (omExpense.ts 無錯誤)
- ✅ i18n 驗證通過 (2275 個鍵)

---

## 🎯 設計決策摘要

| 項目 | 決策 | 說明 |
|------|------|------|
| UI 方案 | 獨立 Data Import 頁面 | `/data-import` 路由 |
| Rollback 策略 | 全部 Rollback | 任何失敗就全部回滾，確保資料一致性 |
| 月度記錄 | 導入時建立 | 每個 Item 建立 12 個 Monthly 記錄，actualAmount = 0 |
| 唯一性檢查 | **6 欄位完整唯一鍵** | Header + Item + Description + Category + OpCo + Budget (v1.2 更新) |
| OpCo 處理 | 保留原始名稱 | 不進行規範化，保留括號標記 |
| 新增欄位 | lastFYActualExpense | Float? 類型，用於 Summary 年度比較 |
| 表單更新 | Last year actual expense | 在 OM Expense Item 表單中新增輸入欄位 |
| **Excel 上傳** | **客戶端解析** | **使用 xlsx/SheetJS 函式庫在瀏覽器端解析 Excel** |

---

## 🐛 問題追蹤

| 問題 | 狀態 | 解決方案 |
|------|------|----------|
| TypeScript 錯誤 (3 處) | ✅ 已修復 | 加入 null check 和 undefined 處理 |
| 英文翻譯不完整 | ✅ 已修復 | 新增 60+ 個翻譯鍵 (Phase 6) |
| 預覽確認機制不足 | ✅ 已修復 | 實作三步驟流程 + 詳細預覽 (Phase 7) |
| 部分記錄導入後消失 | ✅ 已修復 | 後端重複檢測改用 6 欄位唯一鍵 (Phase 8-9) |
| Transaction 超時錯誤 | ✅ 已修復 | 增加超時至 5 分鐘 (Phase 10) |

---

## ✅ 測試結果

### Phase 5 測試 (v1.0) ✅

- [x] Dev server 啟動成功
- [x] 頁面編譯無錯誤
- [x] HTTP 200 響應正常
- [x] Excel 上傳功能可用
- [x] JSON 輸入功能可用

### v1.1 驗證 ✅

- [x] 英文介面測試 (所有翻譯鍵正確顯示)
- [x] 預覽確認流程測試 (三步驟 UI 運作正常)
- [x] i18n 驗證通過 (`pnpm validate:i18n`)

### v1.2 驗證 ✅

- [x] TypeScript 編譯通過
- [x] ESLint 檢查通過 (omExpense.ts 無錯誤)
- [x] i18n 驗證通過 (2275 個鍵)
- [x] 6 欄位唯一鍵邏輯前後端一致

### 待測試 (實際資料)

- [ ] 使用 v3.xlsx 測試 Row 34/35 是否都成功導入
- [ ] 完整導入測試（387 筆 → 應全部導入）
- [ ] 重複導入測試（確認 Rollback）

---

## 📈 統計資訊

### 導入資料統計

| 項目 | 數量 |
|------|------|
| 總資料行數 (含標題) | 388 |
| 資料行數 (不含標題) | 387 |
| 唯一 Items (去重後) | ~352 |
| 唯一 Headers | ~69 |
| Categories | 9 |
| Operating Companies | ~42 |
| 預計 Monthly 記錄 | ~4,224 (352 × 12) |

> **注意**: v1.2 後使用 6 欄位唯一鍵，實際唯一數量可能略有變動

### 9 個 Expense Categories

1. Application System
2. Cloud
3. Computer Room Maintenance
4. Datalines
5. Hardware
6. IT Security
7. Network
8. Others
9. Software

---

## 📁 文件變更清單

### 新增文件

| 文件 | 狀態 | 說明 |
|------|------|------|
| `apps/web/src/app/[locale]/data-import/page.tsx` | ✅ 已建立 | Data Import 頁面 |
| `scripts/convert-excel-to-import-json.py` | ✅ 已建立 | Excel 轉 JSON 腳本 (備用) |

### 修改文件

| 文件 | 狀態 | 說明 |
|------|------|------|
| `packages/db/prisma/schema.prisma` | ✅ 已修改 | OMExpenseItem 新增 lastFYActualExpense 欄位 |
| `packages/api/src/routers/omExpense.ts` | ✅ 已修改 | 新增 `importData` procedure + v1.2 6 欄位唯一鍵修正 |
| `apps/web/src/components/layout/Sidebar.tsx` | ✅ 已修改 | 新增 Data Import 導航 |
| `apps/web/src/messages/en.json` | ✅ 已修改 | 新增 dataImport 翻譯 (部分) |
| `apps/web/src/messages/zh-TW.json` | ✅ 已修改 | 新增 dataImport 翻譯 (部分) |
| `apps/web/package.json` | ✅ 已修改 | 新增 xlsx 依賴 |
| `apps/web/src/app/[locale]/data-import/page.tsx` | ✅ 已修改 | v1.2 更新重複檢測註解 |

---

## 🔗 相關文檔

- [01-requirements.md](./01-requirements.md) - 需求規格
- [02-technical-design.md](./02-technical-design.md) - 技術設計
- [03-implementation-plan.md](./03-implementation-plan.md) - 實施計劃
- [05-enhancements.md](./05-enhancements.md) - v1.1 改進需求 (NEW)
- [docs/import-data-analysis.json](../../../../docs/import-data-analysis.json) - 導入資料分析結果
- [CHANGE-010](../../../4-changes/feature-changes/CHANGE-010-data-import-enhancements.md) - Data Import 日期驗證增強
- [CHANGE-011](../../../4-changes/feature-changes/CHANGE-011-om-expense-item-ongoing-field.md) - isOngoing 欄位支援

---

## 📝 v1.3 開發日誌 (2025-12-11)

### CHANGE-010: Data Import 增強
**完成項目:**
- 日期驗證邏輯增強
- lastFYActualExpense 默認值設定
- currencyId 默認為 USD

**補充修正:**
- 修正 EXCEL_COLUMN_MAP 中 lastFYActualExpense 欄位映射
  - 錯誤: index 13 (Column N)
  - 正確: index 10 (Column K: "FY25 Actual OM Expense Charges")

### CHANGE-011: isOngoing 欄位支援
**完成項目:**
- 新增 OMExpenseItem.isOngoing 欄位
- 前端 Checkbox UI 和條件式驗證
- Data import 邏輯: 空 endDate → isOngoing=true
- updateItem API 支援 isOngoing 處理

**測試發現並修復的問題:**
1. isOngoing 保存無效 → 修復 updateItem procedure
2. Date 對象格式解析錯誤 → 新增 instanceof Date 處理
3. isOngoing 未傳遞到 API → 新增 mutation payload 欄位
4. lastFYActualExpense 欄位映射錯誤 → 修正 index

### Git Commits (v1.3)
| Commit | 描述 |
|--------|------|
| `11cb3c4` | feat(data-import): CHANGE-010 Data Import 增強 |
| `9ff6d8c` | feat(om-expense): CHANGE-011 新增 isOngoing 持續進行中欄位 |
| `b349192` | fix(om-expense): CHANGE-011 修復 isOngoing 保存和清空 endDate |
| `9506345` | fix(data-import): 修復 Date 對象格式的日期解析 |
| `2fec107` | fix(data-import): CHANGE-011 修復 isOngoing 和 lastFYActualExpense 傳遞 |
| `c401f51` | fix(data-import): 修正 EXCEL_COLUMN_MAP lastFYActualExpense 欄位映射 |
