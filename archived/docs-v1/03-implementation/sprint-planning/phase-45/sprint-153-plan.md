# Sprint 153 Plan - Pipeline 基礎 + Steps 1-2

## Phase 45: Orchestration Core

### Sprint 目標
建立 pipeline 模組結構、PipelineContext 資料模型、以及從 PoC 提取的 MemoryStep 和 KnowledgeStep。

---

## User Stories

### US-153-1: PipelineContext 資料模型
**作為** orchestration pipeline，
**我希望** 有一個統一的 context 物件跨步驟攜帶狀態，
**以便** 每個步驟都能讀取前序步驟的結果並寫入自己的輸出。

### US-153-2: MemoryStep（記憶讀取步驟）
**作為** orchestration pipeline，
**我希望** 在 pipeline 第一步讀取用戶記憶（pinned、working、relevant、history），
**以便** 後續步驟（意圖路由、風險評估、LLM 選路）都能參考用戶歷史上下文。

### US-153-3: KnowledgeStep（知識庫搜索步驟）
**作為** orchestration pipeline，
**我希望** 在 pipeline 第二步從 Qdrant 向量搜索企業知識庫，
**以便** LLM 分類器和選路決策有企業特定知識做參考。

### US-153-4: Pipeline 服務骨架
**作為** 開發者，
**我希望** 有一個 OrchestrationPipelineService 骨架，
**以便** 各步驟能被依序執行，且支持暫停/恢復和 SSE 事件發射。

---

## 技術規格

### PipelineContext 結構
```python
@dataclass
class PipelineContext:
    # 身份
    user_id: str
    session_id: str
    request_id: str
    task: str
    # 步驟輸出（隨 pipeline 推進填充）
    memory_text: str = ""
    knowledge_text: str = ""
    routing_decision: Optional[RoutingDecision] = None
    risk_assessment: Optional[RiskAssessment] = None
    completeness_info: Optional[CompletenessInfo] = None
    selected_route: Optional[str] = None
    dispatch_result: Optional[DispatchResult] = None
    # Pipeline 控制
    paused_at: Optional[str] = None  # "hitl" | "dialog"
    completed_steps: List[str] = field(default_factory=list)
    step_latencies: Dict[str, float] = field(default_factory=dict)
```

### MemoryStep 提取來源
- PoC: `agent_team_poc.py` lines 872-913
- 包裝: `UnifiedMemoryManager` + `ContextBudgetManager`
- 輸出: `context.memory_text`

### KnowledgeStep 提取來源
- PoC: `agent_team_poc.py` lines 915-952
- 包裝: Azure OpenAI embedding + Qdrant query
- 輸出: `context.knowledge_text`

### Pipeline 骨架設計
- `OrchestrationPipelineService.run(context) -> PipelineContext`
- 步驟列表: `List[PipelineStep]`，每步有 `name`, `execute(context)` 方法
- 異常信號: `HITLPauseException`, `DialogPauseException`
- SSE 事件佇列: `asyncio.Queue[PipelineEvent]`

---

## 檔案變更

| 檔案 | 動作 | 說明 |
|------|------|------|
| `orchestration/pipeline/__init__.py` | NEW | 模組入口 |
| `orchestration/pipeline/context.py` | NEW | PipelineContext dataclass |
| `orchestration/pipeline/exceptions.py` | NEW | 暫停異常類別 |
| `orchestration/pipeline/service.py` | NEW | OrchestrationPipelineService 骨架 |
| `orchestration/pipeline/steps/__init__.py` | NEW | Steps 模組入口 |
| `orchestration/pipeline/steps/base.py` | NEW | PipelineStep 抽象基類 |
| `orchestration/pipeline/steps/step1_memory.py` | NEW | MemoryStep |
| `orchestration/pipeline/steps/step2_knowledge.py` | NEW | KnowledgeStep |

---

## 驗收標準

- [ ] `from src.integrations.orchestration.pipeline import OrchestrationPipelineService` 成功
- [ ] PipelineContext 能攜帶所有步驟輸出
- [ ] MemoryStep 正確呼叫 UnifiedMemoryManager + ContextBudgetManager
- [ ] KnowledgeStep 正確呼叫 Qdrant 向量搜索
- [ ] Pipeline 骨架能依序執行 Steps 1-2 並填充 context
- [ ] 暫停異常 (HITLPause, DialogPause) 可被 pipeline 捕獲
- [ ] 單元測試通過（mock 後端）

---

**Story Points**: 20
**Sprint Duration**: 2026-04-11
