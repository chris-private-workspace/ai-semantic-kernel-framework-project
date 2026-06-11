# Sprint 41 Checklist: Additional MCP Servers

**Sprint 目標**: 實現 Shell、Filesystem、SSH、LDAP MCP Servers
**總點數**: 35 Story Points
**狀態**: 📋 計劃中
**前置條件**: Sprint 40 完成
**開始日期**: TBD

---

## 前置條件檢查

### Sprint 40 完成確認
- [ ] Azure MCP Server 可用
- [ ] MCP Client 可以連接多個 Server
- [ ] 權限和審計系統正常運作

### 環境準備
- [ ] 安裝依賴套件
  ```bash
  pip install asyncssh aiofiles ldap3
  ```
- [ ] 配置 SSH 測試環境 (可選)
- [ ] 配置 LDAP 測試環境 (可選)

---

## Story Checklist

### S41-1: Shell MCP Server (10 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 確認 PowerShell/Bash 可用
- [ ] 確定命令白名單策略

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/integrations/mcp/servers/shell/`
- [ ] 創建 `backend/src/integrations/mcp/servers/shell/__init__.py`

**實現 ShellConfig** (`servers/shell/executor.py`)
- [ ] `ShellType` 枚舉 (POWERSHELL, BASH, CMD)
- [ ] `ShellConfig` 數據類
  - [ ] `shell_type` 屬性
  - [ ] `timeout_seconds` 屬性
  - [ ] `max_output_size` 屬性
  - [ ] `working_directory` 屬性
  - [ ] `allowed_commands` 屬性
  - [ ] `blocked_commands` 屬性

**實現 CommandResult** (`servers/shell/executor.py`)
- [ ] `CommandResult` 數據類
  - [ ] `exit_code` 屬性
  - [ ] `stdout` 屬性
  - [ ] `stderr` 屬性
  - [ ] `execution_time` 屬性
  - [ ] `truncated` 屬性

**實現 ShellExecutor** (`servers/shell/executor.py`)
- [ ] `DEFAULT_BLOCKED` 黑名單
- [ ] `__init__(config)` 初始化
- [ ] `_validate_config()` 驗證配置
- [ ] `execute(command, env)` 執行命令
  - [ ] 命令安全檢查
  - [ ] 構建 Shell 命令
  - [ ] 異步執行
  - [ ] 超時處理
  - [ ] 輸出截斷
- [ ] `_validate_command(command)` 命令驗證
  - [ ] 黑名單檢查
  - [ ] 白名單檢查 (如配置)
- [ ] `_build_shell_command(command)` 構建命令
- [ ] `_truncate_output(output)` 截斷輸出

**實現 ShellTools** (`servers/shell/tools.py`)
- [ ] `get_tool_schemas()` 返回工具定義
- [ ] `run_command(command, timeout)` 執行命令
- [ ] `run_script(script_path, arguments)` 執行腳本

**實現 ShellMCPServer** (`servers/shell/server.py`)
- [ ] 初始化和工具註冊
- [ ] `list_tools()` 返回所有工具
- [ ] `call_tool()` 執行工具調用
- [ ] `run()` 啟動 Server

**更新配置**
- [ ] 在 `mcp-servers.yaml` 添加 Shell Server

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/shell/test_executor.py`
- [ ] 創建 `tests/unit/integrations/mcp/shell/test_tools.py`
- [ ] 測試命令執行
- [ ] 測試黑名單阻止
- [ ] 測試超時處理
- [ ] 測試輸出截斷

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/shell/executor.py
python -m py_compile src/integrations/mcp/servers/shell/tools.py
python -m py_compile src/integrations/mcp/servers/shell/server.py
pytest tests/unit/integrations/mcp/shell/ -v
```

---

### S41-2: Filesystem MCP Server (8 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 確定沙箱根目錄
- [ ] 確定允許的文件類型

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/integrations/mcp/servers/filesystem/`
- [ ] 創建 `backend/src/integrations/mcp/servers/filesystem/__init__.py`

**實現 FilesystemSandbox** (`servers/filesystem/sandbox.py`)
- [ ] `__init__(allowed_roots, max_file_size, allowed_extensions)`
- [ ] `validate_path(path)` 路徑驗證
  - [ ] 解析絕對路徑
  - [ ] 檢查是否在允許範圍
  - [ ] 檢查擴展名
- [ ] `_is_subpath(path, root)` 子路徑檢查
- [ ] `validate_file_size(size)` 大小驗證

**實現 FilesystemTools** (`servers/filesystem/tools.py`)
- [ ] `__init__(sandbox)` 初始化
- [ ] `read_file(path, encoding)` 讀取文件
  - [ ] 路徑驗證
  - [ ] 異步讀取
  - [ ] 編碼處理
- [ ] `write_file(path, content, encoding, create_backup)` 寫入文件
  - [ ] 路徑驗證
  - [ ] 大小驗證
  - [ ] 備份創建
  - [ ] 異步寫入
- [ ] `list_directory(path, pattern)` 列出目錄
  - [ ] 路徑驗證
  - [ ] Glob 模式支援
  - [ ] 返回文件信息
- [ ] `file_info(path)` 獲取文件信息
  - [ ] 路徑驗證
  - [ ] 返回詳細信息
- [ ] `delete_file(path, confirm)` 刪除文件 (需確認)
- [ ] `create_directory(path)` 創建目錄

**實現 FilesystemMCPServer** (`servers/filesystem/server.py`)
- [ ] 初始化和工具註冊
- [ ] `list_tools()` 返回所有工具
- [ ] `call_tool()` 執行工具調用
- [ ] `run()` 啟動 Server

**更新配置**
- [ ] 在 `mcp-servers.yaml` 添加 Filesystem Server

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/filesystem/test_sandbox.py`
- [ ] 創建 `tests/unit/integrations/mcp/filesystem/test_tools.py`
- [ ] 測試沙箱路徑驗證
- [ ] 測試路徑穿越阻止
- [ ] 測試文件讀寫
- [ ] 測試備份創建

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/filesystem/sandbox.py
python -m py_compile src/integrations/mcp/servers/filesystem/tools.py
python -m py_compile src/integrations/mcp/servers/filesystem/server.py
pytest tests/unit/integrations/mcp/filesystem/ -v
```

---

### S41-3: SSH MCP Server (10 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 確認 asyncssh 安裝
- [ ] 準備測試 SSH 環境 (可選)

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/integrations/mcp/servers/ssh/`
- [ ] 創建 `backend/src/integrations/mcp/servers/ssh/__init__.py`

**實現 SSHConfig** (`servers/ssh/connection.py`)
- [ ] `SSHConfig` 數據類
  - [ ] `host` 屬性
  - [ ] `port` 屬性 (預設 22)
  - [ ] `username` 屬性
  - [ ] `password` 屬性 (可選)
  - [ ] `private_key_path` 屬性 (可選)
  - [ ] `known_hosts` 屬性 (可選)
  - [ ] `timeout` 屬性
  - [ ] `keepalive_interval` 屬性

**實現 SSHConnectionPool** (`servers/ssh/connection.py`)
- [ ] `__init__(max_connections)` 初始化
- [ ] `_get_key(config)` 生成連接 key
- [ ] `get_connection(config)` 獲取或創建連接
  - [ ] 檢查現有連接
  - [ ] 連接有效性檢查
  - [ ] 創建新連接
- [ ] `_create_connection(config)` 創建 SSH 連接
  - [ ] 密碼認證
  - [ ] 金鑰認證
  - [ ] 超時處理
- [ ] `close_all()` 關閉所有連接

**實現 SSHTools** (`servers/ssh/tools.py`)
- [ ] `__init__(connection_pool)` 初始化
- [ ] `execute_command()` 執行遠端命令
  - [ ] 連接管理
  - [ ] 命令執行
  - [ ] 超時處理
  - [ ] 結果返回
- [ ] `upload_file()` 上傳文件
  - [ ] SFTP 連接
  - [ ] 文件傳輸
  - [ ] 進度回報 (可選)
- [ ] `download_file()` 下載文件
  - [ ] SFTP 連接
  - [ ] 文件傳輸
  - [ ] 本地存儲
- [ ] `list_remote_directory()` 列出遠端目錄

**實現 SSHMCPServer** (`servers/ssh/server.py`)
- [ ] 初始化和工具註冊
- [ ] `list_tools()` 返回所有工具
- [ ] `call_tool()` 執行工具調用
- [ ] `run()` 啟動 Server

**更新配置**
- [ ] 在 `mcp-servers.yaml` 添加 SSH Server

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/ssh/test_connection.py`
- [ ] 創建 `tests/unit/integrations/mcp/ssh/test_tools.py`
- [ ] 測試連接池管理 (mock)
- [ ] 測試命令執行 (mock)
- [ ] 測試認證方式
- [ ] 測試超時處理

#### 整合測試 (需要 SSH 環境)
- [ ] 創建 `tests/integration/mcp/test_ssh_integration.py`
- [ ] 測試真實 SSH 連接
- [ ] 測試文件傳輸

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/ssh/connection.py
python -m py_compile src/integrations/mcp/servers/ssh/tools.py
python -m py_compile src/integrations/mcp/servers/ssh/server.py
pytest tests/unit/integrations/mcp/ssh/ -v
```

---

### S41-4: LDAP MCP Server (7 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 確認 ldap3 安裝
- [ ] 準備 LDAP 測試環境 (可選)

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/integrations/mcp/servers/ldap/`
- [ ] 創建 `backend/src/integrations/mcp/servers/ldap/__init__.py`

**實現 LDAPConfig** (`servers/ldap/client.py`)
- [ ] `LDAPConfig` 數據類
  - [ ] `server` 屬性
  - [ ] `port` 屬性 (預設 389)
  - [ ] `use_ssl` 屬性 (預設 False)
  - [ ] `bind_dn` 屬性
  - [ ] `bind_password` 屬性
  - [ ] `base_dn` 屬性
  - [ ] `timeout` 屬性

**實現 LDAPClient** (`servers/ldap/client.py`)
- [ ] `__init__(config)` 初始化
- [ ] `connect()` 建立連接
  - [ ] 創建 Server
  - [ ] 創建 Connection
  - [ ] 綁定認證
- [ ] `disconnect()` 關閉連接
- [ ] `search(search_filter, attributes, search_base, search_scope)` 搜索
  - [ ] 執行搜索
  - [ ] 解析結果
  - [ ] 返回格式化數據

**實現 LDAPTools** (`servers/ldap/tools.py`)
- [ ] `__init__(client)` 初始化
- [ ] `search_users(filter_expr, attributes)` 搜索用戶
  - [ ] 預設屬性列表
  - [ ] 過濾器處理
- [ ] `get_user(username)` 獲取用戶詳情
  - [ ] sAMAccountName 查詢
  - [ ] 完整屬性返回
- [ ] `search_groups(filter_expr, attributes)` 搜索群組
  - [ ] 群組屬性
  - [ ] 成員列表
- [ ] `get_user_groups(username)` 獲取用戶群組
  - [ ] memberOf 屬性解析

**實現 LDAPMCPServer** (`servers/ldap/server.py`)
- [ ] 初始化和工具註冊
- [ ] `list_tools()` 返回所有工具
- [ ] `call_tool()` 執行工具調用
- [ ] `run()` 啟動 Server

**更新配置**
- [ ] 在 `mcp-servers.yaml` 添加 LDAP Server

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/ldap/test_client.py`
- [ ] 創建 `tests/unit/integrations/mcp/ldap/test_tools.py`
- [ ] 測試連接管理 (mock)
- [ ] 測試用戶搜索 (mock)
- [ ] 測試群組搜索 (mock)

#### 整合測試 (需要 LDAP 環境)
- [ ] 創建 `tests/integration/mcp/test_ldap_integration.py`
- [ ] 測試真實 LDAP 連接
- [ ] 測試 AD 用戶查詢

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/ldap/client.py
python -m py_compile src/integrations/mcp/servers/ldap/tools.py
python -m py_compile src/integrations/mcp/servers/ldap/server.py
pytest tests/unit/integrations/mcp/ldap/ -v
```

---

## 驗證命令匯總

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/mcp/servers/shell/executor.py
python -m py_compile src/integrations/mcp/servers/shell/tools.py
python -m py_compile src/integrations/mcp/servers/shell/server.py
python -m py_compile src/integrations/mcp/servers/filesystem/sandbox.py
python -m py_compile src/integrations/mcp/servers/filesystem/tools.py
python -m py_compile src/integrations/mcp/servers/filesystem/server.py
python -m py_compile src/integrations/mcp/servers/ssh/connection.py
python -m py_compile src/integrations/mcp/servers/ssh/tools.py
python -m py_compile src/integrations/mcp/servers/ssh/server.py
python -m py_compile src/integrations/mcp/servers/ldap/client.py
python -m py_compile src/integrations/mcp/servers/ldap/tools.py
python -m py_compile src/integrations/mcp/servers/ldap/server.py
# 預期: 無輸出 (無錯誤)

# 2. 類型檢查
mypy src/integrations/mcp/servers/
# 預期: Success

# 3. 代碼風格
black src/integrations/mcp/servers/ --check
isort src/integrations/mcp/servers/ --check
# 預期: 無需修改

# 4. 運行單元測試
pytest tests/unit/integrations/mcp/ -v --cov=src/integrations/mcp/servers
# 預期: 全部通過，覆蓋率 > 85%

# 5. 安全測試
pytest tests/security/mcp/ -v
# 預期: 全部通過
```

---

## 完成定義

- [ ] 所有 S41 Story 完成
- [ ] Shell MCP Server 可安全執行命令
- [ ] Filesystem MCP Server 可安全操作文件
- [ ] SSH MCP Server 可連接遠端主機
- [ ] LDAP MCP Server 可查詢用戶/群組
- [ ] 所有 Server 已整合到 mcp-servers.yaml
- [ ] 測試覆蓋率 > 85%
- [ ] 安全測試通過
- [ ] 代碼審查完成

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `servers/shell/__init__.py` | 新增 | Shell Server 模組 |
| `servers/shell/executor.py` | 新增 | Shell 執行器 |
| `servers/shell/tools.py` | 新增 | Shell 工具 |
| `servers/shell/server.py` | 新增 | Shell MCP Server |
| `servers/filesystem/__init__.py` | 新增 | Filesystem Server 模組 |
| `servers/filesystem/sandbox.py` | 新增 | 文件系統沙箱 |
| `servers/filesystem/tools.py` | 新增 | Filesystem 工具 |
| `servers/filesystem/server.py` | 新增 | Filesystem MCP Server |
| `servers/ssh/__init__.py` | 新增 | SSH Server 模組 |
| `servers/ssh/connection.py` | 新增 | SSH 連接池 |
| `servers/ssh/tools.py` | 新增 | SSH 工具 |
| `servers/ssh/server.py` | 新增 | SSH MCP Server |
| `servers/ldap/__init__.py` | 新增 | LDAP Server 模組 |
| `servers/ldap/client.py` | 新增 | LDAP 客戶端 |
| `servers/ldap/tools.py` | 新增 | LDAP 工具 |
| `servers/ldap/server.py` | 新增 | LDAP MCP Server |
| `config/mcp-servers.yaml` | 更新 | 添加所有 Server 配置 |
| `tests/unit/integrations/mcp/` | 新增 | 單元測試 |
| `tests/security/mcp/` | 新增 | 安全測試 |

---

## 安全注意事項

### Shell 安全
- 嚴格的命令白名單
- 阻止 Shell 注入
- 限制執行時間和輸出大小
- 隔離工作目錄

### Filesystem 安全
- 沙箱限制訪問範圍
- 阻止路徑穿越攻擊
- 限制文件大小
- 寫入操作需審批

### SSH 安全
- 憑證安全存儲
- 連接加密
- 命令審計
- 高風險操作需人工審批

### LDAP 安全
- 綁定密碼安全存儲
- 查詢結果過濾敏感屬性
- 連接超時控制

---

## 下一步

- Phase 10: Session Mode API
- 整合 MCP Servers 到 Agent 工作流

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
