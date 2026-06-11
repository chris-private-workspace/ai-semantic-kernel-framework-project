# Sprint 32: 會話層統一與 Domain 清理

**Sprint 目標**: 解決所有 P1 級別架構問題，統一會話存儲層，完成 Domain 代碼遷移
**總點數**: 28 Story Points
**優先級**: 🟡 HIGH

---

## 問題背景

根據 Phase 1-5 架構審計，發現以下 P1 級別問題：

### 問題 1: GroupChat 會話層依賴 Domain

```python
# 當前問題代碼 (backend/src/api/v1/groupchat/routes.py)
# ✅ 主邏輯已遷移
from src.integrations.agent_framework.builders import GroupChatBuilderAdapter

# ⚠️ 會話層仍依賴 domain
from src.domain.orchestration.multiturn import (
    MultiTurnSessionManager,  # 已棄用
    SessionStatus,
)
from src.domain.orchestration.memory import (
    ConversationMemoryStore,  # 已棄用
    InMemoryConversationMemoryStore,
)
```

### 問題 2: Domain 代碼殘留統計

```
domain/orchestration/ 目錄:
├── nested/      [5,568 行] - 95% 遷移
├── planning/    [3,956 行] - 20% 遷移 (Sprint 31 處理)
├── memory/      [2,138 行] - 50% 遷移 ⚠️
├── multiturn/   [1,805 行] - 50% 遷移 ⚠️
└── 總計         [11,465 行] - 50.7% 遷移

目標: 達到 95%+ 遷移進度
```

---

## Story 清單

### S32-1: MultiTurnAdapter 創建 (10 pts)

**優先級**: 🟡 P1 - HIGH
**類型**: 新增
**影響範圍**: `backend/src/integrations/agent_framework/multiturn/`

#### 任務清單

1. **設計 MultiTurnAdapter 架構**
   ```python
   # 新文件: backend/src/integrations/agent_framework/multiturn/unified_adapter.py

   from agent_framework import CheckpointStorage, InMemoryCheckpointStorage

   class MultiTurnAdapter:
       """統一的多輪會話適配器

       整合功能:
       - 會話生命週期管理 (原 MultiTurnSessionManager)
       - 對話記憶存儲 (原 ConversationMemoryStore)
       - Turn 追蹤 (原 TurnTracker)
       - 上下文管理 (原 SessionContextManager)
       """

       def __init__(
           self,
           storage: Optional[CheckpointStorage] = None,
           max_turns: int = 100,
           session_timeout: int = 3600,
       ):
           self._storage = storage or InMemoryCheckpointStorage()
           self._max_turns = max_turns
           self._session_timeout = session_timeout
           self._sessions: Dict[str, MultiTurnSession] = {}

       async def create_session(
           self,
           session_id: str,
           metadata: Optional[Dict] = None,
       ) -> MultiTurnSession:
           """創建新的多輪會話"""
           pass

       async def add_turn(
           self,
           session_id: str,
           role: str,
           content: str,
       ) -> Turn:
           """添加對話輪次"""
           pass

       async def get_context(
           self,
           session_id: str,
           max_turns: Optional[int] = None,
       ) -> List[Turn]:
           """獲取會話上下文"""
           pass

       async def save_checkpoint(
           self,
           session_id: str,
       ) -> str:
           """保存會話檢查點"""
           return await self._storage.save(...)

       async def restore_session(
           self,
           checkpoint_id: str,
       ) -> MultiTurnSession:
           """從檢查點恢復會話"""
           pass

       async def close_session(
           self,
           session_id: str,
       ) -> None:
           """關閉會話"""
           pass
   ```

2. **實現核心功能**
   - 會話創建/關閉
   - Turn 添加/查詢
   - 上下文窗口管理
   - 檢查點保存/恢復

3. **整合現有 CheckpointStorageAdapter**
   - 複用 `multiturn/checkpoint_storage.py`
   - 確保與官方 CheckpointStorage 兼容

4. **添加 Redis 後端支持**
   ```python
   class RedisMultiTurnStorage(CheckpointStorage):
       """Redis 後端的會話存儲"""
       pass
   ```

#### 驗收標準
- [ ] MultiTurnAdapter 實現完成
- [ ] 支持 InMemory 和 Redis 後端
- [ ] 官方 CheckpointStorage API 正確使用
- [ ] 單元測試覆蓋 > 80%

---

### S32-2: GroupChat API 會話層遷移 (8 pts)

**優先級**: 🟡 P1 - HIGH
**類型**: 重構
**影響範圍**: `backend/src/api/v1/groupchat/routes.py`

#### 任務清單

1. **替換 Domain 導入**
   ```python
   # 移除
   from src.domain.orchestration.multiturn import (
       MultiTurnSessionManager,
       MultiTurnSession,
       SessionStatus,
   )
   from src.domain.orchestration.memory import (
       ConversationMemoryStore,
       InMemoryConversationMemoryStore,
   )

   # 添加
   from src.integrations.agent_framework.multiturn import (
       MultiTurnAdapter,
       MultiTurnSession,
       SessionStatus,
   )
   ```

2. **更新會話管理端點**
   ```python
   # 更新的端點
   POST /api/v1/groupchat/sessions          → MultiTurnAdapter.create_session()
   GET  /api/v1/groupchat/sessions/{id}     → MultiTurnAdapter.get_session()
   POST /api/v1/groupchat/sessions/{id}/turns → MultiTurnAdapter.add_turn()
   GET  /api/v1/groupchat/sessions/{id}/context → MultiTurnAdapter.get_context()
   POST /api/v1/groupchat/sessions/{id}/checkpoint → MultiTurnAdapter.save_checkpoint()
   DELETE /api/v1/groupchat/sessions/{id}   → MultiTurnAdapter.close_session()
   ```

3. **更新記憶體管理端點**
   ```python
   # 更新的端點
   POST /api/v1/groupchat/memory/store      → MultiTurnAdapter storage
   GET  /api/v1/groupchat/memory/retrieve   → MultiTurnAdapter storage
   DELETE /api/v1/groupchat/memory/clear    → MultiTurnAdapter storage
   ```

4. **確保 API 兼容性**
   - 響應格式保持不變
   - 錯誤代碼保持一致

#### 驗收標準
- [ ] GroupChat routes.py 無 domain.orchestration 導入
- [ ] 41 個 GroupChat API 路由正常工作
- [ ] 現有測試通過 (test_groupchat_api.py)
- [ ] 會話管理功能正常

---

### S32-3: Domain 代碼最終清理 (5 pts)

**優先級**: 🟡 P1 - HIGH
**類型**: 清理
**影響範圍**: `backend/src/domain/orchestration/`

#### 任務清單

1. **統計剩餘 Domain 使用**
   ```bash
   grep -r "from src.domain.orchestration" backend/src/api/
   ```

2. **清理 nested API 殘留依賴**
   - 檢查 `api/v1/nested/routes.py`
   - 確認所有功能使用 NestedWorkflowAdapter

3. **更新棄用模組狀態**
   - multiturn/ → 標記為完全棄用
   - memory/ → 標記為完全棄用

4. **統計遷移進度**
   ```
   目標:
   ├── nested/      95% → 100%
   ├── planning/    20% → 100% (Sprint 31)
   ├── memory/      50% → 95%+
   └── multiturn/   50% → 95%+
   ```

#### 驗收標準
- [ ] Domain 遷移進度達到 95%+
- [ ] 所有 API 路由無 domain.orchestration 直接導入
- [ ] 棄用模組文檔更新

---

### S32-4: 整合測試驗證 (5 pts)

**優先級**: 🟡 P1 - HIGH
**類型**: 測試
**影響範圍**: `backend/tests/`

#### 任務清單

1. **新增 MultiTurnAdapter 測試**
   ```python
   # backend/tests/unit/test_multiturn_adapter.py
   class TestMultiTurnAdapter:
       async def test_create_session(self):
           pass
       async def test_add_turn(self):
           pass
       async def test_save_checkpoint(self):
           pass
       async def test_restore_session(self):
           pass
   ```

2. **更新 GroupChat 整合測試**
   ```python
   # backend/tests/integration/test_groupchat_session.py
   class TestGroupChatSessionIntegration:
       async def test_full_session_lifecycle(self):
           pass
       async def test_checkpoint_and_restore(self):
           pass
   ```

3. **運行完整測試套件**
   ```bash
   pytest tests/ -v --tb=short
   pytest tests/e2e/test_groupchat_workflow.py -v
   ```

4. **驗證無回歸**
   - 所有 3,439+ 測試通過
   - E2E 會話測試通過

#### 驗收標準
- [ ] 新增 MultiTurnAdapter 測試 > 20 個
- [ ] 整合測試覆蓋會話生命週期
- [ ] 所有現有測試通過

---

## 技術規範

### MultiTurnAdapter 接口設計

```python
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    EXPIRED = "expired"

@dataclass
class Turn:
    id: str
    session_id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class MultiTurnSession:
    id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    turns: List[Turn]
    metadata: Optional[Dict[str, Any]] = None
    checkpoint_id: Optional[str] = None

class MultiTurnAdapter:
    async def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> MultiTurnSession: ...
    async def get_session(self, session_id: str) -> Optional[MultiTurnSession]: ...
    async def add_turn(self, session_id: str, role: str, content: str) -> Turn: ...
    async def get_context(self, session_id: str, max_turns: Optional[int] = None) -> List[Turn]: ...
    async def save_checkpoint(self, session_id: str) -> str: ...
    async def restore_session(self, checkpoint_id: str) -> MultiTurnSession: ...
    async def close_session(self, session_id: str) -> None: ...
```

### 存儲後端抽象

```python
from abc import ABC, abstractmethod

class SessionStorage(ABC):
    @abstractmethod
    async def save_session(self, session: MultiTurnSession) -> None: ...

    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[MultiTurnSession]: ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> None: ...

class InMemorySessionStorage(SessionStorage):
    """內存存儲實現"""
    pass

class RedisSessionStorage(SessionStorage):
    """Redis 存儲實現"""
    pass
```

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| 會話數據遷移丟失 | 中 | 高 | 數據備份，兼容模式 |
| 性能下降 | 低 | 中 | 性能測試驗證 |
| API 兼容性破壞 | 中 | 高 | 保持響應格式一致 |

---

## 驗證命令

```bash
# 驗證無 domain.orchestration 導入
grep -r "from src.domain.orchestration.multiturn" backend/src/api/
grep -r "from src.domain.orchestration.memory" backend/src/api/

# 運行 GroupChat 測試
pytest tests/unit/test_groupchat*.py -v
pytest tests/e2e/test_groupchat_workflow.py -v

# 統計遷移進度
find backend/src/domain/orchestration -name "*.py" | xargs wc -l
```

---

## 完成定義

- [ ] 所有 S32 Story 完成
- [ ] MultiTurnAdapter 100% 實現
- [ ] GroupChat API 100% 使用適配器
- [ ] Domain 遷移進度 > 95%
- [ ] 所有測試通過
