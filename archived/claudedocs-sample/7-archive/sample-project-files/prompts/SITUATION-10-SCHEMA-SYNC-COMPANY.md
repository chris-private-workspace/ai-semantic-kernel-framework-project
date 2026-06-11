# SITUATION-10: 公司 Azure 環境 Schema 同步機制

**用途**: 當修改 `schema.prisma` 後需要部署到公司 Azure 環境時，確保數據庫 Schema 與代碼保持同步。

**目標環境**: 公司 Azure 訂閱 (app-itpm-company-dev-001)

**觸發情境**:
- 修改了 `packages/db/prisma/schema.prisma`（新增/修改欄位或表格）
- 準備部署到公司 Azure 環境
- 部署後發現 500 錯誤（可能是 Schema 不同步）
- 需要驗證 Azure 數據庫與 Prisma schema 是否一致

**相關文件**:
- **部署指南**: `SITUATION-7-AZURE-DEPLOY-COMPANY.md`
- **問題排查**: `SITUATION-9-AZURE-TROUBLESHOOT-COMPANY.md`
- **機制說明**: `claudedocs/SCHEMA-SYNC-MECHANISM.md`

---

## 📋 問題背景

### 為什麼需要 Schema 同步機制？

```yaml
本地開發流程:
  命令: pnpm db:push
  效果: 直接將 schema.prisma 同步到本地數據庫
  結果: 所有欄位變更即時生效 ✅

Azure 部署流程:
  命令: prisma migrate deploy (在 docker-entrypoint.sh 中)
  效果: 只執行 migrations/ 資料夾中的 migration 文件
  結果: 如果沒有對應的 migration，欄位不會被創建 ❌
```

### 常見問題場景

| 場景 | 症狀 | 原因 |
|------|------|------|
| 新增欄位後部署 | API 返回 500 錯誤 | Azure 數據庫缺少新欄位 |
| 新增表格後部署 | 頁面無法載入 | Azure 數據庫缺少新表格 |
| 修改欄位類型後部署 | 數據格式錯誤 | 欄位類型不匹配 |

---

## 🔄 Schema 同步流程

### 流程圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Schema 同步完整流程                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 修改 schema.prisma                                       │
│         ↓                                                   │
│  2. pnpm db:generate (重新生成 Prisma Client)                │
│         ↓                                                   │
│  3. 本地測試功能正常                                          │
│         ↓                                                   │
│  4. 部署到 Azure (見 SITUATION-7)                            │
│         ↓                                                   │
│  5. 執行 Schema 檢查 ←─────────────────┐                     │
│         ↓                              │                     │
│  6. 檢查結果                            │                     │
│      ├─ synced → 完成 ✅                │                     │
│      └─ out_of_sync → 執行同步 ─────────┘                     │
│         ↓                                                   │
│  7. 執行 fullSchemaSync                                      │
│         ↓                                                   │
│  8. 驗證同步結果                                              │
│         ↓                                                   │
│  9. 測試頁面功能 → 完成 ✅                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ AI 助手執行步驟

### Step 1: 部署前檢查（本地）

在部署之前，確認 schema.prisma 的變更：

```bash
# 1. 檢查 schema.prisma 最近的變更
git diff packages/db/prisma/schema.prisma

# 2. 確認 Prisma Client 已重新生成
pnpm db:generate

# 3. 本地測試
pnpm dev
# 測試相關功能頁面
```

### Step 2: 部署到 Azure

按照 `SITUATION-7-AZURE-DEPLOY-COMPANY.md` 執行部署流程。

### Step 3: 部署後 Schema 檢查

```bash
BASE_URL="https://app-itpm-company-dev-001.azurewebsites.net"

# 1️⃣ 完整對比 Schema（檢查所有 31 個表格）
curl "$BASE_URL/api/trpc/health.fullSchemaCompare"
```

**檢查結果解讀**:

```json
// ✅ 已同步 - 無需操作
{
  "status": "synced",
  "summary": {
    "totalTablesChecked": 31,
    "missingTables": [],
    "tablesWithMissingColumns": [],
    "allMissingColumns": []
  }
}

// ❌ 未同步 - 需要執行同步
{
  "status": "out_of_sync",
  "summary": {
    "totalTablesChecked": 31,
    "missingTables": ["Permission"],
    "tablesWithMissingColumns": [
      { "table": "Project", "missing": ["projectCode", "globalFlag"] }
    ],
    "allMissingColumns": ["Project.projectCode", "Project.globalFlag"],
    "fixSqlPreviewCount": 5
  },
  "fixSqlPreview": [
    "CREATE TABLE IF NOT EXISTS \"Permission\" ...",
    "ALTER TABLE \"Project\" ADD COLUMN IF NOT EXISTS \"projectCode\" TEXT DEFAULT ''"
  ]
}
```

### Step 4: 執行 Schema 同步

如果 Step 3 顯示 `out_of_sync`：

```bash
# 2️⃣ 執行一鍵完整同步
curl -X POST "$BASE_URL/api/trpc/health.fullSchemaSync"
```

**同步結果解讀**:

```json
{
  "success": true,
  "fixedTables": 5,
  "fixedColumns": 42,
  "stillMissing": 0,
  "results": [
    "=== 完整 Schema 同步開始 ===",
    "📋 Phase 1: 檢查並創建缺失表格...",
    "  ✅ 創建 Permission 表",
    "📋 Phase 2: 修復 Project 表...",
    "  ✅ 添加 projectCode 欄位",
    "..."
  ]
}
```

### Step 5: 驗證同步結果

```bash
# 3️⃣ 再次檢查，確認已同步
curl "$BASE_URL/api/trpc/health.fullSchemaCompare"
# 應該返回 "status": "synced"
```

### Step 6: 功能測試

```bash
# 測試所有主要頁面
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/zh-TW/projects"      # 應返回 200
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/zh-TW/om-expenses"   # 應返回 200
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/zh-TW/om-summary"    # 應返回 200
```

---

## ⚠️ Schema 定義維護（方案 C 完全自動化）

### 當前機制說明（v2.0.0）

**方案 C 自動化** - 欄位列表從 Prisma.dmmf 自動讀取，無需手動維護！

| 組件 | 文件 | 用途 | 維護方式 |
|------|------|------|----------|
| 欄位列表 | `schemaDefinition.ts` → `getSchemaDefinitionFromDMMF()` | 所有表格的欄位列表 | **✅ 全自動** (從 Prisma.dmmf 讀取) |
| SQL 類型 | `schemaDefinition.ts` → `prismaTypeToSqlType()` | Prisma → SQL 類型映射 | **✅ 全自動** |
| 特殊默認值 | `schemaDefinition.ts` → `COLUMN_TYPE_OVERRIDES` | 有特殊默認值的欄位 | **⚠️ 手動** (僅特殊情況) |

### 自動化流程

```
┌─────────────────────────────────────────────────────────┐
│                方案 C: 完全自動化流程                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 修改 schema.prisma (新增欄位)                         │
│         ↓                                               │
│  2. pnpm db:generate                                    │
│         ↓                                               │
│  3. Prisma Client 重新生成                               │
│         ↓                                               │
│  4. Prisma.dmmf 自動包含新欄位 ✅                         │
│         ↓                                               │
│  5. 部署到 Azure                                        │
│         ↓                                               │
│  6. Health API 自動讀取最新 schema ✅                     │
│         ↓                                               │
│  7. fullSchemaCompare 自動檢測差異 ✅                     │
│         ↓                                               │
│  8. fullSchemaSync 自動修復 ✅                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 新增欄位時的維護步驟

**大多數情況（無特殊默認值）- 無需手動維護：**

```bash
# 1. 修改 schema.prisma
Edit: packages/db/prisma/schema.prisma

# 2. 重新生成 Prisma Client（這會自動更新 DMMF）
Bash: pnpm db:generate

# 3. 本地測試
Bash: pnpm dev

# 4. 部署到 Azure（Health API 會自動讀取新欄位）
# 完成！無需其他手動操作 ✅
```

**特殊情況（有特殊默認值）- 需要手動覆蓋：**

```bash
# 只有當欄位需要特殊默認值時，才需要更新 COLUMN_TYPE_OVERRIDES

# 例如：新增 Project.newField 欄位，默認值為 'SpecialValue'
Edit: packages/api/src/lib/schemaDefinition.ts

# 在 COLUMN_TYPE_OVERRIDES.Project 中添加：
# newField: { type: 'TEXT', default: "'SpecialValue'" },
```

### COLUMN_TYPE_OVERRIDES 格式（僅特殊情況需要）

```typescript
// 只需定義有特殊默認值的欄位
// 其他欄位會自動從 Prisma.dmmf 推斷
export const COLUMN_TYPE_OVERRIDES: Record<string, Record<string, ColumnTypeInfo>> = {
  Project: {
    // FEAT-001: 有特殊默認值
    projectCode: { type: 'TEXT', default: "''" },
    globalFlag: { type: 'TEXT', default: "'Region'" },
    priority: { type: 'TEXT', default: "'Medium'" },
    // 新增有特殊默認值的欄位時，在這裡添加
  },
  // 其他表格...
};
```

### Prisma 類型 → SQL 類型自動映射表

| Prisma 類型 | PostgreSQL 類型 | 自動推斷 |
|------------|-----------------|---------|
| `String` | `TEXT` | ✅ |
| `String?` | `TEXT` | ✅ |
| `Int` | `INTEGER` | ✅ |
| `Float` | `DOUBLE PRECISION` | ✅ |
| `Boolean` | `BOOLEAN` | ✅ |
| `DateTime` | `TIMESTAMP(3)` | ✅ |
| `BigInt` | `BIGINT` | ✅ |
| `Json` | `JSONB` | ✅ |

### 默認值自動推斷

| Prisma 默認值 | SQL 默認值 | 自動推斷 |
|--------------|-----------|---------|
| `@default(now())` | `DEFAULT NOW()` | ✅ |
| `@default(uuid())` | `DEFAULT gen_random_uuid()` | ✅ |
| `@default("string")` | `DEFAULT 'string'` | ✅ |
| `@default(0)` | `DEFAULT 0` | ✅ |
| `@default(false)` | `DEFAULT false` | ✅ |
| 特殊業務默認值 | 需手動定義 | ⚠️ |

---

## 🔧 Health API 快速參考

### 診斷 API

| API | 方法 | 用途 |
|-----|------|------|
| `health.fullSchemaCompare` | GET | **⭐ 完整對比所有 31 個表格** |
| `health.schemaCompare` | GET | 舊版對比（部分表格） |
| `health.schemaCheck` | GET | 檢查表格是否存在 |
| `health.dbCheck` | GET | 數據庫連線檢查 |

### 修復 API

| API | 方法 | 用途 |
|-----|------|------|
| `health.fullSchemaSync` | POST | **⭐ 一鍵修復所有差異** |
| `health.fixAllSchemaIssues` | POST | 舊版修復（保留向後兼容） |
| `health.fixPermissionTables` | POST | 修復 Permission 相關表格 |

### 命令速查

```bash
BASE_URL="https://app-itpm-company-dev-001.azurewebsites.net"

# 檢查
curl "$BASE_URL/api/trpc/health.fullSchemaCompare"

# 同步
curl -X POST "$BASE_URL/api/trpc/health.fullSchemaSync"

# 驗證
curl "$BASE_URL/api/trpc/health.fullSchemaCompare"
```

---

## 📋 常見問題 FAQ

### Q1: 為什麼不直接創建 migration 文件？

A: 理論上可以，但有以下考量：
1. Prisma migrations 是不可變的（immutable）
2. 本地開發使用 `db:push` 更方便快速
3. Health API 方案已驗證可行且易於維護
4. 可以在部署後即時修復，無需重新部署

### Q2: fullSchemaSync 會破壞現有數據嗎？

A: 不會。所有操作都使用：
- `CREATE TABLE IF NOT EXISTS` - 只在表格不存在時創建
- `ADD COLUMN IF NOT EXISTS` - 只在欄位不存在時添加
- 不會修改或刪除現有數據

### Q3: 如何知道需要更新 COLUMN_TYPE_MAP？

A: 當你新增的欄位類型不在現有映射中時，需要更新。常見需要手動添加的情況：
- 有特殊默認值的欄位
- 有外鍵約束的欄位
- 複雜類型（如 JSON、ENUM）

### Q4: 如果 fullSchemaSync 執行失敗怎麼辦？

A:
1. 查看錯誤訊息，確認是哪個表格/欄位出問題
2. 檢查 `COLUMN_TYPE_MAP` 是否有對應的類型定義
3. 如果是新表格，可能需要更新 `fullSchemaSync` 中的創建邏輯
4. 參考 `SITUATION-9-AZURE-TROUBLESHOOT-COMPANY.md` 進行排查

---

## 🔗 相關文檔

- [SITUATION-7: 公司環境部署指南](./SITUATION-7-AZURE-DEPLOY-COMPANY.md)
- [SITUATION-9: 公司環境問題排查](./SITUATION-9-AZURE-TROUBLESHOOT-COMPANY.md)
- [Schema 同步機制說明](../../SCHEMA-SYNC-MECHANISM.md)

---

**版本**: 1.1.0
**最後更新**: 2025-12-16
**維護者**: AI 助手 + DevOps Team

---

## 📝 變更記錄

### v1.1.0 (2025-12-16)
- 更新表格數量: 27 → 31 個表格
- 新增表格: Permission, RolePermission, UserPermission, UserOperatingCompany (FEAT-011 權限管理系統)

### v1.0.0 (2025-12-15)
- 初始版本
- 方案 C 完全自動化機制說明
