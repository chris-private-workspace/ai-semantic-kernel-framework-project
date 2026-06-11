# Azure 部署風險評估與緩解策略

**創建日期**: 2025-11-20
**目的**: 識別部署過程中的所有潛在風險並提供緩解方案

---

## 📊 風險總覽

| 風險ID | 風險類別 | 風險等級 | 狀態 | 影響階段 |
|--------|---------|---------|------|---------|
| RISK-001 | 技術 - 文件存儲 | 🔴 關鍵 | 🚨 阻斷中 | 階段 3 |
| RISK-002 | 成本 - 資源超支 | 🟡 中 | ⚠️ 監控中 | 所有階段 |
| RISK-003 | 安全 - 秘密洩露 | 🔴 關鍵 | 🟢 已緩解 | 階段 2, 8 |
| RISK-004 | 技術 - 數據庫遷移失敗 | 🟡 高 | 📋 待緩解 | 階段 5 |
| RISK-005 | 運維 - CI/CD 失敗 | 🟡 中 | 📋 待緩解 | 階段 6 |
| RISK-006 | 業務 - 服務中斷 | 🟡 高 | 📋 待緩解 | 首次部署 |
| RISK-007 | 合規 - 權限不足 | 🟡 中 | 📋 待緩解 | 階段 2, 5 |
| RISK-008 | 技術 - Docker 鏡像過大 | 🟢 低 | 🟢 已緩解 | 階段 1 |
| RISK-009 | 運維 - 監控盲區 | 🟡 中 | 📋 待緩解 | 部署後 |
| RISK-010 | 技術 - Azure AD B2C 整合 | 🟢 低 | 🟢 已解決 | N/A |

---

## 🔴 關鍵風險 (Critical)

### RISK-001: 文件存儲使用本地文件系統

#### 風險描述
當前實作將上傳的文件（報價單、發票、提案文件）保存到本地文件系統 (`process.cwd()/public/uploads/`)。Azure App Service 的容器文件系統是臨時的，容器重啟後文件會丟失。

#### 影響分析
- **嚴重程度**: 🔴 關鍵 (Critical)
- **發生概率**: 100% (容器重啟必然發生)
- **影響範圍**:
  - 所有上傳的文件將永久丟失
  - 數據庫中的 `filePath` 引用將失效
  - 用戶無法下載歷史文件
  - 業務流程中斷（無法查看報價單、發票等）

#### 受影響的文件
```typescript
// 3 個上傳 API 路由
apps/web/src/app/api/upload/quote/route.ts       // ❌ 使用本地文件系統
apps/web/src/app/api/upload/invoice/route.ts     // ❌ 使用本地文件系統
apps/web/src/app/api/upload/proposal/route.ts    // ❌ 使用本地文件系統
```

#### 當前代碼問題
```typescript
// ❌ 當前實作 - 臨時文件系統
const uploadDir = path.join(process.cwd(), "public/uploads/quotes");
await fs.mkdir(uploadDir, { recursive: true });
const filePath = path.join(uploadDir, fileName);
await fs.writeFile(filePath, buffer);

// 存儲本地路徑到數據庫
await prisma.quote.update({
  where: { id },
  data: { filePath: `/uploads/quotes/${fileName}` }  // ❌ 容器重啟後失效
});
```

#### 緩解策略
**階段 3: Blob Storage 遷移 (必須優先完成)**

1. **安裝依賴**:
```bash
pnpm add @azure/storage-blob @azure/identity
```

2. **創建 Blob Storage 服務層** (`apps/web/src/lib/azure-storage.ts`):
```typescript
import { BlobServiceClient } from "@azure/storage-blob";
import { DefaultAzureCredential } from "@azure/identity";

export async function uploadToBlob(
  file: File,
  containerName: string,
  blobName: string
): Promise<string> {
  const credential = new DefaultAzureCredential();
  const blobServiceClient = new BlobServiceClient(
    `https://${process.env.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net`,
    credential
  );

  const containerClient = blobServiceClient.getContainerClient(containerName);
  const blockBlobClient = containerClient.getBlockBlobClient(blobName);

  const arrayBuffer = await file.arrayBuffer();
  await blockBlobClient.upload(arrayBuffer, arrayBuffer.byteLength);

  return blockBlobClient.url;  // ✅ 返回永久 Blob URL
}
```

3. **修改上傳路由**:
```typescript
// ✅ 新實作 - Azure Blob Storage
import { uploadToBlob } from "@/lib/azure-storage";

const blobUrl = await uploadToBlob(file, "quotes", fileName);

await prisma.quote.update({
  where: { id },
  data: { filePath: blobUrl }  // ✅ 永久 Blob URL
});
```

4. **環境變數配置**:
```bash
# Dev 環境使用 Azurite (本地 Blob 模擬器)
AZURE_STORAGE_ACCOUNT_NAME=devstoreaccount1
AZURE_STORAGE_USE_DEVELOPMENT=true

# Prod 環境使用實際 Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=itpmprodstorage
AZURE_STORAGE_USE_DEVELOPMENT=false
```

#### 驗證計劃
- [ ] 本地測試: 使用 Azurite 模擬器測試上傳功能
- [ ] Dev 環境測試: 上傳文件並驗證 Blob URL
- [ ] 容器重啟測試: 重啟容器後驗證文件仍可訪問
- [ ] 遷移腳本測試: 遷移現有文件到 Blob Storage

#### 時間估計
- 實作時間: 6-8 小時
- 測試時間: 2-3 小時
- **總計**: 8-11 小時

#### 狀態
🚨 **阻斷中** - 必須在首次部署前完成

---

### RISK-003: 秘密洩露風險

#### 風險描述
環境變數中包含敏感秘密（數據庫密碼、API 密鑰、Azure 憑證等），如果管理不當可能被洩露到 Git 倉庫或日誌中。

#### 影響分析
- **嚴重程度**: 🔴 關鍵 (Critical)
- **發生概率**: 30% (人為錯誤)
- **影響範圍**:
  - 數據庫被非授權訪問
  - Azure 資源被濫用
  - 潛在的數據洩露
  - 合規違規

#### 緩解策略 (已實施)

1. **✅ 使用 Azure Key Vault**:
   - 所有秘密存儲在 Key Vault 中
   - App Service 使用 Key Vault 引用，不存儲明文

2. **✅ .gitignore 配置**:
```gitignore
# ✅ 已配置
.env
.env.local
.env.*.local
.azure/credentials.json
.azure/*.local
.azure/**/sp-*.json
```

3. **✅ 環境變數範例文件**:
   - 只提交 `.env.example` 文件
   - 使用 Key Vault 引用格式，不包含實際值

4. **✅ GitHub Secrets**:
   - Service Principal 憑證存儲在 GitHub Secrets
   - CI/CD 使用 Secrets，不在代碼中暴露

#### 額外措施
- [ ] 啟用 Azure Key Vault 審計日誌
- [ ] 配置 GitHub Secret Scanning
- [ ] 定期檢查 Git 歷史是否有秘密洩露
- [ ] 使用 `git-secrets` 工具防止提交秘密

#### 狀態
🟢 **已緩解** - 核心措施已實施，額外措施待完成

---

## 🟡 高風險 (High)

### RISK-004: 數據庫遷移失敗

#### 風險描述
Prisma 數據庫遷移在生產環境失敗，導致應用無法啟動或數據損壞。

#### 影響分析
- **嚴重程度**: 🟡 高 (High)
- **發生概率**: 20%
- **影響範圍**:
  - 應用無法啟動
  - 現有數據可能損壞
  - 服務中斷
  - 需要緊急回滾

#### 常見失敗場景
1. **外鍵約束衝突**: 遷移腳本與現有數據不兼容
2. **數據類型不兼容**: PostgreSQL 版本差異
3. **鎖超時**: 遷移過程中表被鎖定
4. **權限不足**: 數據庫用戶缺少 ALTER 權限

#### 緩解策略

**預防措施**:
1. **本地完整測試**:
```bash
# 在本地 PostgreSQL 16 上測試遷移
DATABASE_URL="postgresql://postgres:localdev123@localhost:5434/itpm_dev" pnpm db:migrate
```

2. **Staging 環境驗證**:
   - 在 Staging 環境完全測試遷移流程
   - 使用生產環境數據的匿名化副本測試

3. **遷移腳本審查**:
   - 每個遷移腳本必須經過代碼審查
   - 檢查是否有破壞性更改（如刪除列）

4. **備份策略**:
```bash
# CI/CD 中自動備份
az postgres flexible-server backup create \
  --resource-group itpm-prod-rg \
  --name itpm-prod-db \
  --backup-name "pre-migration-$(date +%Y%m%d-%H%M%S)"
```

**應急計劃**:
1. **遷移失敗處理**:
```yaml
# CI/CD workflow
- name: Database Migration
  run: pnpm db:migrate
  continue-on-error: false  # 失敗立即中止部署

- name: Rollback on Failure
  if: failure()
  run: |
    # 回滾到上一個應用版本
    az webapp deployment slot swap --slot staging --name itpm-prod-app
```

2. **手動回滾計劃**:
```bash
# 1. 恢復數據庫備份
az postgres flexible-server restore \
  --source-server itpm-prod-db \
  --restore-point-in-time "2025-11-20T10:00:00Z"

# 2. 回滾應用到上一個版本
az webapp deployment slot swap --slot staging --name itpm-prod-app
```

#### 驗證清單
- [ ] 本地 PostgreSQL 16 遷移測試通過
- [ ] Staging 環境遷移測試通過
- [ ] 遷移腳本代碼審查完成
- [ ] 備份腳本已加入 CI/CD
- [ ] 回滾計劃已文檔化

#### 狀態
📋 **待緩解** - 階段 5 實施

---

### RISK-006: 服務中斷風險

#### 風險描述
首次部署或後續更新可能導致服務中斷，影響現有用戶。

#### 影響分析
- **嚴重程度**: 🟡 高 (High)
- **發生概率**: 40% (首次部署)
- **影響範圍**:
  - 用戶無法訪問系統
  - 業務流程中斷
  - 用戶信任度下降
  - 可能需要緊急回滾

#### 緩解策略

**1. 藍綠部署 (Blue-Green Deployment)**:
```bash
# Azure App Service 部署槽位
az webapp deployment slot create \
  --name itpm-prod-app \
  --resource-group itpm-prod-rg \
  --slot staging

# 部署到 staging slot
az webapp deployment container config \
  --name itpm-prod-app \
  --resource-group itpm-prod-rg \
  --slot staging \
  --container-image-name itpmprodacr.azurecr.io/itpm-web:v1.2.0

# 驗證 staging slot
curl https://itpm-prod-app-staging.azurewebsites.net/api/health

# 交換槽位 (零停機)
az webapp deployment slot swap \
  --slot staging \
  --name itpm-prod-app \
  --resource-group itpm-prod-rg
```

**2. 健康檢查端點**:
```typescript
// apps/web/src/app/api/health/route.ts
export async function GET() {
  try {
    // 檢查數據庫連接
    await prisma.$queryRaw`SELECT 1`;

    // 檢查 Redis 連接
    await redis.ping();

    return Response.json({
      status: "healthy",
      timestamp: new Date().toISOString(),
      database: "connected",
      redis: "connected"
    });
  } catch (error) {
    return Response.json({
      status: "unhealthy",
      error: error.message
    }, { status: 503 });
  }
}
```

**3. CI/CD 健康檢查**:
```yaml
- name: Health Check
  run: |
    for i in {1..30}; do
      STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://itpm-prod-app-staging.azurewebsites.net/api/health)
      if [ $STATUS -eq 200 ]; then
        echo "Health check passed"
        exit 0
      fi
      echo "Waiting for app to be healthy... ($i/30)"
      sleep 10
    done
    echo "Health check failed after 5 minutes"
    exit 1
```

**4. 維護模式頁面**:
```typescript
// 部署期間顯示維護頁面
export function MaintenanceMode() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold">系統維護中</h1>
        <p className="mt-2 text-gray-600">預計維護時間: 5-10 分鐘</p>
        <p className="mt-1 text-sm text-gray-500">如有緊急需求，請聯繫 IT 支援</p>
      </div>
    </div>
  );
}
```

#### 部署時間窗口
- **Dev 環境**: 隨時部署
- **Staging 環境**: 工作時間（便於測試）
- **Production 環境**:
  - **首次部署**: 週五晚上 21:00 - 23:00 (業務低峰期)
  - **後續更新**: 週二/週四 18:00 - 19:00

#### 溝通計劃
- [ ] 提前 3 天通知所有用戶
- [ ] 部署前 1 天發送提醒郵件
- [ ] 部署開始時在系統中顯示通知
- [ ] 部署完成後發送確認郵件

#### 狀態
📋 **待緩解** - 首次部署前完成

---

## 🟡 中風險 (Medium)

### RISK-002: Azure 資源成本超支

#### 風險描述
Azure 資源使用成本超出預期預算，尤其是數據庫、Blob Storage 和 App Service。

#### 影響分析
- **嚴重程度**: 🟡 中 (Medium)
- **發生概率**: 30%
- **影響範圍**:
  - 預算超支
  - 可能需要降級服務層級
  - 影響長期可持續性

#### 成本預估 (每月)
| 資源 | SKU | 預估成本 (USD) | 優化方案 |
|------|-----|---------------|---------|
| App Service | B1 Basic | $13 | ✅ 合理 |
| PostgreSQL | B1ms (1 vCore, 2GB) | $12 | ✅ 合理 |
| Blob Storage | LRS, Hot Tier | $3-5 | ⚠️ 監控使用量 |
| Container Registry | Basic | $5 | ✅ 合理 |
| Redis Cache | C0 Basic (250MB) | $16 | ⚠️ 考慮按需啟用 |
| **總計** | | **$49-51** | |

#### 緩解策略

**1. 成本監控**:
```bash
# 設置成本警報
az consumption budget create \
  --resource-group itpm-prod-rg \
  --budget-name itpm-monthly-budget \
  --amount 60 \
  --time-grain Monthly \
  --start-date 2025-11-01 \
  --notifications \
    threshold=80 \
    contact-emails=admin@company.com \
    operator=GreaterThan
```

**2. 自動縮放配置**:
```bash
# App Service 自動縮放
az monitor autoscale create \
  --resource-group itpm-prod-rg \
  --resource itpm-prod-app \
  --resource-type Microsoft.Web/serverfarms \
  --min-count 1 \
  --max-count 3 \
  --count 1
```

**3. Blob Storage 生命週期管理**:
```json
{
  "rules": [
    {
      "name": "move-old-quotes-to-cool",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["quotes/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": { "daysAfterModificationGreaterThan": 90 },
            "tierToArchive": { "daysAfterModificationGreaterThan": 365 }
          }
        }
      }
    }
  ]
}
```

**4. 開發環境資源優化**:
- Dev 環境使用較低的 SKU (B1 → Free Tier)
- Dev 環境可以在非工作時間自動停止
- 共享資源（如 Container Registry）

#### 每週成本審查
- [ ] 每週一檢查 Azure Cost Management
- [ ] 識別成本異常（如流量激增）
- [ ] 優化高成本資源
- [ ] 清理未使用的資源

#### 狀態
⚠️ **監控中** - 部署後持續監控

---

### RISK-005: CI/CD Pipeline 失敗

#### 風險描述
GitHub Actions workflow 失敗導致無法自動部署，需要手動干預。

#### 影響分析
- **嚴重程度**: 🟡 中 (Medium)
- **發生概率**: 25%
- **影響範圍**:
  - 部署延遲
  - 需要手動部署
  - 影響開發效率

#### 常見失敗原因
1. **Docker 構建失敗**: 依賴下載超時、網絡問題
2. **ACR 推送失敗**: 憑證過期、網絡問題
3. **測試失敗**: E2E 測試不穩定
4. **數據庫遷移失敗**: 見 RISK-004

#### 緩解策略

**1. 重試機制**:
```yaml
- name: Build and Push Docker Image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: itpmprodacr.azurecr.io/itpm-web:${{ github.sha }}
  env:
    DOCKER_BUILDKIT: 1
  retry:
    max_attempts: 3
    timeout_minutes: 15
```

**2. 依賴緩存**:
```yaml
- name: Setup pnpm
  uses: pnpm/action-setup@v2
  with:
    version: 8.15.3

- name: Cache pnpm dependencies
  uses: actions/cache@v3
  with:
    path: |
      ~/.pnpm-store
      **/node_modules
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}
    restore-keys: |
      ${{ runner.os }}-pnpm-
```

**3. 失敗通知**:
```yaml
- name: Notify on Failure
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.company.com
    server_port: 587
    username: ${{ secrets.SMTP_USERNAME }}
    password: ${{ secrets.SMTP_PASSWORD }}
    subject: "❌ Deployment Failed: ${{ github.workflow }}"
    body: |
      Deployment failed for ${{ github.repository }}
      Branch: ${{ github.ref }}
      Commit: ${{ github.sha }}
      Workflow Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
    to: devops-team@company.com
```

**4. 手動部署備用方案**:
```bash
# 手動部署腳本 (緊急使用)
#!/bin/bash
# scripts/manual-deploy.sh

# 構建 Docker 鏡像
docker build -t itpmprodacr.azurecr.io/itpm-web:manual-$(date +%Y%m%d-%H%M%S) .

# 推送到 ACR
docker push itpmprodacr.azurecr.io/itpm-web:manual-$(date +%Y%m%d-%H%M%S)

# 更新 App Service
az webapp config container set \
  --name itpm-prod-app \
  --resource-group itpm-prod-rg \
  --docker-custom-image-name itpmprodacr.azurecr.io/itpm-web:manual-$(date +%Y%m%d-%H%M%S)
```

#### 狀態
📋 **待緩解** - 階段 6 實施

---

### RISK-007: 權限不足風險

#### 風險描述
Service Principal 或 Managed Identity 權限配置不正確，導致操作失敗。

#### 影響分析
- **嚴重程度**: 🟡 中 (Medium)
- **發生概率**: 35%
- **影響範圍**:
  - CI/CD 無法部署
  - App Service 無法訪問 Key Vault
  - App Service 無法訪問 Blob Storage

#### 所需權限清單

**Service Principal (CI/CD)**:
```bash
# Resource Group Contributor 角色
az role assignment create \
  --assignee <sp-object-id> \
  --role "Contributor" \
  --scope /subscriptions/<sub-id>/resourceGroups/itpm-prod-rg

# ACR Push 權限
az role assignment create \
  --assignee <sp-object-id> \
  --role "AcrPush" \
  --scope /subscriptions/<sub-id>/resourceGroups/itpm-prod-rg/providers/Microsoft.ContainerRegistry/registries/itpmprodacr
```

**Managed Identity (App Service)**:
```bash
# Key Vault Secrets 讀取權限
az keyvault set-policy \
  --name YOUR_COMPANY_KV \
  --object-id <app-service-identity-id> \
  --secret-permissions get list

# Blob Storage Data Contributor 角色
az role assignment create \
  --assignee <app-service-identity-id> \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/<sub-id>/resourceGroups/itpm-prod-rg/providers/Microsoft.Storage/storageAccounts/itpmprodstorage
```

#### 緩解策略

**1. 權限驗證腳本**:
```bash
# scripts/verify-permissions.sh
#!/bin/bash

echo "Verifying Service Principal permissions..."

# 測試 Resource Group 訪問
az group show --name itpm-prod-rg 2>/dev/null
if [ $? -eq 0 ]; then
  echo "✅ Resource Group access: OK"
else
  echo "❌ Resource Group access: FAILED"
fi

# 測試 ACR 訪問
az acr show --name itpmprodacr 2>/dev/null
if [ $? -eq 0 ]; then
  echo "✅ ACR access: OK"
else
  echo "❌ ACR access: FAILED"
fi
```

**2. 最小權限原則**:
- 只授予必要的權限
- 避免使用 Owner 或 Contributor 權限
- 使用 RBAC 而不是 Access Keys

**3. 權限文檔化**:
- 在 `docs/deployment/managed-identity-setup.md` 中詳細記錄所有權限
- 包含完整的 Azure CLI 命令
- 提供權限驗證清單

#### 狀態
📋 **待緩解** - 階段 2, 5 實施

---

### RISK-009: 監控盲區

#### 風險描述
缺少完善的監控和日誌系統，問題發生後難以快速定位和修復。

#### 影響分析
- **嚴重程度**: 🟡 中 (Medium)
- **發生概率**: 60%
- **影響範圍**:
  - 問題發現延遲
  - 故障排查困難
  - 用戶體驗下降

#### 緩解策略

**1. Application Insights 整合**:
```typescript
// apps/web/src/lib/appInsights.ts
import { ApplicationInsights } from '@microsoft/applicationinsights-web';

const appInsights = new ApplicationInsights({
  config: {
    connectionString: process.env.APPLICATIONINSIGHTS_CONNECTION_STRING,
    enableAutoRouteTracking: true,
    enableCorsCorrelation: true,
    enableRequestHeaderTracking: true,
    enableResponseHeaderTracking: true,
  }
});

appInsights.loadAppInsights();
appInsights.trackPageView();

export default appInsights;
```

**2. 結構化日誌**:
```typescript
// 使用 winston 或 pino
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'itpm-web' },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

// 結構化日誌
logger.info('User login', {
  userId: user.id,
  email: user.email,
  timestamp: new Date().toISOString()
});
```

**3. 關鍵指標儀表板**:
- **性能指標**: 響應時間、吞吐量
- **錯誤率**: HTTP 4xx/5xx 錯誤百分比
- **可用性**: 健康檢查成功率
- **資源使用**: CPU、內存、磁盤使用率

**4. 告警規則**:
```bash
# 設置告警
az monitor metrics alert create \
  --name high-error-rate \
  --resource-group itpm-prod-rg \
  --scopes /subscriptions/<sub-id>/resourceGroups/itpm-prod-rg/providers/Microsoft.Web/sites/itpm-prod-app \
  --condition "avg Http5xx > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-ids /subscriptions/<sub-id>/resourceGroups/itpm-prod-rg/providers/Microsoft.Insights/actionGroups/devops-alerts
```

#### 狀態
📋 **待緩解** - 部署後立即實施

---

## 🟢 低風險 (Low)

### RISK-008: Docker 鏡像過大

#### 風險描述
Docker 鏡像體積過大，導致構建和部署時間過長，存儲成本增加。

#### 影響分析
- **嚴重程度**: 🟢 低 (Low)
- **發生概率**: 30%
- **影響範圍**:
  - 構建時間延長
  - 部署時間延長
  - ACR 存儲成本增加

#### 緩解策略 (已實施)

**1. ✅ 多階段構建**:
```dockerfile
# 構建階段 - 只包含構建工具
FROM node:20-alpine AS builder
WORKDIR /app
RUN apk add --no-cache libc6-compat
COPY . .
RUN pnpm install --frozen-lockfile
RUN pnpm build

# 運行階段 - 只包含運行時依賴
FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public
```

**2. ✅ .dockerignore 優化**:
```dockerignore
node_modules
.next
.turbo
.git
*.md
tests
.vscode
```

**3. ✅ Alpine Linux 基礎鏡像**:
```dockerfile
FROM node:20-alpine  # ~180MB vs node:20 ~1GB
```

**4. ✅ Next.js Standalone 輸出**:
```javascript
// next.config.mjs
output: 'standalone'  // 減少 ~50% 鏡像大小
```

#### 實際鏡像大小
- **未優化**: ~1.5GB
- **優化後**: ~500MB
- **壓縮後**: ~200MB

#### 狀態
🟢 **已緩解** - 優化措施已實施

---

### RISK-010: Azure AD B2C 整合問題

#### 風險描述
Azure AD B2C SSO 整合失敗，用戶無法登錄。

#### 影響分析
- **嚴重程度**: 🟢 低 (Low)
- **發生概率**: 5%
- **影響範圍**: SSO 用戶無法登錄（仍可使用本地帳戶）

#### 當前狀態
✅ **已 100% 實現** - 在本地開發環境完整測試

#### 部署時唯一需要更新
在 Azure AD B2C 租戶中配置 Redirect URI:
```
https://itpm-dev-app.azurewebsites.net/api/auth/callback/azure-ad-b2c
https://itpm-staging-app.azurewebsites.net/api/auth/callback/azure-ad-b2c
https://itpm.yourdomain.com/api/auth/callback/azure-ad-b2c
```

#### 驗證計劃
- [ ] Dev 環境測試 Azure AD B2C 登錄
- [ ] Staging 環境測試 Azure AD B2C 登錄
- [ ] Prod 環境測試 Azure AD B2C 登錄

#### 狀態
🟢 **已解決** - 只需配置 Redirect URI

---

## 📋 風險緩解時間表

### 階段 3: Blob Storage 遷移 (第 1-2 週)
- ✅ RISK-001: 文件存儲遷移 (8-11 小時)

### 階段 5: Azure 資源配置 (第 3-4 週)
- 📋 RISK-004: 數據庫遷移失敗 (緩解措施實施)
- 📋 RISK-007: 權限配置 (驗證和文檔化)

### 階段 6: CI/CD Pipeline (第 4-5 週)
- 📋 RISK-005: CI/CD 失敗 (重試機制、緩存、通知)

### 首次部署前 (第 5-6 週)
- 📋 RISK-006: 服務中斷 (藍綠部署、健康檢查、溝通計劃)

### 部署後 (持續)
- ⚠️ RISK-002: 成本監控 (每週審查)
- 📋 RISK-009: 監控系統 (Application Insights 整合)

---

## 🎯 風險緩解優先級

### 🔴 立即處理 (阻斷性)
1. **RISK-001**: Blob Storage 遷移 - 階段 3 必須完成

### 🟡 高優先級 (首次部署前)
2. **RISK-006**: 服務中斷預防 - 藍綠部署配置
3. **RISK-004**: 數據庫遷移失敗 - 備份和回滾策略
4. **RISK-007**: 權限配置 - 完整驗證

### 🟢 中優先級 (部署後 1 個月內)
5. **RISK-005**: CI/CD 穩定性提升
6. **RISK-009**: 監控系統完善
7. **RISK-002**: 成本優化

### ⚪ 低優先級 (已緩解或持續監控)
8. **RISK-003**: 秘密管理 - 已實施，定期審查
9. **RISK-008**: 鏡像大小 - 已優化
10. **RISK-010**: Azure AD B2C - 只需配置 Redirect URI

---

## 📊 風險追蹤儀表板

### 按狀態分類
- 🚨 **阻斷中**: 1 個 (RISK-001)
- 📋 **待緩解**: 4 個 (RISK-004, 005, 006, 007, 009)
- ⚠️ **監控中**: 1 個 (RISK-002)
- 🟢 **已緩解**: 3 個 (RISK-003, 008, 010)

### 按嚴重程度分類
- 🔴 **關鍵**: 2 個 (RISK-001, 003)
- 🟡 **高**: 2 個 (RISK-004, 006)
- 🟡 **中**: 4 個 (RISK-002, 005, 007, 009)
- 🟢 **低**: 2 個 (RISK-008, 010)

---

## 📝 風險審查流程

### 每週風險審查
- **時間**: 每週一 10:00
- **參與者**: 開發團隊、運維負責人
- **議程**:
  1. 檢查新風險
  2. 更新現有風險狀態
  3. 驗證緩解措施效果
  4. 調整優先級

### 每月深度審查
- **時間**: 每月第一個週五 14:00
- **參與者**: 開發團隊、運維團隊、管理層
- **議程**:
  1. 全面風險評估
  2. 緩解策略效果分析
  3. 成本-收益分析
  4. 長期優化計劃

---

**最後更新**: 2025-11-20
**下次審查**: 2025-11-27 (每週審查)
**下次深度審查**: 2025-12-06 (每月深度審查)
