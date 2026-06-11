# Azure 部署文件架構檢查清單

**創建日期**: 2025-11-20
**目的**: 追蹤所有建議創建的文件和目錄的完成狀態

---

## 📊 完成度總覽

**總計**: 9 / 39 個文件已創建 (23%)

| 類別 | 已完成 | 待創建 | 總計 | 完成度 |
|------|--------|--------|------|--------|
| `.azure/` | 5 | 8 | 13 | 38% |
| `docker/` | 2 | 2 | 4 | 50% |
| `docs/deployment/` | 1 | 5 | 6 | 17% |
| `.github/workflows/` | 0 | 3 | 3 | 0% |
| `scripts/` | 0 | 7 | 7 | 0% |
| `claudedocs/` | 1 | 2 | 3 | 33% |
| `其他` | 0 | 3 | 3 | 0% |

---

## 📁 詳細檢查清單

### 1. `.azure/` 目錄 (5/13 = 38%)

#### ✅ 已創建 (5)

```
✅ .azure/README.md
✅ .azure/environments/dev.env.example
✅ .azure/environments/staging.env.example
✅ .azure/environments/prod.env.example
✅ .azure/docs/service-principal-setup.md
```

#### ⏳ 待創建 (8)

```
⏳ .azure/scripts/01-setup-resources.sh
⏳ .azure/scripts/02-setup-database.sh
⏳ .azure/scripts/03-setup-storage.sh
⏳ .azure/scripts/04-setup-acr.sh
⏳ .azure/scripts/05-setup-appservice.sh
⏳ .azure/scripts/06-deploy-app.sh
⏳ .azure/terraform/main.tf (可選)
⏳ .azure/terraform/variables.tf (可選)
```

---

### 2. `docker/` 目錄 (2/4 = 50%)

#### ✅ 已創建 (2)

```
✅ docker/Dockerfile
✅ docker/.dockerignore
```

#### ⏳ 待創建 (2)

```
⏳ docker/Dockerfile.dev
⏳ docker/docker-compose.azure.yml
```

---

### 3. `docs/deployment/` 目錄 (1/6 = 17%)

#### ✅ 已創建 (1)

```
✅ docs/deployment/azure-deployment-plan.md
```

#### ⏳ 待創建 (5)

```
⏳ docs/deployment/00-prerequisites.md
⏳ docs/deployment/01-first-time-setup.md
⏳ docs/deployment/02-ci-cd-setup.md
⏳ docs/deployment/03-troubleshooting.md
⏳ docs/deployment/04-rollback.md
⏳ docs/deployment/key-vault-secrets-list.md
⏳ docs/deployment/managed-identity-setup.md
```

**注意**: 最後兩個文件是額外添加的，不在原建議中。

---

### 4. `.github/workflows/` 目錄 (0/3 = 0%)

#### ⏳ 待創建 (3)

```
⏳ .github/workflows/azure-deploy-dev.yml
⏳ .github/workflows/azure-deploy-staging.yml
⏳ .github/workflows/azure-deploy-prod.yml
```

---

### 5. `scripts/` 目錄 (0/7 = 0%)

#### ⏳ 待創建 - deployment/ (3)

```
⏳ scripts/deployment/pre-deploy-check.js
⏳ scripts/deployment/migrate-to-blob.js
⏳ scripts/deployment/validate-env.js
```

#### ⏳ 待創建 - azure/ (2)

```
⏳ scripts/azure/create-service-principal.sh
⏳ scripts/azure/rotate-secrets.sh
```

#### ⏳ 待創建 - 其他 (2)

```
⏳ scripts/test-docker-build.sh
⏳ scripts/local-azure-test.sh
```

---

### 6. `claudedocs/6-ai-assistant/prompts/` 目錄 (1/3 = 33%)

#### ✅ 已創建 (1)

```
✅ claudedocs/1-planning/features/AZURE-DEPLOY-PREP/00-summary.md
```

#### ⏳ 待創建 (2)

```
⏳ claudedocs/6-ai-assistant/prompts/SITUATION-6-AZURE-DEPLOY.md
⏳ claudedocs/6-ai-assistant/prompts/SITUATION-7-AZURE-TROUBLESHOOT.md
```

---

### 7. 代碼修改 (0/3 = 0%)

#### ⏳ 待創建/修改 (3)

```
⏳ apps/web/src/lib/azure-storage.ts (新建)
⏳ apps/web/src/app/api/upload/quote/route.ts (修改)
⏳ apps/web/src/app/api/upload/invoice/route.ts (修改)
⏳ apps/web/src/app/api/upload/proposal/route.ts (修改)
```

---

## 📋 按階段分組

### ✅ 階段 1: Docker 配置 (已完成)

```
✅ docker/Dockerfile
✅ docker/.dockerignore
✅ apps/web/next.config.mjs (修改 - 添加 standalone)
```

---

### ✅ 階段 2: 部署文件架構 (部分完成)

**已完成**:
```
✅ .azure/README.md
✅ .azure/environments/dev.env.example
✅ .azure/environments/staging.env.example
✅ .azure/environments/prod.env.example
✅ .azure/docs/service-principal-setup.md
✅ docs/deployment/azure-deployment-plan.md
✅ .gitignore (修改)
✅ claudedocs/1-planning/features/AZURE-DEPLOY-PREP/00-summary.md
```

**待完成**:
```
⏳ docker/Dockerfile.dev
⏳ docker/docker-compose.azure.yml
```

---

### ⏳ 階段 3: Blob Storage 實作 (待執行)

```
⏳ apps/web/src/lib/azure-storage.ts
⏳ apps/web/src/app/api/upload/quote/route.ts
⏳ apps/web/src/app/api/upload/invoice/route.ts
⏳ apps/web/src/app/api/upload/proposal/route.ts
⏳ package.json (添加依賴: @azure/storage-blob, @azure/identity)
```

---

### ⏳ 階段 4: AI 助手 Prompts (待執行)

```
⏳ claudedocs/6-ai-assistant/prompts/SITUATION-6-AZURE-DEPLOY.md
⏳ claudedocs/6-ai-assistant/prompts/SITUATION-7-AZURE-TROUBLESHOOT.md
```

---

### ⏳ 階段 5: Azure 資源腳本 (待執行)

```
⏳ .azure/scripts/01-setup-resources.sh
⏳ .azure/scripts/02-setup-database.sh
⏳ .azure/scripts/03-setup-storage.sh
⏳ .azure/scripts/04-setup-acr.sh
⏳ .azure/scripts/05-setup-appservice.sh
⏳ .azure/scripts/06-deploy-app.sh
```

---

### ⏳ 階段 6: CI/CD Pipeline (待執行)

```
⏳ .github/workflows/azure-deploy-dev.yml
⏳ .github/workflows/azure-deploy-staging.yml
⏳ .github/workflows/azure-deploy-prod.yml
```

---

### ⏳ 階段 7: 部署文檔 (待執行)

```
⏳ docs/deployment/00-prerequisites.md
⏳ docs/deployment/01-first-time-setup.md
⏳ docs/deployment/02-ci-cd-setup.md
⏳ docs/deployment/03-troubleshooting.md
⏳ docs/deployment/04-rollback.md
```

---

### ⏳ 階段 8: 密鑰列表和輔助腳本 (待執行)

```
⏳ docs/deployment/key-vault-secrets-list.md
⏳ docs/deployment/managed-identity-setup.md
⏳ scripts/deployment/pre-deploy-check.js
⏳ scripts/deployment/migrate-to-blob.js
⏳ scripts/deployment/validate-env.js
⏳ scripts/azure/create-service-principal.sh
⏳ scripts/azure/rotate-secrets.sh
```

---

## 🔄 補充階段

### ⏳ 階段 9: 測試和驗證工具 (新增)

```
⏳ scripts/test-docker-build.sh
⏳ scripts/local-azure-test.sh
⏳ docker/docker-compose.azure.yml
```

---

### ⏳ 階段 10: Terraform IaC (可選)

```
⏳ .azure/terraform/main.tf
⏳ .azure/terraform/variables.tf
⏳ .azure/terraform/outputs.tf
⏳ .azure/terraform/README.md
```

---

## 📊 按優先級排序

### 🔴 關鍵優先級 (部署阻斷)

```
⏳ apps/web/src/lib/azure-storage.ts
⏳ apps/web/src/app/api/upload/quote/route.ts
⏳ apps/web/src/app/api/upload/invoice/route.ts
⏳ apps/web/src/app/api/upload/proposal/route.ts
```

---

### 🟡 高優先級 (首次部署必需)

```
⏳ .azure/scripts/01-setup-resources.sh
⏳ .azure/scripts/02-setup-database.sh
⏳ .azure/scripts/03-setup-storage.sh
⏳ .azure/scripts/04-setup-acr.sh
⏳ .azure/scripts/05-setup-appservice.sh
⏳ .azure/scripts/06-deploy-app.sh
⏳ docs/deployment/key-vault-secrets-list.md
⏳ docs/deployment/00-prerequisites.md
⏳ docs/deployment/01-first-time-setup.md
```

---

### 🟢 中優先級 (自動化部署)

```
⏳ .github/workflows/azure-deploy-dev.yml
⏳ .github/workflows/azure-deploy-staging.yml
⏳ .github/workflows/azure-deploy-prod.yml
⏳ docs/deployment/02-ci-cd-setup.md
```

---

### ⚪ 低優先級 (輔助工具)

```
⏳ claudedocs/6-ai-assistant/prompts/SITUATION-6-AZURE-DEPLOY.md
⏳ claudedocs/6-ai-assistant/prompts/SITUATION-7-AZURE-TROUBLESHOOT.md
⏳ docs/deployment/03-troubleshooting.md
⏳ docs/deployment/04-rollback.md
⏳ docs/deployment/managed-identity-setup.md
⏳ scripts/deployment/pre-deploy-check.js
⏳ scripts/deployment/migrate-to-blob.js
⏳ scripts/deployment/validate-env.js
⏳ scripts/azure/create-service-principal.sh
⏳ scripts/azure/rotate-secrets.sh
⏳ scripts/test-docker-build.sh
⏳ scripts/local-azure-test.sh
⏳ docker/Dockerfile.dev
⏳ docker/docker-compose.azure.yml
```

---

### ⚫ 可選 (進階功能)

```
⏳ .azure/terraform/main.tf
⏳ .azure/terraform/variables.tf
⏳ .azure/terraform/outputs.tf
⏳ .azure/terraform/README.md
```

---

## 🎯 建議執行順序

### 第一批 (立即執行 - 解決阻斷)
1. 階段 3: Blob Storage 實作 (4 個文件)

### 第二批 (準備部署 - 基礎設施)
2. 階段 5: Azure 資源腳本 (6 個腳本)
3. 階段 8: 密鑰列表 (2 個文檔)
4. 階段 7: 部署文檔 - 前置需求和首次設置 (2 個文檔)

### 第三批 (自動化)
5. 階段 6: CI/CD Pipeline (3 個 workflows)
6. 階段 7: 部署文檔 - CI/CD 和故障排查 (3 個文檔)

### 第四批 (輔助工具)
7. 階段 4: AI 助手 Prompts (2 個 prompts)
8. 階段 8: 輔助腳本 (5 個腳本)
9. 階段 9: 測試工具 (3 個文件)

### 第五批 (可選)
10. 階段 10: Terraform (4 個文件)

---

**最後更新**: 2025-11-20
