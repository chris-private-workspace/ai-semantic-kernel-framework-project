# 📦 Azurite 本地開發環境實施計劃

**創建日期**: 2025-11-20
**狀態**: 🚀 執行中
**優先級**: 🔴 Critical (解除部署阻斷 RISK-001)
**方法論**: SITUATION-2-FEATURE-DEV-PREP

---

## 📋 需求分析

### 功能描述
在本地開發環境中配置 Azurite 模擬器，作為 Azure Blob Storage 的本地替代方案，確保開發環境與 UAT/生產環境的代碼一致性。

### 用戶故事
**作為**開發者
**我希望**在本地開發時使用 Azurite 模擬 Azure Blob Storage
**以便**確保開發環境與生產環境代碼完全一致，避免環境差異導致的 Bug

### 驗收標準
- [x] `azure-storage.ts` 已實現環境自動檢測邏輯
- [ ] docker-compose.yml 包含 Azurite 服務配置
- [ ] .env.example 包含 Azurite 配置說明
- [ ] DEVELOPMENT-SETUP.md 包含 Azurite 設置指引
- [ ] 本地可成功啟動 Azurite 並上傳文件
- [ ] 文件上傳測試通過（Quote, Invoice, Proposal）
- [ ] 測試工具腳本可驗證 Blob Storage 功能

---

## 🏗️ 架構評估

### 數據模型
✅ **無需修改** - Blob Storage 遷移已完成，數據模型支持 Blob URL 存儲

**相關 Prisma Models**:
```prisma
model Quote {
  filePath  String?  // Azure Blob URL: https://storage.blob.core.windows.net/quotes/...
}

model Expense {
  invoiceFilePath String?  // Azure Blob URL
}

model BudgetProposal {
  filePath String?  // Azure Blob URL
}
```

### API
✅ **已完成遷移** - 所有上傳 API 已使用 azure-storage.ts

**已遷移的 API Routes**:
- `apps/web/src/app/api/upload/quote/route.ts` - 報價單上傳
- `apps/web/src/app/api/upload/invoice/route.ts` - 發票上傳
- `apps/web/src/app/api/upload/proposal/route.ts` - 提案文件上傳

### 前端組件
✅ **可直接使用** - 前端無需修改

前端組件調用 API 上傳文件，API 返回 Blob URL，前端將 URL 存儲到數據庫。無論使用 Azurite 還是 Azure Blob Storage，URL 格式一致。

### 服務層
✅ **已完成實現** - `apps/web/src/lib/azure-storage.ts` (~450 lines)

**環境自動檢測邏輯**:
```typescript
function getAzureStorageConfig(): AzureStorageConfig {
  const useDevelopmentStorage =
    process.env.AZURE_STORAGE_USE_DEVELOPMENT === "true" ||
    process.env.NODE_ENV === "development";

  if (useDevelopmentStorage) {
    return {
      accountName: "devstoreaccount1",
      connectionString: "UseDevelopmentStorage=true",
      useDevelopmentStorage: true,
    };
  }

  return {
    accountName: process.env.AZURE_STORAGE_ACCOUNT_NAME!,
    useDevelopmentStorage: false,
  };
}
```

**關鍵特性**:
- ✅ 環境自動檢測（本地 Azurite vs 生產 Azure Blob）
- ✅ Managed Identity 支持（生產環境）
- ✅ 完整錯誤處理和日誌記錄
- ✅ Container 自動創建
- ✅ 上傳、下載、刪除、SAS Token 生成

---

## 📝 文件變更清單

### Docker 配置
- [ ] **docker-compose.yml** - 添加 Azurite 服務定義
  - 描述：添加 Azurite 容器配置，映射端口 10000-10002
  - 預估工作量：20 分鐘

### 環境變數配置
- [ ] **.env.example** - 添加 Azurite 配置說明
  - 描述：添加 AZURE_STORAGE_USE_DEVELOPMENT 環境變數說明
  - 預估工作量：15 分鐘

### 文檔更新
- [ ] **DEVELOPMENT-SETUP.md** - 添加 Azurite 設置步驟
  - 描述：在「系統環境準備」章節添加 Azurite 設置指引
  - 預估工作量：30 分鐘

### 測試工具
- [ ] **scripts/test-blob-storage.js** - Blob Storage 功能測試腳本
  - 描述：驗證上傳、下載、列表、刪除功能
  - 預估工作量：45 分鐘

---

## 🛠️ 實施計劃

### 階段 3.4.1: 添加 Azurite 到 docker-compose.yml (20 分鐘)

**目標**：在 Docker Compose 中添加 Azurite 服務

**變更內容**：
```yaml
# 添加到 docker-compose.yml
azurite:
  image: mcr.microsoft.com/azure-storage/azurite
  container_name: itpm-azurite-dev
  restart: unless-stopped
  ports:
    - "10000:10000"  # Blob service
    - "10001:10001"  # Queue service
    - "10002:10002"  # Table service
  volumes:
    - azurite_data:/data
  command: azurite --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0 --loose
  healthcheck:
    test: nc 127.0.0.1 10000 -z
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - itpm-network

volumes:
  azurite_data:
    driver: local
```

**驗證**：
```bash
docker-compose up -d azurite
docker-compose ps azurite
```

---

### 階段 3.4.2: 更新 .env.example 配置說明 (15 分鐘)

**目標**：添加 Azurite 環境變數說明

**變更內容**：
```bash
# 添加到 .env.example 的 Azure Blob Storage 區塊

# ------------------------------------------------------------------------------
# Azure Blob Storage (檔案上傳: 報價單、發票、提案)
# ------------------------------------------------------------------------------

# 🏠 本地開發環境 (Azurite 模擬器) - 推薦
# 使用 Azurite 確保開發環境與生產環境代碼一致性
AZURE_STORAGE_USE_DEVELOPMENT=true

# 當 AZURE_STORAGE_USE_DEVELOPMENT=true 時，會自動使用以下配置：
# - Connection String: UseDevelopmentStorage=true
# - Account Name: devstoreaccount1 (Azurite 預設)
# - Endpoint: http://127.0.0.1:10000 (本地 Azurite Blob 服務)

# ☁️ Azure 生產環境 (需設置以下變數)
# AZURE_STORAGE_USE_DEVELOPMENT=false
# AZURE_STORAGE_ACCOUNT_NAME="yourstorageaccountname"
# AZURE_STORAGE_ACCOUNT_KEY="your-storage-account-key"  # 僅用於 SAS Token 生成

# 📝 重要提示：
# 1. 本地開發建議使用 Azurite (AZURE_STORAGE_USE_DEVELOPMENT=true)
# 2. 生產環境使用 Managed Identity，無需 AZURE_STORAGE_ACCOUNT_KEY
# 3. Azurite 需先啟動：docker-compose up -d azurite

# Blob Storage Containers (開發和生產環境相同)
AZURE_STORAGE_CONTAINER_QUOTES="quotes"
AZURE_STORAGE_CONTAINER_INVOICES="invoices"
AZURE_STORAGE_CONTAINER_PROPOSALS="proposals"
```

---

### 階段 3.4.3: 更新 DEVELOPMENT-SETUP.md 文檔 (30 分鐘)

**目標**：添加 Azurite 設置指引到開發文檔

**變更位置**：
1. 在「必需軟件」表格添加 Azurite 說明
2. 在「步驟 3: 啟動 Docker 服務」章節添加 Azurite 驗證
3. 在「常見問題排查」添加 Azurite 相關問題

**新增內容**：

**Section 1: 必需軟件更新**
```markdown
| 軟件 | 版本要求 | 用途 | 下載連結 |
|------|----------|------|----------|
| **Docker Desktop** | 最新穩定版 | 容器化服務（PostgreSQL, Redis, MailHog, **Azurite**） | [docker.com](https://www.docker.com/products/docker-desktop) |
```

**Section 2: Docker 服務啟動驗證**
```markdown
### 步驟 3: 啟動 Docker 服務

```bash
# 啟動所有服務（PostgreSQL, Redis, Mailhog, Azurite）
docker-compose up -d

# 驗證服務狀態
docker-compose ps

# 預期輸出：
# NAME                  STATUS         PORTS
# itpm-postgres-dev     Up (healthy)   0.0.0.0:5434->5432/tcp
# itpm-redis-dev        Up (healthy)   0.0.0.0:6381->6379/tcp
# itpm-mailhog          Up             0.0.0.0:1025->1025/tcp, 0.0.0.0:8025->8025/tcp
# itpm-azurite-dev      Up (healthy)   0.0.0.0:10000-10002->10000-10002/tcp
```

**驗證 Azurite 連接**:
```bash
# 使用 curl 測試 Blob Service
curl http://127.0.0.1:10000/devstoreaccount1?comp=list

# 預期回應: XML 格式的 Container 列表（初始為空）
```
```

**Section 3: 常見問題排查**
```markdown
### Azurite 相關問題

#### 問題: Azurite 容器無法啟動
**錯誤訊息**: `Error starting userland proxy: listen tcp4 0.0.0.0:10000: bind: address already in use`

**解決方案**:
```bash
# 檢查端口佔用
# Windows
netstat -ano | findstr :10000

# macOS/Linux
lsof -i :10000

# 停止佔用端口的進程或修改 docker-compose.yml 中的端口映射
```

#### 問題: 文件上傳失敗，提示連接錯誤
**錯誤訊息**: `Error: connect ECONNREFUSED 127.0.0.1:10000`

**解決方案**:
1. 確認 Azurite 容器正在運行：`docker-compose ps azurite`
2. 確認環境變數設置：`.env` 中 `AZURE_STORAGE_USE_DEVELOPMENT=true`
3. 重啟 Next.js 開發伺服器：`pnpm dev`

#### 問題: 上傳成功但無法下載文件
**原因**: Container 不存在

**解決方案**:
Azurite 會自動創建 Container，但如果遇到問題可手動創建：
```bash
# 使用 Azure Storage Explorer 連接到 Azurite
# Connection String: UseDevelopmentStorage=true
# 手動創建 containers: quotes, invoices, proposals
```

或使用測試腳本自動創建：
```bash
node scripts/test-blob-storage.js
```
```

---

### 階段 3.4.4: 本地測試 - 啟動 Azurite 並驗證文件上傳 (30 分鐘)

**目標**：驗證 Azurite 整合功能正常

**測試步驟**：
1. 啟動 Azurite 容器
2. 確認環境變數配置
3. 啟動 Next.js 開發伺服器
4. 測試 3 個上傳 API

**執行命令**：
```bash
# 1. 啟動 Azurite
docker-compose up -d azurite
docker-compose ps azurite

# 2. 檢查環境變數
cat .env | grep AZURE_STORAGE

# 3. 啟動 Next.js
pnpm dev

# 4. 測試文件上傳
# - 登入系統
# - 創建報價單並上傳文件
# - 創建費用記錄並上傳發票
# - 創建預算提案並上傳計劃書
```

**驗證清單**：
- [ ] Azurite 容器成功啟動 (docker-compose ps)
- [ ] 環境變數 AZURE_STORAGE_USE_DEVELOPMENT=true
- [ ] 報價單文件上傳成功
- [ ] 發票文件上傳成功
- [ ] 提案文件上傳成功
- [ ] 數據庫 filePath 欄位包含正確的 Blob URL
- [ ] 可以從瀏覽器訪問上傳的文件

---

### 階段 3.4.5: 創建測試工具腳本 (45 分鐘)

**目標**：提供自動化測試腳本驗證 Blob Storage 功能

**文件**: `scripts/test-blob-storage.js`

**功能**：
- 測試連接 Azurite / Azure Blob Storage
- 測試 Container 創建
- 測試文件上傳（各種格式）
- 測試文件下載
- 測試文件列表
- 測試文件刪除
- 測試錯誤處理

**使用方式**：
```bash
# 測試本地 Azurite
AZURE_STORAGE_USE_DEVELOPMENT=true node scripts/test-blob-storage.js

# 測試生產 Azure Blob Storage
AZURE_STORAGE_USE_DEVELOPMENT=false node scripts/test-blob-storage.js
```

**預期輸出**：
```
[Blob Storage Test] 開始測試...
[Blob Storage Test] 環境: Development (Azurite)
[Blob Storage Test] ✅ 連接成功
[Blob Storage Test] ✅ Container 'quotes' 創建成功
[Blob Storage Test] ✅ 文件上傳成功: test-quote.pdf (1.2 KB)
[Blob Storage Test] ✅ 文件下載成功: test-quote.pdf
[Blob Storage Test] ✅ 文件列表成功: 1 個文件
[Blob Storage Test] ✅ 文件刪除成功: test-quote.pdf
[Blob Storage Test] 所有測試通過！
```

---

## ⏱️ 工作量估算

| 階段 | 任務 | 預估時間 | 優先級 |
|------|------|----------|--------|
| 3.4.1 | 添加 Azurite 到 docker-compose.yml | 20 分鐘 | 🔴 Critical |
| 3.4.2 | 更新 .env.example 配置說明 | 15 分鐘 | 🟡 High |
| 3.4.3 | 更新 DEVELOPMENT-SETUP.md 文檔 | 30 分鐘 | 🟡 High |
| 3.4.4 | 本地測試 - 啟動 Azurite 並驗證 | 30 分鐘 | 🔴 Critical |
| 3.4.5 | 創建測試工具腳本 | 45 分鐘 | 🟢 Medium |

**總計**: 2 小時 20 分鐘

---

## ⚠️ 風險評估

### RISK-3.4.1: Azurite 與 Azure Blob Storage 行為差異
**描述**: Azurite 是模擬器，可能無法 100% 模擬所有 Azure Blob Storage 功能

**影響**: 🟡 Medium - 某些高級功能可能在本地無法測試

**緩解策略**:
- 定期在 Azure 測試環境驗證關鍵功能
- 使用 Azurite 的 `--loose` 模式提高兼容性
- 文檔中明確標註 Azurite 不支持的功能（如 Managed Identity）

**狀態**: 🟢 可接受風險

---

### RISK-3.4.2: 開發者學習成本
**描述**: 開發者需要學習 Azure Storage 概念和 Azurite 使用

**影響**: 🟢 Low - 一次性學習成本

**緩解策略**:
- 提供完整的 DEVELOPMENT-SETUP.md 文檔
- 提供測試腳本和範例代碼
- 團隊內部知識分享和培訓

**狀態**: ✅ 已緩解

---

### RISK-3.4.3: 額外的資源消耗
**描述**: Azurite 容器增加本地開發環境的資源消耗

**影響**: 🟢 Low - Azurite 容器輕量級（<100MB 內存）

**緩解策略**:
- Azurite 容器可以按需啟動/停止
- 提供 docker-compose 配置選項（可選服務）

**狀態**: ✅ 已緩解

---

## 📊 成功指標

### 技術指標
- [x] azure-storage.ts 支持環境自動檢測
- [ ] Azurite 容器成功啟動且健康檢查通過
- [ ] 所有文件上傳 API 在 Azurite 環境下測試通過
- [ ] 測試腳本全部通過（上傳、下載、列表、刪除）
- [ ] 文檔完整且清晰

### 開發體驗指標
- [ ] 開發者可在 10 分鐘內設置完成 Azurite
- [ ] 文檔清晰易懂，無需額外詢問
- [ ] 測試腳本可自動驗證環境配置

---

## 📚 相關文檔

- [Azure Blob Storage 實施總結](./00-summary.md#階段-3-blob-storage-實作)
- [架構決策 ADR-004](./03-architecture-decisions.md#adr-004-azure-blob-storage-for-文件存儲)
- [風險評估 RISK-001](./04-risk-assessment.md#risk-001-文件存儲使用本地文件系統)
- [完整 TODO 列表](./02-complete-todo-list.md#階段-3-blob-storage-實作)

---

## 🔄 下一步行動

完成本階段後，將進入：
- **階段 2.2**: docker/ 輔助文件創建
- **階段 4**: AI 助手 Prompts 創建
- **階段 5**: Azure 資源配置腳本

---

**維護者**: AI Assistant (Claude Code)
**審核者**: Tech Lead
**最後更新**: 2025-11-20
**下次審查**: 階段 3.4 完成後
