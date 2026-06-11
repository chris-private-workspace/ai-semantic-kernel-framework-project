# IPA Platform - Phase 1 to Phase 12 Planning Summary

**Generated**: 2026-03-15
**Source**: Sprint planning documents from `docs/03-implementation/sprint-planning/`
**Scope**: Phase 1 (Sprint 0-6) through Phase 12 (Sprint 48-50)

---

## Phase 1: Foundation & MVP
- **Sprints**: Sprint 0, 1, 2, 3, 4, 5, 6
- **Goal**: Build the complete MVP for the IPA Platform, starting from development infrastructure setup, through core Agent Framework integration, workflow orchestration, human-in-the-loop checkpoints, cross-system connectors, audit logging, notification, developer experience tooling, frontend UI, and finally E2E testing with production deployment readiness.
- **Planned Features**:
  1. **Local Development Environment (S0-1)** -- Docker Compose with PostgreSQL 16, Redis 7, RabbitMQ; .env template; health check endpoint -- `docker-compose.yml`, `scripts/init-db.sql`
  2. **FastAPI Project Structure (S0-2)** -- Standardized backend project skeleton with config management (pydantic Settings), logging, error handling middleware -- `backend/src/core/config.py`, `main.py`, `pyproject.toml`
  3. **CI/CD Pipeline (S0-3)** -- GitHub Actions for lint (Black, isort, flake8, mypy), test, build, coverage upload -- `.github/workflows/ci.yml`
  4. **Azure Resource Provisioning (S0-4)** -- Terraform scripts for App Service, PostgreSQL Flexible Server, Redis Cache, Key Vault, Service Bus -- `infrastructure/main.tf`
  5. **Agent Framework Core Integration (S1-1)** -- AzureOpenAIChatClient initialization, AgentService, AgentExecutor creation, LLM token/cost statistics -- `src/domain/agents/service.py`, `src/api/v1/agents/routes.py`
  6. **Workflow Foundation (S1-2)** -- WorkflowDefinition, WorkflowNode, WorkflowEdge domain models; WorkflowBuilder integration for sequential execution; Workflow CRUD API -- `src/domain/workflows/models.py`, `src/domain/workflows/execution_service.py`, `src/api/v1/workflows/routes.py`
  7. **Tool Integration Mechanism (S1-3)** -- BaseTool abstract class, ToolRegistry, built-in tools (HttpTool, DateTimeTool, get_weather, search_knowledge_base) -- `src/domain/agents/tools/base.py`, `tools/builtin.py`, `tools/registry.py`
  8. **Execution State Management (S1-4)** -- ExecutionStateMachine with state transitions (pending/running/paused/completed/failed/cancelled), Execution CRUD API -- `src/domain/executions/state_machine.py`, `src/api/v1/executions/routes.py`
  9. **Checkpoint Mechanism (S2-1)** -- DatabaseCheckpointStorage adapter wrapping Agent Framework FileCheckpointStorage; checkpoint save/load/list; CheckpointService for pending approvals -- `src/domain/checkpoints/storage.py`, `src/api/v1/checkpoints/routes.py`
  10. **Human-in-the-Loop Approval Flow (S2-2)** -- ApprovalGateway executor using Agent Framework request_info/response_handler pattern; WorkflowResumeService for checkpoint-based resume -- `src/domain/workflows/executors/approval.py`, `src/domain/workflows/resume_service.py`
  11. **Cross-System Connectors (S2-3)** -- BaseConnector abstract class; ServiceNowConnector (get/list/create/update incidents); Dynamics 365 and SharePoint connectors; connector-as-agent-tool wrappers -- `src/domain/connectors/base.py`, `connectors/servicenow.py`, `tools/connector_tools.py`
  12. **Redis LLM Cache (S2-4)** -- LLMCacheService with SHA256-based key generation, TTL, hit/miss statistics; CachedAgentService wrapper; cache stats/clear API -- `src/infrastructure/cache/llm_cache.py`, `src/api/v1/cache/routes.py`
  13. **n8n Webhook Trigger & Error Handling (S3-1)** -- WebhookTriggerService with HMAC signature verification, retry mechanism, n8n error callback -- `src/domain/triggers/webhook.py`, `src/api/v1/triggers/routes.py`
  14. **Prompt Template Management (S3-2)** -- PromptTemplateManager loading YAML templates, variable substitution via string.Template, version management -- `src/domain/prompts/template.py`, `prompts/it_operations.yaml`, `src/api/v1/prompts/routes.py`
  15. **Append-Only Audit Log System (S3-3)** -- AuditLogger with typed AuditAction enum, query by action/actor/execution/time, execution trail retrieval, export -- `src/domain/audit/logger.py`, `src/api/v1/audit/routes.py`
  16. **Microsoft Teams Notification (S3-4)** -- TeamsNotificationService with Adaptive Card support for approval requests, execution completion, error alerts -- `src/domain/notifications/teams.py`
  17. **Cross-Scenario Collaboration (S3-5)** -- ScenarioRouter for IT Operations <-> Customer Service cross-scenario workflow triggering -- `src/domain/routing/scenario_router.py`
  18. **Agent Template Marketplace (S4-1)** -- AgentTemplate data model, TemplateService with YAML loading, category/search filtering, one-click instantiation; 6+ preset templates (IT Triage, CS Helper, Escalation, Report, Knowledge, Monitoring) -- `src/domain/templates/models.py`, `src/domain/templates/service.py`, `src/api/v1/templates/routes.py`
  19. **Few-shot Learning Mechanism (S4-2)** -- LearningService recording human corrections, pg_trgm similarity search for similar cases, few-shot prompt builder, case approval workflow -- `src/domain/learning/service.py`
  20. **DevUI Visual Debugging (S4-3)** -- ExecutionTracer with typed TraceEvents (workflow/executor/LLM/tool/checkpoint/error), timeline API, WebSocket streaming endpoint -- `src/domain/devtools/tracer.py`, `src/api/v1/devtools/routes.py`
  21. **Template Version Management (S4-4)** -- Version numbering, version history viewing, rollback, publish review process -- templates system
  22. **Frontend Architecture (S5-1)** -- React 18 + TypeScript + Vite + TailwindCSS + Shadcn/ui + TanStack Query + React Router + Zustand + Recharts; API client using Fetch API; AppLayout with Sidebar -- `frontend/src/`
  23. **Dashboard Page (S5-2)** -- StatsCards (total executions, success rate, pending approvals, LLM cost), ExecutionChart, RecentExecutions, PendingApprovals -- `src/pages/dashboard/`
  24. **Workflow Management Pages (S5-3)** -- Workflow list, detail, execution trigger, execution history -- `src/pages/workflows/`
  25. **Agent Management Pages (S5-4)** -- Agent list, detail, create from template, test run -- `src/pages/agents/`
  26. **Approval Workbench (S5-5)** -- Pending approval list, detail dialog, approve/reject with feedback -- `src/pages/approvals/`
  27. **E2E Testing Suite (S6-1)** -- Complete E2E test framework with authenticated client; workflow lifecycle test, human approval flow test -- `tests/e2e/`
  28. **Performance Testing & Optimization (S6-2)** -- Locust load test scripts; DB query optimization, cache optimization, API compression -- `tests/load/locustfile.py`
  29. **Security Audit (S6-3)** -- OWASP Top 10 checks, dependency vulnerability scanning (pip-audit, npm audit), auth/authz testing, data encryption verification -- `tests/security/`
  30. **Production Deployment (S6-4)** -- Azure App Service deployment via Docker, ACR push, health check validation, rollback plan -- `deploy/deploy.sh`, Azure Front Door + WAF + CDN
  31. **User Documentation (S6-5)** -- Quick start guide, feature usage, FAQ, admin guide, API reference -- `docs/user-guide/`, `docs/admin-guide/`
- **Planned Story Points**: Sprint 0: 34 pts, Sprint 1: 42 pts, Sprint 2: 45 pts, Sprint 3: 40 pts, Sprint 4: 38 pts, Sprint 5: 45 pts, Sprint 6: 35 pts. **Total: ~279-285 pts**
- **Key Architecture Decisions**:
  - Microsoft Agent Framework (Preview) as the core orchestration engine
  - FastAPI + PostgreSQL 16 + Redis 7 + RabbitMQ as backend stack
  - React 18 + TypeScript + Shadcn/ui as frontend stack
  - Pydantic Settings for configuration management (not os.environ)
  - Azure OpenAI (GPT-4o) as the LLM provider
  - FileCheckpointStorage from Agent Framework for workflow state persistence
  - Adapter pattern wrapping Agent Framework APIs for isolation

---

## Phase 2: Parallel Execution Engine
- **Sprints**: Sprint 7, 8, 9, 10, 11, 12
- **Goal**: Upgrade IPA Platform from basic sequential execution to an enterprise-grade multi-Agent collaboration platform by implementing concurrent execution, agent handoff, group chat, dynamic planning, nested workflows, and integration/optimization.
- **Planned Features**:
  1. **Concurrent Execution (P2-F1)** -- ConcurrentExecutor for parallel agent task execution, 3x throughput improvement -- Sprint 7, 21 pts
  2. **Enhanced Gateway (P2-F2)** -- Advanced gateway with fan-out/fan-in routing and conditional logic -- Sprint 7, 13 pts
  3. **Agent Handoff Mechanism (P2-F3)** -- HandoffExecutor for dynamic agent task delegation and transfer protocol -- Sprint 8, 18 pts
  4. **Collaboration Protocol (P2-F4)** -- Inter-agent collaboration protocol with context sharing -- Sprint 8, 13 pts
  5. **GroupChat Multi-Agent (P2-F5)** -- GroupChatManager with speaker selection strategies for multi-agent discussions -- Sprint 9, 21 pts
  6. **Multi-turn Conversation (P2-F6)** -- Multi-turn dialogue with context preservation across turns -- Sprint 9, 13 pts
  7. **Conversation Memory (P2-F7)** -- Conversation memory store for persistent dialogue state -- Sprint 9, 8 pts
  8. **Dynamic Planning (P2-F8)** -- DynamicPlanner with PlanningAgent and TaskDecomposer for autonomous task planning -- Sprint 10, 21 pts
  9. **Autonomous Decision Making (P2-F9)** -- AutonomousDecisionEngine for self-directed agent decision making -- Sprint 10, 13 pts
  10. **Trial-and-Error Mechanism (P2-F10)** -- TrialAndErrorEngine for iterative learning from failures -- Sprint 10, 8 pts
  11. **Nested Workflows (P2-F11)** -- NestedWorkflowManager for recursive/hierarchical workflow structures -- Sprint 11, 18 pts
  12. **Sub-workflow Execution (P2-F12)** -- Sub-workflow invocation and result aggregation -- Sprint 11, 13 pts
  13. **Recursive Patterns (P2-F13)** -- Support for recursive workflow patterns with depth limiting -- Sprint 11, 8 pts
  14. **Performance Optimization (P2-F14)** -- System-wide performance optimization and benchmarking -- Sprint 12, 13 pts
  15. **UI Integration (P2-F15)** -- Frontend updates for new execution modes and visualization -- Sprint 12, 13 pts
  16. **Documentation & Testing (P2-F16)** -- Comprehensive docs and test coverage for all Phase 2 features -- Sprint 12, 8 pts
- **Planned Story Points**: ~222 pts total
- **Key Architecture Decisions**:
  - New Orchestration Engine layer with Sequential, Concurrent, GroupChat, Handoff, Dynamic Planner, and Nested Workflow executors
  - New Conversation & Memory Layer with Multi-turn Session Manager and Conversation Memory Store
  - All features initially implemented as custom code (later migrated in Phase 3-4)

---

## Phase 3: Official API Migration
- **Sprints**: Sprint 13, 14, 15, 16, 17, 18
- **Goal**: Replace ALL Phase 2 custom implementations with official Microsoft Agent Framework APIs. This was a complete refactoring to address the architecture issue that Phase 2 built entirely custom functionality instead of using official APIs, creating significant technical debt.
- **Planned Features**:
  1. **Infrastructure Preparation (Sprint 13)** -- Agent Framework API wrapper layer, WorkflowBuilder base integration, CheckpointStorage adapter, test framework/mocks, migration guide -- 34 pts
  2. **ConcurrentBuilder Migration (Sprint 14)** -- ConcurrentBuilder adapter, ConcurrentExecutor functionality migration, fan-out/fan-in edge routing, API endpoint updates -- 34 pts
  3. **HandoffBuilder Migration (Sprint 15)** -- HandoffBuilder adapter, HandoffController migration, HandoffUserInputRequest HITL integration -- 34 pts
  4. **GroupChatBuilder Migration (Sprint 16)** -- GroupChatBuilder adapter, GroupChatManager migration, GroupChatOrchestratorExecutor, ManagerSelectionResponse integration -- 42 pts
  5. **MagenticBuilder Migration (Sprint 17)** -- MagenticBuilder adapter, StandardMagenticManager, Task/Progress Ledger integration, Human Intervention system -- 42 pts
  6. **WorkflowExecutor & Integration (Sprint 18)** -- WorkflowExecutor adapter, NestedWorkflowManager migration, full-feature integration testing, performance testing, old code cleanup -- 36 pts
- **Planned Story Points**: 222 pts total (all completed)
- **Key Architecture Decisions**:
  - Wrapper/adapter layer pattern to isolate official Agent Framework API changes
  - Backward-compatible API endpoints throughout migration
  - Each sprint migrates one module, old code retained until next sprint confirms no issues

---

## Phase 4: Advanced Adapters (Complete Refactoring)
- **Sprints**: Sprint 20, 21, 22, 23, 24, 25 (note: Sprint 19 was part of Phase 3 scope)
- **Goal**: Fully reconnect all custom implementations back to official Microsoft Agent Framework architecture, reducing custom code from ~19,844 lines (24.3%) to under 3,000 lines (-85%) and raising official API usage from 2.4% to over 80%.
- **Planned Features**:
  1. **GroupChat Complete Migration (Sprint 20)** -- GroupChat voting adapter extension, full GroupChatBuilder integration -- 34 pts
  2. **Handoff Complete Migration (Sprint 21)** -- Handoff capability matching, complete HandoffBuilder integration -- 32 pts
  3. **Concurrent & Memory Migration (Sprint 22)** -- ConcurrentOrchestration + conversation memory migration -- 28 pts
  4. **Nested Workflow Refactoring (Sprint 23)** -- WorkflowExecutor-based nested workflow support -- 35 pts
  5. **Planning & Multi-turn Migration (Sprint 24)** -- MagenticOrchestration integration, multi-turn session migration -- 30 pts
  6. **Cleanup, Testing & Documentation (Sprint 25)** -- Final code cleanup, comprehensive testing, documentation -- 21 pts
- **Planned Story Points**: 180 pts total (all completed)
- **Key Architecture Decisions**:
  - Adapter-first pattern: `API Layer -> BuilderAdapter -> Official Agent Framework API`
  - Phase 2 custom features (voting, capability matching) preserved through adapter extensions
  - Incremental migration with old code retained until confirmed working

---

## Phase 5: Connector Ecosystem (MVP Core Official API Migration)
- **Sprints**: Sprint 26, 27, 28, 29, 30
- **Goal**: Migrate all Phase 1 MVP core functionality (WorkflowDefinition, WorkflowExecutionService, CheckpointService, ExecutionStateMachine, API routes) to official Agent Framework APIs. Phase 4 audit revealed that while Phase 2-4 adapters were 100% compliant, the original Phase 1 MVP core at 0% compliance with official APIs.
- **Planned Features**:
  1. **Workflow Model Migration (Sprint 26)** -- WorkflowNodeAdapter (Executor-based), WorkflowEdgeAdapter (official Edge), WorkflowDefinitionAdapter, WorkflowContext integration -- 36 pts
  2. **Execution Engine Migration (Sprint 27)** -- SequentialOrchestrationAdapter, WorkflowStatusEventAdapter, ExecutionStateMachine refactoring to official event system -- 38 pts
  3. **Human Approval Migration (Sprint 28)** -- HumanApprovalExecutor based on RequestResponseExecutor, ApprovalRequest/Response models, CheckpointService refactoring to separate storage from approval -- 34 pts
  4. **API Routes Migration (Sprint 29)** -- handoff/routes.py, workflows/routes.py, executions/routes.py, checkpoints/routes.py all migrated to use adapter layer -- 38 pts
  5. **Integration & Acceptance (Sprint 30)** -- E2E integration testing, performance testing (no regression), documentation updates, deprecated code cleanup, final audit -- 34 pts
- **Planned Story Points**: ~183 pts total (all completed)
- **Key Architecture Decisions**:
  - Official `agent_framework.workflows` API as the foundation (Workflow, Executor, Edge, RequestResponseExecutor)
  - Official orchestrations: SequentialOrchestration, ConcurrentOrchestration, HandoffOrchestration, MagenticOrchestration
  - Verification script `verify_official_api_usage.py` as compliance gate

---

## Phase 6: Enterprise Integration (Architecture Closure & Quality Hardening)
- **Sprints**: Sprint 31, 32, 33 (note: these are Phase 6 sprint numbers, not the same as Phase 31-33 in the main overview)
- **Goal**: Resolve all remaining architecture audit issues from Phase 1-5 (overall compliance at 89%), fix P0 issues (Planning API using deprecated code, AgentService API location), P1 issues (GroupChat session layer, domain code residuals), and P2 issues (differentiation feature validation, frontend UI completeness). Prepare for UAT.
- **Planned Features**:
  1. **Planning API Complete Migration (Sprint 31)** -- Planning API route migration to PlanningAdapter, AgentExecutor adapter creation, Concurrent API route fix, deprecated code cleanup -- 28 pts
  2. **Session Layer Unification & Domain Cleanup (Sprint 32)** -- MultiTurnAdapter creation, GroupChat API session layer migration, domain code final cleanup -- 28 pts
  3. **Differentiation Feature Validation & Closure (Sprint 33)** -- Cross-system intelligent correlation validation (60% implemented), proactive patrol mode assessment (40% implemented), frontend UI completeness audit (core 100%), UAT preparation -- 22 pts
- **Planned Story Points**: 78 pts total (all completed)
- **Key Architecture Decisions**:
  - Architecture compliance raised from 89% to 95%+
  - Official API centralization raised from 77.8% to 95%+
  - Domain migration progress raised from 50.7% to ~90%
  - UAT readiness achieved

---

## Phase 7: Multi-turn & Memory (AI Autonomous Decision Capability)
- **Sprints**: Sprint 34, 35, 36
- **Goal**: Enable true LLM-powered AI autonomous decision-making for Phase 2 extension features. Discovery during UAT preparation revealed that TaskDecomposer, AutonomousDecisionEngine, and TrialAndErrorEngine were designed to support LLM but never actually injected with `llm_service`, operating purely on rule-based logic instead of AI reasoning.
- **Planned Features**:
  1. **LLM Service Infrastructure (Sprint 34)** -- LLMServiceProtocol interface definition, AzureOpenAILLMService implementation, MockLLMService for testing, CachedLLMService for production, LLMServiceFactory and configuration management -- 20 pts
  2. **Phase 2 Extension LLM Integration (Sprint 35)** -- PlanningAdapter LLM integration, TaskDecomposer LLM enablement (semantic task decomposition), AutonomousDecisionEngine LLM enablement (contextual decision analysis), TrialAndErrorEngine LLM enablement (error context understanding) -- 23 pts
  3. **Verification & Optimization (Sprint 36)** -- End-to-end AI decision testing, performance benchmarking and optimization, documentation and UAT preparation, LLM fallback strategy verification -- 15 pts
- **Planned Story Points**: 58 pts total
- **Key Architecture Decisions**:
  - LLMServiceProtocol abstraction with multiple implementations (Azure, Mock, Cached)
  - Rule-based logic retained as fallback when LLM is unavailable
  - Structured output with JSON Schema validation for LLM responses
  - Token budget management for cost control

---

## Phase 8: Code Interpreter
- **Sprints**: Sprint 37, 38
- **Goal**: Integrate Azure OpenAI Code Interpreter (Assistants API) into IPA Platform, enabling agents to execute Python code dynamically for data analysis, file processing, mathematical computation, and visualization generation.
- **Planned Features**:
  1. **Code Interpreter Infrastructure (Sprint 37)** -- AssistantManagerService for Azure OpenAI Assistants lifecycle management, CodeInterpreterAdapter adapter implementation, Code Interpreter API endpoints (`/api/v1/code-interpreter/execute`, `/api/v1/code-interpreter/analyze`), unit and integration tests -- 20 pts
  2. **Agent Integration & Extension (Sprint 38)** -- Agent tool extension with Code Interpreter support, file upload and processing functionality, execution result visualization, documentation and examples -- 15 pts
- **Planned Story Points**: 35 pts total
- **Key Architecture Decisions**:
  - Azure OpenAI Assistants API with `tools=["code_interpreter"]` as the execution backend
  - AssistantManagerService managing Assistant, Thread, and Run lifecycle
  - CodeInterpreterAdapter following the same adapter pattern as other Agent Framework integrations
  - Sandboxed execution via Azure (no local code execution)
  - Integration with Phase 7 LLMService infrastructure

---

## Phase 9: MCP Integration (MCP Architecture & Tool Execution Layer)
- **Sprints**: Sprint 39, 40, 41
- **Goal**: Build a unified MCP (Model Context Protocol) architecture providing agents with real execution capabilities for enterprise automation -- managing Azure resources, executing shell scripts, reading/writing files, querying LDAP/AD, and SSH connections to remote servers.
- **Planned Features**:
  1. **MCP Core Framework (Sprint 39)** -- MCP Client core (tool discovery, request routing, permission checking, audit logging), tool registry, permission system with 3-tier security levels (Level 1: read-only auto-execute, Level 2: low-risk write with agent confirmation, Level 3: high-risk requiring human approval), MCP audit trail -- 40 pts
  2. **Azure MCP Server (Sprint 40)** -- Azure CLI wrapping (az vm, az webapp, az storage, az network), Azure resource management, monitoring integration -- 35 pts
  3. **Execution MCP Servers (Sprint 41)** -- Shell MCP Server (PowerShell/Bash/CMD), Filesystem MCP Server, SSH MCP Server (paramiko), LDAP MCP Server (ldap3) -- 35 pts
- **Planned Story Points**: 110 pts total
- **Key Architecture Decisions**:
  - Model Context Protocol (MCP) standard with JSON-RPC 2.0
  - Three-tier security model: read-only (auto), low-risk write (agent confirms), high-risk (human-in-the-loop)
  - All MCP operations recorded in audit trail
  - Each MCP Server has independent permission control
  - MCP Servers reusable across multiple agents

---

## Phase 10: MCP Expansion (Session Mode API)
- **Sprints**: Sprint 42, 43, 44
- **Goal**: Implement interactive Session Mode enabling users to have real-time conversational interactions with agents (similar to ChatGPT/Claude), with file upload/analysis, file generation/download, and in-conversation MCP tool invocation. This creates a dual-mode architecture alongside the existing Workflow Mode.
- **Planned Features**:
  1. **Session Management Core (Sprint 42)** -- Session lifecycle (CREATED -> ACTIVE -> SUSPENDED -> ENDED), session state persistence (PostgreSQL for metadata/history, Redis for real-time state, Azure Blob/local for attachments), Session CRUD API, timeout handling -- 35 pts
  2. **Real-time Communication (Sprint 43)** -- WebSocket bidirectional communication, Server-Sent Events as fallback, streaming responses (stream_start/delta/end events), typing indicators, tool call events with approval request/response -- 35 pts
  3. **Session Features (Sprint 44)** -- File upload (multi-format), file analysis via Code Interpreter (Phase 8), file generation and download, in-conversation MCP tool invocation with approval inheritance, conversation history -- 30 pts
- **Planned Story Points**: 100 pts total
- **Key Architecture Decisions**:
  - Dual-mode architecture: Workflow Mode (backend automation) + Session Mode (real-time dialogue)
  - Shared infrastructure: both modes use same Agent Execution Engine, MCP Tool Layer, LLM Integration
  - WebSocket as primary real-time protocol, SSE as degradation fallback
  - Session state machine: CREATED -> ACTIVE <-> SUSPENDED -> ENDED
  - File storage strategy: PostgreSQL (metadata, permanent), Redis (real-time state, session duration), Blob/local (attachments, configurable retention)

---

## Phase 11: Agent-Session Integration
- **Sprints**: Sprint 45, 46, 47
- **Goal**: Complete the integration between Session Mode (Phase 10) and Agent Framework, creating a unified AgentExecutor that enables true multi-turn conversations through sessions. Phase 10 built session infrastructure but did not connect it to actual Agent execution.
- **Planned Features**:
  1. **Agent Executor Core (Sprint 45)** -- AgentExecutor as unified execution interface supporting both Workflow and Session modes, LLM integration with Azure OpenAI, streaming support for token-by-token response delivery -- 35 pts
  2. **Session-Agent Bridge (Sprint 46)** -- SessionAgentBridge connecting SessionService to AgentExecutor, message processing pipeline (store user msg -> get history -> execute agent -> store assistant msg -> stream response), tool call handling with MCP permission integration -- 30 pts
  3. **Integration & Polish (Sprint 47)** -- End-to-end integration testing, error handling refinement, conversation history management with token limits, documentation -- 25 pts
- **Planned Story Points**: 90 pts total
- **Key Architecture Decisions**:
  - AgentExecutor as the single unified execution interface for both modes
  - Workflow Mode path: `/executions` -> WorkflowExecutor -> Adapters
  - Session Mode path: `/sessions/{id}/messages` -> SessionAgentBridge -> AgentExecutor
  - MessageRole enum: USER, ASSISTANT, SYSTEM, TOOL
  - Tool call flow: LLM decides -> permission check -> auto-execute or human approval -> result back to LLM
  - Workflow orchestration remains the platform's primary capability; session-based dialogue is an additional capability

---

## Phase 12: Claude Agent SDK Integration
- **Sprints**: Sprint 48, 49, 50
- **Goal**: Integrate Anthropic's Claude Agent SDK into IPA Platform to create a Hybrid Agent Architecture that combines the strengths of Microsoft Agent Framework (workflow orchestration) with Claude Agent SDK (autonomous coding, tool use, multi-turn reasoning).
- **Planned Features**:
  1. **Core SDK Integration (Sprint 48)** -- ClaudeSDKClient implementation wrapping Claude Agent SDK, query() API for one-shot interactions, multi-turn session management, Claude model integration (claude-sonnet-4-20250514) -- 35 pts
  2. **Tools & Hooks System (Sprint 49)** -- Built-in tool integration (Read, Write, Edit, Bash, Grep, Glob, WebSearch), Hook interception mechanism (ApprovalHook for write operations, AuditHook for logging, SandboxHook for security), ToolCallContext and HookResult patterns -- 32 pts
  3. **MCP & Hybrid Architecture (Sprint 50)** -- MCP Server integration for Claude SDK (MCPStdioServer for Postgres, GitHub, custom servers), HybridOrchestrator coordinating both frameworks, Task Router for intelligent routing between MAF and Claude SDK, Context Sync for cross-framework state sharing, Capability Match for framework selection, Unified Agent API (`/api/v1/agents/`, `/api/v1/hybrid/`) -- 38 pts
- **Planned Story Points**: 105 pts total
- **Key Architecture Decisions**:
  - Hybrid architecture: Microsoft Agent Framework for structured workflow orchestration + Claude Agent SDK for autonomous reasoning
  - HybridOrchestrator as the central coordinator with Task Router, Context Sync, and Capability Match
  - Claude SDK tools (Read/Write/Edit/Bash/Grep/Glob/WebSearch) integrated alongside MCP tools
  - Hook system for cross-cutting concerns (approval, audit, sandbox)
  - MCPStdioServer pattern for MCP Server integration with Claude SDK
  - Unified API surface abstracting both frameworks

---

## Cross-Phase Summary Table

| Phase | Name | Sprints | Planned Story Points | Primary Theme |
|-------|------|---------|---------------------|---------------|
| Phase 1 | Foundation & MVP | 0-6 | ~285 pts | Dev infra, Agent Framework core, workflows, HITL, connectors, frontend, deployment |
| Phase 2 | Parallel Execution Engine | 7-12 | ~222 pts | Concurrent execution, handoff, group chat, dynamic planning, nested workflows |
| Phase 3 | Official API Migration | 13-18 | ~222 pts | Full refactoring from custom code to official Agent Framework APIs |
| Phase 4 | Advanced Adapters | 20-25 | ~180 pts | Complete adapter-based integration, custom code reduction from 24% to <5% |
| Phase 5 | Connector Ecosystem | 26-30 | ~183 pts | Phase 1 MVP core migration to official APIs (0% -> 95%+ compliance) |
| Phase 6 | Enterprise Integration | 31-33 | ~78 pts | Architecture closure, P0/P1 issue resolution, UAT readiness |
| Phase 7 | Multi-turn & Memory | 34-36 | ~58 pts | LLM service layer, AI autonomous decision enablement for Phase 2 extensions |
| Phase 8 | Code Interpreter | 37-38 | ~35 pts | Azure OpenAI Code Interpreter / Assistants API integration |
| Phase 9 | MCP Integration | 39-41 | ~110 pts | MCP core framework, Azure/Shell/Filesystem/SSH/LDAP MCP servers |
| Phase 10 | MCP Expansion | 42-44 | ~100 pts | Session Mode API, WebSocket real-time communication, file interaction |
| Phase 11 | Agent-Session Integration | 45-47 | ~90 pts | AgentExecutor, SessionAgentBridge, unified execution for both modes |
| Phase 12 | Claude Agent SDK | 48-50 | ~105 pts | Claude SDK integration, hybrid architecture, hooks system |
| **Total** | | **50 Sprints** | **~1,668 pts** | |

---

## Deferred / Out-of-Scope Items Noted in Plans

1. **Phase 1 Sprint 2 (S2-3)**: Dynamics 365 and SharePoint connectors were planned but implementation details were less detailed than ServiceNow -- likely minimal/stub implementations.
2. **Phase 1 Sprint 3 (S3-5)**: Cross-scenario routing `_get_default_workflow()` had a TODO comment for fetching from config/database.
3. **Phase 1 Sprint 5 (S5-5)**: Approval workbench `current_user` extraction marked as TODO.
4. **Phase 6 Sprint 33**: Cross-system intelligent correlation only at 60% implementation; proactive patrol mode only at 40% implementation -- noted as partial delivery.
5. **Phase 7**: LLM fallback strategy (rule-based when LLM unavailable) planned as P2 priority in Sprint 36.
6. **Phase 10**: Azure Blob storage for attachments listed as optional (local storage as alternative).
7. **Phase 12**: Listed as "planning" status with Anthropic API Key configuration and Claude SDK package installation as pending prerequisites.
