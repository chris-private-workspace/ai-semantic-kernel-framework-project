# S2-3: Teams Notification - 實現摘要

**Story ID**: S2-3
**標題**: Microsoft Teams Notification
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-23

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| Teams Webhook 整合 | ✅ | Incoming Webhook |
| 通知模板 | ✅ | Adaptive Cards |
| 事件觸發 | ✅ | 自動發送通知 |
| 配置管理 | ✅ | 多 Channel 支援 |

---

## 🔧 技術實現

### 通知類型

| 類型 | 說明 | 顏色 |
|------|------|------|
| execution_started | 執行開始 | 🔵 藍色 |
| execution_completed | 執行成功 | 🟢 綠色 |
| execution_failed | 執行失敗 | 🔴 紅色 |
| checkpoint_pending | 待審核 | 🟡 黃色 |

### TeamsNotificationService

```python
class TeamsNotificationService:
    """Teams 通知服務"""

    async def send_notification(
        self,
        channel: TeamsChannel,
        notification_type: str,
        data: dict
    ):
        """發送 Teams 通知"""
        card = self._build_adaptive_card(notification_type, data)
        await self._send_to_webhook(channel.webhook_url, card)

    def _build_adaptive_card(self, type: str, data: dict) -> dict:
        """構建 Adaptive Card"""
        return {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {"type": "TextBlock", "text": data["title"], "weight": "bolder"},
                        {"type": "TextBlock", "text": data["message"]},
                    ],
                    "actions": [
                        {"type": "Action.OpenUrl", "title": "查看詳情", "url": data["url"]}
                    ]
                }
            }]
        }
```

### Channel 配置

```python
class TeamsChannel(Base):
    __tablename__ = "teams_channels"

    id = Column(UUID, primary_key=True)
    name = Column(String(100))
    webhook_url = Column(EncryptedString(1000))  # 加密存儲
    notification_types = Column(ARRAY(String))    # 訂閱的通知類型
    is_active = Column(Boolean)
```

---

## 📁 代碼位置

```
backend/src/
├── integrations/teams/
│   ├── __init__.py
│   ├── service.py             # Teams 服務
│   ├── cards.py               # Adaptive Card 模板
│   └── schemas.py             # 數據模型
└── api/v1/teams/
    └── routes.py              # Teams 配置 API
```

---

## 🧪 驗證方式

```bash
# 發送測試通知
curl -X POST http://localhost:8000/api/v1/teams/channels/{id}/test

# 手動發送到 Teams
curl -X POST "YOUR_TEAMS_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test notification from IPA Platform"}'
```

---

## 📝 備註

- Webhook URL 加密存儲
- 支援 Adaptive Cards 豐富格式
- 可配置每個 Channel 接收的通知類型

---

**生成日期**: 2025-11-26
