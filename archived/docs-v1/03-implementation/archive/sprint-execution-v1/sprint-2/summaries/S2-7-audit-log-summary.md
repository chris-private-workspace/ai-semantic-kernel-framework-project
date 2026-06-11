# S2-7: Audit Log Service - 實現摘要

**Story ID**: S2-7
**標題**: Audit Log Service
**Story Points**: 7
**狀態**: ✅ 已完成
**完成日期**: 2025-11-24

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| 審計日誌記錄 | ✅ | 所有操作自動記錄 |
| 日誌查詢 API | ✅ | 多條件搜索 |
| 日誌導出 | ✅ | CSV/JSON 格式 |
| 保留策略 | ✅ | 自動清理舊日誌 |

---

## 🔧 技術實現

### 審計日誌數據模型

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(UUID)
    user_email = Column(String(255))
    action = Column(String(50))          # create, read, update, delete
    resource_type = Column(String(50))   # workflow, execution, agent
    resource_id = Column(UUID)
    old_value = Column(JSONB)            # 變更前的值
    new_value = Column(JSONB)            # 變更後的值
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(String(36))      # 關聯請求 ID
    status = Column(String(20))          # success, failure
    error_message = Column(Text)
```

### AuditService

```python
class AuditService:
    """審計服務"""

    async def log(
        self,
        user: User,
        action: str,
        resource_type: str,
        resource_id: UUID,
        old_value: dict = None,
        new_value: dict = None,
        status: str = "success",
        request: Request = None
    ):
        """記錄審計日誌"""
        log = AuditLog(
            user_id=user.id,
            user_email=user.email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            status=status,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("User-Agent") if request else None,
        )
        await self.db.add(log)

    async def query(
        self,
        filters: AuditLogFilter,
        pagination: Pagination
    ) -> List[AuditLog]:
        """查詢審計日誌"""
        query = select(AuditLog)

        if filters.user_id:
            query = query.where(AuditLog.user_id == filters.user_id)
        if filters.action:
            query = query.where(AuditLog.action == filters.action)
        if filters.resource_type:
            query = query.where(AuditLog.resource_type == filters.resource_type)
        if filters.start_date:
            query = query.where(AuditLog.timestamp >= filters.start_date)
        if filters.end_date:
            query = query.where(AuditLog.timestamp <= filters.end_date)

        return await self.db.execute(query)

    async def export(self, filters: AuditLogFilter, format: str = "csv") -> bytes:
        """導出審計日誌"""
        logs = await self.query(filters, Pagination(limit=10000))
        if format == "csv":
            return self._to_csv(logs)
        return self._to_json(logs)
```

### API 端點

| 方法 | 路徑 | 用途 |
|------|------|------|
| GET | /audit-logs | 查詢日誌 |
| GET | /audit-logs/{id} | 獲取詳情 |
| GET | /audit-logs/export | 導出日誌 |
| GET | /audit-logs/stats | 統計信息 |

### 自動記錄裝飾器

```python
def audit_log(action: str, resource_type: str):
    """審計日誌裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 執行前記錄
            old_value = await get_resource_value(kwargs)

            result = await func(*args, **kwargs)

            # 執行後記錄
            await audit_service.log(
                action=action,
                resource_type=resource_type,
                old_value=old_value,
                new_value=result
            )
            return result
        return wrapper
    return decorator
```

---

## 📁 代碼位置

```
backend/src/
├── domain/audit/
│   ├── __init__.py
│   ├── service.py             # 審計服務
│   └── schemas.py             # 數據模型
├── api/v1/audit/
│   └── routes.py              # 審計 API
└── infrastructure/database/models/
    └── audit_log.py           # 數據庫模型
```

---

## 🧪 驗證方式

```bash
# 查詢審計日誌
curl "http://localhost:8000/api/v1/audit-logs?action=create&resource_type=workflow"

# 導出日誌
curl "http://localhost:8000/api/v1/audit-logs/export?format=csv" > audit.csv
```

---

## 📝 備註

- 日誌保留 90 天，自動清理
- 支援全文搜索
- 合規性報告支援

---

**生成日期**: 2025-11-26
