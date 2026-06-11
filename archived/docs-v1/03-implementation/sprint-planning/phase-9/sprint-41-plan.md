# Sprint 41: Additional MCP Servers

> **目標**: 實現 Shell、Filesystem、SSH、LDAP MCP Servers，擴展 Agent 執行能力

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 41 |
| 總點數 | 35 Story Points |
| 預計時間 | 2 週 |
| 前置條件 | Sprint 40 完成 |
| 狀態 | 📋 計劃中 |

---

## Stories

### S41-1: Shell MCP Server (10 pts)

**描述**: 實現安全的 Shell 命令執行 MCP Server

**功能需求**:
1. 支援 PowerShell (Windows) 和 Bash (Linux)
2. 命令白名單機制
3. 超時控制
4. 輸出大小限制
5. 工作目錄隔離

**技術設計**:

```python
# servers/shell/executor.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import asyncio
import subprocess

class ShellType(Enum):
    """Shell 類型"""
    POWERSHELL = "powershell"
    BASH = "bash"
    CMD = "cmd"


@dataclass
class ShellConfig:
    """Shell 配置"""
    shell_type: ShellType
    timeout_seconds: int = 60
    max_output_size: int = 1024 * 1024  # 1MB
    working_directory: Optional[str] = None
    allowed_commands: List[str] = None  # 白名單
    blocked_commands: List[str] = None  # 黑名單


@dataclass
class CommandResult:
    """命令執行結果"""
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    truncated: bool = False


class ShellExecutor:
    """安全的 Shell 執行器"""

    # 預設黑名單 (危險命令)
    DEFAULT_BLOCKED = [
        "rm -rf /",
        "format",
        "del /s /q",
        "shutdown",
        "reboot",
        ":(){:|:&};:",  # Fork bomb
    ]

    def __init__(self, config: ShellConfig):
        self._config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """驗證配置"""
        if self._config.working_directory:
            # 確保目錄存在且安全
            pass

    async def execute(
        self,
        command: str,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        執行命令

        Args:
            command: 要執行的命令
            env: 環境變數

        Returns:
            CommandResult: 執行結果
        """
        # 1. 命令安全檢查
        self._validate_command(command)

        # 2. 構建執行參數
        shell_cmd = self._build_shell_command(command)

        # 3. 執行命令
        start_time = asyncio.get_event_loop().time()

        try:
            process = await asyncio.create_subprocess_shell(
                shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._config.working_directory,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._config.timeout_seconds
            )

            execution_time = asyncio.get_event_loop().time() - start_time

            # 4. 處理輸出
            stdout_str, truncated = self._truncate_output(stdout.decode())
            stderr_str, _ = self._truncate_output(stderr.decode())

            return CommandResult(
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                execution_time=execution_time,
                truncated=truncated
            )

        except asyncio.TimeoutError:
            return CommandResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {self._config.timeout_seconds} seconds",
                execution_time=self._config.timeout_seconds,
            )

    def _validate_command(self, command: str) -> None:
        """驗證命令安全性"""
        # 檢查黑名單
        for blocked in self.DEFAULT_BLOCKED:
            if blocked in command.lower():
                raise ValueError(f"Blocked command pattern: {blocked}")

        # 檢查白名單 (如果配置)
        if self._config.allowed_commands:
            cmd_base = command.split()[0]
            if cmd_base not in self._config.allowed_commands:
                raise ValueError(f"Command not in whitelist: {cmd_base}")

    def _build_shell_command(self, command: str) -> str:
        """構建 Shell 命令"""
        if self._config.shell_type == ShellType.POWERSHELL:
            return f"powershell -NoProfile -Command \"{command}\""
        elif self._config.shell_type == ShellType.BASH:
            return f"bash -c \"{command}\""
        else:
            return command

    def _truncate_output(self, output: str) -> tuple[str, bool]:
        """截斷過大的輸出"""
        if len(output) > self._config.max_output_size:
            return output[:self._config.max_output_size] + "\n...[truncated]", True
        return output, False
```

```python
# servers/shell/tools.py

from ..core.types import ToolSchema, ToolParameter, ToolInputType, ToolResult

class ShellTools:
    """Shell 工具集"""

    def __init__(self, executor: ShellExecutor):
        self._executor = executor

    def get_tool_schemas(self) -> list[ToolSchema]:
        """獲取工具定義"""
        return [
            ToolSchema(
                name="run_command",
                description="Execute a shell command",
                parameters=[
                    ToolParameter(
                        name="command",
                        type=ToolInputType.STRING,
                        description="The command to execute",
                        required=True
                    ),
                    ToolParameter(
                        name="timeout",
                        type=ToolInputType.INTEGER,
                        description="Timeout in seconds (default: 60)",
                        required=False
                    ),
                ]
            ),
            ToolSchema(
                name="run_script",
                description="Execute a script file",
                parameters=[
                    ToolParameter(
                        name="script_path",
                        type=ToolInputType.STRING,
                        description="Path to the script file",
                        required=True
                    ),
                    ToolParameter(
                        name="arguments",
                        type=ToolInputType.ARRAY,
                        description="Script arguments",
                        required=False
                    ),
                ]
            ),
        ]

    async def run_command(
        self,
        command: str,
        timeout: int = 60
    ) -> ToolResult:
        """執行命令"""
        result = await self._executor.execute(command)

        return ToolResult(
            success=result.exit_code == 0,
            data={
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": result.execution_time,
                "truncated": result.truncated
            },
            error=result.stderr if result.exit_code != 0 else None
        )
```

**風險等級**:
| 工具 | 風險等級 | 審批需求 |
|------|---------|---------|
| run_command | HIGH | HUMAN |
| run_script | HIGH | HUMAN |

**驗收標準**:
- [ ] 支援 PowerShell 和 Bash
- [ ] 命令黑名單有效阻止危險操作
- [ ] 超時機制正常運作
- [ ] 輸出截斷不影響結果
- [ ] 測試覆蓋率 > 85%

---

### S41-2: Filesystem MCP Server (8 pts)

**描述**: 實現安全的文件系統操作 MCP Server

**功能需求**:
1. 文件讀取 (支援多種編碼)
2. 文件寫入 (帶備份)
3. 目錄操作
4. 路徑安全驗證
5. 沙箱隔離

**技術設計**:

```python
# servers/filesystem/sandbox.py

from pathlib import Path
from typing import List, Optional
import os

class FilesystemSandbox:
    """文件系統沙箱"""

    def __init__(
        self,
        allowed_roots: List[str],
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_extensions: Optional[List[str]] = None
    ):
        self._allowed_roots = [Path(r).resolve() for r in allowed_roots]
        self._max_file_size = max_file_size
        self._allowed_extensions = allowed_extensions

    def validate_path(self, path: str) -> Path:
        """驗證路徑是否在允許範圍內"""
        resolved = Path(path).resolve()

        # 檢查是否在允許的根目錄下
        is_allowed = any(
            self._is_subpath(resolved, root)
            for root in self._allowed_roots
        )

        if not is_allowed:
            raise PermissionError(f"Path not in allowed roots: {path}")

        # 檢查擴展名
        if self._allowed_extensions:
            if resolved.suffix.lower() not in self._allowed_extensions:
                raise PermissionError(f"Extension not allowed: {resolved.suffix}")

        return resolved

    def _is_subpath(self, path: Path, root: Path) -> bool:
        """檢查 path 是否是 root 的子路徑"""
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def validate_file_size(self, size: int) -> None:
        """驗證文件大小"""
        if size > self._max_file_size:
            raise ValueError(
                f"File size {size} exceeds limit {self._max_file_size}"
            )
```

```python
# servers/filesystem/tools.py

from pathlib import Path
from typing import Optional, List
import aiofiles
import shutil
from datetime import datetime

class FilesystemTools:
    """文件系統工具集"""

    def __init__(self, sandbox: FilesystemSandbox):
        self._sandbox = sandbox

    async def read_file(
        self,
        path: str,
        encoding: str = "utf-8"
    ) -> ToolResult:
        """讀取文件內容"""
        try:
            validated_path = self._sandbox.validate_path(path)

            async with aiofiles.open(validated_path, "r", encoding=encoding) as f:
                content = await f.read()

            return ToolResult(
                success=True,
                data={"content": content, "path": str(validated_path)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_backup: bool = True
    ) -> ToolResult:
        """寫入文件"""
        try:
            validated_path = self._sandbox.validate_path(path)
            self._sandbox.validate_file_size(len(content.encode(encoding)))

            # 創建備份
            if create_backup and validated_path.exists():
                backup_path = validated_path.with_suffix(
                    f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                shutil.copy2(validated_path, backup_path)

            async with aiofiles.open(validated_path, "w", encoding=encoding) as f:
                await f.write(content)

            return ToolResult(
                success=True,
                data={"path": str(validated_path), "size": len(content)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def list_directory(
        self,
        path: str,
        pattern: str = "*"
    ) -> ToolResult:
        """列出目錄內容"""
        try:
            validated_path = self._sandbox.validate_path(path)

            if not validated_path.is_dir():
                return ToolResult(success=False, error="Not a directory")

            entries = []
            for entry in validated_path.glob(pattern):
                entries.append({
                    "name": entry.name,
                    "type": "directory" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else None,
                    "modified": entry.stat().st_mtime
                })

            return ToolResult(success=True, data={"entries": entries})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def file_info(self, path: str) -> ToolResult:
        """獲取文件信息"""
        try:
            validated_path = self._sandbox.validate_path(path)
            stat = validated_path.stat()

            return ToolResult(
                success=True,
                data={
                    "path": str(validated_path),
                    "exists": validated_path.exists(),
                    "is_file": validated_path.is_file(),
                    "is_dir": validated_path.is_dir(),
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**風險等級**:
| 工具 | 風險等級 | 審批需求 |
|------|---------|---------|
| read_file | LOW | NONE |
| list_directory | LOW | NONE |
| file_info | LOW | NONE |
| write_file | MEDIUM | AGENT |
| delete_file | HIGH | HUMAN |
| create_directory | MEDIUM | AGENT |

**驗收標準**:
- [ ] 沙箱有效限制訪問範圍
- [ ] 支援多種文件編碼
- [ ] 寫入前自動備份
- [ ] 大文件處理正常
- [ ] 測試覆蓋率 > 85%

---

### S41-3: SSH MCP Server (10 pts)

**描述**: 實現安全的 SSH 遠端連接 MCP Server

**功能需求**:
1. SSH 連接管理 (連接池)
2. 遠端命令執行
3. 文件傳輸 (SCP/SFTP)
4. 多種認證方式 (密碼/金鑰)
5. 連接超時和重試

**技術設計**:

```python
# servers/ssh/connection.py

from dataclasses import dataclass
from typing import Optional, Dict
import asyncio
import asyncssh
from asyncssh import SSHClientConnection

@dataclass
class SSHConfig:
    """SSH 連接配置"""
    host: str
    port: int = 22
    username: str = ""
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    known_hosts: Optional[str] = None
    timeout: int = 30
    keepalive_interval: int = 60


class SSHConnectionPool:
    """SSH 連接池"""

    def __init__(self, max_connections: int = 10):
        self._max_connections = max_connections
        self._connections: Dict[str, SSHClientConnection] = {}
        self._lock = asyncio.Lock()

    def _get_key(self, config: SSHConfig) -> str:
        """生成連接 key"""
        return f"{config.username}@{config.host}:{config.port}"

    async def get_connection(
        self,
        config: SSHConfig
    ) -> SSHClientConnection:
        """獲取或創建連接"""
        key = self._get_key(config)

        async with self._lock:
            # 檢查現有連接
            if key in self._connections:
                conn = self._connections[key]
                if not conn.is_closed():
                    return conn
                del self._connections[key]

            # 創建新連接
            conn = await self._create_connection(config)
            self._connections[key] = conn
            return conn

    async def _create_connection(
        self,
        config: SSHConfig
    ) -> SSHClientConnection:
        """創建 SSH 連接"""
        connect_kwargs = {
            "host": config.host,
            "port": config.port,
            "username": config.username,
            "known_hosts": config.known_hosts,
        }

        if config.password:
            connect_kwargs["password"] = config.password
        elif config.private_key_path:
            connect_kwargs["client_keys"] = [config.private_key_path]

        return await asyncio.wait_for(
            asyncssh.connect(**connect_kwargs),
            timeout=config.timeout
        )

    async def close_all(self) -> None:
        """關閉所有連接"""
        async with self._lock:
            for conn in self._connections.values():
                conn.close()
            self._connections.clear()
```

```python
# servers/ssh/tools.py

from typing import Optional, List

class SSHTools:
    """SSH 工具集"""

    def __init__(self, connection_pool: SSHConnectionPool):
        self._pool = connection_pool

    async def execute_command(
        self,
        host: str,
        command: str,
        username: str,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
        timeout: int = 60
    ) -> ToolResult:
        """在遠端主機執行命令"""
        try:
            config = SSHConfig(
                host=host,
                username=username,
                password=password,
                private_key_path=private_key_path,
                timeout=timeout
            )

            conn = await self._pool.get_connection(config)
            result = await conn.run(command, check=False, timeout=timeout)

            return ToolResult(
                success=result.returncode == 0,
                data={
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def upload_file(
        self,
        host: str,
        local_path: str,
        remote_path: str,
        username: str,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None
    ) -> ToolResult:
        """上傳文件到遠端主機"""
        try:
            config = SSHConfig(
                host=host,
                username=username,
                password=password,
                private_key_path=private_key_path,
            )

            conn = await self._pool.get_connection(config)
            async with conn.start_sftp_client() as sftp:
                await sftp.put(local_path, remote_path)

            return ToolResult(
                success=True,
                data={"remote_path": remote_path}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def download_file(
        self,
        host: str,
        remote_path: str,
        local_path: str,
        username: str,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None
    ) -> ToolResult:
        """從遠端主機下載文件"""
        try:
            config = SSHConfig(
                host=host,
                username=username,
                password=password,
                private_key_path=private_key_path,
            )

            conn = await self._pool.get_connection(config)
            async with conn.start_sftp_client() as sftp:
                await sftp.get(remote_path, local_path)

            return ToolResult(
                success=True,
                data={"local_path": local_path}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**風險等級**:
| 工具 | 風險等級 | 審批需求 |
|------|---------|---------|
| execute_command | HIGH | HUMAN |
| upload_file | HIGH | HUMAN |
| download_file | MEDIUM | AGENT |
| list_remote_directory | LOW | NONE |

**驗收標準**:
- [ ] 支援密碼和金鑰認證
- [ ] 連接池正常管理連接
- [ ] 命令超時機制正常
- [ ] SFTP 文件傳輸正常
- [ ] 測試覆蓋率 > 85%

---

### S41-4: LDAP MCP Server (7 pts)

**描述**: 實現 LDAP/Active Directory 查詢 MCP Server

**功能需求**:
1. LDAP 連接管理
2. 用戶查詢
3. 群組查詢
4. OU 查詢
5. 屬性搜索

**技術設計**:

```python
# servers/ldap/client.py

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from ldap3 import Server, Connection, ALL, SUBTREE

@dataclass
class LDAPConfig:
    """LDAP 配置"""
    server: str
    port: int = 389
    use_ssl: bool = False
    bind_dn: str = ""
    bind_password: str = ""
    base_dn: str = ""
    timeout: int = 30


class LDAPClient:
    """LDAP 客戶端"""

    def __init__(self, config: LDAPConfig):
        self._config = config
        self._connection: Optional[Connection] = None

    def connect(self) -> None:
        """建立連接"""
        server = Server(
            self._config.server,
            port=self._config.port,
            use_ssl=self._config.use_ssl,
            get_info=ALL
        )

        self._connection = Connection(
            server,
            user=self._config.bind_dn,
            password=self._config.bind_password,
            auto_bind=True,
            receive_timeout=self._config.timeout
        )

    def disconnect(self) -> None:
        """關閉連接"""
        if self._connection:
            self._connection.unbind()
            self._connection = None

    def search(
        self,
        search_filter: str,
        attributes: List[str] = None,
        search_base: str = None,
        search_scope: str = SUBTREE
    ) -> List[Dict[str, Any]]:
        """執行 LDAP 搜索"""
        if not self._connection:
            raise RuntimeError("Not connected")

        base = search_base or self._config.base_dn
        attrs = attributes or ["*"]

        self._connection.search(
            base,
            search_filter,
            search_scope=search_scope,
            attributes=attrs
        )

        results = []
        for entry in self._connection.entries:
            results.append({
                "dn": str(entry.entry_dn),
                "attributes": dict(entry.entry_attributes_as_dict)
            })

        return results
```

```python
# servers/ldap/tools.py

class LDAPTools:
    """LDAP 工具集"""

    def __init__(self, client: LDAPClient):
        self._client = client

    async def search_users(
        self,
        filter_expr: str = "(objectClass=user)",
        attributes: List[str] = None
    ) -> ToolResult:
        """搜索用戶"""
        try:
            default_attrs = [
                "sAMAccountName",
                "displayName",
                "mail",
                "memberOf",
                "department"
            ]

            results = self._client.search(
                filter_expr,
                attributes=attributes or default_attrs
            )

            return ToolResult(success=True, data={"users": results})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def get_user(
        self,
        username: str
    ) -> ToolResult:
        """獲取用戶詳情"""
        try:
            filter_expr = f"(sAMAccountName={username})"
            results = self._client.search(filter_expr)

            if not results:
                return ToolResult(success=False, error="User not found")

            return ToolResult(success=True, data={"user": results[0]})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def search_groups(
        self,
        filter_expr: str = "(objectClass=group)",
        attributes: List[str] = None
    ) -> ToolResult:
        """搜索群組"""
        try:
            default_attrs = ["cn", "description", "member"]

            results = self._client.search(
                filter_expr,
                attributes=attributes or default_attrs
            )

            return ToolResult(success=True, data={"groups": results})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def get_user_groups(
        self,
        username: str
    ) -> ToolResult:
        """獲取用戶所屬群組"""
        try:
            # 先獲取用戶
            user_result = await self.get_user(username)
            if not user_result.success:
                return user_result

            # 獲取 memberOf 屬性
            member_of = user_result.data["user"]["attributes"].get("memberOf", [])

            return ToolResult(
                success=True,
                data={"groups": member_of}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**風險等級**:
| 工具 | 風險等級 | 審批需求 |
|------|---------|---------|
| search_users | LOW | NONE |
| get_user | LOW | NONE |
| search_groups | LOW | NONE |
| get_user_groups | LOW | NONE |

**驗收標準**:
- [ ] 支援 LDAP 和 LDAPS
- [ ] 用戶查詢正常
- [ ] 群組查詢正常
- [ ] 連接管理正常
- [ ] 測試覆蓋率 > 85%

---

## 技術規格

### 依賴套件

```bash
pip install asyncssh aiofiles ldap3
```

### 文件結構

```
backend/src/integrations/mcp/servers/
├── shell/
│   ├── __init__.py
│   ├── executor.py      # Shell 執行器
│   ├── tools.py         # Shell 工具
│   └── server.py        # Shell MCP Server
│
├── filesystem/
│   ├── __init__.py
│   ├── sandbox.py       # 文件系統沙箱
│   ├── tools.py         # Filesystem 工具
│   └── server.py        # Filesystem MCP Server
│
├── ssh/
│   ├── __init__.py
│   ├── connection.py    # SSH 連接池
│   ├── tools.py         # SSH 工具
│   └── server.py        # SSH MCP Server
│
└── ldap/
    ├── __init__.py
    ├── client.py        # LDAP 客戶端
    ├── tools.py         # LDAP 工具
    └── server.py        # LDAP MCP Server
```

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| Shell 注入攻擊 | 高 | 高 | 命令白名單 + 參數驗證 |
| 路徑穿越攻擊 | 中 | 高 | 沙箱 + 路徑規範化 |
| SSH 憑證洩漏 | 低 | 高 | 安全存儲 + 審計日誌 |
| LDAP 信息洩漏 | 低 | 中 | 屬性過濾 + 權限控制 |

---

## 驗證計劃

### 單元測試
- Shell 命令驗證
- 沙箱路徑驗證
- SSH 連接池
- LDAP 搜索

### 整合測試
- 本地 Shell 執行
- 文件讀寫
- SSH 遠端連接 (測試 VM)
- LDAP 查詢 (測試 AD)

### 安全測試
- 命令注入測試
- 路徑穿越測試
- 認證繞過測試

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
