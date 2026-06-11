# Sprint 82: 主動巡檢與智能關聯

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 82 |
| **Phase** | 23 - 多 Agent 協調與主動巡檢 |
| **Duration** | 5-7 days |
| **Story Points** | 16 pts |
| **Status** | 計劃中 |
| **Priority** | 🟡 P1 中優先 |

---

## Sprint Goal

實現主動巡檢模式和智能關聯分析，讓系統能主動發現問題並進行根因分析。

---

## Prerequisites

- Sprint 81 完成（多 Agent 協調）✅
- mem0 長期記憶系統（Phase 22）✅

---

## User Stories

### S82-1: 主動巡檢模式 (8 pts)

**Description**: 實現 Claude 驅動的主動巡檢，定時掃描系統狀態並發現潛在問題。

**Acceptance Criteria**:
- [ ] 支援定時巡檢（每小時/每日/每週）
- [ ] Claude 主動分析系統狀態
- [ ] 自動風險評估
- [ ] 生成巡檢報告
- [ ] 支援手動觸發

**Files to Create**:
- `backend/src/integrations/patrol/__init__.py`
- `backend/src/integrations/patrol/scheduler.py` (~150 行)
- `backend/src/integrations/patrol/agent.py` (~200 行)
- `backend/src/integrations/patrol/checks/` (目錄)
  - `service_health.py`
  - `api_response.py`
  - `resource_usage.py`
  - `log_analysis.py`
  - `security_scan.py`
- `backend/src/api/v1/patrol/routes.py` (~100 行)

**Technical Design**:
```python
class PatrolScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def schedule_patrol(
        self,
        patrol_config: PatrolConfig
    ):
        """配置定時巡檢"""
        job = self.scheduler.add_job(
            self.execute_patrol,
            trigger=CronTrigger(**patrol_config.cron_expression),
            args=[patrol_config]
        )
        return job.id

class PatrolAgent:
    async def execute_patrol(
        self,
        checks: List[PatrolCheck]
    ) -> PatrolReport:
        """執行巡檢並生成報告"""
        results = []
        for check in checks:
            result = await check.execute()
            results.append(result)

        # Claude 分析結果並生成報告
        analysis = await self.claude.analyze_patrol_results(results)
        return PatrolReport(results=results, analysis=analysis)
```

**API Endpoints**:
```
POST   /api/v1/patrol/trigger          # 手動觸發巡檢
GET    /api/v1/patrol/reports          # 獲取巡檢報告
GET    /api/v1/patrol/schedule         # 獲取巡檢計劃
PUT    /api/v1/patrol/schedule         # 更新巡檢計劃
```

---

### S82-2: 智能關聯與根因分析 (8 pts)

**Description**: 實現多事件關聯推理和 Claude 驅動的根因分析。

**Acceptance Criteria**:
- [ ] 事件時間關聯
- [ ] 系統依賴關聯（CMDB）
- [ ] 語義相似關聯
- [ ] 關聯圖譜視覺化
- [ ] Claude 根因分析

**Files to Create**:
- `backend/src/integrations/correlation/__init__.py`
- `backend/src/integrations/correlation/analyzer.py` (~200 行)
- `backend/src/integrations/correlation/graph.py` (~150 行)
- `backend/src/integrations/rootcause/__init__.py`
- `backend/src/integrations/rootcause/analyzer.py` (~200 行)
- `backend/src/api/v1/correlation/routes.py` (~100 行)

**Technical Design**:
```python
class CorrelationAnalyzer:
    async def find_correlations(
        self,
        event: Event,
        time_window: timedelta = timedelta(hours=1)
    ) -> List[Correlation]:
        """尋找事件關聯"""
        correlations = []

        # 時間關聯
        time_related = await self.time_correlation(event, time_window)
        correlations.extend(time_related)

        # 系統依賴關聯
        dependency_related = await self.dependency_correlation(event)
        correlations.extend(dependency_related)

        # 語義相似關聯 (使用 mem0)
        semantic_related = await self.semantic_correlation(event)
        correlations.extend(semantic_related)

        return correlations

class RootCauseAnalyzer:
    async def analyze_root_cause(
        self,
        event: Event,
        correlations: List[Correlation]
    ) -> RootCauseAnalysis:
        """Claude 驅動的根因分析"""
        # 構建關聯圖譜
        graph = await self.build_correlation_graph(event, correlations)

        # Claude 分析根因
        analysis = await self.claude.analyze_root_cause(
            event=event,
            graph=graph,
            historical_patterns=await self.get_similar_patterns(event)
        )

        return analysis
```

**API Endpoints**:
```
POST   /api/v1/correlation/analyze     # 分析事件關聯
GET    /api/v1/correlation/{event_id}  # 獲取事件關聯
POST   /api/v1/rootcause/analyze       # 根因分析
```

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] 巡檢計劃按時執行
- [ ] 異常能被正確識別
- [ ] 根因分析準確率 > 70%
- [ ] 單元測試覆蓋率 > 80%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| 主動巡檢問題發現率 | > 80% |
| 根因分析準確率 | > 70% |
| 巡檢報告生成時間 | < 5 分鐘 |

---

**Created**: 2026-01-12
**Story Points**: 16 pts
