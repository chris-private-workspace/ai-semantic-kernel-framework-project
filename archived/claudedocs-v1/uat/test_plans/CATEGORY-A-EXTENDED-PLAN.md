# 類別 A：擴展現有 IT Ticket 測試計劃

> **建立日期**: 2025-12-19
> **優先級**: P1 (最高)
> **預估工作量**: 2-3 小時
> **目標覆蓋率提升**: 44% → 62%

---

## 測試目標

在現有的 IT Ticket 生命週期測試 (`it_ticket_lifecycle_test.py`) 基礎上，
完整驗證以下 9 個部分驗證/未驗證的功能。

---

## 功能詳細說明

### 功能 #1: Multi-turn Conversation Sessions (完全驗證)

**原狀態**: 🔶 部分驗證 (Phase 6 使用 GroupChat 但未驗證 session persistence)

**擴展內容**:
- 驗證 `MultiTurnAdapter` session 建立
- 測試 session state persistence (跨 turn 保持狀態)
- 驗證 session resume 功能

**API 端點**:
```
POST /api/v1/groupchat/sessions           # 建立 session
GET  /api/v1/groupchat/sessions/{id}      # 獲取 session 狀態
POST /api/v1/groupchat/sessions/{id}/turn # 添加對話 turn
```

**驗證點**:
- [ ] Session ID 正確生成
- [ ] 對話歷史正確累積
- [ ] Session state 可恢復

---

### 功能 #14: HITL with Escalation (完全驗證)

**原狀態**: 🔶 部分驗證 (測試 checkpoint 但未測試超時升級)

**擴展內容**:
- 設定短超時時間 (5 秒)
- 等待超時觸發
- 驗證 `ApprovalStatus.ESCALATED` 狀態

**API 端點**:
```
POST /api/v1/checkpoints/                 # 建立 checkpoint
GET  /api/v1/checkpoints/{id}             # 獲取狀態 (應為 ESCALATED)
```

**驗證點**:
- [ ] 超時後狀態變為 ESCALATED
- [ ] 升級通知正確發送
- [ ] 升級後仍可審批

---

### 功能 #17: Voting System (完全驗證)

**原狀態**: 🔶 部分驗證 (GroupChat 使用但未驗證投票機制)

**擴展內容**:
- 使用 `GroupChatVotingAdapter` 創建投票 session
- 配置 `VotingMethod.MAJORITY` (多數決)
- 驗證投票結果計算

**API 端點**:
```
POST /api/v1/groupchat/voting/sessions    # 建立投票 session
POST /api/v1/groupchat/voting/vote        # 提交投票
GET  /api/v1/groupchat/voting/result      # 獲取結果
```

**驗證點**:
- [ ] 投票正確累計
- [ ] 多數決正確判定
- [ ] 投票結果包含 tallies

---

### 功能 #20: Decompose Complex Tasks

**原狀態**: ❌ 未驗證

**測試內容**:
- 使用 `PlanningAdapter` 的任務分解功能
- 將複雜 IT 票單分解為子任務
- 驗證分解結果結構

**API 端點**:
```
POST /api/v1/planning/decompose
{
    "task": "處理用戶無法登入問題",
    "context": { "ticket_id": "...", "priority": "high" }
}
```

**驗證點**:
- [ ] 返回子任務列表
- [ ] 每個子任務有明確的 action 和 description
- [ ] 子任務之間有正確的依賴關係

---

### 功能 #21: Plan Step Generation

**原狀態**: ❌ 未驗證

**測試內容**:
- 配合 #20 的分解結果生成執行計劃
- 驗證計劃步驟的完整性
- 測試計劃的可執行性

**API 端點**:
```
POST /api/v1/planning/plans
{
    "goal": "解決用戶登入問題",
    "subtasks": [...],  # 來自 decompose 的結果
    "constraints": { "max_steps": 10 }
}
```

**驗證點**:
- [ ] 返回有序的步驟列表
- [ ] 每步驟有 action, expected_outcome
- [ ] 計劃包含完成條件

---

### 功能 #35: Redis LLM Caching (完全驗證)

**原狀態**: 🔶 部分驗證 (使用 cache 但未驗證 hit/miss)

**擴展內容**:
- 發送相同 LLM 請求兩次
- 驗證第一次為 cache miss
- 驗證第二次為 cache hit

**API 端點**:
```
GET  /api/v1/cache/stats                  # 獲取統計
POST /api/v1/cache/get                    # 查詢快取
```

**驗證點**:
- [ ] 統計顯示 hit_count 增加
- [ ] 第二次請求速度明顯更快
- [ ] Cache key 正確生成

---

### 功能 #36: Cache Invalidation (完全驗證)

**原狀態**: 🔶 部分驗證

**擴展內容**:
- 修改票單內容後觸發 cache invalidation
- 驗證舊 cache 被清除
- 驗證新請求重新計算

**API 端點**:
```
POST /api/v1/cache/clear                  # 清除特定 key
DELETE /api/v1/cache/invalidate/{pattern} # 模式清除
```

**驗證點**:
- [ ] 清除後 cache 統計歸零
- [ ] 新請求為 cache miss
- [ ] 模式匹配正確工作

---

### 功能 #39: Checkpoint State Persistence (完全驗證)

**原狀態**: 🔶 部分驗證 (建立 checkpoint 但未測試恢復)

**擴展內容**:
- 建立 checkpoint 並記錄狀態
- 模擬系統重啟
- 驗證 checkpoint 狀態正確恢復

**API 端點**:
```
POST /api/v1/checkpoints/                 # 建立
GET  /api/v1/checkpoints/{id}             # 獲取 (驗證 persistence)
POST /api/v1/checkpoints/{id}/restore     # 恢復
```

**驗證點**:
- [ ] Checkpoint 資料持久化到資料庫
- [ ] 重新讀取資料正確
- [ ] 執行上下文完整恢復

---

### 功能 #49: Graceful Shutdown (完全驗證)

**原狀態**: 🔶 部分驗證 (有清理但未測試中斷恢復)

**擴展內容**:
- 在執行中途模擬中斷
- 驗證狀態已保存
- 驗證可從中斷點恢復

**測試方式**:
```python
# 模擬中斷
async with timeout(2.0):
    await long_running_workflow()
# 驗證狀態
state = await get_workflow_state(workflow_id)
assert state.status == "interrupted"
# 恢復執行
await resume_workflow(workflow_id)
```

**驗證點**:
- [ ] 中斷狀態正確記錄
- [ ] 進度保存到最後完成的步驟
- [ ] 恢復後從中斷點繼續

---

## 測試執行流程

```
Phase 2.5 (新增): Task Decomposition
  ├─ 調用 /planning/decompose (#20)
  ├─ 調用 /planning/plans (#21)
  └─ 驗證計劃結構

Phase 5 (擴展): Checkpoint with Escalation
  ├─ 建立 checkpoint 並設定 5 秒超時
  ├─ 等待 6 秒
  ├─ 驗證 ESCALATED 狀態 (#14)
  ├─ 驗證 state persistence (#39)
  └─ 測試 resume 功能

Phase 6 (擴展): GroupChat with Full Verification
  ├─ 建立 MultiTurn session (#1)
  ├─ 執行投票決策 (#17)
  └─ 驗證 session persistence

Phase 6.5 (新增): Cache Verification
  ├─ 發送相同請求兩次 (#35)
  ├─ 驗證 cache hit
  ├─ 修改票單
  └─ 驗證 cache invalidation (#36)

Phase 7 (新增): Graceful Shutdown
  ├─ 啟動長時間工作流
  ├─ 模擬中斷
  ├─ 驗證狀態保存
  └─ 恢復並完成 (#49)
```

---

## 預期結果

| 功能 | 驗證前狀態 | 驗證後狀態 |
|-----|-----------|-----------|
| #1 Multi-turn | 🔶 部分 | ✅ 完全 |
| #14 HITL escalation | 🔶 部分 | ✅ 完全 |
| #17 Voting | 🔶 部分 | ✅ 完全 |
| #20 Decompose | ❌ 未驗證 | ✅ 完全 |
| #21 Plan steps | ❌ 未驗證 | ✅ 完全 |
| #35 Redis cache | 🔶 部分 | ✅ 完全 |
| #36 Cache invalidation | 🔶 部分 | ✅ 完全 |
| #39 Checkpoint persist | 🔶 部分 | ✅ 完全 |
| #49 Graceful shutdown | 🔶 部分 | ✅ 完全 |

---

**測試腳本**: `scripts/uat/category_a_extended/it_ticket_extended_test.py`
