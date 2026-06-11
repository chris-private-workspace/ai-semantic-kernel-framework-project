# SITUATION-8: Azure 問題排查指引

**用途**: 當 Azure 部署或運行過程中遇到問題時，使用此指引進行系統化的問題診斷和解決。

**觸發情境**:
- 部署失敗或異常
- 應用程式無法訪問
- 性能問題或響應緩慢
- 資料庫連接錯誤
- 文件上傳失敗
- 認證問題

---

## 🎯 問題排查方法論

### 1. 問題分類矩陣
```yaml
問題類型:
  部署相關:
    - CI/CD Pipeline 失敗
    - Docker 鏡像構建錯誤
    - 資源配置錯誤

  運行時錯誤:
    - 應用程式崩潰
    - 500/502/503 錯誤
    - 記憶體溢出

  連接問題:
    - 資料庫連接失敗
    - Blob Storage 無法訪問
    - Redis 連接超時

  認證授權:
    - Azure AD B2C 登入失敗
    - Managed Identity 權限不足
    - Key Vault 訪問被拒

  性能問題:
    - 響應時間過長
    - CPU/記憶體使用率高
    - 資料庫查詢慢
```

### 2. 系統化排查流程
```yaml
step_1_資訊收集:
  - 錯誤訊息和堆棧追蹤
  - 發生時間和頻率
  - 影響範圍（所有用戶 vs 部分用戶）
  - 最近的變更（代碼/配置/資源）

step_2_快速診斷:
  - 檢查服務狀態
  - 查看日誌
  - 驗證環境配置
  - 測試連接性

step_3_根因分析:
  - 複現問題
  - 隔離變數
  - 檢查依賴服務
  - 查看監控指標

step_4_解決和驗證:
  - 實施修復
  - 測試驗證
  - 監控穩定性
  - 文檔記錄
```

---

## 🔍 常見問題排查

### 問題 1: 部署失敗 - GitHub Actions Pipeline 錯誤

#### 症狀
```
❌ GitHub Actions workflow failed
❌ Azure login step failed
❌ Docker push to ACR failed
```

#### 診斷步驟
```bash
# 1. 檢查 Service Principal 憑證
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# 2. 驗證 Service Principal 權限
az role assignment list \
  --assignee $AZURE_CLIENT_ID \
  --query "[].{Role:roleDefinitionName, Scope:scope}"

# 3. 檢查 GitHub Secrets 配置
# 前往 GitHub Repository → Settings → Secrets and variables → Actions
# 確認以下 secrets 存在且正確：
# - AZURE_CLIENT_ID
# - AZURE_CLIENT_SECRET
# - AZURE_TENANT_ID
# - AZURE_SUBSCRIPTION_ID
```

#### 解決方案
```yaml
scenario_1_憑證過期:
  problem: Service Principal secret 過期
  solution:
    1. 在 Azure Portal 重新生成 Client Secret
    2. 更新 GitHub Secrets 中的 AZURE_CLIENT_SECRET
    3. 重新運行 workflow

scenario_2_權限不足:
  problem: Service Principal 缺少所需權限
  solution:
    1. 確認需要的 Role: Contributor + AcrPush
    2. 執行: az role assignment create --assignee $SP_ID --role Contributor --scope /subscriptions/$SUB_ID
    3. 等待 5 分鐘讓權限生效
    4. 重新運行 workflow

scenario_3_ACR_權限:
  problem: 無法推送到 ACR
  solution:
    1. 確認 ACR 存在: az acr show --name acritpm{env}
    2. 授予權限: az role assignment create --assignee $SP_ID --role AcrPush --scope $ACR_ID
    3. 測試 ACR 登入: az acr login --name acritpm{env}
```

---

### 問題 2: 應用程式無法訪問 - HTTP 502/503 錯誤

#### 症狀
```
❌ https://app-itpm-{env}-001.azurewebsites.net 返回 502 Bad Gateway
❌ 或 503 Service Unavailable
```

#### 診斷步驟
```bash
# 1. 檢查 App Service 狀態
az webapp show \
  --name app-itpm-{env}-001 \
  --resource-group rg-itpm-{env} \
  --query "{Name:name, State:state, DefaultHostName:defaultHostName}"

# 2. 查看應用程式日誌
az webapp log tail \
  --name app-itpm-{env}-001 \
  --resource-group rg-itpm-{env}

# 3. 檢查 Docker 容器狀態
az webapp log show \
  --name app-itpm-{env}-001 \
  --resource-group rg-itpm-{env}

# 4. 驗證環境變數
bash .azure/tests/test-environment-config.sh {env}
```

#### 解決方案
```yaml
scenario_1_容器啟動失敗:
  symptoms:
    - 日誌顯示 "Container ... didn't respond to HTTP pings"
    - 容器持續重啟
  diagnosis:
    - 檢查環境變數: DATABASE_URL, NEXTAUTH_SECRET 等
    - 查看容器日誌中的錯誤訊息
  solution:
    1. 修正缺失的環境變數
    2. 重啟 App Service: az webapp restart --name app-itpm-{env}-001 --resource-group rg-itpm-{env}
    3. 監控啟動過程: az webapp log tail

scenario_2_資料庫連接失敗:
  symptoms:
    - 日誌顯示 "Can't reach database server"
    - 或 "getaddrinfo ENOTFOUND"
  diagnosis:
    - 檢查 DATABASE_URL 格式
    - 驗證 PostgreSQL 防火牆規則
    - 測試資料庫連接
  solution:
    1. 確認 DATABASE_URL 正確:
       postgresql://user:pass@psql-itpm-{env}-001.postgres.database.azure.com:5432/itpm
    2. 添加 App Service IP 到防火牆:
       az postgres flexible-server firewall-rule create \
         --name app-service-access \
         --start-ip-address 0.0.0.0 \
         --end-ip-address 255.255.255.255
    3. 或啟用 Azure 服務訪問:
       az postgres flexible-server firewall-rule create \
         --name AllowAzureServices \
         --start-ip-address 0.0.0.0 \
         --end-ip-address 0.0.0.0

scenario_3_記憶體溢出:
  symptoms:
    - 日誌顯示 "JavaScript heap out of memory"
    - 容器頻繁重啟
  diagnosis:
    - 檢查 App Service Plan 資源配置
    - 查看記憶體使用趨勢
  solution:
    1. 增加 Node.js heap size:
       az webapp config appsettings set \
         --settings NODE_OPTIONS="--max-old-space-size=4096"
    2. 或升級 App Service Plan:
       az appservice plan update --sku P2V2
```

---

### 問題 3: 資料庫連接錯誤

#### 症狀
```
❌ Error: getaddrinfo ENOTFOUND psql-itpm-{env}-001.postgres.database.azure.com
❌ Error: connect ETIMEDOUT
❌ Error: password authentication failed
```

#### 診斷步驟
```bash
# 1. 測試 DNS 解析
nslookup psql-itpm-{env}-001.postgres.database.azure.com

# 2. 測試 PostgreSQL 連接
psql "postgresql://username:password@psql-itpm-{env}-001.postgres.database.azure.com:5432/itpm?sslmode=require"

# 3. 檢查防火牆規則
az postgres flexible-server firewall-rule list \
  --name psql-itpm-{env}-001 \
  --resource-group rg-itpm-{env} \
  --query "[].{Name:name, StartIP:startIpAddress, EndIP:endIpAddress}"

# 4. 驗證 DATABASE_URL 格式
echo $DATABASE_URL
# 應該包含: ?sslmode=require
```

#### 解決方案
```yaml
scenario_1_防火牆阻擋:
  solution:
    # 允許 Azure 服務訪問
    az postgres flexible-server firewall-rule create \
      --resource-group rg-itpm-{env} \
      --name psql-itpm-{env}-001 \
      --rule-name AllowAzureServices \
      --start-ip-address 0.0.0.0 \
      --end-ip-address 0.0.0.0

scenario_2_密碼錯誤:
  solution:
    # 重置管理員密碼
    az postgres flexible-server update \
      --name psql-itpm-{env}-001 \
      --resource-group rg-itpm-{env} \
      --admin-password "NewSecurePassword123!"

    # 更新 Key Vault 密鑰
    bash .azure/scripts/helper/rotate-secret.sh {env} DATABASE-URL "postgresql://..."

scenario_3_SSL_連接問題:
  solution:
    # 確保 DATABASE_URL 包含 SSL 參數
    postgresql://user:pass@host:5432/db?sslmode=require

    # 或下載並使用 SSL 證書
    curl -o /tmp/ca-cert.crt https://dl.cacerts.digicert.com/DigiCertGlobalRootCA.crt.pem
    # 在連接字串中添加: ?sslrootcert=/tmp/ca-cert.crt
```

---

### 問題 4: Azure AD B2C 登入失敗

#### 症狀
```
❌ AADSTS50011: The reply URL does not match
❌ AADSTS700016: Application not found
❌ NextAuth callback error
```

#### 診斷步驟
```bash
# 1. 驗證 Azure AD B2C 配置
echo "Tenant: $AZURE_AD_B2C_TENANT_NAME"
echo "Client ID: $AZURE_AD_B2C_CLIENT_ID"
echo "Redirect URI: $NEXTAUTH_URL/api/auth/callback/azure-ad-b2c"

# 2. 檢查環境變數
bash .azure/tests/test-environment-config.sh {env}

# 3. 測試 B2C 端點
curl https://{tenant-name}.b2clogin.com/{tenant-name}.onmicrosoft.com/B2C_1_signupsignin/v2.0/.well-known/openid-configuration
```

#### 解決方案
```yaml
scenario_1_Redirect_URI_不匹配:
  problem: Reply URL 未在 B2C 應用程式中註冊
  solution:
    1. 前往 Azure Portal → Azure AD B2C → App registrations
    2. 選擇你的應用程式
    3. 前往 Authentication → Add platform → Web
    4. 添加 Redirect URI:
       - Dev: https://app-itpm-dev-001.azurewebsites.net/api/auth/callback/azure-ad-b2c
       - Staging: https://app-itpm-staging-001.azurewebsites.net/api/auth/callback/azure-ad-b2c
       - Prod: https://app-itpm-prod-001.azurewebsites.net/api/auth/callback/azure-ad-b2c
    5. 保存更改

scenario_2_Client_Secret_過期:
  problem: Azure AD B2C Client Secret 過期
  solution:
    1. Azure Portal → B2C → App registrations → Certificates & secrets
    2. 創建新的 Client Secret
    3. 更新 Key Vault:
       bash .azure/scripts/helper/rotate-secret.sh {env} AZUREADB2C-CLIENT-SECRET "new-secret"
    4. 重啟 App Service

scenario_3_租戶配置錯誤:
  problem: Tenant 名稱或 User Flow 錯誤
  solution:
    1. 確認正確的 Tenant 名稱（不含 .onmicrosoft.com）
    2. 確認 User Flow 名稱（B2C_1_signupsignin）
    3. 更新環境變數:
       AZURE_AD_B2C_TENANT_NAME="yourtenantname"
       AZURE_AD_B2C_PRIMARY_USER_FLOW="B2C_1_signupsignin"
```

---

### 問題 5: Blob Storage 文件上傳失敗

#### 症狀
```
❌ BlobServiceClient is not defined
❌ Error: Upload failed with status code 403
❌ Cannot read property 'upload' of undefined
```

#### 診斷步驟
```bash
# 1. 檢查 Storage Account 連接字串
echo $AZURE_STORAGE_ACCOUNT_NAME
echo $AZURE_STORAGE_ACCOUNT_KEY

# 2. 測試 Storage Account 訪問
az storage account show \
  --name stgitpm{env}001 \
  --resource-group rg-itpm-{env}

# 3. 檢查容器存在
az storage container list \
  --account-name stgitpm{env}001 \
  --auth-mode key

# 4. 驗證本地 Azurite（開發環境）
docker ps | grep azurite
curl http://localhost:10000/devstoreaccount1?comp=list
```

#### 解決方案
```yaml
scenario_1_本地開發_Azurite_未啟動:
  diagnosis:
    - docker ps 顯示 azurite 容器未運行
    - 或 .env 中 AZURE_STORAGE_USE_DEVELOPMENT=true 但 Azurite 不可訪問
  solution:
    1. 啟動 Azurite:
       docker-compose up -d azurite
    2. 驗證連接:
       curl http://localhost:10000/devstoreaccount1?comp=list
    3. 確認 .env 配置:
       AZURE_STORAGE_USE_DEVELOPMENT=true
       AZURE_STORAGE_CONNECTION_STRING="UseDevelopmentStorage=true;DevelopmentStorageProxyUri=http://localhost"

scenario_2_生產環境_權限不足:
  diagnosis:
    - 上傳失敗返回 403 Forbidden
    - Managed Identity 或 Account Key 權限不足
  solution:
    1. 確認 Storage Account Key 正確:
       az storage account keys list --account-name stgitpm{env}001
    2. 更新 Key Vault 密鑰:
       bash .azure/scripts/helper/rotate-secret.sh {env} STORAGE-ACCOUNT-KEY "new-key"
    3. 或配置 Managed Identity:
       az role assignment create \
         --assignee $MANAGED_IDENTITY_ID \
         --role "Storage Blob Data Contributor" \
         --scope /subscriptions/$SUB_ID/resourceGroups/rg-itpm-{env}/providers/Microsoft.Storage/storageAccounts/stgitpm{env}001

scenario_3_容器不存在:
  diagnosis:
    - 錯誤訊息顯示 "ContainerNotFound"
  solution:
    1. 創建所需容器:
       az storage container create --name quotes --account-name stgitpm{env}001
       az storage container create --name invoices --account-name stgitpm{env}001
    2. 設置訪問層級（Private）:
       az storage container set-permission --name quotes --public-access off
```

---

### 問題 6: Key Vault 訪問被拒

#### 症狀
```
❌ Error: Access denied to Key Vault
❌ The user, group or application does not have secrets get permission
```

#### 診斷步驟
```bash
# 1. 檢查 Managed Identity
az webapp identity show \
  --name app-itpm-{env}-001 \
  --resource-group rg-itpm-{env} \
  --query "principalId"

# 2. 檢查 Key Vault 訪問策略
az keyvault show \
  --name kv-itpm-{env} \
  --query "properties.accessPolicies[].{ObjectId:objectId, Permissions:permissions}"

# 3. 測試密鑰讀取
az keyvault secret show \
  --vault-name kv-itpm-{env} \
  --name ITPM-{ENV}-DATABASE-URL
```

#### 解決方案
```yaml
scenario_1_Managed_Identity_未啟用:
  solution:
    # 啟用 System-assigned Managed Identity
    az webapp identity assign \
      --name app-itpm-{env}-001 \
      --resource-group rg-itpm-{env}

scenario_2_缺少訪問策略:
  solution:
    # 獲取 Managed Identity Principal ID
    PRINCIPAL_ID=$(az webapp identity show \
      --name app-itpm-{env}-001 \
      --resource-group rg-itpm-{env} \
      --query "principalId" -o tsv)

    # 授予 Key Vault 權限
    az keyvault set-policy \
      --name kv-itpm-{env} \
      --object-id $PRINCIPAL_ID \
      --secret-permissions get list

scenario_3_RBAC_權限配置:
  solution:
    # 使用 RBAC 模式（推薦）
    az role assignment create \
      --assignee $PRINCIPAL_ID \
      --role "Key Vault Secrets User" \
      --scope /subscriptions/$SUB_ID/resourceGroups/rg-itpm-{env}/providers/Microsoft.KeyVault/vaults/kv-itpm-{env}
```

---

## 🛠️ 診斷工具和命令

### 快速診斷腳本
```bash
# 1. 完整連接性測試
bash .azure/tests/test-azure-connectivity.sh {env}

# 2. 環境配置驗證
bash .azure/tests/test-environment-config.sh {env}

# 3. 煙霧測試
bash .azure/tests/smoke-test.sh {env}

# 4. 部署驗證
bash .azure/scripts/helper/verify-deployment.sh {env}
```

### Azure CLI 診斷命令
```bash
# App Service 診斷
az webapp show --name app-itpm-{env}-001 --resource-group rg-itpm-{env}
az webapp list-runtimes --os linux
az webapp config show --name app-itpm-{env}-001 --resource-group rg-itpm-{env}

# 日誌查看
az webapp log tail --name app-itpm-{env}-001 --resource-group rg-itpm-{env}
az webapp log download --name app-itpm-{env}-001 --resource-group rg-itpm-{env}

# 資源狀態
az resource list --resource-group rg-itpm-{env} --output table

# 網路診斷
az network vnet list --resource-group rg-itpm-{env}
az postgres flexible-server firewall-rule list --name psql-itpm-{env}-001 --resource-group rg-itpm-{env}
```

---

## 📊 監控和告警

### 設置日誌級別
```bash
# 啟用詳細日誌
az webapp config appsettings set \
  --name app-itpm-{env}-001 \
  --resource-group rg-itpm-{env} \
  --settings LOG_LEVEL="debug" NODE_ENV="development"

# 啟用 Docker 容器日誌
az webapp log config \
  --name app-itpm-{env}-001 \
  --resource-group rg-itpm-{env} \
  --docker-container-logging filesystem

# 配置日誌保留
az webapp log config \
  --name app-itpm-{env}-001 \
  --resource-group rg-itpm-{env} \
  --failed-request-tracing true \
  --detailed-error-messages true
```

### 性能診斷
```bash
# 查看 CPU/記憶體使用
az monitor metrics list \
  --resource /subscriptions/$SUB_ID/resourceGroups/rg-itpm-{env}/providers/Microsoft.Web/sites/app-itpm-{env}-001 \
  --metric "CpuPercentage" "MemoryPercentage" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1M

# 查看請求統計
az monitor metrics list \
  --resource /subscriptions/$SUB_ID/resourceGroups/rg-itpm-{env}/providers/Microsoft.Web/sites/app-itpm-{env}-001 \
  --metric "Requests" "Http5xx" "ResponseTime" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M
```

---

## 🔄 回滾和恢復

### 緊急回滾流程
```bash
# 1. 快速 Slot Swap 回滾（Production）
az webapp deployment slot swap \
  --name app-itpm-prod-001 \
  --resource-group rg-itpm-prod \
  --slot staging \
  --target-slot production \
  --action swap

# 2. 部署舊版本鏡像
OLD_VERSION="v1.0.0"
az webapp config container set \
  --name app-itpm-{env}-001 \
  --resource-group rg-itpm-{env} \
  --docker-custom-image-name acritpm{env}.azurecr.io/itpm-web:$OLD_VERSION

# 3. 驗證回滾成功
bash .azure/tests/smoke-test.sh {env}
```

### 資料庫恢復
```bash
# 從備份恢復
az postgres flexible-server restore \
  --resource-group rg-itpm-{env} \
  --name psql-itpm-{env}-001-restored \
  --source-server psql-itpm-{env}-001 \
  --restore-time "2025-11-20T10:00:00Z"
```

---

## 📚 參考資源

### 內部文檔
- `docs/deployment/03-troubleshooting.md` - 詳細故障排查指南
- `docs/deployment/04-rollback.md` - 回滾程序文檔
- `.azure/README.md` - Azure 配置概覽

### 外部資源
- [Azure App Service 診斷文檔](https://docs.microsoft.com/azure/app-service/troubleshoot-diagnostic-logs)
- [Azure PostgreSQL 故障排查](https://docs.microsoft.com/azure/postgresql/flexible-server/how-to-troubleshoot-common-connection-issues)
- [Azure AD B2C 故障排查](https://docs.microsoft.com/azure/active-directory-b2c/troubleshoot)

---

## 📞 升級路徑

### Level 1: 自助診斷（0-30 分鐘）
1. 查看本指引和內部文檔
2. 執行診斷腳本
3. 查看應用程式日誌
4. 嘗試常見解決方案

### Level 2: Team 支持（30-60 分鐘）
1. 聯繫團隊成員協助
2. 在 Slack #devops-support 頻道發問
3. 查看歷史類似問題的解決方案

### Level 3: DevOps 升級（1 小時以上）
1. 發送詳細問題報告到 devops@company.com
2. 包含：錯誤訊息、日誌、已嘗試的解決方案
3. 標註影響範圍和緊急程度

### Level 4: Azure 支持（嚴重故障）
1. 在 Azure Portal 創建支持票證
2. 選擇適當的嚴重性級別
3. 提供完整的診斷資訊

---

**版本**: 1.0.0
**最後更新**: 2025-11-20
**維護者**: DevOps Team
