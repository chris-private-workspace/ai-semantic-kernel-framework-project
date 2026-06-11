# Feature 08: n8n 觸發與錯誤處理

**版本**: 1.0  
**日期**: 2025-11-19  
**狀態**: 草稿

---

## 📑 導航

- [← 返回附錄 B 索引](../../prd-appendix-b-features-8-14.md)
- [← 上一個: Feature 07 - DevUI](../features/feature-07-devui.md)
- [→ 下一個: Feature 09 - 提示管理](./feature-9-prompt-management.md)

---

## F8. n8n 觸發與錯誤處理

**分類**: 可靠性  
**優先級**: P0 (必須擁有 - 觸發機制)  
**開發時間**: 2 週  
**複雜度**: ⭐⭐⭐⭐ (高)  
**依賴項**: n8n (self-hosted), RabbitMQ/Azure Service Bus, PostgreSQL  
**風險等級**: 中等（n8n 整合複雜度、錯誤處理策略）

---

### 8.1 功能概述

**什麼是 n8n 觸發與錯誤處理？**

n8n 觸發與錯誤處理是平台的**事件驅動入口層**，負責：
1. **定時觸發**（Cron）：按計劃執行工作流（例如每小時檢查服務器健康狀況）
2. **事件觸發**（Webhook）：響應外部事件（例如 ServiceNow 新工單、Teams 消息）
3. **錯誤處理**：重試邏輯、死信隊列（DLQ）、優雅降級

**為什麼這很重要**：
- **業務連續性**: 自動化工作流需要可靠的觸發機制（不能遺漏事件）
- **容錯性**: 外部 API 可能失敗（ServiceNow 超時、LLM 限流），需要智能重試
- **可觀察性**: 錯誤應該被捕獲、記錄並通知相關人員

**關鍵能力**：
1. **Cron 觸發器**: 定時執行工作流（支持標準 Cron 表達式）
2. **Webhook 觸發器**: HTTP POST 接收外部事件
3. **指數退避重試**: 智能重試策略（避免雪崩）
4. **死信隊列（DLQ）**: 多次失敗後將消息移至 DLQ，手動干預
5. **錯誤通知**: 關鍵錯誤通過 Teams 通知管理員
6. **幂等性保證**: 同一事件不會重複執行

**商業價值**：
- **可靠性**: 99.5%+ 觸發成功率（即使外部系統不穩定）
- **減少人工干預**: 80% 的錯誤自動重試成功
- **快速恢復**: 平均故障恢復時間（MTTR）< 15 分鐘
- **合規性**: 完整的事件追蹤用於審計

**真實世界示例**：

```
場景: ServiceNow 新工單自動觸發客服 Agent

無容錯機制（傳統方式）:
1. ServiceNow webhook 調用我們的 API
2. API 調用 LLM 失敗（限流 429 錯誤）
3. 工單被遺漏，沒有 Agent 處理
4. 客戶投訴，手動補救（2 小時後）
成功率: 60-70%（外部 API 不穩定時）

使用 n8n 觸發與錯誤處理:
1. ServiceNow webhook → n8n 接收事件
2. n8n 將事件放入消息隊列（RabbitMQ）
3. Worker 從隊列取出事件，調用 LLM
4. LLM 限流 429 → 自動重試（指數退避: 1s, 2s, 4s, 8s）
5. 第 3 次重試成功，工單被處理
6. 如果 5 次重試全失敗 → 移至 DLQ，通知管理員
成功率: 95%+（即使外部 API 不穩定）
```

**架構概覽**：

```
┌─────────────────────┐
│  外部觸發源          │
│  - ServiceNow       │
│  - Dynamics 365     │
│  - Microsoft Teams  │
│  - Cron Scheduler   │
└──────────┬──────────┘
           │ 1. 觸發事件
           ▼
┌─────────────────────┐         ┌──────────────────┐
│  n8n                │────────►│  消息隊列        │
│  (觸發層)           │         │  (RabbitMQ)      │
└─────────────────────┘         └────────┬─────────┘
                                         │
                                         │ 2. 消費消息
                                         ▼
                    ┌────────────────────────────────┐
                    │  Workflow Executor (Worker)    │
                    │  - 重試邏輯（指數退避）        │
                    │  - 幂等性檢查                  │
                    └────────┬───────────────────────┘
                             │
                    ┌────────┼────────┐
                    │ 成功   │ 失敗   │
                    ▼        ▼        ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │執行完成  │  │重試隊列  │  │死信隊列  │
         │(結果存儲)│  │(自動重試)│  │(手動干預)│
         └──────────┘  └──────────┘  └────┬─────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │Teams 通知    │
                                    │(F11)         │
                                    └──────────────┘
```

---

## 8.2 用戶故事（完整）

### **US-F8-001: 配置 Cron 定時觸發器**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** IT 管理員（Alex Chen）
- **我想要** 配置定時觸發器，按計劃執行工作流（例如每小時檢查服務器狀態）
- **以便** 我可以實現預防性監控，而不是被動響應故障

**驗收標準**:
1. ✅ **Cron 表達式支持**: 支持標準 Cron 語法（分鐘、小時、天、月、星期）
2. ✅ **時區支持**: 支持指定時區（默認 UTC）
3. ✅ **啟用/禁用**: 可以臨時禁用觸發器而不刪除配置
4. ✅ **下次執行時間**: UI 顯示下次計劃執行時間
5. ✅ **執行歷史**: 顯示最近 50 次執行記錄（時間、狀態、持續時間）
6. ✅ **錯誤處理**: Cron 執行失敗不影響下次計劃執行

**Cron 配置 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 工作流配置: server_health_check                                 [保存] [取消] │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 🕐 觸發器配置                                                                 │
│                                                                               │
│ 觸發類型: *                                                                   │
│ [Cron (定時) ▼]                                                              │
│   選項: Cron、Webhook、手動                                                  │
│                                                                               │
│ Cron 表達式: *                                                                │
│ [0 * * * *                                          ] 每小時執行一次          │
│                                                                               │
│ 常用模板:                                                                     │
│ [每 5 分鐘] [每小時] [每天午夜] [每週一上午 9 點] [自定義]                  │
│                                                                               │
│ 時區:                                                                         │
│ [Asia/Taipei (UTC+8) ▼]                                                      │
│                                                                               │
│ 狀態:                                                                         │
│ [●] 已啟用  [ ] 已禁用                                                       │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📅 執行計劃                                                                   │
│   下次執行: 2025-11-19 15:00:00 (UTC+8)                                      │
│   下下次執行: 2025-11-19 16:00:00 (UTC+8)                                    │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📊 最近執行記錄                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 時間                    │ 狀態    │ 持續時間 │ 詳情                      ││
│ ├─────────────────────────┼─────────┼──────────┼───────────────────────────┤│
│ │ 2025-11-19 14:00:00     │ ✅ 成功 │ 2.3s     │ 3 個服務器健康            ││
│ │ 2025-11-19 13:00:00     │ ✅ 成功 │ 2.1s     │ 3 個服務器健康            ││
│ │ 2025-11-19 12:00:00     │ ❌ 失敗 │ 30.0s    │ 服務器 DB-01 無響應       ││
│ │ 2025-11-19 11:00:00     │ ✅ 成功 │ 2.4s     │ 3 個服務器健康            ││
│ │ 2025-11-19 10:00:00     │ ✅ 成功 │ 2.2s     │ 3 個服務器健康            ││
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [查看完整歷史]                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

**n8n Cron 節點配置**:

```json
{
  "nodes": [
    {
      "type": "n8n-nodes-base.cron",
      "name": "Server Health Check Trigger",
      "parameters": {
        "triggerTimes": {
          "item": [
            {
              "mode": "everyHour"
            }
          ]
        },
        "timezone": "Asia/Taipei"
      },
      "position": [250, 300]
    },
    {
      "type": "n8n-nodes-base.httpRequest",
      "name": "Call IPA API",
      "parameters": {
        "url": "https://ipa.example.com/api/workflows/server_health_check/execute",
        "method": "POST",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "options": {}
      },
      "position": [450, 300]
    }
  ],
  "connections": {
    "Server Health Check Trigger": {
      "main": [
        [
          {
            "node": "Call IPA API",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

**API: 獲取 Cron 執行歷史**:

```bash
GET /api/workflows/{workflow_id}/cron-history?limit=50

響應:
{
  "workflow_id": "server_health_check",
  "trigger_type": "cron",
  "cron_expression": "0 * * * *",
  "timezone": "Asia/Taipei",
  "next_execution": "2025-11-19T15:00:00+08:00",
  "enabled": true,
  "history": [
    {
      "execution_id": "exec_abc123",
      "scheduled_at": "2025-11-19T14:00:00+08:00",
      "started_at": "2025-11-19T14:00:01+08:00",
      "completed_at": "2025-11-19T14:00:03+08:00",
      "status": "completed",
      "duration_ms": 2300,
      "result": "3 servers healthy"
    },
    {
      "execution_id": "exec_abc122",
      "scheduled_at": "2025-11-19T13:00:00+08:00",
      "started_at": "2025-11-19T13:00:01+08:00",
      "completed_at": "2025-11-19T13:00:03+08:00",
      "status": "completed",
      "duration_ms": 2100,
      "result": "3 servers healthy"
    }
  ]
}
```

**完成定義**:
- [ ] 支持標準 Cron 表達式（分鐘、小時、天、月、星期）
- [ ] UI 提供常用模板（每 5 分鐘、每小時、每天等）
- [ ] 支持時區選擇（至少 10 個主要時區）
- [ ] 顯示下次執行時間和執行歷史
- [ ] 可以啟用/禁用觸發器
- [ ] n8n Cron 節點配置並測試
- [ ] API 返回執行歷史

---

### **US-F8-002: 配置 Webhook 事件觸發器**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** IT 管理員（Alex Chen）
- **我想要** 配置 Webhook 觸發器，響應外部系統事件（例如 ServiceNow 新工單）
- **以便** 我可以實現事件驅動的自動化，而不是輪詢

**驗收標準**:
1. ✅ **唯一 Webhook URL**: 每個工作流生成唯一的 Webhook URL
2. ✅ **安全驗證**: 支持簽名驗證（HMAC-SHA256）或 API Key
3. ✅ **請求過濾**: 可選的 JSON 路徑過濾器（僅處理特定事件類型）
4. ✅ **請求日誌**: 記錄所有 Webhook 請求（成功、失敗、過濾掉的）
5. ✅ **測試工具**: UI 提供 Webhook 測試工具（發送模擬請求）
6. ✅ **幂等性**: 同一事件（基於 `idempotency_key`）不會重複執行

**Webhook 配置 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 工作流配置: servicenow_ticket_automation                        [保存] [取消] │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 🔗 Webhook 觸發器配置                                                         │
│                                                                               │
│ Webhook URL: (只讀)                                                           │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ https://ipa.example.com/webhooks/wh_abc123xyz                           │ │
│ │ [📋 複製]                                                                │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🔐 安全設置                                                                   │
│                                                                               │
│ 驗證方式:                                                                     │
│ [●] HMAC-SHA256 簽名  [ ] API Key  [ ] 無（不推薦）                         │
│                                                                               │
│ Secret Key: (隱藏)                                                            │
│ [••••••••••••••••••••••••••••••••] [重新生成]                                │
│                                                                               │
│ 簽名標頭名稱:                                                                 │
│ [X-ServiceNow-Signature        ]                                             │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🎯 請求過濾器（可選）                                                         │
│                                                                               │
│ 僅處理匹配以下條件的請求:                                                     │
│                                                                               │
│ JSON 路徑: [$.event_type                           ]                         │
│ 運算符:     [等於 ▼                                ]                         │
│ 值:         [incident.created                      ]                         │
│                                                                               │
│ [+ 添加條件]                                                                  │
│                                                                               │
│ 示例: 僅處理 ServiceNow 新工單事件，忽略更新和關閉事件                       │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🧪 測試 Webhook                                                               │
│                                                                               │
│ 請求體 (JSON):                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ {                                                                        │ │
│ │   "event_type": "incident.created",                                      │ │
│ │   "incident_id": "INC0012345",                                           │ │
│ │   "priority": "2",                                                       │ │
│ │   "description": "Server DB-01 is not responding"                        │ │
│ │ }                                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [🚀 發送測試請求]                                                             │
│                                                                               │
│ 測試結果:                                                                     │
│ ✅ Webhook 已觸發，工作流執行 ID: exec_test_001                               │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📊 最近 Webhook 請求                                                          │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 時間                    │ 來源 IP      │ 狀態    │ 執行 ID          ││    │
│ ├─────────────────────────┼──────────────┼─────────┼──────────────────┤│    │
│ │ 2025-11-19 14:23:15     │ 10.0.1.45    │ ✅ 已觸發│ exec_abc125      ││    │
│ │ 2025-11-19 14:15:03     │ 10.0.1.45    │ ✅ 已觸發│ exec_abc124      ││    │
│ │ 2025-11-19 14:10:22     │ 10.0.1.45    │ ⊘ 已過濾 │ (更新事件)       ││    │
│ │ 2025-11-19 14:05:11     │ 203.0.113.5  │ ❌ 驗證失敗│ (無效簽名)     ││    │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [查看完整日誌]                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

**ServiceNow Webhook 配置示例**:

```javascript
// ServiceNow Business Rule: 新工單時發送 Webhook

(function executeRule(current, previous /*null when async*/) {
    var request = new sn_ws.RESTMessageV2();
    request.setEndpoint('https://ipa.example.com/webhooks/wh_abc123xyz');
    request.setHttpMethod('POST');
    
    // 計算 HMAC-SHA256 簽名
    var secret = 'your_webhook_secret_key';
    var payload = JSON.stringify({
        event_type: 'incident.created',
        incident_id: current.number.toString(),
        priority: current.priority.toString(),
        description: current.short_description.toString(),
        assigned_to: current.assigned_to.getDisplayValue(),
        created_at: current.sys_created_on.toString()
    });
    
    var signature = new GlideDigest().getMacB64('HmacSHA256', secret, payload);
    
    request.setRequestHeader('Content-Type', 'application/json');
    request.setRequestHeader('X-ServiceNow-Signature', 'sha256=' + signature);
    request.setRequestBody(payload);
    
    var response = request.execute();
    gs.info('Webhook sent to IPA: ' + response.getStatusCode());
    
})(current, previous);
```

**Webhook 處理端點實現**:

```python
from fastapi import APIRouter, Request, HTTPException, Header
import hmac
import hashlib
import json
from typing import Optional

router = APIRouter()

@router.post("/webhooks/{webhook_id}")
async def handle_webhook(
    webhook_id: str,
    request: Request,
    x_servicenow_signature: Optional[str] = Header(None)
):
    """
    處理 Webhook 請求
    
    1. 驗證簽名
    2. 檢查幂等性
    3. 應用過濾器
    4. 觸發工作流執行
    """
    # 1. 加載 Webhook 配置
    webhook_config = await load_webhook_config(webhook_id)
    
    if not webhook_config:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # 2. 讀取請求體
    body = await request.body()
    payload = json.loads(body)
    
    # 3. 驗證簽名（如果啟用）
    if webhook_config["authentication"] == "hmac":
        if not x_servicenow_signature:
            raise HTTPException(status_code=401, detail="Missing signature")
        
        expected_signature = "sha256=" + hmac.new(
            webhook_config["secret"].encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(x_servicenow_signature, expected_signature):
            # 記錄驗證失敗
            await log_webhook_request(
                webhook_id=webhook_id,
                status="auth_failed",
                source_ip=request.client.host,
                payload=payload
            )
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # 4. 檢查幂等性
    idempotency_key = payload.get("idempotency_key") or payload.get("incident_id")
    if idempotency_key:
        existing_execution = await check_idempotency(webhook_id, idempotency_key)
        if existing_execution:
            # 返回已有的執行 ID（避免重複執行）
            return {
                "status": "already_processed",
                "execution_id": existing_execution.execution_id,
                "message": "This event has already been processed"
            }
    
    # 5. 應用過濾器（如果配置）
    if webhook_config.get("filters"):
        if not apply_filters(payload, webhook_config["filters"]):
            # 記錄過濾掉的請求
            await log_webhook_request(
                webhook_id=webhook_id,
                status="filtered",
                source_ip=request.client.host,
                payload=payload
            )
            return {
                "status": "filtered",
                "message": "Request did not match filter criteria"
            }
    
    # 6. 觸發工作流執行
    execution_id = await trigger_workflow_execution(
        workflow_id=webhook_config["workflow_id"],
        trigger_type="webhook",
        trigger_data=payload,
        idempotency_key=idempotency_key
    )
    
    # 7. 記錄成功的 Webhook 請求
    await log_webhook_request(
        webhook_id=webhook_id,
        status="triggered",
        source_ip=request.client.host,
        payload=payload,
        execution_id=execution_id
    )
    
    return {
        "status": "triggered",
        "execution_id": execution_id,
        "message": "Workflow execution started"
    }


async def apply_filters(payload: dict, filters: list) -> bool:
    """應用 JSON 路徑過濾器"""
    for filter_rule in filters:
        json_path = filter_rule["json_path"]  # $.event_type
        operator = filter_rule["operator"]  # "equals"
        expected_value = filter_rule["value"]  # "incident.created"
        
        # 使用 JSONPath 提取值
        import jsonpath_ng
        jsonpath_expr = jsonpath_ng.parse(json_path)
        matches = jsonpath_expr.find(payload)
        
        if not matches:
            return False
        
        actual_value = matches[0].value
        
        if operator == "equals" and actual_value != expected_value:
            return False
        elif operator == "not_equals" and actual_value == expected_value:
            return False
        elif operator == "contains" and expected_value not in str(actual_value):
            return False
    
    return True
```

**完成定義**:
- [ ] 每個工作流生成唯一的 Webhook URL
- [ ] 支持 HMAC-SHA256 簽名驗證
- [ ] 支持 JSON 路徑過濾器（僅處理特定事件）
- [ ] 記錄所有 Webhook 請求（成功、失敗、過濾）
- [ ] UI 提供 Webhook 測試工具
- [ ] 幂等性檢查（基於 idempotency_key）
- [ ] 集成測試（模擬 ServiceNow Webhook）

---

### **US-F8-003: 智能錯誤處理與指數退避重試**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 4 天  
**複雜度**: ⭐⭐⭐⭐

**用戶故事**:
- **作為** IT 管理員（Alex Chen）
- **我想要** 系統自動重試失敗的工作流執行，使用智能退避策略
- **以便** 我可以處理暫時性故障（網絡抖動、API 限流），而不需要手動干預

**驗收標準**:
1. ✅ **可配置重試策略**: 支持配置最大重試次數（1-10）、初始延遲（秒）
2. ✅ **指數退避**: 重試延遲指數增長（1s → 2s → 4s → 8s → 16s）
3. ✅ **抖動（Jitter）**: 添加隨機抖動避免雷鳴群效應（±20% 隨機延遲）
4. ✅ **錯誤分類**: 區分可重試錯誤（429, 503）和不可重試錯誤（400, 401）
5. ✅ **重試狀態追蹤**: UI 顯示當前重試次數和下次重試時間
6. ✅ **重試日誌**: 記錄每次重試的時間、錯誤、延遲

**重試策略配置 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 工作流配置: customer_360_view                                   [保存] [取消] │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 🔄 錯誤處理與重試策略                                                         │
│                                                                               │
│ 啟用自動重試:                                                                 │
│ [●] 是  [ ] 否                                                               │
│                                                                               │
│ 最大重試次數:                                                                 │
│ [5                  ] (1-10 次)                                              │
│                                                                               │
│ 初始重試延遲:                                                                 │
│ [2                  ] 秒                                                     │
│                                                                               │
│ 退避策略:                                                                     │
│ [●] 指數退避 (1s → 2s → 4s → 8s → 16s)                                       │
│ [ ] 固定延遲 (每次相同)                                                      │
│ [ ] 線性增長 (1s → 2s → 3s → 4s → 5s)                                       │
│                                                                               │
│ 添加隨機抖動:                                                                 │
│ [●] 是 (±20% 隨機延遲，避免雷鳴群)  [ ] 否                                  │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🎯 可重試錯誤類型                                                             │
│                                                                               │
│ HTTP 狀態碼:                                                                  │
│ ☑ 429 (Too Many Requests - 限流)                                             │
│ ☑ 500 (Internal Server Error)                                                │
│ ☑ 502 (Bad Gateway)                                                          │
│ ☑ 503 (Service Unavailable)                                                  │
│ ☑ 504 (Gateway Timeout)                                                      │
│                                                                               │
│ 網絡錯誤:                                                                     │
│ ☑ 連接超時 (Connection Timeout)                                              │
│ ☑ 讀取超時 (Read Timeout)                                                    │
│ ☑ 連接重置 (Connection Reset)                                                │
│                                                                               │
│ 不可重試錯誤（跳過重試，直接失敗）:                                          │
│ ☑ 400 (Bad Request - 請求格式錯誤)                                           │
│ ☑ 401 (Unauthorized - 認證失敗)                                              │
│ ☑ 403 (Forbidden - 權限不足)                                                 │
│ ☑ 404 (Not Found - 資源不存在)                                               │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📊 重試模擬器                                                                 │
│                                                                               │
│ 預覽重試時間線（最大 5 次重試）:                                             │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 第 1 次重試: 2s 後 (範圍: 1.6s - 2.4s，含抖動)                           │ │
│ │ 第 2 次重試: 4s 後 (範圍: 3.2s - 4.8s)                                   │ │
│ │ 第 3 次重試: 8s 後 (範圍: 6.4s - 9.6s)                                   │ │
│ │ 第 4 次重試: 16s 後 (範圍: 12.8s - 19.2s)                                │ │
│ │ 第 5 次重試: 32s 後 (範圍: 25.6s - 38.4s)                                │ │
│ │                                                                          │ │
│ │ 總重試時間窗口: 最多 62 秒                                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🔍 最近重試記錄                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 執行 ID       │ 重試次數 │ 最終狀態 │ 錯誤類型           │ 總耗時  ││   │
│ ├───────────────┼──────────┼──────────┼────────────────────┼─────────┤│   │
│ │ exec_abc125   │ 3/5      │ ✅ 成功  │ 429 Rate Limit     │ 14.2s   ││   │
│ │ exec_abc124   │ 1/5      │ ✅ 成功  │ 503 Unavailable    │ 2.3s    ││   │
│ │ exec_abc123   │ 5/5      │ ❌ 失敗  │ 500 Internal Error │ 62.0s   ││   │
│ │ exec_abc122   │ 0/5      │ ✅ 成功  │ (無錯誤)           │ 1.2s    ││   │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [查看詳細重試日誌]                                                            │
└───────────────────────────────────────────────────────────────────────────────┘
```

**重試邏輯實現**:

```python
import asyncio
import random
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

class RetryPolicy:
    """重試策略配置"""
    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 2.0,
        backoff_strategy: str = "exponential",  # exponential, fixed, linear
        jitter: bool = True,
        retryable_errors: list = None
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_strategy = backoff_strategy
        self.jitter = jitter
        self.retryable_errors = retryable_errors or [429, 500, 502, 503, 504]
    
    def calculate_delay(self, attempt: int) -> float:
        """計算重試延遲"""
        if self.backoff_strategy == "exponential":
            delay = self.initial_delay * (2 ** attempt)
        elif self.backoff_strategy == "linear":
            delay = self.initial_delay * (attempt + 1)
        else:  # fixed
            delay = self.initial_delay
        
        # 添加抖動（±20%）
        if self.jitter:
            jitter_range = delay * 0.2
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0.1, delay)  # 最小 100ms
    
    def is_retryable_error(self, error: Exception) -> bool:
        """判斷錯誤是否可重試"""
        if isinstance(error, HTTPException):
            return error.status_code in self.retryable_errors
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return True
        return False


class WorkflowExecutor:
    """工作流執行器（帶重試）"""
    
    def __init__(self, db_session, retry_policy: RetryPolicy):
        self.db = db_session
        self.retry_policy = retry_policy
    
    async def execute_with_retry(
        self,
        execution_id: str,
        workflow_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        執行工作流，帶自動重試
        
        返回: 執行結果
        拋出: 如果所有重試失敗，拋出最後一個異常
        """
        last_exception = None
        
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                # 記錄重試開始
                if attempt > 0:
                    await self._log_retry_attempt(execution_id, attempt)
                
                # 執行工作流
                result = await workflow_func(*args, **kwargs)
                
                # 成功 - 記錄並返回
                if attempt > 0:
                    await self._log_retry_success(execution_id, attempt)
                
                return result
                
            except Exception as error:
                last_exception = error
                
                # 檢查是否可重試
                if not self.retry_policy.is_retryable_error(error):
                    # 不可重試錯誤 - 立即失敗
                    await self._log_non_retryable_error(execution_id, error)
                    raise
                
                # 檢查是否還有重試機會
                if attempt >= self.retry_policy.max_retries:
                    # 重試次數用盡 - 失敗
                    await self._log_retry_exhausted(execution_id, error, attempt)
                    raise
                
                # 計算延遲並等待
                delay = self.retry_policy.calculate_delay(attempt)
                next_retry_time = datetime.utcnow() + timedelta(seconds=delay)
                
                # 記錄重試計劃
                await self._log_retry_scheduled(
                    execution_id=execution_id,
                    attempt=attempt + 1,
                    error=error,
                    delay=delay,
                    next_retry_time=next_retry_time
                )
                
                # 更新執行狀態為「重試中」
                await self._update_execution_status(
                    execution_id=execution_id,
                    status="retrying",
                    retry_count=attempt + 1,
                    next_retry_at=next_retry_time
                )
                
                # 等待後重試
                await asyncio.sleep(delay)
        
        # 不應到達這裡，但以防萬一
        raise last_exception
    
    async def _log_retry_attempt(self, execution_id: str, attempt: int):
        """記錄重試開始"""
        logger.info(f"Execution {execution_id}: Starting retry attempt {attempt}")
    
    async def _log_retry_success(self, execution_id: str, attempt: int):
        """記錄重試成功"""
        logger.info(f"Execution {execution_id}: Retry succeeded on attempt {attempt}")
        
        # 更新執行狀態
        await self._update_execution_status(
            execution_id=execution_id,
            status="completed",
            retry_count=attempt
        )
    
    async def _log_non_retryable_error(self, execution_id: str, error: Exception):
        """記錄不可重試錯誤"""
        logger.error(
            f"Execution {execution_id}: Non-retryable error - {type(error).__name__}: {str(error)}"
        )
        
        # 記錄到數據庫
        retry_log = RetryLog(
            execution_id=execution_id,
            attempt=0,
            error_type=type(error).__name__,
            error_message=str(error),
            retryable=False,
            timestamp=datetime.utcnow()
        )
        self.db.add(retry_log)
        self.db.commit()
    
    async def _log_retry_exhausted(self, execution_id: str, error: Exception, attempts: int):
        """記錄重試次數用盡"""
        logger.error(
            f"Execution {execution_id}: Retry exhausted after {attempts} attempts - {str(error)}"
        )
        
        # 更新執行狀態為失敗
        await self._update_execution_status(
            execution_id=execution_id,
            status="failed",
            retry_count=attempts,
            error=str(error)
        )
    
    async def _log_retry_scheduled(
        self,
        execution_id: str,
        attempt: int,
        error: Exception,
        delay: float,
        next_retry_time: datetime
    ):
        """記錄重試計劃"""
        logger.warning(
            f"Execution {execution_id}: Scheduling retry {attempt} in {delay:.2f}s "
            f"(next retry at {next_retry_time.isoformat()}) - Error: {str(error)}"
        )
        
        # 記錄到數據庫
        retry_log = RetryLog(
            execution_id=execution_id,
            attempt=attempt,
            error_type=type(error).__name__,
            error_message=str(error),
            delay_seconds=delay,
            next_retry_at=next_retry_time,
            retryable=True,
            timestamp=datetime.utcnow()
        )
        self.db.add(retry_log)
        self.db.commit()
    
    async def _update_execution_status(
        self,
        execution_id: str,
        status: str,
        retry_count: int = 0,
        next_retry_at: Optional[datetime] = None,
        error: Optional[str] = None
    ):
        """更新執行狀態"""
        execution = self.db.query(Execution).filter_by(execution_id=execution_id).first()
        
        if execution:
            execution.status = status
            execution.retry_count = retry_count
            execution.next_retry_at = next_retry_at
            if error:
                execution.error = error
            
            self.db.commit()


# 使用示例
async def main():
    retry_policy = RetryPolicy(
        max_retries=5,
        initial_delay=2.0,
        backoff_strategy="exponential",
        jitter=True,
        retryable_errors=[429, 500, 502, 503, 504]
    )
    
    executor = WorkflowExecutor(db_session, retry_policy)
    
    try:
        result = await executor.execute_with_retry(
            execution_id="exec_abc123",
            workflow_func=run_customer_360_workflow,
            customer_id="CUST-5678"
        )
        print(f"Workflow succeeded: {result}")
    except Exception as error:
        print(f"Workflow failed after all retries: {error}")
```

**重試日誌數據庫表**:

```sql
CREATE TABLE retry_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    attempt INTEGER NOT NULL,  -- 第幾次重試 (0 = 首次執行)
    
    -- 錯誤信息
    error_type VARCHAR(100),  -- HTTPException, TimeoutError, etc.
    error_message TEXT,
    error_code VARCHAR(10),  -- HTTP 狀態碼 (429, 503, etc.)
    retryable BOOLEAN DEFAULT true,
    
    -- 重試配置
    delay_seconds DECIMAL(10,3),  -- 延遲秒數
    next_retry_at TIMESTAMP,  -- 下次重試時間
    
    -- 時間戳
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES executions(execution_id)
);

CREATE INDEX idx_retry_execution ON retry_logs(execution_id, attempt);
CREATE INDEX idx_retry_next_retry ON retry_logs(next_retry_at) WHERE next_retry_at IS NOT NULL;
```

**完成定義**:
- [ ] 實現指數退避重試邏輯（帶抖動）
- [ ] 錯誤分類（可重試 vs 不可重試）
- [ ] 重試狀態追蹤和日誌記錄
- [ ] UI 顯示重試配置和模擬器
- [ ] 數據庫表存儲重試日誌
- [ ] 單元測試（模擬各種錯誤場景）

---

### **US-F8-004: 死信隊列（DLQ）與手動干預**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** IT 管理員（Alex Chen）
- **我想要** 多次重試失敗的執行自動移至死信隊列（DLQ），並允許我手動查看、修復和重新執行
- **以便** 我可以處理持久性故障，而不會丟失任何執行請求

**驗收標準**:
1. ✅ **自動移至 DLQ**: 重試次數用盡後，自動移至 DLQ
2. ✅ **DLQ 列表**: UI 顯示所有 DLQ 中的執行（按時間排序）
3. ✅ **錯誤詳情**: 查看完整的錯誤堆棧、重試歷史、輸入數據
4. ✅ **手動重試**: 管理員可以修改輸入並重新執行
5. ✅ **批量操作**: 支持批量重試或批量刪除 DLQ 條目
6. ✅ **通知**: DLQ 新增條目時通過 Teams 通知管理員

**死信隊列 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 死信隊列 (DLQ)                                        [刷新] [批量操作 ▼]     │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 🔍 篩選器                                                                     │
│ [工作流: 全部 ▼] [錯誤類型: 全部 ▼] [日期: 最近 7 天 ▼]                    │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📊 概覽                                                                       │
│   總計: 23 個失敗執行 | 最舊: 5 天前 | 最新: 2 小時前                        │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🗂️ DLQ 條目列表                                                              │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ☐ 執行 ID: exec_abc123                                   [重試] [刪除]  │ │
│ │ ────────────────────────────────────────────────────────────────────────│ │
│ │ 工作流: customer_360_view                                               │ │
│ │ 失敗時間: 2025-11-19 12:30:45                                           │ │
│ │ 重試次數: 5/5 (全部失敗)                                                │ │
│ │ 最後錯誤: HTTPException 503 - ServiceNow API unavailable                │ │
│ │                                                                          │ │
│ │ [▼ 展開詳情]                                                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ☐ 執行 ID: exec_abc122                                   [重試] [刪除]  │ │
│ │ ────────────────────────────────────────────────────────────────────────│ │
│ │ 工作流: refund_decision                                                 │ │
│ │ 失敗時間: 2025-11-19 11:15:22                                           │ │
│ │ 重試次數: 5/5 (全部失敗)                                                │ │
│ │ 最後錯誤: OpenAI API Error 429 - Rate limit exceeded                    │ │
│ │                                                                          │ │
│ │ [▼ 展開詳情]                                                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ☐ 執行 ID: exec_abc121                                   [重試] [刪除]  │ │
│ │ ────────────────────────────────────────────────────────────────────────│ │
│ │ 工作流: it_password_reset                                               │ │
│ │ 失敗時間: 2025-11-18 16:45:10                                           │ │
│ │ 重試次數: 5/5 (全部失敗)                                                │ │
│ │ 最後錯誤: Active Directory connection timeout                           │ │
│ │                                                                          │ │
│ │ [▼ 展開詳情]                                                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [載入更多...]                                                                 │
└───────────────────────────────────────────────────────────────────────────────┘
```

**DLQ 條目詳情展開視圖**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ☑ 執行 ID: exec_abc123                                   [重試] [刪除]  │
│ ────────────────────────────────────────────────────────────────────────│
│ 工作流: customer_360_view                                               │
│ 失敗時間: 2025-11-19 12:30:45                                           │
│ 重試次數: 5/5 (全部失敗)                                                │
│ 最後錯誤: HTTPException 503 - ServiceNow API unavailable                │
│                                                                          │
│ [▲ 折疊詳情]                                                             │
│                                                                          │
│ ────────────────────────────────────────────────────────────────────────│
│                                                                          │
│ 📋 輸入數據                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ {                                                                    ││
│ │   "customer_id": "CUST-5678",                                        ││
│ │   "include_tickets": true,                                           ││
│ │   "include_crm": true,                                               ││
│ │   "include_documents": true                                          ││
│ │ }                                                                    ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│ 📊 重試歷史                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ 重試 1 (2s 後):  ❌ 503 Service Unavailable                          ││
│ │ 重試 2 (4s 後):  ❌ 503 Service Unavailable                          ││
│ │ 重試 3 (8s 後):  ❌ 503 Service Unavailable                          ││
│ │ 重試 4 (16s 後): ❌ 503 Service Unavailable                          ││
│ │ 重試 5 (32s 後): ❌ 503 Service Unavailable                          ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│ 🔍 錯誤詳情                                                              │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ 錯誤類型: HTTPException                                              ││
│ │ HTTP 狀態碼: 503                                                     ││
│ │ 錯誤消息: ServiceNow API is temporarily unavailable                  ││
│ │                                                                      ││
│ │ 堆棧追蹤:                                                            ││
│ │ Traceback (most recent call last):                                  ││
│ │   File "workflow_executor.py", line 123, in execute_step            ││
│ │     response = await servicenow_client.query(...)                   ││
│ │   File "servicenow_client.py", line 45, in query                    ││
│ │     raise HTTPException(status_code=503, detail="API unavailable")  ││
│ │ HTTPException: 503 Service Unavailable                              ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│ 💡 建議的修復                                                            │
│   • ServiceNow API 可能正在維護，稍後重試                               │
│   • 檢查 ServiceNow 服務健康狀況                                        │
│   • 如果問題持續，聯繫 ServiceNow 支持                                  │
│                                                                          │
│ ────────────────────────────────────────────────────────────────────────│
│                                                                          │
│ 🔧 手動重試選項                                                          │
│                                                                          │
│ [ ] 使用原始輸入重試                                                     │
│ [●] 修改輸入後重試 (編輯下方 JSON)                                      │
│                                                                          │
│ 修改後的輸入:                                                            │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ {                                                                    ││
│ │   "customer_id": "CUST-5678",                                        ││
│ │   "include_tickets": true,                                           ││
│ │   "include_crm": false,  ← 暫時跳過 CRM 查詢                         ││
│ │   "include_documents": true                                          ││
│ │ }                                                                    ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│ [取消] [確認重試]                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**DLQ 處理實現**:

```python
from datetime import datetime
from typing import Optional, Dict, Any

class DeadLetterQueueService:
    """死信隊列服務"""
    
    def __init__(self, db_session, notification_service):
        self.db = db_session
        self.notification_service = notification_service
    
    async def move_to_dlq(
        self,
        execution_id: str,
        final_error: Exception,
        retry_count: int,
        retry_history: list
    ):
        """
        將失敗的執行移至 DLQ
        
        參數:
            execution_id: 執行 ID
            final_error: 最後一次錯誤
            retry_count: 總重試次數
            retry_history: 重試歷史記錄
        """
        # 1. 獲取執行詳情
        execution = self.db.query(Execution).filter_by(
            execution_id=execution_id
        ).first()
        
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")
        
        # 2. 創建 DLQ 條目
        dlq_entry = DeadLetterQueueEntry(
            execution_id=execution_id,
            workflow_id=execution.workflow_id,
            workflow_name=execution.workflow.name,
            
            # 輸入數據
            input_data=execution.input_data,
            
            # 錯誤信息
            error_type=type(final_error).__name__,
            error_message=str(final_error),
            error_code=getattr(final_error, 'status_code', None),
            error_stacktrace=self._get_stacktrace(final_error),
            
            # 重試信息
            retry_count=retry_count,
            retry_history=retry_history,
            
            # 狀態
            status="pending",  # pending, retrying, resolved, deleted
            
            # 時間戳
            failed_at=execution.completed_at or datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(dlq_entry)
        self.db.commit()
        
        # 3. 更新執行狀態
        execution.status = "dlq"
        execution.dlq_entry_id = dlq_entry.id
        self.db.commit()
        
        # 4. 發送 Teams 通知
        await self.notification_service.send_dlq_alert(
            workflow_name=execution.workflow.name,
            execution_id=execution_id,
            error_message=str(final_error),
            dlq_entry_id=dlq_entry.id
        )
        
        logger.warning(
            f"Execution {execution_id} moved to DLQ after {retry_count} retries. "
            f"DLQ Entry ID: {dlq_entry.id}"
        )
        
        return dlq_entry
    
    async def list_dlq_entries(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """列出 DLQ 條目"""
        query = self.db.query(DeadLetterQueueEntry)
        
        if workflow_id:
            query = query.filter_by(workflow_id=workflow_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # 按失敗時間倒序
        query = query.order_by(DeadLetterQueueEntry.failed_at.desc())
        
        return query.limit(limit).offset(offset).all()
    
    async def retry_dlq_entry(
        self,
        dlq_entry_id: int,
        modified_input: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        手動重試 DLQ 條目
        
        返回: 新執行的 execution_id
        """
        # 1. 獲取 DLQ 條目
        dlq_entry = self.db.query(DeadLetterQueueEntry).filter_by(
            id=dlq_entry_id
        ).first()
        
        if not dlq_entry:
            raise ValueError(f"DLQ entry not found: {dlq_entry_id}")
        
        if dlq_entry.status != "pending":
            raise ValueError(f"DLQ entry is not pending: {dlq_entry.status}")
        
        # 2. 更新 DLQ 狀態為「重試中」
        dlq_entry.status = "retrying"
        dlq_entry.retry_attempted_at = datetime.utcnow()
        dlq_entry.retry_attempted_by = user_id
        self.db.commit()
        
        # 3. 創建新執行
        input_data = modified_input or dlq_entry.input_data
        
        new_execution_id = await self._create_execution(
            workflow_id=dlq_entry.workflow_id,
            input_data=input_data,
            trigger_type="manual_dlq_retry",
            triggered_by=user_id,
            parent_dlq_entry_id=dlq_entry_id
        )
        
        # 4. 觸發執行
        from workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor(self.db, retry_policy=None)  # 無重試（已在 DLQ）
        
        try:
            result = await executor.execute(new_execution_id)
            
            # 成功 - 標記 DLQ 為已解決
            dlq_entry.status = "resolved"
            dlq_entry.resolved_at = datetime.utcnow()
            dlq_entry.resolved_by = user_id
            dlq_entry.resolution_execution_id = new_execution_id
            self.db.commit()
            
            logger.info(f"DLQ entry {dlq_entry_id} resolved with execution {new_execution_id}")
            
        except Exception as error:
            # 仍然失敗 - DLQ 狀態回到 pending
            dlq_entry.status = "pending"
            self.db.commit()
            
            logger.error(f"DLQ retry {dlq_entry_id} failed: {error}")
            raise
        
        return new_execution_id
    
    async def delete_dlq_entry(self, dlq_entry_id: int, user_id: Optional[str] = None):
        """刪除 DLQ 條目（放棄重試）"""
        dlq_entry = self.db.query(DeadLetterQueueEntry).filter_by(
            id=dlq_entry_id
        ).first()
        
        if not dlq_entry:
            raise ValueError(f"DLQ entry not found: {dlq_entry_id}")
        
        # 軟刪除（標記為已刪除）
        dlq_entry.status = "deleted"
        dlq_entry.deleted_at = datetime.utcnow()
        dlq_entry.deleted_by = user_id
        self.db.commit()
        
        logger.info(f"DLQ entry {dlq_entry_id} deleted by {user_id}")
    
    def _get_stacktrace(self, error: Exception) -> str:
        """獲取錯誤堆棧追蹤"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))
```

**DLQ 數據庫表**:

```sql
CREATE TABLE dead_letter_queue (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) UNIQUE NOT NULL,
    workflow_id VARCHAR(100) NOT NULL,
    workflow_name VARCHAR(200),
    
    -- 輸入數據
    input_data JSONB NOT NULL,
    
    -- 錯誤信息
    error_type VARCHAR(100),
    error_message TEXT,
    error_code VARCHAR(10),
    error_stacktrace TEXT,
    
    -- 重試信息
    retry_count INTEGER DEFAULT 0,
    retry_history JSONB,  -- [{attempt: 1, error: "...", delay: 2.0}, ...]
    
    -- 狀態
    status VARCHAR(20) DEFAULT 'pending',  -- pending, retrying, resolved, deleted
    
    -- 手動重試
    retry_attempted_at TIMESTAMP,
    retry_attempted_by VARCHAR(100),
    resolution_execution_id VARCHAR(100),
    
    -- 解決/刪除
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(100),
    
    -- 時間戳
    failed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES executions(execution_id),
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);

CREATE INDEX idx_dlq_status ON dead_letter_queue(status, failed_at DESC);
CREATE INDEX idx_dlq_workflow ON dead_letter_queue(workflow_id, status);
```

**完成定義**:
- [ ] 自動移至 DLQ（重試用盡後）
- [ ] DLQ 列表 UI（篩選、排序）
- [ ] DLQ 條目詳情視圖（錯誤、重試歷史、輸入）
- [ ] 手動重試功能（可修改輸入）
- [ ] 批量操作（批量重試、批量刪除）
- [ ] Teams 通知（DLQ 新增條目）
- [ ] 數據庫表和索引

---

## 8.3 數據庫架構

完整的 F8 數據庫架構（整合所有用戶故事）:

```sql
-- 工作流觸發配置表
CREATE TABLE workflow_triggers (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(100) NOT NULL,
    
    -- 觸發類型
    trigger_type VARCHAR(20) NOT NULL,  -- cron, webhook, manual
    
    -- Cron 配置
    cron_expression VARCHAR(100),
    cron_timezone VARCHAR(50) DEFAULT 'UTC',
    cron_enabled BOOLEAN DEFAULT true,
    next_cron_execution TIMESTAMP,
    
    -- Webhook 配置
    webhook_id VARCHAR(50) UNIQUE,
    webhook_secret VARCHAR(200),
    webhook_authentication VARCHAR(20),  -- hmac, api_key, none
    webhook_filters JSONB,  -- [{json_path: "$.type", operator: "equals", value: "incident"}]
    
    -- 重試策略
    retry_enabled BOOLEAN DEFAULT true,
    max_retries INTEGER DEFAULT 5,
    initial_delay_seconds DECIMAL(10,3) DEFAULT 2.0,
    backoff_strategy VARCHAR(20) DEFAULT 'exponential',  -- exponential, fixed, linear
    jitter_enabled BOOLEAN DEFAULT true,
    retryable_error_codes INTEGER[],  -- [429, 500, 502, 503, 504]
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);

-- Webhook 請求日誌表
CREATE TABLE webhook_requests (
    id SERIAL PRIMARY KEY,
    webhook_id VARCHAR(50) NOT NULL,
    
    -- 請求信息
    source_ip VARCHAR(45),
    request_headers JSONB,
    request_body JSONB,
    
    -- 處理結果
    status VARCHAR(20),  -- triggered, filtered, auth_failed, error
    execution_id VARCHAR(100),  -- 如果觸發成功
    error_message TEXT,
    
    -- 時間戳
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (webhook_id) REFERENCES workflow_triggers(webhook_id)
);

-- 重試日誌表 (已在 US-F8-003 中定義)
CREATE TABLE retry_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    attempt INTEGER NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    error_code VARCHAR(10),
    retryable BOOLEAN DEFAULT true,
    delay_seconds DECIMAL(10,3),
    next_retry_at TIMESTAMP,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES executions(execution_id)
);

-- 死信隊列表 (已在 US-F8-004 中定義)
CREATE TABLE dead_letter_queue (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) UNIQUE NOT NULL,
    workflow_id VARCHAR(100) NOT NULL,
    workflow_name VARCHAR(200),
    input_data JSONB NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    error_code VARCHAR(10),
    error_stacktrace TEXT,
    retry_count INTEGER DEFAULT 0,
    retry_history JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    retry_attempted_at TIMESTAMP,
    retry_attempted_by VARCHAR(100),
    resolution_execution_id VARCHAR(100),
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(100),
    failed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES executions(execution_id),
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);

-- 索引
CREATE INDEX idx_triggers_workflow ON workflow_triggers(workflow_id);
CREATE INDEX idx_triggers_cron_next ON workflow_triggers(next_cron_execution) WHERE cron_enabled = true;
CREATE INDEX idx_webhook_requests_webhook ON webhook_requests(webhook_id, received_at DESC);
CREATE INDEX idx_retry_execution ON retry_logs(execution_id, attempt);
CREATE INDEX idx_dlq_status ON dead_letter_queue(status, failed_at DESC);
```

---

## 8.4 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **可靠性** | 觸發成功率 | ≥99.5% | 監控 Cron/Webhook 觸發 |
| | 重試成功率 | ≥80% 錯誤自動恢復 | 重試日誌分析 |
| **性能** | Webhook 響應時間 | <100ms（接收並入隊） | API 響應監控 |
| | DLQ 查詢性能 | <500ms（列出 50 條） | 數據庫查詢優化 |
| **可擴展性** | Cron 觸發器數量 | 支持 1000+ 工作流 | n8n 負載測試 |
| | 並發 Webhook 請求 | 500+ req/s | 負載測試 |
| **可觀察性** | 錯誤追蹤 | 100% 錯誤記錄 | 日誌完整性檢查 |
| | DLQ 通知延遲 | <30 秒 | Teams 通知監控 |

---

## 8.5 測試策略

**單元測試**:
- Cron 表達式解析和驗證
- Webhook 簽名驗證（HMAC-SHA256）
- 指數退避算法（含抖動）
- 錯誤分類邏輯（可重試 vs 不可重試）
- DLQ 條目創建和更新

**集成測試**:
- 端到端 Cron 觸發流程
- 端到端 Webhook 觸發流程（模擬 ServiceNow）
- 重試邏輯（模擬各種錯誤：429, 503, timeout）
- DLQ 手動重試流程

**負載測試**:
- 1000 個並發 Webhook 請求
- 100 個工作流同時重試

**混沌工程**:
- 模擬 ServiceNow API 間歇性故障
- 模擬 LLM API 限流（429）
- 模擬網絡超時

---

## 8.6 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| n8n 單點故障 | 中 | 高 | n8n 高可用部署（雙節點）+ 健康檢查 |
| 重試風暴（雪崩） | 低 | 中 | 抖動（Jitter）+ 最大並發重試限制 |
| DLQ 無限增長 | 中 | 中 | 自動歸檔（30 天後）+ 批量清理工具 |
| Webhook 簽名偽造 | 低 | 高 | HMAC-SHA256 + IP 白名單（可選） |

---

## 8.7 未來增強（MVP 後）

1. **優先級隊列**: 高優先級執行優先重試
2. **智能錯誤分類**: 使用 LLM 分析錯誤並建議修復
3. **DLQ 自動恢復**: 檢測外部服務恢復後自動重試 DLQ
4. **分佈式追蹤**: 集成 OpenTelemetry 追蹤跨服務調用
5. **電路斷路器**: 檢測到服務持續故障時自動暫停觸發

---

**✅ F8 完成**：n8n 觸發與錯誤處理功能規範已完整編寫（4 個用戶故事、數據庫架構、NFR、測試策略）。

---

## <a id="f9-prompt-management"></a>F9. 提示管理（YAML 模板）