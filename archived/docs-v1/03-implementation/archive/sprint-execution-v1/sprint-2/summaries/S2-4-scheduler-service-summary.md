# S2-4: Scheduler Service - 實現摘要

**Story ID**: S2-4
**標題**: Scheduler Service
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-24

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| APScheduler 整合 | ✅ | 異步排程器 |
| Cron 表達式支援 | ✅ | 標準 cron 格式 |
| 排程管理 API | ✅ | CRUD 操作 |
| 任務持久化 | ✅ | 數據庫存儲 |

---

## 🔧 技術實現

### 排程數據模型

```python
class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(UUID, primary_key=True)
    name = Column(String(100))
    workflow_id = Column(UUID, ForeignKey("workflows.id"))
    cron_expression = Column(String(100))    # "0 9 * * 1-5"
    timezone = Column(String(50))            # "Asia/Taipei"
    is_active = Column(Boolean)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    created_at = Column(DateTime)
```

### SchedulerService

```python
class SchedulerService:
    """排程服務"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            jobstores={
                'default': SQLAlchemyJobStore(url=DATABASE_URL)
            },
            timezone='Asia/Taipei'
        )

    async def add_job(self, job: ScheduledJob):
        """添加排程任務"""
        self.scheduler.add_job(
            self._execute_workflow,
            CronTrigger.from_crontab(job.cron_expression),
            id=str(job.id),
            args=[job.workflow_id],
            replace_existing=True
        )

    async def remove_job(self, job_id: str):
        """移除排程任務"""
        self.scheduler.remove_job(job_id)

    async def _execute_workflow(self, workflow_id: UUID):
        """執行工作流"""
        # 創建執行實例並啟動
```

### API 端點

| 方法 | 路徑 | 用途 |
|------|------|------|
| POST | /schedules | 創建排程 |
| GET | /schedules | 列表查詢 |
| GET | /schedules/{id} | 獲取詳情 |
| PUT | /schedules/{id} | 更新排程 |
| DELETE | /schedules/{id} | 刪除排程 |
| POST | /schedules/{id}/pause | 暫停排程 |
| POST | /schedules/{id}/resume | 恢復排程 |

### Cron 表達式範例

| 表達式 | 說明 |
|-------|------|
| `0 9 * * 1-5` | 週一至週五 9:00 |
| `0 */2 * * *` | 每 2 小時 |
| `0 0 1 * *` | 每月 1 日 |
| `*/15 * * * *` | 每 15 分鐘 |

---

## 📁 代碼位置

```
backend/src/
├── domain/scheduler/
│   ├── __init__.py
│   ├── service.py             # 排程服務
│   └── schemas.py             # 數據模型
└── api/v1/schedules/
    └── routes.py              # 排程 API
```

---

## 🧪 驗證方式

```bash
# 創建排程
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Report",
    "workflow_id": "xxx",
    "cron_expression": "0 9 * * *"
  }'

# 查看排程狀態
curl http://localhost:8000/api/v1/schedules
```

---

## 📝 備註

- 使用 APScheduler 異步版本
- 任務持久化到數據庫，重啟後自動恢復
- 生產環境可遷移到 Azure Functions Timer

---

**生成日期**: 2025-11-26
