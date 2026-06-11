# Phase 32: Core Business Scenario + Architecture

## 概述

Phase 32 專注於實現 **第一個端到端業務場景（AD 帳號管理）**，同時進行架構加固。本 Phase 整合了原 Phase 30（Azure AI Search）的 SemanticRouter Mock→Real 遷移工作，以場景驅動方式將平台從「技術展示」提升到「業務價值交付」。

本 Phase 基於 `docs/07-analysis/Overview/IPA-Platform-Improvement-Proposal.md` 中的 Phase B 規劃，是 Phase 31（Security Hardening）完成後的自然延續。

## 目標

1. **AD 帳號管理場景基礎** - PatternMatcher AD 規則庫、LDAP MCP 配置、ServiceNow Webhook
2. **SemanticRouter Real 實現** - Azure AI Search 向量搜索取代 Mock（整合原 Phase 30 Sprint 107-110）
3. **架構加固** - Swarm 整合主流程、Layer 4 拆分、L5-L6 循環依賴修復
4. **Multi-Worker + ServiceNow MCP** - 生產級並發能力 + RITM 回寫
5. **E2E 測試 + 驗收** - AD 場景全流程測試、性能基準、驗收報告

## 前置條件

- ✅ Phase 31 完成（Security Hardening — Auth 100%、Rate Limiting、Mock 分離）
- ✅ Azure OpenAI 已配置（Embedding 模型 text-embedding-ada-002）
- ✅ Azure 訂閱可用（Azure AI Search 資源）
- ✅ LDAP MCP Server 就緒（Phase 前期已建立）
- ✅ ServiceNow 開發實例可用
- ✅ InMemoryApprovalStorage 已遷移至 Redis（Phase 31）

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 114](./sprint-114-plan.md) | AD 場景基礎建設 | 40 點 | 📋 計劃中 |
| [Sprint 115](./sprint-115-plan.md) | SemanticRouter Real 實現 | 45 點 | 📋 計劃中 |
| [Sprint 116](./sprint-116-plan.md) | 架構加固 | 45 點 | 📋 計劃中 |
| [Sprint 117](./sprint-117-plan.md) | Multi-Worker + ServiceNow MCP | 40 點 | 📋 計劃中 |
| [Sprint 118](./sprint-118-plan.md) | E2E 測試 + Phase B 驗收 | 35 點 | 📋 計劃中 |

**總計**: ~205 Story Points (5 Sprints)
**預估時程**: 5 週

> **注意**: Sprint 115 整合了原 Phase 30（Azure AI Search）的 Sprint 107-110 計劃內容。詳細技術規格請參考 `docs/03-implementation/sprint-planning/phase-30/` 目錄下的原始 Sprint 計劃。

## 架構概覽

### AD 帳號管理端到端流程

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                Phase 32: AD 帳號管理 E2E 業務流程                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────────┐  │
│  │  ServiceNow   │    │ InputGateway │    │       BusinessIntentRouter           │  │
│  │  (RITM 事件)  │───▶│ (Webhook     │───▶│                                      │  │
│  │              │    │  Receiver)   │    │  L1: PatternMatcher                  │  │
│  │  • 帳號鎖定   │    │              │    │      └─ AD 規則匹配 (rules.yaml)     │  │
│  │  • 密碼重設   │    │              │    │                                      │  │
│  │  • 群組異動   │    │              │    │  L2: AzureSemanticRouter (🆕 Real)   │  │
│  └──────────────┘    └──────────────┘    │      └─ Azure AI Search 向量搜索     │  │
│                                           │                                      │  │
│                                           │  L3: LLMClassifier                   │  │
│                                           │      └─ Fallback                     │  │
│                                           └─────────────┬────────────────────────┘  │
│                                                         │                            │
│                                                         ▼                            │
│  ┌──────────────────────────────────────────────────────────────────────────────┐    │
│  │                    HybridOrchestratorV2                                       │    │
│  │                                                                              │    │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │    │
│  │   │ Agent 選擇    │───▶│ Agent 執行    │───▶│ MCP 工具調用  │                 │    │
│  │   │ (AD Specialist)│    │ (MAF/Claude) │    │              │                 │    │
│  │   └──────────────┘    └──────────────┘    │  ┌──────────┐│                 │    │
│  │                                            │  │ LDAP MCP ││                 │    │
│  │                                            │  │ • unlock  ││                 │    │
│  │                                            │  │ • reset   ││                 │    │
│  │                                            │  │ • group   ││                 │    │
│  │                                            │  └──────────┘│                 │    │
│  │                                            └──────────────┘                 │    │
│  └──────────────────────────────────────────────────────────────────────────────┘    │
│                                                         │                            │
│                                                         ▼                            │
│  ┌──────────────────────────────────────────────────────────────────────────────┐    │
│  │                    ServiceNow MCP (🆕)                                       │    │
│  │                                                                              │    │
│  │   • update_ritm_status() → 更新 RITM 狀態為已完成                           │    │
│  │   • add_work_notes() → 添加執行記錄                                          │    │
│  │   • close_ritm() → 關閉 RITM                                                │    │
│  └──────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 業務價值

| 指標 | 數值 | 說明 |
|------|------|------|
| **月節省工時** | 137.5 小時 | AD 帳號管理自動化 |
| **月節省成本** | $5,740 | 基於 Business Analyst 估算 |
| **ROI** | +112% | 第一年投資回報率 |
| **投資平衡點** | 第 4 個月 | 累計節省 > 累計投入 |
| **路由覆蓋率** | 95% | 從 60%（Mock）提升到 95%（Real） |

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| azure-search-documents | 11.4+ | Azure AI Search SDK |
| azure-identity | 1.14+ | Azure 身份驗證 |
| openai | 1.10+ | Azure OpenAI Embedding |
| gunicorn | 21.0+ | Multi-Worker WSGI |
| python-ldap | 3.4+ | LDAP 操作 (已有) |
| FastAPI | 0.100+ | 後端框架 |
| Pydantic | 2.0+ | 數據驗證 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Azure AI Search 延遲 | 路由變慢 | 設定 timeout、fallback 到 LLMClassifier |
| ServiceNow API 限制 | Webhook 丟失 | 重試機制、冪等處理 |
| LDAP 連接不穩定 | AD 操作失敗 | 連接池、重試、Circuit Breaker |
| Layer 4 拆分影響範圍 | 回歸問題 | 充分測試、漸進式重構 |
| Multi-Worker 記憶體 | InMemory 不一致 | Phase 31 已遷移 Redis |
| Embedding 成本 | 費用增加 | 快取常用查詢、批次處理 |

## 成功標準

- [ ] AD 帳號管理場景端到端可用
- [ ] ServiceNow RITM → Agent 執行 → RITM 關閉全流程通過
- [ ] AzureSemanticRouter 替代 Mock，搜索延遲 < 100ms (P95)
- [ ] 15 條路由成功遷移至 Azure AI Search
- [ ] Swarm 整合到 execute_with_routing() 主流程
- [ ] Layer 4 拆分完成（L4a Input + L4b Decision）
- [ ] L5-L6 循環依賴消除
- [ ] Multi-Worker Uvicorn 運行正常
- [ ] ServiceNow MCP 6 個核心工具可用
- [ ] E2E 測試通過
- [ ] 性能基準文檔完成

## 回滾計劃

```bash
# SemanticRouter 回滾到 Mock
USE_AZURE_SEARCH=false

# ServiceNow Webhook 停用
SERVICENOW_WEBHOOK_ENABLED=false

# Multi-Worker 回滾到單 Worker
UVICORN_WORKERS=1
```

---

**Phase 32 開始時間**: TBD（Phase 31 完成後）
**預估完成時間**: 5 週
**總 Story Points**: ~205 pts
