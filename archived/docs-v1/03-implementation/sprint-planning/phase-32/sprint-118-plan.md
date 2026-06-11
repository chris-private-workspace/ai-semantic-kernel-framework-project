# Sprint 118: E2E 測試 + Phase B 驗收

## 概述

Sprint 118 是 Phase 32 的最後一個 Sprint，專注於 AD 帳號管理場景的端到端測試、Azure AI Search 整合驗證、以及 Phase 32（Phase B）的完整性能基準和驗收報告。本 Sprint 確保所有組件整合正確、性能達標、業務價值可量化。

## 目標

1. AD 場景端到端測試（ServiceNow RITM → Agent → LDAP MCP → Close RITM）
2. Azure AI Search 整合測試 + 監控驗證（整合原 Phase 30 Sprint 110 驗證內容）
3. Phase 32 性能基準 + 驗收報告

## Story Points: 35 點

## 前置條件

- ✅ Sprint 114-117 全部完成
- ✅ AD 場景所有組件就緒（Webhook, PatternMatcher, SemanticRouter, LDAP MCP, ServiceNow MCP）
- ✅ AzureSemanticRouter 運作正常
- ✅ Multi-Worker 配置就緒

## 任務分解

### Story 118-1: AD 場景端到端測試 (3 天, P0)

**目標**: 編寫完整的 AD 帳號管理場景 E2E 測試，覆蓋從 ServiceNow RITM 事件到 RITM 關閉的完整流程

**交付物**:
- `backend/tests/e2e/orchestration/test_ad_scenario_e2e.py`
- `backend/tests/e2e/orchestration/conftest.py`
- `backend/tests/e2e/orchestration/test_ad_scenario_fixtures.py`

**E2E 測試場景**:

```python
class TestADScenarioE2E:
    """AD 帳號管理場景端到端測試"""

    @pytest.mark.asyncio
    async def test_account_unlock_full_flow(self, client, mock_ldap, mock_servicenow):
        """
        完整流程: ServiceNow RITM → InputGateway → PatternMatcher
                  → Agent 執行 → LDAP MCP unlock → Close RITM
        """
        # Step 1: 模擬 ServiceNow Webhook 發送 RITM 事件
        ritm_payload = {
            "sys_id": "abc123",
            "number": "RITM0012345",
            "state": "1",
            "cat_item_name": "AD Account Unlock",
            "requested_for": "john.doe",
            "short_description": "Unlock AD account for john.doe",
            "variables": {"affected_user": "john.doe"},
        }
        response = await client.post(
            "/api/v1/orchestration/webhooks/servicenow",
            json=ritm_payload,
            headers={"X-ServiceNow-Secret": "test-secret"},
        )
        assert response.status_code == 200
        tracking_id = response.json()["tracking_id"]

        # Step 2: 驗證 RITM 被正確映射為 ad.account.unlock intent

        # Step 3: 驗證 PatternMatcher 匹配成功

        # Step 4: 驗證 Agent 被選擇並執行

        # Step 5: 驗證 LDAP MCP unlock 被調用
        mock_ldap.assert_called_with("unlock", user="john.doe")

        # Step 6: 驗證 ServiceNow RITM 被關閉
        mock_servicenow.assert_called_with("close_ritm", sys_id="abc123")

    @pytest.mark.asyncio
    async def test_password_reset_full_flow(self, client, mock_ldap, mock_servicenow):
        """密碼重設完整流程"""

    @pytest.mark.asyncio
    async def test_group_membership_change_full_flow(self, client, mock_ldap, mock_servicenow):
        """群組異動完整流程（需審批）"""

    @pytest.mark.asyncio
    async def test_unknown_ritm_fallback_to_semantic_router(self, client):
        """未知 Catalog Item 觸發 SemanticRouter fallback"""

    @pytest.mark.asyncio
    async def test_ritm_idempotency(self, client):
        """相同 RITM 重複發送不重複執行"""

    @pytest.mark.asyncio
    async def test_ldap_failure_error_handling(self, client, mock_ldap_fail):
        """LDAP 操作失敗的錯誤處理和回報"""

    @pytest.mark.asyncio
    async def test_servicenow_failure_graceful_degradation(self, client, mock_sn_fail):
        """ServiceNow 不可用時的優雅降級"""
```

**測試覆蓋的流程節點**:

| 節點 | 驗證內容 |
|------|----------|
| ServiceNow Webhook | 認證、payload 解析、冪等處理 |
| InputGateway | RITM → RoutingRequest 轉換 |
| PatternMatcher | AD 規則匹配、intent 返回 |
| SemanticRouter | Fallback 場景、搜索精度 |
| Agent Selection | 根據 intent 選擇正確 Agent |
| LDAP MCP | unlock / reset / group 操作 |
| ServiceNow MCP | RITM 狀態更新、關閉 |
| Error Handling | 各節點故障的處理和回報 |

**驗收標準**:
- [ ] 帳號解鎖 E2E 測試通過
- [ ] 密碼重設 E2E 測試通過
- [ ] 群組異動 E2E 測試通過（含審批流程）
- [ ] Fallback 場景測試通過
- [ ] 冪等處理測試通過
- [ ] LDAP 故障處理測試通過
- [ ] ServiceNow 故障降級測試通過
- [ ] 測試覆蓋所有 8 個流程節點

### Story 118-2: Azure AI Search 整合測試 + 監控驗證 (2 天, P1)

> **對應**: Phase 30 Sprint 110 驗證內容

**目標**: 驗證 Azure AI Search 在真實環境中的表現，確保路由精度和延遲達標

**交付物**:
- `backend/tests/e2e/orchestration/test_semantic_routing_e2e.py`
- `backend/tests/performance/orchestration/test_routing_performance.py`
- 監控指標收集腳本

**整合測試場景**:

```python
class TestSemanticRoutingE2E:
    """語義路由端到端測試"""

    @pytest.mark.asyncio
    async def test_full_routing_flow_with_azure(self, client):
        """完整路由流程（Azure AI Search）"""
        # 發送自然語言請求 → 通過三層路由 → 返回正確 intent

    @pytest.mark.asyncio
    async def test_ad_scenario_routing_accuracy(self, client):
        """AD 場景路由精度測試"""
        test_cases = [
            ("Please unlock the account for john.doe", "ad.account.unlock"),
            ("幫 john.doe 重設密碼", "ad.password.reset"),
            ("Add john.doe to the admin group", "ad.group.modify"),
        ]
        for query, expected_intent in test_cases:
            result = await client.post("/api/v1/orchestration/route", json={"query": query})
            assert result.json()["intent"] == expected_intent

    @pytest.mark.asyncio
    async def test_routing_fallback_chain(self, client):
        """L1 → L2 → L3 fallback chain 測試"""

    @pytest.mark.asyncio
    async def test_azure_search_unavailable_fallback(self, client, mock_azure_down):
        """Azure Search 不可用時 fallback 到 Mock"""
```

**性能測試**:

```python
class TestRoutingPerformance:
    """路由性能基準測試"""

    @pytest.mark.asyncio
    async def test_pattern_matcher_latency(self):
        """PatternMatcher 延遲 < 5ms (P95)"""

    @pytest.mark.asyncio
    async def test_semantic_router_latency(self):
        """AzureSemanticRouter 延遲 < 100ms (P95)"""

    @pytest.mark.asyncio
    async def test_full_routing_latency(self):
        """完整路由延遲 < 150ms (P95)"""

    @pytest.mark.asyncio
    async def test_concurrent_routing(self):
        """10 並發路由請求的吞吐量"""

    @pytest.mark.asyncio
    async def test_embedding_cache_effectiveness(self):
        """Embedding 快取命中率 > 50%"""
```

**監控指標**:

| 指標 | 目標值 | 說明 |
|------|--------|------|
| PatternMatcher P95 延遲 | < 5ms | 規則匹配速度 |
| SemanticRouter P95 延遲 | < 100ms | Azure AI Search 搜索 |
| 完整路由 P95 延遲 | < 150ms | 端到端路由 |
| 路由精度 | > 90% | Top-1 精度 |
| 路由覆蓋率 | > 95% | 可識別的 intent 比例 |
| Embedding 快取命中率 | > 50% | 重複查詢的快取效果 |

**驗收標準**:
- [ ] 語義路由 E2E 測試通過
- [ ] AD 場景路由精度 > 90%
- [ ] Fallback chain 正確運作（L1 → L2 → L3）
- [ ] Azure 不可用 fallback 正常
- [ ] 性能基準全部達標
- [ ] 監控指標收集正常

### Story 118-3: Phase 32 性能基準 + 驗收報告 (1 天, P0)

**目標**: 產出 Phase 32 的完整性能基準和驗收報告，量化業務價值

**交付物**:
- `docs/03-implementation/sprint-planning/phase-32/performance-report.md`
- `docs/03-implementation/sprint-planning/phase-32/acceptance-report.md`

**性能基準內容**:

```markdown
## Phase 32 Performance Benchmark

### 路由性能
| 指標 | 目標 | 實測 | 達標 |
|------|------|------|------|
| PatternMatcher P95 | < 5ms | [填入] | [是/否] |
| SemanticRouter P95 | < 100ms | [填入] | [是/否] |
| 完整路由 P95 | < 150ms | [填入] | [是/否] |
| 10 並發吞吐量 | > 50 req/s | [填入] | [是/否] |

### AD 場景性能
| 指標 | 目標 | 實測 | 達標 |
|------|------|------|------|
| 帳號解鎖端到端延遲 | < 5s | [填入] | [是/否] |
| 密碼重設端到端延遲 | < 5s | [填入] | [是/否] |
| 群組異動端到端延遲 | < 10s | [填入] | [是/否] |

### 路由精度
| 場景類型 | 測試數 | 正確數 | 精度 |
|----------|--------|--------|------|
| AD 帳號管理 | [N] | [n] | [%] |
| 一般 IT 請求 | [N] | [n] | [%] |
| 總計 | [N] | [n] | [%] |
```

**驗收報告內容**:

```markdown
## Phase 32 Acceptance Report

### 交付物清單
| 項目 | 狀態 | 說明 |
|------|------|------|
| AD PatternMatcher 規則 | [達成/未達成] | 5 類 AD 規則 |
| LDAP MCP 配置 | [達成/未達成] | 5 項 LDAP 操作 |
| ServiceNow Webhook | [達成/未達成] | RITM 接收和解析 |
| RITM→Intent 映射 | [達成/未達成] | 5 類映射 |
| AzureSemanticRouter | [達成/未達成] | 替代 Mock |
| 路由管理 API | [達成/未達成] | 6 個 CRUD 端點 |
| 15 條路由遷移 | [達成/未達成] | YAML → Azure |
| Swarm 整合主流程 | [達成/未達成] | execute_with_routing() |
| Layer 4 拆分 | [達成/未達成] | L4a + L4b |
| L5-L6 循環依賴修復 | [達成/未達成] | ToolCallbackProtocol |
| Multi-Worker 配置 | [達成/未達成] | Gunicorn |
| ServiceNow MCP | [達成/未達成] | 6 個工具 |
| E2E 測試 | [達成/未達成] | AD 場景全流程 |

### 業務價值驗證
| 指標 | 目標 | 實測 |
|------|------|------|
| 月節省工時 | 137.5 小時 | [填入] |
| 月節省成本 | $5,740 | [填入] |
| ROI | +112% | [填入] |
| 路由覆蓋率 | 95% | [填入] |
```

**驗收標準**:
- [ ] 性能基準報告完成（所有指標有實測數據）
- [ ] 驗收報告完成（所有交付物有狀態）
- [ ] 業務價值可量化
- [ ] 未達標項目有改善計劃

## 技術設計

### 測試目錄結構

```
backend/tests/
├── e2e/
│   └── orchestration/
│       ├── conftest.py                    # 🆕 E2E 測試 fixtures
│       ├── test_ad_scenario_e2e.py        # 🆕 AD 場景 E2E
│       ├── test_ad_scenario_fixtures.py   # 🆕 測試資料
│       └── test_semantic_routing_e2e.py   # 🆕 語義路由 E2E
├── performance/
│   └── orchestration/
│       └── test_routing_performance.py    # 🆕 路由性能測試
└── ...
```

### 測試執行命令

```bash
# AD 場景 E2E 測試
pytest tests/e2e/orchestration/test_ad_scenario_e2e.py -v --timeout=60

# 語義路由 E2E 測試
pytest tests/e2e/orchestration/test_semantic_routing_e2e.py -v

# 性能基準測試
pytest tests/performance/orchestration/test_routing_performance.py -v --benchmark

# 全部 Phase 32 測試
pytest tests/e2e/orchestration/ tests/performance/orchestration/ -v
```

## 依賴

```
# 測試依賴
pytest>=7.4.0            # (已有)
pytest-asyncio>=0.21.0   # (已有)
pytest-benchmark>=4.0.0  # 性能基準測試
httpx>=0.25.0            # (已有) 測試客戶端
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| E2E 測試環境不穩定 | Mock 外部服務（LDAP, ServiceNow）|
| 性能數據波動大 | 多次執行取中位數 |
| Azure AI Search 測試需真實資源 | 提供 Mock fallback 測試模式 |

## 完成標準

- [ ] AD 場景 3 個核心流程 E2E 測試通過
- [ ] 語義路由精度 > 90%
- [ ] 路由延遲 < 150ms (P95)
- [ ] 性能基準報告完成
- [ ] 驗收報告完成
- [ ] Phase 32 所有成功標準達成

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 35
**開始日期**: TBD
