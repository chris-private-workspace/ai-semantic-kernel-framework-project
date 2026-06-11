# Sprint 116: 架構加固

## 概述

Sprint 116 專注於架構層面的關鍵加固：將 Swarm 整合到主編排流程、拆分 Layer 4 為 Input Processing 和 Decision Engine、修復 L5-L6 循環依賴。這些改進消除已知的架構瓶頸，為 AD 場景的完整執行提供堅實的架構基礎。

## 目標

1. 將 Swarm 整合到 `execute_with_routing()` 主流程（不再只是獨立的 demo API）
2. 拆分 Layer 4 為 L4a（Input Processing）和 L4b（Decision Engine）
3. 引入 `ToolCallbackProtocol` 修復 L5-L6 循環依賴

## Story Points: 45 點

## 前置條件

- ✅ Sprint 115 完成（SemanticRouter Real 實現）
- ✅ Phase 31 Mock 分離完成（架構邊界清晰）
- ✅ Swarm 模組就緒 (`backend/src/integrations/swarm/`)
- ✅ Hybrid 模組就緒 (`backend/src/integrations/hybrid/`)

## 任務分解

### Story 116-1: Swarm 整合到 execute_with_routing() (3 天, P1)

**目標**: 在 `HybridOrchestratorV2.execute_with_routing()` 中新增 `SWARM_MODE`，使 Swarm 不再是獨立的 demo API，而是主編排流程的一部分

**交付物**:
- 修改 `backend/src/integrations/hybrid/orchestrator.py`（或對應的 HybridOrchestratorV2 文件）
- 修改 `backend/src/integrations/swarm/swarm_integration.py`
- 新增 `backend/src/integrations/hybrid/swarm_mode.py`
- 新增 `backend/tests/unit/hybrid/test_swarm_mode.py`
- 新增 `backend/tests/integration/hybrid/test_swarm_routing.py`

**設計方式**:

```python
# swarm_mode.py
from enum import Enum
from typing import Optional, Dict, Any


class ExecutionMode(str, Enum):
    """編排執行模式"""
    SINGLE_AGENT = "single_agent"      # 現有: 單 Agent 執行
    HANDOFF = "handoff"                # 現有: Agent 交接
    SWARM_MODE = "swarm_mode"          # 🆕 Swarm 多 Agent 協作


class SwarmModeHandler:
    """Swarm 模式處理器 — 整合到主流程"""

    def __init__(
        self,
        swarm_integration: SwarmIntegration,
        coordinator: ClaudeCoordinator,
    ):
        self._swarm = swarm_integration
        self._coordinator = coordinator

    async def should_use_swarm(
        self, intent: str, context: Dict[str, Any]
    ) -> bool:
        """判斷是否應使用 Swarm 模式"""
        # 基於 intent 複雜度、工具數量、子任務數量判斷
        ...

    async def execute_swarm(
        self, intent: str, context: Dict[str, Any]
    ) -> ExecutionResult:
        """以 Swarm 模式執行"""
        ...
```

**整合邏輯**:
- `execute_with_routing()` 在 intent 解析後，判斷是否需要 Swarm 模式
- 判斷依據：intent 涉及多個子任務、需要多個 MCP 工具協作、使用者明確指定 swarm
- Swarm 模式執行時：
  1. 建立 Swarm（`SwarmIntegration.on_coordination_started()`）
  2. 分配 Worker（每個子任務一個 Worker）
  3. 執行並追蹤（透過 `SwarmTracker` + `SwarmEventEmitter`）
  4. 回報結果
- 不影響現有的 `SINGLE_AGENT` 和 `HANDOFF` 模式

**驗收標準**:
- [ ] `ExecutionMode` 包含 `SWARM_MODE`
- [ ] `SwarmModeHandler` 完整實現
- [ ] `execute_with_routing()` 正確分流到 Swarm
- [ ] 現有 `SINGLE_AGENT` 和 `HANDOFF` 模式不受影響
- [ ] Swarm 事件系統正常觸發（SSE）
- [ ] 向後兼容（Swarm 為可選功能）
- [ ] 整合測試通過

### Story 116-2: Layer 4 拆分 — L4a Input Processing + L4b Decision Engine (3-4 天, P1)

**目標**: 將當前過於龐大的 Layer 4 拆分為兩個獨立子層，提升架構清晰度和可維護性

**交付物**:
- 新增 `backend/src/integrations/orchestration/input/` 目錄（L4a）
- 重組 `backend/src/integrations/orchestration/routing/` 目錄（L4b）
- 修改相關 import 路徑
- 新增 `backend/src/integrations/orchestration/contracts.py`
- 新增 `backend/tests/unit/orchestration/test_layer_contracts.py`

**架構設計**:

```
# 重構前 (Layer 4 混合)
orchestration/
├── routing/          # PatternMatcher + SemanticRouter + LLMClassifier 混在一起
├── input/            # Sprint 114 新增的 Webhook/RITM (已在正確位置)
└── ...

# 重構後 (L4a + L4b 分離)
orchestration/
├── input/            # L4a: Input Processing
│   ├── __init__.py
│   ├── contracts.py          # InputGateway 介面定義
│   ├── servicenow_webhook.py # ServiceNow Webhook
│   ├── ritm_intent_mapper.py # RITM 映射
│   ├── http_input.py         # HTTP API 輸入 (現有)
│   └── sse_input.py          # SSE 輸入 (現有)
│
├── routing/          # L4b: Decision Engine
│   ├── __init__.py
│   ├── contracts.py          # Router 介面定義
│   ├── pattern_matcher.py
│   ├── rules.yaml
│   └── business_intent_router.py
│
├── intent_router/    # L4b 子模組: 語義路由
│   └── semantic_router/
│       ├── azure_semantic_router.py
│       ├── route_manager.py
│       └── ...
│
└── contracts.py      # 🆕 共享契約 (L4a → L4b 介面)
```

**共享契約設計**:

```python
# contracts.py — L4a 和 L4b 之間的契約
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class InputEvent(ABC):
    """輸入事件基類"""
    @abstractmethod
    def to_routing_request(self) -> "RoutingRequest": ...


class RoutingRequest:
    """路由請求 — L4a 輸出、L4b 輸入"""
    query: str
    intent_hint: Optional[str]
    context: Dict[str, Any]
    source: str  # "webhook", "http", "sse"
    metadata: Dict[str, Any]


class RoutingResult:
    """路由結果 — L4b 輸出"""
    intent: str
    confidence: float
    matched_layer: str  # "pattern", "semantic", "llm"
    workflow_type: str
    risk_level: str
    metadata: Dict[str, Any]
```

**驗收標準**:
- [ ] L4a（Input Processing）目錄結構完整
- [ ] L4b（Decision Engine）目錄結構完整
- [ ] 共享契約 `contracts.py` 定義清晰
- [ ] 所有 import 路徑更新完成
- [ ] InputEvent → RoutingRequest → RoutingResult 資料流正確
- [ ] 現有功能不受影響（回歸測試）
- [ ] 契約測試通過

### Story 116-3: L5-L6 循環依賴修復 (1-2 天, P1)

**目標**: 引入 `ToolCallbackProtocol` 作為共享介面，打破 Orchestration（L5）和 Execution Engines（L6）之間的循環依賴

**交付物**:
- 新增 `backend/src/integrations/shared/protocols.py`
- 修改 L5（orchestration）相關文件
- 修改 L6（claude_sdk / agent_framework）相關文件
- 新增 `backend/tests/unit/shared/test_protocols.py`

**問題描述**:
```
# 循環依賴
L5 (orchestration) imports L6 (claude_sdk) for execution
L6 (claude_sdk) imports L5 (orchestration) for tool callbacks
→ Circular import error
```

**解決方案**:

```python
# shared/protocols.py — 共享 Protocol 介面
from typing import Protocol, Dict, Any, Optional


class ToolCallbackProtocol(Protocol):
    """工具調用回調 — L5 和 L6 共享介面"""

    async def on_tool_call(
        self, tool_name: str, input_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """工具被調用時"""
        ...

    async def on_tool_result(
        self, tool_name: str, result: Any, error: Optional[str] = None
    ) -> None:
        """工具調用完成時"""
        ...


class ExecutionEngineProtocol(Protocol):
    """執行引擎 — L6 實現、L5 依賴的介面"""

    async def execute(
        self, intent: str, context: Dict[str, Any]
    ) -> "ExecutionResult":
        ...
```

**修改方式**:
- L5 依賴 `ToolCallbackProtocol`（在 shared/ 中定義）
- L6 實現 `ToolCallbackProtocol`
- 不再直接 import 對方模組
- 使用 Dependency Injection 在 runtime 注入

**驗收標準**:
- [ ] `ToolCallbackProtocol` 定義在 `shared/protocols.py`
- [ ] L5 只 import `shared/protocols.py`，不直接 import L6
- [ ] L6 只 import `shared/protocols.py`，不直接 import L5
- [ ] 循環依賴消除（`python -c "import orchestration; import claude_sdk"` 不報錯）
- [ ] 現有功能正常（Protocol 的 structural subtyping 保證兼容）
- [ ] 單元測試驗證 Protocol 合規

## 技術設計

### 依賴關係修復後

```
L4a (Input) → contracts → L4b (Routing)
                              ↓
L5 (Orchestration) → shared/protocols ← L6 (Execution)
                              ↓
                        L7 (MCP Tools)
```

### 風險控制

| 步驟 | 風險等級 | 回歸策略 |
|------|---------|---------|
| Swarm 整合 | 中 | Feature flag `SWARM_MODE_ENABLED` |
| Layer 4 拆分 | 高 | 保留舊 import 路徑 re-export、漸進式遷移 |
| L5-L6 修復 | 低 | Protocol structural subtyping 保證兼容 |

## 依賴

```
# 無新增外部依賴
# 全部使用 Python 標準庫 (typing, abc, Protocol)
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| Layer 4 拆分影響範圍廣 | 保留舊 import re-export、逐步遷移 |
| Swarm 整合影響現有流程 | Feature flag 控制、充分回歸測試 |
| 循環依賴修復不完整 | Protocol 的 structural subtyping 降低風險 |

## 完成標準

- [ ] Swarm 整合到 `execute_with_routing()` 主流程
- [ ] Layer 4 拆分完成（L4a + L4b）
- [ ] L5-L6 循環依賴消除
- [ ] 所有現有功能回歸測試通過
- [ ] 架構文檔更新

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: TBD
