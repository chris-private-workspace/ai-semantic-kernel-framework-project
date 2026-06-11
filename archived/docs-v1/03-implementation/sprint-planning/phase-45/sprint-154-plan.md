# Sprint 154 Plan - Steps 3-5: 意圖 + 風險 + HITL

## Phase 45: Orchestration Core

### Sprint 目標
將 V8 的三層意圖路由、完整度檢查、引導對話、7 維風險評估、HITL 審批整合到 pipeline 的 Steps 3-5。

---

## User Stories

### US-154-1: IntentStep（意圖分析 + 完整度檢查）
**作為** orchestration pipeline，
**我希望** 用 V8 三層 cascade（Pattern→Semantic→LLM）分析用戶意圖並檢查資訊完整度，
**以便** 準確識別意圖類別、子意圖、和缺失資訊。

### US-154-2: RiskStep（風險評估）
**作為** orchestration pipeline，
**我希望** 用 V8 RiskAssessor 的 7 維度 + 40 ITIL 政策評估風險，並用記憶/知識構建 AssessmentContext，
**以便** 根據上下文做出精確的風險判斷。

### US-154-3: HITLGateStep（HITL 審批閘）
**作為** orchestration pipeline，
**我希望** 在高風險操作時自動暫停、保存 checkpoint、並建立審批請求，
**以便** 危險操作必須經過授權才能執行。

### US-154-4: Dialog 暫停路徑
**作為** orchestration pipeline，
**我希望** 在資訊不完整時暫停並返回引導問題，
**以便** 用戶能補充缺失資訊後繼續 pipeline。

---

## 檔案變更

| 檔案 | 動作 | 說明 |
|------|------|------|
| `pipeline/steps/step3_intent.py` | NEW | IntentStep（包裝 BusinessIntentRouter + CompletenessChecker + GuidedDialogEngine） |
| `pipeline/steps/step4_risk.py` | NEW | RiskStep（包裝 RiskAssessor + AssessmentContext 建構器） |
| `pipeline/steps/step5_hitl.py` | NEW | HITLGateStep（包裝 HITLController + checkpoint + ApprovalService） |

---

**Story Points**: 21
