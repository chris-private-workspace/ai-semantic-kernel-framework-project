# Sprint 153 Checklist - Pipeline 基礎 + Steps 1-2

## Reference
- Plan: [sprint-153-plan.md](sprint-153-plan.md)
- Phase: 45 (Orchestration Core)

---

## 規劃文件

- [x] Phase 45 README
- [x] Sprint 153 plan
- [x] Sprint 153 checklist

## Pipeline 模組結構

- [x] `orchestration/pipeline/__init__.py`
- [x] `orchestration/pipeline/steps/__init__.py`

## PipelineContext + Exceptions

- [x] `pipeline/context.py` — PipelineContext dataclass
  - [x] 身份欄位: user_id, session_id, request_id, task
  - [x] 步驟輸出欄位: memory_text, knowledge_text, routing_decision, risk_assessment 等
  - [x] 控制欄位: paused_at, completed_steps, step_latencies
- [x] `pipeline/exceptions.py` — 暫停異常
  - [x] HITLPauseException (附帶 approval_id, checkpoint_id)
  - [x] DialogPauseException (附帶 questions, dialog_id)
  - [x] PipelineError (通用 pipeline 錯誤)

## PipelineStep 基類

- [x] `pipeline/steps/base.py` — PipelineStep 抽象基類
  - [x] `name` 屬性
  - [x] `async execute(context: PipelineContext) -> PipelineContext` 方法

## MemoryStep (Step 1)

- [x] `pipeline/steps/step1_memory.py`
  - [x] 建立 UnifiedMemoryManager 實例
  - [x] 建立 ContextBudgetManager 實例
  - [x] 呼叫 assemble_context() 取得 token 預算化的記憶文本
  - [x] 寫入 context.memory_text
  - [x] 記錄 TranscriptEntry
  - [x] 錯誤處理: memory 不可用時 graceful fallback (memory_text = "")

## KnowledgeStep (Step 2)

- [x] `pipeline/steps/step2_knowledge.py`
  - [x] Azure OpenAI embedding 呼叫
  - [x] Qdrant query_points 搜索 (top-3)
  - [x] 格式化搜索結果為文本
  - [x] 寫入 context.knowledge_text
  - [x] 記錄 TranscriptEntry
  - [x] 錯誤處理: Qdrant 不可用時 graceful fallback (knowledge_text = "")

## OrchestrationPipelineService 骨架

- [x] `pipeline/service.py`
  - [x] 步驟列表 (List[PipelineStep])
  - [x] run(context) → 依序執行步驟
  - [x] 暫停異常捕獲 (HITLPause, DialogPause)
  - [x] SSE 事件佇列 (asyncio.Queue)
  - [x] 每步記錄 latency 到 context.step_latencies
  - [x] 每步完成後發射 STEP_COMPLETE 事件

## 單元測試

- [x] MemoryStep 測試 (mock UnifiedMemoryManager)
- [x] KnowledgeStep 測試 (mock Qdrant + Azure embeddings)
- [x] PipelineService 骨架測試 (mock steps, 驗證執行順序)

## 驗證

- [x] `from src.integrations.orchestration.pipeline import OrchestrationPipelineService` 成功
- [x] Pipeline 能依序執行 Steps 1-2 並正確填充 context
- [x] 暫停異常能被 pipeline 正確捕獲
