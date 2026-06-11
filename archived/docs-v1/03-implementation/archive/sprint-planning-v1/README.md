# Sprint Planning 文檔導覽

> 📂 本目錄包含 Sprint 0-5 的詳細規劃文檔

## 📄 文檔分類

### 🏗️ 開發階段文檔 (Phase 1: Sprint 0-3) - **當前使用**

| 文檔 | 用途 | 狀態 |
|------|------|------|
| **[sprint-0-local-development.md](./sprint-0-local-development.md)** | 本地開發環境搭建 (Docker Compose) | ✅ 使用中 |
| **sprint-1-core-services.md** | 核心服務實現 (本地版) | 📝 需更新 |
| **sprint-2-integrations.md** | 第三方集成 (本地版) | 📝 需更新 |
| **sprint-3-security-observability.md** | 安全與監控 (本地版) | 📝 需更新 |

### ☁️ 雲端部署文檔 (Phase 2: Sprint 4+) - 未來使用

| 文檔 | 用途 | 狀態 |
|------|------|------|
| **[sprint-0-mvp-revised.md](./sprint-0-mvp-revised.md)** | MVP 基礎設施 (Azure 雲端版) | ⏳ 保留備用 |
| **sprint-4-ui-frontend.md** | 前端實現 + 雲端集成 | 📌 Phase 2 使用 |
| **sprint-5-testing-launch.md** | 測試與部署 (Azure) | 📌 Phase 2 使用 |

### 📋 其他規劃文檔

| 文檔 | 用途 | 狀態 |
|------|------|------|
| **sprint-planning-overview.md** | Sprint 總覽與時間表 | ✅ 完成 |
| **mvp-implementation-plan.md** | MVP 範圍定義 | ✅ 完成 |

---

## 🎯 當前開發策略: Local-First

### Phase 1: Sprint 0-3 (本地開發) - **2025-11-25 開始**
**成本**: $0 Azure 費用  
**工具棧**:
- **容器編排**: Docker Compose
- **數據庫**: PostgreSQL 16 (本地容器)
- **緩存**: Redis 7 (本地容器)
- **消息隊列**: RabbitMQ 3.12 (本地容器)
- **認證**: Mock Authentication
- **日誌**: Console Logging

**使用文檔**: `sprint-0-local-development.md`

### Phase 2: Sprint 4+ (雲端集成) - **2026-01-13 開始**
**成本**: ~$123-143/月  
**工具棧**:
- **部署**: Azure App Service
- **數據庫**: Azure PostgreSQL
- **緩存**: Azure Redis Cache
- **消息隊列**: Azure Service Bus
- **認證**: Azure AD OAuth 2.0
- **監控**: Application Insights

**使用文檔**: `sprint-0-mvp-revised.md`, `sprint-4-ui-frontend.md`, `sprint-5-testing-launch.md`

---

## 🚀 快速開始

### 當前 Sprint 0 (本地開發)
```bash
# 1. 閱讀本地開發指南
cat docs/03-implementation/local-development-guide.md

# 2. 配置環境變量
cp .env.example .env

# 3. 啟動 Docker Compose
docker-compose up -d

# 4. 驗證服務
curl http://localhost:8000/health

# 5. 查看 Swagger API 文檔
open http://localhost:8000/docs
```

### 未來 Sprint 4+ (雲端部署)
```bash
# 1. 閱讀雲端部署指南
cat docs/03-implementation/azure-service-principal-setup.md

# 2. 更新環境變量 (切換到 Azure)
# 修改 .env:
MESSAGE_QUEUE_TYPE=azure_service_bus
AUTH_MODE=azure_ad
LOGGING_MODE=application_insights

# 3. 部署到 Azure
az webapp up --name ipa-platform-api --resource-group ipa-platform-rg
```

---

## 📊 文檔更新狀態

| 文檔 | 本地開發適配 | 雲端部署適配 | 更新日期 |
|------|-------------|-------------|---------|
| sprint-0-local-development.md | ✅ 完成 | N/A | 2025-11-20 |
| sprint-0-mvp-revised.md | ⚠️ 部分 | ✅ 完成 | 2025-11-20 |
| sprint-1-core-services.md | ❌ 待更新 | ✅ 完成 | 2025-11-15 |
| sprint-2-integrations.md | ❌ 待更新 | ✅ 完成 | 2025-11-15 |
| sprint-3-security-observability.md | ❌ 待更新 | ✅ 完成 | 2025-11-15 |
| sprint-4-ui-frontend.md | N/A | ✅ 完成 | 2025-11-15 |
| sprint-5-testing-launch.md | N/A | ✅ 完成 | 2025-11-15 |

---

## 🔄 切換環境

### 從本地切換到 Azure
只需更新 `.env` 環境變量，無需修改代碼:

```bash
# 本地開發 → Azure 生產
sed -i 's/MESSAGE_QUEUE_TYPE=rabbitmq/MESSAGE_QUEUE_TYPE=azure_service_bus/' .env
sed -i 's/AUTH_MODE=mock/AUTH_MODE=azure_ad/' .env
sed -i 's/LOGGING_MODE=console/LOGGING_MODE=application_insights/' .env
```

### 從 Azure 切換回本地
```bash
# Azure 生產 → 本地開發
sed -i 's/MESSAGE_QUEUE_TYPE=azure_service_bus/MESSAGE_QUEUE_TYPE=rabbitmq/' .env
sed -i 's/AUTH_MODE=azure_ad/AUTH_MODE=mock/' .env
sed -i 's/LOGGING_MODE=application_insights/LOGGING_MODE=console/' .env
```

---

## 📞 聯絡

- **技術問題**: 查看 [CONTRIBUTING.md](../../../CONTRIBUTING.md)
- **架構諮詢**: 查看 [technical-architecture.md](../../02-technical-design/technical-architecture.md)
- **本地開發**: 查看 [local-development-guide.md](../local-development-guide.md)

---

**最後更新**: 2025-11-20  
**更新人**: GitHub Copilot  
**版本**: 2.0 (Local-First Strategy)
