# Phase 30: Azure AI Search 整合 SemanticRouter

> **⏸️ 狀態: 延後執行** — 本 Phase 的工作已被納入 Phase 32 Sprint 115 (SemanticRouter Real Implementation)。
> 安全加固（Phase 31）必須先完成。Sprint 107-110 的詳細計劃可作為 Phase 32 Sprint 115 的參考。
>
> **執行順序**: Phase 31 (Security) → Phase 32 (包含本 Phase 工作) → Phase 33 (Production)

## 概述

Phase 30 專注於將 **SemanticRouter** 從內存實現遷移到 **Azure AI Search**，實現持久化向量存儲、動態路由管理和企業級搜索能力。

本 Phase 是 Phase 28 三層路由系統的延伸增強，將 Layer 2 (SemanticRouter) 升級為雲端向量數據庫支持。

## 目標

1. **Azure AI Search 索引** - 建立語義路由向量索引
2. **AzureSemanticRouter** - 實現基於 Azure AI Search 的語義路由器
3. **路由管理 API** - 動態新增/修改/刪除語義路由
4. **資料遷移** - 將現有 15 條路由遷移到 Azure
5. **監控整合** - 建立搜索性能監控

## 前置條件

- ✅ Phase 28 完成 (三層意圖路由系統)
- ✅ Phase 29 完成 (Agent Swarm 可視化)
- ✅ Azure OpenAI 已配置 (Embedding 模型)
- ✅ Azure 訂閱可用
- ⬜ Azure AI Search 資源建立

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 107](./sprint-107-plan.md) | Azure AI Search 資源建立 + 索引設計 | 15 點 | 📋 計劃中 |
| [Sprint 108](./sprint-108-plan.md) | AzureSemanticRouter 實現 | 25 點 | 📋 計劃中 |
| [Sprint 109](./sprint-109-plan.md) | 路由管理 API + 資料遷移 | 20 點 | 📋 計劃中 |
| [Sprint 110](./sprint-110-plan.md) | 整合測試 + 監控 + 文檔 | 15 點 | 📋 計劃中 |

**總計**: 75 Story Points (4 Sprints)
**預估時程**: 3 週 + 0.5 週緩衝 = 3.5 週

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    Phase 30: Azure AI Search 整合架構                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                      BusinessIntentRouter (Phase 28)                         │    │
│  │                                                                              │    │
│  │   Layer 1: PatternMatcher (不變)                                            │    │
│  │     └─ rules.yaml - 34 條規則                                               │    │
│  │                                                                              │    │
│  │   Layer 2: AzureSemanticRouter (🆕 升級)                                    │    │
│  │     ├─ Azure AI Search 向量搜索                                             │    │
│  │     ├─ Azure OpenAI Embedding                                               │    │
│  │     └─ 動態路由管理                                                         │    │
│  │                                                                              │    │
│  │   Layer 3: LLMClassifier (不變)                                             │    │
│  │     └─ Claude Haiku                                                          │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                          │                                           │
│                                          ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                           Azure Cloud                                        │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────┐    ┌──────────────────────────┐             │    │
│  │   │     Azure AI Search      │    │     Azure OpenAI         │             │    │
│  │   │                          │    │                          │             │    │
│  │   │  Index: semantic-routes  │    │  text-embedding-ada-002  │             │    │
│  │   │  • 56 utterances        │◄───│  (Embedding 生成)         │             │    │
│  │   │  • HNSW 向量索引         │    │                          │             │    │
│  │   │  • 混合搜索支持          │    │  gpt-4o                  │             │    │
│  │   │                          │    │  (LLM 分類)              │             │    │
│  │   └──────────────────────────┘    └──────────────────────────┘             │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     Route Management API (🆕 新增)                           │    │
│  │                                                                              │    │
│  │   POST   /api/v1/orchestration/routes          # 新增路由                   │    │
│  │   GET    /api/v1/orchestration/routes          # 列出路由                   │    │
│  │   PUT    /api/v1/orchestration/routes/{id}     # 更新路由                   │    │
│  │   DELETE /api/v1/orchestration/routes/{id}     # 刪除路由                   │    │
│  │   POST   /api/v1/orchestration/routes/sync     # YAML → Azure 同步         │    │
│  │   POST   /api/v1/orchestration/routes/search   # 測試搜索                   │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 環境配置

### 新增環境變量

```bash
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<search-service>.search.windows.net
AZURE_SEARCH_API_KEY=<your-api-key>
AZURE_SEARCH_INDEX_NAME=semantic-routes

# 路由配置
USE_AZURE_SEARCH=true
SEMANTIC_SIMILARITY_THRESHOLD=0.85
SEMANTIC_TOP_K=3
```

### Azure 資源需求

| 資源 | SKU | 估計成本 (USD/月) |
|------|-----|-------------------|
| Azure AI Search | Basic | ~$75 |
| Azure OpenAI (Embeddings) | 按量計費 | ~$10-20 |

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| azure-search-documents | 11.4+ | Azure AI Search SDK |
| azure-identity | 1.14+ | Azure 身份驗證 |
| openai | 1.10+ | Azure OpenAI Embedding |
| Python | 3.11+ | 後端實現 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Azure Search 延遲 | 搜索變慢 | 設定 timeout、fallback 到 LLM |
| Embedding 成本 | 費用增加 | 快取常用查詢、批次處理 |
| 索引同步問題 | 資料不一致 | 定期驗證、版本控制 |
| 網路連接失敗 | 服務中斷 | 重試機制、本地快取 |

## 成功標準

- [ ] Azure AI Search 資源成功建立
- [ ] 索引結構符合設計
- [ ] 15 條路由成功遷移
- [ ] 搜索延遲 < 100ms (P95)
- [ ] 路由管理 API 全部通過測試
- [ ] 與 BusinessIntentRouter 整合成功
- [ ] 監控 dashboard 可用
- [ ] 文檔完整

## 回滾計劃

```bash
# 切換回內存路由器
USE_AZURE_SEARCH=false
```

系統會自動 fallback 到原有的 SemanticRouter 實現。

---

**Phase 30 狀態**: ⏸️ 延後（工作納入 Phase 32 Sprint 115）
**原始預估**: 3.5 週 (3 週 + 0.5 週緩衝)
**總 Story Points**: 75 pts
**參見**: [Phase 32 README](../phase-32/README.md) — Sprint 115 引用本 Phase 的 Sprint 107-110 計劃
