# F4. Cross-Scenario Collaboration

**Category**: Integration & Intelligence  
**Priority**: P0 (Must Have - Core Capability)  
**Development Time**: 2 weeks  
**Complexity**: ⭐⭐⭐⭐ (High)  
**Dependencies**: F1 (Sequential Orchestration), F2 (Checkpointing), F3 (Cross-System Correlation), Event Bus (RabbitMQ/Azure Service Bus)  
**Risk Level**: Medium (Cross-team coordination, async communication complexity)

---

## 📑 Navigation

- [← Features Overview](../prd-appendix-a-features-overview.md)
- [← F3: Cross-System Correlation](./feature-03-correlation.md)
- **F4: Cross-Scenario Collaboration** ← You are here
- [→ F5: Learning-based Collaboration](./feature-05-learning.md)

---

## 4.1 Feature Overview

**What is Cross-Scenario Collaboration?**

Cross-Scenario Collaboration enables agents from different business scenarios (e.g., Customer Service → IT Support, Sales → Finance) to **trigger each other asynchronously** using event-driven architecture. This eliminates manual handoffs, reduces delays, and creates seamless end-to-end automation across departments.

**Why This Matters**:
- **Eliminates Silos**: Breaks down departmental barriers by enabling automatic cross-team workflows
- **Reduces Handoff Time**: Automated triggering reduces delays from hours/days to seconds/minutes
- **Complete Automation**: Enables true end-to-end automation across multiple business processes
- **Audit Trail**: Every cross-scenario invocation is logged for compliance and debugging
- **Resilience**: Async architecture ensures failures don't cascade across scenarios

**Key Capabilities**:
1. **Event-Driven Triggering**: CS Agent completes → Automatically triggers IT Agent via event bus
2. **Async Callbacks**: Triggered agent runs in background, sends results back when complete
3. **Status Tracking**: Initiating agent can check status and retrieve results of triggered agent
4. **Conditional Triggering**: Define rules for when to trigger (e.g., only if ticket severity ≥ High)
5. **Error Handling**: Retry logic, dead letter queue for failed triggers
6. **Cross-Scenario Context**: Pass rich context (customer data, ticket info) to triggered agent

**Business Value**:
- **Faster Resolution**: Customer issues requiring IT escalation resolved 60% faster
- **Reduced Manual Work**: Eliminate 80% of manual handoff emails/messages
- **Better Coordination**: IT team gets complete context automatically (no information loss)
- **Compliance**: Full audit trail of cross-team interactions
- **Scalability**: Handle 1000+ cross-scenario triggers per day

**Real-World Example**:

```
Traditional Process (Manual Handoff):
1. CS Agent resolves customer ticket
2. CS Agent identifies need for IT escalation (VPN issue)
3. CS Agent writes email to IT team with customer details
4. IT team receives email (maybe after hours, sits in queue)
5. IT Agent manually reads email, looks up customer info
6. IT Agent creates new IT ticket
7. IT Agent investigates VPN issue
8. IT Agent replies to CS Agent via email
9. CS Agent updates customer

Total time: 4-8 hours (or next business day)

With Cross-Scenario Collaboration (Automated):
1. CS Agent completes ticket resolution
2. System detects trigger condition: "VPN issue mentioned"
3. CS Agent automatically triggers IT Agent via event
4. IT Agent receives full context (customer ID, ticket, VPN logs)
5. IT Agent runs investigation workflow automatically
6. IT Agent sends results back via callback
7. CS Agent receives results, updates customer ticket

Total time: 5-10 minutes (automated)
```

**Architecture Overview**:

```
┌─────────────┐         Event          ┌──────────────┐
│  CS Agent   │──────────────────────►│  Event Bus   │
│  (Trigger)  │    "IT.VPN.Check"     │ (RabbitMQ)   │
└─────────────┘                       └──────────────┘
                                             │
                                             │ Subscribe
                                             ▼
                                      ┌──────────────┐
                                      │  IT Agent    │
                                      │  (Listener)  │
                                      └──────────────┘
                                             │
                                             │ Async Process
                                             ▼
                                      ┌──────────────┐
                                      │  Results     │
                                      │  Callback    │
                                      └──────────────┘
                                             │
                                             │ POST /callback
                                             ▼
                                      ┌──────────────┐
                                      │  CS Agent    │
                                      │  (Receives)  │
                                      └──────────────┘
```

---

## 4.2 User Stories (Complete)

### **US-F4-001: Trigger IT Agent from CS Workflow**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 4 days  
**Complexity**: ⭐⭐⭐⭐

**User Story**:
- **As a** Customer Service Agent Workflow Developer (Emily Zhang)
- **I want to** configure my CS workflow to automatically trigger an IT agent when specific conditions are met (e.g., VPN issue detected)
- **So that** IT escalations happen instantly without manual handoff, reducing resolution time from hours to minutes

**Acceptance Criteria**:
1. ✅ **YAML Configuration**: Define trigger rules in workflow YAML
   ```yaml
   steps:
     - name: "Resolve Customer Issue"
       agent: "CS.IssueResolution"
       on_complete:
         - condition: "output.category == 'VPN' AND output.severity >= 3"
           trigger:
             scenario: "IT"
             agent: "IT.VPNTroubleshoot"
             event_type: "IT.VPN.Check"
             context:
               customer_id: "${input.customer_id}"
               ticket_id: "${output.ticket_id}"
               issue_details: "${output.summary}"
   ```
2. ✅ **Event Publishing**: System publishes event to event bus when trigger condition met
3. ✅ **Context Passing**: Triggered agent receives full context (customer ID, ticket ID, issue details)
4. ✅ **Status Tracking**: Initiating workflow can query status of triggered agent
5. ✅ **Callback Registration**: Optional callback URL to receive results when triggered agent completes
6. ✅ **Audit Logging**: All trigger events logged with timestamp, source, target, context

**Workflow YAML Example (Complete)**:

```yaml
workflow:
  id: "CS-CustomerIssueResolution"
  name: "Customer Service - Issue Resolution"
  version: "1.0"
  trigger: "manual"
  
  steps:
    # Step 1: Gather customer context
    - id: "step_1"
      name: "Get Customer 360 View"
      agent: "CS.Customer360"
      input:
        customer_id: "${workflow.input.customer_id}"
      output_mapping:
        customer_data: "${output}"
    
    # Step 2: Analyze issue with AI
    - id: "step_2"
      name: "Analyze Issue Category"
      agent: "CS.IssueClassifier"
      input:
        ticket_description: "${workflow.input.description}"
        customer_history: "${step_1.output.customer_data}"
      output_mapping:
        issue_category: "${output.category}"
        severity: "${output.severity}"
        recommended_action: "${output.action}"
    
    # Step 3: Resolve issue
    - id: "step_3"
      name: "Execute Resolution Action"
      agent: "CS.IssueResolution"
      input:
        customer_id: "${workflow.input.customer_id}"
        category: "${step_2.output.issue_category}"
        action: "${step_2.output.recommended_action}"
      
      # Cross-scenario trigger configuration
      on_complete:
        # Trigger 1: IT escalation for VPN issues
        - condition: "${step_2.output.issue_category} == 'VPN' AND ${step_2.output.severity} >= 3"
          trigger:
            scenario: "IT"
            agent: "IT.VPNTroubleshoot"
            event_type: "IT.VPN.Check"
            priority: "high"
            context:
              customer_id: "${workflow.input.customer_id}"
              ticket_id: "${step_3.output.ticket_id}"
              issue_details: "${step_3.output.summary}"
              vpn_logs: "${step_3.output.vpn_logs}"
            callback:
              url: "${workflow.callback_base_url}/cs/tickets/${step_3.output.ticket_id}/it-results"
              method: "POST"
              auth: "bearer_token"
          
        # Trigger 2: Finance team for refund requests
        - condition: "${step_2.output.issue_category} == 'Refund' AND ${step_3.output.amount} > 100"
          trigger:
            scenario: "Finance"
            agent: "Finance.RefundApproval"
            event_type: "Finance.Refund.Request"
            priority: "medium"
            context:
              customer_id: "${workflow.input.customer_id}"
              order_id: "${step_3.output.order_id}"
              amount: "${step_3.output.amount}"
              reason: "${step_3.output.refund_reason}"
            callback:
              url: "${workflow.callback_base_url}/cs/tickets/${step_3.output.ticket_id}/refund-status"
              method: "POST"
    
    # Step 4: Update ticket and notify customer
    - id: "step_4"
      name: "Close Ticket"
      agent: "CS.TicketUpdate"
      input:
        ticket_id: "${step_3.output.ticket_id}"
        status: "Resolved"
        resolution_notes: "${step_3.output.summary}"
```

**Event Message Format (Published to Event Bus)**:

```json
{
  "event_id": "evt_abc123",
  "event_type": "IT.VPN.Check",
  "timestamp": "2025-11-18T10:30:00Z",
  "source": {
    "scenario": "CS",
    "workflow_id": "CS-CustomerIssueResolution",
    "execution_id": "exec_xyz789",
    "step_id": "step_3"
  },
  "target": {
    "scenario": "IT",
    "agent": "IT.VPNTroubleshoot"
  },
  "priority": "high",
  "context": {
    "customer_id": "CUST-5678",
    "ticket_id": "CS-1234",
    "issue_details": "Customer unable to connect to corporate VPN",
    "vpn_logs": "Connection timeout after 30s..."
  },
  "callback": {
    "url": "https://api.example.com/cs/tickets/CS-1234/it-results",
    "method": "POST",
    "auth": "bearer_token"
  },
  "metadata": {
    "retry_count": 0,
    "expires_at": "2025-11-18T12:30:00Z"
  }
}
```

**API: Trigger Status Query**:

```bash
GET /api/triggers/{trigger_id}/status

Response:
{
  "trigger_id": "trg_abc123",
  "event_id": "evt_abc123",
  "status": "running",  // pending | running | completed | failed
  "source_workflow": "CS-CustomerIssueResolution",
  "target_agent": "IT.VPNTroubleshoot",
  "triggered_at": "2025-11-18T10:30:00Z",
  "started_at": "2025-11-18T10:30:15Z",
  "target_execution": {
    "execution_id": "exec_it_456",
    "progress": 65,
    "current_step": "Analyzing VPN logs"
  },
  "estimated_completion": "2025-11-18T10:35:00Z"
}
```

**Definition of Done**:
- [ ] YAML `on_complete.trigger` syntax parsed and validated
- [ ] Event published to event bus when trigger condition met
- [ ] Triggered agent receives full context via event message
- [ ] Status API returns real-time status of triggered execution
- [ ] Callback URL invoked when triggered agent completes
- [ ] All trigger events logged to `cross_scenario_triggers` table
- [ ] Unit tests for condition evaluation logic

---

### **US-F4-002: Receive Callback Results from Triggered Agent**

**Priority**: P0 (Must Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** Customer Service Workflow (system)
- **I want to** receive results from the triggered IT agent via callback when the investigation completes
- **So that** I can automatically update the customer ticket with IT findings without manual intervention

**Acceptance Criteria**:
1. ✅ **Callback Registration**: Initiating workflow provides callback URL when triggering
2. ✅ **Async Execution**: Triggered agent runs in background without blocking initiating workflow
3. ✅ **Callback Invocation**: When triggered agent completes, system POSTs results to callback URL
4. ✅ **Result Format**: Callback payload includes execution status, output data, errors (if any)
5. ✅ **Security**: Callback requests authenticated via bearer token or HMAC signature
6. ✅ **Retry Logic**: Failed callbacks retried 3 times with exponential backoff
7. ✅ **Timeout Handling**: If triggered agent exceeds timeout, callback receives timeout error

**Callback Payload Example (Success)**:

```json
POST https://api.example.com/cs/tickets/CS-1234/it-results
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "trigger_id": "trg_abc123",
  "event_id": "evt_abc123",
  "status": "completed",
  "triggered_at": "2025-11-18T10:30:00Z",
  "completed_at": "2025-11-18T10:34:23Z",
  "duration_seconds": 263,
  "execution": {
    "execution_id": "exec_it_456",
    "agent": "IT.VPNTroubleshoot",
    "output": {
      "root_cause": "Firewall rule blocking VPN port 1194",
      "resolution_action": "Added firewall exception for customer IP",
      "status": "Resolved",
      "customer_impacted": false,
      "follow_up_required": false
    },
    "steps_completed": 5,
    "logs_url": "https://api.example.com/executions/exec_it_456/logs"
  },
  "context": {
    "customer_id": "CUST-5678",
    "ticket_id": "CS-1234"
  }
}
```

**Callback Payload Example (Failure)**:

```json
{
  "trigger_id": "trg_abc123",
  "event_id": "evt_abc123",
  "status": "failed",
  "triggered_at": "2025-11-18T10:30:00Z",
  "failed_at": "2025-11-18T10:35:00Z",
  "duration_seconds": 300,
  "execution": {
    "execution_id": "exec_it_456",
    "agent": "IT.VPNTroubleshoot",
    "error": {
      "code": "TIMEOUT",
      "message": "Agent execution exceeded 5-minute timeout",
      "step_failed": "step_3",
      "details": "VPN log query timed out"
    },
    "steps_completed": 2
  },
  "context": {
    "customer_id": "CUST-5678",
    "ticket_id": "CS-1234"
  }
}
```

**CS Workflow Callback Handler (Example)**:

```python
@router.post("/cs/tickets/{ticket_id}/it-results")
async def receive_it_results(
    ticket_id: str,
    callback_data: CallbackPayload,
    db: Session = Depends(get_db)
):
    """
    Receive callback results from IT agent
    
    This endpoint is called by the triggered IT agent when investigation completes
    """
    logger.info(f"Received IT callback for ticket {ticket_id}, status: {callback_data.status}")
    
    # 1. Validate trigger ID exists
    trigger = db.query(CrossScenarioTrigger).filter_by(
        trigger_id=callback_data.trigger_id
    ).first()
    
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    # 2. Update trigger record
    trigger.status = callback_data.status
    trigger.completed_at = callback_data.completed_at
    trigger.callback_received_at = datetime.utcnow()
    trigger.result_data = callback_data.execution.output
    db.commit()
    
    # 3. Update CS ticket with IT findings
    if callback_data.status == "completed":
        ticket = db.query(Ticket).filter_by(ticket_id=ticket_id).first()
        
        it_output = callback_data.execution.output
        ticket.internal_notes += f"\n\n[IT Investigation Results - {callback_data.completed_at}]\n"
        ticket.internal_notes += f"Root Cause: {it_output['root_cause']}\n"
        ticket.internal_notes += f"Resolution: {it_output['resolution_action']}\n"
        ticket.internal_notes += f"Status: {it_output['status']}\n"
        
        if it_output.get("follow_up_required"):
            ticket.status = "Pending IT Follow-up"
        else:
            ticket.status = "Resolved"
        
        db.commit()
        
        logger.info(f"Ticket {ticket_id} updated with IT results")
    
    elif callback_data.status == "failed":
        # Handle failure - create manual task for CS agent
        ticket = db.query(Ticket).filter_by(ticket_id=ticket_id).first()
        ticket.status = "Escalated - IT Failed"
        ticket.internal_notes += f"\n\n[IT Investigation Failed - {callback_data.failed_at}]\n"
        ticket.internal_notes += f"Error: {callback_data.execution.error['message']}\n"
        db.commit()
        
        logger.error(f"IT investigation failed for ticket {ticket_id}")
    
    return {"message": "Callback processed successfully"}
```

**UI Notification (Real-time Update)**:

```
┌──────────────────────────────────────────────────────────────┐
│ Ticket CS-1234: VPN Connection Issue                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Status: Resolved ✓                                          │
│                                                              │
│ 🔔 IT Investigation Completed (2 minutes ago)               │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Root Cause:                                            │ │
│ │ Firewall rule blocking VPN port 1194                   │ │
│ │                                                        │ │
│ │ Resolution Action:                                     │ │
│ │ Added firewall exception for customer IP              │ │
│ │                                                        │ │
│ │ IT Status: Resolved                                    │ │
│ │ Follow-up Required: No                                 │ │
│ │                                                        │ │
│ │ [View Full IT Logs] [Notify Customer]                 │ │
│ └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] Callback URL registered when triggering cross-scenario agent
- [ ] Triggered agent POSTs results to callback URL on completion
- [ ] Callback payload includes execution status, output, errors
- [ ] Failed callbacks retried 3 times with exponential backoff (1s, 2s, 4s)
- [ ] CS workflow handler updates ticket automatically based on callback
- [ ] UI shows real-time notification when callback received
- [ ] Integration tests for callback success and failure scenarios

---

### **US-F4-003: Monitor Cross-Scenario Triggers Dashboard**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** System Administrator (Michael Wong)
- **I want to** view a dashboard showing all cross-scenario triggers, their status, and performance metrics
- **So that** I can monitor system health, identify bottlenecks, and troubleshoot failed triggers

**Acceptance Criteria**:
1. ✅ **Trigger List**: Display all triggers with filters (scenario, status, date range)
2. ✅ **Status Breakdown**: Show count by status (pending, running, completed, failed)
3. ✅ **Performance Metrics**: Average trigger-to-callback time, success rate, retry count
4. ✅ **Failed Triggers**: Highlight failed triggers with error details
5. ✅ **Drill-down**: Click trigger to see full execution trace and logs
6. ✅ **Real-time Updates**: Dashboard auto-refreshes every 30 seconds

**Dashboard UI Mockup**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Cross-Scenario Collaboration - Monitoring Dashboard                          │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 📊 Overview (Last 24 Hours)                                                  │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐               │
│ │ Total        │ Completed    │ Running      │ Failed       │               │
│ │ 1,247        │ 1,189 (95%)  │ 43 (3%)      │ 15 (2%)      │               │
│ └──────────────┴──────────────┴──────────────┴──────────────┘               │
│                                                                               │
│ ⏱️  Performance Metrics                                                      │
│   Avg Trigger-to-Callback Time: 3.2 minutes                                 │
│   Success Rate: 95.4%  ██████████████████░░ (Target: ≥95%)                 │
│   Avg Retry Count: 0.3 (retries per trigger)                                │
│                                                                               │
│ 🔥 Top Triggered Agents (by volume)                                         │
│   1. IT.VPNTroubleshoot: 456 triggers (37%)                                 │
│   2. Finance.RefundApproval: 234 triggers (19%)                             │
│   3. IT.PasswordReset: 189 triggers (15%)                                   │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📋 Recent Triggers                                                           │
│ [Filter: All Scenarios ▼] [Status: All ▼] [Last 24h ▼]        [🔄 Refresh] │
│                                                                               │
│ ┌────────────┬──────────────┬────────┬────────────────┬──────────┬────────┐│
│ │ Trigger ID │ Source → Tgt │ Status │ Triggered At   │ Duration │ Action ││
│ ├────────────┼──────────────┼────────┼────────────────┼──────────┼────────┤│
│ │ trg_abc123 │ CS → IT      │ ✓ Done │ 10:30:00       │ 4m 23s   │ [View] ││
│ │ trg_def456 │ CS → Finance │ ⏳ Run │ 10:35:12       │ 1m 34s   │ [View] ││
│ │ trg_ghi789 │ Sales → IT   │ ❌ Fail│ 10:28:45       │ 5m 00s   │ [Retry]││
│ │ trg_jkl012 │ CS → IT      │ ✓ Done │ 10:25:30       │ 3m 12s   │ [View] ││
│ │ trg_mno345 │ HR → IT      │ ✓ Done │ 10:20:15       │ 2m 45s   │ [View] ││
│ └────────────┴──────────────┴────────┴────────────────┴──────────┴────────┘│
│                                                                               │
│ ⚠️  Failed Triggers (Last 24 Hours): 15                                     │
│ ┌────────────┬──────────────┬─────────────────────────────────────────────┐│
│ │ Trigger ID │ Source → Tgt │ Error                                       ││
│ ├────────────┼──────────────┼─────────────────────────────────────────────┤│
│ │ trg_ghi789 │ Sales → IT   │ Timeout: Target agent exceeded 5m timeout  ││
│ │ trg_pqr678 │ CS → Finance │ Auth Error: Invalid callback bearer token  ││
│ │ trg_stu901 │ HR → IT      │ Dead Letter: Max retries (3) exceeded      ││
│ └────────────┴──────────────┴─────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────────────────┘
```

**Drill-Down View (Click on Trigger)**:

```
┌──────────────────────────────────────────────────────────────────┐
│ Trigger Details: trg_abc123                               [Close] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Status: ✓ Completed                                             │
│                                                                  │
│ Source:                                                          │
│   Scenario: CS                                                   │
│   Workflow: CS-CustomerIssueResolution                           │
│   Execution ID: exec_xyz789                                      │
│   Step: step_3 (Execute Resolution Action)                       │
│                                                                  │
│ Target:                                                          │
│   Scenario: IT                                                   │
│   Agent: IT.VPNTroubleshoot                                      │
│   Execution ID: exec_it_456                                      │
│                                                                  │
│ Timeline:                                                        │
│   ▶ Triggered: 2025-11-18 10:30:00                              │
│   ▶ Event Published: 10:30:01 (1s)                              │
│   ▶ Agent Started: 10:30:15 (14s queue time)                    │
│   ▶ Agent Completed: 10:34:23 (4m 8s execution)                 │
│   ▶ Callback Sent: 10:34:24 (1s)                                │
│   ▶ Callback Received: 10:34:25 (1s)                            │
│   Total Duration: 4m 25s                                         │
│                                                                  │
│ Context Passed:                                                  │
│   {                                                              │
│     "customer_id": "CUST-5678",                                  │
│     "ticket_id": "CS-1234",                                      │
│     "issue_details": "Customer unable to connect to VPN",        │
│     "vpn_logs": "Connection timeout after 30s..."                │
│   }                                                              │
│                                                                  │
│ Results Received:                                                │
│   {                                                              │
│     "root_cause": "Firewall rule blocking VPN port 1194",        │
│     "resolution_action": "Added firewall exception",             │
│     "status": "Resolved"                                         │
│   }                                                              │
│                                                                  │
│ [View Source Execution] [View Target Execution] [View Event]    │
└──────────────────────────────────────────────────────────────────┘
```

**API: List Triggers with Filters**:

```bash
GET /api/triggers?scenario=CS&status=completed&date_from=2025-11-17&date_to=2025-11-18

Response:
{
  "total": 456,
  "page": 1,
  "page_size": 20,
  "triggers": [
    {
      "trigger_id": "trg_abc123",
      "event_type": "IT.VPN.Check",
      "source_scenario": "CS",
      "target_scenario": "IT",
      "target_agent": "IT.VPNTroubleshoot",
      "status": "completed",
      "triggered_at": "2025-11-18T10:30:00Z",
      "completed_at": "2025-11-18T10:34:25Z",
      "duration_seconds": 265,
      "retry_count": 0
    }
  ]
}
```

**Definition of Done**:
- [ ] Dashboard displays all triggers with filters
- [ ] Status breakdown shows count by status (pending, running, completed, failed)
- [ ] Performance metrics calculated (avg time, success rate, retry count)
- [ ] Failed triggers highlighted with error details
- [ ] Click trigger opens drill-down view with full timeline
- [ ] Dashboard auto-refreshes every 30 seconds
- [ ] Admin can manually retry failed triggers

---

### **US-F4-004: Configure Dead Letter Queue for Failed Triggers**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** System Reliability Engineer (SRE)
- **I want to** send failed triggers (after max retries) to a Dead Letter Queue (DLQ) for manual inspection
- **So that** we can analyze failures, fix issues, and replay messages without losing data

**Acceptance Criteria**:
1. ✅ **DLQ Configuration**: Configure max retries (default: 3) before sending to DLQ
2. ✅ **Auto-DLQ**: Failed triggers automatically sent to DLQ after max retries
3. ✅ **DLQ Inspection**: Admin can view DLQ messages in dashboard
4. ✅ **Manual Replay**: Admin can replay DLQ messages (re-trigger agent)
5. ✅ **Error Categorization**: DLQ messages tagged with error category (timeout, auth, validation)
6. ✅ **Alerts**: Send alert to ops team when DLQ size exceeds threshold (e.g., >50 messages)

**DLQ Configuration (YAML)**:

```yaml
event_bus:
  provider: "rabbitmq"  # or "azure_service_bus"
  connection: "amqp://localhost:5672"
  
  dead_letter_queue:
    enabled: true
    max_retries: 3
    retry_delay_seconds: [10, 30, 60]  # Exponential backoff
    dlq_name: "cross_scenario_dlq"
    alert_threshold: 50
    alert_recipients:
      - "ops-team@example.com"
      - "sre-team@example.com"
```

**DLQ Dashboard UI**:

```
┌──────────────────────────────────────────────────────────────────┐
│ Dead Letter Queue - Failed Triggers                      [Clear] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ⚠️  DLQ Size: 15 messages (Alert threshold: 50)                 │
│                                                                  │
│ 📊 Error Categories:                                            │
│   • Timeout: 8 (53%)                                            │
│   • Auth Error: 4 (27%)                                         │
│   • Validation Error: 2 (13%)                                   │
│   • Unknown: 1 (7%)                                             │
│                                                                  │
│ ────────────────────────────────────────────────────────────────│
│                                                                  │
│ [Filter: All Errors ▼] [Date: Last 7 Days ▼]                   │
│                                                                  │
│ ┌──────────────┬──────────┬───────┬─────────────┬─────────────┐│
│ │ Trigger ID   │ Source   │ Error │ Failed At   │ Action      ││
│ ├──────────────┼──────────┼───────┼─────────────┼─────────────┤│
│ │ trg_ghi789   │ CS → IT  │ Timeout│ 10:28:45   │ [Replay][X] ││
│ │ trg_pqr678   │ CS → Fin │ Auth  │ 09:15:30   │ [Replay][X] ││
│ │ trg_stu901   │ HR → IT  │ Timeout│ 08:45:12   │ [Replay][X] ││
│ └──────────────┴──────────┴───────┴─────────────┴─────────────┘│
│                                                                  │
│ [Select All] [Bulk Replay] [Bulk Delete] [Export CSV]           │
└──────────────────────────────────────────────────────────────────┘
```

**Replay DLQ Message (API)**:

```bash
POST /api/dlq/{message_id}/replay

Response:
{
  "message": "DLQ message replayed successfully",
  "original_trigger_id": "trg_ghi789",
  "new_trigger_id": "trg_xyz999",
  "status": "pending",
  "replayed_at": "2025-11-18T11:00:00Z"
}
```

**Definition of Done**:
- [ ] Failed triggers sent to DLQ after 3 retries
- [ ] DLQ messages displayed in admin dashboard
- [ ] Admin can replay individual or bulk DLQ messages
- [ ] Error categories calculated (timeout, auth, validation)
- [ ] Alert sent when DLQ size exceeds threshold
- [ ] Integration tests for DLQ retry and replay logic

---

## 4.3 Technical Implementation (Detailed)

### 4.3.1 CrossScenarioTriggerService Class

```python
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TriggerStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TriggerContext:
    """Context passed to triggered agent"""
    customer_id: Optional[str] = None
    ticket_id: Optional[str] = None
    order_id: Optional[str] = None
    additional_data: Dict[str, Any] = None

@dataclass
class TriggerConfig:
    """Configuration for cross-scenario trigger"""
    scenario: str
    agent: str
    event_type: str
    priority: str = "medium"
    context: Dict[str, Any] = None
    callback: Optional[Dict[str, Any]] = None

class CrossScenarioTriggerService:
    """
    Service for managing cross-scenario agent triggers via event bus
    """
    
    def __init__(
        self,
        event_bus_client,
        callback_client,
        db_session,
        config: Dict[str, Any]
    ):
        self.event_bus = event_bus_client
        self.callback_client = callback_client
        self.db = db_session
        self.config = config
        
        # Configuration
        self.max_retries = config.get("max_retries", 3)
        self.retry_delays = config.get("retry_delay_seconds", [10, 30, 60])
        self.callback_timeout = config.get("callback_timeout_seconds", 30)
    
    async def trigger_agent(
        self,
        source_workflow_id: str,
        source_execution_id: str,
        source_step_id: str,
        trigger_config: TriggerConfig
    ) -> str:
        """
        Trigger a cross-scenario agent via event bus
        
        Args:
            source_workflow_id: ID of workflow initiating trigger
            source_execution_id: ID of workflow execution
            source_step_id: ID of step that triggered
            trigger_config: Configuration for target agent
            
        Returns:
            trigger_id: Unique ID for tracking this trigger
        """
        trigger_id = self._generate_trigger_id()
        event_id = self._generate_event_id()
        
        logger.info(
            f"Triggering cross-scenario agent: "
            f"{trigger_config.scenario}.{trigger_config.agent} "
            f"from {source_workflow_id}"
        )
        
        # 1. Build event message
        event_message = {
            "event_id": event_id,
            "event_type": trigger_config.event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "source": {
                "scenario": self._extract_scenario(source_workflow_id),
                "workflow_id": source_workflow_id,
                "execution_id": source_execution_id,
                "step_id": source_step_id
            },
            "target": {
                "scenario": trigger_config.scenario,
                "agent": trigger_config.agent
            },
            "priority": trigger_config.priority,
            "context": trigger_config.context or {},
            "callback": trigger_config.callback,
            "metadata": {
                "trigger_id": trigger_id,
                "retry_count": 0,
                "expires_at": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            }
        }
        
        # 2. Save trigger record to database
        trigger_record = CrossScenarioTrigger(
            trigger_id=trigger_id,
            event_id=event_id,
            source_workflow_id=source_workflow_id,
            source_execution_id=source_execution_id,
            target_scenario=trigger_config.scenario,
            target_agent=trigger_config.agent,
            event_type=trigger_config.event_type,
            status=TriggerStatus.PENDING,
            context_data=trigger_config.context,
            callback_config=trigger_config.callback,
            triggered_at=datetime.utcnow()
        )
        self.db.add(trigger_record)
        self.db.commit()
        
        # 3. Publish event to event bus
        try:
            await self.event_bus.publish(
                exchange=f"scenario.{trigger_config.scenario}",
                routing_key=trigger_config.event_type,
                message=json.dumps(event_message),
                priority=self._map_priority(trigger_config.priority)
            )
            
            logger.info(f"Event published successfully: {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}", exc_info=True)
            
            # Update trigger status to failed
            trigger_record.status = TriggerStatus.FAILED
            trigger_record.error_message = str(e)
            self.db.commit()
            
            raise
        
        return trigger_id
    
    async def handle_callback(
        self,
        trigger_id: str,
        callback_data: Dict[str, Any]
    ):
        """
        Handle callback from triggered agent
        
        Args:
            trigger_id: ID of trigger that initiated execution
            callback_data: Results from triggered agent
        """
        logger.info(f"Received callback for trigger {trigger_id}")
        
        # 1. Load trigger record
        trigger = self.db.query(CrossScenarioTrigger).filter_by(
            trigger_id=trigger_id
        ).first()
        
        if not trigger:
            logger.error(f"Trigger not found: {trigger_id}")
            return
        
        # 2. Update trigger record
        trigger.status = callback_data["status"]
        trigger.completed_at = datetime.fromisoformat(callback_data["completed_at"])
        trigger.callback_received_at = datetime.utcnow()
        trigger.result_data = callback_data.get("execution", {}).get("output")
        trigger.duration_seconds = callback_data.get("duration_seconds")
        
        if callback_data["status"] == "failed":
            trigger.error_message = callback_data.get("execution", {}).get("error", {}).get("message")
        
        self.db.commit()
        
        logger.info(
            f"Trigger {trigger_id} callback processed: "
            f"status={callback_data['status']}, "
            f"duration={callback_data.get('duration_seconds')}s"
        )
    
    async def get_trigger_status(self, trigger_id: str) -> Dict[str, Any]:
        """
        Get current status of triggered agent execution
        
        Returns:
            Status details including execution progress (if available)
        """
        trigger = self.db.query(CrossScenarioTrigger).filter_by(
            trigger_id=trigger_id
        ).first()
        
        if not trigger:
            raise ValueError(f"Trigger not found: {trigger_id}")
        
        # Build response
        response = {
            "trigger_id": trigger.trigger_id,
            "event_id": trigger.event_id,
            "status": trigger.status,
            "source_workflow": trigger.source_workflow_id,
            "target_agent": f"{trigger.target_scenario}.{trigger.target_agent}",
            "triggered_at": trigger.triggered_at.isoformat(),
        }
        
        # Add execution details if available
        if trigger.target_execution_id:
            # Query target execution status (from workflow engine)
            execution_status = await self._query_execution_status(trigger.target_execution_id)
            response["target_execution"] = execution_status
        
        if trigger.completed_at:
            response["completed_at"] = trigger.completed_at.isoformat()
            response["duration_seconds"] = trigger.duration_seconds
        
        if trigger.error_message:
            response["error"] = trigger.error_message
        
        return response
    
    async def retry_failed_trigger(self, trigger_id: str) -> str:
        """
        Retry a failed trigger (e.g., from DLQ)
        
        Returns:
            New trigger_id for the retry
        """
        logger.info(f"Retrying failed trigger: {trigger_id}")
        
        # 1. Load original trigger
        original_trigger = self.db.query(CrossScenarioTrigger).filter_by(
            trigger_id=trigger_id
        ).first()
        
        if not original_trigger:
            raise ValueError(f"Trigger not found: {trigger_id}")
        
        # 2. Create new trigger with same config
        trigger_config = TriggerConfig(
            scenario=original_trigger.target_scenario,
            agent=original_trigger.target_agent,
            event_type=original_trigger.event_type,
            context=original_trigger.context_data,
            callback=original_trigger.callback_config
        )
        
        new_trigger_id = await self.trigger_agent(
            source_workflow_id=original_trigger.source_workflow_id,
            source_execution_id=original_trigger.source_execution_id,
            source_step_id="retry",
            trigger_config=trigger_config
        )
        
        # 3. Link original to retry
        original_trigger.retried_as = new_trigger_id
        self.db.commit()
        
        logger.info(f"Trigger retried: {trigger_id} → {new_trigger_id}")
        
        return new_trigger_id
    
    def _generate_trigger_id(self) -> str:
        """Generate unique trigger ID"""
        import uuid
        return f"trg_{uuid.uuid4().hex[:8]}"
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid
        return f"evt_{uuid.uuid4().hex[:8]}"
    
    def _extract_scenario(self, workflow_id: str) -> str:
        """Extract scenario name from workflow ID (e.g., CS-Workflow → CS)"""
        return workflow_id.split("-")[0] if "-" in workflow_id else "Unknown"
    
    def _map_priority(self, priority: str) -> int:
        """Map priority string to integer (for RabbitMQ)"""
        priority_map = {"low": 1, "medium": 5, "high": 9}
        return priority_map.get(priority.lower(), 5)
    
    async def _query_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Query execution status from workflow engine"""
        # Implementation depends on workflow engine API
        # For now, return placeholder
        return {
            "execution_id": execution_id,
            "progress": 65,
            "current_step": "Processing..."
        }
```

### 4.3.2 Event Bus Listener (Consumer)

```python
import pika
import json
from typing import Callable

class RabbitMQEventListener:
    """
    Event bus listener for receiving cross-scenario triggers
    """
    
    def __init__(
        self,
        connection_url: str,
        scenario: str,
        workflow_engine,
        callback_service
    ):
        self.connection_url = connection_url
        self.scenario = scenario
        self.workflow_engine = workflow_engine
        self.callback_service = callback_service
        
        self.connection = None
        self.channel = None
    
    def start_listening(self):
        """
        Start listening for events targeted at this scenario
        """
        logger.info(f"Starting event listener for scenario: {self.scenario}")
        
        # 1. Connect to RabbitMQ
        self.connection = pika.BlockingConnection(
            pika.URLParameters(self.connection_url)
        )
        self.channel = self.connection.channel()
        
        # 2. Declare exchange (topic exchange for routing)
        exchange_name = f"scenario.{self.scenario}"
        self.channel.exchange_declare(
            exchange=exchange_name,
            exchange_type="topic",
            durable=True
        )
        
        # 3. Declare queue
        queue_name = f"{self.scenario}_triggers"
        self.channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={
                "x-max-priority": 10,  # Support priority messages
                "x-message-ttl": 7200000  # 2 hour TTL
            }
        )
        
        # 4. Bind queue to exchange (listen to all events for this scenario)
        self.channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key=f"{self.scenario}.#"  # Wildcard: IT.* matches IT.VPN.Check, IT.Password.Reset
        )
        
        # 5. Set QoS (prefetch 1 message at a time for fair distribution)
        self.channel.basic_qos(prefetch_count=1)
        
        # 6. Start consuming
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=self._handle_message
        )
        
        logger.info(f"Listening on queue: {queue_name}")
        self.channel.start_consuming()
    
    def _handle_message(self, ch, method, properties, body):
        """
        Handle received event message
        """
        try:
            event = json.loads(body)
            logger.info(f"Received event: {event['event_id']}, type: {event['event_type']}")
            
            # 1. Extract target agent
            target_agent = event["target"]["agent"]
            context = event["context"]
            callback_config = event.get("callback")
            trigger_id = event["metadata"]["trigger_id"]
            
            # 2. Trigger workflow execution
            execution_id = self.workflow_engine.execute_agent(
                agent_id=target_agent,
                input_data=context,
                metadata={
                    "trigger_id": trigger_id,
                    "source_workflow": event["source"]["workflow_id"]
                }
            )
            
            logger.info(f"Agent {target_agent} triggered, execution: {execution_id}")
            
            # 3. Register callback handler (async)
            if callback_config:
                asyncio.create_task(
                    self._wait_and_callback(
                        execution_id=execution_id,
                        trigger_id=trigger_id,
                        callback_config=callback_config
                    )
                )
            
            # 4. Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Failed to handle event: {e}", exc_info=True)
            
            # Reject message and requeue (will retry up to max_retries)
            retry_count = properties.headers.get("x-retry-count", 0) if properties.headers else 0
            
            if retry_count < 3:
                # Requeue with incremented retry count
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                logger.warning(f"Message requeued, retry count: {retry_count + 1}")
            else:
                # Max retries exceeded, send to DLQ
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                logger.error(f"Message sent to DLQ after {retry_count} retries")
    
    async def _wait_and_callback(
        self,
        execution_id: str,
        trigger_id: str,
        callback_config: Dict[str, Any]
    ):
        """
        Wait for execution to complete, then send callback
        """
        try:
            # Poll execution status until complete
            while True:
                status = await self.workflow_engine.get_execution_status(execution_id)
                
                if status["status"] in ["completed", "failed"]:
                    break
                
                await asyncio.sleep(5)  # Poll every 5 seconds
            
            # Build callback payload
            callback_payload = {
                "trigger_id": trigger_id,
                "status": status["status"],
                "execution": {
                    "execution_id": execution_id,
                    "output": status.get("output"),
                    "error": status.get("error")
                },
                "completed_at": datetime.utcnow().isoformat(),
                "duration_seconds": status.get("duration_seconds")
            }
            
            # Send callback
            await self.callback_service.send_callback(
                url=callback_config["url"],
                method=callback_config.get("method", "POST"),
                payload=callback_payload,
                auth=callback_config.get("auth")
            )
            
            logger.info(f"Callback sent for trigger {trigger_id}")
            
        except Exception as e:
            logger.error(f"Callback failed for trigger {trigger_id}: {e}", exc_info=True)
```

---

## 4.4 Database Schema

```sql
CREATE TABLE cross_scenario_triggers (
    id SERIAL PRIMARY KEY,
    trigger_id VARCHAR(50) UNIQUE NOT NULL,
    event_id VARCHAR(50) NOT NULL,
    
    -- Source information
    source_workflow_id VARCHAR(100) NOT NULL,
    source_execution_id VARCHAR(100) NOT NULL,
    source_scenario VARCHAR(50),
    
    -- Target information
    target_scenario VARCHAR(50) NOT NULL,
    target_agent VARCHAR(100) NOT NULL,
    target_execution_id VARCHAR(100),
    event_type VARCHAR(100) NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL,  -- pending | running | completed | failed
    
    -- Context and results
    context_data JSONB,
    result_data JSONB,
    callback_config JSONB,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    retried_as VARCHAR(50),  -- Link to retry trigger
    
    -- Timestamps
    triggered_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    callback_received_at TIMESTAMP,
    duration_seconds INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_trigger_status ON cross_scenario_triggers(status, triggered_at DESC);
CREATE INDEX idx_trigger_source ON cross_scenario_triggers(source_workflow_id, source_execution_id);
CREATE INDEX idx_trigger_target ON cross_scenario_triggers(target_scenario, target_agent);
CREATE INDEX idx_trigger_event_type ON cross_scenario_triggers(event_type);
```

---

## 4.5 Non-Functional Requirements (NFR)

| **Category** | **Requirement** | **Target** | **Measurement** |
|-------------|----------------|-----------|----------------|
| **Performance** | Event publish latency | < 100ms | APM monitoring |
| | Queue consumption latency | < 500ms | RabbitMQ metrics |
| | Callback delivery time | < 2 seconds | HTTP logging |
| **Scalability** | Concurrent triggers | 1000+ per day | Load testing |
| | Queue depth | Handle 500+ pending messages | RabbitMQ dashboard |
| **Reliability** | Event delivery guarantee | At-least-once delivery | RabbitMQ confirms |
| | Callback retry | 3 attempts with exponential backoff | Configuration |
| | Dead Letter Queue | Failed messages after 3 retries | DLQ monitoring |
| **Observability** | Trigger success rate | ≥95% | Dashboard metrics |
| | End-to-end latency | P95 < 5 minutes | Distributed tracing |
| | DLQ size | Alert if >50 messages | Alerting system |

---

## 4.6 Testing Strategy

**Unit Tests**:
- Trigger condition evaluation (YAML parsing)
- Event message serialization
- Callback payload generation
- Retry logic with exponential backoff

**Integration Tests**:
- End-to-end trigger flow (CS → IT)
- Callback delivery and handling
- DLQ processing and replay
- Multiple concurrent triggers

**Load Tests**:
- 1000 triggers per hour
- Measure queue depth and latency
- Verify no message loss

---

## 4.7 Risks and Mitigation

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|---------|----------------|-----------|---------------|
| Event bus downtime | Low | High | Health checks, circuit breaker, fallback to direct HTTP |
| Callback timeout | Medium | Medium | 3 retries with exponential backoff, DLQ for failures |
| Message loss | Low | High | RabbitMQ durable queues, publisher confirms, consumer acks |
| Circular triggers | Low | High | Max trigger depth limit, cycle detection |
| DLQ overflow | Medium | Medium | Alert at 50 messages, automated cleanup policy |

---

## 4.8 Future Enhancements (Post-MVP)

1. **Bi-directional Triggers**: IT agent can trigger CS agent back (closed loop)
2. **Trigger Orchestration**: Chain multiple cross-scenario triggers (CS → IT → Finance)
3. **Conditional Callbacks**: Only callback if certain conditions met
4. **Webhook Support**: External systems can trigger IPA workflows via webhooks
5. **Trigger Analytics**: Track most common trigger patterns, optimize routing
6. **GraphQL Subscriptions**: Real-time trigger status updates via GraphQL subscriptions

---

**Next Feature**: [F5. Learning-based Collaboration →](./feature-05-learning.md)
