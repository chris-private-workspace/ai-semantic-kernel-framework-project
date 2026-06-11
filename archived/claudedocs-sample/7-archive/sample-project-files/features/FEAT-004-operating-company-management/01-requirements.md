# FEAT-004: Operating Company (OpCo) Management

> **建立日期**: 2025-11-29
> **狀態**: 🚧 開發中
> **優先級**: High

## 1. 功能概述

### 1.1 背景
營運公司 (Operating Company, OpCo) 是費用轉嫁和 O&M 費用管理的核心實體。目前系統中：
- 後端 API 已完成 (`packages/api/src/routers/operatingCompany.ts`)
- 前端管理頁面尚未建立
- 現有 OpCo 資料是手動透過資料庫建立

### 1.2 目標
建立完整的營運公司管理介面，支援：
- 營運公司列表查看（含過濾和搜尋）
- 新增營運公司
- 編輯營運公司資訊
- 啟用/停用營運公司
- 刪除營運公司（有關聯資料時禁止）

## 2. 功能需求

### 2.1 用戶故事
- 作為 **Supervisor**，我希望能查看所有營運公司列表，以了解系統中有哪些 OpCo
- 作為 **Supervisor**，我希望能新增營運公司，以便在費用轉嫁和 O&M 中使用
- 作為 **Supervisor**，我希望能編輯營運公司資訊，以修正錯誤或更新名稱
- 作為 **Supervisor**，我希望能停用不再使用的營運公司，而非刪除（保留歷史資料）
- 作為 **Admin**，我希望能刪除沒有關聯資料的營運公司

### 2.2 功能列表

| 功能 | 描述 | 權限 |
|------|------|------|
| 列表頁面 | 顯示所有營運公司，支援過濾啟用/停用狀態 | ProjectManager, Supervisor, Admin |
| 新增 | 建立新營運公司（驗證代碼唯一性） | Supervisor, Admin |
| 編輯 | 修改營運公司代碼、名稱、描述 | Supervisor, Admin |
| 切換狀態 | 啟用/停用營運公司 | Supervisor, Admin |
| 刪除 | 刪除無關聯資料的營運公司 | Supervisor, Admin |

### 2.3 資料模型

```prisma
model OperatingCompany {
  id          String   @id @default(uuid())
  code        String   @unique  // 如: "OpCo-HK", "OpCo-SG"
  name        String             // 如: "Hong Kong Operations"
  description String?
  isActive    Boolean  @default(true)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // 關聯
  chargeOuts       ChargeOut[]
  omExpenses       OMExpense[]
  omExpenseMonthly OMExpenseMonthly[]
}
```

## 3. 驗收標準

### 3.1 功能驗收
- [ ] 列表頁面正確顯示所有營運公司
- [ ] 可以過濾顯示啟用/停用的營運公司
- [ ] 可以搜尋營運公司（代碼或名稱）
- [ ] 可以新增營運公司（驗證代碼唯一）
- [ ] 可以編輯營運公司資訊
- [ ] 可以切換啟用/停用狀態
- [ ] 刪除時正確檢查關聯資料

### 3.2 技術驗收
- [ ] 使用 shadcn/ui 組件
- [ ] I18N 完整（繁中 + 英文）
- [ ] TypeScript 無錯誤
- [ ] ESLint 無錯誤
- [ ] 響應式設計

### 3.3 用戶體驗
- [ ] Loading 狀態顯示
- [ ] 錯誤訊息友善
- [ ] 成功操作有 Toast 通知
- [ ] 刪除前有確認對話框

## 4. 相關文檔

- 後端 API: `packages/api/src/routers/operatingCompany.ts`
- 資料模型: `packages/db/prisma/schema.prisma` (OperatingCompany)
- 設計參考: `/vendors` 頁面（類似 CRUD 模式）
