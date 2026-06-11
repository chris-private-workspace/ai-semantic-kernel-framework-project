# Sprint 160: Domain-Specific Tool Schemas

## Phase 46: Agent Expert Registry
**Sprint**: 160
**Story Points**: 8
**Dependencies**: Sprint 159 (Integration) ✅

---

## User Stories

### U1: Domain Tool Mapping
**作為**平台，**我希望**每個專家 domain 有預設的推薦工具集，**以便**新增專家時不需手動列出所有工具。

**Acceptance Criteria**:
- 每個 domain (network, database, application, security, cloud, general) 有預設工具集
- YAML 中 tools 可用 `["*"]` 表示所有工具、`["@domain"]` 表示 domain 預設工具
- Domain 工具集包含 domain 專屬工具 + 共用團隊工具

### U2: Tool Validation
**作為**開發者，**我希望** Registry 載入時驗證 YAML 的 tools 欄位，**以便**提早發現無效工具配置。

**Acceptance Criteria**:
- `tool_validator.py` 驗證 tools 列表中的工具名稱
- 支援通配符 `*` 和 domain 參照 `@domain`
- 提供 `validate_expert_tools()` 函式
- 無效工具名稱記錄 warning（不阻擋載入）

---

## Technical Specification

### Files to Create

| File | Purpose |
|------|---------|
| `experts/domain_tools.py` | Domain-to-tool mappings and resolution |
| `experts/tool_validator.py` | Tool name validation |
| `tests/.../experts/test_domain_tools.py` | Domain tools tests |

### Files to Modify

| File | Change |
|------|--------|
| `experts/registry.py` | Call tool_validator during load |
| `experts/__init__.py` | Export new modules |

### Domain Tool Definitions

```python
DOMAIN_TOOLS = {
    "network": {
        "core": ["assess_risk", "search_knowledge", "search_memory"],
        "specialized": [],  # future: ping, traceroute, nslookup
    },
    "database": {
        "core": ["assess_risk", "search_knowledge", "search_memory", "create_task"],
        "specialized": [],  # future: query_db, explain_plan
    },
    "application": {
        "core": ["assess_risk", "search_knowledge", "create_task", "search_memory"],
        "specialized": [],  # future: check_logs, restart_service
    },
    "security": {
        "core": ["assess_risk", "search_knowledge"],
        "specialized": [],  # future: scan_vulnerability, check_compliance
    },
    "cloud": {
        "core": ["assess_risk", "search_knowledge", "search_memory", "create_task"],
        "specialized": [],  # future: check_cost, list_resources
    },
    "general": {
        "core": ["assess_risk", "search_memory", "search_knowledge"],
        "specialized": [],
    },
}

TEAM_TOOLS = [
    "send_team_message", "check_my_inbox", "read_team_messages",
    "view_team_status", "claim_next_task", "report_task_result",
]
```

### Tool Resolution Logic

```python
def resolve_tools(tools: list[str], domain: str) -> list[str]:
    """Resolve tool list with special tokens.
    
    - ["*"] → all known tools
    - ["@domain"] → domain core + specialized + team tools
    - ["tool1", "tool2"] → explicit list (unchanged)
    """
```

---

## Test Plan

| Test | Description |
|------|-------------|
| `test_resolve_tools_explicit` | Explicit tool list returned unchanged |
| `test_resolve_tools_wildcard` | `["*"]` resolves to all known tools |
| `test_resolve_tools_domain_ref` | `["@domain"]` resolves to domain tools + team tools |
| `test_resolve_tools_mixed` | Mix of explicit + @domain works |
| `test_validate_tools_valid` | Valid tool names pass validation |
| `test_validate_tools_warns_unknown` | Unknown tools log warning |
| `test_domain_tools_all_domains_defined` | All valid domains have entries |
