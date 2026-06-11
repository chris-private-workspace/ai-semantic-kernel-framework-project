# Sprint 80: 學習系統與智能回退

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 80 |
| **Phase** | 22 - Claude 自主能力與學習系統 |
| **Duration** | 5-7 days |
| **Story Points** | 27 pts |
| **Status** | 計劃中 |
| **Priority** | 🔴 P0 高優先 |

---

## Sprint Goal

實現 Few-shot 學習系統、自主決策審計追蹤、Trial-and-Error 智能回退，以及 Claude Session 狀態增強。

---

## Prerequisites

- Sprint 79 完成（Claude 自主規劃引擎 + mem0）✅
- mem0 長期記憶系統運作正常 ✅

---

## User Stories

### S80-1: Few-shot 學習系統 (8 pts)

**Description**: 實現從歷史成功案例學習的 Few-shot 系統，動態增強 Claude 的決策能力。

**Acceptance Criteria**:
- [ ] 歷史成功案例提取機制
- [ ] 動態 prompt 增強（注入相關案例）
- [ ] 案例相似度匹配算法
- [ ] 學習效果追蹤和評估
- [ ] 案例庫自動維護

**Files to Create**:
- `backend/src/integrations/learning/__init__.py`
- `backend/src/integrations/learning/few_shot.py` (~200 行)
- `backend/src/integrations/learning/case_extractor.py` (~150 行)
- `backend/src/integrations/learning/similarity.py` (~100 行)

**Technical Design**:
```python
class FewShotLearner:
    async def get_similar_cases(self, event: Event, top_k: int = 3) -> List[Case]:
        """從歷史記憶中提取相似案例"""
        memories = await self.mem0.search(event.description, top_k=top_k)
        return [Case.from_memory(m) for m in memories]

    async def enhance_prompt(self, base_prompt: str, cases: List[Case]) -> str:
        """用歷史案例增強 prompt"""
        case_examples = "\n".join([c.to_example() for c in cases])
        return f"{base_prompt}\n\n## 參考歷史案例:\n{case_examples}"
```

---

### S80-2: 自主決策審計追蹤 (8 pts)

**Description**: 實現完整的決策審計追蹤系統，確保 AI 決策可解釋和可追溯。

**Acceptance Criteria**:
- [ ] 決策路徑完整記錄
- [ ] 決策依據和上下文保存
- [ ] 可解釋性報告生成
- [ ] 決策品質評分機制
- [ ] 審計日誌查詢 API

**Files to Create**:
- `backend/src/integrations/audit/__init__.py`
- `backend/src/integrations/audit/decision_tracker.py` (~200 行)
- `backend/src/integrations/audit/report_generator.py` (~150 行)
- `backend/src/api/v1/audit/routes.py` (~100 行)

**API Endpoints**:
```
GET    /api/v1/audit/decisions            # 獲取決策記錄
GET    /api/v1/audit/decisions/{id}       # 獲取決策詳情
GET    /api/v1/audit/decisions/{id}/report # 獲取可解釋性報告
```

**Data Model**:
```python
class DecisionAudit(BaseModel):
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

---

### S80-3: Trial-and-Error 智能回退 (6 pts)

**Description**: 實現智能的錯誤處理和回退機制，在執行失敗時自動嘗試備選方案。

**Acceptance Criteria**:
- [ ] 指數退避重試策略
- [ ] 失敗原因分類和分析
- [ ] 自動備選方案生成
- [ ] 回退歷史記錄
- [ ] 學習失敗模式（避免重複錯誤）

**Files to Create**:
- `backend/src/integrations/claude_sdk/autonomous/fallback.py` (~200 行)
- `backend/src/integrations/claude_sdk/autonomous/retry.py` (~100 行)

**Technical Design**:
```python
class SmartFallback:
    async def execute_with_fallback(
        self,
        primary_action: Callable,
        max_retries: int = 3
    ) -> Result:
        for attempt in range(max_retries):
            try:
                return await primary_action()
            except ExecutionError as e:
                failure = self.analyze_failure(e)
                if failure.is_recoverable:
                    alternative = await self.generate_alternative(failure)
                    primary_action = alternative
                    await self.exponential_backoff(attempt)
                else:
                    raise
```

---

### S80-4: Claude Session 狀態增強 (5 pts)

**Description**: 增強 Claude Session 的狀態管理，實現跨會話記憶保持。

**Acceptance Criteria**:
- [ ] Session 狀態持久化到 PostgreSQL
- [ ] 跨會話上下文恢復
- [ ] 上下文壓縮策略（減少 token 使用）
- [ ] Session 過期和清理機制
- [ ] 狀態同步到 mem0

**Files to Modify**:
- `backend/src/integrations/claude_sdk/session.py` (修改 ~100 行)
- `backend/src/domain/sessions/service.py` (修改 ~50 行)

**Technical Design**:
```python
class EnhancedClaudeSession:
    async def save_state(self):
        """保存 Session 狀態到持久化存儲"""
        compressed = self.compress_context()
        await self.checkpoint.save(self.session_id, compressed)
        await self.mem0.add(compressed, user_id=self.user_id)

    async def restore_state(self, session_id: str):
        """從持久化存儲恢復 Session 狀態"""
        state = await self.checkpoint.load(session_id)
        if state:
            self.context = self.decompress_context(state)
```

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] Few-shot 學習能從歷史案例提取範例
- [ ] 決策審計記錄完整且可查詢
- [ ] Trial-and-Error 機制在失敗時自動回退
- [ ] Session 狀態能跨會話保持
- [ ] 單元測試覆蓋率 > 80%
- [ ] API 文檔更新

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Few-shot 案例品質不一 | Medium | Medium | 案例評分和篩選機制 |
| 審計日誌存儲量大 | Medium | High | 定期歸檔和壓縮 |
| 回退邏輯過於複雜 | Medium | Low | 保持簡單的回退策略 |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Few-shot 學習改善決策品質 | > 15% 提升 |
| 審計追蹤完整性 | 100% 決策有記錄 |
| 智能回退成功率 | > 70% |
| Session 恢復成功率 | > 95% |

---

**Created**: 2026-01-12
**Story Points**: 27 pts
