# Sprint 21: Handoff 完整遷移

## Sprint Overview

| Property | Value |
|----------|-------|
| **Sprint** | 21 |
| **Phase** | 4 - 完整重構 |
| **Focus** | 將 Handoff API 遷移到適配器 |
| **Duration** | 2 週 |
| **Total Story Points** | 32 |

## Sprint Goal

將 `domain/orchestration/handoff/` 的所有功能遷移到 `HandoffBuilderAdapter`，確保 API 層完全使用適配器，保留政策映射、能力匹配、上下文傳遞等 Phase 2 功能。

---

## 問題分析

### 當前狀態

| 項目 | 當前值 | 問題 |
|------|--------|------|
| `domain/orchestration/handoff/` | 3,341 行 | 自行實現，未使用官方 API |
| API 層依賴 | 直接使用 HandoffController | 繞過適配器層 |
| `HandoffBuilderAdapter` | 已存在 | 未被 API 層使用 |

### Phase 2 自定義功能

需要保留的 Phase 2 擴展功能:
1. **HandoffPolicy** - IMMEDIATE, GRACEFUL, CONDITIONAL 策略
2. **CapabilityMatcher** - 智能 Agent 能力匹配
3. **ContextTransfer** - 上下文傳遞策略
4. **HandoffTrigger** - 6 種觸發類型

---

## User Stories

### S21-1: 設計政策映射層 (5 pts)

**目標**: 創建 `HandoffPolicyAdapter` 映射 Phase 2 政策到官方 API

**範圍**: 新建 `integrations/agent_framework/builders/handoff_policy.py`

**政策映射表**:

| Phase 2 政策 | 官方 API 映射 | 說明 |
|-------------|---------------|------|
| `IMMEDIATE` | `interaction_mode="autonomous"` | 立即交接，無需確認 |
| `GRACEFUL` | `interaction_mode="human_in_loop"` | 需要人工確認 |
| `CONDITIONAL` | `termination_condition=fn` | 根據條件決定 |

**實現方式**:
```python
# integrations/agent_framework/builders/handoff_policy.py

from enum import Enum
from typing import Callable, Optional, Dict, Any
from domain.orchestration.handoff.controller import HandoffPolicy as LegacyPolicy

class HandoffPolicyAdapter:
    """
    將 Phase 2 HandoffPolicy 映射到官方 API 的配置。
    """

    @staticmethod
    def adapt(
        legacy_policy: LegacyPolicy,
        condition_evaluator: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        返回適配後的配置字典。

        Returns:
            {
                "interaction_mode": str,
                "termination_condition": Optional[Callable],
            }
        """

        if legacy_policy == LegacyPolicy.IMMEDIATE:
            return {
                "interaction_mode": "autonomous",
                "termination_condition": None,
            }

        elif legacy_policy == LegacyPolicy.GRACEFUL:
            return {
                "interaction_mode": "human_in_loop",
                "termination_condition": None,
            }

        elif legacy_policy == LegacyPolicy.CONDITIONAL:
            if not condition_evaluator:
                raise ValueError("CONDITIONAL 政策需要提供 condition_evaluator")

            return {
                "interaction_mode": "autonomous",
                "termination_condition": lambda conv: condition_evaluator(conv),
            }

        else:
            raise ValueError(f"未知政策: {legacy_policy}")
```

**驗收標準**:
- [ ] `HandoffPolicyAdapter` 正確映射所有 3 種政策
- [ ] 映射結果可直接用於官方 `HandoffBuilder`
- [ ] 單元測試覆蓋所有政策類型
- [ ] 錯誤處理完善（缺少 condition_evaluator 時拋出明確錯誤）

---

### S21-2: 整合 CapabilityMatcher (8 pts)

**目標**: 將能力匹配邏輯封裝為選擇器函數

**範圍**: `integrations/agent_framework/builders/handoff.py`

**能力匹配策略**:
1. `BEST_FIT` - 最佳匹配（所有能力都滿足）
2. `FIRST_FIT` - 第一個匹配（快速選擇）
3. `ROUND_ROBIN` - 輪詢（負載均衡）
4. `LEAST_LOADED` - 最小負載

**實現方式**:
```python
class HandoffBuilderAdapter:
    def with_capability_matching(
        self,
        capabilities: Dict[str, List[str]],
        matching_strategy: MatchStrategy = MatchStrategy.BEST_FIT,
    ) -> "HandoffBuilderAdapter":
        """
        啟用能力匹配功能。

        Args:
            capabilities: Agent ID -> 能力列表
            matching_strategy: 匹配策略
        """
        from domain.orchestration.handoff.capability_matcher import CapabilityMatcher

        matcher = CapabilityMatcher(
            capabilities=capabilities,
            strategy=matching_strategy,
        )

        def capability_selector(state) -> str:
            task = state.get("current_task", {})
            required_capabilities = task.get("required_capabilities", [])

            # 使用 Phase 2 的匹配邏輯
            best_match = matcher.find_best_match(required_capabilities)
            return best_match.agent_id

        self._custom_selector = capability_selector
        return self
```

**驗收標準**:
- [ ] 所有 4 種匹配策略正常工作
- [ ] 與官方 `HandoffBuilder` 整合正確
- [ ] 測試覆蓋每種策略
- [ ] 性能基準測試通過

---

### S21-3: 整合 ContextTransfer (5 pts)

**目標**: 保留上下文傳遞邏輯

**範圍**: `integrations/agent_framework/builders/handoff.py`

**上下文傳遞策略**:
1. `FULL` - 完整傳遞所有上下文
2. `MINIMAL` - 最小傳遞（僅必要信息）
3. `FILTERED` - 過濾傳遞（根據過濾函數）
4. `NONE` - 不傳遞

**實現方式**:
```python
class HandoffBuilderAdapter:
    def with_context_transfer(
        self,
        transfer_strategy: ContextTransferStrategy = ContextTransferStrategy.FULL,
        context_filter: Optional[Callable] = None,
    ) -> "HandoffBuilderAdapter":
        """
        配置上下文傳遞策略。
        """
        from domain.orchestration.handoff.context_transfer import ContextTransfer

        self._context_transfer = ContextTransfer(
            strategy=transfer_strategy,
            filter_fn=context_filter,
        )
        return self

    async def _prepare_handoff_context(self, source_state, target_agent):
        """在交接時準備上下文"""
        if self._context_transfer:
            return await self._context_transfer.prepare(source_state, target_agent)
        return source_state
```

**驗收標準**:
- [ ] 所有傳遞策略正常工作
- [ ] 自定義過濾函數正確執行
- [ ] 測試覆蓋每種策略
- [ ] 上下文數據完整性驗證

---

### S21-4: 重構 Handoff API 路由 (8 pts)

**目標**: 修改 API 層以使用 `HandoffBuilderAdapter`

**範圍**: `api/v1/handoff/routes.py`

**修改前**:
```python
from domain.orchestration.handoff.controller import HandoffController

@router.post("/initiate")
async def initiate_handoff(request: HandoffRequest):
    controller = HandoffController(...)
    return await controller.initiate(request)
```

**修改後**:
```python
from integrations.agent_framework.builders.handoff import HandoffBuilderAdapter
from integrations.agent_framework.builders.handoff_policy import HandoffPolicyAdapter

@router.post("/initiate")
async def initiate_handoff(request: HandoffRequest):
    # 適配政策
    policy_config = HandoffPolicyAdapter.adapt(request.policy)

    adapter = HandoffBuilderAdapter(
        id=request.id,
        participants=request.participants,
        **policy_config,
    )

    if request.capability_matching:
        adapter.with_capability_matching(
            capabilities=request.capabilities,
            matching_strategy=request.matching_strategy,
        )

    if request.context_transfer:
        adapter.with_context_transfer(
            transfer_strategy=request.transfer_strategy,
        )

    workflow = adapter.build()
    return await adapter.run(request.initial_context)
```

**需要重構的端點**:
- [ ] `POST /initiate` - 發起交接
- [ ] `POST /execute` - 執行交接
- [ ] `GET /status/{id}` - 查詢狀態
- [ ] `POST /cancel/{id}` - 取消交接
- [ ] `GET /history` - 交接歷史

**驗收標準**:
- [ ] `grep "from domain.orchestration.handoff" api/` 返回 0 結果
- [ ] 所有 API 端點正常工作
- [ ] API 響應格式保持不變
- [ ] 集成測試通過

---

### S21-5: 遷移測試和文檔 (6 pts)

**測試文件**:
- 新建 `tests/unit/test_handoff_adapter.py`
- 新建 `tests/unit/test_handoff_policy_adapter.py`
- 更新 `tests/integration/test_handoff_api.py`

**測試清單**:
- [ ] 政策映射測試（IMMEDIATE, GRACEFUL, CONDITIONAL）
- [ ] 能力匹配測試（BEST_FIT, FIRST_FIT, ROUND_ROBIN, LEAST_LOADED）
- [ ] 上下文傳遞測試（FULL, MINIMAL, FILTERED, NONE）
- [ ] API 端點集成測試
- [ ] 錯誤處理測試
- [ ] 邊界情況測試

**文檔更新**:
- [ ] 創建 `docs/03-implementation/migration/handoff-migration.md`
- [ ] 更新 API 文檔

**驗收標準**:
- [ ] 所有測試通過
- [ ] 測試覆蓋率 > 80%
- [ ] 遷移指南完成

---

## Sprint 完成標準 (Definition of Done)

### 代碼驗證

```bash
# 1. 檢查 API 層不再直接依賴 domain/orchestration/handoff
cd backend
grep -r "from domain.orchestration.handoff" src/api/
# 預期: 返回 0 結果

# 2. 驗證官方 API 使用
python scripts/verify_official_api_usage.py
# 預期: 所有檢查通過

# 3. 運行所有測試
pytest tests/unit/test_handoff*.py tests/integration/test_handoff*.py -v
# 預期: 所有測試通過
```

### 完成確認清單

- [ ] S21-1: 政策映射層完成
- [ ] S21-2: CapabilityMatcher 整合完成
- [ ] S21-3: ContextTransfer 整合完成
- [ ] S21-4: API 路由重構完成
- [ ] S21-5: 測試和文檔完成
- [ ] 所有測試通過
- [ ] 代碼審查完成
- [ ] 更新 bmm-workflow-status.yaml

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 政策映射不完整 | 中 | 高 | 詳細測試每種政策組合 |
| 能力匹配性能 | 低 | 中 | 性能基準測試 |
| 上下文數據丟失 | 中 | 高 | 數據完整性測試 |

---

## 依賴關係

| 依賴項 | 狀態 | 說明 |
|--------|------|------|
| Sprint 20 | 待完成 | GroupChat 遷移 |
| `HandoffBuilderAdapter` | ✅ 存在 | 需要擴展功能 |
| 官方 `HandoffBuilder` | ✅ 可用 | `from agent_framework import HandoffBuilder` |

---

## 時間規劃

| Story | Points | 建議順序 | 依賴 |
|-------|--------|----------|------|
| S21-1: 政策映射層 | 5 | 1 | 無 |
| S21-2: CapabilityMatcher | 8 | 2 | 無 |
| S21-3: ContextTransfer | 5 | 3 | 無 |
| S21-4: API 路由重構 | 8 | 4 | S21-1, S21-2, S21-3 |
| S21-5: 測試和文檔 | 6 | 5 | S21-4 |

---

**創建日期**: 2025-12-06
**最後更新**: 2025-12-06
**版本**: 1.0
