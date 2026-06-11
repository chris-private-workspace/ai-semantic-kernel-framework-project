# FEAT-004: Operating Company Management - 技術設計

## 1. 系統架構

### 1.1 後端 API (已完成)

**Router**: `packages/api/src/routers/operatingCompany.ts`

| Procedure | 類型 | 權限 | 描述 |
|-----------|------|------|------|
| `create` | Mutation | Supervisor | 建立營運公司 |
| `update` | Mutation | Supervisor | 更新營運公司 |
| `getById` | Query | Protected | 查詢單一營運公司 |
| `getAll` | Query | Protected | 查詢營運公司列表 |
| `delete` | Mutation | Supervisor | 刪除營運公司 |
| `toggleActive` | Mutation | Supervisor | 切換啟用狀態 |

### 1.2 前端結構 (待開發)

```
apps/web/src/
├── app/[locale]/operating-companies/
│   ├── page.tsx              # 列表頁面
│   ├── new/page.tsx          # 新增頁面
│   └── [id]/edit/page.tsx    # 編輯頁面
├── components/operating-company/
│   ├── index.ts              # 統一導出
│   ├── OperatingCompanyForm.tsx    # 表單組件
│   └── OperatingCompanyActions.tsx # 操作按鈕
└── messages/
    ├── en.json               # 英文翻譯
    └── zh-TW.json            # 繁中翻譯
```

## 2. 組件設計

### 2.1 列表頁面 (`page.tsx`)

**功能**:
- 表格顯示營運公司列表
- 過濾器（啟用/停用狀態）
- 搜尋功能
- 分頁（如需要）
- 操作按鈕（編輯、切換狀態、刪除）

**依賴**:
- `api.operatingCompany.getAll`
- `api.operatingCompany.toggleActive`
- `api.operatingCompany.delete`
- shadcn/ui: Table, Button, Input, Badge, DropdownMenu

### 2.2 表單組件 (`OperatingCompanyForm.tsx`)

**Props**:
```typescript
interface OperatingCompanyFormProps {
  mode: 'create' | 'edit';
  initialData?: OperatingCompany;
}
```

**欄位**:
- `code`: 公司代碼 (必填, 唯一)
- `name`: 公司名稱 (必填)
- `description`: 描述 (選填)
- `isActive`: 啟用狀態 (編輯模式)

### 2.3 操作按鈕 (`OperatingCompanyActions.tsx`)

**Props**:
```typescript
interface OperatingCompanyActionsProps {
  opCo: OperatingCompany;
  onToggleActive: () => void;
  onDelete: () => void;
}
```

**按鈕**:
- 編輯 (連結到編輯頁)
- 切換狀態 (啟用/停用)
- 刪除 (需確認對話框)

## 3. I18N 設計

### 3.1 翻譯鍵結構

```json
{
  "operatingCompanies": {
    "title": "營運公司",
    "description": "管理系統中的營運公司",
    "table": {
      "code": "公司代碼",
      "name": "公司名稱",
      "description": "描述",
      "status": "狀態",
      "chargeOuts": "費用轉嫁數",
      "omExpenses": "OM費用數",
      "actions": "操作"
    },
    "status": {
      "active": "啟用",
      "inactive": "停用"
    },
    "form": {
      "createTitle": "新增營運公司",
      "editTitle": "編輯營運公司",
      "code": { "label": "公司代碼", "placeholder": "如: OpCo-HK" },
      "name": { "label": "公司名稱", "placeholder": "如: Hong Kong Operations" },
      "description": { "label": "描述", "placeholder": "選填" }
    },
    "actions": {
      "create": "新增營運公司",
      "edit": "編輯",
      "delete": "刪除",
      "activate": "啟用",
      "deactivate": "停用"
    },
    "messages": {
      "createSuccess": "營運公司建立成功",
      "updateSuccess": "營運公司更新成功",
      "deleteSuccess": "營運公司刪除成功",
      "toggleSuccess": "狀態已更新",
      "deleteConfirm": "確定要刪除此營運公司嗎？",
      "deleteWarning": "此操作無法復原"
    },
    "filters": {
      "all": "全部",
      "activeOnly": "僅啟用",
      "inactiveOnly": "僅停用",
      "search": "搜尋公司代碼或名稱"
    },
    "empty": "尚無營運公司"
  }
}
```

## 4. 路由設計

| 路由 | 頁面 | 權限 |
|------|------|------|
| `/operating-companies` | 列表頁 | Protected |
| `/operating-companies/new` | 新增頁 | Supervisor |
| `/operating-companies/[id]/edit` | 編輯頁 | Supervisor |

## 5. 參考實現

- **Vendors 頁面**: `apps/web/src/app/[locale]/vendors/` (類似 CRUD 模式)
- **Users 頁面**: `apps/web/src/app/[locale]/users/` (權限控制參考)
