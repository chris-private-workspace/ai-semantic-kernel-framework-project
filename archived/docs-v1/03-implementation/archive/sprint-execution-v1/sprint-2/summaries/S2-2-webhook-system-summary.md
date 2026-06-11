# S2-2: Webhook System - 實現摘要

**Story ID**: S2-2
**標題**: Webhook System
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-23

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| Webhook 註冊 | ✅ | CRUD API |
| 事件觸發 | ✅ | 自動發送通知 |
| 簽名驗證 | ✅ | HMAC-SHA256 |
| 重試機制 | ✅ | 指數退避 |

---

## 🔧 技術實現

### Webhook 數據模型

```python
class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(UUID, primary_key=True)
    name = Column(String(100))
    url = Column(String(500))           # 目標 URL
    secret = Column(String(100))        # 簽名密鑰
    events = Column(ARRAY(String))      # 訂閱的事件
    is_active = Column(Boolean)
    created_by = Column(UUID)
    created_at = Column(DateTime)
```

### 支援的事件類型

| 事件 | 說明 |
|------|------|
| workflow.created | 工作流創建 |
| workflow.updated | 工作流更新 |
| execution.started | 執行開始 |
| execution.completed | 執行完成 |
| execution.failed | 執行失敗 |
| checkpoint.pending | 等待審核 |

### Webhook 發送服務

```python
class WebhookService:
    """Webhook 服務"""

    async def send(self, webhook: Webhook, event: str, payload: dict):
        """發送 webhook"""
        # 1. 生成簽名
        signature = self._generate_signature(webhook.secret, payload)

        # 2. 發送請求
        headers = {
            "X-IPA-Signature": signature,
            "X-IPA-Event": event,
        }

        # 3. 處理重試
        await self._send_with_retry(webhook.url, payload, headers)

    def _generate_signature(self, secret: str, payload: dict) -> str:
        """生成 HMAC-SHA256 簽名"""
        body = json.dumps(payload, sort_keys=True)
        return hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
```

### API 端點

| 方法 | 路徑 | 用途 |
|------|------|------|
| POST | /webhooks | 創建 webhook |
| GET | /webhooks | 列表查詢 |
| GET | /webhooks/{id} | 獲取詳情 |
| PUT | /webhooks/{id} | 更新 webhook |
| DELETE | /webhooks/{id} | 刪除 webhook |
| POST | /webhooks/{id}/test | 測試 webhook |

---

## 📁 代碼位置

```
backend/src/
├── domain/webhooks/
│   ├── __init__.py
│   ├── service.py             # Webhook 服務
│   └── schemas.py             # 數據模型
└── api/v1/webhooks/
    └── routes.py              # Webhook API
```

---

## 🧪 驗證方式

```bash
# 創建 webhook
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "url": "https://example.com/hook", "events": ["execution.completed"]}'

# 測試 webhook
curl -X POST http://localhost:8000/api/v1/webhooks/{id}/test
```

---

## 📝 備註

- 使用 HMAC-SHA256 簽名確保安全
- 失敗自動重試 (最多 3 次)
- 支援批量事件訂閱

---

**生成日期**: 2025-11-26
