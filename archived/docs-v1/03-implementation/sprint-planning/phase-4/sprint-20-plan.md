# Sprint 20: GroupChat 完整遷移

## Sprint Overview

| Property | Value |
|----------|-------|
| **Sprint** | 20 |
| **Phase** | 4 - 完整重構 |
| **Focus** | 將 GroupChat API 遷移到適配器 |
| **Duration** | 2 週 |
| **Total Story Points** | 34 |

## Sprint Goal

將 `domain/orchestration/groupchat/` 的所有功能遷移到 `GroupChatBuilderAdapter`，確保 API 層完全使用適配器，不再直接依賴 domain 層的自行實現。

---

## 問題分析

### 當前狀態

| 項目 | 當前值 | 問題 |
|------|--------|------|
| `domain/orchestration/groupchat/` | 3,853 行 | 自行實現，未使用官方 API |
| API 層依賴 | 直接使用 GroupChatManager | 繞過適配器層 |
| `GroupChatBuilderAdapter` | 已存在 | 未被 API 層使用 |

### 目標架構

```
API Layer
    ↓
GroupChatBuilderAdapter (integrations/agent_framework/builders/groupchat.py)
    ↓
Official GroupChatBuilder (from agent_framework import GroupChatBuilder)
```

---

## User Stories

### S20-1: 重構 GroupChat API 路由 (8 pts)

**目標**: 修改 API 層以使用 `GroupChatBuilderAdapter` 而非直接使用 domain 層

**範圍**:
- `api/v1/groupchat/routes.py`
- `api/v1/planning/routes.py` (如有 GroupChat 相關調用)

**修改前**:
```python
# api/v1/groupchat/routes.py
from domain.orchestration.groupchat.manager import GroupChatManager

@router.post("/create")
async def create_groupchat(request: GroupChatCreateRequest):
    manager = GroupChatManager(...)  # ❌ 直接使用自行實現
    return await manager.run(request.initial_message)
```

**修改後**:
```python
# api/v1/groupchat/routes.py
from integrations.agent_framework.builders.groupchat import GroupChatBuilderAdapter

@router.post("/create")
async def create_groupchat(request: GroupChatCreateRequest):
    adapter = GroupChatBuilderAdapter(
        id=request.id,
        participants=request.participants,
        selection_method=request.selection_method,
        max_rounds=request.max_rounds,
    )  # ✅ 使用適配器
    workflow = adapter.build()
    return await adapter.run(request.initial_message)
```

**驗收標準**:
- [ ] `grep "from domain.orchestration.groupchat" api/` 返回 0 結果
- [ ] 所有 GroupChat API 端點正常工作
- [ ] API 響應格式保持不變
- [ ] 相關測試通過

---

### S20-2: 整合 SpeakerSelector 到適配器 (8 pts)

**目標**: 將 `domain/orchestration/groupchat/speaker_selector.py` 邏輯遷移到適配器

**範圍**: `integrations/agent_framework/builders/groupchat.py`

**支持的選擇策略**:
1. `ROUND_ROBIN` - 輪流發言
2. `RANDOM` - 隨機選擇
3. `EXPERTISE` - 專業能力匹配
4. `LLM_BASED` - 基於 LLM 的智能選擇
5. `VOTING` - 投票選擇（擴展功能）

**實現方式**:
```python
class GroupChatBuilderAdapter:
    def _create_speaker_selector(self) -> Callable:
        """將 IPA 選擇方法映射到官方 selector_fn"""

        if self._selection_method == SpeakerSelectionMethod.ROUND_ROBIN:
            def round_robin_selector(state: GroupChatStateSnapshot) -> str:
                participants = list(state.participants.keys())
                current_idx = state.round_number % len(participants)
                return participants[current_idx]
            return round_robin_selector

        elif self._selection_method == SpeakerSelectionMethod.EXPERTISE:
            def expertise_selector(state: GroupChatStateSnapshot) -> str:
                # 保留 Phase 2 的專業能力匹配邏輯
                from domain.orchestration.groupchat.speaker_selector import ExpertiseMatcher
                matcher = ExpertiseMatcher(state.participants)
                return matcher.select_best_match(state.current_topic)
            return expertise_selector

        # ... 其他方法
```

**驗收標準**:
- [ ] 所有 5 種選擇策略正常工作
- [ ] 測試覆蓋每種策略
- [ ] 效能基準測試通過（無明顯性能下降）
- [ ] `EXPERTISE` 選擇策略保留 Phase 2 邏輯

---

### S20-3: 整合 Termination 條件 (5 pts)

**目標**: 將 `domain/orchestration/groupchat/termination.py` 邏輯遷移到適配器

**範圍**: `integrations/agent_framework/builders/groupchat.py`

**支持的終止條件**:
1. 輪數限制 (`max_rounds`)
2. 關鍵詞終止 (`termination_keywords`)
3. 共識達成終止 (`consensus_required`)
4. 超時終止 (`timeout`)
5. 自定義終止函數 (`custom_termination_fn`)

**實現方式**:
```python
class GroupChatBuilderAdapter:
    def _create_termination_condition(self) -> Callable:
        """將 IPA 終止條件映射到官方 termination_condition"""

        conditions = []

        # 輪數限制
        if self._max_rounds:
            conditions.append(
                lambda state: state.round_number >= self._max_rounds
            )

        # 關鍵詞終止
        if self._termination_keywords:
            conditions.append(
                lambda state: any(
                    kw in state.last_message.content
                    for kw in self._termination_keywords
                )
            )

        # 共識達成終止
        if self._consensus_required:
            conditions.append(
                lambda state: self._check_consensus(state)
            )

        # 組合所有條件
        def combined_termination(state: GroupChatStateSnapshot) -> bool:
            return any(cond(state) for cond in conditions)

        return combined_termination
```

**驗收標準**:
- [ ] 所有終止條件類型正常工作
- [ ] 測試覆蓋每種終止條件
- [ ] 組合終止條件正確執行

---

### S20-4: 保留 Voting 系統作為擴展 (5 pts)

**目標**: 將投票系統封裝為適配器擴展

**範圍**: 創建新文件 `integrations/agent_framework/builders/groupchat_voting.py`

**實現方式**:
```python
from .groupchat import GroupChatBuilderAdapter
from domain.orchestration.groupchat.voting import VotingSystem, VotingMethod

class GroupChatVotingAdapter(GroupChatBuilderAdapter):
    """
    擴展 GroupChatBuilderAdapter，添加投票功能。

    這是 IPA Platform 的自定義功能，不在官方 API 中。
    通過擴展適配器模式保留此功能。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._voting_system: Optional[VotingSystem] = None

    def with_voting(
        self,
        voting_method: VotingMethod = VotingMethod.MAJORITY,
        min_votes: int = 2,
    ) -> "GroupChatVotingAdapter":
        """啟用投票系統"""
        self._voting_system = VotingSystem(
            method=voting_method,
            min_votes=min_votes,
        )
        return self
```

**驗收標準**:
- [ ] `GroupChatVotingAdapter` 正確繼承 `GroupChatBuilderAdapter`
- [ ] 投票系統功能正常工作
- [ ] 可選擇使用或不使用投票功能
- [ ] 測試覆蓋投票邏輯

---

### S20-5: 遷移 GroupChat 測試 (5 pts)

**目標**: 將測試從 domain 遷移到適配器

**測試文件**:
- `tests/unit/test_groupchat_adapter.py` (新建)
- `tests/unit/test_groupchat_voting_adapter.py` (新建)
- `tests/integration/test_groupchat_api.py` (更新)

**測試清單**:
- [ ] 基本創建和執行測試
- [ ] 5 種選擇策略測試 (round_robin, random, expertise, llm_based, voting)
- [ ] 終止條件測試 (max_rounds, keywords, consensus, timeout)
- [ ] 投票系統測試 (majority, unanimous, ranked)
- [ ] API 端點集成測試
- [ ] 錯誤處理測試
- [ ] 性能基準測試

**驗收標準**:
- [ ] 所有新增測試通過
- [ ] 測試覆蓋率 > 80%
- [ ] 無回歸測試失敗

---

### S20-6: 標記舊代碼為 Deprecated (3 pts)

**目標**: 標記 `domain/orchestration/groupchat/` 為棄用

**範圍**: `domain/orchestration/groupchat/__init__.py`

**修改內容**:
```python
# domain/orchestration/groupchat/__init__.py
"""
GroupChat 模組 - 已棄用

⚠️ 警告: 此模組已棄用，將在 Sprint 25 移除。
請使用 integrations.agent_framework.builders.groupchat 代替。

遷移指南: docs/03-implementation/migration/groupchat-migration.md
"""

import warnings

warnings.warn(
    "domain.orchestration.groupchat 模組已棄用，將在 Sprint 25 移除。"
    "請使用 integrations.agent_framework.builders.groupchat 代替。"
    "遷移指南: docs/03-implementation/migration/groupchat-migration.md",
    DeprecationWarning,
    stacklevel=2,
)

# 保留導出以保持向後兼容
from .manager import GroupChatManager  # noqa: F401
from .speaker_selector import SpeakerSelector  # noqa: F401
from .termination import TerminationCondition  # noqa: F401
```

**驗收標準**:
- [ ] 導入 `domain.orchestration.groupchat` 時顯示棄用警告
- [ ] 向後兼容性保留
- [ ] 創建遷移指南文檔

---

## Sprint 完成標準 (Definition of Done)

### 代碼驗證

```bash
# 1. 檢查 API 層不再直接依賴 domain/orchestration/groupchat
cd backend
grep -r "from domain.orchestration.groupchat" src/api/
# 預期: 返回 0 結果

# 2. 驗證官方 API 使用
python scripts/verify_official_api_usage.py
# 預期: 所有檢查通過

# 3. 運行所有測試
pytest tests/ -v --tb=short
# 預期: 所有測試通過
```

### 完成確認清單

- [ ] S20-1: GroupChat API 路由重構完成
- [ ] S20-2: SpeakerSelector 整合完成
- [ ] S20-3: Termination 條件整合完成
- [ ] S20-4: Voting 系統擴展完成
- [ ] S20-5: 測試遷移完成
- [ ] S20-6: 舊代碼標記 deprecated
- [ ] 所有測試通過
- [ ] 代碼審查完成
- [ ] 更新 bmm-workflow-status.yaml

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| API 響應格式變更 | 低 | 高 | 保持相同的響應 Schema |
| 性能下降 | 低 | 中 | 性能基準測試對比 |
| 測試失敗 | 中 | 中 | 逐步遷移，保留舊代碼 |

---

## 依賴關係

| 依賴項 | 狀態 | 說明 |
|--------|------|------|
| Sprint 19 | ✅ 完成 | 官方 API 整合已完成 |
| `GroupChatBuilderAdapter` | ✅ 存在 | 需要擴展功能 |
| 官方 `GroupChatBuilder` | ✅ 可用 | `from agent_framework import GroupChatBuilder` |

---

## 時間規劃

| Story | Points | 建議順序 | 依賴 |
|-------|--------|----------|------|
| S20-2: SpeakerSelector | 8 | 1 | 無 |
| S20-3: Termination | 5 | 2 | 無 |
| S20-4: Voting 擴展 | 5 | 3 | S20-2 |
| S20-1: API 路由重構 | 8 | 4 | S20-2, S20-3 |
| S20-5: 測試遷移 | 5 | 5 | S20-1, S20-4 |
| S20-6: 標記 Deprecated | 3 | 6 | S20-5 |

**建議執行順序**: 先完成適配器功能 (S20-2, S20-3, S20-4)，再進行 API 遷移 (S20-1)，最後完成測試和清理 (S20-5, S20-6)。

---

**創建日期**: 2025-12-06
**最後更新**: 2025-12-06
**版本**: 1.0
