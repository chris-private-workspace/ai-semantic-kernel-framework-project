# FEAT-008: OM Expense 資料導入功能

> **建立日期**: 2025-12-09
> **最後更新**: 2025-12-09
> **狀態**: 📋 設計中
> **優先級**: High
> **前置依賴**: FEAT-007 (OM Expense 表頭-明細架構重構)

---

## 1. 功能概述

### 1.1 背景

目前公司使用 Excel 工作表來管理 OM (Operation Maintenance) 費用。為了將現有資料遷移到新系統，需要提供資料導入功能，讓用戶可以從準備好的 Excel 檔案批量導入 OM Expense 資料。

### 1.2 目標

- 提供 **獨立的 Data Import 頁面** 讓用戶上傳和導入資料
- 提供 tRPC API endpoint 支援批量導入 OM Expense 資料
- 自動建立缺失的 Operating Company 記錄
- 自動建立缺失的 OM Expense Header 記錄
- **全部 Rollback 策略**：任何失敗就全部回滾，確保資料一致性
- 提供導入結果報告
- **新增 lastFYActualExpense 欄位**：支援上年度實際支出數據導入和編輯

### 1.3 資料來源

準備好的 Excel 檔案：`docs/For Data Import/OM Expense and Detail import data - v2.xlsx`

資料統計：
- 總資料行數：500 行
- 唯一 OM Expense Headers：69 個
- 唯一 OM Expense Items：160 個（header + item 組合）
- Expense Categories：9 個
- Operating Companies：42 個

---

## 2. 功能需求

### 2.1 用戶故事

**作為** 系統管理員
**我希望** 能夠透過專用的導入頁面批量導入現有 Excel 資料到系統
**以便** 快速遷移舊有 OM Expense 資料，開始使用新系統管理

**作為** 使用者
**我希望** 能夠在 OM Expense Item 編輯時輸入上年度實際支出
**以便** 在 Summary 頁面查看年度比較數據

### 2.2 功能列表

#### 2.2.1 資料模型變更

1. **新增 OMExpenseItem 欄位**
   - `lastFYActualExpense`: Float? - 上年度實際支出（可為空）
   - 用途：在 Summary 頁面顯示年度比較數據
   - 輸入方式：手動輸入或批量導入

#### 2.2.2 前端頁面

1. **獨立 Data Import 頁面** (`/data-import`)
   - 檔案上傳區域（拖放或選擇 JSON 檔案）
   - 導入按鈕
   - 處理中狀態顯示（Loading + 進度文字）
   - 導入結果顯示區域

2. **導入結果顯示**
   - 成功：顯示統計摘要（建立的 OpCo、Header、Item 數量）
   - 失敗：顯示錯誤訊息，說明失敗原因
   - 所有資料已 Rollback 的提示

3. **OM Expense Item 編輯表單更新**
   - 新增 "Last year actual expense" 輸入欄位
   - 欄位類型：數字輸入框（可為空）
   - 位置：放在 Budget Amount 欄位附近

#### 2.2.3 後端 API

1. **批量導入 OM Expense 資料** (`importOMExpenseData`)
   - 接收 JSON 格式的導入資料陣列
   - 每筆資料包含 Header 資訊和 Item 資訊
   - 自動處理 Operating Company 建立
   - 自動處理 OM Expense Header 建立
   - 建立 OM Expense Item 記錄（含 lastFYActualExpense）
   - **建立 12 個月度記錄**（actualAmount = 0）

2. **唯一性檢查**
   - 規則：`Header 名稱 + Item 名稱 + Charge to OpCo`
   - 如果發現重複，整體拒絕導入（全部 Rollback）

3. **自動建立缺失記錄**
   - Operating Company：如果 OpCo 不存在，自動建立
   - OM Expense Header：如果 Header 不存在，自動建立

4. **更新 OM Expense Item API**
   - `addItem`: 支援 lastFYActualExpense 欄位
   - `updateItem`: 支援 lastFYActualExpense 欄位

### 2.3 資料欄位映射

| Excel 欄位 | 系統欄位 | 說明 |
|-----------|---------|------|
| OM Expense Header | OMExpense.name | Header 名稱 |
| OM Expense Description | OMExpense.description | Header 描述 |
| Expense Category | OMExpense.category + ExpenseCategory | 類別 |
| OM Expense Item Details | OMExpenseItem.name | Item 名稱 |
| OM Expense Item Details Description | OMExpenseItem.description | Item 描述 |
| FY26 OM Expense Budget Amount (USD) | OMExpenseItem.budgetAmount | 預算金額 |
| Charge to OpCos | OMExpenseItem.opCoId | 關聯 Operating Company |
| OM Expense End Date | OMExpenseItem.endDate | 結束日期 (可空) |
| **FY25 Actual OM Expense Charges** | **OMExpenseItem.lastFYActualExpense** | **上年度實際支出 (新增)** |

**固定值：**
- financialYear：2026 (FY26)
- OMExpenseMonthly.actualAmount：0（12 個月度記錄）

**不導入的欄位：**
- FY26 OM Expense Budget Amount (HKD)
- Increment (%) Compare to FY25
- ~~FY25 Actual OM Expense Charges~~ → 已改為導入
- FY26 Actual OM Expense Charges

### 2.4 業務規則

1. **Financial Year**：所有導入資料的財務年度固定為 2026 (FY26)
2. **Rollback 策略**：**全部 Rollback** - 任何失敗就全部回滾，確保資料一致性
3. **空預算金額**：如果 Budget Amount 為空，設為 0
4. **OpCo 處理**：保留原始名稱（含括號標記），不進行規範化
5. **月度記錄**：每個 Item 自動建立 12 個月度記錄，actualAmount 初始為 0
6. **上年度實際支出**：lastFYActualExpense 可為空，用於 Summary 比較分析

---

## 3. UI/UX 設計

### 3.1 Data Import 頁面結構

```
/data-import
├── 頁面標題：資料導入 (Data Import)
├── 導入說明卡片
│   ├── 支援的檔案格式：JSON
│   ├── 資料格式說明連結
│   └── 範例檔案下載
├── 檔案上傳區域
│   ├── 拖放區域
│   ├── 選擇檔案按鈕
│   └── 已選檔案名稱顯示
├── 導入設定
│   └── Financial Year 選擇（預設 2026）
├── 導入按鈕
└── 結果顯示區域
    ├── 處理中狀態
    ├── 成功結果
    └── 失敗結果
```

### 3.2 OM Expense Item 編輯表單更新

```
OM Expense Item 表單
├── Item Name *
├── Description
├── Budget Amount *
├── **Last year actual expense** (新增)  ← Label
├── OpCo *
├── Start Date
├── End Date *
└── Currency
```

### 3.3 處理狀態

| 狀態 | 顯示內容 |
|------|---------|
| 初始 | 顯示上傳區域和說明 |
| 處理中 | Loading 動畫 + 「正在處理 X 筆資料，請稍候...」 |
| 成功 | ✅ 導入成功摘要（建立的 OpCo、Header、Item 數量） |
| 失敗 | ❌ 導入失敗，顯示錯誤訊息，「所有資料已回滾，請修正後重試」 |

### 3.4 導入結果顯示

**成功時：**
```
✅ 導入成功！

統計摘要：
- 新建 Operating Companies: 42 個
- 新建 OM Expense Headers: 69 個
- 新建 OM Expense Items: 500 個

詳細資訊：
- 建立的 OpCos: RHK, RIT, RAP, ...
- 建立的 Headers: Anaplan, ServiceNow, ...
```

**失敗時：**
```
❌ 導入失敗

錯誤原因：發現重複資料
- Header: "Anaplan"
- Item: "Model Builder"
- OpCo: "RHK"

⚠️ 所有資料已回滾，無任何變更。
請修正資料後重試。
```

---

## 4. 驗收標準

### 4.1 功能驗收

- [ ] Data Import 頁面可正常訪問
- [ ] 檔案上傳功能正常（支援 JSON 格式）
- [ ] API 能夠成功接收並解析導入資料
- [ ] 正確建立缺失的 Operating Company
- [ ] 正確建立缺失的 OM Expense Header
- [ ] 正確建立 OM Expense Item 記錄（含 lastFYActualExpense）
- [ ] 正確建立 12 個 Monthly 記錄（actualAmount = 0）
- [ ] 唯一性檢查正常運作，發現重複時全部 Rollback
- [ ] 導入結果報告顯示正確的統計資訊
- [ ] OM Expense Item 編輯表單顯示 "Last year actual expense" 欄位
- [ ] lastFYActualExpense 可正確新增和編輯

### 4.2 技術驗收

- [ ] Prisma Schema 新增 lastFYActualExpense 欄位
- [ ] Migration 成功執行
- [ ] API 使用 Zod 進行輸入驗證
- [ ] 使用 Prisma Transaction 確保資料一致性（全部成功或全部回滾）
- [ ] 錯誤訊息清晰易懂
- [ ] TypeScript 類型安全
- [ ] 前端頁面響應式設計

### 4.3 用戶體驗

- [ ] 處理中狀態有明確的視覺反饋
- [ ] 錯誤訊息清晰說明失敗原因
- [ ] 成功訊息顯示詳細的統計摘要
- [ ] 支援大量資料導入（500+ 筆）
- [ ] "Last year actual expense" 欄位標籤清晰易懂

---

## 5. 相關文檔

- FEAT-007: OM Expense 表頭-明細架構重構
- `packages/db/prisma/schema.prisma` - 資料模型
- `packages/api/src/routers/omExpense.ts` - OM Expense API
- `packages/api/src/routers/operatingCompany.ts` - Operating Company API
- `docs/import-data-analysis.json` - 導入資料分析結果
