# FEAT-009: Operating Company 數據權限管理 - 技術設計

> **建立日期**: 2025-12-12
> **版本**: 1.0
> **狀態**: 📋 設計中

## 1. 數據模型設計

### 1.1 新增 Prisma Model: UserOperatingCompany

```prisma
// ==================================================================
// FEAT-009: 用戶與營運公司權限關係（多對多）
// ==================================================================

model UserOperatingCompany {
  id                 String   @id @default(uuid())
  userId             String
  operatingCompanyId String
  createdAt          DateTime @default(now())
  createdBy          String?  // 設定此權限的管理員 ID

  // 關聯
  user              User             @relation(fields: [userId], references: [id], onDelete: Cascade)
  operatingCompany  OperatingCompany @relation(fields: [operatingCompanyId], references: [id], onDelete: Cascade)

  // 複合唯一鍵：同一用戶不能重複分配同一 OpCo
  @@unique([userId, operatingCompanyId])
  @@index([userId])
  @@index([operatingCompanyId])
}
```

### 1.2 更新現有 Models

**User Model 新增關聯:**
```prisma
model User {
  // ... 現有欄位 ...

  // FEAT-009: OpCo 數據權限
  operatingCompanyPermissions UserOperatingCompany[]
}
```

**OperatingCompany Model 新增關聯:**
```prisma
model OperatingCompany {
  // ... 現有欄位 ...

  // FEAT-009: 用戶權限關聯
  userPermissions UserOperatingCompany[]
}
```

## 2. API 設計

### 2.1 新增 Procedures (operatingCompany.ts)

#### 2.1.1 getUserPermissions - 獲取用戶的 OpCo 權限
```typescript
getUserPermissions: supervisorProcedure
  .input(z.object({ userId: z.string() }))
  .query(async ({ ctx, input }) => {
    const permissions = await ctx.prisma.userOperatingCompany.findMany({
      where: { userId: input.userId },
      include: { operatingCompany: true },
    });
    return permissions;
  }),
```

#### 2.1.2 setUserPermissions - 設定用戶的 OpCo 權限（整批替換）
```typescript
setUserPermissions: supervisorProcedure
  .input(z.object({
    userId: z.string(),
    operatingCompanyIds: z.array(z.string()),
  }))
  .mutation(async ({ ctx, input }) => {
    await ctx.prisma.$transaction(async (tx) => {
      // 1. 刪除現有權限
      await tx.userOperatingCompany.deleteMany({
        where: { userId: input.userId },
      });

      // 2. 建立新權限
      if (input.operatingCompanyIds.length > 0) {
        await tx.userOperatingCompany.createMany({
          data: input.operatingCompanyIds.map((opCoId) => ({
            userId: input.userId,
            operatingCompanyId: opCoId,
            createdBy: ctx.session.user.id,
          })),
        });
      }
    });

    return { success: true };
  }),
```

#### 2.1.3 getForCurrentUser - 獲取當前用戶可訪問的 OpCo（用於 OM Summary）
```typescript
getForCurrentUser: protectedProcedure
  .input(z.object({
    isActive: z.boolean().optional().default(true),
  }).optional())
  .query(async ({ ctx, input }) => {
    const user = ctx.session.user;

    // Admin 角色預設可以訪問所有 OpCo
    if (user.roleId >= 3) { // Admin
      return ctx.prisma.operatingCompany.findMany({
        where: { isActive: input?.isActive ?? true },
        orderBy: { code: 'asc' },
      });
    }

    // 其他用戶根據權限表過濾
    const permissions = await ctx.prisma.userOperatingCompany.findMany({
      where: { userId: user.id },
      include: {
        operatingCompany: true,
      },
    });

    // 只返回啟用且有權限的 OpCo
    return permissions
      .map((p) => p.operatingCompany)
      .filter((opCo) => input?.isActive ? opCo.isActive : true)
      .sort((a, b) => a.code.localeCompare(b.code));
  }),
```

### 2.2 修改現有 Procedures

#### 2.2.1 getAll - 新增可選的用戶權限過濾
```typescript
getAll: protectedProcedure
  .input(z.object({
    isActive: z.boolean().optional(),
    includeInactive: z.boolean().optional().default(false),
    forCurrentUserOnly: z.boolean().optional().default(false), // 新增
  }).optional())
  .query(async ({ ctx, input }) => {
    // 如果啟用用戶權限過濾
    if (input?.forCurrentUserOnly) {
      // 使用 getForCurrentUser 的邏輯
      // ...
    }

    // 原有邏輯保持不變
    // ...
  }),
```

## 3. 前端設計

### 3.1 組件變更

#### 3.1.1 用戶編輯頁面新增 OpCo 權限設定
**位置**: `apps/web/src/app/[locale]/users/[id]/edit/page.tsx`

```tsx
// 新增 OpCo 權限區塊
<Card>
  <CardHeader>
    <CardTitle>{t('permissions.opCoAccess')}</CardTitle>
    <CardDescription>
      {t('permissions.opCoAccessDescription')}
    </CardDescription>
  </CardHeader>
  <CardContent>
    <OpCoPermissionSelector
      userId={userId}
      selectedIds={selectedOpCoIds}
      onChange={handleOpCoChange}
    />
  </CardContent>
</Card>
```

#### 3.1.2 新增 OpCoPermissionSelector 組件
**位置**: `apps/web/src/components/user/OpCoPermissionSelector.tsx`

```tsx
interface OpCoPermissionSelectorProps {
  userId: string;
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  disabled?: boolean;
}

export function OpCoPermissionSelector({
  userId,
  selectedIds,
  onChange,
  disabled,
}: OpCoPermissionSelectorProps) {
  // 獲取所有 OpCo
  const { data: allOpCos } = api.operatingCompany.getAll.useQuery({
    includeInactive: false,
  });

  // 多選 Checkbox 列表
  return (
    <div className="space-y-2">
      {allOpCos?.map((opCo) => (
        <div key={opCo.id} className="flex items-center space-x-2">
          <Checkbox
            id={opCo.id}
            checked={selectedIds.includes(opCo.id)}
            onCheckedChange={(checked) => {
              if (checked) {
                onChange([...selectedIds, opCo.id]);
              } else {
                onChange(selectedIds.filter((id) => id !== opCo.id));
              }
            }}
            disabled={disabled}
          />
          <Label htmlFor={opCo.id}>{opCo.name}</Label>
        </div>
      ))}
    </div>
  );
}
```

#### 3.1.3 修改 OM Summary 頁面
**位置**: `apps/web/src/app/[locale]/om-summary/page.tsx`

```tsx
// 修改 OpCo 查詢
const { data: opCos } = api.operatingCompany.getForCurrentUser.useQuery();

// 其餘邏輯不變，只是 opCoOptions 會根據用戶權限自動過濾
```

### 3.2 翻譯鍵新增

**en.json:**
```json
{
  "users": {
    "permissions": {
      "opCoAccess": "Operating Company Access",
      "opCoAccessDescription": "Select which Operating Companies this user can view in OM Summary",
      "selectAll": "Select All",
      "selectNone": "Clear All",
      "noPermissions": "No Operating Company permissions assigned",
      "permissionsUpdated": "Operating Company permissions updated successfully"
    }
  }
}
```

**zh-TW.json:**
```json
{
  "users": {
    "permissions": {
      "opCoAccess": "營運公司訪問權限",
      "opCoAccessDescription": "選擇此用戶可以在 OM Summary 中查看的營運公司",
      "selectAll": "全選",
      "selectNone": "清除全部",
      "noPermissions": "尚未分配營運公司權限",
      "permissionsUpdated": "營運公司權限更新成功"
    }
  }
}
```

## 4. 數據遷移策略

### 4.1 Migration 計劃
1. 建立 `UserOperatingCompany` 表
2. 為現有 Admin 用戶自動分配所有 OpCo 權限（可選）
3. 其他用戶需手動設定權限

### 4.2 向後兼容
- 如果用戶沒有任何 OpCo 權限設定，有兩種策略：
  - **策略 A**: 顯示空列表（嚴格模式）
  - **策略 B**: 顯示所有 OpCo（寬鬆模式，推薦初期使用）
- 建議初期使用策略 B，給管理員時間設定權限

## 5. 安全考量

### 5.1 權限檢查層級
```
[前端] → [API 層] → [數據庫]
  ↓         ↓          ↓
隱藏UI   驗證權限   返回過濾數據
```

### 5.2 注意事項
- 權限驗證必須在 API 層實施
- 不要僅依賴前端隱藏 UI
- API 應該驗證用戶是否有權限訪問請求的 OpCo

## 6. 測試計劃

### 6.1 單元測試
- [ ] `getUserPermissions` - 返回正確的權限列表
- [ ] `setUserPermissions` - 正確設定/清除權限
- [ ] `getForCurrentUser` - Admin 返回所有，其他用戶返回授權的

### 6.2 整合測試
- [ ] 用戶 A 有 OpCo-HK 權限，OM Summary 只顯示 HK 數據
- [ ] Admin 用戶看到所有 OpCo
- [ ] 新用戶無權限時的處理

## 7. 文件結構

```
packages/
├── db/prisma/
│   ├── schema.prisma                    # 新增 UserOperatingCompany
│   └── migrations/
│       └── 20251212_feat009_user_opco_permission/
│           └── migration.sql
├── api/src/routers/
│   └── operatingCompany.ts              # 新增 3 個 procedures

apps/web/src/
├── app/[locale]/users/[id]/edit/
│   └── page.tsx                         # 新增 OpCo 權限區塊
├── components/user/
│   └── OpCoPermissionSelector.tsx       # 新增組件
└── messages/
    ├── en.json                          # 新增翻譯
    └── zh-TW.json                       # 新增翻譯
```
