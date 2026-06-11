# S33-2: 主動巡檢模式評估報告

**版本**: 1.0
**評估日期**: 2025-12-08
**狀態**: 部分實現

---

## 1. PRD 原始需求

根據 PRD 決策 F2「主動巡檢模式」，預期功能：

```
- Agent 自主發起定期巡檢任務
- 系統健康監控和異常檢測
- 預測性維護建議
- 自動化問題報告生成
```

---

## 2. 現有實現審計

### 2.1 Webhook 觸發服務 ✅ 完整 (被動式)

| 組件 | 位置 | 行數 | 功能 |
|------|------|------|------|
| WebhookTriggerService | `domain/triggers/webhook.py` | 655 | 被動觸發工作流 |
| Webhook API Routes | `api/v1/triggers/routes.py` | 425 | 觸發端點 |

**功能**:
- HMAC-SHA256 簽名驗證
- n8n 外部觸發支持
- 指數退避重試機制
- 成功/失敗回調通知
- 7 個 API 端點

### 2.2 指標收集器 ✅ 完整

| 組件 | 位置 | 行數 | 功能 |
|------|------|------|------|
| MetricCollector | `core/performance/metric_collector.py` | 716 | 系統/應用指標收集 |

**功能**:
- 系統指標: CPU, 記憶體, 磁碟, 網路
- 應用指標: 請求數, 延遲, 錯誤率, 快取命中率
- 閾值告警: min/max 閾值檢查
- 聚合功能: SUM, AVG, MIN, MAX, P50-P99
- 可配置收集間隔

### 2.3 死鎖檢測器 ✅ 完整

| 組件 | 位置 | 行數 | 功能 |
|------|------|------|------|
| DeadlockDetector | `domain/workflows/deadlock_detector.py` | 718 | 並行執行死鎖檢測 |
| TimeoutHandler | 同上 | - | 超時處理 |

**功能**:
- 等待圖分析 (Wait-for Graph)
- DFS 循環檢測
- 5 種解決策略 (CANCEL_YOUNGEST 等)
- 連續監控模式
- 超時處理

---

## 3. 缺失功能分析

### 3.1 任務調度器 ❌ 未實現

**預期**:
```python
# 定期任務調度
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour='*/4')
async def patrol_connectors():
    """每 4 小時巡檢連接器健康"""
    registry = get_registry()
    health = await registry.health_check_all()
    # 發現異常時自動觸發處理工作流

@scheduler.scheduled_job('cron', hour='0', minute='0')
async def daily_system_report():
    """每日系統健康報告"""
    # 收集指標、分析趨勢、生成報告
```

**現狀**: 無任何調度器實現

### 3.2 Agent 自主巡檢 ❌ 未實現

**預期**:
```python
class PatrolAgent:
    """主動巡檢 Agent"""

    async def run_patrol(self) -> PatrolReport:
        """執行巡檢任務"""
        # 1. 檢查系統健康
        # 2. 檢查連接器狀態
        # 3. 分析異常模式
        # 4. 生成建議

    async def detect_anomalies(self, metrics: List[MetricSample]) -> List[Anomaly]:
        """使用 LLM 分析異常"""

    async def generate_maintenance_recommendations(self) -> List[Recommendation]:
        """生成預測性維護建議"""
```

**現狀**: 無 Agent 自主巡檢能力

### 3.3 定期報告生成 ❌ 未實現

**預期**:
```python
class ReportGenerator:
    async def generate_daily_report(self) -> SystemHealthReport:
        """生成每日健康報告"""

    async def generate_weekly_summary(self) -> WeeklySummary:
        """生成每週摘要"""
```

**現狀**: 無自動報告生成

---

## 4. 差距總結

| 功能 | PRD 要求 | 實現狀態 | 差距 |
|------|----------|----------|------|
| Webhook 觸發 | 被動觸發 | ✅ 完整 | 無 |
| 指標收集 | 系統監控 | ✅ 完整 | 無 |
| 死鎖檢測 | 異常檢測 | ✅ 完整 | 無 |
| 閾值告警 | 問題通知 | ✅ 完整 | 無 |
| 任務調度器 | 定期任務 | ❌ 未實現 | 需 APScheduler 或 Celery |
| Agent 自主巡檢 | 主動式 | ❌ 未實現 | 需創建 PatrolAgent |
| 預測性維護 | LLM 分析 | ❌ 未實現 | 需創建分析服務 |
| 自動報告 | 定期生成 | ❌ 未實現 | 需創建報告生成器 |

---

## 5. 實現狀態評估

### 5.1 被動式監控 (已實現) ✅

```
外部事件 → Webhook Trigger → 工作流執行
          ↑
        n8n / 外部系統
```

### 5.2 主動式巡檢 (未實現) ❌

```
[預期架構]
Scheduler → PatrolAgent → 健康檢查 → 異常分析 → 通知/處理
           每 4 小時        ↓
                      LLM 分析
                          ↓
                    預測性維護建議
```

---

## 6. 建議行動

### 6.1 MVP 補充方案 (建議)

**最小實現** (5-8 Story Points):

```python
# 1. 添加 APScheduler
pip install apscheduler

# 2. 創建基本調度服務
# backend/src/domain/scheduler/service.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        # 定時健康檢查
        self.scheduler.add_job(
            self.patrol_connectors,
            'interval',
            hours=4,
            id='patrol_connectors'
        )

        # 每日報告
        self.scheduler.add_job(
            self.generate_daily_report,
            'cron',
            hour=0,
            minute=0,
            id='daily_report'
        )

        self.scheduler.start()

    async def patrol_connectors(self):
        """巡檢所有連接器"""
        registry = get_registry()
        health = await registry.health_check_all()

        # 發現問題時發送通知
        for name, result in health.items():
            if not result.success:
                await self.notify_issue(name, result)
```

### 6.2 完整方案 (Phase 7)

1. 創建 `PatrolAgent` Agent 類
2. 添加 LLM 異常分析功能
3. 創建預測性維護服務
4. 添加自動報告生成
5. 創建前端巡檢儀表板

**估算工作量**: 20-25 Story Points

---

## 7. 結論

**主動巡檢模式實現狀態**: **部分實現 (40%)**

- ✅ 被動觸發機制完整
- ✅ 指標收集和監控完整
- ✅ 死鎖檢測和告警完整
- ❌ 缺少任務調度器
- ❌ 缺少 Agent 自主巡檢
- ❌ 缺少預測性維護

**MVP 評估**:
- 如果 Stakeholder 接受「被動監控 + 外部調度 (n8n)」的方式，則可視為 MVP 達標
- 如果需要「Agent 自主巡檢」功能，需要補充開發

---

## 相關文件

- `backend/src/domain/triggers/webhook.py`
- `backend/src/api/v1/triggers/routes.py`
- `backend/src/core/performance/metric_collector.py`
- `backend/src/domain/workflows/deadlock_detector.py`
