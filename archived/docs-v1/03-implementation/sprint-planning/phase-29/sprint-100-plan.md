# Sprint 100: Swarm 數據模型 + 後端 API

## 概述

Sprint 100 是 Phase 29 的第一個 Sprint，專注於建立 Agent Swarm 的核心數據模型、狀態追蹤器和後端 API 端點。

## 目標

1. 定義 Swarm 核心數據模型 (WorkerType, WorkerStatus, SwarmMode, SwarmStatus 等)
2. 實現 SwarmTracker 狀態追蹤器
3. 建立 Swarm API 端點
4. 整合 ClaudeCoordinator

## Story Points: 28 點

## 前置條件

- ✅ Phase 28 完成 (三層意圖路由系統)
- ✅ AG-UI Protocol 就緒
- ✅ ClaudeCoordinator 就緒

## 任務分解

### Story 100-1: 定義 Swarm 核心數據模型 (5h, P0)

**目標**: 定義所有 Swarm 相關的數據結構

**交付物**:
- `backend/src/integrations/swarm/__init__.py`
- `backend/src/integrations/swarm/models.py`

**數據模型設計**:

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

class WorkerType(str, Enum):
    """Worker 類型"""
    RESEARCH = "research"
    WRITER = "writer"
    DESIGNER = "designer"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"
    CUSTOM = "custom"

class WorkerStatus(str, Enum):
    """Worker 執行狀態"""
    PENDING = "pending"
    RUNNING = "running"
    THINKING = "thinking"
    TOOL_CALLING = "tool_calling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SwarmMode(str, Enum):
    """Swarm 執行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"

class SwarmStatus(str, Enum):
    """Swarm 整體狀態"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ToolCallInfo:
    """工具調用資訊"""
    tool_id: str
    tool_name: str
    is_mcp: bool
    input_params: Dict[str, Any]
    status: str  # "pending", "running", "completed", "failed"
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

@dataclass
class ThinkingContent:
    """Extended Thinking 內容"""
    content: str
    timestamp: datetime
    token_count: Optional[int] = None

@dataclass
class WorkerMessage:
    """Worker 對話訊息"""
    role: str  # "user", "assistant"
    content: str
    timestamp: datetime
    thinking: Optional[List[ThinkingContent]] = None

@dataclass
class WorkerExecution:
    """單個 Worker 的執行狀態"""
    worker_id: str
    worker_name: str
    worker_type: WorkerType
    role: str
    status: WorkerStatus
    progress: int  # 0-100
    current_task: Optional[str] = None
    tool_calls: List[ToolCallInfo] = field(default_factory=list)
    thinking_contents: List[ThinkingContent] = field(default_factory=list)
    messages: List[WorkerMessage] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentSwarmStatus:
    """Agent Swarm 整體狀態"""
    swarm_id: str
    mode: SwarmMode
    status: SwarmStatus
    overall_progress: int  # 0-100
    workers: List[WorkerExecution]
    total_tool_calls: int
    completed_tool_calls: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**驗收標準**:
- [ ] 所有 Enum 類型定義完整
- [ ] 所有 dataclass 定義完整
- [ ] 類型註解完整
- [ ] 可正確序列化為 JSON

### Story 100-2: 實現 SwarmTracker 狀態追蹤器 (8h, P0)

**目標**: 實現管理 Swarm 狀態的核心追蹤器

**交付物**:
- `backend/src/integrations/swarm/tracker.py`

**核心方法**:

```python
class SwarmTracker:
    """Agent Swarm 狀態追蹤器"""

    def __init__(self, use_redis: bool = False):
        """初始化追蹤器"""

    def create_swarm(
        self,
        swarm_id: str,
        mode: SwarmMode,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentSwarmStatus:
        """創建新的 Swarm"""

    def get_swarm(self, swarm_id: str) -> Optional[AgentSwarmStatus]:
        """獲取 Swarm 狀態"""

    def complete_swarm(
        self,
        swarm_id: str,
        status: SwarmStatus = SwarmStatus.COMPLETED
    ) -> AgentSwarmStatus:
        """完成 Swarm"""

    def start_worker(
        self,
        swarm_id: str,
        worker_id: str,
        worker_name: str,
        worker_type: WorkerType,
        role: str,
        current_task: Optional[str] = None
    ) -> WorkerExecution:
        """開始新的 Worker"""

    def update_worker_progress(
        self,
        swarm_id: str,
        worker_id: str,
        progress: int,
        current_task: Optional[str] = None
    ) -> WorkerExecution:
        """更新 Worker 進度"""

    def add_worker_thinking(
        self,
        swarm_id: str,
        worker_id: str,
        content: str,
        token_count: Optional[int] = None
    ) -> ThinkingContent:
        """添加 Extended Thinking 內容"""

    def add_worker_tool_call(
        self,
        swarm_id: str,
        worker_id: str,
        tool_id: str,
        tool_name: str,
        is_mcp: bool,
        input_params: Dict[str, Any]
    ) -> ToolCallInfo:
        """添加工具調用"""

    def update_tool_call_result(
        self,
        swarm_id: str,
        worker_id: str,
        tool_id: str,
        result: Any = None,
        error: Optional[str] = None
    ) -> ToolCallInfo:
        """更新工具調用結果"""

    def add_worker_message(
        self,
        swarm_id: str,
        worker_id: str,
        role: str,
        content: str
    ) -> WorkerMessage:
        """添加 Worker 對話訊息"""

    def complete_worker(
        self,
        swarm_id: str,
        worker_id: str,
        status: WorkerStatus = WorkerStatus.COMPLETED,
        error: Optional[str] = None
    ) -> WorkerExecution:
        """完成 Worker"""

    def get_worker(
        self,
        swarm_id: str,
        worker_id: str
    ) -> Optional[WorkerExecution]:
        """獲取單個 Worker 狀態"""

    def calculate_overall_progress(self, swarm_id: str) -> int:
        """計算整體進度"""
```

**驗收標準**:
- [ ] 所有方法實現完整
- [ ] 線程安全 (使用鎖)
- [ ] 支持可選 Redis 持久化
- [ ] 單元測試覆蓋率 > 90%

### Story 100-3: 建立 Swarm API 端點 (5h, P0)

**目標**: 建立 Swarm 相關的 REST API 端點

**交付物**:
- `backend/src/api/v1/swarm/__init__.py`
- `backend/src/api/v1/swarm/schemas.py`
- `backend/src/api/v1/swarm/routes.py`
- `backend/src/api/v1/swarm/dependencies.py`

**API 設計**:

```
GET /api/v1/swarm/{swarm_id}
    Response: SwarmStatusResponse

GET /api/v1/swarm/{swarm_id}/workers
    Response: WorkerListResponse

GET /api/v1/swarm/{swarm_id}/workers/{worker_id}
    Response: WorkerDetailResponse
```

**Schema 定義**:

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ToolCallInfoSchema(BaseModel):
    tool_id: str
    tool_name: str
    is_mcp: bool
    input_params: Dict[str, Any]
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

class ThinkingContentSchema(BaseModel):
    content: str
    timestamp: datetime
    token_count: Optional[int] = None

class WorkerMessageSchema(BaseModel):
    role: str
    content: str
    timestamp: datetime

class WorkerSummarySchema(BaseModel):
    worker_id: str
    worker_name: str
    worker_type: str
    role: str
    status: str
    progress: int
    current_task: Optional[str] = None
    tool_calls_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class WorkerDetailResponse(BaseModel):
    worker_id: str
    worker_name: str
    worker_type: str
    role: str
    status: str
    progress: int
    current_task: Optional[str] = None
    tool_calls: List[ToolCallInfoSchema]
    thinking_contents: List[ThinkingContentSchema]
    messages: List[WorkerMessageSchema]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class SwarmStatusResponse(BaseModel):
    swarm_id: str
    mode: str
    status: str
    overall_progress: int
    workers: List[WorkerSummarySchema]
    total_tool_calls: int
    completed_tool_calls: int
    started_at: datetime
    completed_at: Optional[datetime] = None

class WorkerListResponse(BaseModel):
    swarm_id: str
    workers: List[WorkerSummarySchema]
    total: int
```

**驗收標準**:
- [ ] 所有端點實現完整
- [ ] Schema 定義完整
- [ ] 錯誤處理完整 (404, 500)
- [ ] 在主 router 中註冊

### Story 100-4: 整合 ClaudeCoordinator (6h, P1)

**目標**: 將 SwarmTracker 整合到現有的 ClaudeCoordinator 中

**交付物**:
- `backend/src/integrations/swarm/swarm_integration.py`
- 修改 `backend/src/integrations/claude_sdk/autonomous/coordinator.py`

**整合設計**:

```python
class SwarmIntegration:
    """Swarm 整合層，連接 ClaudeCoordinator 和 SwarmTracker"""

    def __init__(self, tracker: SwarmTracker):
        self._tracker = tracker

    def on_coordination_started(
        self,
        swarm_id: str,
        mode: SwarmMode,
        subtasks: List[Dict[str, Any]]
    ) -> AgentSwarmStatus:
        """協調開始時調用"""

    def on_subtask_started(
        self,
        swarm_id: str,
        worker_id: str,
        worker_name: str,
        worker_type: WorkerType,
        role: str,
        task_description: str
    ) -> WorkerExecution:
        """子任務開始時調用"""

    def on_subtask_progress(
        self,
        swarm_id: str,
        worker_id: str,
        progress: int,
        current_task: Optional[str] = None
    ) -> WorkerExecution:
        """子任務進度更新時調用"""

    def on_tool_call(
        self,
        swarm_id: str,
        worker_id: str,
        tool_id: str,
        tool_name: str,
        is_mcp: bool,
        input_params: Dict[str, Any]
    ) -> ToolCallInfo:
        """工具調用時調用"""

    def on_tool_result(
        self,
        swarm_id: str,
        worker_id: str,
        tool_id: str,
        result: Any = None,
        error: Optional[str] = None
    ) -> ToolCallInfo:
        """工具調用完成時調用"""

    def on_thinking(
        self,
        swarm_id: str,
        worker_id: str,
        content: str,
        token_count: Optional[int] = None
    ) -> ThinkingContent:
        """Extended Thinking 內容時調用"""

    def on_subtask_completed(
        self,
        swarm_id: str,
        worker_id: str,
        status: WorkerStatus = WorkerStatus.COMPLETED,
        error: Optional[str] = None
    ) -> WorkerExecution:
        """子任務完成時調用"""

    def on_coordination_completed(
        self,
        swarm_id: str,
        status: SwarmStatus = SwarmStatus.COMPLETED
    ) -> AgentSwarmStatus:
        """協調完成時調用"""
```

**驗收標準**:
- [ ] SwarmIntegration 實現完整
- [ ] ClaudeCoordinator 注入 SwarmIntegration
- [ ] 向後兼容 (SwarmIntegration 為可選)
- [ ] 整合測試通過

### Story 100-5: 單元測試與整合測試 (3h, P1)

**目標**: 編寫完整的測試套件

**交付物**:
- `backend/tests/unit/swarm/test_models.py`
- `backend/tests/unit/swarm/test_tracker.py`
- `backend/tests/integration/swarm/test_api.py`
- `backend/tests/integration/swarm/test_coordinator_integration.py`

**測試範圍**:

| 測試類型 | 測試內容 |
|----------|----------|
| 單元測試 | 數據模型序列化/反序列化 |
| 單元測試 | SwarmTracker 所有方法 |
| 單元測試 | 進度計算邏輯 |
| 單元測試 | 並發安全性 |
| 整合測試 | API 端點完整流程 |
| 整合測試 | ClaudeCoordinator 整合 |

**驗收標準**:
- [ ] 單元測試覆蓋率 > 90%
- [ ] 所有測試通過
- [ ] 無 flaky tests

### Story 100-6: API 文檔與開發文檔 (1h, P2)

**目標**: 編寫 API 參考文檔

**交付物**:
- `docs/api/swarm-api-reference.md`

**驗收標準**:
- [ ] API 端點說明完整
- [ ] 請求/響應示例完整
- [ ] 錯誤碼說明完整

## 技術設計

### 目錄結構

```
backend/src/integrations/swarm/
├── __init__.py
├── models.py           # 數據模型
├── tracker.py          # SwarmTracker
├── swarm_integration.py # 整合層
└── events/             # Sprint 101 (事件系統)

backend/src/api/v1/swarm/
├── __init__.py
├── schemas.py          # Pydantic schemas
├── routes.py           # API routes
└── dependencies.py     # FastAPI dependencies
```

### 線程安全設計

```python
import threading
from typing import Dict

class SwarmTracker:
    def __init__(self):
        self._swarms: Dict[str, AgentSwarmStatus] = {}
        self._lock = threading.RLock()

    def get_swarm(self, swarm_id: str) -> Optional[AgentSwarmStatus]:
        with self._lock:
            return self._swarms.get(swarm_id)
```

## 依賴

```
# 無新增依賴，使用現有套件
pydantic>=2.0
fastapi>=0.100
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| 數據模型過於複雜 | 採用漸進式設計，先實現核心欄位 |
| ClaudeCoordinator 整合困難 | 使用 adapter pattern 保持向後兼容 |
| 並發問題 | 使用 RLock 確保線程安全 |

## 完成標準

- [ ] 所有數據模型定義正確
- [ ] SwarmTracker 正常運作
- [ ] API 端點返回正確數據
- [ ] ClaudeCoordinator 整合成功
- [ ] 測試覆蓋率 > 90%

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 28
**開始日期**: 2026-01-30
