# Azure 部署記錄

## 部署歷史

### 2025-11-21: v2-register 部署（用戶註冊功能）

**部署時間**: 2025-11-21 16:20 (UTC+8)
**執行者**: 開發團隊
**Git Commit**: `696efa6` (chore: 更新 Azure 部署相關配置文件)

#### 部署內容

**新功能**:
1. 用戶註冊系統完整實現
   - POST `/api/auth/register` API endpoint
   - bcrypt 密碼加密（10 輪 salt）
   - Zod 輸入驗證（姓名、Email、密碼）
   - 重複 Email 檢查
   - 預設角色 ID = 1 (ProjectManager)

2. 註冊頁面 (`/zh-TW/register`)
   - 表單驗證（密碼匹配、長度檢查）
   - 註冊成功狀態頁面
   - 自動跳轉到登入頁面

3. 登入頁面 i18n 路由修復
   - 使用 `<Link>` 組件替代 `<a>` 標籤
   - 修復語言前綴丟失問題

**技術更新**:
- 添加 `bcrypt` 和 `@types/bcrypt` 依賴到 `apps/web/package.json`
- 新增翻譯鍵到 `zh-TW.json` 和 `en.json`

#### 部署流程

```bash
# 1. 登入 Azure
az account show
# ✅ 已登入: laikwokho321@yahoo.com.hk

# 2. 登入 Azure Container Registry
az acr login --name acritpmdev
# ✅ Login Succeeded

# 3. 構建 Docker 映像
docker build -t acritpmdev.azurecr.io/itpm-web:v2-register -f docker/Dockerfile .
# ✅ 構建成功
# Digest: sha256:5eb0e9ae92d1549c9801ea6d9d816c84ce0b7abce519947b99cc9705514194d6

# 4. 推送映像到 ACR
docker push acritpmdev.azurecr.io/itpm-web:v2-register
# ✅ 推送成功
# 部分層級已存在（Layer already exists），提升推送速度

# 5. 更新 App Service 容器配置
az webapp config container set \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --docker-custom-image-name acritpmdev.azurecr.io/itpm-web:v2-register \
  --docker-registry-server-url https://acritpmdev.azurecr.io
# ✅ 配置已更新

# 6. 重啟 App Service
az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev
# ✅ 重啟完成
```

#### 驗證結果

**✅ 部署成功指標**:
1. 網站可訪問: https://app-itpm-dev-001.azurewebsites.net
2. HTTP 響應正常: `HTTP/1.1 307 Temporary Redirect`（Next.js 預期行為）
3. 註冊頁面可訪問: `/zh-TW/register`
4. 頁面標題正確: `IT Project Management Platform`
5. Docker 映像已推送到 ACR: `v2-register` 標籤

**⚠️ 已知問題**:
1. 註冊 API endpoint 出現 500 錯誤
   - 測試請求: `POST /api/auth/register`
   - 錯誤響應: `500 Internal Server Error`
   - **可能原因**: bcrypt 原生模組在 Azure Linux 環境下的編譯/運行問題
   - **影響範圍**: 僅影響用戶註冊功能，不影響現有登入和其他功能
   - **待修復**: 需要調查 Docker 映像中 bcrypt 的編譯配置

#### 部署產物

**Docker 映像信息**:
- **Registry**: acritpmdev.azurecr.io
- **Repository**: itpm-web
- **Tag**: v2-register
- **Digest**: sha256:5eb0e9ae92d1549c9801ea6d9d816c84ce0b7abce519947b99cc9705514194d6
- **Size**: ~856 layers (部分層級復用)

**Azure 資源狀態**:
- **Resource Group**: rg-itpm-dev
- **App Service**: app-itpm-dev-001
- **Container Registry**: acritpmdev
- **Database**: psql-itpm-dev-001 (PostgreSQL 16)
- **Runtime**: Node.js 20 (Alpine Linux)

#### 回滾計劃

如需回滾到前一版本：

```bash
# 1. 查看之前的映像版本
az acr repository show-tags \
  --name acritpmdev \
  --repository itpm-web \
  --orderby time_desc

# 2. 回滾到前一版本（例如: v1-stable）
az webapp config container set \
  --name app-itpm-dev-001 \
  --resource-group rg-itpm-dev \
  --docker-custom-image-name acritpmdev.azurecr.io/itpm-web:v1-stable \
  --docker-registry-server-url https://acritpmdev.azurecr.io

# 3. 重啟 App Service
az webapp restart --name app-itpm-dev-001 --resource-group rg-itpm-dev
```

#### 後續行動

**優先級 1 - 修復 bcrypt 問題**:
1. ✅ 已記錄到部署日誌 (2025-11-21 16:45)
2. 待調查 Azure App Service 日誌查看詳細錯誤
3. 待檢查 Docker 映像中 bcrypt 的編譯狀態
4. 待考慮替代方案：
   - 選項 A: 使用預編譯的 bcrypt 二進制文件
   - 選項 B: 切換到純 JavaScript 實現（如 bcryptjs）
   - 選項 C: 在 Dockerfile 中添加 build 步驟確保正確編譯

**優先級 2 - 完整測試**:
1. 修復後進行完整的註冊流程測試
2. 驗證數據庫記錄創建
3. 測試登入功能與註冊的整合

**優先級 3 - 文檔更新**:
1. 更新 `DEVELOPMENT-LOG.md` 記錄本次部署
2. 更新 `claudedocs/3-progress/weekly/2025-W47.md`

#### 相關文件

**本地 Git Commits**:
- `696efa6` - chore: 更新 Azure 部署相關配置文件
- `5221697` - docs(azure): 添加完整的 Azure 部署文檔和 CI/CD 配置
- `8bda808` - feat(auth): 完成用戶註冊系統實現 - bcrypt 密碼加密與完整驗證

**GitHub Repository**:
- https://github.com/laitim2001/ai-it-project-process-management-webapp/

**Azure Portal**:
- App Service: https://portal.azure.com/#resource/subscriptions/b80ddd64-97af-4aff-b34e-799dbf7f697c/resourceGroups/rg-itpm-dev/providers/Microsoft.Web/sites/app-itpm-dev-001
- Container Registry: https://portal.azure.com/#resource/subscriptions/b80ddd64-97af-4aff-b34e-799dbf7f697c/resourceGroups/rg-itpm-dev/providers/Microsoft.ContainerRegistry/registries/acritpmdev

---

## 部署記錄模板

### YYYY-MM-DD: [版本標籤] 部署（[功能描述]）

**部署時間**: YYYY-MM-DD HH:mm (UTC+8)
**執行者**: [姓名/團隊]
**Git Commit**: `[commit-hash]` ([commit message])

#### 部署內容
[描述新功能、bug 修復、技術更新等]

#### 部署流程
```bash
[記錄執行的命令]
```

#### 驗證結果
[記錄驗證步驟和結果]

#### 部署產物
[記錄 Docker 映像信息、Azure 資源狀態等]

#### 回滾計劃
[如何回滾到前一版本的步驟]

#### 後續行動
[需要跟進的事項]

#### 相關文件
[相關文檔和連結]

---

*Last Updated: 2025-11-21*
