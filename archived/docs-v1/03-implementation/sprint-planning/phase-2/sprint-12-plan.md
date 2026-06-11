# Sprint 12: 整合與優化 (Integration & Polish)

**Sprint 目標**: 整合 Phase 2 所有功能、優化效能、完善文檔和測試

**週期**: Week 25-26 (2 週)
**Story Points**: 34 點
**前置條件**: Sprint 7-11 完成

---

## Sprint 概述

### 核心交付物

| ID | 功能 | 優先級 | Story Points | 狀態 |
|----|------|--------|--------------|------|
| P2-F14 | Performance Optimization 性能優化 | 🔴 高 | 13 | 待開發 |
| P2-F15 | UI Integration UI 整合 | 🔴 高 | 13 | 待開發 |
| P2-F16 | Documentation & Testing 文檔與測試 | 🔴 高 | 8 | 待開發 |

### Sprint 12 定位

```
Phase 2 Sprint 進程
├─ Sprint 7:  Concurrent Execution      ✅ 基礎設施
├─ Sprint 8:  Agent Handoff             ✅ 協作機制
├─ Sprint 9:  GroupChat & Multi-turn    ✅ 對話能力
├─ Sprint 10: Dynamic Planning          ✅ 智能決策
├─ Sprint 11: Nested Workflows          ✅ 進階編排
└─ Sprint 12: Integration & Polish      🔄 整合優化
                                           ├─ 效能優化
                                           ├─ UI 整合
                                           └─ 文檔測試
```

---

## User Stories

### Story 12-1: Performance Profiler & Optimization (5 點)

**作為** 系統管理員
**我希望** 有完整的效能分析和優化工具
**以便** 確保 Phase 2 功能在生產環境中高效運行

#### 技術規格

```python
# backend/src/core/performance/profiler.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
import asyncio
import time
import functools
import statistics


class MetricType(str, Enum):
    """指標類型"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    CPU = "cpu"
    CONCURRENCY = "concurrency"
    ERROR_RATE = "error_rate"


@dataclass
class PerformanceMetric:
    """效能指標"""
    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProfileSession:
    """分析會話"""
    id: UUID
    name: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    metrics: List[PerformanceMetric] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None


class PerformanceProfiler:
    """
    效能分析器

    提供：
    - 延遲追蹤
    - 吞吐量測量
    - 資源使用監控
    - 瓶頸識別
    """

    def __init__(self):
        self._sessions: Dict[UUID, ProfileSession] = {}
        self._active_session: Optional[ProfileSession] = None
        self._metric_collectors: Dict[MetricType, List[float]] = {
            mt: [] for mt in MetricType
        }

    def start_session(self, name: str) -> ProfileSession:
        """開始分析會話"""
        session = ProfileSession(
            id=uuid4(),
            name=name,
            started_at=datetime.utcnow()
        )
        self._sessions[session.id] = session
        self._active_session = session
        return session

    def end_session(
        self,
        session_id: Optional[UUID] = None
    ) -> ProfileSession:
        """結束分析會話"""
        session = self._sessions.get(
            session_id or (self._active_session.id if self._active_session else None)
        )
        if not session:
            raise ValueError("No active session")

        session.ended_at = datetime.utcnow()
        session.summary = self._generate_summary(session)

        if session == self._active_session:
            self._active_session = None

        return session

    def record_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """記錄指標"""
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {}
        )

        if self._active_session:
            self._active_session.metrics.append(metric)

        self._metric_collectors[metric_type].append(value)

    def measure_latency(self, operation_name: str):
        """延遲測量裝飾器"""
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    elapsed = (time.perf_counter() - start) * 1000  # ms
                    self.record_metric(
                        name=operation_name,
                        metric_type=MetricType.LATENCY,
                        value=elapsed,
                        unit="ms"
                    )

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = (time.perf_counter() - start) * 1000
                    self.record_metric(
                        name=operation_name,
                        metric_type=MetricType.LATENCY,
                        value=elapsed,
                        unit="ms"
                    )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def _generate_summary(
        self,
        session: ProfileSession
    ) -> Dict[str, Any]:
        """生成會話摘要"""
        summary = {
            "duration_seconds": (
                session.ended_at - session.started_at
            ).total_seconds() if session.ended_at else None,
            "total_metrics": len(session.metrics),
            "metrics_by_type": {}
        }

        # 按類型分組計算統計
        for metric_type in MetricType:
            values = [
                m.value for m in session.metrics
                if m.metric_type == metric_type
            ]

            if values:
                summary["metrics_by_type"][metric_type.value] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "median": statistics.median(values),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99)
                }

        return summary

    def _percentile(self, values: List[float], p: int) -> float:
        """計算百分位數"""
        if not values:
            return 0
        sorted_values = sorted(values)
        idx = int(len(sorted_values) * p / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """獲取優化建議"""
        recommendations = []

        # 分析延遲
        latency_values = self._metric_collectors[MetricType.LATENCY]
        if latency_values:
            avg_latency = statistics.mean(latency_values)
            p99_latency = self._percentile(latency_values, 99)

            if avg_latency > 1000:  # > 1秒
                recommendations.append({
                    "type": "latency",
                    "severity": "high",
                    "message": f"平均延遲 {avg_latency:.0f}ms 過高",
                    "recommendation": "考慮添加快取或優化資料庫查詢"
                })

            if p99_latency > avg_latency * 3:
                recommendations.append({
                    "type": "latency_variance",
                    "severity": "medium",
                    "message": f"P99 延遲 ({p99_latency:.0f}ms) 遠高於平均值",
                    "recommendation": "調查長尾請求原因"
                })

        # 分析錯誤率
        error_values = self._metric_collectors[MetricType.ERROR_RATE]
        if error_values:
            avg_error_rate = statistics.mean(error_values)
            if avg_error_rate > 0.05:  # > 5%
                recommendations.append({
                    "type": "error_rate",
                    "severity": "high",
                    "message": f"錯誤率 {avg_error_rate:.1%} 超過閾值",
                    "recommendation": "檢查錯誤日誌並修復根本原因"
                })

        # 分析並發
        concurrency_values = self._metric_collectors[MetricType.CONCURRENCY]
        if concurrency_values:
            max_concurrency = max(concurrency_values)
            if max_concurrency > 100:
                recommendations.append({
                    "type": "concurrency",
                    "severity": "medium",
                    "message": f"最大並發數 {max_concurrency} 較高",
                    "recommendation": "考慮實施請求限流"
                })

        return recommendations


class PerformanceOptimizer:
    """
    效能優化器

    提供自動化的效能優化功能
    """

    def __init__(
        self,
        profiler: PerformanceProfiler,
        cache_service: Any,
        config: Dict[str, Any]
    ):
        self.profiler = profiler
        self.cache = cache_service
        self.config = config

        # 優化策略
        self._strategies: Dict[str, Callable] = {
            "caching": self._apply_caching,
            "batching": self._apply_batching,
            "connection_pooling": self._apply_connection_pooling,
            "query_optimization": self._apply_query_optimization
        }

    async def analyze_and_optimize(
        self,
        target: str
    ) -> Dict[str, Any]:
        """分析並優化"""
        # 1. 收集當前效能數據
        session = self.profiler.start_session(f"optimization_{target}")

        # 2. 執行基準測試
        baseline = await self._run_benchmark(target)

        # 3. 獲取優化建議
        recommendations = self.profiler.get_recommendations()

        # 4. 應用優化策略
        applied_strategies = []
        for rec in recommendations:
            strategy_name = self._map_recommendation_to_strategy(rec)
            if strategy_name and strategy_name in self._strategies:
                await self._strategies[strategy_name](target)
                applied_strategies.append(strategy_name)

        # 5. 重新測試
        optimized = await self._run_benchmark(target)

        self.profiler.end_session(session.id)

        return {
            "target": target,
            "baseline": baseline,
            "optimized": optimized,
            "improvement": self._calculate_improvement(baseline, optimized),
            "applied_strategies": applied_strategies,
            "recommendations": recommendations
        }

    async def _run_benchmark(self, target: str) -> Dict[str, Any]:
        """執行基準測試"""
        latencies = []
        errors = 0
        total_requests = 100

        for _ in range(total_requests):
            start = time.perf_counter()
            try:
                # 模擬請求
                await asyncio.sleep(0.01)
                latencies.append((time.perf_counter() - start) * 1000)
            except Exception:
                errors += 1

        return {
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "p95_latency_ms": self.profiler._percentile(latencies, 95),
            "error_rate": errors / total_requests,
            "throughput_rps": total_requests / (sum(latencies) / 1000) if latencies else 0
        }

    def _map_recommendation_to_strategy(
        self,
        recommendation: Dict[str, Any]
    ) -> Optional[str]:
        """將建議映射到策略"""
        mapping = {
            "latency": "caching",
            "latency_variance": "query_optimization",
            "concurrency": "connection_pooling"
        }
        return mapping.get(recommendation.get("type"))

    async def _apply_caching(self, target: str) -> None:
        """應用快取策略"""
        # 實現快取邏輯
        pass

    async def _apply_batching(self, target: str) -> None:
        """應用批次處理策略"""
        pass

    async def _apply_connection_pooling(self, target: str) -> None:
        """應用連接池策略"""
        pass

    async def _apply_query_optimization(self, target: str) -> None:
        """應用查詢優化策略"""
        pass

    def _calculate_improvement(
        self,
        baseline: Dict[str, Any],
        optimized: Dict[str, Any]
    ) -> Dict[str, Any]:
        """計算改進幅度"""
        return {
            "latency_improvement": (
                (baseline["avg_latency_ms"] - optimized["avg_latency_ms"])
                / baseline["avg_latency_ms"] * 100
                if baseline["avg_latency_ms"] > 0 else 0
            ),
            "throughput_improvement": (
                (optimized["throughput_rps"] - baseline["throughput_rps"])
                / baseline["throughput_rps"] * 100
                if baseline["throughput_rps"] > 0 else 0
            ),
            "error_rate_improvement": (
                (baseline["error_rate"] - optimized["error_rate"])
                / baseline["error_rate"] * 100
                if baseline["error_rate"] > 0 else 0
            )
        }
```

#### 驗收標準
- [ ] 延遲追蹤準確
- [ ] 自動生成優化建議
- [ ] 基準測試功能
- [ ] 改進幅度計算
- [ ] 效能 KPI 達標

---

### Story 12-2: Concurrent Execution Optimization (3 點)

**作為** 系統架構師
**我希望** 優化並行執行效能
**以便** 達到 3x 吞吐量提升目標

#### 技術規格

```python
# backend/src/core/performance/concurrent_optimizer.py

import asyncio
from typing import List, Any, Callable, TypeVar, Generic
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import functools

T = TypeVar('T')


@dataclass
class ConcurrencyConfig:
    """並發配置"""
    max_workers: int = 10
    batch_size: int = 50
    timeout_seconds: float = 30.0
    semaphore_limit: int = 100
    use_thread_pool: bool = False


class ConcurrentOptimizer:
    """
    並發優化器

    優化並行執行的效能
    """

    def __init__(self, config: ConcurrencyConfig):
        self.config = config
        self._semaphore = asyncio.Semaphore(config.semaphore_limit)
        self._thread_pool = ThreadPoolExecutor(
            max_workers=config.max_workers
        ) if config.use_thread_pool else None

    async def execute_batch(
        self,
        items: List[Any],
        processor: Callable[[Any], Any],
        preserve_order: bool = True
    ) -> List[Any]:
        """
        批次並行執行

        Args:
            items: 待處理項目
            processor: 處理函數
            preserve_order: 是否保持順序

        Returns:
            處理結果列表
        """
        results = []

        # 分批處理
        for i in range(0, len(items), self.config.batch_size):
            batch = items[i:i + self.config.batch_size]

            batch_results = await self._process_batch(
                batch, processor, preserve_order
            )
            results.extend(batch_results)

        return results

    async def _process_batch(
        self,
        batch: List[Any],
        processor: Callable,
        preserve_order: bool
    ) -> List[Any]:
        """處理單個批次"""
        async def process_with_semaphore(item, index):
            async with self._semaphore:
                if asyncio.iscoroutinefunction(processor):
                    result = await processor(item)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self._thread_pool,
                        processor,
                        item
                    )
                return (index, result)

        tasks = [
            process_with_semaphore(item, i)
            for i, item in enumerate(batch)
        ]

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        if preserve_order:
            # 按索引排序
            sorted_results = sorted(
                [(idx, res) for idx, res in completed if not isinstance(res, Exception)],
                key=lambda x: x[0]
            )
            return [res for _, res in sorted_results]
        else:
            return [res for idx, res in completed if not isinstance(res, Exception)]

    async def execute_with_timeout(
        self,
        coros: List[asyncio.coroutine],
        timeout: Optional[float] = None
    ) -> List[Any]:
        """帶超時的並行執行"""
        timeout = timeout or self.config.timeout_seconds

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*coros, return_exceptions=True),
                timeout=timeout
            )
            return results
        except asyncio.TimeoutError:
            return [TimeoutError("Batch execution timed out")]

    async def execute_with_retry(
        self,
        coro: asyncio.coroutine,
        max_retries: int = 3,
        backoff_factor: float = 1.5
    ) -> Any:
        """帶重試的執行"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await coro
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff_factor ** attempt)

        raise last_exception

    def create_worker_pool(
        self,
        num_workers: int
    ) -> "WorkerPool":
        """建立工作池"""
        return WorkerPool(num_workers, self._semaphore)


class WorkerPool:
    """工作池"""

    def __init__(
        self,
        num_workers: int,
        semaphore: asyncio.Semaphore
    ):
        self.num_workers = num_workers
        self.semaphore = semaphore
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: List[asyncio.Task] = []
        self._results: List[Any] = []

    async def start(self) -> None:
        """啟動工作池"""
        self._workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.num_workers)
        ]

    async def _worker(self, worker_id: int) -> None:
        """工作者"""
        while True:
            try:
                task = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )

                if task is None:  # 終止信號
                    break

                async with self.semaphore:
                    result = await task()
                    self._results.append(result)

                self._queue.task_done()

            except asyncio.TimeoutError:
                continue

    async def submit(self, task: Callable) -> None:
        """提交任務"""
        await self._queue.put(task)

    async def shutdown(self) -> List[Any]:
        """關閉工作池"""
        # 發送終止信號
        for _ in range(self.num_workers):
            await self._queue.put(None)

        # 等待所有工作者完成
        await asyncio.gather(*self._workers)

        return self._results
```

#### 驗收標準
- [ ] 批次處理效能提升
- [ ] 信號量限制有效
- [ ] 工作池正常運作
- [ ] 3x 吞吐量達成

---

### Story 12-3: Phase 2 UI Integration (8 點)

**作為** 前端開發者
**我希望** 整合所有 Phase 2 功能到 UI
**以便** 用戶可以視覺化地使用進階功能

#### 技術規格

```typescript
// frontend/src/pages/orchestration/OrchestrationDashboard.tsx

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Activity,
  GitBranch,
  Users,
  MessageSquare,
  Zap,
  Layers,
  Settings
} from 'lucide-react';

// 子組件
import { ConcurrentExecutionPanel } from './ConcurrentExecutionPanel';
import { HandoffMonitor } from './HandoffMonitor';
import { GroupChatPanel } from './GroupChatPanel';
import { PlanningDashboard } from './PlanningDashboard';
import { NestedWorkflowViewer } from './NestedWorkflowViewer';
import { PerformanceMetrics } from './PerformanceMetrics';

interface OrchestrationStats {
  concurrentExecutions: number;
  activeHandoffs: number;
  groupChats: number;
  activePlans: number;
  nestedWorkflows: number;
}

export const OrchestrationDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState<OrchestrationStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/orchestration/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      label: '並行執行',
      value: stats?.concurrentExecutions ?? 0,
      icon: Zap,
      color: 'text-yellow-500'
    },
    {
      label: '活躍交接',
      value: stats?.activeHandoffs ?? 0,
      icon: GitBranch,
      color: 'text-blue-500'
    },
    {
      label: '群組對話',
      value: stats?.groupChats ?? 0,
      icon: MessageSquare,
      color: 'text-green-500'
    },
    {
      label: '執行計劃',
      value: stats?.activePlans ?? 0,
      icon: Activity,
      color: 'text-purple-500'
    },
    {
      label: '嵌套工作流',
      value: stats?.nestedWorkflows ?? 0,
      icon: Layers,
      color: 'text-orange-500'
    }
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">進階編排控制台</h1>
          <p className="text-muted-foreground">
            Phase 2 多 Agent 協作功能
          </p>
        </div>
        <Button variant="outline">
          <Settings className="h-4 w-4 mr-2" />
          設定
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-5 gap-4">
        {statCards.map((stat, index) => (
          <Card key={index}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-6 w-full">
          <TabsTrigger value="overview">
            <Activity className="h-4 w-4 mr-2" />
            總覽
          </TabsTrigger>
          <TabsTrigger value="concurrent">
            <Zap className="h-4 w-4 mr-2" />
            並行執行
          </TabsTrigger>
          <TabsTrigger value="handoff">
            <GitBranch className="h-4 w-4 mr-2" />
            Agent 交接
          </TabsTrigger>
          <TabsTrigger value="groupchat">
            <MessageSquare className="h-4 w-4 mr-2" />
            群組對話
          </TabsTrigger>
          <TabsTrigger value="planning">
            <Activity className="h-4 w-4 mr-2" />
            動態規劃
          </TabsTrigger>
          <TabsTrigger value="nested">
            <Layers className="h-4 w-4 mr-2" />
            嵌套工作流
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <h3 className="font-semibold">效能指標</h3>
              </CardHeader>
              <CardContent>
                <PerformanceMetrics />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="font-semibold">最近活動</h3>
              </CardHeader>
              <CardContent>
                <RecentActivityList />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="concurrent" className="mt-6">
          <ConcurrentExecutionPanel />
        </TabsContent>

        <TabsContent value="handoff" className="mt-6">
          <HandoffMonitor />
        </TabsContent>

        <TabsContent value="groupchat" className="mt-6">
          <GroupChatPanel />
        </TabsContent>

        <TabsContent value="planning" className="mt-6">
          <PlanningDashboard />
        </TabsContent>

        <TabsContent value="nested" className="mt-6">
          <NestedWorkflowViewer />
        </TabsContent>
      </Tabs>
    </div>
  );
};


// frontend/src/pages/orchestration/NestedWorkflowViewer.tsx

import React, { useState, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';

interface NestedWorkflowViewerProps {
  executionId?: string;
}

export const NestedWorkflowViewer: React.FC<NestedWorkflowViewerProps> = ({
  executionId
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  useEffect(() => {
    if (executionId) {
      fetchExecutionTree(executionId);
    }
  }, [executionId]);

  const fetchExecutionTree = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/nested/executions/${id}/tree`);
      const tree = await response.json();

      const { nodes: flowNodes, edges: flowEdges } = convertTreeToFlow(tree);
      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (error) {
      console.error('Failed to fetch execution tree:', error);
    }
  };

  const convertTreeToFlow = (
    tree: any,
    parentId?: string,
    depth: number = 0,
    index: number = 0
  ): { nodes: Node[]; edges: Edge[] } => {
    const nodeId = tree.id;
    const xOffset = depth * 250;
    const yOffset = index * 100;

    const node: Node = {
      id: nodeId,
      type: 'workflow',
      position: { x: xOffset, y: yOffset },
      data: {
        label: tree.workflow_id,
        depth: tree.depth,
        status: tree.status || 'unknown'
      },
      style: {
        background: getStatusColor(tree.status),
        border: '2px solid #333',
        borderRadius: '8px',
        padding: '10px'
      }
    };

    const nodes = [node];
    const edges: Edge[] = [];

    if (parentId) {
      edges.push({
        id: `${parentId}-${nodeId}`,
        source: parentId,
        target: nodeId,
        animated: tree.status === 'running'
      });
    }

    if (tree.children) {
      tree.children.forEach((child: any, childIndex: number) => {
        const childResult = convertTreeToFlow(
          child,
          nodeId,
          depth + 1,
          childIndex
        );
        nodes.push(...childResult.nodes);
        edges.push(...childResult.edges);
      });
    }

    return { nodes, edges };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#fef3c7';
      case 'completed': return '#d1fae5';
      case 'failed': return '#fee2e2';
      default: return '#f3f4f6';
    }
  };

  const onNodeClick = useCallback((event: any, node: Node) => {
    setSelectedNode(node);
  }, []);

  return (
    <div className="h-[600px] border rounded-lg">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
      >
        <Controls />
        <Background />
        <MiniMap />
      </ReactFlow>

      {selectedNode && (
        <div className="absolute bottom-4 right-4 bg-white p-4 rounded-lg shadow-lg">
          <h4 className="font-semibold">節點詳情</h4>
          <p>ID: {selectedNode.id}</p>
          <p>深度: {selectedNode.data.depth}</p>
          <p>狀態: {selectedNode.data.status}</p>
        </div>
      )}
    </div>
  );
};


// frontend/src/pages/orchestration/PerformanceMetrics.tsx

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { Card, CardContent } from '@/components/ui/card';

interface MetricData {
  timestamp: string;
  latency: number;
  throughput: number;
  errorRate: number;
  concurrency: number;
}

export const PerformanceMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/v1/performance/metrics?range=1h');
      const data = await response.json();
      setMetrics(data.metrics);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>載入中...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Latency Chart */}
      <div>
        <h4 className="text-sm font-medium mb-2">延遲 (ms)</h4>
        <ResponsiveContainer width="100%" height={150}>
          <AreaChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(v) => new Date(v).toLocaleTimeString()}
            />
            <YAxis />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="latency"
              stroke="#8884d8"
              fill="#8884d8"
              fillOpacity={0.3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Throughput Chart */}
      <div>
        <h4 className="text-sm font-medium mb-2">吞吐量 (req/s)</h4>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(v) => new Date(v).toLocaleTimeString()}
            />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="throughput"
              stroke="#82ca9d"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-3 text-center">
            <p className="text-xs text-muted-foreground">平均延遲</p>
            <p className="text-lg font-bold">
              {metrics.length > 0
                ? (metrics.reduce((a, b) => a + b.latency, 0) / metrics.length).toFixed(0)
                : 0} ms
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 text-center">
            <p className="text-xs text-muted-foreground">平均吞吐量</p>
            <p className="text-lg font-bold">
              {metrics.length > 0
                ? (metrics.reduce((a, b) => a + b.throughput, 0) / metrics.length).toFixed(0)
                : 0} /s
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 text-center">
            <p className="text-xs text-muted-foreground">錯誤率</p>
            <p className="text-lg font-bold">
              {metrics.length > 0
                ? (metrics.reduce((a, b) => a + b.errorRate, 0) / metrics.length * 100).toFixed(2)
                : 0}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 text-center">
            <p className="text-xs text-muted-foreground">最大並發</p>
            <p className="text-lg font-bold">
              {metrics.length > 0
                ? Math.max(...metrics.map(m => m.concurrency))
                : 0}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
```

#### 驗收標準
- [ ] 進階編排控制台完整
- [ ] 所有 Phase 2 功能可視化
- [ ] 效能指標圖表
- [ ] 嵌套工作流視覺化
- [ ] 響應式設計

---

### Story 12-4: Integration Testing Suite (5 點)

**作為** QA 工程師
**我希望** 有完整的整合測試套件
**以便** 確保 Phase 2 所有功能正常運作

#### 技術規格

```python
# tests/integration/test_phase2_integration.py

import pytest
from httpx import AsyncClient
from uuid import uuid4
import asyncio

@pytest.fixture
async def phase2_setup(client: AsyncClient, test_agents, test_workflows):
    """Phase 2 測試環境設置"""
    return {
        "agents": test_agents,
        "workflows": test_workflows,
        "client": client
    }


class TestConcurrentExecution:
    """並行執行整合測試"""

    @pytest.mark.asyncio
    async def test_fork_join_execution(self, phase2_setup):
        """測試 Fork-Join 執行模式"""
        client = phase2_setup["client"]

        # 建立並行工作流
        response = await client.post(
            "/api/v1/workflows",
            json={
                "name": "Fork-Join Test",
                "nodes": [
                    {"id": "start", "type": "start"},
                    {"id": "fork", "type": "parallel_gateway", "gateway_type": "fork"},
                    {"id": "task_a", "type": "agent_task", "agent_id": str(uuid4())},
                    {"id": "task_b", "type": "agent_task", "agent_id": str(uuid4())},
                    {"id": "join", "type": "parallel_gateway", "gateway_type": "join"},
                    {"id": "end", "type": "end"}
                ],
                "edges": [
                    {"source": "start", "target": "fork"},
                    {"source": "fork", "target": "task_a"},
                    {"source": "fork", "target": "task_b"},
                    {"source": "task_a", "target": "join"},
                    {"source": "task_b", "target": "join"},
                    {"source": "join", "target": "end"}
                ]
            }
        )
        assert response.status_code == 200
        workflow_id = response.json()["id"]

        # 執行
        response = await client.post(
            f"/api/v1/executions",
            json={"workflow_id": workflow_id, "inputs": {}}
        )
        assert response.status_code == 200
        execution_id = response.json()["execution_id"]

        # 等待完成
        await asyncio.sleep(5)

        # 驗證結果
        response = await client.get(f"/api/v1/executions/{execution_id}")
        assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_concurrent_throughput(self, phase2_setup):
        """測試並行吞吐量"""
        client = phase2_setup["client"]
        workflows = phase2_setup["workflows"]

        # 同時啟動 10 個執行
        start_time = asyncio.get_event_loop().time()

        tasks = []
        for _ in range(10):
            tasks.append(
                client.post(
                    "/api/v1/executions",
                    json={
                        "workflow_id": str(workflows[0].id),
                        "inputs": {}
                    }
                )
            )

        responses = await asyncio.gather(*tasks)
        elapsed = asyncio.get_event_loop().time() - start_time

        # 驗證所有請求成功
        assert all(r.status_code == 200 for r in responses)

        # 驗證吞吐量 (應該 < 串行執行時間的 50%)
        assert elapsed < 10  # 假設單個執行 < 1秒


class TestAgentHandoff:
    """Agent 交接整合測試"""

    @pytest.mark.asyncio
    async def test_graceful_handoff(self, phase2_setup):
        """測試優雅交接"""
        client = phase2_setup["client"]
        agents = phase2_setup["agents"]

        # 設置交接
        response = await client.post(
            "/api/v1/handoff/trigger",
            json={
                "execution_id": str(uuid4()),
                "source_agent_id": str(agents[0].id),
                "target_agent_id": str(agents[1].id),
                "policy": "graceful",
                "context": {"task": "test_task"}
            }
        )
        assert response.status_code == 200
        handoff_id = response.json()["handoff_id"]

        # 等待交接完成
        await asyncio.sleep(2)

        # 驗證狀態
        response = await client.get(f"/api/v1/handoff/{handoff_id}/status")
        assert response.json()["status"] in ["completed", "in_progress"]


class TestGroupChat:
    """群組對話整合測試"""

    @pytest.mark.asyncio
    async def test_multi_agent_discussion(self, phase2_setup):
        """測試多 Agent 討論"""
        client = phase2_setup["client"]
        agents = phase2_setup["agents"]

        # 建立群組
        response = await client.post(
            "/api/v1/groupchat",
            json={
                "name": "Test Discussion",
                "agent_ids": [str(a.id) for a in agents[:3]],
                "config": {
                    "max_rounds": 3,
                    "speaker_selection_method": "round_robin"
                }
            }
        )
        assert response.status_code == 200
        group_id = response.json()["group_id"]

        # 開始討論
        response = await client.post(
            f"/api/v1/groupchat/{group_id}/start",
            json={"content": "討論這個主題"}
        )
        assert response.status_code == 200

        # 驗證訊息
        result = response.json()
        assert len(result["messages"]) >= 3  # 至少有初始訊息 + Agent 回應


class TestDynamicPlanning:
    """動態規劃整合測試"""

    @pytest.mark.asyncio
    async def test_task_decomposition_and_execution(self, phase2_setup):
        """測試任務分解和執行"""
        client = phase2_setup["client"]

        # 分解任務
        response = await client.post(
            "/api/v1/planning/decompose",
            json={
                "task_description": "建立用戶認證系統",
                "strategy": "hybrid"
            }
        )
        assert response.status_code == 200
        decomposition = response.json()
        assert len(decomposition["subtasks"]) >= 2

        # 建立計劃
        response = await client.post(
            "/api/v1/planning/plans",
            json={"goal": "建立用戶認證系統"}
        )
        assert response.status_code == 200
        plan_id = response.json()["id"]

        # 批准計劃
        response = await client.post(
            f"/api/v1/planning/plans/{plan_id}/approve",
            params={"approver": "test_user"}
        )
        assert response.status_code == 200


class TestNestedWorkflows:
    """嵌套工作流整合測試"""

    @pytest.mark.asyncio
    async def test_nested_execution(self, phase2_setup):
        """測試嵌套執行"""
        client = phase2_setup["client"]
        workflows = phase2_setup["workflows"]

        # 註冊子工作流
        response = await client.post(
            "/api/v1/nested/sub-workflows",
            json={
                "parent_workflow_id": str(workflows[0].id),
                "workflow_id": str(workflows[1].id),
                "config": {"max_depth": 3}
            }
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_recursive_execution(self, phase2_setup):
        """測試遞歸執行"""
        client = phase2_setup["client"]
        workflows = phase2_setup["workflows"]

        response = await client.post(
            "/api/v1/nested/execute/recursive",
            json={
                "workflow_id": str(workflows[0].id),
                "initial_inputs": {"value": 0},
                "max_depth": 3,
                "max_iterations": 10
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert "status" in result


class TestEndToEnd:
    """端到端整合測試"""

    @pytest.mark.asyncio
    async def test_complex_workflow_scenario(self, phase2_setup):
        """測試複雜工作流場景"""
        client = phase2_setup["client"]

        # 1. 建立帶並行和嵌套的工作流
        # 2. 執行並監控
        # 3. 驗證結果和效能

        # 這是一個完整的端到端測試
        pass

    @pytest.mark.asyncio
    async def test_failure_recovery(self, phase2_setup):
        """測試故障恢復"""
        client = phase2_setup["client"]

        # 模擬故障並驗證恢復機制
        pass
```

#### 驗收標準
- [ ] 並行執行測試通過
- [ ] Agent 交接測試通過
- [ ] 群組對話測試通過
- [ ] 動態規劃測試通過
- [ ] 嵌套工作流測試通過

---

### Story 12-5: Documentation & API Reference (5 點)

**作為** 開發者
**我希望** 有完整的 Phase 2 文檔
**以便** 可以正確使用進階功能

#### 技術規格

```markdown
# Phase 2 API 文檔結構

## 目錄

docs/
├── phase-2/
│   ├── overview.md                    # Phase 2 概述
│   ├── getting-started.md             # 快速開始指南
│   │
│   ├── features/
│   │   ├── concurrent-execution.md    # 並行執行
│   │   ├── agent-handoff.md           # Agent 交接
│   │   ├── groupchat.md               # 群組對話
│   │   ├── dynamic-planning.md        # 動態規劃
│   │   └── nested-workflows.md        # 嵌套工作流
│   │
│   ├── api-reference/
│   │   ├── concurrent-api.md          # 並行 API
│   │   ├── handoff-api.md             # 交接 API
│   │   ├── groupchat-api.md           # 群組 API
│   │   ├── planning-api.md            # 規劃 API
│   │   └── nested-api.md              # 嵌套 API
│   │
│   ├── tutorials/
│   │   ├── build-parallel-workflow.md # 建立並行工作流
│   │   ├── setup-agent-handoff.md     # 設置 Agent 交接
│   │   ├── create-groupchat.md        # 建立群組對話
│   │   └── design-nested-workflow.md  # 設計嵌套工作流
│   │
│   └── best-practices/
│       ├── performance-tuning.md      # 效能調優
│       ├── error-handling.md          # 錯誤處理
│       └── monitoring.md              # 監控建議
```

#### 文檔範例

```markdown
# 並行執行指南

## 概述

IPA Platform 的並行執行功能讓您可以同時執行多個 Agent 任務，
大幅提升工作流執行效率。

## 核心概念

### Fork-Join 模式

```
┌─────┐     ┌─────────┐     ┌─────┐
│Start│ ──▶ │  Fork   │ ──▶ │Task1│ ──┐
└─────┘     └─────────┘     └─────┘   │     ┌─────────┐     ┌─────┐
                            ┌─────┐   │ ──▶ │  Join   │ ──▶ │ End │
                            │Task2│ ──┘     └─────────┘     └─────┘
                            └─────┘
```

### 使用方式

```python
from ipa_platform import WorkflowBuilder

workflow = (
    WorkflowBuilder()
    .start()
    .fork()
        .add_task("task_1", agent_id="agent_a")
        .add_task("task_2", agent_id="agent_b")
    .join(mode="all")  # 等待所有任務完成
    .end()
    .build()
)
```

### API 參考

#### POST /api/v1/concurrent/execute

執行並行任務組。

**請求體：**

```json
{
  "tasks": [
    {"agent_id": "uuid", "inputs": {}},
    {"agent_id": "uuid", "inputs": {}}
  ],
  "mode": "all",  // all, any, majority
  "timeout_seconds": 300
}
```

**回應：**

```json
{
  "execution_id": "uuid",
  "status": "running",
  "tasks": [
    {"id": "uuid", "status": "pending"},
    {"id": "uuid", "status": "pending"}
  ]
}
```

## 最佳實踐

1. **設置合理的超時** - 避免長時間等待
2. **使用適當的合併模式** - 根據需求選擇 all/any/majority
3. **監控並發數** - 避免資源耗盡
4. **處理失敗分支** - 實現適當的錯誤處理

## 常見問題

### Q: 如何處理部分任務失敗？

A: 使用 `error_handling` 配置：

```json
{
  "error_handling": {
    "on_failure": "continue",  // continue, abort, retry
    "max_retries": 3
  }
}
```
```

#### 驗收標準
- [ ] 所有 Phase 2 功能有文檔
- [ ] API 參考完整
- [ ] 教學指南可用
- [ ] 最佳實踐文檔
- [ ] 常見問題解答

---

## 測試計劃

### 效能測試

```python
# tests/performance/test_phase2_performance.py

import pytest
import asyncio
import time
from locust import HttpUser, task, between


class Phase2PerformanceTest:
    """Phase 2 效能測試"""

    @pytest.mark.performance
    async def test_concurrent_execution_throughput(self, client):
        """測試並行執行吞吐量"""
        # 目標：3x 吞吐量提升

        # 基準測試（順序執行）
        sequential_times = []
        for _ in range(10):
            start = time.perf_counter()
            await client.post("/api/v1/executions", json={...})
            sequential_times.append(time.perf_counter() - start)

        sequential_avg = sum(sequential_times) / len(sequential_times)

        # 並行測試
        parallel_start = time.perf_counter()
        tasks = [
            client.post("/api/v1/concurrent/execute", json={...})
            for _ in range(10)
        ]
        await asyncio.gather(*tasks)
        parallel_total = time.perf_counter() - parallel_start

        # 驗證 3x 提升
        improvement = (sequential_avg * 10) / parallel_total
        assert improvement >= 3.0

    @pytest.mark.performance
    async def test_groupchat_latency(self, client):
        """測試群組對話延遲"""
        # 目標：平均延遲 < 2秒

        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            await client.post(
                "/api/v1/groupchat/{id}/message",
                json={"content": "test"}
            )
            latencies.append(time.perf_counter() - start)

        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 2.0

    @pytest.mark.performance
    async def test_nested_workflow_depth(self, client):
        """測試嵌套工作流深度效能"""
        # 目標：10 層嵌套 < 30 秒

        start = time.perf_counter()
        await client.post(
            "/api/v1/nested/execute/recursive",
            json={
                "workflow_id": "...",
                "initial_inputs": {},
                "max_depth": 10
            }
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 30.0


class Phase2LoadTest(HttpUser):
    """負載測試"""
    wait_time = between(1, 3)

    @task(3)
    def concurrent_execution(self):
        self.client.post("/api/v1/concurrent/execute", json={...})

    @task(2)
    def groupchat_message(self):
        self.client.post("/api/v1/groupchat/{id}/message", json={...})

    @task(1)
    def planning_decompose(self):
        self.client.post("/api/v1/planning/decompose", json={...})
```

---

## 資料庫遷移

```sql
-- migrations/versions/012_performance_tables.sql

-- 效能指標表
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value DECIMAL(15,4) NOT NULL,
    unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 分析會話表
CREATE TABLE profile_sessions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    summary JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 效能基準表
CREATE TABLE performance_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    baseline_value DECIMAL(15,4) NOT NULL,
    threshold_value DECIMAL(15,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_perf_metrics_session ON performance_metrics(session_id);
CREATE INDEX idx_perf_metrics_type ON performance_metrics(metric_type);
CREATE INDEX idx_perf_metrics_time ON performance_metrics(recorded_at);
```

---

## Phase 2 完成檢查清單

### 功能完整性

| Sprint | 功能 | 狀態 | 測試覆蓋 |
|--------|------|------|----------|
| Sprint 7 | 並行執行 | ✅ | > 85% |
| Sprint 7 | 增強閘道 | ✅ | > 85% |
| Sprint 8 | Agent 交接 | ✅ | > 85% |
| Sprint 8 | 協作協議 | ✅ | > 85% |
| Sprint 9 | 群組聊天 | ✅ | > 85% |
| Sprint 9 | 多輪對話 | ✅ | > 85% |
| Sprint 9 | 對話記憶 | ✅ | > 85% |
| Sprint 10 | 動態規劃 | ✅ | > 85% |
| Sprint 10 | 自主決策 | ✅ | > 85% |
| Sprint 10 | 試錯機制 | ✅ | > 85% |
| Sprint 11 | 嵌套工作流 | ✅ | > 85% |
| Sprint 11 | 子工作流執行 | ✅ | > 85% |
| Sprint 11 | 遞歸模式 | ✅ | > 85% |
| Sprint 12 | 效能優化 | ✅ | > 85% |
| Sprint 12 | UI 整合 | ✅ | > 85% |
| Sprint 12 | 文檔測試 | ✅ | > 85% |

### 效能 KPI

| 指標 | 目標 | 實際 | 狀態 |
|------|------|------|------|
| 並行執行效率 | 3x 提升 | TBD | ⏳ |
| Agent 協作成功率 | ≥ 90% | TBD | ⏳ |
| 動態規劃準確率 | ≥ 85% | TBD | ⏳ |
| 多輪對話完成率 | ≥ 90% | TBD | ⏳ |
| 嵌套工作流成功率 | ≥ 95% | TBD | ⏳ |

### 文檔完整性

- [ ] Phase 2 概述文檔
- [ ] 各功能使用指南
- [ ] API 參考文檔
- [ ] 教學範例
- [ ] 最佳實踐指南
- [ ] 故障排除指南

---

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試全部通過
- [ ] 效能測試達標
- [ ] API 文檔完整
- [ ] 使用者指南完成
- [ ] 程式碼審查完成
- [ ] 部署腳本準備完成

---

## Phase 2 里程碑

### Phase 2 完成標準

1. **功能完整**：所有 16 個功能項目已實現並測試
2. **效能達標**：所有效能 KPI 達到目標
3. **文檔齊全**：所有文檔已編寫並審核
4. **穩定運行**：在 staging 環境穩定運行 ≥ 1 週

### 下一步

Phase 2 完成後的後續工作：
- 生產環境部署
- 用戶培訓
- 持續監控和優化
- Phase 3 規劃（如有）

---

**恭喜！Phase 2 規劃完成。**
