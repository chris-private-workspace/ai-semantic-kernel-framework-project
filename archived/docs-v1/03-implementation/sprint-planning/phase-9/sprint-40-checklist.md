# Sprint 40 Checklist: Azure MCP Server

**Sprint 目標**: 實現 Azure MCP Server，提供 Azure 資源管理和監控能力
**總點數**: 35 Story Points
**狀態**: 📋 計劃中
**前置條件**: Sprint 39 完成
**開始日期**: TBD

---

## 前置條件檢查

### Sprint 39 完成確認
- [ ] MCP 核心協議可用
- [ ] MCPClient 可以連接到 Server
- [ ] 權限和審計系統運作正常

### 環境準備
- [ ] 安裝 Azure SDK 依賴
  ```bash
  pip install azure-identity azure-mgmt-compute azure-mgmt-resource azure-mgmt-network azure-mgmt-monitor azure-mgmt-storage
  ```
- [ ] 配置 Azure 服務主體
  ```bash
  # .env 配置
  AZURE_TENANT_ID=<tenant-id>
  AZURE_CLIENT_ID=<client-id>
  AZURE_CLIENT_SECRET=<client-secret>
  AZURE_SUBSCRIPTION_ID=<subscription-id>
  ```
- [ ] 驗證 Azure 連接
  ```bash
  az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
  az account show
  ```

---

## Story Checklist

### S40-1: Azure 客戶端管理器 (8 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 確認 Azure SDK 版本
- [ ] 閱讀 Azure Identity 文檔

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/integrations/mcp/servers/azure/`
- [ ] 創建 `backend/src/integrations/mcp/servers/azure/__init__.py`

**實現 AzureCredentialProvider** (`servers/azure/client.py`)
- [ ] `AzureCredentialProvider` 類
  - [ ] `get_credential()` 方法 (DefaultAzureCredential)
  - [ ] `get_subscription_id()` 方法
  - [ ] 環境變數驗證

**實現 AzureClientManager** (`servers/azure/client.py`)
- [ ] `AzureClientManager` 類
  - [ ] `__init__()` 初始化
  - [ ] `compute_client` 屬性 (ComputeManagementClient)
  - [ ] `resource_client` 屬性 (ResourceManagementClient)
  - [ ] `network_client` 屬性 (NetworkManagementClient)
  - [ ] `monitor_client` 屬性 (MonitorManagementClient)
  - [ ] `storage_client` 屬性 (StorageManagementClient)
  - [ ] `_get_or_create_client()` 延遲初始化
  - [ ] `validate_connection()` 連接驗證

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/azure/test_client.py`
- [ ] 測試憑證獲取
- [ ] 測試客戶端延遲初始化
- [ ] 測試連接驗證 (mock)

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/azure/client.py
pytest tests/unit/integrations/mcp/azure/test_client.py -v
```

---

### S40-2: VM 管理工具 (10 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S40-1 完成
- [ ] 確認 VM API 權限

#### 實現任務

**創建工具目錄**
- [ ] 創建 `backend/src/integrations/mcp/servers/azure/tools/`
- [ ] 創建 `backend/src/integrations/mcp/servers/azure/tools/__init__.py`

**實現 VMTools** (`servers/azure/tools/vm.py`)
- [ ] `VMTools` 類
  - [ ] `__init__(client_manager)` 初始化

**實現 list_vms 工具**
- [ ] `list_vms()` 方法
  - [ ] 參數: `resource_group` (optional)
  - [ ] 返回: VM 列表 (name, status, size, location)
  - [ ] 風險等級: LOW
  - [ ] 錯誤處理

**實現 get_vm 工具**
- [ ] `get_vm()` 方法
  - [ ] 參數: `resource_group`, `vm_name`
  - [ ] 返回: VM 詳細信息
  - [ ] 風險等級: LOW

**實現 start_vm 工具**
- [ ] `start_vm()` 方法
  - [ ] 參數: `resource_group`, `vm_name`
  - [ ] 返回: 操作結果
  - [ ] 風險等級: MEDIUM
  - [ ] 異步輪詢等待完成

**實現 stop_vm 工具**
- [ ] `stop_vm()` 方法
  - [ ] 參數: `resource_group`, `vm_name`, `deallocate` (bool)
  - [ ] 返回: 操作結果
  - [ ] 風險等級: MEDIUM

**實現 restart_vm 工具**
- [ ] `restart_vm()` 方法
  - [ ] 參數: `resource_group`, `vm_name`
  - [ ] 返回: 操作結果
  - [ ] 風險等級: MEDIUM

**實現 run_command 工具**
- [ ] `run_command()` 方法
  - [ ] 參數: `resource_group`, `vm_name`, `command`, `parameters`
  - [ ] 返回: 命令輸出
  - [ ] 風險等級: HIGH
  - [ ] 命令白名單驗證

**實現工具註冊**
- [ ] `get_tool_schemas()` 返回所有工具 Schema
- [ ] `execute_tool()` 統一執行入口

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/azure/test_vm_tools.py`
- [ ] 測試 `list_vms()` (mock Azure API)
- [ ] 測試 `start_vm()` (mock Azure API)
- [ ] 測試 `run_command()` 命令驗證
- [ ] 測試錯誤處理

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/azure/tools/vm.py
pytest tests/unit/integrations/mcp/azure/test_vm_tools.py -v
```

---

### S40-3: 資源管理工具 (7 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S40-2 完成

#### 實現任務

**實現 ResourceTools** (`servers/azure/tools/resource.py`)
- [ ] `ResourceTools` 類
  - [ ] `__init__(client_manager)` 初始化

**實現 list_resource_groups 工具**
- [ ] `list_resource_groups()` 方法
  - [ ] 返回: 資源群組列表
  - [ ] 風險等級: LOW

**實現 get_resource_group 工具**
- [ ] `get_resource_group()` 方法
  - [ ] 參數: `name`
  - [ ] 返回: 資源群組詳情
  - [ ] 風險等級: LOW

**實現 list_resources 工具**
- [ ] `list_resources()` 方法
  - [ ] 參數: `resource_group`, `resource_type` (optional)
  - [ ] 返回: 資源列表
  - [ ] 風險等級: LOW

**實現 get_resource 工具**
- [ ] `get_resource()` 方法
  - [ ] 參數: `resource_id`
  - [ ] 返回: 資源詳情
  - [ ] 風險等級: LOW

**實現 list_resource_tags 工具**
- [ ] `list_resource_tags()` 方法
  - [ ] 參數: `resource_id`
  - [ ] 返回: 標籤列表
  - [ ] 風險等級: LOW

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/azure/test_resource_tools.py`
- [ ] 測試資源群組列表
- [ ] 測試資源過濾

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/azure/tools/resource.py
pytest tests/unit/integrations/mcp/azure/test_resource_tools.py -v
```

---

### S40-4: 監控工具 (6 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S40-3 完成

#### 實現任務

**實現 MonitorTools** (`servers/azure/tools/monitor.py`)
- [ ] `MonitorTools` 類
  - [ ] `__init__(client_manager)` 初始化

**實現 get_metrics 工具**
- [ ] `get_metrics()` 方法
  - [ ] 參數: `resource_id`, `metric_names`, `timespan`, `interval`
  - [ ] 返回: 指標數據
  - [ ] 風險等級: LOW
  - [ ] 支援常見指標:
    - [ ] CPU 使用率
    - [ ] 記憶體使用率
    - [ ] 磁盤 IOPS
    - [ ] 網路流量

**實現 list_alerts 工具**
- [ ] `list_alerts()` 方法
  - [ ] 參數: `resource_group` (optional), `severity` (optional)
  - [ ] 返回: 警報列表
  - [ ] 風險等級: LOW

**實現 get_activity_logs 工具**
- [ ] `get_activity_logs()` 方法
  - [ ] 參數: `resource_group`, `start_time`, `end_time`
  - [ ] 返回: 活動日誌
  - [ ] 風險等級: LOW

**實現 get_diagnostic_settings 工具**
- [ ] `get_diagnostic_settings()` 方法
  - [ ] 參數: `resource_id`
  - [ ] 返回: 診斷設定
  - [ ] 風險等級: LOW

#### 單元測試
- [ ] 創建 `tests/unit/integrations/mcp/azure/test_monitor_tools.py`
- [ ] 測試指標查詢
- [ ] 測試時間範圍驗證
- [ ] 測試警報過濾

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/azure/tools/monitor.py
pytest tests/unit/integrations/mcp/azure/test_monitor_tools.py -v
```

---

### S40-5: Azure MCP Server 整合 (4 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S40-4 完成

#### 實現任務

**實現 AzureMCPServer** (`servers/azure/server.py`)
- [ ] `AzureMCPServer` 類
  - [ ] `__init__()` 初始化
    - [ ] 創建 AzureClientManager
    - [ ] 註冊所有工具類
  - [ ] `initialize()` MCP 初始化處理
  - [ ] `list_tools()` 返回所有工具
  - [ ] `call_tool()` 執行工具調用
    - [ ] 路由到正確的工具類
    - [ ] 權限檢查
    - [ ] 審計日誌
  - [ ] `run()` 啟動 Server (Stdio)

**更新 mcp-servers.yaml**
- [ ] 添加 Azure MCP Server 配置
  ```yaml
  azure-mcp:
    name: azure-mcp
    description: Azure Resource Management
    command: python
    args: ["-m", "src.integrations.mcp.servers.azure.server"]
    category: cloud
    risk_level: 2
    enabled: true
    tools:
      - list_vms
      - get_vm
      - start_vm
      - stop_vm
      - restart_vm
      - run_command
      - list_resource_groups
      - get_resource_group
      - list_resources
      - get_resource
      - get_metrics
      - list_alerts
      - get_activity_logs
  ```

**實現主入口**
- [ ] `servers/azure/__main__.py`
  - [ ] 解析命令列參數
  - [ ] 啟動 AzureMCPServer

#### 整合測試
```bash
# 啟動 Azure MCP Server
python -m src.integrations.mcp.servers.azure.server

# 測試工具調用 (通過 MCP Client)
python scripts/test_azure_mcp.py
```

#### 驗證
```bash
python -m py_compile src/integrations/mcp/servers/azure/server.py
pytest tests/unit/integrations/mcp/azure/test_server.py -v

# 整合測試
pytest tests/integration/mcp/test_azure_integration.py -v
```

---

## 驗證命令匯總

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/mcp/servers/azure/client.py
python -m py_compile src/integrations/mcp/servers/azure/tools/vm.py
python -m py_compile src/integrations/mcp/servers/azure/tools/resource.py
python -m py_compile src/integrations/mcp/servers/azure/tools/monitor.py
python -m py_compile src/integrations/mcp/servers/azure/server.py
# 預期: 無輸出 (無錯誤)

# 2. 類型檢查
mypy src/integrations/mcp/servers/azure/
# 預期: Success

# 3. 代碼風格
black src/integrations/mcp/servers/azure/ --check
isort src/integrations/mcp/servers/azure/ --check
# 預期: 無需修改

# 4. 運行單元測試
pytest tests/unit/integrations/mcp/azure/ -v --cov=src/integrations/mcp/servers/azure
# 預期: 全部通過，覆蓋率 > 85%

# 5. 整合測試 (需要 Azure 連接)
pytest tests/integration/mcp/test_azure_integration.py -v
# 預期: 全部通過
```

---

## 完成定義

- [ ] 所有 S40 Story 完成
- [ ] Azure 客戶端管理器可以連接到 Azure
- [ ] VM 工具可以列出、啟動、停止 VM
- [ ] 資源工具可以查詢資源群組和資源
- [ ] 監控工具可以獲取指標和警報
- [ ] Azure MCP Server 可以通過 MCP Client 調用
- [ ] 測試覆蓋率 > 85%
- [ ] 代碼審查完成
- [ ] 語法/類型/風格檢查全部通過

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `servers/azure/__init__.py` | 新增 | Azure Server 模組初始化 |
| `servers/azure/client.py` | 新增 | Azure 客戶端管理器 |
| `servers/azure/tools/__init__.py` | 新增 | 工具模組初始化 |
| `servers/azure/tools/vm.py` | 新增 | VM 管理工具 |
| `servers/azure/tools/resource.py` | 新增 | 資源管理工具 |
| `servers/azure/tools/monitor.py` | 新增 | 監控工具 |
| `servers/azure/server.py` | 新增 | Azure MCP Server 主入口 |
| `servers/azure/__main__.py` | 新增 | 命令列入口 |
| `config/mcp-servers.yaml` | 更新 | 添加 Azure Server 配置 |
| `tests/unit/integrations/mcp/azure/` | 新增 | 單元測試 |
| `tests/integration/mcp/` | 新增 | 整合測試 |

---

## 備註

### Azure 權限需求
| 操作 | 所需角色 |
|------|---------|
| 列出 VM | Reader |
| 啟動/停止 VM | Virtual Machine Contributor |
| 運行命令 | Virtual Machine Contributor + Run Command |
| 查詢監控 | Monitoring Reader |

### 錯誤處理策略
- Azure SDK 異常 → 轉換為 ToolResult 錯誤
- 權限不足 → 清晰的錯誤訊息
- 資源不存在 → 404 錯誤
- 超時 → 可配置的超時處理

### 下一步
- Sprint 41: Shell、Filesystem、SSH、LDAP MCP Servers

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
