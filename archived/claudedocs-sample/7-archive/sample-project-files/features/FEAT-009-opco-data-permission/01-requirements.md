# FEAT-009: Operating Company 數據權限管理

> **建立日期**: 2025-12-12
> **狀態**: 📋 設計中
> **優先級**: Medium
> **關聯功能**: OM Summary, Operating Companies

## 1. 功能概述

### 1.1 背景
目前系統中所有用戶都可以在 OM Summary 頁面看到所有 Operating Company 的數據。為了加強數據安全性和隱私控制，需要實現基於 Operating Company 的數據權限管理，讓管理員可以控制哪些用戶可以看到哪些 Operating Company 的數據。

### 1.2 目標
- 建立用戶與 Operating Company 的授權關係
- 在 OM Summary 頁面實施 OpCo 數據權限過濾
- 提供管理介面讓 Admin/Supervisor 設定用戶的 OpCo 權限
- 不影響其他頁面（如專案管理、費用記錄等）的正常操作

### 1.3 範圍定義
**初期範圍（Phase 1）:**
- 僅應用於 OM Summary 頁面
- 用戶在 OM Summary 的 OpCo 下拉選單只能看到被授權的 OpCo
- 其他頁面（Projects, Expenses, OM Expenses 等）維持現有行為

**未來擴展（Phase 2+）:**
- 可考慮擴展到其他報表頁面
- 可考慮擴展到數據導出功能

## 2. 功能需求

### 2.1 用戶故事

**US-009-1: 管理員設定用戶 OpCo 權限**
```
作為 Admin/Supervisor
我希望能夠設定每個用戶可以訪問哪些 Operating Company 的數據
以便控制敏感財務資訊的可見範圍
```

**US-009-2: 用戶查看 OM Summary 時受權限限制**
```
作為 ProjectManager/Supervisor
當我進入 OM Summary 頁面時
我只能在 OpCo 選擇器中看到被授權給我的 Operating Company
以確保我只能訪問被允許的財務數據
```

**US-009-3: Admin 保留完整訪問權限**
```
作為 Admin
我希望預設可以訪問所有 Operating Company 的數據
以便進行系統管理和監督
```

### 2.2 功能列表

| 編號 | 功能 | 說明 | 優先級 |
|------|------|------|--------|
| F-001 | UserOperatingCompany 關係表 | 建立 User ↔ OperatingCompany 多對多關係 | High |
| F-002 | 用戶 OpCo 權限分配 API | CRUD API 管理用戶的 OpCo 權限 | High |
| F-003 | 用戶權限管理 UI | Users 頁面增加 OpCo 權限設定功能 | High |
| F-004 | OM Summary OpCo 過濾 | 根據用戶權限過濾可選 OpCo | High |
| F-005 | Admin 預設全權限 | Admin 角色預設可訪問所有 OpCo | Medium |
| F-006 | 新用戶預設權限 | 新建用戶時的預設 OpCo 權限策略 | Medium |

## 3. 驗收標準

### 3.1 功能驗收

**AC-001: 權限關係管理**
- [ ] 可以為用戶分配一個或多個 Operating Company 權限
- [ ] 可以移除用戶的 Operating Company 權限
- [ ] 可以查看用戶當前的 Operating Company 權限列表
- [ ] 權限變更即時生效

**AC-002: OM Summary 權限過濾**
- [ ] 用戶進入 OM Summary 頁面時，OpCo 選擇器只顯示被授權的 OpCo
- [ ] 用戶無法通過 URL 參數或 API 訪問未授權的 OpCo 數據
- [ ] 過濾邏輯在後端實施，前端僅顯示過濾後的結果

**AC-003: Admin 特殊處理**
- [ ] Admin 角色用戶預設可以看到所有 OpCo
- [ ] Admin 不需要額外設定 OpCo 權限
- [ ] Admin 可以管理其他用戶的 OpCo 權限

**AC-004: 其他頁面不受影響**
- [ ] Projects 頁面正常運作
- [ ] OM Expenses 頁面正常運作
- [ ] Data Import 頁面正常運作
- [ ] Operating Companies 管理頁面正常運作

### 3.2 技術驗收

- [ ] 新增 Prisma Migration 成功執行
- [ ] API 遵循現有 tRPC 模式
- [ ] UI 使用現有 shadcn/ui 組件
- [ ] 翻譯鍵完整（en + zh-TW）
- [ ] TypeScript 無編譯錯誤
- [ ] ESLint 無錯誤

### 3.3 用戶體驗

- [ ] 權限設定介面直觀易用
- [ ] 權限變更有明確的成功/失敗提示
- [ ] 無權限用戶看到的 OpCo 列表不會顯示「無資料」而是「只顯示授權的選項」
- [ ] 載入狀態有適當的視覺反饋

## 4. 相關文檔

- `packages/db/prisma/schema.prisma` - User, OperatingCompany 模型
- `packages/api/src/routers/operatingCompany.ts` - OpCo API
- `apps/web/src/components/om-summary/OMSummaryFilters.tsx` - OpCo 過濾器
- `apps/web/src/app/[locale]/om-summary/page.tsx` - OM Summary 頁面
- `apps/web/src/app/[locale]/users/` - 用戶管理頁面

## 5. 風險與注意事項

### 5.1 風險
- **R-001**: 新用戶沒有任何 OpCo 權限時，OM Summary 頁面可能顯示空
  - **緩解**: 提供明確的提示訊息，引導用戶聯繫管理員
- **R-002**: 大量用戶批量設定權限可能較繁瑣
  - **緩解**: Phase 2 可考慮增加批量設定功能

### 5.2 注意事項
- 權限檢查必須在後端（API 層）實施，前端只是輔助顯示
- 不要在前端存儲敏感的權限資訊
- 確保向後兼容：現有用戶如果沒有設定權限，應該有合理的預設行為
