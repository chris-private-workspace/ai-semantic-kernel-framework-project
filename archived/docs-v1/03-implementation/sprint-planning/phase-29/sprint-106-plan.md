# Sprint 106: E2E 測試 + 性能優化 + 文檔

## 概述

Sprint 106 是 Phase 29 的最後一個 Sprint，專注於端到端測試、性能優化和文檔編寫，確保 Agent Swarm 可視化功能的穩定性和可維護性。

## 目標

1. 編寫完整的 E2E 測試套件
2. 性能測試與優化
3. 編寫 API 參考文檔
4. 編寫開發者指南
5. 編寫使用者指南
6. 最終驗收測試

## Story Points: 22 點

## 前置條件

- ✅ Sprint 100-105 完成
- ✅ 所有功能開發完成
- ✅ 基礎測試通過

## 任務分解

### Story 106-1: E2E 測試套件 (6h, P0)

**目標**: 編寫完整的端到端測試

**交付物**:
- `backend/tests/e2e/swarm/test_swarm_execution.py`
- `frontend/tests/e2e/swarm.spec.ts` (Playwright)

**測試場景**:

```python
# backend/tests/e2e/swarm/test_swarm_execution.py
import pytest
from httpx import AsyncClient

class TestSwarmE2E:
    """Agent Swarm 端到端測試"""

    @pytest.mark.asyncio
    async def test_swarm_creation_and_execution(self, client: AsyncClient):
        """測試 Swarm 創建和執行流程"""
        # 1. 發送需要多 Agent 協作的請求
        response = await client.post(
            "/api/v1/ag-ui",
            json={
                "session_id": "test_session",
                "message": "分析 APAC ETL Pipeline 連續失敗的問題",
            },
        )
        assert response.status_code == 200

        # 2. 收集 SSE 事件
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                events.append(event)
                if event.get("type") == "RUN_FINISHED":
                    break

        # 3. 驗證 Swarm 事件
        swarm_events = [e for e in events if e.get("event_name", "").startswith("swarm_")]
        assert any(e["event_name"] == "swarm_created" for e in swarm_events)
        assert any(e["event_name"] == "swarm_completed" for e in swarm_events)

        # 4. 驗證 Worker 事件
        worker_events = [e for e in events if e.get("event_name", "").startswith("worker_")]
        assert len(worker_events) > 0

    @pytest.mark.asyncio
    async def test_swarm_api_endpoints(self, client: AsyncClient):
        """測試 Swarm API 端點"""
        # 1. 創建 Swarm (通過執行)
        # ... 執行請求

        # 2. 獲取 Swarm 狀態
        swarm_response = await client.get(f"/api/v1/swarm/{swarm_id}")
        assert swarm_response.status_code == 200
        swarm = swarm_response.json()
        assert "workers" in swarm

        # 3. 獲取 Worker 詳情
        worker_id = swarm["workers"][0]["workerId"]
        worker_response = await client.get(
            f"/api/v1/swarm/{swarm_id}/workers/{worker_id}"
        )
        assert worker_response.status_code == 200

    @pytest.mark.asyncio
    async def test_swarm_error_handling(self, client: AsyncClient):
        """測試錯誤處理"""
        # 測試無效 Swarm ID
        response = await client.get("/api/v1/swarm/invalid_id")
        assert response.status_code == 404

        # 測試無效 Worker ID
        response = await client.get("/api/v1/swarm/valid_swarm/workers/invalid")
        assert response.status_code == 404
```

**前端 E2E 測試 (Playwright)**:

```typescript
// frontend/tests/e2e/swarm.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Agent Swarm Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chat');
  });

  test('should display swarm panel when multi-agent task starts', async ({ page }) => {
    // 1. 發送需要多 Agent 的消息
    await page.fill('[data-testid="chat-input"]', '分析 ETL Pipeline 問題');
    await page.click('[data-testid="send-button"]');

    // 2. 等待 Swarm Panel 出現
    await expect(page.locator('[data-testid="agent-swarm-panel"]')).toBeVisible({
      timeout: 30000,
    });

    // 3. 驗證 Worker 卡片
    const workerCards = page.locator('[data-testid="worker-card"]');
    await expect(workerCards).toHaveCount.above(0);
  });

  test('should open worker detail drawer on click', async ({ page }) => {
    // 1. 等待 Swarm Panel
    await expect(page.locator('[data-testid="agent-swarm-panel"]')).toBeVisible();

    // 2. 點擊 Worker 卡片
    await page.click('[data-testid="worker-card"]:first-child');

    // 3. 驗證 Drawer 打開
    await expect(page.locator('[data-testid="worker-detail-drawer"]')).toBeVisible();

    // 4. 驗證內容
    await expect(page.locator('[data-testid="worker-header"]')).toBeVisible();
    await expect(page.locator('[data-testid="tool-calls-panel"]')).toBeVisible();
  });

  test('should show extended thinking content', async ({ page }) => {
    // 1. 打開 Worker Drawer
    await page.click('[data-testid="worker-card"]:first-child');

    // 2. 等待思考內容
    const thinkingPanel = page.locator('[data-testid="extended-thinking-panel"]');
    await expect(thinkingPanel).toBeVisible({ timeout: 30000 });

    // 3. 驗證思考內容不為空
    const thinkingContent = page.locator('[data-testid="thinking-content"]');
    await expect(thinkingContent).not.toBeEmpty();
  });

  test('should update progress in real-time', async ({ page }) => {
    // 1. 獲取初始進度
    const progressBar = page.locator('[data-testid="overall-progress"]');
    const initialProgress = await progressBar.getAttribute('aria-valuenow');

    // 2. 等待進度更新
    await page.waitForTimeout(3000);

    // 3. 驗證進度變化
    const newProgress = await progressBar.getAttribute('aria-valuenow');
    expect(Number(newProgress)).toBeGreaterThanOrEqual(Number(initialProgress));
  });
});
```

**驗收標準**:
- [ ] 後端 E2E 測試完成
- [ ] 前端 E2E 測試完成
- [ ] 所有測試通過
- [ ] 測試覆蓋所有主要場景

### Story 106-2: 性能測試與優化 (5h, P0)

**目標**: 進行性能測試並優化瓶頸

**交付物**:
- `backend/tests/performance/swarm/test_swarm_performance.py`
- `docs/03-implementation/sprint-planning/phase-29/performance-report.md`

**性能指標**:

| 指標 | 目標值 | 測量方法 |
|------|--------|---------|
| SSE 事件延遲 | < 100ms | 從事件發送到前端接收 |
| Swarm API 響應時間 | < 200ms | P95 |
| Worker Detail API | < 300ms | P95 (包含 thinking history) |
| 前端渲染 FPS | > 55 | React DevTools |
| 記憶體使用 | < 50MB | 1000 事件後 |

**性能測試**:

```python
# backend/tests/performance/swarm/test_swarm_performance.py
import pytest
import asyncio
import time
from statistics import mean, quantiles

class TestSwarmPerformance:
    """Swarm 性能測試"""

    @pytest.mark.asyncio
    async def test_event_throughput(self, swarm_emitter):
        """測試事件吞吐量"""
        events_sent = 0
        start_time = time.time()

        for _ in range(100):
            await swarm_emitter.emit_worker_progress(
                swarm_id="test",
                worker=mock_worker,
            )
            events_sent += 1

        elapsed = time.time() - start_time
        throughput = events_sent / elapsed

        assert throughput > 50, f"Throughput {throughput} < 50 events/sec"

    @pytest.mark.asyncio
    async def test_api_latency(self, client):
        """測試 API 延遲"""
        latencies = []

        for _ in range(100):
            start = time.time()
            await client.get(f"/api/v1/swarm/{swarm_id}")
            latencies.append((time.time() - start) * 1000)

        p95 = quantiles(latencies, n=20)[18]  # 95th percentile
        assert p95 < 200, f"P95 latency {p95}ms > 200ms"

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """測試記憶體使用"""
        import tracemalloc

        tracemalloc.start()
        tracker = SwarmTracker()

        # 模擬大量事件
        for i in range(1000):
            tracker.add_worker_thinking(
                "swarm_1",
                f"worker_{i % 5}",
                f"Thinking content {i}",
            )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert peak < 50 * 1024 * 1024, f"Peak memory {peak/1024/1024}MB > 50MB"
```

**優化措施**:

1. **事件節流**: 進度更新最多 5 events/sec
2. **批量發送**: 合併多個小事件
3. **增量更新**: 只發送變化的部分
4. **延遲加載**: Worker 詳情按需加載
5. **虛擬化**: 長列表使用虛擬滾動

**驗收標準**:
- [ ] 所有性能指標達標
- [ ] 性能報告完成
- [ ] 優化措施實施

### Story 106-3: API 參考文檔 (3h, P0)

**目標**: 編寫完整的 API 參考文檔

**交付物**:
- `docs/api/swarm-api-reference.md`

**文檔結構**:

```markdown
# Agent Swarm API Reference

## Overview

Agent Swarm API 提供了多代理協作的狀態查詢和管理功能。

## Base URL

`/api/v1/swarm`

## Endpoints

### Get Swarm Status

獲取 Agent Swarm 的整體狀態。

**Request**

```
GET /api/v1/swarm/{swarm_id}
```

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| swarm_id | string | Yes | Swarm 唯一標識符 |

**Response**

```json
{
  "swarmId": "swarm_abc123",
  "sessionId": "sess_xyz789",
  "mode": "sequential",
  "status": "executing",
  "totalWorkers": 3,
  "overallProgress": 65,
  "workers": [
    {
      "workerId": "worker_0",
      "workerName": "DiagnosticWorker",
      "workerType": "claude_sdk",
      "role": "diagnostic",
      "status": "completed",
      "progress": 100,
      "currentAction": null,
      "toolCallsCount": 3
    }
  ],
  "createdAt": "2026-03-01T10:00:00Z",
  "startedAt": "2026-03-01T10:00:01Z"
}
```

### Get Worker Detail

獲取單個 Worker 的詳細執行信息。

**Request**

```
GET /api/v1/swarm/{swarm_id}/workers/{worker_id}
```

**Query Parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| include_thinking | boolean | true | 是否包含思考歷史 |
| include_messages | boolean | true | 是否包含對話歷史 |

**Response**

```json
{
  "workerId": "worker_0",
  "workerName": "DiagnosticWorker",
  "taskDescription": "分析 ETL Pipeline 錯誤...",
  "thinkingHistory": [
    {
      "content": "我需要分析這個問題...",
      "timestamp": "2026-03-01T10:00:05Z",
      "tokenCount": 245
    }
  ],
  "toolCalls": [
    {
      "toolCallId": "call_123",
      "toolName": "azure:query_adf_logs",
      "status": "completed",
      "inputArgs": {"pipeline": "APAC_Glider"},
      "outputResult": {"error_count": 47},
      "durationMs": 1245
    }
  ],
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ]
}
```

## SSE Events

### Event Types

| Event Name | Description |
|------------|-------------|
| swarm_created | Swarm 創建 |
| swarm_status_update | Swarm 狀態更新 |
| swarm_completed | Swarm 完成 |
| worker_started | Worker 啟動 |
| worker_progress | Worker 進度更新 |
| worker_thinking | Worker 思考過程 |
| worker_tool_call | Worker 工具調用 |
| worker_completed | Worker 完成 |

### Event Format

```
data: {"type":"CUSTOM","event_name":"worker_progress","payload":{...}}
```
```

**驗收標準**:
- [ ] 所有 API 端點文檔化
- [ ] 包含請求/響應示例
- [ ] 包含錯誤碼說明
- [ ] SSE 事件文檔化

### Story 106-4: 開發者指南 (3h, P1)

**目標**: 編寫開發者整合指南

**交付物**:
- `docs/03-implementation/sprint-planning/phase-29/developer-guide.md`

**文檔內容**:
- 架構概述
- 組件使用指南
- 狀態管理說明
- 事件處理指南
- 擴展指南

**驗收標準**:
- [ ] 架構說明清晰
- [ ] 包含代碼示例
- [ ] 覆蓋常見場景

### Story 106-5: 使用者指南 (2h, P1)

**目標**: 編寫功能使用說明

**交付物**:
- `docs/06-user-guide/agent-swarm-visualization.md`

**文檔內容**:
- 功能介紹
- 介面說明
- 操作指南
- 常見問題

**驗收標準**:
- [ ] 說明清晰易懂
- [ ] 包含截圖
- [ ] 覆蓋所有功能

### Story 106-6: 最終驗收測試 (3h, P0)

**目標**: 進行最終的功能驗收

**交付物**:
- `docs/03-implementation/sprint-planning/phase-29/acceptance-report.md`

**驗收清單**:

| 功能 | 驗收標準 | 通過 |
|------|---------|------|
| Swarm Panel | 正確顯示多 Worker | [ ] |
| Worker Card | 狀態、進度、操作正確 | [ ] |
| Worker Drawer | 詳情完整顯示 | [ ] |
| Extended Thinking | 實時更新 | [ ] |
| Tool Calls | 輸入/輸出正確 | [ ] |
| SSE Events | 實時推送 | [ ] |
| API | 響應正確 | [ ] |
| 性能 | 符合指標 | [ ] |

**驗收標準**:
- [ ] 所有功能驗收通過
- [ ] 驗收報告完成
- [ ] Stakeholder 簽核

## 技術設計

### 測試架構

```
tests/
├── unit/                   # 單元測試
├── integration/            # 整合測試
├── e2e/                    # 端到端測試
│   └── swarm/
│       ├── test_swarm_execution.py
│       └── swarm.spec.ts
└── performance/            # 性能測試
    └── swarm/
        └── test_swarm_performance.py
```

### 文檔架構

```
docs/
├── api/
│   └── swarm-api-reference.md
├── 03-implementation/
│   └── sprint-planning/
│       └── phase-29/
│           ├── developer-guide.md
│           ├── performance-report.md
│           └── acceptance-report.md
└── 06-user-guide/
    └── agent-swarm-visualization.md
```

## 依賴

- pytest-asyncio
- Playwright
- tracemalloc

## 風險

| 風險 | 緩解措施 |
|------|---------|
| E2E 測試不穩定 | 增加重試，合理超時 |
| 性能不達標 | 提前識別，持續優化 |
| 文檔過時 | 與代碼同步更新 |

## 完成標準

- [ ] 所有 Story 完成
- [ ] E2E 測試通過
- [ ] 性能指標達標
- [ ] 文檔完成並審核
- [ ] 最終驗收通過

---

**Sprint 開始**: 2026-03-13
**Sprint 結束**: 2026-03-20
**Story Points**: 22
