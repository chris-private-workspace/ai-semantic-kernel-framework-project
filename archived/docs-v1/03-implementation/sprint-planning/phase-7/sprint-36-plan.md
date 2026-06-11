# Sprint 36: 驗證與優化

**Sprint 目標**: 完整測試 AI 自主決策能力，優化性能，準備 UAT
**總點數**: 15 Story Points
**優先級**: 🟡 重要
**前置條件**: Sprint 34, 35 完成

---

## 背景

Sprint 34-35 完成了 LLM 服務基礎設施和 Phase 2 擴展整合後，本 Sprint 進行全面驗證、性能優化，並準備 UAT 測試。

### 驗證目標

```
┌─────────────────────────────────────────────────────────┐
│               Phase 7 驗證矩陣                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  功能驗證                                               │
│  ├── TaskDecomposer + LLM → 智能任務分解               │
│  ├── DecisionEngine + LLM → 智能決策分析               │
│  ├── TrialAndErrorEngine + LLM → 智能錯誤學習          │
│  └── PlanningAdapter 完整流程 → 端到端 AI 自主決策     │
│                                                         │
│  性能驗證                                               │
│  ├── LLM 調用延遲 < 5 秒 (P95)                         │
│  ├── 緩存命中率 > 30%                                  │
│  └── 並發處理能力驗證                                  │
│                                                         │
│  降級驗證                                               │
│  ├── LLM 不可用 → 規則式降級                           │
│  └── 超時處理 → 優雅失敗                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Story 清單

### S36-1: 端到端 AI 決策測試 (5 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 測試
**影響範圍**: `backend/tests/e2e/`

#### 設計

創建完整的端到端測試套件，驗證 AI 自主決策流程。

```python
# tests/e2e/test_ai_autonomous_decision.py

import pytest
from src.integrations.agent_framework.builders import PlanningAdapter
from src.integrations.llm import AzureOpenAILLMService


class TestAIAutonomousDecision:
    """AI 自主決策端到端測試。

    使用真實 Azure OpenAI API 進行完整流程驗證。
    """

    @pytest.fixture
    def real_llm_service(self):
        """創建真實 LLM 服務（需要有效配置）。"""
        return AzureOpenAILLMService()

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_intelligent_task_decomposition(self, real_llm_service):
        """測試智能任務分解。

        驗證 TaskDecomposer 使用 LLM 進行語義理解和分解。
        """
        adapter = PlanningAdapter("e2e-test", llm_service=real_llm_service)
        adapter.with_task_decomposition()

        # 複雜任務描述
        task = """
        Build a user authentication system with:
        - Email/password login
        - OAuth2 (Google, GitHub)
        - Two-factor authentication
        - Password reset flow
        - Session management
        """

        result = await adapter.decompose(task)

        # 驗證 LLM 智能分解
        assert len(result.subtasks) >= 5
        assert result.confidence >= 0.7
        assert any("oauth" in st.name.lower() for st in result.subtasks)
        assert any("2fa" in st.name.lower() or "two-factor" in st.name.lower()
                   for st in result.subtasks)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_intelligent_decision_making(self, real_llm_service):
        """測試智能決策。

        驗證 DecisionEngine 使用 LLM 進行風險評估和決策分析。
        """
        adapter = PlanningAdapter("e2e-test", llm_service=real_llm_service)
        adapter.with_decision_engine()

        result = await adapter.decide(
            situation="Choose a database for high-traffic e-commerce platform",
            options=[
                "PostgreSQL - Relational, ACID compliant",
                "MongoDB - Document store, flexible schema",
                "Redis - In-memory, high performance",
                "CockroachDB - Distributed SQL"
            ],
            context={
                "traffic": "10M daily users",
                "data_type": "transactions",
                "consistency_requirement": "high"
            }
        )

        # 驗證 LLM 智能決策
        assert result["selected_option"] is not None
        assert len(result["reasoning"]) > 50  # 有實質性推理
        assert result["confidence"] >= 0.6
        assert "risk_assessment" in result

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_full_planning_workflow(self, real_llm_service):
        """測試完整規劃工作流程。

        驗證從任務分解到決策的完整 AI 自主決策流程。
        """
        adapter = PlanningAdapter("e2e-test", llm_service=real_llm_service)
        adapter.with_task_decomposition()
        adapter.with_decision_engine()
        adapter.with_trial_error(max_retries=2)

        result = await adapter.run(
            goal="Implement a REST API for user management with CRUD operations"
        )

        # 驗證完整流程
        assert result.status.value in ["completed", "ready"]
        assert len(result.subtasks) > 0
        assert result.duration_ms > 0
```

#### 任務清單

1. **創建測試目錄結構**
   ```
   backend/tests/e2e/
   ├── __init__.py
   ├── conftest.py                    # E2E fixtures
   ├── test_ai_autonomous_decision.py # 主要測試
   └── test_llm_integration.py        # LLM 直接整合測試
   ```

2. **實現測試用例**
   - 智能任務分解測試
   - 智能決策測試
   - 智能錯誤學習測試
   - 完整規劃工作流程測試

3. **添加測試標記**
   ```python
   # conftest.py
   def pytest_configure(config):
       config.addinivalue_line("markers", "e2e: End-to-end tests (require real API)")
   ```

4. **配置 CI/CD 集成**
   - E2E 測試需要真實 API，可能需要特殊環境

#### 驗收標準
- [ ] E2E 測試套件創建完成
- [ ] 智能任務分解測試通過
- [ ] 智能決策測試通過
- [ ] 完整工作流程測試通過
- [ ] 測試可在 CI/CD 中運行

---

### S36-2: 性能基準測試與優化 (5 pts)

**優先級**: 🟡 P1
**類型**: 測試/優化
**影響範圍**: `backend/tests/performance/`

#### 設計

```python
# tests/performance/test_llm_performance.py

import pytest
import asyncio
import statistics
from src.integrations.llm import LLMServiceFactory


class TestLLMPerformance:
    """LLM 服務性能測試。"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_request_latency(self):
        """測試單個請求延遲。

        目標: P95 < 5 秒
        """
        service = LLMServiceFactory.create()
        latencies = []

        for i in range(10):
            start = asyncio.get_event_loop().time()
            await service.generate("Hello, this is a test prompt.")
            latency = asyncio.get_event_loop().time() - start
            latencies.append(latency)

        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        avg = statistics.mean(latencies)

        print(f"Average latency: {avg:.2f}s")
        print(f"P95 latency: {p95:.2f}s")

        assert p95 < 5.0, f"P95 latency {p95:.2f}s exceeds 5s target"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """測試並發請求處理。

        目標: 10 個並發請求全部成功
        """
        service = LLMServiceFactory.create()

        async def make_request(i):
            return await service.generate(f"Test prompt {i}")

        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        print(f"Successes: {len(successes)}, Failures: {len(failures)}")

        assert len(successes) >= 8, f"Too many failures: {len(failures)}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_effectiveness(self):
        """測試緩存效果。

        目標: 相同請求第二次延遲 < 100ms
        """
        service = LLMServiceFactory.create(use_cache=True)
        prompt = "What is the capital of France?"

        # 第一次請求 (cold)
        start = asyncio.get_event_loop().time()
        await service.generate(prompt)
        cold_latency = asyncio.get_event_loop().time() - start

        # 第二次請求 (cached)
        start = asyncio.get_event_loop().time()
        await service.generate(prompt)
        cached_latency = asyncio.get_event_loop().time() - start

        print(f"Cold latency: {cold_latency:.3f}s")
        print(f"Cached latency: {cached_latency:.3f}s")
        print(f"Speedup: {cold_latency / cached_latency:.1f}x")

        assert cached_latency < 0.1, "Cache miss or slow cache"
```

#### 任務清單

1. **創建性能測試套件**
   - 單請求延遲測試
   - 並發請求測試
   - 緩存效果測試
   - 超時處理測試

2. **建立性能基準**
   | 指標 | 目標 | 實際 |
   |------|------|------|
   | 單請求 P95 延遲 | < 5s | TBD |
   | 並發成功率 (10 req) | > 80% | TBD |
   | 緩存命中延遲 | < 100ms | TBD |

3. **優化措施**
   - 緩存預熱策略
   - 連接池優化
   - 超時配置調整

#### 驗收標準
- [ ] 性能測試套件創建完成
- [ ] P95 延遲 < 5 秒
- [ ] 並發成功率 > 80%
- [ ] 緩存有效工作

---

### S36-3: 文檔更新和 UAT 準備 (3 pts)

**優先級**: 🟡 P1
**類型**: 文檔
**影響範圍**: `docs/`, `claudedocs/`

#### 任務清單

1. **更新技術文檔**
   - `docs/02-architecture/technical-architecture.md` - 添加 LLM 服務層
   - `backend/src/integrations/llm/README.md` - LLM 服務使用指南

2. **更新 UAT 測試計劃**
   - 添加 AI 自主決策測試場景
   - 更新 FEATURE-INDEX.md 中相關功能狀態

3. **更新 CLAUDE.md**
   - 添加 LLM 配置說明
   - 更新開發命令

4. **創建 Phase 7 完成報告**
   ```markdown
   # Phase 7 完成報告

   ## 成果摘要
   - LLM 服務基礎設施完成
   - Phase 2 擴展全部啟用 LLM
   - 端到端 AI 自主決策驗證通過

   ## 性能指標
   - 單請求延遲: X.Xs (P95)
   - 緩存命中率: X%
   - 並發成功率: X%

   ## 新增功能
   - 智能任務分解 (LLM 驅動)
   - 智能決策分析 (LLM 驅動)
   - 智能錯誤學習 (LLM 驅動)
   ```

#### 驗收標準
- [ ] 技術文檔更新完成
- [ ] UAT 測試計劃更新完成
- [ ] CLAUDE.md 更新完成
- [ ] Phase 7 完成報告創建

---

### S36-4: LLM 回退策略驗證 (2 pts)

**優先級**: 🟢 P2
**類型**: 測試
**影響範圍**: `backend/tests/`

#### 設計

驗證 LLM 不可用時的優雅降級。

```python
# tests/unit/test_llm_fallback.py

import pytest
from unittest.mock import AsyncMock, patch
from src.integrations.agent_framework.builders import PlanningAdapter


class TestLLMFallback:
    """LLM 回退策略測試。"""

    @pytest.mark.asyncio
    async def test_decomposer_fallback_on_llm_error(self):
        """測試 LLM 錯誤時降級到規則式分解。"""
        # 創建會失敗的 LLM 服務
        mock_llm = AsyncMock()
        mock_llm.generate.side_effect = Exception("API Error")

        adapter = PlanningAdapter("test", llm_service=mock_llm)
        adapter.with_task_decomposition()

        # 應該降級到規則式，不應該拋出異常
        result = await adapter.decompose("Build an API")

        assert result is not None
        assert len(result.subtasks) > 0  # 規則式分解仍然產生結果

    @pytest.mark.asyncio
    async def test_decomposer_fallback_on_timeout(self):
        """測試 LLM 超時時降級到規則式分解。"""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(side_effect=asyncio.TimeoutError())

        adapter = PlanningAdapter("test", llm_service=mock_llm)
        adapter.with_task_decomposition()

        result = await adapter.decompose("Build an API")

        assert result is not None

    @pytest.mark.asyncio
    async def test_no_llm_uses_rule_based(self):
        """測試無 LLM 服務時使用規則式。"""
        adapter = PlanningAdapter("test", llm_service=None)
        adapter.with_task_decomposition()

        result = await adapter.decompose("Build an API")

        assert result is not None
        # 可以檢查是否使用了規則式（通過日誌或結果特徵）
```

#### 驗收標準
- [ ] LLM 錯誤降級測試通過
- [ ] LLM 超時降級測試通過
- [ ] 無 LLM 規則式測試通過
- [ ] 降級不影響功能完整性

---

## 驗證命令

```bash
# 1. 運行 E2E 測試 (需要真實 API)
cd backend
pytest tests/e2e/ -v -m e2e

# 2. 運行性能測試
pytest tests/performance/ -v -m performance

# 3. 運行回退策略測試
pytest tests/unit/test_llm_fallback.py -v

# 4. 生成測試覆蓋率報告
pytest tests/ -v --cov=src --cov-report=html

# 5. 完整驗證
pytest tests/ -v --ignore=tests/e2e  # 排除需要真實 API 的測試
```

---

## 完成定義

- [ ] 所有 S36 Story 完成
- [ ] E2E 測試套件創建並通過
- [ ] 性能基準測試通過
- [ ] 文檔更新完成
- [ ] 回退策略驗證通過
- [ ] Phase 7 完成報告創建
- [ ] UAT 測試計劃更新

---

## Phase 7 完成標準

| 標準 | 目標 | 狀態 |
|------|------|------|
| LLM 服務基礎設施 | 完成 | ⏳ |
| Phase 2 擴展 LLM 整合 | 100% | ⏳ |
| 端到端測試 | 通過 | ⏳ |
| 性能達標 | P95 < 5s | ⏳ |
| 降級策略 | 驗證 | ⏳ |
| 文檔更新 | 完成 | ⏳ |

---

**創建日期**: 2025-12-21
