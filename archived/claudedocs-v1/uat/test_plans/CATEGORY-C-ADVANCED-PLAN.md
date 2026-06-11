# 類別 C：獨立進階測試場景計劃

> **建立日期**: 2025-12-19
> **優先級**: P3
> **預估工作量**: 2-3 小時
> **目標覆蓋率提升**: 74% → 82%

---

## 測試目標

建立獨立測試場景，驗證與 IT Ticket 場景關聯較弱的進階功能。

---

## 測試場景概覽

| 場景 | 功能 | 描述 |
|-----|------|------|
| 文件審批流程 | #26 | Sub-workflow composition |
| 問題根因分析 | #27 | Recursive execution |
| ServiceNow 同步 | #34 | External connector updates |
| 緊急事件處理 | #37 | Message prioritization |

---

## 功能詳細說明

### 功能 #26: Sub-workflow Composition

**原狀態**: ❌ 未驗證

**測試場景**: 文件審批流程

**場景描述**:
一個文件需要經過多個部門的審批，每個部門的審批是一個子工作流，
最終組合成完整的審批流程。

**業務流程**:
```
主工作流: 文件審批
├── 子工作流 1: 部門主管審批
├── 子工作流 2: 財務審核
├── 子工作流 3: 法務審查
└── 組合結果 → 最終決策
```

**API 端點**:
```
POST /api/v1/nested/compositions
{
    "composition_name": "document_approval",
    "sub_workflows": [
        {"name": "manager_approval", "type": "sequential"},
        {"name": "finance_review", "type": "parallel"},
        {"name": "legal_review", "type": "parallel"}
    ],
    "composition_strategy": "all_required"
}
```

**驗證點**:
- [ ] 子工作流正確組合
- [ ] 各子工作流獨立執行
- [ ] 組合策略正確應用
- [ ] 最終結果正確彙總

---

### 功能 #27: Recursive Execution

**原狀態**: ❌ 未驗證

**測試場景**: 問題根因分析 (5 Whys)

**場景描述**:
使用遞迴方式分析問題的根本原因，每次分析可能觸發更深層的分析，
直到找到根本原因或達到最大遞迴深度。

**業務流程**:
```
問題: 系統響應緩慢
├── Why 1: 為什麼響應緩慢? → 資料庫查詢慢
│   ├── Why 2: 為什麼查詢慢? → 缺少索引
│   │   ├── Why 3: 為什麼缺少索引? → 新功能未優化
│   │   │   ├── Why 4: 為什麼未優化? → 開發時間緊迫
│   │   │   │   └── Why 5: 根因 → 需求變更太頻繁
```

**API 端點**:
```
POST /api/v1/nested/recursive/execute
{
    "workflow_name": "root_cause_analysis",
    "initial_input": {
        "problem": "系統響應緩慢",
        "context": {...}
    },
    "recursion_config": {
        "max_depth": 5,
        "termination_condition": "root_cause_found",
        "continue_on_partial": true
    }
}
```

**驗證點**:
- [ ] 遞迴正確執行
- [ ] 深度限制有效
- [ ] 終止條件正確觸發
- [ ] 遞迴路徑可追蹤

---

### 功能 #34: External Connector Updates

**原狀態**: ❌ 未驗證

**測試場景**: ServiceNow 同步

**場景描述**:
測試與外部系統 (ServiceNow) 的連接器更新功能，
確保狀態變更可正確同步到外部系統。

**業務流程**:
```
IPA 票單狀態變更
    ↓
觸發 ServiceNow 連接器
    ↓
同步狀態到 ServiceNow
    ↓
確認同步成功
```

**API 端點**:
```
PUT /api/v1/connectors/servicenow/sync
{
    "connector_id": "servicenow-prod",
    "sync_data": {
        "ticket_id": "TKT-001",
        "status": "resolved",
        "resolution": "重置密碼後解決"
    },
    "options": {
        "retry_on_failure": true,
        "max_retries": 3
    }
}
```

**驗證點**:
- [ ] 連接器正確觸發
- [ ] 資料格式轉換正確
- [ ] 同步狀態可追蹤
- [ ] 失敗重試機制有效

---

### 功能 #37: Message Prioritization

**原狀態**: ❌ 未驗證

**測試場景**: 緊急事件處理

**場景描述**:
測試消息優先級處理，確保高優先級的緊急事件
能夠優先處理，不被低優先級任務阻塞。

**業務流程**:
```
消息隊列:
├── 低優先級: 一般查詢 (priority: 1)
├── 中優先級: 功能請求 (priority: 5)
├── 高優先級: 系統告警 (priority: 8)
└── 緊急: 安全事件 (priority: 10) ← 優先處理
```

**API 端點**:
```
POST /api/v1/routing/prioritize
{
    "messages": [
        {"id": "msg-1", "content": "一般查詢", "priority": 1},
        {"id": "msg-2", "content": "功能請求", "priority": 5},
        {"id": "msg-3", "content": "安全事件", "priority": 10}
    ],
    "strategy": "highest_first",
    "preempt": true
}

GET /api/v1/routing/queue/status
```

**驗證點**:
- [ ] 優先級正確排序
- [ ] 高優先級優先處理
- [ ] 搶占機制有效
- [ ] 低優先級不會餓死

---

## 測試執行流程

```
Scenario 1: Document Approval (#26)
  ├─ 創建審批文件
  ├─ 啟動組合工作流
  ├─ 執行各子工作流
  └─ 驗證組合結果

Scenario 2: Root Cause Analysis (#27)
  ├─ 輸入問題描述
  ├─ 啟動遞迴分析
  ├─ 追蹤遞迴深度
  └─ 驗證根因識別

Scenario 3: ServiceNow Sync (#34)
  ├─ 準備同步資料
  ├─ 觸發連接器
  ├─ 模擬外部響應
  └─ 驗證同步狀態

Scenario 4: Priority Queue (#37)
  ├─ 提交多優先級消息
  ├─ 驗證處理順序
  ├─ 測試搶占機制
  └─ 驗證公平性
```

---

## 預期結果

| 功能 | 驗證前狀態 | 驗證後狀態 |
|-----|-----------|-----------|
| #26 Sub-workflow composition | ❌ 未驗證 | ✅ 完全 |
| #27 Recursive execution | ❌ 未驗證 | ✅ 完全 |
| #34 External connector updates | ❌ 未驗證 | ✅ 完全 |
| #37 Message prioritization | ❌ 未驗證 | ✅ 完全 |

---

## 模擬策略

由於這些功能可能需要外部系統配合，測試將使用以下模擬策略：

| 功能 | 模擬方式 |
|-----|---------|
| #26 | 模擬子工作流執行和結果 |
| #27 | 模擬遞迴分析過程 |
| #34 | 使用 Mock ServiceNow 響應 |
| #37 | 模擬消息隊列和處理順序 |

---

**測試腳本**: `scripts/uat/category_c_advanced/advanced_workflow_test.py`
