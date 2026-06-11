# Product Requirements Document (PRD)
# Microsoft Agent Framework Platform - IPA

**Version**: 1.0  
**Date**: 2025-11-18  
**Status**: Draft  
**Owner**: Product Team

---

## 📑 Document Navigation

- **[PRD Main Document](./prd-main.md)** ← You are here
- [PRD Appendix A: Features 1-7 Detailed Specifications](./prd-appendix-a-features-1-7.md)
- [PRD Appendix B: Features 8-14 Detailed Specifications](./prd-appendix-b-features-8-14.md)
- [PRD Appendix C: API Specifications (OpenAPI 3.0)](./prd-appendix-c-api-specs.md)

**Related Documents**:
- [Product Brief](../../00-discovery/product-brief/product-brief.md)
- [UI/UX Design Specification](../ui-ux/ui-ux-design-spec.md)

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Overview](#product-overview)
3. [Target Users and Personas](#target-users-and-personas)
4. [MVP Scope](#mvp-scope)
5. [Data Model](#data-model)
6. [Non-Functional Requirements](#non-functional-requirements)
7. [Technical Constraints](#technical-constraints)
8. [Assumptions and Dependencies](#assumptions-and-dependencies)
9. [Success Metrics](#success-metrics)
10. [Glossary](#glossary)

---

## 1. Executive Summary

### 1.1 Product Name
**IPA (Intelligent Process Automation) Platform** - Microsoft Agent Framework-based Enterprise Automation Solution

### 1.2 Problem Statement
Mid-size enterprises (500-2000 employees) struggle with:
- **Reactive firefighting**: IT and CS teams spend 60-70% of time on repetitive manual tasks
- **Data silos**: Customer information scattered across ServiceNow, Dynamics 365, SharePoint
- **High operational costs**: Manual processes cost $10K+/month in labor
- **Poor visibility**: Lack of audit trails and process insights

### 1.3 Solution
An AI-powered automation platform that:
- ✅ Enables **proactive agent mode** (shift from firefighting to prevention)
- ✅ Provides **cross-system correlation** (360° view from 3 enterprise systems)
- ✅ Implements **human-in-the-loop checkpointing** (safety for high-risk operations)
- ✅ Delivers **learning-based collaboration** (AI improves from human feedback)

### 1.4 Business Value
- 💰 **Cost Reduction**: $10K/month savings (40-50% reduction in manual work)
- ⚡ **Efficiency Gain**: 40-50% faster ticket/incident resolution
- 🎯 **Quality Improvement**: 90%+ success rate with <30% human intervention
- 📊 **Visibility**: Complete audit trail and real-time monitoring

### 1.5 MVP Timeline
**12-14 weeks** (Q1 2026) with **14 core features** across 6 categories

---

## 2. Product Overview

### 2.1 Product Positioning

```
┌─────────────────────────────────────────────────────────────────┐
│  Traditional RPA          →  IPA (Our Platform)                 │
├─────────────────────────────────────────────────────────────────┤
│  • Rule-based             →  • AI-powered reasoning             │
│  • Reactive               →  • Proactive prevention             │
│  • Brittle workflows      →  • Adaptive orchestration           │
│  • Single-system          →  • Cross-system correlation         │
│  • No learning            →  • Continuous improvement           │
│  • Vendor lock-in         →  • Microsoft ecosystem native       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Differentiators

| Feature | Our Platform | Competitors |
|---------|--------------|-------------|
| **LLM-Powered Reasoning** | ✅ Azure OpenAI GPT-4o | ⚠️ Limited or none |
| **Proactive Agent Mode** | ✅ Predicts and prevents issues | ❌ Only reactive |
| **Cross-System Correlation** | ✅ Parallel query 3 systems + AI analysis | ❌ Sequential single-system |
| **Human-in-the-loop Checkpointing** | ✅ Configurable YAML rules | ⚠️ Basic approval only |
| **Few-shot Learning** | ✅ Learns from human modifications | ❌ No learning |
| **Developer Experience** | ✅ Pure Python + Microsoft DevUI | ⚠️ Low-code GUI (limited) |
| **Microsoft Ecosystem** | ✅ Native Azure/M365 integration | ⚠️ Third-party connectors |

### 2.3 Tech Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Frontend** | React | 18+ | Modern, component-based |
| | TypeScript | 5.0+ | Type safety |
| | Shadcn UI | Latest | Modern, Tailwind-based, customizable |
| | React Flow | 11+ | Agent workflow visualization |
| | Recharts | 2.5+ | Dashboard charts |
| | Monaco Editor | Latest | Code editing (VS Code engine) |
| **Backend** | Python | 3.11+ | Agent Framework native |
| | FastAPI | 0.100+ | High-performance REST API |
| **Agent Engine** | Agent Framework | Preview | Microsoft native orchestration |
| **Auxiliary** | n8n | Latest | Cron/Webhook triggers |
| **Database** | PostgreSQL | 14+ | Relational data, ACID transactions |
| **Cache** | Redis | 7+ | LLM response cache, session data |
| **LLM** | Azure OpenAI | GPT-4o | Reasoning, correlation, generation |
| **Cloud** | Azure | - | Container Instances, Database, Cache |
| **DevOps** | Docker | Latest | Local dev environment |
| | GitHub Actions | - | CI/CD pipeline |

---

## 3. Target Users and Personas

### 3.1 Primary User: IT Operations Admin

**Profile**:
- **Name**: Alex Chen
- **Role**: Senior IT Operations Manager
- **Age**: 35-45
- **Experience**: 10+ years in enterprise IT
- **Team Size**: Manages 5-8 IT support staff

**Pain Points**:
- 🔥 "My team spends 60% of time on repetitive tickets (password resets, server checks)"
- 📊 "I have no visibility into what's actually happening across our systems"
- 💸 "Manual processes are costing us $15K/month in labor, and errors are frequent"
- ⏱️ "Average incident resolution time is 4-6 hours, customers are frustrated"

**Goals**:
- ✅ Automate 50%+ of routine IT tasks
- ✅ Reduce incident response time to <2 hours
- ✅ Gain real-time visibility into operations
- ✅ Ensure safety with human oversight for risky operations

**User Stories** (High-level, detailed in Appendices):
- "As an IT Admin, I want to create agents to monitor server health, so that I'm alerted before failures occur"
- "As an IT Admin, I want agents to pause before deleting user accounts, so that I can review high-risk operations"
- "As an IT Admin, I want to see all agent executions in a dashboard, so that I can track success rates and costs"

---

### 3.2 Primary User: Customer Support Team Lead

**Profile**:
- **Name**: Sarah Martinez
- **Role**: Customer Support Team Lead
- **Age**: 30-40
- **Experience**: 8+ years in customer service
- **Team Size**: Leads 10-15 CS agents

**Pain Points**:
- 📝 "CS agents spend 30 minutes per ticket searching for customer data across 3 systems"
- 🔍 "We have no way to correlate customer history (CRM, tickets, documents) efficiently"
- 😓 "Complex tickets require escalation to IT, adding 2-4 hours of delay"
- 📈 "Our ticket resolution SLA is 24 hours, but we're averaging 36 hours"

**Goals**:
- ✅ Provide CS agents with instant customer 360° view
- ✅ Automate ticket classification and knowledge article suggestions
- ✅ Enable seamless CS→IT escalation for technical issues
- ✅ Reduce average ticket resolution time to <12 hours

**User Stories**:
- "As a CS Team Lead, I want agents to query customer data from Dynamics, ServiceNow, and SharePoint in parallel, so that CS agents get complete context in <5 seconds"
- "As a CS Team Lead, I want to review AI-suggested solutions before they're sent to customers, so that I maintain quality control"
- "As a CS Team Lead, I want CS agents to automatically trigger IT agents when technical issues are detected, so that we don't waste time on manual handoffs"

---

### 3.3 Secondary User: System Administrator

**Profile**:
- **Name**: Michael Wong
- **Role**: Platform Administrator
- **Age**: 28-35
- **Experience**: 5+ years in DevOps/Platform Engineering

**Responsibilities**:
- Configure platform settings (API keys, webhooks, user permissions)
- Monitor system health and costs
- Manage agent marketplace templates
- Review audit logs for compliance

**User Stories**:
- "As a System Admin, I want to set auto-approval rules for low-risk checkpoints, so that routine operations don't require manual review"
- "As a System Admin, I want to track LLM costs per agent, so that I can optimize spending"
- "As a System Admin, I want to export audit logs for compliance reports, so that I can demonstrate SOC 2 readiness (Phase 2)"

---

### 3.4 Tertiary User: Developer

**Profile**:
- **Name**: Emily Zhang
- **Role**: Backend Developer / Automation Engineer
- **Age**: 25-35
- **Experience**: 3-5 years in Python development

**Responsibilities**:
- Create custom agents using Python
- Debug agent execution failures
- Extend agent marketplace with new templates
- Integrate with internal systems

**User Stories**:
- "As a Developer, I want to write agents in pure Python with full IDE support, so that I can use familiar tools (VS Code, PyCharm)"
- "As a Developer, I want to see LLM call chains and variable states in DevUI, so that I can debug failures in 10-30 minutes instead of 2-4 hours"
- "As a Developer, I want to test agents locally with mock data, so that I don't need to connect to production systems during development"

---

## 4. MVP Scope

### 4.1 In-Scope Features (14 Core Features)

| Category | Feature | Priority | Dev Time | Appendix |
|----------|---------|----------|----------|----------|
| **Core Engine** | F1. Sequential Agent Orchestration | P0 | Design Phase | [Appendix A](./prd-appendix-a-features-1-7.md#f1) |
| **Core Engine** | F2. Human-in-the-loop Checkpointing | P0 | 2 weeks | [Appendix A](./prd-appendix-a-features-1-7.md#f2) |
| **Core Engine** | F3. Cross-System Correlation | P0 | 2 weeks | [Appendix A](./prd-appendix-a-features-1-7.md#f3) |
| **Innovation** | F4. Cross-Scenario Collaboration (CS↔IT) | P1 | 2 weeks | [Appendix A](./prd-appendix-a-features-1-7.md#f4) |
| **Innovation** | F5. Learning-based Collaboration | P1 | 1 week | [Appendix A](./prd-appendix-a-features-1-7.md#f5) |
| **Developer** | F6. Agent Marketplace (Internal Templates) | P0 | 3 weeks | [Appendix A](./prd-appendix-a-features-1-7.md#f6) |
| **Developer** | F7. DevUI Integration | P0 | 2 weeks | [Appendix A](./prd-appendix-a-features-1-7.md#f7) |
| **Reliability** | F8. n8n Triggering + Error Handling | P0 | 2 weeks | [Appendix B](./prd-appendix-b-features-8-14.md#f8) |
| **Reliability** | F9. Prompt Management (YAML Templates) | P0 | 1 week | [Appendix B](./prd-appendix-b-features-8-14.md#f9) |
| **Observability** | F10. Audit Trail (Append-only Logs) | P0 | 1 week | [Appendix B](./prd-appendix-b-features-8-14.md#f10) |
| **Observability** | F11. Teams Notification | P0 | 1 week | [Appendix B](./prd-appendix-b-features-8-14.md#f11) |
| **Observability** | F12. Monitoring Dashboard | P0 | 2 weeks | [Appendix B](./prd-appendix-b-features-8-14.md#f12) |
| **UI/UX** | F13. Modern Web UI | P0 | 4 weeks | [Appendix B](./prd-appendix-b-features-8-14.md#f13) |
| **Performance** | F14. Redis Caching | P0 | 1 week | [Appendix B](./prd-appendix-b-features-8-14.md#f14) |

**Total Development Time**: 24 weeks (raw)  
**With Parallelization** (3 tracks): **12-14 weeks**

---

### 4.2 Out-of-Scope (Deferred to MVP2 or Phase 2)

| Feature | Reason for Deferral | Target Phase |
|---------|---------------------|--------------|
| Multi-Environment Management | Complexity; MVP focuses on single prod environment | MVP2 (Week 15-18) |
| Advanced Execution Modes (Parallel, Conditional) | Agent Framework sequential is sufficient for MVP | MVP2 |
| External Marketplace (Public Templates) | Internal templates sufficient for enterprise MVP | Phase 2 (Year 1 Q2) |
| GDPR/SOC 2/ISO 27001 Compliance | General enterprise security sufficient for MVP | Phase 2 (Year 1 Q3) |
| Role-Based Access Control (RBAC) | Simple user auth sufficient for MVP (10-20 users) | Phase 2 (Year 1 Q2) |
| WebSocket Real-time Updates | Polling (2-3s) sufficient for MVP UX | MVP2 |
| Agent Versioning and Rollback | Git-based manual versioning acceptable for MVP | MVP2 |
| Mobile App / Mobile-Responsive UI | Desktop-first for MVP (admin portal) | Phase 2 (Year 2) |
| Multi-Language Support | English-only for MVP (mid-size US enterprises) | Phase 2 (Year 2) |
| Advanced Analytics (BI Reports) | Basic dashboard sufficient for MVP | Phase 2 (Year 1 Q3) |

**Time Saved by Deferral**: 17-20 weeks

---

## 5. Data Model

### 5.1 Entity Relationship Diagram (ERD)

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     users       │         │     agents      │         │   workflows     │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │         │ id (PK)         │
│ email           │         │ name            │◄────────│ agent_id (FK)   │
│ name            │         │ description     │         │ name            │
│ role            │         │ category        │         │ trigger_type    │
│ created_at      │         │ code            │         │ trigger_config  │
│ updated_at      │         │ config (JSONB)  │         │ created_at      │
└─────────────────┘         │ status          │         └────────┬────────┘
                            │ created_by (FK) │                  │
                            │ created_at      │                  │
                            │ updated_at      │                  │
                            └─────────────────┘                  │
                                                                  │
                            ┌─────────────────┐                  │
                            │   executions    │◄─────────────────┘
                            ├─────────────────┤
                            │ id (PK)         │
                            │ workflow_id(FK) │
                            │ status          │
                            │ started_at      │
                            │ completed_at    │
                            │ result (JSONB)  │
                            │ error           │
                            │ llm_calls       │
                            │ llm_cost        │
                            └────────┬────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
        ┌───────────▼──────┐  ┌─────▼──────┐  ┌─────▼──────────┐
        │  checkpoints     │  │audit_logs  │  │ learning_cases │
        ├──────────────────┤  ├────────────┤  ├────────────────┤
        │ id (PK)          │  │ id (PK)    │  │ id (PK)        │
        │ execution_id(FK) │  │ exec_id(FK)│  │ exec_id (FK)   │
        │ step             │  │ action     │  │ scenario       │
        │ state (JSONB)    │  │ actor      │  │ original_action│
        │ status           │  │ details    │  │ human_modified │
        │ approved_by      │  │ timestamp  │  │ feedback       │
        │ approved_at      │  └────────────┘  │ created_at     │
        │ created_at       │                  └────────────────┘
        └──────────────────┘

┌─────────────────────────┐
│   agent_templates       │  (Marketplace)
├─────────────────────────┤
│ id (PK)                 │
│ name                    │
│ category                │
│ description             │
│ code_template           │  (Jinja2 template with {{ variables }})
│ config_schema (JSONB)   │  (JSON Schema for deployment params)
│ usage_count             │
│ created_at              │
└─────────────────────────┘
```

---

### 5.2 Core Tables Detailed Schema

#### 5.2.1 `users` Table

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,  -- 'admin', 'user', 'developer'
  password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

**Constraints**:
- Email must be valid format (enforced by application)
- Role must be one of: `admin`, `user`, `developer`
- Password must be bcrypt hashed (never store plaintext)

---

#### 5.2.2 `agents` Table

```sql
CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(50) NOT NULL,  -- 'IT', 'CS', 'General'
  code TEXT NOT NULL,  -- Serialized Python Agent code
  config JSONB,  -- Agent-specific configuration
  status VARCHAR(50) NOT NULL DEFAULT 'draft',  -- 'draft', 'active', 'inactive'
  created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  
  CONSTRAINT chk_agent_status CHECK (status IN ('draft', 'active', 'inactive')),
  CONSTRAINT chk_agent_category CHECK (category IN ('IT', 'CS', 'General'))
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_category ON agents(category);
CREATE INDEX idx_agents_created_by ON agents(created_by);
```

**Config JSONB Example**:
```json
{
  "timeout": 300,
  "retry_count": 3,
  "checkpoint_rules": {
    "enabled": true,
    "risk_levels": ["high"]
  },
  "environment_vars": {
    "SERVICENOW_URL": "https://example.service-now.com"
  }
}
```

---

#### 5.2.3 `workflows` Table

```sql
CREATE TABLE workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  trigger_type VARCHAR(50) NOT NULL,  -- 'manual', 'cron', 'webhook'
  trigger_config JSONB,  -- Type-specific trigger configuration
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  
  CONSTRAINT chk_workflow_trigger CHECK (trigger_type IN ('manual', 'cron', 'webhook'))
);

CREATE INDEX idx_workflows_agent_id ON workflows(agent_id);
CREATE INDEX idx_workflows_trigger_type ON workflows(trigger_type);
```

**Trigger Config Examples**:

**Cron**:
```json
{
  "cron_expression": "0 */1 * * *",  // Every hour
  "timezone": "America/New_York"
}
```

**Webhook**:
```json
{
  "webhook_url": "https://api.example.com/webhook/agent-trigger",
  "secret": "hashed_secret_key",
  "allowed_sources": ["192.168.1.0/24"]
}
```

---

#### 5.2.4 `executions` Table

```sql
CREATE TABLE executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  status VARCHAR(50) NOT NULL DEFAULT 'running',  -- 'running', 'success', 'failed', 'paused'
  started_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP,
  result JSONB,  -- Final execution result
  error TEXT,  -- Error message if failed
  llm_calls INTEGER DEFAULT 0,  -- Total LLM API calls
  llm_tokens INTEGER DEFAULT 0,  -- Total tokens used
  llm_cost DECIMAL(10, 4) DEFAULT 0.0000,  -- Total LLM cost in USD
  
  CONSTRAINT chk_execution_status CHECK (status IN ('running', 'success', 'failed', 'paused'))
);

CREATE INDEX idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_started_at ON executions(started_at DESC);
```

**Result JSONB Example**:
```json
{
  "ticket_id": "CS-1234",
  "resolution": "User account unlocked successfully",
  "execution_steps": [
    {"step": 1, "agent": "Ticket Analyzer", "duration_ms": 1200},
    {"step": 2, "agent": "Customer Data", "duration_ms": 2300},
    {"step": 3, "agent": "Solution Generator", "duration_ms": 1800}
  ]
}
```

---

#### 5.2.5 `checkpoints` Table

```sql
CREATE TABLE checkpoints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  step INTEGER NOT NULL,  -- Which step in workflow
  state JSONB NOT NULL,  -- Workflow state at checkpoint
  status VARCHAR(50) NOT NULL DEFAULT 'pending_approval',  -- 'pending_approval', 'approved', 'rejected'
  approved_by UUID REFERENCES users(id),
  approved_at TIMESTAMP,
  feedback TEXT,  -- Human feedback for learning
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  
  CONSTRAINT chk_checkpoint_status CHECK (status IN ('pending_approval', 'approved', 'rejected'))
);

CREATE INDEX idx_checkpoints_execution_id ON checkpoints(execution_id);
CREATE INDEX idx_checkpoints_status ON checkpoints(status);
CREATE INDEX idx_checkpoints_created_at ON checkpoints(created_at DESC);
```

**State JSONB Example**:
```json
{
  "proposed_action": {
    "operation": "delete_user",
    "target": "test@example.com",
    "system": "Dynamics 365"
  },
  "context": {
    "user_tickets": 3,
    "last_activity": "2024-01-15",
    "account_age_days": 180
  },
  "ai_recommendation": {
    "decision": "safe_to_delete",
    "confidence": 0.95,
    "reasoning": "User inactive for 10+ months, all tickets resolved"
  }
}
```

---

#### 5.2.6 `audit_logs` Table

```sql
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,  -- Auto-incrementing for append-only
  execution_id UUID REFERENCES executions(id) ON DELETE CASCADE,
  action VARCHAR(255) NOT NULL,  -- e.g., 'agent_created', 'checkpoint_approved'
  actor VARCHAR(255),  -- User email or 'system'
  details JSONB,  -- Action-specific details
  timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Append-only enforcement: No UPDATE or DELETE allowed
-- Enforced by application-level permissions
-- PostgreSQL Row-Level Security can be used for additional protection

CREATE INDEX idx_audit_logs_execution_id ON audit_logs(execution_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor);
```

**Details JSONB Example**:
```json
{
  "checkpoint_id": "cp-uuid-1234",
  "decision": "approved",
  "modified_params": {
    "target_email": "changed_from_test@example.com"
  },
  "feedback": "This is a test account, safe to delete"
}
```

---

#### 5.2.7 `learning_cases` Table

```sql
CREATE TABLE learning_cases (
  id SERIAL PRIMARY KEY,
  execution_id UUID REFERENCES executions(id) ON DELETE CASCADE,
  scenario VARCHAR(255) NOT NULL,  -- e.g., 'user_account_deletion', 'ticket_classification'
  original_action JSONB NOT NULL,  -- AI's original suggestion
  human_modified_action JSONB NOT NULL,  -- Human's modification
  feedback TEXT,  -- Why human modified it
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_learning_cases_scenario ON learning_cases(scenario);
CREATE INDEX idx_learning_cases_created_at ON learning_cases(created_at DESC);
```

**Purpose**: Store human modifications for Few-shot Learning. When similar scenarios occur, AI will reference these cases in LLM prompts.

**Example**:
```json
{
  "original_action": {
    "operation": "reset_password",
    "send_email": false
  },
  "human_modified_action": {
    "operation": "reset_password",
    "send_email": true,
    "email_template": "security_alert"
  },
  "feedback": "Always send email for security-related password resets"
}
```

---

#### 5.2.8 `agent_templates` Table

```sql
CREATE TABLE agent_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  category VARCHAR(50) NOT NULL,  -- 'IT', 'CS', 'General'
  description TEXT NOT NULL,
  code_template TEXT NOT NULL,  -- Jinja2 template with {{ variables }}
  config_schema JSONB NOT NULL,  -- JSON Schema for deployment parameters
  usage_count INTEGER NOT NULL DEFAULT 0,  -- How many times deployed
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  
  CONSTRAINT chk_template_category CHECK (category IN ('IT', 'CS', 'General'))
);

CREATE INDEX idx_agent_templates_category ON agent_templates(category);
CREATE INDEX idx_agent_templates_usage_count ON agent_templates(usage_count DESC);
```

**Code Template Example** (Jinja2):
```python
async def main():
    # Server Health Check Agent
    servers = {{ server_list }}  # Injected during deployment
    threshold_cpu = {{ cpu_threshold }}
    threshold_memory = {{ memory_threshold }}
    
    for server in servers:
        cpu = await get_cpu_usage(server)
        memory = await get_memory_usage(server)
        
        if cpu > threshold_cpu or memory > threshold_memory:
            await send_teams_alert(server, cpu, memory)
```

**Config Schema Example** (JSON Schema):
```json
{
  "type": "object",
  "properties": {
    "agent_name": {"type": "string", "description": "Agent display name"},
    "server_list": {
      "type": "array",
      "items": {"type": "string", "format": "ipv4"},
      "description": "List of server IPs to monitor"
    },
    "cpu_threshold": {"type": "number", "minimum": 0, "maximum": 100},
    "memory_threshold": {"type": "number", "minimum": 0, "maximum": 100},
    "teams_webhook_url": {"type": "string", "format": "uri"}
  },
  "required": ["agent_name", "server_list", "cpu_threshold", "memory_threshold", "teams_webhook_url"]
}
```

---

## 6. Non-Functional Requirements (NFR)

### 6.1 Performance Requirements

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Agent Execution Latency** | P95 < 5 seconds (end-to-end) | Application Insights P95 metric |
| **LLM API Call Latency** | P95 < 3 seconds per call | Azure OpenAI response time |
| **Dashboard Load Time** | < 2 seconds (initial page load) | Lighthouse Performance Score ≥ 90 |
| **Concurrent Executions** | 50+ simultaneous workflows | Load testing with JMeter |
| **Database Query Time** | P95 < 100ms | PostgreSQL `EXPLAIN ANALYZE` |
| **Redis Cache Hit Rate** | ≥ 60% | Redis INFO stats |
| **API Response Time** | P95 < 500ms (excluding LLM calls) | FastAPI middleware logging |

---

### 6.2 Scalability Requirements

| Dimension | Target | Strategy |
|-----------|--------|----------|
| **Agents** | Support 100+ agents per workspace | PostgreSQL partitioning by agent_id if needed |
| **Executions** | 1000+ executions/day | PostgreSQL indexes on timestamp, asynchronous processing |
| **Users** | 50-100 concurrent users | Azure Container Instances auto-scaling (CPU > 70%) |
| **Storage** | Accommodate 1 year of audit logs | Time-series partitioning, cold storage after 90 days |
| **LLM Tokens** | 10M tokens/month | Azure OpenAI quota management, caching |

---

### 6.3 Reliability Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **System Uptime** | 99.0% (MVP), 99.5% (Phase 2) | Azure Container Instances health checks, auto-restart |
| **Data Durability** | 99.99% (no data loss) | PostgreSQL ACID transactions, automated daily backups |
| **Checkpoint Recovery** | 100% (all checkpoints recoverable) | PostgreSQL state persistence, transaction rollback support |
| **Error Recovery** | Auto-retry 3 times with exponential backoff | n8n retry logic, FastAPI exception handlers |
| **Audit Log Integrity** | 100% (append-only, immutable) | PostgreSQL row-level security, no DELETE permission |

---

### 6.4 Security Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **Authentication** | JWT-based, session timeout 24h | FastAPI JWT middleware, bcrypt password hashing |
| **API Authorization** | Role-based (admin, user, developer) | FastAPI dependency injection for role checks |
| **Data Encryption in Transit** | TLS 1.3 | Azure Front Door SSL termination |
| **Data Encryption at Rest** | AES-256 | Azure Database for PostgreSQL TDE (Transparent Data Encryption) |
| **Secrets Management** | No secrets in code/config | Azure Key Vault integration |
| **LLM Data Isolation** | Enterprise-grade | Azure OpenAI (no shared training data) |
| **Audit Compliance** | Append-only logs | PostgreSQL audit_logs table (no UPDATE/DELETE) |

**Deferred to Phase 2**:
- GDPR compliance (data retention policies, right to erasure)
- SOC 2 / ISO 27001 certification
- Multi-factor authentication (MFA)
- Advanced RBAC (granular permissions per agent)

---

### 6.5 Usability Requirements

| Requirement | Target | Validation Method |
|-------------|--------|-------------------|
| **Onboarding Time** | New user can create first agent in < 30 minutes | User testing with 5 IT admins |
| **Dashboard Learnability** | 90% of users understand metrics without training | Survey after 1 week usage |
| **Error Messages** | Clear, actionable (no cryptic codes) | User testing, accessibility review |
| **Agent Creation Success Rate** | ≥ 80% of agents deploy successfully on first try | Telemetry tracking |
| **Checkpoint Approval Time** | Average < 5 minutes from notification to decision | Application Insights tracking |

---

### 6.6 Observability Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **Execution Logging** | 100% of executions logged | PostgreSQL executions table, Application Insights |
| **LLM Call Tracing** | Full call chain visible in DevUI | Custom LLM wrapper with logging |
| **Error Tracking** | 100% of errors captured with stack traces | Application Insights exceptions |
| **Performance Monitoring** | Real-time dashboard metrics | Recharts dashboard, Azure Monitor integration |
| **Audit Trail** | Complete history for compliance | PostgreSQL audit_logs (append-only) |
| **Alerting** | Notify admins of failures via Teams | Microsoft Teams webhook integration |

---

### 6.7 Maintainability Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **Code Coverage** | ≥ 70% (unit + integration tests) | pytest for backend, Jest for frontend |
| **Documentation** | API docs auto-generated | FastAPI OpenAPI 3.0, Swagger UI |
| **Deployment Time** | < 10 minutes (CI/CD) | GitHub Actions pipeline |
| **Rollback Time** | < 5 minutes | Docker image versioning, Azure Container Instances rollback |
| **Debugging Time** | Average < 30 minutes (vs 2-4 hours without DevUI) | DevUI execution tracing, Monaco Editor breakpoints |

---

## 7. Technical Constraints

### 7.1 Platform Constraints

| Constraint | Impact | Mitigation |
|------------|--------|-----------|
| **Agent Framework Preview** | API may change, limited docs | • Keep framework code isolated in adapters<br>• Weekly monitoring of Microsoft updates<br>• Maintain fallback to pure Python orchestration |
| **Azure OpenAI Quota** | 10M tokens/month limit (estimated) | • Redis caching (target 60% hit rate)<br>• Prompt optimization (reduce token usage)<br>• Quota alerts at 80% usage |
| **PostgreSQL Connection Limits** | Default 100 connections | • Connection pooling (SQLAlchemy max 20 connections)<br>• Monitor with pg_stat_activity |
| **n8n Workflow Limits** | 100 active workflows (community edition) | • Use n8n only for Cron/Webhook triggers<br>• Upgrade to n8n Enterprise if needed in Phase 2 |

---

### 7.2 Integration Constraints

| System | API Limitations | Workaround |
|--------|----------------|------------|
| **ServiceNow** | 1000 API calls/hour | • Redis caching (TTL 1 day)<br>• Batch queries where possible |
| **Dynamics 365** | 5000 API calls/day/user | • Service account with higher quota<br>• Caching customer data |
| **SharePoint** | Throttling at 2000 requests/minute | • Exponential backoff retry<br>• Document search result caching |
| **Azure OpenAI** | 10 requests/second (TPM quota) | • Request queuing with asyncio<br>• Priority queue for interactive requests |

---

### 7.3 Development Constraints

| Constraint | Details | Impact |
|------------|---------|--------|
| **Team Size** | 2-3 full-time developers + 1 part-time UI/UX | Limited to 14 MVP features, no advanced features |
| **Timeline** | 12-14 weeks MVP deadline | Must use pre-built components (Shadcn UI), defer non-critical features |
| **Budget** | Azure costs ~$880/month estimated | Must optimize LLM usage, avoid over-provisioning |
| **Technology Lock-in** | Microsoft ecosystem (Azure, Agent Framework) | Acceptable trade-off for native integration benefits |

---

## 8. Assumptions and Dependencies

### 8.1 Assumptions

1. **Agent Framework Stability**: Microsoft will maintain backward compatibility during Preview phase
2. **User Technical Proficiency**: IT admins and developers are comfortable with Python code
3. **Enterprise Systems Availability**: ServiceNow, Dynamics 365, SharePoint APIs are accessible and stable
4. **Azure OpenAI Access**: Organization has Azure OpenAI access approved (waitlist cleared)
5. **Network Access**: On-premise dev environment can access Azure services (no firewall restrictions)
6. **Data Volume**: Average 100 executions/day during MVP phase (scales to 1000/day in Phase 2)
7. **Single Tenant**: MVP supports single enterprise workspace (multi-tenancy in Phase 2)

### 8.2 Dependencies

| Dependency | Provider | Risk Level | Contingency |
|------------|----------|------------|-------------|
| **Agent Framework Preview** | Microsoft | 🟡 Medium | Maintain pure Python orchestration fallback |
| **Azure OpenAI API** | Microsoft | 🟢 Low | Well-established service, enterprise SLA |
| **n8n Community Edition** | n8n GmbH | 🟢 Low | Can replace with custom Cron/Webhook service |
| **ServiceNow API Access** | Customer | 🟡 Medium | Provide mock API adapter for testing |
| **Dynamics 365 API Access** | Customer | 🟡 Medium | Provide mock API adapter for testing |
| **SharePoint API Access** | Customer | 🟢 Low | Fallback to file-based document search |
| **Azure Infrastructure** | Microsoft | 🟢 Low | 99.9% SLA for Container Instances, Database |
| **GitHub Actions** | GitHub | 🟢 Low | Can fallback to manual deployment if needed |

---

## 9. Success Metrics

### 9.1 Technical Metrics (KPI)

| Metric | Baseline | 1 Month | 3 Months | 6 Months |
|--------|----------|---------|----------|----------|
| **Agent Execution Success Rate** | - | ≥ 85% | ≥ 90% | ≥ 95% |
| **Average Execution Time** | - | < 60s | < 45s | < 30s |
| **LLM Cost per Execution** | - | < $0.10 | < $0.08 | < $0.05 |
| **Cache Hit Rate** | - | ≥ 50% | ≥ 60% | ≥ 70% |
| **System Uptime** | - | ≥ 99.0% | ≥ 99.0% | ≥ 99.5% |

---

### 9.2 Business Metrics (KPI)

| Metric | Baseline (Manual) | 1 Month Target | 3 Months Target |
|--------|-------------------|----------------|-----------------|
| **Ticket Resolution Time** | 4-6 hours | 2-3 hours | 1-2 hours |
| **Manual Work Reduction** | 0% | 30% | 40-50% |
| **Monthly Operational Cost** | $25K | $20K | $15K |
| **Human Intervention Rate** | 100% | < 40% | < 30% |
| **Customer Satisfaction (CSAT)** | 3.5/5 | 4.0/5 | 4.5/5 |

---

### 9.3 Developer Experience Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time to Create Agent** | < 30 minutes | User testing |
| **Agent Deployment Success Rate** | ≥ 80% first-time | Telemetry |
| **Debugging Time** | < 30 minutes (vs 2-4 hours) | Developer survey |
| **Marketplace Template Adoption** | ≥ 50% of agents from templates | Usage tracking |
| **Developer Satisfaction** | ≥ 4.0/5 | Quarterly survey |

---

## 10. Glossary

| Term | Definition |
|------|------------|
| **Agent** | A self-contained automation unit powered by Agent Framework and LLM reasoning |
| **Agent Framework** | Microsoft's preview framework for orchestrating AI agents with native Python support |
| **Checkpoint** | A pause point in workflow execution requiring human approval before proceeding |
| **Cross-System Correlation** | Parallel querying and AI-powered analysis of data from multiple enterprise systems (ServiceNow, Dynamics, SharePoint) |
| **Few-shot Learning** | LLM technique where AI learns from human-provided examples (learning cases) to improve future suggestions |
| **IPA** | Intelligent Process Automation - differentiated from traditional RPA by AI reasoning capabilities |
| **Learning Case** | Recorded instance of human modification to AI suggestion, stored for future Few-shot Learning |
| **LLM** | Large Language Model (e.g., GPT-4o) - AI model used for reasoning, analysis, and generation |
| **Proactive Agent Mode** | Agents that predict and prevent issues (vs reactive agents that only respond to incidents) |
| **Sequential Orchestration** | Agents execute in order (Agent 1 → Agent 2 → Agent 3), each passing results to the next |
| **Workflow** | A configured instance of an agent with specific trigger and execution settings |

---

## 📚 Next Steps

1. **Review Detailed Feature Specifications**:
   - [Appendix A: Features 1-7](./prd-appendix-a-features-1-7.md)
   - [Appendix B: Features 8-14](./prd-appendix-b-features-8-14.md)

2. **Review API Specifications**:
   - [Appendix C: OpenAPI 3.0 Specs](./prd-appendix-c-api-specs.md)

3. **Review UI/UX Design**:
   - [UI/UX Design Specification](../ui-ux/ui-ux-design-spec.md)

4. **Proceed to Development**:
   - Follow [Development Roadmap](../../00-discovery/product-brief/product-brief-appendix-c-roadmap.md)

---

**Document Status**: ✅ Approved for Development  
**Next Review Date**: 2025-12-01 (Post-MVP)

**Approval Signatures**:
- Product Manager: _________________ Date: _______
- Technical Lead: _________________ Date: _______
- UI/UX Lead: _________________ Date: _______
