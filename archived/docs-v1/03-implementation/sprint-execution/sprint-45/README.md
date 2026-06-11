# Sprint 45: Agent Executor Core

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| **Sprint 編號** | 45 |
| **Phase** | 11 - Agent-Session Integration |
| **名稱** | Agent Executor Core |
| **目標** | 建立統一的 Agent 執行器，整合 LLM 調用與串流支援 |
| **總點數** | 35 Story Points |
| **開始日期** | 2025-12-23 |
| **狀態** | 🔄 進行中 |

---

## User Stories

| Story | 名稱 | 點數 | 優先級 | 狀態 |
|-------|------|------|--------|------|
| S45-1 | AgentExecutor 核心類別 | 13 | P0 | ⏳ 待開始 |
| S45-2 | LLM 串流整合 | 10 | P0 | ⏳ 待開始 |
| S45-3 | 工具調用框架 | 8 | P1 | ⏳ 待開始 |
| S45-4 | 執行事件系統 | 4 | P1 | ⏳ 待開始 |

---

## Story 詳情

### S45-1: AgentExecutor 核心類別 (13 pts)

**描述**: 統一的 Agent 執行介面，支援 Workflow 和 Session 模式共享執行邏輯

**功能需求**:
- AgentExecutor 類別實現
- 支援 Agent 配置載入
- 訊息構建邏輯 (system + history + user)
- 執行事件定義 (ExecutionEvent)
- 同步與非同步執行模式

**交付物**:
- `domain/sessions/executor.py` - AgentExecutor 主類別

---

### S45-2: LLM 串流整合 (10 pts)

**描述**: 串流式 LLM 回應，讓用戶即時看到 Agent 回應

**功能需求**:
- Azure OpenAI 串流調用
- SSE 格式處理
- Token 計數追蹤
- 超時與重試機制
- 錯誤處理與恢復

**交付物**:
- `domain/sessions/streaming.py` - StreamingLLMHandler

---

### S45-3: 工具調用框架 (8 pts)

**描述**: 工具調用處理框架，讓 Agent 可執行 MCP 工具

**功能需求**:
- 工具調用解析
- MCP 工具執行整合
- 工具結果回傳 LLM
- 多輪工具調用支援
- 工具權限檢查

**交付物**:
- `domain/sessions/tool_handler.py` - ToolCallHandler

---

### S45-4: 執行事件系統 (4 pts)

**描述**: 統一的執行事件系統，追蹤和處理執行過程

**功能需求**:
- 事件類型定義完整
- 事件序列化支援
- WebSocket 事件格式
- 事件日誌記錄

**交付物**:
- `domain/sessions/events.py` - ExecutionEvent 系統

---

## 技術規格

### 文件結構

```
backend/src/domain/sessions/
├── __init__.py           # 模組匯出 (更新)
├── events.py             # 執行事件系統 (S45-4)
├── executor.py           # AgentExecutor (S45-1)
├── streaming.py          # StreamingLLMHandler (S45-2)
└── tool_handler.py       # ToolCallHandler (S45-3)
```

### 依賴項

- LLMService (Phase 3)
- Agent domain model (Phase 3)
- MCPClient (Phase 9)
- ToolRegistry (Phase 9)
- SessionService (Phase 10)

### 外部套件

- `openai` >= 1.0 (AsyncAzureOpenAI)
- `tiktoken` >= 0.5 (Token 計數)

---

## 驗收標準

- [ ] AgentExecutor 可正常實例化
- [ ] 訊息構建正確包含 system prompt
- [ ] 串流回應正確生成事件
- [ ] 工具調用正確執行
- [ ] 錯誤正確捕獲和報告
- [ ] 首個 token 回應 < 2秒
- [ ] 測試覆蓋率 > 85%

---

## 相關文檔

- [Sprint 45 Plan](../../sprint-planning/phase-11/sprint-45-plan.md)
- [Sprint 45 Checklist](../../sprint-planning/phase-11/sprint-45-checklist.md)
- [Phase 11 README](../../sprint-planning/phase-11/README.md)

---

**創建日期**: 2025-12-23
**更新日期**: 2025-12-23
