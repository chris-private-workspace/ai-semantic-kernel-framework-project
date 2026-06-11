# Sprint 122 Checklist: Azure 部署 + 可觀測性

## 開發任務

### Story 122-1: Azure App Service 部署
- [ ] Azure 資源建立
  - [ ] Resource Group: `rg-ipa-platform`
  - [ ] App Service Plan (B2): `asp-ipa-backend`
  - [ ] Web App (Backend): `app-ipa-backend`
  - [ ] App Service Plan (B1): `asp-ipa-frontend`
  - [ ] Web App (Frontend): `app-ipa-frontend`
  - [ ] Azure Container Registry: `acripa`
  - [ ] Application Insights: `appi-ipa`
- [ ] Azure Database for PostgreSQL 配置
  - [ ] 建立 Flexible Server (B1ms tier)
  - [ ] 建立 database: `ipa_platform`
  - [ ] 配置 firewall rules（允許 App Service）
  - [ ] 驗證連線正常
- [ ] Azure Cache for Redis 配置
  - [ ] 建立 Basic C0 instance
  - [ ] 配置 access key
  - [ ] 驗證連線正常
- [ ] Backend App Service 配置
  - [ ] Container source 指向 ACR
  - [ ] 配置環境變量（DB_HOST, DB_NAME, REDIS_HOST 等）
  - [ ] 啟用 System-assigned Managed Identity
  - [ ] 啟用 Always On
  - [ ] 啟用 HTTPS Only
  - [ ] 配置 CORS（僅允許 frontend URL）
  - [ ] 配置 health check path: `/health`
  - [ ] 部署 backend Docker image
  - [ ] 驗證 health check 通過
  - [ ] 驗證 API 端點可訪問
- [ ] Frontend App Service 配置
  - [ ] Container source 指向 ACR
  - [ ] 啟用 HTTPS Only
  - [ ] 部署 frontend Docker image
  - [ ] 驗證 SPA 可訪問
  - [ ] 驗證前端可呼叫後端 API
- [ ] CI/CD 更新
  - [ ] 更新 deploy workflow 指向 Azure resources
  - [ ] 配置 ACR push credentials (GitHub Secrets)
  - [ ] 配置 Azure deploy credentials
  - [ ] 測試自動部署流程
- [ ] 基本功能驗證
  - [ ] API health check
  - [ ] 用戶登入流程
  - [ ] Agent 對話基本流程
  - [ ] 前端頁面載入正常

### Story 122-2: OpenTelemetry + Azure Monitor 整合
- [ ] 建立 observability 模組 (`backend/src/core/observability/`)
  - [ ] `__init__.py`
  - [ ] `setup.py` — OTel 初始化
  - [ ] `spans.py` — 自定義 span helpers
  - [ ] `metrics.py` — 自定義 metrics
- [ ] OpenTelemetry SDK 初始化
  - [ ] TracerProvider 配置
  - [ ] MeterProvider 配置
  - [ ] LoggerProvider 配置
  - [ ] AzureMonitorTraceExporter
  - [ ] AzureMonitorMetricExporter
  - [ ] Connection string 從環境變量讀取
- [ ] Auto-Instrumentation 配置
  - [ ] FastAPI instrumentation（HTTP 請求追蹤）
  - [ ] httpx / aiohttp instrumentation（外部 HTTP 呼叫）
  - [ ] Redis instrumentation（快取操作）
  - [ ] psycopg2 / asyncpg instrumentation（資料庫操作）
- [ ] Custom Instrumentation
  - [ ] Agent execution span（start/end/error）
  - [ ] LLM call span（model, tokens, duration）
  - [ ] MCP tool call span（tool name, duration, result）
  - [ ] Orchestration span（routing decision, mode）
- [ ] Custom Metrics
  - [ ] `agent.execution.duration` (Histogram)
  - [ ] `agent.execution.count` (Counter)
  - [ ] `llm.call.duration` (Histogram)
  - [ ] `llm.tokens.used` (Counter)
  - [ ] `mcp.tool.call.duration` (Histogram)
  - [ ] `api.request.error_rate` (Counter)
- [ ] 在 FastAPI startup 中初始化 OTel
- [ ] Application Insights 驗證
  - [ ] Traces 可見
  - [ ] Metrics 可見
  - [ ] Application Map 顯示服務依賴
  - [ ] 端到端 transaction 可追蹤
- [ ] 性能測試
  - [ ] OTel overhead < 5%（benchmark 測試）

### Story 122-3: 結構化日誌 + Request ID 追蹤
- [ ] 建立 logging 模組 (`backend/src/core/logging/`)
  - [ ] `__init__.py`
  - [ ] `setup.py` — structlog 配置
  - [ ] `middleware.py` — RequestIdMiddleware
  - [ ] `filters.py` — 敏感資訊過濾器
- [ ] RequestIdMiddleware 實現
  - [ ] 從 X-Request-ID header 讀取（或自動生成 UUID）
  - [ ] 注入 ContextVar
  - [ ] 在 response header 中返回 X-Request-ID
- [ ] structlog 配置
  - [ ] JSON 格式輸出
  - [ ] 自動包含 timestamp、level、logger
  - [ ] 自動包含 request_id（from ContextVar）
  - [ ] 自動包含 OTel trace_id / span_id
  - [ ] 敏感資訊過濾器（密碼、token、API key）
- [ ] 替換現有日誌呼叫
  - [ ] 掃描並替換 `print()` 語句
  - [ ] 掃描並替換 `logging.info/warning/error()` 語句
  - [ ] 確認無 `console.log` 等遺漏（前端不在此範圍）
- [ ] 在 FastAPI startup 中初始化 logging
- [ ] 驗證
  - [ ] API 請求日誌為 JSON 格式
  - [ ] 日誌包含 request_id
  - [ ] 跨服務可透過 request_id 追蹤
  - [ ] 敏感資訊未出現在日誌中

## 品質檢查

### 代碼品質
- [ ] 類型提示完整
- [ ] Docstrings 完整
- [ ] 遵循專案代碼風格
- [ ] 無 hardcoded Azure connection strings
- [ ] 所有敏感配置使用環境變量或 Key Vault

### 測試
- [ ] OTel setup 單元測試
- [ ] RequestIdMiddleware 單元測試
- [ ] structlog 配置測試
- [ ] 敏感資訊過濾器測試
- [ ] Azure 部署後功能驗證

### 安全
- [ ] 所有 Azure 密鑰使用 Key Vault 或 App Settings（非明文）
- [ ] Managed Identity 取代密碼認證（Azure 資源間）
- [ ] Application Insights connection string 不在代碼中
- [ ] 日誌中無敏感資訊洩漏

## 驗收標準

- [ ] Backend + Frontend 在 Azure App Service 上正常運行
- [ ] Application Insights 中可見 traces、metrics、logs
- [ ] API 請求帶有 X-Request-ID 全鏈路追蹤
- [ ] 所有日誌為 JSON 結構化格式
- [ ] CI/CD 可自動部署到 Azure
- [ ] 基本業務功能在雲端環境正常運作

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: 待定
