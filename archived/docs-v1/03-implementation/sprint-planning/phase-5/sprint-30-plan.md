# Sprint 30: 整合與驗收

**Sprint 目標**: 完整整合測試、文檔更新和最終驗收
**週期**: 2 週
**Story Points**: 34 點
**Phase 5 功能**: P5-F5 (整合與驗收)

---

## Sprint 概覽

### 目標
1. E2E 整合測試 - 完整工作流測試
2. 效能測試 - 確保遷移後效能無退化
3. 文檔更新 - API 文檔、架構圖更新
4. 棄用代碼清理 - 移除不再需要的 domain 代碼
5. 最終審計和驗收

### 成功標準
- [ ] E2E 測試覆蓋完整工作流場景
- [ ] 效能無退化 (回應時間 <= 現有實現)
- [ ] 文檔完整更新
- [ ] 棄用代碼完全清理
- [ ] 最終審計符合性 >= 95%

---

## User Stories

### S30-1: E2E 整合測試 (8 點)

**描述**: 完整的端到端工作流測試，驗證所有遷移後的功能正常運作。

**測試場景**:

1. **簡單順序工作流**
   - 創建工作流 → 添加節點 → 執行 → 驗證結果

2. **帶人工審批的工作流**
   - 創建工作流 → 執行 → 暫停等待審批 → 審批 → 繼續執行 → 完成

3. **並行執行工作流**
   - 創建並行工作流 → 執行 → 驗證所有分支完成

4. **Agent 交接工作流**
   - 創建 agents → 設置交接 → 執行交接 → 驗證結果

5. **GroupChat 工作流**
   - 創建 group → 添加 agents → 執行對話 → 驗證輪流發言

6. **錯誤恢復工作流**
   - 創建工作流 → 模擬錯誤 → 驗證錯誤處理 → 重試 → 完成

**驗收標準**:
- [ ] 6 個核心場景測試通過
- [ ] 無功能回歸
- [ ] 測試可重複執行

**檔案**:
- `backend/tests/e2e/test_complete_workflow.py`
- `backend/tests/e2e/test_approval_workflow.py`
- `backend/tests/e2e/test_concurrent_workflow.py`
- `backend/tests/e2e/test_handoff_workflow.py`
- `backend/tests/e2e/test_groupchat_workflow.py`
- `backend/tests/e2e/test_error_recovery.py`

**技術任務**:

```python
# tests/e2e/test_complete_workflow.py
"""
完整工作流 E2E 測試

測試從創建到完成的完整工作流生命週期
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from src.main import app


class TestCompleteWorkflow:
    """完整工作流端到端測試"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.e2e
    async def test_simple_sequential_workflow(self, client, sample_agent):
        """測試簡單順序工作流"""
        # 1. 創建工作流
        workflow_response = client.post(
            "/api/v1/workflows",
            json={
                "name": "Test Sequential Workflow",
                "nodes": [
                    {"id": "node-1", "type": "agent", "agent_id": str(sample_agent.id)},
                    {"id": "node-2", "type": "function", "config": {"function_name": "process"}},
                ],
                "edges": [
                    {"source": "start", "target": "node-1"},
                    {"source": "node-1", "target": "node-2"},
                    {"source": "node-2", "target": "end"},
                ]
            }
        )
        assert workflow_response.status_code == 201
        workflow_id = workflow_response.json()["id"]

        # 2. 執行工作流
        run_response = client.post(
            f"/api/v1/workflows/{workflow_id}/run",
            json={"input": "test data"}
        )
        assert run_response.status_code == 200
        execution_id = run_response.json()["execution_id"]

        # 3. 等待完成
        import asyncio
        for _ in range(30):  # 最多等待 30 秒
            status_response = client.get(f"/api/v1/executions/{execution_id}")
            if status_response.json()["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        # 4. 驗證結果
        final_status = client.get(f"/api/v1/executions/{execution_id}").json()
        assert final_status["status"] == "completed"
        assert "result" in final_status

    @pytest.mark.e2e
    async def test_workflow_with_approval(self, client, sample_agent, sample_approver):
        """測試帶人工審批的工作流"""
        # 1. 創建帶審批節點的工作流
        workflow_response = client.post(
            "/api/v1/workflows",
            json={
                "name": "Approval Workflow",
                "nodes": [
                    {"id": "process", "type": "agent", "agent_id": str(sample_agent.id)},
                    {"id": "approve", "type": "approval", "config": {"risk_level": "high"}},
                    {"id": "finalize", "type": "function", "config": {"function_name": "finalize"}},
                ],
                "edges": [
                    {"source": "start", "target": "process"},
                    {"source": "process", "target": "approve"},
                    {"source": "approve", "target": "finalize"},
                    {"source": "finalize", "target": "end"},
                ]
            }
        )
        workflow_id = workflow_response.json()["id"]

        # 2. 執行工作流
        run_response = client.post(
            f"/api/v1/workflows/{workflow_id}/run",
            json={"input": "test"}
        )
        execution_id = run_response.json()["execution_id"]

        # 3. 驗證工作流暫停
        import asyncio
        await asyncio.sleep(2)
        status = client.get(f"/api/v1/executions/{execution_id}").json()
        assert status["status"] == "waiting_approval"

        # 4. 獲取待審批請求
        pending = client.get("/api/v1/checkpoints/pending").json()
        assert len(pending["approvals"]) > 0
        approval_id = pending["approvals"][0]["request_id"]

        # 5. 審批
        approve_response = client.post(
            f"/api/v1/checkpoints/{approval_id}/approve",
            json={"reason": "Approved for testing"}
        )
        assert approve_response.status_code == 200

        # 6. 驗證工作流繼續並完成
        for _ in range(30):
            status = client.get(f"/api/v1/executions/{execution_id}").json()
            if status["status"] == "completed":
                break
            await asyncio.sleep(1)

        assert status["status"] == "completed"
```

---

### S30-2: 效能測試 (8 點)

**描述**: 確保遷移後效能無退化。

**測試項目**:

1. **工作流執行時間**
   - 簡單工作流 < 500ms
   - 複雜工作流 < 2000ms
   - 帶審批工作流 (不含等待時間) < 1000ms

2. **API 回應時間**
   - GET 端點 < 100ms
   - POST 端點 < 500ms
   - 列表端點 < 200ms

3. **並行處理能力**
   - 10 並行執行 < 5000ms
   - 50 並行執行 < 15000ms

4. **記憶體使用**
   - 基準記憶體 < 512MB
   - 高負載 < 1GB

**驗收標準**:
- [ ] 所有效能指標達標
- [ ] 無效能退化 (與遷移前比較)
- [ ] 效能報告生成

**檔案**:
- `backend/tests/performance/test_workflow_performance.py`
- `backend/tests/performance/test_api_performance.py`
- `backend/tests/performance/test_concurrent_performance.py`

**技術任務**:

```python
# tests/performance/test_workflow_performance.py
"""
工作流效能測試
"""

import pytest
import time
import asyncio
from statistics import mean, stdev


class TestWorkflowPerformance:
    """工作流效能測試"""

    @pytest.mark.performance
    async def test_simple_workflow_execution_time(self, workflow_adapter, sample_workflow):
        """測試簡單工作流執行時間"""
        times = []

        for _ in range(10):
            start = time.perf_counter()
            result = await workflow_adapter.run(
                workflow_id=sample_workflow.id,
                input_data={"test": "data"}
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 毫秒

        avg_time = mean(times)
        std_time = stdev(times)

        # 驗證效能指標
        assert avg_time < 500, f"平均執行時間 {avg_time:.2f}ms 超過 500ms"
        assert std_time < 100, f"標準差 {std_time:.2f}ms 過高"

        # 記錄效能數據
        print(f"\n簡單工作流效能:")
        print(f"  平均: {avg_time:.2f}ms")
        print(f"  標準差: {std_time:.2f}ms")
        print(f"  最小: {min(times):.2f}ms")
        print(f"  最大: {max(times):.2f}ms")

    @pytest.mark.performance
    async def test_concurrent_execution(self, workflow_adapter, sample_workflow):
        """測試並行執行效能"""
        async def run_one():
            return await workflow_adapter.run(
                workflow_id=sample_workflow.id,
                input_data={"test": "concurrent"}
            )

        # 10 並行
        start = time.perf_counter()
        results = await asyncio.gather(*[run_one() for _ in range(10)])
        end = time.perf_counter()
        time_10 = (end - start) * 1000

        assert all(r.success for r in results)
        assert time_10 < 5000, f"10 並行執行時間 {time_10:.2f}ms 超過 5000ms"

        print(f"\n並行執行效能:")
        print(f"  10 並行: {time_10:.2f}ms")


class TestAPIPerformance:
    """API 效能測試"""

    @pytest.mark.performance
    def test_get_endpoint_response_time(self, client, sample_workflow):
        """測試 GET 端點回應時間"""
        times = []

        for _ in range(100):
            start = time.perf_counter()
            response = client.get(f"/api/v1/workflows/{sample_workflow.id}")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)
        p95_time = sorted(times)[94]  # 95th percentile

        assert avg_time < 50, f"平均回應時間 {avg_time:.2f}ms 超過 50ms"
        assert p95_time < 100, f"P95 回應時間 {p95_time:.2f}ms 超過 100ms"

        print(f"\nGET 端點效能:")
        print(f"  平均: {avg_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
```

---

### S30-3: 文檔更新 (6 點)

**描述**: 更新 API 文檔、架構圖和開發指南。

**更新內容**:

1. **API 文檔**
   - 更新 OpenAPI/Swagger 描述
   - 更新端點說明
   - 添加新模型文檔

2. **架構文檔**
   - 更新 technical-architecture.md
   - 添加 Phase 5 架構變更
   - 更新組件圖

3. **開發指南**
   - 更新 CLAUDE.md
   - 更新適配器使用指南
   - 添加遷移後的最佳實踐

**驗收標準**:
- [ ] API 文檔完整
- [ ] 架構圖反映新結構
- [ ] 開發指南更新

**檔案**:
- `docs/02-architecture/technical-architecture.md`
- `docs/05-reference/api-documentation.md`
- `CLAUDE.md`

---

### S30-4: 棄用代碼清理 (6 點)

**描述**: 移除不再需要的 domain 代碼。

**清理範圍**:

1. **可刪除的代碼**
   - `domain/workflows/models.py` 中的舊 WorkflowDefinition (如果完全遷移)
   - 舊的執行邏輯 (如果完全遷移)
   - 棄用的 CheckpointService 方法

2. **需保留的代碼**
   - 平台特定功能 (ScenarioRouter, ConnectorService, etc.)
   - 尚未遷移的功能

3. **標記棄用的代碼**
   - 添加 `@deprecated` 裝飾器
   - 添加棄用警告

**驗收標準**:
- [ ] 無遺留自行實現代碼 (Phase 2-5 功能)
- [ ] 棄用代碼有明確標記
- [ ] 無破壞性刪除

**注意事項**:
- ⚠️ 只刪除確定不再使用的代碼
- ⚠️ 保留向後兼容的時間
- ⚠️ 記錄所有刪除內容

---

### S30-5: 最終審計和驗收 (6 點)

**描述**: 執行最終符合性審計，確認 Phase 5 目標達成。

**審計項目**:

1. **官方 API 使用驗證**
   - 所有 Phase 5 適配器使用官方 API
   - 驗證腳本通過

2. **遺留代碼檢查**
   - 無 SK/AutoGen import
   - 無直接 domain 使用 (Phase 2-5 功能)

3. **測試覆蓋率**
   - 單元測試 >= 80%
   - 整合測試 >= 70%

4. **效能基準**
   - 無效能退化

5. **文檔完整性**
   - API 文檔完整
   - 架構圖更新

**驗收標準**:
- [ ] 符合性 >= 95%
- [ ] 所有測試通過
- [ ] 效能達標
- [ ] 文檔完整

**輸出**:
- `PHASE5-FINAL-AUDIT-REPORT.md`

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] E2E 測試全部通過
   - [ ] 效能測試全部達標
   - [ ] 文檔完整更新
   - [ ] 棄用代碼清理完成

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 整合測試覆蓋率 >= 70%
   - [ ] E2E 測試覆蓋 6 核心場景

3. **審計完成**
   - [ ] 最終審計符合性 >= 95%
   - [ ] 審計報告生成
   - [ ] 所有問題已修復

4. **Phase 5 驗收**
   - [ ] 所有 Sprint 26-30 完成
   - [ ] 總 Story Points: 180 點
   - [ ] 目標達成確認

---

## 相關文檔

- [Phase 5 Overview](./README.md)
- [Phase 5 完整計劃](./PHASE5-MVP-REFACTORING-PLAN.md)
- [Sprint 29 Plan](./sprint-29-plan.md) - API Routes 遷移
- [Sprint 25 審計報告](../../sprint-execution/sprint-25/FINAL-COMPREHENSIVE-AUDIT.md)
