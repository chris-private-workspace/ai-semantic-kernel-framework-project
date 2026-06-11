# Sprint 45 Design Decisions

## 設計決策記錄

### D45-1: ExecutionEvent 事件類型設計

**日期**: 2025-12-23

**背景**: 需要定義統一的執行事件類型，支援 WebSocket 和 SSE 兩種通訊方式

**決策**: 採用枚舉定義事件類型，包含以下分類:
- 內容事件: CONTENT, CONTENT_DELTA
- 工具事件: TOOL_CALL, TOOL_RESULT, APPROVAL_REQUIRED, APPROVAL_RESPONSE
- 狀態事件: STARTED, DONE, ERROR
- 系統事件: HEARTBEAT

**理由**:
1. 清晰的事件分類便於處理
2. 支援串流 (delta) 和完整內容兩種模式
3. 審批流程需要專門的事件類型

---

### D45-2: AgentExecutor 統一介面

**日期**: 2025-12-23

**背景**: Workflow 和 Session 模式都需要執行 Agent，需要統一介面

**決策**:
- AgentExecutor 提供 `execute()` 方法，返回 `AsyncIterator[ExecutionEvent]`
- 支援 `stream=True/False` 參數控制串流模式
- 內部封裝 LLM 調用和工具處理

**理由**:
1. 統一介面減少重複代碼
2. 串流模式提供更好的用戶體驗
3. 事件驅動設計支援各種回應格式

---

### D45-3: 工具調用累積策略

**日期**: 2025-12-23

**背景**: Azure OpenAI 串流模式下，工具調用以 delta 形式返回

**決策**:
- 使用 `_accumulate_tool_call()` 方法累積工具調用 delta
- 完整的工具調用在串流結束後一次性發送 TOOL_CALL 事件

**理由**:
1. 工具調用需要完整參數才能執行
2. 累積策略確保數據完整性
3. 與 OpenAI API 行為一致

---

### D45-4: Token 計數策略

**日期**: 2025-12-23

**背景**: 需要追蹤 Token 使用量用於監控和成本控制

**決策**:
- 使用 tiktoken 庫進行本地估算
- 在 DONE 事件中包含 usage 信息
- 估算值用於監控，不用於計費

**理由**:
1. 本地估算避免額外 API 調用
2. tiktoken 與 OpenAI 計數一致
3. 估算值足夠用於監控目的

---

## 待決策事項

無

---

**更新日期**: 2025-12-23
