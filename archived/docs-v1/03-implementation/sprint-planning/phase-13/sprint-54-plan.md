# Sprint 54: HybridOrchestrator Refactor

## Sprint 概述

**Sprint 目標**: 重構 HybridOrchestrator，實現統一執行層和 Tool 回調整合

**Story Points**: 35 點
**預估工期**: 1 週

## User Stories

### S54-1: Unified Tool Executor 實現 (13 pts)

**As a** 系統架構師
**I want** 統一的 Tool 執行層
**So that** 無論 MAF 還是 Claude，所有 Tool 都由 Claude 統一處理

**Acceptance Criteria**:
- [ ] UnifiedToolExecutor 類別實現
- [ ] 支持來自 MAF 和 Claude 的 Tool 調用
- [ ] Hook 管道整合 (前處理、後處理)
- [ ] 結果自動同步回源框架
- [ ] 執行日誌和指標收集
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/hybrid/
├── execution/
│   ├── __init__.py
│   ├── unified_executor.py   # UnifiedToolExecutor 主類別
│   ├── tool_router.py        # Tool 路由邏輯
│   ├── result_handler.py     # 結果處理和同步
│   └── tests/
│       └── test_executor.py
```

**Implementation Details**:
```python
# unified_executor.py
from typing import Dict, Any, Optional
from enum import Enum

class ToolSource(Enum):
    MAF = "maf"           # 來自 MAF Workflow
    CLAUDE = "claude"     # 來自 Claude Session
    HYBRID = "hybrid"     # 混合模式觸發

class UnifiedToolExecutor:
    """
    統一 Tool 執行層

    核心設計:
    - 所有 Tool 執行通過 Claude
    - MAF Workflow 的 Tool 調用被攔截並路由到這裡
    - 結果自動同步回源框架

    流程:
    1. 接收 Tool 調用請求 (來自 MAF 或 Claude)
    2. 執行 pre-hooks (Approval, Audit, Sandbox)
    3. 通過 Claude 執行 Tool
    4. 執行 post-hooks (Logging, Result Transform)
    5. 同步結果回源框架
    """

    def __init__(
        self,
        claude_client: ClaudeSDKClient,
        tool_registry: ToolRegistry,
        hook_manager: HookManager,
        context_bridge: ContextBridge,
        metrics_collector: MetricsCollector,
    ):
        self.claude = claude_client
        self.registry = tool_registry
        self.hooks = hook_manager
        self.bridge = context_bridge
        self.metrics = metrics_collector

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        source: ToolSource,
        context: HybridContext,
        approval_required: bool = False,
    ) -> ToolExecutionResult:
        """
        統一執行 Tool

        Args:
            tool_name: Tool 名稱
            arguments: Tool 參數
            source: 調用來源 (maf/claude/hybrid)
            context: 當前混合上下文
            approval_required: 是否需要人工審批
        """
        execution_id = str(uuid.uuid4())

        try:
            # 1. Pre-hooks
            hook_result = await self._run_pre_hooks(
                tool_name, arguments, source, context
            )
            if hook_result.blocked:
                return ToolExecutionResult(
                    success=False,
                    error=hook_result.reason,
                    blocked_by_hook=True,
                )

            # 2. 人工審批檢查
            if approval_required or hook_result.requires_approval:
                approval = await self._request_approval(
                    tool_name, arguments, context
                )
                if not approval.approved:
                    return ToolExecutionResult(
                        success=False,
                        error="Approval denied",
                        approval_denied=True,
                    )

            # 3. 執行 Tool (通過 Claude)
            start_time = time.time()
            result = await self._execute_via_claude(
                tool_name, arguments, context
            )
            execution_time = time.time() - start_time

            # 4. Post-hooks
            await self._run_post_hooks(
                tool_name, arguments, result, source, context
            )

            # 5. 同步結果回源框架
            await self._sync_result_to_source(
                result, source, context
            )

            # 6. 收集指標
            self.metrics.record_tool_execution(
                tool_name=tool_name,
                source=source,
                success=result.success,
                duration=execution_time,
            )

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                error=str(e),
            )

    async def _execute_via_claude(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: HybridContext,
    ) -> ToolResult:
        """通過 Claude 執行 Tool"""
        tool = self.registry.get_tool_instance(tool_name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")

        return await tool.execute(**arguments)
```

---

### S54-2: MAF Tool Callback 整合 (10 pts)

**As a** 開發者
**I want** MAF Workflow 的 Tool 調用能路由到統一執行層
**So that** MAF 也能享受 Claude 的 Tool 能力和 Hook 機制

**Acceptance Criteria**:
- [ ] MAF Adapter 擴展，支持 Tool Callback
- [ ] Tool Callback 攔截器實現
- [ ] GroupChat, Handoff, Concurrent Adapter 整合
- [ ] 結果回傳機制
- [ ] 錯誤處理和重試邏輯

**Technical Tasks**:
```python
# tool_callback.py
class MAFToolCallback:
    """
    MAF Tool 回調處理器

    當 MAF Workflow 中的 Agent 需要執行 Tool 時，
    此回調會將請求路由到 UnifiedToolExecutor。
    """

    def __init__(
        self,
        unified_executor: UnifiedToolExecutor,
        context_bridge: ContextBridge,
    ):
        self.executor = unified_executor
        self.bridge = context_bridge

    async def on_tool_request(
        self,
        agent_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        workflow_context: Dict[str, Any],
    ) -> ToolResult:
        """
        處理來自 MAF Agent 的 Tool 請求

        1. 從 workflow_context 建立 HybridContext
        2. 調用 UnifiedToolExecutor
        3. 返回結果給 MAF Agent
        """
        # 建立 HybridContext
        maf_context = MAFContext.from_workflow(workflow_context)
        hybrid_context = await self.bridge.get_or_create_hybrid(
            maf_context=maf_context
        )

        # 執行 Tool
        result = await self.executor.execute(
            tool_name=tool_name,
            arguments=arguments,
            source=ToolSource.MAF,
            context=hybrid_context,
        )

        return result

# Adapter 擴展範例
class GroupChatBuilderAdapterV2(GroupChatBuilderAdapter):
    """整合 Tool Callback 的 GroupChat Adapter"""

    def __init__(
        self,
        *args,
        tool_callback: Optional[MAFToolCallback] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.tool_callback = tool_callback

    def _create_agent_config(self, agent_def: AgentDefinition) -> dict:
        config = super()._create_agent_config(agent_def)

        # 注入 Tool Callback
        if self.tool_callback:
            config["tool_callback"] = self.tool_callback.on_tool_request

        return config
```

---

### S54-3: HybridOrchestrator V2 重構 (7 pts)

**As a** 開發者
**I want** 重構後的 HybridOrchestrator
**So that** 它能整合 Intent Router、Context Bridge 和 Unified Executor

**Acceptance Criteria**:
- [ ] HybridOrchestratorV2 類別實現
- [ ] 整合 Phase 13 所有組件
- [ ] 支持 Workflow、Chat、Hybrid 三種模式
- [ ] 向後兼容舊版 API
- [ ] 平滑升級路徑

**Technical Tasks**:
```python
# orchestrator_v2.py
class HybridOrchestratorV2:
    """
    重構後的混合編排器

    整合:
    - IntentRouter: 意圖分析和模式選擇
    - ContextBridge: 跨框架上下文同步
    - UnifiedToolExecutor: 統一 Tool 執行
    - FrameworkSelector: 框架能力匹配 (保留)
    """

    def __init__(
        self,
        # 核心組件
        maf_client: AgentFrameworkClient,
        claude_client: ClaudeSDKClient,
        # Phase 13 新組件
        intent_router: IntentRouter,
        context_bridge: ContextBridge,
        unified_executor: UnifiedToolExecutor,
        # 現有組件
        framework_selector: FrameworkSelector,
        session_service: SessionService,
        checkpoint_storage: CheckpointStorage,
    ):
        ...

    async def execute(
        self,
        request: HybridRequest,
        session_id: Optional[str] = None,
    ) -> HybridResult:
        """
        執行混合任務

        流程:
        1. 意圖分析 (Intent Router)
        2. 上下文準備 (Context Bridge)
        3. 根據模式執行
        4. 結果同步和返回
        """
        # 1. 意圖分析
        intent = await self.intent_router.analyze_intent(
            user_input=request.input,
            session_context=await self._get_session_context(session_id),
        )

        # 2. 上下文準備
        context = await self.context_bridge.get_or_create_hybrid(
            session_id=session_id
        )

        # 3. 模式執行
        if intent.mode == ExecutionMode.WORKFLOW_MODE:
            result = await self._execute_workflow_mode(
                request, intent, context
            )
        elif intent.mode == ExecutionMode.CHAT_MODE:
            result = await self._execute_chat_mode(
                request, intent, context
            )
        else:  # HYBRID_MODE
            result = await self._execute_hybrid_mode(
                request, intent, context
            )

        # 4. 上下文同步
        await self.context_bridge.sync_after_execution(
            result, context
        )

        return result

    async def _execute_workflow_mode(
        self,
        request: HybridRequest,
        intent: IntentAnalysis,
        context: HybridContext,
    ) -> HybridResult:
        """
        Workflow 模式執行

        MAF 主導，但 Tool 執行通過 Unified Executor
        """
        ...

    async def _execute_chat_mode(
        self,
        request: HybridRequest,
        intent: IntentAnalysis,
        context: HybridContext,
    ) -> HybridResult:
        """
        Chat 模式執行

        Claude 主導，直接使用 Claude Session
        """
        ...

    async def _execute_hybrid_mode(
        self,
        request: HybridRequest,
        intent: IntentAnalysis,
        context: HybridContext,
    ) -> HybridResult:
        """
        Hybrid 模式執行

        動態切換，根據執行過程中的需求調整
        """
        ...
```

---

### S54-4: 整合測試與文檔 (5 pts)

**As a** QA 工程師
**I want** Phase 13 完整的整合測試
**So that** 所有組件協同工作正常

**Acceptance Criteria**:
- [ ] 端到端整合測試
- [ ] 效能基準測試
- [ ] Phase 13 技術文檔
- [ ] API 遷移指南
- [ ] 示範程式碼

**Technical Tasks**:
- `backend/tests/integration/hybrid/test_phase13_integration.py`
- `docs/03-implementation/sprint-execution/sprint-54/README.md`
- `docs/guides/hybrid-orchestrator-v2-migration.md`

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| Intent Router | Sprint 52 | 📋 待完成 |
| Context Bridge | Sprint 53 | 📋 待完成 |
| ToolRegistry | Phase 12 | ✅ 已完成 |
| HookManager | Phase 12 | ✅ 已完成 |
| MAF Adapters | Phase 4-7 | ✅ 已完成 |

## Risks

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 重構影響現有功能 | 回歸錯誤 | 保持向後兼容，漸進式升級 |
| Tool Callback 效能 | 延遲增加 | 快取、批量處理優化 |
| MAF Adapter 修改 | 官方 API 相容性 | 最小化修改，使用裝飾器模式 |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] 效能測試達標
- [ ] 向後兼容驗證
- [ ] 文檔完整
- [ ] Code Review 完成
