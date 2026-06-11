# Sprint 82 技術決策記錄

## Sprint 資訊

| 項目 | 內容 |
|------|------|
| **Sprint** | 82 |
| **Phase** | 23 |
| **主題** | 主動巡檢與智能關聯 |

---

## 決策記錄

### D82-1: 主動巡檢架構設計

**日期**: 2026-01-12

**背景**:
需要實現 Claude 驅動的主動巡檢系統，定時掃描系統狀態並發現潛在問題。

**決策**:
採用分層架構設計：
1. **PatrolScheduler**: 調度器，負責定時任務管理
2. **PatrolAgent**: 巡檢代理，負責執行巡檢並分析結果
3. **PatrolCheck**: 檢查項目基類，定義檢查接口

**巡檢類型**:
| 類型 | 說明 | 頻率建議 |
|------|------|----------|
| service_health | 服務健康檢查 | 每 5 分鐘 |
| api_response | API 響應檢查 | 每 10 分鐘 |
| resource_usage | 資源使用檢查 | 每 15 分鐘 |
| log_analysis | 日誌分析檢查 | 每小時 |
| security_scan | 安全掃描檢查 | 每日 |

**理由**:
- 關注點分離：調度、執行、檢查各司其職
- 可擴展性：易於添加新的檢查項目
- 可配置性：支援不同頻率和檢查組合

---

### D82-2: 巡檢報告結構設計

**日期**: 2026-01-12

**背景**:
需要標準化巡檢報告格式，便於分析和歸檔。

**決策**:
設計 PatrolReport 標準格式：
```python
@dataclass
class PatrolReport:
    report_id: str
    patrol_id: str
    started_at: datetime
    completed_at: datetime
    checks: List[CheckResult]
    overall_status: PatrolStatus  # HEALTHY/WARNING/CRITICAL
    risk_score: float  # 0-100
    summary: str  # Claude 生成的摘要
    recommendations: List[str]  # Claude 生成的建議
```

**風險評分算法**:
- HEALTHY 檢查: 0 分
- WARNING 檢查: 20 分
- CRITICAL 檢查: 50 分
- 最終評分 = min(100, sum(所有檢查得分))

---

### D82-3: 智能關聯分析策略

**日期**: 2026-01-12

**背景**:
需要實現多事件關聯推理，支援時間、系統依賴和語義相似關聯。

**決策**:
三種關聯分析策略：

1. **時間關聯** (TimeCorrelation)
   - 在指定時間窗口內查找相關事件
   - 預設窗口: 1 小時
   - 權重: 0.4

2. **系統依賴關聯** (DependencyCorrelation)
   - 基於 CMDB 系統依賴關係
   - 查找上下游系統事件
   - 權重: 0.35

3. **語義相似關聯** (SemanticCorrelation)
   - 使用 mem0 向量搜索
   - 基於事件描述的語義相似度
   - 權重: 0.25

**關聯評分**:
```
total_score = (time_score * 0.4) + (dependency_score * 0.35) + (semantic_score * 0.25)
```

---

### D82-4: 根因分析流程設計

**日期**: 2026-01-12

**背景**:
需要 Claude 驅動的根因分析，基於關聯事件推理出問題根本原因。

**決策**:
根因分析流程：

1. **數據收集**
   - 收集目標事件詳情
   - 獲取所有關聯事件
   - 查詢歷史相似模式

2. **圖譜構建**
   - 建立事件關聯圖譜
   - 計算節點重要性
   - 識別關鍵路徑

3. **Claude 分析**
   - 輸入: 事件、關聯圖譜、歷史模式
   - 輸出: 根因假設、置信度、證據鏈

4. **結果驗證**
   - 檢查根因假設與證據一致性
   - 計算整體置信度
   - 生成修復建議

**根因分析輸出**:
```python
@dataclass
class RootCauseAnalysis:
    analysis_id: str
    event_id: str
    root_cause: str
    confidence: float  # 0-1
    evidence_chain: List[Evidence]
    contributing_factors: List[str]
    recommendations: List[Recommendation]
    similar_historical_cases: List[HistoricalCase]
```

---

### D82-5: 關聯圖譜視覺化設計

**日期**: 2026-01-12

**背景**:
需要將關聯關係以圖譜形式呈現，便於人工分析和理解。

**決策**:
圖譜數據結構：
```python
@dataclass
class CorrelationGraph:
    nodes: List[GraphNode]
    edges: List[GraphEdge]

@dataclass
class GraphNode:
    id: str
    type: str  # event/service/component
    label: str
    severity: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class GraphEdge:
    source: str
    target: str
    relation_type: str  # time/dependency/semantic
    weight: float
    label: str
```

**視覺化輸出格式**:
- JSON 格式 (前端 D3.js/ECharts 渲染)
- Mermaid 格式 (Markdown 文檔嵌入)
- DOT 格式 (Graphviz 渲染)

---

## 總結

Sprint 82 將完成兩個核心功能：

1. **主動巡檢系統** (S82-1): 定時掃描、風險評估、報告生成
2. **智能關聯分析** (S82-2): 多維度關聯、圖譜構建、根因推理

所有決策均考慮了可擴展性和與現有系統的整合。

---

**最後更新**: 2026-01-12
**Sprint 狀態**: 進行中
