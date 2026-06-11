# Sprint 50 Checklist: MCP & Hybrid Architecture - MCP 與混合架構

**Sprint 目標**: 實現 MCP Server 整合與雙框架混合架構
**週期**: Week 5-6
**總點數**: 38 點
**狀態**: 📋 計劃中 (0/38 點)

---

## 快速驗證命令

```bash
# 啟動服務
cd backend
uvicorn main:app --reload --port 8000

# 執行單元測試
pytest tests/unit/integrations/claude_sdk/mcp/ -v
pytest tests/unit/integrations/claude_sdk/hybrid/ -v

# 測試 MCP 連接
python -c "
import asyncio
from src.integrations.claude_sdk.mcp import MCPStdioServer

async def test():
    server = MCPStdioServer(
        name='test',
        command='echo',
        args=['hello']
    )
    print('MCP Server created')

asyncio.run(test())
"

# 檢查型別
mypy src/integrations/claude_sdk/mcp/
mypy src/integrations/claude_sdk/hybrid/
```

---

## S50-1: MCP Server 基礎 (10 點) 📋

### 檔案結構
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/` 目錄
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/__init__.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/base.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/stdio.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/http.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/types.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/exceptions.py`

### MCPTool 類別
- [ ] `MCPTool.name` 屬性
- [ ] `MCPTool.description` 屬性
- [ ] `MCPTool.input_schema` 屬性
- [ ] `MCPTool.server` 屬性

### MCPToolResult 類別
- [ ] `MCPToolResult.content` 屬性
- [ ] `MCPToolResult.success` 屬性 (預設 True)
- [ ] `MCPToolResult.error` 屬性 (可選)

### MCPServer 基礎類別
- [ ] `MCPServer.__init__()` 接受 name 參數
- [ ] `MCPServer.__init__()` 接受 timeout 參數
- [ ] `MCPServer.is_connected` 屬性
- [ ] `MCPServer.connect()` 抽象方法
- [ ] `MCPServer.disconnect()` 抽象方法
- [ ] `MCPServer.list_tools()` 抽象方法
- [ ] `MCPServer.execute_tool()` 抽象方法
- [ ] `MCPServer.__aenter__()` Context Manager 支援
- [ ] `MCPServer.__aexit__()` Context Manager 支援

### MCPStdioServer 實現
- [ ] 接受 `command` 參數 (必要)
- [ ] 接受 `args` 參數 (命令參數列表)
- [ ] 接受 `env` 參數 (環境變數)
- [ ] 接受 `cwd` 參數 (工作目錄)
- [ ] `connect()` 啟動子進程
- [ ] `_initialize()` 發送初始化請求
- [ ] `_send_request()` JSON-RPC 請求發送
- [ ] `disconnect()` 終止子進程
- [ ] `list_tools()` 查詢可用工具
- [ ] `execute_tool()` 執行工具調用
- [ ] 進程錯誤處理
- [ ] 超時處理

### MCPHTTPServer 實現
- [ ] 接受 `url` 參數 (必要)
- [ ] 接受 `api_key` 參數
- [ ] 接受 `headers` 參數
- [ ] `_get_headers()` 組合請求標頭
- [ ] `connect()` 建立 aiohttp Session
- [ ] `connect()` 執行健康檢查
- [ ] `disconnect()` 關閉 Session
- [ ] `list_tools()` GET /tools 端點
- [ ] `execute_tool()` POST /tools/call 端點
- [ ] HTTP 錯誤處理
- [ ] 超時處理

### MCP 例外類別
- [ ] `MCPError` 基礎例外
- [ ] `MCPConnectionError` 連接錯誤
- [ ] `MCPTimeoutError` 超時錯誤
- [ ] `MCPToolError` 工具執行錯誤

### 測試
- [ ] `test_mcp_server_base_class` 通過
- [ ] `test_stdio_server_connect` 通過
- [ ] `test_stdio_server_disconnect` 通過
- [ ] `test_stdio_server_list_tools` 通過
- [ ] `test_stdio_server_execute_tool` 通過
- [ ] `test_stdio_server_timeout` 通過
- [ ] `test_http_server_connect` 通過
- [ ] `test_http_server_disconnect` 通過
- [ ] `test_http_server_list_tools` 通過
- [ ] `test_http_server_execute_tool` 通過
- [ ] `test_http_server_error_handling` 通過

---

## S50-2: MCP Manager 與工具發現 (8 點) 📋

### 檔案結構
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/manager.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/mcp/discovery.py`

### MCPManager 實現
- [ ] `MCPManager.__init__()` 初始化
- [ ] `_servers` 字典儲存 Server
- [ ] `_tools` 字典儲存工具索引
- [ ] `add_server()` 添加 Server
- [ ] `remove_server()` 移除 Server
- [ ] `connect_all()` 並行連接所有 Server
- [ ] `disconnect_all()` 斷開所有 Server
- [ ] `discover_tools()` 發現所有工具
- [ ] `execute_tool()` 執行指定工具
- [ ] `execute_tool()` 支援 "server:tool" 格式
- [ ] `_find_tool_server()` 搜尋工具所屬 Server
- [ ] `list_servers()` 列出 Server 狀態
- [ ] `health_check()` 健康檢查
- [ ] `__aenter__()` Context Manager
- [ ] `__aexit__()` Context Manager

### 工具發現機制
- [ ] 自動掃描所有已連接 Server
- [ ] 建立 tool_name → server 映射
- [ ] 支援重複工具名稱處理
- [ ] 工具快取機制

### 測試
- [ ] `test_manager_add_server` 通過
- [ ] `test_manager_remove_server` 通過
- [ ] `test_manager_connect_all` 通過
- [ ] `test_manager_connect_all_partial_failure` 通過
- [ ] `test_manager_discover_tools` 通過
- [ ] `test_manager_execute_tool_by_ref` 通過
- [ ] `test_manager_execute_tool_by_name` 通過
- [ ] `test_manager_health_check` 通過
- [ ] `test_manager_context_manager` 通過

---

## S50-3: Hybrid Orchestrator (12 點) 📋

### 檔案結構
- [ ] 建立 `backend/src/integrations/claude_sdk/hybrid/` 目錄
- [ ] 建立 `backend/src/integrations/claude_sdk/hybrid/__init__.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hybrid/orchestrator.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hybrid/capability.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hybrid/selector.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hybrid/types.py`

### TaskCapability 枚舉
- [ ] `MULTI_AGENT` 多代理協作
- [ ] `HANDOFF` 代理交接
- [ ] `FILE_OPERATIONS` 檔案操作
- [ ] `CODE_EXECUTION` 程式碼執行
- [ ] `WEB_SEARCH` 網頁搜尋
- [ ] `DATABASE_ACCESS` 資料庫存取
- [ ] `PLANNING` 任務規劃
- [ ] `CONVERSATION` 對話管理

### TaskAnalysis 類別
- [ ] `capabilities` 集合
- [ ] `complexity` 複雜度 (0.0-1.0)
- [ ] `recommended_framework` 推薦框架
- [ ] `confidence` 信心度

### CapabilityMatcher 實現
- [ ] `CAPABILITY_KEYWORDS` 關鍵字映射
- [ ] `FRAMEWORK_CAPABILITIES` 框架能力映射
- [ ] `analyze()` 分析任務提示
- [ ] `_select_framework()` 根據能力選擇框架
- [ ] 關鍵字識別正確
- [ ] 複雜度計算正確

### HybridResult 類別
- [ ] `content` 執行結果
- [ ] `framework_used` 使用的框架
- [ ] `tool_calls` 工具調用列表
- [ ] `tokens_used` Token 使用量
- [ ] `duration` 執行時間

### HybridOrchestrator 實現
- [ ] `__init__()` 接受 claude_client 參數
- [ ] `__init__()` 接受 ms_agent_service 參數
- [ ] `__init__()` 接受 capability_matcher 參數
- [ ] `execute()` 執行混合任務
- [ ] `execute()` 支援 force_framework 參數
- [ ] `execute()` 支援 session_id 參數
- [ ] `_execute_claude()` Claude SDK 執行
- [ ] `_execute_ms_agent()` Microsoft Agent 執行
- [ ] 上下文同步調用
- [ ] 執行時間記錄
- [ ] `create_hybrid_session()` 建立混合 Session

### FrameworkSelector 實現
- [ ] `TASK_FRAMEWORK_MAP` 任務類型映射
- [ ] `select()` 選擇框架
- [ ] 支援 task_type 參數
- [ ] 支援 capabilities 參數
- [ ] 支援 user_preference 參數
- [ ] 用戶偏好優先邏輯

### 測試
- [ ] `test_capability_matcher_analyze` 通過
- [ ] `test_capability_matcher_keywords` 通過
- [ ] `test_capability_matcher_framework_selection` 通過
- [ ] `test_orchestrator_init` 通過
- [ ] `test_orchestrator_execute_claude` 通過
- [ ] `test_orchestrator_execute_ms_agent` 通過
- [ ] `test_orchestrator_force_framework` 通過
- [ ] `test_orchestrator_auto_routing` 通過
- [ ] `test_framework_selector_task_type` 通過
- [ ] `test_framework_selector_capabilities` 通過
- [ ] `test_framework_selector_user_preference` 通過

---

## S50-4: Context Synchronizer (8 點) 📋

### 檔案結構
- [ ] 建立 `backend/src/integrations/claude_sdk/hybrid/sync.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hybrid/state.py`

### SharedContext 類別
- [ ] `session_id` 屬性
- [ ] `messages` 列表
- [ ] `tool_results` 列表
- [ ] `metadata` 字典
- [ ] `active_framework` 屬性
- [ ] `to_claude_format()` 轉換方法
- [ ] `to_ms_format()` 轉換方法

### ContextSynchronizer 實現
- [ ] `__init__()` 接受 redis_client 參數
- [ ] `_local_cache` 本地快取
- [ ] `get_context()` 獲取上下文
- [ ] `get_context()` 先查本地快取
- [ ] `get_context()` 再查 Redis
- [ ] `get_context()` 自動建立新上下文
- [ ] `save_context()` 儲存上下文
- [ ] `save_context()` 寫入 Redis
- [ ] `sync_to()` 同步到目標框架
- [ ] `add_message()` 添加訊息
- [ ] `add_message()` 包含 timestamp
- [ ] `add_message()` 包含 framework 標記
- [ ] `add_tool_result()` 添加工具結果
- [ ] `sync_result()` 同步執行結果
- [ ] `clear_context()` 清除上下文
- [ ] Redis TTL 設定 (2 小時)

### SharedState 類別
- [ ] `session_id` 屬性
- [ ] `current_agent` 屬性
- [ ] `workflow_status` 屬性
- [ ] `pending_approvals` 列表
- [ ] `error_count` 計數器
- [ ] `last_framework` 屬性

### StateManager 實現
- [ ] `__init__()` 接受 redis_client 參數
- [ ] `get_state()` 獲取狀態
- [ ] `update_state()` 更新狀態
- [ ] `transition_framework()` 記錄框架切換

### 測試
- [ ] `test_shared_context_to_claude_format` 通過
- [ ] `test_shared_context_to_ms_format` 通過
- [ ] `test_synchronizer_get_context_new` 通過
- [ ] `test_synchronizer_get_context_cached` 通過
- [ ] `test_synchronizer_get_context_redis` 通過
- [ ] `test_synchronizer_save_context` 通過
- [ ] `test_synchronizer_add_message` 通過
- [ ] `test_synchronizer_add_tool_result` 通過
- [ ] `test_synchronizer_sync_result` 通過
- [ ] `test_synchronizer_clear_context` 通過
- [ ] `test_state_manager_get_state` 通過
- [ ] `test_state_manager_update_state` 通過
- [ ] `test_state_manager_transition_framework` 通過

---

## 測試完成

### 單元測試
- [ ] `tests/unit/integrations/claude_sdk/mcp/test_base.py`
- [ ] `tests/unit/integrations/claude_sdk/mcp/test_stdio.py`
- [ ] `tests/unit/integrations/claude_sdk/mcp/test_http.py`
- [ ] `tests/unit/integrations/claude_sdk/mcp/test_manager.py`
- [ ] `tests/unit/integrations/claude_sdk/hybrid/test_capability.py`
- [ ] `tests/unit/integrations/claude_sdk/hybrid/test_orchestrator.py`
- [ ] `tests/unit/integrations/claude_sdk/hybrid/test_selector.py`
- [ ] `tests/unit/integrations/claude_sdk/hybrid/test_sync.py`
- [ ] `tests/unit/integrations/claude_sdk/hybrid/test_state.py`

### 整合測試
- [ ] `tests/integration/claude_sdk/test_mcp_servers.py`
- [ ] `tests/integration/claude_sdk/test_hybrid_workflow.py`

### 覆蓋率
- [ ] 單元測試覆蓋率 ≥ 85%
- [ ] 整合測試覆蓋率 ≥ 70%

---

## 文檔完成

- [ ] MCP Server API 文檔
- [ ] Hybrid Architecture 設計文檔
- [ ] 框架選擇指南
- [ ] Context 同步機制說明
- [ ] 整合範例程式碼

---

## Sprint 完成標準

- [ ] 所有 checkbox 完成
- [ ] 所有測試通過
- [ ] Code Review 完成
- [ ] 安全審查完成
- [ ] 無 Critical/High Bug
- [ ] 文檔更新完成

---

## 依賴確認

### 外部依賴
- [ ] `aiohttp` 套件安裝
- [ ] Redis 服務運行中
- [ ] Sprint 48-49 完成

### 內部依賴
- [ ] ClaudeSDKClient 可正常運作
- [ ] Tools 系統可正常運作
- [ ] Hooks 系統可正常運作
- [ ] Microsoft Agent Framework 整合完成

---

## 完成統計表

| Story | 點數 | 狀態 | 完成日期 |
|-------|------|------|----------|
| S50-1 | 10 | 📋 | - |
| S50-2 | 8 | 📋 | - |
| S50-3 | 12 | 📋 | - |
| S50-4 | 8 | 📋 | - |
| **總計** | **38** | **0%** | - |
