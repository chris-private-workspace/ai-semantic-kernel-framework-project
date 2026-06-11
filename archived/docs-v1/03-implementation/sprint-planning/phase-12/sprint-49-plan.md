# Sprint 49: Tools & Hooks System - 工具與攔截系統

**Sprint 目標**: 實現 Claude SDK 內建工具和 Hooks 攔截系統
**週期**: Week 3-4 (2 週)
**Story Points**: 32 點
**MVP 功能**: F12 - Claude Agent SDK 工具與控制

---

## Sprint 概覽

### 目標

1. **Built-in Tools** - 實現核心工具 (Read, Write, Edit, Bash, Grep, Glob)
2. **Hooks 系統** - 實現行為攔截機制 (Approval, Audit, RateLimit, Sandbox)
3. **工具權限控制** - 安全控制和執行限制
4. **Web 工具** - 實現 WebSearch 和 WebFetch

### 成功標準

- [ ] 所有 Built-in Tools 可正常執行
- [ ] Hooks 可攔截並控制工具執行
- [ ] ApprovalHook 可要求人工審批
- [ ] SandboxHook 可限制檔案存取範圍
- [ ] 單元測試覆蓋率 ≥ 85%

---

## 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                   Tools & Hooks System                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Hook Chain                        │    │
│  │                                                      │    │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │    │
│  │  │Approval│→ │ Audit  │→ │  Rate  │→ │Sandbox │    │    │
│  │  │  Hook  │  │  Hook  │  │ Limit  │  │  Hook  │    │    │
│  │  └────────┘  └────────┘  └────────┘  └────────┘    │    │
│  │       ↓           ↓           ↓           ↓         │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │              HookResult                       │  │    │
│  │  │  ALLOW | REJECT | MODIFY                     │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Built-in Tools                      │    │
│  │                                                      │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │    │
│  │  │  File   │  │ Command │  │   Web   │             │    │
│  │  │  Tools  │  │  Tools  │  │  Tools  │             │    │
│  │  │         │  │         │  │         │             │    │
│  │  │ • Read  │  │ • Bash  │  │ • Search│             │    │
│  │  │ • Write │  │ • Task  │  │ • Fetch │             │    │
│  │  │ • Edit  │  │         │  │         │             │    │
│  │  │ • Glob  │  └─────────┘  └─────────┘             │    │
│  │  │ • Grep  │                                       │    │
│  │  └─────────┘                                       │    │
│  │                                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## User Stories

### S49-1: Built-in File Tools (8 點)

**描述**: 實現檔案系統操作工具 - Read, Write, Edit, MultiEdit, Glob, Grep。

**驗收標準**:
- [ ] Read 工具可讀取檔案內容，支援行範圍
- [ ] Write 工具可寫入檔案，支援建立目錄
- [ ] Edit 工具可進行文字替換
- [ ] MultiEdit 工具可批次編輯多個檔案
- [ ] Glob 工具可搜尋符合模式的檔案
- [ ] Grep 工具可搜尋檔案內容

**技術任務**:

1. **建立工具基礎架構 (`backend/src/integrations/claude_sdk/tools/__init__.py`)**

```python
"""Built-in tools for Claude SDK."""

from .base import Tool, ToolResult
from .file_tools import Read, Write, Edit, MultiEdit, Glob, Grep
from .command_tools import Bash, Task
from .web_tools import WebSearch, WebFetch
from .registry import get_tool_definitions, execute_tool

__all__ = [
    "Tool",
    "ToolResult",
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "Glob",
    "Grep",
    "Bash",
    "Task",
    "WebSearch",
    "WebFetch",
    "get_tool_definitions",
    "execute_tool",
]
```

2. **建立工具基礎類別 (`backend/src/integrations/claude_sdk/tools/base.py`)**

```python
"""Base classes for Claude SDK tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class ToolResult:
    """Result from tool execution."""

    content: str
    success: bool = True
    error: Optional[str] = None


class Tool(ABC):
    """Base class for all tools."""

    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        pass
```

3. **建立檔案工具 (`backend/src/integrations/claude_sdk/tools/file_tools.py`)**

```python
"""File system tools for Claude SDK."""

import os
import glob as glob_module
import re
from typing import Optional, List, Dict, Any
from pathlib import Path

from .base import Tool, ToolResult


class Read(Tool):
    """Read file contents."""

    name = "Read"
    description = "Read file contents. Supports reading specific line ranges."

    def __init__(self, max_chars: int = 100000):
        self.max_chars = max_chars

    async def execute(
        self,
        path: str,
        encoding: str = "utf-8",
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> ToolResult:
        """
        Read file contents.

        Args:
            path: File path (absolute or relative)
            encoding: Text encoding (default: utf-8)
            start_line: Start reading from this line (1-indexed)
            end_line: Stop reading at this line (inclusive)

        Returns:
            ToolResult with file content
        """
        try:
            path = os.path.abspath(path)

            if not os.path.exists(path):
                return ToolResult(
                    content="",
                    success=False,
                    error=f"File not found: {path}",
                )

            with open(path, "r", encoding=encoding) as f:
                if start_line is not None or end_line is not None:
                    lines = f.readlines()
                    start = (start_line or 1) - 1
                    end = end_line or len(lines)
                    content = "".join(lines[start:end])
                else:
                    content = f.read()

            if len(content) > self.max_chars:
                content = content[:self.max_chars] + f"\n... (truncated at {self.max_chars} chars)"

            return ToolResult(content=content)

        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "encoding": {"type": "string", "default": "utf-8"},
                "start_line": {"type": "integer", "description": "Start line (1-indexed)"},
                "end_line": {"type": "integer", "description": "End line (inclusive)"},
            },
            "required": ["path"],
        }


class Write(Tool):
    """Write content to a file."""

    name = "Write"
    description = "Write content to a file. Can create parent directories."

    async def execute(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = False,
        overwrite: bool = True,
    ) -> ToolResult:
        """
        Write content to file.

        Args:
            path: File path
            content: Content to write
            encoding: Text encoding
            create_dirs: Create parent directories if needed
            overwrite: Overwrite if file exists

        Returns:
            ToolResult indicating success or failure
        """
        try:
            path = os.path.abspath(path)

            if not overwrite and os.path.exists(path):
                return ToolResult(
                    content="",
                    success=False,
                    error=f"File already exists: {path}",
                )

            if create_dirs:
                os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding=encoding) as f:
                f.write(content)

            return ToolResult(content=f"Successfully wrote {len(content)} chars to {path}")

        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"},
                "encoding": {"type": "string", "default": "utf-8"},
                "create_dirs": {"type": "boolean", "default": False},
                "overwrite": {"type": "boolean", "default": True},
            },
            "required": ["path", "content"],
        }


class Edit(Tool):
    """Edit existing file content."""

    name = "Edit"
    description = "Edit file by replacing text. Supports replace all occurrences."

    async def execute(
        self,
        path: str,
        old_text: str,
        new_text: str,
        replace_all: bool = False,
    ) -> ToolResult:
        """
        Edit file by replacing text.

        Args:
            path: File path
            old_text: Text to find
            new_text: Replacement text
            replace_all: Replace all occurrences

        Returns:
            ToolResult indicating success or failure
        """
        try:
            path = os.path.abspath(path)

            if not os.path.exists(path):
                return ToolResult(
                    content="",
                    success=False,
                    error=f"File not found: {path}",
                )

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if old_text not in content:
                return ToolResult(
                    content="",
                    success=False,
                    error=f"Text not found in file: {old_text[:50]}...",
                )

            if replace_all:
                new_content = content.replace(old_text, new_text)
                count = content.count(old_text)
            else:
                new_content = content.replace(old_text, new_text, 1)
                count = 1

            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult(content=f"Replaced {count} occurrence(s) in {path}")

        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "old_text": {"type": "string", "description": "Text to find"},
                "new_text": {"type": "string", "description": "Replacement text"},
                "replace_all": {"type": "boolean", "default": False},
            },
            "required": ["path", "old_text", "new_text"],
        }


class MultiEdit(Tool):
    """Apply multiple edits atomically."""

    name = "MultiEdit"
    description = "Apply multiple edits to files atomically."

    async def execute(self, edits: List[Dict[str, str]]) -> ToolResult:
        """
        Apply multiple edits.

        Args:
            edits: List of edit operations, each with path, old_text, new_text

        Returns:
            ToolResult indicating success or failure
        """
        edit_tool = Edit()
        results = []
        failed = []

        for i, edit in enumerate(edits):
            result = await edit_tool.execute(**edit)
            if result.success:
                results.append(f"Edit {i+1}: {result.content}")
            else:
                failed.append(f"Edit {i+1} failed: {result.error}")

        if failed:
            return ToolResult(
                content="\n".join(results + failed),
                success=False,
                error=f"{len(failed)} edit(s) failed",
            )

        return ToolResult(content=f"Applied {len(edits)} edits successfully")

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "edits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "old_text": {"type": "string"},
                            "new_text": {"type": "string"},
                        },
                        "required": ["path", "old_text", "new_text"],
                    },
                },
            },
            "required": ["edits"],
        }


class Glob(Tool):
    """Find files by pattern."""

    name = "Glob"
    description = "Find files matching a glob pattern."

    def __init__(self, max_files: int = 10000):
        self.max_files = max_files

    async def execute(
        self,
        pattern: str,
        path: Optional[str] = None,
        exclude: Optional[List[str]] = None,
        include_hidden: bool = False,
    ) -> ToolResult:
        """
        Find files by pattern.

        Args:
            pattern: Glob pattern (e.g., **/*.py)
            path: Base directory
            exclude: Patterns to exclude
            include_hidden: Include hidden files

        Returns:
            ToolResult with matching file paths
        """
        try:
            base_path = os.path.abspath(path or ".")
            full_pattern = os.path.join(base_path, pattern)

            files = glob_module.glob(full_pattern, recursive=True)

            # Filter excludes
            if exclude:
                for exc in exclude:
                    exc_pattern = os.path.join(base_path, exc)
                    exc_files = set(glob_module.glob(exc_pattern, recursive=True))
                    files = [f for f in files if f not in exc_files]

            # Filter hidden
            if not include_hidden:
                files = [f for f in files if not any(
                    part.startswith(".") for part in Path(f).parts
                )]

            # Limit results
            if len(files) > self.max_files:
                files = files[:self.max_files]
                truncated = True
            else:
                truncated = False

            result = "\n".join(files)
            if truncated:
                result += f"\n... (truncated at {self.max_files} files)"

            return ToolResult(content=result)

        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern"},
                "path": {"type": "string", "description": "Base directory"},
                "exclude": {"type": "array", "items": {"type": "string"}},
                "include_hidden": {"type": "boolean", "default": False},
            },
            "required": ["pattern"],
        }


class Grep(Tool):
    """Search file contents."""

    name = "Grep"
    description = "Search for patterns in file contents."

    def __init__(self, max_matches: int = 1000):
        self.max_matches = max_matches

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        regex: bool = False,
        case_sensitive: bool = True,
        before: int = 0,
        after: int = 0,
        max_matches: Optional[int] = None,
    ) -> ToolResult:
        """
        Search file contents.

        Args:
            pattern: Search pattern
            path: File or directory path
            regex: Use regex matching
            case_sensitive: Case sensitive search
            before: Context lines before match
            after: Context lines after match
            max_matches: Limit results

        Returns:
            ToolResult with matching lines
        """
        try:
            path = os.path.abspath(path)
            limit = max_matches or self.max_matches
            matches = []

            if os.path.isfile(path):
                files = [path]
            else:
                files = glob_module.glob(os.path.join(path, "**/*"), recursive=True)
                files = [f for f in files if os.path.isfile(f)]

            flags = 0 if case_sensitive else re.IGNORECASE
            if regex:
                compiled = re.compile(pattern, flags)
            else:
                compiled = re.compile(re.escape(pattern), flags)

            for filepath in files:
                if len(matches) >= limit:
                    break

                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines):
                        if compiled.search(line):
                            match_lines = []

                            # Add context before
                            start = max(0, i - before)
                            for j in range(start, i):
                                match_lines.append(f"  {j+1}: {lines[j].rstrip()}")

                            # Add match line
                            match_lines.append(f"→ {i+1}: {line.rstrip()}")

                            # Add context after
                            end = min(len(lines), i + after + 1)
                            for j in range(i + 1, end):
                                match_lines.append(f"  {j+1}: {lines[j].rstrip()}")

                            matches.append(f"{filepath}:\n" + "\n".join(match_lines))

                            if len(matches) >= limit:
                                break

                except Exception:
                    continue

            result = "\n\n".join(matches)
            if len(matches) >= limit:
                result += f"\n\n... (limited to {limit} matches)"

            return ToolResult(content=result or "No matches found")

        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern"},
                "path": {"type": "string", "default": "."},
                "regex": {"type": "boolean", "default": False},
                "case_sensitive": {"type": "boolean", "default": True},
                "before": {"type": "integer", "default": 0},
                "after": {"type": "integer", "default": 0},
                "max_matches": {"type": "integer"},
            },
            "required": ["pattern"],
        }
```

---

### S49-2: Bash 和 Task 工具 (6 點)

**描述**: 實現命令執行工具 Bash 和子任務委派工具 Task。

**驗收標準**:
- [ ] Bash 工具可執行 shell 命令
- [ ] 支援工作目錄設定
- [ ] 支援超時控制
- [ ] 實現命令白名單/黑名單
- [ ] Task 工具可委派子任務給子代理

**技術任務**:

1. **建立命令工具 (`backend/src/integrations/claude_sdk/tools/command_tools.py`)**

```python
"""Command execution tools for Claude SDK."""

import asyncio
import os
import re
from typing import Optional, List, Dict, Any

from .base import Tool, ToolResult


class Bash(Tool):
    """Execute shell commands."""

    name = "Bash"
    description = "Execute shell commands with security controls."

    # Default dangerous patterns
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",
        r":()\s*{\s*:|:&\s*};\s*:",  # Fork bomb
        r">\s*/dev/sd",
        r"mkfs\.",
        r"dd\s+if=",
        r"curl\s+.*\|\s*bash",
        r"wget\s+.*\|\s*sh",
    ]

    def __init__(
        self,
        allowed_commands: Optional[List[str]] = None,
        denied_commands: Optional[List[str]] = None,
        timeout: int = 120,
        max_output: int = 100000,
    ):
        self.allowed_commands = allowed_commands
        self.denied_commands = denied_commands or []
        self.timeout = timeout
        self.max_output = max_output

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ToolResult:
        """
        Execute a shell command.

        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Timeout in seconds
            env: Environment variables

        Returns:
            ToolResult with stdout, stderr, and exit code
        """
        try:
            # Security checks
            security_result = self._check_security(command)
            if not security_result.success:
                return security_result

            # Set up environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)

            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=exec_env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout or self.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    content="",
                    success=False,
                    error=f"Command timed out after {timeout or self.timeout}s",
                )

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Truncate if needed
            if len(stdout_str) > self.max_output:
                stdout_str = stdout_str[:self.max_output] + "\n... (truncated)"
            if len(stderr_str) > self.max_output:
                stderr_str = stderr_str[:self.max_output] + "\n... (truncated)"

            output = f"Exit code: {process.returncode}\n"
            if stdout_str:
                output += f"\nSTDOUT:\n{stdout_str}"
            if stderr_str:
                output += f"\nSTDERR:\n{stderr_str}"

            return ToolResult(
                content=output,
                success=process.returncode == 0,
            )

        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def _check_security(self, command: str) -> ToolResult:
        """Check command against security rules."""
        # Check dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return ToolResult(
                    content="",
                    success=False,
                    error=f"Blocked dangerous command pattern: {pattern}",
                )

        # Check denied commands
        for denied in self.denied_commands:
            if denied in command:
                return ToolResult(
                    content="",
                    success=False,
                    error=f"Command denied: {denied}",
                )

        # Check allowed commands (if specified)
        if self.allowed_commands:
            cmd_parts = command.split()
            if cmd_parts and cmd_parts[0] not in self.allowed_commands:
                return ToolResult(
                    content="",
                    success=False,
                    error=f"Command not in allowed list: {cmd_parts[0]}",
                )

        return ToolResult(content="", success=True)

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
                "cwd": {"type": "string", "description": "Working directory"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"},
                "env": {"type": "object", "description": "Environment variables"},
            },
            "required": ["command"],
        }


class Task(Tool):
    """Delegate subtasks to specialized subagents."""

    name = "Task"
    description = "Delegate complex subtasks to specialized subagents."

    async def execute(
        self,
        prompt: str,
        tools: Optional[List[str]] = None,
        agent_type: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> ToolResult:
        """
        Delegate a subtask.

        Args:
            prompt: Task description
            tools: Tools for subagent
            agent_type: Specialized agent type
            system_prompt: Custom instructions
            max_tokens: Token limit
            timeout: Timeout in seconds

        Returns:
            ToolResult with subagent response
        """
        try:
            # Import here to avoid circular dependency
            from ..client import ClaudeSDKClient

            # Create subagent
            client = ClaudeSDKClient(
                system_prompt=system_prompt,
                tools=tools or [],
            )

            result = await client.query(
                prompt=prompt,
                max_tokens=max_tokens,
                timeout=timeout,
            )

            return ToolResult(content=result.content, success=result.successful)

        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Task description"},
                "tools": {"type": "array", "items": {"type": "string"}},
                "agent_type": {"type": "string"},
                "system_prompt": {"type": "string"},
                "max_tokens": {"type": "integer"},
                "timeout": {"type": "integer"},
            },
            "required": ["prompt"],
        }
```

---

### S49-3: Hooks 基礎系統 (10 點)

**描述**: 實現 Hooks 攔截系統，包含 ApprovalHook、AuditHook、RateLimitHook、SandboxHook。

**驗收標準**:
- [ ] Hook 基礎類別定義完成
- [ ] ApprovalHook 可要求人工審批寫入操作
- [ ] AuditHook 可記錄所有工具調用
- [ ] RateLimitHook 可限制調用頻率
- [ ] SandboxHook 可限制檔案存取範圍
- [ ] Hooks 可組合使用，依優先順序執行

**技術任務**:

1. **建立 Hooks 基礎架構 (`backend/src/integrations/claude_sdk/hooks/__init__.py`)**

```python
"""Hooks system for Claude SDK."""

from .base import Hook, HookResult
from .approval import ApprovalHook
from .audit import AuditHook
from .rate_limit import RateLimitHook
from .sandbox import SandboxHook

__all__ = [
    "Hook",
    "HookResult",
    "ApprovalHook",
    "AuditHook",
    "RateLimitHook",
    "SandboxHook",
]
```

2. **建立 Hook 基礎類別 (`backend/src/integrations/claude_sdk/hooks/base.py`)**

```python
"""Base Hook class for Claude SDK."""

from abc import ABC
from typing import Optional

from ..types import (
    ToolCallContext,
    ToolResultContext,
    QueryContext,
    HookResult,
)


class Hook(ABC):
    """
    Base class for all hooks.

    Hooks provide interception points throughout agent execution.
    Implement specific methods to intercept at different lifecycle stages.
    """

    priority: int = 50  # Higher priority executes first (0-100)

    async def on_session_start(self, session_id: str) -> None:
        """Called when a new session starts."""
        pass

    async def on_session_end(self, session_id: str) -> None:
        """Called when session ends."""
        pass

    async def on_query_start(self, context: QueryContext) -> HookResult:
        """Called before processing a query."""
        return HookResult.ALLOW

    async def on_query_end(self, context: QueryContext, result: str) -> None:
        """Called after query completes."""
        pass

    async def on_tool_call(self, context: ToolCallContext) -> HookResult:
        """
        Called before tool execution.

        Returns:
            HookResult.ALLOW - Allow execution
            HookResult.reject(reason) - Block execution
            HookResult.modify(args) - Modify arguments
        """
        return HookResult.ALLOW

    async def on_tool_result(self, context: ToolResultContext) -> None:
        """Called after tool execution completes."""
        pass

    async def on_error(self, error: Exception) -> None:
        """Called when an error occurs."""
        pass
```

3. **建立 ApprovalHook (`backend/src/integrations/claude_sdk/hooks/approval.py`)**

```python
"""Approval hook requiring human confirmation for certain operations."""

from typing import Optional, Set, Callable, Awaitable

from .base import Hook
from ..types import ToolCallContext, HookResult


class ApprovalHook(Hook):
    """
    Require human approval for specific tool operations.

    Example:
        hook = ApprovalHook(
            tools_requiring_approval={"Write", "Edit", "Bash"},
            approval_handler=my_approval_function
        )
    """

    priority = 90  # High priority - check early

    DEFAULT_WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "Bash"}

    def __init__(
        self,
        tools_requiring_approval: Optional[Set[str]] = None,
        approval_handler: Optional[Callable[..., Awaitable[bool]]] = None,
    ):
        """
        Initialize approval hook.

        Args:
            tools_requiring_approval: Set of tool names requiring approval
            approval_handler: Async function to request approval
        """
        self.tools = tools_requiring_approval or self.DEFAULT_WRITE_TOOLS
        self.approval_handler = approval_handler or self._default_approval

    async def on_tool_call(self, context: ToolCallContext) -> HookResult:
        """Check if tool requires approval."""
        if context.tool_name not in self.tools:
            return HookResult.ALLOW

        approved = await self.approval_handler(
            tool=context.tool_name,
            args=context.args,
            session_id=context.session_id,
        )

        if approved:
            return HookResult.ALLOW
        return HookResult.reject(f"User rejected {context.tool_name}")

    async def _default_approval(
        self,
        tool: str,
        args: dict,
        session_id: Optional[str],
    ) -> bool:
        """Default CLI approval prompt."""
        print(f"\n{'='*50}")
        print(f"APPROVAL REQUIRED: {tool}")
        print(f"Arguments: {args}")
        print(f"{'='*50}")

        response = input("Approve? (y/n): ").strip().lower()
        return response == "y"
```

4. **建立 AuditHook (`backend/src/integrations/claude_sdk/hooks/audit.py`)**

```python
"""Audit hook for logging all agent activities."""

import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from .base import Hook
from ..types import ToolCallContext, ToolResultContext, QueryContext, HookResult


class AuditHook(Hook):
    """
    Log all agent activities for audit trail.

    Example:
        hook = AuditHook(log_file="agent_audit.log")
    """

    priority = 100  # Highest priority - always log first

    SENSITIVE_KEYS = {"password", "token", "api_key", "secret", "credential"}

    def __init__(
        self,
        log_file: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize audit hook.

        Args:
            log_file: Path to log file (optional)
            logger: Logger instance (optional)
        """
        self.log_file = log_file
        self.logger = logger or logging.getLogger("claude_sdk.audit")

    async def on_session_start(self, session_id: str) -> None:
        self._log("SESSION_START", {"session_id": session_id})

    async def on_session_end(self, session_id: str) -> None:
        self._log("SESSION_END", {"session_id": session_id})

    async def on_query_start(self, context: QueryContext) -> HookResult:
        self._log("QUERY_START", {
            "session_id": context.session_id,
            "prompt": context.prompt[:200] if context.prompt else "",
            "tools": context.tools,
        })
        return HookResult.ALLOW

    async def on_query_end(self, context: QueryContext, result: str) -> None:
        self._log("QUERY_END", {
            "session_id": context.session_id,
            "result_length": len(result),
        })

    async def on_tool_call(self, context: ToolCallContext) -> HookResult:
        self._log("TOOL_CALL", {
            "session_id": context.session_id,
            "tool": context.tool_name,
            "tool_source": context.tool_source,
            "mcp_server": context.mcp_server,
            "args": self._sanitize_args(context.args),
        })
        return HookResult.ALLOW

    async def on_tool_result(self, context: ToolResultContext) -> None:
        self._log("TOOL_RESULT", {
            "session_id": context.session_id,
            "tool": context.tool_name,
            "success": context.success,
            "result_length": len(context.result) if context.result else 0,
            "duration": context.duration,
        })

    async def on_error(self, error: Exception) -> None:
        self._log("ERROR", {
            "error_type": type(error).__name__,
            "error_message": str(error),
        })

    def _log(self, event: str, data: Dict[str, Any]) -> None:
        """Write log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            **data,
        }

        # Log to logger
        self.logger.info(json.dumps(entry))

        # Log to file if specified
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from args."""
        sanitized = {}
        for key, value in args.items():
            if any(s in key.lower() for s in self.SENSITIVE_KEYS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_args(value)
            else:
                sanitized[key] = value
        return sanitized
```

5. **建立 RateLimitHook (`backend/src/integrations/claude_sdk/hooks/rate_limit.py`)**

```python
"""Rate limiting hook for controlling execution speed."""

import time
from typing import List

from .base import Hook
from ..types import ToolCallContext, ToolResultContext, HookResult


class RateLimitHook(Hook):
    """
    Limit tool execution rate.

    Example:
        hook = RateLimitHook(max_calls_per_minute=60, max_concurrent=5)
    """

    priority = 80  # High priority - check before expensive operations

    def __init__(
        self,
        max_calls_per_minute: int = 60,
        max_concurrent: int = 5,
    ):
        """
        Initialize rate limit hook.

        Args:
            max_calls_per_minute: Maximum calls per minute
            max_concurrent: Maximum concurrent operations
        """
        self.max_calls_per_minute = max_calls_per_minute
        self.max_concurrent = max_concurrent
        self.call_times: List[float] = []
        self.active_calls = 0

    async def on_tool_call(self, context: ToolCallContext) -> HookResult:
        now = time.time()

        # Clean old entries (older than 1 minute)
        self.call_times = [t for t in self.call_times if now - t < 60]

        # Check rate limit
        if len(self.call_times) >= self.max_calls_per_minute:
            wait_time = 60 - (now - self.call_times[0])
            return HookResult.reject(
                f"Rate limit exceeded. Try again in {wait_time:.1f}s"
            )

        # Check concurrent limit
        if self.active_calls >= self.max_concurrent:
            return HookResult.reject(
                f"Too many concurrent calls ({self.max_concurrent} max)"
            )

        self.call_times.append(now)
        self.active_calls += 1
        return HookResult.ALLOW

    async def on_tool_result(self, context: ToolResultContext) -> None:
        self.active_calls = max(0, self.active_calls - 1)
```

6. **建立 SandboxHook (`backend/src/integrations/claude_sdk/hooks/sandbox.py`)**

```python
"""Sandbox hook for restricting file system access."""

import os
from typing import List, Set, Optional

from .base import Hook
from ..types import ToolCallContext, HookResult


class SandboxHook(Hook):
    """
    Restrict file system access to specific directories.

    Example:
        hook = SandboxHook(
            allowed_paths=["/project", "/tmp"],
            denied_patterns=[".env", ".git", "node_modules"]
        )
    """

    priority = 85  # High priority - security check

    FILE_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "Glob", "Grep"}

    DEFAULT_DENIED_PATTERNS = [
        ".env",
        ".git",
        "node_modules",
        "__pycache__",
        ".ssh",
        ".aws",
        "credentials",
        ".npmrc",
        ".pypirc",
    ]

    def __init__(
        self,
        allowed_paths: List[str],
        denied_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize sandbox hook.

        Args:
            allowed_paths: List of allowed directory paths
            denied_patterns: Patterns to block (in path)
        """
        self.allowed_paths = [os.path.abspath(p) for p in allowed_paths]
        self.denied_patterns = denied_patterns or self.DEFAULT_DENIED_PATTERNS

    async def on_tool_call(self, context: ToolCallContext) -> HookResult:
        if context.tool_name not in self.FILE_TOOLS:
            return HookResult.ALLOW

        # Get path from args
        path = context.args.get("path", "")
        if not path:
            return HookResult.ALLOW

        abs_path = os.path.abspath(path)

        # Check allowed paths
        if not any(abs_path.startswith(allowed) for allowed in self.allowed_paths):
            return HookResult.reject(
                f"Access denied: {path} is outside allowed directories"
            )

        # Check denied patterns
        for pattern in self.denied_patterns:
            if pattern in abs_path:
                return HookResult.reject(
                    f"Access denied: {pattern} files are restricted"
                )

        return HookResult.ALLOW
```

---

### S49-4: Web Tools 實現 (8 點)

**描述**: 實現 WebSearch 和 WebFetch 工具，支援網頁搜尋和內容抓取。

**驗收標準**:
- [ ] WebSearch 可執行網頁搜尋並返回結果
- [ ] WebFetch 可抓取網頁內容
- [ ] 支援 HTTP headers 設定
- [ ] 支援超時控制
- [ ] 錯誤處理完善

**技術任務**:

1. **建立 Web 工具 (`backend/src/integrations/claude_sdk/tools/web_tools.py`)**

```python
"""Web tools for Claude SDK."""

import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .base import Tool, ToolResult


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str


class WebSearch(Tool):
    """Search the web."""

    name = "WebSearch"
    description = "Search the web and return results."

    def __init__(self, search_api_key: Optional[str] = None):
        self.api_key = search_api_key

    async def execute(
        self,
        query: str,
        num_results: int = 10,
    ) -> ToolResult:
        """
        Search the web.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            ToolResult with search results
        """
        try:
            # This is a placeholder - in production, integrate with a search API
            # Options: Google Custom Search, Bing Search, Brave Search, etc.

            # For now, return a helpful message
            return ToolResult(
                content=f"Search query: {query}\n"
                        f"(WebSearch requires search API configuration)",
                success=True,
            )

        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        }


class WebFetch(Tool):
    """Fetch content from a URL."""

    name = "WebFetch"
    description = "Fetch and process content from a URL."

    def __init__(
        self,
        timeout: int = 30,
        max_content_length: int = 1000000,
    ):
        self.timeout = timeout
        self.max_content_length = max_content_length

    async def execute(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
        timeout: Optional[int] = None,
    ) -> ToolResult:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch
            headers: Request headers
            method: HTTP method (default: GET)
            timeout: Timeout in seconds

        Returns:
            ToolResult with page content
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout or self.timeout),
                ) as response:
                    content = await response.text()

                    # Truncate if needed
                    if len(content) > self.max_content_length:
                        content = content[:self.max_content_length]
                        content += f"\n... (truncated at {self.max_content_length} chars)"

                    result = f"Status: {response.status}\n"
                    result += f"Content-Type: {response.headers.get('Content-Type', 'unknown')}\n"
                    result += f"\n{content}"

                    return ToolResult(
                        content=result,
                        success=response.status < 400,
                    )

        except aiohttp.ClientError as e:
            return ToolResult(
                content="",
                success=False,
                error=f"HTTP error: {str(e)}",
            )
        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "headers": {"type": "object", "description": "Request headers"},
                "method": {"type": "string", "default": "GET"},
                "timeout": {"type": "integer"},
            },
            "required": ["url"],
        }
```

---

## 時間規劃

| 任務 | 預估時間 | 負責人 |
|------|----------|--------|
| S49-1: Built-in File Tools | 2 天 | Backend |
| S49-2: Bash 和 Task 工具 | 1.5 天 | Backend |
| S49-3: Hooks 基礎系統 | 3 天 | Backend |
| S49-4: Web Tools 實現 | 2 天 | Backend |
| 整合測試 | 1 天 | QA |
| 文檔更新 | 0.5 天 | Tech Writer |

---

## 測試要求

### 單元測試

```python
# tests/unit/integrations/claude_sdk/tools/test_file_tools.py

import pytest
import tempfile
import os

from src.integrations.claude_sdk.tools.file_tools import Read, Write, Edit, Glob, Grep


class TestRead:
    """Tests for Read tool."""

    @pytest.mark.asyncio
    async def test_read_file(self, tmp_path):
        """Test reading a file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!")

        tool = Read()
        result = await tool.execute(path=str(file_path))

        assert result.success
        assert result.content == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_file_not_found(self):
        """Test reading non-existent file."""
        tool = Read()
        result = await tool.execute(path="/nonexistent/file.txt")

        assert not result.success
        assert "not found" in result.error.lower()


class TestSandboxHook:
    """Tests for SandboxHook."""

    @pytest.mark.asyncio
    async def test_allows_within_sandbox(self):
        """Test that paths within sandbox are allowed."""
        from src.integrations.claude_sdk.hooks import SandboxHook
        from src.integrations.claude_sdk.types import ToolCallContext

        hook = SandboxHook(allowed_paths=["/project"])
        context = ToolCallContext(
            tool_name="Read",
            args={"path": "/project/src/main.py"},
        )

        result = await hook.on_tool_call(context)
        assert result.allowed

    @pytest.mark.asyncio
    async def test_blocks_outside_sandbox(self):
        """Test that paths outside sandbox are blocked."""
        from src.integrations.claude_sdk.hooks import SandboxHook
        from src.integrations.claude_sdk.types import ToolCallContext

        hook = SandboxHook(allowed_paths=["/project"])
        context = ToolCallContext(
            tool_name="Read",
            args={"path": "/etc/passwd"},
        )

        result = await hook.on_tool_call(context)
        assert result.is_rejected
```

---

## 風險與緩解

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 命令注入攻擊 | 高 | 中 | 嚴格的命令白名單和黑名單 |
| 檔案系統越權存取 | 高 | 中 | SandboxHook 強制執行 |
| Rate Limit 繞過 | 中 | 低 | 多層 rate limiting |
| Hook 執行順序問題 | 中 | 中 | 明確的優先級系統 |

---

## 完成定義

- [ ] 所有 User Stories 完成並通過驗收
- [ ] 單元測試覆蓋率 ≥ 85%
- [ ] 安全審查通過
- [ ] 文檔更新完成
- [ ] Code Review 完成

---

## 依賴

- **Sprint 48**: Core SDK Integration (必須完成)
- **外部依賴**: aiohttp (Web 工具)
