# 類別 B：批次處理並行場景測試計劃

> **建立日期**: 2025-12-19
> **優先級**: P2
> **預估工作量**: 3-4 小時
> **目標覆蓋率提升**: 62% → 74%

---

## 測試目標

建立新的「批次票單處理」場景，驗證並行執行、分支管理和錯誤隔離功能。

---

## 測試場景描述

### 場景：批次 IT 票單處理

**背景**: IT 支援團隊需要同時處理多張類似的票單，系統應能並行處理以提高效率。

**業務流程**:
1. 接收 3-5 張待處理票單
2. 並行執行分類 (Fan-out)
3. 並行執行初步診斷
4. 匯總結果 (Fan-in)
5. 生成批次處理報告

---

## 功能詳細說明

### 功能 #15: Concurrent Execution

**原狀態**: ❌ 未驗證

**測試內容**:
- 使用 `ConcurrentBuilderAdapter` 並行處理多張票單
- 驗證並行執行的效能提升
- 確認所有票單都被正確處理

**API 端點**:
```
POST /api/v1/concurrent/execute
{
    "mode": "parallel",
    "tasks": [
        {"ticket_id": "TKT-001", "action": "classify"},
        {"ticket_id": "TKT-002", "action": "classify"},
        {"ticket_id": "TKT-003", "action": "classify"}
    ],
    "max_concurrency": 3
}
```

**驗證點**:
- [ ] 所有任務並行啟動
- [ ] 總執行時間 < 單一任務時間 × 任務數
- [ ] 每個任務結果獨立返回

---

### 功能 #22: Parallel Branch Management

**原狀態**: ❌ 未驗證

**測試內容**:
- 同時執行分類和初步診斷兩個分支
- 管理分支狀態
- 驗證分支間獨立性

**API 端點**:
```
POST /api/v1/concurrent/execute
{
    "mode": "parallel_branches",
    "branches": [
        {"name": "classification", "executor": "classifier_agent"},
        {"name": "diagnosis", "executor": "diagnostic_agent"}
    ]
}

GET /api/v1/concurrent/{id}/branches
```

**驗證點**:
- [ ] 兩個分支同時啟動
- [ ] 可獨立查詢每個分支狀態
- [ ] 分支結果互不影響

---

### 功能 #23: Fan-out/Fan-in Pattern

**原狀態**: ❌ 未驗證

**測試內容**:
- Fan-out: 將單一任務分發到多個 Agent
- Fan-in: 彙總所有 Agent 的結果
- 驗證結果合併邏輯

**API 端點**:
```
POST /api/v1/concurrent/execute
{
    "mode": "fan_out_fan_in",
    "input": {"ticket_id": "TKT-001", "data": "..."},
    "fan_out_agents": [
        "network_analyzer",
        "security_scanner",
        "performance_checker"
    ],
    "aggregation_strategy": "merge_all"
}
```

**驗證點**:
- [ ] 輸入正確分發到所有 Agent
- [ ] 每個 Agent 獨立分析
- [ ] 結果正確彙總

---

### 功能 #24: Branch Timeout Handling

**原狀態**: ❌ 未驗證

**測試內容**:
- 設定分支超時時間
- 驗證超時分支正確處理
- 確認未超時分支繼續執行

**API 端點**:
```
POST /api/v1/concurrent/execute
{
    "mode": "parallel_branches",
    "branches": [
        {"name": "fast_task", "timeout": 5000},
        {"name": "slow_task", "timeout": 2000}  # 會超時
    ],
    "on_timeout": "continue_others"
}
```

**驗證點**:
- [ ] 超時分支標記為 TIMEOUT
- [ ] 其他分支繼續執行
- [ ] 超時不影響最終彙總

---

### 功能 #25: Error Isolation in Branches

**原狀態**: ❌ 未驗證

**測試內容**:
- 模擬某個分支發生錯誤
- 驗證錯誤被隔離
- 其他分支正常完成

**API 端點**:
```
POST /api/v1/concurrent/execute
{
    "mode": "parallel_branches",
    "branches": [
        {"name": "normal_task"},
        {"name": "failing_task", "simulate_error": true}
    ],
    "error_policy": "isolate"
}
```

**驗證點**:
- [ ] 錯誤分支標記為 FAILED
- [ ] 錯誤訊息被記錄
- [ ] 正常分支不受影響
- [ ] 部分結果仍可使用

---

### 功能 #28: Nested Workflow Context

**原狀態**: ❌ 未驗證

**測試內容**:
- 在批次處理中嵌套子工作流
- 驗證上下文正確傳遞
- 確認子工作流可存取父級資料

**API 端點**:
```
POST /api/v1/nested/sub-workflows/execute
{
    "parent_workflow_id": "batch-001",
    "sub_workflow": {
        "name": "detailed_diagnosis",
        "inherit_context": true
    },
    "context_propagation": "full"
}
```

**驗證點**:
- [ ] 子工作流正確啟動
- [ ] 父級上下文可存取
- [ ] 子工作流結果回傳父級

---

## 測試執行流程

```
Phase 1: Setup Batch
  ├─ 創建 3 張測試票單
  └─ 初始化並行執行器

Phase 2: Concurrent Classification (#15)
  ├─ 並行分類 3 張票單
  ├─ 記錄執行時間
  └─ 驗證效能提升

Phase 3: Parallel Branches (#22)
  ├─ 啟動分類分支
  ├─ 啟動診斷分支
  └─ 驗證分支獨立性

Phase 4: Fan-out/Fan-in (#23)
  ├─ 分發到 3 個分析 Agent
  ├─ 等待所有結果
  └─ 彙總分析報告

Phase 5: Timeout & Error Handling (#24, #25)
  ├─ 設定短超時分支
  ├─ 模擬錯誤分支
  └─ 驗證隔離機制

Phase 6: Nested Context (#28)
  ├─ 啟動子工作流
  ├─ 傳遞批次上下文
  └─ 驗證上下文傳遞
```

---

## 預期結果

| 功能 | 驗證前狀態 | 驗證後狀態 |
|-----|-----------|-----------|
| #15 Concurrent execution | ❌ 未驗證 | ✅ 完全 |
| #22 Parallel branches | ❌ 未驗證 | ✅ 完全 |
| #23 Fan-out/Fan-in | ❌ 未驗證 | ✅ 完全 |
| #24 Branch timeout | ❌ 未驗證 | ✅ 完全 |
| #25 Error isolation | ❌ 未驗證 | ✅ 完全 |
| #28 Nested context | ❌ 未驗證 | ✅ 完全 |

---

## 效能基準

| 測試項目 | 預期指標 |
|---------|---------|
| 3 票單並行分類 | < 單一票單時間 × 1.5 |
| Fan-out 到 3 Agent | < 單一 Agent 時間 × 2 |
| 錯誤隔離響應 | < 100ms |
| 超時檢測 | 精確度 ±500ms |

---

**測試腳本**: `scripts/uat/category_b_concurrent/concurrent_batch_test.py`
