# 多環境 Azure 部署策略

**創建時間**: 2025-11-21 17:30 (UTC+8)
**場景**: 個人 Azure 測試環境 → 公司 Azure 生產環境
**目標**: 建立無縫的開發、測試、部署流程

---

## 當前情況分析

### 環境限制

**個人 Azure 環境**（當前測試環境）:
- ✅ 可以自由訪問和配置
- ✅ 適合開發和測試部署流程
- ✅ 可以驗證應用程式基本功能
- ⚠️ 無法連接公司 Azure AD（Entra ID）
- ⚠️ 無法測試真實的 SSO 登入流程

**公司 Azure 環境**（目標生產環境）:
- ✅ 提供真實的 Azure AD SSO
- ✅ 正式的生產環境資源
- ❌ 開發機器無法登入（權限/網路限制）
- ❌ 需要特殊權限或跳板機訪問
- ❌ 配置變更可能需要審批流程

### 技術架構問題

**Azure AD B2C vs Azure AD (Entra ID)**:

當前代碼使用的是 **Azure AD B2C**，但您的需求是 **Azure AD (Entra ID) SSO**。

**關鍵差異**:

| 特性 | Azure AD B2C | Azure AD (Entra ID) |
|------|--------------|---------------------|
| 用途 | 外部用戶身份管理 | 企業內部員工 SSO |
| 用戶來源 | 自定義註冊流程 | 公司 Active Directory |
| 多租戶 | 支援（B2C 租戶） | 單租戶（公司 AD） |
| 自定義 UI | 完全自定義 | 有限自定義 |
| 成本 | 按月活躍用戶計費 | 包含在 M365 授權 |
| **NextAuth Provider** | `AzureADB2C` | `AzureAD` |

**您的需求**: 使用公司 Azure AD (Entra ID) 進行企業 SSO

---

## 問題 1 修正：從 Azure AD B2C 遷移到 Azure AD

### 當前配置（錯誤）

**代碼位置**: `apps/web/src/auth.ts:42, 104-119`

```typescript
import AzureADB2C from 'next-auth/providers/azure-ad-b2c';

// ...

AzureADB2C({
  clientId: process.env.AUTH_AZURE_AD_B2C_ID,
  clientSecret: process.env.AUTH_AZURE_AD_B2C_SECRET,
  issuer: process.env.AUTH_AZURE_AD_B2C_ISSUER,
  // ...
})
```

### 正確配置（Azure AD / Entra ID）

**應該使用**:

```typescript
import AzureAD from 'next-auth/providers/azure-ad';

// ...

AzureAD({
  clientId: process.env.AZURE_AD_CLIENT_ID!,
  clientSecret: process.env.AZURE_AD_CLIENT_SECRET!,
  tenantId: process.env.AZURE_AD_TENANT_ID!,
  authorization: {
    params: {
      scope: 'openid profile email User.Read',
    },
  },
})
```

**環境變數差異**:

```bash
# ❌ 舊的（Azure AD B2C）
AUTH_AZURE_AD_B2C_ID=...
AUTH_AZURE_AD_B2C_SECRET=...
AUTH_AZURE_AD_B2C_ISSUER=...

# ✅ 新的（Azure AD / Entra ID）
AZURE_AD_CLIENT_ID=...
AZURE_AD_CLIENT_SECRET=...
AZURE_AD_TENANT_ID=...
```

---

## 多環境部署策略

### 策略 A: 環境變數隔離 - **推薦**

**核心概念**: 使用不同的環境變數文件分離個人和公司環境配置

#### 文件結構

```
project-root/
├── .env.development.local       # 本地開發（密碼登入）
├── .env.personal-azure          # 個人 Azure 測試環境
├── .env.company-azure.template  # 公司 Azure 配置模板（不含敏感數據）
└── .env.production              # 生產環境（由 Azure App Service 提供）
```

#### 1. `.env.development.local`（本地開發）

```bash
# ========================================
# 本地開發環境（密碼登入為主）
# ========================================

NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000

# 資料庫（本地 Docker）
DATABASE_URL="postgresql://postgres:localdev123@localhost:5434/itpm_dev"

# NextAuth.js
NEXTAUTH_SECRET="local-dev-secret-change-in-production"
NEXTAUTH_URL="http://localhost:3000"

# Azure AD - 停用（本地開發使用密碼登入）
# AZURE_AD_CLIENT_ID=
# AZURE_AD_CLIENT_SECRET=
# AZURE_AD_TENANT_ID=

# 郵件服務（Mailhog）
SMTP_HOST=localhost
SMTP_PORT=1025
```

#### 2. `.env.personal-azure`（個人 Azure 測試）

```bash
# ========================================
# 個人 Azure 測試環境
# ========================================

NODE_ENV=production
NEXT_PUBLIC_APP_URL=https://app-itpm-dev-001.azurewebsites.net

# 資料庫（Azure PostgreSQL）
DATABASE_URL="postgresql://itpmadmin:***@psql-itpm-dev-001.postgres.database.azure.com:5432/itpm_dev?sslmode=require"

# NextAuth.js
NEXTAUTH_SECRET="***"
NEXTAUTH_URL="https://app-itpm-dev-001.azurewebsites.net"

# Azure AD - 個人租戶（僅用於測試基礎設施）
AZURE_AD_CLIENT_ID="<your-personal-ad-app-id>"
AZURE_AD_CLIENT_SECRET="<your-personal-ad-secret>"
AZURE_AD_TENANT_ID="<your-personal-tenant-id>"

# 郵件服務（SendGrid）
SENDGRID_API_KEY="***"
SENDGRID_FROM_EMAIL="noreply@personal-test.com"

# 儲存（Azure Blob）
AZURE_STORAGE_ACCOUNT_NAME="***"
AZURE_STORAGE_ACCOUNT_KEY="***"
```

#### 3. `.env.company-azure.template`（公司環境模板）

```bash
# ========================================
# 公司 Azure 生產環境配置模板
# 注意：此文件不包含真實密鑰，僅作為配置參考
# ========================================

NODE_ENV=production
NEXT_PUBLIC_APP_URL=https://itpm.company.com  # 公司實際域名

# 資料庫（公司 Azure PostgreSQL）
DATABASE_URL="postgresql://<company-db-user>:<password>@<company-db-host>:5432/itpm_prod?sslmode=require"

# NextAuth.js
NEXTAUTH_SECRET="<generate-with-openssl-rand-base64-32>"
NEXTAUTH_URL="https://itpm.company.com"

# Azure AD - 公司租戶（真實的公司 SSO）
AZURE_AD_CLIENT_ID="<company-ad-app-id>"
AZURE_AD_CLIENT_SECRET="<company-ad-secret>"
AZURE_AD_TENANT_ID="<company-tenant-id>"  # 公司的 Tenant ID

# 郵件服務（公司 SMTP 或 SendGrid）
SENDGRID_API_KEY="<company-sendgrid-key>"
SENDGRID_FROM_EMAIL="noreply@company.com"

# 儲存（公司 Azure Blob）
AZURE_STORAGE_ACCOUNT_NAME="<company-storage-account>"
AZURE_STORAGE_ACCOUNT_KEY="<company-storage-key>"

# Application Insights（公司監控）
APPINSIGHTS_INSTRUMENTATIONKEY="<company-insights-key>"
```

#### 4. 部署腳本

**`scripts/deploy-personal.sh`**（部署到個人 Azure）:

```bash
#!/bin/bash
set -e

echo "🚀 部署到個人 Azure 測試環境..."

# 1. 載入個人環境變數
export $(cat .env.personal-azure | grep -v '^#' | xargs)

# 2. 登入個人 Azure
az login --tenant $AZURE_AD_TENANT_ID

# 3. 構建 Docker 映像
docker build -t acritpmdev.azurecr.io/itpm-web:test-$(date +%Y%m%d-%H%M%S) -f docker/Dockerfile .

# 4. 推送到 ACR
docker push acritpmdev.azurecr.io/itpm-web:test-$(date +%Y%m%d-%H%M%S)

# 5. 更新 App Service
az webapp config container set \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --docker-custom-image-name acritpmdev.azurecr.io/itpm-web:test-$(date +%Y%m%d-%H%M%S)

# 6. 重啟 App Service
az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev

echo "✅ 部署完成！"
```

**`scripts/deploy-company.sh`**（部署到公司 Azure - 需要公司網路訪問）:

```bash
#!/bin/bash
set -e

echo "🏢 部署到公司 Azure 生產環境..."

# 1. 檢查是否在公司網路（或使用 VPN/跳板機）
echo "⚠️  警告：此腳本需要公司網路訪問權限"
read -p "確認已連接到公司網路？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 2. 登入公司 Azure（需要公司帳號）
az login --tenant <COMPANY_TENANT_ID>

# 3. 構建生產映像
docker build -t <company-acr>.azurecr.io/itpm-web:prod-$(date +%Y%m%d-%H%M%S) -f docker/Dockerfile .

# 4. 推送到公司 ACR
docker push <company-acr>.azurecr.io/itpm-web:prod-$(date +%Y%m%d-%H%M%S)

# 5. 更新公司 App Service
az webapp config container set \
  --name <company-app-service> \
  --resource-group <company-rg> \
  --docker-custom-image-name <company-acr>.azurecr.io/itpm-web:prod-$(date +%Y%m%d-%H%M%S)

# 6. 更新環境變數（從 Azure Key Vault 讀取）
az webapp config appsettings set \
  --name <company-app-service> \
  --resource-group <company-rg> \
  --settings @company-app-settings.json

# 7. 重啟 App Service
az webapp restart --name <company-app-service> --resource-group <company-rg>

echo "✅ 公司環境部署完成！"
```

---

### 策略 B: 使用 Azure DevOps / GitHub Actions CI/CD - **生產推薦**

**核心概念**: 自動化部署流程，避免手動操作和本地環境限制

#### GitHub Actions Workflow

**`.github/workflows/deploy-to-company-azure.yml`**:

```yaml
name: Deploy to Company Azure Production

on:
  push:
    branches:
      - main  # 或 production 分支
  workflow_dispatch:  # 允許手動觸發

env:
  AZURE_WEBAPP_NAME: itpm-prod
  AZURE_RESOURCE_GROUP: rg-itpm-prod
  DOCKER_IMAGE_NAME: company-acr.azurecr.io/itpm-web

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment: production  # 使用 GitHub Environments 管理密鑰

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Azure Container Registry
        uses: docker/login-action@v2
        with:
          registry: company-acr.azurecr.io
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Build Docker image
        run: |
          docker build \
            -t ${{ env.DOCKER_IMAGE_NAME }}:${{ github.sha }} \
            -t ${{ env.DOCKER_IMAGE_NAME }}:latest \
            -f docker/Dockerfile .

      - name: Push Docker image
        run: |
          docker push ${{ env.DOCKER_IMAGE_NAME }}:${{ github.sha }}
          docker push ${{ env.DOCKER_IMAGE_NAME }}:latest

      - name: Log in to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ env.AZURE_WEBAPP_NAME }}
          resource-group: ${{ env.AZURE_RESOURCE_GROUP }}
          images: ${{ env.DOCKER_IMAGE_NAME }}:${{ github.sha }}

      - name: Update App Settings (from Key Vault)
        run: |
          az webapp config appsettings set \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --settings \
              AZURE_AD_CLIENT_ID="@Microsoft.KeyVault(SecretUri=${{ secrets.KEYVAULT_URI }}/secrets/AZURE-AD-CLIENT-ID/)" \
              AZURE_AD_CLIENT_SECRET="@Microsoft.KeyVault(SecretUri=${{ secrets.KEYVAULT_URI }}/secrets/AZURE-AD-CLIENT-SECRET/)" \
              DATABASE_URL="@Microsoft.KeyVault(SecretUri=${{ secrets.KEYVAULT_URI }}/secrets/DATABASE-URL/)"

      - name: Run database migrations
        run: |
          # 使用 Azure CLI 執行遠端命令或 SSH 到容器
          az webapp ssh --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --command "cd /app && pnpm db:migrate"

      - name: Restart App Service
        run: |
          az webapp restart \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }}

      - name: Health Check
        run: |
          sleep 30
          curl -f https://itpm.company.com/api/health || exit 1
```

**GitHub Secrets 配置**:

在 GitHub Repository Settings → Secrets and variables → Actions 中添加：

```
AZURE_CREDENTIALS         # Azure Service Principal credentials (JSON)
ACR_USERNAME              # Azure Container Registry 用戶名
ACR_PASSWORD              # Azure Container Registry 密碼
KEYVAULT_URI              # Azure Key Vault URI
```

**優點**:
- ✅ 完全自動化，無需本地登入公司 Azure
- ✅ GitHub Actions runner 可以訪問公司網路（透過 Self-hosted runner）
- ✅ 所有密鑰存儲在 GitHub Secrets 和 Azure Key Vault
- ✅ 完整的部署歷史和回滾能力
- ✅ 支援多環境部署（dev, staging, prod）

---

### 策略 C: 使用跳板機（Bastion Host）- **手動部署備用方案**

**場景**: 當無法使用 CI/CD 時，透過公司內部跳板機進行部署

#### 架構

```
本地開發機
  → Git Push → GitHub
  → 跳板機（公司內網，有 Azure 訪問權限）
  → 執行部署腳本 → 公司 Azure
```

#### 實施步驟

1. **準備跳板機環境**:
   ```bash
   # SSH 到跳板機
   ssh user@company-bastion.internal

   # 安裝必要工具
   sudo apt update
   sudo apt install -y docker.io azure-cli git

   # 登入公司 Azure
   az login --tenant <COMPANY_TENANT_ID>
   ```

2. **在跳板機上克隆倉庫**:
   ```bash
   git clone https://github.com/company/itpm-webapp.git
   cd itpm-webapp
   ```

3. **執行部署**:
   ```bash
   # 拉取最新代碼
   git pull origin main

   # 執行部署腳本
   ./scripts/deploy-company.sh
   ```

**優點**:
- ✅ 不需要本地訪問公司 Azure
- ✅ 跳板機在公司內網，有完整權限

**缺點**:
- ⚠️ 需要手動操作
- ⚠️ 跳板機需要維護和權限管理

---

## 測試流程建議

### 階段 1: 本地開發（完全隔離）

**目標**: 驗證業務邏輯和 UI，不依賴 Azure

```bash
# 使用 .env.development.local
pnpm dev

# 測試項目：
# - 密碼登入 ✅
# - 資料庫操作 ✅
# - UI 功能 ✅
# - API 端點 ✅
```

**跳過測試**: Azure AD SSO（因為無法連接公司 AD）

---

### 階段 2: 個人 Azure 測試（基礎設施驗證）

**目標**: 驗證 Docker 映像、Azure 服務整合、部署流程

```bash
# 使用 .env.personal-azure
./scripts/deploy-personal.sh

# 測試項目：
# - Docker 映像構建 ✅
# - Azure App Service 部署 ✅
# - Azure PostgreSQL 連接 ✅
# - Azure Blob Storage ✅
# - 密碼登入（生產環境） ✅
```

**跳過測試**:
- Azure AD SSO（使用個人租戶，無法模擬公司 AD）

**替代方案**:
- 在代碼中添加條件邏輯，個人環境停用 Azure AD
  ```typescript
  // apps/web/src/auth.ts
  providers: [
    // 僅在公司環境啟用 Azure AD
    ...(process.env.ENABLE_AZURE_AD === 'true' ? [
      AzureAD({
        clientId: process.env.AZURE_AD_CLIENT_ID!,
        clientSecret: process.env.AZURE_AD_CLIENT_SECRET!,
        tenantId: process.env.AZURE_AD_TENANT_ID!,
      })
    ] : []),

    // 密碼登入始終啟用
    Credentials({ /* ... */ })
  ]
  ```

---

### 階段 3: 公司 Azure 測試/預發布（完整功能驗證）

**目標**: 在類似生產的環境中驗證所有功能，包括 Azure AD SSO

**方式 1**: 使用 GitHub Actions 自動部署到 staging 環境

```yaml
# 觸發條件：推送到 develop 分支
on:
  push:
    branches:
      - develop

environment: staging  # 公司 Azure Staging 環境
```

**方式 2**: 請公司 IT 部門協助部署到 staging

**測試項目**:
- ✅ 所有業務功能
- ✅ Azure AD SSO 登入（公司員工帳號）
- ✅ 資料庫遷移
- ✅ 檔案上傳（Azure Blob）
- ✅ 郵件發送
- ✅ 效能測試
- ✅ 安全掃描

---

### 階段 4: 公司 Azure 生產部署

**部署流程**:

```
1. Code Review ✅
   ↓
2. 合併到 main 分支 ✅
   ↓
3. GitHub Actions 自動觸發部署 ✅
   ↓
4. 執行資料庫遷移 ✅
   ↓
5. 部署新版本 Docker 映像 ✅
   ↓
6. Health Check ✅
   ↓
7. 通知團隊 ✅
```

**回滾計劃**:
```bash
# 如果新版本有問題，一鍵回滾到前一版本
az webapp config container set \
  --name itpm-prod \
  --resource-group rg-itpm-prod \
  --docker-custom-image-name company-acr.azurecr.io/itpm-web:previous-stable
```

---

## 權限和訪問管理

### 開發人員權限需求

**個人 Azure（開發測試）**:
- ✅ 完全訪問權限（你自己的訂閱）

**公司 Azure（生產環境）**:
- ❌ 不需要直接訪問（透過 CI/CD）
- ✅ 需要的最小權限：
  - GitHub Repository Write（推送代碼觸發 CI/CD）
  - 查看 Azure Portal 資源狀態（只讀）
  - 訪問部署日誌（Application Insights）

### Service Principal 配置（給 GitHub Actions）

**由公司 IT 部門創建**:

```bash
# 創建 Service Principal
az ad sp create-for-rbac \
  --name "github-actions-itpm" \
  --role contributor \
  --scopes /subscriptions/<company-subscription-id>/resourceGroups/rg-itpm-prod \
  --sdk-auth

# 輸出結果（保存到 GitHub Secrets）
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "...",
  "activeDirectoryEndpointUrl": "...",
  "resourceManagerEndpointUrl": "..."
}
```

**權限設置**:
- Contributor 在 `rg-itpm-prod` Resource Group
- ACR Push 權限
- Key Vault Reader 權限

---

## 配置管理最佳實踐

### 1. 使用 Azure Key Vault 存儲敏感數據

**好處**:
- ✅ 密鑰不存儲在代碼或環境變數文件中
- ✅ 集中管理和輪換密鑰
- ✅ 訪問日誌和審計

**配置方式**:

```bash
# App Service 環境變數引用 Key Vault
az webapp config appsettings set \
  --name itpm-prod \
  --resource-group rg-itpm-prod \
  --settings \
    DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://kv-itpm-prod.vault.azure.net/secrets/DATABASE-URL/)" \
    AZURE_AD_CLIENT_SECRET="@Microsoft.KeyVault(SecretUri=https://kv-itpm-prod.vault.azure.net/secrets/AZURE-AD-CLIENT-SECRET/)"
```

### 2. 環境特定配置文件

**不要在代碼中硬編碼環境差異**，使用環境變數：

```typescript
// ❌ 錯誤：硬編碼
const isDev = true;
const apiUrl = isDev ? 'http://localhost:3000' : 'https://itpm.company.com';

// ✅ 正確：使用環境變數
const apiUrl = process.env.NEXT_PUBLIC_APP_URL;
```

### 3. 配置驗證腳本

**`scripts/validate-config.sh`**:

```bash
#!/bin/bash

echo "🔍 驗證環境配置..."

required_vars=(
  "DATABASE_URL"
  "NEXTAUTH_SECRET"
  "NEXTAUTH_URL"
  "AZURE_AD_CLIENT_ID"
  "AZURE_AD_CLIENT_SECRET"
  "AZURE_AD_TENANT_ID"
)

missing_vars=()

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    missing_vars+=("$var")
  fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
  echo "❌ 缺少必要的環境變數："
  printf '%s\n' "${missing_vars[@]}"
  exit 1
fi

echo "✅ 所有必要的環境變數已設置"
```

---

## 推薦實施順序

### 第一步：修正 Azure AD 配置（立即）

1. 將代碼從 Azure AD B2C 改為 Azure AD
2. 更新環境變數名稱
3. 在個人 Azure 環境測試基本功能（不含 SSO）

**時間**: 1 小時

---

### 第二步：完善個人 Azure 測試環境（本週）

1. 修復 bcrypt 問題（使用 bcryptjs）
2. 修復 locale 路由問題
3. 完整測試所有功能（除了 Azure AD SSO）
4. 記錄部署流程和遇到的問題

**時間**: 4 小時

---

### 第三步：準備公司環境配置模板（本週）

1. 創建 `.env.company-azure.template`
2. 記錄所有需要的環境變數
3. 與公司 IT 部門確認：
   - Azure AD 應用程式註冊
   - Tenant ID
   - 需要的權限和 Scope

**時間**: 2 小時

---

### 第四步：設置 CI/CD Pipeline（下週）

1. 創建 GitHub Actions workflow
2. 配置 GitHub Secrets
3. 請公司 IT 創建 Service Principal
4. 測試自動部署到 staging

**時間**: 1 天

---

### 第五步：公司環境首次部署（與 IT 協作）

1. IT 部門創建 Azure 資源（如果尚未創建）
2. 配置 Azure AD 應用程式註冊
3. 設置 Key Vault 和密鑰
4. 執行首次部署（手動或透過 CI/CD）
5. 驗證 Azure AD SSO 登入

**時間**: 1 天（包含 IT 協作時間）

---

## 風險管理

### 潛在風險和緩解措施

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 無法訪問公司 Azure | 高 | 使用 CI/CD，不需要本地訪問 |
| Azure AD 配置錯誤 | 高 | 與 IT 部門緊密協作，提前準備文檔 |
| 個人環境測試不完整 | 中 | 明確標記測試範圍，在 staging 補充測試 |
| 部署後 SSO 不工作 | 高 | 準備回滾計劃，保留密碼登入作為備用 |
| 環境變數配置錯誤 | 中 | 使用配置驗證腳本，自動化檢查 |
| 資料庫遷移失敗 | 高 | 在 staging 先測試遷移，備份生產資料庫 |

---

## 總結和行動計劃

### 立即行動（今天）

1. ✅ 修正 Azure AD 配置（從 B2C 改為 Azure AD）
2. ✅ 修復 bcrypt 問題（使用 bcryptjs）
3. ✅ 修復 locale 路由問題

### 短期計劃（本週）

1. 完善個人 Azure 測試環境
2. 創建公司環境配置模板
3. 與公司 IT 部門溝通需求

### 中期計劃（下週）

1. 設置 GitHub Actions CI/CD
2. 配置 Azure Key Vault
3. 部署到公司 staging 環境

### 長期計劃（未來）

1. 完善監控和告警（Application Insights）
2. 自動化測試和安全掃描
3. 建立完整的 DevOps 流程

---

**關鍵要點**:
- ✅ 個人 Azure 用於驗證**基礎設施和部署流程**
- ✅ 不需要在個人環境測試 Azure AD SSO
- ✅ 使用 CI/CD 解決無法訪問公司 Azure 的問題
- ✅ 與公司 IT 部門緊密協作，提前規劃
- ✅ 保留密碼登入作為備用方案

---

**最後更新**: 2025-11-21 17:30 (UTC+8)
**文檔作者**: AI Assistant
**審核狀態**: 待與用戶確認
