# IPA Platform - MVP Implementation Plan (項目執行計劃)

> 📌 **更新說明** (2025-11-20): 本文檔已調整為 MVP 版本  
> - **部署方案**: Kubernetes → **Azure App Service**  
> - **消息隊列**: RabbitMQ → **Azure Service Bus**  
> - **監控方案**: ELK Stack → **Application Insights + Azure Monitor**

**版本**: 1.1 (MVP Revised)  
**創建日期**: 2025-11-19  
**更新日期**: 2025-11-20  
**項目週期**: 12週 (2025-11-25 至 2026-02-14)  
**團隊規模**: 8人

---

## 📋 目錄

1. [項目概覽](#項目概覽)
2. [開發里程碑](#開發里程碑)
3. [團隊組織與分工](#團隊組織與分工)
4. [Sprint 詳細規劃](#sprint-詳細規劃)
5. [技術實施路線](#技術實施路線)
6. [風險管理](#風險管理)
7. [質量保證策略](#質量保證策略)
8. [交付物清單](#交付物清單)

---

## 1. 項目概覽

### 1.1 項目目標

構建一個基於 Microsoft Agent Framework 的企業級智能流程自動化平台，實現：
- ✅ **14 個核心功能** (參考 [PRD](../01-planning/prd/prd-main.md))
- ✅ **3 個核心服務** (Workflow/Execution/Agent)
- ✅ **完整的 UI/UX** (React 18 + Shadcn UI)
- ✅ **生產就緒的基礎設施** (Kubernetes + CI/CD + 監控)

### 1.2 開發時間線

```
2025-11-25              2025-12-20              2026-01-17              2026-02-14
    │                       │                       │                       │
    ├─ Sprint 0 ────────────┤                       │                       │
    │  基礎設施搭建          │                       │                       │
    │                       ├─ Sprint 1 ────────────┤                       │
    │                       │  核心服務開發          │                       │
    │                       │                       ├─ Sprint 2 ────────────┤
    │                       │                       │  集成 + 安全           │
    │                       │                       │                       ├─ Sprint 3/4/5
    │                       │                       │                       │  UI + 測試
    ▼                       ▼                       ▼                       ▼
  Week 1-2                Week 3-4                Week 5-8                Week 9-12
Infrastructure         Core Services           Integrations            UI + Testing
```

### 1.3 Story Points 分配

| Sprint | Story Points | 功能範疇 | 狀態 |
|--------|--------------|----------|------|
| **Sprint 0** | 42 | 基礎設施 (K8s, CI/CD, DB, Auth) | 📄 規劃完成 |
| **Sprint 1** | 45 | 核心服務 (Workflow/Execution/Agent) | 📋 待規劃 |
| **Sprint 2** | 40 | 集成 (n8n, Teams, 監控, 審計) | 📋 待規劃 |
| **Sprint 3** | 38 | 安全與可觀測性 (RBAC, 加密, 追蹤) | 📋 待規劃 |
| **Sprint 4** | 42 | UI/前端 (Dashboard, 工作流編輯器) | 📋 待規劃 |
| **Sprint 5** | 35 | 測試與上線 (集成測試, 性能優化) | 📋 待規劃 |
| **總計** | **242** | 14 個核心功能 | - |

---

## 2. 開發里程碑

### 里程碑 1: 基礎設施就緒 (Week 2)
**日期**: 2025-12-06  
**交付物**:
- ✅ Azure App Service 運行 (Staging + Production)
- ✅ CI/CD 流水線自動化部署
- ✅ Azure PostgreSQL + Redis + Service Bus 運行
- ✅ OAuth 2.0 身份驗證工作
- ✅ Application Insights 監控和日誌就緒

**驗收標準**:
- [ ] 所有開發人員可以本地運行完整棧
- [ ] 代碼提交自動觸發 CI/CD
- [ ] Azure Monitor 和 App Insights 顯示系統指標
- [ ] 可以使用 Azure AD 登錄測試環境

**阻礙因素**:
- 🟡 Azure Service Principal 權限配置
- 🟢 無 K8s 學習曲線（已簡化）

---

### 里程碑 2: 核心服務完成 (Week 4)
**日期**: 2025-12-20  
**交付物**:
- ✅ Workflow Service (CRUD + 版本管理)
- ✅ Execution Service (狀態機 + 步驟編排)
- ✅ Agent Service (Agent Framework 集成)
- ✅ API Gateway (Kong) 配置
- ✅ 單元測試覆蓋率 > 80%

**驗收標準**:
- [ ] 可以通過 API 創建和執行工作流
- [ ] 支持 Agent 順序編排 (A → B → C)
- [ ] Agent Framework 插件架構可擴展
- [ ] 所有 API 有 Swagger 文檔

**阻礙因素**:
- 🔴 Agent Framework 學習曲線陡峭
- 🟡 狀態機複雜度超出估算

---

### 里程碑 3: 集成與安全完成 (Week 8)
**日期**: 2026-01-17  
**交付物**:
- ✅ n8n Webhook 觸發器
- ✅ Microsoft Teams 通知集成
- ✅ 審計日誌系統
- ✅ RBAC 權限系統
- ✅ 數據加密 (傳輸 + 靜態)
- ✅ 分佈式追蹤 (OpenTelemetry)

**驗收標準**:
- [ ] n8n 可以觸發工作流執行
- [ ] 失敗時自動發送 Teams 通知
- [ ] 所有用戶操作記錄到審計日誌
- [ ] 安全漏洞掃描通過 (無 P0/P1 漏洞)

**阻礙因素**:
- 🟡 n8n Webhook 簽名驗證複雜
- 🟡 Teams API 限流問題

---

### 里程碑 4: UI 與前端完成 (Week 10)
**日期**: 2026-01-31  
**交付物**:
- ✅ React 18 應用 (Vite + TypeScript)
- ✅ Dashboard (實時指標)
- ✅ 工作流列表與編輯器
- ✅ 執行監控視圖
- ✅ Agent 配置 UI
- ✅ 響應式設計 (桌面 + 平板)

**驗收標準**:
- [ ] 用戶可以在 UI 中創建工作流
- [ ] Dashboard 顯示實時執行狀態
- [ ] 工作流編輯器支持拖拽配置
- [ ] Lighthouse 性能得分 ≥ 90

**阻礙因素**:
- 🔴 工作流編輯器複雜度高 (考慮用 React Flow)
- 🟡 實時更新性能問題

---

### 里程碑 5: MVP 上線 (Week 12)
**日期**: 2026-02-14  
**交付物**:
- ✅ 完整的集成測試套件
- ✅ 性能優化 (P95 < 5s)
- ✅ 負載測試通過 (50+ 並發)
- ✅ 用戶文檔 + API 文檔
- ✅ 生產環境部署

**驗收標準**:
- [ ] 所有 14 個核心功能通過 UAT
- [ ] 無 P0/P1 Bug
- [ ] 性能指標達標 (參考 PRD NFR)
- [ ] 生產環境穩定運行 7 天

**阻礙因素**:
- 🔴 性能優化可能需要額外時間
- 🟡 UAT 發現的 Bug 量未知

---

## 3. 團隊組織與分工

### 3.1 團隊結構

```
Product Owner (1)
      │
      ├─── Backend Team (3)
      │    ├─ Tech Lead (1)
      │    ├─ Backend Engineer 1 (Workflow Service)
      │    └─ Backend Engineer 2 (Execution/Agent Service)
      │
      ├─── Frontend Team (2)
      │    ├─ Frontend Lead (UI 架構)
      │    └─ Frontend Engineer (組件開發)
      │
      ├─── DevOps Engineer (1)
      │    └─ Infrastructure + CI/CD
      │
      └─── QA Engineer (1)
           └─ 測試自動化 + 手動測試
```

### 3.2 Sprint 職責分配

#### Sprint 0: 基礎設施
- **DevOps** (主導): K8s, CI/CD, 監控 (21 points)
- **Backend** (支持): 數據庫, 認證, 緩存 (21 points)
- **Frontend**: 休息/學習 Shadcn UI
- **QA**: 設置測試框架

#### Sprint 1: 核心服務
- **Backend Team** (主導): 3 個核心服務 (45 points)
- **DevOps** (支持): API Gateway
- **Frontend**: React 應用初始化
- **QA**: 單元測試框架

#### Sprint 2: 集成
- **Backend** (主導): n8n, Teams, 審計日誌 (40 points)
- **DevOps** (主導): 監控集成
- **Frontend**: Design system 實現
- **QA**: 集成測試

#### Sprint 3: 安全
- **Backend** (主導): RBAC, 加密 (38 points)
- **DevOps** (主導): 分佈式追蹤
- **Frontend**: 認證 UI
- **QA**: 安全測試

#### Sprint 4: UI
- **Frontend** (主導): Dashboard, 編輯器 (42 points)
- **Backend** (支持): API 優化
- **DevOps**: 前端 CI/CD
- **QA**: E2E 測試

#### Sprint 5: 測試與上線
- **QA** (主導): 集成測試, 負載測試 (35 points)
- **Backend**: Bug 修復, 性能優化
- **Frontend**: UI/UX 優化
- **DevOps**: 生產部署

---

## 4. Sprint 詳細規劃

### Sprint 0: 基礎設施搭建 (Week 1-2)
📄 **詳細文檔**: [sprint-0-infrastructure-foundation.md](./sprint-planning/sprint-0-infrastructure-foundation.md)

**目標**: 建立開發、測試、生產環境
**Story Points**: 42
**團隊**: DevOps (主導) + Backend (支持)

**核心任務**:
- S0-1: 開發環境設置 (Docker Compose)
- S0-2: Kubernetes 集群 (AKS)
- S0-3: CI/CD 流水線 (GitHub Actions)
- S0-4: 數據庫基礎設施 (PostgreSQL)
- S0-5: Redis 緩存
- S0-6: RabbitMQ 消息隊列
- S0-7: 認證框架 (OAuth 2.0 + JWT)
- S0-8: 監控棧 (Prometheus + Grafana)
- S0-9: 日誌基礎設施 (ELK)

---

### Sprint 1: 核心服務開發 (Week 3-4)
📋 **詳細文檔**: 待創建 `sprint-1-core-services.md`

**目標**: 實現 Workflow/Execution/Agent 三大核心服務
**Story Points**: 45
**團隊**: Backend Team (主導)

**核心任務**:
- S1-1: Workflow Service - CRUD
- S1-2: Workflow Service - 版本管理
- S1-3: Execution Service - 狀態機
- S1-4: Execution Service - 步驟編排
- S1-5: Execution Service - 錯誤處理
- S1-6: Agent Service - Agent Framework 集成
- S1-7: Agent Service - Tool Factory
- S1-8: API Gateway 設置
- S1-9: 測試框架設置

**技術要點**:
- 使用 FastAPI 構建 REST API
- Entity Framework Core for .NET (如果使用 .NET)
- Agent Framework SDK 集成
- Hangfire 用於後台任務編排

---

### Sprint 2: 集成開發 (Week 5-6)
📋 **詳細文檔**: 待創建 `sprint-2-integrations.md`

**目標**: 實現外部集成和審計功能
**Story Points**: 40
**團隊**: Backend (主導) + DevOps (監控)

**核心任務**:
- S2-1: n8n Webhook 集成
- S2-2: n8n 工作流觸發器
- S2-3: Teams 通知服務
- S2-4: Teams 審批流程
- S2-5: 監控集成服務 (OpenTelemetry)
- S2-6: Alert Manager 集成
- S2-7: 審計日誌服務
- S2-8: Admin Dashboard API

---

### Sprint 3: 安全與可觀測性 (Week 7-8)
📋 **詳細文檔**: 待創建 `sprint-3-security-observability.md`

**目標**: 安全強化和完整的可觀測性
**Story Points**: 38
**團隊**: Backend (RBAC) + DevOps (追蹤)

**核心任務**:
- S3-1: RBAC 權限系統
- S3-2: API 安全強化
- S3-3: 數據加密 (靜態)
- S3-4: Secrets 管理 (Azure Key Vault)
- S3-5: 安全審計 Dashboard
- S3-6: 分佈式追蹤 (Jaeger)
- S3-7: 自定義業務指標
- S3-8: 性能監控 Dashboard
- S3-9: 安全滲透測試

---

### Sprint 4: UI 與前端開發 (Week 9-10)
📋 **詳細文檔**: 待創建 `sprint-4-ui-frontend.md`

**目標**: 完整的 Web UI 和用戶體驗
**Story Points**: 42
**團隊**: Frontend Team (主導)

**核心任務**:
- S4-1: React 應用初始化
- S4-2: Design System 實現 (Shadcn UI)
- S4-3: 認證 UI (登錄/登出)
- S4-4: Dashboard 實現
- S4-5: 工作流列表視圖
- S4-6: 工作流編輯器 (拖拽式)
- S4-7: 執行監控視圖
- S4-8: Agent 配置 UI
- S4-9: 響應式設計
- S4-10: E2E 測試設置 (Playwright)

---

### Sprint 5: 測試與上線準備 (Week 11-12)
📋 **詳細文檔**: 待創建 `sprint-5-testing-launch.md`

**目標**: 完整測試、性能優化、生產部署
**Story Points**: 35
**團隊**: 全員參與

**核心任務**:
- S5-1: 集成測試套件
- S5-2: 負載測試 (k6)
- S5-3: 性能優化
- S5-4: Bug 修復 Sprint
- S5-5: 用戶文檔
- S5-6: 部署 Runbook
- S5-7: UAT 準備

---

## 5. 技術實施路線

### 5.1 技術棧演進

```
Week 1-2: Infrastructure Setup
├─ Azure Kubernetes Service (AKS)
├─ PostgreSQL 16 + Redis 7 + RabbitMQ 3.12
├─ GitHub Actions CI/CD
└─ Prometheus + Grafana + ELK

Week 3-4: Backend Core
├─ Python 3.11 + FastAPI
├─ Agent Framework SDK
├─ SQLAlchemy ORM
└─ Hangfire (background jobs)

Week 5-6: Integrations
├─ n8n Community Edition
├─ Microsoft Teams Webhooks
├─ OpenTelemetry
└─ Azure Key Vault

Week 7-8: Security & Observability
├─ JWT + OAuth 2.0
├─ RBAC (Role-Based Access Control)
├─ Jaeger (distributed tracing)
└─ Prometheus custom metrics

Week 9-10: Frontend
├─ React 18 + TypeScript + Vite
├─ Shadcn UI (Tailwind-based)
├─ React Flow (workflow editor)
├─ TanStack Query (data fetching)
└─ Monaco Editor (code editing)

Week 11-12: Testing & Launch
├─ pytest (backend unit tests)
├─ Jest + Testing Library (frontend)
├─ Playwright (E2E tests)
├─ k6 (load testing)
└─ Production deployment
```

### 5.2 架構演進路線

#### Phase 1: Monolith (Sprint 0-1)
```
┌─────────────────────────────────────┐
│   Single FastAPI Application        │
│   ├─ Workflow Module                │
│   ├─ Execution Module                │
│   └─ Agent Module                    │
└─────────────────────────────────────┘
```

#### Phase 2: Modular Monolith (Sprint 2-3)
```
┌─────────────────────────────────────┐
│   API Gateway (Kong)                 │
└────────────┬────────────────────────┘
             │
     ┌───────┼───────┐
     │       │       │
   ┌─▼─┐  ┌─▼─┐  ┌─▼─┐
   │W  │  │E  │  │A  │  (Still monolith, but separated modules)
   │S  │  │S  │  │S  │
   └───┘  └───┘  └───┘
```

#### Phase 3: Production Ready (Sprint 4-5)
```
┌─────────────────────────────────────┐
│   React Frontend (Nginx)            │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   API Gateway (Kong)                 │
└────────────┬────────────────────────┘
             │
     ┌───────┼───────┐
     │       │       │
   ┌─▼─┐  ┌─▼─┐  ┌─▼─┐
   │W  │  │E  │  │A  │
   │S  │  │S  │  │S  │
   └─┬─┘  └─┬─┘  └─┬─┘
     │      │      │
     └──────┼──────┘
            │
   ┌────────▼────────┐
   │  PostgreSQL     │
   │  Redis          │
   │  RabbitMQ       │
   └─────────────────┘
```

---

## 6. 風險管理

### 6.1 技術風險

| 風險 | 嚴重性 | 概率 | 緩解策略 | 責任人 |
|------|--------|------|----------|--------|
| **Agent Framework 學習曲線** | 🔴 高 | 🟡 中 | • 第一週專門學習時間<br>• 創建內部文檔<br>• 考慮備用方案 (純 Python 編排) | Tech Lead |
| **n8n Webhook 可靠性** | 🟡 中 | 🟡 中 | • 實現重試機制<br>• Circuit breaker 模式<br>• 監控 n8n 健康狀態 | Backend Lead |
| **工作流編輯器複雜度** | 🔴 高 | 🟡 中 | • 使用 React Flow 庫<br>• MVP 只做基礎功能<br>• 延後高級功能到 Phase 2 | Frontend Lead |
| **Azure 配置延遲** | 🟡 中 | 🟡 中 | • 第一天立即開始配置<br>• 使用 Minikube 本地測試<br>• 預留緩衝時間 | DevOps |
| **性能未達標** | 🟡 中 | 🟢 低 | • 早期性能測試<br>• Redis 緩存優化<br>• Database indexing | Backend Lead |

### 6.2 進度風險

| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| **假期影響 (Sprint 2)** | Sprint 2 在 12/23-1/3，可能人員不足 | • 降低 Sprint 2 velocity<br>• 提前完成關鍵任務 |
| **任務估算不準** | 某些 Sprint 可能延期 | • 每個 Sprint 預留 10% buffer<br>• 每日站會及早發現問題 |
| **依賴阻塞** | 後續 Sprint 無法開始 | • 關鍵路徑任務優先<br>• 並行開發可能的任務 |
| **團隊成員離職** | 知識流失，進度延遲 | • 代碼審查確保知識共享<br>• 文檔記錄關鍵決策 |

### 6.3 業務風險

| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| **需求變更** | 重新規劃，延期 | • 鎖定 MVP 範圍<br>• 延後非關鍵功能 |
| **預算超支** | Azure 成本超過預期 | • 每日監控 Azure 成本<br>• 優化 LLM 使用 |
| **利益相關者期望** | 功能不符預期 | • 每 Sprint 演示<br>• 早期 UAT 反饋 |

---

## 7. 質量保證策略

### 7.1 測試策略

| 測試類型 | 覆蓋率目標 | 工具 | 責任人 |
|----------|------------|------|--------|
| **單元測試** | ≥ 80% | pytest, Jest | 各開發人員 |
| **集成測試** | 所有 API endpoints | pytest + TestClient | Backend Team |
| **E2E 測試** | 關鍵用戶流程 | Playwright | QA Engineer |
| **性能測試** | P95 < 5s | k6, Locust | QA + DevOps |
| **安全測試** | 無 P0/P1 漏洞 | Trivy, Snyk, OWASP ZAP | DevOps |
| **UI 測試** | 所有頁面 | Storybook, Chromatic | Frontend Team |

### 7.2 Code Review 流程

```
Developer → Create PR → Automated Tests
                              │
                              ▼
                         Tests Pass?
                              │
                    ┌─────────┴─────────┐
                   NO                  YES
                    │                   │
                    ▼                   ▼
              Fix & Push          Code Review
                                  (1+ Approvers)
                                        │
                                        ▼
                                  Approved?
                                        │
                              ┌─────────┴─────────┐
                             NO                  YES
                              │                   │
                              ▼                   ▼
                       Address Comments     Merge to main
                                                  │
                                                  ▼
                                         Auto-deploy Staging
```

### 7.3 Definition of Done (DoD)

每個任務必須滿足：
- [ ] 代碼已提交並合併到 main
- [ ] 單元測試覆蓋率 ≥ 80%
- [ ] 集成測試通過
- [ ] Code review 已批准
- [ ] 無 linting 錯誤
- [ ] API 文檔已更新 (Swagger)
- [ ] 部署到 Staging 成功
- [ ] 煙霧測試通過
- [ ] 技術文檔已更新

---

## 8. 交付物清單

### 8.1 技術交付物

| 交付物 | 描述 | Sprint | 負責人 |
|--------|------|--------|--------|
| **源代碼** | 所有服務的完整代碼 | 0-5 | 開發團隊 |
| **Docker Images** | 所有服務的容器鏡像 | 0-5 | DevOps |
| **Kubernetes Manifests** | 部署配置 (Helm Charts) | 0 | DevOps |
| **CI/CD Pipeline** | GitHub Actions workflows | 0 | DevOps |
| **數據庫 Schema** | PostgreSQL schema + migrations | 0-2 | Backend |
| **API Documentation** | OpenAPI 3.0 specs | 1-4 | Backend |
| **UI Components** | Storybook 組件庫 | 4 | Frontend |

### 8.2 文檔交付物

| 交付物 | 描述 | Sprint | 負責人 |
|--------|------|--------|--------|
| **用戶手冊** | 最終用戶操作指南 | 5 | Product Owner |
| **API 文檔** | REST API 使用說明 | 1-4 | Backend |
| **架構文檔** | 系統架構圖和說明 | 0 | Tech Lead |
| **部署 Runbook** | 生產部署步驟 | 0, 5 | DevOps |
| **故障排除指南** | 常見問題和解決方案 | 5 | 全員 |
| **開發者指南** | 如何創建 Agent | 1 | Backend |

### 8.3 測試交付物

| 交付物 | 描述 | Sprint | 負責人 |
|--------|------|--------|--------|
| **測試計劃** | 完整的測試策略 | 1 | QA |
| **測試用例** | 所有功能的測試案例 | 1-5 | QA |
| **測試報告** | 測試結果和覆蓋率 | 5 | QA |
| **性能測試報告** | 負載測試結果 | 5 | QA + DevOps |
| **安全測試報告** | 滲透測試結果 | 3, 5 | DevOps |

---

## 9. 成功標準

### 9.1 MVP 交付標準

✅ **功能完整性**
- 14 個核心功能全部實現 (參考 [PRD Features](../01-planning/prd/prd-main.md#mvp-scope))
- 所有功能通過 UAT

✅ **性能指標**
- Agent 執行延遲 P95 < 5s
- Dashboard 加載時間 < 2s
- 支持 50+ 並發執行
- 緩存命中率 ≥ 60%

✅ **質量指標**
- 測試覆蓋率 ≥ 80%
- 無 P0/P1 Bug
- 代碼 linting 通過
- 安全掃描無高危漏洞

✅ **可用性指標**
- 系統可用性 ≥ 99.0%
- MTTR (平均恢復時間) < 30 分鐘
- 自動化部署成功率 > 95%

✅ **文檔完整性**
- 用戶手冊完成
- API 文檔自動生成
- 部署 Runbook 完成
- 故障排除指南完成

### 9.2 Go-Live 檢查清單

#### 技術就緒
- [ ] 生產環境配置完成
- [ ] SSL 證書配置
- [ ] 監控和告警配置
- [ ] 日誌收集正常
- [ ] 備份策略實施
- [ ] 災難恢復計劃就緒

#### 安全就緒
- [ ] 滲透測試通過
- [ ] OWASP Top 10 檢查通過
- [ ] Secrets 管理正確 (Key Vault)
- [ ] RBAC 配置正確
- [ ] 審計日誌啟用

#### 運維就緒
- [ ] 部署 Runbook 測試
- [ ] 回滾程序測試
- [ ] On-call 輪值表
- [ ] 故障響應流程
- [ ] 性能基準建立

#### 業務就緒
- [ ] UAT 通過
- [ ] 用戶培訓完成
- [ ] Support 團隊準備就緒
- [ ] 溝通計劃執行

---

## 10. 附錄

### 10.1 相關文檔

- [Product Brief](../00-discovery/product-brief/product-brief.md)
- [PRD Main](../01-planning/prd/prd-main.md)
- [UI/UX Design Spec](../01-planning/ui-ux/ui-ux-design-spec.md)
- [Technical Architecture](../02-architecture/technical-architecture.md)
- [Solutioning Gate Check](../02-architecture/gate-check/solutioning-gate-check.md)
- [Sprint Status Tracking](./sprint-status.yaml)

### 10.2 會議節奏

| 會議 | 頻率 | 時長 | 參與者 |
|------|------|------|--------|
| **Daily Standup** | 每天 10:00 AM | 15 分鐘 | 全員 |
| **Sprint Planning** | Sprint 開始 | 2 小時 | 全員 |
| **Sprint Review** | Sprint 結束 | 1 小時 | 全員 + 利益相關者 |
| **Sprint Retrospective** | Sprint 結束 | 1 小時 | 全員 |
| **Tech Sync** | 每週三 | 30 分鐘 | 技術團隊 |
| **Stakeholder Update** | 每兩週 | 30 分鐘 | PO + 管理層 |

### 10.3 溝通渠道

- **Teams Channel**: `ipa-platform-dev`
- **GitHub Repository**: `org/ipa-platform`
- **Jira Board**: `IPA-MVP`
- **Confluence**: `IPA Platform Documentation`
- **Azure DevOps**: CI/CD + Artifacts

---

**文檔狀態**: ✅ 已完成  
**上次更新**: 2025-11-19  
**下次審查**: 2025-11-25 (Sprint 0 開始前)

**批准簽名**:
- Product Owner: _________________ 日期: _______
- Tech Lead: _________________ 日期: _______
- DevOps Lead: _________________ 日期: _______
