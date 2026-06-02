# V2 資料庫 Schema 設計

**建立日期**：2026-04-23
**版本**：V2.0
**對應**：Phase 49 Sprint 49.2 實作

---

## 設計原則

1. **從零設計**：項目從未上線，無歷史包袱
2. **配合 11 範疇**：每個 schema 服務具體範疇
3. **Multi-tenant native + RLS**：**所有 session-scoped 表帶 `tenant_id` + 啟用 PostgreSQL Row-Level Security**
4. **Audit-ready**：關鍵操作有完整 audit trail
5. **Async-first**：配合 SQLAlchemy 2.x async
6. **Append-only where required**：audit / state_snapshot 不可改
7. **Partition Day 1**：高量表（messages / audit_log / message_events）月度 partition

### Multi-Tenant 強制標準（2026-04-23 強化）

> **校正**：原版只在主業務表有 tenant_id，但 sessions/messages/tool_calls 等也必須有，否則無法 RLS。

**所有 session-scoped 表必須有 `tenant_id UUID NOT NULL` 欄位**：
- sessions, messages, message_events
- tool_calls, tool_results
- state_snapshots, loop_states
- approvals, risk_assessments, guardrail_events
- verification_results
- subagent_runs, subagent_messages
- worker_tasks
- memory_session_summary

**啟用 PostgreSQL Row-Level Security (RLS)**：
```sql
-- 對所有帶 tenant_id 的表啟用 RLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
-- ... 其他表

-- Policy：當前 session 只能看自己 tenant 的資料
CREATE POLICY tenant_isolation ON sessions
    USING (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE POLICY tenant_isolation ON messages
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- ... 其他表
```

**Connection 設定**：
```python
# 每個 request 開始時設置
async with db.begin() as conn:
    await conn.execute(
        text("SET LOCAL app.tenant_id = :tid"),
        {"tid": current_tenant_id}
    )
    # 後續 query 自動受 RLS 限制
```

**禁止繞過 RLS**：
- ❌ `SET ROLE postgres`
- ❌ `BYPASSRLS` 角色（只給 DBA admin）
- ✅ App 角色強制受 RLS 約束

---

## Schema 全景

### 11 個 Schema 群組

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Identity & Tenancy                                       │
│    tenants / users / roles / role_permissions               │
├─────────────────────────────────────────────────────────────┤
│ 2. Sessions & Conversations  (範疇 1, 5, 7)                 │
│    sessions / messages / message_events                     │
├─────────────────────────────────────────────────────────────┤
│ 3. Tools  (範疇 2)                                          │
│    tools_registry / tool_calls / tool_results               │
├─────────────────────────────────────────────────────────────┤
│ 4. Memory  (範疇 3)                                         │
│    memory_system / memory_tenant / memory_role              │
│    memory_user / memory_session_summary                     │
├─────────────────────────────────────────────────────────────┤
│ 5. State & Checkpoint  (範疇 7)                             │
│    state_snapshots / loop_states                            │
├─────────────────────────────────────────────────────────────┤
│ 6. Governance  (範疇 9)                                     │
│    approvals / risk_assessments / guardrail_events          │
├─────────────────────────────────────────────────────────────┤
│ 7. Audit  (範疇 9, append-only)                             │
│    audit_log                                                │
├─────────────────────────────────────────────────────────────┤
│ 8. Verification  (範疇 10)                                  │
│    verification_results                                     │
├─────────────────────────────────────────────────────────────┤
│ 9. Subagent  (範疇 11)                                      │
│    subagent_runs / subagent_messages                        │
├─────────────────────────────────────────────────────────────┤
│ 10. Workers & Queue                                         │
│    worker_tasks / worker_results                            │
├─────────────────────────────────────────────────────────────┤
│ 11. Business Domain                                         │
│    patrol_* / correlation_* / rootcause_* / incident_*      │
│    （Phase 55 細化）                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Group 1: Identity & Tenancy

### `tenants`
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL,           -- e.g., "ACME_CORP"
    display_name VARCHAR(256) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',  -- active / suspended / archived
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_status ON tenants(status);
```

### `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(256) NOT NULL,
    display_name VARCHAR(256),
    external_id VARCHAR(256),                   -- Entra ID / LDAP ID
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (tenant_id, email)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_external ON users(external_id) WHERE external_id IS NOT NULL;
```

### `roles`
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code VARCHAR(64) NOT NULL,                  -- e.g., "finance_manager"
    display_name VARCHAR(256) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (tenant_id, code)
);
```

### `user_roles`
```sql
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),
    
    PRIMARY KEY (user_id, role_id)
);
```

### `role_permissions`
```sql
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    resource_type VARCHAR(64) NOT NULL,         -- "tool" / "memory_layer" / "agent"
    resource_pattern VARCHAR(256) NOT NULL,     -- "tool:patrol_*" / "memory:tenant:*"
    action VARCHAR(32) NOT NULL,                -- "read" / "write" / "execute"
    constraints JSONB DEFAULT '{}',             -- e.g., {"hitl_required": true}
    
    UNIQUE (role_id, resource_type, resource_pattern, action)
);

CREATE INDEX idx_role_perms_role ON role_permissions(role_id);
```

---

## Group 2: Sessions & Conversations

### `sessions`
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    title VARCHAR(512),
    status VARCHAR(32) NOT NULL DEFAULT 'active',  -- active / paused / completed / failed
    
    -- Loop state pointer
    current_state_snapshot_id UUID,             -- → state_snapshots.id
    
    -- Statistics
    total_turns INT NOT NULL DEFAULT 0,
    total_tokens INT NOT NULL DEFAULT 0,
    total_cost_usd DECIMAL(10, 4) DEFAULT 0,
    
    -- Lifecycle
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_sessions_tenant_user ON sessions(tenant_id, user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_active ON sessions(last_active_at DESC);
```

### `messages`
> 對話歷史。對應範疇 1 的 `messages[]` 持久化。

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Position in conversation
    sequence_num INT NOT NULL,                  -- 0, 1, 2, ... 連續
    turn_num INT NOT NULL,                      -- loop turn number
    
    -- Content
    role VARCHAR(32) NOT NULL,                  -- system / user / assistant / tool
    content_type VARCHAR(32) NOT NULL,          -- text / tool_call / tool_result / thinking
    content JSONB NOT NULL,                     -- 結構化內容
    
    -- Metadata
    model VARCHAR(64),                          -- if assistant: which model
    tokens_in INT,
    tokens_out INT,
    
    -- Compaction tracking
    is_compacted BOOLEAN NOT NULL DEFAULT FALSE,
    compacted_from_ids UUID[] DEFAULT '{}',     -- 若是壓縮結果，原始訊息 IDs
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (session_id, sequence_num)
);

CREATE INDEX idx_messages_session_seq ON messages(session_id, sequence_num);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_session_turn ON messages(session_id, turn_num);
```

### `message_events`
> SSE 事件流持久化（用於 replay / debug）

```sql
CREATE TABLE message_events (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    event_type VARCHAR(64) NOT NULL,            -- loop_start / turn_start / llm_request / ...
    event_data JSONB NOT NULL,
    
    sequence_num BIGINT NOT NULL,               -- 全局單調遞增
    timestamp_ms BIGINT NOT NULL,               -- 毫秒精度
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_message_events_session ON message_events(session_id, sequence_num);
CREATE INDEX idx_message_events_type ON message_events(event_type);
```

---

## Group 3: Tools

### `tools_registry`
> 工具元數據（DB 端註冊）。範疇 2 的支撐表。

```sql
CREATE TABLE tools_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    name VARCHAR(128) NOT NULL,                 -- e.g., "memory_search"
    version VARCHAR(32) NOT NULL DEFAULT '1.0',
    category VARCHAR(64) NOT NULL,              -- "memory" / "search" / "exec" / "enterprise"
    description TEXT NOT NULL,
    
    -- Schemas
    input_schema JSONB NOT NULL,                -- JSON Schema
    output_schema JSONB NOT NULL,
    
    -- Behavior
    is_mutating BOOLEAN NOT NULL DEFAULT FALSE,
    sandbox_level VARCHAR(32) NOT NULL DEFAULT 'none',  -- none / process / container
    
    -- HITL policy
    hitl_policy VARCHAR(32) NOT NULL DEFAULT 'auto',  -- auto / ask_once / always_ask
    risk_level VARCHAR(32) NOT NULL DEFAULT 'low',    -- low / medium / high / critical
    
    -- Permission template (specific permissions in role_permissions)
    required_permission VARCHAR(128),
    
    -- Status
    status VARCHAR(32) NOT NULL DEFAULT 'active',  -- active / deprecated / disabled
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (name, version)
);

CREATE INDEX idx_tools_status ON tools_registry(status) WHERE status = 'active';
CREATE INDEX idx_tools_category ON tools_registry(category);
```

### `tool_calls`
```sql
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id),    -- 觸發此 tool call 的 LLM message
    
    tool_name VARCHAR(128) NOT NULL,
    tool_version VARCHAR(32),
    
    arguments JSONB NOT NULL,                   -- 解析後的參數
    
    -- Permission / HITL
    permission_check_passed BOOLEAN NOT NULL,
    approval_id UUID,                           -- → approvals.id (if HITL triggered)
    
    -- Execution
    status VARCHAR(32) NOT NULL DEFAULT 'pending',  -- pending / executing / succeeded / failed / cancelled
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INT,
    
    -- Sandbox
    sandbox_used VARCHAR(32),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX idx_tool_calls_status ON tool_calls(status);
CREATE INDEX idx_tool_calls_tool ON tool_calls(tool_name);
```

### `tool_results`
```sql
CREATE TABLE tool_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_call_id UUID NOT NULL REFERENCES tool_calls(id) ON DELETE CASCADE,
    
    is_error BOOLEAN NOT NULL DEFAULT FALSE,
    result JSONB NOT NULL,                      -- 結構化結果或錯誤
    
    -- Size tracking (範疇 4 用)
    raw_size_bytes INT NOT NULL,
    truncated BOOLEAN NOT NULL DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_results_call ON tool_results(tool_call_id);
```

---

## Group 4: Memory（5 層）

### `memory_system`（Layer 1）
> 全局系統規則 / 安全政策

```sql
CREATE TABLE memory_system (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(256) NOT NULL UNIQUE,
    category VARCHAR(64) NOT NULL,              -- "safety" / "policy" / "compliance"
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `memory_tenant`（Layer 2）
> 租戶級記憶（公司知識 / playbook）

```sql
CREATE TABLE memory_tenant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    key VARCHAR(256) NOT NULL,
    category VARCHAR(64) NOT NULL,              -- "playbook" / "domain_knowledge"
    content TEXT NOT NULL,
    
    -- Vector embedding（in Qdrant，此處只存 reference）
    vector_id VARCHAR(128),
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (tenant_id, key)
);

CREATE INDEX idx_memory_tenant_tenant ON memory_tenant(tenant_id);
CREATE INDEX idx_memory_tenant_category ON memory_tenant(tenant_id, category);
```

### `memory_role`（Layer 3）
> 角色級記憶

```sql
CREATE TABLE memory_role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    
    key VARCHAR(256) NOT NULL,
    category VARCHAR(64) NOT NULL,              -- "workflow" / "approval_rule"
    content TEXT NOT NULL,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (role_id, key)
);

CREATE INDEX idx_memory_role_role ON memory_role(role_id);
```

### `memory_user`（Layer 4）
> 使用者級記憶（個人偏好 / 過往決策）

```sql
CREATE TABLE memory_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    category VARCHAR(64) NOT NULL,              -- "preference" / "fact" / "decision"
    content TEXT NOT NULL,
    
    -- Vector embedding（Qdrant reference）
    vector_id VARCHAR(128),
    
    -- Provenance
    source VARCHAR(64),                         -- "extracted" / "manual" / "system"
    source_session_id UUID REFERENCES sessions(id),
    confidence DECIMAL(3, 2),                   -- 0.00 - 1.00
    
    -- Lifecycle
    expires_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_memory_user_user ON memory_user(user_id);
CREATE INDEX idx_memory_user_category ON memory_user(user_id, category);
CREATE INDEX idx_memory_user_expires ON memory_user(expires_at) WHERE expires_at IS NOT NULL;
```

### `memory_session_summary`（Layer 5 持久化）
> Session 結束後的摘要（即時 messages 在 Redis）

```sql
CREATE TABLE memory_session_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE UNIQUE,
    
    summary TEXT NOT NULL,
    key_decisions JSONB DEFAULT '[]',
    unresolved_issues JSONB DEFAULT '[]',
    
    extracted_to_user_memory BOOLEAN NOT NULL DEFAULT FALSE,
    extraction_completed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Group 5: State & Checkpoint（範疇 7）

### `state_snapshots`
> 每輪 loop 完成後的快照。**Append-only**。

```sql
CREATE TABLE state_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Versioning
    version INT NOT NULL,                       -- 在 session 內單調遞增（從 1 開始）
    parent_version INT,                         -- 上個版本（用於 time-travel）
    
    -- State content
    turn_num INT NOT NULL,
    state_data JSONB NOT NULL,                  -- 完整 LoopState 序列化
    
    -- Checksum（防意外篡改）
    state_hash VARCHAR(64) NOT NULL,            -- SHA-256 of state_data
    
    -- Why this snapshot exists
    reason VARCHAR(64) NOT NULL,                -- "turn_end" / "hitl_pause" / "error" / "manual"
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE (session_id, version)
);

CREATE INDEX idx_state_snapshots_session ON state_snapshots(session_id, version DESC);

-- 防 update / delete（append-only）
CREATE OR REPLACE FUNCTION prevent_state_snapshot_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'state_snapshots is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER state_snapshots_no_update
    BEFORE UPDATE OR DELETE ON state_snapshots
    FOR EACH ROW EXECUTE FUNCTION prevent_state_snapshot_modification();
```

### `loop_states`（current state pointer）
> 每個 session 當前 state（快取，避免每次都查最新 snapshot）

```sql
CREATE TABLE loop_states (
    session_id UUID PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    current_snapshot_id UUID NOT NULL REFERENCES state_snapshots(id),
    current_version INT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Group 6: Governance（範疇 9）

### `approvals`
> HITL 審批記錄

```sql
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- What needs approval
    action_type VARCHAR(64) NOT NULL,           -- "tool_call" / "send_email" / "modify_data"
    action_summary TEXT NOT NULL,
    action_payload JSONB NOT NULL,
    
    -- Risk
    risk_level VARCHAR(32) NOT NULL,            -- low / medium / high / critical
    risk_score DECIMAL(3, 2),
    risk_reasoning TEXT,
    
    -- Approver
    required_approver_role VARCHAR(64),
    approver_user_id UUID REFERENCES users(id),
    
    -- State
    status VARCHAR(32) NOT NULL DEFAULT 'pending',  -- pending / approved / rejected / expired
    decision_reason TEXT,
    
    -- Notification
    teams_notification_sent BOOLEAN DEFAULT FALSE,
    teams_message_id VARCHAR(256),
    
    -- Lifecycle
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    decided_at TIMESTAMPTZ
);

CREATE INDEX idx_approvals_status ON approvals(status);
CREATE INDEX idx_approvals_session ON approvals(session_id);
CREATE INDEX idx_approvals_pending ON approvals(created_at) WHERE status = 'pending';
```

### `risk_assessments`
```sql
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    tool_call_id UUID REFERENCES tool_calls(id),
    
    risk_level VARCHAR(32) NOT NULL,
    risk_score DECIMAL(3, 2) NOT NULL,
    
    triggered_rules JSONB DEFAULT '[]',          -- 觸發的政策規則
    reasoning TEXT,
    
    requires_approval BOOLEAN NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_session ON risk_assessments(session_id);
```

### `guardrail_events`
> Guardrail 觸發事件（input / output / tool / tripwire）

```sql
CREATE TABLE guardrail_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    
    layer VARCHAR(32) NOT NULL,                 -- "input" / "output" / "tool" / "tripwire"
    check_type VARCHAR(64) NOT NULL,            -- "pii" / "jailbreak" / "toxicity" / "permission"
    
    passed BOOLEAN NOT NULL,
    severity VARCHAR(32),                       -- "info" / "warning" / "error" / "critical"
    
    detected_pattern TEXT,
    action_taken VARCHAR(64),                   -- "allow" / "block" / "tripwire_fired"
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_guardrail_events_session ON guardrail_events(session_id);
CREATE INDEX idx_guardrail_events_layer ON guardrail_events(layer);
CREATE INDEX idx_guardrail_events_failed ON guardrail_events(created_at) WHERE passed = FALSE;
```

---

## Group 7: Audit（**Append-Only**）

### `audit_log`
> 所有重要操作的不可篡改紀錄。**範疇 9 核心**。

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    
    -- Identity
    tenant_id UUID NOT NULL,
    user_id UUID,                               -- nullable for system operations
    session_id UUID,
    
    -- Operation
    operation VARCHAR(128) NOT NULL,            -- "tool_executed" / "approval_granted" / etc.
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(256),
    
    -- Detail
    operation_data JSONB NOT NULL,
    operation_result VARCHAR(32),               -- "success" / "failure" / "denied"
    
    -- Chain integrity（hash chain）
    previous_log_hash VARCHAR(64),
    current_log_hash VARCHAR(64) NOT NULL,
    
    timestamp_ms BIGINT NOT NULL,               -- 精確時間戳
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_log(tenant_id);
CREATE INDEX idx_audit_session ON audit_log(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX idx_audit_user ON audit_log(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_operation ON audit_log(operation);
CREATE INDEX idx_audit_time ON audit_log(timestamp_ms DESC);

-- Append-only enforcement（修正：UPDATE/DELETE 與 TRUNCATE 必須分開）
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only';
END;
$$ LANGUAGE plpgsql;

-- ROW-level trigger for UPDATE/DELETE
CREATE TRIGGER audit_log_no_update_delete
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- STATEMENT-level trigger for TRUNCATE（必須分開）
CREATE TRIGGER audit_log_no_truncate
    BEFORE TRUNCATE ON audit_log
    FOR EACH STATEMENT EXECUTE FUNCTION prevent_audit_modification();

-- 額外防護：撤銷 app role 的危險權限
-- （由 DBA 在部署時執行，不寫在 migration）
-- REVOKE TRUNCATE ON audit_log FROM ipa_app_role;
-- REVOKE DROP ON audit_log FROM ipa_app_role;
```

#### 額外安全措施（DBA 部署檢查清單）
- [ ] 應用 role（`ipa_app_role`）只有 INSERT 權限
- [ ] DDL role（`ipa_admin_role`）與 app role 分離
- [ ] `previous_log_hash` 改為 NOT NULL（首筆用 sentinel `'0'.repeat(64)`）
- [ ] 定期 hash chain 完整性檢查（每日批次驗證 chain 連續性）

---

## Group 8: Verification（範疇 10）

### `verification_results`
```sql
CREATE TABLE verification_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    verifier_type VARCHAR(64) NOT NULL,         -- "rules" / "llm_judge" / "visual"
    target_type VARCHAR(64) NOT NULL,           -- "final_output" / "tool_result" / "intermediate"
    target_reference VARCHAR(256),              -- e.g., message_id
    
    -- Result
    passed BOOLEAN NOT NULL,
    confidence DECIMAL(3, 2),
    reasoning TEXT,
    
    -- Self-correction tracking
    correction_attempt INT NOT NULL DEFAULT 0,  -- 第幾次嘗試
    
    -- LLM-judge specific
    judge_model VARCHAR(64),
    judge_tokens_used INT,
    
    duration_ms INT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_verification_session ON verification_results(session_id);
CREATE INDEX idx_verification_failed ON verification_results(created_at) WHERE passed = FALSE;
```

---

## Group 9: Subagent（範疇 11）

### `subagent_runs`
```sql
CREATE TABLE subagent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Mode
    mode VARCHAR(32) NOT NULL,                  -- "fork" / "teammate" / "handoff" / "as_tool"
    role VARCHAR(64),                           -- e.g., "analyst" / "researcher"
    
    -- Task
    task_description TEXT NOT NULL,
    
    -- Lifecycle
    status VARCHAR(32) NOT NULL DEFAULT 'running',  -- running / completed / failed
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Result（必須 ≤ 2K token，範疇 4 約束）
    summary TEXT,
    summary_tokens INT,
    
    -- Resource usage
    total_turns INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    total_cost_usd DECIMAL(10, 4) DEFAULT 0,
    
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_subagent_parent ON subagent_runs(parent_session_id);
CREATE INDEX idx_subagent_status ON subagent_runs(status);
```

### `subagent_messages`
> Teammate 模式的 mailbox 訊息

```sql
CREATE TABLE subagent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_run_id UUID NOT NULL REFERENCES subagent_runs(id),
    to_run_id UUID REFERENCES subagent_runs(id),    -- NULL = broadcast
    
    content JSONB NOT NULL,
    delivered BOOLEAN NOT NULL DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `agent_catalog`（Sprint 57.70 — per-tenant AgentSpec definitions）
> 每租戶的 AgentSpec 定義目錄：Cat 11 Subagent Registry 與 HANDOFF persona 解析的持久後盾。
> 取代 Sprint 57.68 的硬編碼 3-entry persona stand-in（`persona_registry.py`）。
> 欄位對齊 mockup AgentSpec（`reference/design-mockups/page-agents.jsx`）。
> Multi-tenant 鐵律：`TenantScopedMixin` + RLS（2 policy + FORCE，mirror `0019`）；
> `UNIQUE(tenant_id, key)` 使 role key 每租戶唯一。budget/tools/allowed_modes 已 STORED（JSONB），
> 但尚未在 loop 中 enforce（Sprint 57.70 §9 — 延後）。

```sql
CREATE TABLE agent_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,  -- TenantScopedMixin

    key VARCHAR(64) NOT NULL,                  -- role / immutable id (e.g. "researcher")
    name VARCHAR(128) NOT NULL,
    model VARCHAR(128),                        -- nullable
    system_prompt TEXT NOT NULL,
    allowed_modes JSONB NOT NULL DEFAULT '[]',  -- subset of fork/as_tool/teammate/handoff
    status VARCHAR(32) NOT NULL DEFAULT 'live',  -- live / staging
    metadata JSONB NOT NULL DEFAULT '{}',       -- budget{max_tokens,duration,concurrent,depth} + tools[]
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_agent_catalog_tenant_key UNIQUE (tenant_id, key)
);

CREATE INDEX idx_agent_catalog_tenant ON agent_catalog(tenant_id);

-- RLS（2 policy + FORCE；check_rls_policies lint）
ALTER TABLE agent_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_catalog FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_agent_catalog ON agent_catalog
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_insert_agent_catalog ON agent_catalog
    FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

> Alembic `0023_agent_catalog` 建表 + RLS + 為**既有**租戶 materialize 3 個 default agents
> （researcher/reviewer/planner）；新/空租戶在 runtime 由 `persona_registry.py:DEFAULT_AGENTS`
> 硬編碼 fallback 覆蓋（無 read-path lazy-write）。

---

## Group 10: Workers & Queue

### `worker_tasks`
> 任務佇列（即使用 Celery / Temporal，仍需 DB 紀錄供查詢）

```sql
CREATE TABLE worker_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    
    task_type VARCHAR(64) NOT NULL,             -- "agent_loop" / "memory_extraction" / "verification"
    queue_name VARCHAR(64) NOT NULL,
    
    payload JSONB NOT NULL,
    
    -- Lifecycle
    status VARCHAR(32) NOT NULL DEFAULT 'pending',  -- pending / running / succeeded / failed / cancelled
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 2,
    
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Worker info
    worker_id VARCHAR(128),
    
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_worker_tasks_status ON worker_tasks(status, queue_name);
CREATE INDEX idx_worker_tasks_session ON worker_tasks(session_id);
```

---

## Group 11: Business Domain

> Phase 55 細化。先列骨架。

```sql
-- Patrol
CREATE TABLE patrol_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    -- ... (Phase 55 設計)
);

-- Correlation, Rootcause, Audit (business), Incident
-- ... 同上
```

---

## Group 12: Production-Critical（2026-04-23 新增）

> **校正**：原版缺多個 SaaS production 必需表。本 Group 必須在 Phase 49 Sprint 49.2 建立。

### `api_keys`
> Tenant API 金鑰管理（外部系統呼叫 V2 API 用）

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    name VARCHAR(128) NOT NULL,                 -- 用途說明
    key_prefix VARCHAR(16) NOT NULL,            -- 顯示用前 8 碼（如 "ipa_xxxxx..."）
    key_hash VARCHAR(128) NOT NULL,             -- bcrypt hash
    
    permissions JSONB DEFAULT '[]',             -- 權限範圍
    rate_limit_tier VARCHAR(32) DEFAULT 'standard',
    
    status VARCHAR(32) NOT NULL DEFAULT 'active',  -- active / revoked / expired
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_active ON api_keys(status) WHERE status = 'active';
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
```

### `rate_limits`
> Per-tenant rate limit 配額追蹤

```sql
CREATE TABLE rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    resource_type VARCHAR(64) NOT NULL,         -- "llm_tokens" / "tool_calls" / "api_requests"
    window_type VARCHAR(32) NOT NULL,           -- "minute" / "hour" / "day" / "month"
    
    quota INT NOT NULL,                         -- 上限
    used INT NOT NULL DEFAULT 0,
    
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    
    UNIQUE (tenant_id, resource_type, window_type, window_start)
);

CREATE INDEX idx_rate_limits_lookup ON rate_limits(tenant_id, resource_type, window_end DESC);
```

### `cost_ledger`
> 細粒度成本紀錄（per LLM call / tool call）

```sql
CREATE TABLE cost_ledger (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    
    cost_type VARCHAR(32) NOT NULL,             -- "llm" / "tool" / "storage" / "compute"
    sub_type VARCHAR(64),                       -- "azure_openai_gpt5_4_input" / etc.
    
    quantity DECIMAL(20, 6) NOT NULL,           -- tokens / API calls / GB-hours
    unit VARCHAR(32) NOT NULL,                  -- "tokens" / "calls" / "gb_hours"
    
    unit_cost_usd DECIMAL(14, 6) NOT NULL,      -- 改高精度（原 DECIMAL(10,4) 不夠）
    total_cost_usd DECIMAL(14, 6) NOT NULL,
    
    metadata JSONB DEFAULT '{}',                -- model / provider / cache_hit etc.
    incurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cost_tenant_time ON cost_ledger(tenant_id, incurred_at DESC);
CREATE INDEX idx_cost_session ON cost_ledger(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX idx_cost_type ON cost_ledger(cost_type);
```

### `llm_invocations`
> 每次 LLM call 完整紀錄（對應 LangSmith run）

```sql
CREATE TABLE llm_invocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    parent_invocation_id UUID REFERENCES llm_invocations(id),  -- 樹狀（subagent 用）
    
    -- Provider info
    provider VARCHAR(32) NOT NULL,              -- "azure_openai" / "anthropic" / "openai"
    model VARCHAR(64) NOT NULL,
    deployment_name VARCHAR(128),               -- Azure deployment name
    
    -- Request
    request_messages JSONB,                     -- 完整 messages（可選 truncate）
    request_tools JSONB,                        -- tool schemas
    request_metadata JSONB,                     -- temperature / max_tokens 等
    
    -- Response
    response_content TEXT,
    response_tool_calls JSONB,
    response_finish_reason VARCHAR(32),
    
    -- Tokens（含 prompt cache，2025+ 標準）
    prompt_tokens INT,
    completion_tokens INT,
    cache_read_input_tokens INT,                -- prompt caching hit
    cache_write_input_tokens INT,               -- prompt caching miss
    thinking_tokens INT,                        -- extended thinking
    total_tokens INT,
    
    -- Performance
    latency_ms INT,
    time_to_first_token_ms INT,
    
    -- Cost（也記在 cost_ledger，這裡為 denormalized 方便）
    cost_usd DECIMAL(14, 6),
    
    -- Status
    status VARCHAR(32) NOT NULL,                -- "success" / "error" / "timeout"
    error_message TEXT,
    
    invoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_llm_inv_tenant ON llm_invocations(tenant_id, invoked_at DESC);
CREATE INDEX idx_llm_inv_session ON llm_invocations(session_id);
CREATE INDEX idx_llm_inv_parent ON llm_invocations(parent_invocation_id) WHERE parent_invocation_id IS NOT NULL;
CREATE INDEX idx_llm_inv_model ON llm_invocations(provider, model);
```

### `outbox`
> 事務性訊息發送（Teams 通知 / Email / Webhook 用 outbox pattern）

```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    destination VARCHAR(32) NOT NULL,           -- "teams" / "email" / "webhook"
    destination_address VARCHAR(512) NOT NULL,  -- channel id / email / URL
    
    payload JSONB NOT NULL,
    
    status VARCHAR(32) NOT NULL DEFAULT 'pending',  -- pending / sending / sent / failed
    retry_count INT NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMPTZ,
    
    -- Provenance
    source_type VARCHAR(64) NOT NULL,           -- "approval_request" / "alert" / etc.
    source_id VARCHAR(256),
    
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_outbox_pending ON outbox(next_retry_at) WHERE status IN ('pending', 'failed');
CREATE INDEX idx_outbox_tenant ON outbox(tenant_id);
```

---

## 修訂：Messages 表 Day 1 Partition

> **校正（2026-04-23）**：原版未 partition。1 年內可能撞牆。

### `messages` 改為月度 partition

```sql
-- 主表（partitioned by created_at month）
CREATE TABLE messages (
    id UUID NOT NULL,
    session_id UUID NOT NULL,
    tenant_id UUID NOT NULL,                    -- 新增（原版缺）
    sequence_num INT NOT NULL,
    turn_num INT NOT NULL,
    role VARCHAR(32) NOT NULL,
    content_type VARCHAR(32) NOT NULL,
    content JSONB NOT NULL,
    model VARCHAR(64),
    tokens_in INT,
    tokens_out INT,
    is_compacted BOOLEAN NOT NULL DEFAULT FALSE,
    -- 注意：compacted_from_ids 改為獨立 message_compaction_links 表（見 P1）
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (id, created_at),               -- partition key 必須在 PK
    UNIQUE (session_id, sequence_num, created_at)
) PARTITION BY RANGE (created_at);

-- 第一個月分區
CREATE TABLE messages_2026_05 PARTITION OF messages
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE messages_2026_06 PARTITION OF messages
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- 後續用 pg_partman 自動建立未來分區

-- 索引（每個分區自動繼承）
CREATE INDEX idx_messages_session_seq ON messages(session_id, sequence_num);
CREATE INDEX idx_messages_tenant_session ON messages(tenant_id, session_id, created_at DESC);
CREATE INDEX idx_messages_role ON messages(role);
```

### `audit_log` 同樣 partition

```sql
-- audit_log 改為月度 partition + 冷儲分層
CREATE TABLE audit_log (
    id BIGSERIAL NOT NULL,
    tenant_id UUID NOT NULL,
    -- ... 其他欄位同原版
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 月度分區 + 90 天後移到冷儲
```

### `message_events` 同樣 partition

> 保留期 30 天 + archive 到 object store

---

## 修訂：cost_usd 精度提升

所有 `cost_usd` 欄位從 `DECIMAL(10, 4)` 改為 `DECIMAL(14, 6)`：

```sql
-- sessions.total_cost_usd
ALTER TABLE sessions ALTER COLUMN total_cost_usd TYPE DECIMAL(14, 6);
-- subagent_runs.total_cost_usd
ALTER TABLE subagent_runs ALTER COLUMN total_cost_usd TYPE DECIMAL(14, 6);
```

**理由**：GPT-5.4-nano 等便宜模型 cost per 1K tokens 可能 $0.0001 級別，4 位精度已截斷。

---

## ER 關係圖（核心）

```
tenants ──┬── users ──── user_roles ──── roles ──── role_permissions
          │
          ├── memory_tenant
          │
          └── sessions ──┬── messages
                         ├── message_events
                         ├── tool_calls ──── tool_results
                         ├── state_snapshots ── loop_states
                         ├── approvals
                         ├── risk_assessments
                         ├── guardrail_events
                         ├── verification_results
                         ├── subagent_runs ── subagent_messages
                         ├── worker_tasks
                         └── memory_session_summary

audit_log（橫切，引用所有上表）

memory_system（全局）
memory_role（角色級）
memory_user（使用者級）

tools_registry（全局工具元數據）
```

---

## Vector DB（Qdrant）整合

PostgreSQL 不存 vector，向量在 Qdrant：

```
Qdrant collections（per tenant namespace）:
├── tenant:{tenant_id}:memory_tenant     # Layer 2 vectors
├── tenant:{tenant_id}:memory_user       # Layer 4 vectors
└── tenant:{tenant_id}:knowledge         # KB vectors
```

PostgreSQL 中只存 `vector_id` reference，實際向量在 Qdrant。

---

## Migration 策略

### Phase 49 Sprint 49.2 執行順序（2026-04-23 修訂）

```
0001_initial_identity.sql        # tenants / users / roles / role_permissions / user_roles
0002_audit.sql                   # audit_log（先建，後續所有 insert 都記）
0003_api_keys_rate_limits.sql    # api_keys / rate_limits
0004_sessions_partitioned.sql    # sessions / messages (partitioned) / message_events (partitioned)
0005_tools.sql                   # tools_registry / tool_calls / tool_results
0006_memory.sql                  # 5 個 memory tables
0007_state.sql                   # state_snapshots / loop_states + append-only triggers
0008_governance.sql              # approvals / risk_assessments / guardrail_events
0009_verification.sql            # verification_results
0010_subagent.sql                # subagent_runs / subagent_messages
0011_workers_outbox.sql          # worker_tasks / outbox
0012_cost_llm.sql                # cost_ledger / llm_invocations
0013_rls_policies.sql            # 啟用所有表 RLS + policies
0014_indexes_optimization.sql    # 補完優化索引
```

**順序變動原因**：
- audit_log 提前到 0002（其他表 insert 都要 audit）
- api_keys / rate_limits 在 sessions 之前（API call 開始就需要）
- RLS policies 統一最後一個 migration（讓所有表都建好後一次套用）

每個 migration 都有對應 down 方法（雖然從零，未來可能需要回滾）。

---

## 性能考量

### 索引策略
- 所有 `tenant_id` 帶索引（multi-tenant query 必需）
- 所有 `session_id` 帶索引（session-scoped query 必需）
- 時間欄位（`created_at`, `last_active_at`）帶索引（時間範圍 query）
- Partial index 用於高頻條件（如 `WHERE status = 'pending'`）

### Partition 策略（Phase 56+ 考慮）
- `messages` / `message_events` / `audit_log` 可按月 partition
- `state_snapshots` 可按 session 範圍 partition

### 預估容量（V2 初期）
- 1000 sessions/day × 50 messages/session = 50K rows/day
- 1 年 = ~18M rows（messages）
- audit_log 約 2-3 倍 = ~50M rows
- **單表 < 100M 不需 partition**

---

## ORM Models 對應（SQLAlchemy 2.x async）

```python
# backend/src/infrastructure/database/models/
├── __init__.py
├── base.py              # DeclarativeBase
├── identity.py          # Tenant / User / Role / RolePermission
├── sessions.py          # Session / Message / MessageEvent
├── tools.py             # ToolRegistry / ToolCall / ToolResult
├── memory.py            # 5 Memory tables
├── state.py             # StateSnapshot / LoopState
├── governance.py        # Approval / RiskAssessment / GuardrailEvent
├── audit.py             # AuditLog (read-only after insert)
├── verification.py      # VerificationResult
├── subagent.py          # SubagentRun / SubagentMessage
└── workers.py           # WorkerTask
```

每個 model 包含：
- Async query methods
- Pydantic 對應 schema（用於 API）
- Migration auto-generation 支援

---

## 待 Phase 49.2 確認的細節

- [ ] UUID v4 vs v7（v7 帶時序，效能較好）
- [ ] JSONB vs separate tables（部分 metadata 可能該獨立成表）
- [ ] Soft delete vs hard delete 政策
- [ ] Encryption at rest（敏感欄位如 PII）
- [ ] Row-level security（PostgreSQL RLS）用於 tenant 隔離

---

## 結論

本 schema 設計：
- ✅ 涵蓋 11 範疇所需資料
- ✅ Multi-tenant native
- ✅ Append-only for audit / state
- ✅ 配合 Vector DB（Qdrant）
- ✅ 為 Phase 49 Sprint 49.2 提供完整起點

**下一步**：Sprint 49.2 執行時依此設計建立 Alembic migrations + ORM models。
