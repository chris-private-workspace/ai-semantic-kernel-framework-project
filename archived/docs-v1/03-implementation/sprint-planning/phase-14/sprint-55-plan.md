# Sprint 55: Risk Assessment Engine

## Sprint 概述

**Sprint 目標**: 實現基於風險等級的智能審批決策引擎

**Story Points**: 30 點
**預估工期**: 1 週

## User Stories

### S55-1: Risk Assessment Engine 核心 (12 pts)

**As a** 系統管理員
**I want** 基於風險等級的操作評估
**So that** 敏感操作能得到適當的審批流程

**Acceptance Criteria**:
- [ ] RiskAssessmentEngine 類別實現
- [ ] RiskLevel 枚舉 (LOW, MEDIUM, HIGH, CRITICAL)
- [ ] RiskAssessment 資料模型
- [ ] 多維度風險評分算法
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/hybrid/
├── risk/
│   ├── __init__.py
│   ├── engine.py           # RiskAssessmentEngine 主類別
│   ├── models.py           # RiskLevel, RiskAssessment, RiskFactor
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── operation.py    # OperationAnalyzer
│   │   ├── context.py      # ContextEvaluator
│   │   └── pattern.py      # PatternDetector
│   ├── scoring/
│   │   ├── __init__.py
│   │   └── scorer.py       # RiskScorer
│   └── tests/
```

**Implementation Details**:
```python
# engine.py
class RiskAssessmentEngine:
    def __init__(
        self,
        operation_analyzer: OperationAnalyzer,
        context_evaluator: ContextEvaluator,
        pattern_detector: PatternDetector,
        scorer: RiskScorer,
        config: RiskConfig,
    ):
        ...

    async def assess(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: HybridContext,
        history: Optional[List[ToolCall]] = None,
    ) -> RiskAssessment:
        # 1. 操作分析
        op_risk = await self.operation_analyzer.analyze(tool_name, arguments)

        # 2. 上下文評估
        ctx_risk = await self.context_evaluator.evaluate(context)

        # 3. 模式檢測
        pattern_risk = await self.pattern_detector.detect(
            tool_name, arguments, history
        )

        # 4. 綜合評分
        assessment = self.scorer.calculate(op_risk, ctx_risk, pattern_risk)

        return assessment
```

---

### S55-2: Operation Analyzer (8 pts)

**As a** 安全工程師
**I want** 詳細的操作風險分析
**So that** 每個 Tool 操作都能被準確評估

**Acceptance Criteria**:
- [ ] Tool 類型風險矩陣 (Read=LOW, Write=MEDIUM, Delete=HIGH, Bash=VARIABLE)
- [ ] 參數敏感度分析 (路徑、命令、數據量)
- [ ] 目標範圍評估 (單文件、目錄、系統)
- [ ] 危險模式檢測 (rm -rf, sudo, 等)

**Technical Tasks**:
```python
# analyzers/operation.py
class OperationAnalyzer:
    # Tool 基礎風險等級
    TOOL_BASE_RISK = {
        "Read": 0.1,
        "Glob": 0.1,
        "Grep": 0.1,
        "Write": 0.4,
        "Edit": 0.4,
        "MultiEdit": 0.5,
        "Bash": 0.6,  # 動態調整
        "WebFetch": 0.2,
        "WebSearch": 0.1,
    }

    # 敏感路徑模式
    SENSITIVE_PATHS = [
        r"/etc/.*",
        r"/root/.*",
        r".*\.env.*",
        r".*password.*",
        r".*secret.*",
        r".*\.pem$",
        r".*\.key$",
    ]

    # 危險命令模式
    DANGEROUS_COMMANDS = [
        r"rm\s+-rf",
        r"sudo\s+",
        r"chmod\s+777",
        r"curl.*\|\s*bash",
        r"wget.*\|\s*sh",
    ]

    async def analyze(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> OperationRisk:
        base_risk = self.TOOL_BASE_RISK.get(tool_name, 0.5)

        # 參數分析
        param_risk = self._analyze_parameters(tool_name, arguments)

        # 目標範圍
        scope_risk = self._analyze_scope(tool_name, arguments)

        # 危險模式
        danger_risk = self._detect_dangerous_patterns(tool_name, arguments)

        return OperationRisk(
            base_risk=base_risk,
            param_risk=param_risk,
            scope_risk=scope_risk,
            danger_risk=danger_risk,
            factors=self._collect_factors(),
        )
```

---

### S55-3: Context Evaluator & Pattern Detector (5 pts)

**As a** 安全工程師
**I want** 上下文和歷史模式分析
**So that** 風險評估考慮更多維度

**Acceptance Criteria**:
- [ ] ContextEvaluator 實現 (用戶信任度、環境、會話狀態)
- [ ] PatternDetector 實現 (歷史行為、異常檢測)
- [ ] 可配置的評估權重

**Technical Tasks**:
```python
# analyzers/context.py
class ContextEvaluator:
    async def evaluate(self, context: HybridContext) -> ContextRisk:
        # 用戶信任度
        user_trust = self._evaluate_user_trust(context.user_info)

        # 環境因素 (production vs development)
        env_risk = self._evaluate_environment(context.environment)

        # 會話狀態 (是否有異常行為)
        session_risk = self._evaluate_session_state(context.session_state)

        return ContextRisk(
            user_trust=user_trust,
            env_risk=env_risk,
            session_risk=session_risk,
        )

# analyzers/pattern.py
class PatternDetector:
    async def detect(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        history: List[ToolCall],
    ) -> PatternRisk:
        # 頻率異常
        frequency_anomaly = self._detect_frequency_anomaly(tool_name, history)

        # 行為偏差
        behavior_deviation = self._detect_behavior_deviation(
            tool_name, arguments, history
        )

        # 升級模式 (逐漸增加敏感操作)
        escalation = self._detect_escalation_pattern(history)

        return PatternRisk(
            frequency_anomaly=frequency_anomaly,
            behavior_deviation=behavior_deviation,
            escalation_detected=escalation,
        )
```

---

### S55-4: API 與 ApprovalHook 整合 (5 pts)

**As a** 開發者
**I want** Risk Engine 整合到審批流程
**So that** 審批決策基於風險評估

**Acceptance Criteria**:
- [ ] `GET /api/v1/hybrid/risk/assess` 端點
- [ ] ApprovalHook 整合 Risk Assessment
- [ ] 風險閾值可配置
- [ ] 審計日誌記錄

**API Specification**:
```yaml
/api/v1/hybrid/risk/assess:
  post:
    summary: 評估操作風險
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required:
              - tool_name
              - arguments
            properties:
              tool_name:
                type: string
              arguments:
                type: object
              session_id:
                type: string
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                score:
                  type: number
                  minimum: 0
                  maximum: 1
                level:
                  type: string
                  enum: [low, medium, high, critical]
                recommendation:
                  type: string
                factors:
                  type: array
```

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| Unified Tool Executor | Sprint 54 | 📋 待完成 |
| ApprovalHook | Phase 12 | ✅ 已完成 |
| HookManager | Phase 12 | ✅ 已完成 |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 風險評估準確率 > 90% (測試案例)
- [ ] API 文檔更新
- [ ] Code Review 完成
