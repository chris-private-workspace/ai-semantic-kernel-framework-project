# Sprint 2: Integrations & Extensions - 詳細規劃

> ℹ️ **開發策略**: 本 Sprint 繼續**本地優先開發**  
> 🐳 **開發環境**: Docker Compose (完全本地)  
> 🔔 **通知方式**: Console/Mock Teams Notifications (Phase 1)  
> 📁 **文件存儲**: 本地文件系統 (Phase 1) → Azure Blob (Phase 2)  
> 💰 **成本**: $0 Azure 費用

**版本**: 1.1 (Local-First)  
**創建日期**: 2025-11-19  
**更新日期**: 2025-11-20  
**Sprint 期間**: 2025-12-23 至 2026-01-03 (2週)  
**團隊規模**: 8人

**⚠️ 注意**: 此 Sprint 跨越假期（12/23-1/3），預期團隊可用性降低 30-40%

---

## 📋 Sprint 目標

實現關鍵的外部集成功能，包括 n8n 觸發器、Teams 通知、監控集成和審計日誌系統。

### 核心目標
1. ✅ 集成 n8n Webhook 觸發器
2. ✅ 實現 Microsoft Teams 通知
3. ✅ 建立完整的審計日誌系統
4. ✅ 集成監控和告警系統
5. ✅ 實現 Admin Dashboard 後端 API

### 成功標準
- n8n 可以通過 Webhook 觸發工作流
- 執行失敗/成功時自動發送 Teams 通知
- 所有用戶操作記錄到審計日誌
- Prometheus 收集自定義業務指標
- Admin Dashboard API 返回實時統計數據

---

## 📊 Story Points 分配

**總計劃點數**: 40  
**假期調整**: 預計完成 28-32 點 (70-80%)

**按優先級分配**:
- P0 (Critical): 29 點 (73%)
- P1 (High): 11 點 (27%)

---

## 🎯 Sprint Backlog

### S2-1: n8n Webhook Integration
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 1  
**依賴**: S1-3 (Execution Service)

#### 描述
實現 n8n Webhook 接收器，支持 HMAC-SHA256 簽名驗證，允許 n8n 工作流觸發 IPA 平台執行。

#### 驗收標準
- [ ] 實現 POST /api/webhooks/n8n endpoint
- [ ] HMAC-SHA256 簽名驗證
- [ ] 支持自定義 payload 解析
- [ ] Webhook 事件記錄到審計日誌
- [ ] 錯誤時返回標準化響應
- [ ] 支持 webhook 測試端點

#### 技術實現細節

```python
# n8n Webhook Handler
import hmac
import hashlib
from fastapi import Request, HTTPException

class N8nWebhookService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """驗證 n8n webhook 簽名"""
        expected_signature = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_webhook(
        self,
        workflow_id: str,
        payload: dict,
        headers: dict
    ) -> dict:
        """處理 n8n webhook"""
        # 提取觸發數據
        trigger_data = {
            "source": "n8n",
            "workflow_id": workflow_id,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 創建執行
        execution_service = ExecutionService(db)
        execution = execution_service.create_execution(
            workflow_id=workflow_id,
            triggered_by="n8n-webhook",
            trigger_data=trigger_data
        )
        
        return {
            "execution_id": execution.id,
            "status": "started",
            "message": "Workflow execution triggered successfully"
        }

# API Endpoints
@router.post("/api/webhooks/n8n/{workflow_id}")
async def n8n_webhook(
    workflow_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    接收 n8n webhook 觸發
    
    Headers:
    - X-N8n-Signature: HMAC-SHA256 簽名
    """
    # 獲取請求體
    body = await request.body()
    payload = await request.json()
    
    # 驗證簽名
    signature = request.headers.get("X-N8n-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    webhook_secret = os.getenv("N8N_WEBHOOK_SECRET")
    service = N8nWebhookService(webhook_secret)
    
    if not service.verify_signature(body, signature):
        # 記錄失敗的驗證嘗試
        logger.warning(f"Invalid webhook signature for workflow {workflow_id}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # 驗證工作流存在
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 處理 webhook
    result = await service.handle_webhook(
        workflow_id=workflow_id,
        payload=payload,
        headers=dict(request.headers)
    )
    
    # 記錄到審計日誌
    audit_log = AuditLog(
        action="webhook_received",
        actor="n8n",
        details={
            "workflow_id": workflow_id,
            "execution_id": result["execution_id"]
        }
    )
    db.add(audit_log)
    db.commit()
    
    return result

# Webhook 測試端點
@router.post("/api/webhooks/n8n/{workflow_id}/test")
async def test_n8n_webhook(
    workflow_id: str,
    test_payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """測試 webhook (無需簽名驗證)"""
    service = N8nWebhookService("")
    result = await service.handle_webhook(
        workflow_id=workflow_id,
        payload=test_payload,
        headers={}
    )
    return {"test_mode": True, **result}
```

```yaml
# n8n Workflow 配置示例
nodes:
  - name: "Trigger IPA Workflow"
    type: "n8n-nodes-base.httpRequest"
    parameters:
      method: "POST"
      url: "https://ipa-platform.example.com/api/webhooks/n8n/{{workflow_id}}"
      authentication: "genericCredentialType"
      genericAuthType: "httpHeaderAuth"
      headers:
        X-N8n-Signature: "{{$hmacSha256($binary.data, $env.N8N_WEBHOOK_SECRET)}}"
      bodyParameters:
        parameters:
          - name: "data"
            value: "={{$json}}"
```

#### 子任務
1. [ ] 實現 N8nWebhookService 類
2. [ ] 實現 HMAC-SHA256 簽名驗證
3. [ ] 創建 webhook 接收 endpoint
4. [ ] 創建 webhook 測試 endpoint
5. [ ] 集成審計日誌記錄
6. [ ] 編寫單元測試 (簽名驗證)
7. [ ] 編寫集成測試 (完整 webhook 流程)
8. [ ] 創建 n8n 集成文檔

---

### S2-2: n8n Workflow Trigger (Outbound)
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 1  
**依賴**: S2-1

#### 描述
實現從 IPA 平台主動觸發 n8n 工作流的功能。

#### 驗收標準
- [ ] 實現 n8n API 客戶端
- [ ] 支持觸發 n8n workflow by ID
- [ ] 傳遞執行上下文到 n8n
- [ ] 處理 n8n API 錯誤和重試
- [ ] 記錄觸發結果

#### 技術實現細節

```python
# n8n Client
class N8nClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def trigger_workflow(
        self,
        workflow_id: str,
        data: dict
    ) -> dict:
        """觸發 n8n 工作流"""
        url = f"{self.base_url}/webhook/{workflow_id}"
        
        try:
            response = await self.client.post(
                url,
                json=data,
                headers={"X-N8N-API-KEY": self.api_key}
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json()
            }
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to trigger n8n workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_workflow_status(self, execution_id: str) -> dict:
        """獲取 n8n 工作流執行狀態"""
        url = f"{self.base_url}/executions/{execution_id}"
        
        response = await self.client.get(
            url,
            headers={"X-N8N-API-KEY": self.api_key}
        )
        response.raise_for_status()
        
        return response.json()

# API Endpoint
@router.post("/api/workflows/{workflow_id}/trigger-n8n")
async def trigger_n8n_workflow(
    workflow_id: str,
    n8n_workflow_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """從 IPA 觸發 n8n 工作流"""
    n8n_client = N8nClient(
        base_url=os.getenv("N8N_BASE_URL"),
        api_key=os.getenv("N8N_API_KEY")
    )
    
    result = await n8n_client.trigger_workflow(
        workflow_id=n8n_workflow_id,
        data=data
    )
    
    # 記錄到審計日誌
    audit_log = AuditLog(
        action="n8n_workflow_triggered",
        actor=current_user.email,
        details={
            "ipa_workflow_id": workflow_id,
            "n8n_workflow_id": n8n_workflow_id,
            "success": result["success"]
        }
    )
    db.add(audit_log)
    db.commit()
    
    return result
```

#### 子任務
1. [ ] 實現 N8nClient 類
2. [ ] 實現 trigger_workflow 方法
3. [ ] 實現 get_workflow_status 方法
4. [ ] 創建觸發 endpoint
5. [ ] 實現錯誤處理和重試
6. [ ] 編寫單元測試
7. [ ] 編寫集成測試 (使用 n8n test instance)

---

### S2-3: Teams Notification Service
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 2  
**依賴**: S1-3 (Execution Service)

#### 描述
實現 Microsoft Teams 通知服務，支持 Adaptive Cards 格式化通知。

#### 驗收標準
- [ ] 實現 Teams Webhook 客戶端
- [ ] 支持 Adaptive Cards 通知
- [ ] 執行成功/失敗自動通知
- [ ] Checkpoint 審批通知
- [ ] 支持通知模板管理
- [ ] 錯誤處理和重試

#### 技術實現細節

```python
# Teams Notification Service
class TeamsNotificationService:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def send_notification(
        self,
        title: str,
        message: str,
        color: str = "0078D4",
        facts: List[dict] = None,
        actions: List[dict] = None
    ) -> bool:
        """發送 Teams 通知 (Adaptive Card)"""
        card = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "Container",
                            "style": "emphasis",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "size": "Large",
                                    "weight": "Bolder",
                                    "text": title,
                                    "wrap": True,
                                    "color": "Accent"
                                }
                            ]
                        },
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True,
                            "spacing": "Medium"
                        }
                    ]
                }
            }]
        }
        
        # 添加 Facts (key-value pairs)
        if facts:
            fact_set = {
                "type": "FactSet",
                "facts": facts
            }
            card["attachments"][0]["content"]["body"].append(fact_set)
        
        # 添加 Actions (buttons)
        if actions:
            card["attachments"][0]["content"]["actions"] = actions
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json=card,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Teams notification: {str(e)}")
            return False
    
    async def send_execution_success(self, execution: Execution):
        """發送執行成功通知"""
        await self.send_notification(
            title="✅ Workflow Execution Successful",
            message=f"Workflow **{execution.workflow.name}** completed successfully",
            color="28A745",
            facts=[
                {"title": "Execution ID", "value": str(execution.id)},
                {"title": "Duration", "value": f"{execution.duration_seconds}s"},
                {"title": "LLM Cost", "value": f"${execution.llm_cost:.4f}"},
                {"title": "Completed At", "value": execution.completed_at.strftime("%Y-%m-%d %H:%M:%S")}
            ],
            actions=[
                {
                    "type": "Action.OpenUrl",
                    "title": "View Details",
                    "url": f"{os.getenv('FRONTEND_URL')}/executions/{execution.id}"
                }
            ]
        )
    
    async def send_execution_failed(self, execution: Execution):
        """發送執行失敗通知"""
        await self.send_notification(
            title="❌ Workflow Execution Failed",
            message=f"Workflow **{execution.workflow.name}** failed with error",
            color="DC3545",
            facts=[
                {"title": "Execution ID", "value": str(execution.id)},
                {"title": "Error", "value": execution.error[:200]},
                {"title": "Failed At", "value": execution.completed_at.strftime("%Y-%m-%d %H:%M:%S")}
            ],
            actions=[
                {
                    "type": "Action.OpenUrl",
                    "title": "View Error Details",
                    "url": f"{os.getenv('FRONTEND_URL')}/executions/{execution.id}"
                },
                {
                    "type": "Action.Http",
                    "title": "Retry Execution",
                    "method": "POST",
                    "url": f"{os.getenv('API_URL')}/api/executions/{execution.id}/retry"
                }
            ]
        )
    
    async def send_checkpoint_approval_request(
        self,
        checkpoint: Checkpoint,
        execution: Execution
    ):
        """發送 Checkpoint 審批請求"""
        await self.send_notification(
            title="⏸️ Workflow Approval Required",
            message=f"Workflow **{execution.workflow.name}** is waiting for approval at step {checkpoint.step}",
            color="FFC107",
            facts=[
                {"title": "Execution ID", "value": str(execution.id)},
                {"title": "Step", "value": str(checkpoint.step)},
                {"title": "Proposed Action", "value": checkpoint.state.get("proposed_action", "N/A")}
            ],
            actions=[
                {
                    "type": "Action.Http",
                    "title": "✅ Approve",
                    "method": "POST",
                    "url": f"{os.getenv('API_URL')}/api/checkpoints/{checkpoint.id}/approve"
                },
                {
                    "type": "Action.Http",
                    "title": "❌ Reject",
                    "method": "POST",
                    "url": f"{os.getenv('API_URL')}/api/checkpoints/{checkpoint.id}/reject"
                }
            ]
        )

# 集成到 Execution Service
class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.teams_service = TeamsNotificationService(
            webhook_url=os.getenv("TEAMS_WEBHOOK_URL")
        )
    
    async def complete_execution(self, execution_id: str, result: dict):
        """完成執行並發送通知"""
        # ... existing code ...
        
        # 發送成功通知
        await self.teams_service.send_execution_success(execution)
    
    async def fail_execution(self, execution_id: str, error: str):
        """執行失敗並發送通知"""
        # ... existing code ...
        
        # 發送失敗通知
        await self.teams_service.send_execution_failed(execution)
```

#### 子任務
1. [ ] 實現 TeamsNotificationService 類
2. [ ] 實現 Adaptive Card 模板
3. [ ] 實現執行成功通知
4. [ ] 實現執行失敗通知
5. [ ] 實現 Checkpoint 審批通知
6. [ ] 集成到 Execution Service
7. [ ] 編寫單元測試
8. [ ] 編寫集成測試 (使用 test webhook)

---

### S2-4: Teams Approval Flow
**Story Points**: 8  
**優先級**: P1 - High  
**負責人**: Backend Engineer 2  
**依賴**: S2-3

#### 描述
實現 Teams 審批工作流，支持通過 Teams 消息按鈕進行 Checkpoint 審批。

#### 驗收標準
- [ ] 實現審批/拒絕 webhook endpoints
- [ ] 支持審批意見輸入
- [ ] 審批後自動更新執行狀態
- [ ] 記錄審批人和時間
- [ ] 審批結果通知

#### 技術實現細節

```python
# Checkpoint Approval Endpoints
@router.post("/api/checkpoints/{checkpoint_id}/approve")
async def approve_checkpoint(
    checkpoint_id: str,
    approval_data: CheckpointApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """審批 Checkpoint"""
    checkpoint = db.query(Checkpoint).filter(
        Checkpoint.id == checkpoint_id
    ).first()
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    if checkpoint.status != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Checkpoint is already {checkpoint.status}"
        )
    
    # 更新 checkpoint 狀態
    checkpoint.status = "approved"
    checkpoint.approved_by = current_user.id
    checkpoint.approved_at = datetime.utcnow()
    checkpoint.feedback = approval_data.feedback
    db.commit()
    
    # 恢復執行
    execution_service = ExecutionService(db)
    await execution_service.resume_execution(checkpoint.execution_id)
    
    # 發送審批結果通知
    teams_service = TeamsNotificationService(os.getenv("TEAMS_WEBHOOK_URL"))
    await teams_service.send_notification(
        title="✅ Checkpoint Approved",
        message=f"Checkpoint at step {checkpoint.step} has been approved by {current_user.name}",
        color="28A745"
    )
    
    return {"message": "Checkpoint approved, execution resumed"}

@router.post("/api/checkpoints/{checkpoint_id}/reject")
async def reject_checkpoint(
    checkpoint_id: str,
    rejection_data: CheckpointRejectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒絕 Checkpoint"""
    checkpoint = db.query(Checkpoint).filter(
        Checkpoint.id == checkpoint_id
    ).first()
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    # 更新 checkpoint 狀態
    checkpoint.status = "rejected"
    checkpoint.approved_by = current_user.id
    checkpoint.approved_at = datetime.utcnow()
    checkpoint.feedback = rejection_data.reason
    db.commit()
    
    # 終止執行
    execution_service = ExecutionService(db)
    await execution_service.fail_execution(
        checkpoint.execution_id,
        f"Checkpoint rejected by {current_user.name}: {rejection_data.reason}"
    )
    
    # 發送拒絕通知
    teams_service = TeamsNotificationService(os.getenv("TEAMS_WEBHOOK_URL"))
    await teams_service.send_notification(
        title="❌ Checkpoint Rejected",
        message=f"Checkpoint at step {checkpoint.step} has been rejected",
        color="DC3545",
        facts=[
            {"title": "Rejected By", "value": current_user.name},
            {"title": "Reason", "value": rejection_data.reason}
        ]
    )
    
    return {"message": "Checkpoint rejected, execution terminated"}
```

#### 子任務
1. [ ] 創建 CheckpointApprovalRequest schema
2. [ ] 實現 approve_checkpoint endpoint
3. [ ] 實現 reject_checkpoint endpoint
4. [ ] 集成執行恢復/終止邏輯
5. [ ] 實現審批結果通知
6. [ ] 編寫單元測試
7. [ ] 編寫集成測試

---

### S2-5: Monitoring Integration Service
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: Backend Engineer 2  
**依賴**: S0-8 (Monitoring Stack)

#### 描述
實現 OpenTelemetry 自動化儀表板，為所有服務添加分佈式追蹤、指標收集和日誌關聯。

#### 驗收標準
- [ ] 所有 API 請求自動記錄 span
- [ ] 自定義業務指標導出到 Prometheus
- [ ] 追蹤上下文在服務間傳播
- [ ] Jaeger UI 可查看完整調用鏈
- [ ] 指標包含：請求量、延遲、錯誤率

#### 技術實現細節

**1. OpenTelemetry SDK 設置**

```python
# app/core/telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from prometheus_client import start_http_server

def setup_telemetry(app):
    # 設置 Tracer Provider (Jaeger)
    tracer_provider = TracerProvider()
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
        agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(tracer_provider)
    
    # 設置 Meter Provider (Prometheus)
    start_http_server(port=8001)  # Prometheus metrics endpoint
    meter_provider = MeterProvider(
        metric_readers=[PrometheusMetricReader()]
    )
    metrics.set_meter_provider(meter_provider)
    
    # 自動儀表化 FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # 自動儀表化 SQLAlchemy
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        enable_commenter=True,
        commenter_options={"db_framework": "sqlalchemy"}
    )
    
    return tracer_provider, meter_provider
```

**2. 自定義業務指標**

```python
# app/services/metrics_service.py
from opentelemetry import metrics

class MetricsService:
    def __init__(self):
        meter = metrics.get_meter(__name__)
        
        # 計數器：工作流執行次數
        self.workflow_executions = meter.create_counter(
            name="workflow_executions_total",
            description="Total number of workflow executions",
            unit="1"
        )
        
        # 直方圖：執行時長
        self.execution_duration = meter.create_histogram(
            name="execution_duration_seconds",
            description="Workflow execution duration",
            unit="s"
        )
        
        # 計數器：LLM API 調用次數
        self.llm_api_calls = meter.create_counter(
            name="llm_api_calls_total",
            description="Total LLM API calls",
            unit="1"
        )
        
        # 計數器：LLM Token 使用量
        self.llm_tokens_used = meter.create_counter(
            name="llm_tokens_used_total",
            description="Total LLM tokens consumed",
            unit="tokens"
        )
    
    def record_execution_start(self, workflow_id: str):
        self.workflow_executions.add(
            1, 
            {"workflow_id": workflow_id, "status": "started"}
        )
    
    def record_execution_complete(
        self, 
        workflow_id: str, 
        duration_seconds: float,
        status: str
    ):
        self.execution_duration.record(
            duration_seconds,
            {"workflow_id": workflow_id, "status": status}
        )
        self.workflow_executions.add(
            1,
            {"workflow_id": workflow_id, "status": status}
        )
    
    def record_llm_call(
        self, 
        model: str, 
        tokens_used: int,
        cost: float
    ):
        self.llm_api_calls.add(1, {"model": model})
        self.llm_tokens_used.add(tokens_used, {"model": model})
```

**3. 手動 Span 創建（複雜業務邏輯）**

```python
# app/services/execution_service.py
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class ExecutionService:
    async def execute_workflow(self, workflow_id: str):
        with tracer.start_as_current_span("execute_workflow") as span:
            span.set_attribute("workflow_id", workflow_id)
            
            # 子 span: 加載工作流
            with tracer.start_as_current_span("load_workflow"):
                workflow = await self.load_workflow(workflow_id)
                span.set_attribute("workflow_version", workflow.version)
            
            # 子 span: 執行步驟
            for step in workflow.steps:
                with tracer.start_as_current_span(f"execute_step_{step.order}") as step_span:
                    step_span.set_attribute("step_type", step.type)
                    try:
                        result = await self.execute_step(step)
                        step_span.set_status(trace.Status(trace.StatusCode.OK))
                    except Exception as e:
                        step_span.set_status(
                            trace.Status(trace.StatusCode.ERROR, str(e))
                        )
                        step_span.record_exception(e)
                        raise
```

#### 子任務

1. [ ] 安裝 OpenTelemetry SDK 和 exporters
2. [ ] 配置 Tracer Provider (Jaeger)
3. [ ] 配置 Meter Provider (Prometheus)
4. [ ] 實現 MetricsService 類
5. [ ] 在關鍵業務邏輯添加 span
6. [ ] 配置 Prometheus 抓取端點
7. [ ] 驗證 Jaeger UI 顯示追蹤

#### 測試計劃

```python
# tests/integration/test_telemetry.py
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

def test_workflow_execution_creates_spans():
    # 設置內存 span exporter
    span_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)
    
    # 執行工作流
    execution_service = ExecutionService(db)
    await execution_service.execute_workflow("test-workflow-123")
    
    # 驗證 spans
    spans = span_exporter.get_finished_spans()
    assert len(spans) > 0
    assert any(s.name == "execute_workflow" for s in spans)
    assert any(s.attributes.get("workflow_id") == "test-workflow-123" for s in spans)
```

---

### S2-6: Alert Manager Integration
**Story Points**: 3  
**優先級**: P1 - High  
**負責人**: DevOps Engineer  
**依賴**: S0-8 (Monitoring Stack), S2-5 (Monitoring Integration)

#### 描述
配置 Prometheus AlertManager，設置關鍵指標的告警規則，並集成通知渠道（Email、Teams）。

#### 驗收標準
- [ ] AlertManager 部署並運行
- [ ] 配置 5+ 告警規則（服務下線、高錯誤率等）
- [ ] 告警通知發送到 Teams 和 Email
- [ ] Grafana 顯示告警歷史
- [ ] 告警規則可通過 ConfigMap 更新

#### 技術實現細節

**1. Prometheus 告警規則**

```yaml
# k8s/monitoring/prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ipa-platform-alerts
  namespace: monitoring
spec:
  groups:
    - name: ipa_platform
      interval: 30s
      rules:
        # 告警 1: API 高錯誤率
        - alert: HighAPIErrorRate
          expr: |
            rate(http_requests_total{status=~"5.."}[5m]) 
            / 
            rate(http_requests_total[5m]) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "High API error rate detected"
            description: "API error rate is {{ $value | humanizePercentage }} for {{ $labels.endpoint }}"
        
        # 告警 2: 服務下線
        - alert: ServiceDown
          expr: up{job="ipa-platform"} == 0
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: "Service {{ $labels.instance }} is down"
            description: "Service has been down for more than 2 minutes"
        
        # 告警 3: 高延遲
        - alert: HighLatency
          expr: |
            histogram_quantile(0.95, 
              rate(http_request_duration_seconds_bucket[5m])
            ) > 5
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High API latency detected"
            description: "P95 latency is {{ $value }}s for {{ $labels.endpoint }}"
        
        # 告警 4: 數據庫連接池耗盡
        - alert: DatabaseConnectionPoolExhausted
          expr: |
            (pg_stat_activity_count / pg_settings_max_connections) > 0.8
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Database connection pool usage is high"
            description: "Connection pool is {{ $value | humanizePercentage }} full"
        
        # 告警 5: 磁盤空間不足
        - alert: DiskSpaceLow
          expr: |
            (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Disk space is running low"
            description: "Only {{ $value | humanizePercentage }} disk space remaining"
```

**2. AlertManager 配置**

```yaml
# k8s/monitoring/alertmanager-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
    
    route:
      group_by: ['alertname', 'severity']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'teams-notifications'
      routes:
        - match:
            severity: critical
          receiver: 'teams-critical'
          continue: true
        - match:
            severity: warning
          receiver: 'teams-warnings'
    
    receivers:
      - name: 'teams-critical'
        webhook_configs:
          - url: 'http://prometheus-msteams:2000/alertmanager'
            send_resolved: true
      
      - name: 'teams-warnings'
        webhook_configs:
          - url: 'http://prometheus-msteams:2000/alertmanager-warnings'
            send_resolved: true
      
      - name: 'teams-notifications'
        webhook_configs:
          - url: 'http://prometheus-msteams:2000/alertmanager'
            send_resolved: true
```

**3. Prometheus-MSTeams 部署**

```yaml
# k8s/monitoring/prometheus-msteams.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus-msteams
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus-msteams
  template:
    metadata:
      labels:
        app: prometheus-msteams
    spec:
      containers:
        - name: prometheus-msteams
          image: bzon/prometheus-msteams:v1.5.1
          ports:
            - containerPort: 2000
          env:
            - name: TEAMS_INCOMING_WEBHOOK_URL
              valueFrom:
                secretKeyRef:
                  name: teams-webhook-secret
                  key: webhook_url
            - name: TEAMS_REQUEST_URI
              value: "alertmanager"
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-msteams
  namespace: monitoring
spec:
  selector:
    app: prometheus-msteams
  ports:
    - port: 2000
      targetPort: 2000
```

#### 子任務

1. [ ] 創建 Prometheus 告警規則
2. [ ] 部署 AlertManager
3. [ ] 配置 AlertManager 路由
4. [ ] 部署 prometheus-msteams
5. [ ] 測試告警觸發和通知
6. [ ] 在 Grafana 添加告警面板

#### 測試計劃

- 手動觸發告警（例如：停止服務）
- 驗證 Teams 收到通知
- 驗證告警解決後收到恢復通知
- 測試不同 severity 級別的路由

---

### S2-7: Audit Log Service
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 1  
**依賴**: S0-4 (Database), S0-9 (Logging Infrastructure)

#### 描述
實現完整的審計日誌系統，記錄所有用戶操作、API 調用、工作流變更等，用於合規性和安全審計。

#### 驗收標準
- [ ] 所有 API 請求記錄到審計日誌
- [ ] 日誌包含：用戶、時間戳、操作、資源、IP、結果
- [ ] 審計日誌不可刪除（只能標記為已歸檔）
- [ ] 提供審計日誌查詢 API
- [ ] 日誌自動輪轉（保留 1 年）

#### 技術實現細節

**1. 審計日誌數據模型**

```python
# app/models/audit_log.py
from sqlalchemy import Column, String, DateTime, JSON, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
import uuid
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用戶信息
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    
    # 操作信息
    action = Column(String(100), nullable=False, index=True)  # CREATE, UPDATE, DELETE, EXECUTE
    resource_type = Column(String(50), nullable=False, index=True)  # workflow, execution, agent
    resource_id = Column(String(255), nullable=True, index=True)
    
    # 請求信息
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    endpoint = Column(String(500), nullable=False)
    request_body = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=False)
    
    # 上下文信息
    ip_address = Column(String(45), nullable=False)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # 變更信息
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # 時間戳
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # 軟刪除（審計日誌不可真正刪除）
    archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_resource_time', 'resource_type', 'resource_id', 'timestamp'),
    )
```

**2. 審計日誌服務**

```python
# app/services/audit_service.py
from app.models.audit_log import AuditLog
from sqlalchemy.orm import Session
from fastapi import Request
import json

class AuditService:
    def __init__(self, db: Session):
        self.db = db
    
    async def log_api_call(
        self,
        request: Request,
        user_id: str,
        user_email: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        request_body: dict = None,
        response_status: int = 200,
        old_values: dict = None,
        new_values: dict = None
    ):
        audit_log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            method=request.method,
            endpoint=str(request.url),
            request_body=request_body,
            response_status=response_status,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_id=request.headers.get("x-request-id"),
            old_values=old_values,
            new_values=new_values
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        return audit_log
    
    def query_logs(
        self,
        user_id: str = None,
        resource_type: str = None,
        resource_id: str = None,
        action: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
        offset: int = 0
    ):
        query = self.db.query(AuditLog).filter(AuditLog.archived == False)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if start_time:
            query = query.filter(AuditLog.timestamp >= start_time)
        if end_time:
            query = query.filter(AuditLog.timestamp <= end_time)
        
        total = query.count()
        logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        return {"total": total, "logs": logs}
```

**3. FastAPI Middleware（自動審計）**

```python
# app/middleware/audit_middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import json
import time

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 跳過健康檢查和靜態文件
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # 記錄請求時間
        start_time = time.time()
        
        # 讀取請求 body（需要緩存）
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            request._body = body  # 緩存供後續使用
        
        # 處理請求
        response = await call_next(request)
        
        # 計算處理時間
        process_time = time.time() - start_time
        
        # 記錄審計日誌（異步，不阻塞響應）
        if hasattr(request.state, "user"):
            user = request.state.user
            audit_service = AuditService(request.state.db)
            
            # 解析 action 和 resource
            action, resource_type = self._parse_endpoint(request.method, request.url.path)
            
            await audit_service.log_api_call(
                request=request,
                user_id=user.id,
                user_email=user.email,
                action=action,
                resource_type=resource_type,
                request_body=json.loads(body) if body else None,
                response_status=response.status_code
            )
        
        return response
    
    def _parse_endpoint(self, method: str, path: str):
        # 根據 method 和 path 推斷 action 和 resource_type
        if "workflows" in path:
            resource_type = "workflow"
            if method == "POST":
                action = "CREATE"
            elif method == "PUT" or method == "PATCH":
                action = "UPDATE"
            elif method == "DELETE":
                action = "DELETE"
            else:
                action = "READ"
        elif "executions" in path:
            resource_type = "execution"
            action = "EXECUTE" if method == "POST" else "READ"
        # ... 其他資源類型
        else:
            resource_type = "unknown"
            action = method
        
        return action, resource_type
```

**4. 審計日誌 API**

```python
# app/api/v1/audit_logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.audit_service import AuditService
from datetime import datetime

router = APIRouter()

@router.get("/api/audit-logs/")
async def list_audit_logs(
    user_id: str = Query(None),
    resource_type: str = Query(None),
    resource_id: str = Query(None),
    action: str = Query(None),
    start_time: datetime = Query(None),
    end_time: datetime = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 只有管理員可以查看所有用戶的日誌
    if not current_user.is_admin and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    audit_service = AuditService(db)
    result = audit_service.query_logs(
        user_id=user_id or current_user.id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )
    
    return result

@router.get("/api/audit-logs/{log_id}")
async def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    audit_service = AuditService(db)
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    # 只有管理員或日誌所有者可以查看
    if not current_user.is_admin and log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return log
```

#### 子任務

1. [ ] 創建 AuditLog 數據模型和遷移
2. [ ] 實現 AuditService
3. [ ] 創建 AuditMiddleware
4. [ ] 實現審計日誌查詢 API
5. [ ] 配置日誌輪轉（PostgreSQL partitioning）
6. [ ] 編寫單元測試
7. [ ] 編寫集成測試

#### 測試計劃

```python
# tests/integration/test_audit_logs.py
def test_api_call_creates_audit_log(client, db, test_user):
    # 創建工作流
    response = client.post(
        "/api/workflows/",
        json={"name": "Test Workflow"},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    
    assert response.status_code == 201
    
    # 驗證審計日誌
    audit_log = db.query(AuditLog).filter(
        AuditLog.user_id == test_user.id,
        AuditLog.action == "CREATE",
        AuditLog.resource_type == "workflow"
    ).first()
    
    assert audit_log is not None
    assert audit_log.method == "POST"
    assert "workflows" in audit_log.endpoint
    assert audit_log.response_status == 201
```

---

### S2-8: Admin Dashboard APIs
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: Backend Engineer 2  
**依賴**: S1-1 (Workflow Service), S1-3 (Execution Service)

#### 描述
創建 Admin Dashboard 所需的後端 REST API，提供統計數據、實時指標、用戶管理等功能。

#### 驗收標準
- [ ] 統計 API 返回工作流/執行數量
- [ ] 實時指標 API 返回當前運行狀態
- [ ] 用戶管理 API 支持 CRUD
- [ ] 系統健康狀態 API
- [ ] 所有 API 有適當的緩存策略

#### 技術實現細節

**1. 統計數據 API**

```python
# app/api/v1/admin/statistics.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db, require_admin
from app.models.workflow import Workflow
from app.models.execution import Execution
from datetime import datetime, timedelta
from app.core.cache import cache

router = APIRouter()

@router.get("/api/admin/statistics/overview")
@cache(expire=60)  # 緩存 1 分鐘
async def get_overview_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    # 工作流統計
    total_workflows = db.query(func.count(Workflow.id)).scalar()
    active_workflows = db.query(func.count(Workflow.id)).filter(
        Workflow.is_active == True
    ).scalar()
    
    # 執行統計
    total_executions = db.query(func.count(Execution.id)).scalar()
    successful_executions = db.query(func.count(Execution.id)).filter(
        Execution.status == "completed"
    ).scalar()
    failed_executions = db.query(func.count(Execution.id)).filter(
        Execution.status == "failed"
    ).scalar()
    
    # 今日執行
    today = datetime.utcnow().date()
    today_executions = db.query(func.count(Execution.id)).filter(
        func.date(Execution.created_at) == today
    ).scalar()
    
    # 成功率
    success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
    
    return {
        "workflows": {
            "total": total_workflows,
            "active": active_workflows
        },
        "executions": {
            "total": total_executions,
            "successful": successful_executions,
            "failed": failed_executions,
            "today": today_executions,
            "success_rate": round(success_rate, 2)
        }
    }

@router.get("/api/admin/statistics/trend")
@cache(expire=300)  # 緩存 5 分鐘
async def get_execution_trend(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    # 過去 N 天的執行趨勢
    start_date = datetime.utcnow() - timedelta(days=days)
    
    trend_data = db.query(
        func.date(Execution.created_at).label("date"),
        func.count(Execution.id).label("total"),
        func.sum(case((Execution.status == "completed", 1), else_=0)).label("successful"),
        func.sum(case((Execution.status == "failed", 1), else_=0)).label("failed")
    ).filter(
        Execution.created_at >= start_date
    ).group_by(
        func.date(Execution.created_at)
    ).order_by(
        func.date(Execution.created_at)
    ).all()
    
    return {
        "period": f"Last {days} days",
        "data": [
            {
                "date": str(row.date),
                "total": row.total,
                "successful": row.successful,
                "failed": row.failed
            }
            for row in trend_data
        ]
    }
```

**2. 實時指標 API**

```python
# app/api/v1/admin/metrics.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.execution import Execution

router = APIRouter()

@router.get("/api/admin/metrics/realtime")
async def get_realtime_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    # 當前運行中的執行
    running_executions = db.query(Execution).filter(
        Execution.status == "running"
    ).all()
    
    # 待處理的執行
    pending_executions = db.query(func.count(Execution.id)).filter(
        Execution.status == "pending"
    ).scalar()
    
    # 過去 5 分鐘的執行
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    recent_executions = db.query(func.count(Execution.id)).filter(
        Execution.created_at >= five_minutes_ago
    ).scalar()
    
    # 平均執行時長（過去 1 小時）
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    avg_duration = db.query(
        func.avg(Execution.duration_seconds)
    ).filter(
        Execution.completed_at >= one_hour_ago,
        Execution.status == "completed"
    ).scalar()
    
    return {
        "running_executions": len(running_executions),
        "pending_executions": pending_executions,
        "recent_executions": recent_executions,
        "average_duration_seconds": round(avg_duration, 2) if avg_duration else None,
        "active_workflows": [
            {
                "execution_id": ex.id,
                "workflow_id": ex.workflow_id,
                "started_at": ex.started_at,
                "current_step": ex.current_step
            }
            for ex in running_executions
        ]
    }
```

**3. 系統健康狀態 API**

```python
# app/api/v1/admin/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import settings
import redis
import psutil
import requests

router = APIRouter()

@router.get("/api/admin/health")
async def get_system_health(db: Session = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "components": {}
    }
    
    # 檢查數據庫
    try:
        db.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "up",
            "type": "PostgreSQL"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "down",
            "error": str(e)
        }
    
    # 檢查 Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["components"]["redis"] = {
            "status": "up",
            "type": "Redis"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["redis"] = {
            "status": "down",
            "error": str(e)
        }
    
    # 檢查 RabbitMQ
    try:
        response = requests.get(
            f"{settings.RABBITMQ_URL}/api/healthchecks/node",
            auth=(settings.RABBITMQ_USER, settings.RABBITMQ_PASS),
            timeout=5
        )
        if response.status_code == 200:
            health_status["components"]["rabbitmq"] = {
                "status": "up",
                "type": "RabbitMQ"
            }
        else:
            raise Exception("Health check failed")
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["rabbitmq"] = {
            "status": "down",
            "error": str(e)
        }
    
    # 系統資源
    health_status["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    return health_status
```

**4. 用戶管理 API**

```python
# app/api/v1/admin/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter()

@router.get("/api/admin/users/")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.email.contains(search)) | (User.name.contains(search))
        )
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "users": users
    }

@router.post("/api/admin/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    user_service = UserService(db)
    
    # 檢查 email 是否已存在
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = user_service.create_user(user_data)
    return user

@router.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 軟刪除
    user.is_active = False
    user.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "User deleted successfully"}
```

#### 子任務

1. [ ] 實現統計數據 API
2. [ ] 實現實時指標 API
3. [ ] 實現系統健康狀態 API
4. [ ] 實現用戶管理 API
5. [ ] 添加 Redis 緩存
6. [ ] 編寫單元測試
7. [ ] 編寫 API 文檔

#### 測試計劃

```python
# tests/integration/test_admin_apis.py
def test_overview_statistics(client, admin_user):
    response = client.get(
        "/api/admin/statistics/overview",
        headers={"Authorization": f"Bearer {admin_user.token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "workflows" in data
    assert "executions" in data
    assert data["workflows"]["total"] >= 0

def test_non_admin_cannot_access(client, regular_user):
    response = client.get(
        "/api/admin/statistics/overview",
        headers={"Authorization": f"Bearer {regular_user.token}"}
    )
    
    assert response.status_code == 403
```

---

## 📈 Sprint 2 Metrics

### Velocity Tracking
- **計劃點數**: 40
- **調整點數** (假期): 28-32
- **關鍵任務**: S2-1, S2-3, S2-7 (P0)

### Risk Register
- 🔴 假期期間人員可用性降低
- 🟡 n8n Webhook 簽名驗證複雜度
- 🟡 Teams API 限流問題

### Definition of Done
- [ ] 所有代碼已合併到 main
- [ ] 單元測試覆蓋率 ≥ 80%
- [ ] 集成測試通過
- [ ] API 文檔已更新
- [ ] 部署到 Staging 成功
- [ ] Code review 已批准

---

**文檔狀態**: ✅ 已完成  
**上次更新**: 2025-11-19  
**下次審查**: Sprint 2 開始前 (2025-12-23)