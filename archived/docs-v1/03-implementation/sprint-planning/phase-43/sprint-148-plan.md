# Sprint 148: Swarm Core Engine — 真正的多 Agent 並行執行

## Sprint 目標

1. TaskDecomposer：用 LLM 將複雜任務拆解為獨立子任務
2. SwarmWorkerExecutor：每個 Worker 獨立執行 LLM + function calling
3. SwarmModeHandler 改為真正 asyncio.gather() 並行
4. 每個 Worker 執行中發射 SSE 事件（thinking, tool_call, progress, completed）
5. ExecutionHandler → SwarmModeHandler 完整接線

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 43 — Agent Swarm 完整實現 |
| **Sprint** | 148 |
| **Story Points** | 14 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S148-1: TaskDecomposer — LLM 任務拆解 (4 SP)

**作為** Swarm 模式的使用者
**我希望** 系統能自動將我的複雜請求拆解為多個子任務
**以便** 每個 Worker Agent 能專注處理一個明確的子任務

**技術規格**:

**改動 1: `backend/src/integrations/swarm/task_decomposer.py` — 新建**
- 使用 `LLMServiceProtocol.generate_structured()` 將用戶輸入拆解為子任務
- 輸出結構：
  ```python
  @dataclass
  class DecomposedTask:
      task_id: str
      title: str           # 子任務標題
      description: str     # 詳細描述
      role: str           # 需要的專家角色 (network, database, application, security, etc.)
      priority: int       # 優先級 (1=最高)
      dependencies: list  # 依賴其他子任務的 ID（用於 sequential/pipeline 模式）
      tools_needed: list  # 建議使用的工具名稱

  @dataclass
  class TaskDecomposition:
      original_task: str
      mode: str           # parallel / sequential / pipeline
      sub_tasks: list[DecomposedTask]
      reasoning: str      # LLM 的拆解理由
  ```
- LLM Prompt 包含：
  - 可用工具列表（從 ToolRegistry 取得）
  - 可用角色定義（預設 5 種：network_expert, db_expert, app_expert, security_expert, general）
  - 拆解規則：每個子任務必須獨立可執行、有明確的輸出格式
- 如果任務太簡單（LLM 判斷只需 1 個 worker），直接建立單個子任務

**改動 2: `backend/src/integrations/swarm/worker_roles.py` — 新建**
- 定義 Worker 角色與對應的 system prompt：
  ```python
  WORKER_ROLES = {
      "network_expert": {
          "name": "網路專家",
          "system_prompt": "你是一位資深網路工程師...",
          "tools": ["assess_risk", "search_knowledge"],
      },
      "db_expert": {
          "name": "資料庫專家",
          "system_prompt": "你是一位資深 DBA...",
          "tools": ["assess_risk", "search_knowledge", "search_memory"],
      },
      "app_expert": {
          "name": "應用層專家",
          "system_prompt": "你是一位資深應用開發工程師...",
          "tools": ["assess_risk", "search_knowledge", "create_task"],
      },
      "security_expert": {
          "name": "資安專家",
          "system_prompt": "你是一位資深資安工程師...",
          "tools": ["assess_risk", "search_knowledge"],
      },
      "general": {
          "name": "通用助手",
          "system_prompt": "你是一位 IT 運維助手...",
          "tools": ["assess_risk", "search_memory", "search_knowledge"],
      },
  }
  ```
- 每個角色有獨立的 system prompt，引導 LLM 以該角色思考
- 每個角色有允許使用的工具子集

### S148-2: SwarmWorkerExecutor — 真正的 Worker 執行 (5 SP)

**作為** Swarm Pipeline
**我希望** 每個 Worker 能獨立執行 LLM function calling 並即時報告進度
**以便** 前端能看到每個 Worker 的思考過程、工具調用和結果

**技術規格**:

**改動 1: `backend/src/integrations/swarm/worker_executor.py` — 新建**
- `SwarmWorkerExecutor` class：
  ```python
  class SwarmWorkerExecutor:
      def __init__(
          self,
          worker_id: str,
          role: str,
          task: DecomposedTask,
          llm_service: LLMServiceProtocol,
          tool_registry: OrchestratorToolRegistry,
          event_emitter: PipelineEventEmitter,
          timeout: float = 60.0,
      ): ...

      async def execute(self) -> WorkerResult:
          """完整的 Worker 執行流程"""
          # 1. 發射 SWARM_WORKER_START
          # 2. 建立角色 system prompt + 子任務 prompt
          # 3. function calling loop (max 5 iterations):
          #    - 呼叫 llm_service.chat_with_tools()
          #    - 發射 SWARM_WORKER_THINKING (每次 LLM 回應)
          #    - 如果有 tool_calls:
          #      - 發射 SWARM_WORKER_TOOL_CALL (每個 tool)
          #      - 執行 tool_registry.execute()
          #      - 發射 SWARM_WORKER_PROGRESS
          #    - 如果是純文字回應 → 完成
          # 4. 發射 SWARM_WORKER_COMPLETED
          # 5. 回傳 WorkerResult
  ```
- Worker 的 tool_registry 會被過濾，只允許該角色可用的工具
- 每個 Worker 有獨立的 message 歷史（不共享）
- timeout 超時 → 發射 SWARM_WORKER_FAILED + 回傳部分結果

**改動 2: `backend/src/integrations/swarm/models.py` — 擴充**
- 新增 `WorkerResult` dataclass：
  ```python
  @dataclass
  class WorkerResult:
      worker_id: str
      role: str
      task_title: str
      status: str  # "completed" | "failed" | "timeout"
      content: str  # 最終回應文字
      tool_calls_made: list[dict]  # 調用過的工具
      thinking_steps: list[str]    # 思考過程
      duration_ms: float
      error: Optional[str] = None
  ```

### S148-3: SwarmModeHandler 並行執行 + SSE 接線 (5 SP)

**作為** Pipeline ExecutionHandler
**我希望** SwarmModeHandler 能真正並行執行多個 Worker 並串流事件
**以便** 前端即時看到所有 Worker 的狀態

**技術規格**:

**改動 1: `backend/src/integrations/hybrid/swarm_mode.py` — 重寫 _execute_all_workers()**
- 替換現有的 for loop 為 `asyncio.gather(*worker_tasks)`
- 每個 worker 用 `SwarmWorkerExecutor` 執行
- 加入 `max_concurrent_workers` 配置（預設 5，避免 API rate limit）
- 使用 `asyncio.Semaphore` 控制並行數
- 每個 Worker 失敗不影響其他 Worker（`return_exceptions=True`）

**改動 2: `backend/src/integrations/hybrid/swarm_mode.py` — execute() 接入 PipelineEventEmitter**
- execute() 接受 `event_emitter: PipelineEventEmitter` 參數
- 開始時發射 SWARM_STARTED
- 結束時發射 SWARM_COMPLETED
- 每個 Worker 的事件由 SwarmWorkerExecutor 直接發射

**改動 3: `backend/src/integrations/hybrid/orchestrator/handlers/execution.py` — SWARM_MODE 完整接線**
- ExecutionHandler 的 SWARM_MODE 分支改為呼叫 `swarm_handler.execute()`
- 傳入 `llm_service`、`tool_registry`、`event_emitter`
- 接收 SwarmResult（含所有 WorkerResult）
- 將 SwarmResult 傳給 ResultAggregator（Sprint 150）

**改動 4: `backend/src/integrations/hybrid/orchestrator/mediator.py` — 傳遞 event_emitter**
- 確保 ExecutionHandler 能存取 event_emitter
- 將 event_emitter 放入 pipeline_context

## 驗收標準

- [ ] TaskDecomposer 能用 LLM 將複雜任務拆為 2-5 個子任務
- [ ] SwarmWorkerExecutor 能獨立執行 LLM function calling
- [ ] 每個 Worker 有角色 system prompt 和工具子集
- [ ] Workers 真正用 asyncio.gather() 並行執行
- [ ] Semaphore 控制最大並行數
- [ ] 每個 Worker 執行中發射 THINKING / TOOL_CALL / PROGRESS / COMPLETED 事件
- [ ] Worker 失敗不影響其他 Worker
- [ ] Worker timeout 有 graceful fallback
- [ ] ExecutionHandler 完整接線 SwarmModeHandler
- [ ] event_emitter 貫穿到 Worker 層
- [ ] 不使用任何 mock 數據
- [ ] `black . && isort . && flake8 .` 通過

## 相關連結

- [Phase 43 計劃](./README.md)
- [Sprint 149 Plan](./sprint-149-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 14
