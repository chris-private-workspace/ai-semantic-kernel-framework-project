# SITUATION-9: Azure 公司環境問題排查指引

**用途**: 當**公司 Azure 訂閱**部署或運行過程中遇到問題時，使用此指引進行企業級故障診斷和規範化問題解決。

**目標環境**: 公司 Azure 訂閱（Staging、Production、正式環境）

**觸發情境**:

- 生產環境故障
- 部署到公司環境失敗
- 企業級權限問題
- 網路配置問題
- 合規性相關問題
- 需要與 Azure Administrator 協作

**特點**: 企業級故障排查，結構化升級流程，合規性優先

---

## 🎯 公司環境問題排查原則

### 1. 安全和合規優先

```yaml
enterprise_troubleshooting:
  - ✅ 遵守變更管理流程
  - ✅ 記錄所有診斷操作
  - ✅ 避免破壞性操作
  - ✅ 保護生產數據
  - ✅ 及時升級和通知
  - ⚠️  不得隨意修改生產配置
```

### 2. 結構化升級路徑

```yaml
escalation_levels:
  Level_1_Self_Diagnosis: 0-30 分鐘
    - 查看監控和告警
    - 檢查日誌
    - 執行基礎診斷腳本
    - 查閱文檔

  Level_2_DevOps_Team: 30-60 分鐘
    - 聯繫內部 DevOps
    - Slack #devops-support
    - 共享診斷結果

  Level_3_Azure_Administrator: 1-2 小時
    - 權限相關問題
    - 網路配置問題
    - 訂閱配額問題

  Level_4_Microsoft_Support: 嚴重故障
    - 平台級別問題
    - 需要 Microsoft 介入
```

### 3. 變更管理

```yaml
change_management:
  診斷操作:
    - 只讀操作: 無需審批
    - 重啟服務: 需要團隊知情
    - 配置變更: 需要 CAB 批准
    - 回滾操作: 需要緊急批准

  記錄要求:
    - 記錄問題症狀
    - 記錄診斷步驟
    - 記錄修復操作
    - 更新故障知識庫
```

---

## 🔍 企業級問題診斷

### 🔴 問題 0: .dockerignore 排除 Migrations（2025-11-26 關鍵發現）

> ⚠️ **高頻致命問題**：這是公司環境部署最常見的根本原因之一！

#### 症狀

```
❌ 用戶註冊返回 500 Internal Server Error
❌ 容器日誌顯示 "No migration found in prisma/migrations"
❌ API 返回 "The table public.Role does not exist"
❌ API 返回 "The table public.Currency does not exist"
❌ Seed 執行失敗
```

#### 根本原因分析

```yaml
root_cause_chain:
  level_1: .dockerignore 包含 "**/migrations" 規則
  level_2: Docker build context 排除 migrations 資料夾
  level_3: Container 中 /app/packages/db/prisma/migrations/ 為空
  level_4: startup.sh 執行 "prisma migrate deploy" 報告 "No migration found"
  level_5: 資料庫 Schema 未建立（沒有 Role、Currency 等表）
  level_6: Seed 無法執行（依賴表結構）
  level_7: 用戶註冊時 roleId 外鍵約束失敗

為什麼其他電腦可能沒問題:
  - 可能使用不同版本的 .dockerignore
  - 可能使用不同的 Dockerfile 位置
  - 可能使用不同的部署方式（非 Docker）
```

#### 快速診斷

```bash
# 1. 檢查 .dockerignore 是否排除 migrations
grep -n "migrations" .dockerignore
# 如果看到 "**/migrations" 未被註解，這就是問題！

# 2. 驗證 Docker image 中 migrations 是否存在
docker run --rm acritpmcompany.azurecr.io/itpm-web:latest \
  ls -la /app/packages/db/prisma/migrations/
# 如果顯示空目錄或找不到，這就是問題！

# 3. 查看容器日誌中的 migration 訊息
az webapp log tail --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N | grep -i "migration"
# 應該看到 "X migrations found" 而非 "No migration found"
```

#### 解決方案

**步驟 1: 修改 .dockerignore**

```bash
# 編輯 .dockerignore，註解掉 migrations 排除規則
# 找到這行:
**/migrations
# 改為:
# **/migrations  <-- REMOVED: migrations are required for prisma migrate deploy
```

**步驟 2: 確認 .gitignore 允許 migration SQL**

```bash
# 確保 .gitignore 不排除 Prisma migration SQL
# 添加這行:
!packages/db/prisma/migrations/**/*.sql
```

**步驟 3: 重建並推送 Docker image**

```bash
# 重建
docker build -f docker/Dockerfile -t acritpmcompany.azurecr.io/itpm-web:latest .

# 驗證 migrations 存在
docker run --rm acritpmcompany.azurecr.io/itpm-web:latest \
  ls -la /app/packages/db/prisma/migrations/
# 應該看到: 20251024082756_init/, 20251111065801_new/, 20251126100000_add_currency/

# 推送
docker push acritpmcompany.azurecr.io/itpm-web:latest

# 重啟 App Service
az webapp restart --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N
```

**步驟 4: 等待 migration 執行完成**

```bash
# 等待 2-3 分鐘，然後查看日誌確認 migration 成功
az webapp log tail --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N | grep -i "migration\|ITPM"

# 預期看到:
# 🚀 ITPM 應用程式啟動
# 📦 執行 Prisma 資料庫遷移...
# 3 migrations found in prisma/migrations
# Applying migration `20251024082756_init`
# Applying migration `20251111065801_new`
# Applying migration `20251126100000_add_currency`
# All migrations have been successfully applied.
```

**步驟 5: 執行 Seed**

```bash
# 使用 curl 或 PowerShell 執行 seed
curl -X POST "https://app-itpm-company-dev-001.azurewebsites.net/api/admin/seed" \
  -H "Authorization: Bearer <NEXTAUTH_SECRET>" \
  -H "Content-Type: application/json"

# 預期成功響應:
# {"success":true,"results":{"roles":{"processed":3},"currencies":{"processed":6}}}
```

**步驟 6: 驗證修復**

```bash
# 測試用戶註冊
curl -X POST "https://app-itpm-company-dev-001.azurewebsites.net/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","name":"Test User"}'

# 預期成功響應:
# {"success":true,"message":"註冊成功","user":{...}}
```

#### 預防措施

```yaml
prevention_checklist:
  - [ ] 部署前檢查 .dockerignore 不排除 migrations
  - [ ] CI/CD pipeline 中添加 migrations 存在性驗證
  - [ ] 容器啟動後立即檢查日誌確認 migration 執行
  - [ ] 文檔化這個問題供團隊參考

recommended_ci_check:
  # 在 GitHub Actions 中添加驗證步驟
  - name: Verify migrations exist in Docker image
    run: |
      docker run --rm $IMAGE_NAME ls /app/packages/db/prisma/migrations/ | grep -q "migration.sql"
```

**詳細參考**: `azure/docs/DEPLOYMENT-TROUBLESHOOTING.md`

---

### 🔴 問題 0.1: FEAT-001 Schema 不匹配 - Project 欄位缺失（2025-12-02 發現）

> ⚠️ **高頻致命問題**：schema.prisma 定義了新欄位但 migration 未包含，導致特定頁面 500 錯誤！

#### 症狀

```
❌ /zh-TW/projects 頁面返回 500 Internal Server Error
❌ API project.getAll 返回 500 錯誤
❌ 其他頁面（如 /users、/dashboard）可以正常訪問
❌ 登入功能正常，僅特定 API 出錯
❌ 容器日誌可能顯示 Prisma 查詢錯誤或 "column does not exist"
```

#### 根本原因分析

```yaml
root_cause_chain:
  level_1: schema.prisma 中 Project model 定義了 FEAT-001 新欄位
  level_2: 現有的 migration SQL 只添加了 currencyId，缺少其他 3 個欄位
  level_3: 資料庫 Project 表缺少 projectCode, globalFlag, priority 欄位
  level_4: Prisma Client 生成的 SQL 嘗試 SELECT 不存在的欄位
  level_5: PostgreSQL 返回 "column projectCode does not exist" 錯誤
  level_6: tRPC 將錯誤包裝為 500 Internal Server Error

schema_mismatch_details:
  schema.prisma_Project_model:
    - projectCode String @unique  # 必填，缺失 ❌
    - globalFlag String @default("Region")  # 必填，缺失 ❌
    - priority String @default("Medium")  # 必填，缺失 ❌
    - currencyId String?  # 可選，已存在 ✅

  migration_20251126100000_add_currency:
    - ALTER TABLE "Project" ADD COLUMN "currencyId" TEXT  # ✅ 已添加
    # projectCode, globalFlag, priority 都未添加！

why_only_projects_affected:
  - User 表沒有新增欄位，所以 /users 正常
  - Dashboard 可能只用聚合查詢，不涉及缺失欄位
  - Project 相關 API 都會觸發完整 SELECT，包含缺失欄位
```

#### 快速診斷

```bash
# 1. 確認問題範圍 - 比較不同 API 的響應
# 測試 user.getAll（應該成功）
curl -s "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/user.getAll" \
  -H "Cookie: <your-session-cookie>" | head -c 200

# 測試 project.getAll（應該失敗）
curl -s "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/project.getAll" \
  -H "Cookie: <your-session-cookie>" | head -c 200

# 2. 檢查 migrations 是否包含 FEAT-001 欄位
cat packages/db/prisma/migrations/*/migration.sql | grep -E "projectCode|globalFlag|priority"
# 如果沒有輸出，說明 migration 缺少這些欄位

# 3. 檢查 schema.prisma 中 Project model 的 FEAT-001 欄位
grep -A 5 "FEAT-001" packages/db/prisma/schema.prisma
# 應該看到 projectCode, globalFlag, priority, currencyId

# 4. 查看容器日誌中的錯誤詳情
az webapp log tail --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N 2>&1 | grep -i "error\|column\|prisma"
```

#### 解決方案

**方案 A: 創建補充 migration（推薦）**

```bash
# 1. 創建新的 migration 目錄
mkdir -p packages/db/prisma/migrations/20251202100000_add_feat001_project_fields

# 2. 創建 migration.sql
cat > packages/db/prisma/migrations/20251202100000_add_feat001_project_fields/migration.sql << 'EOF'
-- FEAT-001: 添加缺失的 Project 欄位 (projectCode, globalFlag, priority)

-- 添加欄位（先設為 nullable 以支援現有資料）
ALTER TABLE "Project" ADD COLUMN IF NOT EXISTS "projectCode" TEXT;
ALTER TABLE "Project" ADD COLUMN IF NOT EXISTS "globalFlag" TEXT DEFAULT 'Region';
ALTER TABLE "Project" ADD COLUMN IF NOT EXISTS "priority" TEXT DEFAULT 'Medium';

-- 為現有記錄生成臨時 projectCode（使用 UUID 前 8 位）
UPDATE "Project" SET "projectCode" = 'PRJ-' || SUBSTRING(id::text, 1, 8) WHERE "projectCode" IS NULL;

-- 設置 NOT NULL 約束
ALTER TABLE "Project" ALTER COLUMN "projectCode" SET NOT NULL;
ALTER TABLE "Project" ALTER COLUMN "globalFlag" SET NOT NULL;
ALTER TABLE "Project" ALTER COLUMN "priority" SET NOT NULL;

-- 添加唯一約束
CREATE UNIQUE INDEX IF NOT EXISTS "Project_projectCode_key" ON "Project"("projectCode");

-- 添加索引
CREATE INDEX IF NOT EXISTS "Project_projectCode_idx" ON "Project"("projectCode");
CREATE INDEX IF NOT EXISTS "Project_globalFlag_idx" ON "Project"("globalFlag");
CREATE INDEX IF NOT EXISTS "Project_priority_idx" ON "Project"("priority");
EOF

# 3. 重建 Docker image
docker build -f docker/Dockerfile -t acritpmcompany.azurecr.io/itpm-web:v7-fix-feat001 .

# 4. 驗證 migration 存在於 image 中
docker run --rm acritpmcompany.azurecr.io/itpm-web:v7-fix-feat001 \
  ls -la /app/packages/db/prisma/migrations/

# 5. 推送並部署
docker push acritpmcompany.azurecr.io/itpm-web:v7-fix-feat001
az webapp config container set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --docker-custom-image-name acritpmcompany.azurecr.io/itpm-web:v7-fix-feat001
az webapp restart --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N
```

**方案 B: 直接執行 SQL（緊急修復）**

```bash
# 如果需要緊急修復且無法重新部署，可以直接連接資料庫執行 SQL
# 需要 Azure PostgreSQL 訪問權限

# 使用 psql 或 Azure Data Studio 連接
psql "postgresql://itpmadmin:password@psql-itpm-company-dev-001.postgres.database.azure.com:5432/itpm_dev?sslmode=require"

# 執行 SQL（同上面的 migration.sql 內容）
```

#### 驗證修復

```bash
# 1. 等待容器重啟（2-3 分鐘）
sleep 180

# 2. 查看日誌確認 migration 執行
az webapp log tail --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N 2>&1 | grep -i "migration"
# 應該看到 "Applying migration 20251202100000_add_feat001_project_fields"

# 3. 測試 /projects 頁面
curl -s -o /dev/null -w "%{http_code}" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/projects"
# 應該返回 200 或 302（未登入時重定向）

# 4. 測試 API
curl -s "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/project.getAll" \
  -H "Cookie: <your-session-cookie>"
# 應該返回 JSON 數據，而非 500 錯誤
```

#### 預防措施

```yaml
prevention_checklist:
  開發流程:
    - [ ] 每次修改 schema.prisma 後，執行 `pnpm db:migrate` 創建 migration
    - [ ] 不要手動修改 schema.prisma 而跳過 migration
    - [ ] 在 PR 中確認 schema 變更有對應的 migration

  部署前驗證:
    - [ ] 比較 schema.prisma 欄位和 migration SQL 的一致性
    - [ ] 在本地 Docker 環境測試完整部署流程
    - [ ] 驗證所有核心 API 端點（project, user, budget 等）

  CI/CD 強化:
    - name: Validate schema-migration consistency
      run: |
        # 檢查 schema.prisma 中的 model 欄位是否都有對應的 migration
        # 這個腳本需要自行實現
        pnpm prisma migrate diff --from-empty --to-schema-datamodel=./packages/db/prisma/schema.prisma
```

---

### 🔴 問題 0.2: Post-MVP 表格缺失（2025-12-03 發現）

> ⚠️ **高頻致命問題**：Azure 資料庫缺少 Post-MVP 階段的表格，導致特定功能頁面 500 錯誤！

#### 症狀

```
❌ /zh-TW/om-expenses 頁面返回 500 Internal Server Error
❌ /zh-TW/om-summary 頁面返回 500 Internal Server Error
❌ /zh-TW/charge-outs 頁面返回 500 Internal Server Error
❌ API omExpense.getCategories、omExpense.getAll 返回 500 錯誤
❌ 其他頁面（如 /projects、/users、/login）可以正常訪問
❌ 登入功能正常，僅特定 Post-MVP 功能出錯
```

#### 根本原因分析

```yaml
root_cause_chain:
  level_1: schema.prisma 定義了 Post-MVP 新表格（共 8 個）
  level_2: 但這些 migration 可能未被執行或資料庫中缺少這些表格
  level_3: Azure 資料庫只有 MVP 階段的表格
  level_4: omExpense.getCategories API 查詢 ExpenseCategory 表
  level_5: PostgreSQL 返回 "relation ExpenseCategory does not exist" 錯誤
  level_6: tRPC 將錯誤包裝為 500 Internal Server Error

missing_postmvp_tables:
  - ExpenseCategory  # 費用類別 - om-expenses 核心依賴
  - OperatingCompany  # 營運公司
  - OMExpense  # 營運費用
  - OMExpenseMonthly  # 月度營運費用
  - ChargeOut  # 費用分攤
  - ChargeOutItem  # 分攤明細
  - PurchaseOrderItem  # 採購單明細
  - ExpenseItem  # 費用明細

why_specific_pages_fail:
  - /om-expenses 依賴 ExpenseCategory 表 → 表不存在 → 500
  - /om-summary 依賴 OMExpense 和 ExpenseCategory 表 → 500
  - /projects 使用 MVP 階段的 Project 表 → 正常
  - /users 使用 MVP 階段的 User 表 → 正常
```

#### 快速診斷

```bash
# 1. 確認問題範圍 - 測試 MVP vs Post-MVP 頁面
echo "=== MVP 頁面（應該正常）==="
curl -s -o /dev/null -w "projects: %{http_code}\n" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/projects"
curl -s -o /dev/null -w "users: %{http_code}\n" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/users"

echo "=== Post-MVP 頁面（可能 500）==="
curl -s -o /dev/null -w "om-expenses: %{http_code}\n" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/om-expenses"
curl -s -o /dev/null -w "om-summary: %{http_code}\n" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/om-summary"
curl -s -o /dev/null -w "charge-outs: %{http_code}\n" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/charge-outs"

# 2. 檢查 migrations 是否包含 Post-MVP 表格
echo "=== 檢查 migration SQL ==="
cat packages/db/prisma/migrations/*/migration.sql | grep -E "CREATE TABLE.*ExpenseCategory|CREATE TABLE.*OperatingCompany|CREATE TABLE.*OMExpense"
# 如果沒有輸出，說明 migration 缺少這些表格

# 3. 統計 schema.prisma 中的 model 數量 vs migration 中的 CREATE TABLE 數量
echo "=== Schema vs Migration 表格數量 ==="
SCHEMA_MODELS=$(grep "^model " packages/db/prisma/schema.prisma | wc -l)
MIGRATION_TABLES=$(grep -E "CREATE TABLE" packages/db/prisma/migrations/*/migration.sql | wc -l)
echo "Schema models: $SCHEMA_MODELS"
echo "Migration CREATE TABLE: $MIGRATION_TABLES"
# 如果 SCHEMA_MODELS > MIGRATION_TABLES，說明有表格缺失

# 4. 查看容器日誌中的錯誤
az webapp log tail --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N 2>&1 | grep -i "relation.*does not exist\|error"
```

#### 解決方案

**方案 A: 創建 Post-MVP 表格 migration（推薦）**

```bash
# 1. 創建新的 migration 目錄
mkdir -p packages/db/prisma/migrations/20251202110000_add_postmvp_tables

# 2. 創建 idempotent migration SQL
# 參見 SITUATION-7-AZURE-DEPLOY-COMPANY.md「問題 0.7」章節的完整 SQL

# 3. 重建並部署 Docker image
docker build -f docker/Dockerfile -t acritpmcompany.azurecr.io/itpm-web:v8-postmvp-tables .

# 4. 驗證 migration 存在於 image 中
docker run --rm acritpmcompany.azurecr.io/itpm-web:v8-postmvp-tables \
  ls -la /app/packages/db/prisma/migrations/

# 5. 推送並部署
az acr login --name acritpmcompany
docker push acritpmcompany.azurecr.io/itpm-web:v8-postmvp-tables

az webapp config container set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --container-image-name acritpmcompany.azurecr.io/itpm-web:v8-postmvp-tables

az webapp restart --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N
```

**方案 B: 直接執行 SQL（緊急修復）**

```bash
# 如果需要緊急修復，可以直接連接資料庫執行 SQL
# 使用 psql 或 Azure Data Studio 連接
psql "postgresql://itpmadmin:password@psql-itpm-company-dev-001.postgres.database.azure.com:5432/itpm_dev?sslmode=require"

# 執行 CREATE TABLE IF NOT EXISTS 語句（參見完整 migration SQL）
```

#### 驗證修復

```bash
# 1. 等待容器重啟（2-3 分鐘）
sleep 180

# 2. 查看日誌確認 migration 執行
az webapp log tail --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N 2>&1 | grep -i "migration"

# 3. 測試所有 Post-MVP 頁面
echo "=== 驗證 Post-MVP 頁面修復 ==="
curl -s -o /dev/null -w "om-expenses: %{http_code}\n" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/om-expenses"
curl -s -o /dev/null -w "om-summary: %{http_code}\n" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/om-summary"
curl -s -o /dev/null -w "charge-outs: %{http_code}\n" "https://app-itpm-company-dev-001.azurewebsites.net/zh-TW/charge-outs"
# 所有頁面應該返回 200
```

#### 預防措施

```yaml
prevention_checklist:
  部署前必檢:
    - [ ] 比較 schema.prisma model 數量和 migration CREATE TABLE 數量
    - [ ] 確保所有 Post-MVP 表格都有對應的 migration SQL
    - [ ] 在本地 Docker 環境先測試完整部署流程

  部署後必檢:
    - [ ] 不能只測試登入頁面就認為部署成功
    - [ ] 必須測試所有主要功能頁面：
        - /projects、/users（MVP）
        - /om-expenses、/om-summary、/charge-outs（Post-MVP）
    - [ ] 使用自動化腳本測試所有頁面 HTTP 狀態碼

  Idempotent migration 最佳實踐:
    - 使用 CREATE TABLE IF NOT EXISTS
    - 使用 CREATE INDEX IF NOT EXISTS
    - 使用 ON CONFLICT DO NOTHING 處理 seed 數據
    - 允許 migration 重複執行而不出錯
```

**詳細參考**: SITUATION-7-AZURE-DEPLOY-COMPANY.md「問題 0.7」章節

---

### 問題 0.5: Migration SQL 檔案缺失（Currency 表不存在）

> ⚠️ **次要問題**：當 schema.prisma 有新 model 但沒有對應 migration 時發生

#### 症狀

```
❌ Migration 報告成功執行
❌ 但 Seed 時報錯: "The table public.Currency does not exist"
❌ 日誌顯示 "2 migrations found" 但實際需要 3 個
```

#### 根本原因

```yaml
cause: schema.prisma 中新增了 Currency model，但沒有對應的 migration SQL

missing_relationship:
  schema_prisma_has:
    - model Currency { ... }
    - BudgetPool.currencyId -> Currency
    - Project.currencyId -> Currency

  migrations_folder_has:
    - 20251024082756_init (不含 Currency)
    - 20251111065801_new (不含 Currency)
    # 缺少 Currency migration!
```

#### 解決方案

```bash
# 1. 創建新的 migration
mkdir -p packages/db/prisma/migrations/20251126100000_add_currency

# 2. 創建 migration.sql（參見 azure/docs/DEPLOYMENT-TROUBLESHOOTING.md 中的完整 SQL）

# 3. 如果 schema 中欄位是必填但資料庫有現有資料，改為 nullable
# 例如: BudgetPool.currencyId String -> String?

# 4. 重建並部署
docker build -f docker/Dockerfile -t acritpmcompany.azurecr.io/itpm-web:latest .
docker push acritpmcompany.azurecr.io/itpm-web:latest
az webapp restart --name app-itpm-company-dev-001 --resource-group RG-RCITest-RAPO-N8N
```

---

### 問題 0.5b: Docker 建置失敗 - Prisma 初始化問題（實戰經驗）

> ⚠️ **高頻問題**：這是首次部署時遇到的主要障礙，記錄詳細解決方案。

#### 症狀

```
❌ docker build 失敗
❌ PrismaClientInitializationError: Prisma Client could not locate the Query Engine
❌ Error: ENOENT: no such file or directory, open '.../libquery_engine-linux-musl-openssl-3.0.x.so.node'
❌ Next.js build 階段嘗試連接資料庫
```

#### 根本原因分析

```yaml
root_cause:
  issue: Prisma Client 在 import 時就嘗試初始化
  why_fails:
    - Docker 建置階段沒有資料庫連接
    - Next.js build 會預渲染 API routes
    - Alpine Linux 需要特定的 binary target

  affected_files:
    - packages/db/src/index.ts
    - packages/db/prisma/schema.prisma
    - apps/web/src/app/api/**/route.ts
```

#### 解決方案

**步驟 1: 實作 Prisma Proxy Lazy Loading**

```typescript
// packages/db/src/index.ts
import { PrismaClient } from '@prisma/client';

let prismaInstance: PrismaClient | null = null;

function getPrisma(): PrismaClient {
  if (!prismaInstance) {
    prismaInstance = new PrismaClient();
  }
  return prismaInstance;
}

// 使用 Proxy 實現真正的 lazy loading
// 只有在實際調用方法時才會初始化 PrismaClient
export const prisma = new Proxy({} as PrismaClient, {
  get(_target, prop: keyof PrismaClient) {
    return getPrisma()[prop];
  },
});

export * from '@prisma/client';
```

**步驟 2: 添加 Alpine Linux Binary Target**

```prisma
// packages/db/prisma/schema.prisma
generator client {
  provider      = "prisma-client-js"
  binaryTargets = ["native", "linux-musl-openssl-3.0.x"]
}
```

**步驟 3: 防止 API Routes 預渲染**

```typescript
// 在所有使用資料庫的 API route 文件開頭添加
export const dynamic = 'force-dynamic';
```

需要修改的檔案清單：

- `apps/web/src/app/api/auth/[...nextauth]/route.ts`
- `apps/web/src/app/api/projects/route.ts`
- `apps/web/src/app/api/projects/[id]/route.ts`
- `apps/web/src/app/api/health/route.ts`

**步驟 4: Dockerfile 配置**

```dockerfile
# 確保建置階段有佔位符 DATABASE_URL
ENV DATABASE_URL="postgresql://placeholder:placeholder@placeholder:5432/placeholder"
ENV SKIP_ENV_VALIDATION=1

# 確保 Prisma 生成在正確位置
RUN pnpm prisma generate --schema=./packages/db/prisma/schema.prisma
```

#### 驗證修復

```bash
# 重新建置 Docker 映像
docker build --no-cache -t acritpmcompany.azurecr.io/itpm-web:latest -f Dockerfile .

# 確認建置成功後推送
docker push acritpmcompany.azurecr.io/itpm-web:latest
```

---

### 問題 0.5: 資源創建權限被拒（實戰經驗）

#### 症狀

```
❌ Authorization failed for action 'Microsoft.KeyVault/vaults/write'
❌ The subscription is not registered to use namespace 'Microsoft.XXX'
❌ 無法創建某些 Azure 資源
```

#### 診斷步驟

```bash
# 檢查當前帳號權限
az role assignment list \
  --assignee $(az account show --query user.name -o tsv) \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table

# 檢查訂閱註冊的資源提供者
az provider list --query "[?registrationState=='Registered'].namespace" -o table
```

#### 解決方案：替代方案

**Key Vault 替代方案 - 直接使用 App Settings**

```bash
# 當無法創建 Key Vault 時，直接配置環境變數
az webapp config appsettings set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --settings \
    DATABASE_URL="postgresql://adminuser:password@psql-itpm-company-dev-001.postgres.database.azure.com:5432/itpm?sslmode=require" \
    NEXTAUTH_SECRET="your-generated-secret" \
    NEXTAUTH_URL="https://app-itpm-company-dev-001.azurewebsites.net" \
    NODE_ENV="production"
```

**注意事項**：

- App Settings 中的值會顯示在 Azure Portal 中
- 對於高度敏感的生產環境，仍應申請 Key Vault 權限
- 可以聯繫 Azure Administrator 申請：
  - `Microsoft.KeyVault/vaults/write` 權限
  - 或請求在共用 Key Vault 中創建 secrets

---

### 🔴 問題 0.8: Prisma Client Docker 生成失敗（2025-12-03 發現）

> ⚠️ **致命問題**：Docker 建置時 `pnpm --filter db run db:generate` 失敗導致 Prisma Client 不完整！

#### 症狀

```
❌ Docker build 失敗或成功但運行時錯誤
❌ PrismaClientInitializationError: Prisma Client could not locate the Query Engine
❌ Error: ENOENT: no such file or directory, open '.../libquery_engine-linux-musl-openssl-3.0.x.so.node'
❌ pnpm filter 命令在 Docker 中執行失敗
```

#### 根本原因

```yaml
root_cause_chain:
  level_1: Dockerfile 使用 pnpm --filter db run db:generate
  level_2: pnpm filter 在多階段 Docker build 中工作不穩定
  level_3: Prisma Client 生成不完整或完全失敗
  level_4: 運行時找不到 Query Engine binary
  level_5: 所有資料庫操作失敗
```

#### 解決方案

**修改 Dockerfile，使用 npx 直接執行**：

```dockerfile
# 舊的方式（不穩定）
# RUN pnpm --filter db run db:generate

# 新的方式（推薦）
RUN cd packages/db && npx prisma generate --schema=./prisma/schema.prisma
```

**驗證步驟**：

```bash
# 建置後驗證 Prisma Client 存在
docker run --rm acritpmcompany.azurecr.io/itpm-web:latest \
  ls -la /app/node_modules/.prisma/client/

# 應該看到:
# - libquery_engine-linux-musl-openssl-3.0.x.so.node
# - schema.prisma
# - index.js
```

---

### 🔴 問題 0.9: OpenSSL 3.0 相容性問題（2025-12-03 發現）

> ⚠️ **致命問題**：Alpine Linux 3.22 移除了 OpenSSL 1.1，導致 Prisma Query Engine 無法載入！

#### 症狀

```
❌ Error loading shared library libssl.so.1.1
❌ Prisma Client 初始化失敗
❌ 資料庫連接全部失敗
❌ health.dbCheck 返回 unhealthy
```

#### 根本原因

```yaml
root_cause:
  issue: Prisma 預設嘗試載入 OpenSSL 1.1 版本的 Query Engine
  alpine_change: Alpine Linux 3.22+ 只提供 OpenSSL 3.0
  mismatch: libquery_engine-linux-musl.so.node 嘗試載入 libssl.so.1.1
  result: 動態連結失敗，Prisma 無法初始化
```

#### 解決方案

**步驟 1: 確保 schema.prisma 有正確的 binaryTargets**

```prisma
// packages/db/prisma/schema.prisma
generator client {
  provider      = "prisma-client-js"
  binaryTargets = ["native", "linux-musl-openssl-3.0.x"]  // 關鍵！
}
```

**步驟 2: 在 Dockerfile 設置環境變數指向正確的 Engine**

```dockerfile
# 在 runner stage 添加
ENV PRISMA_QUERY_ENGINE_LIBRARY=/app/node_modules/.prisma/client/libquery_engine-linux-musl-openssl-3.0.x.so.node
```

**步驟 3: 複製正確的 Engine 文件**

```dockerfile
# 確保複製 OpenSSL 3.0 版本的 engine
COPY --from=builder --chown=nextjs:nodejs \
  /app/node_modules/.pnpm/@prisma+client@5.22.0_prisma@5.22.0/node_modules/.prisma \
  ./node_modules/.prisma
```

**驗證步驟**：

```bash
# 檢查 engine 文件是否存在
docker run --rm acritpmcompany.azurecr.io/itpm-web:latest \
  ls /app/node_modules/.prisma/client/ | grep libquery_engine

# 應該看到: libquery_engine-linux-musl-openssl-3.0.x.so.node
```

---

### 🔴 問題 0.10: Migration 卡住（finishedAt 為 null）（2025-12-03 發現）

> ⚠️ **致命問題**：Migration 記錄顯示已執行但 finishedAt 為 null，導致表格缺失！

#### 症狀

```
❌ health.schemaCheck 顯示部分表格缺失
❌ _prisma_migrations 表有記錄但 finished_at 為 NULL
❌ 應用程式部分功能 500 錯誤
❌ Prisma 認為 migration 仍在進行中，不會重新執行
```

#### 根本原因

```yaml
root_cause_chain:
  level_1: Migration 執行中斷（容器重啟、超時、錯誤）
  level_2: _prisma_migrations 記錄的 finished_at 為 NULL
  level_3: Prisma migrate deploy 認為 migration 仍在進行
  level_4: 不會重新執行未完成的 migration
  level_5: 表格沒有被創建
```

#### 快速診斷

```bash
# 使用 Health API 檢查
curl "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/health.schemaCheck"

# 返回示例（問題狀態）：
# {
#   "ExpenseCategory": { "exists": false },
#   "OMExpense": { "exists": false },
#   "_prisma_migrations": { "hasPendingMigration": true }
# }
```

#### 解決方案

**方案 A: 使用 Health API 修復（推薦）**

```bash
# 1. 修復卡住的 migration 並創建缺失表格
curl -X POST "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/health.fixMigration"

# 2. 創建所有缺失的 Post-MVP 表格
curl -X POST "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/health.fixAllTables"

# 3. 驗證修復
curl "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/health.schemaCheck"
```

**方案 B: 直接資料庫修復（需要資料庫訪問權限）**

```sql
-- 標記卡住的 migration 為完成
UPDATE _prisma_migrations
SET finished_at = NOW()
WHERE finished_at IS NULL;

-- 然後重新部署或重啟容器讓 migration 重新執行
```

---

### 🔴 問題 0.11: Azure Storage 環境變數未配置（2025-12-03 發現）

> ⚠️ **致命問題**：Quote 上傳功能返回 500 錯誤，缺少 Azure Blob Storage 配置！

#### 症狀

```
❌ /zh-TW/quotes/new 頁面上傳報價單時返回 500 錯誤
❌ POST /api/upload/quote 返回 "缺少 AZURE_STORAGE_ACCOUNT_NAME 環境變數"
❌ 所有文件上傳功能無法使用
```

#### 根本原因

```yaml
root_cause:
  - Azure App Service 未配置 Azure Storage 相關環境變數
  - AZURE_STORAGE_ACCOUNT_NAME 未設置
  - AZURE_STORAGE_ACCOUNT_KEY 未設置
  - 應用程式無法連接到 Azure Blob Storage
```

#### 解決方案

```bash
# 1. 首先確認或創建 Storage Account
az storage account show --name stitpmcompanydev001 --resource-group RG-RCITest-RAPO-N8N

# 2. 獲取 Storage Account Key
az storage account keys list --account-name stitpmcompanydev001 --resource-group RG-RCITest-RAPO-N8N --query "[0].value" -o tsv

# 3. 配置 App Service 環境變數
az webapp config appsettings set \
  --name app-itpm-company-dev-001 \
  --resource-group RG-RCITest-RAPO-N8N \
  --settings \
    AZURE_STORAGE_ACCOUNT_NAME="stitpmcompanydev001" \
    AZURE_STORAGE_ACCOUNT_KEY="<your-storage-account-key>" \
    AZURE_STORAGE_CONTAINER_QUOTES="quotes" \
    AZURE_STORAGE_CONTAINER_INVOICES="invoices"

# 4. 創建 Blob 容器（如果不存在）
az storage container create --name quotes --account-name stitpmcompanydev001
az storage container create --name invoices --account-name stitpmcompanydev001
```

#### 驗證步驟

```bash
# 訪問 /zh-TW/quotes/new 並嘗試上傳文件
# 應該不再返回 500 錯誤
```

---

### ✅ 問題 0.12: omExpense API 返回 500（2025-12-03 發現並解決）

> ✅ **已解決**：OMExpense 表缺少 `categoryId` 和 `sourceExpenseId` 欄位

#### 症狀

```
❌ /zh-TW/om-expenses 頁面返回 500 Internal Server Error
❌ /zh-TW/om-summary 頁面返回 500 Internal Server Error
❌ health.schemaCheck 顯示所有表格都存在
❌ 但 omExpense.getAll 和 omExpense.getSummary 仍然失敗
```

#### 根本原因

```yaml
root_cause:
  issue: OMExpense 表缺少 categoryId 和 sourceExpenseId 欄位
  database_columns: 14 個（缺少 2 個）
  prisma_expects: 16 個（包含 categoryId, sourceExpenseId）
  error: "column 'OMExpense.categoryId' does not exist"
```

#### 解決方案

**使用 Health API 修復**：

```bash
# 調用修復端點添加缺失欄位
curl -X POST "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/health.fixOmExpenseSchema"

# 返回：
# {
#   "success": true,
#   "results": [
#     "Added categoryId column",
#     "Added sourceExpenseId column",
#     "Created indexes"
#   ]
# }
```

#### 驗證結果

```bash
# 測試 API（需要登入）
curl "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/omExpense.getAll"
# 應該返回 401 UNAUTHORIZED（正確行為，需要認證）而非 500

# 使用診斷端點確認
curl "https://app-itpm-company-dev-001.azurewebsites.net/api/trpc/health.diagOmExpense"
# 應該顯示 "success": true
```

---

### 🔧 Health API 診斷工具完整指南

> 這些端點用於遠程診斷和修復，無需直接訪問資料庫

#### 端點列表

| 端點 | 方法 | 用途 |
|------|------|------|
| `health.ping` | GET | 基礎健康檢查 |
| `health.dbCheck` | GET | 資料庫連線檢查 |
| `health.schemaCheck` | GET | 驗證所有表格是否存在 |
| `health.fixMigration` | POST | 修復卡住的 migration |
| `health.fixAllTables` | POST | 創建所有缺失的 Post-MVP 表格 |
| `health.diagOmExpense` | GET | 診斷 OMExpense 查詢問題 |
| `health.diagOpCo` | GET | 診斷 OperatingCompany 數據 |
| `health.fixOmExpenseSchema` | POST | 修復 OMExpense 缺失欄位 |

#### 使用範例

```bash
BASE_URL="https://app-itpm-company-dev-001.azurewebsites.net"

# 1. 基礎健康檢查
curl "$BASE_URL/api/trpc/health.ping"

# 2. 資料庫連線檢查
curl "$BASE_URL/api/trpc/health.dbCheck"

# 3. Schema 完整性檢查
curl "$BASE_URL/api/trpc/health.schemaCheck"

# 4. 診斷 OMExpense 問題
curl "$BASE_URL/api/trpc/health.diagOmExpense"

# 5. 修復 Migration
curl -X POST "$BASE_URL/api/trpc/health.fixMigration"

# 6. 創建所有缺失表格
curl -X POST "$BASE_URL/api/trpc/health.fixAllTables"

# 7. 修復 OMExpense Schema
curl -X POST "$BASE_URL/api/trpc/health.fixOmExpenseSchema"
```

---

### 問題 1: 生產環境無法訪問 - 嚴重故障

#### 症狀

```
🚨 Critical: https://app-itpm-company-prod-001.azurewebsites.net 返回 502/503
🚨 影響: 所有用戶無法訪問
🚨 優先級: P1 - 立即處理
```

#### 立即行動（0-5 分鐘）

```yaml
immediate_actions:
  1. 確認故障範圍:
    - 是否影響所有用戶
    - 開始時間
    - 相關症狀

  2. 通知團隊:
    - Slack #incidents 頻道
    - Email: devops@company.com
    - 緊急熱線: +886-XXX-XXXX

  3. 開始記錄:
    - 創建故障記錄
    - 記錄開始時間
    - 記錄診斷步驟
```

#### 快速診斷（5-15 分鐘）

```bash
# 1. 檢查 App Service 狀態
az webapp show \
  --name app-itpm-company-prod-001 \
  --resource-group rg-itpm-company-prod \
  --query "{Name:name, State:state, AvailabilityState:availabilityState}"

# 2. 查看 Application Insights 告警
az monitor metrics alert list \
  --resource-group rg-itpm-company-prod \
  --query "[?enabled==\`true\`].{Name:name, Severity:severity, State:monitorState}"

# 3. 即時日誌（最重要）
az webapp log tail \
  --name app-itpm-company-prod-001 \
  --resource-group rg-itpm-company-prod | head -100

# 4. 檢查最近部署
az webapp deployment list \
  --name app-itpm-company-prod-001 \
  --resource-group rg-itpm-company-prod \
  --query "[0].{Time:end_time, Status:status, Id:id}"
```

#### 決策樹（15-30 分鐘）

**如果是最近部署導致**:

```yaml
immediate_rollback:
  decision: 立即回滾到上一個穩定版本
  approval: DevOps Team Lead 口頭批准（記錄在案）

  rollback_steps:
    # Slot Swap 回滾
    az webapp deployment slot swap \
      --name app-itpm-company-prod-001 \
      --resource-group rg-itpm-company-prod \
      --slot staging \
      --target-slot production \
      --action swap

    # 驗證
    bash azure/tests/smoke-test.sh company-prod

    # 通知
    - 通知團隊回滾完成
    - 更新故障記錄
    - 安排事後分析 (Post-Mortem)
```

**如果是基礎設施問題**:

```yaml
escalate_to_azure_admin:
  scenarios:
    - 資料庫無法連接
    - 網路問題
    - Azure 平台問題

  actions: 1. 收集診斷信息 2. 聯繫 Azure Administrator 3. 提供完整上下文 4. 等待專家介入
```

---

### 問題 2: 部署到公司環境失敗

#### 症狀

```
❌ bash azure/scripts/deploy-to-company.sh prod 失敗
❌ CI/CD Pipeline 失敗
❌ 權限被拒或配額超限
```

#### 診斷步驟

**步驟 1: 檢查部署權限**

```bash
# 驗證當前帳號權限
az role assignment list \
  --assignee $(az account show --query user.name -o tsv) \
  --resource-group rg-itpm-company-prod \
  --query "[].{Role:roleDefinitionName, Scope:scope}"

# 檢查 Service Principal 權限（CI/CD）
az role assignment list \
  --assignee $AZURE_CLIENT_ID \
  --query "[].{Role:roleDefinitionName, Scope:scope}"
```

**步驟 2: 檢查配額限制**

```bash
# 查看訂閱配額使用
az vm list-usage --location eastasia -o table

# 查看資源群組配額
az group show --name rg-itpm-company-prod --query "{Tags:tags, Location:location}"
```

**步驟 3: 檢查網路配置**

```bash
# 驗證 VNet 配置（如適用）
az network vnet list --resource-group rg-itpm-company-prod

# 檢查 NSG 規則
az network nsg list --resource-group rg-itpm-company-prod

# 驗證 Private Endpoint（如適用）
az network private-endpoint list --resource-group rg-itpm-company-prod
```

#### 常見原因和解決方案

**原因 1: 權限不足**

```yaml
symptoms:
  - 'Authorization failed'
  - 'The client ... does not have authorization'

resolution:
  1. 確認需要的權限:
    - Contributor（資源群組層級）
    - Key Vault Secrets User
    - Storage Blob Data Contributor

  2. 聯繫 Azure Administrator:
    - 提供錯誤訊息
    - 說明需要的操作
    - 請求授予權限

  3. 權限授予後驗證: az role assignment list --assignee <your-principal-id>
```

**原因 2: 配額超限**

```yaml
symptoms:
  - "QuotaExceeded"
  - "Subscription has reached its quota"

resolution:
  1. 檢查配額使用情況
  2. 請求配額增加:
     - Azure Portal → Support → New support request
     - 選擇 "Service and subscription limits (quotas)"
     - 描述需求和業務理由

  3. 或清理未使用資源
```

**原因 3: 網路限制**

```yaml
symptoms:
  - 'NetworkAccessDenied'
  - 'Connection timeout'

resolution:
  1. 確認部署來源 IP 2. 與 Azure Admin 確認防火牆規則 3. 確認 VNet/Subnet 配置正確 4. 驗證 Private
  Endpoint 連接
```

---

### 問題 3: 資料庫連接問題（企業級）

#### 症狀

```
❌ 應用程式無法連接 PostgreSQL
❌ Managed Identity 認證失敗
❌ Private Endpoint 連接超時
```

#### 企業環境特殊考慮

**Private Endpoint 診斷**

```bash
# 檢查 Private Endpoint 狀態
az network private-endpoint show \
  --name pe-psql-itpm-company-prod \
  --resource-group rg-itpm-company-prod \
  --query "{Name:name, ProvisioningState:provisioningState, ConnectionState:privateLinkServiceConnections[0].privateLinkServiceConnectionState}"

# 檢查 Private DNS Zone
az network private-dns zone list \
  --resource-group rg-itpm-company-prod \
  --query "[?contains(name, 'postgres')].{Name:name, RecordSets:numberOfRecordSets}"

# 測試 DNS 解析（從 App Service）
az webapp ssh --name app-itpm-company-prod-001 --resource-group rg-itpm-company-prod
# 在 SSH 會話中: nslookup psql-itpm-company-prod-001.postgres.database.azure.com
```

**Managed Identity 診斷**

```bash
# 確認 Managed Identity 已啟用
az webapp identity show \
  --name app-itpm-company-prod-001 \
  --resource-group rg-itpm-company-prod

# 檢查 PostgreSQL AAD 管理員配置
az postgres flexible-server ad-admin list \
  --server-name psql-itpm-company-prod-001 \
  --resource-group rg-itpm-company-prod

# 測試 Managed Identity 連接
# 確認資料庫用戶已創建並授權
```

#### 升級路徑

```yaml
if_private_endpoint_issue:
  escalate_to: Azure Network Administrator
  provide:
    - Private Endpoint 名稱和狀態
    - DNS 解析結果
    - VNet/Subnet 配置
    - 錯誤日誌

if_managed_identity_issue:
  escalate_to: Azure AD Administrator
  provide:
    - Managed Identity Principal ID
    - 所需的資料庫權限
    - 錯誤訊息（認證失敗）
```

---

### 問題 4: Key Vault 訪問問題（企業級）

#### 症狀

```
❌ Access denied to Key Vault
❌ The user, group or application does not have secrets get permission
❌ 共用 Key Vault 權限配置問題
```

#### 企業環境診斷

**檢查 Key Vault 訪問策略**

```bash
# 如果使用共用企業 Key Vault
VAULT_NAME="kv-company-shared"  # 替換為實際名稱

# 檢查訪問策略
az keyvault show \
  --name $VAULT_NAME \
  --query "properties.accessPolicies[?objectId=='<APP_PRINCIPAL_ID>'].{Permissions:permissions}"

# 檢查 RBAC 模式（如果啟用）
az role assignment list \
  --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-itpm-company-prod/providers/Microsoft.KeyVault/vaults/$VAULT_NAME \
  --assignee <APP_PRINCIPAL_ID>
```

**檢查網路限制**

```bash
# Key Vault 防火牆規則
az keyvault network-rule list \
  --name $VAULT_NAME \
  --query "{DefaultAction:defaultAction, IPRules:ipRules, VnetRules:virtualNetworkRules}"

# 如果使用 Private Endpoint
az network private-endpoint list \
  --resource-group rg-itpm-company-prod \
  --query "[?contains(name, 'keyvault')].{Name:name, State:privateLinkServiceConnections[0].privateLinkServiceConnectionState}"
```

#### 權限申請流程

```yaml
key_vault_access_request:
  1. 準備信息:
    application_name: 'IT Project Management Platform'
    environment: 'Production'
    managed_identity_principal_id: '<from az webapp identity show>'
    required_permissions: 'secrets: get, list'
    business_justification: 'Access production secrets for app configuration'

  2. 提交申請:
    to: Azure Administrator
    via: Email或內部工單系統
    include: 所有準備的信息

  3. 等待批准:
    typical_time: 1-2 工作日
    follow_up: 如緊急，聯繫 DevOps Team Lead

  4. 驗證訪問:
    # 批准後測試
    az keyvault secret show \ --vault-name $VAULT_NAME \ --name ITPM-PROD-DATABASE-URL \ --query
    "value"
```

---

## 📊 監控和告警管理

### Application Insights 診斷

**查看實時監控**

```bash
# 查看最近錯誤
az monitor app-insights query \
  --app app-itpm-company-prod-insights \
  --resource-group rg-itpm-company-prod \
  --analytics-query "exceptions | where timestamp > ago(1h) | summarize count() by type, outerMessage | order by count_ desc"

# 查看性能指標
az monitor app-insights query \
  --app app-itpm-company-prod-insights \
  --resource-group rg-itpm-company-prod \
  --analytics-query "requests | where timestamp > ago(1h) | summarize avg(duration) by bin(timestamp, 5m)"

# 查看可用性測試結果
az monitor app-insights query \
  --app app-itpm-company-prod-insights \
  --resource-group rg-itpm-company-prod \
  --analytics-query "availabilityResults | where timestamp > ago(1h) | summarize successRate = count(success==true)*100.0/count() by bin(timestamp, 5m)"
```

### 告警規則管理

```bash
# 查看活動告警
az monitor metrics alert list \
  --resource-group rg-itpm-company-prod \
  --query "[?enabled==\`true\`].{Name:name, Severity:severity, Condition:criteria}"

# 查看告警歷史
az monitor activity-log alert list \
  --resource-group rg-itpm-company-prod

# 臨時禁用告警（維護窗口）
# 需要 CAB 批准
az monitor metrics alert update \
  --name alert-high-cpu \
  --resource-group rg-itpm-company-prod \
  --enabled false
```

---

## 🔄 企業級回滾程序

### Production 回滾審批流程

```yaml
rollback_approval_process:
  severity_p1_critical:
    approval: DevOps Team Lead 口頭批准（5分鐘內）
    notification: 即時通知 CAB（事後補充）
    documentation: 創建緊急變更記錄

  severity_p2_high:
    approval: 需要 CAB 快速審批（30分鐘）
    notification: Slack + Email
    documentation: 標準變更流程

  severity_p3_medium:
    approval: 需要完整 CAB 審批
    notification: 正常變更請求流程
    documentation: 完整變更文檔
```

### Slot Swap 回滾（推薦）

```bash
# 生產環境回滾（需要批准）
echo "⚠️  準備回滾到 Staging Slot"
echo "當前 Production Slot: $(az webapp config show --name app-itpm-company-prod-001 --resource-group rg-itpm-company-prod --query linuxFxVersion -o tsv)"

# 執行 Swap
az webapp deployment slot swap \
  --name app-itpm-company-prod-001 \
  --resource-group rg-itpm-company-prod \
  --slot staging \
  --target-slot production \
  --action swap

# 驗證
bash azure/tests/smoke-test.sh company-prod

# 通知
echo "回滾完成，通知團隊和利益相關者"
```

### 版本回滾

```bash
# 部署舊版本（需要批准）
STABLE_VERSION="v1.5.2"  # 最後已知穩定版本

az webapp config container set \
  --name app-itpm-company-prod-001 \
  --resource-group rg-itpm-company-prod \
  --docker-custom-image-name acritpmcompany.azurecr.io/itpm-web:$STABLE_VERSION

# 重啟
az webapp restart --name app-itpm-company-prod-001 --resource-group rg-itpm-company-prod

# 監控 15 分鐘
az webapp log tail --name app-itpm-company-prod-001 --resource-group rg-itpm-company-prod
```

---

## 📞 升級和協作流程

### Level 1: 自助診斷（0-30 分鐘）

```yaml
self_diagnosis:
  actions:
    - 查看 Application Insights
    - 檢查告警歷史
    - 查看應用程式日誌
    - 執行基礎診斷腳本
    - 查閱內部文檔和知識庫

  tools:
    - bash azure/tests/test-azure-connectivity.sh company-prod
    - az webapp log tail
    - Application Insights 查詢
```

### Level 2: DevOps Team（30-60 分鐘）

```yaml
devops_escalation:
  contact:
    - Slack: #devops-support
    - Email: devops@company.com
    - Phone: +886-XXX-XXXX（緊急）

  provide:
    - 問題症狀描述
    - 影響範圍
    - 已執行的診斷步驟
    - 日誌和錯誤訊息
    - 環境信息（company/prod）

  response_time:
    - P1 Critical: 15 分鐘內
    - P2 High: 30 分鐘內
    - P3 Medium: 2 小時內
```

### Level 3: Azure Administrator（1-2 小時）

```yaml
azure_admin_escalation:
  scenarios:
    - 權限問題
    - 網路配置問題
    - Key Vault 訪問問題
    - 訂閱配額問題
    - Private Endpoint 問題

  contact:
    - Email: azure-admin@company.com
    - 內部工單系統

  prepare:
    - 完整錯誤訊息
    - 資源 ID 和名稱
    - 所需的權限或配置
    - 業務影響說明
```

### Level 4: Microsoft Azure Support（嚴重故障）

```yaml
microsoft_support:
  when_to_escalate:
    - Azure 平台問題
    - 服務中斷
    - 數據丟失風險
    - 無法通過內部資源解決

  how_to_create_ticket:
    1. Azure Portal → Help + support → New support request
    2. 選擇 Issue type: Technical
    3. 選擇 Severity:
       - Severity A (Critical): 生產系統完全中斷
       - Severity B (High): 生產系統嚴重降級
       - Severity C (Moderate): 次要影響
    4. 提供詳細問題描述和診斷資訊
    5. 附上日誌、截圖、錯誤訊息

  response_time:
    - Severity A: < 1 小時
    - Severity B: < 4 小時
    - Severity C: < 8 小時（工作時間）
```

---

## 📝 故障記錄和事後分析

### 故障記錄模板

```markdown
# 故障記錄 - [故障簡述]

## 基本信息

- **故障時間**: 2025-XX-XX XX:XX
- **發現時間**: 2025-XX-XX XX:XX
- **恢復時間**: 2025-XX-XX XX:XX
- **總持續時間**: X 小時 X 分鐘
- **環境**: company/prod
- **嚴重級別**: P1/P2/P3
- **影響範圍**: 所有用戶 / 部分功能

## 症狀描述

[詳細描述問題症狀]

## 根本原因

[經診斷確認的根本原因]

## 診斷過程

1. [診斷步驟 1]
2. [診斷步驟 2] ...

## 修復操作

1. [修復步驟 1]
2. [修復步驟 2] ...

## 影響評估

- 受影響用戶數: XX
- 業務損失: XX
- SLA 影響: XX%

## 後續行動

- [ ] 更新監控告警
- [ ] 更新文檔
- [ ] 技術改進
- [ ] 流程優化

## 參與人員

- 發現: XXX
- 診斷: XXX
- 修復: XXX
```

### Post-Mortem 流程

```yaml
post_mortem_meeting:
  timing: 故障恢復後 48 小時內
  participants:
    - DevOps Team
    - 開發團隊
    - Azure Administrator（如相關）
    - 產品負責人

  agenda:
    1. 時間線回顧（5 分鐘） 2. 根本原因分析（10 分鐘） 3. 影響評估（5 分鐘） 4. 改進措施討論（20
    分鐘） 5. 行動項分配（10 分鐘）

  outputs:
    - Post-Mortem 報告
    - 改進措施清單
    - 更新的 Runbook
    - 知識庫文章
```

---

## ✅ 企業環境問題排查檢查清單

### 診斷前準備

- [ ] 確認問題環境（company/dev|staging|prod）
- [ ] 確認問題開始時間
- [ ] 評估影響範圍和嚴重性
- [ ] 創建故障記錄
- [ ] 通知相關團隊

### 診斷階段

- [ ] 查看 Application Insights
- [ ] 檢查告警歷史
- [ ] 查看應用程式日誌
- [ ] 執行自動化診斷腳本
- [ ] 檢查最近的變更記錄
- [ ] 驗證基礎設施狀態

### 升級決策

- [ ] 30 分鐘內未解決 → 升級到 DevOps Team
- [ ] 涉及權限/網路 → 升級到 Azure Admin
- [ ] 平台級別問題 → 升級到 Microsoft Support

### 修復後驗證

- [ ] 執行煙霧測試
- [ ] 監控 30 分鐘穩定性
- [ ] 驗證所有功能正常
- [ ] 檢查 Application Insights 指標恢復正常
- [ ] 更新故障記錄
- [ ] 通知團隊問題已解決

### 後續行動

- [ ] 安排 Post-Mortem 會議
- [ ] 更新知識庫
- [ ] 更新監控告警
- [ ] 實施預防措施
- [ ] 更新 Runbook

---

## 🎓 參考資源

### 內部文檔

- `SITUATION-7-AZURE-DEPLOY-COMPANY.md` - 公司環境部署指引
- `azure/environments/company/README.md` - 公司環境配置說明
- `claudedocs/AZURE-DEPLOYMENT-FILE-STRUCTURE-GUIDE.md` - 目錄結構指引

### 企業流程文檔

- 變更管理流程（內部鏈接）
- CAB 審批流程（內部鏈接）
- 故障升級流程（內部鏈接）
- Post-Mortem 模板（內部鏈接）

### Azure 官方文檔

- [Azure App Service 企業級診斷](https://docs.microsoft.com/azure/app-service/troubleshoot-diagnostic-logs)
- [Application Insights 故障排查](https://docs.microsoft.com/azure/azure-monitor/app/troubleshoot)
- [Azure Support 指南](https://azure.microsoft.com/support/options/)

---

## 🎯 實戰經驗總結：2025-11-25 ~ 2025-11-26 公司環境部署

### 遇到的問題和解決時間

| 問題                              | 嚴重性   | 解決時間 | 解決方案                  |
| --------------------------------- | -------- | -------- | ------------------------- |
| **.dockerignore 排除 migrations** | **致命** | ~3 小時  | 註解 `**/migrations` 規則 |
| **FEAT-001 Schema 不匹配**        | **致命** | ~2 小時  | 創建補充 migration SQL    |
| **Post-MVP 表格缺失**             | **致命** | ~1 小時  | 創建 idempotent migration |
| **Currency migration 缺失**       | **高**   | ~1 小時  | 創建新 migration SQL      |
| Prisma 建置初始化                 | 高       | ~2 小時  | Proxy lazy loading        |
| Key Vault 權限不足                | 中       | ~30 分鐘 | 改用 App Settings         |
| API Route 預渲染                  | 中       | ~30 分鐘 | dynamic export            |
| Alpine binary target              | 低       | ~15 分鐘 | schema.prisma 配置        |

### 關鍵學習

```yaml
lessons_learned:
  0_dockerignore_critical:
    - '.dockerignore 是第一個要檢查的檔案'
    - '**/migrations 規則會導致所有 migration 被排除'
    - '容器中沒有 migrations = 資料庫無法初始化'
    - "日誌顯示 'No migration found' 是明顯指標"

  0.1_schema_migration_mismatch:
    - 'schema.prisma 和 migration SQL 必須保持一致'
    - '特定頁面 500 錯誤而其他頁面正常 = 可能是該 model 的欄位缺失'
    - '檢查方法: grep migration SQL 是否包含 schema.prisma 中的所有欄位'
    - 'FEAT-001 等功能開發時，必須同時創建完整的 migration'
    - '部署前應驗證所有核心 API 端點，不只是登入頁面'

  0.2_postmvp_tables_missing:
    - '部分頁面正常不代表部署完全成功'
    - 'Post-MVP 功能（om-expenses、om-summary、charge-outs）有獨立的表格依賴'
    - '必須測試所有主要頁面，不能只測試登入頁面'
    - '使用 idempotent migration（IF NOT EXISTS）確保可重複執行'
    - '比較 schema.prisma model 數量和 migration CREATE TABLE 數量'

  0.5_migration_completeness:
    - 'schema.prisma 新增 model 必須有對應 migration'
    - '手動創建 migration 時需要完整的 SQL'
    - 'nullable 欄位可以解決現有資料兼容性問題'

  1_prisma_lazy_loading:
    - 標準的 singleton 模式不夠，需要 Proxy
    - import 時就會觸發初始化
    - 必須延遲到實際調用時才初始化

  2_docker_build:
    - 建置階段需要 DATABASE_URL 佔位符
    - SKIP_ENV_VALIDATION=1 很重要
    - Alpine Linux 需要特定 binary target

  3_nextjs_api_routes:
    - 預設會在建置時預渲染
    - 使用資料庫的 route 必須標記 dynamic
    - export const dynamic = 'force-dynamic'

  4_enterprise_permissions:
    - 不一定有權限創建所有資源
    - 準備替代方案（如 App Settings）
    - 提前與 Azure Admin 確認權限範圍

  5_startup_script:
    - 'startup.sh 確保 migration 在應用啟動前執行'
    - '環境變數在運行時才可用'
    - '先 migrate，再啟動 Next.js'

  6_seed_api:
    - 'Seed API 比 CLI seed 更適合容器化環境'
    - '可以遠程調用，不需要 SSH 進容器'
    - '提供詳細的執行結果供驗證'
```

### 推薦的診斷順序

```yaml
troubleshooting_order:
  0. 容器內 Migrations 缺失（最高優先檢查）:
    - 檢查 .dockerignore 是否排除 migrations
    - 驗證 Docker image 中 migrations 是否存在
    - 查看日誌確認 "X migrations found"
    - 詳見「問題 0」章節

  0.1. Schema-Migration 不匹配（特定頁面 500 錯誤）:
    - 症狀: 某些頁面 500，其他頁面正常
    - 檢查: schema.prisma 欄位 vs migration SQL 欄位
    - 命令: grep "projectCode\|globalFlag\|priority" migrations/*/migration.sql
    - 詳見「問題 0.1」章節

  0.2. Post-MVP 表格缺失（Post-MVP 功能 500 錯誤）:
    - 症狀: /om-expenses、/om-summary、/charge-outs 返回 500
    - 其他頁面（/projects、/users）正常
    - 檢查: schema.prisma model 數量 vs migration CREATE TABLE 數量
    - 命令: grep "CREATE TABLE.*ExpenseCategory" migrations/*/migration.sql
    - 解決: 創建 Post-MVP 表格的 idempotent migration
    - 詳見「問題 0.2」章節

  1. Docker 建置失敗:
    - 檢查 Prisma lazy loading
    - 檢查 binaryTargets
    - 檢查 dynamic exports

  2. 部署失敗:
    - 檢查 ACR 登入
    - 檢查映像是否存在
    - 檢查 App Service 配置

  3. 運行時錯誤:
    - 檢查環境變數
    - 檢查資料庫連接
    - 查看 App Service 日誌
    - 執行 Seed API 檢查資料狀態

  4. 權限問題:
    - 列出當前權限
    - 確認資源提供者註冊
    - 聯繫 Azure Administrator
```

### 關鍵架構元件

```yaml
startup_sequence:
  1_container_start: docker/startup.sh 執行
  2_migration_deploy: prisma migrate deploy（需要 migrations 資料夾）
  3_app_start: node apps/web/.next/standalone/apps/web/server.js
  4_seed_api: POST /api/admin/seed（手動觸發初始資料）

key_files:
  docker/startup.sh: 容器啟動腳本，執行 migration 和啟動 Next.js
  docker/Dockerfile: 容器建置配置
  .dockerignore: 控制 Docker build context 包含的檔案
  packages/db/prisma/migrations/: Prisma migration SQL 檔案
  apps/web/src/app/api/admin/seed/route.ts: Seed API 端點
```

---

**版本**: 2.0.0 **最後更新**: 2025-12-03 **維護者**: DevOps Team + Azure Administrator
**適用環境**: 公司 Azure 訂閱（Staging、Production、正式環境） **審批**: 需要 DevOps Team
Lead 和 Azure Administrator 批准 **更新記錄**:

- v2.0.0 (2025-12-03): **重大更新** - 文檔重組和新增問題
  - **[重組]** 本文檔現為完整的「故障排查指南」，與 SITUATION-7「部署流程指南」分離
  - **[新增]** 問題 0.8: Prisma Client Docker 生成失敗（pnpm filter 不穩定）
  - **[新增]** 問題 0.9: OpenSSL 3.0 相容性問題（Alpine 3.22 移除 1.1）
  - **[新增]** 問題 0.10: Migration 卡住（finishedAt 為 null）
  - **[新增]** 問題 0.11: Azure Storage 環境變數未配置
  - **[新增]** 問題 0.12: omExpense API 返回 500（已解決）
  - **[新增]** Health API 診斷工具完整指南
- v1.4.0 (2025-12-03):
  - **[關鍵]** 添加「問題 0.2: Post-MVP 表格缺失」- Azure 資料庫缺少 ExpenseCategory 等 8 個 Post-MVP 表格導致 500 錯誤
  - 記錄 /om-expenses、/om-summary 頁面 500 錯誤的案例和解決方案
  - 強調「部分頁面正常不代表部署完全成功」的關鍵學習
  - 添加 idempotent migration（IF NOT EXISTS）最佳實踐
  - 更新診斷順序，添加 Post-MVP 表格缺失檢查
  - 更新問題表格，添加 Post-MVP 表格缺失問題
- v1.3.0 (2025-12-02):
  - **[關鍵]** 添加「問題 0.1: FEAT-001 Schema 不匹配」- schema.prisma 欄位與 migration SQL 不一致導致特定頁面 500 錯誤
  - 更新診斷順序，添加 Schema-Migration 一致性檢查
  - 更新關鍵學習，添加 schema-migration 一致性檢查要點
  - 更新問題表格，添加 FEAT-001 Schema 不匹配問題
- v1.2.0 (2025-11-26):
  - **[關鍵]** 添加「問題 0: .dockerignore 排除 Migrations」- 這是最常見的致命問題
  - 添加「問題 0.5: Migration SQL 檔案缺失」（Currency 表問題）
  - 更新診斷順序，將 migrations 檢查放在最高優先
  - 添加 startup.sh、Seed API、關鍵架構元件說明
  - 添加詳細的根本原因鏈分析和預防措施
- v1.1.0 (2025-11-25): 添加 Docker 建置問題、權限問題章節，以及實戰經驗總結
