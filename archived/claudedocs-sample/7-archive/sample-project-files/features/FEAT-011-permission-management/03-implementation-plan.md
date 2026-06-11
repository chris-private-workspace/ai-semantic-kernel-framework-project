# FEAT-011: Permission Management - 實施計劃

> **建立日期**: 2025-12-14
> **狀態**: 🚧 開發中
> **版本**: 1.0

## 1. 實施概覽

### 1.1 Phase 1 範圍 (FEAT-011 核心)
- Sidebar 菜單權限管理
- 用戶權限配置 UI
- 路由訪問控制

### 1.2 時間估算
| 階段 | 任務 | 預估時間 |
|------|------|----------|
| 1.1 | 數據模型 | 1-2 hr |
| 1.2 | 種子數據 | 1 hr |
| 1.3 | 後端 API | 2-3 hr |
| 1.4 | 前端 Hook | 1-2 hr |
| 1.5 | Sidebar 改造 | 2-3 hr |
| 1.6 | 用戶權限 UI | 2-3 hr |
| 1.7 | 路由保護 | 1-2 hr |
| 1.8 | 測試驗證 | 1-2 hr |
| **總計** | | **~12-18 hr** |

## 2. 詳細任務分解

### Phase 1.1: 數據模型

**目標**: 建立 Permission, RolePermission, UserPermission 三個新模型

**任務清單**:
- [ ] 在 `schema.prisma` 新增 Permission 模型
- [ ] 在 `schema.prisma` 新增 RolePermission 模型
- [ ] 在 `schema.prisma` 新增 UserPermission 模型
- [ ] 更新 User 模型添加 permissions 關聯
- [ ] 更新 Role 模型添加 defaultPermissions 關聯
- [ ] 執行 `pnpm db:generate`
- [ ] 執行 `pnpm db:push` 或創建遷移

**驗收標準**:
- [ ] Prisma Schema 無錯誤
- [ ] Prisma Client 成功生成
- [ ] 資料庫表結構正確建立

**文件變更**:
```
packages/db/prisma/schema.prisma (修改)
```

---

### Phase 1.2: 種子數據

**目標**: 建立 17 個菜單權限和 3 個角色預設配置

**任務清單**:
- [ ] 創建 `seed-permissions.ts` 種子腳本
- [ ] 定義 17 個菜單權限記錄
- [ ] 定義 Admin 角色預設權限 (全部)
- [ ] 定義 Supervisor 角色預設權限
- [ ] 定義 ProjectManager 角色預設權限
- [ ] 更新 `seed.ts` 調用權限種子
- [ ] 執行種子腳本驗證

**驗收標準**:
- [ ] Permission 表有 17 筆記錄
- [ ] RolePermission 表有正確的角色-權限映射
- [ ] 可重複執行（冪等性）

**文件變更**:
```
packages/db/prisma/seed-permissions.ts (新增)
packages/db/prisma/seed.ts (修改)
```

**種子數據定義**:
```typescript
// 17 個菜單權限
const MENU_PERMISSIONS = [
  // Overview (1)
  { code: 'menu:dashboard', name: '儀表板', category: 'menu', sortOrder: 100 },

  // Project Budget (3)
  { code: 'menu:budget-pools', name: '預算池', category: 'menu', sortOrder: 200 },
  { code: 'menu:projects', name: '專案', category: 'menu', sortOrder: 210 },
  { code: 'menu:proposals', name: '提案', category: 'menu', sortOrder: 220 },

  // Procurement (7)
  { code: 'menu:vendors', name: '供應商', category: 'menu', sortOrder: 300 },
  { code: 'menu:quotes', name: '報價單', category: 'menu', sortOrder: 310 },
  { code: 'menu:purchase-orders', name: '採購單', category: 'menu', sortOrder: 320 },
  { code: 'menu:expenses', name: '費用', category: 'menu', sortOrder: 330 },
  { code: 'menu:om-expenses', name: 'OM 費用', category: 'menu', sortOrder: 340 },
  { code: 'menu:om-summary', name: 'OM 總覽', category: 'menu', sortOrder: 350 },
  { code: 'menu:charge-outs', name: '費用轉嫁', category: 'menu', sortOrder: 360 },

  // System (6)
  { code: 'menu:users', name: '用戶管理', category: 'menu', sortOrder: 400 },
  { code: 'menu:operating-companies', name: '營運公司', category: 'menu', sortOrder: 410 },
  { code: 'menu:om-expense-categories', name: 'OM 費用類別', category: 'menu', sortOrder: 420 },
  { code: 'menu:currencies', name: '幣別', category: 'menu', sortOrder: 430 },
  { code: 'menu:data-import', name: 'OM 數據導入', category: 'menu', sortOrder: 440 },
  { code: 'menu:project-data-import', name: '專案數據導入', category: 'menu', sortOrder: 450 },

  // Settings (1)
  { code: 'menu:settings', name: '設定', category: 'menu', sortOrder: 500 },
];
```

---

### Phase 1.3: 後端 API

**目標**: 建立 permission.ts Router 提供權限 CRUD API

**任務清單**:
- [ ] 創建 `packages/api/src/routers/permission.ts`
- [ ] 實現 `getAllPermissions` (protectedProcedure)
- [ ] 實現 `getMyPermissions` (protectedProcedure)
- [ ] 實現 `getUserPermissions` (adminProcedure)
- [ ] 實現 `setUserPermission` (adminProcedure)
- [ ] 實現 `setUserPermissions` 批量版 (adminProcedure)
- [ ] 實現 `getRolePermissions` (adminProcedure)
- [ ] 在 `root.ts` 註冊 permissionRouter
- [ ] TypeScript 編譯通過

**驗收標準**:
- [ ] 所有 API 正常工作
- [ ] 權限檢查正確 (Admin only)
- [ ] Zod 輸入驗證完整
- [ ] 錯誤處理完善

**文件變更**:
```
packages/api/src/routers/permission.ts (新增)
packages/api/src/root.ts (修改)
```

---

### Phase 1.4: 前端 Hook

**目標**: 建立 usePermissions Hook 和權限常量

**任務清單**:
- [ ] 創建 `apps/web/src/hooks/usePermissions.ts`
- [ ] 實現 `usePermissions` Hook
- [ ] 實現 `hasPermission(code)` 方法
- [ ] 實現 `hasAnyPermission(codes)` 方法
- [ ] 實現 `hasAllPermissions(codes)` 方法
- [ ] 定義 `MENU_PERMISSIONS` 常量對象
- [ ] 配置 React Query 緩存策略

**驗收標準**:
- [ ] Hook 正確返回權限列表
- [ ] 方法正確判斷權限
- [ ] 緩存策略生效

**文件變更**:
```
apps/web/src/hooks/usePermissions.ts (新增)
apps/web/src/hooks/index.ts (修改，導出)
```

---

### Phase 1.5: Sidebar 改造

**目標**: 根據用戶權限動態過濾 Sidebar 菜單

**任務清單**:
- [ ] 修改 `Sidebar.tsx` 導入 usePermissions
- [ ] 為每個菜單項添加權限檢查
- [ ] 實現空區段自動隱藏
- [ ] 添加載入狀態處理 (Skeleton)
- [ ] 測試各角色的菜單顯示

**驗收標準**:
- [ ] Admin 看到所有菜單
- [ ] 其他角色根據權限看到部分菜單
- [ ] 空區段正確隱藏
- [ ] 無權限菜單完全不顯示

**文件變更**:
```
apps/web/src/components/layout/Sidebar.tsx (修改)
```

**改造示例**:
```typescript
// 原本
const navigation = [
  { name: 'Dashboard', href: '/dashboard', ... },
  { name: 'Projects', href: '/projects', ... },
];

// 改造後
const navigation = [
  hasPermission('menu:dashboard') && { name: 'Dashboard', href: '/dashboard', ... },
  hasPermission('menu:projects') && { name: 'Projects', href: '/projects', ... },
].filter(Boolean);
```

---

### Phase 1.6: 用戶權限配置 UI

**目標**: 在用戶編輯頁面添加菜單權限配置

**任務清單**:
- [ ] 創建 `MenuPermissionSelector.tsx` 組件
- [ ] 實現權限分類顯示 (按 category 分組)
- [ ] 實現權限勾選/取消勾選
- [ ] 顯示角色預設標記
- [ ] 實現全選/清除快捷操作
- [ ] 在用戶編輯頁整合組件
- [ ] 添加 i18n 翻譯鍵

**驗收標準**:
- [ ] 組件正確顯示所有菜單權限
- [ ] 勾選/取消正確保存
- [ ] 角色預設權限正確標記
- [ ] 保存後立即生效
- [ ] 中英文翻譯完整

**文件變更**:
```
apps/web/src/components/user/MenuPermissionSelector.tsx (新增)
apps/web/src/app/[locale]/users/[id]/edit/page.tsx (修改)
apps/web/src/messages/en.json (修改)
apps/web/src/messages/zh-TW.json (修改)
```

**i18n 翻譯鍵**:
```json
{
  "users": {
    "permissions": {
      "title": "Menu Permissions",
      "description": "Configure which menu items this user can see",
      "categories": {
        "menu": "Menu Access"
      },
      "selectAll": "Select All",
      "clearAll": "Clear All",
      "roleDefault": "Role Default",
      "userOverride": "User Override"
    }
  }
}
```

---

### Phase 1.7: 路由保護

**目標**: 阻止用戶通過 URL 直接訪問無權限頁面

**任務清單**:
- [ ] 創建 `lib/route-permissions.ts` 路由映射
- [ ] 創建 `app/[locale]/unauthorized/page.tsx` 頁面
- [ ] 擴展 `middleware.ts` 添加權限檢查
- [ ] 測試各種訪問場景

**驗收標準**:
- [ ] 無權限訪問正確重定向到 /unauthorized
- [ ] 未授權頁面顯示友善提示
- [ ] 有權限用戶正常訪問

**文件變更**:
```
apps/web/src/lib/route-permissions.ts (新增)
apps/web/src/app/[locale]/unauthorized/page.tsx (新增)
apps/web/src/middleware.ts (修改)
apps/web/src/messages/en.json (修改)
apps/web/src/messages/zh-TW.json (修改)
```

**注意事項**:
- Middleware 中無法使用 tRPC，需用 fetch
- 考慮緩存權限結果以提升性能
- 可選擇延後實施，先完成前端隱藏

---

### Phase 1.8: 測試驗證

**目標**: 確保所有功能正常運作

**測試案例**:
| 測試場景 | 預期結果 |
|----------|----------|
| Admin 登入 | 看到所有菜單 |
| Supervisor 登入 | 看到除「用戶管理」外的菜單 |
| ProjectManager 登入 | 看到核心業務菜單 |
| Admin 修改用戶權限 | 權限立即生效 |
| 用戶直接訪問無權限 URL | 重定向到 /unauthorized |
| 權限變更後刷新頁面 | 菜單正確更新 |

**驗收清單**:
- [ ] 功能測試通過
- [ ] TypeScript 編譯無錯誤
- [ ] ESLint 無錯誤
- [ ] i18n 驗證通過
- [ ] 手動測試各角色場景

---

## 3. 依賴關係圖

```
Phase 1.1 數據模型
    ↓
Phase 1.2 種子數據
    ↓
Phase 1.3 後端 API
    ↓
Phase 1.4 前端 Hook ─────┬───→ Phase 1.5 Sidebar 改造
                         │
                         └───→ Phase 1.6 用戶權限 UI
                                      ↓
                              Phase 1.7 路由保護
                                      ↓
                              Phase 1.8 測試驗證
```

## 4. 風險和緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Middleware 權限查詢性能 | 每次請求增加延遲 | 使用緩存 / 延後實施 |
| 現有用戶無權限記錄 | 無法看到任何菜單 | 向後兼容：無記錄時使用角色預設 |
| 角色 ID 映射問題 | 權限分配錯誤 | 使用 role.name 而非 roleId |
| 前端緩存過期 | 權限變更不即時 | invalidate 相關查詢 |

## 5. 回滾計劃

如果實施過程中發現重大問題：

1. **數據庫回滾**: 刪除新增的 3 個表
2. **代碼回滾**: 恢復 Sidebar.tsx 原始版本
3. **移除 API**: 從 root.ts 移除 permissionRouter

## 6. 後續擴展

### Future Phase 2: 模組操作權限
- 新增 CRUD 權限種子數據
- 擴展 permission Router
- 各 Router 添加權限檢查中間件
- 前端操作按鈕權限控制

### 預留權限代碼
```typescript
// Project CRUD
'project:view', 'project:create', 'project:edit', 'project:delete'

// Proposal CRUD + Approve
'proposal:view', 'proposal:create', 'proposal:edit', 'proposal:approve'

// Expense CRUD + Approve
'expense:view', 'expense:create', 'expense:edit', 'expense:approve'

// ... 其他模組
```

---

**維護者**: AI Assistant
**最後更新**: 2025-12-14
