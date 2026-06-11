# FEAT-011: Permission Management - 技術設計

> **建立日期**: 2025-12-14
> **狀態**: 🚧 開發中
> **版本**: 1.0

## 1. 架構概覽

### 1.1 設計原則
1. **可擴展性**: 支援未來新增模組操作權限 (CRUD)
2. **向後兼容**: 無權限記錄的用戶採用角色預設權限
3. **雙重保護**: 前端隱藏 + 後端驗證
4. **高性能**: React Query 緩存 + 最小化 API 調用

### 1.2 權限計算邏輯
```
用戶有效權限 = 角色預設權限 UNION 用戶授予權限 MINUS 用戶撤銷權限

偽代碼:
effectivePermissions = Set()
for perm in roleDefaultPermissions:
    effectivePermissions.add(perm)
for userPerm in userPermissions:
    if userPerm.granted:
        effectivePermissions.add(userPerm.code)
    else:
        effectivePermissions.remove(userPerm.code)
```

### 1.3 系統架構圖
```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
├──────────────────┬──────────────────┬───────────────────────┤
│   Sidebar.tsx    │ usePermissions   │  PermissionSelector   │
│  (權限過濾菜單)   │    (Hook)        │   (用戶權限配置)       │
├──────────────────┴──────────────────┴───────────────────────┤
│                     middleware.ts                            │
│                    (路由訪問控制)                             │
├─────────────────────────────────────────────────────────────┤
│                      tRPC API                                │
├─────────────────────────────────────────────────────────────┤
│                  permission.ts Router                        │
│  getMyPermissions | getUserPermissions | setUserPermissions  │
├─────────────────────────────────────────────────────────────┤
│                      Database                                │
├────────────┬────────────────┬───────────────────────────────┤
│ Permission │ RolePermission │ UserPermission                │
└────────────┴────────────────┴───────────────────────────────┘
```

## 2. 數據模型設計

### 2.1 Prisma Schema

```prisma
// packages/db/prisma/schema.prisma

// ============================================================
// FEAT-011: Permission Management Models
// ============================================================

/// 權限定義表 - 系統內建的權限項目
model Permission {
  id          String   @id @default(uuid())
  code        String   @unique  // 權限代碼: "menu:dashboard", "project:create"
  name        String             // 顯示名稱: "儀表板", "建立專案"
  category    String             // 分類: "menu", "project", "proposal", ...
  description String?            // 權限說明
  isActive    Boolean  @default(true)
  sortOrder   Int      @default(0)  // 排序順序
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // Relations
  rolePermissions RolePermission[]
  userPermissions UserPermission[]

  @@index([category])
  @@index([code])
  @@index([isActive])
}

/// 角色預設權限 - 定義各角色的預設權限
model RolePermission {
  id           String   @id @default(uuid())
  roleId       Int
  permissionId String
  createdAt    DateTime @default(now())

  role       Role       @relation(fields: [roleId], references: [id], onDelete: Cascade)
  permission Permission @relation(fields: [permissionId], references: [id], onDelete: Cascade)

  @@unique([roleId, permissionId])
  @@index([roleId])
  @@index([permissionId])
}

/// 用戶權限覆寫 - 用戶個別的權限配置（覆寫角色預設）
model UserPermission {
  id           String   @id @default(uuid())
  userId       String
  permissionId String
  granted      Boolean  @default(true)  // true=授予, false=撤銷
  createdBy    String?                   // 配置者 ID
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  user       User       @relation(fields: [userId], references: [id], onDelete: Cascade)
  permission Permission @relation(fields: [permissionId], references: [id], onDelete: Cascade)

  @@unique([userId, permissionId])
  @@index([userId])
  @@index([permissionId])
}
```

### 2.2 關聯模型更新

```prisma
// 更新 User 模型
model User {
  // ... 現有欄位 ...

  // FEAT-011: 用戶權限
  permissions UserPermission[]
}

// 更新 Role 模型
model Role {
  // ... 現有欄位 ...

  // FEAT-011: 角色預設權限
  defaultPermissions RolePermission[]
}
```

### 2.3 種子數據結構

```typescript
// packages/db/prisma/seed-permissions.ts

export const MENU_PERMISSIONS = [
  // Overview
  { code: 'menu:dashboard', name: '儀表板', category: 'menu', sortOrder: 100 },

  // Project Budget
  { code: 'menu:budget-pools', name: '預算池', category: 'menu', sortOrder: 200 },
  { code: 'menu:projects', name: '專案', category: 'menu', sortOrder: 210 },
  { code: 'menu:proposals', name: '提案', category: 'menu', sortOrder: 220 },

  // Procurement
  { code: 'menu:vendors', name: '供應商', category: 'menu', sortOrder: 300 },
  { code: 'menu:quotes', name: '報價單', category: 'menu', sortOrder: 310 },
  { code: 'menu:purchase-orders', name: '採購單', category: 'menu', sortOrder: 320 },
  { code: 'menu:expenses', name: '費用', category: 'menu', sortOrder: 330 },
  { code: 'menu:om-expenses', name: 'OM 費用', category: 'menu', sortOrder: 340 },
  { code: 'menu:om-summary', name: 'OM 總覽', category: 'menu', sortOrder: 350 },
  { code: 'menu:charge-outs', name: '費用轉嫁', category: 'menu', sortOrder: 360 },

  // System
  { code: 'menu:users', name: '用戶管理', category: 'menu', sortOrder: 400 },
  { code: 'menu:operating-companies', name: '營運公司', category: 'menu', sortOrder: 410 },
  { code: 'menu:om-expense-categories', name: 'OM 費用類別', category: 'menu', sortOrder: 420 },
  { code: 'menu:currencies', name: '幣別', category: 'menu', sortOrder: 430 },
  { code: 'menu:data-import', name: 'OM 數據導入', category: 'menu', sortOrder: 440 },
  { code: 'menu:project-data-import', name: '專案數據導入', category: 'menu', sortOrder: 450 },
  { code: 'menu:settings', name: '設定', category: 'menu', sortOrder: 500 },
];

// 角色預設權限 (roleId: 1=Admin, 2=ProjectManager, 3=Supervisor)
// 注意: 實際 roleId 需根據資料庫 Role 表確認
export const ROLE_DEFAULT_PERMISSIONS = {
  Admin: ['*'], // 所有權限
  Supervisor: [
    'menu:dashboard', 'menu:budget-pools', 'menu:projects', 'menu:proposals',
    'menu:vendors', 'menu:quotes', 'menu:purchase-orders', 'menu:expenses',
    'menu:om-expenses', 'menu:om-summary', 'menu:charge-outs',
    'menu:operating-companies', 'menu:om-expense-categories', 'menu:currencies',
    'menu:data-import', 'menu:project-data-import', 'menu:settings',
  ],
  ProjectManager: [
    'menu:dashboard', 'menu:budget-pools', 'menu:projects', 'menu:proposals',
    'menu:vendors', 'menu:quotes', 'menu:purchase-orders', 'menu:expenses',
    'menu:om-expenses', 'menu:om-summary', 'menu:settings',
  ],
};
```

## 3. API 設計

### 3.1 Permission Router

```typescript
// packages/api/src/routers/permission.ts

import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { createTRPCRouter, protectedProcedure, adminProcedure } from '../trpc';

// ============================================================
// Zod Schemas
// ============================================================

const permissionCategoryEnum = z.enum(['menu', 'project', 'proposal', 'expense', 'system']);

// ============================================================
// Router
// ============================================================

export const permissionRouter = createTRPCRouter({
  /**
   * 獲取所有權限定義
   * 權限：Protected (所有登入用戶)
   */
  getAllPermissions: protectedProcedure
    .input(z.object({
      category: permissionCategoryEnum.optional(),
      isActive: z.boolean().optional().default(true),
    }).optional())
    .query(async ({ ctx, input }) => {
      const where: Record<string, unknown> = {};

      if (input?.category) {
        where.category = input.category;
      }
      if (input?.isActive !== undefined) {
        where.isActive = input.isActive;
      }

      return ctx.prisma.permission.findMany({
        where,
        orderBy: { sortOrder: 'asc' },
      });
    }),

  /**
   * 獲取當前用戶的有效權限列表
   * 權限：Protected
   * 返回：權限代碼陣列 (合併角色預設 + 用戶覆寫)
   */
  getMyPermissions: protectedProcedure.query(async ({ ctx }) => {
    const userId = ctx.session.user.id;
    const roleId = ctx.session.user.role?.id;
    const roleName = ctx.session.user.role?.name;

    // Admin 擁有所有權限
    if (roleName === 'Admin') {
      const allPermissions = await ctx.prisma.permission.findMany({
        where: { isActive: true },
        select: { code: true },
      });
      return allPermissions.map(p => p.code);
    }

    // 獲取角色預設權限
    const rolePermissions = await ctx.prisma.rolePermission.findMany({
      where: { roleId },
      include: { permission: { select: { code: true } } },
    });
    const rolePermCodes = new Set(rolePermissions.map(rp => rp.permission.code));

    // 獲取用戶覆寫權限
    const userPermissions = await ctx.prisma.userPermission.findMany({
      where: { userId },
      include: { permission: { select: { code: true } } },
    });

    // 計算有效權限
    const effectivePermissions = new Set(rolePermCodes);
    for (const up of userPermissions) {
      if (up.granted) {
        effectivePermissions.add(up.permission.code);
      } else {
        effectivePermissions.delete(up.permission.code);
      }
    }

    return Array.from(effectivePermissions);
  }),

  /**
   * 獲取指定用戶的權限配置
   * 權限：Admin only
   */
  getUserPermissions: adminProcedure
    .input(z.object({ userId: z.string().min(1) }))
    .query(async ({ ctx, input }) => {
      // 獲取用戶和角色
      const user = await ctx.prisma.user.findUnique({
        where: { id: input.userId },
        include: { role: true },
      });

      if (!user) {
        throw new TRPCError({ code: 'NOT_FOUND', message: '用戶不存在' });
      }

      // 獲取所有權限
      const allPermissions = await ctx.prisma.permission.findMany({
        where: { isActive: true },
        orderBy: { sortOrder: 'asc' },
      });

      // 獲取角色預設權限
      const rolePermissions = await ctx.prisma.rolePermission.findMany({
        where: { roleId: user.roleId },
        select: { permissionId: true },
      });
      const rolePermIds = new Set(rolePermissions.map(rp => rp.permissionId));

      // 獲取用戶覆寫
      const userPermissions = await ctx.prisma.userPermission.findMany({
        where: { userId: input.userId },
      });
      const userPermMap = new Map(userPermissions.map(up => [up.permissionId, up.granted]));

      // 組合結果
      return allPermissions.map(perm => ({
        id: perm.id,
        code: perm.code,
        name: perm.name,
        category: perm.category,
        // 是否為角色預設
        isRoleDefault: rolePermIds.has(perm.id),
        // 用戶覆寫狀態: null=使用角色預設, true=授予, false=撤銷
        userOverride: userPermMap.get(perm.id) ?? null,
        // 有效狀態
        isEffective: userPermMap.has(perm.id)
          ? userPermMap.get(perm.id)!
          : rolePermIds.has(perm.id),
      }));
    }),

  /**
   * 設定用戶權限覆寫
   * 權限：Admin only
   */
  setUserPermission: adminProcedure
    .input(z.object({
      userId: z.string().min(1),
      permissionId: z.string().min(1),
      granted: z.boolean().nullable(), // null = 移除覆寫，使用角色預設
    }))
    .mutation(async ({ ctx, input }) => {
      const { userId, permissionId, granted } = input;

      // 驗證用戶存在
      const user = await ctx.prisma.user.findUnique({ where: { id: userId } });
      if (!user) {
        throw new TRPCError({ code: 'NOT_FOUND', message: '用戶不存在' });
      }

      // 驗證權限存在
      const permission = await ctx.prisma.permission.findUnique({ where: { id: permissionId } });
      if (!permission) {
        throw new TRPCError({ code: 'NOT_FOUND', message: '權限不存在' });
      }

      if (granted === null) {
        // 移除覆寫
        await ctx.prisma.userPermission.deleteMany({
          where: { userId, permissionId },
        });
      } else {
        // 建立或更新覆寫
        await ctx.prisma.userPermission.upsert({
          where: {
            userId_permissionId: { userId, permissionId },
          },
          create: {
            userId,
            permissionId,
            granted,
            createdBy: ctx.session.user.id,
          },
          update: {
            granted,
          },
        });
      }

      return { success: true };
    }),

  /**
   * 批量設定用戶權限
   * 權限：Admin only
   */
  setUserPermissions: adminProcedure
    .input(z.object({
      userId: z.string().min(1),
      permissions: z.array(z.object({
        permissionId: z.string(),
        granted: z.boolean(),
      })),
    }))
    .mutation(async ({ ctx, input }) => {
      const { userId, permissions } = input;

      // 驗證用戶存在
      const user = await ctx.prisma.user.findUnique({ where: { id: userId } });
      if (!user) {
        throw new TRPCError({ code: 'NOT_FOUND', message: '用戶不存在' });
      }

      // Transaction: 刪除現有覆寫，建立新覆寫
      await ctx.prisma.$transaction(async (tx) => {
        // 刪除現有用戶權限覆寫
        await tx.userPermission.deleteMany({ where: { userId } });

        // 建立新的覆寫（只保存與角色預設不同的）
        if (permissions.length > 0) {
          await tx.userPermission.createMany({
            data: permissions.map(p => ({
              userId,
              permissionId: p.permissionId,
              granted: p.granted,
              createdBy: ctx.session.user.id,
            })),
          });
        }
      });

      return { success: true };
    }),

  /**
   * 獲取角色預設權限
   * 權限：Admin only
   */
  getRolePermissions: adminProcedure
    .input(z.object({ roleId: z.number() }))
    .query(async ({ ctx, input }) => {
      const rolePermissions = await ctx.prisma.rolePermission.findMany({
        where: { roleId: input.roleId },
        include: { permission: true },
        orderBy: { permission: { sortOrder: 'asc' } },
      });

      return rolePermissions.map(rp => ({
        id: rp.permission.id,
        code: rp.permission.code,
        name: rp.permission.name,
        category: rp.permission.category,
      }));
    }),
});
```

### 3.2 Router 註冊

```typescript
// packages/api/src/root.ts

import { permissionRouter } from './routers/permission';

export const appRouter = createTRPCRouter({
  // ... 現有 routers ...
  permission: permissionRouter,
});
```

## 4. 前端設計

### 4.1 usePermissions Hook

```typescript
// apps/web/src/hooks/usePermissions.ts

import { useCallback, useMemo } from 'react';
import { api } from '@/lib/trpc';

export function usePermissions() {
  const { data: permissions, isLoading, error } = api.permission.getMyPermissions.useQuery(
    undefined,
    {
      staleTime: 5 * 60 * 1000, // 5 分鐘緩存
      refetchOnWindowFocus: false,
    }
  );

  const hasPermission = useCallback(
    (code: string): boolean => {
      if (!permissions) return false;
      return permissions.includes(code);
    },
    [permissions]
  );

  const hasAnyPermission = useCallback(
    (codes: string[]): boolean => {
      if (!permissions) return false;
      return codes.some((code) => permissions.includes(code));
    },
    [permissions]
  );

  const hasAllPermissions = useCallback(
    (codes: string[]): boolean => {
      if (!permissions) return false;
      return codes.every((code) => permissions.includes(code));
    },
    [permissions]
  );

  return {
    permissions: permissions ?? [],
    isLoading,
    error,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  };
}

// 權限代碼常量
export const MENU_PERMISSIONS = {
  DASHBOARD: 'menu:dashboard',
  BUDGET_POOLS: 'menu:budget-pools',
  PROJECTS: 'menu:projects',
  PROPOSALS: 'menu:proposals',
  VENDORS: 'menu:vendors',
  QUOTES: 'menu:quotes',
  PURCHASE_ORDERS: 'menu:purchase-orders',
  EXPENSES: 'menu:expenses',
  OM_EXPENSES: 'menu:om-expenses',
  OM_SUMMARY: 'menu:om-summary',
  CHARGE_OUTS: 'menu:charge-outs',
  USERS: 'menu:users',
  OPERATING_COMPANIES: 'menu:operating-companies',
  OM_EXPENSE_CATEGORIES: 'menu:om-expense-categories',
  CURRENCIES: 'menu:currencies',
  DATA_IMPORT: 'menu:data-import',
  PROJECT_DATA_IMPORT: 'menu:project-data-import',
  SETTINGS: 'menu:settings',
} as const;
```

### 4.2 Sidebar 改造

```typescript
// apps/web/src/components/layout/Sidebar.tsx (關鍵改動)

import { usePermissions, MENU_PERMISSIONS } from '@/hooks/usePermissions';

export function Sidebar() {
  const { hasPermission, isLoading } = usePermissions();

  // 定義導航項目並關聯權限
  const navigation: NavigationSection[] = [
    {
      title: t('sections.overview'),
      items: [
        hasPermission(MENU_PERMISSIONS.DASHBOARD) && {
          name: t('menu.dashboard'),
          href: '/dashboard',
          icon: LayoutDashboard,
        },
      ].filter(Boolean) as NavigationItem[],
    },
    {
      title: t('sections.projectBudget'),
      items: [
        hasPermission(MENU_PERMISSIONS.BUDGET_POOLS) && { ... },
        hasPermission(MENU_PERMISSIONS.PROJECTS) && { ... },
        hasPermission(MENU_PERMISSIONS.PROPOSALS) && { ... },
      ].filter(Boolean) as NavigationItem[],
    },
    // ... 其他區段
  ];

  // 過濾空區段
  const filteredNavigation = navigation.filter(
    (section) => section.items.length > 0
  );

  if (isLoading) {
    return <SidebarSkeleton />;
  }

  return (
    <nav>
      {filteredNavigation.map((section) => (
        // ... 渲染邏輯
      ))}
    </nav>
  );
}
```

### 4.3 MenuPermissionSelector 組件

```typescript
// apps/web/src/components/user/MenuPermissionSelector.tsx

interface MenuPermissionSelectorProps {
  userId: string;
}

export function MenuPermissionSelector({ userId }: MenuPermissionSelectorProps) {
  const t = useTranslations('users.permissions');
  const utils = api.useUtils();

  const { data: permissions, isLoading } = api.permission.getUserPermissions.useQuery({ userId });

  const setPermissionMutation = api.permission.setUserPermission.useMutation({
    onSuccess: () => {
      utils.permission.getUserPermissions.invalidate({ userId });
    },
  });

  const handleToggle = (permissionId: string, currentEffective: boolean) => {
    setPermissionMutation.mutate({
      userId,
      permissionId,
      granted: !currentEffective,
    });
  };

  // 分組顯示
  const groupedPermissions = useMemo(() => {
    if (!permissions) return {};
    return permissions.reduce((acc, perm) => {
      if (!acc[perm.category]) acc[perm.category] = [];
      acc[perm.category].push(perm);
      return acc;
    }, {} as Record<string, typeof permissions>);
  }, [permissions]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('title')}</CardTitle>
        <CardDescription>{t('description')}</CardDescription>
      </CardHeader>
      <CardContent>
        {Object.entries(groupedPermissions).map(([category, perms]) => (
          <div key={category} className="mb-4">
            <h4 className="font-medium mb-2">{t(`categories.${category}`)}</h4>
            <div className="space-y-2">
              {perms.map((perm) => (
                <div key={perm.id} className="flex items-center justify-between">
                  <Label>{perm.name}</Label>
                  <Checkbox
                    checked={perm.isEffective}
                    onCheckedChange={() => handleToggle(perm.id, perm.isEffective)}
                    disabled={setPermissionMutation.isLoading}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
```

## 5. 路由保護

### 5.1 路由-權限映射

```typescript
// apps/web/src/lib/route-permissions.ts

export const ROUTE_PERMISSION_MAP: Record<string, string> = {
  '/dashboard': 'menu:dashboard',
  '/budget-pools': 'menu:budget-pools',
  '/projects': 'menu:projects',
  '/proposals': 'menu:proposals',
  '/vendors': 'menu:vendors',
  '/quotes': 'menu:quotes',
  '/purchase-orders': 'menu:purchase-orders',
  '/expenses': 'menu:expenses',
  '/om-expenses': 'menu:om-expenses',
  '/om-summary': 'menu:om-summary',
  '/charge-outs': 'menu:charge-outs',
  '/users': 'menu:users',
  '/operating-companies': 'menu:operating-companies',
  '/om-expense-categories': 'menu:om-expense-categories',
  '/settings/currencies': 'menu:currencies',
  '/data-import': 'menu:data-import',
  '/project-data-import': 'menu:project-data-import',
  '/settings': 'menu:settings',
};

export function getRequiredPermission(pathname: string): string | null {
  // 精確匹配
  if (ROUTE_PERMISSION_MAP[pathname]) {
    return ROUTE_PERMISSION_MAP[pathname];
  }

  // 前綴匹配 (如 /projects/123/edit → menu:projects)
  for (const [route, permission] of Object.entries(ROUTE_PERMISSION_MAP)) {
    if (pathname.startsWith(route + '/')) {
      return permission;
    }
  }

  return null;
}
```

### 5.2 Middleware 擴展

```typescript
// apps/web/src/middleware.ts (擴展)

import { getRequiredPermission } from '@/lib/route-permissions';

export async function middleware(request: NextRequest) {
  // ... 現有認證檢查 ...

  // FEAT-011: 權限檢查
  const pathname = request.nextUrl.pathname;
  const requiredPermission = getRequiredPermission(pathname);

  if (requiredPermission && session?.user) {
    // 從 API 或緩存獲取用戶權限
    // 注意: middleware 中需要使用 fetch 而非 tRPC
    const permissions = await fetchUserPermissions(session.user.id);

    if (!permissions.includes(requiredPermission)) {
      return NextResponse.redirect(new URL('/unauthorized', request.url));
    }
  }

  return NextResponse.next();
}
```

## 6. 性能考量

### 6.1 緩存策略
1. **React Query 緩存**: staleTime 5 分鐘
2. **權限變更時**: invalidate 相關查詢
3. **Middleware**: 考慮 Redis 緩存（如果頻繁調用）

### 6.2 優化建議
- 首次載入時預取權限 (`prefetchQuery`)
- 使用 `select` 減少數據傳輸
- 批量查詢代替多次單獨查詢

## 7. 測試策略

### 7.1 單元測試
- 權限計算邏輯測試
- usePermissions Hook 測試

### 7.2 整合測試
- API Router 測試
- 權限 CRUD 測試

### 7.3 E2E 測試
- 不同角色用戶的 Sidebar 顯示
- 路由訪問控制測試

---

**維護者**: AI Assistant
**最後更新**: 2025-12-14
