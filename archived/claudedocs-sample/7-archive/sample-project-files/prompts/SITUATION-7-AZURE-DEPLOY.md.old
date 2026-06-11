# SITUATION-7: Azure 部署指引

**用途**: 當需要執行 Azure 部署任務時，使用此指引確保正確、安全、高效的部署流程。

**觸發情境**:
- 首次部署到 Azure 環境（Dev/Staging/Prod）
- 更新現有 Azure 資源配置
- 執行應用程式版本部署
- 配置 CI/CD Pipeline
- 故障排查部署問題

---

## 🎯 核心原則

### 1. 安全第一
```yaml
security_checklist:
  - ✅ 切勿在代碼中硬編碼密鑰
  - ✅ 所有敏感資料存放在 Azure Key Vault
  - ✅ 使用 Managed Identity 進行服務間認證
  - ✅ 驗證 Service Principal 權限最小化
  - ✅ 生產環境需要人工審批
  - ✅ 部署前備份現有配置
```

### 2. 階段性部署
```yaml
deployment_sequence:
  1. Dev 環境: 自動部署，快速驗證
  2. Staging 環境: 自動部署 + 完整測試
  3. Production 環境: 手動審批 + Blue-Green 部署
```

### 3. 驗證為王
```yaml
validation_gates:
  pre_deployment:
    - 環境變數完整性檢查
    - 依賴服務可用性驗證
    - 資源配額檢查

  post_deployment:
    - 煙霧測試（5 個關鍵端點）
    - 健康檢查端點響應
    - 日誌檢查無錯誤
```

---

## 📋 部署前檢查清單

### 環境準備
```bash
# 1. 登入 Azure CLI
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# 2. 驗證必需工具
node --version     # >= 20.0.0
pnpm --version     # >= 8.0.0
docker --version   # 確認 Docker daemon 運行中

# 3. 檢查環境變數
pnpm check:env

# 4. 驗證 Azure 連接性
bash .azure/tests/test-azure-connectivity.sh dev
```

### 密鑰配置檢查
```bash
# 確認 Key Vault 密鑰已設置
bash .azure/scripts/helper/list-secrets.sh dev

# 驗證 App Service 環境變數
bash .azure/tests/test-environment-config.sh dev
```

---

## 🚀 部署執行流程

### 方案 A: 使用 CI/CD Pipeline（推薦）

#### 1. 部署到 Dev 環境
```yaml
workflow: .github/workflows/azure-deploy-dev.yml
trigger: push to main branch
approval: 不需要
steps:
  1. 自動觸發 GitHub Actions
  2. 構建 Docker 鏡像
  3. 推送到 ACR
  4. 部署到 App Service (Dev Slot)
  5. 執行煙霧測試
  6. 通知部署結果
```

#### 2. 部署到 Staging 環境
```yaml
workflow: .github/workflows/azure-deploy-staging.yml
trigger: manual dispatch 或 tag push
approval: 不需要
steps:
  1. 手動觸發或自動觸發（git tag v*）
  2. 構建生產級 Docker 鏡像
  3. 推送到 ACR (staging tag)
  4. 部署到 Staging Slot
  5. 執行完整測試套件
  6. 生成測試報告
```

#### 3. 部署到 Production 環境
```yaml
workflow: .github/workflows/azure-deploy-prod.yml
trigger: manual dispatch only
approval: ✅ 需要（Team Lead/DevOps）
steps:
  1. 手動觸發工作流
  2. 等待審批（GitHub Environment Protection）
  3. 構建生產 Docker 鏡像
  4. 推送到 ACR (prod tag)
  5. 部署到 Production Staging Slot
  6. 執行煙霧測試
  7. **Slot Swap** (Staging → Production)
  8. 監控 5 分鐘無異常
  9. 通知部署成功
```

### 方案 B: 手動部署腳本

#### 1. 首次部署 - 創建資源
```bash
# 按順序執行資源配置腳本
bash .azure/scripts/01-setup-resources.sh dev
bash .azure/scripts/02-setup-database.sh dev
bash .azure/scripts/03-setup-storage.sh dev
bash .azure/scripts/04-setup-acr.sh dev
bash .azure/scripts/05-setup-appservice.sh dev

# 配置環境變數和密鑰
bash .azure/scripts/helper/configure-app-settings.sh dev

# 驗證配置
bash .azure/tests/test-environment-config.sh dev
```

#### 2. 應用程式部署
```bash
# 構建 Docker 鏡像
docker build -t itpm-web:latest -f docker/Dockerfile .

# 標記並推送到 ACR
az acr login --name acritpmdev
docker tag itpm-web:latest acritpmdev.azurecr.io/itpm-web:v1.0.0
docker push acritpmdev.azurecr.io/itpm-web:v1.0.0

# 部署到 App Service
bash .azure/scripts/06-deploy-app.sh dev v1.0.0

# 執行煙霧測試
bash .azure/tests/smoke-test.sh dev
```

---

## 🔍 部署後驗證

### 自動化驗證
```bash
# 1. 煙霧測試（5 個關鍵測試）
bash .azure/tests/smoke-test.sh <environment>
# 預期結果: 5/5 tests passed

# 2. 健康檢查
bash .azure/scripts/helper/verify-deployment.sh <environment>
# 預期結果: App State = Running, HTTP 200

# 3. 查看最近日誌
az webapp log tail --name app-itpm-<env>-001 --resource-group rg-itpm-<env>
```

### 手動驗證
```yaml
manual_checks:
  - 訪問應用程式 URL: https://app-itpm-<env>-001.azurewebsites.net
  - 測試登入功能（Azure AD B2C + 本地認證）
  - 驗證資料庫連接（創建測試項目）
  - 檢查文件上傳（Blob Storage）
  - 查看通知系統（Email 測試）
```

---

## 🛡️ 安全最佳實踐

### 密鑰管理
```yaml
key_vault_usage:
  naming_convention: "ITPM-{ENV}-{CATEGORY}-{NAME}"

  required_secrets:
    - ITPM-{ENV}-DATABASE-URL
    - ITPM-{ENV}-NEXTAUTH-SECRET
    - ITPM-{ENV}-AZUREADB2C-CLIENT-SECRET
    - ITPM-{ENV}-STORAGE-ACCOUNT-KEY
    - ITPM-{ENV}-SENDGRID-API-KEY

  rotation_schedule:
    NEXTAUTH-SECRET: 每 90 天
    STORAGE-ACCOUNT-KEY: 每 180 天
    SENDGRID-API-KEY: 每年
```

### 輪換密鑰
```bash
# 生成新密鑰
NEW_SECRET=$(openssl rand -base64 32)

# 輪換 Key Vault 密鑰
bash .azure/scripts/helper/rotate-secret.sh prod NEXTAUTH-SECRET "$NEW_SECRET"

# 腳本會自動：
# 1. 備份舊版本資訊
# 2. 創建新版本
# 3. 重啟 App Service
# 4. 驗證健康狀態
```

---

## 📊 監控和日誌

### 查看應用程式日誌
```bash
# 即時日誌串流
az webapp log tail --name app-itpm-<env>-001 --resource-group rg-itpm-<env>

# 下載日誌文件
az webapp log download --name app-itpm-<env>-001 --resource-group rg-itpm-<env>

# 查看 Docker 容器日誌
az webapp log show --name app-itpm-<env>-001 --resource-group rg-itpm-<env>
```

### Application Insights（未來增強）
```yaml
monitoring_setup:
  - 配置 Application Insights
  - 設置自定義指標
  - 配置告警規則
  - 創建儀表板
```

---

## 🔄 回滾程序

### Production 環境回滾
```bash
# 方案 1: Slot Swap 回滾（最快）
az webapp deployment slot swap \
  --name app-itpm-prod-001 \
  --resource-group rg-itpm-prod \
  --slot staging \
  --target-slot production \
  --action swap

# 方案 2: 部署舊版本鏡像
az webapp config container set \
  --name app-itpm-prod-001 \
  --resource-group rg-itpm-prod \
  --docker-custom-image-name acritpmprod.azurecr.io/itpm-web:v1.0.0-previous

# 方案 3: 從 Git 回滾並重新部署
git revert <commit-hash>
git push origin main
# 觸發 CI/CD Pipeline
```

### 驗證回滾成功
```bash
# 1. 檢查應用程式版本
curl https://app-itpm-prod-001.azurewebsites.net/api/version

# 2. 執行煙霧測試
bash .azure/tests/smoke-test.sh prod

# 3. 監控錯誤率
# 查看 Application Insights 或日誌
```

---

## 📚 常見部署情境

### 情境 1: 資料庫遷移部署
```yaml
steps:
  1. 備份生產資料庫:
     pg_dump > backup-$(date +%Y%m%d).sql

  2. 在 Staging 測試遷移:
     pnpm db:migrate

  3. 部署應用到 Staging Slot:
     執行 CI/CD Pipeline

  4. 驗證遷移成功:
     pnpm db:studio
     檢查新欄位/表格

  5. Slot Swap 到 Production:
     az webapp deployment slot swap

  6. 監控應用程式日誌:
     az webapp log tail
```

### 情境 2: 環境變數更新
```bash
# 1. 在 Key Vault 更新密鑰
az keyvault secret set \
  --vault-name kv-itpm-prod \
  --name ITPM-PROD-NEW-SETTING \
  --value "new-value"

# 2. 更新 App Service 環境變數
az webapp config appsettings set \
  --name app-itpm-prod-001 \
  --resource-group rg-itpm-prod \
  --settings NEW_SETTING="@Microsoft.KeyVault(VaultName=kv-itpm-prod;SecretName=ITPM-PROD-NEW-SETTING)"

# 3. 重啟應用程式
az webapp restart --name app-itpm-prod-001 --resource-group rg-itpm-prod

# 4. 驗證新設置生效
bash .azure/tests/test-environment-config.sh prod
```

### 情境 3: 緊急修復部署
```yaml
priority: 🚨 Critical
timeline: < 30 minutes

steps:
  1. 創建 hotfix 分支:
     git checkout -b hotfix/critical-bug

  2. 修復 + 提交:
     git commit -m "fix: critical security vulnerability"

  3. 直接部署到 Production Staging Slot:
     手動觸發 azure-deploy-prod.yml

  4. 快速煙霧測試:
     bash .azure/tests/smoke-test.sh prod

  5. 立即 Swap:
     az webapp deployment slot swap

  6. 監控 10 分鐘:
     az webapp log tail

  7. 合併 hotfix:
     git checkout main
     git merge hotfix/critical-bug
```

---

## ⚙️ 配置參考

### App Service 配置
```yaml
app_service_settings:
  runtime: "NODE:20-lts"
  always_on: true
  http20_enabled: true

  deployment_slots:
    staging:
      auto_swap: false
      traffic_percentage: 0

    production:
      traffic_percentage: 100

  health_check:
    path: "/api/health"
    interval: 30
    timeout: 10
```

### Docker 配置
```yaml
docker_settings:
  registry: "acritpm{env}.azurecr.io"
  image_name: "itpm-web"
  tag_strategy: "v{major}.{minor}.{patch}"

  build_args:
    NODE_ENV: production
    NEXT_TELEMETRY_DISABLED: 1

  resource_limits:
    cpu: "2.0"
    memory: "4Gi"
```

---

## 🎓 學習資源

### 官方文檔
- [Azure App Service 文檔](https://docs.microsoft.com/azure/app-service/)
- [Azure Key Vault 最佳實踐](https://docs.microsoft.com/azure/key-vault/general/best-practices)
- [Azure Container Registry](https://docs.microsoft.com/azure/container-registry/)

### 內部文檔
- `docs/deployment/01-first-time-setup.md` - 首次部署完整指南
- `docs/deployment/02-ci-cd-setup.md` - CI/CD 配置指南
- `docs/deployment/03-troubleshooting.md` - 常見問題排查
- `.azure/README.md` - Azure 配置總覽

---

## 📞 支持和協助

### 問題排查流程
1. 查看 `docs/deployment/03-troubleshooting.md`
2. 檢查應用程式日誌: `az webapp log tail`
3. 驗證環境配置: `bash .azure/tests/test-environment-config.sh`
4. 查看 GitHub Actions 工作流日誌
5. 聯繫 DevOps 團隊

### 聯絡資訊
- DevOps Team: devops@company.com
- Azure 管理員: azure-admin@company.com
- 緊急熱線: +886-XXX-XXXX

---

**版本**: 1.0.0
**最後更新**: 2025-11-20
**維護者**: DevOps Team
