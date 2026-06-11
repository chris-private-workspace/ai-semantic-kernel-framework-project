# Sprint 101 技術決策

## 決策記錄

### D101-1: 事件類型設計 (待確認)

**日期**: 2026-01-29

**決策**: 使用 Python dataclasses 定義事件 payload

**原因**:
1. 與 Sprint 100 的數據模型保持一致
2. 提供類型安全和 IDE 支持
3. 易於序列化為 JSON

---

### D101-2: 事件節流策略 (待確認)

**日期**: 2026-01-29

**決策**:
- 節流間隔: 200ms
- 批量發送閾值: 5 事件

**優先級事件 (立即發送)**:
- `swarm_created`
- `swarm_completed`
- `worker_started`
- `worker_completed`
- `worker_tool_call`

**節流事件**:
- `swarm_status_update`
- `worker_progress`
- `worker_thinking`

**原因**:
1. 優先級事件是關鍵狀態變化，需要立即通知
2. 進度類事件頻率高，節流可減少網路負載
3. 200ms 間隔在視覺上感知為實時，同時避免過度更新

---

### D101-3: SSE 事件格式 (待確認)

**日期**: 2026-01-29

**決策**: 使用 AG-UI CustomEvent 格式

**格式**:
```json
{
  "type": "CUSTOM",
  "event_name": "swarm_created",
  "payload": { ... }
}
```

**原因**:
1. 與現有 AG-UI 事件系統一致
2. 前端已有處理 CustomEvent 的基礎設施
3. 不需要額外的事件解析邏輯

---

## 待決策事項

### P101-1: 事件持久化

**問題**: 是否需要持久化事件到數據庫？

**選項**:
1. 不持久化 - 事件只在記憶體中傳遞
2. 持久化到 Redis - 支持短期重放
3. 持久化到 PostgreSQL - 支持長期審計

**傾向**: 選項 1 (不持久化)，在 Phase 29 保持簡單

---

### P101-2: 斷線重連策略

**問題**: 前端 SSE 斷線後如何恢復狀態？

**選項**:
1. 重新連接後調用 REST API 獲取完整狀態
2. 服務端保留最近 N 個事件，重連時重放
3. 混合策略

**傾向**: 選項 1，利用已有的 REST API

---

## 參考文檔

- Sprint 101 計劃: `docs/03-implementation/sprint-planning/phase-29/sprint-101-plan.md`
- AG-UI 事件系統: `backend/src/integrations/ag_ui/events.py`
- HybridEventBridge: `backend/src/integrations/ag_ui/bridge.py`
