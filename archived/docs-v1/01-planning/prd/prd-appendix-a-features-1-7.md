# PRD Appendix A: Features 1-7 Detailed Specifications

**Version**: 1.0  
**Date**: 2025-11-18  
**Status**: Draft

---

## 📑 Document Navigation

- [PRD Main Document](./prd-main.md)
- **[PRD Appendix A: Features 1-7](./prd-appendix-a-features-1-7.md)** ← You are here
- [PRD Appendix B: Features 8-14](./prd-appendix-b-features-8-14.md)
- [PRD Appendix C: API Specifications](./prd-appendix-c-api-specs.md)

---

## Table of Contents

- [F1. Sequential Agent Orchestration](#f1-sequential-agent-orchestration)
- [F2. Human-in-the-loop Checkpointing](#f2-human-in-the-loop-checkpointing)
- [F3. Cross-System Correlation](#f3-cross-system-correlation)
- [F4. Cross-Scenario Collaboration](#f4-cross-scenario-collaboration)
- [F5. Learning-based Collaboration](#f5-learning-based-collaboration)
- [F6. Agent Marketplace](#f6-agent-marketplace)
- [F7. DevUI Integration](#f7-devui-integration)

---

<a id="f1-sequential-agent-orchestration"></a>
## F1. Sequential Agent Orchestration

**Category**: Engine (Core)  
**Priority**: P0 (Foundational - Must Have)  
**Development Time**: Design Phase (Architecture)  
**Complexity**: ⭐⭐⭐ (Medium-High)  
**Dependencies**: Microsoft Agent Framework (Preview), FastAPI, PostgreSQL  
**Risk Level**: Medium (Agent Framework API may change during preview)

---

### 1.1 Feature Overview

**What is Sequential Agent Orchestration?**

Sequential Agent Orchestration is the **foundational capability** that enables multiple AI agents to work together in a coordinated pipeline. Each agent executes its specialized task, passes results to the next agent, and collectively achieves complex automation goals that no single agent could accomplish alone.

**Why This Matters**:
- **Business Complexity**: Real-world processes require multiple steps (e.g., ticket analysis → customer lookup → solution generation)
- **Specialization**: Different agents have different skills (one analyzes text, another queries databases, another generates responses)
- **Reusability**: Agents can be reused across multiple workflows
- **Observability**: Clear execution flow makes debugging easier
- **Scalability**: Add new agents to workflows without rewriting existing logic

**Key Capabilities**:
1. **Sequential Execution**: Agents execute in strict order (Agent A → Agent B → Agent C)
2. **Context Passing**: JSON data flows seamlessly between agents with full type preservation
3. **Error Handling**: Automatic workflow termination on failure with detailed error logging
4. **State Persistence**: Complete execution state saved to PostgreSQL for recovery and auditing
5. **Observability**: Full execution trace with timestamps, inputs, outputs, and errors
6. **Validation**: Schema validation between agent transitions (optional but recommended)

**Business Value**:
- **Automation**: Enable complex multi-step processes without human intervention
- **Cost Reduction**: Eliminate manual hand-offs between systems ($10K+/month savings)
- **Faster Resolution**: Reduce ticket resolution time from 24 hours to 2-3 hours
- **Auditability**: Complete execution logs for compliance and debugging
- **Agility**: Rapidly prototype new workflows by combining existing agents

**Real-World Example**:
```
IT Ticket Triage Workflow:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Ticket Analyzer │ -> │ Customer Data   │ -> │ Solution        │
│ Agent           │    │ Retrieval Agent │    │ Generator Agent │
└─────────────────┘    └─────────────────┘    └─────────────────┘
      ↓                        ↓                        ↓
  Extract key info      Get customer context    Generate solution
  (ticket_id,           (purchase history,      (recommended actions,
   priority,            support history,         root cause,
   customer_id)         sentiment)               next steps)
```

---

### 1.2 User Stories (Complete)

#### **US-F1-001: Create Multi-Step Workflow with Visual Canvas**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As an** IT Operations Admin (Alex Chen)
- **I want to** create a workflow that chains 3 agents together using a visual drag-and-drop interface:
  1. **Ticket Analyzer Agent**: Extracts structured data from unstructured ServiceNow ticket text
  2. **Customer Data Agent**: Retrieves customer 360 view from Dynamics 365 and SharePoint
  3. **Solution Generator Agent**: Uses GPT-4o to generate recommended solution based on ticket + customer context
- **So that** I can automate the entire ticket triage process without writing code

**Acceptance Criteria**:
1. ✅ **Visual Canvas**: User sees a drag-and-drop workflow canvas (using React Flow)
2. ✅ **Agent Library**: User can drag agents from left sidebar agent library to canvas
3. ✅ **Connect Agents**: User can draw arrows between agents to define execution sequence
4. ✅ **Data Mapping**: System automatically validates that Agent A's output schema matches Agent B's expected input schema
5. ✅ **Manual Mapping**: User can manually map fields if schemas don't auto-match (e.g., `ticket_id` from Agent 1 → `customer_id` lookup in Agent 2)
6. ✅ **Save Workflow**: System saves workflow configuration to `workflows` table in PostgreSQL
7. ✅ **Test Mode**: User can run workflow in test mode with sample input before deploying to production
8. ✅ **Execution Preview**: System displays expected data flow with sample data before execution
9. ✅ **Error Prevention**: System prevents saving workflow if validation fails (e.g., circular dependencies, unconnected agents)
10. ✅ **Version Control**: System saves workflow version history (MVP: simple version counter)

**UI Mockup (ASCII)**:
```
┌──────────────────────────────────────────────────────────────────────┐
│ Workflow Editor: IT Ticket Triage                          [Save] [Test] [Deploy] │
├────────────┬─────────────────────────────────────────────────────────┤
│ Agent Lib  │  Canvas                                                 │
│            │                                                         │
│ ┌────────┐ │   ┌─────────────────┐                                  │
│ │Ticket  │ │   │ Ticket Analyzer │                                  │
│ │Analyzer│ │   │ Agent           │                                  │
│ └────────┘ │   └────────┬────────┘                                  │
│            │            │ outputs: {ticket_id, priority, category}  │
│ ┌────────┐ │            ↓                                           │
│ │Customer│ │   ┌─────────────────┐                                  │
│ │Data    │ │   │ Customer Data   │                                  │
│ └────────┘ │   │ Agent           │                                  │
│            │   └────────┬────────┘                                  │
│ ┌────────┐ │            │ outputs: {customer_360}                   │
│ │Solution│ │            ↓                                           │
│ │Gen     │ │   ┌─────────────────┐                                  │
│ └────────┘ │   │ Solution        │                                  │
│            │   │ Generator Agent │                                  │
│ ... more   │   └─────────────────┘                                  │
│            │            │ outputs: {solution, confidence}           │
└────────────┴────────────┴───────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] User can create workflow with 3+ agents using visual canvas
- [ ] System validates data compatibility between connected agents
- [ ] Workflow saves to database with complete configuration (agents, sequence, mappings)
- [ ] User can execute test run with sample input and view detailed results
- [ ] System prevents invalid workflows from being saved

**Technical Notes**:
- Use **React Flow** library for visual canvas
- Store workflow as JSON in `workflows.trigger_config` JSONB field
- Implement schema validation using JSON Schema
- Support both automatic and manual field mapping

---

#### **US-F1-002: Pass Complex JSON Data Between Agents with Type Preservation**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** pass complex nested JSON data from Agent 1 to Agent 2 with complete type preservation and no data loss
- **So that** downstream agents receive accurate structured data without manual parsing or transformation

**Acceptance Criteria**:
1. ✅ **Type Preservation**: System preserves all JSON primitive types:
   - `string`: "CS-1234", "john@example.com"
   - `number`: 42, 3.14159, -10
   - `boolean`: true, false
   - `null`: null
2. ✅ **Nested Structures**: System preserves complex nested structures:
   - Objects within arrays: `[{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]`
   - Arrays within objects: `{"tags": ["urgent", "billing"], "metadata": {...}}`
   - Deep nesting (up to 10 levels): `{"level1": {"level2": {"level3": {...}}}}`
3. ✅ **Large Payloads**: System handles payloads up to 10MB per agent output (log warning if >5MB)
4. ✅ **Schema Validation**: If agent defines output schema (JSON Schema), system validates before passing to next agent
5. ✅ **Data Logging**: System logs all data transfers to `executions.result` JSONB field for debugging
6. ✅ **Error Messages**: If validation fails, system provides clear error message with:
   - Expected schema
   - Actual data received
   - Specific validation error (e.g., "Expected string, got number")
7. ✅ **Unicode Support**: System correctly handles Unicode characters (emoji, Chinese, etc.)
8. ✅ **Special Values**: System correctly handles edge cases (empty string "", empty array [], empty object {})

**Example Data Flow**:
```json
// Agent 1 Output: Ticket Analyzer
{
  "ticket_id": "CS-1234",
  "customer_id": "CUST-5678",
  "priority": 3,
  "tags": ["billing", "refund", "urgent"],
  "sentiment": "frustrated",
  "confidence": 0.87,
  "extracted_entities": {
    "amount": 99.99,
    "currency": "USD",
    "product_ids": [101, 102],
    "mentioned_dates": ["2025-11-15", "2025-11-18"]
  },
  "raw_text": "I need a refund for my recent purchase...",
  "metadata": {
    "processing_time_ms": 1250,
    "llm_model": "gpt-4o",
    "llm_tokens": 450
  }
}

// Agent 2 Input: Customer Data (receives full Agent 1 context)
{
  "customer_id": "CUST-5678",          // Extracted from Agent 1
  "ticket_context": {                  // Full Agent 1 output preserved
    "ticket_id": "CS-1234",
    "priority": 3,
    "tags": ["billing", "refund", "urgent"],
    "extracted_entities": {...}        // Nested structure preserved
  }
}

// Agent 3 Input: Solution Generator (receives merged context)
{
  "ticket": {...},                     // From Agent 1
  "customer_360": {                    // From Agent 2
    "profile": {...},
    "purchase_history": [...],
    "support_history": [...]
  }
}
```

**Definition of Done**:
- [ ] All JSON types preserved across agent boundaries (verified by unit tests)
- [ ] Nested structures preserved correctly (up to 10 levels deep)
- [ ] Large payloads (up to 10MB) handled without errors
- [ ] Schema validation runs if agent defines output schema
- [ ] All data transfers logged to database for debugging
- [ ] Clear error messages displayed if validation fails

**Technical Notes**:
- Use Python's native `json` module (preserves types correctly)
- Store in PostgreSQL JSONB (binary JSON, efficient indexing)
- Implement JSON Schema validation using `jsonschema` library
- Log payload size warnings if >5MB

---

#### **US-F1-003: Handle Agent Failures with Graceful Error Recovery**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As an** IT Operations Admin (Alex Chen)
- **I want to** automatically stop the workflow if any agent fails, receive detailed error information via Teams notification, and have the option to manually retry or debug
- **So that** I can prevent cascading errors, quickly diagnose issues, and maintain system reliability

**Acceptance Criteria**:
1. ✅ **Immediate Stop**: System stops workflow execution immediately when any agent raises an exception
2. ✅ **Error Context Logging**: System logs complete error context to `executions` table:
   - Failed agent name and ID
   - Execution step number (e.g., "Step 2 of 5")
   - Full error message and stack trace
   - Input data that caused the failure
   - Timestamp of failure (ISO 8601 format)
   - Previous successful steps' outputs
3. ✅ **Partial Results Preservation**: System saves outputs from all successful agents before failure
4. ✅ **Teams Notification**: System sends Microsoft Teams Adaptive Card notification within 5 seconds with:
   - Workflow name and execution ID
   - Failed agent name
   - Error message (first 200 characters)
   - Link to detailed error page
   - "Retry" and "View Details" action buttons
5. ✅ **Database Status Update**: System updates `executions.status` to `failed` and sets `executions.error` field
6. ✅ **Manual Retry Option**: User can click "Retry" button to re-run workflow from beginning with same input
7. ✅ **Resume from Checkpoint**: If Human-in-the-loop Checkpointing (F2) is enabled, user can resume from last successful checkpoint
8. ✅ **Error Analytics**: System tracks error frequency by agent type for monitoring dashboard (F12)

**Error Notification Example (Microsoft Teams Adaptive Card)**:
```json
{
  "type": "AdaptiveCard",
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "version": "1.5",
  "body": [
    {
      "type": "Container",
      "style": "attention",
      "items": [
        {
          "type": "TextBlock",
          "text": "❌ Workflow Execution Failed",
          "weight": "bolder",
          "size": "large",
          "color": "attention"
        }
      ]
    },
    {
      "type": "FactSet",
      "facts": [
        {"title": "Workflow", "value": "IT: Server Health Check"},
        {"title": "Execution ID", "value": "exec-20251118-789"},
        {"title": "Failed Agent", "value": "Database Query Agent"},
        {"title": "Step", "value": "2 of 5"},
        {"title": "Error", "value": "Connection timeout to SQL Server (10.0.0.50:1433)"},
        {"title": "Time", "value": "2025-11-18 14:32:15 UTC"},
        {"title": "Duration", "value": "12.5 seconds"}
      ]
    },
    {
      "type": "TextBlock",
      "text": "**Partial Results Saved**: Ticket Analyzer Agent completed successfully. Results preserved for debugging.",
      "wrap": true,
      "spacing": "medium"
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "🔍 View Details",
      "url": "https://ipa.example.com/executions/exec-20251118-789"
    },
    {
      "type": "Action.OpenUrl",
      "title": "🔄 Retry Workflow",
      "url": "https://ipa.example.com/executions/exec-20251118-789/retry"
    },
    {
      "type": "Action.OpenUrl",
      "title": "🐛 Debug",
      "url": "https://ipa.example.com/debug/exec-20251118-789"
    }
  ]
}
```

**Definition of Done**:
- [ ] Workflow stops immediately on first agent failure
- [ ] Complete error context logged to database (all required fields)
- [ ] Teams notification sent within 5 seconds of failure
- [ ] User can view partial results from successful agents
- [ ] User can retry workflow from UI with one click
- [ ] Error analytics tracked for monitoring dashboard

**Technical Notes**:
- Use Python `try-except` blocks around each agent execution
- Implement exponential backoff for transient errors (optional for MVP)
- Store stack trace as text in `executions.error` field
- Use Microsoft Teams Incoming Webhook for notifications

---

#### **US-F1-004: Monitor Workflow Execution in Real-Time (MVP: Polling)**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐

**User Story**:
- **As an** IT Operations Admin (Alex Chen)
- **I want to** see real-time progress of my workflow execution (which agents have completed, which is currently running, estimated time remaining)
- **So that** I can monitor long-running workflows and quickly identify bottlenecks

**Acceptance Criteria**:
1. ✅ **Execution Status Page**: User navigates to `/executions/{execution_id}` to see live status
2. ✅ **Progress Indicator**: UI shows visual progress bar (e.g., "3 of 5 agents completed")
3. ✅ **Current Step**: UI highlights currently executing agent
4. ✅ **Step Timing**: UI shows duration for each completed step
5. ✅ **Polling**: Frontend polls backend every 2-3 seconds for status updates (MVP approach)
6. ✅ **Auto-Refresh**: UI automatically updates without manual refresh
7. ✅ **Completion Notification**: UI shows success/failure banner when workflow completes

**UI Mockup**:
```
┌─────────────────────────────────────────────────────────────┐
│ Execution: exec-20251118-789                    [Refresh]   │
├─────────────────────────────────────────────────────────────┤
│ Status: ⏳ Running    Duration: 15.2s    Progress: 60%      │
│                                                             │
│ ✅ Step 1: Ticket Analyzer Agent            (2.3s)         │
│ ✅ Step 2: Customer Data Agent              (8.1s)         │
│ ⏳ Step 3: Solution Generator Agent          (running...)   │
│ ⏸️  Step 4: Email Notification Agent         (pending)      │
│ ⏸️  Step 5: Database Update Agent            (pending)      │
│                                                             │
│ [View Logs] [Stop Execution]                                │
└─────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] User can view real-time execution progress
- [ ] UI polls backend every 2-3 seconds for updates
- [ ] UI shows completed/running/pending status for each agent
- [ ] UI displays duration for completed steps
- [ ] UI automatically refreshes without user interaction

**Technical Notes**:
- MVP uses **polling** (frontend fetches `/api/executions/{id}` every 2-3s)
- Future enhancement (MVP2): Use **WebSocket** for true real-time updates
- Store step-level progress in `executions.result` JSONB field

---

### 1.3 Technical Implementation (Detailed)

#### 1.3.1 Workflow Engine Architecture

**High-Level Design**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Engine                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Workflow   │───→│   Agent      │───→│    State     │  │
│  │  Executor   │    │   Executor   │    │   Manager    │  │
│  └─────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                    │         │
│         │                   │                    │         │
│         ↓                   ↓                    ↓         │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Validation │    │   Context    │    │   Database   │  │
│  │  Engine     │    │   Manager    │    │   Logger     │  │
│  └─────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Core Components**:

1. **WorkflowExecutor**: Orchestrates entire workflow execution
2. **AgentExecutor**: Executes individual agents
3. **ContextManager**: Manages data flow between agents
4. **StateManager**: Persists execution state to database
5. **ValidationEngine**: Validates agent inputs/outputs against schemas

---

#### 1.3.2 Implementation Code (Python + FastAPI)

**1. Workflow Data Model**:
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class AgentConfig(BaseModel):
    """Configuration for a single agent in workflow"""
    agent_id: str = Field(..., description="Agent UUID")
    agent_name: str = Field(..., description="Human-readable agent name")
    order: int = Field(..., description="Execution order (1-based)")
    input_mapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="Map previous agent outputs to this agent's inputs"
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for validating agent output"
    )
    timeout_seconds: int = Field(default=300, description="Max execution time")
    retry_on_failure: bool = Field(default=False, description="Auto-retry on failure")
    max_retries: int = Field(default=0, description="Max retry attempts")

class WorkflowConfig(BaseModel):
    """Complete workflow configuration"""
    workflow_id: str
    workflow_name: str
    agents: List[AgentConfig] = Field(..., description="Ordered list of agents")
    global_timeout_seconds: int = Field(default=900, description="Max workflow time")
    stop_on_error: bool = Field(default=True, description="Stop on first error")
    save_checkpoints: bool = Field(default=False, description="Enable checkpointing (F2)")

class ExecutionStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"        # For checkpoints (F2)
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowExecution(BaseModel):
    """Workflow execution state"""
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    current_step: int = Field(default=0, description="Current agent index (0-based)")
    total_steps: int
    started_at: str          # ISO 8601 timestamp
    completed_at: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict, description="Shared context")
    results: Dict[str, Any] = Field(default_factory=dict, description="Per-agent results")
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
```

---

**2. Workflow Executor Class**:
```python
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    """
    Executes workflows with sequential agent orchestration
    """
    
    def __init__(
        self,
        db_session,
        agent_executor,
        state_manager,
        validation_engine,
        notification_service
    ):
        self.db = db_session
        self.agent_executor = agent_executor
        self.state_manager = state_manager
        self.validation_engine = validation_engine
        self.notification_service = notification_service
    
    async def execute_workflow(
        self,
        workflow_config: WorkflowConfig,
        initial_context: Dict[str, Any]
    ) -> WorkflowExecution:
        """
        Execute workflow with sequential agent orchestration
        
        Args:
            workflow_config: Workflow configuration
            initial_context: Initial input data
            
        Returns:
            WorkflowExecution: Final execution state
        """
        # 1. Initialize execution
        execution = self._initialize_execution(workflow_config, initial_context)
        
        try:
            # 2. Execute agents sequentially
            for agent_config in workflow_config.agents:
                execution.current_step = agent_config.order - 1
                
                # 2a. Update status in database
                await self.state_manager.update_execution_status(
                    execution.execution_id,
                    ExecutionStatus.RUNNING,
                    current_step=execution.current_step
                )
                
                # 2b. Prepare agent input
                agent_input = self._prepare_agent_input(
                    agent_config,
                    execution.context
                )
                
                # 2c. Validate input (if schema defined)
                if agent_config.output_schema:
                    self.validation_engine.validate(
                        agent_input,
                        agent_config.output_schema
                    )
                
                # 2d. Execute agent with timeout
                try:
                    agent_result = await asyncio.wait_for(
                        self.agent_executor.execute(
                            agent_config.agent_id,
                            agent_input
                        ),
                        timeout=agent_config.timeout_seconds
                    )
                except asyncio.TimeoutError:
                    raise Exception(
                        f"Agent '{agent_config.agent_name}' timed out "
                        f"after {agent_config.timeout_seconds}s"
                    )
                
                # 2e. Store agent result
                execution.results[agent_config.agent_name] = agent_result
                
                # 2f. Merge result into shared context
                execution.context.update(agent_result)
                
                # 2g. Log progress
                logger.info(
                    f"Workflow {execution.execution_id}: "
                    f"Completed step {agent_config.order}/{execution.total_steps} "
                    f"(Agent: {agent_config.agent_name})"
                )
            
            # 3. Mark as completed
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow().isoformat()
            
            # 4. Save final state
            await self.state_manager.save_execution(execution)
            
            logger.info(
                f"Workflow {execution.execution_id} completed successfully "
                f"in {self._calculate_duration(execution)}s"
            )
            
            return execution
            
        except Exception as e:
            # Handle failure
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow().isoformat()
            
            # Save failed state
            await self.state_manager.save_execution(execution)
            
            # Send notification
            await self.notification_service.send_failure_notification(
                execution,
                error=str(e)
            )
            
            logger.error(
                f"Workflow {execution.execution_id} failed at step "
                f"{execution.current_step + 1}: {e}",
                exc_info=True
            )
            
            # Re-raise if stop_on_error enabled
            if workflow_config.stop_on_error:
                raise
            
            return execution
    
    def _initialize_execution(
        self,
        workflow_config: WorkflowConfig,
        initial_context: Dict[str, Any]
    ) -> WorkflowExecution:
        """Initialize workflow execution state"""
        return WorkflowExecution(
            execution_id=f"exec-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8]}",
            workflow_id=workflow_config.workflow_id,
            status=ExecutionStatus.PENDING,
            current_step=0,
            total_steps=len(workflow_config.agents),
            started_at=datetime.utcnow().isoformat(),
            context=initial_context.copy(),
            results={},
            metadata={
                "workflow_name": workflow_config.workflow_name,
                "agent_count": len(workflow_config.agents)
            }
        )
    
    def _prepare_agent_input(
        self,
        agent_config: AgentConfig,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare input for agent from shared context
        
        Applies input_mapping if configured, otherwise passes full context
        """
        if agent_config.input_mapping:
            # Apply custom field mapping
            agent_input = {}
            for target_field, source_field in agent_config.input_mapping.items():
                if source_field in context:
                    agent_input[target_field] = context[source_field]
                else:
                    logger.warning(
                        f"Missing mapped field '{source_field}' in context "
                        f"for agent '{agent_config.agent_name}'"
                    )
            return agent_input
        else:
            # Pass full context
            return context.copy()
    
    def _calculate_duration(self, execution: WorkflowExecution) -> float:
        """Calculate execution duration in seconds"""
        if not execution.completed_at:
            return 0.0
        
        start = datetime.fromisoformat(execution.started_at)
        end = datetime.fromisoformat(execution.completed_at)
        return (end - start).total_seconds()
```

---

**3. API Endpoints**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    input_data: Dict[str, Any],
    workflow_executor: WorkflowExecutor = Depends(get_workflow_executor)
):
    """
    Execute a workflow
    
    **Request Body**:
    ```json
    {
      "ticket_id": "CS-1234",
      "priority": 3
    }
    ```
    
    **Response**:
    ```json
    {
      "execution_id": "exec-20251118-abc123",
      "status": "running",
      "message": "Workflow execution started"
    }
    ```
    """
    # 1. Load workflow configuration from database
    workflow_config = await load_workflow_config(workflow_id)
    if not workflow_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found"
        )
    
    # 2. Start async execution (non-blocking)
    execution = await workflow_executor.execute_workflow(
        workflow_config,
        initial_context=input_data
    )
    
    return {
        "execution_id": execution.execution_id,
        "status": execution.status.value,
        "message": "Workflow execution started",
        "current_step": execution.current_step,
        "total_steps": execution.total_steps
    }

@router.get("/{workflow_id}/executions/{execution_id}")
async def get_execution_status(
    workflow_id: str,
    execution_id: str,
    state_manager: StateManager = Depends(get_state_manager)
):
    """
    Get workflow execution status (for polling)
    
    **Response**:
    ```json
    {
      "execution_id": "exec-20251118-abc123",
      "status": "running",
      "current_step": 2,
      "total_steps": 5,
      "duration_seconds": 15.2,
      "results": {...}
    }
    ```
    """
    execution = await state_manager.get_execution(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found"
        )
    
    return {
        "execution_id": execution.execution_id,
        "workflow_id": execution.workflow_id,
        "status": execution.status.value,
        "current_step": execution.current_step,
        "total_steps": execution.total_steps,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "duration_seconds": _calculate_duration(execution),
        "results": execution.results if execution.status == ExecutionStatus.COMPLETED else {},
        "error": execution.error
    }

@router.post("/{workflow_id}/executions/{execution_id}/retry")
async def retry_execution(
    workflow_id: str,
    execution_id: str,
    workflow_executor: WorkflowExecutor = Depends(get_workflow_executor)
):
    """
    Retry failed workflow execution with same input
    
    **Response**:
    ```json
    {
      "new_execution_id": "exec-20251118-def456",
      "status": "running",
      "message": "Workflow retry started"
    }
    ```
    """
    # 1. Load original execution
    original_execution = await load_execution(execution_id)
    if not original_execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found"
        )
    
    # 2. Extract original input from context
    original_input = original_execution.context
    
    # 3. Start new execution
    workflow_config = await load_workflow_config(workflow_id)
    new_execution = await workflow_executor.execute_workflow(
        workflow_config,
        initial_context=original_input
    )
    
    return {
        "new_execution_id": new_execution.execution_id,
        "status": new_execution.status.value,
        "message": "Workflow retry started"
    }
```

---

### 1.4 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Sequential Orchestration Flow                     │
└─────────────────────────────────────────────────────────────────────┘

User Input
   │
   │ {"ticket_id": "CS-1234"}
   ↓
┌──────────────────────┐
│ Workflow Executor    │
│ - Load config        │
│ - Initialize state   │
└──────────┬───────────┘
           │
           │ Context: {"ticket_id": "CS-1234"}
           ↓
┌──────────────────────┐
│ Agent 1: Ticket      │───→ Save to DB
│ Analyzer             │    (executions table)
│ - Extract entities   │
│ - Classify priority  │
└──────────┬───────────┘
           │
           │ Context: {
           │   "ticket_id": "CS-1234",
           │   "priority": 3,
           │   "customer_id": "CUST-5678",
           │   "category": "billing"
           │ }
           ↓
┌──────────────────────┐
│ Agent 2: Customer    │───→ Query Dynamics 365
│ Data Retrieval       │───→ Query SharePoint
│ - Get customer 360   │───→ Query ServiceNow
└──────────┬───────────┘
           │
           │ Context: {
           │   ...(previous context),
           │   "customer_360": {
           │     "profile": {...},
           │     "purchase_history": [...],
           │     "support_history": [...]
           │   }
           │ }
           ↓
┌──────────────────────┐
│ Agent 3: Solution    │───→ Call GPT-4o
│ Generator            │
│ - Generate solution  │
└──────────┬───────────┘
           │
           │ Context: {
           │   ...(previous context),
           │   "solution": {
           │     "recommendation": "Process refund",
           │     "confidence": 0.92,
           │     "next_steps": [...]
           │   }
           │ }
           ↓
┌──────────────────────┐
│ Workflow Complete    │───→ Save final result
│ - Status: completed  │───→ Send notification
│ - Total time: 15.2s  │
└──────────────────────┘
```

---

### 1.5 Database Schema (Detailed)

**Executions Table** (from PRD Main Document):
```sql
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled')),
    current_step INT DEFAULT 0,
    total_steps INT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    context JSONB NOT NULL DEFAULT '{}',          -- Shared context between agents
    results JSONB NOT NULL DEFAULT '{}',          -- Per-agent results
    error TEXT,                                   -- Error message if failed
    llm_calls INT DEFAULT 0,                      -- Total LLM API calls
    llm_tokens INT DEFAULT 0,                     -- Total tokens used
    llm_cost DECIMAL(10, 4) DEFAULT 0.00,        -- Total cost in USD
    metadata JSONB DEFAULT '{}',                  -- Additional metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_started_at ON executions(started_at DESC);
CREATE INDEX idx_executions_context_gin ON executions USING GIN (context);
```

**Example Execution Record**:
```json
{
  "id": "exec-20251118-abc123",
  "workflow_id": "wf-it-ticket-triage",
  "status": "completed",
  "current_step": 3,
  "total_steps": 3,
  "started_at": "2025-11-18T14:30:00Z",
  "completed_at": "2025-11-18T14:30:15Z",
  "context": {
    "ticket_id": "CS-1234",
    "priority": 3,
    "customer_id": "CUST-5678",
    "customer_360": {...},
    "solution": {...}
  },
  "results": {
    "Ticket Analyzer Agent": {
      "ticket_id": "CS-1234",
      "priority": 3,
      "duration_ms": 2300
    },
    "Customer Data Agent": {
      "customer_360": {...},
      "duration_ms": 8100
    },
    "Solution Generator Agent": {
      "solution": {...},
      "duration_ms": 4800
    }
  },
  "error": null,
  "llm_calls": 2,
  "llm_tokens": 1250,
  "llm_cost": 0.0375,
  "metadata": {
    "workflow_name": "IT: Ticket Triage",
    "user_id": "user-alex-chen"
  }
}
```

---

### 1.6 UI Components

**1. Workflow Canvas (React Flow)**:
```tsx
import ReactFlow, { 
  Node, 
  Edge, 
  Controls, 
  Background 
} from 'reactflow';
import 'reactflow/dist/style.css';

interface AgentNode extends Node {
  data: {
    agentName: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    duration?: number;
    outputs?: Record<string, any>;
  };
}

export const WorkflowCanvas = ({ execution }: { execution: WorkflowExecution }) => {
  const nodes: AgentNode[] = execution.workflow.agents.map((agent, index) => ({
    id: agent.agent_id,
    type: 'default',
    position: { x: 250 * index, y: 100 },
    data: {
      agentName: agent.agent_name,
      status: getAgentStatus(execution, index),
      duration: execution.results[agent.agent_name]?.duration_ms,
      outputs: execution.results[agent.agent_name]
    }
  }));

  const edges: Edge[] = execution.workflow.agents.slice(0, -1).map((agent, index) => ({
    id: `${agent.agent_id}-${execution.workflow.agents[index + 1].agent_id}`,
    source: agent.agent_id,
    target: execution.workflow.agents[index + 1].agent_id,
    animated: execution.current_step === index + 1,
    style: { stroke: getEdgeColor(execution, index) }
  }));

  return (
    <div style={{ height: '500px' }}>
      <ReactFlow 
        nodes={nodes} 
        edges={edges}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};
```

---

### 1.7 Non-Functional Requirements (NFR)

| **Category** | **Requirement** | **Target** | **Measurement** |
|-------------|----------------|-----------|----------------|
| **Performance** | Workflow execution latency | P95 < 5 seconds (for 3-agent workflow) | Monitor via APM |
| | Agent transition overhead | < 100ms per transition | Database logging |
| | Context serialization | < 50ms for 10MB payload | Unit tests |
| **Scalability** | Max agents per workflow | 10 agents (MVP), 20 (future) | Hard limit in validation |
| | Concurrent workflows | 50+ executions simultaneously | Load testing |
| | Workflow complexity | Support nested workflows (future) | Design consideration |
| **Reliability** | Failure handling | 100% of errors caught and logged | Unit tests + monitoring |
| | Partial result preservation | 100% of successful agent outputs saved | Database constraints |
| | Transient error retry | 3 attempts with exponential backoff | Configuration |
| **Security** | Context data isolation | No cross-execution data leakage | Security audit |
| | Sensitive data handling | PII masked in logs | Logging middleware |
| **Usability** | Workflow creation time | < 5 minutes for 3-agent workflow | User testing |
| | Error message clarity | 90% of users understand error without support | User survey |
| **Observability** | Execution logging | 100% of executions logged | Database audit |
| | Performance metrics | P50, P95, P99 latency tracked | APM dashboard |
| | Error tracking | Error rate by agent type | Monitoring dashboard |
| **Maintainability** | Code coverage | > 80% for workflow engine | pytest-cov |
| | API documentation | 100% endpoints documented | OpenAPI spec |

---

### 1.8 Testing Strategy

#### **Unit Tests**:
```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_workflow_execution_success():
    """Test successful 3-agent workflow execution"""
    # Arrange
    workflow_config = WorkflowConfig(
        workflow_id="test-wf",
        workflow_name="Test Workflow",
        agents=[
            AgentConfig(agent_id="a1", agent_name="Agent 1", order=1),
            AgentConfig(agent_id="a2", agent_name="Agent 2", order=2),
            AgentConfig(agent_id="a3", agent_name="Agent 3", order=3)
        ]
    )
    
    agent_executor = AsyncMock()
    agent_executor.execute.side_effect = [
        {"result_a1": "data1"},
        {"result_a2": "data2"},
        {"result_a3": "data3"}
    ]
    
    executor = WorkflowExecutor(
        db_session=Mock(),
        agent_executor=agent_executor,
        state_manager=AsyncMock(),
        validation_engine=Mock(),
        notification_service=AsyncMock()
    )
    
    # Act
    execution = await executor.execute_workflow(
        workflow_config,
        initial_context={"input": "test"}
    )
    
    # Assert
    assert execution.status == ExecutionStatus.COMPLETED
    assert execution.current_step == 2
    assert "result_a1" in execution.context
    assert "result_a2" in execution.context
    assert "result_a3" in execution.context

@pytest.mark.asyncio
async def test_workflow_execution_failure():
    """Test workflow stops on agent failure"""
    # Arrange
    workflow_config = WorkflowConfig(
        workflow_id="test-wf",
        workflow_name="Test Workflow",
        agents=[
            AgentConfig(agent_id="a1", agent_name="Agent 1", order=1),
            AgentConfig(agent_id="a2", agent_name="Agent 2", order=2)
        ],
        stop_on_error=True
    )
    
    agent_executor = AsyncMock()
    agent_executor.execute.side_effect = [
        {"result_a1": "data1"},
        Exception("Agent 2 failed")
    ]
    
    executor = WorkflowExecutor(
        db_session=Mock(),
        agent_executor=agent_executor,
        state_manager=AsyncMock(),
        validation_engine=Mock(),
        notification_service=AsyncMock()
    )
    
    # Act & Assert
    with pytest.raises(Exception, match="Agent 2 failed"):
        await executor.execute_workflow(
            workflow_config,
            initial_context={"input": "test"}
        )
```

#### **Integration Tests**:
- Test end-to-end workflow execution with real agents
- Test database persistence and retrieval
- Test Teams notification delivery
- Test polling API endpoints

#### **Load Tests**:
- 50 concurrent workflow executions
- 10-agent workflows
- 10MB context payload

---

### 1.9 Risks and Mitigation

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|---------|----------------|-----------|---------------|
| Agent Framework API changes during preview | **Medium** | High | Implement adapter pattern, monitor GitHub releases |
| Agent execution timeout | Low | Medium | Implement configurable timeouts, auto-retry logic |
| Large context payload performance | Low | Medium | Implement payload size warnings, compression for >5MB |
| Database connection pool exhaustion | Low | High | Use connection pooling (50+ connections), monitor usage |
| Circular workflow dependencies | Low | Low | Implement cycle detection in validation engine |

---

### 1.10 Future Enhancements (Post-MVP)

1. **Parallel Agent Execution**: Execute independent agents simultaneously (US-F1-004)
2. **Conditional Branching**: Support if/else logic in workflows (e.g., "if priority > 3, route to Agent B")
3. **Sub-Workflows**: Nest workflows within workflows for modularity
4. **Workflow Templates**: Pre-built workflow templates in Marketplace (F6)
5. **Visual Debugging**: Step-through debugging in DevUI (F7)
6. **Workflow Versioning**: Git-like version control for workflows

---

**Next Feature**: [F2. Human-in-the-loop Checkpointing →](#f2-human-in-the-loop-checkpointing)

---

<a id="f2-human-in-the-loop-checkpointing"></a>
## F2. Human-in-the-loop Checkpointing

**Category**: Safety & Control  
**Priority**: P0 (Must Have - Critical Safety Feature)  
**Development Time**: 2 weeks  
**Complexity**: ⭐⭐⭐⭐ (High)  
**Dependencies**: F1 (Sequential Orchestration), PostgreSQL, Microsoft Teams, Redis (optional for caching)  
**Risk Level**: Medium (Approval timeout handling critical)

---

### 2.1 Feature Overview

**What is Human-in-the-loop Checkpointing?**

Human-in-the-loop (HITL) Checkpointing is a **critical safety mechanism** that pauses workflow execution at predefined decision points, requiring explicit human approval before allowing AI agents to proceed with high-risk actions. This ensures that humans remain in control of critical operations while still benefiting from AI automation.

**Why This Matters**:
- **Risk Mitigation**: Prevents AI from making irreversible mistakes (e.g., deleting production data, sending incorrect communications)
- **Compliance**: Meets regulatory requirements for human oversight in sensitive operations (GDPR, SOC 2, HIPAA)
- **Trust Building**: Allows gradual trust in AI by starting with manual approval and evolving to auto-approval as confidence grows
- **Learning Opportunity**: Captures human modifications to AI suggestions, enabling continuous improvement (F5)
- **Accountability**: Creates clear audit trail of who approved what action and when

**Key Capabilities**:
1. **Configurable Triggers**: Define checkpoint rules via YAML (risk level, operation type, data thresholds)
2. **Rich Context Display**: Show AI's proposed action, reasoning, confidence score, and relevant data
3. **Flexible Approval Actions**: Approve, reject, or modify parameters before proceeding
4. **Auto-Approval Rules**: Configure automatic approval for low-risk operations
5. **Timeout Handling**: Automatically escalate or cancel if approval not received within SLA
6. **Modification Tracking**: Record all human changes for learning (F5)

**Business Value**:
- **Safety**: Prevent $100K+ incidents from AI mistakes (e.g., wrong customer data deletion)
- **Compliance**: Pass audits by demonstrating human oversight controls
- **Gradual Adoption**: Start with 100% human approval, reduce to <30% as confidence builds
- **Continuous Improvement**: Learn from human corrections to improve AI accuracy
- **Peace of Mind**: Users can sleep well knowing critical actions require approval

**Real-World Example**:
```
CS Agent Workflow: Send Refund Email
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Analyze Ticket ✅ Completed                         │
│ Step 2: Calculate Refund Amount ✅ Completed ($99.99)       │
│ Step 3: Generate Email ✅ Completed                         │
│                                                             │
│ ⏸️  CHECKPOINT: High-Risk Operation Detected                │
│                                                             │
│ AI proposes:                                                │
│   Action: Send refund confirmation email                    │
│   Recipient: john@example.com                               │
│   Amount: $99.99                                            │
│   Confidence: 87%                                           │
│                                                             │
│ ⚠️  Requires approval because:                              │
│   • Risk Level: HIGH (involves money)                       │
│   • Operation Type: SEND_EMAIL                              │
│                                                             │
│ [Approve] [Modify] [Reject]                                 │
└─────────────────────────────────────────────────────────────┘
```

---

### 2.2 User Stories (Complete)

#### **US-F2-001: Configure Checkpoint Rules via YAML**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As an** IT Operations Admin (Alex Chen)
- **I want to** configure checkpoint rules using a simple YAML file
- **So that** I can define exactly when the system should pause for approval without writing code

**Acceptance Criteria**:
1. ✅ **YAML Configuration**: User can define checkpoint rules in YAML format
2. ✅ **Trigger Conditions**: Support multiple trigger types:
   - `risk_level`: "low", "medium", "high", "critical"
   - `operation_type`: ["delete", "send_email", "modify_critical", "financial_transaction", "external_api_call"]
   - `data_threshold`: Numeric conditions (e.g., amount > 1000)
   - `agent_confidence`: Threshold below which approval required (e.g., < 0.8)
   - `custom_field`: Any field in execution context
3. ✅ **Auto-Approval Rules**: Configure when to skip human approval
4. ✅ **Timeout Configuration**: Set approval timeout with escalation behavior
5. ✅ **Notification Settings**: Configure who gets notified (email, Teams, Slack)
6. ✅ **Schema Validation**: System validates YAML syntax on save
7. ✅ **Hot Reload**: Changes take effect without restarting system (within 30s)
8. ✅ **Rule Priority**: Support multiple rules with priority order (first match wins)

**YAML Configuration Schema**:
```yaml
# checkpoint-rules.yaml
version: "1.0"
checkpoints:
  # Rule 1: Critical financial transactions
  - name: "High-Value Financial Operations"
    priority: 1
    trigger:
      risk_level: ["high", "critical"]
      operation_type: ["financial_transaction", "refund"]
      data_threshold:
        field: "amount"
        operator: ">"
        value: 1000
    action:
      auto_approve: false
      require_approval_count: 2  # Require 2 approvals
      timeout_seconds: 3600      # 1 hour
      escalation:
        enabled: true
        after_seconds: 1800      # Escalate after 30 min
        escalate_to: ["manager@example.com"]
      notification:
        channels: ["teams", "email"]
        recipients: ["finance-team@example.com"]
    
  # Rule 2: Data deletion operations
  - name: "Data Deletion Safety"
    priority: 2
    trigger:
      operation_type: ["delete", "drop_table", "truncate"]
      risk_level: ["high", "critical"]
    action:
      auto_approve: false
      timeout_seconds: 7200      # 2 hours
      on_timeout: "cancel"       # Cancel workflow if no approval
      notification:
        channels: ["teams"]
        recipients: ["admin@example.com"]
  
  # Rule 3: Low-confidence AI decisions
  - name: "Low Confidence Decisions"
    priority: 3
    trigger:
      agent_confidence:
        operator: "<"
        value: 0.75
    action:
      auto_approve: false
      timeout_seconds: 1800
      notification:
        channels: ["teams"]
  
  # Rule 4: Auto-approve low-risk operations
  - name: "Auto-Approve Safe Operations"
    priority: 10
    trigger:
      risk_level: ["low"]
      operation_type: ["read", "query", "search"]
    action:
      auto_approve: true
      log_decision: true         # Still log for audit
```

**Definition of Done**:
- [ ] User can create/edit checkpoint rules in YAML format
- [ ] System validates YAML syntax and shows clear error messages
- [ ] All trigger types work correctly (risk_level, operation_type, data_threshold, confidence)
- [ ] Auto-approval rules work as expected
- [ ] Timeout and escalation behavior works correctly
- [ ] Changes take effect within 30 seconds (hot reload)
- [ ] Unit tests cover all trigger combinations

**Technical Notes**:
- Store YAML in `workflows.trigger_config` JSONB field
- Use PyYAML for parsing
- Implement rule matching engine with priority ordering
- Cache parsed rules in Redis for performance

---

#### **US-F2-002: Approve or Reject Checkpoint with Rich Context**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 4 days  
**Complexity**: ⭐⭐⭐⭐

**User Story**:
- **As an** IT Operations Admin (Alex Chen)
- **I want to** see complete context about what the AI is proposing to do, including data, reasoning, and confidence score
- **So that** I can make an informed decision to approve or reject the action

**Acceptance Criteria**:
1. ✅ **Real-time Notification**: User receives Teams notification within 5 seconds of checkpoint creation
2. ✅ **Context Display**: Approval page shows:
   - Workflow name and execution ID
   - Current step description
   - AI's proposed action (structured display)
   - AI's reasoning (why this action)
   - Confidence score (0-100%)
   - Relevant data (customer info, ticket details, etc.)
   - Risk assessment (why approval required)
   - Previous execution history (if available)
3. ✅ **Approve Action**: User clicks "Approve" → workflow resumes immediately
4. ✅ **Reject Action**: User clicks "Reject" → workflow terminates, user enters rejection reason
5. ✅ **Pending List**: User sees list of all pending approvals (sortable by priority, age)
6. ✅ **Approval SLA**: UI shows time remaining before timeout
7. ✅ **Mobile Friendly**: Approval page works on mobile devices
8. ✅ **Audit Trail**: All approval decisions logged to `audit_logs` table

**Approval Page UI Mockup**:
```
┌────────────────────────────────────────────────────────────────────┐
│ Checkpoint Approval: exec-20251118-abc123                   [Back] │
├────────────────────────────────────────────────────────────────────┤
│ Workflow: CS - Send Refund Email                                   │
│ Status: ⏸️  Waiting for Approval                                   │
│ Time Remaining: ⏱️  52 minutes                                      │
│                                                                    │
│ ╔══════════════════════════════════════════════════════════════╗  │
│ ║ 🤖 AI Proposed Action                                        ║  │
│ ╚══════════════════════════════════════════════════════════════╝  │
│                                                                    │
│ Operation: Send Email                                              │
│ Confidence: 87% ████████░░                                         │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────┐   │
│ │ Email Details:                                              │   │
│ │   To: john.doe@example.com                                 │   │
│ │   Subject: Refund Confirmation - Order #12345              │   │
│ │   Amount: $99.99                                            │   │
│ │   Template: refund_confirmation_v2                          │   │
│ │                                                             │   │
│ │ Attachments:                                                │   │
│ │   • refund_receipt.pdf (45KB)                              │   │
│ └────────────────────────────────────────────────────────────┘   │
│                                                                    │
│ ╔══════════════════════════════════════════════════════════════╗  │
│ ║ 💭 AI Reasoning                                              ║  │
│ ╚══════════════════════════════════════════════════════════════╝  │
│                                                                    │
│ "Based on ticket CS-1234 analysis, customer requested refund      │
│  for defective product (Order #12345). Purchase confirmed in      │
│  Dynamics 365. Customer has 3-year positive history (15 orders,   │
│  no previous refunds). Refund amount matches order total.          │
│  Email template verified against company policy."                  │
│                                                                    │
│ ╔══════════════════════════════════════════════════════════════╗  │
│ ║ ⚠️  Risk Assessment                                          ║  │
│ ╚══════════════════════════════════════════════════════════════╝  │
│                                                                    │
│ Risk Level: HIGH                                                   │
│ Reasons:                                                           │
│   • Financial transaction (>$50)                                   │
│   • External communication (email)                                 │
│   • Irreversible action                                            │
│                                                                    │
│ ╔══════════════════════════════════════════════════════════════╗  │
│ ║ 📊 Supporting Data                                           ║  │
│ ╚══════════════════════════════════════════════════════════════╝  │
│                                                                    │
│ Customer: John Doe (CUST-5678)                                     │
│   • Total Orders: 15 ($1,247.50)                                   │
│   • Previous Refunds: 0                                            │
│   • Account Age: 3 years                                           │
│   • Support Tickets: 2 (both resolved)                             │
│                                                                    │
│ Order #12345:                                                      │
│   • Date: 2025-11-10                                               │
│   • Product: Wireless Headphones                                   │
│   • Amount: $99.99                                                 │
│   • Status: Delivered 2025-11-12                                   │
│                                                                    │
│ ╔══════════════════════════════════════════════════════════════╗  │
│ ║ 🕐 Execution History                                         ║  │
│ ╚══════════════════════════════════════════════════════════════╝  │
│                                                                    │
│ ✅ Step 1: Ticket Analyzer (2.3s)                                  │
│ ✅ Step 2: Customer 360 Query (8.1s)                               │
│ ✅ Step 3: Refund Calculator (1.5s)                                │
│ ✅ Step 4: Email Generator (3.2s)                                  │
│ ⏸️  Step 5: Send Email (waiting for approval)                      │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────┐   │
│ │ 💬 Add Comment (Optional)                                   │   │
│ │ ┌──────────────────────────────────────────────────────┐   │   │
│ │ │ e.g., "Verified with customer service policy"         │   │   │
│ │ └──────────────────────────────────────────────────────┘   │   │
│ └────────────────────────────────────────────────────────────┘   │
│                                                                    │
│ [✅ Approve]  [✏️  Modify Parameters]  [❌ Reject]                  │
│                                                                    │
│ Approved by you will resume workflow immediately.                  │
└────────────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] User receives Teams notification within 5 seconds
- [ ] Approval page displays all required context (action, reasoning, confidence, data, risk)
- [ ] User can approve with optional comment
- [ ] User can reject with required reason
- [ ] Workflow resumes within 2 seconds after approval
- [ ] All decisions logged to audit_logs table
- [ ] UI works on mobile (responsive design)

**Technical Notes**:
- Use **Shadcn UI** components (Card, Badge, Button, Textarea)
- Store checkpoint in `checkpoints` table with status="pending"
- Send Teams notification via Incoming Webhook
- Use polling (2-3s) for real-time status updates in UI

---

#### **US-F2-003: Modify AI Parameters Before Approval**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐⭐

**User Story**:
- **As a** CS Team Lead (Sarah Martinez)
- **I want to** modify the AI's proposed parameters before approving (e.g., change email recipient, adjust refund amount)
- **So that** I can correct AI mistakes without rejecting and restarting the entire workflow

**Acceptance Criteria**:
1. ✅ **Modify Button**: User clicks "Modify Parameters" on approval page
2. ✅ **Dynamic Form**: System generates editable form based on action type:
   - **Send Email**: Edit recipient, subject, body, attachments
   - **Financial Transaction**: Edit amount, currency, account
   - **Database Update**: Edit field values
   - **API Call**: Edit request parameters
3. ✅ **JSON Editor**: For complex parameters, show JSON editor with syntax highlighting (Monaco Editor)
4. ✅ **Field Validation**: Validate modified values (e.g., email format, amount > 0)
5. ✅ **Preview Changes**: Show diff of original vs modified parameters
6. ✅ **Save & Approve**: User submits modifications → workflow resumes with new parameters
7. ✅ **Learning Capture**: System records modification as learning case (F5)
8. ✅ **Audit Trail**: Log original and modified values to audit_logs

**Modification Modal UI**:
```
┌────────────────────────────────────────────────────────────────┐
│ Modify Parameters                                      [Close] │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ 📝 Edit Email Parameters                                       │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐│
│ │ To (Email Address) *                                       ││
│ │ ┌──────────────────────────────────────────────────────┐  ││
│ │ │ john.doe@example.com                                  │  ││
│ │ └──────────────────────────────────────────────────────┘  ││
│ │                                                            ││
│ │ Subject *                                                  ││
│ │ ┌──────────────────────────────────────────────────────┐  ││
│ │ │ Refund Confirmation - Order #12345                    │  ││
│ │ └──────────────────────────────────────────────────────┘  ││
│ │                                                            ││
│ │ Amount (USD) *                                             ││
│ │ ┌──────────────────────────────────────────────────────┐  ││
│ │ │ 99.99                                                  │  ││
│ │ └──────────────────────────────────────────────────────┘  ││
│ │                                                            ││
│ │ Email Body                                                 ││
│ │ ┌──────────────────────────────────────────────────────┐  ││
│ │ │ Dear John,                                            │  ││
│ │ │                                                       │  ││
│ │ │ Your refund of $99.99 has been processed for Order   │  ││
│ │ │ #12345. Please allow 5-7 business days...            │  ││
│ │ └──────────────────────────────────────────────────────┘  ││
│ └────────────────────────────────────────────────────────────┘│
│                                                                │
│ ╔══════════════════════════════════════════════════════════╗  │
│ ║ Advanced: JSON Editor (Optional)                         ║  │
│ ╚══════════════════════════════════════════════════════════╝  │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐│
│ │ {                                                          ││
│ │   "to": "john.doe@example.com",                           ││
│ │   "subject": "Refund Confirmation - Order #12345",        ││
│ │   "amount": 99.99,                                         ││
│ │   "currency": "USD",                                       ││
│ │   "template": "refund_confirmation_v2",                   ││
│ │   "attachments": ["refund_receipt.pdf"]                   ││
│ │ }                                                          ││
│ └────────────────────────────────────────────────────────────┘│
│                                                                │
│ ⚠️  Changes will be saved as a learning case for AI improvement│
│                                                                │
│ [Preview Changes]  [Cancel]  [Save & Approve]                 │
└────────────────────────────────────────────────────────────────┘
```

**Parameter Diff Preview**:
```
┌────────────────────────────────────────────────────────────────┐
│ Review Changes                                         [Back]  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ 📝 Parameter Changes                                           │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐│
│ │ Field: amount                                              ││
│ │   Original:  99.99                                         ││
│ │   Modified:  89.99  (↓ $10.00)                            ││
│ │                                                            ││
│ │ Field: subject                                             ││
│ │   Original:  Refund Confirmation - Order #12345           ││
│ │   Modified:  URGENT: Refund Confirmation - Order #12345   ││
│ │              (↑ Added "URGENT:")                           ││
│ └────────────────────────────────────────────────────────────┘│
│                                                                │
│ ✅ All changes validated successfully                          │
│                                                                │
│ 💡 These changes will be recorded as a learning case to help  │
│    the AI make better suggestions in the future.              │
│                                                                │
│ [Go Back]  [Confirm & Approve]                                │
└────────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] User can click "Modify Parameters" button
- [ ] System generates dynamic form based on action type
- [ ] User can edit parameters in form or JSON editor
- [ ] System validates modified values (type, format, constraints)
- [ ] User can preview changes (original vs modified)
- [ ] Modified parameters passed to agent on approval
- [ ] Modification recorded as learning case in database
- [ ] Audit log shows original and modified values

**Technical Notes**:
- Use **Shadcn UI Form** components with **React Hook Form** for validation
- Use **Monaco Editor** for JSON editing (same as VS Code)
- Implement JSON Schema validation for complex parameters
- Store modifications in `learning_cases` table (F5)

---

#### **US-F2-004: Configure Auto-Approval Rules**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** System Admin (Michael Wong)
- **I want to** configure automatic approval for low-risk operations that meet specific criteria
- **So that** I can reduce manual approval overhead while maintaining safety controls

**Acceptance Criteria**:
1. ✅ **Auto-Approval Configuration**: Admin can enable/disable auto-approval per rule
2. ✅ **Condition-Based**: Support complex conditions (e.g., "auto-approve if risk=low AND confidence>0.9 AND amount<$50")
3. ✅ **Time-Based**: Auto-approve during business hours only (optional)
4. ✅ **Gradual Rollout**: Start with 0% auto-approval, increase to target % over time
5. ✅ **Override**: Manual approval always takes precedence over auto-approval
6. ✅ **Audit Trail**: All auto-approvals logged with decision reasoning
7. ✅ **Monitoring**: Dashboard shows auto-approval rate and accuracy
8. ✅ **Emergency Stop**: Admin can disable all auto-approval with one click

**Auto-Approval Configuration Example**:
```yaml
# Auto-Approval Rules
auto_approval:
  enabled: true
  global_settings:
    business_hours_only: true
    business_hours:
      timezone: "America/New_York"
      monday_friday: "09:00-17:00"
      saturday_sunday: "disabled"
    emergency_stop: false  # Admin can set to true to disable all
  
  rules:
    # Rule 1: Low-risk read operations
    - name: "Auto-Approve Safe Reads"
      enabled: true
      conditions:
        risk_level: "low"
        operation_type: ["read", "query", "search"]
        confidence: ">= 0.8"
      action:
        auto_approve: true
        log_decision: true
        notify: false  # Don't send notification
    
    # Rule 2: Small financial transactions
    - name: "Auto-Approve Small Refunds"
      enabled: true
      conditions:
        risk_level: ["low", "medium"]
        operation_type: "financial_transaction"
        data_threshold:
          field: "amount"
          operator: "<="
          value: 50
        confidence: ">= 0.9"
      action:
        auto_approve: true
        log_decision: true
        notify: true  # Send notification after auto-approval
        notification_channels: ["teams"]
    
    # Rule 3: Gradual rollout for email operations
    - name: "Gradual Auto-Approve Emails"
      enabled: true
      conditions:
        operation_type: "send_email"
        risk_level: "low"
        confidence: ">= 0.85"
      action:
        auto_approve: true
        rollout_percentage: 25  # Auto-approve 25% of qualifying ops
        log_decision: true
```

**Auto-Approval Notification Example**:
```
🤖 Auto-Approved Checkpoint
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workflow: CS - Send Refund Email
Execution: exec-20251118-xyz789

✅ Automatically approved (no manual action required)

Reason: Matches auto-approval rule "Auto-Approve Small Refunds"
  • Risk Level: LOW ✓
  • Operation: financial_transaction ✓
  • Amount: $35.00 ✓ (< $50)
  • Confidence: 92% ✓ (>= 90%)

Action Taken: Sent refund confirmation email to customer

[View Details] [Disable Auto-Approval]
```

**Definition of Done**:
- [ ] Admin can configure auto-approval rules via YAML
- [ ] System evaluates conditions correctly (risk, confidence, thresholds)
- [ ] Auto-approval respects business hours (if configured)
- [ ] All auto-approvals logged to audit_logs with reasoning
- [ ] Dashboard shows auto-approval rate and errors
- [ ] Admin can emergency-stop all auto-approval

**Technical Notes**:
- Evaluate auto-approval rules before creating checkpoint
- Store auto-approval decision in `checkpoints.metadata` JSONB
- Implement A/B testing framework for gradual rollout

---

### 2.3 Technical Implementation (Detailed)

#### 2.3.1 StateManager Class (Complete)

```python
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio

class CheckpointStatus(str, Enum):
    """Checkpoint approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"

class StateManager:
    """
    Manages workflow checkpoints and approvals
    """
    
    def __init__(self, db_session, notification_service, learning_service):
        self.db = db_session
        self.notification_service = notification_service
        self.learning_service = learning_service
    
    async def save_checkpoint(
        self,
        execution_id: str,
        step: int,
        state: Dict[str, Any],
        proposed_action: Dict[str, Any],
        reasoning: str,
        confidence: float,
        risk_level: str,
        timeout_seconds: int = 3600
    ) -> str:
        """
        Save workflow checkpoint and pause execution
        
        Args:
            execution_id: Execution UUID
            step: Current workflow step (0-based)
            state: Complete workflow context/state
            proposed_action: AI's proposed action details
            reasoning: AI's reasoning for this action
            confidence: AI confidence score (0.0-1.0)
            risk_level: Risk assessment ("low", "medium", "high", "critical")
            timeout_seconds: Approval timeout (default 1 hour)
            
        Returns:
            checkpoint_id: Created checkpoint UUID
        """
        # 1. Create checkpoint record
        checkpoint_id = f"chkpt-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8]}"
        timeout_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
        
        checkpoint_data = {
            "id": checkpoint_id,
            "execution_id": execution_id,
            "step": step,
            "state": state,
            "proposed_action": proposed_action,
            "reasoning": reasoning,
            "confidence": confidence,
            "risk_level": risk_level,
            "status": CheckpointStatus.PENDING,
            "timeout_at": timeout_at.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "original_action": proposed_action.copy(),  # Preserve original
                "notification_sent": False
            }
        }
        
        # 2. Insert into database
        await self.db.execute(
            """
            INSERT INTO checkpoints (
                id, execution_id, step, state, status, 
                approved_by, approved_at, feedback, created_at
            ) VALUES (
                :id, :execution_id, :step, :state, :status,
                NULL, NULL, NULL, :created_at
            )
            """,
            {
                "id": checkpoint_id,
                "execution_id": execution_id,
                "step": step,
                "state": json.dumps(checkpoint_data),
                "status": CheckpointStatus.PENDING.value,
                "created_at": checkpoint_data["created_at"]
            }
        )
        await self.db.commit()
        
        # 3. Update execution status to 'paused'
        await self.db.execute(
            """
            UPDATE executions
            SET status = 'paused', updated_at = :updated_at
            WHERE id = :execution_id
            """,
            {
                "execution_id": execution_id,
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        await self.db.commit()
        
        # 4. Send Teams notification
        await self.notification_service.send_checkpoint_notification(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            proposed_action=proposed_action,
            reasoning=reasoning,
            confidence=confidence,
            risk_level=risk_level,
            timeout_at=timeout_at
        )
        
        # 5. Start timeout monitoring (async task)
        asyncio.create_task(
            self._monitor_checkpoint_timeout(checkpoint_id, timeout_seconds)
        )
        
        logger.info(
            f"Checkpoint {checkpoint_id} created for execution {execution_id} "
            f"(step {step}, timeout: {timeout_seconds}s)"
        )
        
        return checkpoint_id
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint data for display/approval
        
        Returns:
            Checkpoint data dict or None if not found
        """
        result = await self.db.execute(
            """
            SELECT id, execution_id, step, state, status, 
                   approved_by, approved_at, feedback, created_at
            FROM checkpoints
            WHERE id = :checkpoint_id
            """,
            {"checkpoint_id": checkpoint_id}
        )
        row = await result.fetchone()
        
        if not row:
            return None
        
        checkpoint_data = json.loads(row["state"])
        return {
            "id": row["id"],
            "execution_id": row["execution_id"],
            "step": row["step"],
            "status": row["status"],
            "approved_by": row["approved_by"],
            "approved_at": row["approved_at"],
            "feedback": row["feedback"],
            "created_at": row["created_at"],
            **checkpoint_data  # Merge state data
        }
    
    async def approve_checkpoint(
        self,
        checkpoint_id: str,
        approved_by: str,
        modified_params: Optional[Dict[str, Any]] = None,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Approve checkpoint and resume workflow
        
        Args:
            checkpoint_id: Checkpoint UUID
            approved_by: User ID who approved
            modified_params: Modified parameters (if any)
            feedback: Optional approval comment
            
        Returns:
            True if successful, False if checkpoint expired/invalid
        """
        # 1. Load checkpoint
        checkpoint = await self.load_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        # 2. Validate status
        if checkpoint["status"] != CheckpointStatus.PENDING.value:
            logger.warning(
                f"Cannot approve checkpoint {checkpoint_id}: "
                f"status is {checkpoint['status']}"
            )
            return False
        
        # 3. Check if timed out
        timeout_at = datetime.fromisoformat(checkpoint["timeout_at"])
        if datetime.utcnow() > timeout_at:
            await self._handle_checkpoint_timeout(checkpoint_id)
            return False
        
        # 4. Update checkpoint status
        await self.db.execute(
            """
            UPDATE checkpoints
            SET status = 'approved',
                approved_by = :approved_by,
                approved_at = :approved_at,
                feedback = :feedback,
                state = :state
            WHERE id = :checkpoint_id
            """,
            {
                "checkpoint_id": checkpoint_id,
                "approved_by": approved_by,
                "approved_at": datetime.utcnow().isoformat(),
                "feedback": feedback,
                "state": json.dumps({
                    **checkpoint,
                    "modified_params": modified_params,
                    "status": CheckpointStatus.APPROVED.value
                })
            }
        )
        await self.db.commit()
        
        # 5. Record learning case if parameters modified
        if modified_params:
            await self.learning_service.record_learning_case(
                execution_id=checkpoint["execution_id"],
                scenario=checkpoint["proposed_action"].get("operation_type"),
                original_action=checkpoint["proposed_action"],
                human_modified_action=modified_params,
                feedback=feedback
            )
            
            logger.info(
                f"Recorded learning case for checkpoint {checkpoint_id}: "
                f"User modified parameters"
            )
        
        # 6. Update execution status to 'running'
        await self.db.execute(
            """
            UPDATE executions
            SET status = 'running', updated_at = :updated_at
            WHERE id = :execution_id
            """,
            {
                "execution_id": checkpoint["execution_id"],
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        await self.db.commit()
        
        # 7. Resume workflow execution
        await self._resume_workflow(
            checkpoint["execution_id"],
            modified_params or checkpoint["proposed_action"]
        )
        
        logger.info(
            f"Checkpoint {checkpoint_id} approved by {approved_by}. "
            f"Workflow {checkpoint['execution_id']} resumed."
        )
        
        return True
    
    async def reject_checkpoint(
        self,
        checkpoint_id: str,
        rejected_by: str,
        reason: str
    ) -> bool:
        """
        Reject checkpoint and terminate workflow
        
        Args:
            checkpoint_id: Checkpoint UUID
            rejected_by: User ID who rejected
            reason: Rejection reason (required)
            
        Returns:
            True if successful
        """
        # 1. Update checkpoint status
        await self.db.execute(
            """
            UPDATE checkpoints
            SET status = 'rejected',
                approved_by = :rejected_by,
                approved_at = :rejected_at,
                feedback = :reason
            WHERE id = :checkpoint_id
            """,
            {
                "checkpoint_id": checkpoint_id,
                "rejected_by": rejected_by,
                "rejected_at": datetime.utcnow().isoformat(),
                "reason": reason
            }
        )
        await self.db.commit()
        
        # 2. Load checkpoint to get execution_id
        checkpoint = await self.load_checkpoint(checkpoint_id)
        
        # 3. Update execution status to 'failed'
        await self.db.execute(
            """
            UPDATE executions
            SET status = 'failed',
                error = :error,
                completed_at = :completed_at
            WHERE id = :execution_id
            """,
            {
                "execution_id": checkpoint["execution_id"],
                "error": f"Checkpoint rejected by {rejected_by}: {reason}",
                "completed_at": datetime.utcnow().isoformat()
            }
        )
        await self.db.commit()
        
        # 4. Send rejection notification
        await self.notification_service.send_rejection_notification(
            execution_id=checkpoint["execution_id"],
            rejected_by=rejected_by,
            reason=reason
        )
        
        logger.info(
            f"Checkpoint {checkpoint_id} rejected by {rejected_by}. "
            f"Workflow {checkpoint['execution_id']} terminated."
        )
        
        return True
    
    async def _monitor_checkpoint_timeout(
        self,
        checkpoint_id: str,
        timeout_seconds: int
    ):
        """
        Monitor checkpoint and handle timeout
        
        Runs as async background task
        """
        await asyncio.sleep(timeout_seconds)
        
        # Check if checkpoint still pending
        checkpoint = await self.load_checkpoint(checkpoint_id)
        if checkpoint and checkpoint["status"] == CheckpointStatus.PENDING.value:
            await self._handle_checkpoint_timeout(checkpoint_id)
    
    async def _handle_checkpoint_timeout(self, checkpoint_id: str):
        """Handle checkpoint approval timeout"""
        checkpoint = await self.load_checkpoint(checkpoint_id)
        
        # Update checkpoint status
        await self.db.execute(
            """
            UPDATE checkpoints
            SET status = 'timeout',
                approved_at = :timeout_at,
                feedback = 'Approval timeout exceeded'
            WHERE id = :checkpoint_id
            """,
            {
                "checkpoint_id": checkpoint_id,
                "timeout_at": datetime.utcnow().isoformat()
            }
        )
        await self.db.commit()
        
        # Update execution status to 'failed'
        await self.db.execute(
            """
            UPDATE executions
            SET status = 'failed',
                error = 'Checkpoint approval timeout',
                completed_at = :completed_at
            WHERE id = :execution_id
            """,
            {
                "execution_id": checkpoint["execution_id"],
                "completed_at": datetime.utcnow().isoformat()
            }
        )
        await self.db.commit()
        
        # Send timeout notification
        await self.notification_service.send_timeout_notification(
            checkpoint_id=checkpoint_id,
            execution_id=checkpoint["execution_id"]
        )
        
        logger.warning(
            f"Checkpoint {checkpoint_id} timed out. "
            f"Workflow {checkpoint['execution_id']} terminated."
        )
    
    async def _resume_workflow(
        self,
        execution_id: str,
        approved_params: Dict[str, Any]
    ):
        """
        Resume workflow execution after approval
        
        Sends message to workflow engine to continue
        """
        # Implementation depends on workflow engine architecture
        # Could use message queue, direct function call, or event bus
        pass
    
    async def list_pending_checkpoints(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List all pending checkpoints (for approval dashboard)
        
        Args:
            user_id: Filter by assigned user (optional)
            limit: Max results (default 50)
            
        Returns:
            List of checkpoint dicts
        """
        query = """
            SELECT c.id, c.execution_id, c.step, c.state, c.created_at,
                   e.workflow_id, w.name as workflow_name
            FROM checkpoints c
            JOIN executions e ON c.execution_id = e.id
            JOIN workflows w ON e.workflow_id = w.id
            WHERE c.status = 'pending'
            ORDER BY c.created_at DESC
            LIMIT :limit
        """
        
        result = await self.db.execute(query, {"limit": limit})
        rows = await result.fetchall()
        
        return [
            {
                "id": row["id"],
                "execution_id": row["execution_id"],
                "workflow_id": row["workflow_id"],
                "workflow_name": row["workflow_name"],
                "step": row["step"],
                "created_at": row["created_at"],
                **json.loads(row["state"])
            }
            for row in rows
        ]
```

---

### 2.4 API Endpoints (Complete)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])

class ApproveCheckpointRequest(BaseModel):
    """Request body for checkpoint approval"""
    approved_by: str = Field(..., description="User ID approving")
    modified_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Modified parameters (if any)"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Optional approval comment"
    )

class RejectCheckpointRequest(BaseModel):
    """Request body for checkpoint rejection"""
    rejected_by: str = Field(..., description="User ID rejecting")
    reason: str = Field(..., description="Rejection reason (required)")

@router.get("")
async def list_pending_checkpoints(
    limit: int = 50,
    state_manager: StateManager = Depends(get_state_manager)
):
    """
    List all pending checkpoints
    
    **Response**:
    ```json
    {
      "checkpoints": [
        {
          "id": "chkpt-20251118-abc123",
          "execution_id": "exec-20251118-xyz789",
          "workflow_name": "CS - Send Refund Email",
          "step": 4,
          "proposed_action": {...},
          "risk_level": "high",
          "confidence": 0.87,
          "created_at": "2025-11-18T14:30:00Z",
          "timeout_at": "2025-11-18T15:30:00Z"
        }
      ],
      "total": 3
    }
    ```
    """
    checkpoints = await state_manager.list_pending_checkpoints(limit=limit)
    
    return {
        "checkpoints": checkpoints,
        "total": len(checkpoints)
    }

@router.get("/{checkpoint_id}")
async def get_checkpoint_detail(
    checkpoint_id: str,
    state_manager: StateManager = Depends(get_state_manager)
):
    """
    Get detailed checkpoint information for approval page
    
    **Response**: Complete checkpoint data including context
    """
    checkpoint = await state_manager.load_checkpoint(checkpoint_id)
    
    if not checkpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{checkpoint_id}' not found"
        )
    
    return checkpoint

@router.put("/{checkpoint_id}/approve")
async def approve_checkpoint(
    checkpoint_id: str,
    request: ApproveCheckpointRequest,
    state_manager: StateManager = Depends(get_state_manager)
):
    """
    Approve checkpoint (with optional parameter modifications)
    
    **Request Body**:
    ```json
    {
      "approved_by": "user-alex-chen",
      "modified_params": {
        "amount": 89.99,
        "subject": "URGENT: Refund Confirmation"
      },
      "feedback": "Reduced amount by $10 per policy"
    }
    ```
    
    **Response**:
    ```json
    {
      "message": "Checkpoint approved successfully",
      "checkpoint_id": "chkpt-20251118-abc123",
      "execution_id": "exec-20251118-xyz789",
      "workflow_resumed": true
    }
    ```
    """
    success = await state_manager.approve_checkpoint(
        checkpoint_id=checkpoint_id,
        approved_by=request.approved_by,
        modified_params=request.modified_params,
        feedback=request.feedback
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkpoint cannot be approved (may be expired or already processed)"
        )
    
    checkpoint = await state_manager.load_checkpoint(checkpoint_id)
    
    return {
        "message": "Checkpoint approved successfully",
        "checkpoint_id": checkpoint_id,
        "execution_id": checkpoint["execution_id"],
        "workflow_resumed": True
    }

@router.put("/{checkpoint_id}/reject")
async def reject_checkpoint(
    checkpoint_id: str,
    request: RejectCheckpointRequest,
    state_manager: StateManager = Depends(get_state_manager)
):
    """
    Reject checkpoint and terminate workflow
    
    **Request Body**:
    ```json
    {
      "rejected_by": "user-alex-chen",
      "reason": "Refund amount exceeds policy limit"
    }
    ```
    
    **Response**:
    ```json
    {
      "message": "Checkpoint rejected",
      "checkpoint_id": "chkpt-20251118-abc123",
      "execution_id": "exec-20251118-xyz789",
      "workflow_terminated": true
    }
    ```
    """
    success = await state_manager.reject_checkpoint(
        checkpoint_id=checkpoint_id,
        rejected_by=request.rejected_by,
        reason=request.reason
    )
    
    checkpoint = await state_manager.load_checkpoint(checkpoint_id)
    
    return {
        "message": "Checkpoint rejected",
        "checkpoint_id": checkpoint_id,
        "execution_id": checkpoint["execution_id"],
        "workflow_terminated": True
    }

@router.put("/{checkpoint_id}/modify")
async def modify_checkpoint_params(
    checkpoint_id: str,
    modified_params: Dict[str, Any],
    state_manager: StateManager = Depends(get_state_manager)
):
    """
    Preview parameter modifications (without approving)
    
    **Response**: Diff of original vs modified parameters
    """
    checkpoint = await state_manager.load_checkpoint(checkpoint_id)
    
    if not checkpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{checkpoint_id}' not found"
        )
    
    original = checkpoint["proposed_action"]
    
    # Calculate diff
    diff = []
    for key, new_value in modified_params.items():
        old_value = original.get(key)
        if old_value != new_value:
            diff.append({
                "field": key,
                "original": old_value,
                "modified": new_value,
                "change_type": "updated" if old_value else "added"
            })
    
    return {
        "checkpoint_id": checkpoint_id,
        "diff": diff,
        "validation": "passed"  # Add actual validation logic
    }
```

---

### 2.5 Non-Functional Requirements (NFR)

| **Category** | **Requirement** | **Target** | **Measurement** |
|-------------|----------------|-----------|----------------|
| **Performance** | Checkpoint save time | < 500ms | Database logging |
| | Workflow resume time | < 2 seconds after approval | End-to-end timing |
| | Teams notification delivery | < 5 seconds | Webhook latency |
| | Approval page load time | < 1 second | Frontend APM |
| **Scalability** | Concurrent pending checkpoints | 100+ simultaneously | Load testing |
| | Approval throughput | 50+ approvals/minute | Stress testing |
| **Reliability** | Checkpoint durability | 99.99% (no data loss) | Database backups |
| | Timeout handling accuracy | 100% (all timeouts caught) | Integration tests |
| | Resume success rate | 99.5% after approval | Error monitoring |
| **Security** | Approval authorization | Role-based (only authorized users) | Unit tests |
| | Audit trail completeness | 100% of decisions logged | Database audit |
| | Parameter validation | 100% (prevent injection) | Security tests |
| **Usability** | Average approval time | < 5 minutes | User analytics |
| | Modification error rate | < 5% (validation catches errors) | User testing |
| | Mobile approval support | 100% functionality on mobile | Cross-device testing |
| **Observability** | Checkpoint metrics | Track pending count, avg approval time | Dashboard |
| | Auto-approval accuracy | Track auto-approval vs human override rate | Monitoring |
| | Timeout rate | Track % of checkpoints that timeout | Alerting |

---

### 2.6 Database Schema (Detailed)

**Checkpoints Table**:
```sql
CREATE TABLE checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    step INT NOT NULL,                       -- Workflow step number
    state JSONB NOT NULL,                    -- Complete checkpoint state
    status VARCHAR(20) NOT NULL CHECK (      -- Approval status
        status IN ('pending', 'approved', 'rejected', 'timeout', 'auto_approved')
    ),
    approved_by VARCHAR(100),                -- User ID who approved/rejected
    approved_at TIMESTAMP WITH TIME ZONE,    -- Approval timestamp
    feedback TEXT,                           -- Approval/rejection comment
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_checkpoints_execution_id ON checkpoints(execution_id);
CREATE INDEX idx_checkpoints_status ON checkpoints(status);
CREATE INDEX idx_checkpoints_created_at ON checkpoints(created_at DESC);
CREATE INDEX idx_checkpoints_state_gin ON checkpoints USING GIN (state);
```

**Example Checkpoint Record**:
```json
{
  "id": "chkpt-20251118-abc123",
  "execution_id": "exec-20251118-xyz789",
  "step": 4,
  "state": {
    "proposed_action": {
      "operation_type": "send_email",
      "to": "john.doe@example.com",
      "subject": "Refund Confirmation - Order #12345",
      "amount": 99.99,
      "template": "refund_confirmation_v2"
    },
    "reasoning": "Customer requested refund for defective product...",
    "confidence": 0.87,
    "risk_level": "high",
    "timeout_at": "2025-11-18T15:30:00Z",
    "metadata": {
      "original_action": {...},
      "notification_sent": true,
      "auto_approval_eligible": false
    }
  },
  "status": "approved",
  "approved_by": "user-alex-chen",
  "approved_at": "2025-11-18T14:35:12Z",
  "feedback": "Verified with customer service policy",
  "created_at": "2025-11-18T14:30:00Z"
}
```

---

### 2.7 Testing Strategy

#### **Unit Tests**:
```python
@pytest.mark.asyncio
async def test_save_checkpoint():
    """Test checkpoint creation and notification"""
    state_manager = StateManager(
        db_session=AsyncMock(),
        notification_service=AsyncMock(),
        learning_service=AsyncMock()
    )
    
    checkpoint_id = await state_manager.save_checkpoint(
        execution_id="exec-test",
        step=2,
        state={"key": "value"},
        proposed_action={"operation": "test"},
        reasoning="Test reasoning",
        confidence=0.9,
        risk_level="high",
        timeout_seconds=3600
    )
    
    assert checkpoint_id.startswith("chkpt-")
    state_manager.notification_service.send_checkpoint_notification.assert_called_once()

@pytest.mark.asyncio
async def test_approve_checkpoint_with_modifications():
    """Test checkpoint approval with parameter modifications"""
    state_manager = StateManager(...)
    
    success = await state_manager.approve_checkpoint(
        checkpoint_id="chkpt-test",
        approved_by="user-test",
        modified_params={"amount": 89.99},
        feedback="Reduced amount"
    )
    
    assert success is True
    state_manager.learning_service.record_learning_case.assert_called_once()
```

---

### 2.8 Risks and Mitigation

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|---------|----------------|-----------|---------------|
| Approval timeout not handled | Low | Critical | Comprehensive timeout monitoring, alerting |
| Parameter modification breaks workflow | Medium | High | JSON Schema validation, preview before apply |
| Teams notification delivery failure | Low | Medium | Retry logic (3 attempts), fallback to email |
| Database connection loss during approval | Low | High | Transaction management, auto-reconnect |
| Race condition (double approval) | Low | Medium | Database unique constraints, optimistic locking |

---

### 2.9 Future Enhancements (Post-MVP)

1. **Multi-Approver Support**: Require N approvals before proceeding (e.g., 2 out of 3 approvers)
2. **Approval Workflows**: Route approvals through escalation chain (L1 → L2 → Manager)
3. **Conditional Checkpoints**: Dynamic checkpoint creation based on runtime conditions
4. **Batch Approval**: Approve multiple similar checkpoints at once
5. **Mobile App**: Native mobile app for faster approvals
6. **Voice Approval**: Approve via voice command (Alexa, Google Assistant)
7. **Smart Routing**: ML-based routing to best approver based on expertise

---

**Next Feature**: [F3. Cross-System Correlation →](#f3-cross-system-correlation)

