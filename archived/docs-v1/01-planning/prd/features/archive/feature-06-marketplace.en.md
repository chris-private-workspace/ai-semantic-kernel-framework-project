# F6. Agent Marketplace

**Category**: Developer Experience & Ecosystem  
**Priority**: P1 (Should Have - Accelerates Adoption)  
**Development Time**: 2 weeks  
**Complexity**: ⭐⭐⭐⭐ (High)  
**Dependencies**: F1 (Sequential Orchestration), JSON Schema Validator, Code Sandbox (optional), Azure Blob Storage  
**Risk Level**: Medium (Code quality, security vulnerabilities, licensing)

---

## 📑 Navigation

- [← Features Overview](../prd-appendix-a-features-overview.md)
- [← F5: Learning-based Collaboration](./feature-05-learning.md)
- **F6: Agent Marketplace** ← You are here
- [→ F7: DevUI Integration](./feature-07-devui.md)

---

## 6.1 Feature Overview

**What is Agent Marketplace?**

Agent Marketplace is a **built-in template library** with 6-8 pre-configured agent templates (Customer Service, IT Support, Sales, Finance, HR, Data Analysis) that developers can **deploy with one click**. Each template includes complete prompt engineering, JSON Schema for inputs/outputs, Python code (if needed), and example workflows.

**Why This Matters**:
- **Faster Time-to-Value**: Deploy production-ready agents in minutes instead of days
- **Best Practices**: Templates built by experts with proven prompt engineering
- **Learning Resource**: Developers learn by example, understand patterns
- **Consistency**: Standardized agent structure across organization
- **Extensibility**: Templates are starting points, fully customizable

**Key Capabilities**:
1. **Built-in Templates**: 6-8 curated agent templates for common use cases
2. **One-Click Deployment**: Deploy template → Automatically create agent, workflow, schemas
3. **Customization**: Edit prompts, schemas, code before deployment
4. **Version Control**: Templates versioned (v1.0, v1.1), track updates
5. **Template Validation**: JSON Schema validation, code syntax checks
6. **Preview Mode**: Test template in sandbox before deployment
7. **Usage Analytics**: Track which templates are most popular

**Business Value**:
- **Onboarding Speed**: New developers productive in 1 hour instead of 1 week
- **Reduced Errors**: Pre-validated templates reduce configuration mistakes by 80%
- **Knowledge Sharing**: Capture and share best practices organization-wide
- **Lower TCO**: Reusable templates reduce development cost by 40%
- **Competitive Edge**: Rich ecosystem attracts more users to platform

**Built-in Templates (MVP)**:

| Template ID | Name | Category | Use Case | Complexity |
|------------|------|----------|----------|------------|
| `tmpl_cs_refund` | CS Refund Decision | Customer Service | Approve/reject refund requests based on policy | ⭐⭐⭐ |
| `tmpl_it_password` | IT Password Reset | IT Support | Validate user identity, reset password | ⭐⭐ |
| `tmpl_sales_lead` | Sales Lead Scoring | Sales | Score leads based on firmographics, behavior | ⭐⭐⭐⭐ |
| `tmpl_fin_expense` | Finance Expense Approval | Finance | Approve/reject expense claims based on rules | ⭐⭐⭐ |
| `tmpl_hr_interview` | HR Interview Scheduler | HR | Schedule candidate interviews, avoid conflicts | ⭐⭐⭐ |
| `tmpl_data_report` | Data Report Generator | Data Analysis | Generate summary reports from structured data | ⭐⭐⭐⭐ |

**Real-World Example**:

```
Traditional Approach (Build from Scratch):
1. Developer reads documentation (2 hours)
2. Design agent prompt (3 hours)
3. Define JSON Schema for inputs (1 hour)
4. Write validation logic (2 hours)
5. Test with sample data (2 hours)
6. Debug and refine (4 hours)
Total: 14 hours

With Agent Marketplace:
1. Browse marketplace, select "CS Refund Decision" template
2. Preview template (5 minutes)
3. Click "Deploy"
4. System creates agent with pre-configured prompt, schema, examples
5. Customize for specific business rules (30 minutes)
6. Test with sample data (15 minutes)
Total: 50 minutes (93% faster)
```

**Architecture Overview**:

```
┌──────────────────┐
│  Marketplace UI  │
│  (Browse, Search)│
└────────┬─────────┘
         │
         │ 1. Select template
         ▼
┌──────────────────┐         ┌───────────────┐
│  Template Detail │────────►│  Template JSON│
│  Page (Preview)  │         │  (Blob Storage)
└────────┬─────────┘         └───────────────┘
         │
         │ 2. Deploy
         ▼
┌──────────────────┐
│  Deployment      │
│  Service         │
└────────┬─────────┘
         │
         │ 3. Create resources
         ▼
┌──────────────────┬──────────────────┬──────────────────┐
│  Agent           │  Workflow        │  JSON Schema     │
│  (agents table)  │  (workflows)     │  (schemas)       │
└──────────────────┴──────────────────┴──────────────────┘
```

---

## 6.2 User Stories (Complete)

### **US-F6-001: Browse and Search Agent Templates**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** browse a marketplace of pre-built agent templates, filter by category, and search by keyword
- **So that** I can quickly find a template that matches my use case instead of building from scratch

**Acceptance Criteria**:
1. ✅ **Template Gallery**: Display all templates in grid view with thumbnail, name, description
2. ✅ **Category Filter**: Filter by category (Customer Service, IT Support, Sales, Finance, HR, Data Analysis)
3. ✅ **Keyword Search**: Search templates by name, description, tags
4. ✅ **Sorting**: Sort by popularity (deploy count), newest, name (A-Z)
5. ✅ **Template Card**: Each card shows:
   - Template name and icon
   - Short description (1-2 sentences)
   - Category badge
   - Complexity rating (⭐⭐⭐)
   - Deploy count
   - Version (e.g., v1.2)
6. ✅ **Click to Detail**: Click template opens detail page with full info

**Marketplace UI (Gallery View)**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Agent Marketplace                                     [Search...] [Category ▼]│
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 🎯 Featured Templates (Most Popular)                                         │
│                                                                               │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│ │ 🎫 CS Refund     │  │ 🔑 IT Password   │  │ 📊 Sales Lead    │           │
│ │ Decision         │  │ Reset            │  │ Scoring          │           │
│ │                  │  │                  │  │                  │           │
│ │ Approve/reject   │  │ Validate user    │  │ Score leads based│           │
│ │ refund requests  │  │ and reset pass   │  │ on firmographics │           │
│ │                  │  │                  │  │                  │           │
│ │ Category: CS     │  │ Category: IT     │  │ Category: Sales  │           │
│ │ Complexity: ⭐⭐⭐│  │ Complexity: ⭐⭐  │  │ Complexity: ⭐⭐⭐⭐│           │
│ │ Deploys: 234     │  │ Deploys: 189     │  │ Deploys: 156     │           │
│ │ Version: v1.2    │  │ Version: v1.0    │  │ Version: v1.3    │           │
│ │                  │  │                  │  │                  │           │
│ │ [View Details]   │  │ [View Details]   │  │ [View Details]   │           │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                               │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│ │ 💰 Finance       │  │ 👥 HR Interview  │  │ 📈 Data Report   │           │
│ │ Expense Approval │  │ Scheduler        │  │ Generator        │           │
│ │                  │  │                  │  │                  │           │
│ │ [View Details]   │  │ [View Details]   │  │ [View Details]   │           │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                               │
│ Filter by Category: [All] [CS] [IT] [Sales] [Finance] [HR] [Data]           │
│ Sort by: [Popularity ▼]                                                      │
└───────────────────────────────────────────────────────────────────────────────┘
```

**API: List Templates**:

```bash
GET /api/marketplace/templates?category=CS&sort=popularity&page=1

Response:
{
  "total": 6,
  "page": 1,
  "page_size": 20,
  "templates": [
    {
      "template_id": "tmpl_cs_refund",
      "name": "CS Refund Decision",
      "description": "Approve or reject customer refund requests based on company policy",
      "category": "Customer Service",
      "complexity": 3,
      "version": "1.2",
      "deploy_count": 234,
      "tags": ["customer service", "refund", "policy"],
      "created_at": "2025-09-15T10:00:00Z",
      "updated_at": "2025-11-01T14:30:00Z"
    }
  ]
}
```

**Definition of Done**:
- [ ] Marketplace UI displays all templates in grid view
- [ ] Filter by category works (CS, IT, Sales, Finance, HR, Data)
- [ ] Keyword search filters templates by name/description
- [ ] Sort by popularity, newest, name works
- [ ] Template card shows all required info (name, category, complexity, deploys, version)
- [ ] Click template opens detail page

---

### **US-F6-002: View Template Details and Preview**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 3 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** view complete template details including prompt, input/output schema, code examples, and test it in a sandbox
- **So that** I can understand exactly what the template does before deploying

**Acceptance Criteria**:
1. ✅ **Template Overview**: Display name, description, category, complexity, version, author
2. ✅ **Prompt Preview**: Show complete LLM prompt template with placeholders
3. ✅ **Input Schema**: Display JSON Schema for inputs (with examples)
4. ✅ **Output Schema**: Display JSON Schema for outputs (with examples)
5. ✅ **Code Preview**: Show Python code (if template includes custom logic)
6. ✅ **Example Workflow**: Show sample workflow YAML using this agent
7. ✅ **Test Sandbox**: Interactive form to test agent with sample input
8. ✅ **Deploy Button**: One-click deploy button

**Template Detail Page UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ ← Back to Marketplace          CS Refund Decision v1.2          [Deploy]      │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 📋 Overview                                                                   │
│   Category: Customer Service                                                  │
│   Complexity: ⭐⭐⭐ (Medium)                                                  │
│   Author: IPA Team                                                            │
│   Deploys: 234 | Last Updated: Nov 1, 2025                                   │
│                                                                               │
│   Description:                                                                │
│   Automatically approve or reject customer refund requests based on company   │
│   policy (30-day return window, customer tier, product type). Uses GPT-4o     │
│   to analyze request details and provide reasoning.                           │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🤖 LLM Prompt Template                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ You are an AI assistant helping with customer refund decisions.         │ │
│ │                                                                          │ │
│ │ Company Policy:                                                          │ │
│ │ - Standard returns: 30-day window                                        │ │
│ │ - Premium customers: 45-day window                                       │ │
│ │ - Defective products: Always approve (regardless of time)               │ │
│ │ - Customer loyalty: Consider customer tier and purchase history          │ │
│ │                                                                          │ │
│ │ Input:                                                                   │ │
│ │ {input_data}                                                             │ │
│ │                                                                          │ │
│ │ Analyze and provide decision in JSON format:                             │ │
│ │ {{                                                                       │ │
│ │   "decision": "Approved" or "Rejected",                                  │ │
│ │   "reasoning": "Brief explanation",                                      │ │
│ │   "refund_amount": number,                                               │ │
│ │   "follow_up_action": "string"                                           │ │
│ │ }}                                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📥 Input Schema (JSON Schema)                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ {                                                                        │ │
│ │   "type": "object",                                                      │ │
│ │   "required": ["customer_id", "product", "issue", "purchase_date"],     │ │
│ │   "properties": {                                                        │ │
│ │     "customer_id": {"type": "string"},                                   │ │
│ │     "product": {"type": "string"},                                       │ │
│ │     "issue": {"type": "string", "enum": ["defective", "not_satisfied"]},│ │
│ │     "purchase_date": {"type": "string", "format": "date"},               │ │
│ │     "customer_tier": {"type": "string", "enum": ["standard", "premium"]}│ │
│ │   }                                                                      │ │
│ │ }                                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 📤 Output Schema (JSON Schema)                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ {                                                                        │ │
│ │   "type": "object",                                                      │ │
│ │   "required": ["decision", "reasoning"],                                 │ │
│ │   "properties": {                                                        │ │
│ │     "decision": {"type": "string", "enum": ["Approved", "Rejected"]},   │ │
│ │     "reasoning": {"type": "string"},                                     │ │
│ │     "refund_amount": {"type": "number"},                                 │ │
│ │     "follow_up_action": {"type": "string"}                               │ │
│ │   }                                                                      │ │
│ │ }                                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🧪 Test in Sandbox                                                           │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Customer ID: [CUST-5678        ]                                         │ │
│ │ Product:     [Wireless Headphones]                                       │ │
│ │ Issue:       [Defective ▼]                                               │ │
│ │ Purchase Date: [2025-10-15   ]                                           │ │
│ │ Customer Tier: [Premium ▼]                                               │ │
│ │                                                                          │ │
│ │ [Run Test]                                                               │ │
│ │                                                                          │ │
│ │ Result:                                                                  │ │
│ │ ✓ Decision: Approved                                                     │ │
│ │   Reasoning: Premium customer, defective product within 45-day policy    │ │
│ │   Refund Amount: $99.99                                                  │ │
│ │   Follow-up: Send return label via email                                 │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📝 Example Workflow (YAML)                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ workflow:                                                                │ │
│ │   id: "refund-workflow"                                                  │ │
│ │   steps:                                                                 │ │
│ │     - id: "step_1"                                                       │ │
│ │       agent: "CS.RefundDecision"                                         │ │
│ │       input:                                                             │ │
│ │         customer_id: "${workflow.input.customer_id}"                     │ │
│ │         product: "${workflow.input.product}"                             │ │
│ │         issue: "defective"                                               │ │
│ │         purchase_date: "2025-10-15"                                      │ │
│ │         customer_tier: "premium"                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [🚀 Deploy This Template]  [⭐ Mark as Favorite]                            │
└───────────────────────────────────────────────────────────────────────────────┘
```

**API: Get Template Details**:

```bash
GET /api/marketplace/templates/tmpl_cs_refund

Response:
{
  "template_id": "tmpl_cs_refund",
  "name": "CS Refund Decision",
  "description": "Approve or reject customer refund requests based on company policy",
  "category": "Customer Service",
  "complexity": 3,
  "version": "1.2",
  "author": "IPA Team",
  "prompt_template": "You are an AI assistant...",
  "input_schema": {
    "type": "object",
    "required": ["customer_id", "product", "issue", "purchase_date"],
    "properties": {...}
  },
  "output_schema": {
    "type": "object",
    "required": ["decision", "reasoning"],
    "properties": {...}
  },
  "code": null,  // Optional Python code
  "example_workflow": "workflow:\n  id: \"refund-workflow\"...",
  "tags": ["customer service", "refund", "policy"],
  "deploy_count": 234,
  "created_at": "2025-09-15T10:00:00Z",
  "updated_at": "2025-11-01T14:30:00Z"
}
```

**Sandbox Test API**:

```bash
POST /api/marketplace/templates/tmpl_cs_refund/test
{
  "input": {
    "customer_id": "CUST-5678",
    "product": "Wireless Headphones",
    "issue": "defective",
    "purchase_date": "2025-10-15",
    "customer_tier": "premium"
  }
}

Response:
{
  "output": {
    "decision": "Approved",
    "reasoning": "Premium customer, defective product within 45-day policy",
    "refund_amount": 99.99,
    "follow_up_action": "Send return label via email"
  },
  "execution_time_ms": 2340,
  "tokens_used": 456,
  "cost_usd": 0.0137
}
```

**Definition of Done**:
- [ ] Template detail page shows all required info (prompt, schemas, code, example)
- [ ] Prompt template displayed with syntax highlighting
- [ ] Input/output JSON Schema displayed with collapsible sections
- [ ] Sandbox test form allows user to input sample data
- [ ] Test API executes template and returns result
- [ ] Example workflow YAML displayed
- [ ] Deploy button redirects to deployment flow

---

### **US-F6-003: Deploy Template with One Click**

**Priority**: P1 (Should Have)  
**Estimated Dev Time**: 4 days  
**Complexity**: ⭐⭐⭐⭐

**User Story**:
- **As a** Developer (Emily Zhang)
- **I want to** deploy a template with one click and automatically create an agent, workflow, and schemas in my workspace
- **So that** I can start using the agent immediately without manual configuration

**Acceptance Criteria**:
1. ✅ **Deploy Button**: Click "Deploy" opens deployment modal
2. ✅ **Customization Options**: Allow user to customize:
   - Agent name (default: template name)
   - Agent ID (auto-generated, editable)
   - LLM model (GPT-4o, GPT-4, GPT-3.5)
   - Temperature (0.0 - 1.0)
   - Max tokens (100 - 4000)
3. ✅ **Validation**: Validate agent ID uniqueness before deployment
4. ✅ **Automatic Creation**: System creates:
   - Agent record in `agents` table
   - Input/output schemas in `schemas` table
   - Example workflow in `workflows` table (optional)
5. ✅ **Success Feedback**: Show success message with link to new agent
6. ✅ **Deploy Analytics**: Track deployment count per template

**Deployment Modal UI**:

```
┌───────────────────────────────────────────────────────────────┐
│ Deploy Template: CS Refund Decision                   [Close] │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ 🚀 Deploy this template to your workspace                    │
│                                                               │
│ Agent Configuration:                                          │
│                                                               │
│ Agent Name: *                                                 │
│ [CS Refund Decision Agent                                  ]  │
│                                                               │
│ Agent ID: *                                                   │
│ [cs_refund_decision_001                                    ]  │
│ ℹ️  Must be unique across workspace                          │
│                                                               │
│ LLM Model: *                                                  │
│ [GPT-4o ▼] (Recommended)                                     │
│   Options: GPT-4o, GPT-4, GPT-3.5-turbo                      │
│                                                               │
│ Temperature: [0.3        ] (0.0 = deterministic, 1.0 = creative)│
│                                                               │
│ Max Tokens: [2000       ] (100 - 4000)                       │
│                                                               │
│ ────────────────────────────────────────────────────────────│
│                                                               │
│ Additional Options:                                           │
│ ☑ Create example workflow                                    │
│ ☐ Enable learning (requires F5)                              │
│ ☐ Add to favorites                                            │
│                                                               │
│ ────────────────────────────────────────────────────────────│
│                                                               │
│ What will be created:                                         │
│   ✓ Agent: cs_refund_decision_001                            │
│   ✓ Input Schema: cs_refund_decision_input_v1                │
│   ✓ Output Schema: cs_refund_decision_output_v1              │
│   ✓ Example Workflow: refund_workflow_001 (optional)         │
│                                                               │
│ [Cancel]                                    [🚀 Deploy Now]  │
└───────────────────────────────────────────────────────────────┘
```

**Deployment Success Modal**:

```
┌───────────────────────────────────────────────────────────────┐
│ ✅ Deployment Successful!                             [Close] │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Your agent has been deployed successfully!                    │
│                                                               │
│ Agent Details:                                                │
│   Name: CS Refund Decision Agent                              │
│   ID: cs_refund_decision_001                                  │
│   Status: ✓ Active                                            │
│                                                               │
│ Created Resources:                                            │
│   ✓ Agent (agents/cs_refund_decision_001)                    │
│   ✓ Input Schema (schemas/cs_refund_decision_input_v1)       │
│   ✓ Output Schema (schemas/cs_refund_decision_output_v1)     │
│   ✓ Example Workflow (workflows/refund_workflow_001)         │
│                                                               │
│ Next Steps:                                                   │
│   1. [View Agent Details] → Configure advanced settings      │
│   2. [Run Example Workflow] → Test with sample data          │
│   3. [Integrate into Workflow] → Add to existing workflow    │
│                                                               │
│ [Go to Agent Page]  [Run Example]  [Close]                   │
└───────────────────────────────────────────────────────────────┘
```

**Deployment API**:

```bash
POST /api/marketplace/templates/tmpl_cs_refund/deploy
{
  "agent_name": "CS Refund Decision Agent",
  "agent_id": "cs_refund_decision_001",
  "llm_model": "gpt-4o",
  "temperature": 0.3,
  "max_tokens": 2000,
  "create_example_workflow": true,
  "enable_learning": false
}

Response:
{
  "message": "Template deployed successfully",
  "agent_id": "cs_refund_decision_001",
  "resources_created": {
    "agent": "agents/cs_refund_decision_001",
    "input_schema": "schemas/cs_refund_decision_input_v1",
    "output_schema": "schemas/cs_refund_decision_output_v1",
    "example_workflow": "workflows/refund_workflow_001"
  },
  "deployed_at": "2025-11-18T10:30:00Z"
}
```

**Deployment Service Implementation**:

```python
class MarketplaceDeploymentService:
    """
    Service for deploying marketplace templates
    """
    
    def __init__(self, db_session, workflow_service, schema_service):
        self.db = db_session
        self.workflow_service = workflow_service
        self.schema_service = schema_service
    
    async def deploy_template(
        self,
        template_id: str,
        agent_name: str,
        agent_id: str,
        llm_model: str,
        temperature: float,
        max_tokens: int,
        create_example_workflow: bool = True,
        enable_learning: bool = False
    ) -> Dict[str, Any]:
        """
        Deploy marketplace template to user's workspace
        
        Creates:
        - Agent record
        - Input/output schemas
        - Example workflow (optional)
        """
        # 1. Load template
        template = await self._load_template(template_id)
        
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # 2. Validate agent_id uniqueness
        existing_agent = self.db.query(Agent).filter_by(agent_id=agent_id).first()
        if existing_agent:
            raise ValueError(f"Agent ID already exists: {agent_id}")
        
        # 3. Create agent
        agent = Agent(
            agent_id=agent_id,
            name=agent_name,
            description=template["description"],
            prompt_template=template["prompt_template"],
            llm_model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            input_schema_id=f"{agent_id}_input_v1",
            output_schema_id=f"{agent_id}_output_v1",
            learning_enabled=enable_learning,
            deployed_from_template=template_id,
            status="active"
        )
        self.db.add(agent)
        
        # 4. Create input schema
        input_schema = Schema(
            schema_id=f"{agent_id}_input_v1",
            name=f"{agent_name} Input Schema",
            schema_type="input",
            json_schema=template["input_schema"],
            version="1.0"
        )
        self.db.add(input_schema)
        
        # 5. Create output schema
        output_schema = Schema(
            schema_id=f"{agent_id}_output_v1",
            name=f"{agent_name} Output Schema",
            schema_type="output",
            json_schema=template["output_schema"],
            version="1.0"
        )
        self.db.add(output_schema)
        
        # 6. Create example workflow (optional)
        workflow_id = None
        if create_example_workflow and template.get("example_workflow"):
            workflow_yaml = template["example_workflow"].replace(
                "${agent_id}",
                agent_id
            )
            workflow = await self.workflow_service.create_workflow_from_yaml(
                workflow_yaml=workflow_yaml,
                workflow_id=f"{agent_id}_example",
                name=f"{agent_name} Example Workflow"
            )
            workflow_id = workflow.workflow_id
        
        self.db.commit()
        
        # 7. Update template deploy count
        await self._increment_deploy_count(template_id)
        
        logger.info(f"Template deployed: {template_id} → {agent_id}")
        
        return {
            "message": "Template deployed successfully",
            "agent_id": agent_id,
            "resources_created": {
                "agent": f"agents/{agent_id}",
                "input_schema": f"schemas/{agent_id}_input_v1",
                "output_schema": f"schemas/{agent_id}_output_v1",
                "example_workflow": f"workflows/{workflow_id}" if workflow_id else None
            },
            "deployed_at": datetime.utcnow().isoformat()
        }
    
    async def _load_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Load template from database or blob storage"""
        # Load from templates table or Azure Blob Storage
        template = self.db.query(MarketplaceTemplate).filter_by(
            template_id=template_id
        ).first()
        
        if not template:
            return None
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "prompt_template": template.prompt_template,
            "input_schema": template.input_schema,
            "output_schema": template.output_schema,
            "example_workflow": template.example_workflow
        }
    
    async def _increment_deploy_count(self, template_id: str):
        """Increment template deploy count"""
        template = self.db.query(MarketplaceTemplate).filter_by(
            template_id=template_id
        ).first()
        
        if template:
            template.deploy_count += 1
            self.db.commit()
```

**Definition of Done**:
- [ ] Deploy button opens modal with customization options
- [ ] User can customize agent name, ID, LLM model, temperature, max tokens
- [ ] System validates agent ID uniqueness before deployment
- [ ] System creates agent, input schema, output schema, example workflow
- [ ] Success modal shows created resources with links
- [ ] Deploy count incremented in template analytics
- [ ] Integration tests for full deployment flow

---

### **US-F6-004: Template Usage Analytics**

**Priority**: P2 (Nice to Have)  
**Estimated Dev Time**: 2 days  
**Complexity**: ⭐⭐⭐

**User Story**:
- **As a** Platform Administrator (Michael Wong)
- **I want to** view analytics showing which templates are most popular, deploy trends, and user feedback
- **So that** I can identify which templates to improve or add more of

**Acceptance Criteria**:
1. ✅ **Popularity Ranking**: Show templates ranked by deploy count
2. ✅ **Deploy Trend**: Chart showing deploys over time (daily/weekly/monthly)
3. ✅ **Category Distribution**: Pie chart showing deploys by category
4. ✅ **User Feedback**: Collect and display user ratings (1-5 stars) for templates
5. ✅ **Search Analytics**: Track which keywords users search for (identify gaps)

**Analytics Dashboard UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Marketplace Analytics                                            [Export CSV] │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 📊 Overview (Last 30 Days)                                                   │
│   Total Templates: 6                                                          │
│   Total Deploys: 1,247                                                        │
│   Avg Deploys per Template: 208                                              │
│   User Satisfaction: 4.6/5 ⭐⭐⭐⭐⭐                                          │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🏆 Most Popular Templates (by Deploy Count)                                  │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. CS Refund Decision: 234 deploys (18.8%)  ████████████████░░░░        │ │
│ │ 2. IT Password Reset: 189 deploys (15.2%)   █████████████░░░░░░░        │ │
│ │ 3. Sales Lead Scoring: 156 deploys (12.5%)  ██████████░░░░░░░░░         │ │
│ │ 4. Finance Expense: 145 deploys (11.6%)     █████████░░░░░░░░░░         │ │
│ │ 5. HR Interview: 134 deploys (10.7%)        ████████░░░░░░░░░░░         │ │
│ │ 6. Data Report: 389 deploys (31.2%)         ████████████████████         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 📈 Deploy Trend (Last 30 Days)                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 60│                                                        ●              │ │
│ │   │                                                   ●───●               │ │
│ │ 50│                                              ●───●                    │ │
│ │   │                                         ●───●                         │ │
│ │ 40│                                    ●───●                              │ │
│ │   │                               ●───●                                   │ │
│ │ 30│                          ●───●                                        │ │
│ │   │                     ●───●                                             │ │
│ │ 20│                ●───●                                                  │ │
│ │   │           ●───●                                                       │ │
│ │ 10│      ●───●                                                            │ │
│ │   └────┬────┬────┬────┬────┬────┬────┬────┬────┬───                     │ │
│ │       W1   W2   W3   W4   W5   W6   W7   W8                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 🎯 Category Distribution                                                     │
│   Customer Service: 234 (18.8%)                                              │
│   IT Support: 189 (15.2%)                                                    │
│   Data Analysis: 389 (31.2%)                                                 │
│   Sales: 156 (12.5%)                                                         │
│   Finance: 145 (11.6%)                                                       │
│   HR: 134 (10.7%)                                                            │
│                                                                               │
│ 🔍 Top Search Keywords (identify gaps)                                       │
│   1. "data analysis": 89 searches                                            │
│   2. "customer service": 67 searches                                         │
│   3. "email automation": 45 searches (⚠️ No template available)              │
│   4. "invoice processing": 34 searches (⚠️ No template available)            │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Definition of Done**:
- [ ] Analytics dashboard shows deploy count, trend, category distribution
- [ ] User ratings (1-5 stars) collected and displayed
- [ ] Search analytics identify missing templates
- [ ] Export analytics as CSV

---

## 6.3 Database Schema

```sql
CREATE TABLE marketplace_templates (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,  -- CS, IT, Sales, Finance, HR, Data
    complexity INTEGER DEFAULT 1,  -- 1-5 stars
    
    -- Template content
    prompt_template TEXT NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    code TEXT,  -- Optional Python code
    example_workflow TEXT,  -- YAML
    
    -- Metadata
    version VARCHAR(20) DEFAULT '1.0',
    author VARCHAR(100) DEFAULT 'IPA Team',
    tags TEXT[],
    
    -- Analytics
    deploy_count INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2),  -- 1.00 - 5.00
    rating_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketplace_deployments (
    id SERIAL PRIMARY KEY,
    deployment_id VARCHAR(50) UNIQUE NOT NULL,
    template_id VARCHAR(50) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    
    -- User info
    deployed_by VARCHAR(100) NOT NULL,
    workspace_id VARCHAR(100),
    
    -- Configuration
    llm_model VARCHAR(50),
    temperature DECIMAL(3,2),
    max_tokens INTEGER,
    
    -- Timestamps
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (template_id) REFERENCES marketplace_templates(template_id)
);

CREATE TABLE marketplace_ratings (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(50) NOT NULL,
    rating INTEGER NOT NULL,  -- 1-5
    comment TEXT,
    rated_by VARCHAR(100) NOT NULL,
    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (template_id) REFERENCES marketplace_templates(template_id)
);

-- Indexes
CREATE INDEX idx_template_category ON marketplace_templates(category, deploy_count DESC);
CREATE INDEX idx_template_popularity ON marketplace_templates(deploy_count DESC);
CREATE INDEX idx_deployment_template ON marketplace_deployments(template_id, deployed_at DESC);
```

---

## 6.4 Non-Functional Requirements (NFR)

| **Category** | **Requirement** | **Target** | **Measurement** |
|-------------|----------------|-----------|----------------|
| **Performance** | Template list load time | < 1 second | Page load metrics |
| | Template detail load time | < 500ms | API response time |
| | Deployment time | < 5 seconds | End-to-end deployment |
| **Scalability** | Total templates | Support 50+ templates | Database capacity |
| | Concurrent deploys | 100+ per hour | Load testing |
| **Quality** | Template validation | 100% pass JSON Schema validation | Automated tests |
| | Code quality | All templates pass linting | CI/CD checks |
| **Usability** | Template discovery | Users find template in <2 minutes | User testing |
| | Deployment success rate | ≥95% | Deployment metrics |

---

## 6.5 Testing Strategy

**Unit Tests**:
- JSON Schema validation
- Agent ID uniqueness check
- Template deployment logic
- Analytics calculation

**Integration Tests**:
- End-to-end deployment flow
- Template search and filter
- Sandbox test execution

**User Acceptance Tests**:
- Browse marketplace
- Deploy template
- Customize and test agent

---

## 6.6 Risks and Mitigation

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|---------|----------------|-----------|---------------|
| Low-quality templates | Medium | High | Peer review, automated validation, user ratings |
| Security vulnerabilities in code | Low | Critical | Code scanning, sandboxed execution, security audit |
| Template versioning conflicts | Medium | Medium | Semantic versioning, backward compatibility checks |
| Licensing issues | Low | High | Clear licensing terms, open-source preferred |

---

## 6.7 Future Enhancements (Post-MVP)

1. **Community Templates**: Allow users to publish custom templates
2. **Template Marketplace**: Paid premium templates from vendors
3. **Template Forking**: Fork and customize existing templates
4. **Version Updates**: Notify users when template updates available
5. **Template Collections**: Curated template packs for industries (Healthcare, Retail, Finance)
6. **A/B Testing**: Compare template performance variants

---

**Next Feature**: [F7. DevUI Integration →](./feature-07-devui.md)
