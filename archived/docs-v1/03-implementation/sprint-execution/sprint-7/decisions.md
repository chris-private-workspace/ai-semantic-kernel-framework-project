# Sprint 7: 並行執行引擎 - Decisions Log

**Sprint 目標**: 實現多 Agent 並行執行能力
**紀錄用途**: 追蹤 Sprint 中的重要技術決策和架構選擇

---

## 決策記錄

### DEC-S7-001: 並行執行模式設計

**日期**: 2025-12-05
**狀態**: ✅ 決定

**背景**:
需要支援多種並行執行策略以滿足不同業務場景需求。

**決策**:
採用 4 種並行模式:
1. `ALL` - 等待所有任務完成
2. `ANY` - 任一任務完成即返回
3. `MAJORITY` - 多數任務完成即返回
4. `FIRST_SUCCESS` - 第一個成功的任務

**理由**:
- 涵蓋常見並行場景
- 與 Agent Framework 設計一致
- 提供靈活的執行策略選擇

**影響**:
- ConcurrentExecutor 需實現所有 4 種模式
- API 需支援模式配置

---

### DEC-S7-002: 死鎖檢測算法選擇

**日期**: 2025-12-05
**狀態**: ✅ 決定

**背景**:
並行執行可能產生循環依賴導致死鎖。

**決策**:
採用等待圖 (Wait-for Graph) + DFS 循環檢測算法

**理由**:
- 算法成熟可靠
- 時間複雜度 O(V+E) 可接受
- 可清楚識別死鎖循環路徑

**影響**:
- DeadlockDetector 實現基於圖論算法
- 需要維護任務等待關係

---

### DEC-S7-003: Gateway 合併策略

**日期**: 2025-12-05
**狀態**: ✅ 決定

**背景**:
並行分支結果需要合併傳遞給下游節點。

**決策**:
支援 4 種合併策略:
1. `COLLECT_ALL` - 收集所有結果為列表
2. `MERGE_DICT` - 合併為字典
3. `FIRST_RESULT` - 取第一個結果
4. `AGGREGATE` - 自定義聚合函數

**理由**:
- 不同場景需要不同合併方式
- 提供擴展性 (自定義聚合)
- 與 Join Strategy 配合使用

---

### DEC-S7-004: Concurrent API 架構設計

**日期**: 2025-12-05
**狀態**: ✅ 決定

**背景**:
需要設計 REST API 和 WebSocket 支援並行執行監控和控制。

**決策**:
1. RESTful API:
   - POST /concurrent/execute - 創建並行執行
   - GET /concurrent/{id}/status - 查詢執行狀態
   - GET /concurrent/{id}/branches - 列出所有分支
   - POST /concurrent/{id}/cancel - 取消執行
   - GET /concurrent/stats - 統計數據

2. WebSocket:
   - ws://concurrent/ws/{execution_id} - 監控特定執行
   - 支援 11 種事件類型

**理由**:
- RESTful 設計符合現有 API 風格
- WebSocket 提供實時更新能力
- 分離關注點: 執行控制 vs 狀態監控

**影響**:
- 需要 ConnectionManager 管理 WebSocket 連接
- 需要事件發布機制
- API Router 註冊到 v1 模組

---

### DEC-S7-005: 死鎖解決策略

**日期**: 2025-12-05
**狀態**: ✅ 決定

**背景**:
檢測到死鎖後需要決定如何解決。

**決策**:
提供 5 種解決策略:
1. `CANCEL_YOUNGEST` - 取消最新加入的任務
2. `CANCEL_OLDEST` - 取消最早的任務
3. `CANCEL_ALL` - 取消所有死鎖任務
4. `CANCEL_LOWEST_PRIORITY` - 取消最低優先級任務
5. `NOTIFY_ONLY` - 僅通知，不自動解決

**理由**:
- 不同場景需要不同解決方式
- 預設策略: CANCEL_YOUNGEST (影響最小)
- NOTIFY_ONLY 保留人工介入選項

---

## 待決策事項

<!-- 記錄需要討論或決定的事項 -->

- 暫無

---

## 相關連結

- [Sprint 7 Plan](../../sprint-planning/phase-2/sprint-7-plan.md)
- [Progress Log](./progress.md)
