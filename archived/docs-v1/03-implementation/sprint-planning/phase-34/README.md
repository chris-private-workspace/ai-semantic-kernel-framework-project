# Phase 34: Feature Expansion（功能擴展）

## 概述

Phase 34 專注於 **業務場景擴展與整合深化**，在 Phase 33 建立的生產化基礎上，擴展 AD 帳號管理以外的業務場景，並完善核心模組從 Mock 到 Real 的遷移。

本 Phase 基於 `docs/07-analysis/Overview/IPA-Platform-Improvement-Proposal.md` 中 Phase D 的規劃。

> **Status**: Sprint 規劃完成 — 10 Sprints (124-133), ~260 pts

## 目標

1. **擴展業務場景** — 超越 AD 帳號管理，支持 IT 事件處理等新場景
2. **外部系統整合** — n8n、Azure Data Factory、D365 等 MCP 整合
3. **核心模組完善** — LLMClassifier Mock→Real、Correlation/RootCause 真實資料
4. **架構加固** — MAF Anti-Corruption Layer、HybridOrchestratorV2 重構
5. **品質目標** — 測試覆蓋率提升至 80%
6. **前端完善** — ReactFlow 工作流視覺化

## 前置條件

- ⬜ Phase 33 完成（生產化就緒、Docker on Azure、60% 覆蓋率）
- ⬜ 團隊內部已開始使用 IPA Platform
- ⬜ 第一場景（AD 帳號管理）已穩定運行
- ⬜ 收集到初期使用回饋

## 優先級項目

### P1 — 高優先級（預估 80-100 pts）

| 項目 | 說明 | 預估工作量 | 業務價值 |
|------|------|----------|---------|
| **n8n 整合** | 3 種協作模式：IPA 觸發 n8n、n8n 觸發 IPA、雙向協作 | 2-3 週 | IPA + n8n 互補，覆蓋更多自動化場景 |
| **Azure Data Factory MCP** | ETL 場景整合，Pipeline 觸發/監控/管理 | 1.5-2 週 | 資料工程自動化 |
| **IT 事件處理場景** | ServiceNow 事件→分析→建議→執行，第二個完整業務場景 | 2 週 | 預估月節省 ~$4,000 |

**n8n 3 種協作模式**:
```
模式 1: IPA 觸發 n8n
  用戶請求 → IPA Agent 分析 → 呼叫 n8n Webhook → n8n 執行工作流

模式 2: n8n 觸發 IPA
  n8n 工作流 → 呼叫 IPA API → IPA Agent 處理 → 返回結果

模式 3: 雙向協作
  用戶請求 → IPA 推理決策 → n8n 編排執行 → IPA 監控結果
```

### P2 — 中優先級（預估 70-90 pts）

| 項目 | 說明 | 預估工作量 | 技術價值 |
|------|------|----------|---------|
| **LLMClassifier Mock→Real** | 將三層路由的 Layer 3 從 Mock 遷移到真實 LLM | 1 週 | 路由覆蓋最後 10%，三層路由完整 |
| **D365 MCP Server** | Dynamics 365 業務系統整合 | 1.5 週 | 業務系統資料存取 |
| **Correlation/RootCause 真實資料** | 從硬編碼/偽造資料遷移到真實事件資料 | 1.5 週 | 事件關聯分析可用 |
| **MAF Anti-Corruption Layer** | 隔離 MAF preview API 變更的影響 | 1 週 | MAF API 變更風險隔離 |
| **測試覆蓋率 → 80%** | 補強 Phase 33 後的覆蓋率差距 | 2-3 週 | 品質目標達成 |

### P3 — 低優先級（預估 50-70 pts）

| 項目 | 說明 | 預估工作量 | 長期價值 |
|------|------|----------|---------|
| **HybridOrchestratorV2 重構 (Mediator)** | 消除 God Object（1,254 LOC、11 依賴），重構為 Mediator Pattern | 2-3 週 | 架構可維護性 |
| **ReactFlow 工作流視覺化** | 安裝 ReactFlow，實現工作流 DAG 視覺化 | 1.5-2 週 | 前端完整度 |

## 預估規模

| 優先級 | 預估 Story Points | 預估 Sprints |
|--------|-------------------|-------------|
| P1 | 80-100 pts | 3-4 sprints |
| P2 | 70-90 pts | 3-4 sprints |
| P3 | 50-70 pts | 2-3 sprints |
| **Total** | **200-260 pts** | **8-11 sprints** |

## Sprint 規劃明細

### P1 Sprints (Sprint 124-127, 105 pts)

| Sprint | 主題 | Story Points |
|--------|------|-------------|
| **124** | n8n 整合 Mode 1 + Mode 2 | 25 pts |
| **125** | n8n 整合 Mode 3 + Azure Data Factory MCP | 30 pts |
| **126** | IT 事件處理場景（ServiceNow → 分析 → 修復） | 30 pts |
| **127** | P1 整合測試 + E2E 驗證 | 20 pts |

### P2 Sprints (Sprint 128-131, 95 pts)

| Sprint | 主題 | Story Points |
|--------|------|-------------|
| **128** | LLMClassifier Mock→Real + MAF Anti-Corruption Layer | 25 pts |
| **129** | D365 MCP Server | 25 pts |
| **130** | Correlation/RootCause 真實資料連接 | 20 pts |
| **131** | 測試覆蓋率 → 80% | 25 pts |

### P3 Sprints (Sprint 132-133, 60 pts)

| Sprint | 主題 | Story Points |
|--------|------|-------------|
| **132** | HybridOrchestratorV2 重構（Mediator Pattern） | 30 pts |
| **133** | ReactFlow 工作流視覺化 + Phase 34 驗收 | 30 pts |

**Total**: 10 Sprints, **260 Story Points**

## 依賴於 Phase 33

| Phase 33 交付物 | Phase 34 依賴項目 |
|----------------|-----------------|
| InMemory 全面替換 | n8n 整合需要可靠的狀態管理 |
| Azure 部署 | 所有新整合需要雲端環境 |
| CI/CD Pipeline | 持續交付新功能 |
| 60% 測試覆蓋率 | 80% 覆蓋率的基礎 |
| 結構化日誌 + OTel | 新整合的可觀測性 |
| Redis Distributed Lock | 多 Worker 環境下的安全性 |

## 月度運營成本變化（相對 Phase 33）

| 項目 | Phase 33 成本 | Phase 34 新增 | 說明 |
|------|-------------|-------------|------|
| Azure App Service | ~$162 | +$0-50 | 可能需要更高 tier |
| Azure Database | ~$50-100 | +$0-50 | 資料量增加 |
| Azure Cache for Redis | ~$20-50 | +$0 | 維持 |
| LLM API | ~$120-1,200 | +$200-500 | 新場景增加呼叫量 |
| n8n (self-hosted) | $0 | +$50-100 | Docker 部署 |
| Azure Data Factory | $0 | +$50-200 | 依 Pipeline 使用量 |
| **合計** | ~$300-1,460 | +$300-900 | **~$600-2,360/月** |

## 成功標準

| 標準 | 測量方式 |
|------|---------|
| 3+ 業務場景端到端可用 | 功能驗證 |
| n8n 整合 3 種模式可用 | 整合測試 |
| LLMClassifier 使用真實 LLM | 路由準確度測試 |
| 測試覆蓋率 ≥ 80% | Coverage.py 報告 |
| 月節省 > $10,000 | 業務指標追蹤 |
| 無 CRITICAL 已知問題 | Issue tracking |

## 風險

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Phase 33 延期 | Phase 34 被迫推遲 | Phase 33 設有 1 週緩衝 |
| n8n 整合複雜度超預期 | 工期延長 | 先實現最簡單的模式（模式 1），漸進擴展 |
| LLM API 成本超預算 | 運營壓力 | 設置 budget alerts，使用 caching 減少重複呼叫 |
| MAF API breaking changes | 整合中斷 | ACL 隔離層提供緩衝 |
| HybridOrchestratorV2 重構風險 | 核心功能中斷 | 漸進式重構，保持向後兼容 |

---

**Phase 34 狀態**: 📋 Sprint 規劃完成
**Story Points**: 260 pts（10 Sprints: 124-133）
**基於文件**: `docs/07-analysis/Overview/IPA-Platform-Improvement-Proposal.md` Phase D
**Last Updated**: 2026-02-24
