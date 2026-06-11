# 效能調優最佳實踐

## 概述

本文檔提供 IPA Platform Phase 2 功能的效能調優指南，幫助您優化系統效能。

---

## 並行執行優化

### 1. 合理設置並發數

```python
# 根據系統資源設置
executor = ForkJoinExecutor(
    max_concurrent_tasks=min(cpu_count() * 2, 20),  # 不超過 CPU 核數的 2 倍
    semaphore_limit=100
)
```

### 2. 批次處理大量任務

```python
# 分批處理避免資源耗盡
from src.core.concurrent import ConcurrentOptimizer

optimizer = ConcurrentOptimizer(
    config=ConcurrencyConfig(
        batch_size=50,  # 每批 50 個任務
        max_workers=10
    )
)

results = await optimizer.execute_batch(
    items=large_task_list,
    processor=process_task,
    preserve_order=True
)
```

### 3. 使用適當的 Join 模式

```python
# 只需要第一個結果時使用 'any'
result = await executor.execute_fork_join(
    tasks=tasks,
    join_mode="any"  # 減少等待時間
)
```

---

## Agent 交接優化

### 1. 預熱目標 Agent

```python
# 提前初始化可能的目標 Agent
await controller.warm_up_agents(["agent_b", "agent_c"])
```

### 2. 最小化上下文傳輸

```python
# 只傳遞必要的上下文
context = {
    "essential_data": essential,
    # 排除大型物件
    # "large_history": history  # 避免
}
```

### 3. 使用能力快取

```python
# 快取 Agent 能力資訊
matcher = CapabilityMatcher(
    cache_enabled=True,
    cache_ttl_seconds=300  # 5 分鐘快取
)
```

---

## 群組對話優化

### 1. 限制對話輪數

```python
config = GroupConfig(
    max_rounds=10,  # 合理限制
    early_termination=True
)
```

### 2. 使用對話摘要

```python
# 長對話自動摘要
memory = ConversationMemory(
    max_messages=50,
    summary_threshold=30,
    summary_method="extractive"  # 更快的摘要方式
)
```

### 3. 選擇性載入歷史

```python
# 只載入相關歷史
history = await memory.get_relevant_history(
    query=current_topic,
    limit=20
)
```

---

## 動態規劃優化

### 1. 快取分解結果

```python
# 相似任務使用快取
planner = DynamicPlanner(
    decomposition_cache=True,
    cache_similarity_threshold=0.85
)
```

### 2. 平行分解

```python
# 大任務並行分解
decomposition = await planner.decompose_task(
    description=task,
    parallel_analysis=True
)
```

### 3. 增量計劃更新

```python
# 避免重建整個計劃
await planner.update_plan_incremental(
    plan_id=plan.id,
    changes=changes
)
```

---

## 嵌套工作流優化

### 1. 限制嵌套深度

```python
executor = NestedExecutor(
    max_depth=5,  # 不建議超過 5 層
    depth_exceeded_action="fail"
)
```

### 2. 使用上下文隔離

```python
# 減少上下文傳遞開銷
config = SubWorkflowConfig(
    inherit_context=False,
    propagate_keys=["user_id"]  # 只傳遞必要的
)
```

### 3. 平行執行子工作流

```python
# 無依賴的子工作流並行執行
results = await executor.execute_parallel_nested(
    parent_workflow_id="main",
    child_workflows=independent_workflows
)
```

---

## 通用優化建議

### 1. 啟用 Redis 快取

```python
# 設定 LLM 回應快取
cache_config = {
    "enabled": True,
    "ttl_seconds": 3600,
    "max_size": 10000
}
```

### 2. 使用連接池

```python
# 資料庫連接池
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_timeout": 30
}
```

### 3. 非同步 I/O

```python
# 始終使用非同步操作
async def process_request():
    results = await asyncio.gather(
        fetch_data(),
        call_api(),
        query_database()
    )
```

### 4. 監控和警報

```python
# 設置效能閾值警報
collector.set_threshold("cpu_percent", max_value=80)
collector.set_threshold("memory_percent", max_value=85)
collector.set_threshold("avg_latency_ms", max_value=500)
```

---

## 效能測試

### 基準測試

```python
from src.core.performance import BenchmarkRunner

runner = BenchmarkRunner()

# 運行基準測試
result = await runner.run_async(
    name="api_benchmark",
    func=api_call,
    iterations=100,
    warmup_iterations=10
)

print(f"Avg latency: {result.mean_ms:.2f}ms")
print(f"P99 latency: {result.p99_ms:.2f}ms")
```

### 負載測試

```bash
# 使用 locust 進行負載測試
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10
```

---

## 效能檢查清單

- [ ] 並發數設置合理
- [ ] 批次處理大量任務
- [ ] 快取已啟用
- [ ] 連接池已配置
- [ ] 非同步操作使用正確
- [ ] 效能監控已設置
- [ ] 閾值警報已配置
- [ ] 定期執行基準測試
