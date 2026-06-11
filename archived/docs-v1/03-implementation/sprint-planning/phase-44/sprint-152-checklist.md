# Sprint 152 Checklist: Integration — Builder 整合 + API 端點 + E2E 驗證

**Sprint**: 152 | **Phase**: 44 | **Story Points**: 7
**Plan**: [sprint-152-plan.md](./sprint-152-plan.md)

---

## S152-1: MagenticBuilderAdapter 整合 Registry + Selector (3 SP)

### MagenticBuilderAdapter 改動
- [ ] `__init__()` 初始化 `ManagerModelRegistry.get_instance()`
- [ ] `__init__()` 初始化 `ManagerModelSelector(self._registry)`
- [ ] 新增 `build_with_model_selection(risk_level, complexity, manager_model_override)` 方法
- [ ] `build_with_model_selection()` 呼叫 `self._selector.select_model()` 取得 model_key
- [ ] `build_with_model_selection()` 呼叫 `self._registry.create_manager_agent(model_key)` 取得 manager
- [ ] `create_manager_agent()` 內部用 `Agent(client, name=...)` positional（PoC 已驗證）
- [ ] `build_with_model_selection()` 呼叫 `self.with_manager(manager)` 設定 manager
- [ ] `build_with_model_selection()` 呼叫 `self.build()` 構建 workflow
- [ ] `build()` 已修復為 `MagenticBuilder(..., manager_agent=self._manager)`（Sprint 151）
- [ ] 原有 `build()` 行為不變（向後兼容）

### ExecutionHandler 改動
- [ ] SWARM_MODE 分支改為呼叫 `build_with_model_selection()`
- [ ] 從 PipelineContext 或 RoutingDecision 取得 risk_level
- [ ] risk_level 不可用時預設 MEDIUM
- [ ] 保留 legacy fallback 路徑

### FrameworkSelector 傳遞
- [ ] 確認 `select_framework()` 的 routing_decision 正確包含 risk_level
- [ ] IntentAnalysis 返回值包含 risk_level 資訊
- [ ] risk_level 在 Mediator pipeline 中正確傳遞到 ExecutionHandler

### 整合測試
- [ ] `build_with_model_selection(CRITICAL)` → claude-opus-4-6 Manager
- [ ] `build_with_model_selection(LOW)` → claude-haiku-4-5 Manager
- [ ] `build_with_model_selection(override="gpt-4o")` → gpt-4o Manager
- [ ] 不帶參數 → 預設模型（claude-sonnet-4-6）
- [ ] 原有 `build()` 呼叫不受影響

---

## S152-2: Manager Model API 端點 (1 SP)

### 路由建立
- [ ] 建立 `backend/src/api/v1/orchestration/manager_model_routes.py`
- [ ] `GET /` — 列出所有可用模型 + 預設值
- [ ] `POST /test/{model_key}` — 測試模型連線（簡單 prompt）
- [ ] `POST /select` — 根據 risk_level + complexity 自動選擇
- [ ] 錯誤處理（無效 model_key、API 不可用）

### 路由註冊
- [ ] `main.py` 新增 `include_router(manager_model_router)`
- [ ] prefix 為 `/api/v1/orchestration`

### API 測試
- [ ] `GET /api/v1/orchestration/manager-models/` → 6 個模型清單
- [ ] `POST /test/gpt-4o` → {"status": "ok"}
- [ ] `POST /select?risk_level=CRITICAL` → "claude-opus-4-6"
- [ ] `POST /select?risk_level=LOW` → "claude-haiku-4-5"
- [ ] 無效 model_key → {"status": "error"}

---

## S152-3: E2E 驗證 — 逐步模型測試 (3 SP)

### Step 1: gpt-4o 回歸測試
- [ ] 不設 ANTHROPIC_API_KEY，確認自動 fallback 到 gpt-4o
- [ ] Swarm 模式執行「系統故障排查」
- [ ] Manager Agent 成功規劃子任務
- [ ] Workers 正常執行
- [ ] SSE 事件正確串流
- [ ] 結果與 Sprint 148 一致

### Step 2: claude-haiku-4-5 快速驗證
- [ ] 設定 ANTHROPIC_API_KEY
- [ ] 手動 override model_key="claude-haiku-4-5"
- [ ] Manager Agent 使用 Claude Haiku 進行規劃
- [ ] Workers 正常執行
- [ ] 回應速度快（Haiku 特性）

### Step 3: claude-sonnet-4-6 + Extended Thinking
- [ ] override model_key="claude-sonnet-4-6"
- [ ] Extended Thinking 啟用（budget_tokens=5000）
- [ ] Manager thinking 過程在 SSE 事件中可觀察
- [ ] 規劃品質優於 Haiku
- [ ] thinking blocks 正確處理

### Step 4: claude-opus-4-6 完整能力
- [ ] override model_key="claude-opus-4-6"
- [ ] Extended Thinking 啟用（budget_tokens=10000）
- [ ] Task Ledger 分解品質最優
- [ ] Progress Ledger 正確追蹤
- [ ] 深度推理能力展現

### Step 5: 自動選擇策略
- [ ] 「系統全面崩潰」→ CRITICAL → claude-opus-4-6
- [ ] 「部署失敗排查」→ HIGH → claude-sonnet-4-6
- [ ] 「常規變更管理」→ MEDIUM → gpt-4o
- [ ] 「查詢服務狀態」→ LOW → claude-haiku-4-5
- [ ] 無 ANTHROPIC_API_KEY → 全部 fallback 到 gpt-4o

---

## 驗收測試

### 功能驗收
- [ ] 5 步 E2E 測試全部通過
- [ ] gpt-4o 回歸無退步
- [ ] Anthropic 3 個模型都可正常使用
- [ ] 自動選擇策略符合 YAML 配置
- [ ] Manager Model API 3 個端點正常運作
- [ ] SSE 事件正確串流（包含 Manager thinking）

### 品質驗收
- [ ] TypeScript 零錯誤
- [ ] Python 型別檢查通過（mypy）
- [ ] 單元測試覆蓋率 >= 80%
- [ ] 無安全漏洞（API key 不暴露在回應中）

### 向後兼容
- [ ] 原有 `build()` 呼叫不受影響
- [ ] 不設 ANTHROPIC_API_KEY 時系統行為與升級前完全一致
- [ ] 現有 Chat/Workflow 模式不受影響
- [ ] 現有 Swarm 模式功能不退步
