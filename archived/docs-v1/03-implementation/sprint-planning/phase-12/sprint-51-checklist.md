# Sprint 51 Checklist: API Routes Completion

## Quick Verification

```bash
# 1. File structure check
dir backend\src\api\v1\claude_sdk\ /B

# Expected files:
# __init__.py
# routes.py           (Sprint 48)
# schemas.py          (Sprint 48)
# tools_routes.py     (S51-1)
# hooks_routes.py     (S51-2)
# mcp_routes.py       (S51-3)
# hybrid_routes.py    (S51-4)

# 2. Run tests
cd backend
pytest tests/unit/api/v1/claude_sdk/ -v

# 3. Check API routes loaded
python -c "from src.api.v1.claude_sdk import router; print([r.path for r in router.routes])"

# 4. Test endpoints (requires server running)
curl http://localhost:8000/api/v1/claude-sdk/tools
curl http://localhost:8000/api/v1/claude-sdk/hooks
curl http://localhost:8000/api/v1/claude-sdk/mcp/servers
curl http://localhost:8000/api/v1/claude-sdk/hybrid/capabilities
```

---

## S51-1: Tools API Routes (8 points)

### File Structure
- [ ] `backend/src/api/v1/claude_sdk/tools_routes.py` created
- [ ] `backend/tests/unit/api/v1/claude_sdk/test_tools_routes.py` created

### Schemas Implementation
- [ ] `ToolParameter` schema defined
- [ ] `ToolInfo` schema defined
- [ ] `ToolExecuteRequest` schema defined
- [ ] `ToolExecuteResponse` schema defined
- [ ] `ToolValidateRequest` schema defined
- [ ] `ToolValidateResponse` schema defined

### Endpoints Implementation
- [ ] `GET /claude-sdk/tools` - List all tools
  - [ ] Returns list of `ToolInfo`
  - [ ] Supports `category` filter parameter
  - [ ] Supports `include_disabled` parameter
- [ ] `GET /claude-sdk/tools/{name}` - Get tool details
  - [ ] Returns `ToolInfo` for valid tool
  - [ ] Returns 404 for unknown tool
- [ ] `POST /claude-sdk/tools/execute` - Execute tool
  - [ ] Validates request parameters
  - [ ] Checks tool existence
  - [ ] Handles approval requirement
  - [ ] Returns execution result
  - [ ] Handles timeout
- [ ] `POST /claude-sdk/tools/validate` - Validate parameters
  - [ ] Validates tool existence
  - [ ] Validates parameter types
  - [ ] Returns validation errors

### Integration
- [ ] Imports from `src.integrations.claude_sdk.tools.registry`
- [ ] Uses `ToolRegistry.list_tools()`
- [ ] Uses `ToolRegistry.get_tool()`
- [ ] Uses `ToolRegistry.execute()`
- [ ] Uses `ToolRegistry.validate_parameters()`

### Tests
- [ ] `test_list_tools_returns_all_tools`
- [ ] `test_list_tools_filter_by_category`
- [ ] `test_get_tool_returns_tool_info`
- [ ] `test_get_tool_not_found`
- [ ] `test_execute_tool_success`
- [ ] `test_execute_tool_requires_approval`
- [ ] `test_validate_tool_parameters_valid`
- [ ] `test_validate_tool_parameters_invalid`

---

## S51-2: Hooks API Routes (5 points)

### File Structure
- [ ] `backend/src/api/v1/claude_sdk/hooks_routes.py` created
- [ ] `backend/tests/unit/api/v1/claude_sdk/test_hooks_routes.py` created

### Schemas Implementation
- [ ] `HookType` enum defined (approval, audit, rate_limit, sandbox, custom)
- [ ] `HookPriority` enum defined (LOW, NORMAL, HIGH, CRITICAL)
- [ ] `HookConfig` schema defined
- [ ] `HookInfo` schema defined
- [ ] `HookRegisterRequest` schema defined
- [ ] `HookRegisterResponse` schema defined

### Endpoints Implementation
- [ ] `GET /claude-sdk/hooks` - List all hooks
  - [ ] Returns list of `HookInfo`
  - [ ] Supports `type` filter parameter
  - [ ] Supports `enabled_only` parameter
- [ ] `GET /claude-sdk/hooks/{id}` - Get hook details
  - [ ] Returns `HookInfo` for valid hook
  - [ ] Returns 404 for unknown hook
- [ ] `POST /claude-sdk/hooks/register` - Register new hook
  - [ ] Creates hook with specified type
  - [ ] Assigns priority
  - [ ] Returns hook ID
  - [ ] Returns 201 status code
- [ ] `DELETE /claude-sdk/hooks/{id}` - Remove hook
  - [ ] Removes existing hook
  - [ ] Returns 204 on success
  - [ ] Returns 404 for unknown hook
- [ ] `PUT /claude-sdk/hooks/{id}/enable` - Enable hook
  - [ ] Sets `enabled=True`
  - [ ] Returns updated `HookInfo`
- [ ] `PUT /claude-sdk/hooks/{id}/disable` - Disable hook
  - [ ] Sets `enabled=False`
  - [ ] Returns updated `HookInfo`

### Integration
- [ ] Imports from `src.integrations.claude_sdk.hooks`
- [ ] Uses `HookManager.list_hooks()`
- [ ] Uses `HookManager.get_hook()`
- [ ] Uses `HookManager.register_hook()`
- [ ] Uses `HookManager.remove_hook()`
- [ ] Uses `HookManager.enable_hook()`
- [ ] Uses `HookManager.disable_hook()`

### Tests
- [ ] `test_list_hooks_returns_all`
- [ ] `test_list_hooks_filter_by_type`
- [ ] `test_get_hook_returns_info`
- [ ] `test_get_hook_not_found`
- [ ] `test_register_hook_success`
- [ ] `test_register_hook_invalid_type`
- [ ] `test_remove_hook_success`
- [ ] `test_enable_disable_hook`

---

## S51-3: MCP API Routes (7 points)

### File Structure
- [ ] `backend/src/api/v1/claude_sdk/mcp_routes.py` created
- [ ] `backend/tests/unit/api/v1/claude_sdk/test_mcp_routes.py` created

### Schemas Implementation
- [ ] `MCPTransport` enum defined (stdio, http, websocket)
- [ ] `MCPServerStatus` enum defined (connected, disconnected, connecting, error)
- [ ] `MCPServerInfo` schema defined
- [ ] `MCPToolInfo` schema defined
- [ ] `MCPConnectRequest` schema defined
- [ ] `MCPConnectResponse` schema defined
- [ ] `MCPExecuteRequest` schema defined
- [ ] `MCPExecuteResponse` schema defined
- [ ] `MCPHealthResponse` schema defined

### Endpoints Implementation
- [ ] `GET /claude-sdk/mcp/servers` - List MCP servers
  - [ ] Returns list of `MCPServerInfo`
  - [ ] Supports `status` filter
  - [ ] Supports `transport` filter
- [ ] `POST /claude-sdk/mcp/servers/connect` - Connect to server
  - [ ] Connects to specified endpoint
  - [ ] Discovers available tools
  - [ ] Returns `MCPConnectResponse`
  - [ ] Returns 503 on connection failure
- [ ] `POST /claude-sdk/mcp/servers/{id}/disconnect` - Disconnect server
  - [ ] Disconnects server
  - [ ] Returns 204 on success
  - [ ] Returns 404 for unknown server
- [ ] `GET /claude-sdk/mcp/servers/{id}/health` - Health check
  - [ ] Returns `MCPHealthResponse`
  - [ ] Includes latency measurement
  - [ ] Returns 404 for unknown server
- [ ] `GET /claude-sdk/mcp/tools` - List MCP tools
  - [ ] Returns list of `MCPToolInfo`
  - [ ] Supports `server_id` filter
- [ ] `POST /claude-sdk/mcp/tools/execute` - Execute MCP tool
  - [ ] Executes tool on specified server
  - [ ] Returns `MCPExecuteResponse`
  - [ ] Handles timeout

### Integration
- [ ] Imports from `src.integrations.claude_sdk.mcp.manager`
- [ ] Uses `MCPManager.list_servers()`
- [ ] Uses `MCPManager.connect()`
- [ ] Uses `MCPManager.disconnect()`
- [ ] Uses `MCPManager.health_check()`
- [ ] Uses `MCPManager.list_tools()`
- [ ] Uses `MCPManager.execute_tool()`

### Tests
- [ ] `test_list_mcp_servers`
- [ ] `test_list_mcp_servers_filter_status`
- [ ] `test_connect_mcp_server_success`
- [ ] `test_connect_mcp_server_failure`
- [ ] `test_disconnect_mcp_server`
- [ ] `test_health_check_success`
- [ ] `test_health_check_not_found`
- [ ] `test_list_mcp_tools`
- [ ] `test_execute_mcp_tool_success`
- [ ] `test_execute_mcp_tool_timeout`

---

## S51-4: Hybrid API Routes (5 points)

### File Structure
- [ ] `backend/src/api/v1/claude_sdk/hybrid_routes.py` created
- [ ] `backend/tests/unit/api/v1/claude_sdk/test_hybrid_routes.py` created

### Schemas Implementation
- [ ] `ExecutionPreference` enum defined
- [ ] `CapabilityType` enum defined
- [ ] `CapabilityInfo` schema defined
- [ ] `HybridExecuteRequest` schema defined
- [ ] `HybridExecuteResponse` schema defined
- [ ] `HybridAnalyzeRequest` schema defined
- [ ] `HybridAnalyzeResponse` schema defined
- [ ] `HybridMetrics` schema defined
- [ ] `ContextSyncRequest` schema defined
- [ ] `ContextSyncResponse` schema defined

### Endpoints Implementation
- [ ] `POST /claude-sdk/hybrid/execute` - Execute hybrid request
  - [ ] Auto-selects best executor
  - [ ] Returns `HybridExecuteResponse`
  - [ ] Includes execution timing
  - [ ] Includes decision reason
- [ ] `POST /claude-sdk/hybrid/analyze` - Analyze task
  - [ ] Returns `HybridAnalyzeResponse`
  - [ ] Includes capability matching
  - [ ] Includes alternatives
- [ ] `GET /claude-sdk/hybrid/metrics` - Get metrics
  - [ ] Returns `HybridMetrics`
  - [ ] Supports `period_days` parameter
- [ ] `POST /claude-sdk/hybrid/context/sync` - Sync context
  - [ ] Synchronizes context between executors
  - [ ] Returns `ContextSyncResponse`
  - [ ] Reports conflicts
- [ ] `GET /claude-sdk/hybrid/capabilities` - List capabilities
  - [ ] Returns list of `CapabilityInfo`

### Integration
- [ ] Imports from `src.integrations.claude_sdk.hybrid.orchestrator`
- [ ] Imports from `src.integrations.claude_sdk.hybrid.selector`
- [ ] Imports from `src.integrations.claude_sdk.hybrid.capability`
- [ ] Imports from `src.integrations.claude_sdk.hybrid.synchronizer`
- [ ] Uses `HybridOrchestrator.execute()`
- [ ] Uses `HybridOrchestrator.get_metrics()`
- [ ] Uses `CapabilitySelector.analyze()`
- [ ] Uses `ContextSynchronizer.sync()`
- [ ] Uses `CapabilityRegistry.list_all()`

### Tests
- [ ] `test_hybrid_execute_success`
- [ ] `test_hybrid_execute_preference_claude`
- [ ] `test_hybrid_execute_preference_agent`
- [ ] `test_hybrid_analyze_returns_recommendation`
- [ ] `test_get_hybrid_metrics`
- [ ] `test_context_sync_success`
- [ ] `test_context_sync_with_conflicts`
- [ ] `test_list_capabilities`

---

## Router Integration

### __init__.py Update
- [ ] Import `tools_router` from `tools_routes`
- [ ] Import `hooks_router` from `hooks_routes`
- [ ] Import `mcp_router` from `mcp_routes`
- [ ] Import `hybrid_router` from `hybrid_routes`
- [ ] Include all routers in main `router`

### Verification
- [ ] All endpoints appear in OpenAPI docs (`/docs`)
- [ ] All endpoints have proper tags
- [ ] All endpoints have proper request/response models

---

## Fix Records

| Issue | Description | Resolution | Date |
|-------|-------------|------------|------|
| | | | |
| | | | |

---

## Completion Statistics

| Story | Files | Tests | Status |
|-------|-------|-------|--------|
| S51-1: Tools API | 2 | 8 | [ ] |
| S51-2: Hooks API | 2 | 8 | [ ] |
| S51-3: MCP API | 2 | 10 | [ ] |
| S51-4: Hybrid API | 2 | 8 | [ ] |
| **Total** | **8** | **34** | [ ] |

---

## Final Verification

### API Endpoint Count
- [ ] Tools: 4 endpoints
- [ ] Hooks: 6 endpoints
- [ ] MCP: 6 endpoints
- [ ] Hybrid: 5 endpoints
- [ ] **Total: 21 new endpoints**

### Phase 12 UAT Test Compatibility
- [ ] Sprint 49 test scenarios work without simulation
- [ ] Sprint 50 test scenarios work without simulation
- [ ] All API calls return proper responses

### Documentation
- [ ] OpenAPI spec updated (auto-generated)
- [ ] sprint-51-plan.md complete
- [ ] sprint-51-checklist.md complete

---

**Created**: 2025-12-26
**Status**: Planning
**Last Updated**: 2025-12-26
