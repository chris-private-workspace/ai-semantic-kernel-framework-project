# Sprint 56: Mode Switcher & HITL

## Sprint 概述

**Sprint 目標**: 實現動態模式切換和增強的 Human-in-the-Loop 機制

**Story Points**: 35 點
**預估工期**: 1 週

## User Stories

### S56-1: Mode Switcher 核心實現 (13 pts)

**As a** 系統架構師
**I want** 動態模式切換機制
**So that** 系統能在 Workflow 和 Chat 模式間平滑切換

**Acceptance Criteria**:
- [ ] ModeSwitcher 類別實現
- [ ] SwitchTrigger 和 SwitchResult 資料模型
- [ ] 切換觸發條件檢測
- [ ] 狀態保存和遷移邏輯
- [ ] 回滾機制
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/hybrid/
├── switching/
│   ├── __init__.py
│   ├── switcher.py         # ModeSwitcher 主類別
│   ├── models.py           # SwitchTrigger, SwitchResult, ModeTransition
│   ├── triggers/
│   │   ├── __init__.py
│   │   ├── complexity.py   # 複雜度變化觸發
│   │   ├── user.py         # 用戶請求觸發
│   │   ├── failure.py      # 失敗恢復觸發
│   │   └── resource.py     # 資源約束觸發
│   ├── migration/
│   │   ├── __init__.py
│   │   └── state_migrator.py  # 狀態遷移邏輯
│   └── tests/
```

**Implementation Details**:
```python
# switcher.py
class ModeSwitcher:
    def __init__(
        self,
        trigger_detectors: List[TriggerDetector],
        state_migrator: StateMigrator,
        checkpoint_storage: UnifiedCheckpointStorage,
        context_bridge: ContextBridge,
    ):
        ...

    async def should_switch(
        self,
        current_mode: ExecutionMode,
        current_state: ExecutionState,
        new_input: str,
    ) -> Optional[SwitchTrigger]:
        """
        檢測是否需要切換模式

        檢測順序:
        1. 用戶明確請求
        2. 失敗恢復需求
        3. 資源約束
        4. 複雜度變化
        """
        for detector in self.trigger_detectors:
            trigger = await detector.detect(
                current_mode, current_state, new_input
            )
            if trigger:
                return trigger
        return None

    async def execute_switch(
        self,
        trigger: SwitchTrigger,
        context: HybridContext,
    ) -> SwitchResult:
        """
        執行模式切換

        步驟:
        1. 建立切換前 Checkpoint
        2. 遷移狀態到目標模式
        3. 初始化目標模式
        4. 驗證切換成功
        5. 更新上下文
        """
        switch_id = str(uuid.uuid4())

        try:
            # 1. 保存切換前狀態
            checkpoint = await self._create_switch_checkpoint(
                context, trigger
            )

            # 2. 遷移狀態
            migrated_state = await self.state_migrator.migrate(
                context,
                trigger.source_mode,
                trigger.target_mode,
            )

            # 3. 初始化目標模式
            new_context = await self._initialize_target_mode(
                trigger.target_mode,
                migrated_state,
            )

            # 4. 驗證
            validation = await self._validate_switch(new_context)
            if not validation.success:
                await self.rollback_switch(checkpoint)
                return SwitchResult(
                    success=False,
                    error=validation.error,
                )

            return SwitchResult(
                success=True,
                switch_id=switch_id,
                new_mode=trigger.target_mode,
                new_context=new_context,
                checkpoint_id=checkpoint.checkpoint_id,
            )

        except Exception as e:
            await self.rollback_switch(checkpoint)
            raise

    async def rollback_switch(
        self,
        checkpoint_id_or_checkpoint: Union[str, HybridCheckpoint],
    ) -> bool:
        """回滾失敗的模式切換"""
        ...
```

---

### S56-2: Trigger Detectors (8 pts)

**As a** 開發者
**I want** 多種切換觸發檢測器
**So that** 系統能智能識別何時需要切換模式

**Acceptance Criteria**:
- [ ] ComplexityTriggerDetector (任務複雜度變化)
- [ ] UserRequestTriggerDetector (用戶明確請求)
- [ ] FailureTriggerDetector (失敗恢復)
- [ ] ResourceTriggerDetector (資源約束)
- [ ] 可配置的觸發閾值

**Technical Tasks**:
```python
# triggers/complexity.py
class ComplexityTriggerDetector(TriggerDetector):
    """
    複雜度變化觸發器

    場景:
    - Chat → Workflow: 簡單問答變成多步驟任務
    - Workflow → Chat: 複雜任務變成簡單問答
    """

    async def detect(
        self,
        current_mode: ExecutionMode,
        state: ExecutionState,
        new_input: str,
    ) -> Optional[SwitchTrigger]:
        # 分析新輸入的複雜度
        complexity = await self._analyze_complexity(new_input)

        # Chat 模式下複雜度升高
        if current_mode == ExecutionMode.CHAT_MODE:
            if complexity.requires_multi_agent or complexity.step_count > 3:
                return SwitchTrigger(
                    trigger_type="complexity",
                    source_mode=ExecutionMode.CHAT_MODE,
                    target_mode=ExecutionMode.WORKFLOW_MODE,
                    reason="Task complexity increased, multi-agent required",
                    confidence=complexity.confidence,
                )

        # Workflow 模式下複雜度降低
        if current_mode == ExecutionMode.WORKFLOW_MODE:
            if complexity.is_simple_query and not state.has_pending_steps:
                return SwitchTrigger(
                    trigger_type="complexity",
                    source_mode=ExecutionMode.WORKFLOW_MODE,
                    target_mode=ExecutionMode.CHAT_MODE,
                    reason="Simple query detected, switching to chat",
                    confidence=complexity.confidence,
                )

        return None

# triggers/failure.py
class FailureTriggerDetector(TriggerDetector):
    """
    失敗恢復觸發器

    場景:
    - Workflow 執行失敗，需要 Chat 診斷
    - 多次重試失敗，降級處理
    """

    async def detect(
        self,
        current_mode: ExecutionMode,
        state: ExecutionState,
        new_input: str,
    ) -> Optional[SwitchTrigger]:
        if state.consecutive_failures >= self.config.failure_threshold:
            return SwitchTrigger(
                trigger_type="failure",
                source_mode=current_mode,
                target_mode=ExecutionMode.CHAT_MODE,
                reason=f"Consecutive failures ({state.consecutive_failures}), switching to diagnostic chat",
                confidence=0.9,
            )
        return None
```

---

### S56-3: State Migration (7 pts)

**As a** 開發者
**I want** 可靠的狀態遷移機制
**So that** 模式切換不會丟失重要狀態

**Acceptance Criteria**:
- [ ] StateMigrator 實現
- [ ] MAF → Chat 狀態遷移
- [ ] Chat → MAF 狀態遷移
- [ ] 遷移驗證邏輯
- [ ] 資料完整性保證

**Technical Tasks**:
```python
# migration/state_migrator.py
class StateMigrator:
    """狀態遷移器"""

    async def migrate(
        self,
        context: HybridContext,
        source_mode: ExecutionMode,
        target_mode: ExecutionMode,
    ) -> MigratedState:
        if source_mode == ExecutionMode.WORKFLOW_MODE:
            return await self._workflow_to_chat(context)
        elif source_mode == ExecutionMode.CHAT_MODE:
            return await self._chat_to_workflow(context)
        else:
            return await self._hybrid_migration(context, target_mode)

    async def _workflow_to_chat(
        self,
        context: HybridContext,
    ) -> MigratedState:
        """
        Workflow → Chat 遷移

        保留:
        - 執行歷史 (轉為對話歷史)
        - 中間結果
        - Tool 調用記錄

        轉換:
        - Workflow step → Chat context summary
        - Agent states → System prompt context
        """
        ...

    async def _chat_to_workflow(
        self,
        context: HybridContext,
    ) -> MigratedState:
        """
        Chat → Workflow 遷移

        保留:
        - 對話歷史 (作為 workflow context)
        - Tool 調用結果
        - 用戶意圖

        轉換:
        - Conversation → Initial workflow state
        - Claude context → Workflow variables
        """
        ...
```

---

### S56-4: Enhanced HITL & API (7 pts)

**As a** API 使用者
**I want** 增強的 Human-in-the-Loop API
**So that** 可以精細控制審批和模式切換

**Acceptance Criteria**:
- [ ] `POST /api/v1/hybrid/switch` 手動觸發模式切換
- [ ] `GET /api/v1/hybrid/switch/status` 查詢切換狀態
- [ ] `POST /api/v1/hybrid/switch/rollback` 回滾切換
- [ ] 風險型審批 API 整合
- [ ] WebSocket 切換事件通知

**API Specification**:
```yaml
/api/v1/hybrid/switch:
  post:
    summary: 手動觸發模式切換
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required:
              - session_id
              - target_mode
            properties:
              session_id:
                type: string
              target_mode:
                type: string
                enum: [workflow, chat, hybrid]
              reason:
                type: string
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                switch_id:
                  type: string
                success:
                  type: boolean
                new_mode:
                  type: string
                checkpoint_id:
                  type: string
```

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| Risk Assessment Engine | Sprint 55 | 📋 待完成 |
| Context Bridge | Sprint 53 | 📋 待完成 |
| Unified Checkpoint | Sprint 57 | 📋 待完成 (部分) |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 模式切換成功率 > 99%
- [ ] 回滾機制測試通過
- [ ] API 文檔更新
- [ ] Code Review 完成
