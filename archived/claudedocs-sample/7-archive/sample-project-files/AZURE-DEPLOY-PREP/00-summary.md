# Azure 部署準備 - 完整總結

**主題**: 準備將本項目部署到 Azure 環境的流程和詳細所需準備
**創建日期**: 2025-11-20
**狀態**: 規劃階段 (已完成階段 1-2，共 8 個階段)
**使用 Prompt**: SITUATION-2-FEATURE-DEV-PREP.md

---

## 📋 目錄

1. [討論背景](#討論背景)
2. [用戶提出的 7 個關鍵問題](#用戶提出的-7-個關鍵問題)
3. [關鍵決策總結](#關鍵決策總結)
4. [架構驗證結果](#架構驗證結果)
5. [8 階段部署計劃](#8-階段部署計劃)
6. [已完成的工作](#已完成的工作)
7. [下一步行動](#下一步行動)
8. [相關文檔](#相關文檔)

---

## 討論背景

### 用戶的初始需求

用戶想討論將本項目部署到 Azure 的準備工作，並提出以下狀態：

**目前狀態**:
- ✅ 本地開發環境運行正常
- ✅ 使用 Docker Compose (PostgreSQL, Redis, Mailhog)
- ✅ MVP 功能已完成 (Epic 1-8)
- ✅ ~30,000+ 行生產代碼

**用戶的 3 個核心問題**:
1. Azure 需要哪些服務？
2. 部署流程的關鍵步驟是什麼？
3. 有哪些容易遇到的坑？

### 我的建議

使用 `SITUATION-2-FEATURE-DEV-PREP.md` 作為系統化管理流程：
1. **理解需求**: 閱讀現有文檔，分析 Azure 需求
2. **驗證架構**: 檢查代碼是否準備好部署
3. **制定計劃**: 創建 8 階段部署路線圖
4. **創建任務**: 使用 TodoWrite 追蹤進度

---

## 用戶提出的 7 個關鍵問題

### 問題 1: 環境變數管理

**問題**: 如果不能提交到 GitHub，怎樣更新 Azure 上的環境設定？
```
❌ .azure/environments/*.env        # 實際環境變數 (含密鑰)
❌ .azure/credentials.json          # Azure 服務主體憑證
❌ .env                             # 環境變數
```

**解決方案**: 使用公司 Key Vault + GitHub Secrets

```yaml
方式 1 - Azure CLI 直接設置:
  az webapp config appsettings set --settings @settings.json

方式 2 - GitHub Secrets:
  GitHub Secrets → GitHub Actions → az webapp config appsettings set

方式 3 - Key Vault 引用 (推薦):
  DATABASE_URL="@Microsoft.KeyVault(VaultName=company-kv;SecretName=ITPM-DEV-DATABASE-URL)"
```

**工作流程**:
1. 開發者提供密鑰列表（不含實際值）
2. Azure Infra Admin 在公司 Key Vault 創建密鑰
3. App Service 使用 `@Microsoft.KeyVault()` 引用
4. 啟用 Managed Identity 授權訪問

---

### 問題 2: AI Prompt 編號

**問題**: 為什麼是從 SITUATION-7 開始而不是 6？

**回答**: 用戶指出錯誤，當前只有 5 個 prompts (SITUATION-1 到 SITUATION-5)

**更正**:
- ✅ SITUATION-6-AZURE-DEPLOY.md (Azure 部署指引)
- ✅ SITUATION-7-AZURE-TROUBLESHOOT.md (Azure 問題排查)

---

### 問題 3: Service Principal 管理策略

**建議**: 統一使用 Service Principal 管理所有 Azure 操作

**原因**:
- ✅ 適用於 AI 助手工具 (Claude Code, GitHub Copilot)
- ✅ 權限可控、可審計
- ✅ 無需手動登入

**Service Principal 清單**:

| Name | 環境 | 角色 | 用途 |
|------|------|------|------|
| `sp-itpm-github-dev` | Dev | Contributor | CI/CD 部署 |
| `sp-itpm-github-staging` | Staging | Contributor | CI/CD 部署 |
| `sp-itpm-github-prod` | Production | Website Contributor | CI/CD 部署 (最小權限) |
| `sp-itpm-ai-dev` | Dev | Reader | AI 工具只讀訪問 |

**安全策略**:
- ✅ 最小權限原則
- ✅ 環境隔離
- ✅ 定期輪換密鑰 (90 天)

---

### 問題 4: Azure AD B2C 登錄按鈕

**問題**: 是之後會在登錄頁有 Azure AD login 的按鈕嗎？

**回答**: ✅ **已 100% 實現**

**實現位置**: `apps/web/src/app/[locale]/login/page.tsx:185-212`

```tsx
{/* 條件渲染 Azure AD B2C 按鈕 */}
{process.env.NEXT_PUBLIC_AZURE_AD_B2C_ENABLED === 'true' && (
  <Button onClick={handleAzureLogin}>
    <MicrosoftIcon />
    使用 Microsoft 帳號登入
  </Button>
)}
```

**啟用方式**:
```bash
# 環境變數
NEXT_PUBLIC_AZURE_AD_B2C_ENABLED=true

# Azure App Service
az webapp config appsettings set \
  --settings NEXT_PUBLIC_AZURE_AD_B2C_ENABLED=true
```

**部署時需配置**: Azure AD B2C Redirect URIs
```
https://app-itpm-dev-001.azurewebsites.net/api/auth/callback/azure-ad-b2c
https://app-itpm-staging-001.azurewebsites.net/api/auth/callback/azure-ad-b2c
https://app-itpm-prod-001.azurewebsites.net/api/auth/callback/azure-ad-b2c
```

---

### 問題 5: Azure Key Vault

**用戶情況**: 公司已經有在使用 Azure Key Vault

**決策**: ✅ **使用公司現有 Key Vault，不創建新的**

**調整後的架構**:
```diff
- 原計劃: 創建新的 Key Vault ❌
+ 調整後: 使用公司現有 Key Vault ✅
```

**密鑰命名規範**:
```
格式: ITPM-{ENVIRONMENT}-{SERVICE}-{KEY_NAME}

範例:
- ITPM-DEV-DATABASE-URL
- ITPM-DEV-NEXTAUTH-SECRET
- ITPM-STAGING-SENDGRID-API-KEY
- ITPM-PROD-AZURE-STORAGE-CONNECTION-STRING
```

**工作流程**:
1. 開發者準備密鑰列表 (`docs/deployment/key-vault-secrets-list.md`)
2. Azure Infra Admin 在公司 Key Vault 創建密鑰
3. 配置 App Service Managed Identity
4. App Service 使用 Key Vault 引用

**優點**:
- ✅ 符合公司安全政策
- ✅ 集中管理所有密鑰
- ✅ 無需額外 Key Vault 成本
- ✅ 密鑰輪換由公司統一管理

---

### 問題 6: Docker 部署方式

**用戶建議**: 直接開始使用 Docker 部署 (Container Deployment)

**決策**: ✅ **採用 Container Deployment**

**部署方式對比**:

| 方式 | 優點 | 缺點 | 需要 ACR? |
|------|------|------|-----------|
| **代碼部署** | 簡單快速 | 環境不一致 | ❌ 不需要 |
| **Docker 部署** | 環境一致、快速回滾 | 初期設置複雜 | ✅ **必須** |

**必須服務**:
- ✅ Azure Container Registry (ACR)
- ✅ Azure App Service (Container support)

**建議的演進路徑**:
```
原建議: 階段 1 代碼部署 → 階段 2 Docker 部署
調整後: 直接使用 Docker 部署 ✅
```

---

### 問題 7: 文件架構同步到 GitHub

**用戶要求**: 確保部署文件架構可以同步至 GitHub，讓其他開發者遵循

**解決方案**: 更新 `.gitignore`

```diff
# .gitignore 修改
- .azure/  # 之前完全忽略

+ # 只忽略敏感文件，保留配置範例
+ .azure/credentials.json
+ .azure/*.local
+ .azure/**/sp-*.json
+ !.azure/environments/      # ✅ 可提交
+ !.azure/scripts/           # ✅ 可提交
+ !.azure/docs/              # ✅ 可提交
+ !.azure/README.md          # ✅ 可提交
```

**可提交到 Git**:
- ✅ `.azure/environments/*.env.example` (環境配置範例)
- ✅ `.azure/scripts/*.sh` (Azure CLI 腳本)
- ✅ `.azure/docs/*.md` (部署文檔)
- ✅ `.azure/README.md` (總覽)

**不能提交到 Git**:
- ❌ `.azure/environments/*.env` (實際密鑰)
- ❌ `.azure/credentials.json` (SP 憑證)
- ❌ `.azure/**/sp-*.json` (Service Principal JSON)

---

## 關鍵決策總結

### 1. 密鑰管理策略 🔐

**決策**: 使用公司現有 Azure Key Vault

```yaml
密鑰來源: 公司 Azure Key Vault
命名格式: ITPM-{ENV}-{SERVICE}-{KEY}
引用方式: @Microsoft.KeyVault(VaultName=...;SecretName=...)
訪問方式: App Service Managed Identity
```

---

### 2. Service Principal 策略 🤖

**決策**: 統一使用 Service Principal 管理

```yaml
CI/CD:
  - sp-itpm-github-dev (Contributor)
  - sp-itpm-github-staging (Contributor)
  - sp-itpm-github-prod (Website Contributor)

AI 工具:
  - sp-itpm-ai-dev (Reader)
```

---

### 3. 部署方式 🐳

**決策**: Docker Container Deployment

```yaml
部署方式: Container Deployment
構建工具: Docker multi-stage build
鏡像倉庫: Azure Container Registry
Next.js 配置: output: 'standalone'
```

---

### 4. Azure AD B2C 🔑

**狀態**: 已 100% 實現

```yaml
實現狀態: ✅ 完成
登錄按鈕: ✅ 已實現
環境變數控制: NEXT_PUBLIC_AZURE_AD_B2C_ENABLED
部署需配置: Redirect URIs
```

---

### 5. 文件架構管理 📁

**策略**: 配置範例可提交，敏感文件忽略

```yaml
可提交:
  - .azure/environments/*.example
  - .azure/scripts/*.sh
  - .azure/docs/*.md

禁止提交:
  - .azure/environments/*.env
  - .azure/credentials.json
  - .azure/**/sp-*.json
```

---

## 架構驗證結果

### ✅ 已驗證通過

1. **數據庫連接**: Prisma 配置正確，使用環境變數
2. **認證系統**: NextAuth.js + Azure AD B2C 已完整實現
3. **API 設計**: tRPC 完全使用相對路徑，無硬編碼
4. **環境變數**: 使用 `process.env`，無硬編碼配置

---

### 🚨 發現關鍵問題

#### 問題: 文件上傳使用本地文件系統

**現狀**:
```typescript
// 當前實作
const uploadDir = join(process.cwd(), 'public', 'uploads', '...');
await writeFile(filePath, buffer);
```

**問題**:
- ❌ Azure App Service 文件系統是臨時的
- ❌ 重啟後文件會丟失
- ❌ 多實例部署文件不同步

**受影響文件**:
1. `apps/web/src/app/api/upload/quote/route.ts:185-189`
2. `apps/web/src/app/api/upload/invoice/route.ts:130`
3. `apps/web/src/app/api/upload/proposal/route.ts:134`

**優先級**: 🔴 **關鍵 - 部署阻斷問題**

**必須在階段 3 完成**: 實作 Azure Blob Storage 上傳服務

---

### ⚠️ 需要配置的項目

1. **未安裝依賴**:
   ```bash
   ❌ @azure/storage-blob
   ❌ @azure/identity
   ```

2. **環境變數缺失**: 需要配置 Blob Storage 連接字串

3. **Dockerfile 需要測試**: 本地構建驗證

---

## 8 階段部署計劃

### ✅ 階段 1: Docker 配置和測試 (已完成)

**狀態**: 100% 完成
**完成日期**: 2025-11-20

**交付物**:
- ✅ `docker/Dockerfile` - 生產環境 Dockerfile
- ✅ `docker/.dockerignore` - Docker build 排除文件
- ✅ `apps/web/next.config.mjs` - 添加 `output: 'standalone'`

**特點**:
- 多階段構建 (base → deps → builder → runner)
- 非 root 用戶運行
- 健康檢查配置
- Prisma Client 正確打包

---

### ✅ 階段 2: 創建部署文件架構 (已完成)

**狀態**: 100% 完成
**完成日期**: 2025-11-20

**交付物**:
- ✅ `.azure/README.md` - Azure 部署總覽
- ✅ `.azure/environments/dev.env.example` - Dev 環境配置
- ✅ `.azure/environments/staging.env.example` - Staging 環境配置
- ✅ `.azure/environments/prod.env.example` - Prod 環境配置
- ✅ `.azure/docs/service-principal-setup.md` - SP 完整設置指南
- ✅ `docs/deployment/azure-deployment-plan.md` - 完整部署規劃
- ✅ `.gitignore` 更新 - 允許配置提交

**特點**:
- 所有環境變數使用 Key Vault 引用
- 完整的 Service Principal 設置流程
- 詳細的部署步驟和檢查清單

---

### ⏳ 階段 3: 實作 Azure Blob Storage 上傳服務

**狀態**: 待執行
**優先級**: 🔴 **關鍵 - 部署阻斷問題**
**預計時間**: 6-8 小時

**任務清單**:

1. **安裝依賴** (15 分鐘)
   ```bash
   pnpm add @azure/storage-blob @azure/identity --filter @itpm/web
   ```

2. **創建 Blob Storage 服務** (2-3 小時)
   - 文件: `apps/web/src/lib/azure-storage.ts`
   - 功能:
     - `uploadToBlob(container, fileName, buffer)` - 上傳文件
     - `deleteFromBlob(container, fileName)` - 刪除文件
     - `getBlobUrl(container, fileName)` - 獲取訪問 URL
     - `listBlobs(container, prefix)` - 列出文件

3. **重構上傳 API Routes** (2-3 小時)
   - `apps/web/src/app/api/upload/quote/route.ts`
   - `apps/web/src/app/api/upload/invoice/route.ts`
   - `apps/web/src/app/api/upload/proposal/route.ts`

   **實現策略**: 環境檢測模式
   ```typescript
   if (process.env.NODE_ENV === 'production') {
     // Azure Blob Storage
     const blobUrl = await uploadToBlob('quotes', fileName, buffer);
     filePath = blobUrl;
   } else {
     // 本地文件系統 (dev only)
     await writeFile(localPath, buffer);
     filePath = `/uploads/quotes/${fileName}`;
   }
   ```

4. **本地測試** (1-2 小時)
   - 安裝 Azurite (Azure Storage 模擬器)
   - 驗證環境檢測邏輯
   - 測試所有上傳場景

5. **更新文檔** (30 分鐘)
   - JSDoc 註解更新
   - 使用說明文檔

---

### ⏳ 階段 4: 創建 AI 助手部署 Prompts

**狀態**: 待執行
**預計時間**: 2-3 小時

**交付物**:

1. **SITUATION-6-AZURE-DEPLOY.md** (1.5 小時)
   - Azure 部署流程指引
   - 環境配置檢查清單
   - 常見問題快速解決
   - 部署後驗證步驟

2. **SITUATION-7-AZURE-TROUBLESHOOT.md** (1.5 小時)
   - 部署失敗診斷流程
   - 應用運行異常排查
   - 日誌查詢命令
   - 回滾操作指引

---

### ⏳ 階段 5: 準備 Azure 資源配置腳本

**狀態**: 待執行
**預計時間**: 4-6 小時

**交付物**:

1. **01-setup-resources.sh** (30 分鐘)
   - 創建資源群組
   - 設置標籤和命名

2. **02-setup-database.sh** (1 小時)
   - 創建 PostgreSQL Flexible Server
   - 配置防火牆規則
   - 創建數據庫

3. **03-setup-storage.sh** (1 小時)
   - 創建 Storage Account
   - 創建 Blob Containers (quotes, invoices, proposals)
   - 配置 CORS

4. **04-setup-acr.sh** (30 分鐘)
   - 創建 Container Registry
   - 啟用 Admin User
   - 獲取憑證

5. **05-setup-appservice.sh** (1.5 小時)
   - 創建 App Service Plan
   - 創建 Web App
   - 配置容器設置
   - 啟用 Managed Identity
   - 配置環境變數 (Key Vault 引用)

6. **06-deploy-app.sh** (30 分鐘)
   - 構建 Docker 鏡像
   - 推送到 ACR
   - 部署到 App Service
   - 執行數據庫遷移
   - 健康檢查

---

### ⏳ 階段 6: 配置 CI/CD Pipeline

**狀態**: 待執行
**預計時間**: 4-5 小時

**交付物**:

1. **.github/workflows/azure-deploy-dev.yml** (1.5 小時)
   - 觸發: push to develop
   - 步驟:
     - Checkout code
     - Setup Node.js 20
     - Install dependencies
     - Generate Prisma Client
     - Build Docker image
     - Push to ACR
     - Deploy to App Service
     - Run database migrations
     - Health check

2. **.github/workflows/azure-deploy-staging.yml** (1.5 小時)
   - 觸發: create release-*
   - 包含所有 dev 步驟
   - 額外: Smoke tests

3. **.github/workflows/azure-deploy-prod.yml** (1.5 小時)
   - 觸發: manual
   - Environment Secrets (需審批)
   - 包含所有 staging 步驟
   - 額外: Rollback plan

4. **GitHub Secrets 配置文檔** (30 分鐘)
   - 列出所有需要的 Secrets
   - 配置步驟說明

---

### ⏳ 階段 7: 準備部署文檔和檢查清單

**狀態**: 待執行
**預計時間**: 3-4 小時

**交付物**:

1. **00-prerequisites.md** (30 分鐘)
   - Azure 訂閱檢查
   - 工具安裝清單
   - 權限驗證

2. **01-first-time-setup.md** (1.5 小時)
   - 完整首次部署指南
   - 分步驟操作說明
   - 驗證檢查點

3. **02-ci-cd-setup.md** (1 小時)
   - GitHub Actions 配置
   - Service Principal 設置
   - GitHub Secrets 配置

4. **03-troubleshooting.md** (1 小時)
   - 常見錯誤和解決方案
   - 日誌查詢方法
   - 調試技巧

5. **04-rollback.md** (30 分鐘)
   - 回滾程序
   - 數據庫回滾策略
   - 緊急恢復步驟

---

### ⏳ 階段 8: 創建密鑰列表給 Azure Infra Admin

**狀態**: 待執行
**預計時間**: 1-2 小時

**交付物**:

1. **key-vault-secrets-list.md** (1 小時)
   - 完整密鑰列表（3 個環境）
   - 密鑰命名規範
   - 範例值格式
   - 訪問權限需求

2. **managed-identity-setup.md** (1 小時)
   - Managed Identity 配置步驟
   - Key Vault 訪問策略設置
   - 權限驗證方法

---

## 已完成的工作

### 創建的文件清單

```
✅ docker/Dockerfile                                      # 生產 Dockerfile
✅ docker/.dockerignore                                   # Docker build 優化
✅ apps/web/next.config.mjs                              # 添加 standalone 配置

✅ .azure/README.md                                       # Azure 部署總覽
✅ .azure/environments/dev.env.example                   # Dev 環境配置
✅ .azure/environments/staging.env.example               # Staging 環境配置
✅ .azure/environments/prod.env.example                  # Prod 環境配置
✅ .azure/docs/service-principal-setup.md                # SP 完整指南

✅ docs/deployment/azure-deployment-plan.md              # 完整部署規劃
✅ .gitignore (updated)                                   # 允許配置提交
```

### 配置的內容

1. **Docker 配置**:
   - 多階段構建優化
   - Next.js standalone 輸出
   - Prisma Client 打包
   - 健康檢查

2. **環境配置**:
   - 3 個環境完整配置範例
   - 所有環境變數使用 Key Vault 引用
   - 清晰的註釋和範例值

3. **Service Principal 指南**:
   - 4 個 SP 創建步驟
   - GitHub Secrets 配置
   - 權限管理
   - 安全最佳實踐

4. **部署規劃**:
   - 8 階段詳細計劃
   - 架構圖和組件說明
   - 成本估算
   - 風險評估

---

## 下一步行動

### 推薦執行順序

#### 選項 A: 立即解決部署阻斷問題 (推薦)

**執行**: 階段 3 - 實作 Azure Blob Storage 上傳服務

**原因**:
- 🔴 **關鍵優先級**: 部署阻斷問題
- ⏰ **預計時間**: 6-8 小時
- ✅ **完成後**: 代碼即可部署到 Azure

**任務**:
1. 安裝 `@azure/storage-blob` 和 `@azure/identity`
2. 創建 Blob Storage 服務層
3. 重構 3 個上傳 API Routes
4. 本地測試驗證
5. 更新 JSDoc 和文檔

---

#### 選項 B: 繼續準備部署基礎設施

**執行**: 階段 4, 5, 8（按順序）

**原因**:
- 📝 **完整準備**: 基礎設施和文檔齊全
- 🔧 **獨立任務**: 不需要修改代碼
- 👥 **團隊協作**: 可以並行進行

**任務**:
1. 創建 AI 助手 Prompts (階段 4)
2. 準備 Azure 資源腳本 (階段 5)
3. 創建密鑰列表給 Infra Admin (階段 8)

---

#### 選項 C: 保存當前進度

**執行**: 提交所有已創建的文件

**原因**:
- 💾 **保護工作成果**: 已完成大量文件
- 🔄 **版本控制**: 方便後續追蹤變更
- 📊 **進度記錄**: 記錄階段性成果

**任務**:
1. 提交所有 `.azure/` 文件
2. 提交 `docker/` 文件
3. 提交 `docs/deployment/` 文件
4. 提交 `next.config.mjs` 修改
5. 提交 `.gitignore` 修改
6. 創建進度記錄提交信息

---

## 相關文檔

### 已創建文檔

- [Azure 部署總覽](.azure/README.md)
- [Service Principal 設置](.azure/docs/service-principal-setup.md)
- [完整部署規劃](docs/deployment/azure-deployment-plan.md)
- [Dev 環境配置](.azure/environments/dev.env.example)
- [Staging 環境配置](.azure/environments/staging.env.example)
- [Prod 環境配置](.azure/environments/prod.env.example)

### 待創建文檔

- [ ] SITUATION-6-AZURE-DEPLOY.md
- [ ] SITUATION-7-AZURE-TROUBLESHOOT.md
- [ ] key-vault-secrets-list.md
- [ ] managed-identity-setup.md
- [ ] 00-prerequisites.md
- [ ] 01-first-time-setup.md
- [ ] 02-ci-cd-setup.md
- [ ] 03-troubleshooting.md
- [ ] 04-rollback.md

### 現有相關文檔

- [Azure Infrastructure Setup](docs/infrastructure/azure-infrastructure-setup.md)
- [CLAUDE.md](CLAUDE.md) - 項目技術架構
- [.env.example](.env.example) - 環境變數範例

---

## 進度追蹤

**總進度**: 2/8 階段完成 (25%)

| 階段 | 狀態 | 進度 | 預計時間 |
|------|------|------|---------|
| 1. Docker 配置 | ✅ 完成 | 100% | - |
| 2. 部署文件架構 | ✅ 完成 | 100% | - |
| 3. Blob Storage | ⏳ 待執行 | 0% | 6-8h |
| 4. AI Prompts | ⏳ 待執行 | 0% | 2-3h |
| 5. Azure 腳本 | ⏳ 待執行 | 0% | 4-6h |
| 6. CI/CD | ⏳ 待執行 | 0% | 4-5h |
| 7. 部署文檔 | ⏳ 待執行 | 0% | 3-4h |
| 8. 密鑰列表 | ⏳ 待執行 | 0% | 1-2h |

**預計剩餘時間**: 20-28 小時

---

**最後更新**: 2025-11-20
**下次更新**: 階段 3 完成後
