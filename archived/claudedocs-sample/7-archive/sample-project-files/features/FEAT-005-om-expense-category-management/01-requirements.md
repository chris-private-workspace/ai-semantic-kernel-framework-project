# FEAT-005: OM Expense Category Management - OM 費用類別管理

> **建立日期**: 2025-12-01
> **狀態**: 🚧 開發中
> **優先級**: High

## 1. 功能概述

### 1.1 背景
目前 OMExpense（O&M 費用）的 `category` 欄位是自由文字 String 類型，缺乏標準化管理：
- 用戶可以輸入任意文字作為類別
- 無法統一管理和維護費用類別
- 難以進行類別統計和分析
- 輸入不一致導致數據混亂

### 1.2 目標
建立獨立的 OMExpenseCategory 管理系統：
- 創建新的 `OMExpenseCategory` 數據模型
- 提供費用類別的 CRUD 管理介面
- 將 OMExpense 的 `category` 從 String 轉換為外鍵關係
- 確保數據一致性和可管理性

## 2. 功能需求

### 2.1 用戶故事
- **作為系統管理員**，我希望能夠管理 O&M 費用類別，以便統一分類標準
- **作為財務人員**，我希望在建立 O&M 費用時可以從預定義類別中選擇，以確保數據一致性
- **作為報表分析人員**，我希望費用類別是標準化的，以便進行準確的統計分析

### 2.2 功能列表

#### 2.2.1 OMExpenseCategory 管理
| 功能 | 描述 |
|------|------|
| 列表查看 | 顯示所有費用類別，支援排序和過濾 |
| 新增類別 | 建立新的費用類別（代碼、名稱、描述） |
| 編輯類別 | 修改現有類別資訊 |
| 啟用/停用 | 控制類別是否可用 |
| 刪除類別 | 刪除無關聯的類別 |

#### 2.2.2 預設類別（Seed Data）
| 代碼 | 名稱（中文） | 名稱（英文） |
|------|-------------|-------------|
| MAINT | 維護費 | Maintenance |
| LICENSE | 軟體授權費 | Software License |
| COMM | 通訊費 | Communication |
| HOSTING | 託管費 | Hosting |
| SUPPORT | 技術支援費 | Technical Support |
| OTHER | 其他 | Other |

#### 2.2.3 OMExpense 整合
- OMExpense 建立/編輯時顯示類別下拉選單
- 只顯示已啟用的類別
- 類別為必填欄位

## 3. 驗收標準

### 3.1 功能驗收
- [ ] 可以新增費用類別（代碼、名稱、描述）
- [ ] 可以編輯費用類別
- [ ] 可以啟用/停用費用類別
- [ ] 可以刪除無關聯的類別
- [ ] 有關聯的類別不能刪除（顯示警告）
- [ ] OMExpense 表單顯示類別下拉選單
- [ ] 預設類別已透過 Seed 建立

### 3.2 技術驗收
- [ ] OMExpenseCategory Prisma Model 已建立
- [ ] omExpenseCategory API Router 已實現
- [ ] TypeScript 無錯誤
- [ ] ESLint 無新增錯誤
- [ ] i18n 翻譯完整（zh-TW + en）

### 3.3 用戶體驗
- [ ] 頁面載入有 Loading 狀態
- [ ] 操作失敗有明確錯誤提示
- [ ] 側邊欄導航項目已添加
- [ ] 響應式設計（桌面/手機）

## 4. 相關文檔
- [02-technical-design.md](./02-technical-design.md) - 技術設計
- [03-implementation-plan.md](./03-implementation-plan.md) - 實施計劃
- [04-progress.md](./04-progress.md) - 進度追蹤
- [packages/db/prisma/schema.prisma](../../../../../packages/db/prisma/schema.prisma) - 數據模型
