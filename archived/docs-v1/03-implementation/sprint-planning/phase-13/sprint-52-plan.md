# Sprint 52: Intent Router & Mode Detection

## Sprint 概述

**Sprint 目標**: 實現智能意圖路由器，準確區分 Workflow Mode 與 Chat Mode

**Story Points**: 35 點
**預估工期**: 1 週

## User Stories

### S52-1: Intent Router 核心實現 (13 pts)

**As a** 系統架構師
**I want** 一個智能意圖路由器
**So that** 系統能根據用戶輸入自動選擇最佳執行模式

**Acceptance Criteria**:
- [ ] IntentRouter 類別實現，支援意圖分析
- [ ] ExecutionMode 枚舉：WORKFLOW_MODE, CHAT_MODE, HYBRID_MODE
- [ ] IntentAnalysis 資料模型，包含 mode, confidence, reasoning
- [ ] 基於規則的初始分類器實現
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/hybrid/
├── intent/
│   ├── __init__.py
│   ├── router.py           # IntentRouter 主類別
│   ├── models.py           # ExecutionMode, IntentAnalysis
│   ├── classifiers/
│   │   ├── __init__.py
│   │   ├── base.py         # BaseClassifier 抽象類
│   │   ├── rule_based.py   # 規則式分類器
│   │   └── llm_based.py    # LLM 輔助分類器 (S52-2)
│   └── tests/
│       └── test_router.py
```

**Implementation Details**:
```python
# router.py
class IntentRouter:
    def __init__(
        self,
        classifiers: List[BaseClassifier],
        default_mode: ExecutionMode = ExecutionMode.CHAT_MODE,
        confidence_threshold: float = 0.7,
    ):
        self.classifiers = classifiers
        self.default_mode = default_mode
        self.threshold = confidence_threshold

    async def analyze_intent(
        self,
        user_input: str,
        session_context: Optional[SessionContext] = None,
        history: Optional[List[Message]] = None,
    ) -> IntentAnalysis:
        """
        分析用戶意圖

        決策邏輯:
        1. 檢查是否包含明確的 workflow 關鍵字
        2. 分析任務複雜度 (步驟數、依賴關係)
        3. 檢查是否需要多代理協作
        4. 評估是否需要持久化/checkpoint
        """
        ...
```

---

### S52-2: Mode Detection Algorithm (10 pts)

**As a** 開發者
**I want** 精確的模式檢測算法
**So that** Intent Router 能做出準確的分類決策

**Acceptance Criteria**:
- [ ] 複雜度分析器 (ComplexityAnalyzer) 實現
- [ ] 多代理需求檢測器 (MultiAgentDetector) 實現
- [ ] LLM 輔助分類器整合 (可選，作為 fallback)
- [ ] 決策日誌記錄，支援後續分析優化
- [ ] 準確率測試套件，目標 > 85%

**Technical Tasks**:
```python
# classifiers/rule_based.py
class RuleBasedClassifier(BaseClassifier):
    """
    基於規則的分類器

    規則範例:
    - 包含 "workflow", "流程", "步驟" → WORKFLOW_MODE
    - 包含 "聊天", "問答", "解釋" → CHAT_MODE
    - 多個實體 + 依賴關係 → WORKFLOW_MODE
    """

    WORKFLOW_KEYWORDS = [
        "workflow", "流程", "步驟", "pipeline",
        "多個 agent", "協作", "handoff", "群組聊天",
    ]

    CHAT_KEYWORDS = [
        "解釋", "說明", "為什麼", "怎麼",
        "幫我", "分析", "建議",
    ]

# complexity_analyzer.py
class ComplexityAnalyzer:
    """
    任務複雜度分析器

    評估維度:
    - 步驟數量估計
    - 資源依賴數量
    - 預期執行時間
    - 是否需要狀態持久化
    """

    def analyze(self, input_text: str, context: Dict) -> ComplexityScore:
        ...
```

---

### S52-3: API 整合與路由端點 (7 pts)

**As a** API 使用者
**I want** 意圖分析 API 端點
**So that** 前端可以預覽系統將使用的執行模式

**Acceptance Criteria**:
- [ ] `POST /api/v1/hybrid/analyze-intent` 端點
- [ ] `GET /api/v1/hybrid/modes` 列出支援的執行模式
- [ ] 整合至現有 HybridOrchestrator
- [ ] OpenAPI 文檔更新
- [ ] 端對端測試

**API Specification**:
```yaml
/api/v1/hybrid/analyze-intent:
  post:
    summary: 分析用戶意圖並推薦執行模式
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required:
              - input
            properties:
              input:
                type: string
                description: 用戶輸入文字
              session_id:
                type: string
                description: 可選的 session ID，用於上下文參考
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                mode:
                  type: string
                  enum: [workflow, chat, hybrid]
                confidence:
                  type: number
                  minimum: 0
                  maximum: 1
                reasoning:
                  type: string
                suggested_framework:
                  type: string
                  enum: [maf, claude, hybrid]
```

---

### S52-4: 整合測試與文檔 (5 pts)

**As a** QA 工程師
**I want** 完整的測試覆蓋和文檔
**So that** 功能穩定且易於維護

**Acceptance Criteria**:
- [ ] 整合測試涵蓋所有執行模式
- [ ] 邊界情況測試 (模糊輸入、空輸入等)
- [ ] 效能基準測試 (分類延遲 < 50ms)
- [ ] API 使用文檔
- [ ] 架構決策文檔 (ADR)

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| HybridOrchestrator | Sprint 50-51 | ✅ 已完成 |
| FrameworkSelector | Sprint 50 | ✅ 已完成 |
| SessionService | Phase 11 | ✅ 已完成 |

## Risks

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 分類準確率不足 | 使用錯誤模式 | 設置 confidence 閾值，低於時詢問用戶 |
| LLM 分類延遲 | API 響應慢 | 規則優先，LLM 作為 fallback |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] Code Review 完成
- [ ] API 文檔更新
- [ ] 部署到測試環境驗證
