# Sprint 154 Checklist - Steps 3-5: 意圖 + 風險 + HITL

## Reference
- Plan: [sprint-154-plan.md](sprint-154-plan.md)
- Phase: 45 (Orchestration Core)

---

## IntentStep (Step 3)

- [x] `pipeline/steps/step3_intent.py`
  - [x] 包裝 V8 BusinessIntentRouter（三層 cascade）
  - [x] 整合 CompletenessChecker
  - [x] 完整時：寫入 context.routing_decision + context.completeness_info
  - [x] 不完整時：呼叫 GuidedDialogEngine → raise DialogPauseException
  - [x] 記錄 TranscriptEntry

## RiskStep (Step 4)

- [x] `pipeline/steps/step4_risk.py`
  - [x] 從 context.memory_text + knowledge_text 構建 AssessmentContext
  - [x] 呼叫 V8 RiskAssessor.assess()
  - [x] 寫入 context.risk_assessment
  - [x] 記錄 TranscriptEntry

## HITLGateStep (Step 5)

- [x] `pipeline/steps/step5_hitl.py`
  - [x] 檢查 risk_level + intent_category 是否需要審批
  - [x] 需要時：保存 checkpoint → 建立 ApprovalRequest → raise HITLPauseException
  - [x] 不需要時：直接通過
  - [x] 記錄 TranscriptEntry

## 單元測試

- [x] IntentStep 測試（mock BusinessIntentRouter）
- [x] RiskStep 測試（mock RiskAssessor）
- [x] HITLGateStep 測試（mock ApprovalService + CheckpointStorage）
- [x] Dialog 暫停路徑測試（不完整意圖 → DialogPauseException）
- [x] HITL 暫停路徑測試（高風險 → HITLPauseException）

## 驗證

- [x] Pipeline 在不完整意圖時正確暫停（DialogPauseException）
- [x] Pipeline 在高風險變更時正確暫停（HITLPauseException）
- [x] 低風險查詢能通過 Steps 3-5 不暫停
