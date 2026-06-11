# FEAT-010: Project Data Import & Fiscal Year Enhancement

> **建立日期**: 2025-12-12
> **狀態**: 📋 設計中
> **優先級**: High

## 1. 功能概述

### 1.1 背景
目前 Project 模型缺少 Fiscal Year 欄位，無法記錄專案所屬的財務年度。此外，需要支援從 Excel 批量導入專案資料，以提高資料建立效率。

### 1.2 目標
1. **Part A**: 擴展 Project 模型，新增 Fiscal Year 和其他業務欄位
2. **Part B**: 建立專案資料導入功能，支援從 Excel 批量導入

## 2. 功能需求

### 2.1 Part A: Schema 擴展

#### 新增欄位
| 欄位 | 類型 | 說明 | 預設值 |
|------|------|------|--------|
| fiscalYear | Int? | 財務年度 | null |
| isCdoReviewRequired | Boolean | CDO 審核需求 | false |
| isManagerConfirmed | Boolean | Manager 已確認 | false |
| payForWhat | String? | 付款原因 | null |
| payToWhom | String? | 付款對象 | null |

#### UI 調整
- Project 列表頁：新增 Fiscal Year 過濾器
- Project 表單頁：新增上述 5 個欄位的輸入

### 2.2 Part B: 專案資料導入

#### Excel 模板結構 (19 欄位)
```
| 欄位 | 類型 | 說明 |
|------|------|------|
| No. | Int | 導入序號 (略過) |
| Fiscal Year | Int | 財務年度 |
| Project Category | String | 專案類別 |
| Project Name | String | 專案名稱 |
| Project Description | String | 專案描述 |
| Expense Type | String | 費用類型 |
| Bugget Category | String | 預算類別名稱 (查找) |
| Project Code | String | 專案編號 (唯一) |
| Global Flag | String | 全域標誌 |
| Probability | String | 機率 |
| Team | String | 團隊 |
| PIC | String | 負責人 |
| Currency | String | 貨幣代碼 (查找) |
| Is CDO review required | Y/N | CDO 審核需求 |
| Is Manager Confirmed | Y/N | Manager 確認 |
| Pay for what | String | 付款原因 |
| Pay to whom | String | 付款對象 |
| Total Amount (USD) | Float | 美元總金額 |
| Total Amount | Float | 原幣總金額 |
```

#### 導入功能需求
1. 上傳 Excel 檔案 (.xlsx)
2. 解析並驗證資料格式
3. 顯示預覽（新增 / 更新 / 跳過 / 錯誤）
4. 重複檢測（by projectCode）
5. 確認後執行導入
6. 顯示導入結果

## 3. 驗收標準

### 3.1 功能驗收 - Part A
- [ ] Project 模型新增 5 個欄位
- [ ] Project 列表頁可按 Fiscal Year 過濾
- [ ] Project 表單頁可編輯新欄位
- [ ] 現有專案資料不受影響

### 3.2 功能驗收 - Part B
- [ ] 可上傳 Excel 檔案
- [ ] 正確解析所有 19 欄位
- [ ] 預覽顯示準確
- [ ] 重複檢測功能正常
- [ ] 導入 100 筆測試資料成功
- [ ] 錯誤處理和訊息清晰

### 3.3 技術驗收
- [ ] TypeScript 編譯無錯誤
- [ ] ESLint 無新增錯誤
- [ ] i18n 翻譯完整 (en + zh-TW)
- [ ] Prisma migration 成功

### 3.4 用戶體驗
- [ ] 導入流程直觀（3 步驟：上傳 → 預覽 → 確認）
- [ ] 錯誤訊息有用且可理解
- [ ] 載入狀態有適當提示

## 4. 相關文檔

### 資料來源
- Excel 模板: `docs/For Data Import/project-data-import-template-v1.xlsx`
- 資料量: 100 筆專案

### 參考實現
- OM Expense Data Import: `apps/web/src/app/[locale]/data-import/`
- FEAT-008 規劃文檔: `claudedocs/1-planning/features/FEAT-008-om-expense-data-import/`

### 關聯文件
- `packages/db/prisma/schema.prisma` - Project 模型
- `packages/api/src/routers/project.ts` - Project API
- `apps/web/src/app/[locale]/projects/` - Project 頁面
