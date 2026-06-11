# Sprint 113: MCP Security + Validation

## 概述

Sprint 113 是 Phase 31 的最後一個 Sprint，專注於 MCP 模組的安全閉環（Permission Pattern 運行時啟用、Shell/SSH 命令白名單）、ContextSynchronizer 並發安全最小修復、全局異常處理器修復，以及 Phase 31 整體的整合測試和安全掃描。

## 目標

1. MCP Permission Pattern 運行時啟用（28 patterns → 實際檢查）
2. Shell/SSH MCP 命令白名單 + HITL 審批機制
3. ContextSynchronizer asyncio.Lock 最小修復
4. 全局異常處理器修復（防止 error_type 洩漏）
5. Phase 31 整合測試 + 安全驗證

## Story Points: 40 點

## 前置條件

- ✅ Sprint 111 完成 (Auth + Quick Wins)
- ✅ Sprint 112 完成 (Mock Separation + Redis)
- ✅ 全局 Auth Middleware 已啟用
- ✅ Factory Pattern 已建立

## 任務分解

### Story 113-1: MCP Permission 運行時啟用 (2-3 天, P0)

**目標**: MCP 模組已定義 28 個 Permission Pattern 但運行時完全未調用 `check_permission`。在所有 MCP server handler 中插入權限檢查。

**交付物**:
- 修改 `backend/src/integrations/mcp/` 下的所有 MCP server handler
- 新增/修改 permission check middleware

**背景分析**:

根據 Security Architect 和 Integration Architect 的報告，MCP 模組中：
- 定義了 28 個 permission patterns（如 `filesystem:read`, `shell:execute` 等）
- 但 0 處調用 `check_permission()` — 安全設計形同虛設
- 5 個 MCP servers: Azure, Filesystem, LDAP, Shell, SSH

**修改方式**:

1. **找到 permission pattern 定義位置**:
```bash
grep -rn "permission" backend/src/integrations/mcp/
grep -rn "check_permission" backend/src/integrations/mcp/
```

2. **在每個 MCP handler 中插入 check_permission**:

```python
# Before (無權限檢查)
async def handle_filesystem_read(request):
    path = request.params["path"]
    return await read_file(path)

# After (有權限檢查)
async def handle_filesystem_read(request, user: dict = Depends(get_current_user)):
    path = request.params["path"]

    # 權限檢查
    await check_permission(
        user_id=user["user_id"],
        permission="filesystem:read",
        resource=path,
        context={"mcp_server": "filesystem"}
    )

    return await read_file(path)
```

3. **漸進式啟用策略**:

```python
# Phase 1: Log-only 模式（本 Sprint）
MCP_PERMISSION_MODE = os.environ.get("MCP_PERMISSION_MODE", "log")

async def check_permission(user_id, permission, resource, context):
    """檢查用戶是否有指定的 MCP 操作權限"""
    has_permission = await _evaluate_permission(user_id, permission, resource)

    if not has_permission:
        if MCP_PERMISSION_MODE == "enforce":
            raise PermissionError(
                f"User {user_id} lacks permission '{permission}' "
                f"for resource '{resource}'"
            )
        else:  # log mode
            logger.warning(
                f"PERMISSION_DENIED (log-only): user={user_id}, "
                f"permission={permission}, resource={resource}"
            )
```

4. **覆蓋範圍**:

| MCP Server | Handlers | Permission Patterns |
|------------|----------|-------------------|
| Azure | TBD | azure:* |
| Filesystem | TBD | filesystem:read, filesystem:write, filesystem:delete |
| LDAP | TBD | ldap:read, ldap:write |
| Shell | TBD | shell:execute |
| SSH | TBD | ssh:connect, ssh:execute |

**驗收標準**:
- [ ] 所有 MCP server handler 中有 check_permission 調用
- [ ] 28 個 permission patterns 全部對應到 handler
- [ ] Log-only 模式下不阻斷操作，但記錄 WARNING
- [ ] Enforce 模式下拒絕無權限操作（返回 403）
- [ ] MCP_PERMISSION_MODE 可通過環境變量切換
- [ ] 單元測試覆蓋 log-only 和 enforce 兩種模式

### Story 113-2: Shell/SSH MCP 命令白名單 (2 天, P0)

**目標**: 為 Shell 和 SSH MCP servers 實現命令白名單機制，非白名單命令需經 HITL 審批

**交付物**:
- 新增 `backend/src/integrations/mcp/security/command_whitelist.py`
- 修改 Shell MCP server handler
- 修改 SSH MCP server handler

**設計方案**:

```python
# backend/src/integrations/mcp/security/command_whitelist.py
from typing import List, Optional
import re

class CommandWhitelist:
    """MCP 命令白名單管理器

    白名單中的命令直接執行，不在白名單中的需要 HITL 審批。
    """

    # 預設白名單（安全的唯讀命令）
    DEFAULT_WHITELIST: List[str] = [
        # 系統資訊
        "whoami", "hostname", "date", "uptime",
        # 檔案查看（唯讀）
        "ls", "dir", "cat", "head", "tail", "wc", "find", "grep",
        # 網路診斷
        "ping", "nslookup", "dig", "traceroute",
        # 系統狀態
        "ps", "top", "df", "du", "free",
        # AD 相關（唯讀）
        "dsquery", "dsget", "Get-ADUser", "Get-ADGroup",
    ]

    # 明確封鎖（即使在白名單中也不允許）
    BLOCKED_PATTERNS: List[str] = [
        r"rm\s+(-rf?|--recursive)", r"del\s+/[sfq]",
        r"format\s+", r"mkfs\.",
        r"dd\s+if=", r">\s*/dev/sd",
        r"chmod\s+777", r"curl.*\|\s*(ba)?sh",
        r"wget.*\|\s*(ba)?sh",
    ]

    def __init__(self, additional_whitelist: Optional[List[str]] = None):
        self._whitelist = set(self.DEFAULT_WHITELIST)
        if additional_whitelist:
            self._whitelist.update(additional_whitelist)
        self._blocked_patterns = [re.compile(p) for p in self.BLOCKED_PATTERNS]

    def check_command(self, command: str) -> str:
        """檢查命令安全性

        Returns:
            "allowed" — 白名單命令，直接執行
            "blocked" — 封鎖命令，拒絕執行
            "requires_approval" — 非白名單命令，需 HITL 審批
        """
        # 先檢查是否在封鎖列表
        for pattern in self._blocked_patterns:
            if pattern.search(command):
                return "blocked"

        # 提取命令名稱（第一個 token）
        cmd_name = command.strip().split()[0] if command.strip() else ""

        # 檢查是否在白名單
        if cmd_name in self._whitelist:
            return "allowed"

        return "requires_approval"
```

**整合到 MCP handler**:

```python
async def handle_shell_execute(request, user):
    command = request.params["command"]
    whitelist = CommandWhitelist()

    result = whitelist.check_command(command)

    if result == "blocked":
        raise PermissionError(f"Command blocked by security policy: {command}")

    if result == "requires_approval":
        # 觸發 HITL 審批流程
        approval = await request_hitl_approval(
            user_id=user["user_id"],
            action="shell:execute",
            details={"command": command},
            reason="Non-whitelisted command requires manual approval"
        )
        if not approval.approved:
            raise PermissionError(f"Command rejected by HITL: {command}")

    # 執行命令
    return await execute_shell_command(command)
```

**驗收標準**:
- [ ] CommandWhitelist 類完整實現
- [ ] 白名單命令直接執行（不觸發審批）
- [ ] 封鎖命令直接拒絕（返回 403）
- [ ] 非白名單命令觸發 HITL 審批
- [ ] HITL 審批拒絕時命令不執行
- [ ] Shell MCP handler 整合白名單
- [ ] SSH MCP handler 整合白名單
- [ ] 白名單可通過環境變量或配置文件擴展
- [ ] 單元測試覆蓋所有三種路徑 (allowed/blocked/requires_approval)

### Story 113-3: ContextSynchronizer asyncio.Lock (0.5 天, P1)

**目標**: 為 2 個 ContextSynchronizer 實現添加 asyncio.Lock，防止並發環境下的競爭條件

**交付物**:
- 修改 2 個 ContextSynchronizer 實現文件

**背景**:

根據 V7 架構分析，存在 2 份 ContextSynchronizer 實現（重複代碼），均使用 in-memory dict 且無鎖保護。在單 Worker 模式下風險較低，但 Multi-Worker 前必須修復。

**修改方式**:

1. **搜索 ContextSynchronizer 定義位置**:
```bash
grep -rn "class ContextSynchronizer" backend/src/
```

2. **添加 asyncio.Lock**:

```python
# Before
class ContextSynchronizer:
    def __init__(self):
        self._contexts: dict[str, Any] = {}

    async def sync_context(self, session_id: str, context: dict) -> None:
        self._contexts[session_id] = context

    async def get_context(self, session_id: str) -> Optional[dict]:
        return self._contexts.get(session_id)

# After
import asyncio

class ContextSynchronizer:
    def __init__(self):
        self._contexts: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def sync_context(self, session_id: str, context: dict) -> None:
        async with self._lock:
            self._contexts[session_id] = {**context}  # 不可變複製

    async def get_context(self, session_id: str) -> Optional[dict]:
        async with self._lock:
            ctx = self._contexts.get(session_id)
            return {**ctx} if ctx else None  # 返回副本，防止外部修改
```

3. **對兩份實現都做相同修改**。

**驗收標準**:
- [ ] 2 個 ContextSynchronizer 都添加了 asyncio.Lock
- [ ] sync_context 在 lock 保護下執行
- [ ] get_context 在 lock 保護下執行
- [ ] 返回 context 的副本（不是原始引用）
- [ ] 單元測試驗證並發安全（asyncio.gather 多個同時寫入）

### Story 113-4: 全局異常處理器修復 (0.25 天, P1)

**目標**: 修改全局異常處理器，防止 `error_type` 在錯誤回應中洩漏，避免暴露內部實現細節

**交付物**:
- 修改全局異常處理器文件

**修改方式**:

1. **找到全局異常處理器**:
```bash
grep -rn "exception_handler\|ExceptionMiddleware" backend/src/
```

2. **修改錯誤回應格式**:

```python
# Before (洩漏 error_type)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "error_type": type(exc).__name__,  # 洩漏: "SQLAlchemyError", "ConnectionRefusedError" 等
            "detail": traceback.format_exc()    # 洩漏: 完整堆疊
        }
    )

# After (安全版本)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # 記錄完整錯誤到日誌（不暴露給客戶端）
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,
        extra={"request_path": request.url.path}
    )

    env = os.environ.get("ENVIRONMENT", "development")

    if env == "development":
        # Development: 包含額外資訊幫助調試
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),  # 僅在 dev 環境
            }
        )
    else:
        # Production: 只返回通用錯誤訊息
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
            }
        )
```

**驗收標準**:
- [ ] 錯誤回應中無 `error_type` 欄位
- [ ] 錯誤回應中無 `traceback` / `stacktrace`
- [ ] Production 環境只返回 "Internal server error"
- [ ] Development 環境包含 detail（幫助調試）
- [ ] 完整錯誤資訊記錄到日誌
- [ ] 日誌包含 request path 上下文

### Story 113-5: Phase 31 整合測試 + 安全掃描 (0.5 天, P0)

**目標**: 驗證 Phase 31 所有 Sprint 的修改協同運作，執行安全掃描確認安全評分提升

**交付物**:
- 新增 `backend/tests/integration/security/test_phase31_integration.py`
- 安全掃描報告

**測試範圍**:

```python
# backend/tests/integration/security/test_phase31_integration.py

class TestPhase31SecurityIntegration:
    """Phase 31 安全加固整合測試"""

    # Sprint 111: Quick Wins
    async def test_cors_origin_correct(self):
        """CORS 允許 localhost:3005"""

    async def test_no_hardcoded_jwt_secret(self):
        """JWT Secret 從環境變量讀取"""

    async def test_no_console_log_in_auth_store(self):
        """authStore 無 console.log"""

    # Sprint 111: Auth
    async def test_unauthenticated_request_returns_401(self):
        """無 Token 請求返回 401"""

    async def test_expired_token_returns_401(self):
        """過期 Token 返回 401"""

    async def test_valid_token_passes(self):
        """有效 Token 正常通過"""

    async def test_public_routes_no_auth(self):
        """白名單路由無需認證"""

    async def test_rate_limiting_returns_429(self):
        """超過限制返回 429"""

    # Sprint 112: Mock Separation
    async def test_no_mock_in_production_code(self):
        """生產代碼無 Mock 類"""

    async def test_factory_production_no_fallback(self):
        """Production 環境 Factory 不 fallback"""

    async def test_redis_approval_storage(self):
        """Redis 審批存儲正常運作"""

    # Sprint 113: MCP Security
    async def test_mcp_permission_check_called(self):
        """MCP handler 調用 check_permission"""

    async def test_shell_whitelist_blocks_dangerous(self):
        """Shell 白名單阻斷危險命令"""

    async def test_shell_non_whitelist_requires_approval(self):
        """非白名單命令觸發 HITL 審批"""

    async def test_context_synchronizer_thread_safe(self):
        """ContextSynchronizer 並發安全"""

    async def test_error_response_no_leak(self):
        """錯誤回應不洩漏 error_type"""
```

**安全掃描項目**:

| 檢查項目 | 方法 | 預期結果 |
|----------|------|---------|
| 硬編碼 secrets | `grep -rn "secret\|password\|api_key" backend/src/` | 0 硬編碼 |
| console.log PII | `grep -rn "console.log" frontend/src/stores/` | 0 結果 |
| Mock in production | `grep -rn "class Mock" backend/src/` | 0 結果 |
| Auth 覆蓋率 | 未帶 Token 請求所有端點 | 全部 401（除白名單） |
| Rate Limiting | 快速連續請求 | 429 觸發 |
| MCP Permission | 調用 MCP handler | check_permission 被調用 |

**驗收標準**:
- [ ] 所有整合測試通過
- [ ] 安全掃描報告無 CRITICAL 項目
- [ ] Auth 覆蓋率驗證 = 100%
- [ ] Rate Limiting 驗證通過
- [ ] MCP Permission 驗證通過
- [ ] 錯誤回應驗證無洩漏

## 技術設計

### 目錄結構變更

```
backend/src/integrations/mcp/
├── security/                           # 新增: MCP 安全子模組
│   ├── __init__.py
│   └── command_whitelist.py            # 新增: 命令白名單
├── servers/
│   ├── azure.py                        # 修改: 添加 check_permission
│   ├── filesystem.py                   # 修改: 添加 check_permission
│   ├── ldap.py                         # 修改: 添加 check_permission
│   ├── shell.py                        # 修改: 添加 check_permission + 白名單
│   └── ssh.py                          # 修改: 添加 check_permission + 白名單
└── permissions.py                      # 修改: 啟用運行時檢查

backend/src/integrations/hybrid/
└── context_synchronizer.py             # 修改: 添加 asyncio.Lock (2 處)

backend/tests/integration/security/
└── test_phase31_integration.py         # 新增: Phase 31 整合測試
```

### 依賴

```
# 無新增依賴
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| MCP Permission 阻斷正常工具調用 | 先用 log-only 模式，驗證後再 enforce |
| 白名單過嚴影響 Agent 功能 | 預設白名單包含常用安全命令，可通過配置擴展 |
| ContextSynchronizer Lock 影響性能 | asyncio.Lock 是輕量級鎖，單 Worker 下影響極小 |
| 整合測試發現前兩個 Sprint 的問題 | 預留 0.5 天處理整合問題 |

## 完成標準

- [ ] MCP Permission 28 patterns 全部有運行時檢查
- [ ] Shell/SSH 有命令白名單
- [ ] 非白名單命令觸發 HITL 審批
- [ ] ContextSynchronizer 有 asyncio.Lock
- [ ] 全局異常處理器不洩漏 error_type
- [ ] Phase 31 整合測試全部通過
- [ ] 安全掃描無 CRITICAL 項目
- [ ] 安全評分從 1/10 提升到 6/10

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: TBD
