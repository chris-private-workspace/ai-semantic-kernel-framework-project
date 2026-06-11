# Feature 11: Teams 通知

**版本**: 1.0  
**日期**: 2025-11-19  
**狀態**: 草稿

---

## 📑 導航

- [← 返回附錄 B 索引](../../prd-appendix-b-features-8-14.md)
- [← 上一個: Feature 10 - 審計追蹤](./feature-10-audit-trail.md)
- [→ 下一個: Feature 12 - 監控儀表板](./feature-12-monitoring-dashboard.md)

---

## <a id="f11-teams-notification"></a>F11. Teams 通知

**功能類別**: Observability (可觀察性)  
**優先級**: P0 (必須擁有)  
**估計開發時間**: 1 週  
**複雜度**: ⭐⭐

---

### 11.1 功能概述

**定義**:
F11（Teams 通知）提供與 **Microsoft Teams 的深度集成**，自動發送工作流執行結果、錯誤告警、DLQ 通知、系統事件至指定的 Teams 頻道，支持 Adaptive Cards 富文本格式和快捷操作按鈕。

**為什麼重要**:
- **主動通知**: 團隊無需主動查看系統，關鍵事件自動推送
- **快速響應**: 錯誤告警在 30 秒內到達 Teams，減少響應時間 80%
- **協作便利**: 在 Teams 中直接討論問題，無需切換工具
- **企業標準**: Teams 是企業標準協作工具，符合 IT 策略

**核心能力**:
1. **多場景通知**: 執行成功/失敗、DLQ 告警、系統事件
2. **Adaptive Cards**: 富文本卡片，包含按鈕、圖表、快捷操作
3. **可配置路由**: 不同事件路由至不同頻道（如錯誤→運維頻道）
4. **快捷操作**: 直接在 Teams 中重試執行、查看詳情、靜默告警
5. **通知聚合**: 相同錯誤聚合為一條通知（避免刷屏）
6. **靜音規則**: 支持靜音期（如非工作時間）

**業務價值**:
- **響應速度**: 從 2 小時降至 5 分鐘（主動通知 vs 被動查看）
- **協作效率**: 問題討論時間減少 60%（無需切換工具）
- **告警疲勞**: 聚合通知減少 70% 消息量

**架構圖**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      F11. Teams 通知架構                               │
└────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────┐
   │                      事件源（觸發器）                           │
   │  • 執行完成（成功/失敗）                                        │
   │  • DLQ 新增條目                                                 │
   │  • 系統事件（服務啟動/停止）                                    │
   │  • 審計告警（可疑操作）                                         │
   └───────────────────────┬─────────────────────────────────────────┘
                           │ 發布事件
                           ↓
   ┌─────────────────────────────────────────────────────────────────┐
   │                    通知路由服務                                 │
   │  • 根據事件類型選擇通知模板                                     │
   │  • 應用靜音規則（工作時間、頻率限制）                           │
   │  • 聚合相同錯誤（5 分鐘窗口）                                   │
   └───────┬─────────────────────────────┬───────────────────────────┘
           │                             │
           ↓                             ↓
   ┌──────────────┐            ┌──────────────┐
   │ Teams Webhook│            │ 通知日誌     │
   │ Connector    │            │ (PostgreSQL) │
   └──────┬───────┘            └──────────────┘
          │
          ↓
   ┌──────────────────────────────────────────────────────────────────┐
   │                      Microsoft Teams                             │
   │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
   │  │ #ops-alerts    │  │ #cs-workflows  │  │ #it-support    │   │
   │  │ (運維告警)     │  │ (客服工作流)   │  │ (IT 支持)      │   │
   │  └────────────────┘  └────────────────┘  └────────────────┘   │
   └──────────────────────────────────────────────────────────────────┘
```

---

### 11.2 用戶故事

#### **US-F11-001: 執行結果通知（成功/失敗）**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐

**用戶故事**:
- **作為** 運維工程師（Lisa Chen）
- **我想要** 在工作流執行失敗時收到 Teams 通知
- **以便** 我可以立即響應問題，而不是被動等待用戶報告

**驗收標準**:

1. ✅ **失敗通知**: 執行失敗後 30 秒內發送 Teams 消息
2. ✅ **Adaptive Card**: 使用 Adaptive Card 格式（包含執行 ID、錯誤、耗時）
3. ✅ **快捷操作**: 包含「查看詳情」「重試執行」「靜音 1 小時」按鈕
4. ✅ **成功通知（可選）**: 可配置是否通知成功執行
5. ✅ **頻道路由**: 根據工作流配置發送至指定頻道
6. ✅ **@提及**: 支持 @特定用戶或團隊

**Teams Adaptive Card 示例（失敗通知）**:

```json
{
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "Container",
      "style": "attention",
      "items": [
        {
          "type": "ColumnSet",
          "columns": [
            {
              "type": "Column",
              "width": "auto",
              "items": [
                {
                  "type": "Image",
                  "url": "https://cdn.example.com/icons/error.png",
                  "size": "small"
                }
              ]
            },
            {
              "type": "Column",
              "width": "stretch",
              "items": [
                {
                  "type": "TextBlock",
                  "text": "工作流執行失敗",
                  "weight": "bolder",
                  "size": "large",
                  "color": "attention"
                },
                {
                  "type": "TextBlock",
                  "text": "Customer 360 View Workflow",
                  "size": "medium",
                  "spacing": "none"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "type": "FactSet",
      "facts": [
        {
          "title": "執行 ID:",
          "value": "exec_abc123"
        },
        {
          "title": "工作流:",
          "value": "customer_360_view"
        },
        {
          "title": "觸發方式:",
          "value": "Webhook (ServiceNow)"
        },
        {
          "title": "失敗時間:",
          "value": "2025-11-19 14:30:45"
        },
        {
          "title": "執行耗時:",
          "value": "12.3 秒"
        },
        {
          "title": "錯誤類型:",
          "value": "HTTPException 503"
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "**錯誤詳情:**",
      "weight": "bolder",
      "spacing": "medium"
    },
    {
      "type": "TextBlock",
      "text": "ServiceNow API is temporarily unavailable. Connection timed out after 30 seconds.",
      "wrap": true,
      "color": "attention"
    },
    {
      "type": "TextBlock",
      "text": "**影響範圍:**",
      "weight": "bolder",
      "spacing": "medium"
    },
    {
      "type": "TextBlock",
      "text": "• 客戶 ID: CUST-5678\n• 相關票務: TICKET-1234\n• 重試次數: 5/5 (已用盡)",
      "wrap": true
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "查看詳情",
      "url": "https://ipa.company.com/executions/exec_abc123"
    },
    {
      "type": "Action.Http",
      "title": "重試執行",
      "method": "POST",
      "url": "https://ipa.company.com/api/executions/exec_abc123/retry",
      "headers": [
        {
          "name": "Authorization",
          "value": "Bearer {{TEAMS_BOT_TOKEN}}"
        }
      ]
    },
    {
      "type": "Action.Http",
      "title": "靜音 1 小時",
      "method": "POST",
      "url": "https://ipa.company.com/api/notifications/mute",
      "body": "{\"execution_id\": \"exec_abc123\", \"duration_hours\": 1}"
    }
  ]
}
```

**Python 實現**:

```python
import requests
from typing import Dict, Any, Optional

class TeamsNotificationService:
    """Teams 通知服務"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_execution_failure(
        self,
        execution_id: str,
        workflow_name: str,
        trigger_type: str,
        error_type: str,
        error_message: str,
        duration_seconds: float,
        retry_count: int,
        max_retries: int,
        customer_id: Optional[str] = None
    ):
        """發送執行失敗通知"""
        
        # 構建 Adaptive Card
        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            self._build_header("工作流執行失敗", workflow_name, "attention"),
                            self._build_fact_set({
                                "執行 ID": execution_id,
                                "工作流": workflow_name,
                                "觸發方式": trigger_type,
                                "失敗時間": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                "執行耗時": f"{duration_seconds:.1f} 秒",
                                "錯誤類型": error_type
                            }),
                            {
                                "type": "TextBlock",
                                "text": f"**錯誤詳情:**\n{error_message}",
                                "wrap": True,
                                "color": "attention"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"**重試狀態:** {retry_count}/{max_retries}",
                                "wrap": True
                            }
                        ],
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "查看詳情",
                                "url": f"https://ipa.company.com/executions/{execution_id}"
                            },
                            {
                                "type": "Action.Http",
                                "title": "重試執行",
                                "method": "POST",
                                "url": f"https://ipa.company.com/api/executions/{execution_id}/retry"
                            }
                        ]
                    }
                }
            ]
        }
        
        # 發送至 Teams
        response = requests.post(self.webhook_url, json=card)
        
        if response.status_code != 200:
            logger.error(f"Failed to send Teams notification: {response.text}")
            raise Exception(f"Teams notification failed: {response.status_code}")
        
        # 記錄通知日誌
        await self._log_notification(
            notification_type="execution_failure",
            execution_id=execution_id,
            status="sent"
        )
    
    def _build_header(self, title: str, subtitle: str, style: str = "default") -> Dict:
        """構建卡片頭部"""
        return {
            "type": "Container",
            "style": style,
            "items": [
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "bolder",
                    "size": "large",
                    "color": "attention" if style == "attention" else "default"
                },
                {
                    "type": "TextBlock",
                    "text": subtitle,
                    "size": "medium",
                    "spacing": "none"
                }
            ]
        }
    
    def _build_fact_set(self, facts: Dict[str, str]) -> Dict:
        """構建事實集合"""
        return {
            "type": "FactSet",
            "facts": [
                {"title": f"{key}:", "value": value}
                for key, value in facts.items()
            ]
        }
```

**完成定義**:

- [ ] Adaptive Card 模板生成
- [ ] Teams Webhook 集成
- [ ] 快捷操作按鈕實現
- [ ] 頻道路由配置
- [ ] 通知日誌記錄

---

#### **US-F11-002: DLQ 告警通知**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 1 天  
**複雜度**: ⭐⭐

**用戶故事**:
- **作為** 運維工程師（Alex Chen）
- **我想要** 在執行進入 DLQ 時收到 Teams 告警
- **以便** 我可以及時處理持久性故障

**驗收標準**:

1. ✅ **DLQ 告警**: 執行移至 DLQ 後立即發送通知
2. ✅ **聚合告警**: 5 分鐘內相同錯誤聚合為一條（避免刷屏）
3. ✅ **嚴重程度**: 使用紅色主題標識高優先級
4. ✅ **快捷操作**: 包含「查看 DLQ」「手動重試」按鈕
5. ✅ **@提及**: 自動 @on-call 工程師
6. ✅ **統計信息**: 顯示當前 DLQ 總數

**DLQ 告警 Adaptive Card**:

```json
{
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "Container",
      "style": "attention",
      "items": [
        {
          "type": "TextBlock",
          "text": "⚠️ 執行進入死信隊列 (DLQ)",
          "weight": "bolder",
          "size": "large",
          "color": "attention"
        }
      ]
    },
    {
      "type": "FactSet",
      "facts": [
        {
          "title": "執行 ID:",
          "value": "exec_abc123"
        },
        {
          "title": "工作流:",
          "value": "customer_360_view"
        },
        {
          "title": "重試次數:",
          "value": "5/5 (已用盡)"
        },
        {
          "title": "最後錯誤:",
          "value": "ServiceNow API unavailable (503)"
        },
        {
          "title": "進入 DLQ 時間:",
          "value": "2025-11-19 14:35:22"
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "**當前 DLQ 狀態:**",
      "weight": "bolder"
    },
    {
      "type": "TextBlock",
      "text": "• 總計: 12 個失敗執行\n• 最舊: 3 天前\n• 需要人工干預",
      "wrap": true,
      "color": "attention"
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "查看 DLQ 隊列",
      "url": "https://ipa.company.com/dlq"
    },
    {
      "type": "Action.OpenUrl",
      "title": "手動重試",
      "url": "https://ipa.company.com/dlq/exec_abc123/retry"
    }
  ],
  "msteams": {
    "entities": [
      {
        "type": "mention",
        "text": "<at>Lisa Chen</at>",
        "mentioned": {
          "id": "lisa.chen@company.com",
          "name": "Lisa Chen"
        }
      }
    ]
  }
}
```

**完成定義**:

- [ ] DLQ 事件監聽
- [ ] 告警聚合邏輯（5 分鐘窗口）
- [ ] @提及功能
- [ ] DLQ 統計信息收集

---

#### **US-F11-003: 通知路由與靜音規則**

**優先級**: P1 (重要)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** IT 管理員（Tom Wang）
- **我想要** 配置不同類型通知發送至不同 Teams 頻道，並設置靜音規則
- **以便** 我可以避免告警疲勞，確保通知到達正確的團隊

**驗收標準**:

1. ✅ **頻道路由**: 不同事件類型路由至不同頻道
2. ✅ **靜音時段**: 配置靜音時段（如非工作時間僅發送 Critical）
3. ✅ **頻率限制**: 相同告警 10 分鐘內最多發送 3 次
4. ✅ **優先級過濾**: 只通知 P0/P1 工作流的錯誤
5. ✅ **動態配置**: 通過 YAML 配置文件管理路由規則
6. ✅ **通知測試**: UI 提供測試按鈕，驗證配置正確

**通知路由配置**:

```yaml
# config/teams_notification_routing.yaml
notification_routing:
  - name: "運維告警"
    webhook_url: "https://outlook.office.com/webhook/xxx/IncomingWebhook/yyy"
    channels: ["#ops-alerts"]
    event_types:
      - "execution.failed"
      - "dlq.entry_added"
      - "system.error"
    filters:
      priority: ["P0", "P1"]
      severity: ["error", "critical"]
    
  - name: "客服工作流"
    webhook_url: "https://outlook.office.com/webhook/aaa/IncomingWebhook/bbb"
    channels: ["#cs-workflows"]
    event_types:
      - "execution.completed"
      - "execution.failed"
    filters:
      workflow_category: ["customer_service"]
    
  - name: "IT 支持"
    webhook_url: "https://outlook.office.com/webhook/ccc/IncomingWebhook/ddd"
    channels: ["#it-support"]
    event_types:
      - "execution.completed"
    filters:
      workflow_category: ["it_support"]

mute_rules:
  - name: "非工作時間靜音"
    enabled: true
    schedule:
      timezone: "Asia/Taipei"
      mute_periods:
        - days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
          time_ranges: ["18:00-09:00"]  # 晚上 6 點至早上 9 點
        - days: ["Saturday", "Sunday"]
          time_ranges: ["00:00-23:59"]  # 週末全天
    exceptions:
      severity: ["critical"]  # Critical 事件仍然通知
  
  - name: "頻率限制"
    enabled: true
    rate_limit:
      window_minutes: 10
      max_notifications: 3
    aggregation:
      enabled: true
      window_minutes: 5
      group_by: ["workflow_id", "error_type"]
```

**Python 實現**:

```python
from datetime import datetime, time
import yaml
from typing import List, Dict, Any

class NotificationRouter:
    """通知路由器"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.routing_rules = self.config["notification_routing"]
        self.mute_rules = self.config["mute_rules"]
    
    async def route_notification(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """路由通知到對應頻道"""
        
        # 1. 檢查靜音規則
        if self._is_muted(event_type, event_data):
            logger.info(f"Notification muted: {event_type}")
            return
        
        # 2. 查找匹配的路由規則
        for rule in self.routing_rules:
            if self._matches_rule(event_type, event_data, rule):
                # 3. 發送通知
                await self._send_to_webhook(
                    webhook_url=rule["webhook_url"],
                    event_type=event_type,
                    event_data=event_data
                )
    
    def _is_muted(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """檢查是否被靜音"""
        
        for rule in self.mute_rules:
            if not rule.get("enabled", True):
                continue
            
            # 檢查時段靜音
            if "schedule" in rule:
                if self._is_in_mute_period(rule["schedule"]):
                    # 檢查例外情況
                    exceptions = rule.get("exceptions", {})
                    severity = event_data.get("severity")
                    
                    if severity not in exceptions.get("severity", []):
                        return True
            
            # 檢查頻率限制
            if "rate_limit" in rule:
                if self._exceeds_rate_limit(event_type, event_data, rule["rate_limit"]):
                    return True
        
        return False
    
    def _is_in_mute_period(self, schedule: Dict) -> bool:
        """檢查當前時間是否在靜音時段"""
        import pytz
        
        tz = pytz.timezone(schedule["timezone"])
        now = datetime.now(tz)
        
        current_day = now.strftime("%A")
        current_time = now.time()
        
        for period in schedule["mute_periods"]:
            if current_day in period["days"]:
                for time_range in period["time_ranges"]:
                    start_str, end_str = time_range.split("-")
                    start_time = time.fromisoformat(start_str)
                    end_time = time.fromisoformat(end_str)
                    
                    if start_time <= current_time <= end_time:
                        return True
        
        return False
```

**完成定義**:

- [ ] YAML 配置解析
- [ ] 路由規則匹配
- [ ] 靜音時段檢查
- [ ] 頻率限制實現
- [ ] 通知聚合邏輯

---

#### **US-F11-004: 通知統計與健康監控**

**優先級**: P2 (次要)  
**估計開發時間**: 1.5 天  
**複雜度**: ⭐⭐

**用戶故事**:
- **作為** 運維經理（Michael Tan）
- **我想要** 查看通知發送統計和失敗率
- **以便** 我可以監控通知系統的健康狀況

**驗收標準**:

1. ✅ **發送統計**: 每日/每週發送量統計
2. ✅ **成功率**: 通知發送成功率（目標 ≥99%）
3. ✅ **延遲監控**: 從事件發生到通知發送的延遲
4. ✅ **失敗重試**: 發送失敗自動重試 3 次
5. ✅ **告警**: 通知系統異常時通過備用渠道告警（Email）
6. ✅ **儀表板**: Web UI 顯示通知統計

**完成定義**:

- [ ] 通知日誌統計
- [ ] 成功率計算
- [ ] 延遲監控
- [ ] 失敗重試邏輯
- [ ] 儀表板 API

---

### 11.3 數據庫架構

```sql
-- 通知日誌表
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    
    -- 通知信息
    notification_type VARCHAR(50) NOT NULL,  -- execution_failure, dlq_alert, etc.
    event_type VARCHAR(100) NOT NULL,
    
    -- 關聯資源
    execution_id VARCHAR(100),
    workflow_id VARCHAR(100),
    
    -- Teams 信息
    webhook_url VARCHAR(500) NOT NULL,
    channel_name VARCHAR(100),
    
    -- 發送狀態
    status VARCHAR(20) NOT NULL,  -- sent, failed, muted
    retry_count INTEGER DEFAULT 0,
    
    -- 卡片內容
    card_content JSONB,
    
    -- 時間
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    
    -- 錯誤
    error TEXT
);

CREATE INDEX idx_notification_status ON notification_logs(status, created_at DESC);
CREATE INDEX idx_notification_execution ON notification_logs(execution_id);
CREATE INDEX idx_notification_type ON notification_logs(notification_type, created_at DESC);

-- 通知聚合表（防刷屏）
CREATE TABLE notification_aggregations (
    id SERIAL PRIMARY KEY,
    
    -- 聚合鍵
    aggregation_key VARCHAR(200) NOT NULL,  -- workflow_id + error_type
    
    -- 聚合統計
    count INTEGER DEFAULT 1,
    first_occurrence TIMESTAMP NOT NULL,
    last_occurrence TIMESTAMP NOT NULL,
    
    -- 是否已通知
    notified BOOLEAN DEFAULT false,
    notified_at TIMESTAMP,
    
    UNIQUE(aggregation_key)
);

CREATE INDEX idx_aggregation_key ON notification_aggregations(aggregation_key, notified);
```

---

### 11.4 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **性能** | 通知延遲 | <30 秒（從事件到發送） | APM 監控 |
| **可靠性** | 發送成功率 | ≥99% | 通知日誌統計 |
| **可用性** | Teams 故障降級 | 自動切換至 Email | 健康檢查 |

---

### 11.5 測試策略

**單元測試**:
- Adaptive Card 生成
- 路由規則匹配
- 靜音規則檢查

**集成測試**:
- 端到端通知發送（模擬 Teams Webhook）
- 快捷操作按鈕功能

**性能測試**:
- 1000 條/分鐘通知發送

---

### 11.6 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| Teams Webhook 失效 | 中 | 中 | 自動檢測 + Email 降級 |
| 告警刷屏 | 高 | 中 | 聚合 + 頻率限制 |
| 通知延遲 | 低 | 低 | 異步隊列 + 監控 |

---

**✅ F11 完成**：Teams 通知功能規範已完整編寫（4 個用戶故事、數據庫架構、NFR、測試策略）。

---
