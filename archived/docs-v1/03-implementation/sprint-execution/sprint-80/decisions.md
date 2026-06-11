# Sprint 80 Decisions: 學習系統與智能回退

> **Phase 22**: Claude 自主能力與學習系統
> **日期**: 2026-01-12

---

## 架構決策

### ADR-80-1: Few-shot 學習系統設計

**決策**: 基於 mem0 記憶系統實現 Few-shot 學習

**背景**:
- 需要從歷史成功案例學習
- 需要動態增強 Claude 的決策能力
- 需要與 Sprint 79 的 mem0 整合

**架構**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Few-shot 學習系統                         │
├─────────────────────────────────────────────────────────────┤
│  1. CaseExtractor                                           │
│     - 從 mem0 提取歷史成功案例                               │
│     - 過濾低品質案例                                         │
├─────────────────────────────────────────────────────────────┤
│  2. SimilarityCalculator                                    │
│     - 計算案例與當前事件的相似度                              │
│     - 支援語義相似度和餘弦相似度                              │
├─────────────────────────────────────────────────────────────┤
│  3. FewShotLearner                                          │
│     - 選擇最相關的 top-k 案例                                │
│     - 動態增強 prompt                                        │
│     - 追蹤學習效果                                           │
└─────────────────────────────────────────────────────────────┘
```

---

### ADR-80-2: 決策審計追蹤設計

**決策**: 實現完整的決策審計系統，記錄所有 AI 決策

**數據模型**:
```python
class DecisionAudit:
    decision_id: str
    timestamp: datetime
    event_context: Dict[str, Any]
    thinking_process: str        # Extended Thinking 輸出
    selected_action: str
    alternatives_considered: List[str]
    confidence_score: float
    outcome: Optional[str]
    quality_score: Optional[float]
```

**存儲策略**:
- 實時審計記錄存入 PostgreSQL
- 高頻查詢數據緩存到 Redis
- 歷史數據定期歸檔

---

### ADR-80-3: 智能回退策略

**決策**: 採用指數退避 + 備選方案生成

**重試策略**:
| 嘗試次數 | 等待時間 | 行為 |
|----------|----------|------|
| 1 | 1s | 直接重試 |
| 2 | 2s | 重試 + 調整參數 |
| 3 | 4s | 生成備選方案 |
| 4+ | 8s | 人工介入 |

**失敗分類**:
| 類型 | 可恢復 | 處理方式 |
|------|--------|----------|
| TRANSIENT | ✅ | 自動重試 |
| RESOURCE | ✅ | 等待 + 重試 |
| VALIDATION | ✅ | 調整輸入重試 |
| PERMISSION | ❌ | 人工介入 |
| FATAL | ❌ | 立即中止 |

---

### ADR-80-4: Session 狀態持久化

**決策**: Session 狀態雙重持久化 (PostgreSQL + mem0)

**策略**:
```
┌─────────────────────────────────────────────────────────────┐
│                Session 狀態管理                              │
├─────────────────────────────────────────────────────────────┤
│  1. 即時狀態 → PostgreSQL                                   │
│     - 完整對話歷史                                          │
│     - 工具調用記錄                                          │
│     - TTL: 7 天                                             │
├─────────────────────────────────────────────────────────────┤
│  2. 壓縮摘要 → mem0                                         │
│     - 關鍵上下文摘要                                         │
│     - 用戶偏好快照                                          │
│     - 永久存儲                                              │
└─────────────────────────────────────────────────────────────┘
```

**壓縮策略**:
- 保留最近 10 條完整消息
- 壓縮早期消息為摘要
- 提取關鍵實體和決策

---

## 技術決策

### TDR-80-1: 案例相似度算法

**決策**: 混合相似度計算

```python
def calculate_similarity(case: Case, event: Event) -> float:
    # 語義相似度 (70% 權重)
    semantic = cosine_similarity(
        embed(case.description),
        embed(event.description)
    )

    # 結構相似度 (30% 權重)
    structural = jaccard_similarity(
        case.affected_systems,
        event.affected_systems
    )

    return 0.7 * semantic + 0.3 * structural
```

---

### TDR-80-2: 審計日誌 API 設計

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/audit/decisions` | 列出決策記錄 |
| GET | `/api/v1/audit/decisions/{id}` | 獲取決策詳情 |
| GET | `/api/v1/audit/decisions/{id}/report` | 獲取可解釋性報告 |
| POST | `/api/v1/audit/decisions/{id}/outcome` | 更新決策結果 |

---

## 實現總結

### 新增模組

| 模組 | 行數 | 核心類 |
|------|------|--------|
| `integrations/learning/` | ~980 行 | FewShotLearner, CaseExtractor, SimilarityCalculator |
| `integrations/audit/` | ~1090 行 | DecisionTracker, AuditReportGenerator |
| `autonomous/retry.py` | ~300 行 | RetryPolicy |
| `autonomous/fallback.py` | ~420 行 | SmartFallback |
| `claude_sdk/session_state.py` | ~420 行 | SessionStateManager |

### API 端點 (新增)

- `GET /api/v1/decisions` - 查詢決策記錄
- `GET /api/v1/decisions/{id}` - 獲取決策詳情
- `GET /api/v1/decisions/{id}/report` - 獲取可解釋性報告
- `POST /api/v1/decisions/{id}/feedback` - 添加反饋
- `GET /api/v1/decisions/statistics` - 決策統計
- `GET /api/v1/decisions/summary` - 摘要報告

### 驗證結果

所有模組導入驗證通過 ✅

---

**更新日期**: 2026-01-12
**Sprint 狀態**: ✅ 完成
