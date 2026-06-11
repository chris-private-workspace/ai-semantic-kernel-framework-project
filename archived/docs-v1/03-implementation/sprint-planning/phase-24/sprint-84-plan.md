# Sprint 84: 生態整合與審批流程

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 84 |
| **Phase** | 24 - 前端完善與生態整合 |
| **Duration** | 5-7 days |
| **Story Points** | 20 pts |
| **Status** | 計劃中 |
| **Priority** | 🟢 P2 低優先 |

---

## Sprint Goal

實現 n8n 觸發整合、多級審批流程、效能監控和通知系統。

---

## Prerequisites

- Sprint 83 完成（WorkflowViz + Dashboard）✅
- 前端基礎（Phase 16-19）✅

---

## User Stories

### S84-1: n8n 觸發整合 (8 pts)

**Description**: 實現 n8n 工作流與 IPA Platform 的雙向整合。

**Acceptance Criteria**:
- [ ] Webhook 配置管理
- [ ] 簽名驗證
- [ ] 觸發執行
- [ ] 結果回饋到 n8n
- [ ] 工作流模板

**Files to Create**:
- `backend/src/integrations/n8n/__init__.py`
- `backend/src/integrations/n8n/trigger.py` (~150 行)
- `backend/src/integrations/n8n/callback.py` (~100 行)
- `backend/src/api/v1/triggers/routes.py` (~100 行)

**Technical Design**:
```python
class N8nTrigger:
    async def handle_webhook(
        self,
        request: WebhookRequest
    ) -> WebhookResponse:
        """處理 n8n Webhook 請求"""
        # 驗證簽名
        if not self.verify_signature(request):
            raise InvalidSignatureError()

        # 執行工作流
        execution = await self.execute_workflow(
            workflow_id=request.workflow_id,
            payload=request.payload
        )

        # 返回執行結果
        return WebhookResponse(
            execution_id=execution.id,
            status=execution.status
        )

    async def callback_to_n8n(
        self,
        callback_url: str,
        result: ExecutionResult
    ):
        """將結果回饋到 n8n"""
        await self.http_client.post(
            callback_url,
            json=result.to_dict()
        )
```

**API Endpoints**:
```
POST   /api/v1/n8n/webhook              # n8n Webhook 端點
GET    /api/v1/n8n/workflows            # 獲取 n8n 工作流
POST   /api/v1/n8n/trigger              # 觸發 n8n 工作流
```

---

### S84-2: 多級審批流程 (5 pts)

**Description**: 實現分層審批配置和升級路徑管理。

**Acceptance Criteria**:
- [ ] 多級審批配置
- [ ] 升級路徑管理
- [ ] 審批超時處理
- [ ] 審批委託

**Files to Create/Modify**:
- `backend/src/domain/approval/multi_level.py` (~200 行)
- `backend/src/domain/approval/escalation.py` (~100 行)
- `backend/src/api/v1/approval/routes.py` (修改 ~50 行)

**Technical Design**:
```python
class MultiLevelApproval:
    async def submit_for_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalChain:
        """提交多級審批"""
        # 確定審批鏈
        chain = await self.determine_approval_chain(request)

        # 創建審批記錄
        for level in chain.levels:
            await self.create_approval_record(level)

        # 通知第一級審批人
        await self.notify_approvers(chain.levels[0])

        return chain

    async def handle_escalation(
        self,
        approval_id: str
    ):
        """處理審批升級"""
        approval = await self.get_approval(approval_id)

        if approval.is_timeout:
            # 升級到下一級
            next_level = await self.get_next_level(approval)
            await self.escalate(approval, next_level)
```

---

### S84-3: 效能監控 + Claude 使用統計 (5 pts)

**Description**: 增強效能監控，添加 Claude API 使用統計。

**Acceptance Criteria**:
- [ ] Claude token 使用統計
- [ ] API 調用頻率
- [ ] 歷史對比
- [ ] 趨勢預測

**Files to Create**:
- `backend/src/integrations/monitoring/claude_metrics.py` (~150 行)
- `frontend/src/components/monitoring/ClaudeUsage.tsx` (~150 行)

**Technical Design**:
```python
class ClaudeMetrics:
    async def record_usage(
        self,
        session_id: str,
        input_tokens: int,
        output_tokens: int,
        model: str
    ):
        """記錄 Claude 使用情況"""
        await self.metrics_store.record({
            'session_id': session_id,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'model': model,
            'timestamp': datetime.utcnow()
        })

    async def get_usage_summary(
        self,
        start_date: date,
        end_date: date
    ) -> UsageSummary:
        """獲取使用摘要"""
        data = await self.metrics_store.query(start_date, end_date)
        return UsageSummary(
            total_tokens=sum(d['input_tokens'] + d['output_tokens'] for d in data),
            total_requests=len(data),
            daily_breakdown=self.calculate_daily_breakdown(data)
        )
```

---

### S84-4: 短信/郵件通知整合 (2 pts)

**Description**: 整合短信和郵件通知渠道。

**Acceptance Criteria**:
- [ ] 郵件通知
- [ ] 通知模板管理
- [ ] 發送追蹤

**Files to Create**:
- `backend/src/integrations/notifications/__init__.py`
- `backend/src/integrations/notifications/email.py` (~100 行)
- `backend/src/integrations/notifications/templates.py` (~50 行)

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] n8n 整合測試通過
- [ ] 審批流程正常
- [ ] 通知發送成功
- [ ] 單元測試覆蓋率 > 80%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| n8n 觸發成功率 | > 99% |
| 審批處理時間 | < 5 分鐘（系統處理） |
| 通知送達率 | > 99% |

---

**Created**: 2026-01-12
**Story Points**: 20 pts
