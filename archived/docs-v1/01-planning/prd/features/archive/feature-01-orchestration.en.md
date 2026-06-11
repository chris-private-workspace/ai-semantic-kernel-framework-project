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

