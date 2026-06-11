# Orchestration API Reference

**版本**: 1.0.0
**創建日期**: 2026-01-16
**Phase**: 28 (Sprint 99)

---

## 概述

Orchestration API 提供三層意圖路由、引導式對話和人機協作審批功能。

**Base URL**: `/api/v1/orchestration`

---

## API Endpoints

### Intent Classification

#### POST /api/v1/orchestration/intent/classify

對用戶輸入進行意圖分類，使用三層路由架構。

**Request**:
```json
{
  "content": "ETL Pipeline 今天跑失敗了",
  "source": "user",
  "metadata": {
    "user_id": "user@example.com",
    "session_id": "session-123"
  }
}
```

**Request Parameters**:
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| content | string | 是 | 用戶輸入內容 |
| source | string | 否 | 來源類型 (user, servicenow, prometheus) |
| metadata | object | 否 | 額外元數據 |

**Response** (200 OK):
```json
{
  "data": {
    "intent_category": "incident",
    "sub_intent": "etl_failure",
    "confidence": 0.95,
    "workflow_type": "sequential",
    "risk_level": "high",
    "completeness": {
      "is_complete": false,
      "missing_fields": ["error_message", "affected_scope"],
      "completeness_score": 0.6,
      "suggestions": ["請問是什麼錯誤訊息？", "影響範圍有多大？"]
    },
    "routing_layer": "pattern",
    "rule_id": "incident_etl_failure",
    "reasoning": "Pattern matched: ETL.*失敗",
    "processing_time_ms": 5.2
  },
  "message": "Classification successful"
}
```

**Response Schema**:
| 欄位 | 類型 | 說明 |
|------|------|------|
| intent_category | string | 意圖類別 (incident, request, change, query, unknown) |
| sub_intent | string | 子意圖 |
| confidence | float | 信心分數 (0.0 - 1.0) |
| workflow_type | string | 工作流類型 (simple, sequential, magentic, handoff) |
| risk_level | string | 風險等級 (low, medium, high, critical) |
| completeness | object | 完整度評估 |
| routing_layer | string | 使用的路由層 (pattern, semantic, llm) |
| processing_time_ms | float | 處理時間 (毫秒) |

**Error Responses**:

| 狀態碼 | 說明 |
|--------|------|
| 400 | Invalid request body |
| 500 | Internal server error |

---

### Guided Dialog

#### POST /api/v1/orchestration/dialog/start

開始一個新的引導式對話會話。

**Request**:
```json
{
  "user_input": "系統有問題",
  "user_id": "user@example.com",
  "max_turns": 5
}
```

**Response** (200 OK):
```json
{
  "data": {
    "dialog_id": "dialog-abc123",
    "state": {
      "phase": "gathering",
      "turn_count": 0,
      "is_complete": false,
      "routing_decision": {
        "intent_category": "incident",
        "confidence": 0.7,
        "completeness": {
          "is_complete": false,
          "missing_fields": ["system_name", "error_message"],
          "completeness_score": 0.4
        }
      }
    },
    "message": "了解，這是一個事件報告。\n為了更快地協助您，請回答以下問題：\n\n1. 請問是哪個系統有問題？\n2. 有什麼錯誤訊息嗎？",
    "questions": [
      {
        "question": "請問是哪個系統有問題？",
        "target_field": "system_name",
        "options": ["ETL Pipeline", "DataWarehouse", "Web Application", "其他"],
        "priority": 100
      },
      {
        "question": "有什麼錯誤訊息嗎？",
        "target_field": "error_message",
        "priority": 90
      }
    ],
    "should_continue": true,
    "next_action": "gather_info"
  },
  "message": "Dialog started"
}
```

#### POST /api/v1/orchestration/dialog/{dialog_id}/respond

處理用戶對引導式對話的回應。

**Request**:
```json
{
  "response": "是 ETL Pipeline，錯誤訊息是 connection timeout"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "dialog_id": "dialog-abc123",
    "state": {
      "phase": "complete",
      "turn_count": 1,
      "is_complete": true,
      "routing_decision": {
        "intent_category": "incident",
        "sub_intent": "etl_failure",
        "confidence": 0.95,
        "completeness": {
          "is_complete": true,
          "completeness_score": 0.9
        }
      }
    },
    "message": "感謝您提供的資訊。\n\n已收集完成，將進行事件處理：\n- 類型：etl_failure\n- 處理方式：sequential\n- 風險等級：high",
    "questions": [],
    "should_continue": false,
    "next_action": "execute_sequential"
  },
  "message": "Dialog response processed"
}
```

#### GET /api/v1/orchestration/dialog/{dialog_id}

獲取對話狀態。

**Response** (200 OK):
```json
{
  "data": {
    "dialog_id": "dialog-abc123",
    "status": "gathering",
    "turn_count": 1,
    "is_complete": false,
    "collected_fields": {
      "system_name": "ETL Pipeline"
    },
    "missing_fields": ["error_message", "affected_scope"],
    "routing_decision": {
      "intent_category": "incident",
      "sub_intent": "etl_failure"
    }
  },
  "message": "Dialog state retrieved"
}
```

#### DELETE /api/v1/orchestration/dialog/{dialog_id}

結束並清理對話會話。

**Response** (200 OK):
```json
{
  "data": {
    "dialog_id": "dialog-abc123",
    "final_state": "completed"
  },
  "message": "Dialog ended"
}
```

---

### HITL (Human-in-the-Loop) Approval

#### POST /api/v1/orchestration/hitl/request

創建新的審批請求。

**Request**:
```json
{
  "routing_decision_id": "decision-xyz789",
  "requester": "user@example.com",
  "timeout_minutes": 30,
  "approvers": ["admin@example.com", "manager@example.com"],
  "metadata": {
    "reason": "高風險操作需要審批"
  }
}
```

**Response** (201 Created):
```json
{
  "data": {
    "request_id": "approval-req-123",
    "status": "pending",
    "created_at": "2026-01-16T10:30:00Z",
    "expires_at": "2026-01-16T11:00:00Z",
    "risk_level": "high",
    "approval_type": "single",
    "routing_decision": {
      "intent_category": "incident",
      "sub_intent": "system_unavailable",
      "workflow_type": "magentic"
    }
  },
  "message": "Approval request created"
}
```

#### GET /api/v1/orchestration/hitl/{request_id}

獲取審批請求狀態。

**Response** (200 OK):
```json
{
  "data": {
    "request_id": "approval-req-123",
    "status": "pending",
    "created_at": "2026-01-16T10:30:00Z",
    "expires_at": "2026-01-16T11:00:00Z",
    "requester": "user@example.com",
    "approvers": ["admin@example.com"],
    "history": [
      {
        "event_type": "created",
        "timestamp": "2026-01-16T10:30:00Z",
        "actor": "user@example.com"
      },
      {
        "event_type": "notification_sent",
        "timestamp": "2026-01-16T10:30:01Z",
        "actor": "system"
      }
    ]
  },
  "message": "Approval request retrieved"
}
```

#### POST /api/v1/orchestration/hitl/{request_id}/approve

批准審批請求。

**Request**:
```json
{
  "approver": "admin@example.com",
  "comment": "已確認風險可控，批准執行"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "request_id": "approval-req-123",
    "status": "approved",
    "approved_by": "admin@example.com",
    "approved_at": "2026-01-16T10:45:00Z",
    "comment": "已確認風險可控，批准執行"
  },
  "message": "Request approved"
}
```

#### POST /api/v1/orchestration/hitl/{request_id}/reject

拒絕審批請求。

**Request**:
```json
{
  "approver": "admin@example.com",
  "comment": "需要更多調查才能執行"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "request_id": "approval-req-123",
    "status": "rejected",
    "rejected_by": "admin@example.com",
    "rejected_at": "2026-01-16T10:45:00Z",
    "comment": "需要更多調查才能執行"
  },
  "message": "Request rejected"
}
```

#### POST /api/v1/orchestration/hitl/{request_id}/cancel

取消審批請求。

**Request**:
```json
{
  "canceller": "user@example.com",
  "reason": "問題已自行解決"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "request_id": "approval-req-123",
    "status": "cancelled"
  },
  "message": "Request cancelled"
}
```

#### GET /api/v1/orchestration/hitl/pending

列出所有待審批請求。

**Query Parameters**:
| 參數 | 類型 | 說明 |
|------|------|------|
| approver | string | 按審批人過濾 |
| risk_level | string | 按風險等級過濾 |
| limit | int | 返回數量上限 (默認 20) |
| offset | int | 分頁偏移 |

**Response** (200 OK):
```json
{
  "data": [
    {
      "request_id": "approval-req-123",
      "status": "pending",
      "risk_level": "high",
      "requester": "user@example.com",
      "created_at": "2026-01-16T10:30:00Z",
      "expires_at": "2026-01-16T11:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "message": "Pending requests retrieved"
}
```

---

### System Source Processing

#### POST /api/v1/orchestration/webhook/servicenow

處理 ServiceNow Webhook。

**Request Headers**:
```
x-servicenow-webhook: true
Content-Type: application/json
```

**Request**:
```json
{
  "incident_number": "INC0012345",
  "category": "incident",
  "subcategory": "etl_failure",
  "short_description": "ETL Pipeline 失敗",
  "priority": "P1",
  "assignment_group": "IT Operations",
  "caller_id": "user@example.com"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "intent_category": "incident",
    "sub_intent": "etl_failure",
    "routing_layer": "servicenow_mapping",
    "processing_time_ms": 3.5
  },
  "message": "ServiceNow webhook processed"
}
```

#### POST /api/v1/orchestration/webhook/prometheus

處理 Prometheus AlertManager Webhook。

**Request Headers**:
```
x-prometheus-alertmanager: true
Content-Type: application/json
```

**Request**:
```json
{
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighCPUUsage",
        "severity": "critical",
        "job": "api-server",
        "instance": "api-1"
      },
      "annotations": {
        "summary": "CPU usage is above 90%",
        "description": "API server CPU is critically high"
      },
      "startsAt": "2026-01-16T10:00:00Z"
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "data": {
    "intent_category": "incident",
    "sub_intent": "resource_alert",
    "risk_level": "critical",
    "routing_layer": "prometheus_mapping",
    "processing_time_ms": 2.8
  },
  "message": "Prometheus alert processed"
}
```

---

### Metrics

#### GET /api/v1/orchestration/metrics

獲取監控指標。

**Response** (200 OK):
```json
{
  "data": {
    "routing": {
      "total_requests": 1000,
      "pattern_matches": 700,
      "semantic_matches": 200,
      "llm_fallbacks": 100,
      "avg_latency_ms": 25.5,
      "p95_latency_ms": 85.2
    },
    "dialog": {
      "total_rounds": 500,
      "completion_rate": 0.85,
      "avg_rounds_per_dialog": 2.3
    },
    "hitl": {
      "total_requests": 50,
      "approved": 40,
      "rejected": 5,
      "expired": 5,
      "avg_approval_time_seconds": 180
    },
    "system_sources": {
      "servicenow_requests": 100,
      "prometheus_alerts": 50
    }
  },
  "message": "Metrics retrieved"
}
```

---

## Data Types

### ITIntentCategory

意圖類別枚舉。

```
incident  - 事件報告 (系統故障、錯誤等)
request   - 服務請求 (權限申請、帳號創建等)
change    - 變更請求 (配置變更、部署等)
query     - 一般查詢 (狀態查詢、資訊詢問等)
unknown   - 無法分類
```

### RiskLevel

風險等級枚舉。

```
critical - 立即處理，業務影響
high     - 緊急，重大影響
medium   - 標準優先級
low      - 可排程
```

### WorkflowType

工作流類型枚舉。

```
simple     - 直接單一 Agent 回應
sequential - 順序步驟工作流
magentic   - 多 Agent 協作編排
concurrent - 並行處理工作流
handoff    - 轉交人工處理
```

### ApprovalStatus

審批狀態枚舉。

```
pending   - 等待審批
approved  - 已批准
rejected  - 已拒絕
expired   - 已過期
cancelled - 已取消
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_INPUT | 400 | 無效的輸入參數 |
| DIALOG_NOT_FOUND | 404 | 對話會話不存在 |
| APPROVAL_NOT_FOUND | 404 | 審批請求不存在 |
| APPROVAL_NOT_PENDING | 400 | 審批請求不在待審批狀態 |
| APPROVAL_EXPIRED | 400 | 審批請求已過期 |
| CLASSIFICATION_FAILED | 500 | 意圖分類失敗 |
| INTERNAL_ERROR | 500 | 內部服務器錯誤 |

---

## Rate Limits

| Endpoint | Rate Limit | 說明 |
|----------|------------|------|
| /intent/classify | 100 req/min | 意圖分類 |
| /dialog/* | 50 req/min | 對話操作 |
| /hitl/* | 30 req/min | 審批操作 |
| /webhook/* | 200 req/min | Webhook |
| /metrics | 10 req/min | 監控指標 |

---

## SDK Usage

### Python

```python
from orchestration import (
    BusinessIntentRouter,
    GuidedDialogEngine,
    HITLController,
    create_mock_router,
    create_mock_dialog_engine,
    create_mock_hitl_controller,
)

# Intent Classification
router = create_mock_router()
decision = await router.route("ETL Pipeline 失敗了")
print(f"Intent: {decision.intent_category.value}")
print(f"Layer: {decision.routing_layer}")

# Guided Dialog
engine = create_mock_dialog_engine()
response = await engine.start_dialog("系統有問題")
print(f"Questions: {response.questions}")

# HITL Approval
controller, storage, notification = create_mock_hitl_controller()
request = await controller.request_approval(
    routing_decision=decision,
    risk_assessment=assessment,
    requester="user@example.com",
)
```

---

**API Version**: 1.0.0
**Last Updated**: 2026-01-16
**Phase**: 28 (Sprint 99)
