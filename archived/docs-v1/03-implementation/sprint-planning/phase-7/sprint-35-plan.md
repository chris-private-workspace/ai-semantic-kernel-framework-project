# Sprint 35: Phase 2 擴展 LLM 整合

**Sprint 目標**: 將 LLM 服務注入所有 Phase 2 擴展組件，實現真正的 AI 自主決策
**總點數**: 23 Story Points
**優先級**: 🔴 CRITICAL
**前置條件**: Sprint 34 完成

---

## 背景

Sprint 34 創建了 LLM 服務基礎設施後，本 Sprint 將把 LLM 服務注入到所有 Phase 2 擴展組件中，使其從「規則式自動化」升級為「AI 自主決策」。

### 修改目標

```python
# 修改前 (規則式)
self._task_decomposer = TaskDecomposer(
    max_subtasks=max_subtasks,
    max_depth=max_depth,
)  # ❌ 無 LLM

# 修改後 (AI 自主)
self._task_decomposer = TaskDecomposer(
    llm_service=self._llm_service,  # ✅ 注入 LLM
    max_subtasks=max_subtasks,
    max_depth=max_depth,
)
```

---

## Story 清單

### S35-1: PlanningAdapter LLM 整合 (8 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 重構
**影響範圍**: `backend/src/integrations/agent_framework/builders/planning.py`

#### 設計

```python
# 修改 PlanningAdapter 構造函數

class PlanningAdapter:
    """動態規劃適配器 - 現在支援 LLM!"""

    def __init__(
        self,
        id: str,
        config: Optional[PlanningConfig] = None,
        llm_service: Optional[LLMServiceProtocol] = None,  # 新增參數
    ):
        self._id = id
        self._config = config or PlanningConfig()

        # 官方 Builder 實例
        self._magentic_builder = MagenticBuilder()

        # LLM 服務 (Phase 7 新增)
        self._llm_service = llm_service
        self._ensure_llm_service()

        # Phase 2 擴展功能
        self._task_decomposer: Optional[TaskDecomposer] = None
        self._decision_engine: Optional[AutonomousDecisionEngine] = None
        self._trial_error_engine: Optional[TrialAndErrorEngine] = None

    def _ensure_llm_service(self) -> None:
        """確保 LLM 服務可用。"""
        if self._llm_service is None:
            from src.integrations.llm import LLMServiceFactory
            self._llm_service = LLMServiceFactory.get_singleton()
            logger.info(f"PlanningAdapter '{self._id}': Using singleton LLM service")
```

#### 任務清單

1. **更新 PlanningAdapter 構造函數**
   - 添加 `llm_service` 參數
   - 實現 `_ensure_llm_service()` 方法
   - 更新日誌記錄

2. **更新 with_task_decomposition()**
   ```python
   def with_task_decomposition(
       self,
       strategy: DecompositionStrategy = DecompositionStrategy.HYBRID,
       max_subtasks: Optional[int] = None,
       max_depth: Optional[int] = None,
   ) -> "PlanningAdapter":
       self._decomposition_strategy = strategy

       self._task_decomposer = TaskDecomposer(
           llm_service=self._llm_service,  # ✅ 注入 LLM
           max_subtasks=max_subtasks or self._config.max_subtasks,
           max_depth=max_depth or self._config.max_depth,
       )

       self._mode = PlanningMode.DECOMPOSED
       logger.info(f"Enabled task decomposition with LLM: {strategy.value}")
       return self
   ```

3. **更新 with_decision_engine()**
   ```python
   def with_decision_engine(
       self,
       risk_threshold: float = 0.7,
       auto_decision_confidence: float = 0.8,
       rules: Optional[List[DecisionRule]] = None,
   ) -> "PlanningAdapter":
       self._decision_engine = AutonomousDecisionEngine(
           llm_service=self._llm_service,  # ✅ 注入 LLM
           risk_threshold=risk_threshold,
           auto_decision_confidence=auto_decision_confidence,
       )

       if rules:
           for rule in rules:
               self._decision_engine.add_rule(...)

       self._mode = PlanningMode.DECISION_DRIVEN
       logger.info("Enabled decision engine with LLM")
       return self
   ```

4. **更新 with_trial_error()**
   ```python
   def with_trial_error(
       self,
       max_retries: int = 3,
       learning_threshold: float = 0.6,
   ) -> "PlanningAdapter":
       self._trial_error_engine = TrialAndErrorEngine(
           llm_service=self._llm_service,  # ✅ 注入 LLM
           max_retries=max_retries,
           learning_threshold=learning_threshold,
           timeout_seconds=int(self._config.timeout_seconds),
       )

       self._mode = PlanningMode.ADAPTIVE
       logger.info("Enabled trial-error engine with LLM")
       return self
   ```

5. **添加導入語句**
   ```python
   from src.integrations.llm import LLMServiceProtocol, LLMServiceFactory
   ```

#### 驗收標準
- [ ] PlanningAdapter 接受 `llm_service` 參數
- [ ] 所有 `with_*` 方法注入 LLM 服務
- [ ] 自動獲取單例 LLM 服務（如未提供）
- [ ] 語法檢查通過
- [ ] 現有測試不受影響（向後兼容）

---

### S35-2: TaskDecomposer LLM 啟用 (5 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 驗證/修復
**影響範圍**: `backend/src/domain/orchestration/planning/task_decomposer.py`

#### 背景

TaskDecomposer 已經設計支援 LLM（有 `llm_service` 參數），但需要驗證 LLM 路徑是否正確工作。

#### 任務清單

1. **驗證現有 LLM 邏輯**
   ```python
   # 驗證這段邏輯正確工作
   if self.llm_service:
       response = await self.llm_service.generate(
           prompt=prompt,
           max_tokens=2000
       )
       return self._parse_decomposition_response(task_id, response)

   # Fallback: simple rule-based decomposition
   return self._rule_based_decomposition(task_id, task_description, "hierarchical")
   ```

2. **優化 LLM Prompt 模板**
   ```python
   DECOMPOSITION_PROMPT_TEMPLATE = """
   You are a task decomposition expert. Break down the following task into subtasks.

   Task: {task_description}
   Strategy: {strategy}
   Max Subtasks: {max_subtasks}
   Max Depth: {max_depth}

   Please provide a JSON response with the following structure:
   {
       "subtasks": [
           {
               "name": "subtask name",
               "description": "what this subtask does",
               "priority": "high|medium|low",
               "dependencies": ["dependency_id"],
               "estimated_duration_minutes": 30
           }
       ],
       "execution_order": ["subtask_id_1", "subtask_id_2"],
       "confidence": 0.85
   }
   """
   ```

3. **添加結構化輸出支援**
   - 使用 `generate_structured()` 替代 `generate()` + 手動解析
   - 定義輸出 JSON Schema

4. **增強錯誤處理**
   - LLM 失敗時優雅降級到規則式
   - 添加重試邏輯

#### 驗收標準
- [ ] LLM 路徑正確觸發（非規則式）
- [ ] Prompt 模板優化完成
- [ ] 結構化輸出正常工作
- [ ] 錯誤處理和降級正確

---

### S35-3: DecisionEngine LLM 啟用 (5 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 驗證/修復
**影響範圍**: `backend/src/domain/orchestration/planning/decision_engine.py`

#### 任務清單

1. **驗證現有 LLM 邏輯**
   ```python
   # decision_engine.py 行 329-360
   if self.llm_service:
       # 應該執行 LLM 決策分析
       ...
   ```

2. **優化決策 Prompt**
   ```python
   DECISION_PROMPT_TEMPLATE = """
   You are a decision-making expert. Analyze the following situation and options.

   Situation: {situation}
   Decision Type: {decision_type}

   Options:
   {options_list}

   Context:
   {context}

   Please analyze each option and provide a JSON response:
   {
       "selected_option": "option_id",
       "confidence": 0.85,
       "reasoning": "explanation of why this option was chosen",
       "pros": ["advantage 1", "advantage 2"],
       "cons": ["disadvantage 1"],
       "risk_assessment": {
           "level": "low|medium|high",
           "factors": ["risk factor 1"],
           "mitigations": ["mitigation 1"]
       }
   }
   """
   ```

3. **添加結構化輸出支援**

4. **驗證風險評估邏輯**
   - 確保 LLM 返回的風險評估正確解析
   - 驗證置信度計算

#### 驗收標準
- [ ] LLM 決策分析正確觸發
- [ ] Prompt 模板優化完成
- [ ] 風險評估正確解析
- [ ] 決策記錄包含 LLM 推理

---

### S35-4: TrialAndErrorEngine LLM 啟用 (5 pts)

**優先級**: 🟡 P1
**類型**: 驗證/修復
**影響範圍**: `backend/src/domain/orchestration/planning/trial_error.py`

#### 任務清單

1. **驗證現有 LLM 邏輯**
   ```python
   # trial_error.py 行 355-390
   if self.llm_service:
       # 應該執行 LLM 錯誤分析
       response = await self.llm_service.generate(
           prompt=prompt,
           max_tokens=1000
       )
   ```

2. **優化錯誤分析 Prompt**
   ```python
   ERROR_ANALYSIS_PROMPT_TEMPLATE = """
   You are an error analysis expert. Analyze the following execution failure.

   Task: {task_description}
   Error: {error_message}
   Attempt: {attempt_number} of {max_attempts}

   Previous attempts:
   {previous_attempts}

   Please analyze and provide a JSON response:
   {
       "error_category": "category name",
       "root_cause": "analysis of root cause",
       "is_recoverable": true,
       "suggested_fix": "how to fix this",
       "parameter_adjustments": {
           "param1": "new_value"
       },
       "confidence": 0.75
   }
   """
   ```

3. **添加學習模式支援**
   - 成功/失敗模式學習
   - 參數調整建議

4. **驗證重試邏輯**
   - 確保 LLM 建議的參數調整被應用

#### 驗收標準
- [ ] LLM 錯誤分析正確觸發
- [ ] Prompt 模板優化完成
- [ ] 參數調整建議正確應用
- [ ] 學習模式正常工作

---

## 整合測試設計

### 端到端測試用例

```python
# tests/integration/test_planning_with_llm.py

import pytest
from src.integrations.agent_framework.builders import PlanningAdapter
from src.integrations.llm import MockLLMService


class TestPlanningAdapterWithLLM:
    """PlanningAdapter LLM 整合測試。"""

    @pytest.fixture
    def mock_llm(self):
        """創建 Mock LLM 服務。"""
        return MockLLMService(responses={
            "decompose": '{"subtasks": [...], "confidence": 0.9}',
            "decide": '{"selected_option": "option_1", "confidence": 0.85}',
        })

    @pytest.mark.asyncio
    async def test_decomposition_uses_llm(self, mock_llm):
        """驗證任務分解使用 LLM。"""
        adapter = PlanningAdapter("test", llm_service=mock_llm)
        adapter.with_task_decomposition()

        result = await adapter.decompose("Build a REST API")

        assert mock_llm.call_count > 0
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_decision_uses_llm(self, mock_llm):
        """驗證決策使用 LLM。"""
        adapter = PlanningAdapter("test", llm_service=mock_llm)
        adapter.with_decision_engine()

        result = await adapter.decide(
            situation="Choose deployment strategy",
            options=["Blue-Green", "Canary", "Rolling"]
        )

        assert mock_llm.call_count > 0
        assert result["reasoning"] is not None
```

---

## 驗證命令

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/agent_framework/builders/planning.py

# 2. 驗證 LLM 注入
python -c "
from src.integrations.agent_framework.builders import PlanningAdapter

adapter = PlanningAdapter('test')
print(f'LLM Service: {adapter._llm_service}')
adapter.with_task_decomposition()
print(f'TaskDecomposer LLM: {adapter._task_decomposer.llm_service}')
"
# 預期: LLM Service 和 TaskDecomposer LLM 都不為 None

# 3. 運行整合測試
pytest tests/integration/test_planning_with_llm.py -v

# 4. 驗證現有測試不受影響
pytest tests/unit/test_planning*.py -v
```

---

## 完成定義

- [ ] 所有 S35 Story 完成
- [ ] PlanningAdapter 注入 LLM 服務
- [ ] TaskDecomposer 使用 LLM
- [ ] DecisionEngine 使用 LLM
- [ ] TrialAndErrorEngine 使用 LLM
- [ ] 整合測試通過
- [ ] 現有測試不受影響
- [ ] 代碼審查完成

---

**創建日期**: 2025-12-21
