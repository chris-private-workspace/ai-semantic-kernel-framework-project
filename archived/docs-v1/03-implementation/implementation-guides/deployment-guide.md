# IPA Platform - Deployment Guide

**版本**: v1.0.0
**日期**: 2025-11-20
**目標**: 提供完整的Azure部署指南

---

## 📋 目錄

1. [前置準備](#前置準備)
2. [Azure 資源部署](#azure-資源部署)
3. [GitHub Actions 配置](#github-actions-配置)
4. [首次部署](#首次部署)
5. [驗證部署](#驗證部署)
6. [常見問題](#常見問題)

---

## 🎯 前置準備

### 1. 必需工具

```bash
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 或在 Windows 上
winget install -e --id Microsoft.AzureCLI

# 驗證安裝
az --version
```

### 2. Azure 登入

```bash
# 登入 Azure
az login

# 選擇訂閱 (如果有多個)
az account list --output table
az account set --subscription "<subscription-id>"

# 驗證當前訂閱
az account show
```

### 3. 創建 Service Principal (用於 GitHub Actions)

```bash
# 獲取訂閱 ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# 創建 Service Principal
az ad sp create-for-rbac \
  --name "sp-ipa-github-actions" \
  --role Contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --sdk-auth

# 輸出類似:
# {
#   "clientId": "xxx",
#   "clientSecret": "xxx",
#   "subscriptionId": "xxx",
#   "tenantId": "xxx",
#   ...
# }
```

**重要**: 保存完整的 JSON 輸出，稍後會用於 GitHub Secrets

---

## 🏗️ Azure 資源部署

### 選項 1: 使用自動化腳本 (推薦)

#### Staging 環境

```bash
# 進入腳本目錄
cd infrastructure/azure/scripts

# 給予執行權限
chmod +x deploy-staging.sh

# 執行部署
./deploy-staging.sh
```

**腳本會提示輸入**:
- PostgreSQL 管理員密碼 (至少 8 字符)

**部署時間**: 約 15-20 分鐘

#### Production 環境

```bash
chmod +x deploy-production.sh
./deploy-production.sh
```

---

### 選項 2: 使用 Azure Bicep

```bash
# 編譯 Bicep 模板
az bicep build --file infrastructure/azure/bicep/main.bicep

# 部署 Staging
az deployment sub create \
  --name ipa-staging-deployment \
  --location eastus \
  --template-file infrastructure/azure/bicep/main.bicep \
  --parameters \
    environment=staging \
    location=eastus \
    postgresAdminUsername=ipaadmin \
    postgresAdminPassword='<your-password>'

# 獲取輸出
az deployment sub show \
  --name ipa-staging-deployment \
  --query properties.outputs
```

---

### 選項 3: 手動部署 (分步驟)

<details>
<summary>展開查看手動部署步驟</summary>

#### 1. 創建 Resource Group

```bash
az group create \
  --name rg-ipa-staging-eastus \
  --location eastus \
  --tags Environment=staging Project=ipa-platform
```

#### 2. 創建 App Service Plan

```bash
az appservice plan create \
  --name asp-ipa-staging-eastus \
  --resource-group rg-ipa-staging-eastus \
  --location eastus \
  --is-linux \
  --sku B1
```

#### 3. 創建 Backend Web App

```bash
az webapp create \
  --name app-ipa-backend-staging \
  --resource-group rg-ipa-staging-eastus \
  --plan asp-ipa-staging-eastus \
  --runtime "PYTHON:3.11"
```

#### 4. 創建 PostgreSQL Server

```bash
az postgres flexible-server create \
  --name psql-ipa-staging-eastus \
  --resource-group rg-ipa-staging-eastus \
  --location eastus \
  --admin-user ipaadmin \
  --admin-password '<your-password>' \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 16
```

#### 5. 創建 Database

```bash
az postgres flexible-server db create \
  --resource-group rg-ipa-staging-eastus \
  --server-name psql-ipa-staging-eastus \
  --database-name ipa_platform_staging
```

#### 6. 創建 Redis

```bash
az redis create \
  --name redis-ipa-shared-eastus \
  --resource-group rg-ipa-staging-eastus \
  --location eastus \
  --sku Standard \
  --vm-size C1
```

#### 7. 創建 Service Bus

```bash
az servicebus namespace create \
  --name sb-ipa-staging-eastus \
  --resource-group rg-ipa-staging-eastus \
  --location eastus \
  --sku Standard

# 創建 Queue
az servicebus queue create \
  --name workflow-execution-queue \
  --namespace-name sb-ipa-staging-eastus \
  --resource-group rg-ipa-staging-eastus
```

#### 8. 創建 Key Vault

```bash
az keyvault create \
  --name kv-ipa-$(openssl rand -hex 4) \
  --resource-group rg-ipa-staging-eastus \
  --location eastus \
  --enable-soft-delete true
```

</details>

---

## 🔐 配置 Secrets

### 1. 在 Key Vault 中存儲連接字串

```bash
# 設置變數
KEYVAULT_NAME="<your-keyvault-name>"
RG_NAME="rg-ipa-staging-eastus"

# PostgreSQL 連接字串
POSTGRES_SERVER="psql-ipa-staging-eastus"
POSTGRES_USER="ipaadmin"
POSTGRES_PASSWORD="<your-password>"
POSTGRES_DB="ipa_platform_staging"

POSTGRES_CONNECTION_STRING="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}.postgres.database.azure.com/${POSTGRES_DB}?sslmode=require"

az keyvault secret set \
  --vault-name "$KEYVAULT_NAME" \
  --name "staging-database-connection-string" \
  --value "$POSTGRES_CONNECTION_STRING"

# Redis 連接字串
REDIS_NAME="redis-ipa-shared-eastus"
REDIS_KEY=$(az redis list-keys \
  --name "$REDIS_NAME" \
  --resource-group "$RG_NAME" \
  --query primaryKey -o tsv)

REDIS_CONNECTION_STRING="${REDIS_NAME}.redis.cache.windows.net:6380,password=${REDIS_KEY},ssl=True,abortConnect=False,db=1"

az keyvault secret set \
  --vault-name "$KEYVAULT_NAME" \
  --name "staging-redis-connection-string" \
  --value "$REDIS_CONNECTION_STRING"

# Service Bus 連接字串
SERVICEBUS_NAMESPACE="sb-ipa-staging-eastus"
SERVICEBUS_CONNECTION_STRING=$(az servicebus namespace authorization-rule keys list \
  --resource-group "$RG_NAME" \
  --namespace-name "$SERVICEBUS_NAMESPACE" \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString -o tsv)

az keyvault secret set \
  --vault-name "$KEYVAULT_NAME" \
  --name "staging-servicebus-connection-string" \
  --value "$SERVICEBUS_CONNECTION_STRING"

# JWT Secret (生成隨機密鑰)
JWT_SECRET=$(openssl rand -base64 32)

az keyvault secret set \
  --vault-name "$KEYVAULT_NAME" \
  --name "staging-jwt-secret-key" \
  --value "$JWT_SECRET"
```

---

## 🔧 配置 App Service

### 1. 啟用 Managed Identity

```bash
BACKEND_APP_NAME="app-ipa-backend-staging"

# 啟用系統分配的 Managed Identity
PRINCIPAL_ID=$(az webapp identity assign \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RG_NAME" \
  --query principalId -o tsv)

# 授予 Key Vault 訪問權限
az keyvault set-policy \
  --name "$KEYVAULT_NAME" \
  --object-id "$PRINCIPAL_ID" \
  --secret-permissions get list
```

### 2. 配置 App Settings

```bash
# 從 Key Vault 引用 secrets
az webapp config appsettings set \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RG_NAME" \
  --settings \
    ENVIRONMENT="staging" \
    DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://${KEYVAULT_NAME}.vault.azure.net/secrets/staging-database-connection-string/)" \
    REDIS_URL="@Microsoft.KeyVault(SecretUri=https://${KEYVAULT_NAME}.vault.azure.net/secrets/staging-redis-connection-string/)" \
    SERVICEBUS_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://${KEYVAULT_NAME}.vault.azure.net/secrets/staging-servicebus-connection-string/)" \
    JWT_SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://${KEYVAULT_NAME}.vault.azure.net/secrets/staging-jwt-secret-key/)"
```

---

## 🚀 GitHub Actions 配置

### 1. 在 GitHub Repository 中設置 Secrets

前往: `Settings` → `Secrets and variables` → `Actions`

創建以下 Secrets:

| Secret 名稱 | 值來源 | 說明 |
|------------|-------|------|
| `AZURE_CREDENTIALS_STAGING` | Service Principal JSON | 完整的 SP JSON (來自前置準備步驟 3) |
| `AZURE_CREDENTIALS_PRODUCTION` | Service Principal JSON | Production 環境 SP |
| `AZURE_KEYVAULT_NAME` | Key Vault 名稱 | 例如: kv-ipa-abc123 |

### 2. 創建 Environment

1. 前往 `Settings` → `Environments`
2. 創建 `staging` environment
3. 創建 `production` environment (可選添加 approval required)

### 3. 驗證 Workflow 文件

確認以下文件存在:
- `.github/workflows/backend-staging-deploy.yml`
- `.github/workflows/backend-production-deploy.yml`
- `.github/workflows/frontend-staging-deploy.yml`
- `.github/workflows/frontend-production-deploy.yml`

---

## 📦 首次部署

### 1. 手動觸發部署

**方式 1: 推送到分支**

```bash
# Staging: 推送到 develop 分支
git checkout develop
git push origin develop

# Production: 推送到 main 分支
git checkout main
git push origin main
```

**方式 2: 手動觸發 Workflow**

1. 前往 GitHub Repository
2. 點擊 `Actions` tab
3. 選擇 workflow (例如: "Backend - Deploy to Staging")
4. 點擊 `Run workflow`
5. 選擇分支並點擊 `Run workflow`

### 2. 監控部署進度

- 在 GitHub Actions tab 查看實時日誌
- 檢查每個步驟的狀態
- 查看測試結果和覆蓋率

### 3. 運行數據庫遷移

```bash
# 手動運行 (如果 CI/CD 中未自動執行)
az webapp ssh --name app-ipa-backend-staging --resource-group rg-ipa-staging-eastus

# 在 App Service SSH 中
cd /home/site/wwwroot
alembic upgrade head
```

---

## ✅ 驗證部署

### 1. Health Check

```bash
# Backend
curl https://app-ipa-backend-staging.azurewebsites.net/health

# 預期輸出:
# {
#   "status": "healthy",
#   "version": "0.1.1"
# }

# Frontend
curl https://app-ipa-frontend-staging.azurewebsites.net
```

### 2. Database 連接測試

```bash
# SSH 到 App Service
az webapp ssh --name app-ipa-backend-staging --resource-group rg-ipa-staging-eastus

# 測試數據庫連接
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    result = conn.execute('SELECT version()')
    print(result.fetchone())
"
```

### 3. Redis 連接測試

```bash
python -c "
import os
import redis
r = redis.from_url(os.environ['REDIS_URL'])
r.set('test_key', 'test_value')
print(r.get('test_key'))
"
```

### 4. Service Bus 測試

```bash
python -c "
import os
from azure.servicebus import ServiceBusClient
conn_str = os.environ['SERVICEBUS_CONNECTION_STRING']
client = ServiceBusClient.from_connection_string(conn_str)
print('Service Bus connection successful')
"
```

### 5. Application Insights 驗證

1. 前往 Azure Portal
2. 搜尋並開啟 Application Insights: `appi-ipa-staging-eastus`
3. 查看 `Live Metrics` - 應該看到實時數據
4. 查看 `Failures` - 檢查是否有錯誤
5. 查看 `Performance` - 檢查響應時間

---

## 🔍 監控與日誌

### 查看應用程式日誌

```bash
# 實時查看日誌
az webapp log tail \
  --name app-ipa-backend-staging \
  --resource-group rg-ipa-staging-eastus

# 下載日誌
az webapp log download \
  --name app-ipa-backend-staging \
  --resource-group rg-ipa-staging-eastus \
  --log-file app-logs.zip
```

### Application Insights 查詢

```kusto
// 查看最近的請求
requests
| where timestamp > ago(1h)
| project timestamp, name, resultCode, duration
| order by timestamp desc

// 查看錯誤
exceptions
| where timestamp > ago(24h)
| summarize count() by type, outerMessage

// 查看慢查詢
dependencies
| where type == "SQL"
| where duration > 1000
| project timestamp, name, duration
```

---

## 🔄 更新和回滾

### 部署新版本

```bash
# 觸發 CI/CD (推送到對應分支)
git checkout develop
git pull
# 做你的更改
git add .
git commit -m "feat: new feature"
git push origin develop
```

### 回滾 (使用 Deployment Slots)

```bash
# Production 使用 Blue-Green deployment
# 回滾只需交換 slots

az webapp deployment slot swap \
  --name app-ipa-backend-prod \
  --resource-group rg-ipa-prod-eastus \
  --slot staging \
  --target-slot production
```

### 回滾到特定版本

```bash
# 查看部署歷史
az webapp deployment list-publishing-credentials \
  --name app-ipa-backend-staging \
  --resource-group rg-ipa-staging-eastus

# Re-deploy 特定 commit
git checkout <commit-hash>
git push origin develop --force  # 觸發 CI/CD
```

---

## ❓ 常見問題

### Q1: 部署失敗，提示 "Could not find setup.py"

**A**: 確保你的 `requirements.txt` 在正確的位置，並且 GitHub Actions workflow 的 `working-directory` 配置正確。

### Q2: Health check 失敗

**A**: 檢查:
1. App Service 是否正確啟動: `az webapp log tail`
2. 環境變數是否正確配置
3. 數據庫遷移是否成功執行

### Q3: Database 連接錯誤

**A**: 檢查:
1. PostgreSQL firewall 規則是否允許 App Service outbound IP
2. 連接字串是否正確
3. PostgreSQL server 是否在運行

### Q4: Key Vault 訪問被拒絕

**A**: 確保:
1. App Service Managed Identity 已啟用
2. Key Vault access policy 已正確配置
3. 使用 `@Microsoft.KeyVault()` 語法引用 secrets

### Q5: GitHub Actions 提示權限不足

**A**: 檢查:
1. Service Principal 是否有 Contributor 權限
2. `AZURE_CREDENTIALS` secret 是否正確配置
3. SP 是否已過期 (需要輪換)

---

## 📊 部署檢查清單

### 部署前

- [ ] Azure CLI 已安裝並登入
- [ ] Service Principal 已創建
- [ ] GitHub Secrets 已配置
- [ ] 環境變數已檢查
- [ ] 數據庫遷移腳本已準備

### 部署中

- [ ] 所有 Azure 資源創建成功
- [ ] Secrets 存儲在 Key Vault
- [ ] App Service Managed Identity 已配置
- [ ] CI/CD workflow 運行成功
- [ ] 所有測試通過

### 部署後

- [ ] Health check 端點返回 200
- [ ] 數據庫連接正常
- [ ] Redis 連接正常
- [ ] Service Bus 連接正常
- [ ] Application Insights 接收數據
- [ ] 日誌正常輸出
- [ ] 性能指標正常

---

## 📚 相關資源

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [GitHub Actions for Azure](https://github.com/Azure/actions)
- [Azure Bicep Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)
- [Application Insights Documentation](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)

---

**文檔版本**: v1.0.0
**最後更新**: 2025-11-20
**維護者**: DevOps Team
