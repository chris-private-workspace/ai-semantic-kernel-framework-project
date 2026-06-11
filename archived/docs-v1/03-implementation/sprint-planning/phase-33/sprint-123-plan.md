# Sprint 123: 測試覆蓋率 + 品質衝刺

## 概述

Sprint 123 是 Phase 33 的最後一個 Sprint，專注於提升測試覆蓋率至 60% 目標。重點覆蓋 Orchestration、Auth、MCP 三個關鍵模組，並生成完整的覆蓋率報告來驗證 Phase 33 的品質目標。

## 目標

1. 為 Orchestration 模組編寫單元和整合測試
2. 為 Auth 模組編寫完整測試
3. 為 MCP 模組編寫安全相關測試
4. 執行完整測試套件，驗證 60%+ 覆蓋率目標

## Story Points: 35 點

## 前置條件

- ⬜ Sprint 122 完成（Azure 部署 + 可觀測性就緒）
- ⬜ Phase 31 Auth Middleware 已實現
- ⬜ Phase 31 MCP Permission 已啟用
- ⬜ 所有 InMemory 存儲已遷移

## 任務分解

### Story 123-1: 測試覆蓋 — Orchestration 模組 (2 天, P1)

**目標**: 為 Orchestration 模組（路由、意圖、對話管理）編寫單元和整合測試

**交付物**:
- `backend/tests/unit/orchestration/` 測試套件
- `backend/tests/integration/orchestration/` 整合測試

**背景**:
Orchestration 是平台最核心的模組之一，包含 Phase 28 的三層意圖路由系統。目前 API 測試覆蓋率僅 33%（13/39 模組），Orchestration 相關測試嚴重不足。

**測試範圍**:

| 子模組 | 測試重點 | 測試類型 |
|--------|---------|---------|
| BusinessIntentRouter | 路由決策邏輯、層級回退 | 單元 |
| PatternMatcher | 規則匹配、優先級排序 | 單元 |
| SemanticRouter | 向量相似度搜索（Mock LLM） | 單元 |
| LLMClassifier | 分類結果解析（Mock LLM） | 單元 |
| DialogManager | 多輪對話狀態管理 | 單元 + 整合 |
| IntentRoutingAPI | API 端點完整流程 | 整合 |
| execute_with_routing() | 端到端路由→執行流程 | 整合 |

**關鍵測試案例**:

```python
# 路由決策測試
class TestBusinessIntentRouter:
    async def test_pattern_match_priority_over_semantic(self):
        """Pattern match 應優先於 Semantic routing"""
        ...

    async def test_fallback_chain_pattern_to_semantic_to_llm(self):
        """三層回退鏈：Pattern → Semantic → LLM"""
        ...

    async def test_unknown_intent_returns_default(self):
        """未知意圖返回預設處理"""
        ...

# 對話管理測試
class TestDialogManager:
    async def test_multi_turn_context_preservation(self):
        """多輪對話上下文保持"""
        ...

    async def test_session_timeout_cleanup(self):
        """會話超時自動清理"""
        ...
```

**驗收標準**:
- [ ] Orchestration 模組測試覆蓋率 > 70%
- [ ] 三層路由決策邏輯全面測試
- [ ] 多輪對話場景測試
- [ ] 錯誤處理和邊界條件測試
- [ ] 所有測試獨立可執行（不依賴執行順序）

### Story 123-2: 測試覆蓋 — Auth 模組 (1.5 天, P1)

**目標**: 為 Auth Middleware、JWT 驗證、角色存取控制編寫完整測試

**交付物**:
- `backend/tests/unit/auth/` 測試套件
- `backend/tests/integration/auth/` 整合測試

**背景**:
Phase 31 實現了全局 Auth Middleware，Auth 覆蓋率從 7% 提升到 100%。本 Sprint 為這些新的安全機制編寫測試，確保安全防護有效。

**測試範圍**:

| 子模組 | 測試重點 | 測試類型 |
|--------|---------|---------|
| JWT Middleware | Token 驗證、過期處理、格式錯誤 | 單元 |
| AuthN | 用戶認證流程、登入/登出 | 單元 + 整合 |
| AuthZ | 角色檢查、權限控制 | 單元 |
| Rate Limiting | 限流觸發、限流恢復 | 整合 |
| Session 管理 | Session 建立/銷毀/過期 | 單元 + 整合 |

**關鍵測試案例**:

```python
class TestJWTMiddleware:
    async def test_valid_token_passes(self):
        """有效 JWT Token 通過驗證"""
        ...

    async def test_expired_token_rejected(self):
        """過期 Token 被拒絕（401）"""
        ...

    async def test_malformed_token_rejected(self):
        """格式錯誤的 Token 被拒絕（401）"""
        ...

    async def test_missing_token_rejected(self):
        """缺少 Token 的請求被拒絕（401）"""
        ...

class TestRoleBasedAccess:
    async def test_admin_can_access_admin_endpoints(self):
        """Admin 角色可訪問管理端點"""
        ...

    async def test_user_cannot_access_admin_endpoints(self):
        """普通用戶不能訪問管理端點（403）"""
        ...

class TestRateLimiting:
    async def test_rate_limit_triggers_after_threshold(self):
        """超過限流閾值後返回 429"""
        ...

    async def test_rate_limit_resets_after_window(self):
        """時間窗口過後限流重置"""
        ...
```

**驗收標準**:
- [ ] Auth 模組測試覆蓋率 > 80%
- [ ] JWT 驗證邊界條件全面覆蓋
- [ ] 角色權限控制測試完整
- [ ] Rate Limiting 觸發和恢復測試
- [ ] 安全相關的負面測試案例完整（invalid token, expired, wrong role）

### Story 123-3: 測試覆蓋 — MCP 模組 (1.5 天, P1)

**目標**: 為 MCP Permission 檢查、命令白名單、工具執行安全機制編寫測試

**交付物**:
- `backend/tests/unit/mcp/` 測試套件
- `backend/tests/integration/mcp/` 整合測試

**背景**:
Phase 31 啟用了 MCP Permission Patterns，添加了 Shell/SSH 命令白名單。本 Sprint 驗證這些安全機制的有效性。

**測試範圍**:

| 子模組 | 測試重點 | 測試類型 |
|--------|---------|---------|
| Permission Check | `check_permission()` 調用驗證 | 單元 |
| Command Whitelist | Shell/SSH 白名單機制 | 單元 |
| Tool Execution | MCP 工具調用安全流程 | 整合 |
| MCP Server Manager | 伺服器啟動/停止/健康檢查 | 單元 |
| Error Handling | 工具調用失敗處理 | 單元 |

**關鍵測試案例**:

```python
class TestMCPPermission:
    async def test_authorized_tool_call_succeeds(self):
        """已授權的工具調用成功"""
        ...

    async def test_unauthorized_tool_call_blocked(self):
        """未授權的工具調用被攔截"""
        ...

class TestShellWhitelist:
    async def test_whitelisted_command_allowed(self):
        """白名單內的命令可執行"""
        ...

    async def test_non_whitelisted_command_blocked(self):
        """白名單外的命令被攔截"""
        ...

    async def test_command_injection_blocked(self):
        """命令注入嘗試被攔截"""
        ...

class TestToolExecution:
    async def test_tool_timeout_handling(self):
        """工具執行超時處理"""
        ...

    async def test_tool_error_propagation(self):
        """工具錯誤正確傳播"""
        ...
```

**驗收標準**:
- [ ] MCP 模組測試覆蓋率 > 70%
- [ ] Permission check 全面測試
- [ ] Shell/SSH 白名單安全測試（含注入攻擊測試）
- [ ] 工具調用生命週期測試
- [ ] 錯誤處理和超時測試

### Story 123-4: Phase 33 驗證 + 覆蓋率報告 (1 天, P0)

**目標**: 執行完整測試套件，生成覆蓋率報告，驗證 Phase 33 所有品質目標

**交付物**:
- 完整覆蓋率報告（HTML + 文字）
- Phase 33 驗證報告
- 覆蓋率差距分析文件

**驗證項目**:

| 驗證項目 | 目標 | 測量方式 |
|---------|------|---------|
| 測試覆蓋率 | ≥ 60% | `pytest --cov=src --cov-report=html` |
| InMemory 存儲 | 0 個殘留 | `grep -r "InMemory" backend/src/` |
| Checkpoint 統一 | 4 系統全部接入 | 功能驗證 |
| Azure 部署 | 正常運行 | Health check + 功能測試 |
| 結構化日誌 | JSON 格式 | 日誌輸出檢查 |
| Request ID | 全鏈路追蹤 | API 請求驗證 |
| OTel | Traces/Metrics 可見 | Application Insights 檢查 |

**覆蓋率報告指令**:

```bash
cd backend
pytest --cov=src \
       --cov-report=html:htmlcov \
       --cov-report=term-missing \
       --cov-branch \
       -v
```

**驗收標準**:
- [ ] 整體測試覆蓋率 ≥ 60%
- [ ] 0 個 test failure
- [ ] 覆蓋率報告生成並記錄
- [ ] Phase 33 所有 Sprint 的驗收標準回顧確認
- [ ] 差距分析文件記錄（哪些模組覆蓋率仍低，Phase 34 需補強）
- [ ] 團隊內部使用的 readiness 確認

## 技術設計

### 測試目錄結構（新增部分）

```
backend/tests/
├── unit/
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── test_business_intent_router.py
│   │   ├── test_pattern_matcher.py
│   │   ├── test_semantic_router.py
│   │   ├── test_llm_classifier.py
│   │   └── test_dialog_manager.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── test_jwt_middleware.py
│   │   ├── test_role_based_access.py
│   │   ├── test_rate_limiting.py
│   │   └── test_session_management.py
│   └── mcp/
│       ├── __init__.py
│       ├── test_permission_check.py
│       ├── test_shell_whitelist.py
│       ├── test_tool_execution.py
│       └── test_mcp_server_manager.py
├── integration/
│   ├── orchestration/
│   │   ├── test_routing_api.py
│   │   └── test_execute_with_routing.py
│   ├── auth/
│   │   └── test_auth_flow.py
│   └── mcp/
│       └── test_mcp_integration.py
└── conftest.py
```

### Mock 策略

| 被 Mock 的外部依賴 | Mock 方式 | 說明 |
|-------------------|---------|------|
| LLM API（Claude, Azure OpenAI） | `unittest.mock.patch` | 避免真實 API 呼叫 |
| Redis | `fakeredis` 或 `unittest.mock` | 單元測試不需真實 Redis |
| PostgreSQL | `pytest-asyncio` + fixture | 使用測試 DB |
| MCP 外部工具 | `unittest.mock.AsyncMock` | 模擬工具回應 |

## 依賴

```
# 測試依賴（已存在於 requirements-dev.txt）
pytest>=7.0
pytest-asyncio>=0.21
pytest-cov>=4.0
fakeredis>=2.0           # Redis mock（如尚未安裝）
httpx>=0.24              # FastAPI TestClient
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| 60% 覆蓋率目標無法達成 | 優先覆蓋關鍵路徑，接受部分低優先模組覆蓋率較低 |
| 測試與 Mock 代碼分離衝突 | Phase 31 Mock 分離後，測試專用 Mock 放在 `tests/mocks/` |
| 測試執行時間過長 | 標記 slow tests，CI 中分離 fast/slow test suites |
| 整合測試需要 Redis/PostgreSQL | CI 中使用 Docker services 提供測試環境 |

## 完成標準

- [ ] 整體測試覆蓋率 ≥ 60%
- [ ] Orchestration 模組覆蓋率 > 70%
- [ ] Auth 模組覆蓋率 > 80%
- [ ] MCP 模組覆蓋率 > 70%
- [ ] 覆蓋率報告生成並記錄
- [ ] Phase 33 驗證報告完成
- [ ] 所有測試通過（0 failures）

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 35
**開始日期**: 待定
