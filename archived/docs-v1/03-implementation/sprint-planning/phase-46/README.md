# Phase 46: Agent Team V4 — P2 Upgrades + Agent Expert Registry

## Overview

Phase 46 extends the Agent Team system (Phase 43-45) with production-readiness upgrades and a CC-style Agent Expert Registry.

**Phase 45 delivered**: 8-step pipeline, 3 dispatch routes, Agent Team visualization, ConversationLog, HITL, LLMCallPool.

**Phase 46 delivers**: Graceful shutdown, error recovery, and a configurable Agent Expert Registry where each expert has its own system prompt, tools, model, and domain.

## Sprint Overview

| Sprint | Title | Story Points | Status |
|--------|-------|-------------|--------|
| 156 | Graceful Shutdown Protocol | TBD | Planned |
| 157 | Error Recovery with Retry | TBD | Planned |
| 158 | Expert Definition Format + Registry Core | 13 | In Progress |
| 159 | TaskDecomposer + Executor Integration | 13 | Planned |
| 160 | Domain-Specific Tool Schemas | 8 | Planned |
| 161 | Frontend Expert Visualization | 8 | Planned |
| 162 | Management API + Hot Reload | 13 | Planned |

## Architecture: Agent Expert Registry

### Design Reference
- Claude Code: `.claude/agents/*.md` with YAML frontmatter
- CC source study: `docs/07-analysis/claude-code-study/06-agent-system/agent-delegation.md`

### Key Components

```
backend/src/integrations/orchestration/experts/
├── __init__.py                          # Public exports
├── registry.py                          # AgentExpertRegistry + AgentExpertDefinition
├── exceptions.py                        # Expert-specific exceptions
├── domain_tools.py                      # Domain-specific tool schemas (Sprint 160)
├── tool_validator.py                    # Tool schema validation (Sprint 160)
└── definitions/                         # YAML expert definitions
    ├── network_expert.yaml
    ├── database_expert.yaml
    ├── application_expert.yaml
    ├── security_expert.yaml
    ├── cloud_expert.yaml
    └── general.yaml
```

### Fallback Chain
1. YAML expert definition (from `experts/definitions/`)
2. `worker_roles.py` legacy role (backward compat)
3. `general.yaml` as final safety net

### Integration Points
- `TaskDecomposer` — enriched roles text with expert capabilities
- `TeamExecutor` — per-expert system prompt, model, tools
- `SubagentExecutor` — same expert integration
- `TeamToolRegistry` — per-expert tool whitelist + domain tools
- Frontend `AgentCard` — domain badges, capabilities chips

## Worktree

- Branch: `feature/phase-46-agent-expert-registry`
- Path: `C:\Users\Chris\Downloads\ai-semantic-kernel-expert-registry`
