# FEAT-011: Permission Management (權限管理系統)

> **建立日期**: 2025-12-14
> **狀態**: 🚧 開發中
> **優先級**: High
> **相關功能**: FEAT-009 (OpCo Data Permission)

## 1. 功能概述

### 1.1 背景
目前系統採用硬編碼的角色權限控制 (RBAC)，僅支援 3 個固定角色 (Admin, Supervisor, ProjectManager)。所有 Sidebar 菜單對所有登入用戶可見，無法根據業務需求動態配置用戶可訪問的功能模組。

### 1.2 目標
建立可配置的權限管理系統，支援：
1. **Phase 1 (FEAT-011)**: Sidebar 菜單權限 - 控制用戶可見/可訪問的菜單項目
2. **Future Phase**: 模組操作權限 - 控制各模組的 CRUD 操作權限

### 1.3 預期效益
- Admin 可靈活配置各用戶的功能權限
- 不同部門用戶只看到相關功能，減少介面複雜度
- 為未來細粒度權限控制奠定基礎
- 提升系統安全性和合規性

## 2. 功能需求

### 2.1 用戶故事

#### US-011-01: 菜單權限配置
**作為** Admin
**我希望** 能夠配置各用戶可看到的 Sidebar 菜單項目
**以便** 根據用戶職責提供適當的功能訪問

**驗收標準**:
- [ ] 用戶編輯頁面新增「菜單權限」配置區塊
- [ ] 可勾選/取消勾選各菜單項目
- [ ] 配置立即生效（無需重新登入）
- [ ] 支援「全選」和「清除」快捷操作

#### US-011-02: 角色預設權限
**作為** Admin
**我希望** 新用戶自動獲得其角色的預設菜單權限
**以便** 減少重複配置工作

**驗收標準**:
- [ ] Admin 角色預設擁有所有菜單權限
- [ ] Supervisor 角色預設擁有除「用戶管理」外的所有權限
- [ ] ProjectManager 角色預設擁有核心業務功能權限
- [ ] 支援配置角色預設權限

#### US-011-03: 菜單動態過濾
**作為** 一般用戶
**我希望** Sidebar 只顯示我有權限訪問的菜單項目
**以便** 獲得簡潔清晰的導航體驗

**驗收標準**:
- [ ] Sidebar 根據用戶權限動態顯示菜單
- [ ] 無權限的菜單項目完全隱藏（非 disabled）
- [ ] 空的分類區段自動隱藏
- [ ] 權限變更後即時更新（無需刷新頁面）

#### US-011-04: 路由訪問控制
**作為** 系統管理員
**我希望** 用戶無法通過 URL 直接訪問無權限的頁面
**以便** 確保系統安全性

**驗收標準**:
- [ ] 無權限用戶訪問受保護路由時重定向到提示頁面
- [ ] 顯示「無權限訪問」的友善提示
- [ ] 提供返回儀表板的連結
- [ ] 記錄未授權訪問嘗試（可選）

### 2.2 功能列表

#### Phase 1: 菜單權限 (FEAT-011 核心)

| 功能 | 描述 | 優先級 |
|------|------|--------|
| **P1-01** 權限數據模型 | Permission, RolePermission, UserPermission 表 | P0 |
| **P1-02** 種子數據 | 17 個菜單權限定義 + 角色預設配置 | P0 |
| **P1-03** 權限 API | getMyPermissions, getUserPermissions, setUserPermissions | P0 |
| **P1-04** usePermissions Hook | 前端權限查詢和緩存 | P0 |
| **P1-05** Sidebar 改造 | 根據權限動態過濾菜單 | P0 |
| **P1-06** 用戶權限配置 UI | 在用戶編輯頁面添加權限選擇器 | P0 |
| **P1-07** 路由 Middleware | 訪問控制和未授權重定向 | P1 |
| **P1-08** 無權限提示頁 | /unauthorized 頁面 | P1 |

#### Future Phase: 模組操作權限 (預留擴展)

| 功能 | 描述 | 優先級 |
|------|------|--------|
| **F-01** CRUD 權限定義 | 各模組的 view/create/edit/delete 權限 | P2 |
| **F-02** API 權限中間件 | Router 層權限檢查 | P2 |
| **F-03** 前端操作控制 | 按鈕/操作的權限隱藏 | P2 |
| **F-04** 批量權限配置 | 角色層級的 CRUD 權限管理 | P2 |

### 2.3 菜單權限清單

| 權限代碼 | 菜單項目 | 預設角色 |
|----------|----------|----------|
| `menu:dashboard` | 儀表板 | All |
| `menu:budget-pools` | 預算池 | All |
| `menu:projects` | 專案 | All |
| `menu:proposals` | 提案 | All |
| `menu:vendors` | 供應商 | All |
| `menu:quotes` | 報價單 | All |
| `menu:purchase-orders` | 採購單 | All |
| `menu:expenses` | 費用 | All |
| `menu:om-expenses` | OM 費用 | All |
| `menu:om-summary` | OM 總覽 | All |
| `menu:charge-outs` | 費用轉嫁 | Admin, Supervisor |
| `menu:users` | 用戶管理 | Admin |
| `menu:operating-companies` | 營運公司 | Admin, Supervisor |
| `menu:om-expense-categories` | OM 費用類別 | Admin, Supervisor |
| `menu:currencies` | 幣別 | Admin, Supervisor |
| `menu:data-import` | OM 數據導入 | Admin, Supervisor |
| `menu:project-data-import` | 專案數據導入 | Admin, Supervisor |
| `menu:settings` | 設定 | All |

## 3. 驗收標準

### 3.1 功能驗收
- [ ] Admin 可在用戶編輯頁配置菜單權限
- [ ] 權限配置立即生效
- [ ] Sidebar 正確顯示有權限的菜單
- [ ] 無權限菜單完全隱藏
- [ ] URL 直接訪問無權限頁面時正確重定向
- [ ] 新用戶自動獲得角色預設權限

### 3.2 技術驗收
- [ ] 權限數據模型正確建立
- [ ] API 返回正確的權限列表
- [ ] 前端 Hook 正確緩存權限數據
- [ ] Middleware 正確攔截未授權訪問
- [ ] TypeScript 類型完整
- [ ] ESLint 無錯誤

### 3.3 用戶體驗
- [ ] 權限配置界面直觀易用
- [ ] 權限變更無需刷新頁面
- [ ] 無權限提示頁友善清晰
- [ ] 支援中英文多語言

## 4. 非功能需求

### 4.1 性能
- 權限查詢響應時間 < 100ms
- 使用 React Query 緩存，避免重複查詢
- 考慮 Redis 緩存（如果查詢頻繁）

### 4.2 安全性
- 權限配置 API 僅 Admin 可訪問
- 前端隱藏 + 後端驗證雙重保護
- 記錄權限變更審計日誌（可選）

### 4.3 可維護性
- 新增菜單項目時，只需添加種子數據
- 權限代碼命名規範：`category:action`
- 完整的類型定義和 JSDoc 文檔

## 5. 相關文檔

- [02-technical-design.md](./02-technical-design.md) - 技術設計
- [03-implementation-plan.md](./03-implementation-plan.md) - 實施計劃
- [04-progress.md](./04-progress.md) - 進度追蹤

## 6. 變更記錄

| 日期 | 版本 | 變更內容 | 作者 |
|------|------|----------|------|
| 2025-12-14 | 1.0 | 初始版本 | AI Assistant |

---

**維護者**: AI Assistant
**最後更新**: 2025-12-14
