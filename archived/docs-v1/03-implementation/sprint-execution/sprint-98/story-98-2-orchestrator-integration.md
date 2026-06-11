# Story 98-2: 整合 BusinessIntentRouter 到 HybridOrchestratorV2

## 概述

| 屬性 | 值 |
|------|-----|
| **Story 編號** | S98-2 |
| **名稱** | 整合 BusinessIntentRouter 到 Orchestrator |
| **點數** | 4 |
| **優先級** | P0 |
| **狀態** | ✅ 完成 |

## 目標

在 Orchestrator 入口整合業務意圖路由和所有 Phase 28 組件。

## 變更清單

### 1. 新增 Phase 28 組件導入

```python
from src.integrations.orchestration import (
    # Sprint 93: BusinessIntentRouter
    BusinessIntentRouter,
    RoutingDecision,
    CompletenessInfo,
    # Sprint 94: GuidedDialogEngine
    GuidedDialogEngine,
    DialogResponse,
    # Sprint 95: InputGateway
    InputGateway,
    IncomingRequest,
    SourceType,
    # Sprint 96: RiskAssessor
    RiskAssessor,
    RiskAssessment,
    # Sprint 97: HITLController
    HITLController,
    ApprovalRequest,
    ApprovalStatus,
)
```

### 2. 新增初始化參數

- [x] `input_gateway: Optional[InputGateway]`
- [x] `business_router: Optional[BusinessIntentRouter]`
- [x] `guided_dialog: Optional[GuidedDialogEngine]`
- [x] `risk_assessor: Optional[RiskAssessor]`
- [x] `hitl_controller: Optional[HITLController]`

### 3. 新增屬性訪問器

- [x] `input_gateway` property
- [x] `business_router` property
- [x] `guided_dialog` property
- [x] `risk_assessor` property
- [x] `hitl_controller` property
- [x] `has_phase_28_components()` method

### 4. 新增執行方法

- [x] `execute_with_routing()` - Phase 28 完整執行流程
- [x] `_handle_guided_dialog()` - 引導式對話處理
- [x] `_handle_hitl()` - HITL 審批處理

## Phase 28 執行流程

```
1. InputGateway.process() → 來源識別和處理
2. 檢查 completeness.is_sufficient
3. GuidedDialogEngine → 資訊收集 (如需要)
4. RiskAssessor.assess() → 風險評估
5. HITLController → 審批 (如需要)
6. FrameworkSelector.select_framework() → 框架選擇
7. 執行 (Claude SDK / MAF)
```

## 使用範例

```python
# 創建帶有 Phase 28 組件的 Orchestrator
orchestrator = HybridOrchestratorV2(
    # Phase 28 Components
    input_gateway=create_input_gateway(),
    business_router=create_router(),
    guided_dialog=create_guided_dialog_engine(),
    risk_assessor=RiskAssessor(),
    hitl_controller=create_hitl_controller(),
    # Phase 13 Components
    framework_selector=FrameworkSelector(),
)

# 使用 Phase 28 流程執行
request = IncomingRequest(
    content="我想申請一個新的虛擬機",
    source_type=SourceType.USER,
)
result = await orchestrator.execute_with_routing(
    request,
    requester="user@example.com",
)

# 或使用原有流程 (向後兼容)
result = await orchestrator.execute("簡單問題")
```

## 向後兼容性

- [x] 原有 `execute()` 方法保持不變
- [x] Phase 28 組件為可選參數
- [x] 無 Phase 28 組件時使用原有流程

---

**完成日期**: 2026-01-16
