# S2-1: n8n Integration - 實現摘要

**Story ID**: S2-1
**標題**: n8n Integration
**Story Points**: 8
**狀態**: ✅ 已完成
**完成日期**: 2025-11-23

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| n8n 部署 | ✅ | Docker Compose 配置 |
| Webhook 觸發 | ✅ | IPA → n8n 觸發 |
| 回調接收 | ✅ | n8n → IPA 回調 |
| 工作流模板 | ✅ | 預設整合模板 |

---

## 🔧 技術實現

### n8n 配置

| 配置項 | 值 |
|-------|---|
| 版本 | n8n 1.x |
| 端口 | 5678 |
| Webhook URL | http://localhost:5678/webhook |
| 認證 | Basic Auth |

### 整合架構

```
IPA Platform                     n8n
    │                             │
    │ POST /webhook/trigger ───→  │ Webhook Node
    │                             │     ↓
    │                             │ Workflow Execution
    │                             │     ↓
    │ ←─── POST /api/callback ─── │ HTTP Request Node
    │                             │
```

### N8nClient 實現

```python
class N8nClient:
    """n8n 整合客戶端"""

    async def trigger_workflow(self, webhook_id: str, data: dict) -> dict:
        """觸發 n8n 工作流"""
        url = f"{self.base_url}/webhook/{webhook_id}"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            return response.json()

    async def get_workflow_status(self, execution_id: str) -> dict:
        """查詢執行狀態"""
        # 通過 n8n API 查詢
```

### 回調處理

```python
@router.post("/api/v1/n8n/callback")
async def n8n_callback(
    callback: N8nCallback,
    background_tasks: BackgroundTasks
):
    """處理 n8n 回調"""
    # 1. 驗證回調簽名
    # 2. 更新執行狀態
    # 3. 觸發後續流程
```

---

## 📁 代碼位置

```
backend/src/
├── integrations/n8n/
│   ├── __init__.py
│   ├── client.py              # N8n 客戶端
│   └── schemas.py             # 數據模型
└── api/v1/n8n/
    └── routes.py              # 回調 API
```

---

## 🧪 驗證方式

```bash
# 訪問 n8n UI
http://localhost:5678

# 測試 webhook 觸發
curl -X POST http://localhost:5678/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

---

## 📝 備註

- n8n 作為外部工作流引擎補充
- 支援雙向整合 (觸發和回調)
- Webhook 密鑰通過環境變量管理

---

**生成日期**: 2025-11-26
