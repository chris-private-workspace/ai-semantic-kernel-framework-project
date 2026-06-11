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

