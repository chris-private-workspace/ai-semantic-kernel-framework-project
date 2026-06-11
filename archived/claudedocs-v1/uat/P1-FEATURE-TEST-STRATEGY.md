# P1 核心功能測試策略分析
## 5 個待測試功能的實現方案

**分析日期**: 2025-12-19

---

## API 端點支援分析

### 後端 API 已完整支援這 5 個功能

| # | 功能 | API 端點 | 狀態 |
|---|------|---------|------|
| 4 | 跨場景協作 (CS↔IT) | `/routing/route`, `/routing/relations`, `/routing/executions/{id}/chain` | [OK] 可測試 |
| 17 | Collaboration Protocol | `/handoff/*` (協作協議) | [OK] 可測試 |
| 23 | Autonomous Decision | `/planning/decisions`, `/planning/decisions/{id}/approve|reject` | [OK] 可測試 |
| 24 | Trial-and-Error 試錯 | `/planning/trial`, `/planning/trial/insights`, `/planning/trial/recommendations` | [OK] 可測試 |
| 39 | Agent to Agent (A2A) | `/handoff/trigger` (source→target agent) | [OK] 可測試 |

---

## 建議方案：新建 Category D 測試

### 為什麼不整合到現有測試？

| 考量因素 | 整合到現有 | 新建 Category D |
|---------|-----------|----------------|
| **測試焦點** | 會模糊現有測試目的 | 清晰專注於 P1 功能 |
| **複雜度** | 現有測試已有 15+ 階段 | 獨立測試易於維護 |
| **執行時間** | 會拉長現有測試時間 | 可獨立快速執行 |
| **失敗隔離** | 影響現有測試結果 | 不影響已通過測試 |
| **編號一致性** | 需修改大量現有代碼 | 從頭使用正確編號 |

**建議：創建新的 Category D 測試腳本**

---

## Category D 測試設計

### 目錄結構

```
scripts/uat/
├── base.py                          # 基礎類 (現有)
├── it_ticket_integrated_test.py     # Category A (現有)
├── category_b_concurrent/           # Category B (現有)
├── category_c_advanced/             # Category C (現有)
└── category_d_planning/             # Category D (新建)
    ├── __init__.py
    ├── planning_decision_test.py    # P1 測試腳本
    └── test_results_category_d.json
```

### 測試場景設計

```
┌──────────────────────────────────────────────────────────────────────────┐
│              Category D: Planning & Cross-Scenario Test                   │
│                    (5 P1 功能專項測試)                                     │
└──────────────────────────────────────────────────────────────────────────┘

場景 1: 跨場景協作 (#4)
    ├─ Step 1: 建立 IT Operations 場景工單
    ├─ Step 2: 路由到 Customer Service 場景
    ├─ Step 3: 驗證執行鏈 (execution chain)
    └─ Step 4: 驗證關聯關係 (relations)

場景 2: Agent 間通訊 (#39 A2A)
    ├─ Step 1: 建立 Source Agent
    ├─ Step 2: 建立 Target Agent
    ├─ Step 3: 觸發 A2A Handoff
    └─ Step 4: 驗證上下文傳遞

場景 3: 協作協議 (#17)
    ├─ Step 1: 配置協作協議
    ├─ Step 2: 觸發多 Agent 協作
    ├─ Step 3: 驗證協議執行
    └─ Step 4: 驗證協作結果

場景 4: 自主決策 (#23)
    ├─ Step 1: 提交決策請求
    ├─ Step 2: 獲取決策選項
    ├─ Step 3: 審批決策
    └─ Step 4: 驗證決策執行

場景 5: 試錯機制 (#24)
    ├─ Step 1: 啟動試錯執行
    ├─ Step 2: 模擬失敗場景
    ├─ Step 3: 驗證重試機制
    ├─ Step 4: 獲取洞察與建議
    └─ Step 5: 驗證統計資訊
```

---

## 同時需要修正的問題

### Category B 功能編號修正

| 目前使用 | 應該改為 | 說明 |
|---------|---------|------|
| #22 Parallel branch management | 移除或改為描述性 | 主列表 #22 是 Dynamic Planning |
| #23 Fan-out/Fan-in pattern | 移除或改為描述性 | 主列表 #23 是 Autonomous Decision |
| #24 Branch timeout handling | 移除或改為描述性 | 主列表 #24 是 Trial-and-Error |
| #25 Error isolation | 移除或改為描述性 | 主列表 #25 是 Nested Workflows |
| #28 Nested workflow context | 移除或改為描述性 | 主列表 #28 是 投票系統 |

**建議修正方式**: 改為使用描述性標籤，不使用編號：
```python
# Before
features = {
    22: FeatureVerification(22, "Parallel branch management"),
}

# After
features = {
    "B-1": FeatureVerification("B-1", "Parallel branch management"),
    # 註: 此功能不在主列表中，屬於 Category B 特有測試
}
```

### Category C 功能編號修正

| 目前使用 | 應該改為 | 說明 |
|---------|---------|------|
| #37 Message prioritization | 移除或改為描述性 | 主列表 #37 是 主動巡檢模式 |

---

## 實施計劃

### Phase 1: 修正編號不一致 (建議先執行)

1. 更新 `category_b_concurrent/concurrent_batch_test.py`
   - 將錯誤編號改為描述性標籤 (B-1, B-2 等)
   - 添加註解說明與主列表的對應關係

2. 更新 `category_c_advanced/advanced_workflow_test.py`
   - 修正 #37 → C-4 或 "Message prioritization"
   - 確保 #26, #27, #34 正確對應

### Phase 2: 創建 Category D 測試

1. 創建目錄結構
2. 實現 5 個場景的測試代碼
3. 使用正確的功能編號 (#4, #17, #23, #24, #39)
4. 執行測試並驗證

---

## 預估工作量

| 任務 | 複雜度 | 預估時間 |
|------|-------|---------|
| 修正 Category B 編號 | 低 | ~30 分鐘 |
| 修正 Category C 編號 | 低 | ~20 分鐘 |
| 創建 Category D 框架 | 中 | ~1 小時 |
| 實現 5 個測試場景 | 高 | ~3-4 小時 |
| 執行與調試 | 中 | ~1 小時 |
| **總計** | - | **~6-7 小時** |

---

## 決策點

請確認以下選項：

1. **測試組織方式**
   - [ ] A: 創建新的 Category D (推薦)
   - [ ] B: 整合到現有 Category A/B/C

2. **編號修正方式**
   - [ ] A: 使用描述性標籤 (B-1, C-4 等)
   - [ ] B: 完全移除編號，只用功能名稱
   - [ ] C: 保留編號但添加映射表

3. **執行順序**
   - [ ] A: 先修正編號，再創建 Category D
   - [ ] B: 先創建 Category D，後修正編號
   - [ ] C: 同時進行

---

**報告生成**: 2025-12-19
**分析者**: Claude Code
