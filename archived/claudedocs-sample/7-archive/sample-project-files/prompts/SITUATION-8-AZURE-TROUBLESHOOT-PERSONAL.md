# SITUATION-8: Azure 個人環境問題排查指引

**用途**: 當**個人 Azure 訂閱**部署或運行過程中遇到問題時，使用此指引進行快速診斷和自助解決。

**目標環境**: 個人 Azure 訂閱（開發、測試環境）

**觸發情境**:

- 部署失敗或異常
- 應用程式無法訪問
- 資料庫連接錯誤
- 文件上傳失敗
- 認證問題
- 性能問題

**特點**: 快速自助診斷，靈活問題解決，學習導向

---

## 🎯 個人環境問題排查原則

### 1. 快速診斷優先

```yaml
troubleshooting_mindset:
  - ✅ 從最常見問題開始檢查
  - ✅ 使用自動化診斷腳本
  - ✅ 查看日誌和錯誤訊息
  - ✅ 試錯和學習並行
  - ℹ️  不需要複雜的升級流程
```

### 2. 自助解決為主

```yaml
self_service_approach:
  工具:
    - 自動化診斷腳本（azure/tests/）
    - Azure CLI 命令
    - 日誌串流（即時查看）
    - Web 搜索和文檔查閱

  資源:
    - 個人完全控制權限
    - 可以自由重啟服務
    - 可以調整防火牆規則
    - 可以重新部署測試
```

### 3. 學習機會

```yaml
learning_mindset:
  每個問題都是學習機會:
    - 理解 Azure 服務如何運作
    - 熟悉診斷工具使用
    - 掌握常見問題模式
    - 累積故障排查經驗
```

---

## 🔍 常見問題快速診斷

### 🔴 問題 0: 容器內 Migrations 缺失（高頻致命問題）

> ⚠️ **最常見根本原因**: 這是個人環境部署失敗最常見的原因之一！

#### 症狀

```
❌ 用戶註冊返回 500 Internal Server Error
❌ API 返回 "The table public.Role does not exist"
❌ API 返回 "The table public.Currency does not exist"
❌ 容器日誌顯示 "No migration found in prisma/migrations"
❌ Seed 失敗或無法執行
```

#### 快速診斷

```bash
# 1. 檢查 .dockerignore 是否排除 migrations
grep -n "migrations" .dockerignore
# 如果看到未被註解的 "**/migrations"，這就是問題！

# 2. 驗證本地 Docker image 中 migrations 是否存在
docker build -f docker/Dockerfile -t test-build .
docker run --rm test-build ls -la /app/packages/db/prisma/migrations/
# 應該看到 3 個資料夾：20251024082756_init, 20251111065801_new, 20251126100000_add_currency

# 3. 查看日誌中的 migration 訊息
az webapp log tail --name app-itpm-dev-001 --resource-group rg-itpm-dev | grep -i "migration"
# 應該看到 "3 migrations found" 而非 "No migration found"
```

#### 根本原因

```yaml
root_cause_chain:
  level_1: .dockerignore 包含 "**/migrations" 規則
  level_2: Docker build context 排除 migrations 資料夾
  level_3: Container 中 /app/packages/db/prisma/migrations/ 為空
  level_4: prisma migrate deploy 報告 "No migration found"
  level_5: 資料庫表結構未建立
  level_6: 應用程式嘗試操作不存在的表 → 500 錯誤
```

#### 快速修復

```bash
# 步驟 1: 修改 .dockerignore
# 找到並註解掉 migrations 排除規則
# 將 "**/migrations" 改為 "# **/migrations"

# 步驟 2: 確認 .gitignore 允許 migration SQL
# 添加這行: !packages/db/prisma/migrations/**/*.sql

# 步驟 3: 重建並推送 Docker image
docker build -f docker/Dockerfile -t acritpmdev.azurecr.io/itpm-web:latest .
docker push acritpmdev.azurecr.io/itpm-web:latest

# 步驟 4: 重啟 App Service
az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev

# 步驟 5: 驗證 migration 執行成功
az webapp log tail --name app-itpm-dev-001 --resource-group rg-itpm-dev | grep -i "migration"
# 預期: "3 migrations found" 和 "All migrations have been successfully applied"

# 步驟 6: 執行 Seed（如果需要）
curl -X POST "https://app-itpm-dev-001.azurewebsites.net/api/admin/seed" \
  -H "Content-Type: application/json"
```

**詳細說明**: 參見 `azure/docs/DEPLOYMENT-TROUBLESHOOTING.md`

---

### 問題 1: 應用程式無法訪問 - HTTP 502/503 錯誤

#### 症狀

```
❌ https://app-itpm-dev-001.azurewebsites.net 返回 502 Bad Gateway
❌ 或 503 Service Unavailable
❌ 頁面顯示 "Application Error"
```

#### 快速診斷步驟

```bash
# 1. 檢查 App Service 狀態
az webapp show \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --query "{Name:name, State:state, AvailabilityState:availabilityState}"

# 2. 查看即時日誌（最重要）
az webapp log tail \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev

# 3. 檢查容器啟動狀態
az webapp log show \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --query "[?contains(message, 'Container')].message"
```

#### 常見原因和快速修復

**原因 1: 容器啟動失敗**

```yaml
症狀:
  - 日誌顯示 "Container didn't respond to HTTP pings"
  - 或 "Application startup failed"

診斷:
  # 查找錯誤訊息
  az webapp log tail --name app-itpm-dev-001 --resource-group rg-itpm-dev | grep -i "error"

可能原因:
  - 缺少環境變數（DATABASE_URL, NEXTAUTH_SECRET）
  - Prisma Client 未生成
  - Node.js 版本不匹配

快速修復:
  # 驗證環境變數
  az webapp config appsettings list \
    --name app-itpm-dev-001 \
    --resource-group rg-itpm-dev \
    --query "[?name=='DATABASE_URL' || name=='NEXTAUTH_SECRET']"

  # 重新部署（修復 Prisma 問題）
  bash azure/scripts/06-deploy-app.sh

  # 重啟 App Service
  az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev
```

**原因 2: 資料庫連接失敗**

```yaml
症狀:
  - 日誌顯示 "Can't reach database server"
  - 或 "getaddrinfo ENOTFOUND psql-itpm-dev-001"

診斷:
  # 測試資料庫連接
  psql "postgresql://itpmadmin:PASSWORD@psql-itpm-dev-001.postgres.database.azure.com:5432/itpm_dev?sslmode=require"

快速修復:
  # 1. 確認防火牆規則（允許 Azure 服務）
  az postgres flexible-server firewall-rule create \
    --resource-group rg-itpm-dev \
    --name psql-itpm-dev-001 \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

  # 2. 驗證 DATABASE_URL 格式
  # 確保包含 ?sslmode=require
  # postgresql://user:pass@host:5432/db?sslmode=require

  # 3. 重啟 App Service
  az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev
```

**原因 3: 記憶體不足**

```yaml
症狀:
  - 日誌顯示 "JavaScript heap out of memory"
  - 容器頻繁重啟

快速修復:
  # 增加 Node.js heap size
  az webapp config appsettings set \
    --name app-itpm-dev-001 \
    --resource-group rg-itpm-dev \
    --settings NODE_OPTIONS="--max-old-space-size=2048"

  # 或升級 App Service Plan（臨時解決）
  az appservice plan update \
    --name plan-itpm-dev \
    --resource-group rg-itpm-dev \
    --sku B2
```

---

### 問題 2: 部署失敗

#### 症狀

```
❌ bash azure/scripts/deploy-to-personal.sh dev 失敗
❌ Docker 映像推送失敗
❌ 資源創建錯誤
```

#### 診斷步驟

```bash
# 1. 檢查 Azure 登入狀態
az account show

# 2. 驗證 Azure CLI 版本
az --version

# 3. 檢查 Docker daemon
docker ps

# 4. 驗證 ACR 訪問
az acr login --name acritpmdev
```

#### 常見原因和快速修復

**原因 1: Docker 映像構建失敗**

```yaml
症狀:
  - Docker build 過程中出現錯誤
  - 或 Prisma generate 失敗

診斷:
  # 本地構建測試
  docker build -t itpm-web:test -f docker/Dockerfile .

快速修復:
  # 1. 清理 Docker 緩存
  docker system prune -a

  # 2. 確認 pnpm install 成功
  pnpm install

  # 3. 重新生成 Prisma Client
  pnpm db:generate

  # 4. 重新構建
  docker build -t acritpmdev.azurecr.io/itpm-web:latest -f docker/Dockerfile .
```

**原因 2: ACR 推送權限問題**

```yaml
症狀:
  - docker push 失敗
  - 或 "unauthorized: authentication required"

快速修復:
  # 重新登入 ACR
  az acr login --name acritpmdev

  # 確認 Admin 帳號已啟用
  az acr update --name acritpmdev --admin-enabled true

  # 推送映像
  docker push acritpmdev.azurecr.io/itpm-web:latest
```

**原因 3: 資源配額限制**

```yaml
症狀:
  - "QuotaExceeded" 錯誤
  - 或 "The subscription ... has reached its quota"

快速修復:
  # 查看當前配額使用
  az vm list-usage --location eastasia -o table

  # 刪除未使用資源釋放配額
  az resource list --resource-group rg-itpm-dev-temp --query "[].id" -o tsv | xargs -I {} az resource delete --ids {}

  # 或更換區域
  # 修改 azure/environments/personal/dev.env.example
  # LOCATION="japaneast"  # 換到其他區域
```

---

### 問題 3: 資料庫連接錯誤

#### 症狀

```
❌ Error: getaddrinfo ENOTFOUND psql-itpm-dev-001.postgres.database.azure.com
❌ Error: connect ETIMEDOUT
❌ Error: password authentication failed
```

#### 快速診斷腳本

```bash
# 使用自動化診斷腳本
bash azure/tests/test-azure-connectivity.sh dev

# 預期輸出:
# ✅ Azure 登入: 成功
# ✅ PostgreSQL DNS 解析: 成功
# ✅ PostgreSQL 連接: 成功
# ✅ 防火牆規則: 已配置
```

#### 常見原因和快速修復

**原因 1: 防火牆阻擋**

```bash
# 快速修復: 允許所有 Azure 服務訪問
az postgres flexible-server firewall-rule create \
  --resource-group rg-itpm-dev \
  --name psql-itpm-dev-001 \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# 允許本地開發機器訪問（可選）
MY_IP=$(curl -s ifconfig.me)
az postgres flexible-server firewall-rule create \
  --resource-group rg-itpm-dev \
  --name psql-itpm-dev-001 \
  --rule-name AllowMyIP \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP
```

**原因 2: 密碼錯誤**

```bash
# 重置資料庫管理員密碼
NEW_PASSWORD="NewSecurePassword123!"

az postgres flexible-server update \
  --name psql-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --admin-password "$NEW_PASSWORD"

# 更新 Key Vault 密鑰
az keyvault secret set \
  --vault-name kv-itpm-dev \
  --name ITPM-DEV-DATABASE-URL \
  --value "postgresql://itpmadmin:$NEW_PASSWORD@psql-itpm-dev-001.postgres.database.azure.com:5432/itpm_dev?sslmode=require"

# 重啟 App Service
az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev
```

**原因 3: SSL 連接問題**

```yaml
症狀:
  - "SSL connection has been closed unexpectedly"

快速修復:
  # 確保 DATABASE_URL 包含 sslmode=require
  postgresql://user:pass@host:5432/db?sslmode=require

  # 更新 Key Vault
  az keyvault secret set \
    --vault-name kv-itpm-dev \
    --name ITPM-DEV-DATABASE-URL \
    --value "postgresql://itpmadmin:PASSWORD@psql-itpm-dev-001.postgres.database.azure.com:5432/itpm_dev?sslmode=require"
```

---

### 問題 4: 文件上傳失敗 (Blob Storage)

#### 症狀

```
❌ BlobServiceClient is not defined
❌ Error: Upload failed with status code 403
❌ Container not found
```

#### 快速診斷

```bash
# 1. 檢查 Storage Account
az storage account show \
  --name stitpmdev001 \
  --resource-group rg-itpm-dev

# 2. 列出容器
az storage container list \
  --account-name stitpmdev001 \
  --auth-mode login

# 3. 測試上傳
echo "test" > test.txt
az storage blob upload \
  --account-name stitpmdev001 \
  --container-name quotes \
  --name test.txt \
  --file test.txt \
  --auth-mode login
```

#### 快速修復

**原因 1: 容器不存在**

```bash
# 創建缺失的容器
az storage container create \
  --name quotes \
  --account-name stitpmdev001 \
  --auth-mode login

az storage container create \
  --name invoices \
  --account-name stitpmdev001 \
  --auth-mode login

# 設置為 Private
az storage container set-permission \
  --name quotes \
  --public-access off \
  --account-name stitpmdev001 \
  --auth-mode login
```

**原因 2: Managed Identity 權限不足**

```bash
# 獲取 App Service Managed Identity
PRINCIPAL_ID=$(az webapp identity show \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --query principalId -o tsv)

# 授予 Storage Blob Data Contributor 權限
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-itpm-dev/providers/Microsoft.Storage/storageAccounts/stitpmdev001
```

**原因 3: 環境變數配置錯誤**

```bash
# 檢查環境變數
az webapp config appsettings list \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --query "[?contains(name, 'STORAGE')]"

# 更新配置
az webapp config appsettings set \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --settings AZURE_STORAGE_ACCOUNT_NAME="stitpmdev001" \
              AZURE_STORAGE_CONTAINER_QUOTES="quotes" \
              AZURE_STORAGE_CONTAINER_INVOICES="invoices"
```

---

### 問題 5: 登入失敗 (Azure AD B2C 或本地認證)

#### 症狀

```
❌ AADSTS50011: The reply URL does not match
❌ NextAuth callback error
❌ Invalid credentials（本地認證）
```

#### Azure AD B2C 問題診斷

```bash
# 驗證配置
az webapp config appsettings list \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --query "[?contains(name, 'AZURE_AD_B2C')]"

# 檢查 Redirect URI
echo "Expected Redirect URI:"
echo "https://app-itpm-dev-001.azurewebsites.net/api/auth/callback/azure-ad-b2c"
```

#### 快速修復

**原因 1: Redirect URI 未註冊**

```yaml
解決步驟:
  1. 前往 Azure Portal → Azure AD B2C → App registrations
  2. 選擇你的應用程式
  3. 前往 Authentication → Add platform → Web
  4. 添加 Redirect URI:
     https://app-itpm-dev-001.azurewebsites.net/api/auth/callback/azure-ad-b2c
  5. 保存更改
  6. 等待 5 分鐘讓配置生效
```

**原因 2: 本地認證資料庫問題**

```bash
# 檢查 User 表
pnpm db:studio
# 打開 Prisma Studio 查看 User 表

# 或使用 psql
psql "postgresql://itpmadmin:PASSWORD@psql-itpm-dev-001.postgres.database.azure.com:5432/itpm_dev?sslmode=require" -c "SELECT id, email, name FROM \"User\" LIMIT 5;"

# 如果需要，運行遷移
pnpm db:migrate
```

---

## 🛠️ 自動化診斷工具

### 完整診斷套件

```bash
# 1. 環境配置檢查
pnpm check:env

# 2. Azure 連接性測試
bash azure/tests/test-azure-connectivity.sh dev

# 3. 環境變數驗證
bash azure/tests/test-environment-config.sh dev

# 4. 部署健康檢查
bash azure/scripts/helper/verify-deployment.sh

# 5. 煙霧測試（完整功能測試）
bash azure/tests/smoke-test.sh dev
```

### 快速日誌查看

```bash
# 即時日誌串流（推薦）
az webapp log tail --name app-itpm-dev-001 --resource-group rg-itpm-dev

# 只看錯誤
az webapp log tail --name app-itpm-dev-001 --resource-group rg-itpm-dev | grep -i "error\|exception\|failed"

# 只看最近 100 行
az webapp log tail --name app-itpm-dev-001 --resource-group rg-itpm-dev | tail -100

# 下載完整日誌
az webapp log download \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --log-file logs-$(date +%Y%m%d-%H%M%S).zip
```

---

## 🔄 快速回滾和重置

### 回滾到上一個版本

```bash
# 查看可用的 Docker 映像版本
az acr repository show-tags --name acritpmdev --repository itpm-web

# 切換到舊版本
OLD_VERSION="v1.0.0"  # 替換為你的穩定版本
az webapp config container set \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --docker-custom-image-name acritpmdev.azurecr.io/itpm-web:$OLD_VERSION

# 重啟
az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev
```

### 完全重新部署

```bash
# 從頭開始重新部署（保留資料庫）
bash azure/scripts/deploy-to-personal.sh dev

# 如果需要清空資料庫（危險操作）
pnpm db:push --force-reset
pnpm db:seed
```

### 重置環境變數

```bash
# 重新配置所有環境變數
bash azure/scripts/helper/configure-app-settings.sh dev

# 或手動設置關鍵變數
az webapp config appsettings set \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --settings \
    DATABASE_URL="@Microsoft.KeyVault(VaultName=kv-itpm-dev;SecretName=ITPM-DEV-DATABASE-URL)" \
    NEXTAUTH_SECRET="@Microsoft.KeyVault(VaultName=kv-itpm-dev;SecretName=ITPM-DEV-NEXTAUTH-SECRET)" \
    NEXTAUTH_URL="https://app-itpm-dev-001.azurewebsites.net"
```

---

## 📊 性能問題診斷

### 查看資源使用

```bash
# CPU 和記憶體使用率
az monitor metrics list \
  --resource /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-itpm-dev/providers/Microsoft.Web/sites/app-itpm-dev-001 \
  --metric "CpuPercentage" "MemoryPercentage" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M

# 請求統計
az monitor metrics list \
  --resource /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-itpm-dev/providers/Microsoft.Web/sites/app-itpm-dev-001 \
  --metric "Requests" "Http5xx" "ResponseTime" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
```

### 如果響應慢

```yaml
可能原因:
  1. App Service Plan 層級太低
  2. 資料庫查詢慢
  3. 冷啟動（容器剛重啟）

快速修復:
  # 臨時升級 App Service Plan
  az appservice plan update \
    --name plan-itpm-dev \
    --resource-group rg-itpm-dev \
    --sku B2

  # 啟用 Always On（避免冷啟動）
  az webapp config set \
    --name app-itpm-dev-001 \
    --resource-group rg-itpm-dev \
    --always-on true

  # 查看慢查詢（PostgreSQL）
  psql "..." -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

---

## 🎓 學習和參考資源

### 內部文檔

- `azure/environments/personal/README.md` - 個人環境配置說明
- `SITUATION-6-AZURE-DEPLOY-PERSONAL.md` - 部署指引
- `claudedocs/AZURE-DEPLOYMENT-FILE-STRUCTURE-GUIDE.md` - 目錄結構指引
- `claudedocs/AZURE-PRISMA-FIX-DEPLOYMENT-SUCCESS.md` - Prisma 問題歷史案例

### Azure 官方文檔

- [Azure App Service 診斷](https://docs.microsoft.com/azure/app-service/troubleshoot-diagnostic-logs)
- [PostgreSQL 故障排查](https://docs.microsoft.com/azure/postgresql/flexible-server/how-to-troubleshoot-common-connection-issues)
- [Blob Storage 故障排查](https://docs.microsoft.com/azure/storage/common/storage-troubleshoot)

### 常見錯誤代碼參考

```yaml
HTTP_502_Bad_Gateway:
  原因: 容器啟動失敗或應用程式崩潰
  查看: az webapp log tail

HTTP_503_Service_Unavailable:
  原因: App Service 正在重啟或過載
  查看: az webapp show（檢查狀態）

ETIMEDOUT:
  原因: 網路連接超時（通常是防火牆）
  查看: 防火牆規則配置

ENOTFOUND:
  原因: DNS 解析失敗
  查看: 檢查主機名拼寫
```

---

## ✅ 問題排查檢查清單

### 快速診斷流程

- [ ] 應用程式是否可訪問？
- [ ] 日誌中有明顯錯誤嗎？
- [ ] 環境變數是否完整？
- [ ] 資料庫連接正常嗎？
- [ ] 最近有部署或配置變更嗎？

### 診斷工具運行

- [ ] `pnpm check:env` 通過
- [ ] `bash azure/tests/test-azure-connectivity.sh dev` 通過
- [ ] `bash azure/tests/test-environment-config.sh dev` 通過
- [ ] `bash azure/scripts/helper/verify-deployment.sh` 通過

### 嘗試的修復方法

- [ ] 重啟 App Service
- [ ] 重新部署應用程式
- [ ] 檢查防火牆規則
- [ ] 驗證環境變數
- [ ] 檢查 Key Vault 訪問權限

---

## 💡 問題解決技巧

### 1. 善用日誌串流

```bash
# 開兩個終端視窗
# 終端 1: 持續監控日誌
az webapp log tail --name app-itpm-dev-001 --resource-group rg-itpm-dev

# 終端 2: 執行操作
az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev
# 在終端 1 即時看到重啟過程
```

### 2. 使用 Web 搜索

```yaml
搜索技巧:
  - 複製完整錯誤訊息
  - 搜索 "Azure App Service" + 錯誤訊息
  - 查看 Stack Overflow
  - 查閱 Azure 官方文檔
```

### 3. 實驗和試錯

```yaml
個人環境優勢:
  - 可以自由嘗試不同解決方案
  - 失敗了可以重新部署
  - 累積經驗用於未來問題
  - 學習 Azure 服務運作原理
```

### 4. 記錄解決方案

```bash
# 將成功的解決方案記錄下來
echo "問題: 資料庫連接失敗" >> ~/azure-troubleshooting-notes.md
echo "解決: 添加防火牆規則 AllowAzureServices" >> ~/azure-troubleshooting-notes.md
echo "日期: $(date)" >> ~/azure-troubleshooting-notes.md
```

---

**版本**: 1.1.0 **最後更新**: 2025-11-26 **維護者**: 開發團隊
**適用環境**: 個人 Azure 訂閱（開發、測試、學習） **更新記錄**:

- v1.1.0
  (2025-11-26): 添加「問題 0: 容器內 Migrations 缺失」高頻致命問題診斷（從公司環境學到的教訓）
- v1.0.0 (2025-11-23): 初始版本
