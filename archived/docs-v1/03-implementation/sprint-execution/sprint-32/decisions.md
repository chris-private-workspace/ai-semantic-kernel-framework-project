# Sprint 32 Decisions: 會話層統一與 Domain 清理

**Sprint 目標**: 解決所有 P1 級別架構問題

---

## 決策記錄

### D32-001: MultiTurnAdapter 設計策略

**日期**: 2025-12-08
**狀態**: ✅ 已決定

**背景**:
需要創建統一的 MultiTurnAdapter 整合以下功能：
- 會話生命週期管理 (原 MultiTurnSessionManager)
- 對話記憶存儲 (原 ConversationMemoryStore)
- Turn 追蹤 (原 TurnTracker)
- 上下文管理 (原 SessionContextManager)

**選項**:
1. 創建新的 `multiturn/unified_adapter.py` 整合所有功能
2. 擴展現有的 `multiturn/checkpoint_storage.py`
3. 創建多個小型適配器分別處理各功能

**決定**: 選項 1 **已在 Sprint 24 完成** - 使用現有 `multiturn/adapter.py`

**發現**:
在分析過程中發現，`MultiTurnAdapter` 已於 Sprint 24 (S24-3) 實現，包含：
- `adapter.py`: MultiTurnAdapter 主類，整合所有功能
- `checkpoint_storage.py`: 多種存儲後端實現
- 完整導出在 `__init__.py`

**現有實現功能清單**:
1. ✅ 使用官方 `CheckpointStorage` API
2. ✅ `SessionState` 枚舉 (ACTIVE, PAUSED, COMPLETED 等)
3. ✅ `Message`, `TurnResult`, `SessionInfo` 數據類
4. ✅ 會話生命週期: `start()`, `pause()`, `resume()`, `complete()`
5. ✅ Turn 操作: `add_turn()`, `get_history()`, `get_context_messages()`
6. ✅ 上下文管理: `ContextManager` 類
7. ✅ Checkpoint 操作: `save_checkpoint()`, `restore_checkpoint()`

**結論**: S32-1 主要工作轉為驗證現有實現並進行小幅增強 (如需要)

---

### D32-002: 會話存儲後端選擇

**日期**: 2025-12-08
**狀態**: ✅ 已決定

**背景**:
MultiTurnAdapter 需要支持多種存儲後端。

**選項**:
1. 僅支持 InMemory (簡單，但不適合生產)
2. 支持 InMemory + Redis (平衡)
3. 支持 InMemory + Redis + PostgreSQL (完整)

**決定**: 選項 3 **已在 Sprint 24 實現**

**現有存儲後端**:
- `InMemoryCheckpointStorage` (官方 API)
- `RedisCheckpointStorage` (自定義擴展)
- `PostgresCheckpointStorage` (自定義擴展)
- `FileCheckpointStorage` (自定義擴展，用於開發測試)

---

### D32-003: GroupChat 會話層遷移策略

**日期**: 2025-12-08
**狀態**: ✅ 已完成

**背景**:
GroupChat API (`api/v1/groupchat/routes.py`) 仍直接導入 domain 層會話管理模組。

**實施方案**:
創建 `MultiTurnAPIService` 包裝器 (`multiturn_service.py`)，提供與舊 API 相同的接口：

```python
# 新導入 (已實施)
from src.api.v1.groupchat.multiturn_service import (
    MultiTurnAPIService,
    MultiTurnSession,
    SessionMessage,
    SessionStatus,
    get_multiturn_service,
)
```

**遷移的端點** (8 個):
1. `POST /sessions/` - create_session
2. `GET /sessions/` - list_sessions
3. `GET /sessions/{id}` - get_session
4. `POST /sessions/{id}/turns` - execute_turn
5. `GET /sessions/{id}/history` - get_session_history
6. `PATCH /sessions/{id}/context` - update_session_context
7. `POST /sessions/{id}/close` - close_session
8. `DELETE /sessions/{id}` - delete_session

**API 兼容性**: ✅ 完全兼容

---

### D32-004: Domain 層 API 使用分析

**日期**: 2025-12-08
**狀態**: ✅ 已完成

**背景**:
分析所有 API 模組的 domain 層導入，確認遷移狀態。

**分析結果**:

| 模組 | 導入來源 | 狀態 | 說明 |
|------|----------|------|------|
| groupchat | domain.orchestration.multiturn | ✅ 已遷移 | Sprint 32 |
| groupchat | domain.orchestration.memory | ✅ 已遷移 | Sprint 32 |
| nested | domain.orchestration.nested | ✅ 保留 | 擴展功能 |
| agents | domain.agents.service | ✅ 正常 | 服務層 |
| workflows | domain.workflows | ✅ 正常 | 服務層 |
| checkpoints | domain.checkpoints | ✅ 正常 | 服務層 |
| executions | domain.executions | ✅ 正常 | 服務層 |

**結論**:
- `domain.orchestration.multiturn` 和 `domain.orchestration.memory` 已完成遷移
- `domain.orchestration.nested` 保留用於擴展功能 (有明確註釋)
- 其他 domain 層導入為正常服務層使用，不需遷移

---

## 技術約束

1. **官方 API 使用**:
   - 必須使用官方 `CheckpointStorage` 接口
   - 參考 `agent_framework.checkpoints` 模組

2. **API 兼容性**:
   - GroupChat API 響應格式必須保持不變
   - 錯誤代碼必須保持一致

3. **測試要求**:
   - 新增測試 > 30 個
   - 測試覆蓋率 > 80%

---

## 參考資料

- [Sprint 32 Plan](../../sprint-planning/phase-6/sprint-32-plan.md)
- [Sprint 31 Decisions](../sprint-31/decisions.md)
- [Deprecated Modules Guide](../../migration/deprecated-modules.md)
