# Sprint 148 Checklist: Swarm Core Engine — 真正的多 Agent 並行執行

**Sprint**: 148 | **Phase**: 43 | **Story Points**: 14
**Plan**: [sprint-148-plan.md](./sprint-148-plan.md)

---

## S148-1: TaskDecomposer — LLM 任務拆解 (4 SP)

### task_decomposer.py 新建
- [ ] `swarm/task_decomposer.py` — TaskDecomposer class
- [ ] 使用 LLMServiceProtocol.generate_structured() 拆解任務
- [ ] DecomposedTask dataclass（task_id, title, description, role, priority, dependencies, tools_needed）
- [ ] TaskDecomposition dataclass（original_task, mode, sub_tasks, reasoning）
- [ ] LLM prompt 含可用工具列表、角色定義、拆解規則
- [ ] 簡單任務自動判斷為單 worker

### worker_roles.py 新建
- [ ] `swarm/worker_roles.py` — WORKER_ROLES 角色定義
- [ ] 5 種角色：network_expert, db_expert, app_expert, security_expert, general
- [ ] 每個角色有獨立 system prompt
- [ ] 每個角色有允許使用的工具子集

## S148-2: SwarmWorkerExecutor — 真正的 Worker 執行 (5 SP)

### worker_executor.py 新建
- [ ] `swarm/worker_executor.py` — SwarmWorkerExecutor class
- [ ] 接收 worker_id, role, task, llm_service, tool_registry, event_emitter
- [ ] execute() 方法：完整的 function calling loop
- [ ] 發射 SWARM_WORKER_START 事件
- [ ] 發射 SWARM_WORKER_THINKING 事件（每次 LLM 回應）
- [ ] 發射 SWARM_WORKER_TOOL_CALL 事件（每個工具調用）
- [ ] 發射 SWARM_WORKER_PROGRESS 事件（進度更新）
- [ ] 發射 SWARM_WORKER_COMPLETED 事件
- [ ] tool_registry 按角色過濾可用工具
- [ ] 獨立 message 歷史（不共享）
- [ ] timeout 超時 → SWARM_WORKER_FAILED + 部分結果

### models.py 擴充
- [ ] WorkerResult dataclass（worker_id, role, status, content, tool_calls_made, thinking_steps, duration_ms, error）

## S148-3: SwarmModeHandler 並行執行 + SSE 接線 (5 SP)

### swarm_mode.py 重寫
- [ ] _execute_all_workers() — asyncio.gather(*worker_tasks, return_exceptions=True)
- [ ] asyncio.Semaphore 控制 max_concurrent_workers（預設 5）
- [ ] 每個 Worker 用 SwarmWorkerExecutor 執行
- [ ] Worker 失敗不影響其他 Worker

### execute() SSE 接線
- [ ] execute() 接受 event_emitter 參數
- [ ] 開始時發射 SWARM_STARTED（swarm_id, mode, total_workers, tasks[]）
- [ ] 結束時發射 SWARM_COMPLETED（final_result, duration, worker_summaries）

### ExecutionHandler 接線
- [ ] execution.py SWARM_MODE 呼叫 swarm_handler.execute()
- [ ] 傳入 llm_service, tool_registry, event_emitter
- [ ] 接收 SwarmResult 含所有 WorkerResult

### Mediator event_emitter 傳遞
- [ ] event_emitter 放入 pipeline_context
- [ ] ExecutionHandler 從 pipeline_context 取得 event_emitter

## 驗收測試

- [ ] TaskDecomposer 能拆解複雜任務為 2-5 個子任務
- [ ] SwarmWorkerExecutor 完整執行 LLM function calling
- [ ] 每個 Worker 有角色 prompt + 工具子集
- [ ] asyncio.gather() 真正並行
- [ ] Semaphore 控制最大並行數
- [ ] 6 種 Worker SSE 事件正確發射
- [ ] Worker 失敗不影響其他
- [ ] timeout graceful fallback
- [ ] ExecutionHandler 完整接線
- [ ] 不使用任何 mock 數據
- [ ] `black . && isort . && flake8 .` 通過

---

**狀態**: 📋 計劃中
