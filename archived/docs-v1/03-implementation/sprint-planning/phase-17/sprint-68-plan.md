# Sprint 68: Sandbox Isolation + Chat History

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint Number** | 68 |
| **Phase** | 17 - Agentic Chat Enhancement |
| **Duration** | 3-4 days |
| **Total Points** | 21 |
| **Focus** | Sandbox security architecture and chat history persistence |

## Sprint Goals

1. Implement sandbox directory isolation for agent operations
2. Create file upload API with security validation
3. Complete chat history API implementation
4. Integrate frontend with history loading

## Prerequisites

- Phase 16 completed (Unified Agentic Chat Interface)
- ThreadManager and SessionModel operational
- AG-UI SSE events working

---

## Stories

### S68-1: Sandbox Directory Structure (3 pts)

**Description**: Create the sandbox directory structure and configuration for user-scoped file isolation.

**Acceptance Criteria**:
- [ ] Create `data/uploads/`, `data/sandbox/`, `data/outputs/`, `data/temp/` directories
- [ ] Implement user-scoped subdirectory creation
- [ ] Add directory cleanup for inactive users
- [ ] Configure in environment variables

**Technical Details**:
```python
# backend/src/core/sandbox_config.py
from pathlib import Path
from typing import List

class SandboxConfig:
    """Configuration for sandbox directory isolation."""

    BASE_DATA_DIR: Path = Path("data")

    # User-scoped directories
    UPLOADS_DIR: str = "uploads"
    SANDBOX_DIR: str = "sandbox"
    OUTPUTS_DIR: str = "outputs"
    TEMP_DIR: str = "temp"

    @classmethod
    def get_user_dir(cls, user_id: str, dir_type: str) -> Path:
        """Get user-scoped directory path."""
        return cls.BASE_DATA_DIR / dir_type / user_id

    @classmethod
    def ensure_user_dirs(cls, user_id: str) -> dict[str, Path]:
        """Create all user directories if they don't exist."""
        dirs = {}
        for dir_type in [cls.UPLOADS_DIR, cls.SANDBOX_DIR, cls.OUTPUTS_DIR]:
            path = cls.get_user_dir(user_id, dir_type)
            path.mkdir(parents=True, exist_ok=True)
            dirs[dir_type] = path
        return dirs
```

**Files to Create**:
- `backend/src/core/sandbox_config.py`
- `data/.gitkeep` files for directory structure

---

### S68-2: SandboxHook Path Validation (5 pts)

**Description**: Implement path validation hook to restrict agent file operations to sandbox directories only.

**Acceptance Criteria**:
- [ ] Create `SandboxHook` with allowlist-based path validation
- [ ] Block access to source code directories (`backend/`, `frontend/`, `src/`)
- [ ] Block access to sensitive file patterns (`*.py`, `*.tsx`, `*.env`)
- [ ] Integrate with Claude SDK hook pipeline
- [ ] Log blocked access attempts
- [ ] Return clear error messages for blocked operations

**Technical Details**:
```python
# backend/src/integrations/claude_sdk/hooks/sandbox.py
import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class SandboxValidationResult:
    allowed: bool
    reason: Optional[str] = None
    resolved_path: Optional[Path] = None

class SandboxHook:
    """Hook to validate and restrict file system access."""

    # Allowed path patterns (user_id will be interpolated)
    ALLOWED_PATTERNS: List[str] = [
        r"^data/uploads/[a-zA-Z0-9\-]+/",
        r"^data/sandbox/[a-zA-Z0-9\-]+/",
        r"^data/outputs/[a-zA-Z0-9\-]+/",
    ]

    # Blocked path patterns (absolute block)
    BLOCKED_PATTERNS: List[str] = [
        r"^backend/",
        r"^frontend/",
        r"^src/",
        r"^scripts/",
        r"^docs/",
        r"^\.claude/",
        r"^\.git/",
        r"\.env$",
        r"\.env\.",
        r"credentials",
        r"secrets?\.json$",
    ]

    # Blocked file extensions for write operations
    BLOCKED_WRITE_EXTENSIONS: List[str] = [
        ".py", ".tsx", ".ts", ".js", ".jsx",
        ".sh", ".bat", ".ps1", ".cmd",
        ".sql", ".yaml", ".yml", ".toml",
    ]

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._compiled_allowed = [re.compile(p) for p in self.ALLOWED_PATTERNS]
        self._compiled_blocked = [re.compile(p) for p in self.BLOCKED_PATTERNS]

    def validate_path(
        self,
        path: str,
        operation: str = "read"
    ) -> SandboxValidationResult:
        """Validate if path access is allowed."""
        normalized = self._normalize_path(path)

        # Check blocked patterns first (absolute block)
        for pattern in self._compiled_blocked:
            if pattern.search(normalized):
                return SandboxValidationResult(
                    allowed=False,
                    reason=f"Access to '{normalized}' is blocked for security reasons"
                )

        # Check extension for write operations
        if operation in ("write", "edit", "delete"):
            ext = Path(normalized).suffix.lower()
            if ext in self.BLOCKED_WRITE_EXTENSIONS:
                return SandboxValidationResult(
                    allowed=False,
                    reason=f"Writing to '{ext}' files is not allowed"
                )

        # Check allowed patterns
        for pattern in self._compiled_allowed:
            if pattern.match(normalized):
                return SandboxValidationResult(
                    allowed=True,
                    resolved_path=Path(normalized)
                )

        # Default: block if not explicitly allowed
        return SandboxValidationResult(
            allowed=False,
            reason=f"Path '{normalized}' is outside allowed sandbox directories"
        )

    def _normalize_path(self, path: str) -> str:
        """Normalize path to prevent traversal attacks."""
        # Remove leading slashes and normalize
        path = path.lstrip("/\\")
        # Resolve .. and . components
        try:
            resolved = Path(path).resolve()
            # Get relative to current working directory
            cwd = Path.cwd()
            return str(resolved.relative_to(cwd))
        except (ValueError, RuntimeError):
            return path
```

**Files to Create**:
- `backend/src/integrations/claude_sdk/hooks/sandbox.py`

**Files to Modify**:
- `backend/src/integrations/claude_sdk/hooks/__init__.py` - Export SandboxHook
- `backend/src/integrations/claude_sdk/client.py` - Integrate SandboxHook

---

### S68-3: File Upload API (5 pts)

**Description**: Implement file upload API endpoint with security validation and session-scoped storage.

**Acceptance Criteria**:
- [ ] Create `POST /api/v1/ag-ui/upload` endpoint
- [ ] Validate file types (allowlist: txt, pdf, csv, json, md, etc.)
- [ ] Limit file size (default: 10MB)
- [ ] Store in session-scoped upload directory
- [ ] Return upload path for agent reference
- [ ] Add delete endpoint for uploaded files

**Technical Details**:
```python
# backend/src/api/v1/ag_ui/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import aiofiles
from pathlib import Path

router = APIRouter(prefix="/upload", tags=["File Upload"])

ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml",
    ".pdf", ".docx", ".xlsx",
    ".png", ".jpg", ".jpeg", ".gif",
    ".log", ".html", ".css",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
) -> dict:
    """Upload file to session sandbox directory."""
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds {MAX_FILE_SIZE // 1024 // 1024}MB limit"
        )

    # Save to session directory
    upload_dir = SandboxConfig.get_session_dir(user_id, "uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return {
        "success": True,
        "filename": file.filename,
        "path": f"data/uploads/{user_id}/{file.filename}",
        "size": len(content),
    }

@router.get("/list")
async def list_uploads(
    user_id: str = Depends(get_user_id),
) -> dict:
    """List files in session upload directory."""
    upload_dir = SandboxConfig.get_session_dir(user_id, "uploads")
    if not upload_dir.exists():
        return {"files": []}

    files = []
    for f in upload_dir.iterdir():
        if f.is_file():
            files.append({
                "filename": f.name,
                "path": f"data/uploads/{user_id}/{f.name}",
                "size": f.stat().st_size,
            })
    return {"files": files}

@router.delete("/{filename}")
async def delete_upload(
    filename: str,
    user_id: str = Depends(get_user_id),
) -> dict:
    """Delete uploaded file."""
    upload_dir = SandboxConfig.get_session_dir(user_id, "uploads")
    file_path = upload_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    file_path.unlink()
    return {"success": True, "deleted": filename}
```

**Files to Create**:
- `backend/src/api/v1/ag_ui/upload.py`

**Files to Modify**:
- `backend/src/api/v1/ag_ui/__init__.py` - Include upload router

---

### S68-4: History API Implementation (5 pts)

**Description**: Complete the chat history API that was a TODO placeholder, implementing full message retrieval with pagination.

**Acceptance Criteria**:
- [ ] Implement `GET /api/v1/ag-ui/threads/{thread_id}/history`
- [ ] Return messages with pagination (offset, limit)
- [ ] Include tool calls and their results
- [ ] Include approval states
- [ ] Sort by timestamp (oldest first for display)
- [ ] Cache results in Redis (5-minute TTL)

**Technical Details**:
```python
# backend/src/api/v1/ag_ui/routes.py - Update existing TODO

@router.get("/threads/{thread_id}/history")
async def get_thread_history(
    thread_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """Get chat history for a thread."""
    # Try cache first
    cache_key = f"thread_history:{thread_id}:{offset}:{limit}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query from database
    thread = await get_thread_manager().get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Get messages with pagination
    messages = await db.query(MessageModel)\
        .filter(MessageModel.thread_id == thread_id)\
        .order_by(MessageModel.created_at.asc())\
        .offset(offset)\
        .limit(limit)\
        .all()

    # Get total count
    total = await db.query(func.count(MessageModel.id))\
        .filter(MessageModel.thread_id == thread_id)\
        .scalar()

    result = {
        "thread_id": thread_id,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls or [],
                "approval_state": msg.approval_state,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ],
        "pagination": {
            "offset": offset,
            "limit": limit,
            "total": total,
            "has_more": offset + limit < total,
        }
    }

    # Cache for 5 minutes
    await redis.setex(cache_key, 300, json.dumps(result))

    return result
```

**Files to Modify**:
- `backend/src/api/v1/ag_ui/routes.py` - Implement history endpoint

---

### S68-5: Frontend History Integration (3 pts)

**Description**: Add history loading to the frontend, calling the history API on page load and syncing with localStorage cache.

**Acceptance Criteria**:
- [ ] Add `loadHistory()` method to `useUnifiedChat`
- [ ] Call on component mount with thread_id
- [ ] Merge with localStorage cache (prefer backend as source of truth)
- [ ] Handle loading state during fetch
- [ ] Show empty state for new conversations
- [ ] Handle pagination for long histories

**Technical Details**:
```typescript
// frontend/src/hooks/useUnifiedChat.ts - Add to existing hook

interface HistoryResponse {
  thread_id: string;
  messages: Array<{
    id: string;
    role: 'user' | 'assistant' | 'tool';
    content: string;
    tool_calls?: ToolCall[];
    approval_state?: ApprovalState;
    created_at: string;
  }>;
  pagination: {
    offset: number;
    limit: number;
    total: number;
    has_more: boolean;
  };
}

const loadHistory = async (threadId: string) => {
  if (!threadId) return;

  setHistoryLoading(true);
  try {
    const response = await fetch(`/api/v1/ag-ui/threads/${threadId}/history`);
    if (!response.ok) {
      throw new Error('Failed to load history');
    }

    const data: HistoryResponse = await response.json();

    // Convert to ChatMessage format
    const historyMessages: ChatMessage[] = data.messages.map((msg) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      toolCalls: msg.tool_calls,
      approvalState: msg.approval_state,
      timestamp: new Date(msg.created_at),
    }));

    // Replace local messages with backend history
    setMessages(historyMessages);
  } catch (error) {
    console.error('Failed to load history:', error);
    // Fall back to localStorage if available
  } finally {
    setHistoryLoading(false);
  }
};

// Call on mount
useEffect(() => {
  if (threadId) {
    loadHistory(threadId);
  }
}, [threadId]);
```

**Files to Modify**:
- `frontend/src/hooks/useUnifiedChat.ts` - Add loadHistory
- `frontend/src/pages/UnifiedChat.tsx` - Pass threadId

---

## Technical Notes

### Sandbox Integration with Claude SDK

```python
# Integration in ClaudeSDKClient
class ClaudeSDKClient:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.sandbox_hook = SandboxHook(user_id)

    async def execute_tool(self, tool_name: str, args: dict) -> ToolResult:
        # Validate file paths in args
        if tool_name in ("Read", "Write", "Edit", "Glob", "Grep"):
            path = args.get("file_path") or args.get("path")
            if path:
                result = self.sandbox_hook.validate_path(
                    path,
                    operation="write" if tool_name in ("Write", "Edit") else "read"
                )
                if not result.allowed:
                    return ToolResult(
                        success=False,
                        error=result.reason
                    )
```

### History Sync Strategy

```
Backend (PostgreSQL) = Source of Truth
         ↓
    Redis Cache (5-min TTL)
         ↓
    Frontend (localStorage)

On Page Load:
1. Check localStorage for cached thread_id
2. Call GET /threads/{id}/history
3. Replace localStorage with backend data
4. Subscribe to SSE for new messages
```

---

## Dependencies

### From Previous Phases
- ThreadManager from Phase 15
- SessionModel and MessageModel
- Redis cache infrastructure

### New Dependencies
- `python-multipart` for file uploads
- `aiofiles` for async file operations

---

## Definition of Done

- [ ] All 5 stories completed and tested
- [ ] Sandbox blocks access to `backend/`, `frontend/` directories
- [ ] File upload works with size/type validation
- [ ] History API returns paginated messages
- [ ] Frontend loads history on page mount
- [ ] Unit tests for SandboxHook validation
- [ ] Integration test for upload flow

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Path traversal attack | High | Strict normalization, allowlist-only |
| Large file uploads | Medium | Size limits, streaming for large files |
| History sync conflicts | Low | Backend as source of truth |

---

## Sprint Velocity Reference

Sandbox and persistence work requiring careful security implementation.
Expected completion: 3-4 days for 21 pts
