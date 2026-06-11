# Sprint 156 Checklist - 生產 API + 後處理

## Reference
- Plan: [sprint-156-plan.md](sprint-156-plan.md)
- Phase: 45 (Orchestration Core)

---

## PostProcessStep (Step 8)
- [x] `pipeline/steps/step8_postprocess.py`
- [x] Checkpoint 保存 (WorkflowCheckpoint → Redis)
- [x] 異步記憶抽取 (MemoryExtractionService fire-and-forget)
- [x] 記憶合併觸發 (MemoryConsolidationService)

## API Schemas
- [x] `chat_schemas.py` — ChatRequest, ResumeRequest, DialogRespondRequest, SessionStatusResponse

## API Routes
- [x] `chat_routes.py`
- [x] POST /orchestration/chat (SSE 串流)
- [x] POST /orchestration/chat/resume
- [x] POST /orchestration/chat/dialog-respond
- [x] GET /orchestration/chat/session/{id}

## 路由註冊
- [x] orchestration/__init__.py — 匯出 chat_router
- [x] api/v1/__init__.py — protected_router.include_router

## 測試
- [x] PostProcessStep 單元測試
- [x] Chat schemas 驗證測試
