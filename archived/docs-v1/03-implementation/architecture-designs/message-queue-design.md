# Message Queue 架構設計文檔

## 1. 概述

### 1.1 目的

消息隊列在系統中用於：
- **異步任務處理**：工作流執行、長時間運行任務
- **服務解耦**：微服務間通信、事件驅動架構
- **負載均衡**：分散任務到多個 Worker
- **可靠性保證**：消息持久化、重試機制、死信隊列
- **峰值削峰**：處理突發流量
- **事件溯源**：記錄系統事件歷史

### 1.2 技術選型

**生產環境（Azure）**：
- **Azure Service Bus**（完全託管服務）
- Premium 層支持高級功能
- 原生 Azure 集成
- 企業級 SLA

**本地開發環境**：
- **RabbitMQ 3.12+**（Docker 容器）
- 與 Service Bus 概念相似
- 易於本地調試
- 抽象層保證兼容性

### 1.3 部署架構

**本地開發**：
```
┌─────────────────────────────────────────┐
│   Docker Compose Environment            │
│                                          │
│  ┌──────────┐      ┌──────────┐        │
│  │ Backend  │─────▶│ RabbitMQ │        │
│  │ FastAPI  │◀─────│  3.12    │        │
│  └──────────┘      └──────────┘        │
│                     - Queues            │
│                     - Exchanges         │
│                     - Dead Letter Queue │
└─────────────────────────────────────────┘
```

**Azure 生產環境**：
```
┌──────────────────────────────────────────────────┐
│   Azure Resource Group                           │
│                                                   │
│  ┌──────────────┐      ┌─────────────────────┐  │
│  │  App Service │─────▶│ Service Bus         │  │
│  │  (Backend)   │◀─────│ - Namespace         │  │
│  └──────────────┘      │ - Queues            │  │
│                        │ - Topics/Subscr.    │  │
│  ┌──────────────┐      │ - Dead Letter Queue │  │
│  │  Functions   │─────▶└─────────────────────┘  │
│  │  (Workers)   │         ↑                      │
│  └──────────────┘         │                      │
│                      Managed Identity            │
└──────────────────────────────────────────────────┘
```

## 2. 隊列設計

### 2.1 核心隊列

| 隊列名稱 | 用途 | 消息類型 | TTL | 最大重試 |
|---------|------|---------|-----|---------|
| `workflow-execution` | 工作流執行請求 | ExecutionRequest | 1h | 3 |
| `workflow-steps` | 工作流步驟執行 | StepExecution | 30m | 3 |
| `notifications` | 通知發送 | Notification | 15m | 5 |
| `webhooks` | Webhook 調用 | WebhookCall | 10m | 3 |
| `agent-tasks` | AI Agent 任務 | AgentTask | 2h | 2 |
| `audit-logs` | 審計日誌異步寫入 | AuditLog | 5m | 5 |

### 2.2 死信隊列（Dead Letter Queue）

所有隊列配置對應的 DLQ：
```
workflow-execution -> workflow-execution-dlq
workflow-steps -> workflow-steps-dlq
notifications -> notifications-dlq
...
```

**DLQ 策略**：
- 達到最大重試次數後移入 DLQ
- 消息過期後移入 DLQ
- 處理失敗且不可重試的錯誤移入 DLQ

**DLQ 處理**：
- 人工審查和修復
- 重新入隊（修復後）
- 記錄到監控系統

### 2.3 優先級隊列

支持緊急任務優先處理：
```python
# 優先級級別
class Priority(int, Enum):
    LOW = 0      # 批處理任務
    NORMAL = 1   # 一般任務（默認）
    HIGH = 2     # 用戶觸發任務
    CRITICAL = 3 # 緊急任務
```

## 3. 消息模型

### 3.1 消息結構

**標準消息格式**：
```python
{
    "message_id": "uuid",
    "correlation_id": "uuid",  # 用於追蹤相關消息
    "message_type": "workflow.execution.start",
    "timestamp": "2025-11-20T10:00:00Z",
    "version": "1.0",
    "priority": 1,
    "payload": {
        # 消息具體內容
    },
    "metadata": {
        "user_id": "uuid",
        "tenant_id": "uuid",
        "source": "api",
        "retry_count": 0
    }
}
```

### 3.2 消息類型定義

**工作流執行消息**：
```python
{
    "message_type": "workflow.execution.start",
    "payload": {
        "execution_id": "uuid",
        "workflow_id": "uuid",
        "workflow_version_id": "uuid",
        "input_data": {...},
        "triggered_by": "user_id"
    }
}
```

**工作流步驟消息**：
```python
{
    "message_type": "workflow.step.execute",
    "payload": {
        "execution_id": "uuid",
        "step_id": "uuid",
        "step_name": "Call Agent",
        "step_config": {...},
        "previous_output": {...}
    }
}
```

**通知消息**：
```python
{
    "message_type": "notification.send",
    "payload": {
        "user_id": "uuid",
        "notification_type": "email|sms|push",
        "subject": "Workflow Completed",
        "content": "...",
        "template_id": "uuid"
    }
}
```

**Webhook 消息**：
```python
{
    "message_type": "webhook.call",
    "payload": {
        "webhook_id": "uuid",
        "url": "https://...",
        "method": "POST",
        "headers": {...},
        "body": {...},
        "timeout_seconds": 30
    }
}
```

**Agent 任務消息**：
```python
{
    "message_type": "agent.task.execute",
    "payload": {
        "task_id": "uuid",
        "agent_id": "uuid",
        "agent_type": "agent_framework",
        "prompt": "...",
        "context": {...},
        "tools": [...]
    }
}
```

## 4. Azure Service Bus 配置

### 4.1 Namespace 配置

**Staging**：
```bicep
resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: 'sb-ai-framework-staging'
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    minimumTlsVersion: '1.2'
  }
}
```

**Production**：
```bicep
resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: 'sb-ai-framework-prod'
  location: location
  sku: {
    name: 'Premium'
    tier: 'Premium'
    capacity: 1  // 1, 2, 4, 8 messaging units
  }
  properties: {
    minimumTlsVersion: '1.2'
    zoneRedundant: true
  }
}
```

### 4.2 Queue 配置

```bicep
resource workflowExecutionQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: 'workflow-execution'
  properties: {
    maxDeliveryCount: 3
    lockDuration: 'PT5M'  // 5 minutes
    defaultMessageTimeToLive: 'PT1H'  // 1 hour
    deadLetteringOnMessageExpiration: true
    enablePartitioning: true  // Standard tier
    maxSizeInMegabytes: 1024
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'
  }
}
```

### 4.3 Topic 和 Subscription（事件驅動）

**Topic 配置**（用於發布/訂閱模式）：
```bicep
resource workflowEventsTopic 'Microsoft.ServiceBus/namespaces/topics@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: 'workflow-events'
  properties: {
    defaultMessageTimeToLive: 'PT1H'
    maxSizeInMegabytes: 1024
    enablePartitioning: true
  }
}

// Subscription for audit service
resource auditSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = {
  parent: workflowEventsTopic
  name: 'audit-service'
  properties: {
    maxDeliveryCount: 5
    lockDuration: 'PT2M'
  }
}

// Subscription for notification service
resource notificationSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = {
  parent: workflowEventsTopic
  name: 'notification-service'
  properties: {
    maxDeliveryCount: 5
    lockDuration: 'PT2M'
  }
}
```

### 4.4 訪問策略

```bicep
resource sendOnlyPolicy 'Microsoft.ServiceBus/namespaces/authorizationRules@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: 'SendOnlyPolicy'
  properties: {
    rights: ['Send']
  }
}

resource listenOnlyPolicy 'Microsoft.ServiceBus/namespaces/authorizationRules@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: 'ListenOnlyPolicy'
  properties: {
    rights: ['Listen']
  }
}

resource managePolicy 'Microsoft.ServiceBus/namespaces/authorizationRules@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: 'ManagePolicy'
  properties: {
    rights: ['Manage', 'Send', 'Listen']
  }
}
```

## 5. RabbitMQ 本地配置

### 5.1 Docker Compose 配置

```yaml
rabbitmq:
  image: rabbitmq:3.12-management-alpine
  container_name: ai-framework-rabbitmq
  environment:
    RABBITMQ_DEFAULT_USER: admin
    RABBITMQ_DEFAULT_PASS: admin
    RABBITMQ_DEFAULT_VHOST: ai-framework
  ports:
    - "5672:5672"    # AMQP protocol
    - "15672:15672"  # Management UI
  volumes:
    - rabbitmq_data:/var/lib/rabbitmq
    - ./scripts/rabbitmq-init.sh:/docker-entrypoint-init.d/init.sh:ro
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 5.2 隊列初始化腳本

```bash
#!/bin/bash
# scripts/rabbitmq-init.sh

# Wait for RabbitMQ to be ready
sleep 10

# Declare queues with dead letter exchanges
rabbitmqadmin declare queue name=workflow-execution \
  durable=true \
  arguments='{"x-dead-letter-exchange":"dlx", "x-dead-letter-routing-key":"workflow-execution-dlq"}'

rabbitmqadmin declare queue name=workflow-execution-dlq durable=true

rabbitmqadmin declare queue name=workflow-steps \
  durable=true \
  arguments='{"x-dead-letter-exchange":"dlx", "x-dead-letter-routing-key":"workflow-steps-dlq"}'

rabbitmqadmin declare queue name=workflow-steps-dlq durable=true

# ... 其他隊列配置
```

## 6. 抽象層設計

### 6.1 統一接口

```python
class MessageQueueProvider(ABC):
    """Message queue provider abstraction"""

    @abstractmethod
    async def send_message(
        self,
        queue_name: str,
        message: dict,
        priority: int = 1,
        delay_seconds: int = 0
    ) -> str:
        """Send message to queue"""
        pass

    @abstractmethod
    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        wait_time_seconds: int = 0
    ) -> List[Message]:
        """Receive messages from queue"""
        pass

    @abstractmethod
    async def complete_message(
        self,
        message: Message
    ) -> None:
        """Mark message as completed"""
        pass

    @abstractmethod
    async def abandon_message(
        self,
        message: Message,
        reason: str = None
    ) -> None:
        """Abandon message (will be retried)"""
        pass

    @abstractmethod
    async def dead_letter_message(
        self,
        message: Message,
        reason: str
    ) -> None:
        """Move message to dead letter queue"""
        pass
```

### 6.2 實現類

**Azure Service Bus Provider**：
```python
class ServiceBusProvider(MessageQueueProvider):
    """Azure Service Bus implementation"""

    def __init__(self, connection_string: str):
        self.client = ServiceBusClient.from_connection_string(
            connection_string
        )

    async def send_message(self, queue_name: str, message: dict, ...):
        async with self.client:
            sender = self.client.get_queue_sender(queue_name)
            async with sender:
                msg = ServiceBusMessage(
                    body=json.dumps(message),
                    application_properties={
                        "priority": priority
                    }
                )
                await sender.send_messages(msg)
```

**RabbitMQ Provider**：
```python
class RabbitMQProvider(MessageQueueProvider):
    """RabbitMQ implementation"""

    def __init__(self, connection_url: str):
        self.connection = await aio_pika.connect_robust(
            connection_url
        )

    async def send_message(self, queue_name: str, message: dict, ...):
        async with self.connection.channel() as channel:
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    priority=priority
                ),
                routing_key=queue_name
            )
```

## 7. 消息處理模式

### 7.1 消費者模式

**基礎消費者**：
```python
class MessageConsumer:
    """Base message consumer"""

    def __init__(
        self,
        queue_provider: MessageQueueProvider,
        queue_name: str,
        handler: Callable
    ):
        self.queue_provider = queue_provider
        self.queue_name = queue_name
        self.handler = handler

    async def start(self):
        """Start consuming messages"""
        while True:
            messages = await self.queue_provider.receive_messages(
                self.queue_name,
                max_messages=10,
                wait_time_seconds=20
            )

            for message in messages:
                try:
                    await self.handler(message.payload)
                    await self.queue_provider.complete_message(message)
                except RetryableError as e:
                    logger.warning(f"Retryable error: {e}")
                    await self.queue_provider.abandon_message(
                        message,
                        reason=str(e)
                    )
                except Exception as e:
                    logger.error(f"Fatal error: {e}")
                    await self.queue_provider.dead_letter_message(
                        message,
                        reason=str(e)
                    )
```

### 7.2 批量處理

```python
class BatchMessageConsumer:
    """Batch message consumer for high throughput"""

    async def process_batch(self, messages: List[Message]):
        """Process messages in batch"""
        tasks = [
            self.process_single(msg)
            for msg in messages
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        # Handle results
        for msg, result in zip(messages, results):
            if isinstance(result, Exception):
                await self.handle_error(msg, result)
            else:
                await self.queue_provider.complete_message(msg)
```

### 7.3 競爭消費者（Competing Consumers）

多個 Worker 實例競爭處理消息：
```python
# Worker 1, 2, 3 同時監聽同一個隊列
# Service Bus 自動負載均衡
# RabbitMQ 使用 prefetch_count 控制

consumer = MessageConsumer(
    queue_provider=provider,
    queue_name="workflow-execution",
    handler=execute_workflow
)

# 每個 Worker 最多同時處理 5 條消息
await consumer.start(prefetch_count=5)
```

## 8. 重試策略

### 8.1 指數退避重試

```python
class RetryPolicy:
    """Exponential backoff retry policy"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, retry_count: int) -> float:
        """Calculate delay for given retry count"""
        delay = self.base_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_delay)

# 示例：
# Retry 1: 1s
# Retry 2: 2s
# Retry 3: 4s
```

### 8.2 條件重試

```python
class ConditionalRetryPolicy:
    """Retry based on exception type"""

    RETRYABLE_EXCEPTIONS = {
        ConnectionError,
        TimeoutError,
        TemporaryError
    }

    NON_RETRYABLE_EXCEPTIONS = {
        ValidationError,
        AuthorizationError,
        NotFoundError
    }

    @staticmethod
    def should_retry(exception: Exception) -> bool:
        """Check if exception is retryable"""
        exception_type = type(exception)
        return exception_type in ConditionalRetryPolicy.RETRYABLE_EXCEPTIONS
```

## 9. 消息過濾和路由

### 9.1 消息過濾（Service Bus Filters）

```python
# SQL-like filter on message properties
subscription_filter = SqlRuleFilter(
    "user_id = 'specific-user' AND priority >= 2"
)

# Correlation filter (more efficient)
correlation_filter = CorrelationRuleFilter(
    correlation_id="workflow-123",
    properties={
        "message_type": "workflow.execution.start"
    }
)
```

### 9.2 路由策略

**基於消息類型路由**：
```python
MESSAGE_ROUTING = {
    "workflow.execution.start": "workflow-execution",
    "workflow.step.execute": "workflow-steps",
    "notification.send": "notifications",
    "webhook.call": "webhooks",
    "agent.task.execute": "agent-tasks"
}

def route_message(message: dict) -> str:
    """Route message to appropriate queue"""
    message_type = message.get("message_type")
    return MESSAGE_ROUTING.get(message_type, "default-queue")
```

## 10. 監控和可觀測性

### 10.1 關鍵指標

**隊列指標**：
- `queue_depth` - 隊列深度
- `messages_sent` - 發送消息數
- `messages_received` - 接收消息數
- `messages_completed` - 完成消息數
- `messages_abandoned` - 放棄消息數
- `messages_dead_lettered` - 死信消息數

**處理指標**：
- `processing_time` - 處理時長
- `retry_count` - 重試次數
- `error_rate` - 錯誤率
- `throughput` - 吞吐量

### 10.2 Azure Monitor 集成

```python
from azure.monitor.opentelemetry import configure_azure_monitor

# Enable Application Insights
configure_azure_monitor(
    connection_string=settings.appinsights_connection_string
)

# Custom metrics
tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("process_message")
async def process_message(message: Message):
    span = trace.get_current_span()
    span.set_attribute("queue.name", message.queue_name)
    span.set_attribute("message.id", message.message_id)

    try:
        # Process message
        result = await handler(message.payload)
        span.set_attribute("result.status", "success")
        return result
    except Exception as e:
        span.set_attribute("result.status", "error")
        span.record_exception(e)
        raise
```

### 10.3 告警規則

**Azure Service Bus Alerts**：
- Dead letter messages > 10
- Active messages > 1000 (積壓告警)
- Server errors > 10/min
- Throttled requests > 5/min

**自定義告警**：
- Processing time > 30s (P95)
- Error rate > 5%
- Retry rate > 20%

## 11. 安全性

### 11.1 認證授權

**Azure Service Bus**：
- Managed Identity（推薦）
- Connection String（開發環境）
- SAS Token（特定場景）

**RabbitMQ**：
- 用戶名/密碼
- TLS 客戶端證書
- OAuth 2.0 插件

### 11.2 消息加密

**傳輸加密**：
- Azure Service Bus: TLS 1.2+（強制）
- RabbitMQ: TLS/SSL 配置

**數據加密**：
```python
from cryptography.fernet import Fernet

class EncryptedMessageQueue:
    """Message queue with payload encryption"""

    def __init__(self, queue_provider, encryption_key: bytes):
        self.queue_provider = queue_provider
        self.cipher = Fernet(encryption_key)

    async def send_encrypted(self, queue_name: str, message: dict):
        """Send message with encrypted payload"""
        encrypted_payload = self.cipher.encrypt(
            json.dumps(message["payload"]).encode()
        )

        message["payload"] = base64.b64encode(encrypted_payload).decode()
        message["encrypted"] = True

        await self.queue_provider.send_message(queue_name, message)

    async def receive_encrypted(self, queue_name: str):
        """Receive and decrypt message"""
        messages = await self.queue_provider.receive_messages(queue_name)

        for msg in messages:
            if msg.payload.get("encrypted"):
                encrypted_data = base64.b64decode(
                    msg.payload["payload"]
                )
                decrypted = self.cipher.decrypt(encrypted_data)
                msg.payload["payload"] = json.loads(decrypted.decode())

        return messages
```

## 12. 成本優化

### 12.1 Azure Service Bus 定價

**Standard Tier**：
- $0.05 per million operations
- 適合中小規模應用

**Premium Tier**：
- $0.928 per messaging unit/hour
- 1 Messaging Unit ≈ 1000 messages/sec
- 適合大規模生產環境

### 12.2 成本優化策略

1. **批量處理**: 減少操作次數
2. **消息壓縮**: 減少數據傳輸量
3. **合理 TTL**: 避免消息積壓
4. **使用 Topics**: 多訂閱者共享消息
5. **監控使用量**: 及時調整配置

## 13. 災難恢復

### 13.1 備份策略

**Azure Service Bus**：
- Geo-Disaster Recovery（Premium tier）
- 自動備份到配對區域
- 無需手動干預

**RabbitMQ**：
- 定期導出隊列配置
- 消息持久化到磁盤
- 定期備份數據目錄

### 13.2 故障恢復

**失敗場景處理**：
```python
class ResilientMessageQueue:
    """Message queue with failover support"""

    def __init__(
        self,
        primary_provider: MessageQueueProvider,
        fallback_provider: Optional[MessageQueueProvider] = None
    ):
        self.primary = primary_provider
        self.fallback = fallback_provider

    async def send_with_fallback(self, queue_name: str, message: dict):
        """Send message with automatic failover"""
        try:
            return await self.primary.send_message(queue_name, message)
        except Exception as e:
            logger.error(f"Primary provider failed: {e}")

            if self.fallback:
                logger.info("Failing over to fallback provider")
                return await self.fallback.send_message(queue_name, message)
            else:
                raise
```

## 14. 最佳實踐

### 14.1 消息設計

1. **冪等性**: 處理器必須是冪等的
2. **小消息**: 消息體 < 256KB
3. **完整信息**: 包含處理所需的所有信息
4. **版本化**: 支持消息格式演進

### 14.2 隊列設計

1. **單一職責**: 每個隊列處理一種任務類型
2. **合理 TTL**: 根據業務特性設置
3. **DLQ 監控**: 及時處理死信消息
4. **分區**: 高吞吐量場景啟用分區

### 14.3 消費者設計

1. **併發控制**: 控制 prefetch_count
2. **優雅關閉**: 處理中的消息完成後再退出
3. **錯誤處理**: 區分可重試和不可重試錯誤
4. **日誌記錄**: 詳細記錄處理過程

## 15. 測試策略

### 15.1 單元測試

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_send_message():
    """Test message sending"""
    mock_provider = AsyncMock(spec=MessageQueueProvider)
    mock_provider.send_message.return_value = "msg-id-123"

    queue_service = QueueService(mock_provider)
    msg_id = await queue_service.send(
        "test-queue",
        {"data": "test"}
    )

    assert msg_id == "msg-id-123"
    mock_provider.send_message.assert_called_once()
```

### 15.2 集成測試

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_roundtrip():
    """Test sending and receiving message"""
    # Use real RabbitMQ in Docker
    provider = RabbitMQProvider(settings.rabbitmq_url)

    # Send message
    test_message = {"test": "data"}
    await provider.send_message("test-queue", test_message)

    # Receive message
    messages = await provider.receive_messages("test-queue")
    assert len(messages) == 1
    assert messages[0].payload == test_message
```

## 16. 參考資料

- [Azure Service Bus Documentation](https://docs.microsoft.com/azure/service-bus-messaging/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/)
- [Competing Consumers Pattern](https://docs.microsoft.com/azure/architecture/patterns/competing-consumers)
