# Azure Service Principal 設置指南

本文檔提供完整的 Azure Service Principal 設置步驟，用於 CI/CD 流程的自動化部署。

## 📋 目錄

- [什麼是 Service Principal](#什麼是-service-principal)
- [前置要求](#前置要求)
- [創建 Service Principal](#創建-service-principal)
- [配置權限](#配置權限)
- [設置 GitHub Secrets](#設置-github-secrets)
- [驗證配置](#驗證配置)
- [故障排除](#故障排除)

---

## 🎯 什麼是 Service Principal

**Service Principal** 是 Azure AD 中的一個身份，用於應用程序或服務進行身份驗證和授權，而不需要使用用戶憑證。

### 使用場景
- CI/CD 管道自動部署到 Azure
- 自動化腳本訪問 Azure 資源
- 應用程序訪問 Azure 服務

---

## ✅ 前置要求

### 權限要求
- Azure 訂閱的 **所有者 (Owner)** 或 **貢獻者 (Contributor)** 權限
- Azure AD 的 **應用程序管理員** 權限（創建 App Registration）

### 工具安裝
```bash
# 安裝 Azure CLI
# Windows (使用管理員權限)
winget install -e --id Microsoft.AzureCLI

# 驗證安裝
az --version

# 登錄 Azure
az login
```

---

## 🚀 創建 Service Principal

### 方法 1: 使用 Azure CLI（推薦）

#### 1. 設置變量
```bash
# 設置訂閱 ID（從 Azure Portal 獲取）
$SUBSCRIPTION_ID = "your-subscription-id"
$SP_NAME = "sp-ipa-platform-cicd"
$RESOURCE_GROUP = "rg-ipa-platform"
```

#### 2. 創建 Service Principal
```bash
# 登錄到特定訂閱
az account set --subscription $SUBSCRIPTION_ID

# 創建 Service Principal 並分配 Contributor 角色
az ad sp create-for-rbac `
  --name $SP_NAME `
  --role Contributor `
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP `
  --sdk-auth
```

#### 3. 保存輸出
**重要**: 輸出內容僅顯示一次，請立即保存到安全位置。

輸出示例：
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### 方法 2: 使用 Azure Portal

#### 1. 註冊應用程序
1. 進入 **Azure Portal** → **Azure Active Directory**
2. 左側菜單選擇 **App registrations** → **New registration**
3. 填寫信息：
   - **Name**: `sp-ipa-platform-cicd`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: 留空
4. 點擊 **Register**

#### 2. 創建 Client Secret
1. 進入剛創建的 App → **Certificates & secrets**
2. 點擊 **New client secret**
3. 填寫：
   - **Description**: `GitHub Actions CI/CD`
   - **Expires**: 選擇有效期（建議 24 months）
4. 點擊 **Add**
5. **立即複製 Value**（只顯示一次！）

#### 3. 記錄必要信息
在 **App Overview** 頁面記錄：
- **Application (client) ID**
- **Directory (tenant) ID**

---

## 🔒 配置權限

### 1. 分配角色到 Service Principal

```bash
# 分配 Contributor 角色到特定資源組
az role assignment create `
  --assignee $CLIENT_ID `
  --role "Contributor" `
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP

# 如需訪問 Key Vault，分配額外權限
az role assignment create `
  --assignee $CLIENT_ID `
  --role "Key Vault Secrets Officer" `
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/kv-ipa-platform
```

### 2. 驗證角色分配

```bash
# 列出 Service Principal 的所有角色
az role assignment list --assignee $CLIENT_ID --output table
```

### 3. 推薦的權限配置

| 資源類型 | 推薦角色 | 用途 |
|---------|---------|------|
| Resource Group | Contributor | 創建和管理資源 |
| App Service | Website Contributor | 部署應用 |
| PostgreSQL | Contributor | 管理數據庫 |
| Key Vault | Key Vault Secrets Officer | 讀取/寫入 secrets |
| Service Bus | Azure Service Bus Data Owner | 管理消息隊列 |

---

## 🔐 設置 GitHub Secrets

### 1. 進入 GitHub Repository Settings
1. 打開你的 GitHub 倉庫
2. **Settings** → **Secrets and variables** → **Actions**
3. 點擊 **New repository secret**

### 2. 添加以下 Secrets

#### 必需的 Secrets

| Secret Name | Value | 說明 |
|------------|-------|------|
| `AZURE_CREDENTIALS` | 完整的 JSON 輸出 | Service Principal 完整憑證 |
| `AZURE_SUBSCRIPTION_ID` | `xxxxxxxx-xxxx-...` | Azure 訂閱 ID |
| `AZURE_TENANT_ID` | `xxxxxxxx-xxxx-...` | Azure AD 租戶 ID |
| `AZURE_CLIENT_ID` | `xxxxxxxx-xxxx-...` | Service Principal 客戶端 ID |
| `AZURE_CLIENT_SECRET` | `xxxxx...` | Service Principal 客戶端密鑰 |

#### 可選的 Secrets（用於應用配置）

| Secret Name | Value | 說明 |
|------------|-------|------|
| `AZURE_APP_SERVICE_NAME` | `app-ipa-platform` | App Service 名稱 |
| `AZURE_RESOURCE_GROUP` | `rg-ipa-platform` | 資源組名稱 |
| `DATABASE_CONNECTION_STRING` | `postgresql://...` | 數據庫連接字符串 |
| `REDIS_CONNECTION_STRING` | `redis://...` | Redis 連接字符串 |

### 3. 設置示例

```bash
# AZURE_CREDENTIALS 的完整 JSON 格式
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

---

## ✅ 驗證配置

### 1. 本地測試 Service Principal

```bash
# 使用 Service Principal 登錄
az login --service-principal `
  --username $CLIENT_ID `
  --password $CLIENT_SECRET `
  --tenant $TENANT_ID

# 測試訪問訂閱
az account show

# 測試列出資源
az resource list --resource-group $RESOURCE_GROUP --output table

# 登出
az logout
```

### 2. 測試 GitHub Actions

創建測試工作流 `.github/workflows/test-azure-connection.yml`：

```yaml
name: Test Azure Connection

on:
  workflow_dispatch:  # 手動觸發

jobs:
  test-connection:
    runs-on: ubuntu-latest
    
    steps:
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Test Azure CLI
        run: |
          az account show
          az group list --output table
      
      - name: Azure Logout
        run: az logout
```

運行此工作流驗證連接：
1. 進入 GitHub → **Actions** → **Test Azure Connection**
2. 點擊 **Run workflow**
3. 查看執行日誌

---

## 🛠️ 故障排除

### 問題 1: "Insufficient privileges to complete the operation"

**原因**: Service Principal 沒有足夠權限

**解決方法**:
```bash
# 檢查當前角色
az role assignment list --assignee $CLIENT_ID --output table

# 分配更高級別的角色
az role assignment create `
  --assignee $CLIENT_ID `
  --role "Contributor" `
  --scope /subscriptions/$SUBSCRIPTION_ID
```

### 問題 2: "The client secret has expired"

**原因**: Client Secret 過期

**解決方法**:
1. 進入 Azure Portal → Azure AD → App registrations
2. 選擇你的 App → **Certificates & secrets**
3. 刪除舊的 secret，創建新的
4. 更新 GitHub Secrets

### 問題 3: "Failed to authenticate with Azure"

**原因**: 憑證信息錯誤

**解決方法**:
```bash
# 驗證 JSON 格式是否正確
echo $AZURE_CREDENTIALS | python -m json.tool

# 確認各項值是否正確
az ad sp show --id $CLIENT_ID
```

### 問題 4: "Resource not found"

**原因**: Service Principal 沒有訪問特定資源的權限

**解決方法**:
```bash
# 檢查資源是否存在
az resource list --name $RESOURCE_NAME --output table

# 分配特定資源的權限
az role assignment create `
  --assignee $CLIENT_ID `
  --role "Contributor" `
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$APP_NAME"
```

---

## 🔄 Service Principal 生命週期管理

### 定期輪換 Client Secret

建議每 **6-12 個月** 輪換一次：

```bash
# 創建新的 Client Secret
az ad sp credential reset `
  --id $CLIENT_ID `
  --append `
  --years 2

# 更新 GitHub Secrets
# 驗證新 secret 可用後，刪除舊的
az ad sp credential delete `
  --id $CLIENT_ID `
  --key-id $OLD_KEY_ID
```

### 審計 Service Principal 使用

```bash
# 查看 Service Principal 的所有活動
az monitor activity-log list `
  --caller $CLIENT_ID `
  --start-time 2025-11-01 `
  --output table
```

---

## 📚 參考資料

- [Azure Service Principal 官方文檔](https://learn.microsoft.com/azure/active-directory/develop/app-objects-and-service-principals)
- [GitHub Actions Azure Login](https://github.com/marketplace/actions/azure-login)
- [Azure RBAC 角色](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles)

---

## 🆘 需要幫助？

如果遇到問題：
1. 檢查 [故障排除](#故障排除) 部分
2. 查看 Azure Portal 的 Activity Log
3. 聯繫 DevOps 團隊

---

**安全提示**: 
- 🔒 絕不將 Service Principal 憑證提交到代碼庫
- 🔒 定期輪換 Client Secret
- 🔒 使用最小權限原則
- 🔒 啟用 Azure AD 條件訪問策略
