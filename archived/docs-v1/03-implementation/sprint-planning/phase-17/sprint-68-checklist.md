# Sprint 68 Checklist: Sandbox Isolation + Chat History

## Sprint Information

| Field | Value |
|-------|-------|
| **Sprint** | 68 |
| **Phase** | 17 - Agentic Chat Enhancement |
| **Focus** | Sandbox Security + Chat History |
| **Points** | 21 pts |
| **Status** | ✅ Completed |

---

## Pre-Sprint Checklist

- [x] Phase 16 completed and stable
- [x] ThreadManager operational
- [x] Redis cache working
- [x] PostgreSQL MessageModel available

---

## Story Completion Tracking

### S68-1: Sandbox Directory Structure (3 pts)

| Task | Status | Notes |
|------|--------|-------|
| Create `data/uploads/` directory | ✅ | Per-user structure |
| Create `data/sandbox/` directory | ✅ | Per-user structure |
| Create `data/outputs/` directory | ✅ | Per-user structure |
| Create `data/temp/` directory | ✅ | Shared temp |
| Create `SandboxConfig` class | ✅ | |
| Implement `get_user_dir()` | ✅ | |
| Implement `ensure_user_dirs()` | ✅ | |
| Add `.gitkeep` files | ✅ | |
| Add to `.gitignore` (data/*) | ✅ | |

**Files Created**:
- [x] `backend/src/core/sandbox_config.py`
- [x] `data/.gitkeep`

---

### S68-2: SandboxHook Path Validation (5 pts)

| Task | Status | Notes |
|------|--------|-------|
| Create `SandboxHook` class | ✅ | |
| Define `ALLOWED_PATTERNS` | ✅ | |
| Define `BLOCKED_PATTERNS` | ✅ | |
| Define `BLOCKED_WRITE_EXTENSIONS` | ✅ | |
| Implement `validate_path()` | ✅ | |
| Implement `_normalize_path()` | ✅ | |
| Handle path traversal (`../`) | ✅ | |
| Export from hooks `__init__.py` | ✅ | |
| Integrate with `ClaudeSDKClient` | ✅ | |
| Add logging for blocked attempts | ✅ | |

**Files Created**:
- [x] `backend/src/integrations/claude_sdk/hooks/sandbox.py`

**Files Modified**:
- [x] `backend/src/integrations/claude_sdk/hooks/__init__.py`
- [x] `backend/src/integrations/claude_sdk/client.py`

**Test Cases**:
- [x] Block `backend/src/main.py` - should fail
- [x] Block `frontend/package.json` - should fail
- [x] Allow `data/uploads/{session}/file.txt` - should pass
- [x] Block `data/uploads/../backend/x.py` - should fail (traversal)
- [x] Block write to `.py` files - should fail
- [x] Allow read from sandbox dir - should pass

---

### S68-3: File Upload API (5 pts)

| Task | Status | Notes |
|------|--------|-------|
| Create `upload.py` router | ✅ | |
| Define `ALLOWED_EXTENSIONS` | ✅ | |
| Define `MAX_FILE_SIZE` (10MB) | ✅ | |
| Implement `POST /upload` | ✅ | |
| Validate file extension | ✅ | |
| Validate file size | ✅ | |
| Save to user directory | ✅ | |
| Implement `GET /upload/list` | ✅ | |
| Implement `DELETE /upload/{filename}` | ✅ | |
| Include router in main app | ✅ | |

**Files Created**:
- [x] `backend/src/api/v1/ag_ui/upload.py`

**Files Modified**:
- [x] `backend/src/api/v1/ag_ui/__init__.py`

**Test Cases**:
- [x] Upload valid `.txt` file - should succeed
- [x] Upload `.py` file - should fail
- [x] Upload file > 10MB - should fail
- [x] List uploaded files - should return list
- [x] Delete uploaded file - should succeed

---

### S68-4: History API Implementation (5 pts)

| Task | Status | Notes |
|------|--------|-------|
| Locate TODO at routes.py:506 | ✅ | |
| Implement query from MessageModel | ✅ | |
| Add pagination (offset, limit) | ✅ | |
| Include tool_calls in response | ✅ | |
| Include approval_state | ✅ | |
| Sort by created_at ASC | ✅ | |
| Add Redis cache (5-min TTL) | ✅ | |
| Return total count | ✅ | |
| Handle thread not found | ✅ | |

**Files Modified**:
- [x] `backend/src/api/v1/ag_ui/routes.py`

**Test Cases**:
- [x] Get history for existing thread - should return messages
- [x] Get history for non-existent thread - should return 404
- [x] Pagination works correctly
- [x] Cache hit on second request

---

### S68-5: Frontend History Integration (3 pts)

| Task | Status | Notes |
|------|--------|-------|
| Add `loadHistory()` to useUnifiedChat | ✅ | |
| Add `historyLoading` state | ✅ | |
| Call on component mount | ✅ | |
| Convert API response to ChatMessage | ✅ | |
| Handle loading state | ✅ | |
| Handle empty history | ✅ | |
| Fall back to localStorage on error | ✅ | |

**Files Modified**:
- [x] `frontend/src/hooks/useUnifiedChat.ts`
- [x] `frontend/src/pages/UnifiedChat.tsx`

**Test Cases**:
- [x] History loads on page mount
- [x] Shows loading spinner during fetch
- [x] Shows messages after load
- [x] New conversation shows empty state

---

## Integration Testing

| Scenario | Status | Notes |
|----------|--------|-------|
| Agent reads from sandbox dir | ✅ | Verified |
| Agent reads from backend/ | ✅ | Blocked as expected |
| Agent writes to outputs/ | ✅ | Verified |
| Agent writes .py file | ✅ | Blocked as expected |
| Upload file, agent reads it | ✅ | E2E flow verified |
| Send message, refresh, history loads | ✅ | Persistence verified |

---

## Post-Sprint Checklist

- [x] All stories complete (21 pts)
- [x] Security audit on sandbox paths
- [x] No path traversal vulnerabilities
- [x] History API documented
- [x] Upload API documented
- [x] README updated with Phase 17 progress

---

## Notes

### Security Considerations
- Path normalization MUST handle `../` attacks ✅
- Extension blocklist MUST be enforced for writes ✅
- User isolation MUST be verified ✅

### Performance Considerations
- History cache reduces DB load ✅
- File upload should stream for large files ✅
- Pagination prevents loading all messages at once ✅

---

**Checklist Status**: ✅ Completed
**Last Updated**: 2026-01-08

---

## Implementation Summary

### Files Created
- `backend/src/core/sandbox_config.py` - Sandbox directory configuration
- `backend/src/api/v1/ag_ui/upload.py` - File upload API endpoints
- `frontend/src/utils/guestUser.ts` - Guest User ID management

### Files Modified
- `backend/src/integrations/claude_sdk/hooks/sandbox.py` - Added UserSandboxHook
- `backend/src/integrations/claude_sdk/hooks/__init__.py` - Export UserSandboxHook
- `backend/src/api/v1/ag_ui/__init__.py` - Include upload router
- `backend/src/api/v1/ag_ui/dependencies.py` - Added get_user_id
- `backend/src/api/v1/ag_ui/routes.py` - Implemented history endpoint
- `frontend/src/hooks/useUnifiedChat.ts` - Added history loading
- `.gitignore` - Added data/* exclusions
