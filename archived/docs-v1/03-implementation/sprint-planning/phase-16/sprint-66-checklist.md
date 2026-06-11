# Sprint 66 Checklist: Tool Integration Bug Fix

## Overview

| Attribute | Value |
|-----------|-------|
| **Sprint** | 66 |
| **Phase** | 16 - Unified Agentic Chat Interface |
| **Type** | Bug Fix Sprint |
| **Story Points** | 10 pts |
| **Status** | In Progress |

---

## S66-1: Fix Claude Executor Tool Passing (3 pts)

**File**: `backend/src/api/v1/ag_ui/dependencies.py`

### Tasks

- [ ] **T1**: Modify `_create_claude_executor()` to accept and use tools parameter
  - [ ] Extract tool names from Dict format: `[t.get("name") for t in tools]`
  - [ ] Pass to `client.query(tools=tool_names)`

### Code Changes

```python
# Line 90-111 修改
async def claude_executor(
    prompt: str,
    history: Optional[List[Dict[str, Any]]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,  # 已有
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    try:
        # 轉換工具格式
        tool_names = []
        if tools:
            tool_names = [t.get("name") for t in tools if t.get("name")]

        result = await client.query(
            prompt=prompt,
            tools=tool_names,  # ← 添加這行
            max_tokens=max_tokens or 4096,
        )
        ...
```

### Verification

- [ ] Backend starts without errors
- [ ] `/api/v1/ag-ui/status` shows `claude_executor_enabled: true`

---

## S66-2: Add AG-UI Tool Events (3 pts)

**File**: `backend/src/integrations/ag_ui/bridge.py`

### Tasks

- [ ] **T1**: Add tool event types import
- [ ] **T2**: Modify `_generate_events_from_result()` to handle tool_calls
- [ ] **T3**: Generate TOOL_CALL_START, TOOL_CALL_ARGS, TOOL_CALL_END events

### Code Changes

```python
# 在 _generate_events_from_result() 中添加
def _generate_events_from_result(
    self,
    result: HybridResultV2,
    run_id: str,
    thread_id: str,
) -> Generator[AGUIEvent, None, None]:
    ...

    # 處理工具調用
    if hasattr(result, 'tool_calls') and result.tool_calls:
        for tc in result.tool_calls:
            # TOOL_CALL_START
            yield AGUIEvent(
                type=AGUIEventType.TOOL_CALL_START,
                run_id=run_id,
                thread_id=thread_id,
                data={
                    "tool_call_id": tc.id,
                    "tool_name": tc.name,
                },
            )

            # TOOL_CALL_ARGS
            yield AGUIEvent(
                type=AGUIEventType.TOOL_CALL_ARGS,
                run_id=run_id,
                thread_id=thread_id,
                data={
                    "tool_call_id": tc.id,
                    "args": tc.args,
                },
            )

            # TOOL_CALL_END
            yield AGUIEvent(
                type=AGUIEventType.TOOL_CALL_END,
                run_id=run_id,
                thread_id=thread_id,
                data={
                    "tool_call_id": tc.id,
                    "result": getattr(tc, 'result', None),
                },
            )
```

### Verification

- [ ] Tool events appear in SSE stream
- [ ] Frontend receives tool call data

---

## S66-3: Configure Default Tools (2 pts)

**File**: `frontend/src/pages/UnifiedChat.tsx`

### Tasks

- [ ] **T1**: Define default tool configurations
- [ ] **T2**: Pass tools to useUnifiedChat hook

### Code Changes

```typescript
// 添加預設工具定義
const DEFAULT_TOOLS = [
  // Low-risk tools
  {
    name: "Read",
    description: "Read file contents from the filesystem",
    parameters: {
      type: "object",
      properties: {
        file_path: { type: "string", description: "Path to file" },
      },
      required: ["file_path"],
    },
  },
  {
    name: "WebSearch",
    description: "Search the web for information",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" },
      },
      required: ["query"],
    },
  },
  {
    name: "Glob",
    description: "Find files matching a pattern",
    parameters: {
      type: "object",
      properties: {
        pattern: { type: "string", description: "Glob pattern" },
      },
      required: ["pattern"],
    },
  },
  // High-risk tools
  {
    name: "Write",
    description: "Write content to a file",
    parameters: {
      type: "object",
      properties: {
        file_path: { type: "string", description: "Path to file" },
        content: { type: "string", description: "Content to write" },
      },
      required: ["file_path", "content"],
    },
  },
  {
    name: "Bash",
    description: "Execute a shell command",
    parameters: {
      type: "object",
      properties: {
        command: { type: "string", description: "Command to execute" },
      },
      required: ["command"],
    },
  },
];

// 使用預設工具
const {
  messages,
  ...
} = useUnifiedChat({
  threadId,
  sessionId,
  apiUrl,
  tools: tools.length > 0 ? tools : DEFAULT_TOOLS,  // ← 使用預設工具
  ...
});
```

### Verification

- [ ] Tools are sent in API request
- [ ] Backend receives tool definitions

---

## S66-4: Add HITL Risk Assessment (2 pts)

**File**: `backend/src/integrations/ag_ui/bridge.py`

### Tasks

- [ ] **T1**: Define HIGH_RISK_TOOLS constant
- [ ] **T2**: Add requires_approval to TOOL_CALL_START event

### Code Changes

```python
# 定義高風險工具
HIGH_RISK_TOOLS = ["Write", "Edit", "MultiEdit", "Bash", "Task"]

# 在 TOOL_CALL_START 事件中添加風險標記
yield AGUIEvent(
    type=AGUIEventType.TOOL_CALL_START,
    run_id=run_id,
    thread_id=thread_id,
    data={
        "tool_call_id": tc.id,
        "tool_name": tc.name,
        "requires_approval": tc.name in HIGH_RISK_TOOLS,  # ← 添加
        "risk_level": "high" if tc.name in HIGH_RISK_TOOLS else "low",
    },
)
```

### Verification

- [ ] High-risk tools have `requires_approval: true`
- [ ] Low-risk tools have `requires_approval: false`

---

## Documentation Updates

### Files to Update

- [ ] **Phase 16 README.md**: Add Sprint 66 to overview table
- [ ] **CLAUDE.md**: Update Phase 16 status if needed

---

## Testing

### Unit Tests

- [ ] Test tool name extraction from Dict
- [ ] Test tool event generation
- [ ] Test risk level detection

### Integration Tests

- [ ] Send message → Tool executes → Result returned
- [ ] High-risk tool → Approval required
- [ ] SSE stream contains tool events

### Manual Testing

| Test Case | Expected | Status |
|-----------|----------|--------|
| "請搜尋 AI 新聞" | WebSearch executes | [ ] |
| "請讀取 README.md" | Read executes | [ ] |
| "請寫入 test.txt" | HITL approval shown | [ ] |
| Tool UI display | Events visible | [ ] |

---

## Completion Checklist

- [ ] All code changes implemented
- [ ] All tests passing
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] Phase 16 README updated
- [ ] Sprint 66 marked complete

---

## Notes

- Keep changes minimal and focused
- Preserve existing functionality
- Test incrementally after each change
