# Sprint 39 Checklist: MCP Core Framework

**Sprint 目標**: 建立 MCP (Model Context Protocol) 核心架構，為所有執行工具提供統一的基礎設施
**總點數**: 40 Story Points
**狀態**: 📋 計劃中
**前置條件**: Phase 8 完成
**開始日期**: TBD

---

## 前置條件檢查

### Phase 8 完成確認
- [ ] Code Interpreter 功能可用
- [ ] CodeInterpreterTool 整合完成
- [ ] 文件上傳/下載功能正常

### 環境準備
- [ ] 安裝 MCP 相關依賴
  ```bash
  pip install mcp pyyaml aiofiles
  ```
- [ ] 確認 Python 版本 >= 3.10

---

## Story Checklist

### S39-1: MCP 核心協議實現 (10 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 閱讀 MCP 規範文檔
- [ ] 確認 JSON-RPC 2.0 格式

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/integrations/mcp/`
- [ ] 創建 `backend/src/integrations/mcp/__init__.py`
- [ ] 創建 `backend/src/integrations/mcp/core/`
- [ ] 創建 `backend/src/integrations/mcp/core/__init__.py`

**實現類型定義** (`core/types.py`)
- [ ] `ToolInputType` 枚舉
- [ ] `ToolParameter` 數據類
- [ ] `ToolSchema` 數據類
  - [ ] `to_mcp_format()` 方法
- [ ] `ToolResult` 數據類
  - [ ] `to_mcp_format()` 方法
- [ ] `MCPRequest` 數據類
- [ ] `MCPResponse` 數據類

**實現協議處理器** (`core/protocol.py`)
- [ ] `MCPProtocol` 類
  - [ ] `register_tool()` 方法
  - [ ] `handle_request()` 方法
  - [ ] `_handle_initialize()` 方法
  - [ ] `_handle_tools_list()` 方法
  - [ ] `_handle_tools_call()` 方法
  - [ ] `create_request()` 方法

**實現傳輸層** (`core/transport.py`)
- [ ] `BaseTransport` 抽象基類
- [ ] `StdioTransport` 類
  - [ ] `start()` 方法
  - [ ] `stop()` 方法
  - [ ] `send()` 方法

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/test_types.py`
- [ ] 創建 `tests/unit/integrations/mcp/test_protocol.py`
- [ ] 測試 `ToolSchema.to_mcp_format()`
- [ ] 測試 `MCPProtocol.handle_request()`

#### 驗證
```bash
python -m py_compile src/integrations/mcp/core/types.py
python -m py_compile src/integrations/mcp/core/protocol.py
python -m py_compile src/integrations/mcp/core/transport.py
pytest tests/unit/integrations/mcp/test_types.py -v
pytest tests/unit/integrations/mcp/test_protocol.py -v
```

---

### S39-2: MCP Client 實現 (10 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S39-1 完成
- [ ] 確認傳輸層正常工作

#### 實現任務

**實現 ServerConfig** (`core/client.py`)
- [ ] `ServerConfig` 數據類
  - [ ] name, command, args, env, transport 屬性

**實現 MCPClient** (`core/client.py`)
- [ ] `MCPClient` 類
  - [ ] `__init__()` 初始化
  - [ ] `connect()` 連接到 Server
  - [ ] `disconnect()` 斷開連接
  - [ ] `list_tools()` 列出工具
  - [ ] `call_tool()` 調用工具
  - [ ] `_parse_tool_schema()` 解析 Schema
  - [ ] `connected_servers` 屬性
  - [ ] `close()` 關閉所有連接

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/test_client.py`
- [ ] 測試 `MCPClient.connect()`
- [ ] 測試 `MCPClient.list_tools()`
- [ ] 測試 `MCPClient.call_tool()`
- [ ] 測試錯誤處理

#### 驗證
```bash
python -m py_compile src/integrations/mcp/core/client.py
pytest tests/unit/integrations/mcp/test_client.py -v
```

---

### S39-3: MCP Server 註冊表 (8 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S39-2 完成

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/integrations/mcp/registry/`
- [ ] 創建 `backend/src/integrations/mcp/registry/__init__.py`

**實現 ServerMetadata** (`registry/server_registry.py`)
- [ ] `ServerMetadata` 數據類
  - [ ] name, description, version, category
  - [ ] risk_level, enabled, config

**實現 MCPServerRegistry** (`registry/server_registry.py`)
- [ ] `register()` 方法
- [ ] `unregister()` 方法
- [ ] `get()` 方法
- [ ] `list_servers()` 方法
- [ ] `get_servers_by_category()` 方法
- [ ] `get_servers_by_risk_level()` 方法
- [ ] `set_enabled()` 方法
- [ ] `load_from_yaml()` 方法
- [ ] `save_to_yaml()` 方法

**創建配置文件**
- [ ] 創建 `backend/config/mcp-servers.yaml`
- [ ] 添加預設 Server 配置

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/test_server_registry.py`
- [ ] 測試 `register()/unregister()`
- [ ] 測試 `list_servers()`
- [ ] 測試 `load_from_yaml()`

#### 驗證
```bash
python -m py_compile src/integrations/mcp/registry/server_registry.py
pytest tests/unit/integrations/mcp/test_server_registry.py -v
```

---

### S39-4: 權限與審計系統 (8 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S39-3 完成

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/integrations/mcp/security/`
- [ ] 創建 `backend/src/integrations/mcp/security/__init__.py`

**實現權限系統** (`security/permissions.py`)
- [ ] `RiskLevel` 枚舉
- [ ] `ApprovalRequirement` 枚舉
- [ ] `ToolPermission` 數據類
- [ ] `PermissionCheckResult` 數據類
- [ ] `MCPPermissionManager` 類
  - [ ] `set_permission()` 方法
  - [ ] `get_permission()` 方法
  - [ ] `check_permission()` 方法
  - [ ] `_check_condition()` 方法
  - [ ] `set_default_policy()` 方法

**實現審計日誌** (`security/audit.py`)
- [ ] `AuditEventType` 枚舉
- [ ] `AuditEvent` 數據類
- [ ] `MCPAuditLogger` 類
  - [ ] `log_tool_call()` 方法
  - [ ] `log_tool_result()` 方法
  - [ ] `log_permission_check()` 方法
  - [ ] `query()` 方法
  - [ ] `_sanitize_arguments()` 方法

**整合到 MCPClient**
- [ ] 調用前權限檢查
- [ ] 調用後審計記錄

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/test_permissions.py`
- [ ] 創建 `tests/unit/integrations/mcp/test_audit.py`
- [ ] 測試權限檢查邏輯
- [ ] 測試審計記錄
- [ ] 測試敏感信息過濾

#### 驗證
```bash
python -m py_compile src/integrations/mcp/security/permissions.py
python -m py_compile src/integrations/mcp/security/audit.py
pytest tests/unit/integrations/mcp/test_permissions.py -v
pytest tests/unit/integrations/mcp/test_audit.py -v
```

---

### S39-5: MCP 管理 API (4 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S39-4 完成

#### 實現任務

**創建 API 目錄**
- [ ] 創建 `backend/src/api/v1/mcp/`
- [ ] 創建 `backend/src/api/v1/mcp/__init__.py`

**實現 API 路由** (`api/v1/mcp/routes.py`)
- [ ] `ServerStatusResponse` Schema
- [ ] `ToolListResponse` Schema
- [ ] `GET /mcp/servers` - 列出 Server
- [ ] `POST /mcp/servers/{name}/connect` - 連接
- [ ] `POST /mcp/servers/{name}/disconnect` - 斷開
- [ ] `GET /mcp/servers/{name}/tools` - 列出工具
- [ ] `GET /mcp/audit` - 查詢審計日誌

**更新路由註冊**
- [ ] 更新 `api/v1/__init__.py`

#### API 測試
```bash
# 列出 Server
curl http://localhost:8000/api/v1/mcp/servers

# 連接 Server
curl -X POST http://localhost:8000/api/v1/mcp/servers/azure-mcp/connect

# 列出工具
curl http://localhost:8000/api/v1/mcp/servers/azure-mcp/tools

# 查詢審計日誌
curl http://localhost:8000/api/v1/mcp/audit
```

#### 驗證
```bash
python -m py_compile src/api/v1/mcp/routes.py
pytest tests/unit/api/v1/test_mcp.py -v
```

---

## 驗證命令匯總

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/mcp/core/types.py
python -m py_compile src/integrations/mcp/core/protocol.py
python -m py_compile src/integrations/mcp/core/transport.py
python -m py_compile src/integrations/mcp/core/client.py
python -m py_compile src/integrations/mcp/registry/server_registry.py
python -m py_compile src/integrations/mcp/security/permissions.py
python -m py_compile src/integrations/mcp/security/audit.py
python -m py_compile src/api/v1/mcp/routes.py
# 預期: 無輸出 (無錯誤)

# 2. 類型檢查
mypy src/integrations/mcp/
# 預期: Success

# 3. 代碼風格
black src/integrations/mcp/ --check
isort src/integrations/mcp/ --check
# 預期: 無需修改

# 4. 運行單元測試
pytest tests/unit/integrations/mcp/ -v --cov=src/integrations/mcp
# 預期: 全部通過，覆蓋率 > 85%

# 5. API 測試
curl http://localhost:8000/api/v1/mcp/servers
# 預期: {"servers": [...]}
```

---

## 完成定義

- [ ] 所有 S39 Story 完成
- [ ] MCP 核心協議實現完成
- [ ] MCPClient 可以連接和調用工具
- [ ] Server 註冊表功能完整
- [ ] 權限和審計系統運作正常
- [ ] 管理 API 可用
- [ ] 測試覆蓋率 > 85%
- [ ] 代碼審查完成
- [ ] 語法/類型/風格檢查全部通過

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `src/integrations/mcp/__init__.py` | 新增 | MCP 模組初始化 |
| `src/integrations/mcp/core/types.py` | 新增 | MCP 類型定義 |
| `src/integrations/mcp/core/protocol.py` | 新增 | MCP 協議處理器 |
| `src/integrations/mcp/core/transport.py` | 新增 | 傳輸層實現 |
| `src/integrations/mcp/core/client.py` | 新增 | MCP 客戶端 |
| `src/integrations/mcp/registry/server_registry.py` | 新增 | Server 註冊表 |
| `src/integrations/mcp/security/permissions.py` | 新增 | 權限系統 |
| `src/integrations/mcp/security/audit.py` | 新增 | 審計日誌 |
| `src/api/v1/mcp/routes.py` | 新增 | MCP 管理 API |
| `config/mcp-servers.yaml` | 新增 | Server 配置文件 |
| `tests/unit/integrations/mcp/` | 新增 | 單元測試 |

---

## 備註

### MCP 規範參考
- 官方文檔: https://modelcontextprotocol.io/
- JSON-RPC 2.0: https://www.jsonrpc.org/specification

### 風險等級說明
| 等級 | 說明 | 審批需求 |
|------|------|---------|
| 1 (LOW) | 只讀操作 | 自動執行 |
| 2 (MEDIUM) | 低風險寫操作 | Agent 確認 |
| 3 (HIGH) | 高風險操作 | 人工審批 |

### 下一步
- Sprint 40: Azure MCP Server 實現
- Sprint 41: 其他 MCP Server 實現

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
