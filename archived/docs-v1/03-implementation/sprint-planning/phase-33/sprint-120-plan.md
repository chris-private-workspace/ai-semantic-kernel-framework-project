# Sprint 120: InMemory 完成 + Checkpoint 統一設計

## 概述

Sprint 120 完成剩餘 InMemory 存儲類的遷移（使生產代碼中 InMemory 存儲歸零），並開始設計與實現 UnifiedCheckpointRegistry 來統一平台中 4 個獨立的 Checkpoint 系統。

## 目標

1. 替換剩餘 4-5 個 InMemory 存儲類，達到零 InMemory 存儲在生產代碼中
2. 設計並實現 UnifiedCheckpointRegistry，統一 4 個 Checkpoint 系統的介面

## Story Points: 40 點

## 前置條件

- ⬜ Sprint 119 完成（前 4 個 InMemory 存儲已遷移）
- ⬜ StorageBackend Protocol 已定義
- ⬜ RedisStorageBackend 已實現
- ⬜ Redis 服務可用

## 任務分解

### Story 120-1: 替換剩餘 InMemory 存儲類 (3.5 天, P0)

**目標**: 完成全部 InMemory 存儲類的遷移，使生產代碼中零 InMemory 存儲殘留

**交付物**:
- 修改剩餘 InMemory 存儲模組
- 新增對應的 Redis/PostgreSQL 實現

**待遷移的存儲類**:

平台共有 9 個 InMemory 存儲類，Sprint 119 已遷移 4 個，本 Sprint 完成剩餘的：

| # | 存儲類 | 所在模組 | 目標存儲 |
|---|--------|---------|---------|
| 5 | InMemoryEventStore | 事件系統 | Redis Streams / PostgreSQL |
| 6 | InMemoryTaskQueue | 任務隊列 | Redis List / Sorted Set |
| 7 | InMemoryConversationHistory | 對話歷史 | PostgreSQL |
| 8 | InMemoryToolRegistry | 工具註冊 | Redis Hash |
| 9 | 其他殘留 InMemory 類 | 各模組 | 依類型選擇 Redis / PostgreSQL |

> **注意**: 具體存儲類名稱需在 Sprint 119 遷移過程中確認，上述為根據 V7 分析報告推測。實際遷移前需 `grep -r "InMemory" backend/src/` 確認完整清單。

**實現方式**:
- 複用 Sprint 119 定義的 StorageBackend Protocol
- 複用 RedisStorageBackend 基礎實現
- 對話歷史等大容量資料使用 PostgreSQL（避免 Redis 記憶體壓力）
- 事件存儲可考慮 Redis Streams（自然適配事件流）

**驗收標準**:
- [ ] `grep -r "InMemory" backend/src/` 返回 0 個生產代碼結果（測試檔案除外）
- [ ] 所有存儲類均有 Redis/PostgreSQL 實現
- [ ] 環境感知配置生效（`STORAGE_BACKEND` 環境變量）
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] 所有現有功能不受影響

### Story 120-2: UnifiedCheckpointRegistry 設計 + 實現 (2 天, P1)

**目標**: 設計統一的 Checkpoint 註冊表，為 4 個獨立 Checkpoint 系統提供統一介面

**交付物**:
- `backend/src/infrastructure/checkpoint/unified_registry.py`
- `backend/src/infrastructure/checkpoint/protocol.py`
- 設計文件 / 介面定義

**背景**:
平台目前有 4 個獨立的 Checkpoint 系統（V7 分析確認），彼此不協調：

| # | Checkpoint 系統 | 所屬模組 | 用途 |
|---|----------------|---------|------|
| 1 | Claude SDK Checkpoint | `integrations/claude_sdk/` | Claude Agent 執行快照 |
| 2 | Orchestration Checkpoint | `integrations/orchestration/` | 編排流程狀態 |
| 3 | Workflow Checkpoint | `domain/workflows/` | 工作流步驟狀態 |
| 4 | Session Checkpoint | `domain/sessions/` | 用戶會話狀態 |

**設計方向**:

```python
from typing import Protocol, Optional, Dict, Any
from datetime import datetime

class CheckpointProvider(Protocol):
    """Checkpoint 提供者協議 — 每個子系統實現此介面"""

    @property
    def provider_name(self) -> str:
        """提供者名稱（如 'claude_sdk', 'orchestration'）"""
        ...

    async def save_checkpoint(
        self,
        checkpoint_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        ...

    async def load_checkpoint(
        self, checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        ...

    async def list_checkpoints(
        self, filter_criteria: Optional[Dict[str, Any]] = None
    ) -> list:
        ...

    async def delete_checkpoint(self, checkpoint_id: str) -> None:
        ...


class UnifiedCheckpointRegistry:
    """統一 Checkpoint 註冊表"""

    def __init__(self, storage_backend):
        self._providers: Dict[str, CheckpointProvider] = {}
        self._storage = storage_backend

    def register_provider(self, provider: CheckpointProvider) -> None:
        """註冊 Checkpoint 提供者"""
        ...

    async def save(
        self,
        provider_name: str,
        checkpoint_id: str,
        data: Dict[str, Any]
    ) -> None:
        """透過統一介面保存 checkpoint"""
        ...

    async def load(
        self,
        provider_name: str,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """透過統一介面載入 checkpoint"""
        ...

    async def list_all(self) -> Dict[str, list]:
        """列出所有提供者的 checkpoints"""
        ...

    async def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """清理過期的 checkpoints"""
        ...
```

**驗收標準**:
- [ ] CheckpointProvider Protocol 定義完整
- [ ] UnifiedCheckpointRegistry 基本實現完成
- [ ] 至少 1 個現有 Checkpoint 系統成功接入 Registry
- [ ] 清理過期 checkpoint 功能正常
- [ ] 單元測試覆蓋率 > 85%
- [ ] 設計文件記錄統一方案

## 技術設計

### Checkpoint 統一策略

```
┌───────────────────────────────────────────────────┐
│            UnifiedCheckpointRegistry               │
│                                                    │
│  register() / save() / load() / list_all()        │
│  cleanup_expired()                                 │
├───────────┬───────────┬───────────┬───────────────┤
│ Claude SDK│ Orchestr. │ Workflow  │ Session       │
│ Provider  │ Provider  │ Provider  │ Provider      │
├───────────┴───────────┴───────────┴───────────────┤
│              StorageBackend                        │
│         (Redis + PostgreSQL)                       │
└───────────────────────────────────────────────────┘
```

### 遷移方式

1. **Sprint 120**: 定義 Protocol + Registry + 接入第 1 個 Provider
2. **Sprint 121**: 接入剩餘 3 個 Provider，完成統一

## 依賴

```
# 無新增依賴，複用 Sprint 119 的 Redis 基礎設施
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| 4 個 Checkpoint 系統差異大 | Protocol 設計足夠泛化，允許 metadata 擴展 |
| 統一過程中打破現有功能 | 先接入 1 個驗證設計，再推廣到其他 |
| InMemory 存儲遺漏未發現的類 | 使用 grep 全面掃描，包含動態生成的實例 |

## 完成標準

- [ ] InMemory 存儲：生產代碼中 0 個殘留
- [ ] UnifiedCheckpointRegistry 設計與基本實現完成
- [ ] 至少 1 個 Checkpoint 系統接入統一 Registry
- [ ] 所有測試通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: 待定
