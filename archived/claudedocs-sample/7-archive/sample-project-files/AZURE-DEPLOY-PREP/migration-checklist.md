# Azure AD B2C → Azure AD (Entra ID) 遷移清單

**創建時間**: 2025-11-21 18:00 (UTC+8)
**目標**: 從 Azure AD B2C 遷移到 Azure AD (Entra ID) 企業 SSO

---

## ⚠️ 重要提醒：資料庫 Seed Data

> **🚨 Azure 部署必讀!**
>
> 除了 Azure AD 遷移，Azure 首次部署後**必須執行資料庫 seed data 初始化**，否則會導致 **Registration API 500 錯誤** (P2003 外鍵約束)。
>
> **快速檢查**:
> - [ ] 已執行 `pnpm db:migrate` (創建表結構)
> - [ ] **已執行 `pnpm db:seed:minimal`** (插入基礎資料：Role、Currency)
> - [ ] 已驗證 Role 表包含 3 筆記錄 (ID: 1, 2, 3)
> - [ ] 已驗證 Currency 表包含 6 筆記錄
>
> **完整步驟請參閱**:
> - 📋 **部署檢查清單**: `claudedocs/AZURE-DEPLOYMENT-CHECKLIST.md` (Section "Step 4: 執行 Seed Data")
> - 📖 **部署手冊**: `docs/deployment/AZURE-DEPLOYMENT-GUIDE.md` (Section 2.6)
> - 📝 **實施總結**: `claudedocs/AZURE-SEED-DATA-IMPLEMENTATION-SUMMARY.md`
> - 🔧 **自動化腳本**: `scripts/azure-seed.sh`
>
> **為什麼必要?**
> - User 表的 `roleId` 字段引用 Role 表，如果 Role 表為空，用戶註冊會失敗
> - BudgetPool 需要 Currency 表資料
> - 本地環境有完整 seed data，Azure 環境只有 schema（只執行了 migration）

---

## ✅ 已完成的修改

### 1. `apps/web/src/auth.ts` - NextAuth 主配置文件

**修改內容**:
- ✅ Import 從 `AzureADB2C` 改為 `AzureAD`
- ✅ Provider 配置更新：
  - 使用 `AzureAD()` 替代 `AzureADB2C()`
  - 環境變數：`AZURE_AD_CLIENT_ID`, `AZURE_AD_CLIENT_SECRET`, `AZURE_AD_TENANT_ID`
  - 添加 `authorization.params.scope`: `'openid profile email User.Read'`
- ✅ Profile 映射更新（支援 `upn` 欄位）
- ✅ JWT callback 中 provider 檢查從 `'azure-ad-b2c'` 改為 `'azure-ad'`

**程式碼變更**:
```typescript
// 第 42 行
import AzureAD from 'next-auth/providers/azure-ad';

// 第 103-128 行
...(process.env.AZURE_AD_CLIENT_ID &&
    process.env.AZURE_AD_CLIENT_SECRET &&
    process.env.AZURE_AD_TENANT_ID
  ? [
      AzureAD({
        clientId: process.env.AZURE_AD_CLIENT_ID,
        clientSecret: process.env.AZURE_AD_CLIENT_SECRET,
        tenantId: process.env.AZURE_AD_TENANT_ID,
        authorization: {
          params: {
            scope: 'openid profile email User.Read',
          },
        },
        profile(profile: any) {
          return {
            id: profile.sub || profile.oid,
            email: profile.email || profile.preferred_username || profile.upn,
            name: profile.name || `${profile.given_name || ''} ${profile.family_name || ''}`.trim(),
            image: profile.picture,
            emailVerified: profile.email_verified ? new Date() : null,
          };
        },
      }),
    ]
  : []),

// 第 218 行
if (account?.provider === 'azure-ad' && user) {
```

---

## 📋 待完成的修改

### 2. `.env.example` - 環境變數範例文件

**文件路徑**: `.env.example`

**需要修改的內容**:

```bash
# ❌ 刪除以下 Azure AD B2C 相關變數
AZURE_AD_B2C_TENANT_NAME="yourtenantname"
AZURE_AD_B2C_TENANT_ID="your-tenant-id-guid"
AZURE_AD_B2C_DOMAIN="${AZURE_AD_B2C_TENANT_NAME}.b2clogin.com"
AZURE_AD_B2C_CLIENT_ID="your-client-id-guid"
AZURE_AD_B2C_CLIENT_SECRET="your-client-secret"
AZURE_AD_B2C_PRIMARY_USER_FLOW="B2C_1_signupsignin"
AZURE_AD_B2C_PROFILE_EDIT_FLOW="B2C_1_profileediting"
AZURE_AD_B2C_PASSWORD_RESET_FLOW="B2C_1_passwordreset"
AZURE_AD_B2C_SCOPE="openid profile email offline_access"

# ✅ 添加以下 Azure AD (Entra ID) 變數
# ========================================
# Azure AD (Entra ID) SSO 認證（企業用戶）
# ========================================

# Azure AD 租戶 ID（公司的 Azure AD Tenant ID）
AZURE_AD_TENANT_ID="your-company-tenant-id-guid"

# Azure AD 應用程式註冊
AZURE_AD_CLIENT_ID="your-app-registration-client-id"
AZURE_AD_CLIENT_SECRET="your-app-registration-client-secret"

# 注意：
# - AZURE_AD_TENANT_ID: 從 Azure Portal → Azure Active Directory → Overview → Tenant ID
# - AZURE_AD_CLIENT_ID 和 CLIENT_SECRET: 從 Azure Portal → App Registrations → 你的應用程式
# - Redirect URI 必須設置為: https://your-app-url/api/auth/callback/azure-ad
```

---

### 3. `.env.development.local` - 本地開發環境變數

**文件路徑**: `.env.development.local`（如果不存在則創建）

**內容**:
```bash
# ========================================
# 本地開發環境配置
# ========================================

NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000

# 資料庫（本地 Docker）
DATABASE_URL="postgresql://postgres:localdev123@localhost:5434/itpm_dev"

# NextAuth.js
NEXTAUTH_SECRET="local-dev-secret-change-in-production-12345678"
NEXTAUTH_URL="http://localhost:3000"

# Azure AD - 本地開發時不啟用（使用密碼登入）
# AZURE_AD_CLIENT_ID=
# AZURE_AD_CLIENT_SECRET=
# AZURE_AD_TENANT_ID=

# 郵件服務（Mailhog - Docker）
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=""
SMTP_PASSWORD=""

# Redis（本地 Docker）
REDIS_URL="redis://localhost:6381"

# 開發模式標記
ENABLE_AZURE_AD=false  # 本地開發停用 Azure AD
```

---

### 4. `apps/web/package.json` - 檢查 next-auth 依賴

**文件路徑**: `apps/web/package.json`

**檢查項目**:
- ✅ `next-auth` 版本 >= 5.0.0（確認支援 Azure AD provider）
- ✅ 如果需要，添加 `bcryptjs` 和 `@types/bcryptjs`

**執行命令**:
```bash
# 檢查當前版本
pnpm list next-auth --filter=@itpm/web

# 如果需要更新
pnpm add next-auth@latest --filter=@itpm/web

# 添加 bcryptjs（用於修復 bcrypt 問題）
pnpm add bcryptjs @types/bcryptjs --filter=@itpm/web
```

---

### 5. 修復 bcrypt 問題（使用 bcryptjs）

**文件路徑**: `apps/web/src/app/api/auth/register/route.ts` 和 `apps/web/src/auth.ts`

**當前問題**: bcrypt 原生模組在 Azure 環境下無法運行

**解決方案**: 替換為 bcryptjs（純 JavaScript 實現）

**需要修改的文件**:

#### A. `apps/web/src/auth.ts`

```typescript
// 第 44 行 - 已完成
import bcrypt from 'bcryptjs';  // ✅ 已從 'bcrypt' 改為 'bcryptjs'
```

#### B. `apps/web/src/app/api/auth/register/route.ts`

```typescript
// 第 41 行
import bcrypt from 'bcryptjs';  // 改為 bcryptjs

// 其他代碼保持不變，API 完全相同
```

---

### 6. 修復 locale 路由問題

**問題**: NextAuth 重定向到 `/login` 但頁面實際在 `/[locale]/login`

**解決方案**: 修改 `auth.config.ts` 的 pages 配置

**文件路徑**: `apps/web/src/auth.config.ts`

**修改內容**:
```typescript
// 第 73-76 行
pages: {
  signIn: '/zh-TW/login',  // ✅ 添加預設 locale
  error: '/zh-TW/login',   // ✅ 添加預設 locale
}
```

**或使用動態檢測**（更好的方案）:
```typescript
// apps/web/src/auth.config.ts
import { headers } from 'next/headers';

export const authConfig: NextAuthConfig = {
  pages: {
    get signIn() {
      try {
        const headersList = headers();
        const locale = headersList.get('x-next-intl-locale') || 'zh-TW';
        return `/${locale}/login`;
      } catch {
        return '/zh-TW/login'; // fallback
      }
    },
    get error() {
      try {
        const headersList = headers();
        const locale = headersList.get('x-next-intl-locale') || 'zh-TW';
        return `/${locale}/login`;
      } catch {
        return '/zh-TW/login'; // fallback
      }
    },
  },
  // ... 其他配置
};
```

---

### 7. 更新 middleware.ts（如果需要）

**文件路徑**: `apps/web/src/middleware.ts`

**檢查項目**:
- ✅ 確認 matcher 包含登入相關路由
- ✅ 確認沒有硬編碼 Azure AD B2C 特定邏輯

**當前 matcher**:
```typescript
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/projects/:path*',
    '/budget-pools/:path*',
    '/budget-proposals/:path*',
    '/vendors/:path*',
    '/purchase-orders/:path*',
    '/expenses/:path*',
    '/users/:path*',
  ],
};
```

**建議添加（可選）**:
```typescript
export const config = {
  matcher: [
    '/',              // 添加根路徑
    '/login',         // 添加 /login（處理重定向）
    '/dashboard/:path*',
    '/projects/:path*',
    // ... 其他路由
  ],
};
```

---

### 8. 更新翻譯文件（可選）

**文件路徑**:
- `apps/web/src/messages/zh-TW.json`
- `apps/web/src/messages/en.json`

**檢查項目**:
- ✅ 確認 Azure AD 登入按鈕的翻譯鍵存在
- ✅ 如果需要，更新按鈕文字從 "Azure AD B2C" 到 "Microsoft 登入" 或 "公司帳號登入"

**zh-TW.json**:
```json
{
  "auth": {
    "login": {
      "azureLogin": "使用 Microsoft 登入",  // 或 "使用公司帳號登入"
      "orDivider": "或",
      "email": {
        "label": "Email",
        "placeholder": "your.email@example.com"
      }
      // ... 其他翻譯
    }
  }
}
```

---

### 9. 創建 Azure AD 應用程式註冊（公司 IT 部門）

**由公司 IT 部門執行**:

#### Step 1: 在 Azure Portal 註冊應用程式

1. 登入 Azure Portal: https://portal.azure.com
2. 前往 "Azure Active Directory" → "App registrations"
3. 點擊 "New registration"
4. 填寫資訊：
   - Name: `ITPM Web Application`
   - Supported account types: `Accounts in this organizational directory only (Single tenant)`
   - Redirect URI:
     - Type: `Web`
     - URI: `https://your-app-url.azurewebsites.net/api/auth/callback/azure-ad`

#### Step 2: 配置 API Permissions

1. 前往 "API permissions"
2. 添加以下權限（Microsoft Graph）:
   - `User.Read` (Delegated)
   - `email` (Delegated)
   - `openid` (Delegated)
   - `profile` (Delegated)
3. 點擊 "Grant admin consent" 授予權限

#### Step 3: 創建 Client Secret

1. 前往 "Certificates & secrets"
2. 點擊 "New client secret"
3. 設置過期時間（建議：24 months）
4. **複製 Client Secret Value**（只顯示一次！）

#### Step 4: 記錄配置資訊

需要記錄以下資訊：
- `AZURE_AD_TENANT_ID`: 從 "Overview" 頁面的 "Directory (tenant) ID"
- `AZURE_AD_CLIENT_ID`: 從 "Overview" 頁面的 "Application (client) ID"
- `AZURE_AD_CLIENT_SECRET`: 剛才創建的 Client Secret Value

---

### 10. 更新 Azure App Service 環境變數

**個人 Azure 測試環境**:

```bash
# 如果個人環境不測試 Azure AD，可以不設置
# 或設置但不啟用（ENABLE_AZURE_AD=false）

az webapp config appsettings set \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --settings \
    AZURE_AD_CLIENT_ID="" \
    AZURE_AD_CLIENT_SECRET="" \
    AZURE_AD_TENANT_ID="" \
    ENABLE_AZURE_AD=false
```

**公司 Azure 生產環境**（由公司電腦執行）:

```bash
# 使用真實的公司 Azure AD 配置
az webapp config appsettings set \
  --name <company-app-service-name> \
  --resource-group <company-resource-group> \
  --settings \
    AZURE_AD_CLIENT_ID="<company-client-id>" \
    AZURE_AD_CLIENT_SECRET="<company-client-secret>" \
    AZURE_AD_TENANT_ID="<company-tenant-id>" \
    ENABLE_AZURE_AD=true
```

**或使用 Azure Key Vault**（推薦）:
```bash
az webapp config appsettings set \
  --name <company-app-service-name> \
  --resource-group <company-resource-group> \
  --settings \
    AZURE_AD_CLIENT_ID="@Microsoft.KeyVault(SecretUri=https://kv-itpm-prod.vault.azure.net/secrets/AZURE-AD-CLIENT-ID/)" \
    AZURE_AD_CLIENT_SECRET="@Microsoft.KeyVault(SecretUri=https://kv-itpm-prod.vault.azure.net/secrets/AZURE-AD-CLIENT-SECRET/)" \
    AZURE_AD_TENANT_ID="@Microsoft.KeyVault(SecretUri=https://kv-itpm-prod.vault.azure.net/secrets/AZURE-AD-TENANT-ID/)"
```

---

## 🧪 測試計劃

### 階段 1: 本地開發測試

```bash
# 1. 確保環境變數正確
cat .env.development.local

# 2. 啟動本地開發服務器
pnpm dev

# 3. 測試密碼登入（Azure AD 應該不可見）
# 訪問 http://localhost:3000/zh-TW/login
# 應該只看到 Email/Password 登入表單

# 4. 測試註冊功能
# 訪問 http://localhost:3000/zh-TW/register
# 註冊新用戶

# 5. 測試密碼登入
# 使用剛註冊的帳號登入
```

**預期結果**:
- ✅ 密碼登入正常工作
- ✅ 註冊功能正常工作
- ✅ 沒有看到 "使用 Microsoft 登入" 按鈕（因為 ENABLE_AZURE_AD=false）

---

### 階段 2: 個人 Azure 測試

```bash
# 1. 構建 Docker 映像
docker build -t acritpmdev.azurecr.io/itpm-web:v3-azure-ad -f docker/Dockerfile .

# 2. 推送到 ACR
docker push acritpmdev.azurecr.io/itpm-web:v3-azure-ad

# 3. 更新 App Service
az webapp config container set \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --docker-custom-image-name acritpmdev.azurecr.io/itpm-web:v3-azure-ad

# 4. 重啟 App Service
az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev

# 5. 測試
# 訪問 https://app-itpm-dev-001.azurewebsites.net/zh-TW/login
# - 密碼登入應該正常工作
# - 註冊應該正常工作（使用 bcryptjs）
# - 如果 ENABLE_AZURE_AD=false，Azure AD 按鈕不顯示
```

**預期結果**:
- ✅ 網站可訪問
- ✅ 密碼登入正常
- ✅ 註冊功能正常（修復了 bcrypt 500 錯誤）
- ✅ 沒有 404 錯誤（修復了 locale 路由問題）

---

### 階段 3: 公司 Azure 測試（需要公司網路）

**前提條件**:
- ✅ 公司 IT 已創建 Azure AD 應用程式註冊
- ✅ 已獲得 AZURE_AD_CLIENT_ID, CLIENT_SECRET, TENANT_ID
- ✅ 在公司電腦上執行

**測試步驟**:

```bash
# 1. 在公司電腦上克隆/拉取最新代碼
git clone https://github.com/your-org/itpm-webapp.git
# 或
git pull origin main

# 2. 構建 Docker 映像
docker build -t company-acr.azurecr.io/itpm-web:prod-azure-ad -f docker/Dockerfile .

# 3. 登入公司 Azure
az login --tenant <COMPANY_TENANT_ID>

# 4. 登入公司 ACR
az acr login --name company-acr

# 5. 推送映像
docker push company-acr.azurecr.io/itpm-web:prod-azure-ad

# 6. 更新 App Service 環境變數
az webapp config appsettings set \
  --name <company-app-service> \
  --resource-group <company-rg> \
  --settings \
    AZURE_AD_CLIENT_ID="<company-client-id>" \
    AZURE_AD_CLIENT_SECRET="<company-client-secret>" \
    AZURE_AD_TENANT_ID="<company-tenant-id>" \
    ENABLE_AZURE_AD=true

# 7. 更新容器
az webapp config container set \
  --name <company-app-service> \
  --resource-group <company-rg> \
  --docker-custom-image-name company-acr.azurecr.io/itpm-web:prod-azure-ad

# 8. 重啟 App Service
az webapp restart --name <company-app-service> --resource-group <company-rg>
```

**功能測試**:

1. **測試 Azure AD SSO 登入**:
   - 訪問 https://itpm.company.com/zh-TW/login
   - 點擊 "使用 Microsoft 登入" 按鈕
   - 應該跳轉到 Microsoft 登入頁面
   - 使用公司帳號登入
   - 應該成功登入並重定向到 dashboard

2. **測試密碼登入**（如果啟用）:
   - 使用 Email/Password 登入
   - 應該正常工作

3. **測試註冊功能**:
   - 新用戶註冊
   - 應該正常工作（沒有 500 錯誤）

**預期結果**:
- ✅ Azure AD SSO 登入成功
- ✅ 用戶信息正確顯示（姓名、Email）
- ✅ 用戶自動創建到資料庫（roleId = 1）
- ✅ 登入後正確重定向到 dashboard
- ✅ Session 正常維持
- ✅ 登出正常工作

---

## 📝 部署流程（您的建議）

### 個人電腦（本地開發）

```
1. 修改代碼 ✅
   ↓
2. 本地測試（密碼登入）✅
   ↓
3. 部署到個人 Azure 測試 ✅
   ↓
4. 驗證所有功能（除了 Azure AD）✅
   ↓
5. Git commit + push 到 GitHub ✅
```

### 公司電腦（部署到生產）

```
1. Git pull 最新代碼 ✅
   ↓
2. 構建 Docker 映像 ✅
   ↓
3. 登入公司 Azure ✅
   ↓
4. 推送映像到公司 ACR ✅
   ↓
5. 更新 App Service 配置 ✅
   ↓
6. 部署新版本 ✅
   ↓
7. 測試 Azure AD SSO 登入 ✅
```

---

## ⚠️ 注意事項

### 1. Redirect URI 配置

**關鍵**: Azure AD 應用程式註冊中的 Redirect URI **必須完全匹配**：

```
正確格式: https://your-app-url/api/auth/callback/azure-ad
                                   ^^^^^^^^^^^^^^^^^^^^
                                   NextAuth.js 標準路由

錯誤示例:
- https://your-app-url/login ❌
- https://your-app-url/zh-TW/login ❌
- https://your-app-url/api/auth/signin ❌
```

### 2. 環境變數檢查

**部署前務必確認**:
```bash
# 檢查 App Service 環境變數
az webapp config appsettings list \
  --name <app-service-name> \
  --resource-group <resource-group> \
  --query "[?name=='AZURE_AD_CLIENT_ID' || name=='AZURE_AD_CLIENT_SECRET' || name=='AZURE_AD_TENANT_ID']"

# 應該看到三個變數都已設置
```

### 3. 密鑰安全

**永遠不要**:
- ❌ 提交 `.env` 文件到 Git
- ❌ 在代碼中硬編碼密鑰
- ❌ 在公開的地方分享 CLIENT_SECRET

**應該**:
- ✅ 使用 `.env.example` 作為模板（不含真實值）
- ✅ 使用 Azure Key Vault 存儲生產密鑰
- ✅ 定期輪換 CLIENT_SECRET

### 4. 回滾計劃

如果新版本有問題，快速回滾：

```bash
# 回滾到前一個穩定版本
az webapp config container set \
  --name <app-service-name> \
  --resource-group <resource-group> \
  --docker-custom-image-name acritpmdev.azurecr.io/itpm-web:v2-register

# 重啟
az webapp restart --name <app-service-name> --resource-group <resource-group>
```

---

## 📚 相關文檔

- Azure AD 應用程式註冊: https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app
- NextAuth.js Azure AD Provider: https://next-auth.js.org/providers/azure-ad
- Microsoft Graph Permissions: https://learn.microsoft.com/en-us/graph/permissions-reference

---

**最後更新**: 2025-11-21 18:00 (UTC+8)
**狀態**: 部分完成（auth.ts 已修改，環境變數和測試待完成）
**下一步**: 完成剩餘的修改並測試
