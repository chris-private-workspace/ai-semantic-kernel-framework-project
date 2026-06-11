# Phase 33: Production Readiness + Quality

## 概述

Phase 33 專注於 **生產化準備與品質提升**，將 IPA Platform 從開發階段推向可供團隊內部使用的狀態。核心工作包括：InMemory 存儲全面替換、Checkpoint 系統統一、Docker 化部署到 Azure、可觀測性建設、以及測試覆蓋率提升至 60%。

本 Phase 基於 `docs/07-analysis/Overview/IPA-Platform-Improvement-Proposal.md` 中 Phase C 的規劃，是將平台從「可展示」提升到「可使用」的關鍵轉折點。

## 目標

1. **InMemory 存儲全面遷移** - 將全部 9 個 InMemory 存儲類替換為 Redis/PostgreSQL，重啟不丟失狀態
2. **ContextSynchronizer 升級** - 從 Phase 31 的 asyncio.Lock 最小修復升級為 Redis Distributed Lock
3. **4 Checkpoint 系統統一** - 設計並實現 UnifiedCheckpointRegistry，統一 4 個獨立的 Checkpoint 系統
4. **Docker 化 + CI/CD** - 建立生產級 Dockerfile（前後端），配置自動化 CI/CD Pipeline
5. **Azure 部署** - 部署到 Azure App Service B2 tier，配置環境變量與網路
6. **可觀測性** - OpenTelemetry + Azure Monitor + 結構化日誌 + Request ID 追蹤
7. **測試覆蓋率 → 60%** - 重點覆蓋 Orchestration、Auth、MCP 模組

## 前置條件

- ⬜ Phase 32 完成
- ⬜ Phase 31 安全加固完成（Auth Middleware、Mock 分離、Rate Limiting）
- ⬜ Azure 訂閱可用（App Service、Database for PostgreSQL、Cache for Redis）
- ⬜ GitHub 或 Azure DevOps 帳號可用（CI/CD Pipeline）

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 119](./sprint-119-plan.md) | InMemory Storage 遷移（前 4 個關鍵存儲） | 45 點 | 📋 計劃中 |
| [Sprint 120](./sprint-120-plan.md) | InMemory 完成 + Checkpoint 統一設計 | 40 點 | 📋 計劃中 |
| [Sprint 121](./sprint-121-plan.md) | Checkpoint 統一 + CI/CD Pipeline | 40 點 | 📋 計劃中 |
| [Sprint 122](./sprint-122-plan.md) | Azure 部署 + 可觀測性 | 45 點 | 📋 計劃中 |
| [Sprint 123](./sprint-123-plan.md) | 測試覆蓋率 + 品質衝刺 | 35 點 | 📋 計劃中 |

**總計**: ~205 Story Points (5 Sprints)
**預估時程**: 5 週 + 1 週緩衝 = 6 週

## 基礎設施架構

### Azure 部署架構

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Azure Resource Group                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────┐    ┌──────────────────────┐              │
│  │  Azure App Service   │    │  Azure App Service   │              │
│  │  (Backend - B2)      │    │  (Frontend - B1)     │              │
│  │  FastAPI + Uvicorn   │    │  Nginx + React SPA   │              │
│  │  ~$107/mo            │    │  ~$55/mo             │              │
│  └──────────┬───────────┘    └──────────────────────┘              │
│             │                                                        │
│  ┌──────────▼───────────┐    ┌──────────────────────┐              │
│  │  Azure Database for  │    │  Azure Cache for     │              │
│  │  PostgreSQL          │    │  Redis               │              │
│  │  (Flexible, B1ms)    │    │  (Basic C0)          │              │
│  │  ~$50-100/mo         │    │  ~$20-50/mo          │              │
│  └──────────────────────┘    └──────────────────────┘              │
│                                                                      │
│  ┌──────────────────────┐                                           │
│  │  Azure Monitor       │                                           │
│  │  Application Insights│                                           │
│  │  (含 OTel 整合)      │                                           │
│  └──────────────────────┘                                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 月度運營成本估算

| 項目 | 月成本 | 說明 |
|------|--------|------|
| Azure App Service B2 (Backend) | ~$107 | 2 vCPU, 3.5 GB RAM |
| Azure App Service B1 (Frontend) | ~$55 | 1 vCPU, 1.75 GB RAM |
| Azure Database for PostgreSQL | ~$50-100 | Flexible Server, B1ms |
| Azure Cache for Redis | ~$20-50 | Basic C0 |
| Azure Monitor / App Insights | ~$0-50 | 基本用量免費 |
| LLM API (Claude + Azure OpenAI) | ~$120-1,200 | 依使用量 |
| **合計** | **~$300-1,460/月** | |

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| Docker | 24+ | 容器化 |
| GitHub Actions / Azure DevOps | - | CI/CD |
| OpenTelemetry | 1.x | 分散式追蹤 |
| Azure Monitor | - | 雲端監控 |
| structlog / python-json-logger | latest | 結構化日誌 |
| Redis (Distributed Lock) | 7.x | 分散式鎖 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| InMemory 遷移導致回歸 | 功能中斷 | 漸進式遷移，每個存儲類獨立遷移並測試 |
| Checkpoint 系統耦合度高 | 遷移困難 | 先設計統一介面（Registry），再逐一遷移 |
| Azure 部署環境差異 | 本地正常雲端異常 | Docker 確保環境一致性，staging 環境先行驗證 |
| CI/CD Pipeline 不穩定 | 部署失敗 | 分步建置（build → test → deploy），每步獨立驗證 |
| 測試覆蓋率目標過高 | 延期 | 優先覆蓋關鍵路徑（Orchestration、Auth、MCP） |
| Azure 成本超預算 | 預算壓力 | 使用 B-tier（非 P-tier），啟用自動縮放限制 |

## 成功標準

- [ ] InMemory 存儲類：0 個殘留在生產代碼中
- [ ] ContextSynchronizer 使用 Redis Distributed Lock
- [ ] 4 Checkpoint 系統統一為 UnifiedCheckpointRegistry
- [ ] Backend + Frontend 均有生產級 Dockerfile
- [ ] CI/CD Pipeline 可自動執行 build → test → deploy
- [ ] 成功部署到 Azure App Service
- [ ] OpenTelemetry + Azure Monitor 可觀測 traces/metrics/logs
- [ ] 結構化 JSON 日誌 + X-Request-ID 全鏈路追蹤
- [ ] 測試覆蓋率 ≥ 60%
- [ ] 團隊內部可以開始使用

---

**Phase 33 開始時間**: 待 Phase 32 完成後
**預估完成時間**: 5-6 週
**總 Story Points**: ~205 pts
**基於文件**: `docs/07-analysis/Overview/IPA-Platform-Improvement-Proposal.md` Phase C
