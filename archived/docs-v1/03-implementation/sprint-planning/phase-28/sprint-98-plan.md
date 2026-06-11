# Sprint 98: HybridOrchestratorV2 整合

## 概述

Sprint 98 專注於將 Phase 28 的所有新組件整合到現有的 **HybridOrchestratorV2** 架構中。

## 目標

1. 重命名 IntentRouter → FrameworkSelector
2. 整合 BusinessIntentRouter 到 Orchestrator
3. 整合 GuidedDialogEngine 到 API 層
4. 整合 HITL 到現有審批流程

## Story Points: 25 點

## 前置條件

- ✅ Sprint 97 完成 (HITLController)
- ✅ 所有 Phase 28 組件就緒
- ✅ HybridOrchestratorV2 現有功能穩定

## 任務分解

### Story 98-1: 重命名 IntentRouter → FrameworkSelector (2h, P0)

**目標**: 重命名現有 IntentRouter 以避免混淆

**交付物**:
- 更新 `backend/src/integrations/hybrid/intent/router.py`
- 更新所有引用文件

**變更清單**:
- [ ] `IntentRouter` → `FrameworkSelector`
- [ ] `IntentAnalysis` → `FrameworkAnalysis`
- [ ] `analyze_intent()` → `select_framework()`
- [ ] 更新 imports
- [ ] 更新測試文件

**驗收標準**:
- [ ] 重命名完成
- [ ] 所有測試通過
- [ ] 無破壞性變更

### Story 98-2: 整合 BusinessIntentRouter (4h, P0)

**目標**: 在 Orchestrator 入口整合業務意圖路由

**交付物**:
- 更新 `backend/src/integrations/hybrid/orchestrator_v2.py`

**整合點**:

```python
class HybridOrchestratorV2:
    def __init__(
        self,
        # 現有參數
        framework_selector: FrameworkSelector,  # 重命名後
        context_bridge: ContextBridge,
        # 新增參數
        input_gateway: InputGateway,
        business_router: BusinessIntentRouter,
        guided_dialog: GuidedDialogEngine,
        risk_assessor: RiskAssessor,
        hitl_controller: HITLController,
    ):
        pass

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """
        執行流程 (更新)

        1. InputGateway 處理輸入
        2. BusinessIntentRouter 分類意圖
        3. 檢查完整度，需要時啟動 GuidedDialog
        4. RiskAssessor 評估風險
        5. 需要時啟動 HITL 審批
        6. FrameworkSelector 選擇執行框架
        7. 執行工作流
        """
```

**驗收標準**:
- [ ] 整合完成
- [ ] 流程正確
- [ ] 向後相容

### Story 98-3: 整合 GuidedDialogEngine 到 API 層 (4h, P0)

**目標**: 在 API 層支援引導式對話

**交付物**:
- `backend/src/api/v1/orchestration/dialog_routes.py`

**API 端點**:

```
POST /api/v1/orchestration/dialog/start
- 啟動對話，返回第一輪問題

POST /api/v1/orchestration/dialog/{dialog_id}/respond
- 提交用戶回答，返回下一輪問題或完成

GET /api/v1/orchestration/dialog/{dialog_id}/status
- 獲取對話狀態

DELETE /api/v1/orchestration/dialog/{dialog_id}
- 取消對話
```

**驗收標準**:
- [ ] API 路由實現完成
- [ ] 多輪對話正常工作
- [ ] 狀態管理正確

### Story 98-4: 整合 HITL 到現有審批流程 (4h, P0)

**目標**: 整合新的 HITL 到現有審批機制

**交付物**:
- 更新 `backend/src/api/v1/orchestration/approval_routes.py`
- 更新 `orchestrator_v2.py`

**API 端點**:

```
GET /api/v1/orchestration/approvals
- 獲取待審批列表

GET /api/v1/orchestration/approvals/{approval_id}
- 獲取審批詳情

POST /api/v1/orchestration/approvals/{approval_id}/decision
- 提交審批決定 (approve/reject)

POST /api/v1/orchestration/approvals/{approval_id}/callback
- Teams Webhook 回調
```

**驗收標準**:
- [ ] 審批 API 實現完成
- [ ] 與現有 ApprovalHook 整合
- [ ] Teams 回調正常工作

## 技術設計

### 更新後的 HybridOrchestratorV2

```python
class HybridOrchestratorV2:
    """
    混合編排器 V2 (Phase 28 整合)

    執行流程:
    1. InputGateway → 來源識別和處理
    2. BusinessIntentRouter → IT 意圖分類
    3. GuidedDialogEngine → 資訊收集 (如需要)
    4. RiskAssessor → 風險評估
    5. HITLController → 審批 (如需要)
    6. FrameworkSelector → 框架選擇
    7. 執行 (Claude SDK / MAF)
    """

    def __init__(
        self,
        # Phase 28 新增
        input_gateway: InputGateway,
        business_router: BusinessIntentRouter,
        guided_dialog: GuidedDialogEngine,
        risk_assessor: RiskAssessor,
        hitl_controller: HITLController,
        # 現有組件 (重命名)
        framework_selector: FrameworkSelector,
        context_bridge: ContextBridge,
        tool_executor: UnifiedToolExecutor,
    ):
        self.input_gateway = input_gateway
        self.business_router = business_router
        self.guided_dialog = guided_dialog
        self.risk_assessor = risk_assessor
        self.hitl_controller = hitl_controller
        self.framework_selector = framework_selector
        self.context_bridge = context_bridge
        self.tool_executor = tool_executor

    async def execute(
        self,
        request: ExecutionRequest,
        session_context: Optional[SessionContext] = None,
    ) -> ExecutionResult:
        """執行混合編排"""

        # 1. InputGateway 處理
        routing_decision = await self.input_gateway.process(request)

        # 2. 檢查完整度
        if not routing_decision.completeness.is_sufficient:
            # 啟動引導式對話
            dialog_result = await self._handle_guided_dialog(
                routing_decision, request
            )
            if dialog_result.needs_more_info:
                return ExecutionResult(
                    status="pending_info",
                    dialog_id=dialog_result.dialog_id,
                    questions=dialog_result.questions,
                )
            routing_decision = dialog_result.routing_decision

        # 3. 風險評估
        risk_assessment = self.risk_assessor.assess(routing_decision)

        # 4. HITL 審批 (如需要)
        if risk_assessment.requires_approval:
            approval_result = await self._handle_hitl(
                routing_decision, risk_assessment, request
            )
            if approval_result.status == "pending":
                return ExecutionResult(
                    status="pending_approval",
                    approval_id=approval_result.approval_id,
                )
            if approval_result.status == "rejected":
                return ExecutionResult(
                    status="rejected",
                    reason=approval_result.reason,
                )

        # 5. 框架選擇
        framework_analysis = await self.framework_selector.select_framework(
            user_input=request.content,
            session_context=session_context,
            routing_decision=routing_decision,
        )

        # 6. 執行
        if framework_analysis.mode == ExecutionMode.WORKFLOW_MODE:
            return await self._execute_workflow_mode(
                request, routing_decision, session_context
            )
        else:
            return await self._execute_chat_mode(
                request, routing_decision, session_context
            )
```

### 整合流程圖

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    HybridOrchestratorV2 執行流程 (Phase 28)                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ExecutionRequest                                                                │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ 1. InputGateway.process()                                                │    │
│  │    來源識別 → 分流處理                                                  │    │
│  └───────────────────────────────┬─────────────────────────────────────────┘    │
│                                  │                                               │
│                                  ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ 2. 檢查 completeness.is_sufficient                                       │    │
│  └───────────────────────────────┬─────────────────────────────────────────┘    │
│                                  │                                               │
│              ┌───────────────────┴───────────────────┐                          │
│              │                                       │                          │
│             No                                      Yes                         │
│              │                                       │                          │
│              ▼                                       │                          │
│  ┌─────────────────────────────┐                    │                          │
│  │ GuidedDialogEngine          │                    │                          │
│  │   生成問題 → 收集回答      │                    │                          │
│  │   增量更新 → 重新檢查      │                    │                          │
│  └─────────────┬───────────────┘                    │                          │
│                │                                     │                          │
│                └─────────────────────────────────────┤                          │
│                                                      │                          │
│                                                      ▼                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ 3. RiskAssessor.assess()                                                 │    │
│  │    評估風險等級                                                         │    │
│  └───────────────────────────────┬─────────────────────────────────────────┘    │
│                                  │                                               │
│              ┌───────────────────┴───────────────────┐                          │
│              │ requires_approval?                    │                          │
│              └───────────────────┬───────────────────┘                          │
│                                  │                                               │
│             Yes                  │                  No                           │
│              │                   │                   │                          │
│              ▼                   │                   │                          │
│  ┌─────────────────────────────┐│                   │                          │
│  │ HITLController              ││                   │                          │
│  │   發送審批請求              ││                   │                          │
│  │   等待審批結果              ││                   │                          │
│  └─────────────┬───────────────┘│                   │                          │
│                │                 │                   │                          │
│                └─────────────────┼───────────────────┤                          │
│                                  │                   │                          │
│                                  ▼                   │                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ 4. FrameworkSelector.select_framework()                                  │    │
│  │    選擇 WORKFLOW_MODE / CHAT_MODE                                       │    │
│  └───────────────────────────────┬─────────────────────────────────────────┘    │
│                                  │                                               │
│                                  ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ 5. 執行                                                                  │    │
│  │    WORKFLOW_MODE → MAF Worker                                           │    │
│  │    CHAT_MODE → Claude SDK                                               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 完成標準

- [ ] 所有 Story 完成
- [ ] 重命名無破壞性變更
- [ ] 整合測試通過
- [ ] API 正常工作
- [ ] 向後相容

---

**Sprint 開始**: 2026-02-27
**Sprint 結束**: 2026-03-06
**Story Points**: 25
