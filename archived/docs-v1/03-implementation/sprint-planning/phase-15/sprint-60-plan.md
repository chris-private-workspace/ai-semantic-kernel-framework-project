# Sprint 60: AG-UI Advanced Features (5-7) & Integration

## Sprint 概述

**Sprint 目標**: 實現 AG-UI 最後 3 個進階功能 (Tool-based Generative UI、Shared State、Predictive State Updates) 並完成整合測試

**Story Points**: 27 點
**預估工期**: 1 週

## User Stories

### S60-1: Tool-based Generative UI (8 pts)

**As a** 前端開發者
**I want** 基於工具的自定義 UI 組件生成和渲染系統
**So that** 工具執行結果能以豐富的視覺化組件呈現

**Acceptance Criteria**:
- [ ] 後端 `UIComponentType` 枚舉 (form, chart, card, table, list, button_group, custom)
- [ ] 後端 `UIComponentDefinition` Pydantic 模型
- [ ] 後端 `ToolBasedUIHandler` 類別
- [ ] 後端支持 `ui_component` 自定義事件
- [ ] 前端 `CustomUIRenderer` 動態組件渲染器
- [ ] 前端 `DynamicForm` 動態表單組件
- [ ] 前端 `DynamicChart` 動態圖表組件
- [ ] 前端 `DynamicCard` 動態卡片組件
- [ ] 前端 `DynamicTable` 動態表格組件
- [ ] 支持組件交互事件回傳
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/features/
└── tool_based_ui.py         # ToolBasedUIHandler, UIComponentDefinition

frontend/src/components/ag-ui/
├── CustomUIRenderer.tsx     # 動態組件渲染器
└── ui-components/
    ├── index.ts             # Barrel export
    ├── DynamicForm.tsx      # 動態表單
    ├── DynamicChart.tsx     # 動態圖表
    ├── DynamicCard.tsx      # 動態卡片
    ├── DynamicTable.tsx     # 動態表格
    ├── DynamicList.tsx      # 動態列表
    └── DynamicButtonGroup.tsx # 動態按鈕組
```

**Implementation Details**:
```python
# backend/src/integrations/ag_ui/features/tool_based_ui.py
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
from src.integrations.ag_ui.events import CustomEvent, AGUIEventType

class UIComponentType(str, Enum):
    """預定義 UI 組件類型"""
    FORM = "form"
    CHART = "chart"
    CARD = "card"
    TABLE = "table"
    LIST = "list"
    BUTTON_GROUP = "button_group"
    CUSTOM = "custom"

class UIComponentDefinition(BaseModel):
    """UI 組件定義"""
    component_type: UIComponentType
    component_id: str
    props: Dict[str, Any]
    children: Optional[List["UIComponentDefinition"]] = None
    events: Optional[List[str]] = None

class ToolBasedUIHandler:
    """工具式 UI 生成處理器"""

    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry

    async def generate_ui_component(
        self,
        tool_name: str,
        tool_result: Any,
        context: HybridContext,
    ) -> Optional[CustomEvent]:
        """根據工具結果生成 UI 組件"""
        tool_config = self.registry.get_tool_config(tool_name)
        if not tool_config.ui_rendering:
            return None

        component = self._build_component(tool_config.ui_template, tool_result)

        return CustomEvent(
            type=AGUIEventType.CUSTOM,
            name="ui_component",
            data={
                "component_id": component.component_id,
                "component_type": component.component_type.value,
                "props": component.props,
                "children": [c.model_dump() for c in component.children] if component.children else None,
                "events": component.events,
            },
        )

    def _build_component(
        self,
        template: str,
        data: Any,
    ) -> UIComponentDefinition:
        """根據模板和數據建構組件"""
        ...
```

```tsx
// frontend/src/components/ag-ui/CustomUIRenderer.tsx
import dynamic from 'next/dynamic';

const componentMap: Record<string, React.ComponentType<any>> = {
  form: dynamic(() => import('./ui-components/DynamicForm')),
  chart: dynamic(() => import('./ui-components/DynamicChart')),
  card: dynamic(() => import('./ui-components/DynamicCard')),
  table: dynamic(() => import('./ui-components/DynamicTable')),
  list: dynamic(() => import('./ui-components/DynamicList')),
  button_group: dynamic(() => import('./ui-components/DynamicButtonGroup')),
};

interface CustomUIRendererProps {
  componentId: string;
  componentType: string;
  props: Record<string, any>;
  children?: any[];
  events?: string[];
  onEvent: (eventName: string, data: any) => void;
}

export function CustomUIRenderer({
  componentId,
  componentType,
  props,
  children,
  events,
  onEvent,
}: CustomUIRendererProps) {
  const Component = componentMap[componentType];

  if (!Component) {
    return (
      <div className="p-4 border border-dashed rounded text-muted-foreground">
        未知組件類型: {componentType}
      </div>
    );
  }

  const eventHandlers = events?.reduce((acc, eventName) => {
    acc[`on${eventName.charAt(0).toUpperCase() + eventName.slice(1)}`] = (data: any) => {
      onEvent(eventName, { componentId, ...data });
    };
    return acc;
  }, {} as Record<string, (data: any) => void>) || {};

  return (
    <Component {...props} {...eventHandlers}>
      {children?.map((child, index) => (
        <CustomUIRenderer
          key={child.component_id || index}
          {...child}
          onEvent={onEvent}
        />
      ))}
    </Component>
  );
}
```

---

### S60-2: Shared State (8 pts)

**As a** 後端開發者
**I want** 前後端雙向狀態同步機制
**So that** 應用狀態能在前後端保持一致

**Acceptance Criteria**:
- [ ] 後端 `SharedStateHandler` 整合 ContextBridge
- [ ] 後端生成 `StateSnapshotEvent` 和 `StateDeltaEvent`
- [ ] 後端支持狀態 Schema 驗證
- [ ] 後端支持衝突解決策略 (last_write_wins, local_priority, remote_priority)
- [ ] 前端 `useSharedState` Hook
- [ ] 前端 `StateSyncManager` 組件
- [ ] 前端支持防抖發送
- [ ] 前端支持衝突解決
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/features/
└── shared_state.py          # SharedStateHandler, StateChange

frontend/src/
├── hooks/
│   └── useSharedState.ts    # 共享狀態 Hook
└── components/ag-ui/
    └── StateSyncManager.tsx # 狀態同步管理器
```

**Implementation Details**:
```python
# backend/src/integrations/ag_ui/features/shared_state.py
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from src.integrations.hybrid.context import ContextBridge
from src.integrations.ag_ui.events import StateSnapshotEvent, StateDeltaEvent, AGUIEventType

class StateChange(BaseModel):
    """狀態變更"""
    path: str
    old_value: Any
    new_value: Any
    source: str  # "frontend" | "backend"
    timestamp: datetime

class SharedStateHandler:
    """共享狀態處理器"""

    def __init__(
        self,
        context_bridge: ContextBridge,
        state_schema: Optional[Dict[str, Any]] = None,
    ):
        self.context_bridge = context_bridge
        self.state_schema = state_schema
        self._state_version: int = 0

    async def get_full_state(self, session_id: str) -> StateSnapshotEvent:
        """獲取完整狀態快照"""
        state = await self.context_bridge.get_unified_state(session_id)
        self._state_version += 1

        return StateSnapshotEvent(
            type=AGUIEventType.STATE_SNAPSHOT,
            state=state,
            version=self._state_version,
        )

    async def apply_delta(
        self,
        session_id: str,
        delta: Dict[str, Any],
        source: str = "frontend",
    ) -> StateDeltaEvent:
        """應用增量狀態更新"""
        if self.state_schema:
            self._validate_delta(delta)

        await self.context_bridge.apply_state_delta(session_id, delta)
        self._state_version += 1

        return StateDeltaEvent(
            type=AGUIEventType.STATE_DELTA,
            delta=delta,
            version=self._state_version,
            source=source,
        )

    async def handle_conflict(
        self,
        local_state: Dict[str, Any],
        remote_state: Dict[str, Any],
        strategy: str = "last_write_wins",
    ) -> Dict[str, Any]:
        """處理狀態衝突"""
        match strategy:
            case "last_write_wins":
                return remote_state
            case "local_priority":
                return {**remote_state, **local_state}
            case "remote_priority":
                return {**local_state, **remote_state}
            case _:
                raise ValueError(f"Unknown strategy: {strategy}")
```

```tsx
// frontend/src/hooks/useSharedState.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAGUI } from '@/providers/AGUIProvider';

interface UseSharedStateOptions {
  conflictStrategy?: 'last_write_wins' | 'local_priority' | 'remote_priority';
  debounceMs?: number;
}

export function useSharedState<T extends Record<string, any>>(
  options: UseSharedStateOptions = {}
) {
  const { sharedState, updateState } = useAGUI();
  const [localState, setLocalState] = useState<T>(sharedState as T);
  const [version, setVersion] = useState(0);
  const pendingUpdates = useRef<Map<string, any>>(new Map());

  const { conflictStrategy = 'last_write_wins', debounceMs = 100 } = options;

  useEffect(() => {
    setLocalState(prev => {
      const hasConflict = Object.keys(pendingUpdates.current).some(
        key => sharedState[key] !== pendingUpdates.current.get(key)
      );

      if (hasConflict) {
        return resolveConflict(prev, sharedState as T, conflictStrategy);
      }

      return sharedState as T;
    });
  }, [sharedState, conflictStrategy]);

  const setValue = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setLocalState(prev => ({ ...prev, [key]: value }));
    pendingUpdates.current.set(key as string, value);

    debounce(() => {
      updateState(key as string, value);
      pendingUpdates.current.delete(key as string);
    }, debounceMs);
  }, [updateState, debounceMs]);

  return {
    state: localState,
    setValue,
    version,
    isPending: pendingUpdates.current.size > 0,
  };
}
```

---

### S60-3: Predictive State Updates (6 pts)

**As a** 用戶
**I want** 操作有即時視覺反饋
**So that** 不用等待後端確認就能看到結果

**Acceptance Criteria**:
- [ ] 後端 `PredictiveStateConfig` 配置模型
- [ ] 後端 `PredictiveStateHandler` 類別
- [ ] 後端支持預測器註冊
- [ ] 後端支持預測確認和回滾
- [ ] 前端 `useOptimisticState` Hook
- [ ] 前端支持樂觀更新
- [ ] 前端支持更新失敗回滾
- [ ] 前端視覺回滾動畫
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/features/
└── predictive_state.py      # PredictiveStateHandler

frontend/src/hooks/
└── useOptimisticState.ts    # 樂觀狀態 Hook
```

**Implementation Details**:
```python
# backend/src/integrations/ag_ui/features/predictive_state.py
from typing import Dict, Any, Callable, Optional, List
import uuid
from pydantic import BaseModel
from src.integrations.ag_ui.events import StateDeltaEvent, AGUIEventType

class PredictiveStateConfig(BaseModel):
    """樂觀更新配置"""
    tool_name: str
    predict_fn: str
    affected_state_paths: List[str]
    rollback_on_failure: bool = True

class PredictiveStateHandler:
    """樂觀狀態更新處理器"""

    def __init__(
        self,
        predictors: Optional[Dict[str, Callable]] = None,
    ):
        self.predictors = predictors or {}
        self._pending_predictions: Dict[str, Dict[str, Any]] = {}

    def register_predictor(
        self,
        name: str,
        predict_fn: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    ):
        """註冊預測器"""
        self.predictors[name] = predict_fn

    async def predict_state_update(
        self,
        config: PredictiveStateConfig,
        tool_args: Dict[str, Any],
        current_state: Dict[str, Any],
    ) -> Optional[StateDeltaEvent]:
        """預測狀態更新"""
        predictor = self.predictors.get(config.predict_fn)
        if not predictor:
            return None

        predicted_delta = predictor(tool_args, current_state)

        prediction_id = str(uuid.uuid4())
        self._pending_predictions[prediction_id] = {
            "config": config,
            "original_state": {
                path: self._get_nested(current_state, path)
                for path in config.affected_state_paths
            },
            "predicted_delta": predicted_delta,
        }

        return StateDeltaEvent(
            type=AGUIEventType.STATE_DELTA,
            delta=predicted_delta,
            prediction_id=prediction_id,
            is_prediction=True,
        )

    async def confirm_prediction(self, prediction_id: str) -> None:
        """確認預測"""
        self._pending_predictions.pop(prediction_id, None)

    async def rollback_prediction(
        self,
        prediction_id: str,
    ) -> Optional[StateDeltaEvent]:
        """回滾預測"""
        prediction = self._pending_predictions.pop(prediction_id, None)
        if not prediction:
            return None

        return StateDeltaEvent(
            type=AGUIEventType.STATE_DELTA,
            delta=prediction["original_state"],
            prediction_id=prediction_id,
            is_rollback=True,
        )
```

```tsx
// frontend/src/hooks/useOptimisticState.ts
import { useState, useCallback, useRef } from 'react';

interface OptimisticUpdate<T> {
  predictionId: string;
  originalValue: T;
  predictedValue: T;
  timestamp: number;
}

export function useOptimisticState<T>(
  initialValue: T,
  onCommit: (value: T) => Promise<boolean>,
) {
  const [value, setValue] = useState<T>(initialValue);
  const pendingUpdates = useRef<Map<string, OptimisticUpdate<T>>>(new Map());

  const optimisticUpdate = useCallback(async (
    predictedValue: T,
    predictionId?: string,
  ) => {
    const id = predictionId || `local_${Date.now()}`;

    pendingUpdates.current.set(id, {
      predictionId: id,
      originalValue: value,
      predictedValue,
      timestamp: Date.now(),
    });

    setValue(predictedValue);

    try {
      const success = await onCommit(predictedValue);
      if (success) {
        pendingUpdates.current.delete(id);
      } else {
        rollback(id);
      }
    } catch (error) {
      rollback(id);
    }
  }, [value, onCommit]);

  const rollback = useCallback((predictionId: string) => {
    const update = pendingUpdates.current.get(predictionId);
    if (update) {
      setValue(update.originalValue);
      pendingUpdates.current.delete(predictionId);
    }
  }, []);

  const confirmPrediction = useCallback((predictionId: string) => {
    pendingUpdates.current.delete(predictionId);
  }, []);

  return {
    value,
    optimisticUpdate,
    rollback,
    confirmPrediction,
    hasPending: pendingUpdates.current.size > 0,
  };
}
```

---

### S60-4: Integration & E2E Testing (5 pts)

**As a** QA 工程師
**I want** 完整的 AG-UI 功能整合測試
**So that** 確保所有功能正確運作且整合無誤

**Acceptance Criteria**:
- [ ] 7 大功能 E2E 測試
- [ ] 效能測試 (狀態同步延遲 < 50ms)
- [ ] 效能測試 (樂觀更新回滾時間 < 100ms)
- [ ] 效能測試 (UI 組件渲染時間 < 200ms)
- [ ] API 文檔更新
- [ ] AG-UI 整合使用指南
- [ ] Code Review 完成

**Technical Tasks**:
```
backend/tests/e2e/ag_ui/
├── test_full_flow.py        # 完整流程 E2E 測試
└── test_performance.py      # 效能測試

frontend/tests/e2e/ag-ui/
└── full-flow.spec.ts        # 前端 E2E 測試

docs/guides/
└── ag-ui-integration-guide.md  # 整合使用指南
```

**Implementation Details**:
```python
# backend/tests/e2e/ag_ui/test_full_flow.py
import pytest
import httpx
from httpx_sse import aiter_sse
import json

@pytest.mark.e2e
class TestAGUIFullFlow:
    """AG-UI 完整流程 E2E 測試"""

    async def test_agentic_chat_flow(self, test_client: httpx.AsyncClient):
        """Feature 1: Agentic Chat"""
        async with aiter_sse(test_client.post("/api/v1/ag-ui", json={
            "messages": [{"role": "user", "content": "Hello!"}],
        })) as events:
            event_types = [e.event async for e in events]

        assert "RUN_STARTED" in event_types
        assert "TEXT_MESSAGE_START" in event_types
        assert "TEXT_MESSAGE_CONTENT" in event_types
        assert "TEXT_MESSAGE_END" in event_types
        assert "RUN_FINISHED" in event_types

    async def test_tool_rendering_flow(self, test_client):
        """Feature 2: Backend Tool Rendering"""
        async with aiter_sse(test_client.post("/api/v1/ag-ui", json={
            "messages": [{"role": "user", "content": "Search for Python"}],
            "tools": [{"name": "search", "description": "Web search"}],
        })) as events:
            tool_events = [e async for e in events if "TOOL_CALL" in e.event]

        assert any(e.event == "TOOL_CALL_END" for e in tool_events)

    async def test_human_in_loop_flow(self, test_client):
        """Feature 3: Human-in-the-Loop"""
        events = []
        async with aiter_sse(test_client.post("/api/v1/ag-ui", json={
            "messages": [{"role": "user", "content": "Delete all files"}],
        })) as sse:
            async for e in sse:
                events.append(e)
                if e.event == "CUSTOM" and "approval_required" in e.data:
                    approval_data = json.loads(e.data)
                    await test_client.post(
                        f"/api/v1/ag-ui/approvals/{approval_data['approval_id']}/approve"
                    )

    async def test_generative_ui_progress(self, test_client):
        """Feature 4: Agentic Generative UI"""
        async with aiter_sse(test_client.post("/api/v1/ag-ui", json={
            "messages": [{"role": "user", "content": "Run workflow"}],
        })) as events:
            progress_events = [e async for e in events if "workflow_progress" in str(e.data)]

        assert len(progress_events) > 0

    async def test_tool_based_ui(self, test_client):
        """Feature 5: Tool-based Generative UI"""
        async with aiter_sse(test_client.post("/api/v1/ag-ui", json={
            "messages": [{"role": "user", "content": "Create chart"}],
            "tools": [{"name": "create_chart", "ui_rendering": True}],
        })) as events:
            ui_events = [e async for e in events if "ui_component" in str(e.data)]

        assert len(ui_events) > 0

    async def test_shared_state_sync(self, test_client):
        """Feature 6: Shared State"""
        async with aiter_sse(test_client.post("/api/v1/ag-ui", json={
            "messages": [{"role": "user", "content": "Update my name"}],
            "state": {"user_name": "Alice"},
        })) as events:
            state_events = [e async for e in events if "STATE" in e.event]

        assert any(e.event == "STATE_SNAPSHOT" for e in state_events)

    async def test_predictive_state_updates(self, test_client):
        """Feature 7: Predictive State Updates"""
        async with aiter_sse(test_client.post("/api/v1/ag-ui", json={
            "messages": [{"role": "user", "content": "Add item"}],
            "state": {"items": []},
        })) as events:
            delta_events = [e async for e in events if "is_prediction" in str(e.data)]

        assert len(delta_events) > 0
```

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| AG-UI Basic Features | Sprint 59 | 📋 待完成 |
| HybridEventBridge | Sprint 58 | 📋 待完成 |
| ContextBridge | Phase 13 | ✅ 已完成 |
| ToolRegistry | Phase 12 | ✅ 已完成 |

## 新增前端依賴

```json
{
  "dependencies": {
    "recharts": "^2.10.0"
  }
}
```

## 效能目標

| 指標 | 目標值 |
|------|--------|
| 狀態同步延遲 | < 50ms |
| 樂觀更新回滾時間 | < 100ms |
| UI 組件渲染時間 | < 200ms |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 後端單元測試覆蓋率 > 85%
- [ ] 前端組件測試完成
- [ ] 7 大功能 E2E 測試全部通過
- [ ] 效能測試達標
- [ ] API 文檔更新
- [ ] 整合使用指南完成
- [ ] Code Review 完成
