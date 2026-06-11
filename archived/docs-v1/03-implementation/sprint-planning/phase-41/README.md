# Phase 41: Chat Pipeline Integration — E2E 可視化

## 概述

Phase 41 專注於 **將完整 10 步 E2E Pipeline 接入 Chat 介面**，讓用戶在對話中能即時看到每個管線步驟的執行過程。

Phase 40 建立了獨立頁面和組件（Sessions、Tasks、Knowledge、Memory），但 **UnifiedChat 仍使用舊的 orchestration flow**（REST 一次性呼叫），未接通新的 `/orchestrator/chat` SSE 串流管線。用戶在 Chat 中看不到：意圖分類過程、任務分發、工具調用、記憶檢索等步驟。

> **Status**: 📋 規劃中 — 3 Sprints (141-143), ~28 SP

## 核心問題

### 現狀（Phase 40 後）

```
用戶輸入 → useOrchestration (REST) → 3 個獨立 API 呼叫 → 一次性回應
                                      ↑ 沒有 SSE 串流
                                      ↑ 沒有中間步驟顯示
                                      ↑ 沒有 inline 組件
```

### 目標（Phase 41 後）

```
用戶輸入 → /orchestrator/chat (SSE) → 即時串流每個步驟：
  ├─ IntentStatusChip (意圖 + 風險 + 模式)
  ├─ TaskProgressCard (任務分發 + 進度)
  ├─ ToolCallTracker (工具調用過程)
  ├─ MemoryHint (相關記憶提示)
  ├─ 打字效果 (LLM token 串流)
  └─ 最終回應
```

## 前置條件

- ✅ Phase 39 — 後端 Pipeline 組裝（OrchestratorBootstrap + 7 handler wiring）
- ✅ Phase 40 — 前端組件已建立（IntentStatusChip, TaskProgressCard, MemoryHint）
- ✅ `/orchestrator/chat` 端點已可用且返回完整 PipelineResponse
- ✅ AG-UI SSE 端點 `/ag-ui/run-v2` 已存在（MediatorEventBridge）
- ✅ E2E 38/38 API 測試通過

## 架構決策

### 選擇方案：統一 SSE 管線

**方案 A（選用）**: UnifiedChat 改用 `/orchestrator/chat` + AG-UI SSE 雙通道
- POST `/orchestrator/chat` 送訊息，取得 session_id + 同步回應
- 同時用 SSE `/ag-ui/run-v2` 接收中間事件（思考、工具、進度）
- 好處：不改後端，利用已有的 MediatorEventBridge

**方案 B（備選）**: 後端新增 `/orchestrator/chat/stream` SSE 端點
- 一個連線同時返回管線事件和最終回應
- 好處：更簡潔；壞處：需要改後端

**決定用方案 A**：前端改動為主，後端不變。

### 消除雙路徑

現有 `handleSend()` 有兩條路徑（orchestration ON/OFF）。Phase 41 後統一為一條路徑：
1. POST `/orchestrator/chat` （含 content + session_id）
2. 解析 PipelineResponse → 顯示 IntentStatusChip + 回應
3. 如果有 task_id → 顯示 TaskProgressCard
4. MemoryHint 在輸入框上方顯示

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 141](./sprint-141-plan.md) | Chat → Orchestrator Pipeline 接通 | ~10 點 | 📋 計劃中 |
| [Sprint 142](./sprint-142-plan.md) | Inline 組件嵌入 + 工具調用顯示 | ~10 點 | 📋 計劃中 |
| [Sprint 143](./sprint-143-plan.md) | Memory 整合 + Session Resume UI + 完善 | ~8 點 | 📋 計劃中 |

**總計**: ~28 Story Points (3 Sprints)

## 改動範圍

### 需要修改的核心檔案

| 檔案 | 改動描述 |
|------|---------|
| `pages/UnifiedChat.tsx` | 消除雙路徑，統一用 orchestrator pipeline |
| `hooks/useUnifiedChat.ts` | 改 sendMessage() 指向 `/orchestrator/chat` |
| `hooks/useOrchestratorChat.ts` | 加強 SSE 事件處理（pipeline 中間事件） |
| `components/unified-chat/MessageList.tsx` | 擴展 timeline 支援 4 種 item type |
| `components/unified-chat/ChatArea.tsx` | 傳遞 orchestration metadata 到 MessageList |
| `components/unified-chat/index.ts` | 匯出 IntentStatusChip, TaskProgressCard, MemoryHint |

### 已建但未接入的組件（Phase 40）

| 組件 | 嵌入位置 | 數據來源 |
|------|---------|---------|
| IntentStatusChip | 用戶訊息下方 | PipelineResponse.intent_category + risk_level |
| TaskProgressCard | Chat timeline 中 | PipelineResponse.task_id → useTask hook |
| MemoryHint | ChatInput 上方 | Orchestrator context handler 記憶數據 |
| ToolCallTracker | Chat timeline 中 | SSE TOOL_CALL_START/END 事件 |

## E2E 流程可視化目標

用戶在 Chat 中應該看到的完整流程：

```
┌─────────────────────────────────────────────────┐
│ Chat 介面                                        │
│                                                   │
│  [You] 請幫我檢查 Production DB 的連線狀態        │
│                                                   │
│  ┌─ IntentStatusChip ──────────────────────────┐ │
│  │ 🧠 意圖：query | 🛡️ 風險：LOW | ⚡ 模式：workflow │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─ TaskProgressCard ─────────────────────────┐  │
│  │ 📋 task-abc123  DB Health Check    🔵 執行中 │  │
│  │ ████████░░░░░░░░  60%                      │  │
│  │ ▸ 3 個步驟                                  │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌─ ToolCallTracker ─────────────────────────┐   │
│  │ 🔧 mcp_shell_execute  ✅ 完成 (1.2s)      │   │
│  │ 🔧 mcp_sql_query      🔄 執行中...        │   │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  [AI] 檢查結果如下：                              │
│       ✅ 網路連通                                 │
│       ✅ PostgreSQL 回應正常 (12ms)               │
│       ⚠️ 連線池使用率 85%                         │
│                                                   │
│  ┌─ MemoryHint ───────────────────────────────┐  │
│  │ 🧠 找到 2 條相關記憶                        │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  [輸入框] Type a message...                       │
└─────────────────────────────────────────────────┘
```

## 成功標準

- [ ] 用戶發送訊息後，Chat 中顯示 IntentStatusChip（意圖 + 風險 + 執行模式）
- [ ] 當有任務被 dispatch 時，Chat 中顯示 TaskProgressCard（即時進度）
- [ ] 工具調用過程在 Chat 中以 ToolCallTracker 顯示
- [ ] LLM 回應以打字效果即時串流（非一次性出現）
- [ ] Chat 輸入框上方顯示 MemoryHint（當有相關記憶時）
- [ ] Session Resume 能恢復對話歷史並顯示之前的 pipeline 狀態
- [ ] 所有 10 步流程在 Chat 中有可視化對應
- [ ] 不影響現有功能（工作流模式、審批流程仍正常）
- [ ] TypeScript 零錯誤、npm run build 通過

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| UnifiedChat 改動大可能破壞現有功能 | 高 | 漸進式：先加新路徑，保留舊路徑作 fallback |
| SSE 事件格式後端未完全支援 | 中 | 先用 PipelineResponse 同步數據，SSE 作增強 |
| MessageList timeline 複雜度增加 | 中 | 新增 item type 用獨立 renderer，不改現有邏輯 |
| ToolCallTracker 數據來源不明確 | 低 | 先從 PipelineResponse metadata 取，後續接 SSE |

---

**Phase 41 前置**: Phase 39 (E2E Assembly D) + Phase 40 (Frontend Enhancement)
**總 Story Points**: ~28 pts
**Sprint 範圍**: Sprint 141-143
**技術棧**: React 18 + TypeScript + Shadcn UI + useOrchestratorChat hook
