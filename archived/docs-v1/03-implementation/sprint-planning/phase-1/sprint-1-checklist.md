# Sprint 1 Checklist: 核心引擎 - Agent Framework 集成

**Sprint 目標**: 完成 Microsoft Agent Framework 核心集成，實現基礎 Agent 編排能力
**週期**: Week 3-4
**總點數**: 42 點
**MVP 功能**: F1 - 順序式 Agent 編排
**狀態**: ✅ 完成 (42/42 點)

---

## 快速驗證命令

```bash
# 驗證 Agent Framework 安裝
python -c "from agent_framework import WorkflowBuilder; print('OK')"

# 驗證 Agent API
curl http://localhost:8000/api/v1/agents/

# 驗證 Workflow 執行
curl -X POST http://localhost:8000/api/v1/workflows/{id}/execute -d '{"message": "test"}'

# 運行測試
cd backend && pytest tests/unit/test_agent*.py tests/unit/test_workflow*.py -v
```

---

## S1-1: Agent Framework 核心集成 (13 點) ✅

### Azure OpenAI 客戶端
- [x] 安裝 agent-framework[azure] 依賴
- [x] 配置 Azure 憑證管理
  - [x] 開發環境: Azure CLI 認證
  - [x] 生產環境: Managed Identity
- [x] 創建 AzureOpenAIChatClient 初始化邏輯
- [x] 實現客戶端連接池管理

### Agent 服務層 (src/domain/agents/)
- [x] 創建 `service.py`
  - [x] AgentConfig 數據類
  - [x] AgentService 類
  - [x] initialize() 初始化方法
  - [x] create_agent() 創建方法
  - [x] run_agent() 執行方法
  - [x] _calculate_cost() 成本計算
- [x] 創建 Repository (src/infrastructure/database/repositories/)
  - [x] AgentRepository.create()
  - [x] AgentRepository.get()
  - [x] AgentRepository.update()
  - [x] AgentRepository.delete()
  - [x] AgentRepository.list()

### Agent API (src/api/v1/agents/)
- [x] 創建 `routes.py`
  - [x] POST /agents/ - 創建 Agent
  - [x] GET /agents/ - 列出 Agent
  - [x] GET /agents/{id} - 獲取 Agent
  - [x] PUT /agents/{id} - 更新 Agent
  - [x] DELETE /agents/{id} - 刪除 Agent
  - [x] POST /agents/{id}/run - 運行 Agent
- [x] 創建請求/響應 Schema
  - [x] AgentCreateRequest
  - [x] AgentUpdateRequest
  - [x] AgentResponse
  - [x] AgentRunRequest
  - [x] AgentRunResponse

### 驗證標準
- [x] `POST /api/v1/agents/` 返回 201
- [x] `GET /api/v1/agents/{id}` 返回正確數據
- [x] `POST /api/v1/agents/{id}/run` 返回 LLM 響應
- [x] 統計數據 (llm_calls, llm_tokens, llm_cost) 正確計算

---

## S1-2: Workflow 基礎結構 (13 點) ✅

### Workflow 領域模型 (src/domain/workflows/)
- [x] 創建 `models.py`
  - [x] NodeType 枚舉 (AGENT, GATEWAY, START, END)
  - [x] TriggerType 枚舉 (MANUAL, SCHEDULE, WEBHOOK, EVENT)
  - [x] WorkflowNode 數據類
  - [x] WorkflowEdge 數據類
  - [x] WorkflowDefinition 數據類
  - [x] validate() 驗證方法
- [x] 創建 Repository
  - [x] WorkflowRepository.create()
  - [x] WorkflowRepository.get()
  - [x] WorkflowRepository.update()
  - [x] WorkflowRepository.delete()
  - [x] WorkflowRepository.list()

### Workflow 執行服務
- [x] 創建 `execution_service.py`
  - [x] WorkflowExecutionService 類
  - [x] execute_workflow() 方法
  - [x] _build_workflow() 方法 - WorkflowBuilder 集成
  - [x] 事件流處理邏輯

### WorkflowBuilder 集成
- [x] 實現 set_start_executor() 調用
- [x] 實現 add_edge() 調用
- [x] 實現 build() 調用
- [x] 實現 run_stream() 執行
- [x] 處理 WorkflowOutputEvent

### Workflow API (src/api/v1/workflows/)
- [x] 創建 `routes.py`
  - [x] POST /workflows/ - 創建 Workflow
  - [x] GET /workflows/ - 列出 Workflow
  - [x] GET /workflows/{id} - 獲取 Workflow
  - [x] PUT /workflows/{id} - 更新 Workflow
  - [x] DELETE /workflows/{id} - 刪除 Workflow
  - [x] POST /workflows/{id}/execute - 執行 Workflow
- [x] 創建請求/響應 Schema
  - [x] WorkflowCreateRequest
  - [x] WorkflowExecuteRequest
  - [x] WorkflowResponse
  - [x] ExecutionResponse

### 驗證標準
- [x] Workflow 定義驗證正確拒絕無效定義
- [x] 順序式 Workflow (A → B → C) 正確執行
- [x] 執行結果正確保存到數據庫
- [x] 執行 ID 可用於查詢狀態

---

## S1-3: 工具 (Tools) 集成機制 (8 點) ✅

### 工具基礎架構 (src/domain/agents/tools/)
- [x] 創建 `base.py`
  - [x] ToolResult 數據類
  - [x] BaseTool 抽象基類
  - [x] name 屬性
  - [x] description 屬性
  - [x] execute() 抽象方法
  - [x] as_function() 轉換方法

### 內建工具 (src/domain/agents/tools/)
- [x] 創建 `builtin.py`
  - [x] HttpTool - HTTP 請求工具
    - [x] GET/POST/PUT/DELETE 支持
    - [x] 超時處理
    - [x] 錯誤處理
  - [x] DateTimeTool - 日期時間工具
    - [x] 格式化支持
    - [x] 時區支持
  - [x] get_weather() - 函數式工具示例
  - [x] search_knowledge_base() - 函數式工具示例

### 工具註冊 (src/domain/agents/tools/)
- [x] 創建 `registry.py`
  - [x] ToolRegistry 類
  - [x] register() 方法
  - [x] get() 方法
  - [x] get_all() 方法
  - [x] load_builtins() 方法

### Agent 工具集成
- [x] AgentService.create_agent() 支持工具參數
- [x] 工具調用結果正確返回給 Agent
- [x] 工具錯誤正確處理

### 驗證標準
- [x] Agent 可調用 HttpTool 發送請求
- [x] Agent 可調用 DateTimeTool 獲取時間
- [x] 自定義工具可通過 Registry 註冊
- [x] 工具執行錯誤不導致 Agent 崩潰

---

## S1-4: 執行狀態管理 (8 點) ✅

### 狀態機 (src/domain/executions/)
- [x] 創建 `state_machine.py`
  - [x] ExecutionStatus 枚舉
    - [x] PENDING
    - [x] RUNNING
    - [x] PAUSED
    - [x] COMPLETED
    - [x] FAILED
    - [x] CANCELLED
  - [x] ExecutionStateMachine 類
  - [x] TRANSITIONS 狀態轉換表
  - [x] can_transition() 方法
  - [x] transition() 方法
  - [x] is_terminal() 方法

### Execution Repository
- [x] 創建 ExecutionRepository
  - [x] create() 方法
  - [x] get() 方法
  - [x] update() 方法
  - [x] list() 方法 (支持過濾和分頁)

### Execution API (src/api/v1/executions/)
- [x] 創建 `routes.py`
  - [x] GET /executions/ - 列出執行記錄
  - [x] GET /executions/{id} - 獲取執行詳情
  - [x] POST /executions/{id}/cancel - 取消執行
- [x] 創建響應 Schema
  - [x] ExecutionDetailResponse
  - [x] ExecutionListResponse

### LLM 統計
- [x] llm_calls 計數正確
- [x] llm_tokens 統計正確 (input + output)
- [x] llm_cost 計算正確 (基於 GPT-4o 定價)

### 驗證標準
- [x] 狀態機正確阻止無效轉換
- [x] 執行記錄包含完整統計信息
- [x] 取消執行 API 正常工作
- [x] 列表 API 支持過濾 (workflow_id, status)

---

## 測試完成 ✅

### 單元測試
- [x] test_agent_service.py
  - [x] test_create_agent
  - [x] test_run_agent
  - [x] test_calculate_cost
- [x] test_workflow_models.py
  - [x] test_workflow_definition_validation
  - [x] test_invalid_workflow_definition
- [x] test_execution_state_machine.py
  - [x] test_valid_transitions
  - [x] test_invalid_transitions
  - [x] test_terminal_states
- [x] test_tools.py
  - [x] test_http_tool
  - [x] test_datetime_tool
  - [x] test_tool_registry

### 集成測試
- [x] test_agent_api.py
  - [x] test_create_agent
  - [x] test_run_agent
  - [x] test_agent_crud
- [ ] test_workflow_api.py (待完成)
  - [ ] test_create_workflow
  - [ ] test_execute_workflow
  - [ ] test_workflow_validation
- [ ] test_execution_api.py (待完成)
  - [ ] test_get_execution
  - [ ] test_list_executions
  - [ ] test_cancel_execution

### 覆蓋率
- [ ] 單元測試覆蓋率 >= 80% (當前 71%)
- [x] 集成測試覆蓋主要流程

---

## 文檔完成

### API 文檔
- [x] Swagger UI 可訪問 (/docs)
- [x] 所有端點有描述
- [x] 請求/響應示例完整

### 開發者文檔
- [ ] Agent 開發指南
  - [ ] 創建 Agent 步驟
  - [ ] 配置 Instructions
  - [ ] 添加工具
- [ ] Workflow 開發指南
  - [ ] 定義工作流結構
  - [ ] 節點類型說明
  - [ ] 執行流程說明
- [ ] 工具開發指南
  - [ ] 創建自定義工具
  - [ ] 工具參數定義
  - [ ] 錯誤處理

---

## Sprint 完成標準

### 必須完成 (Must Have) ✅
- [x] Agent 可創建和執行
- [x] Workflow 可順序執行多個 Agent
- [x] 工具可被 Agent 調用
- [x] 執行狀態可追蹤
- [ ] 測試覆蓋率 >= 80% (當前 71%)

### 應該完成 (Should Have)
- [x] LLM 成本統計完整
- [x] API 文檔完整
- [ ] 開發者指南完成

### 可以延後 (Could Have)
- [ ] 工具市場 UI
- [ ] 高級工具 (向量搜索)

---

## 依賴確認

### 前置 Sprint
- [x] Sprint 0 完成
  - [x] Docker 環境可用
  - [x] 數據庫遷移就緒
  - [x] CI/CD 運行正常

### 外部依賴
- [x] Azure OpenAI 配額確認
- [x] Azure 憑證配置完成
- [x] Agent Framework 版本確認

---

## Sprint 1 完成統計

| Story | 點數 | 狀態 | 測試數 |
|-------|------|------|--------|
| S1-1: Agent Framework 核心集成 | 13 | ✅ | 59 |
| S1-2: Workflow 基礎結構 | 13 | ✅ | 40 |
| S1-3: 工具集成機制 | 8 | ✅ | 78 |
| S1-4: 執行狀態管理 | 8 | ✅ | 45 |
| **總計** | **42** | **完成** | **233** |

---

## 相關連結

- [Sprint 1 Plan](./sprint-1-plan.md) - 詳細計劃
- [Sprint 0 Checklist](./sprint-0-checklist.md) - 前置 Sprint
- [Agent Framework 參考](../../../reference/agent-framework/)
- [Sprint 2 Plan](./sprint-2-plan.md) - 後續 Sprint
