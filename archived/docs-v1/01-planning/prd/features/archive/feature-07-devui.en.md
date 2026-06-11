# F7. DevUI Integration

**Category**: Developer Experience  
**Priority**: P1 (Should Have - Critical for Debugging)  
**Development Time**: 1.5 weeks  
**Complexity**: ⭐⭐⭐⭐ (High)  
**Dependencies**: F1 (Sequential Orchestration), React Flow, SignalR/WebSocket, Distributed Tracing (optional)  
**Risk Level**: Low (Well-defined scope, UI-only feature)

---

## 📑 Navigation

- [← Features Overview](../prd-appendix-a-features-overview.md)
- [← F6: Agent Marketplace](./feature-06-marketplace.md)
- **F7: DevUI Integration** ← You are here
- [✓ All Features Complete]

---

## 7.1 Feature Overview

**What is DevUI Integration?**

DevUI Integration provides **developer-focused debugging tools** directly in the IPA UI, enabling developers to trace agent execution flows, inspect LLM prompts/responses, view API calls, and analyze performance bottlenecks—all in a visual, interactive interface.

**Why This Matters**:
- **Faster Debugging**: Reduce debugging time from hours to minutes with visual execution traces
- **Transparency**: See exactly what LLM receives (prompt) and returns (response)
- **Performance Optimization**: Identify slow steps, API bottlenecks, retry loops
- **Learning Tool**: Understand how agents work by inspecting real execution flows
- **Troubleshooting**: Quickly diagnose failures with detailed error context

**Key Capabilities**:
1. **Execution Trace API**: Backend API providing step-by-step execution details
2. **Visual DAG (Directed Acyclic Graph)**: React Flow canvas showing workflow execution path
3. **Step-by-Step Timeline**: Chronological view of all steps with timestamps
4. **Prompt/Response Inspector**: View full LLM prompts and responses (with token count)
5. **API Call Logs**: See all external API calls (ServiceNow, Dynamics, etc.) with latency
6. **Error Context**: Detailed error messages with stack traces and suggested fixes
7. **Real-time Updates**: Live execution progress via WebSocket

**Business Value**:
- **Developer Productivity**: 70% faster debugging (3 hours → 50 minutes)
- **Reduced MTTR**: Mean Time To Repair reduced from 2 hours to 20 minutes
- **Knowledge Transfer**: Junior developers learn faster by inspecting execution traces
- **Quality Assurance**: QA team can verify agent behavior without developer help
- **Cost Optimization**: Identify expensive LLM calls, optimize token usage

**Real-World Example**:

```
Problem: Customer refund workflow failing at step 3 (out of 5 steps)

Traditional Debugging (Without DevUI):
1. Check logs (scattered across files) - 20 minutes
2. Add debug prints to code - 15 minutes
3. Redeploy and re-run workflow - 10 minutes
4. Analyze new logs - 20 minutes
5. Identify issue: LLM timeout due to oversized prompt - 30 minutes
Total: 95 minutes

With DevUI Integration:
1. Open execution trace in UI - 10 seconds
2. Visual DAG shows step 3 marked red (failed) - 5 seconds
3. Click step 3 → See error: "LLM timeout (30s exceeded)" - 5 seconds
4. View prompt inspector → Prompt is 12,000 tokens (way too large) - 10 seconds
5. Identify root cause: Customer has 500+ past orders, all included in context - 20 seconds
Total: 50 seconds (99% faster)
```

**Architecture Overview**:

```
┌─────────────────┐
│  Workflow       │
│  Execution      │
└────────┬────────┘
         │
         │ 1. Emit execution events
         ▼
┌─────────────────┐         ┌──────────────┐
│  Execution      │────────►│  Database    │
│  Trace Service  │         │  (traces)    │
└────────┬────────┘         └──────────────┘
         │
         │ 2. Store trace data
         ▼
┌─────────────────┐         ┌──────────────┐
│  Trace API      │◄────────│  DevUI       │
│  (REST)         │         │  (React)     │
└────────┬────────┘         └──────────────┘
         │
         │ 3. Real-time updates
         ▼
┌─────────────────┐
│  WebSocket      │
│  (SignalR)      │
└─────────────────┘
```

---

## 7.2 User Stories (Complete)

### **US-F7-001: View Visual Execution DAG (Directed Acyclic Graph)**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 4 days  
**Complexity**: ⭐⭐⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** view a visual DAG showing the execution path of my workflow, with each step's status (pending/running/completed/failed)
- **So that** I can quickly understand the workflow structure and identify which step failed

**Acceptance Criteria**:
1. ✅ **Visual Canvas**: Display workflow as interactive DAG using React Flow
2. ✅ **Node Status**: Each node shows status indicator:
   - ⏳ Pending (gray)
   - ▶️ Running (blue, pulsing animation)
   - ✅ Completed (green)
   - ❌ Failed (red)
3. ✅ **Execution Path**: Highlight executed path (bold edges)
4. ✅ **Node Details**: Click node to open detail panel with:
   - Step name, agent ID
   - Start time, end time, duration
   - Input data (JSON)
   - Output data (JSON)
   - Error message (if failed)
5. ✅ **Pan & Zoom**: Support pan, zoom, fit-to-screen
6. ✅ **Real-time Updates**: DAG updates live as workflow executes (via WebSocket)

**Visual DAG UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Execution Trace: refund_workflow_001 (Execution ID: exec_xyz789)             │
│ Status: ❌ Failed at Step 3 | Duration: 4m 23s | Started: 10:30:00           │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ [Fit to Screen] [Zoom In] [Zoom Out] [Timeline View] [Export]                │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                          │ │
│ │     ┌───────────┐                                                       │ │
│ │     │  START    │                                                       │ │
│ │     └─────┬─────┘                                                       │ │
│ │           │                                                             │ │
│ │           ▼                                                             │ │
│ │     ┌───────────────┐                                                  │ │
│ │     │  Step 1       │  ✅                                               │ │
│ │     │  Customer360  │  (2.3s)                                          │ │
│ │     └───────┬───────┘                                                  │ │
│ │             │                                                           │ │
│ │             ▼                                                           │ │
│ │     ┌───────────────┐                                                  │ │
│ │     │  Step 2       │  ✅                                               │ │
│ │     │  Classify     │  (1.8s)                                          │ │
│ │     └───────┬───────┘                                                  │ │
│ │             │                                                           │ │
│ │             ▼                                                           │ │
│ │     ┌───────────────┐  ← SELECTED                                     │ │
│ │     │  Step 3       │  ❌                                               │ │
│ │     │  Refund       │  (30s timeout)                                   │ │
│ │     │  Decision     │                                                   │ │
│ │     └───────────────┘                                                  │ │
│ │             │                                                           │ │
│ │             ▼ (not executed)                                           │ │
│ │     ┌───────────────┐                                                  │ │
│ │     │  Step 4       │  ⏳ (pending)                                    │ │
│ │     │  Update Ticket│                                                  │ │
│ │     └───────┬───────┘                                                  │ │
│ │             │                                                           │ │
│ │             ▼                                                           │ │
│ │     ┌───────────────┐                                                  │ │
│ │     │  END          │                                                  │ │
│ │     └───────────────┘                                                  │ │
│ │                                                                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Step 3 Details: Refund Decision                                [Close]  │ │
│ │                                                                          │ │
│ │ Status: ❌ Failed                                                        │ │
│ │ Agent: CS.RefundDecision                                                 │ │
│ │ Duration: 30.0s (exceeded timeout)                                      │ │
│ │ Started: 10:32:15 | Ended: 10:32:45                                     │ │
│ │                                                                          │ │
│ │ Error:                                                                   │ │
│ │ LLM request timeout after 30 seconds                                     │ │
│ │                                                                          │ │
│ │ Suggested Fix:                                                           │ │
│ │ - Reduce prompt size (current: 12,000 tokens)                           │ │
│ │ - Increase timeout in agent config                                      │ │
│ │ - Check Azure OpenAI service health                                     │ │
│ │                                                                          │ │
│ │ [View Input Data] [View Prompt] [Retry Step] [View Logs]               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

**React Flow DAG Component**:

```typescript
import ReactFlow, { Node, Edge, Controls, Background } from 'reactflow';
import 'reactflow/dist/style.css';

interface ExecutionNode extends Node {
  data: {
    stepId: string;
    stepName: string;
    agentId: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    duration: number;
    error?: string;
  };
}

export const ExecutionDAG: React.FC<{ executionId: string }> = ({ executionId }) => {
  const [nodes, setNodes] = useState<ExecutionNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<ExecutionNode | null>(null);
  
  // Fetch execution trace
  useEffect(() => {
    fetchExecutionTrace(executionId).then(trace => {
      // Convert trace steps to React Flow nodes
      const flowNodes: ExecutionNode[] = trace.steps.map((step, index) => ({
        id: step.step_id,
        type: 'custom',
        position: { x: 250, y: index * 150 },
        data: {
          stepId: step.step_id,
          stepName: step.name,
          agentId: step.agent_id,
          status: step.status,
          duration: step.duration_ms / 1000,
          error: step.error
        }
      }));
      
      // Create edges between steps
      const flowEdges: Edge[] = [];
      for (let i = 0; i < flowNodes.length - 1; i++) {
        flowEdges.push({
          id: `e${i}-${i+1}`,
          source: flowNodes[i].id,
          target: flowNodes[i + 1].id,
          animated: flowNodes[i].data.status === 'completed',
          style: { stroke: flowNodes[i].data.status === 'failed' ? '#ef4444' : '#10b981' }
        });
      }
      
      setNodes(flowNodes);
      setEdges(flowEdges);
    });
  }, [executionId]);
  
  // Real-time updates via WebSocket
  useEffect(() => {
    const ws = new WebSocket(`wss://api.example.com/executions/${executionId}/stream`);
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      
      // Update node status
      setNodes(prevNodes => 
        prevNodes.map(node => 
          node.id === update.step_id 
            ? { ...node, data: { ...node.data, status: update.status } }
            : node
        )
      );
    };
    
    return () => ws.close();
  }, [executionId]);
  
  const onNodeClick = (event: React.MouseEvent, node: ExecutionNode) => {
    setSelectedNode(node);
  };
  
  return (
    <div style={{ height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={onNodeClick}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
      
      {selectedNode && (
        <StepDetailPanel step={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  );
};
```

**API: Get Execution Trace**:

```bash
GET /api/executions/{execution_id}/trace

Response:
{
  "execution_id": "exec_xyz789",
  "workflow_id": "refund_workflow_001",
  "status": "failed",
  "started_at": "2025-11-18T10:30:00Z",
  "ended_at": "2025-11-18T10:34:23Z",
  "duration_ms": 263000,
  "steps": [
    {
      "step_id": "step_1",
      "name": "Get Customer 360 View",
      "agent_id": "CS.Customer360",
      "status": "completed",
      "started_at": "2025-11-18T10:30:00Z",
      "ended_at": "2025-11-18T10:30:02Z",
      "duration_ms": 2300,
      "input": {...},
      "output": {...}
    },
    {
      "step_id": "step_3",
      "name": "Refund Decision",
      "agent_id": "CS.RefundDecision",
      "status": "failed",
      "started_at": "2025-11-18T10:32:15Z",
      "ended_at": "2025-11-18T10:32:45Z",
      "duration_ms": 30000,
      "error": {
        "code": "LLM_TIMEOUT",
        "message": "LLM request timeout after 30 seconds",
        "details": "Azure OpenAI API did not respond within timeout",
        "suggested_fixes": [
          "Reduce prompt size (current: 12,000 tokens)",
          "Increase timeout in agent config",
          "Check Azure OpenAI service health"
        ]
      }
    }
  ]
}
```

**Definition of Done**:
- [ ] Visual DAG displays workflow execution as React Flow canvas
- [ ] Each node shows status indicator (pending, running, completed, failed)
- [ ] Click node opens detail panel with step info
- [ ] DAG supports pan, zoom, fit-to-screen
- [ ] Real-time updates via WebSocket
- [ ] Failed nodes highlighted in red with error message
- [ ] Integration tests for trace API

---

### **US-F7-002: LLM Prompt/Response Inspector**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** view the exact LLM prompt sent to Azure OpenAI and the response received
- **So that** I can debug prompt engineering issues and optimize token usage

**Acceptance Criteria**:
1. ✅ **Prompt View**: Display full LLM prompt with syntax highlighting
2. ✅ **Response View**: Display full LLM response (JSON or text)
3. ✅ **Token Count**: Show prompt tokens, completion tokens, total tokens
4. ✅ **Cost Estimate**: Calculate and display cost (based on GPT-4o pricing)
5. ✅ **Model Info**: Show model name, temperature, max tokens, top_p
6. ✅ **Latency**: Show LLM API call latency (time to first token, total time)
7. ✅ **Copy Button**: One-click copy prompt/response to clipboard

**Prompt Inspector UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Step 3: Refund Decision - LLM Prompt Inspector                      [Close]  │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ Model Configuration:                                                          │
│   Model: gpt-4o (Azure OpenAI)                                               │
│   Temperature: 0.3 | Max Tokens: 2000 | Top P: 1.0                          │
│                                                                               │
│ Token Usage:                                                                  │
│   Prompt Tokens: 12,345 ⚠️ (very large)                                      │
│   Completion Tokens: 156                                                      │
│   Total Tokens: 12,501                                                        │
│   Estimated Cost: $0.375 (prompt: $0.370, completion: $0.005)                │
│                                                                               │
│ Latency:                                                                      │
│   Time to First Token: 3.2s                                                  │
│   Total Time: 30.0s (TIMEOUT)                                                │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ [📝 Prompt] [📤 Response] [📊 Token Analysis]                                │
│                                                                               │
│ Prompt (12,345 tokens):                                          [Copy]      │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ You are an AI assistant helping with customer refund decisions.         │ │
│ │                                                                          │ │
│ │ Company Policy:                                                          │ │
│ │ - Standard returns: 30-day window                                        │ │
│ │ - Premium customers: 45-day window                                       │ │
│ │ - Defective products: Always approve                                     │ │
│ │                                                                          │ │
│ │ Customer Context:                                                        │ │
│ │ {                                                                        │ │
│ │   "customer_id": "CUST-5678",                                            │ │
│ │   "tier": "Premium",                                                     │ │
│ │   "purchase_history": [                                                  │ │
│ │     {"order_id": "12345", "date": "2025-10-15", "amount": 99.99},      │ │
│ │     {"order_id": "12346", "date": "2025-09-20", "amount": 49.99},      │ │
│ │     ... (498 more orders - ISSUE: Too much context!) ...                │ │
│ │   ]                                                                      │ │
│ │ }                                                                        │ │
│ │                                                                          │ │
│ │ Current Request:                                                         │ │
│ │ {                                                                        │ │
│ │   "product": "Wireless Headphones",                                      │ │
│ │   "issue": "Defective",                                                  │ │
│   "purchase_date": "2025-10-15"                                           │ │
│ │ }                                                                        │ │
│ │                                                                          │ │
│ │ Provide decision in JSON format...                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ⚠️  Warning: Prompt is very large (12,345 tokens)                            │
│ Recommendation: Limit purchase_history to last 10 orders (reduce by 95%)     │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Token Analysis Tab**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Token Analysis                                                                │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ Prompt Breakdown (12,345 tokens):                                            │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ System Message: 234 tokens (2%)  ████                                    │ │
│ │ Company Policy: 156 tokens (1%)  ██                                      │ │
│ │ Customer Context: 11,789 tokens (95%) ████████████████████████████████  │ │
│ │   ↳ purchase_history: 11,500 tokens (93%) ← PROBLEM                     │ │
│ │   ↳ Other fields: 289 tokens (2%)                                        │ │
│ │ Current Request: 166 tokens (2%)  ██                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ Optimization Suggestions:                                                     │
│   1. Limit purchase_history to last 10 orders (save 11,000 tokens, -89%)    │
│   2. Remove unnecessary fields from customer context (save 200 tokens, -2%) │
│   3. Use summarized purchase stats instead of full list (save 11,300, -92%) │
│                                                                               │
│ Optimized Token Count: 1,045 tokens (92% reduction)                          │
│ Cost Savings: $0.330/call → $12.87/month @ 100 calls/day                    │
└───────────────────────────────────────────────────────────────────────────────┘
```

**API: Get LLM Call Details**:

```bash
GET /api/executions/{execution_id}/steps/{step_id}/llm-calls

Response:
{
  "step_id": "step_3",
  "llm_calls": [
    {
      "call_id": "llm_call_001",
      "model": "gpt-4o",
      "temperature": 0.3,
      "max_tokens": 2000,
      "top_p": 1.0,
      "prompt": "You are an AI assistant...",
      "response": "{\"decision\": \"Approved\", ...}",
      "tokens": {
        "prompt": 12345,
        "completion": 156,
        "total": 12501
      },
      "cost_usd": 0.375,
      "latency": {
        "time_to_first_token_ms": 3200,
        "total_time_ms": 30000,
        "timed_out": true
      },
      "timestamp": "2025-11-18T10:32:15Z"
    }
  ]
}
```

**Definition of Done**:
- [ ] Prompt inspector displays full LLM prompt with syntax highlighting
- [ ] Response displayed with JSON formatting
- [ ] Token count shown (prompt, completion, total)
- [ ] Cost estimate calculated and displayed
- [ ] Token analysis tab shows prompt breakdown
- [ ] Optimization suggestions provided for large prompts
- [ ] Copy button copies prompt/response to clipboard

---

### **US-F7-003: Step-by-Step Timeline View**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** view a chronological timeline of all workflow steps with timestamps, duration, and status
- **So that** I can identify performance bottlenecks and understand execution order

**Acceptance Criteria**:
1. ✅ **Timeline View**: Display steps in chronological order (vertical timeline)
2. ✅ **Timestamps**: Show start time, end time for each step
3. ✅ **Duration Bars**: Visual bar showing relative duration of each step
4. ✅ **Status Icons**: Icon for each status (✅ completed, ❌ failed, ⏳ pending)
5. ✅ **Performance Insights**: Highlight slowest steps (>5s)
6. ✅ **Expand/Collapse**: Click step to expand and see input/output/error
7. ✅ **Export**: Export timeline as CSV or JSON

**Timeline View UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Execution Timeline: refund_workflow_001                      [DAG View] [Export]│
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ Total Duration: 4m 23s (263 seconds) | Steps: 3/5 completed                  │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 10:30:00 │ ✅ Step 1: Get Customer 360 View                  [2.3s]    │ │
│ │          │ ██                                                           │ │
│ │          │ Agent: CS.Customer360                                        │ │
│ │          │ Started: 10:30:00 | Ended: 10:30:02                         │ │
│ │          │ [▼ Expand]                                                   │ │
│ │          │                                                              │ │
│ │ 10:30:02 │ ✅ Step 2: Classify Issue                        [1.8s]    │ │
│ │          │ █                                                            │ │
│ │          │ Agent: CS.IssueClassifier                                   │ │
│ │          │ Started: 10:30:02 | Ended: 10:30:04                         │ │
│ │          │ [▼ Expand]                                                   │ │
│ │          │                                                              │ │
│ │ 10:32:15 │ ❌ Step 3: Refund Decision               [30.0s] ⚠️ SLOW  │ │
│ │          │ ███████████████████████████████████                          │ │
│ │          │ Agent: CS.RefundDecision                                     │ │
│ │          │ Started: 10:32:15 | Ended: 10:32:45 (TIMEOUT)               │ │
│ │          │ Error: LLM request timeout after 30 seconds                  │ │
│ │          │ [▲ Collapse]                                                 │ │
│ │          │                                                              │ │
│ │          │ Input:                                                       │ │
│ │          │ {                                                            │ │
│ │          │   "customer_id": "CUST-5678",                                │ │
│ │          │   "product": "Wireless Headphones",                          │ │
│ │          │   "issue": "Defective"                                       │ │
│ │          │ }                                                            │ │
│ │          │                                                              │ │
│ │          │ Error Details:                                               │ │
│ │          │ LLM prompt too large (12,345 tokens)                         │ │
│ │          │ Exceeded 30-second timeout                                   │ │
│ │          │                                                              │ │
│ │          │ [View LLM Prompt] [View Logs] [Retry Step]                  │ │
│ │          │                                                              │ │
│ │ 10:32:45 │ ⏳ Step 4: Update Ticket                  [Not Started]    │ │
│ │          │ (waiting for step 3 to complete)                            │ │
│ │          │                                                              │ │
│ │ -        │ ⏳ Step 5: Notify Customer                [Not Started]    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 📊 Performance Insights:                                                     │
│   • Step 3 is the bottleneck (30.0s, 95% of total time)                     │
│   • Recommendation: Optimize LLM prompt (reduce token count)                 │
│   • Steps 1-2 executed efficiently (<3s each)                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] Timeline view displays steps in chronological order
- [ ] Each step shows start time, end time, duration
- [ ] Duration bars visualize relative time
- [ ] Slow steps (>5s) highlighted with warning
- [ ] Click step to expand and see input/output/error
- [ ] Export timeline as CSV or JSON

---

### **US-F7-004: External API Call Logs**

**Priority**: P2 (Nice to Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** view all external API calls made during workflow execution (ServiceNow, Dynamics 365, SharePoint, OpenAI)
- **So that** I can debug integration issues and identify slow external services

**Acceptance Criteria**:
1. ✅ **API Call List**: Display all external API calls with:
   - Service name (ServiceNow, Dynamics 365, etc.)
   - HTTP method and endpoint
   - Request headers (sanitized, no auth tokens)
   - Response status code
   - Latency (time to response)
2. ✅ **Filtering**: Filter by service, status code, latency
3. ✅ **Sorting**: Sort by latency (identify slowest calls)
4. ✅ **Request/Response View**: Click call to see full request/response
5. ✅ **Retry Indicator**: Show if call was retried (and how many times)

**API Call Logs UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ External API Calls (Step 1: Customer 360 View)                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ [Filter: All Services ▼] [Status: All ▼] [Sort: Latency ▼]                  │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Service        │ Method │ Endpoint            │ Status │ Latency │ Retry││
│ ├────────────────┼────────┼─────────────────────┼────────┼─────────┼──────┤│
│ │ ServiceNow     │ GET    │ /api/now/table/...  │ 200    │ 1.2s    │ -    ││
│ │ Dynamics 365   │ GET    │ /api/data/v9.2/...  │ 200    │ 2.8s    │ -    ││
│ │ SharePoint     │ GET    │ /_api/search/query  │ 200    │ 1.5s    │ -    ││
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ Click row to view request/response details                                   │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] API call logs displayed for each step
- [ ] Filter by service, status code, latency
- [ ] Sort by latency to identify slowest calls
- [ ] Click call to see full request/response
- [ ] Retry indicator shown if applicable

---

## 7.3 Technical Implementation (Backend)

### 7.3.1 Execution Trace Service

```python
from datetime import datetime
from typing import List, Dict, Any

class ExecutionTraceService:
    """
    Service for capturing and storing execution trace data
    """
    
    def __init__(self, db_session, websocket_manager):
        self.db = db_session
        self.ws_manager = websocket_manager
    
    async def record_step_start(
        self,
        execution_id: str,
        step_id: str,
        step_name: str,
        agent_id: str,
        input_data: Dict[str, Any]
    ):
        """Record step start event"""
        trace_event = ExecutionTraceEvent(
            execution_id=execution_id,
            step_id=step_id,
            step_name=step_name,
            agent_id=agent_id,
            event_type="step_start",
            status="running",
            input_data=input_data,
            timestamp=datetime.utcnow()
        )
        self.db.add(trace_event)
        self.db.commit()
        
        # Send real-time update via WebSocket
        await self.ws_manager.send_update(execution_id, {
            "type": "step_start",
            "step_id": step_id,
            "status": "running"
        })
    
    async def record_step_complete(
        self,
        execution_id: str,
        step_id: str,
        output_data: Dict[str, Any],
        duration_ms: int
    ):
        """Record step completion"""
        # Update trace event
        trace_event = self.db.query(ExecutionTraceEvent).filter_by(
            execution_id=execution_id,
            step_id=step_id
        ).first()
        
        trace_event.status = "completed"
        trace_event.output_data = output_data
        trace_event.duration_ms = duration_ms
        trace_event.ended_at = datetime.utcnow()
        self.db.commit()
        
        # Send real-time update
        await self.ws_manager.send_update(execution_id, {
            "type": "step_complete",
            "step_id": step_id,
            "status": "completed",
            "duration_ms": duration_ms
        })
    
    async def record_llm_call(
        self,
        execution_id: str,
        step_id: str,
        model: str,
        prompt: str,
        response: str,
        tokens: Dict[str, int],
        latency_ms: int
    ):
        """Record LLM API call"""
        llm_call = LLMCallLog(
            execution_id=execution_id,
            step_id=step_id,
            model=model,
            prompt=prompt,
            response=response,
            prompt_tokens=tokens["prompt"],
            completion_tokens=tokens["completion"],
            total_tokens=tokens["total"],
            latency_ms=latency_ms,
            timestamp=datetime.utcnow()
        )
        self.db.add(llm_call)
        self.db.commit()
```

---

## 7.4 Database Schema

```sql
CREATE TABLE execution_trace_events (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    step_name VARCHAR(200),
    agent_id VARCHAR(100),
    
    -- Event details
    event_type VARCHAR(50),  -- step_start, step_complete, step_failed
    status VARCHAR(20),  -- pending, running, completed, failed
    
    -- Data
    input_data JSONB,
    output_data JSONB,
    error_data JSONB,
    
    -- Timing
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE llm_call_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    
    -- LLM details
    model VARCHAR(50),
    temperature DECIMAL(3,2),
    max_tokens INTEGER,
    
    -- Request/Response
    prompt TEXT,
    response TEXT,
    
    -- Tokens
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd DECIMAL(10,6),
    
    -- Performance
    latency_ms INTEGER,
    timed_out BOOLEAN DEFAULT false,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_call_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    
    -- API details
    service_name VARCHAR(100),  -- ServiceNow, Dynamics365, etc.
    method VARCHAR(10),  -- GET, POST, PUT, DELETE
    endpoint TEXT,
    
    -- Request/Response
    request_headers JSONB,
    response_status INTEGER,
    response_body TEXT,
    
    -- Performance
    latency_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_trace_execution ON execution_trace_events(execution_id, step_id);
CREATE INDEX idx_llm_execution ON llm_call_logs(execution_id, step_id);
CREATE INDEX idx_api_execution ON api_call_logs(execution_id, step_id);
```

---

## 7.5 Non-Functional Requirements (NFR)

| **Category** | **Requirement** | **Target** | **Measurement** |
|-------------|----------------|-----------|----------------|
| **Performance** | Trace API load time | < 500ms | API response time |
| | DAG rendering time | < 1 second | Frontend metrics |
| | WebSocket latency | < 100ms | Real-time monitoring |
| **Scalability** | Trace retention | 30 days (configurable) | Database policy |
| | Concurrent viewers | 100+ simultaneous users | Load testing |
| **Usability** | Time to find issue | < 2 minutes | User testing |
| | Learning curve | <30 minutes for new developers | User feedback |

---

## 7.6 Testing Strategy

**Unit Tests**:
- Trace event recording
- LLM call logging
- API call logging

**Integration Tests**:
- End-to-end trace capture
- WebSocket real-time updates
- DAG rendering

---

## 7.7 Risks and Mitigation

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|---------|----------------|-----------|---------------|
| Large trace data storage | Medium | Medium | 30-day retention, compression, archival |
| Sensitive data exposure | Low | High | Sanitize auth tokens, PII masking |
| WebSocket connection drops | Medium | Low | Auto-reconnect, fallback to polling |

---

## 7.8 Future Enhancements (Post-MVP)

1. **Distributed Tracing**: Integration with OpenTelemetry
2. **Performance Profiling**: Flame graphs for step execution
3. **Comparison View**: Compare two executions side-by-side
4. **Replay Mode**: Replay execution with different inputs
5. **Alerting**: Set alerts on slow steps, high error rates

---

**✅ All Features Complete!** This concludes F1-F7 PRD specifications.
