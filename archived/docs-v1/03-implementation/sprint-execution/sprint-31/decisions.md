# Sprint 31 Decisions: Planning API 完整遷移

**Sprint 目標**: 解決所有 P0 級別架構問題

---

## 決策記錄

### D31-001: Planning API 遷移策略

**日期**: 2025-12-08
**狀態**: ✅ 已決定
**背景**:
Planning API 目前直接使用 `domain.orchestration.planning` 模組（已棄用），需要遷移至 `PlanningAdapter`。

**選項**:
1. 完全重寫所有端點，使用 PlanningAdapter
2. 漸進式遷移，保留部分 domain 導入作為過渡
3. 創建中間層包裝，逐步替換

**決定**: 選項 3 - 擴展 PlanningAdapter 添加細粒度包裝方法

**理由**:
1. PlanningAdapter 已使用官方 `MagenticBuilder` (符合架構目標)
2. 內部已導入 Phase 2 擴展模組 (TaskDecomposer, DecisionEngine, TrialAndErrorEngine)
3. 只需添加公開的包裝方法暴露細粒度功能
4. routes.py 只需導入 PlanningAdapter，所有 domain 導入集中在適配器層
5. API 響應格式保持不變，確保向後兼容

**實施細節**:
- 在 PlanningAdapter 添加 `@property` 訪問器暴露內部引擎
- 添加 `decompose_task()`, `refine_decomposition()` 等包裝方法
- 添加 DynamicPlanner 整合 (目前缺失)
- routes.py 創建單例 PlanningAdapter 實例並使用包裝方法

---

### D31-002: AgentExecutor 適配器位置

**日期**: 2025-12-08
**狀態**: ✅ 已決定
**背景**:
`domain/agents/service.py` 中的官方 API 導入應該移至適配器層。

**選項**:
1. 創建新的 `builders/agent_executor.py`
2. 擴展現有的 `core/execution.py`
3. 創建 `agents/` 子目錄專門處理 Agent 相關適配器

**決定**: 選項 1 - 創建新的 `builders/agent_executor.py`

**理由**:
1. 與現有 builders 模式一致 (groupchat.py, handoff.py, concurrent.py 等)
2. 集中管理官方 API 導入 (ChatAgent, ChatMessage, Role, AzureOpenAIResponsesClient)
3. 保持 domain 層與 integrations 層的清晰分離
4. service.py 只需導入適配器，符合架構規範

**實施細節**:
- 創建 `AgentExecutorAdapter` 類包裝 ChatAgent 操作
- 提供 `execute()`, `execute_simple()`, `test_connection()` 方法
- 更新 service.py 使用適配器，移除直接官方 API 導入
- 更新 `__init__.py` 導出新適配器

---

## 技術約束

1. **API 兼容性**:
   - 所有 API 響應格式必須保持不變
   - 錯誤代碼必須保持一致

2. **測試要求**:
   - 所有現有測試必須通過
   - 新增適配器必須有對應測試

3. **棄用警告**:
   - 正常使用流程不應觸發 DeprecationWarning
   - 所有棄用模組必須有清晰的遷移指引

---

## 參考資料

- [Sprint 31 Plan](../../sprint-planning/phase-6/sprint-31-plan.md)
- [Phase 1-5 審計報告](../PHASE-1-5-COMPREHENSIVE-ARCHITECTURE-AUDIT.md)
- [Deprecated Modules Guide](../migration/deprecated-modules.md)
