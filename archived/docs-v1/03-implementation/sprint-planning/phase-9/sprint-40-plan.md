# Sprint 40: Azure MCP Server

**Sprint 目標**: 實現 Azure MCP Server，讓 Agent 能夠管理和監控 Azure 雲端資源
**總點數**: 35 Story Points
**優先級**: 🔴 CRITICAL
**前置條件**: Sprint 39 完成

---

## 背景

Azure MCP Server 是本專案最核心的執行工具，因為公司的基礎設施主要運行在 Azure 上。這個 MCP Server 將讓 Agent 能夠：

1. 查詢 VM 狀態和指標
2. 執行基本的資源管理操作
3. 收集日誌和診斷信息
4. 監控資源健康狀態

### 架構設計

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure MCP Server                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    MCP Protocol Layer                     │   │
│  │  • tools/list    • tools/call    • resources/list        │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │                    Tool Categories                        │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │    VM       │  │  Storage    │  │   Network   │       │   │
│  │  │   Tools     │  │   Tools     │  │   Tools     │       │   │
│  │  │             │  │             │  │             │       │   │
│  │  │ • list_vms  │  │ • list_sa   │  │ • list_vnets│       │   │
│  │  │ • get_vm    │  │ • get_blob  │  │ • get_nsg   │       │   │
│  │  │ • start_vm  │  │             │  │             │       │   │
│  │  │ • stop_vm   │  │             │  │             │       │   │
│  │  │ • restart_vm│  │             │  │             │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │  Monitor    │  │   Logs      │  │  Resource   │       │   │
│  │  │   Tools     │  │   Tools     │  │   Graph     │       │   │
│  │  │             │  │             │  │             │       │   │
│  │  │ • get_metric│  │ • query_logs│  │ • search    │       │   │
│  │  │ • list_alert│  │ • get_diag  │  │ • list_rg   │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └───────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │                  Azure SDK Layer                          │   │
│  │                                                           │   │
│  │  • azure-mgmt-compute     • azure-mgmt-storage           │   │
│  │  • azure-mgmt-network     • azure-mgmt-monitor           │   │
│  │  • azure-mgmt-resource    • azure-identity               │   │
│  └───────────────────────────────────────────────────────────┘   │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Azure Cloud   │
                    │   Resources     │
                    └─────────────────┘
```

---

## Story 清單

### S40-1: Azure SDK 整合層 (8 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/mcp/servers/azure/`

#### 設計

```python
# 文件: backend/src/integrations/mcp/servers/azure/client.py

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.storage import StorageManagementClient

logger = logging.getLogger(__name__)


@dataclass
class AzureConfig:
    """Azure 配置。"""
    subscription_id: str
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class AzureClientManager:
    """Azure 客戶端管理器。

    統一管理所有 Azure SDK 客戶端。

    Example:
        ```python
        config = AzureConfig(subscription_id="xxx")
        manager = AzureClientManager(config)

        # 獲取 Compute 客戶端
        compute = manager.compute
        vms = compute.virtual_machines.list_all()

        # 獲取 Resource 客戶端
        resource = manager.resource
        rgs = resource.resource_groups.list()
        ```
    """

    def __init__(self, config: AzureConfig):
        """初始化管理器。

        Args:
            config: Azure 配置
        """
        self._config = config
        self._credential = DefaultAzureCredential()
        self._clients: Dict[str, Any] = {}

    @property
    def compute(self) -> ComputeManagementClient:
        """獲取 Compute 客戶端。"""
        if "compute" not in self._clients:
            self._clients["compute"] = ComputeManagementClient(
                credential=self._credential,
                subscription_id=self._config.subscription_id,
            )
        return self._clients["compute"]

    @property
    def resource(self) -> ResourceManagementClient:
        """獲取 Resource 客戶端。"""
        if "resource" not in self._clients:
            self._clients["resource"] = ResourceManagementClient(
                credential=self._credential,
                subscription_id=self._config.subscription_id,
            )
        return self._clients["resource"]

    @property
    def network(self) -> NetworkManagementClient:
        """獲取 Network 客戶端。"""
        if "network" not in self._clients:
            self._clients["network"] = NetworkManagementClient(
                credential=self._credential,
                subscription_id=self._config.subscription_id,
            )
        return self._clients["network"]

    @property
    def monitor(self) -> MonitorManagementClient:
        """獲取 Monitor 客戶端。"""
        if "monitor" not in self._clients:
            self._clients["monitor"] = MonitorManagementClient(
                credential=self._credential,
                subscription_id=self._config.subscription_id,
            )
        return self._clients["monitor"]

    @property
    def storage(self) -> StorageManagementClient:
        """獲取 Storage 客戶端。"""
        if "storage" not in self._clients:
            self._clients["storage"] = StorageManagementClient(
                credential=self._credential,
                subscription_id=self._config.subscription_id,
            )
        return self._clients["storage"]

    def close(self) -> None:
        """關閉所有客戶端。"""
        for client in self._clients.values():
            if hasattr(client, "close"):
                client.close()
        self._clients.clear()
```

#### 任務清單

1. **創建 Azure 模組結構**
   ```
   backend/src/integrations/mcp/servers/azure/
   ├── __init__.py
   ├── client.py           # Azure SDK 客戶端管理
   ├── server.py           # MCP Server 主程式
   ├── tools/
   │   ├── __init__.py
   │   ├── vm.py           # VM 工具
   │   ├── resource.py     # 資源工具
   │   ├── network.py      # 網路工具
   │   ├── storage.py      # 存儲工具
   │   └── monitor.py      # 監控工具
   └── schemas.py          # 工具 Schema 定義
   ```

2. **實現 AzureConfig**
   - 配置管理
   - 環境變數支援

3. **實現 AzureClientManager**
   - 認證管理
   - 客戶端快取
   - 資源清理

#### 驗收標準
- [ ] Azure SDK 正確初始化
- [ ] 認證機制正常工作
- [ ] 可以連接到 Azure 訂閱

---

### S40-2: VM 管理工具 (10 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/mcp/servers/azure/tools/vm.py`

#### 設計

```python
# 文件: backend/src/integrations/mcp/servers/azure/tools/vm.py

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

from ..client import AzureClientManager
from ...core.types import ToolSchema, ToolParameter, ToolInputType, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class VMInfo:
    """VM 信息。"""
    id: str
    name: str
    resource_group: str
    location: str
    vm_size: str
    status: str
    os_type: str
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None


class VMTools:
    """VM 管理工具集。

    提供 VM 查詢和管理功能。

    Tools:
        - list_vms: 列出所有 VM
        - get_vm: 獲取 VM 詳情
        - get_vm_status: 獲取 VM 運行狀態
        - start_vm: 啟動 VM
        - stop_vm: 停止 VM
        - restart_vm: 重啟 VM
        - run_command: 在 VM 上執行命令
    """

    def __init__(self, client_manager: AzureClientManager):
        """初始化 VM 工具。

        Args:
            client_manager: Azure 客戶端管理器
        """
        self._manager = client_manager

    @staticmethod
    def get_schemas() -> List[ToolSchema]:
        """獲取所有工具 Schema。"""
        return [
            ToolSchema(
                name="list_vms",
                description="列出訂閱中的所有虛擬機",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="可選的資源組過濾",
                        required=False,
                    ),
                ],
            ),
            ToolSchema(
                name="get_vm",
                description="獲取虛擬機詳細信息",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="資源組名稱",
                        required=True,
                    ),
                    ToolParameter(
                        name="vm_name",
                        type=ToolInputType.STRING,
                        description="虛擬機名稱",
                        required=True,
                    ),
                ],
            ),
            ToolSchema(
                name="get_vm_status",
                description="獲取虛擬機運行狀態",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="資源組名稱",
                        required=True,
                    ),
                    ToolParameter(
                        name="vm_name",
                        type=ToolInputType.STRING,
                        description="虛擬機名稱",
                        required=True,
                    ),
                ],
            ),
            ToolSchema(
                name="start_vm",
                description="啟動虛擬機",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="資源組名稱",
                        required=True,
                    ),
                    ToolParameter(
                        name="vm_name",
                        type=ToolInputType.STRING,
                        description="虛擬機名稱",
                        required=True,
                    ),
                ],
            ),
            ToolSchema(
                name="stop_vm",
                description="停止虛擬機 (保留 IP)",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="資源組名稱",
                        required=True,
                    ),
                    ToolParameter(
                        name="vm_name",
                        type=ToolInputType.STRING,
                        description="虛擬機名稱",
                        required=True,
                    ),
                ],
            ),
            ToolSchema(
                name="restart_vm",
                description="重啟虛擬機",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="資源組名稱",
                        required=True,
                    ),
                    ToolParameter(
                        name="vm_name",
                        type=ToolInputType.STRING,
                        description="虛擬機名稱",
                        required=True,
                    ),
                ],
            ),
            ToolSchema(
                name="run_command",
                description="在虛擬機上執行命令",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="資源組名稱",
                        required=True,
                    ),
                    ToolParameter(
                        name="vm_name",
                        type=ToolInputType.STRING,
                        description="虛擬機名稱",
                        required=True,
                    ),
                    ToolParameter(
                        name="command",
                        type=ToolInputType.STRING,
                        description="要執行的命令",
                        required=True,
                    ),
                    ToolParameter(
                        name="command_id",
                        type=ToolInputType.STRING,
                        description="命令類型 (RunPowerShellScript, RunShellScript)",
                        required=False,
                    ),
                ],
            ),
        ]

    async def list_vms(
        self,
        resource_group: Optional[str] = None,
    ) -> ToolResult:
        """列出虛擬機。

        Args:
            resource_group: 可選的資源組過濾

        Returns:
            VM 列表
        """
        try:
            compute = self._manager.compute

            if resource_group:
                vms = compute.virtual_machines.list(resource_group)
            else:
                vms = compute.virtual_machines.list_all()

            vm_list = []
            for vm in vms:
                # 解析資源組
                parts = vm.id.split("/")
                rg = parts[parts.index("resourceGroups") + 1]

                vm_list.append({
                    "id": vm.id,
                    "name": vm.name,
                    "resource_group": rg,
                    "location": vm.location,
                    "vm_size": vm.hardware_profile.vm_size,
                    "os_type": vm.storage_profile.os_disk.os_type,
                })

            return ToolResult(
                success=True,
                content=vm_list,
                metadata={"count": len(vm_list)},
            )

        except Exception as e:
            logger.error(f"Failed to list VMs: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )

    async def get_vm(
        self,
        resource_group: str,
        vm_name: str,
    ) -> ToolResult:
        """獲取 VM 詳情。"""
        try:
            compute = self._manager.compute
            vm = compute.virtual_machines.get(
                resource_group,
                vm_name,
                expand="instanceView",
            )

            # 獲取狀態
            status = "Unknown"
            if vm.instance_view and vm.instance_view.statuses:
                for s in vm.instance_view.statuses:
                    if s.code.startswith("PowerState/"):
                        status = s.code.replace("PowerState/", "")
                        break

            return ToolResult(
                success=True,
                content={
                    "id": vm.id,
                    "name": vm.name,
                    "resource_group": resource_group,
                    "location": vm.location,
                    "vm_size": vm.hardware_profile.vm_size,
                    "os_type": vm.storage_profile.os_disk.os_type,
                    "status": status,
                    "provisioning_state": vm.provisioning_state,
                },
            )

        except Exception as e:
            logger.error(f"Failed to get VM {vm_name}: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )

    async def get_vm_status(
        self,
        resource_group: str,
        vm_name: str,
    ) -> ToolResult:
        """獲取 VM 運行狀態。"""
        try:
            compute = self._manager.compute
            instance_view = compute.virtual_machines.instance_view(
                resource_group,
                vm_name,
            )

            statuses = []
            for status in instance_view.statuses:
                statuses.append({
                    "code": status.code,
                    "level": status.level,
                    "display_status": status.display_status,
                    "time": status.time.isoformat() if status.time else None,
                })

            return ToolResult(
                success=True,
                content={
                    "vm_name": vm_name,
                    "statuses": statuses,
                },
            )

        except Exception as e:
            logger.error(f"Failed to get VM status {vm_name}: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )

    async def start_vm(
        self,
        resource_group: str,
        vm_name: str,
    ) -> ToolResult:
        """啟動 VM。"""
        try:
            compute = self._manager.compute
            # 異步操作
            poller = compute.virtual_machines.begin_start(
                resource_group,
                vm_name,
            )
            # 不等待完成，返回操作 ID
            return ToolResult(
                success=True,
                content={
                    "message": f"Starting VM {vm_name}",
                    "operation_id": poller.operation_id,
                },
            )

        except Exception as e:
            logger.error(f"Failed to start VM {vm_name}: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )

    async def stop_vm(
        self,
        resource_group: str,
        vm_name: str,
    ) -> ToolResult:
        """停止 VM (保留 IP)。"""
        try:
            compute = self._manager.compute
            poller = compute.virtual_machines.begin_power_off(
                resource_group,
                vm_name,
            )
            return ToolResult(
                success=True,
                content={
                    "message": f"Stopping VM {vm_name}",
                    "operation_id": poller.operation_id,
                },
            )

        except Exception as e:
            logger.error(f"Failed to stop VM {vm_name}: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )

    async def restart_vm(
        self,
        resource_group: str,
        vm_name: str,
    ) -> ToolResult:
        """重啟 VM。"""
        try:
            compute = self._manager.compute
            poller = compute.virtual_machines.begin_restart(
                resource_group,
                vm_name,
            )
            return ToolResult(
                success=True,
                content={
                    "message": f"Restarting VM {vm_name}",
                    "operation_id": poller.operation_id,
                },
            )

        except Exception as e:
            logger.error(f"Failed to restart VM {vm_name}: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )

    async def run_command(
        self,
        resource_group: str,
        vm_name: str,
        command: str,
        command_id: str = "RunPowerShellScript",
    ) -> ToolResult:
        """在 VM 上執行命令。"""
        try:
            from azure.mgmt.compute.models import RunCommandInput

            compute = self._manager.compute

            run_command_input = RunCommandInput(
                command_id=command_id,
                script=[command],
            )

            poller = compute.virtual_machines.begin_run_command(
                resource_group,
                vm_name,
                run_command_input,
            )

            # 等待命令完成
            result = poller.result()

            output = []
            if result.value:
                for v in result.value:
                    output.append({
                        "code": v.code,
                        "level": v.level,
                        "message": v.message,
                    })

            return ToolResult(
                success=True,
                content={
                    "vm_name": vm_name,
                    "command": command,
                    "output": output,
                },
            )

        except Exception as e:
            logger.error(f"Failed to run command on {vm_name}: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )
```

#### 任務清單

1. **實現 VMTools 類**
   - list_vms()
   - get_vm()
   - get_vm_status()
   - start_vm()
   - stop_vm()
   - restart_vm()
   - run_command()

2. **定義工具 Schema**
   - 符合 MCP 規範

3. **權限分級**
   - 只讀: list_vms, get_vm, get_vm_status (Level 1)
   - 低風險: restart_vm (Level 2)
   - 高風險: start_vm, stop_vm, run_command (Level 3)

#### 驗收標準
- [ ] 所有 VM 工具正常工作
- [ ] 錯誤處理完整
- [ ] 權限分級正確

---

### S40-3: 資源和監控工具 (8 pts)

**優先級**: 🟡 P1
**類型**: 新增
**影響範圍**: `backend/src/integrations/mcp/servers/azure/tools/`

#### 設計

```python
# 文件: backend/src/integrations/mcp/servers/azure/tools/resource.py

class ResourceTools:
    """資源管理工具集。

    Tools:
        - list_resource_groups: 列出資源組
        - get_resource_group: 獲取資源組詳情
        - list_resources: 列出資源組中的資源
        - search_resources: 搜索資源
    """

    @staticmethod
    def get_schemas() -> List[ToolSchema]:
        return [
            ToolSchema(
                name="list_resource_groups",
                description="列出訂閱中的所有資源組",
                parameters=[],
            ),
            ToolSchema(
                name="list_resources",
                description="列出資源組中的所有資源",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="資源組名稱",
                        required=True,
                    ),
                    ToolParameter(
                        name="resource_type",
                        type=ToolInputType.STRING,
                        description="可選的資源類型過濾",
                        required=False,
                    ),
                ],
            ),
        ]

    async def list_resource_groups(self) -> ToolResult:
        """列出資源組。"""
        ...

    async def list_resources(
        self,
        resource_group: str,
        resource_type: Optional[str] = None,
    ) -> ToolResult:
        """列出資源。"""
        ...
```

```python
# 文件: backend/src/integrations/mcp/servers/azure/tools/monitor.py

class MonitorTools:
    """監控工具集。

    Tools:
        - get_metrics: 獲取資源指標
        - list_alerts: 列出告警
        - query_logs: 查詢日誌
    """

    @staticmethod
    def get_schemas() -> List[ToolSchema]:
        return [
            ToolSchema(
                name="get_metrics",
                description="獲取資源的監控指標",
                parameters=[
                    ToolParameter(
                        name="resource_id",
                        type=ToolInputType.STRING,
                        description="資源 ID",
                        required=True,
                    ),
                    ToolParameter(
                        name="metric_names",
                        type=ToolInputType.ARRAY,
                        description="指標名稱列表",
                        required=True,
                    ),
                    ToolParameter(
                        name="timespan",
                        type=ToolInputType.STRING,
                        description="時間範圍 (例如: PT1H, P1D)",
                        required=False,
                    ),
                ],
            ),
            ToolSchema(
                name="list_alerts",
                description="列出活動告警",
                parameters=[
                    ToolParameter(
                        name="resource_group",
                        type=ToolInputType.STRING,
                        description="可選的資源組過濾",
                        required=False,
                    ),
                ],
            ),
        ]

    async def get_metrics(
        self,
        resource_id: str,
        metric_names: List[str],
        timespan: str = "PT1H",
    ) -> ToolResult:
        """獲取指標。"""
        ...

    async def list_alerts(
        self,
        resource_group: Optional[str] = None,
    ) -> ToolResult:
        """列出告警。"""
        ...
```

#### 任務清單

1. **實現 ResourceTools**
   - list_resource_groups()
   - list_resources()

2. **實現 MonitorTools**
   - get_metrics()
   - list_alerts()

3. **實現 NetworkTools** (基礎)
   - list_vnets()
   - list_nsgs()

#### 驗收標準
- [ ] 資源查詢正常工作
- [ ] 指標獲取正確
- [ ] 告警列表可用

---

### S40-4: Azure MCP Server 主程式 (5 pts)

**優先級**: 🟡 P1
**類型**: 新增
**影響範圍**: `backend/src/integrations/mcp/servers/azure/server.py`

#### 設計

```python
# 文件: backend/src/integrations/mcp/servers/azure/server.py

import asyncio
import sys
import json
from typing import Dict, Any

from ...core.protocol import MCPProtocol
from ...core.types import ToolResult
from .client import AzureClientManager, AzureConfig
from .tools.vm import VMTools
from .tools.resource import ResourceTools
from .tools.monitor import MonitorTools


class AzureMCPServer:
    """Azure MCP Server。

    提供 Azure 資源管理和監控功能的 MCP Server。

    Usage:
        ```bash
        # 作為 MCP Server 運行
        python -m mcp_servers.azure

        # 環境變數配置
        AZURE_SUBSCRIPTION_ID=xxx
        AZURE_TENANT_ID=xxx (可選)
        ```
    """

    def __init__(self, config: AzureConfig):
        """初始化 Server。

        Args:
            config: Azure 配置
        """
        self._config = config
        self._protocol = MCPProtocol()
        self._client_manager = AzureClientManager(config)

        # 初始化工具
        self._vm_tools = VMTools(self._client_manager)
        self._resource_tools = ResourceTools(self._client_manager)
        self._monitor_tools = MonitorTools(self._client_manager)

        # 註冊工具
        self._register_tools()

    def _register_tools(self) -> None:
        """註冊所有工具。"""
        # 註冊 VM 工具
        for schema in VMTools.get_schemas():
            handler = getattr(self._vm_tools, schema.name)
            self._protocol.register_tool(schema.name, handler, schema)

        # 註冊 Resource 工具
        for schema in ResourceTools.get_schemas():
            handler = getattr(self._resource_tools, schema.name)
            self._protocol.register_tool(schema.name, handler, schema)

        # 註冊 Monitor 工具
        for schema in MonitorTools.get_schemas():
            handler = getattr(self._monitor_tools, schema.name)
            self._protocol.register_tool(schema.name, handler, schema)

    async def run(self) -> None:
        """運行 Server (stdio 模式)。"""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                request_data = json.loads(line)
                from ...core.types import MCPRequest
                request = MCPRequest(**request_data)

                response = await self._protocol.handle_request(request)

                response_data = {
                    "jsonrpc": response.jsonrpc,
                    "id": response.id,
                }
                if response.result is not None:
                    response_data["result"] = response.result
                if response.error is not None:
                    response_data["error"] = response.error

                print(json.dumps(response_data), flush=True)

            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": str(e),
                    }
                }
                print(json.dumps(error_response), flush=True)

    def cleanup(self) -> None:
        """清理資源。"""
        self._client_manager.close()


def main():
    """主入口。"""
    import os

    config = AzureConfig(
        subscription_id=os.environ.get("AZURE_SUBSCRIPTION_ID", ""),
        tenant_id=os.environ.get("AZURE_TENANT_ID"),
        client_id=os.environ.get("AZURE_CLIENT_ID"),
        client_secret=os.environ.get("AZURE_CLIENT_SECRET"),
    )

    server = AzureMCPServer(config)

    try:
        asyncio.run(server.run())
    finally:
        server.cleanup()


if __name__ == "__main__":
    main()
```

#### 任務清單

1. **實現 AzureMCPServer**
   - 工具註冊
   - stdio 通訊
   - 錯誤處理

2. **創建入口點**
   - `__main__.py`
   - 環境變數配置

3. **更新 MCP Server 註冊表配置**
   - 添加 azure-mcp 配置

#### 驗收標準
- [ ] Server 可以啟動
- [ ] 工具列表正確返回
- [ ] 工具調用正常工作

---

### S40-5: 測試和文檔 (4 pts)

**優先級**: 🟢 P2
**類型**: 測試/文檔
**影響範圍**: `tests/`, `docs/`

#### 任務清單

1. **單元測試**
   - 測試 AzureClientManager
   - 測試 VMTools (mock)
   - 測試 AzureMCPServer

2. **整合測試**
   - 端到端測試 (需要 Azure 測試訂閱)

3. **文檔**
   - Azure MCP Server 使用指南
   - 配置說明
   - 工具參考

#### 驗收標準
- [ ] 測試覆蓋率 > 80%
- [ ] 文檔完整

---

## 驗證命令

```bash
# 1. 安裝依賴
pip install azure-identity azure-mgmt-compute azure-mgmt-resource azure-mgmt-network azure-mgmt-monitor azure-mgmt-storage

# 2. 語法檢查
cd backend
python -m py_compile src/integrations/mcp/servers/azure/client.py
python -m py_compile src/integrations/mcp/servers/azure/tools/vm.py
python -m py_compile src/integrations/mcp/servers/azure/server.py

# 3. 運行測試
pytest tests/unit/integrations/mcp/servers/azure/ -v

# 4. 手動測試 (需要設置環境變數)
export AZURE_SUBSCRIPTION_ID=xxx
python -m src.integrations.mcp.servers.azure

# 5. 通過 MCP Client 測試
curl -X POST http://localhost:8000/api/v1/mcp/servers/azure-mcp/connect
curl http://localhost:8000/api/v1/mcp/servers/azure-mcp/tools
```

---

## 完成定義

- [ ] 所有 S40 Story 完成
- [ ] Azure SDK 整合層完成
- [ ] VM 管理工具全部可用
- [ ] 資源和監控工具可用
- [ ] MCP Server 正常運行
- [ ] 測試覆蓋率 > 80%
- [ ] 文檔完整

---

**創建日期**: 2025-12-22
