# SITUATION-7: Azure 公司環境部署指引

**用途**: 當需要部署到**公司 Azure 訂閱**時，使用此指引確保符合企業規範、安全合規的正式部署流程。

**目標環境**: 公司 Azure 訂閱（用於正式部署、生產環境、客戶訪問）

**觸發情境**:

- 首次部署到公司 Azure 環境
- 正式環境版本更新
- 執行生產部署
- 配置符合企業規範的資源
- Staging → Production 升級

**故障排查**: 如遇到部署問題，請參閱 **SITUATION-9-AZURE-TROUBLESHOOT-COMPANY.md**

**Schema 同步**: 如需了解 Schema 同步機制詳情，請參閱 **SITUATION-10-SCHEMA-SYNC-COMPANY.md**

---

## 📋 快速開始檢查清單

在開始部署之前，請確認以下事項：

```yaml
部署前必檢:
  - [ ] 已登入正確的 Azure 訂閱 (az account show)
  - [ ] 擁有資源群組的 Contributor 權限
  - [ ] .dockerignore 不排除 migrations 資料夾
  - [ ] schema.prisma 包含 linux-musl-openssl-3.0.x binaryTarget
  - [ ] 所有 migration SQL 檔案都已提交到 Git
  - [ ] 環境變數配置檔案已準備好
  - [ ] ⚠️ 確認所有 schema 變更都有對應的 migration（見下方警告）
```

### ⚠️ 關鍵警告：db push vs migration

```yaml
critical_warning:
  問題: 開發時使用 "prisma db push" 不會創建 migration 文件
  後果: 本地數據庫有新欄位/表，但 Azure 部署時不會執行

  發生過的案例 (2025-12-08):
    - FEAT-006: Project 8 個新欄位 + ProjectChargeOutOpCo 表 → 無 migration
    - FEAT-007: OMExpense 3 個新欄位 → 無 migration
    - 結果: 部署後 /projects, /om-expenses, /om-summary 全部 500 錯誤

  預防措施:
    1. 開發完成後，執行 "pnpm db:migrate" 創建正式 migration
    2. 或確保 health.ts 有對應的修復 API
    3. 部署後立即執行 schema 修復 API
```

---

## 🎯 公司環境部署原則

### 1. 安全與合規優先

```yaml
enterprise_requirements:
  - ✅ 所有部署需經授權確認
  - ✅ 符合公司 Azure 命名規範
  - ✅ 遵守企業安全政策
  - ✅ 監控和告警機制
  - ✅ 備份和災難恢復策略
```

### 2. 企業架構標準

```yaml
enterprise_architecture:
  資源群組: "RG-RCITest-RAPO-N8N"
  App_Service: "app-itpm-company-dev-001"
  PostgreSQL: "psql-itpm-company-dev-001"
  ACR: "acritpmcompany"
  監控: Application Insights + Log Analytics
```

---

## 🚀 部署執行流程

### 階段 1: 環境準備（10 分鐘）

#### 1.1 確認 Azure 登入

```bash
# 確認當前訂閱
az account show --query "{Name:name, SubscriptionId:id}" -o table

# 如果需要切換訂閱
az account set --subscription "YOUR-SUBSCRIPTION-ID"
```

#### 1.2 確認 ACR 登入

```bash
# 登入 Azure Container Registry
az acr login --name acritpmcompany

# 驗證登入成功
docker pull acritpmcompany.azurecr.io/itpm-web:latest 2>/dev/null && echo "ACR 登入成功" || echo "首次部署，繼續"
```

### 階段 2: 建置 Docker 映像（15 分鐘）

#### 2.1 關鍵檢查點 ⚠️

**在建置之前，必須確認以下配置正確：**

```bash
# 1. 確認 .dockerignore 不排除 migrations
grep -n "migrations" .dockerignore
# ⚠️ 如果看到 "**/migrations" 未被註解，必須先註解掉！

# 2. 確認 schema.prisma 有正確的 binaryTargets
grep -A 2 "binaryTargets" packages/db/prisma/schema.prisma
# 必須包含: "linux-musl-openssl-3.0.x"

# 3. 確認 migrations 資料夾有內容
ls packages/db/prisma/migrations/
# 必須看到 migration 資料夾（如 20251024082756_init/）
```

#### 2.2 建置映像

```bash
# 設定版本標籤（使用日期或版本號）
VERSION="v$(date +%Y%m%d-%H%M%S)"
IMAGE_TAG="acritpmcompany.azurecr.io/itpm-web:$VERSION"

# 建置 Docker 映像
docker build -t $IMAGE_TAG -f Dockerfile .

# 驗證建置成功
docker images | grep itpm-web
```

#### 2.3 驗證映像內容 ⚠️

**關鍵步驟 - 確保映像包含必要檔案：**

```bash
# 驗證 migrations 存在
docker run --rm $IMAGE_TAG ls /app/packages/db/prisma/migrations/
# 必須看到 migration 資料夾列表

# 驗證 Prisma Client 存在
docker run --rm $IMAGE_TAG ls /app/node_modules/.prisma/client/ | grep libquery_engine
# 必須看到: libquery_engine-linux-musl-openssl-3.0.x.so.node
```

### 階段 3: 推送和部署（10 分鐘）

#### 3.1 推送到 ACR

```bash
# 推送映像
docker push $IMAGE_TAG

# 同時標記為 latest
docker tag $IMAGE_TAG acritpmcompany.azurecr.io/itpm-web:latest
docker push acritpmcompany.azurecr.io/itpm-web:latest
```

#### 3.2 更新 App Service

```bash
# 更新容器配置
az webapp config container set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --container-image-name $IMAGE_TAG

# 重啟 App Service
az webapp restart \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N

echo "部署完成，等待 2-3 分鐘讓容器啟動..."
```

### 階段 4: 部署後驗證（5 分鐘）

#### 4.1 健康檢查

```bash
BASE_URL="https://app-itpm-company-dev-001.azurewebsites.net"

# 等待容器啟動
sleep 120

# 基礎健康檢查
curl -s "$BASE_URL/api/trpc/health.ping"
# 預期: {"result":{"data":{"json":{"message":"pong",...}}}}

# 資料庫連線檢查
curl -s "$BASE_URL/api/trpc/health.dbCheck"
# 預期: {"status":"healthy","database":"connected"}

# Schema 完整性檢查
curl -s "$BASE_URL/api/trpc/health.schemaCheck"
# 預期: 所有表格 exists: true
```

#### 4.2 頁面功能驗證 ⚠️

**關鍵步驟 - 必須測試所有主要頁面：**

```bash
echo "=== 驗證所有主要頁面 ==="

# MVP 頁面
curl -s -o /dev/null -w "登入頁面: %{http_code}\n" "$BASE_URL/zh-TW/login"
curl -s -o /dev/null -w "專案列表: %{http_code}\n" "$BASE_URL/zh-TW/projects"
curl -s -o /dev/null -w "用戶列表: %{http_code}\n" "$BASE_URL/zh-TW/users"
curl -s -o /dev/null -w "儀表板: %{http_code}\n" "$BASE_URL/zh-TW/dashboard"

# Post-MVP 頁面
curl -s -o /dev/null -w "OM費用: %{http_code}\n" "$BASE_URL/zh-TW/om-expenses"
curl -s -o /dev/null -w "OM摘要: %{http_code}\n" "$BASE_URL/zh-TW/om-summary"
curl -s -o /dev/null -w "費用分攤: %{http_code}\n" "$BASE_URL/zh-TW/charge-outs"

# 所有頁面應該返回 200 或 302（重定向到登入）
# 如果返回 500，請參閱 SITUATION-9 故障排查
```

---

## 🔑 環境變數配置

### 必要環境變數

```bash
az webapp config appsettings set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --settings \
    DATABASE_URL="postgresql://USER:PASSWORD@psql-itpm-company-dev-001.postgres.database.azure.com:5432/DATABASE?sslmode=require" \
    NEXTAUTH_SECRET="your-generated-secret-min-32-chars" \
    NEXTAUTH_URL="https://app-itpm-company-dev-001.azurewebsites.net" \
    NODE_ENV="production"
```

### Azure Storage 配置（文件上傳功能）

```bash
az webapp config appsettings set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --settings \
    AZURE_STORAGE_ACCOUNT_NAME="stitpmcompanydev001" \
    AZURE_STORAGE_ACCOUNT_KEY="<your-storage-account-key>" \
    AZURE_STORAGE_CONTAINER_QUOTES="quotes" \
    AZURE_STORAGE_CONTAINER_INVOICES="invoices"
```

### Azure AD B2C 配置（可選）

```bash
az webapp config appsettings set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --settings \
    AZURE_AD_B2C_TENANT_NAME="yourtenantname" \
    AZURE_AD_B2C_TENANT_ID="your-tenant-id" \
    AZURE_AD_B2C_CLIENT_ID="your-client-id" \
    AZURE_AD_B2C_CLIENT_SECRET="your-client-secret" \
    AZURE_AD_B2C_PRIMARY_USER_FLOW="B2C_1_signupsignin"
```

---

## 🔧 Health API 診斷工具

部署後可使用以下端點進行診斷和修復：

### ⭐ 推薦: 完整 Schema 同步機制 (2025-12-15 新增)

由於本地開發使用 `db:push` 而 Azure 使用 `migrate deploy`，Schema 經常不同步。
新增的完整 Schema 同步 API 一次性解決所有同步問題：

| 端點 | 方法 | 用途 |
|------|------|------|
| `health.fullSchemaCompare` | GET | **⭐ 完整對比所有 31 個表格和欄位** |
| `health.fullSchemaSync` | POST | **⭐ 一鍵修復所有缺失表格和欄位** |

**部署後標準 Schema 同步流程：**

```bash
BASE_URL="https://app-itpm-company-dev-001.azurewebsites.net"

# 1️⃣ 完整對比 Schema (檢查所有 31 個表格)
curl "$BASE_URL/api/trpc/health.fullSchemaCompare"
# 返回: status ("synced" | "out_of_sync"), 缺失表格/欄位列表, SQL 修復預覽

# 2️⃣ 如果有差異，執行一鍵完整同步
curl -X POST "$BASE_URL/api/trpc/health.fullSchemaSync"
# 自動執行 9 個修復階段:
# - Phase 1: 創建缺失表格 (Permission, RolePermission, UserPermission, etc.)
# - Phase 2: 修復 Project 表 (FEAT-001/006/010 共 19 欄位)
# - Phase 3: 修復 PurchaseOrder 表 (date, currencyId, approvedDate)
# - Phase 4: 修復 BudgetPool 表 (isActive, description, currencyId)
# - Phase 5: 修復 Expense 表 (7 欄位)
# - Phase 6: 修復 ExpenseItem 表 (categoryId, chargeOutOpCoId)
# - Phase 7: 修復 OMExpense 表 (FEAT-007 共 6 欄位)
# - Phase 8: 修復 OMExpenseItem 表 (lastFYActualExpense, isOngoing)
# - Phase 9: 創建必要索引

# 3️⃣ 驗證同步結果
curl "$BASE_URL/api/trpc/health.fullSchemaCompare"
# 應該返回 "status": "synced"
```

**詳細機制說明**: 請參閱 `claudedocs/SCHEMA-SYNC-MECHANISM.md`

### 診斷端點

| 端點 | 方法 | 用途 |
|------|------|------|
| `health.ping` | GET | 基礎健康檢查 |
| `health.dbCheck` | GET | 資料庫連線檢查 |
| `health.schemaCheck` | GET | 驗證所有表格是否存在 |
| `health.schemaCompare` | GET | 比較 schema.prisma vs 實際資料庫欄位 (舊版，部分表格) |
| `health.diagOmExpense` | GET | 診斷 OMExpense 相關表格和欄位 |
| `health.diagProjectSummary` | GET | 診斷 Project Summary 所需的表格和欄位 |

### 修復端點 (舊版，保留向後兼容)

| 端點 | 方法 | 用途 |
|------|------|------|
| `health.fixMigration` | POST | 修復卡住的 migration |
| `health.fixAllTables` | POST | 創建所有缺失表格 |
| `health.fixOmExpenseSchema` | POST | 修復 OMExpense 欄位 |
| `health.fixExpenseItemSchema` | POST | 修復 ExpenseItem 欄位 |
| `health.fixAllSchemaIssues` | POST | 修復部分 Schema 不同步問題 |
| `health.fixAllSchemaComplete` | POST | 修復部分 Schema (保留向後兼容) |
| `health.createOMExpenseItemTable` | POST | 創建 FEAT-007 OMExpenseItem 表格 |
| `health.fixFeat006AndFeat007Columns` | POST | 修復 FEAT-006/007 缺失欄位和表格 |

**舊版使用範例（保留向後兼容）：**

```bash
BASE_URL="https://app-itpm-company-dev-001.azurewebsites.net"

# 🔍 診斷：比較 schema.prisma 定義 vs 資料庫實際欄位
curl "$BASE_URL/api/trpc/health.schemaCompare"
# 返回：缺失欄位列表（如 ExpenseItem.chargeOutOpCoId）

# 🔧 一鍵修復所有 Schema 不同步問題
curl -X POST "$BASE_URL/api/trpc/health.fixAllSchemaIssues"

# 如果 schema 檢查顯示表格缺失
curl -X POST "$BASE_URL/api/trpc/health.fixAllTables"

# 如果 omExpense API 返回 500
curl -X POST "$BASE_URL/api/trpc/health.fixOmExpenseSchema"

# 如果 expense.create 返回 chargeOutOpCoId 欄位錯誤
curl -X POST "$BASE_URL/api/trpc/health.fixExpenseItemSchema"
```

### FEAT-006/007 專用修復流程 (2025-12-08+)

如果 `/projects`、`/om-expenses`、`/om-summary` 頁面出現 500 錯誤：

```bash
BASE_URL="https://app-itpm-company-dev-001.azurewebsites.net"

# 1️⃣ 先診斷問題
curl "$BASE_URL/api/trpc/health.diagOmExpense"
curl "$BASE_URL/api/trpc/health.diagProjectSummary"

# 2️⃣ 創建 FEAT-007 OMExpenseItem 表格（如果不存在）
curl -X POST "$BASE_URL/api/trpc/health.createOMExpenseItemTable"

# 3️⃣ 修復 FEAT-006/007 缺失欄位和 ProjectChargeOutOpCo 表格
curl -X POST "$BASE_URL/api/trpc/health.fixFeat006AndFeat007Columns"

# 修復內容：
# - Project: projectCategory, projectType, expenseType, chargeBackToOpCo,
#           chargeOutMethod, probability, team, personInCharge (8 欄位)
# - OMExpense: totalBudgetAmount, totalActualSpent, defaultOpCoId (3 欄位)
# - ProjectChargeOutOpCo: 整個表格 + 索引 + 外鍵約束
```

**詳細診斷指南：** 請參閱 SITUATION-9-AZURE-TROUBLESHOOT-COMPANY.md

---

## 🔄 回滾程序

### 快速回滾到上一版本

```bash
# 查看可用的映像標籤
az acr repository show-tags --name acritpmcompany --repository itpm-web --output table

# 回滾到指定版本
STABLE_VERSION="v20251202-previous"
az webapp config container set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --container-image-name acritpmcompany.azurecr.io/itpm-web:$STABLE_VERSION

# 重啟
az webapp restart \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N
```

---

## ⚠️ 關鍵提醒（基於實戰經驗）

### 1. .dockerignore 配置

```yaml
critical_check:
  問題: .dockerignore 包含 "**/migrations" 會導致所有 migration 被排除
  症狀: 容器啟動後報 "No migration found"，資料庫表格不存在
  預防: 確保 .dockerignore 中 migrations 相關行被註解
  驗證: docker run --rm IMAGE ls /app/packages/db/prisma/migrations/
```

### 2. Prisma OpenSSL 相容性

```yaml
critical_check:
  問題: Alpine 3.22+ 只有 OpenSSL 3.0，Prisma 預設用 1.1
  症狀: Error loading shared library libssl.so.1.1
  預防:
    - schema.prisma 必須包含 binaryTargets = ["native", "linux-musl-openssl-3.0.x"]
    - Dockerfile 必須設置 PRISMA_QUERY_ENGINE_LIBRARY 環境變數
```

### 3. 部署後驗證

```yaml
critical_check:
  問題: 只測試登入頁面，忽略其他功能頁面
  症狀: 登入正常但 /om-expenses 等頁面返回 500
  預防: 部署後必須測試所有主要頁面（見 4.2 節）
  原因: Post-MVP 功能依賴額外的資料庫表格
```

### 4. Migration 執行

```yaml
critical_check:
  問題: Migration 執行中斷，finishedAt 為 null
  症狀: schema.check 顯示表格缺失，但 migrations 記錄存在
  預防: 使用 health.fixMigration 或 health.fixAllTables API 修復
```

---

## 📁 相關檔案參考

```
專案根目錄/
├── Dockerfile                    # Docker 建置配置
├── docker-entrypoint.sh          # 容器啟動腳本
├── .dockerignore                 # ⚠️ 確保不排除 migrations
├── packages/
│   └── db/
│       └── prisma/
│           ├── schema.prisma     # ⚠️ 確保 binaryTargets 正確
│           └── migrations/       # ⚠️ 必須包含在 Docker image 中
└── packages/
    └── api/
        └── src/
            └── routers/
                └── health.ts     # Health API 診斷端點
```

---

## ✅ 部署完成檢查清單

```yaml
部署後確認:
  基礎檢查:
    - [ ] health.ping 返回 pong
    - [ ] health.dbCheck 返回 healthy
    - [ ] health.schemaCheck 所有表格存在

  頁面測試:
    - [ ] /zh-TW/login 可以訪問
    - [ ] /zh-TW/projects 可以訪問
    - [ ] /zh-TW/users 可以訪問
    - [ ] /zh-TW/om-expenses 可以訪問
    - [ ] /zh-TW/om-summary 可以訪問

  功能測試:
    - [ ] 可以登入系統
    - [ ] 可以查看專案列表
    - [ ] 可以上傳文件（如果配置了 Azure Storage）

部署後通知:
  - [ ] 通知團隊部署完成
  - [ ] 更新部署記錄
  - [ ] 監控 15 分鐘穩定性
```

---

## 📞 問題處理

如果部署過程中遇到任何問題：

1. **首先查閱**: `SITUATION-9-AZURE-TROUBLESHOOT-COMPANY.md`
2. **常見問題快速索引**:
   - 500 錯誤 → SITUATION-9 問題 0.1, 0.2, 0.12
   - Migration 問題 → SITUATION-9 問題 0, 0.10
   - Prisma 初始化失敗 → SITUATION-9 問題 0.8, 0.9
   - 文件上傳失敗 → SITUATION-9 問題 0.11
3. **升級路徑**:
   - 30 分鐘內無法解決 → 聯繫 DevOps Team
   - 權限問題 → 聯繫 Azure Administrator

---

**版本**: 2.2.0 **最後更新**: 2025-12-15 **維護者**: DevOps Team + Azure Administrator

**更新記錄**:

- v2.2.0 (2025-12-15): **完整 Schema 同步機制**
  - 🆕 新增 `health.fullSchemaCompare` API - 完整對比所有 31 個表格
  - 🆕 新增 `health.fullSchemaSync` API - 一鍵修復所有 Schema 差異
  - 📝 新增 "推薦: 完整 Schema 同步機制" 章節
  - 📝 參考文檔: `claudedocs/SCHEMA-SYNC-MECHANISM.md`
  - ⚙️ 新增 `schemaDefinition.ts` 作為唯一真相來源
  - 🔧 9 個修復階段覆蓋所有已知 Schema 差異
- v2.1.0 (2025-12-08): **FEAT-006/007 部署經驗更新**
  - 🚨 新增關鍵警告：db push vs migration 差異導致的 Schema 不同步問題
  - 新增診斷端點：health.diagOmExpense, health.diagProjectSummary
  - 新增修復端點：health.createOMExpenseItemTable, health.fixFeat006AndFeat007Columns
  - 新增 FEAT-006/007 專用修復流程章節
  - 記錄 Project 8 欄位、OMExpense 3 欄位、ProjectChargeOutOpCo 表格修復經驗
- v2.0.0 (2025-12-03): **重大重組**
  - 將文檔精簡為「部署流程指南」
  - 移除所有問題排查歷史到 SITUATION-9
  - 添加關鍵提醒章節（基於實戰經驗）
  - 簡化部署步驟為 4 個階段
  - 添加完整的部署後驗證清單
  - 行數從 2,333 行精簡到 ~500 行
- v1.8.0 (2025-12-03): 修復 omExpense API 500 錯誤
- v1.7.0 (2025-12-03): 新增診斷端點
- v1.6.0 (2025-12-03): Docker 建置和 Migration 診斷工具
- v1.5.0 (2025-12-03): 添加 Post-MVP 表格缺失問題
