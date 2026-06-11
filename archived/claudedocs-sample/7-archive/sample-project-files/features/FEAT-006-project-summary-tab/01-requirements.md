# FEAT-006: Project Summary Tab

> **建立日期**: 2025-12-05
> **狀態**: 📋 設計中
> **優先級**: High
> **預計工時**: 3-4 天

---

## 1. 功能概述

### 1.1 背景
目前 OM Summary 頁面只顯示 O&M 費用的匯總數據。用戶希望在同一頁面中增加 Project Summary Tab，以便在同一介面上快速切換查看 O&M 費用和專案預算的彙總資訊。

### 1.2 目標
- 在 OM Summary 頁面增加 Tab 切換功能
- 新增 Project Summary Tab 顯示專案彙總數據
- 擴展 Project 數據模型以支援新欄位
- 提供類似 OM Summary 的篩選和分組功能

### 1.3 設計稿
![Project Summary Page Design](../../../../Downloads/it-budget-project-management-portal-project-summary-screen-1.png)

---

## 2. 功能需求

### 2.1 用戶故事

**作為** 預算管理者
**我希望** 能夠在同一頁面上查看專案預算匯總
**以便** 快速了解各 OpCo、Budget Category 下的專案分佈和預算狀況

### 2.2 功能列表

#### 2.2.1 Tab 切換功能
- [ ] 在 OM Summary 頁面頂部增加 Tab 組件
- [ ] Tab 1: OM Summary（現有功能）
- [ ] Tab 2: Project Summary（新功能）
- [ ] Tab 切換時保持篩選器狀態（如 FY）

#### 2.2.2 Project Summary 篩選器
- [ ] FY 選擇（單選）：FY2025, FY2026, FY2027 等
- [ ] Budget Category 選擇（多選）

#### 2.2.3 Category 匯總表格
- [ ] 按 Budget Category 分組顯示
- [ ] 每個 Category 顯示預算總額和專案數量
- [ ] 底部顯示 Grand Total

#### 2.2.4 Project 明細表格
- [ ] 按 OpCo 分組
- [ ] 每個 OpCo 下按 Category 分組
- [ ] 顯示每個專案的詳細信息
- [ ] 每組顯示小計（Sub Total）

#### 2.2.5 Project 欄位擴展
- [ ] 新增 `projectCategory` - 專案類別
- [ ] 新增 `projectType` - 專案或預算 (Project/Budget)
- [ ] 新增 `expenseType` - 費用類型 (Expense/Capital/Collection)
- [ ] 新增 `chargeBackToOpCo` - 是否向 OpCo 收費
- [ ] 新增 `chargeOutOpCos` - 向哪些 OpCo 收費（多選）
- [ ] 新增 `chargeOutMethod` - 如何向 OpCo 收費
- [ ] 新增 `probability` - 機率 (High/Medium/Low)
- [ ] 新增 `team` - 團隊
- [ ] 新增 `personInCharge` - 負責人

---

## 3. 欄位規格

### 3.1 需要新增的 Project 欄位

| 欄位名稱 | 類型 | 必填 | 預設值 | 說明 |
|----------|------|------|--------|------|
| `projectCategory` | String | 否 | null | 專案類別（如 Data Lines, Hardware, Software） |
| `projectType` | String | 是 | "Project" | "Project" 或 "Budget" |
| `expenseType` | String | 是 | "Expense" | "Expense", "Capital", "Collection" |
| `chargeBackToOpCo` | Boolean | 是 | false | 是否需要向 OpCo 收費 |
| `chargeOutMethod` | String | 否 | null | 收費方式說明（自由文字） |
| `probability` | String | 是 | "Medium" | "High", "Medium", "Low" |
| `team` | String | 否 | null | 負責團隊 |
| `personInCharge` | String | 否 | null | 負責人（PIC） |

### 3.2 多對多關係：Project ↔ OperatingCompany

```
ProjectChargeOutOpCo (中間表)
├── id          String @id @default(uuid())
├── projectId   String
├── opCoId      String
├── project     Project @relation(...)
└── opCo        OperatingCompany @relation(...)
```

---

## 4. 驗收標準

### 4.1 功能驗收
- [ ] Tab 切換正常工作，狀態保持
- [ ] FY 和 Budget Category 篩選器功能正常
- [ ] Category 匯總表格數據正確
- [ ] Project 明細表格按 OpCo → Category 正確分組
- [ ] 新欄位可在 Project 表單中編輯
- [ ] API 返回正確的匯總數據

### 4.2 技術驗收
- [ ] Prisma Schema 正確更新
- [ ] tRPC API 正確實現
- [ ] TypeScript 類型完整
- [ ] 無 ESLint 錯誤

### 4.3 用戶體驗
- [ ] 響應式設計支援 mobile/tablet/desktop
- [ ] 載入狀態正確顯示
- [ ] 錯誤狀態正確處理
- [ ] I18N 支援（繁中/英文）

---

## 5. 相關文檔

### 5.1 參考文檔
- [FEAT-003: OM Summary Page](../FEAT-003-om-summary-page/)
- [OM Summary Page 實現](../../../../apps/web/src/app/[locale]/om-summary/page.tsx)
- [Project Router](../../../../packages/api/src/routers/project.ts)

### 5.2 設計參考
- 設計稿：`it-budget-project-management-portal-project-summary-screen-1.png`

---

**最後更新**: 2025-12-05
**作者**: AI Assistant
