# Sprint 152: Integration — Builder 整合 + API 端點 + E2E 驗證

## Sprint 目標

1. MagenticBuilderAdapter 整合 ManagerModelRegistry + ManagerModelSelector
2. FrameworkSelector / ExecutionHandler 傳遞 risk_level 到 Builder
3. 新增 Manager Model API 端點（列出/測試/自動選擇）
4. E2E 驗證：逐步測試 gpt-4o → haiku → sonnet → opus

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 44 — Magentic Orchestrator Agent |
| **Sprint** | 152 |
| **Story Points** | 7 點 |
| **狀態** | 📋 計劃中 |
| **前置** | Sprint 151 完成 |

## User Stories

### S152-1: MagenticBuilderAdapter 整合 Registry + Selector (3 SP)

**作為** 平台開發者
**我希望** MagenticBuilderAdapter 能根據風險等級自動選擇最佳 Manager 模型
**以便** 不同複雜度的任務使用最適合的 LLM（Opus 做深度推理，Haiku 做簡單查詢）

**技術規格**:

**改動 1: `backend/src/integrations/agent_framework/builders/magentic.py` — 整合 Registry**
- `__init__()` 中初始化 `ManagerModelRegistry.get_instance()` 和 `ManagerModelSelector`
- 新增 `build_with_model_selection()` 方法：
  ```python
  def build_with_model_selection(
      self,
      risk_level: RiskLevel = None,
      complexity: str = "MEDIUM",
      manager_model_override: str | None = None,
  ) -> "MagenticBuilderAdapter":
      model_key = self._selector.select_model(risk_level, complexity, manager_model_override)
      manager_agent = self._registry.create_manager_agent(model_key)
      # PoC 驗證: Agent(client, name=...) positional, 然後透過構造函數注入
      self.with_manager(manager_agent)
      return self.build()
      # build() 內部: MagenticBuilder(participants=..., manager_agent=self._manager)
  ```
- 保留原有 `build()` 方法不變（向後兼容）
- `build()` 已修復為在構造 `MagenticBuilder` 時傳入 `manager_agent=`（Sprint 151 S151-1）
- `build_with_model_selection()` 是新入口，ExecutionHandler 呼叫此方法

**改動 2: `backend/src/integrations/hybrid/orchestrator/handlers/execution.py` — SWARM_MODE 呼叫**
- SWARM_MODE 分支改為呼叫 `build_with_model_selection(risk_level=context.risk_level)`
- 從 PipelineContext 或 RoutingDecision 中取得 risk_level
- 若 risk_level 不可用，預設 MEDIUM

**改動 3: `backend/src/integrations/hybrid/intent/router.py` — 傳遞 routing_decision**
- 確認 `select_framework()` 的 `routing_decision` 參數正確傳遞 risk_level
- 在 IntentAnalysis 返回值中包含 risk_level（若尚未包含）

**驗收標準**:
- `build_with_model_selection(risk_level=CRITICAL)` → 使用 claude-opus-4-6 作為 Manager
- `build_with_model_selection(risk_level=LOW)` → 使用 claude-haiku-4-5 作為 Manager
- `build_with_model_selection(manager_model_override="gpt-4o")` → 使用 gpt-4o
- 不帶參數時使用預設模型（claude-sonnet-4-6）
- 原有 `build()` 行為不變（向後兼容）

### S152-2: Manager Model API 端點 (1 SP)

**作為** 前端開發者 / 運維人員
**我希望** 有 API 可以查詢可用模型、測試模型連線、查看自動選擇結果
**以便** 在前端顯示模型資訊並支持手動 override

**技術規格**:

**新增: `backend/src/api/v1/orchestration/manager_model_routes.py` (~50 LOC)**

```python
router = APIRouter(prefix="/manager-models", tags=["Manager Models"])

@router.get("/")           # 列出所有可用模型 + 預設值
@router.post("/test/{model_key}")  # 測試模型連線（傳 "OK" prompt）
@router.post("/select")    # 根據 risk_level + complexity 自動選擇
```

**改動: `backend/main.py` — 註冊路由**
- 新增 `app.include_router(manager_model_router, prefix="/api/v1/orchestration")`

**驗收標準**:
- `GET /api/v1/orchestration/manager-models/` → 返回 6 個模型清單
- `POST /api/v1/orchestration/manager-models/test/gpt-4o` → 返回 {"status": "ok"}
- `POST /api/v1/orchestration/manager-models/select?risk_level=CRITICAL` → 返回 "claude-opus-4-6"
- 無效 model_key → 返回 {"status": "error"}

### S152-3: E2E 驗證 — 逐步模型測試 (3 SP)

**作為** 品質保證
**我希望** 逐步驗證每個 Provider 和模型的完整 Magentic 流程
**以便** 確認多模型切換在真實環境中正確運作

**技術規格**:

**測試順序（由低風險到高風險）**:

**Step 1: gpt-4o 回歸測試**
- 目的：確認 build() 修復和 Registry 整合不破壞現有功能
- 方式：使用預設配置（無 ANTHROPIC_API_KEY），應自動 fallback 到 gpt-4o
- 驗證：Swarm 模式 E2E — 執行「系統故障排查」，結果與 Sprint 148 一致

**Step 2: claude-haiku-4-5 快速驗證**
- 目的：驗證 Anthropic 路徑 end-to-end
- 方式：設定 ANTHROPIC_API_KEY，手動 override model_key="claude-haiku-4-5"
- 驗證：Manager Agent 成功規劃子任務，Workers 正常執行

**Step 3: claude-sonnet-4-6 + Extended Thinking**
- 目的：驗證 Extended Thinking 整合
- 方式：override model_key="claude-sonnet-4-6"，啟用 thinking (budget_tokens=5000)
- 驗證：Manager 的 thinking 過程可在 SSE 事件中觀察

**Step 4: claude-opus-4-6 完整能力**
- 目的：驗證最強推理模型的 Magentic 完整流程
- 方式：override model_key="claude-opus-4-6"，thinking (budget_tokens=10000)
- 驗證：Task Ledger 分解品質優於其他模型，Progress Ledger 正確追蹤

**Step 5: 自動選擇策略**
- 目的：驗證 ManagerModelSelector 的自動策略
- 方式：模擬不同 risk_level 的輸入，檢查實際使用的模型
- 驗證：
  - 「系統全面崩潰」→ CRITICAL → claude-opus-4-6
  - 「部署失敗」→ HIGH → claude-sonnet-4-6
  - 「建立服務請求」→ LOW → claude-haiku-4-5

**驗收標準**:
- 5 個 Step 全部通過
- gpt-4o 回歸無退步
- Anthropic 3 個模型都可正常使用
- 自動選擇策略符合 YAML 配置
- SSE 事件正確串流（包含 Manager thinking）

## 測試矩陣

| 模型 | Provider | Thinking | 測試場景 | 預期 |
|------|---------|----------|---------|------|
| gpt-4o | Azure | ❌ | 回歸（現有功能） | 行為與修復前一致 |
| claude-haiku-4-5 | Anthropic | ❌ | 簡單查詢 | 快速回應，正確規劃 |
| claude-sonnet-4-6 | Anthropic | ✅ 5K | 安全事件分析 | thinking 可見，品質良好 |
| claude-opus-4-6 | Anthropic | ✅ 10K | 系統崩潰排查 | 深度推理，最佳品質 |
| auto-select | Mixed | 視策略 | 不同 risk_level | 正確匹配策略 |

## 依賴

- Sprint 151 全部完成（AnthropicChatClient, Registry, Selector, build() 修復）
- ANTHROPIC_API_KEY 環境變數（Step 2-4 測試需要）
- AZURE_OPENAI_ENDPOINT + API_KEY（Step 1 測試需要）

---

**Sprint 152 前置**: Sprint 151 完成
**Story Points**: 7 pts
**核心交付**: Builder 整合 + API 端點 + 5 步 E2E 驗證
