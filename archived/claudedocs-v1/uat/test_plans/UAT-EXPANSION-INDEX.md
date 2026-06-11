# UAT 測試擴展主索引

> **建立日期**: 2025-12-19
> **目的**: 管理和追蹤 UAT 測試擴展計劃，將覆蓋率從 44% 提升至 100%

---

## 測試分類總覽

| 類別 | 描述 | 功能數 | 狀態 | 文件夾 |
|-----|------|-------|-----|-------|
| **A** | 擴展現有 IT Ticket 測試 | 9 | 🔲 待實現 | `category_a_extended/` |
| **B** | 新增批次處理子場景 | 6 | 🔲 待實現 | `category_b_concurrent/` |
| **C** | 獨立進階測試場景 | 4 | 🔲 待實現 | `category_c_advanced/` |

---

## 類別 A：擴展現有 IT Ticket 測試

**目標**: 在現有 IT Ticket 生命週期測試中完整驗證部分測試的功能

**測試計劃文件**: [CATEGORY-A-EXTENDED-PLAN.md](./CATEGORY-A-EXTENDED-PLAN.md)

**測試腳本**: `scripts/uat/category_a_extended/it_ticket_extended_test.py`

### 包含功能 (9 個)

| # | 功能 | 原狀態 | 擴展方式 |
|---|-----|-------|---------|
| #1 | Multi-turn conversation sessions | 🔶 部分 | Phase 6 添加 session persistence |
| #14 | HITL with escalation | 🔶 部分 | Phase 5 添加超時升級測試 |
| #17 | Voting system | 🔶 部分 | Phase 6 使用真實投票決策 |
| #20 | Decompose complex tasks | ❌ 未驗證 | Phase 2 觸發任務分解 |
| #21 | Plan step generation | ❌ 未驗證 | 配合 #20 生成處理計劃 |
| #35 | Redis LLM caching | 🔶 部分 | 添加 cache hit/miss 驗證 |
| #36 | Cache invalidation | 🔶 部分 | 測試票單修改後 cache 失效 |
| #39 | Checkpoint state persistence | 🔶 部分 | Phase 5 驗證狀態恢復 |
| #49 | Graceful shutdown | 🔶 部分 | 添加中斷恢復測試 |

---

## 類別 B：批次處理並行場景

**目標**: 驗證並行執行、分支管理和錯誤隔離功能

**測試計劃文件**: [CATEGORY-B-CONCURRENT-PLAN.md](./CATEGORY-B-CONCURRENT-PLAN.md)

**測試腳本**: `scripts/uat/category_b_concurrent/concurrent_batch_test.py`

### 包含功能 (6 個)

| # | 功能 | 原狀態 | 測試場景 |
|---|-----|-------|---------|
| #15 | Concurrent execution | ❌ 未驗證 | 批次處理多張票單 |
| #22 | Parallel branch management | ❌ 未驗證 | 同時處理分類+初步診斷 |
| #23 | Fan-out/Fan-in pattern | ❌ 未驗證 | 多 Agent 並行分析後彙總 |
| #24 | Branch timeout handling | ❌ 未驗證 | 設定並行分支超時 |
| #25 | Error isolation in branches | ❌ 未驗證 | 某分支失敗不影響其他 |
| #28 | Nested workflow context | ❌ 未驗證 | 嵌套子流程上下文傳遞 |

---

## 類別 C：獨立進階測試場景

**目標**: 測試與 IT Ticket 場景關聯較弱的進階功能

**測試計劃文件**: [CATEGORY-C-ADVANCED-PLAN.md](./CATEGORY-C-ADVANCED-PLAN.md)

**測試腳本**: `scripts/uat/category_c_advanced/advanced_workflow_test.py`

### 包含功能 (4 個)

| # | 功能 | 原狀態 | 獨立測試場景 |
|---|-----|-------|------------|
| #26 | Sub-workflow composition | ❌ 未驗證 | 文件審批流程場景 |
| #27 | Recursive execution | ❌ 未驗證 | 問題根因分析遞迴場景 |
| #34 | External connector updates | ❌ 未驗證 | ServiceNow 同步場景 |
| #37 | Message prioritization | ❌ 未驗證 | 緊急事件處理場景 |

---

## 實現優先順序

| 優先級 | 類別 | 功能數 | 預估工作量 | 預期覆蓋率提升 |
|-------|------|-------|-----------|--------------|
| **P1** | A | 9 | 2-3 小時 | 44% → 62% |
| **P2** | B | 6 | 3-4 小時 | 62% → 74% |
| **P3** | C | 4 | 2-3 小時 | 74% → 82% |

---

## API 端點參考

### 類別 A 相關 API
```
POST /api/v1/planning/decompose       # 任務分解
POST /api/v1/planning/plans           # 計劃生成
POST /api/v1/checkpoints/             # Checkpoint 管理
GET  /api/v1/cache/stats              # Cache 統計
POST /api/v1/groupchat/sessions       # GroupChat sessions
```

### 類別 B 相關 API
```
POST /api/v1/concurrent/execute       # 並行執行
GET  /api/v1/concurrent/{id}/status   # 並行狀態
GET  /api/v1/concurrent/{id}/branches # 分支狀態
POST /api/v1/nested/sub-workflows/execute  # 嵌套工作流
```

### 類別 C 相關 API
```
POST /api/v1/nested/compositions      # 工作流組合
POST /api/v1/nested/recursive/execute # 遞迴執行
PUT  /api/v1/connectors/{id}/sync     # 連接器同步
POST /api/v1/routing/prioritize       # 消息優先級
```

---

## 測試執行指南

### 執行單一類別
```bash
cd scripts/uat

# 類別 A
python category_a_extended/it_ticket_extended_test.py

# 類別 B
python category_b_concurrent/concurrent_batch_test.py

# 類別 C
python category_c_advanced/advanced_workflow_test.py
```

### 執行全部擴展測試
```bash
cd scripts/uat
python -m pytest category_a_extended/ category_b_concurrent/ category_c_advanced/ -v
```

---

## 進度追蹤

### 類別 A 進度
- [ ] 測試計劃完成
- [ ] 測試腳本完成
- [ ] 測試執行通過
- [ ] 結果記錄

### 類別 B 進度
- [ ] 測試計劃完成
- [ ] 測試腳本完成
- [ ] 測試執行通過
- [ ] 結果記錄

### 類別 C 進度
- [ ] 測試計劃完成
- [ ] 測試腳本完成
- [ ] 測試執行通過
- [ ] 結果記錄

---

**最後更新**: 2025-12-19
