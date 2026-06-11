# Phase 38: E2E Assembly C — 記憶與知識組裝

## 概述

Phase 38 專注於實現 **記憶與知識系統的端到端組裝**，讓 Orchestrator Agent 具備跨對話記憶能力和企業知識檢索能力，能像資深 IT 運維主管一樣工作——記得過去處理過的問題，並能查閱企業知識庫回答專業問題。

本 Phase 是 E2E Assembly 系列的第三階段（C），在 Phase 37 (B) 完成基礎編排組裝後，為 Orchestrator 注入「記憶」與「知識」兩大核心能力。

## 目標

1. **自動記憶寫入 + 檢索注入** - 對話結束自動摘要存入 Long-term Memory，新對話自動檢索相關記憶注入上下文
2. **RAG Pipeline** - 完整的文檔解析、Chunking、Embedding、向量索引、檢索 + Reranking 管線
3. **Agent Skills + 知識管理** - MAF Agent Skills 打包 ITIL SOP，知識庫管理 UI 與 API
4. **整合測試 + 效能調優** - 端到端 10 步流程測試、記憶持續性驗證、RAG 品質評估

## 前置條件

- ✅ Phase 37 (E2E Assembly B) 完成
- ✅ mem0 + Qdrant 記憶基礎設施就緒
- ✅ Redis Working Memory 機制就緒
- ✅ Azure OpenAI Embedding 模型可用 (text-embedding-3-large)
- ✅ MAF RC4 Agent Skills API 就緒 (FileAgentSkillsProvider)
- ✅ Orchestrator Agent 基礎編排能力就緒

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 117](./sprint-117-plan.md) | 自動記憶寫入 + 檢索注入 | ~10 點 | ✅ 完成 |
| [Sprint 118](./sprint-118-plan.md) | RAG Pipeline | ~10 點 | ✅ 完成 |
| [Sprint 119](./sprint-119-plan.md) | Agent Skills + 知識管理 | ~10 點 | ✅ 完成 |
| [Sprint 120](./sprint-120-plan.md) | 整合測試 + 效能調優 + 文檔 | ~8 點 | ✅ 完成 |

**總計**: ~38 Story Points (4 Sprints)
**預估時程**: 3 週 + 0.5 週緩衝 = 3.5 週

## 架構概覽

### 記憶系統架構（三層記憶）

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    Phase 38: 記憶與知識系統架構                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                        三層記憶系統 (Memory Layers)                          │    │
│  │                                                                              │    │
│  │   Layer 1: Working Memory (Redis, TTL 30min)                                │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │  • 當前對話上下文 (current conversation context)                      │  │    │
│  │   │  • 工具調用結果緩存 (tool call result cache)                          │  │    │
│  │   │  • 即時狀態 (real-time state)                                         │  │    │
│  │   │  ──── 自動提升 ↓ (對話結束時摘要提升) ────                             │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │   Layer 2: Session Memory (PostgreSQL, TTL 7d)                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │  • 對話摘要 (conversation summaries)                                  │  │    │
│  │   │  • 任務執行記錄 (task execution records)                              │  │    │
│  │   │  • 用戶偏好快照 (user preference snapshots)                           │  │    │
│  │   │  ──── 自動提升 ↓ (重要記憶提升至永久層) ────                           │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │   Layer 3: Long-term Memory (mem0 + Qdrant)                                 │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │  • Episodic Memory: 過去事件記錄（問題、處理方式、結果、教訓）         │  │    │
│  │   │  • Semantic Memory: 學習到的知識和模式                                 │  │    │
│  │   │  • 語義搜索 + 時間範圍 + 用戶篩選                                     │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 知識系統架構（三層知識）

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        知識系統架構 (Knowledge Layers)                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Layer A: Agent Skills（結構化知識）                                         │    │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │  │  • ITIL Incident Management SOP                                      │  │    │
│  │  │  • Change Management SOP                                             │  │    │
│  │  │  • Enterprise Architecture Reference                                 │  │    │
│  │  │  • FileAgentSkillsProvider (MAF RC4 context_provider 單數)           │  │    │
│  │  └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │  Layer B: Vector RAG（非結構化知識）                                         │    │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │  │  文檔解析 → Chunking → Embedding → Qdrant 向量索引                    │  │    │
│  │  │  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  ┌───────────┐  │  │    │
│  │  │  │ PDF/Word │  │ Recursive +  │  │ text-embed-   │  │  Qdrant   │  │  │    │
│  │  │  │ HTML/MD  │→│ Semantic     │→│ ding-3-large  │→│ Collection│  │  │    │
│  │  │  │ Parser   │  │ Chunking     │  │ (Azure)       │  │ Manager   │  │  │    │
│  │  │  └──────────┘  └──────────────┘  └───────────────┘  └───────────┘  │  │    │
│  │  │                                                                      │  │    │
│  │  │  檢索: Hybrid Search (vector + keyword) + Cross-Encoder Reranking   │  │    │
│  │  └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │  Layer C: Agentic RAG（自主檢索）                                           │    │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │  │  Orchestrator Agent 自主決定：                                        │  │    │
│  │  │  • 何時搜索（判斷問題是否需要知識庫支援）                               │  │    │
│  │  │  • 搜索什麼（生成最佳查詢語句）                                        │  │    │
│  │  │  • search_knowledge() function tool                                  │  │    │
│  │  │  • search_memory() function tool                                     │  │    │
│  │  └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 端到端資料流

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                     Orchestrator 記憶 + 知識 資料流                            │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  新對話開始                                                                    │
│  ┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │ 用戶輸入 │───▶│ 檢索相關記憶  │───▶│ 注入 Context │───▶│ Orchestrator │    │
│  └─────────┘    │ (mem0 search) │    │ (memory +    │    │ Agent 推理   │    │
│                  └──────────────┘    │  knowledge)  │    └──────┬───────┘    │
│                                      └──────────────┘           │            │
│                                                                  ↓            │
│  對話進行中                                    ┌──────────────────────┐       │
│  ┌──────────────────────────────────────────┐ │ search_knowledge()  │       │
│  │ Working Memory (Redis) 持續更新            │ │ search_memory()     │       │
│  │ • 對話歷史、工具結果、中間狀態             │ │ (Agent 自主調用)     │       │
│  └──────────────────────────────────────────┘ └──────────────────────┘       │
│                                                                               │
│  對話結束                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ 自動摘要生成  │───▶│ 寫入 mem0    │───▶│ 清理 Working │                   │
│  │ (LLM 摘要)   │    │ Episodic     │    │ Memory       │                   │
│  │ 問題/處理/    │    │ Long-term    │    │ (Redis TTL)  │                   │
│  │ 結果/教訓     │    └──────────────┘    └──────────────┘                   │
│  └──────────────┘                                                            │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Sprint 詳細內容

### Sprint 117: 自動記憶寫入 + 檢索注入 (~10 SP)

| Story | 描述 | SP |
|-------|------|-----|
| S117-1 | 對話結束時自動摘要 → 寫入 mem0 episodic (Long-term Memory) | 2 |
| S117-2 | 摘要 prompt 設計（提取：問題描述、處理方式、結果、教訓） | 2 |
| S117-3 | 新對話開始時自動檢索相關記憶 → 注入 Orchestrator context | 2 |
| S117-4 | search_memory() tool 完善：語義搜索 + 時間範圍 + 用戶篩選 | 2 |
| S117-5 | Working Memory (Redis) 與 Long-term Memory (mem0+Qdrant) 自動提升機制 | 2 |

### Sprint 118: RAG Pipeline (~10 SP)

| Story | 描述 | SP |
|-------|------|-----|
| S118-1 | 文檔解析器：PDF / Word / HTML / Markdown 解析 | 2 |
| S118-2 | Chunking 策略：recursive + semantic chunking | 2 |
| S118-3 | Embedding：Azure OpenAI text-embedding-3-large 整合 | 1 |
| S118-4 | 向量索引：Qdrant collection 管理（建立、更新、刪除） | 2 |
| S118-5 | 檢索 + Reranking：hybrid search (vector + keyword) + cross-encoder reranking | 2 |
| S118-6 | search_knowledge() function tool：Orchestrator 自主決定何時/如何檢索 | 1 |

### Sprint 119: Agent Skills + 知識管理 (~10 SP)

| Story | 描述 | SP |
|-------|------|-----|
| S119-1 | MAF Agent Skills 打包：ITIL Incident Management SOP | 2 |
| S119-2 | MAF Agent Skills 打包：Change Management SOP | 2 |
| S119-3 | MAF Agent Skills 打包：Enterprise Architecture Reference | 1 |
| S119-4 | FileAgentSkillsProvider 配置（RC4 API：context_provider 單數） | 1 |
| S119-5 | 知識庫管理 UI：文檔上傳頁面、索引狀態、搜索測試 | 2 |
| S119-6 | 知識庫 CRUD API | 2 |

### Sprint 120: 整合測試 + 效能調優 + 文檔 (~8 SP)

| Story | 描述 | SP |
|-------|------|-----|
| S120-1 | 端到端整合測試：完整 10 步流程測試 | 2 |
| S120-2 | 記憶系統測試：跨 session 記憶持續性驗證 | 1 |
| S120-3 | RAG 品質測試：retrieval accuracy、answer relevance 評估 | 1 |
| S120-4 | 效能調優：LLM call latency、RAG 檢索延遲、SSE 串流延遲 | 2 |
| S120-5 | 完整文檔：系統架構更新、部署指南、使用者手冊 | 1 |
| S120-6 | V9 代碼庫分析（基於 E2E Assembly 完成後的全新狀態） | 1 |

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| mem0 | latest | Long-term Memory 管理 |
| Qdrant | 1.7+ | 向量資料庫（記憶 + 知識） |
| Azure OpenAI | text-embedding-3-large | 文本向量化 |
| Redis | 7.0+ | Working Memory (TTL 30min) |
| PostgreSQL | 16+ | Session Memory (TTL 7d) |
| FastAPI | 0.100+ | 後端 API 框架 |
| React | 18.2+ | 知識庫管理 UI |
| MAF RC4 | latest | Agent Skills (FileAgentSkillsProvider) |
| LangChain / Unstructured | latest | 文檔解析 + Chunking |

## 交付物與驗收場景

### 場景 1: 跨對話記憶

```
用戶: 「你好，上次提到的 Pipeline 問題解決了嗎？」

Orchestrator (自動檢索記憶):
  → mem0 搜索: "Pipeline 問題" + user_id
  → 找到記憶: "2026-03-15 用戶報告 CI/CD Pipeline timeout，
     原因是 Docker image 過大，已建議分層建構 + 快取"

Orchestrator 回覆:
  「你好！上次您提到 CI/CD Pipeline timeout 的問題，我們分析後發現是
   Docker image 過大導致的，建議採用分層建構和快取策略。請問這個方案
   實施後效果如何？」
```

### 場景 2: 企業知識庫查詢

```
用戶: 「依照公司的變更管理流程，這個操作需要怎麼做？」

Orchestrator (自主決定檢索):
  → search_knowledge("變更管理流程 操作步驟")
  → Agent Skills: Change Management SOP
  → Vector RAG: 相關歷史變更記錄

Orchestrator 回覆:
  「根據公司的變更管理 SOP，此操作屬於『標準變更』類別，需要：
   1. 填寫變更請求單 (RFC)
   2. 由 CAB 審批（標準變更可自動審批）
   3. 排定維護窗口
   4. 執行變更並記錄結果
   根據過去類似變更的記錄，建議在非尖峰時段執行...」
```

### 場景 3: 完整 10 步端到端流程

```
步驟 1:  用戶發起對話
步驟 2:  自動檢索相關記憶 → 注入上下文
步驟 3:  Orchestrator 理解意圖 + 評估風險
步驟 4:  選擇合適 Agent（MAF/Claude）
步驟 5:  Agent 執行時自主查詢知識庫 (search_knowledge)
步驟 6:  Agent 參考歷史記憶 (search_memory)
步驟 7:  工具調用 + 結果回傳
步驟 8:  SSE 串流回應用戶
步驟 9:  對話結束 → 自動摘要 → 寫入 Long-term Memory
步驟 10: Working Memory 清理 / Session Memory 歸檔
```

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| mem0 向量搜索延遲過高 | 新對話啟動慢 | 異步預取、快取熱門記憶、限制搜索範圍 |
| RAG 檢索品質不佳 | 回答不準確 | Hybrid search + Reranking、Chunking 策略調優 |
| 文檔解析格式不支援 | 知識庫覆蓋不全 | 漸進式支援、優先 PDF/Markdown、fallback 純文字 |
| 記憶摘要品質不穩定 | 記憶失真 | 摘要 prompt 精心設計、人工抽檢機制 |
| Qdrant 集群穩定性 | 記憶/知識不可用 | 健康檢查、降級策略（fallback 到無記憶模式） |
| Agent Skills 格式不相容 | SOP 無法載入 | RC4 API 嚴格測試、FileAgentSkillsProvider 驗證 |
| LLM Token 消耗過高 | 成本超標 | 記憶注入 token 預算控制、摘要壓縮、分層載入 |

## 效能目標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 記憶檢索延遲 | < 500ms (P95) | 新對話開始時的記憶注入 |
| RAG 檢索延遲 | < 1s (P95) | search_knowledge() 調用 |
| 摘要生成延遲 | < 3s | 對話結束時的自動摘要 |
| Retrieval Accuracy | > 85% | RAG 檢索準確率 |
| Answer Relevance | > 80% | 知識庫回答相關性 |
| 跨 Session 記憶命中率 | > 90% | 相關記憶正確召回 |
| SSE 串流首 Token | < 500ms | 端到端響應速度 |

## 成功標準

- [ ] 對話結束時自動生成摘要並寫入 mem0 Long-term Memory
- [ ] 新對話開始時自動檢索並注入相關歷史記憶
- [ ] search_memory() 支援語義搜索、時間範圍、用戶篩選
- [ ] 三層記憶 (Working → Session → Long-term) 自動提升機制運作正常
- [ ] RAG Pipeline 完整運作：解析 → Chunking → Embedding → 索引 → 檢索 → Reranking
- [ ] search_knowledge() function tool 被 Orchestrator 正確自主調用
- [ ] ITIL SOP Agent Skills 正確載入並可查詢
- [ ] 知識庫管理 UI 可上傳文檔、查看索引狀態、執行搜索測試
- [ ] 完整 10 步端到端流程可成功執行
- [ ] 跨 session 記憶持續性驗證通過
- [ ] RAG retrieval accuracy > 85%
- [ ] 效能指標達標（記憶檢索 < 500ms、RAG < 1s）
- [ ] 系統架構文檔、部署指南、使用者手冊完成
- [ ] V9 代碼庫分析報告產出

---

**Phase 38 狀態**: ✅ 完成
**總 Story Points**: ~38 pts
**前置條件**: Phase 37 (E2E Assembly B) ✅ 完成
