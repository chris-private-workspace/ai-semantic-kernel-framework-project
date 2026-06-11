# Feature 12: 監控儀表板

**版本**: 1.0  
**日期**: 2025-11-19  
**狀態**: 草稿

---

## 📑 導航

- [← 返回附錄 B 索引](../../prd-appendix-b-features-8-14.md)
- [← 上一個: Feature 11 - Teams 通知](./feature-11-teams-notification.md)
- [→ 下一個: Feature 13 - 現代 Web UI](./feature-13-modern-web-ui.md)

---

## <a id="f12-monitoring-dashboard"></a>F12. 監控儀表板

**功能類別**: Observability (可觀察性)  
**優先級**: P0 (必須擁有)  
**估計開發時間**: 2 週  
**複雜度**: ⭐⭐⭐⭐

---

### 12.1 功能概述

**定義**:
F12（監控儀表板）提供**實時系統健康監控**，包括執行統計、性能指標、資源使用、錯誤趨勢、SLA 達成率等關鍵指標的可視化儀表板，支持自定義儀表板和告警閾值配置。

**為什麼重要**:
- **主動監控**: 在問題影響用戶前提前發現異常
- **性能優化**: 識別瓶頸，優化系統性能
- **容量規劃**: 根據趨勢預測資源需求
- **SLA 管理**: 追蹤服務水平協議達成情況

**核心能力**:
1. **實時指標**: 執行成功率、平均耗時、吞吐量、錯誤率
2. **資源監控**: CPU、內存、磁盤、數據庫連接池
3. **業務指標**: 各工作流執行次數、成本、用戶活躍度
4. **告警配置**: 自定義告警閾值（如錯誤率 >5%）
5. **趨勢分析**: 7 天/30 天趨勢圖表
6. **自定義儀表板**: 用戶可創建個性化儀表板

**業務價值**:
- **故障發現時間**: 從被動等待（2 小時）降至主動發現（5 分鐘）
- **系統可用性**: 從 95% 提升至 99.5%
- **運維效率**: 減少 60% 人工巡檢工作

**架構圖**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                    F12. 監控儀表板架構                                 │
└────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────┐
   │                      數據源                                     │
   │  • PostgreSQL (執行記錄)                                        │
   │  • Redis (實時指標)                                             │
   │  • Prometheus (系統指標)                                        │
   │  • Elasticsearch (日誌聚合)                                     │
   └───────────────────────┬─────────────────────────────────────────┘
                           │ 採集
                           ↓
   ┌─────────────────────────────────────────────────────────────────┐
   │                    指標聚合服務                                 │
   │  • 實時聚合（1 分鐘窗口）                                       │
   │  • 歷史聚合（1 小時/1 天窗口）                                  │
   │  • 計算 SLA、成功率、P95 延遲                                   │
   └───────┬─────────────────────────────┬───────────────────────────┘
           │ 寫入                        │ 查詢
           ↓                             ↓
   ┌──────────────┐            ┌──────────────────────────────────┐
   │ TimescaleDB  │            │      Dashboard API               │
   │ (時序數據庫) │            │  GET /api/metrics/realtime       │
   └──────────────┘            │  GET /api/metrics/history        │
                               └──────┬───────────────────────────┘
                                      │ 提供數據
                                      ↓
   ┌─────────────────────────────────────────────────────────────────┐
   │                        Web UI (React)                           │
   │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
   │  │ 執行概覽儀表板 │  │ 資源監控儀表板 │  │ 業務指標儀表板 │  │
   │  │ • 成功率      │  │ • CPU/內存     │  │ • 工作流排名  │  │
   │  │ • 吞吐量      │  │ • 數據庫連接   │  │ • 成本統計    │  │
   │  └────────────────┘  └────────────────┘  └────────────────┘  │
   └─────────────────────────────────────────────────────────────────┘
```

---

### 12.2 用戶故事

#### **US-F12-001: 執行概覽儀表板**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 運維工程師（Lisa Chen）
- **我想要** 查看實時執行統計（成功率、吞吐量、平均耗時）
- **以便** 我可以快速了解系統健康狀況

**驗收標準**:

1. ✅ **實時指標卡片**: 成功率、總執行次數、平均耗時、錯誤次數
2. ✅ **趨勢圖表**: 最近 24 小時執行次數趨勢（每小時）
3. ✅ **錯誤率趨勢**: 最近 7 天錯誤率變化
4. ✅ **Top 5 慢執行**: 耗時最長的 5 個執行
5. ✅ **Top 5 失敗工作流**: 失敗次數最多的 5 個工作流
6. ✅ **自動刷新**: 每 30 秒自動刷新數據

**儀表板 UI 設計**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 監控儀表板 > 執行概覽                                     最後更新: 剛剛       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 📊 實時指標 (最近 24 小時)                                                    │
│                                                                               │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌──────────┐│
│ │ 總執行次數      │  │ 成功率          │  │ 平均耗時        │  │ 錯誤次數 ││
│ │                 │  │                 │  │                 │  │          ││
│ │   1,234         │  │   96.5% ✓       │  │   3.2 秒        │  │   43     ││
│ │                 │  │                 │  │                 │  │          ││
│ │ ↑ 12% vs 昨天   │  │ ↓ 0.5% vs 昨天  │  │ ↓ 0.3s vs 昨天  │  │ ↑ 5      ││
│ └─────────────────┘  └─────────────────┘  └─────────────────┘  └──────────┘│
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📈 執行趨勢 (最近 24 小時)                          [1H] [6H] [24H] [7D]     │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 100 │                                                                   │ │
│ │     │                        ╭───╮                                      │ │
│ │  80 │                 ╭──────╯   ╰──╮                                  │ │
│ │     │          ╭──────╯              ╰───╮                             │ │
│ │  60 │     ╭────╯                          ╰─╮                          │ │
│ │     │ ╭───╯                                 ╰───╮                      │ │
│ │  40 │─╯                                         ╰─                     │ │
│ │     │                                                                   │ │
│ │  20 │                                                                   │ │
│ │     └─────────────────────────────────────────────────────────────────│ │
│ │       00:00   04:00   08:00   12:00   16:00   20:00   23:59          │ │
│ │                                                                         │ │
│ │       ─ 成功執行   ─ 失敗執行                                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ ⚠️ Top 5 慢執行                            🔥 Top 5 失敗工作流               │
│                                                                               │
│ ┌───────────────────────────────────┐    ┌───────────────────────────────┐ │
│ │ 1. customer_360_view              │    │ 1. refund_decision            │ │
│ │    執行: exec_abc123              │    │    失敗次數: 12               │ │
│ │    耗時: 45.3 秒                  │    │    錯誤率: 15.2%              │ │
│ │    [查看詳情]                     │    │    [查看錯誤]                 │ │
│ │                                   │    │                               │ │
│ │ 2. it_password_reset              │    │ 2. customer_360_view          │ │
│ │    執行: exec_def456              │    │    失敗次數: 8                │ │
│ │    耗時: 38.1 秒                  │    │    錯誤率: 6.5%               │ │
│ │    [查看詳情]                     │    │    [查看錯誤]                 │ │
│ │                                   │    │                               │ │
│ │ 3. leave_approval                 │    │ 3. it_password_reset          │ │
│ │    執行: exec_ghi789              │    │    失敗次數: 5                │ │
│ │    耗時: 32.5 秒                  │    │    錯誤率: 4.2%               │ │
│ │    [查看詳情]                     │    │    [查看錯誤]                 │ │
│ └───────────────────────────────────┘    └───────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

**FastAPI 實現**:

```python
from fastapi import APIRouter
from datetime import datetime, timedelta
from typing import List, Dict, Any

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/realtime")
async def get_realtime_metrics(hours: int = 24):
    """獲取實時指標"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # 1. 總執行次數
    total_executions = db.query(Execution).filter(
        Execution.created_at >= cutoff_time
    ).count()
    
    # 2. 成功率
    successful_count = db.query(Execution).filter(
        Execution.created_at >= cutoff_time,
        Execution.status == "completed"
    ).count()
    
    success_rate = (successful_count / total_executions * 100) if total_executions > 0 else 0
    
    # 3. 平均耗時
    avg_duration = db.query(
        func.avg(Execution.duration_seconds)
    ).filter(
        Execution.created_at >= cutoff_time
    ).scalar() or 0
    
    # 4. 錯誤次數
    error_count = db.query(Execution).filter(
        Execution.created_at >= cutoff_time,
        Execution.status == "failed"
    ).count()
    
    return {
        "total_executions": total_executions,
        "success_rate": round(success_rate, 1),
        "avg_duration_seconds": round(avg_duration, 1),
        "error_count": error_count
    }

@router.get("/trend")
async def get_execution_trend(hours: int = 24, interval: str = "1h"):
    """獲取執行趨勢"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # 按小時分組統計
    trend_data = db.query(
        func.date_trunc('hour', Execution.created_at).label('hour'),
        func.count(Execution.id).label('total'),
        func.count(Execution.id).filter(Execution.status == 'completed').label('success'),
        func.count(Execution.id).filter(Execution.status == 'failed').label('failed')
    ).filter(
        Execution.created_at >= cutoff_time
    ).group_by('hour').order_by('hour').all()
    
    return {
        "trend": [
            {
                "timestamp": row.hour.isoformat(),
                "total": row.total,
                "success": row.success,
                "failed": row.failed
            }
            for row in trend_data
        ]
    }

@router.get("/top-slow-executions")
async def get_top_slow_executions(limit: int = 5):
    """獲取最慢的執行"""
    
    slow_executions = db.query(Execution).order_by(
        Execution.duration_seconds.desc()
    ).limit(limit).all()
    
    return {
        "slow_executions": [
            {
                "execution_id": exec.execution_id,
                "workflow_name": exec.workflow.name,
                "duration_seconds": exec.duration_seconds,
                "created_at": exec.created_at.isoformat()
            }
            for exec in slow_executions
        ]
    }

@router.get("/top-failed-workflows")
async def get_top_failed_workflows(limit: int = 5):
    """獲取失敗最多的工作流"""
    
    failed_workflows = db.query(
        Workflow.workflow_id,
        Workflow.name,
        func.count(Execution.id).label('failed_count'),
        func.count(Execution.id).filter(Execution.status == 'failed') * 100.0 / func.count(Execution.id).label('error_rate')
    ).join(Execution).filter(
        Execution.status == 'failed'
    ).group_by(
        Workflow.workflow_id, Workflow.name
    ).order_by(
        func.count(Execution.id).desc()
    ).limit(limit).all()
    
    return {
        "failed_workflows": [
            {
                "workflow_id": row.workflow_id,
                "workflow_name": row.name,
                "failed_count": row.failed_count,
                "error_rate": round(row.error_rate, 1)
            }
            for row in failed_workflows
        ]
    }
```

**完成定義**:

- [ ] 實時指標 API
- [ ] 趨勢圖表數據 API
- [ ] Top N 慢執行查詢
- [ ] Top N 失敗工作流查詢
- [ ] 前端圖表組件（Recharts/Chart.js）
- [ ] 自動刷新機制

---

#### **US-F12-002: 資源監控儀表板**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐⭐

**用戶故事**:
- **作為** DevOps 工程師（Mark Lee）
- **我想要** 監控系統資源使用情況（CPU、內存、數據庫連接）
- **以便** 我可以在資源不足前進行擴容

**驗收標準**:

1. ✅ **CPU/內存使用率**: 實時顯示應用服務器 CPU 和內存使用率
2. ✅ **數據庫連接池**: 活躍連接數、空閒連接數、等待隊列
3. ✅ **Redis 緩存**: 命中率、內存使用、連接數
4. ✅ **磁盤空間**: 數據庫存儲、日誌存儲剩餘空間
5. ✅ **網絡流量**: 入站/出站流量統計
6. ✅ **告警配置**: CPU >80%、內存 >85%、磁盤 >90% 自動告警

**Python 實現（Prometheus 集成）**:

```python
from prometheus_client import Gauge, Counter, Histogram
import psutil
from sqlalchemy import create_engine

# Prometheus 指標定義
cpu_usage = Gauge('ipa_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('ipa_memory_usage_percent', 'Memory usage percentage')
db_connections_active = Gauge('ipa_db_connections_active', 'Active database connections')
redis_hit_rate = Gauge('ipa_redis_hit_rate', 'Redis cache hit rate')

class ResourceMonitor:
    """資源監控服務"""
    
    def __init__(self, db_engine, redis_client):
        self.db = db_engine
        self.redis = redis_client
    
    async def collect_metrics(self):
        """收集所有資源指標"""
        
        # 1. CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_usage.set(cpu_percent)
        
        # 2. 內存使用率
        memory = psutil.virtual_memory()
        memory_usage.set(memory.percent)
        
        # 3. 數據庫連接池
        db_pool_status = self.db.pool.status()
        db_connections_active.set(db_pool_status['checked_out'])
        
        # 4. Redis 緩存命中率
        redis_info = self.redis.info('stats')
        hits = redis_info.get('keyspace_hits', 0)
        misses = redis_info.get('keyspace_misses', 0)
        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
        redis_hit_rate.set(hit_rate)
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "db_connections": db_pool_status,
            "redis_hit_rate": hit_rate * 100
        }

@router.get("/resources")
async def get_resource_metrics():
    """獲取資源指標"""
    monitor = ResourceMonitor(db_engine, redis_client)
    return await monitor.collect_metrics()
```

**完成定義**:

- [ ] Prometheus 指標採集
- [ ] 資源監控 API
- [ ] 告警閾值配置
- [ ] 前端資源儀表板

---

#### **US-F12-003: 業務指標儀表板**

**優先級**: P1 (重要)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 產品經理（Michael Tan）
- **我想要** 查看業務指標（各工作流使用頻率、成本、用戶活躍度）
- **以便** 我可以評估產品價值和優化方向

**驗收標準**:

1. ✅ **工作流排行**: 執行次數最多的 Top 10 工作流
2. ✅ **成本統計**: LLM API 調用成本（按工作流分組）
3. ✅ **用戶活躍度**: 日活躍用戶 (DAU)、月活躍用戶 (MAU)
4. ✅ **執行時段分佈**: 24 小時執行熱力圖
5. ✅ **SLA 達成率**: 各工作流 SLA 達成率（目標 <5 秒）
6. ✅ **導出報告**: 支持導出為 Excel/PDF

**業務指標 API**:

```python
@router.get("/business/workflow-ranking")
async def get_workflow_ranking(days: int = 7, limit: int = 10):
    """工作流執行排行"""
    
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    ranking = db.query(
        Workflow.workflow_id,
        Workflow.name,
        func.count(Execution.id).label('execution_count'),
        func.avg(Execution.duration_seconds).label('avg_duration'),
        func.sum(Execution.llm_cost_usd).label('total_cost')
    ).join(Execution).filter(
        Execution.created_at >= cutoff_time
    ).group_by(
        Workflow.workflow_id, Workflow.name
    ).order_by(
        func.count(Execution.id).desc()
    ).limit(limit).all()
    
    return {
        "ranking": [
            {
                "workflow_id": row.workflow_id,
                "workflow_name": row.name,
                "execution_count": row.execution_count,
                "avg_duration": round(row.avg_duration, 1),
                "total_cost_usd": round(row.total_cost, 2)
            }
            for row in ranking
        ]
    }

@router.get("/business/user-activity")
async def get_user_activity():
    """用戶活躍度統計"""
    
    # DAU (最近 24 小時)
    dau = db.query(
        func.count(func.distinct(Execution.triggered_by))
    ).filter(
        Execution.created_at >= datetime.utcnow() - timedelta(days=1)
    ).scalar()
    
    # MAU (最近 30 天)
    mau = db.query(
        func.count(func.distinct(Execution.triggered_by))
    ).filter(
        Execution.created_at >= datetime.utcnow() - timedelta(days=30)
    ).scalar()
    
    return {
        "dau": dau,
        "mau": mau,
        "dau_mau_ratio": round(dau / mau * 100, 1) if mau > 0 else 0
    }

@router.get("/business/sla-compliance")
async def get_sla_compliance(sla_threshold_seconds: float = 5.0):
    """SLA 達成率"""
    
    compliance_by_workflow = db.query(
        Workflow.workflow_id,
        Workflow.name,
        func.count(Execution.id).label('total'),
        func.count(Execution.id).filter(
            Execution.duration_seconds <= sla_threshold_seconds
        ).label('within_sla')
    ).join(Execution).group_by(
        Workflow.workflow_id, Workflow.name
    ).all()
    
    return {
        "sla_compliance": [
            {
                "workflow_id": row.workflow_id,
                "workflow_name": row.name,
                "compliance_rate": round(row.within_sla / row.total * 100, 1) if row.total > 0 else 0,
                "total_executions": row.total
            }
            for row in compliance_by_workflow
        ]
    }
```

**完成定義**:

- [ ] 工作流排行 API
- [ ] 成本統計 API
- [ ] 用戶活躍度 API
- [ ] SLA 達成率計算
- [ ] Excel/PDF 報告導出

---

#### **US-F12-004: 自定義儀表板與告警配置**

**優先級**: P2 (次要)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐⭐

**用戶故事**:
- **作為** IT 管理員（Tom Wang）
- **我想要** 創建自定義儀表板並配置告警規則
- **以便** 我可以關注最重要的指標

**驗收標準**:

1. ✅ **自定義儀表板**: 用戶可添加/移除/排列指標卡片
2. ✅ **告警規則**: 配置告警條件（如錯誤率 >5%）
3. ✅ **告警渠道**: 支持 Teams、Email、Webhook
4. ✅ **告警靜音**: 臨時靜音特定告警（1 小時、24 小時）
5. ✅ **儀表板分享**: 生成公開鏈接供非登錄用戶查看
6. ✅ **儀表板模板**: 提供預設模板（運維視圖、業務視圖）

**告警配置示例**:

```yaml
# config/alert_rules.yaml
alert_rules:
  - name: "高錯誤率告警"
    enabled: true
    condition:
      metric: "error_rate"
      operator: ">"
      threshold: 5.0
      window_minutes: 5
    severity: "critical"
    channels:
      - type: "teams"
        webhook_url: "https://outlook.office.com/webhook/xxx"
      - type: "email"
        recipients: ["ops-team@company.com"]
    
  - name: "CPU 過高告警"
    enabled: true
    condition:
      metric: "cpu_usage_percent"
      operator: ">"
      threshold: 80.0
      window_minutes: 3
    severity: "warning"
    channels:
      - type: "teams"
        webhook_url: "https://outlook.office.com/webhook/xxx"
    
  - name: "DLQ 積壓告警"
    enabled: true
    condition:
      metric: "dlq_count"
      operator: ">"
      threshold: 10
      window_minutes: 10
    severity: "error"
    channels:
      - type: "teams"
        webhook_url: "https://outlook.office.com/webhook/xxx"
```

**完成定義**:

- [ ] 自定義儀表板編輯器
- [ ] 告警規則引擎
- [ ] 告警渠道集成
- [ ] 告警靜音功能
- [ ] 儀表板分享鏈接

---

### 12.3 數據庫架構

```sql
-- 指標時序數據表（TimescaleDB 分區表）
CREATE TABLE metrics_timeseries (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 4) NOT NULL,
    
    -- 標籤（用於過濾）
    labels JSONB,
    
    -- 聚合級別 (raw, 1h, 1d)
    aggregation_level VARCHAR(10) DEFAULT 'raw'
);

-- 轉換為 TimescaleDB 超表
SELECT create_hypertable('metrics_timeseries', 'time');

-- 索引
CREATE INDEX idx_metrics_name_time ON metrics_timeseries(metric_name, time DESC);
CREATE INDEX idx_metrics_labels ON metrics_timeseries USING GIN(labels);

-- 自定義儀表板配置表
CREATE TABLE dashboards (
    id SERIAL PRIMARY KEY,
    dashboard_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- 基本信息
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- 所有者
    owner_user_id VARCHAR(100),
    
    -- 配置
    layout JSONB NOT NULL,  -- 卡片佈局配置
    widgets JSONB NOT NULL,  -- 各卡片配置
    
    -- 分享
    is_public BOOLEAN DEFAULT false,
    public_token VARCHAR(100),
    
    -- 時間
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 告警規則表
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- 規則信息
    name VARCHAR(200) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    
    -- 條件
    metric_name VARCHAR(100) NOT NULL,
    operator VARCHAR(10) NOT NULL,  -- >, <, >=, <=, ==
    threshold DECIMAL(20, 4) NOT NULL,
    window_minutes INTEGER DEFAULT 5,
    
    -- 嚴重程度
    severity VARCHAR(20) NOT NULL,  -- info, warning, error, critical
    
    -- 告警渠道
    channels JSONB NOT NULL,
    
    -- 狀態
    last_triggered_at TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 告警歷史表
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(50) NOT NULL,
    
    -- 觸發信息
    triggered_at TIMESTAMP NOT NULL,
    metric_value DECIMAL(20, 4) NOT NULL,
    threshold DECIMAL(20, 4) NOT NULL,
    
    -- 通知狀態
    notification_sent BOOLEAN DEFAULT false,
    notification_channels JSONB,
    
    -- 恢復
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    
    FOREIGN KEY (rule_id) REFERENCES alert_rules(rule_id)
);

CREATE INDEX idx_alert_history_rule ON alert_history(rule_id, triggered_at DESC);
CREATE INDEX idx_alert_history_unresolved ON alert_history(resolved, triggered_at) WHERE NOT resolved;
```

---

### 12.4 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **性能** | 儀表板加載時間 | <2 秒 | 前端性能監控 |
| | 指標查詢延遲 | <500ms | API 響應時間 |
| **可擴展性** | 支持指標數量 | 1000+ 指標類型 | TimescaleDB 容量 |
| | 數據保留期 | 90 天高精度 + 1 年聚合 | 自動壓縮策略 |
| **可靠性** | 告警延遲 | <1 分鐘（從閾值觸發到通知） | 告警日誌 |
| | 告警準確率 | >99%（無誤報） | 告警歷史分析 |

---

### 12.5 測試策略

**單元測試**:

- 指標計算邏輯（成功率、平均值、百分位數）
- 告警規則匹配
- SLA 達成率計算

**集成測試**:

- 端到端指標採集 → 存儲 → 查詢
- 告警觸發 → Teams/Email 通知

**性能測試**:

- 100 萬條指標數據查詢性能
- 1000 個並發儀表板請求

**壓力測試**:

- 10000 指標/秒寫入 TimescaleDB

---

### 12.6 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| TimescaleDB 存儲空間不足 | 中 | 中 | 自動壓縮 + 數據歸檔 |
| 告警風暴（短時間大量告警） | 高 | 中 | 告警聚合 + 頻率限制 |
| Prometheus 採集失敗 | 低 | 中 | 降級至數據庫查詢 |
| 儀表板加載慢 | 中 | 低 | Redis 緩存 + 數據預聚合 |

---

### 12.7 未來增強（MVP 後）

1. **異常檢測**: 使用 ML 自動檢測指標異常（如突增/突降）
2. **預測性告警**: 根據趨勢預測資源不足（提前 1 小時告警）
3. **根因分析**: 自動分析錯誤的根本原因（關聯日誌、指標）
4. **移動端儀表板**: iOS/Android 原生應用
5. **語音告警**: 關鍵告警通過電話語音通知

---

**✅ F12 完成**：監控儀表板功能規範已完整編寫（4 個用戶故事、數據庫架構、NFR、測試策略）。

---
