# Sprint 57: Unified Checkpoint & Polish

## Sprint 概述

**Sprint 目標**: 實現統一 Checkpoint 系統並完成 Phase 14 整合與優化

**Story Points**: 30 點
**預估工期**: 1 週

## User Stories

### S57-1: Unified Checkpoint Structure (10 pts)

**As a** 系統架構師
**I want** 統一的 Checkpoint 結構
**So that** MAF 和 Claude 狀態能在同一結構中管理和恢復

**Acceptance Criteria**:
- [ ] HybridCheckpoint 資料結構實現
- [ ] 支持 MAF 和 Claude 雙狀態存儲
- [ ] 版本控制機制
- [ ] 序列化/反序列化支持
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/hybrid/
├── checkpoint/
│   ├── __init__.py
│   ├── models.py           # HybridCheckpoint, MAFState, ClaudeState
│   ├── storage.py          # UnifiedCheckpointStorage
│   ├── serialization.py    # 序列化邏輯
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── redis.py        # Redis 後端
│   │   ├── postgres.py     # PostgreSQL 後端
│   │   └── filesystem.py   # 文件系統後端
│   └── tests/
```

**Implementation Details**:
```python
# models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class MAFCheckpointState:
    """MAF 狀態快照"""
    workflow_id: str
    workflow_name: str
    current_step: int
    total_steps: int
    agent_states: Dict[str, Dict[str, Any]]
    variables: Dict[str, Any]
    pending_approvals: List[str]
    execution_log: List[Dict[str, Any]]

@dataclass
class ClaudeCheckpointState:
    """Claude 狀態快照"""
    session_id: str
    conversation_history: List[Dict[str, Any]]
    tool_call_history: List[Dict[str, Any]]
    context_variables: Dict[str, Any]
    system_prompt_hash: str
    active_hooks: List[str]
    mcp_states: Dict[str, Any]

@dataclass
class HybridCheckpoint:
    """統一 Checkpoint 結構"""
    # 標識
    version: int = 2
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""

    # 框架狀態
    maf_state: Optional[MAFCheckpointState] = None
    claude_state: Optional[ClaudeCheckpointState] = None

    # 執行模式
    execution_mode: ExecutionMode = ExecutionMode.CHAT_MODE
    mode_history: List[ModeTransition] = field(default_factory=list)

    # 風險檔案
    risk_profile: Optional[RiskProfile] = None

    # 同步元資料
    sync_version: int = 0
    sync_status: SyncStatus = SyncStatus.SYNCED
    last_sync: Optional[datetime] = None

    # 時間戳
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # 壓縮標記
    compressed: bool = False
    compression_algorithm: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """序列化為字典"""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HybridCheckpoint":
        """從字典反序列化"""
        ...
```

---

### S57-2: Unified Checkpoint Storage (10 pts)

**As a** 開發者
**I want** 支持多後端的 Checkpoint 存儲
**So that** 可以根據需求選擇合適的存儲方案

**Acceptance Criteria**:
- [ ] UnifiedCheckpointStorage 抽象類
- [ ] Redis 後端實現 (快速存取)
- [ ] PostgreSQL 後端實現 (持久化)
- [ ] Filesystem 後端實現 (備份)
- [ ] 恢復邏輯實現
- [ ] 過期清理機制

**Technical Tasks**:
```python
# storage.py
from abc import ABC, abstractmethod

class UnifiedCheckpointStorage(ABC):
    """統一 Checkpoint 存儲抽象類"""

    @abstractmethod
    async def save(
        self,
        checkpoint: HybridCheckpoint,
        ttl: Optional[int] = None,
    ) -> str:
        """保存 Checkpoint"""
        ...

    @abstractmethod
    async def load(
        self,
        checkpoint_id: str,
    ) -> Optional[HybridCheckpoint]:
        """載入 Checkpoint"""
        ...

    @abstractmethod
    async def delete(
        self,
        checkpoint_id: str,
    ) -> bool:
        """刪除 Checkpoint"""
        ...

    @abstractmethod
    async def list_by_session(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[HybridCheckpoint]:
        """列出 Session 的所有 Checkpoint"""
        ...

    async def restore(
        self,
        checkpoint_id: str,
        orchestrator: HybridOrchestratorV2,
    ) -> RestoreResult:
        """
        從 Checkpoint 恢復執行狀態

        步驟:
        1. 載入 Checkpoint
        2. 驗證完整性
        3. 恢復 MAF 狀態 (如有)
        4. 恢復 Claude 狀態 (如有)
        5. 同步上下文
        6. 返回恢復結果
        """
        ...

# backends/redis.py
class RedisCheckpointStorage(UnifiedCheckpointStorage):
    """Redis Checkpoint 存儲"""

    def __init__(
        self,
        redis_client: Redis,
        key_prefix: str = "hybrid_checkpoint:",
        default_ttl: int = 86400,  # 24 hours
    ):
        ...

# backends/postgres.py
class PostgresCheckpointStorage(UnifiedCheckpointStorage):
    """PostgreSQL Checkpoint 存儲"""

    def __init__(
        self,
        session: AsyncSession,
    ):
        ...
```

---

### S57-3: Phase 14 整合測試 (5 pts)

**As a** QA 工程師
**I want** Phase 14 完整的整合測試
**So that** 所有組件協同工作正常

**Acceptance Criteria**:
- [ ] 風險評估 + 審批流程端到端測試
- [ ] 模式切換完整流程測試
- [ ] Checkpoint 保存/恢復測試
- [ ] 跨框架恢復測試
- [ ] 效能基準測試

**Technical Tasks**:
```python
# tests/integration/hybrid/test_phase14_integration.py
class TestPhase14Integration:
    """Phase 14 整合測試"""

    async def test_risk_based_approval_flow(self):
        """測試風險評估驅動的審批流程"""
        # 1. 建立 Session
        # 2. 執行低風險操作 (自動通過)
        # 3. 執行高風險操作 (觸發審批)
        # 4. 審批通過後繼續
        ...

    async def test_mode_switch_workflow_to_chat(self):
        """測試 Workflow → Chat 模式切換"""
        # 1. 啟動 Workflow 模式
        # 2. 執行幾個步驟
        # 3. 觸發切換 (簡單問答)
        # 4. 驗證切換成功
        # 5. 在 Chat 模式繼續
        ...

    async def test_checkpoint_restore_cross_framework(self):
        """測試跨框架 Checkpoint 恢復"""
        # 1. 執行混合任務
        # 2. 保存 Checkpoint
        # 3. 模擬中斷
        # 4. 恢復 Checkpoint
        # 5. 驗證狀態完整
        ...

    async def test_full_hybrid_scenario(self):
        """完整混合場景測試"""
        # 1. 開始 Chat 模式
        # 2. 任務變複雜，切換到 Workflow
        # 3. 執行高風險操作，觸發審批
        # 4. 審批通過，繼續執行
        # 5. 保存 Checkpoint
        # 6. 遇到簡單問題，切換回 Chat
        # 7. 驗證整體流程
        ...
```

---

### S57-4: 文檔與優化 (5 pts)

**As a** 開發者
**I want** 完整的 Phase 13-14 文檔
**So that** 後續開發和維護有據可依

**Acceptance Criteria**:
- [ ] 架構設計文檔
- [ ] API 遷移指南
- [ ] 效能優化建議
- [ ] 部署配置指南
- [ ] 示範程式碼

**Deliverables**:
- `docs/guides/hybrid-architecture-guide.md`
- `docs/guides/checkpoint-management.md`
- `docs/api/hybrid-api-reference.md`
- `docs/deployment/hybrid-configuration.md`
- `examples/hybrid-integration/`

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| Mode Switcher | Sprint 56 | 📋 待完成 |
| Risk Assessment | Sprint 55 | 📋 待完成 |
| Context Bridge | Sprint 53 | 📋 待完成 |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] Checkpoint 恢復成功率 > 99.9%
- [ ] 文檔完整
- [ ] Phase 14 Demo 準備就緒
- [ ] Code Review 完成

---

## Phase 14 Completion Checklist

- [ ] Sprint 55 完成 (Risk Assessment)
- [ ] Sprint 56 完成 (Mode Switcher)
- [ ] Sprint 57 完成 (Unified Checkpoint)
- [ ] Phase 14 整合測試通過
- [ ] 文檔完整
- [ ] 效能基準達標
- [ ] Code Review 完成

---

## Phase 13-14 總結

完成 Phase 13-14 後，IPA Platform 將具備：

1. **智能意圖路由** - 自動判斷 Workflow vs Chat 模式
2. **跨框架上下文同步** - MAF 和 Claude 狀態無縫銜接
3. **統一 Tool 執行** - 所有工具通過 Claude 執行
4. **風險評估審批** - 基於風險等級的智能 HITL
5. **動態模式切換** - Workflow ↔ Chat 平滑切換
6. **統一 Checkpoint** - 跨框架狀態保存與恢復

**總 Story Points**: Phase 13 (105) + Phase 14 (95) = **200 Story Points**
**預估總工期**: 6 週 (6 Sprints)
