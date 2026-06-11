# Azure 部署架構決策記錄 (ADR)

**創建日期**: 2025-11-20
**目的**: 記錄所有關鍵架構決策、理由和影響

---

## 📋 決策總覽

| 決策編號 | 決策主題 | 狀態 | 影響等級 |
|---------|---------|------|---------|
| ADR-001 | Docker 容器部署 | ✅ 已採用 | 🔴 關鍵 |
| ADR-002 | Azure Key Vault 策略 | ✅ 已採用 | 🔴 關鍵 |
| ADR-003 | Service Principal 管理 | ✅ 已採用 | 🔴 關鍵 |
| ADR-004 | Azure Blob Storage | ✅ 已採用 | 🔴 關鍵 |
| ADR-005 | Next.js Standalone 輸出 | ✅ 已採用 | 🟡 高 |
| ADR-006 | CI/CD 使用 GitHub Actions | ✅ 已採用 | 🟡 高 |
| ADR-007 | 環境變數格式 | ✅ 已採用 | 🟡 高 |
| ADR-008 | Terraform 可選性 | 📋 待決定 | 🟢 中 |

---

## ADR-001: Docker 容器部署

### 決策內容
採用 Docker 容器部署到 Azure App Service，不使用代碼部署 (Code Deployment)。

### 理由
1. **一致性**: 開發、測試、生產環境完全一致
2. **可移植性**: 未來可輕鬆遷移到 AKS 或其他 Kubernetes 平台
3. **依賴管理**: 所有依賴（Node.js、系統庫、Prisma）打包在鏡像中
4. **版本控制**: 每個版本有唯一的鏡像標籤，便於回滾
5. **行業最佳實踐**: 現代 Node.js 應用標準部署方式

### 實施細節
```dockerfile
# 多階段構建
FROM node:20-alpine AS base
FROM base AS builder  # 構建階段
FROM base AS runner   # 運行階段
```

### 影響
- ✅ **正面影響**:
  - 部署流程簡化
  - 環境一致性保證
  - 更容易進行藍綠部署
  - 便於未來擴展到多容器架構

- ⚠️ **需要額外工作**:
  - 設置 Azure Container Registry (ACR)
  - 創建 Docker 構建腳本
  - CI/CD 需要包含鏡像構建步驟

### 相關文件
- `docker/Dockerfile` - 生產環境 Dockerfile
- `docker/Dockerfile.dev` - 開發環境 Dockerfile
- `docker/.dockerignore` - 構建優化
- `.azure/scripts/04-setup-acr.sh` - ACR 設置腳本

### 狀態
✅ **已採用** - Dockerfile 已創建並測試

---

## ADR-002: Azure Key Vault 策略

### 決策內容
使用公司現有的 Azure Key Vault，不創建新的 Key Vault。

### 理由
1. **成本節約**: 避免創建額外的 Key Vault 資源
2. **統一管理**: 所有秘密在同一 Key Vault 中集中管理
3. **權限簡化**: 使用現有的 RBAC 和存取策略
4. **合規性**: 符合公司安全政策和審計要求
5. **運維成本**: 減少需要維護的基礎設施

### 實施細節
**Key Vault 引用格式**:
```bash
DATABASE_URL=@Microsoft.KeyVault(VaultName=YOUR_COMPANY_KV;SecretName=ITPM-DEV-DATABASE-URL)
NEXTAUTH_SECRET=@Microsoft.KeyVault(VaultName=YOUR_COMPANY_KV;SecretName=ITPM-DEV-NEXTAUTH-SECRET)
```

**命名約定**:
- **Dev 環境**: `ITPM-DEV-{SECRET_NAME}`
- **Staging 環境**: `ITPM-STAGING-{SECRET_NAME}`
- **Prod 環境**: `ITPM-PROD-{SECRET_NAME}`

### 影響
- ✅ **正面影響**:
  - 零額外基礎設施成本
  - 利用現有安全基礎設施
  - 統一的秘密管理流程
  - 簡化權限管理

- ⚠️ **需要協調**:
  - 需要向 IT 部門申請 Key Vault 存取權限
  - 需要創建 30+ 個秘密（每個環境 ~10 個）
  - 需要配置 Managed Identity 的存取策略

### 相關文件
- `.azure/environments/dev.env.example` - Dev 環境範例
- `.azure/environments/staging.env.example` - Staging 環境範例
- `.azure/environments/prod.env.example` - Prod 環境範例
- `docs/deployment/key-vault-secrets-list.md` - 完整秘密清單
- `docs/deployment/managed-identity-setup.md` - Managed Identity 配置指南

### 狀態
✅ **已採用** - 環境範例已創建

---

## ADR-003: Service Principal 管理

### 決策內容
統一使用 Service Principal 進行所有 Azure 自動化操作，不使用個人帳戶。

### 理由
1. **安全性**: Service Principal 是機器身份，沒有人員變動風險
2. **權限控制**: 可以精確控制每個 SP 的權限範圍
3. **審計追蹤**: 所有操作都可追溯到特定 SP
4. **最佳實踐**: 符合 Azure 安全建議
5. **CI/CD 需求**: GitHub Actions 需要 SP 憑證

### 實施細節
**4 個 Service Principal**:

1. **ITPM-Deploy-Dev-SP**
   - 用途: Dev 環境 CI/CD
   - 權限: Resource Group Contributor
   - GitHub Secret: `AZURE_CREDENTIALS_DEV`

2. **ITPM-Deploy-Staging-SP**
   - 用途: Staging 環境 CI/CD
   - 權限: Resource Group Contributor
   - GitHub Secret: `AZURE_CREDENTIALS_STAGING`

3. **ITPM-Deploy-Prod-SP**
   - 用途: Prod 環境 CI/CD
   - 權限: Resource Group Contributor
   - GitHub Secret: `AZURE_CREDENTIALS_PROD`

4. **ITPM-AI-Tools-SP**
   - 用途: AI 助手 (Claude/Cursor) 執行自動化腳本
   - 權限: Reader + 特定操作權限
   - 存儲位置: `.azure/credentials.json` (gitignored)

### 影響
- ✅ **正面影響**:
  - 更高的安全性
  - 更好的權限隔離
  - 完整的審計記錄
  - 符合企業安全標準

- ⚠️ **需要維護**:
  - SP 憑證需要定期輪換（90 天）
  - 需要創建和配置 4 個 SP
  - 需要管理 GitHub Secrets

### 相關文件
- `.azure/docs/service-principal-setup.md` - SP 創建指南
- `scripts/azure/create-service-principal.sh` - 自動化創建腳本
- `scripts/azure/rotate-secrets.sh` - 憑證輪換腳本

### 狀態
✅ **已採用** - 設置指南已創建

---

## ADR-004: Azure Blob Storage

### 決策內容
將文件上傳從本地文件系統遷移到 Azure Blob Storage。

### 理由
1. **Azure App Service 限制**: 容器文件系統是臨時的，重啟會丟失
2. **可擴展性**: Blob Storage 支持無限擴展
3. **成本效率**: 按使用付費，比 Persistent Volume 便宜
4. **高可用性**: 內建跨區域複製
5. **CDN 整合**: 未來可輕鬆接入 Azure CDN
6. **安全性**: 支持 SAS Token 和細粒度權限控制

### 實施細節
**當前問題**:
```typescript
// ❌ 當前實作 - 本地文件系統
const uploadDir = path.join(process.cwd(), "public/uploads/quotes");
await fs.mkdir(uploadDir, { recursive: true });
const filePath = path.join(uploadDir, fileName);
await fs.writeFile(filePath, buffer);
```

**遷移方案**:
```typescript
// ✅ 新實作 - Azure Blob Storage
import { uploadToBlob } from "@/lib/azure-storage";

const blobUrl = await uploadToBlob(
  file,
  "quotes",  // container name
  fileName
);

// 數據庫存儲 Blob URL 而不是本地路徑
await prisma.quote.update({
  where: { id },
  data: { filePath: blobUrl }
});
```

**環境檢測**:
```typescript
// 支持本地開發（Azurite）和生產環境
const storageConnectionString =
  process.env.NODE_ENV === "production"
    ? process.env.AZURE_STORAGE_CONNECTION_STRING
    : "UseDevelopmentStorage=true";  // Azurite
```

### 影響
- ✅ **正面影響**:
  - 解決部署阻斷問題
  - 文件永久保存
  - 支持大文件上傳
  - 更好的災難恢復能力

- ⚠️ **需要額外工作**:
  - 創建 3 個 Blob Container (quotes, invoices, proposals)
  - 修改 3 個上傳 API 路由
  - 安裝 `@azure/storage-blob` 和 `@azure/identity`
  - 本地開發需要 Azurite
  - 遷移現有文件到 Blob Storage

### 相關文件
- `apps/web/src/lib/azure-storage.ts` - Blob Storage 服務層
- `apps/web/src/app/api/upload/quote/route.ts` - 報價單上傳
- `apps/web/src/app/api/upload/invoice/route.ts` - 發票上傳
- `apps/web/src/app/api/upload/proposal/route.ts` - 提案上傳
- `scripts/deployment/migrate-to-blob.js` - 數據遷移腳本
- `.azure/scripts/03-setup-storage.sh` - Blob Storage 設置

### 狀態
🚨 **關鍵阻斷** - 必須在首次部署前完成

---

## ADR-005: Next.js Standalone 輸出

### 決策內容
啟用 Next.js 的 `output: 'standalone'` 模式用於 Docker 部署。

### 理由
1. **鏡像大小**: 顯著減少 Docker 鏡像大小（~50% 減少）
2. **啟動速度**: 更快的容器啟動時間
3. **依賴優化**: 只包含生產環境需要的依賴
4. **官方推薦**: Next.js 官方推薦的 Docker 部署方式
5. **資源效率**: 更少的內存和存儲占用

### 實施細節
**next.config.mjs 修改**:
```javascript
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@itpm/api', '@itpm/db'],

  // ✅ 啟用 standalone 輸出
  output: 'standalone',

  // Turborepo monorepo 支持
  experimental: {
    outputFileTracingRoot: path.join(__dirname, '../../'),
  },
};
```

**Dockerfile 整合**:
```dockerfile
# 複製 standalone 輸出
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

# 啟動命令
CMD ["node", "apps/web/server.js"]
```

### 影響
- ✅ **正面影響**:
  - 鏡像大小: ~1.5GB → ~500MB
  - 啟動時間: ~10s → ~3s
  - 內存使用: ~500MB → ~250MB
  - 更好的資源利用率

- ⚠️ **需要注意**:
  - Public 文件需要單獨複製
  - Static 文件需要單獨複製
  - Monorepo 需要配置 `outputFileTracingRoot`

### 相關文件
- `apps/web/next.config.mjs` - Next.js 配置
- `docker/Dockerfile` - 生產 Dockerfile
- `docker/Dockerfile.dev` - 開發 Dockerfile

### 狀態
✅ **已採用** - 配置已完成並測試

---

## ADR-006: CI/CD 使用 GitHub Actions

### 決策內容
使用 GitHub Actions 作為 CI/CD 平台，不使用 Azure DevOps Pipelines。

### 理由
1. **代碼同源**: 代碼和 CI/CD 配置在同一個 GitHub 倉庫
2. **成本**: GitHub Actions 對開源和小團隊免費
3. **生態系統**: 豐富的社區 Actions 和範例
4. **熟悉度**: 團隊已熟悉 GitHub 工作流
5. **簡單性**: 不需要額外的 Azure DevOps 組織設置

### 實施細節
**3 個獨立的 Workflow**:

1. **azure-deploy-dev.yml**
   - 觸發: Push to `develop` branch
   - 環境: Dev
   - 自動部署: 是

2. **azure-deploy-staging.yml**
   - 觸發: Push to `staging` branch
   - 環境: Staging
   - 自動部署: 是
   - 額外: Smoke tests

3. **azure-deploy-prod.yml**
   - 觸發: Tag push (`v*`)
   - 環境: Production
   - 自動部署: 需要手動批准
   - 額外: 完整測試套件 + 藍綠部署

**共同步驟**:
```yaml
1. Checkout code
2. Setup Node.js 20
3. Install pnpm
4. Install dependencies
5. Run tests
6. Build Docker image
7. Push to ACR
8. Deploy to App Service
9. Database migration
10. Health check
11. Notify (成功/失敗)
```

### 影響
- ✅ **正面影響**:
  - 統一的開發體驗
  - 免費的 CI/CD 計算資源
  - 簡化的權限管理
  - 豐富的社區支持

- ⚠️ **需要配置**:
  - GitHub Secrets (3 個環境的 SP 憑證)
  - GitHub Environments (dev, staging, prod)
  - Branch protection rules

### 相關文件
- `.github/workflows/azure-deploy-dev.yml`
- `.github/workflows/azure-deploy-staging.yml`
- `.github/workflows/azure-deploy-prod.yml`
- `docs/deployment/02-ci-cd-setup.md`

### 狀態
📋 **待實施** - Workflow 文件尚未創建

---

## ADR-007: 環境變數格式

### 決策內容
在 Azure App Service 配置中使用 Key Vault 引用，不直接存儲明文秘密。

### 理由
1. **安全性**: 秘密存儲在 Key Vault，不在 App Service 配置中
2. **審計**: Key Vault 提供完整的存取日誌
3. **輪換**: 更新秘密不需要重啟應用
4. **合規性**: 符合安全合規要求
5. **最佳實踐**: Azure 官方推薦方式

### 實施細節
**環境變數範例檔案** (`.azure/environments/dev.env.example`):
```bash
# ❌ 錯誤: 明文秘密
DATABASE_URL=postgresql://user:password@host/db

# ✅ 正確: Key Vault 引用
DATABASE_URL=@Microsoft.KeyVault(VaultName=YOUR_COMPANY_KV;SecretName=ITPM-DEV-DATABASE-URL)
```

**Azure CLI 配置命令**:
```bash
az webapp config appsettings set \
  --resource-group itpm-dev-rg \
  --name itpm-dev-app \
  --settings \
    "DATABASE_URL=@Microsoft.KeyVault(VaultName=YOUR_COMPANY_KV;SecretName=ITPM-DEV-DATABASE-URL)"
```

**Managed Identity 權限**:
```bash
az keyvault set-policy \
  --name YOUR_COMPANY_KV \
  --object-id <app-service-managed-identity-id> \
  --secret-permissions get list
```

### 影響
- ✅ **正面影響**:
  - 最高級別的秘密保護
  - 集中化的秘密管理
  - 自動的秘密輪換支持
  - 完整的審計追蹤

- ⚠️ **需要配置**:
  - 啟用 App Service Managed Identity
  - 配置 Key Vault 存取策略
  - 在 Key Vault 中創建所有秘密

### 相關文件
- `.azure/environments/*.env.example` - 環境變數範例
- `docs/deployment/key-vault-secrets-list.md` - 秘密清單
- `docs/deployment/managed-identity-setup.md` - Managed Identity 指南
- `.azure/scripts/05-setup-appservice.sh` - App Service 設置

### 狀態
✅ **已採用** - 範例文件已創建

---

## ADR-008: Terraform 可選性

### 決策內容
Terraform IaC (Infrastructure as Code) 為可選功能，不作為首次部署的必需項。

### 理由
1. **學習曲線**: Terraform 需要額外學習投入
2. **手動可行**: Azure CLI 腳本已足夠應對當前規模
3. **靈活性**: 先使用腳本驗證架構，後期再轉換為 IaC
4. **資源限制**: 6 個 Azure 資源的管理複雜度可控
5. **優先級**: 快速部署優先於完美的 IaC

### 實施選項
**Option A: 使用 Azure CLI 腳本** (當前方案)
```bash
.azure/scripts/
├── 01-setup-resources.sh      # 創建 Resource Group, VNET
├── 02-setup-database.sh        # 創建 PostgreSQL
├── 03-setup-storage.sh         # 創建 Blob Storage
├── 04-setup-acr.sh             # 創建 Container Registry
├── 05-setup-appservice.sh      # 創建 App Service
└── 06-deploy-app.sh            # 部署應用
```

**Option B: 使用 Terraform** (可選升級)
```hcl
.azure/terraform/
├── main.tf                     # 主配置
├── variables.tf                # 變數定義
├── outputs.tf                  # 輸出值
└── README.md                   # 使用指南
```

### 影響
- ✅ **正面影響**:
  - 更快的實施時間
  - 更低的學習成本
  - 更直觀的腳本（對不熟悉 Terraform 的人）
  - 保留未來升級到 IaC 的選項

- ⚠️ **潛在問題**:
  - 手動腳本容易出錯
  - 缺少狀態追蹤
  - 環境重建較困難
  - 不符合 IaC 最佳實踐

### 決策標準
**何時應該使用 Terraform**:
- ✅ 需要管理 >10 個 Azure 資源
- ✅ 多個環境需要完全一致
- ✅ 團隊熟悉 Terraform
- ✅ 需要版本控制基礎設施狀態
- ✅ 計劃頻繁重建環境

**何時可以使用腳本**:
- ✅ 資源數量 <10 個
- ✅ 環境變化不頻繁
- ✅ 團隊不熟悉 Terraform
- ✅ 優先考慮快速部署
- ✅ 手動操作可接受

### 相關文件
- `.azure/scripts/*.sh` - 6 個 Azure CLI 腳本
- `.azure/terraform/*.tf` - (可選) Terraform 配置
- `docs/deployment/01-first-time-setup.md` - 首次部署指南

### 狀態
📋 **待決定** - 首次部署後根據實際情況決定

---

## 📊 決策影響矩陣

| 決策 | 安全性 | 成本 | 複雜度 | 維護性 | 可擴展性 |
|------|--------|------|--------|--------|---------|
| ADR-001 Docker | 🟢 高 | 🟡 中 | 🟢 低 | 🟢 高 | 🟢 優秀 |
| ADR-002 Key Vault | 🟢 優秀 | 🟢 低 | 🟡 中 | 🟢 高 | 🟢 優秀 |
| ADR-003 Service Principal | 🟢 優秀 | 🟢 免費 | 🟡 中 | 🟡 中 | 🟢 高 |
| ADR-004 Blob Storage | 🟢 高 | 🟢 低 | 🟡 中 | 🟢 高 | 🟢 優秀 |
| ADR-005 Standalone | 🟢 高 | 🟢 優秀 | 🟢 低 | 🟢 高 | 🟢 高 |
| ADR-006 GitHub Actions | 🟢 高 | 🟢 免費 | 🟢 低 | 🟢 高 | 🟢 高 |
| ADR-007 Env Format | 🟢 優秀 | 🟢 免費 | 🟡 中 | 🟢 高 | 🟢 高 |
| ADR-008 No Terraform | 🟡 中 | 🟢 免費 | 🟢 低 | 🟡 中 | 🟡 中 |

**圖例**:
- 🟢 **優秀/高/低** (取決於指標，越綠越好)
- 🟡 **中等**
- 🔴 **差/低/高** (取決於指標，紅色表示關注點)

---

## 🔄 決策審查計劃

### 短期審查 (1 個月後)
1. **ADR-004 Blob Storage** - 驗證性能和成本
2. **ADR-006 GitHub Actions** - 評估 CI/CD 穩定性
3. **ADR-008 Terraform** - 重新評估是否需要 IaC

### 中期審查 (3 個月後)
1. **ADR-001 Docker** - 評估是否需要遷移到 AKS
2. **ADR-003 Service Principal** - 檢查憑證輪換流程
3. **ADR-007 Env Format** - 評估 Key Vault 成本和複雜度

### 長期審查 (6 個月後)
1. 全面架構審查
2. 根據實際使用情況優化所有決策
3. 考慮引入新技術（如 Azure Functions, Event Grid）

---

## 📚 參考資料

- [Next.js Docker Deployment](https://nextjs.org/docs/deployment#docker-image)
- [Azure App Service Container Deployment](https://learn.microsoft.com/azure/app-service/configure-custom-container)
- [Azure Key Vault Best Practices](https://learn.microsoft.com/azure/key-vault/general/best-practices)
- [Service Principal vs Managed Identity](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [Azure Blob Storage Security](https://learn.microsoft.com/azure/storage/blobs/security-recommendations)
- [GitHub Actions for Azure](https://github.com/marketplace?type=actions&query=azure)

---

**最後更新**: 2025-11-20
**下次審查**: 2025-12-20 (1 個月後)
