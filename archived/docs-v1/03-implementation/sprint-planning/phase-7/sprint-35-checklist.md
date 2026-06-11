# Sprint 35 Checklist: Phase 2 擴展 LLM 整合

**Sprint 目標**: 將 LLM 服務注入所有 Phase 2 擴展組件
**總點數**: 23 Story Points
**狀態**: ✅ 已完成
**完成日期**: 2025-12-21
**前置條件**: Sprint 34 完成 ✅

---

## Story Checklist

### S35-1: PlanningAdapter LLM 整合 (8 pts)

**狀態**: ✅ 已完成

#### 準備工作
- [x] 確認 Sprint 34 完成
- [x] 確認 LLMServiceFactory 可用
- [x] 閱讀現有 PlanningAdapter 代碼

#### 實現任務
- [x] 添加 LLM 導入語句
  ```python
  from src.integrations.llm import LLMServiceFactory
  from src.integrations.llm.protocol import LLMServiceProtocol
  ```
- [x] 更新 `__init__` 方法
  - [x] 添加 `llm_service` 參數
  - [x] 實現 `_ensure_llm_service()` 方法
  - [x] 添加 `with_llm_service()` 鏈式方法
- [x] 更新 `with_task_decomposition()` 方法
  - [x] 傳遞 `llm_service` 給 TaskDecomposer
- [x] 更新 `with_decision_engine()` 方法
  - [x] 傳遞 `llm_service` 給 DecisionEngine
- [x] 更新 `with_trial_error()` 方法
  - [x] 傳遞 `llm_service` 給 TrialAndErrorEngine
- [x] 更新 `with_dynamic_planner()` 方法
  - [x] 確保 TaskDecomposer 獲得 LLM 服務
- [x] 更新 `decompose_task()` 方法
  - [x] 創建 TaskDecomposer 時注入 LLM
- [x] 更新工廠函數
  - [x] `create_planning_adapter()` 接受 llm_service
  - [x] `create_decomposed_planner()` 接受 llm_service
  - [x] `create_full_planner()` 接受 llm_service

#### 驗證
- [x] 語法檢查通過
- [x] 類型檢查通過
- [x] 現有測試通過（向後兼容）

---

### S35-2: TaskDecomposer LLM 驗證 (5 pts)

**狀態**: ✅ 已完成

#### 準備工作
- [x] 分析現有 LLM 邏輯 (行 313-321)
- [x] 確認 Prompt 模板位置

#### 實現任務
- [x] 驗證 `if self.llm_service:` 路徑正確觸發
- [x] 確認 llm_service 參數在 __init__ 中正確接收 (line 228)
- [x] 確認 _decompose_simple/hybrid/llm 方法正確使用 llm_service
- [x] 確認降級邏輯正常工作（無 LLM 時使用規則式）

#### 驗證
- [x] LLM 路徑正確觸發（測試確認）
- [x] 降級邏輯正常工作

---

### S35-3: DecisionEngine LLM 驗證 (5 pts)

**狀態**: ✅ 已完成

#### 準備工作
- [x] 分析現有 LLM 邏輯 (行 329-360)
- [x] 確認決策輸出格式

#### 實現任務
- [x] 驗證 `if self.llm_service:` 路徑正確觸發
- [x] 確認 llm_service 參數在 __init__ 中正確接收 (line 174)
- [x] 確認 analyze 方法正確使用 llm_service
- [x] 確認降級邏輯正常工作

#### 驗證
- [x] LLM 決策分析正確觸發
- [x] 降級邏輯正常工作

---

### S35-4: TrialAndErrorEngine LLM 驗證 (5 pts)

**狀態**: ✅ 已完成

#### 準備工作
- [x] 分析現有 LLM 邏輯 (行 355-390)
- [x] 確認錯誤分析輸出格式

#### 實現任務
- [x] 驗證 `if self.llm_service:` 路徑正確觸發
- [x] 確認 llm_service 參數在 __init__ 中正確接收 (line 181)
- [x] 確認 analyze_failure 方法正確使用 llm_service
- [x] 確認降級邏輯正常工作

#### 驗證
- [x] LLM 錯誤分析正確觸發
- [x] 降級邏輯正常工作

---

## 驗證命令

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/agent_framework/builders/planning.py
python -m py_compile src/domain/orchestration/planning/task_decomposer.py
python -m py_compile src/domain/orchestration/planning/decision_engine.py
python -m py_compile src/domain/orchestration/planning/trial_error.py
# 預期: 無輸出 ✅

# 2. 運行 LLM 注入測試
pytest tests/unit/integrations/agent_framework/builders/test_planning_llm_injection.py -v
# 預期: 21 passed ✅
# 結果: 21 tests passed
```

---

## 完成定義

- [x] 所有 S35 Story 完成
- [x] PlanningAdapter.__init__ 接受 llm_service 參數
- [x] with_llm_service() 鏈式方法
- [x] _ensure_llm_service() 自動獲取單例
- [x] with_task_decomposition() 注入 LLM
- [x] with_decision_engine() 注入 LLM
- [x] with_trial_error() 注入 LLM
- [x] with_dynamic_planner() 注入 LLM
- [x] decompose_task() 注入 LLM
- [x] 工廠函數支援 llm_service 參數
- [x] TaskDecomposer 已支援 llm_service (驗證)
- [x] DecisionEngine 已支援 llm_service (驗證)
- [x] TrialAndErrorEngine 已支援 llm_service (驗證)
- [x] 所有現有測試通過（向後兼容）
- [x] 新增 21 個 LLM 注入測試
- [x] 代碼審查完成

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `builders/planning.py` | ✅ 修改 | 添加 LLM 服務注入邏輯 |
| `tests/unit/.../test_planning_llm_injection.py` | ✅ 新增 | 21 個 LLM 注入測試 |

---

## 實現細節

### LLM 注入模式

```python
# 構造函數注入
adapter = PlanningAdapter(id="test", llm_service=my_llm)

# 鏈式方法注入
adapter = PlanningAdapter(id="test").with_llm_service(my_llm)

# 自動單例獲取
adapter = PlanningAdapter(id="test")  # 自動調用 LLMServiceFactory.create(singleton=True)
```

### 降級策略

```python
# 各組件內部自動降級
if self.llm_service:
    # 使用 AI 自主決策
    result = await self.llm_service.generate_structured(...)
else:
    # 使用規則式邏輯
    result = self._rule_based_logic(...)
```

---

## 回滾計劃

如果 LLM 整合導致問題：

1. **快速回滾**: PlanningAdapter 保持向後兼容，`llm_service=None` 時使用規則式
2. **降級策略**: 各組件內部有 `if self.llm_service:` 檢查，無 LLM 時自動降級
3. **配置開關**: 可通過 `LLM_ENABLED=false` 環境變量禁用 LLM

---

**創建日期**: 2025-12-21
**完成日期**: 2025-12-21
