# Sprint 53: Context Bridge & Sync

## Sprint 概述

**Sprint 目標**: 實現跨框架上下文橋接，確保 MAF 和 Claude 狀態同步

**Story Points**: 35 點
**預估工期**: 1 週

## User Stories

### S53-1: Context Bridge 核心實現 (13 pts)

**As a** 系統架構師
**I want** 一個跨框架上下文橋接器
**So that** MAF Workflow 和 Claude Session 能共享狀態

**Acceptance Criteria**:
- [ ] ContextBridge 類別實現
- [ ] MAFContext 資料模型 (workflow state, checkpoints, agent states)
- [ ] ClaudeContext 資料模型 (session history, tool calls, context vars)
- [ ] HybridContext 合併模型
- [ ] 雙向同步方法 (sync_to_claude, sync_to_maf)
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/hybrid/
├── context/
│   ├── __init__.py
│   ├── bridge.py           # ContextBridge 主類別
│   ├── models.py           # MAFContext, ClaudeContext, HybridContext
│   ├── mappers/
│   │   ├── __init__.py
│   │   ├── maf_mapper.py   # MAF 狀態映射器
│   │   └── claude_mapper.py # Claude 狀態映射器
│   ├── sync/
│   │   ├── __init__.py
│   │   ├── synchronizer.py # 同步邏輯
│   │   └── conflict.py     # 衝突解決策略
│   └── tests/
│       └── test_bridge.py
```

**Implementation Details**:
```python
# models.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass
class MAFContext:
    """Microsoft Agent Framework 上下文"""
    workflow_id: str
    workflow_name: str
    current_step: int
    total_steps: int
    agent_states: Dict[str, AgentState]
    checkpoint_data: Dict[str, Any]
    pending_approvals: List[ApprovalRequest]
    execution_history: List[ExecutionRecord]
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ClaudeContext:
    """Claude Agent SDK 上下文"""
    session_id: str
    conversation_history: List[Message]
    tool_call_history: List[ToolCall]
    current_system_prompt: str
    context_variables: Dict[str, Any]
    active_hooks: List[str]
    mcp_server_states: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class HybridContext:
    """合併的混合上下文"""
    maf: Optional[MAFContext]
    claude: Optional[ClaudeContext]
    primary_framework: str  # "maf" | "claude"
    sync_status: SyncStatus
    version: int
    created_at: datetime
    updated_at: datetime

# bridge.py
class ContextBridge:
    def __init__(
        self,
        maf_mapper: MAFMapper,
        claude_mapper: ClaudeMapper,
        synchronizer: ContextSynchronizer,
    ):
        self.maf_mapper = maf_mapper
        self.claude_mapper = claude_mapper
        self.synchronizer = synchronizer

    async def sync_to_claude(
        self,
        maf_context: MAFContext,
        existing_claude: Optional[ClaudeContext] = None,
    ) -> ClaudeContext:
        """
        將 MAF 上下文同步到 Claude

        轉換:
        - workflow_id → session metadata
        - checkpoint_data → context_variables
        - execution_history → conversation_history (摘要)
        - pending_approvals → tool_call_history (待處理)
        """
        ...

    async def sync_to_maf(
        self,
        claude_context: ClaudeContext,
        existing_maf: Optional[MAFContext] = None,
    ) -> MAFContext:
        """
        將 Claude 上下文同步回 MAF

        轉換:
        - conversation_history → execution_history
        - tool_call_history → checkpoint updates
        - context_variables → workflow metadata
        """
        ...
```

---

### S53-2: 狀態映射器實現 (10 pts)

**As a** 開發者
**I want** 精確的狀態映射邏輯
**So that** 兩框架間的資料轉換準確無誤

**Acceptance Criteria**:
- [ ] MAFMapper 實現所有 MAF 狀態類型映射
- [ ] ClaudeMapper 實現所有 Claude 狀態類型映射
- [ ] 支持 Checkpoint 資料結構映射
- [ ] 支持對話歷史壓縮與展開
- [ ] 映射錯誤處理與日誌

**Technical Tasks**:
```python
# maf_mapper.py
class MAFMapper:
    """MAF 狀態映射器"""

    def to_claude_context_vars(
        self,
        checkpoint: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Checkpoint → Claude context variables"""
        ...

    def to_claude_history(
        self,
        execution_records: List[ExecutionRecord],
        max_messages: int = 50,
    ) -> List[Message]:
        """執行記錄 → 對話歷史 (壓縮)"""
        ...

    def agent_state_to_system_prompt(
        self,
        agent_states: Dict[str, AgentState],
    ) -> str:
        """Agent 狀態 → System prompt 附加資訊"""
        ...

# claude_mapper.py
class ClaudeMapper:
    """Claude 狀態映射器"""

    def to_maf_checkpoint(
        self,
        context_vars: Dict[str, Any],
        tool_calls: List[ToolCall],
    ) -> Dict[str, Any]:
        """Claude 上下文 → MAF Checkpoint"""
        ...

    def to_execution_records(
        self,
        conversation: List[Message],
    ) -> List[ExecutionRecord]:
        """對話歷史 → MAF 執行記錄"""
        ...
```

---

### S53-3: 同步機制與衝突解決 (7 pts)

**As a** 開發者
**I want** 可靠的同步機制
**So that** 並發更新不會導致資料不一致

**Acceptance Criteria**:
- [ ] ContextSynchronizer 實現
- [ ] 樂觀鎖版本控制
- [ ] 衝突檢測與解決策略
- [ ] 同步事件發布
- [ ] 同步失敗回滾機制

**Technical Tasks**:
```python
# sync/synchronizer.py
class ContextSynchronizer:
    """上下文同步器"""

    def __init__(
        self,
        cache: Redis,
        event_publisher: EventPublisher,
        conflict_resolver: ConflictResolver,
    ):
        ...

    async def sync(
        self,
        source: Union[MAFContext, ClaudeContext],
        target_type: str,  # "maf" | "claude"
        strategy: SyncStrategy = SyncStrategy.MERGE,
    ) -> SyncResult:
        """
        同步上下文

        策略:
        - MERGE: 合併兩邊變更
        - SOURCE_WINS: 來源覆蓋目標
        - TARGET_WINS: 保留目標
        - MANUAL: 需要人工介入
        """
        ...

    async def detect_conflict(
        self,
        local: HybridContext,
        remote: HybridContext,
    ) -> Optional[Conflict]:
        """檢測版本衝突"""
        ...

# sync/conflict.py
class ConflictResolver:
    """衝突解決器"""

    def resolve(
        self,
        conflict: Conflict,
        strategy: ConflictStrategy,
    ) -> Resolution:
        """
        解決衝突

        優先級:
        1. 用戶輸入 > 系統生成
        2. 最新時間戳 > 舊時間戳
        3. 更多變更 > 少變更
        """
        ...
```

---

### S53-4: 整合與 API (5 pts)

**As a** API 使用者
**I want** Context Bridge API
**So that** 可以查看和管理跨框架上下文

**Acceptance Criteria**:
- [ ] `GET /api/v1/hybrid/context/{session_id}` 獲取混合上下文
- [ ] `POST /api/v1/hybrid/context/sync` 觸發手動同步
- [ ] 整合至 HybridOrchestrator
- [ ] WebSocket 同步事件通知

**API Specification**:
```yaml
/api/v1/hybrid/context/{session_id}:
  get:
    summary: 獲取混合上下文
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                maf_context:
                  $ref: '#/components/schemas/MAFContext'
                claude_context:
                  $ref: '#/components/schemas/ClaudeContext'
                sync_status:
                  type: string
                  enum: [synced, pending, conflict]
                version:
                  type: integer

/api/v1/hybrid/context/sync:
  post:
    summary: 手動觸發上下文同步
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required:
              - session_id
              - direction
            properties:
              session_id:
                type: string
              direction:
                type: string
                enum: [maf_to_claude, claude_to_maf, bidirectional]
              strategy:
                type: string
                enum: [merge, source_wins, target_wins]
```

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| Intent Router | Sprint 52 | 📋 待完成 |
| CheckpointStorage | Phase 7-8 | ✅ 已完成 |
| SessionService | Phase 11 | ✅ 已完成 |
| Redis Cache | Infrastructure | ✅ 已完成 |

## Risks

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 資料結構不兼容 | 映射失敗 | 實現漸進式映射，允許部分失敗 |
| 同步延遲 | 狀態不一致 | 使用事件驅動同步 + 版本控制 |
| 衝突頻繁 | 用戶體驗差 | 智能合併策略 + 衝突提示 |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] 同步延遲 < 100ms
- [ ] Code Review 完成
- [ ] 部署到測試環境驗證
