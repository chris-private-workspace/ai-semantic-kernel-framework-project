# Sprint 145 Checklist: Orchestrator SSE 串流端點

**Sprint**: 145 | **Phase**: 42 | **Story Points**: 12
**Plan**: [sprint-145-plan.md](./sprint-145-plan.md)

---

## S145-1: 後端 SSE 端點 (5 SP)

- [x] `routes.py` — POST /orchestrator/chat/stream SSE 端點
- [x] FastAPI StreamingResponse + text/event-stream
- [x] 保留 POST /orchestrator/chat 同步端點
- [x] `sse_events.py` — PipelineEventEmitter (asyncio.Queue)
- [x] SSEEvent dataclass + SSEEventType enum (12 types)
- [x] stream() + emit() + keepalive
- [x] Mediator execute() 接受 event_emitter 參數
- [x] 每步 emit + asyncio.sleep(0) yield

## S145-2: 前端 SSE 接收 (4 SP)

- [x] `useSSEChat.ts` — fetch + ReadableStream SSE hook
- [x] SSE 格式解析 + 12 handler callbacks
- [x] UnifiedChat handleSend 改用 sendSSE()
- [x] ROUTING_COMPLETE 即時更新 IntentStatusChip
- [x] TEXT_DELTA 即時更新 content
- [x] isSSEStreaming 驅動 loading 狀態

## S145-3: AG-UI EventBridge 映射 (3 SP)

- [x] PIPELINE_TO_AGUI_MAP: 12 Pipeline events -> AG-UI protocol names
- [x] SSEEvent.to_agui_sse_string(): AG-UI 格式輸出
- [x] PipelineEventEmitter.stream(agui_format=True) 支援

## 額外修復

- [x] 三層路由永遠執行（不因 force_mode 跳過）
- [x] enum 用 .value 序列化
- [x] routes.py context 變數修復
- [x] PipelineResponse 加入 execution_mode, suggested_mode, tool_calls

---

**Status**: Done
