# REFACTOR-001: Extend LLMServiceProtocol with chat_with_tools()

## Problem

AgentHandler (Sprint 144) bypasses `LLMServiceProtocol` by directly creating an `AsyncAzureOpenAI` client for function calling. This violates the protocol abstraction — all LLM calls should go through `LLMServiceProtocol`.

**Root Cause**: `LLMServiceProtocol` only defines `generate()` and `generate_structured()`. Neither supports Azure OpenAI's `tools` parameter for function calling.

**Current Workaround** (in `agent_handler.py`):
```python
# Bypasses protocol — creates client directly
def _get_openai_client(self):
    if self._llm_service and hasattr(self._llm_service, "_client"):
        self._openai_client = self._llm_service._client  # accessing private attr
    else:
        self._openai_client = AsyncAzureOpenAI(...)  # duplicate client creation
```

## Solution

Extend `LLMServiceProtocol` with a `chat_with_tools()` method.

### Files to Modify

| File | Change |
|------|--------|
| `backend/src/integrations/llm/protocol.py` | Add `chat_with_tools()` to protocol |
| `backend/src/integrations/llm/azure_openai.py` | Implement `chat_with_tools()` in AzureOpenAILLMService |
| `backend/src/integrations/hybrid/orchestrator/agent_handler.py` | Use `llm_service.chat_with_tools()` instead of direct client |

### New Method Signature

```python
# In LLMServiceProtocol
async def chat_with_tools(
    self,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    max_tokens: int = 2048,
    temperature: float = 0.7,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Chat completion with function calling support.

    Returns:
        {
            "content": str | None,
            "tool_calls": [{"id": str, "function": {"name": str, "arguments": str}}] | None,
            "finish_reason": str,
        }
    """
```

### Implementation in AzureOpenAILLMService

```python
async def chat_with_tools(self, messages, tools=None, ...):
    response = await self._call_with_retry(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        tools=tools,
        tool_choice=tool_choice,
    )
    choice = response.choices[0]
    return {
        "content": choice.message.content,
        "tool_calls": [
            {"id": tc.id, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in (choice.message.tool_calls or [])
        ],
        "finish_reason": choice.finish_reason,
    }
```

### AgentHandler Changes

Remove `_get_openai_client()` and direct client creation. Replace with:
```python
result = await self._llm_service.chat_with_tools(
    messages=messages,
    tools=tool_schemas,
)
```

## Acceptance Criteria

- [ ] `LLMServiceProtocol` has `chat_with_tools()` method
- [ ] `AzureOpenAILLMService` implements `chat_with_tools()`
- [ ] `AgentHandler` uses `llm_service.chat_with_tools()` (no direct OpenAI client)
- [ ] `_call_with_retry()` accepts optional `tools` and `tool_choice` params
- [ ] Function calling loop still works (max 5 iterations)
- [ ] Existing `generate()` and `generate_structured()` unchanged
- [ ] Syntax check + import verification pass

## Risk Assessment

- **Low Risk**: Additive change to protocol (existing methods unchanged)
- **No Breaking Changes**: `chat_with_tools()` has a default implementation path
- **Estimated Effort**: 1-2 SP

## Related

- Sprint 144: AgentHandler Function Calling (created the workaround)
- Feedback: [feedback_check_existing_before_building.md](../../../.claude/projects/.../memory/feedback_check_existing_before_building.md)

---

## Modification History

- 2026-05-26: Sprint 57.52 — renumbered 001→002 (closes AD-REFACTOR-Numbering-Collision; Sprint 57.51 Day 0.8 BONUS observation: 2 files shared REFACTOR-001 prefix; this older Phase 35-38/Sprint 144 era file gets renumbered to REFACTOR-002; newer Sprint 57.22 audit file `REFACTOR-001-claude-md-memory-md-bloat-audit.md` retains REFACTOR-001 as canonical reference per `sprint-workflow.md §Sprint Closeout` policy)
