# Sprint 126: IT 事件處理場景

## 概述

Sprint 126 實現 Phase 34 的第二個端到端業務場景：IT 事件處理。整合 ServiceNow 事件管理，建立從事件接收、智能分析、建議生成到自動/人工執行的完整流程。預估月節省 ~$4,000。

## 目標

1. 實現 IT 事件接收與分類（ServiceNow Incident → IPA）
2. 實現智能分析與建議生成（LLM 輔助根因分析）
3. 實現自動修復行動（低風險）+ HITL 審批（高風險）
4. 建立事件處理 Dashboard 視圖

## Story Points: 30 點

## 前置條件

- ⬜ Sprint 124-125 完成（n8n + ADF 基礎整合）
- ⬜ ServiceNow MCP Server 已可用（Phase 32 Sprint 117）
- ⬜ 三層路由系統穩定運行

## 任務分解

### Story 126-1: 事件接收與分類 (2 天, P1)

**目標**: ServiceNow Incident Webhook → IPA 意圖分類

**流程**:
```
ServiceNow Incident Created/Updated
  → Webhook 通知 IPA
  → InputGateway 標準化
  → BusinessIntentRouter 分類
    → ITIntentCategory.INCIDENT
    → 子分類: NETWORK / SERVER / APPLICATION / SECURITY / OTHER
```

**交付物**:
- `src/integrations/orchestration/input/incident_handler.py` — 事件輸入處理
- PatternMatcher 新增 IT 事件規則庫（30+ 規則）
- 事件嚴重度評估（P1-P4 映射）

### Story 126-2: 智能分析與建議 (3 天, P1)

**目標**: LLM 輔助根因分析，生成修復建議

**交付物**:
- `src/integrations/incident/analyzer.py` — IncidentAnalyzer
- `src/integrations/incident/recommender.py` — ActionRecommender

**分析流程**:
```
Incident Data
  → 歷史事件比對（Correlation）
  → LLM 根因分析
  → 知識庫查詢（過去解決方案）
  → 生成建議列表（按信心度排序）
  → 風險評估（RiskAssessor）
  → 低風險: 自動執行
  → 高風險: HITL 審批
```

### Story 126-3: 自動修復與審批 (2 天, P1)

**目標**: 低風險行動自動執行，高風險行動走 HITL 審批

**交付物**:
- `src/integrations/incident/executor.py` — IncidentExecutor
- HITL 審批流程與 ServiceNow 狀態回寫
- 自動修復行動庫（重啟服務、清理日誌、擴展資源）

**自動修復行動庫**:

| 行動 | 風險等級 | 自動/審批 |
|------|---------|----------|
| 重啟應用服務 | LOW | 自動 |
| 清理磁碟空間 | LOW | 自動 |
| 擴展 VM 資源 | MEDIUM | 審批 |
| 網路 ACL 變更 | HIGH | 審批 |
| AD 帳號解鎖 | LOW | 自動 |
| 防火牆規則變更 | CRITICAL | 審批 |

### Story 126-4: 測試與驗證 (1 天, P1)

**測試範圍**:

| 測試檔案 | 範圍 |
|----------|------|
| `test_incident_handler.py` | 事件接收與分類 |
| `test_incident_analyzer.py` | 根因分析邏輯 |
| `test_incident_recommender.py` | 建議生成與排序 |
| `test_incident_executor.py` | 自動修復與審批流程 |
| `test_incident_e2e.py` | 端到端事件處理 |

## 業務價值

| 指標 | 目前 | 目標 |
|------|------|------|
| 平均事件處理時間 | 45 min | 10 min |
| 人工介入率 | 100% | 30%（高風險才需審批） |
| 月處理事件量 | ~200 | ~200（自動處理 140+） |
| 預估月節省 | $0 | ~$4,000 |

## 依賴

- 改善提案 Phase D P1: IT 事件處理場景
- ServiceNow MCP Server（Phase 32）
- RiskAssessor（Phase 28）
- HITLController（Phase 28）
