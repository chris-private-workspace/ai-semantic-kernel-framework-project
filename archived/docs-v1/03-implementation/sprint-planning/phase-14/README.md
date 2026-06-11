# Phase 14: Advanced Hybrid Features (進階混合功能)

## 概述

Phase 14 專注於建立**風險評估引擎**、**動態模式切換**和**統一 Checkpoint 系統**，完善混合架構的進階功能。

## 目標

1. **Risk Assessment Engine** - 基於風險等級的智能審批決策
2. **Mode Switcher** - Workflow ↔ Chat 動態模式切換
3. **Unified Checkpoint** - 統一的 Checkpoint 結構，支持跨框架恢復

## 前置條件

- ✅ Phase 13 完成 (Hybrid Core Architecture)
- ✅ Intent Router 就緒
- ✅ Context Bridge 就緒
- ✅ Unified Tool Executor 就緒

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 55](./sprint-55-plan.md) | Risk Assessment Engine | 30 點 | ✅ 完成 |
| [Sprint 56](./sprint-56-plan.md) | Mode Switcher & HITL | 35 點 | ✅ 完成 |
| [Sprint 57](./sprint-57-plan.md) | Unified Checkpoint & Polish | 30 點 | 📋 計劃中 |

**總計**: 95 Story Points (65/95 已完成，68%)

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Phase 14 Architecture                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │               Risk Assessment Engine (NEW)                    │       │
│  │                                                               │       │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │       │
│  │  │ Operation       │  │ Context         │  │ Pattern      │  │       │
│  │  │ Analyzer        │  │ Evaluator       │  │ Detector     │  │       │
│  │  │                 │  │                 │  │              │  │       │
│  │  │ - Tool type     │  │ - Session state │  │ - Historical │  │       │
│  │  │ - Parameters    │  │ - User trust    │  │ - Anomaly    │  │       │
│  │  │ - Target path   │  │ - Environment   │  │ - Risk trend │  │       │
│  │  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘  │       │
│  │           │                    │                   │          │       │
│  │           └────────────────────┼───────────────────┘          │       │
│  │                                ▼                              │       │
│  │                    ┌───────────────────────┐                  │       │
│  │                    │   Risk Score Engine   │                  │       │
│  │                    │   (0.0 - 1.0 scale)   │                  │       │
│  │                    │                       │                  │       │
│  │                    │   LOW:    0.0 - 0.3   │                  │       │
│  │                    │   MEDIUM: 0.3 - 0.6   │                  │       │
│  │                    │   HIGH:   0.6 - 0.8   │                  │       │
│  │                    │   CRITICAL: 0.8 - 1.0 │                  │       │
│  │                    └───────────────────────┘                  │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                              │                                           │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                   Mode Switcher (NEW)                         │       │
│  │                                                               │       │
│  │  Workflow Mode ◄────────── Dynamic Switch ──────────► Chat Mode  │   │
│  │                                                               │       │
│  │  Triggers:                                                    │       │
│  │  - Complexity change (simple → complex)                       │       │
│  │  - User explicit request                                      │       │
│  │  - Failure recovery                                           │       │
│  │  - Resource constraints                                       │       │
│  │                                                               │       │
│  │  ┌─────────────────────────────────────────────────────┐     │       │
│  │  │            State Preservation Layer                  │     │       │
│  │  │                                                      │     │       │
│  │  │  - Checkpoint snapshot before switch                 │     │       │
│  │  │  - Context migration                                 │     │       │
│  │  │  - Rollback capability                               │     │       │
│  │  └─────────────────────────────────────────────────────┘     │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                              │                                           │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │               Unified Checkpoint (REFACTORED)                 │       │
│  │                                                               │       │
│  │  ┌─────────────────────────────────────────────────────┐     │       │
│  │  │              HybridCheckpoint Structure               │     │       │
│  │  │                                                       │     │       │
│  │  │  {                                                    │     │       │
│  │  │    "version": 2,                                      │     │       │
│  │  │    "maf_state": { /* MAF Checkpoint */ },             │     │       │
│  │  │    "claude_state": { /* Claude Context */ },          │     │       │
│  │  │    "execution_mode": "workflow|chat|hybrid",          │     │       │
│  │  │    "risk_profile": { /* Risk Assessment */ },         │     │       │
│  │  │    "sync_metadata": { /* Sync Info */ }               │     │       │
│  │  │  }                                                    │     │       │
│  │  └─────────────────────────────────────────────────────┘     │       │
│  │                                                               │       │
│  │  Storage Backends: Redis | PostgreSQL | Filesystem            │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心組件

### 1. Risk Assessment Engine (Sprint 55)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

class RiskLevel(Enum):
    LOW = "low"           # 0.0 - 0.3: 自動執行
    MEDIUM = "medium"     # 0.3 - 0.6: 記錄審計
    HIGH = "high"         # 0.6 - 0.8: 需要審批
    CRITICAL = "critical" # 0.8 - 1.0: 需要多重審批

@dataclass
class RiskAssessment:
    score: float          # 0.0 - 1.0
    level: RiskLevel
    factors: List[RiskFactor]
    recommendation: str   # "auto_execute" | "audit_log" | "require_approval" | "block"
    reasoning: str

class RiskAssessmentEngine:
    """
    風險評估引擎

    評估維度:
    1. 操作類型 (read vs write vs delete)
    2. 目標範圍 (單文件 vs 目錄 vs 系統)
    3. 操作參數 (敏感路徑、危險命令)
    4. 上下文因素 (用戶信任度、環境)
    5. 歷史模式 (異常行為檢測)
    """

    async def assess(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: HybridContext,
        history: Optional[List[ToolCall]] = None,
    ) -> RiskAssessment:
        """
        評估操作風險

        流程:
        1. 操作分析 (Tool 類型和參數)
        2. 上下文評估 (用戶、環境、狀態)
        3. 模式檢測 (歷史行為分析)
        4. 綜合評分
        5. 生成建議
        """
        ...
```

### 2. Mode Switcher (Sprint 56)

```python
@dataclass
class SwitchTrigger:
    """模式切換觸發條件"""
    trigger_type: str     # "complexity" | "user_request" | "failure" | "resource"
    source_mode: ExecutionMode
    target_mode: ExecutionMode
    reason: str
    confidence: float

class ModeSwitcher:
    """
    動態模式切換器

    支持場景:
    - Chat → Workflow: 任務變複雜，需要多代理協作
    - Workflow → Chat: 遇到簡單問答，或工作流失敗需要診斷
    - Hybrid 動態調整: 根據執行過程自動優化
    """

    async def should_switch(
        self,
        current_mode: ExecutionMode,
        current_state: ExecutionState,
        new_input: str,
    ) -> Optional[SwitchTrigger]:
        """判斷是否需要切換模式"""
        ...

    async def execute_switch(
        self,
        trigger: SwitchTrigger,
        context: HybridContext,
        checkpoint_storage: CheckpointStorage,
    ) -> SwitchResult:
        """
        執行模式切換

        步驟:
        1. 保存當前狀態 (Checkpoint)
        2. 遷移上下文
        3. 初始化目標模式
        4. 驗證切換成功
        """
        ...

    async def rollback_switch(
        self,
        switch_result: SwitchResult,
    ) -> bool:
        """回滾失敗的模式切換"""
        ...
```

### 3. Unified Checkpoint (Sprint 57)

```python
@dataclass
class HybridCheckpoint:
    """統一的 Checkpoint 結構"""
    version: int = 2
    checkpoint_id: str
    session_id: str

    # MAF 狀態
    maf_state: Optional[MAFCheckpointState]

    # Claude 狀態
    claude_state: Optional[ClaudeCheckpointState]

    # 執行模式
    execution_mode: ExecutionMode
    mode_history: List[ModeTransition]

    # 風險檔案
    risk_profile: RiskProfile

    # 同步元資料
    sync_metadata: SyncMetadata

    # 時間戳
    created_at: datetime
    updated_at: datetime

class UnifiedCheckpointStorage:
    """
    統一 Checkpoint 存儲

    支持:
    - 跨框架狀態恢復
    - 模式切換點保存
    - 風險歷史追蹤
    - 版本化 Checkpoint
    """

    async def save(
        self,
        checkpoint: HybridCheckpoint,
    ) -> str:
        """保存 Checkpoint"""
        ...

    async def load(
        self,
        checkpoint_id: str,
    ) -> HybridCheckpoint:
        """載入 Checkpoint"""
        ...

    async def restore(
        self,
        checkpoint_id: str,
        orchestrator: HybridOrchestratorV2,
    ) -> RestoreResult:
        """
        從 Checkpoint 恢復執行狀態

        支持:
        - 完整恢復 (MAF + Claude)
        - 部分恢復 (僅 MAF 或僅 Claude)
        - 模式切換後恢復
        """
        ...
```

## 與現有系統整合

| 現有組件 | Phase 14 整合方式 |
|----------|-------------------|
| `ApprovalHook` | 整合 Risk Assessment，基於風險等級決定是否需要審批 |
| `CheckpointStorage` | 擴展為 UnifiedCheckpointStorage，支持 HybridCheckpoint |
| `HybridOrchestratorV2` | 整合 Mode Switcher，支持動態模式切換 |
| `SessionService` | 添加模式切換事件發布 |

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 後端實現 |
| FastAPI | 0.100+ | API 整合 |
| Redis | 7.x | Checkpoint 快取、風險歷史 |
| PostgreSQL | 16.x | Checkpoint 持久化 |
| Pydantic | 2.x | 資料模型驗證 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 風險評估誤判 | 錯誤阻擋/放行 | 可調整閾值 + 審計日誌 + 用戶反饋循環 |
| 模式切換資料丟失 | 狀態不一致 | Checkpoint 保證 + 回滾機制 |
| Checkpoint 膨脹 | 存儲壓力 | 壓縮 + 過期清理 + 增量存儲 |

## 成功標準

- [ ] 風險評估準確率 > 95% (基於測試案例)
- [ ] 模式切換成功率 > 99%
- [ ] Checkpoint 恢復成功率 > 99.9%
- [ ] 現有功能回歸測試 100% 通過

---

**Phase 14 開始時間**: 待 Phase 13 完成
**預估完成時間**: 3 週 (3 Sprints)
