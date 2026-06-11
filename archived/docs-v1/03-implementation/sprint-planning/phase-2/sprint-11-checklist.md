# Sprint 11 Checklist: 嵌套工作流 (Nested Workflows & Advanced Orchestration)

**Sprint 目標**: 實現工作流嵌套和遞歸執行能力，支援複雜的階層式流程編排
**週期**: Week 23-24
**總點數**: 39 點
**Phase 2 功能**: P2-F11 Nested Workflows + P2-F12 Sub-workflow Execution + P2-F13 Recursive Patterns
**狀態**: ✅ 完成 (39/39 點)
**完成日期**: 2025-12-05

---

## 快速驗證命令

```bash
# 驗證嵌套工作流模組
python -c "from src.domain.orchestration.nested import NestedWorkflowManager; print('OK')"

# 驗證嵌套 API
curl http://localhost:8000/api/v1/nested/status

# 執行嵌套工作流
curl -X POST http://localhost:8000/api/v1/nested/execute \
  -H "Content-Type: application/json" \
  -d '{"parent_workflow_id": "uuid", "sub_workflow_id": "uuid"}'

# 運行嵌套測試
cd backend && pytest tests/unit/test_nested*.py tests/unit/test_recursive*.py -v
```

---

## S11-1: NestedWorkflowManager 嵌套工作流管理器 (8 點) ✅

### 核心管理器 (src/domain/orchestration/nested/)
- [x] 創建 `workflow_manager.py`
  - [x] NestedWorkflowType 枚舉
    - [x] INLINE - 內聯定義
    - [x] REFERENCE - 引用現有
    - [x] DYNAMIC - 動態生成
    - [x] RECURSIVE - 遞歸調用
  - [x] WorkflowScope 枚舉
    - [x] ISOLATED - 完全隔離
    - [x] INHERITED - 繼承上下文
    - [x] SHARED - 共享上下文
  - [x] NestedWorkflowConfig 數據類
    - [x] workflow_type 屬性
    - [x] scope 屬性
    - [x] max_depth 屬性
    - [x] timeout_seconds 屬性
    - [x] retry_on_failure 屬性
    - [x] max_retries 屬性
    - [x] pass_context 屬性
    - [x] return_outputs 屬性
  - [x] SubWorkflowReference 數據類
    - [x] id 屬性
    - [x] parent_workflow_id 屬性
    - [x] workflow_id 屬性
    - [x] definition 屬性
    - [x] config 屬性
    - [x] input_mapping 屬性
    - [x] output_mapping 屬性
    - [x] position 屬性
    - [x] status 屬性
  - [x] NestedExecutionContext 數據類
    - [x] execution_id 屬性
    - [x] parent_execution_id 屬性
    - [x] workflow_id 屬性
    - [x] depth 屬性
    - [x] path 屬性
    - [x] variables 屬性
    - [x] parent_variables 屬性
  - [x] NestedWorkflowManager 類
    - [x] __init__() 初始化方法
    - [x] register_sub_workflow() 註冊子工作流
    - [x] _has_cycle() 循環依賴檢測
    - [x] execute_sub_workflow() 執行子工作流
    - [x] _create_child_context() 創建子上下文
    - [x] _execute_reference_workflow() 執行引用工作流
    - [x] _execute_inline_workflow() 執行內聯工作流
    - [x] _execute_dynamic_workflow() 執行動態工作流
    - [x] _execute_recursive_workflow() 執行遞歸工作流
    - [x] _map_outputs() 映射輸出
    - [x] get_execution_tree() 獲取執行樹
    - [x] cancel_nested_execution() 取消嵌套執行

### 依賴圖管理
- [x] 創建 `dependency_graph.py` (內建於 workflow_manager.py)
  - [x] DependencyGraph 類
  - [x] add_dependency() 添加依賴
  - [x] remove_dependency() 移除依賴
  - [x] has_cycle() 循環檢測
  - [x] get_topological_order() 拓撲排序
  - [x] visualize() 視覺化

### 驗證標準
- [x] 支援工作流嵌套結構
- [x] 正確的深度限制
- [x] 循環依賴檢測
- [x] 上下文傳遞正確
- [x] 單元測試覆蓋率 > 85%

---

## S11-2: SubWorkflowExecutor 子工作流執行器 (5 點) ✅

### 執行器實現 (src/domain/orchestration/nested/)
- [x] 創建 `sub_executor.py`
  - [x] SubWorkflowExecutionMode 枚舉
    - [x] SYNC - 同步等待
    - [x] ASYNC - 異步執行
    - [x] FIRE_AND_FORGET - 發射即忘
    - [x] CALLBACK - 完成回調
  - [x] SubExecutionState 數據類
    - [x] execution_id 屬性
    - [x] sub_workflow_id 屬性
    - [x] mode 屬性
    - [x] status 屬性
    - [x] result 屬性
    - [x] error 屬性
    - [x] callback 屬性
  - [x] SubWorkflowExecutor 類
    - [x] __init__() 初始化方法
    - [x] execute() 執行
    - [x] execute_async() 異步執行
    - [x] execute_with_callback() 回調執行
    - [x] wait_for_completion() 等待完成
    - [x] cancel() 取消執行
    - [x] get_status() 獲取狀態

### 執行池管理
- [x] 創建 `execution_pool.py` (內建於 sub_executor.py)
  - [x] SubWorkflowPool 類
  - [x] submit() 提交執行
  - [x] get_result() 獲取結果
  - [x] cancel_all() 取消所有
  - [x] get_active_count() 獲取活躍數

### 驗證標準
- [x] 同步執行正確
- [x] 異步執行不阻塞
- [x] 回調正確觸發
- [x] 超時處理正常
- [x] 取消操作有效

---

## S11-3: RecursivePatternHandler 遞歸模式處理器 (5 點) ✅

### 遞歸處理 (src/domain/orchestration/nested/)
- [x] 創建 `recursive_handler.py`
  - [x] RecursionStrategy 枚舉
    - [x] DEPTH_FIRST - 深度優先
    - [x] BREADTH_FIRST - 廣度優先
    - [x] PARALLEL - 並行執行
  - [x] TerminationConditionType 枚舉
    - [x] CONDITION - 條件表達式
    - [x] MAX_DEPTH - 最大深度
    - [x] MAX_ITERATIONS - 最大迭代次數
    - [x] TIMEOUT - 超時
    - [x] CONVERGENCE - 收斂檢測
    - [x] USER_ABORT - 用戶終止
  - [x] TerminationCondition 數據類
    - [x] condition_type 屬性
    - [x] check_function 屬性
    - [x] max_iterations 屬性
    - [x] timeout_seconds 屬性
  - [x] RecursivePatternHandler 類
    - [x] __init__() 初始化方法
    - [x] execute_recursive() 執行遞歸
    - [x] _check_termination() 檢查終止
    - [x] _execute_iteration() 執行迭代
    - [x] set_termination_condition() 設置終止條件
    - [x] get_recursion_depth() 獲取深度
    - [x] get_iteration_history() 獲取迭代歷史

### 堆疊管理
- [x] 創建 `recursion_stack.py` (內建於 recursive_handler.py)
  - [x] RecursionStack 類
  - [x] push() 入棧
  - [x] pop() 出棧
  - [x] peek() 查看棧頂
  - [x] get_depth() 獲取深度
  - [x] is_overflow() 溢出檢查
  - [x] get_trace() 獲取追蹤

### 記憶化支援
- [x] 創建 Memoization 支援
  - [x] MemoizationCache 類
  - [x] get_cached() 獲取緩存
  - [x] set_cached() 設置緩存
  - [x] compute_hash() 計算輸入哈希

### 驗證標準
- [x] 遞歸執行正確
- [x] 終止條件有效
- [x] 堆疊溢出保護
- [x] 記憶化優化工作
- [x] 迭代歷史可追蹤

---

## S11-4: WorkflowCompositionBuilder 工作流組合構建器 (5 點) ✅

### 組合構建 (src/domain/orchestration/nested/)
- [x] 創建 `composition_builder.py`
  - [x] CompositionType 枚舉
    - [x] SEQUENCE - 順序組合
    - [x] PARALLEL - 並行組合
    - [x] CONDITIONAL - 條件組合
    - [x] LOOP - 循環組合
    - [x] SWITCH - 選擇組合
  - [x] WorkflowComponent 數據類
    - [x] component_id 屬性
    - [x] component_type 屬性
    - [x] workflow_reference 屬性
    - [x] inputs 屬性
    - [x] outputs 屬性
  - [x] WorkflowCompositionBuilder 類 (Fluent API)
    - [x] __init__() 初始化方法
    - [x] add_sequential() / sequence() 添加順序
    - [x] add_parallel() / parallel() 添加並行
    - [x] add_conditional() / conditional() 添加條件
    - [x] add_loop() / loop() 添加循環
    - [x] add_switch() / switch() 添加選擇
    - [x] build() 構建組合
    - [x] validate() 驗證組合
    - [x] optimize() 優化組合

### 模板支援
- [x] 創建 `composition_templates.py` (內建於 composition_builder.py)
  - [x] CompositionTemplate 類
  - [x] create_map_reduce() Map-Reduce 模板
  - [x] create_scatter_gather() Scatter-Gather 模板
  - [x] create_pipeline() Pipeline 模板
  - [x] create_saga() Saga 模板

### 驗證標準
- [x] 順序組合正確
- [x] 並行組合正確
- [x] 條件組合正確
- [x] 循環組合正確
- [x] 模板可用

---

## S11-5: Nested Workflow API 路由 (8 點) ✅

### API 路由 (src/api/v1/nested/)
- [x] 創建 `routes.py`
  - [x] POST /nested/configs - 創建嵌套配置
  - [x] GET /nested/configs - 列出配置
  - [x] GET /nested/configs/{id} - 獲取配置
  - [x] DELETE /nested/configs/{id} - 刪除配置
  - [x] POST /nested/sub-workflows/execute - 執行子工作流
  - [x] POST /nested/sub-workflows/batch - 批次執行
  - [x] GET /nested/sub-workflows/{id}/status - 獲取狀態
  - [x] POST /nested/sub-workflows/{id}/cancel - 取消執行
  - [x] POST /nested/recursive/execute - 遞歸執行
  - [x] GET /nested/recursive/{id}/status - 獲取遞歸狀態
  - [x] POST /nested/compositions - 創建組合
  - [x] POST /nested/compositions/execute - 執行組合
  - [x] POST /nested/context/propagate - 傳播上下文
  - [x] GET /nested/context/flow/{id} - 獲取數據流
  - [x] GET /nested/context/tracker/stats - 獲取追蹤統計
  - [x] GET /nested/stats - 獲取整體統計

### 請求/響應 Schema
- [x] 創建 `schemas.py`
  - [x] NestedWorkflowTypeEnum
  - [x] WorkflowScopeEnum
  - [x] SubWorkflowExecutionModeEnum
  - [x] RecursionStrategyEnum
  - [x] CompositionTypeEnum
  - [x] PropagationTypeEnum
  - [x] ExecutionStatusEnum
  - [x] CreateNestedConfigRequest/Response
  - [x] SubWorkflowExecuteRequest/Response
  - [x] BatchExecuteRequest/Response
  - [x] RecursiveExecuteRequest/Response
  - [x] CompositionCreateRequest/Response
  - [x] ContextPropagateRequest/Response

### 驗證標準
- [x] 所有 API 端點可用
- [x] 執行樹正確呈現
- [x] 組合 API 正確
- [x] 驗證 API 有效
- [x] API 文檔完整

---

## S11-6: Context Propagation 上下文傳播 (8 點) ✅

### 上下文傳播 (src/domain/orchestration/nested/)
- [x] 創建 `context_propagation.py`
  - [x] PropagationType 枚舉
    - [x] COPY - 深拷貝
    - [x] REFERENCE - 引用共享
    - [x] MERGE - 合併
    - [x] FILTER - 過濾傳播
  - [x] VariableScopeType 枚舉
    - [x] LOCAL - 本地作用域
    - [x] PARENT - 父級作用域
    - [x] GLOBAL - 全局作用域
    - [x] INHERITED - 繼承作用域
  - [x] DataFlowDirection 枚舉
    - [x] DOWNSTREAM - 向下流動
    - [x] UPSTREAM - 向上流動
    - [x] BIDIRECTIONAL - 雙向流動
  - [x] ContextPropagator 類
    - [x] propagate_down() 向下傳播
    - [x] propagate_up() 向上傳播
    - [x] merge_contexts() 合併上下文
    - [x] isolate_context() 隔離上下文
    - [x] transform_context() 轉換上下文

### 變數作用域
- [x] 創建 VariableScope 類
  - [x] define_variable() 定義變數
  - [x] get() 獲取變數
  - [x] set() 設置變數
  - [x] resolve() 解析引用
  - [x] create_child() 創建子作用域

### 數據流追蹤
- [x] 創建 DataFlowTracker 類
  - [x] record_flow() 記錄流動
  - [x] get_events() 獲取事件
  - [x] get_events_for_workflow() 獲取工作流事件
  - [x] get_stats() 獲取統計
  - [x] clear() 清除記錄

### 驗證標準
- [x] 向下傳播正確
- [x] 向上傳播正確
- [x] 作用域隔離有效
- [x] 數據流可追蹤
- [x] 引用解析正確

---

## 測試完成 ✅

### 單元測試
- [x] test_nested_workflow_manager.py (25 tests)
  - [x] test_register_sub_workflow
  - [x] test_cycle_detection
  - [x] test_execute_sub_workflow
  - [x] test_depth_limit
  - [x] test_context_propagation
- [x] test_sub_executor.py (20 tests)
  - [x] test_sync_execution
  - [x] test_async_execution
  - [x] test_callback_execution
  - [x] test_cancellation
- [x] test_recursive_handler.py (25 tests)
  - [x] test_recursive_execution
  - [x] test_termination_condition
  - [x] test_stack_overflow_protection
  - [x] test_memoization
- [x] test_composition_builder.py (25 tests)
  - [x] test_sequential_composition
  - [x] test_parallel_composition
  - [x] test_conditional_composition
  - [x] test_loop_composition
- [x] test_context_propagation.py (25 tests)
  - [x] test_propagate_down
  - [x] test_propagate_up
  - [x] test_scope_isolation

### 整合測試
- [x] test_nested_api.py (25 tests)
  - [x] test_create_nested_config
  - [x] test_execute_sub_workflow
  - [x] test_recursive_execution
  - [x] test_composition_execution
  - [x] test_context_propagation

### 覆蓋率
- [x] 單元測試覆蓋率 >= 85%
- [x] 整合測試覆蓋主要流程

**總測試數**: 145 個測試案例

---

## 資料庫遷移 ⏳ (延後)

### 遷移腳本
- [ ] 創建 `011_nested_workflow_tables.sql`
  - [ ] nested_workflows 表
  - [ ] sub_workflow_references 表
  - [ ] nested_executions 表
  - [ ] execution_contexts 表
  - [ ] composition_definitions 表
  - [ ] 相關索引

**註**: 資料庫遷移將在 Sprint 12 整合階段一併處理

---

## 文檔完成 ✅

### API 文檔
- [x] Swagger 嵌套工作流 API 文檔
- [x] 請求/響應範例
- [x] 錯誤碼說明

### 開發者文檔
- [x] 嵌套工作流指南
  - [x] 嵌套類型說明
  - [x] 深度限制配置
  - [x] 循環依賴處理
- [x] 遞歸模式指南
  - [x] 終止條件設定
  - [x] 記憶化優化
- [x] 工作流組合指南
  - [x] 組合模式說明
  - [x] 內建模板使用
- [x] 上下文傳播指南
  - [x] 作用域類型
  - [x] 變數映射

---

## Sprint 完成標準

### 必須完成 (Must Have) ✅
- [x] NestedWorkflowManager 支援嵌套
- [x] SubWorkflowExecutor 可執行子工作流
- [x] 循環依賴檢測有效
- [x] 深度限制正確
- [x] 測試覆蓋率 >= 85%

### 應該完成 (Should Have) ✅
- [x] 遞歸模式支援
- [x] 工作流組合構建器
- [x] 文檔完整

### 可以延後 (Could Have) ✅
- [x] 進階組合模板 (map_reduce, pipeline, scatter_gather, saga)
- [x] 執行樹視覺化

---

## 依賴確認

### 前置 Sprint
- [x] Sprint 7-10 完成
  - [x] 並行執行
  - [x] 動態規劃

### 外部依賴
- [x] 工作流引擎核心
- [x] 執行服務
- [x] 持久化存儲

---

## Sprint 11 完成統計

| Story | 點數 | 狀態 | 測試數 |
|-------|------|------|--------|
| S11-1: NestedWorkflowManager | 8 | ✅ 完成 | 25 |
| S11-2: SubWorkflowExecutor | 5 | ✅ 完成 | 20 |
| S11-3: RecursivePatternHandler | 5 | ✅ 完成 | 25 |
| S11-4: WorkflowCompositionBuilder | 5 | ✅ 完成 | 25 |
| S11-5: Nested Workflow API | 8 | ✅ 完成 | 25 |
| S11-6: Context Propagation | 8 | ✅ 完成 | 25 |
| **總計** | **39** | **✅ 完成** | **145** |

---

## 關鍵實現細節

### 嵌套工作流類型
```python
class NestedWorkflowType(str, Enum):
    INLINE = "inline"       # 內聯定義
    REFERENCE = "reference" # 引用現有
    DYNAMIC = "dynamic"     # 動態生成
    RECURSIVE = "recursive" # 遞歸自調用
```

### 執行模式
```python
class SubWorkflowExecutionMode(str, Enum):
    SYNC = "sync"                   # 同步等待
    ASYNC = "async"                 # 異步非阻塞
    FIRE_AND_FORGET = "fire_and_forget"  # 發射即忘
    CALLBACK = "callback"           # 回調模式
```

### 遞歸策略
```python
class RecursionStrategy(str, Enum):
    DEPTH_FIRST = "depth_first"     # 深度優先
    BREADTH_FIRST = "breadth_first" # 廣度優先
    PARALLEL = "parallel"           # 並行執行
```

### 上下文傳播
```python
class PropagationType(str, Enum):
    COPY = "copy"           # 深拷貝
    REFERENCE = "reference" # 引用共享
    MERGE = "merge"         # 合併
    FILTER = "filter"       # 過濾傳播
```

---

## 相關連結

- [Sprint 11 Plan](./sprint-11-plan.md) - 詳細計劃
- [Sprint 11 Progress](../../sprint-execution/sprint-11/progress.md) - 進度記錄
- [Sprint 11 Decisions](../../sprint-execution/sprint-11/decisions.md) - 決策記錄
- [Phase 2 Overview](./README.md) - Phase 2 概述
- [Sprint 10 Checklist](./sprint-10-checklist.md) - 前置 Sprint
- [Sprint 12 Plan](./sprint-12-plan.md) - 後續 Sprint

---

**完成時間**: 2025-12-05
**Commit**: 151dc70
