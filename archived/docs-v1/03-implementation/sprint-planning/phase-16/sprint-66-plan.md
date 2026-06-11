# Sprint 66: Tool Integration Bug Fix

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint** | 66 |
| **Phase** | 16 - Unified Agentic Chat Interface |
| **Type** | Bug Fix Sprint |
| **Story Points** | 10 pts |
| **Duration** | 1 day |
| **Goal** | Fix tool parameter passing to enable full Agentic functionality |

## Problem Statement

Phase 16 Unified Chat Interface was marked complete, but tool calling functionality is broken due to a critical parameter passing issue:

### Root Cause

**File**: `backend/src/api/v1/ag_ui/dependencies.py`
**Location**: Line 107-111

```python
# Current broken code
result = await client.query(
    prompt=prompt,
    max_tokens=max_tokens or 4096,
)
# Missing: tools=tools parameter!
```

The `tools` parameter is received by the `claude_executor` function but never passed to `client.query()`, causing Claude SDK's complete agentic loop to be bypassed.

### Architecture Status

| Layer | Status | Notes |
|-------|--------|-------|
| Frontend → API | OK | Tools passed in request |
| API → Bridge | OK | RunAgentInput contains tools |
| Bridge → Orchestrator | OK | execute() receives tools |
| Orchestrator → Claude Executor | WARN | Tools received but unused |
| **Claude Executor → Claude SDK** | BROKEN | `client.query()` missing tools |
| Claude SDK Tool Execution | OK | Complete agentic loop implemented |
| Built-in Tools | OK | 10 tools available (Read, Write, Bash, etc.) |

---

## User Stories

### S66-1: Fix Claude Executor Tool Passing (3 pts)

**As a** system
**I want** the Claude executor to pass tools to Claude SDK
**So that** Claude can use tools during conversation

**Acceptance Criteria:**
- [ ] `_create_claude_executor()` passes `tools` parameter to `client.query()`
- [ ] Tool names are correctly extracted from Dict format
- [ ] Claude SDK receives tool definitions and can invoke them

**Technical Details:**
- File: `backend/src/api/v1/ag_ui/dependencies.py`
- Convert `List[Dict[str, Any]]` to `List[str]` (tool names)
- Pass to `client.query(tools=tool_names)`

---

### S66-2: Add AG-UI Tool Events (3 pts)

**As a** frontend developer
**I want** tool call events to be emitted via AG-UI SSE
**So that** I can display tool status in the UI

**Acceptance Criteria:**
- [ ] `TOOL_CALL_START` event emitted when tool begins
- [ ] `TOOL_CALL_ARGS` event contains tool parameters
- [ ] `TOOL_CALL_END` event includes result or error

**Technical Details:**
- File: `backend/src/integrations/ag_ui/bridge.py`
- Add event generation in `_generate_events_from_result()`
- Handle tool_calls from HybridResultV2

---

### S66-3: Configure Default Tools (2 pts)

**As a** user
**I want** default tools available in the chat interface
**So that** I can perform file and web operations

**Acceptance Criteria:**
- [ ] Default tools configured in UnifiedChat.tsx
- [ ] Low-risk tools: Read, Glob, Grep, WebSearch, WebFetch
- [ ] High-risk tools: Write, Edit, MultiEdit, Bash, Task

**Technical Details:**
- File: `frontend/src/pages/UnifiedChat.tsx`
- Define tool schemas matching Claude SDK format
- Pass to `useUnifiedChat` hook

---

### S66-4: Add HITL Risk Assessment (2 pts)

**As a** security-conscious user
**I want** high-risk tool calls to require my approval
**So that** destructive operations don't execute automatically

**Acceptance Criteria:**
- [ ] High-risk tools identified: Write, Edit, MultiEdit, Bash, Task
- [ ] TOOL_CALL_START event includes `requires_approval: true`
- [ ] UI can differentiate and show approval dialog

**Technical Details:**
- File: `backend/src/integrations/ag_ui/bridge.py`
- Define HIGH_RISK_TOOLS constant
- Add risk level to tool events

---

## Technical Implementation

### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/src/api/v1/ag_ui/dependencies.py` | Modify | Fix tool parameter passing |
| `backend/src/integrations/ag_ui/bridge.py` | Add | Tool events + HITL |
| `frontend/src/pages/UnifiedChat.tsx` | Add | Default tool configuration |
| `docs/03-implementation/sprint-planning/phase-16/README.md` | Update | Add Sprint 66 |

### Implementation Order

```
1. dependencies.py (core fix)
   ↓
2. bridge.py (tool events)
   ↓
3. UnifiedChat.tsx (default tools)
   ↓
4. bridge.py (HITL)
   ↓
5. Testing
```

---

## Testing Plan

### Unit Tests

1. Test `_create_claude_executor()` passes tools correctly
2. Test tool event generation in bridge
3. Test HITL risk detection

### Integration Tests

1. Send message → Claude uses tool → Tool result returned
2. High-risk tool → Requires approval event
3. Tool events appear in SSE stream

### Manual Testing

1. Navigate to http://localhost:3005/chat
2. Send: "請搜尋最新的 AI 新聞" → WebSearch executes
3. Send: "請讀取 README.md" → Read executes
4. Send: "請在 test.txt 寫入 Hello" → HITL approval required

---

## Expected Outcomes

After this sprint:

| Test Case | Expected Behavior |
|-----------|-------------------|
| "Search for AI news" | WebSearch tool auto-executes, results returned |
| "Read README.md" | Read tool auto-executes, file content shown |
| "Write to test.txt" | HITL approval dialog shown, then executes |
| Tool UI | Shows TOOL_CALL_START/ARGS/END events |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Claude SDK tool format mismatch | Verify against existing tool definitions |
| HITL blocking indefinitely | Add timeout for approval requests |
| Event serialization errors | Validate event data before sending |

---

## Definition of Done

- [ ] All acceptance criteria met for S66-1 through S66-4
- [ ] Manual testing confirms tool execution works
- [ ] HITL approval flow functional
- [ ] Tool events visible in frontend
- [ ] Documentation updated
- [ ] No regression in existing functionality
