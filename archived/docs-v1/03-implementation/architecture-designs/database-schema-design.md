# Database Schema Design - IPA Platform

**版本**: v1.0.0
**日期**: 2025-11-20
**數據庫**: PostgreSQL 16

---

## 🎯 設計原則

### DDD (Domain-Driven Design)
- 遵循聚合根 (Aggregate Root) 設計
- 每個聚合有明確的邊界
- 使用值對象 (Value Objects) 表示不可變數據

### 數據完整性
- 外鍵約束確保參照完整性
- Check 約束驗證數據有效性
- Unique 約束防止重複數據

### 性能優化
- 適當的索引策略
- 分區表 (如果需要)
- 審計日誌表分離

---

## 📊 Entity Relationship Diagram

```
┌─────────────────┐
│     users       │ (認證用戶)
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐       ┌─────────────────┐
│   workflows     │◄──────┤ workflow_versions│
│  (工作流定義)    │ 1   N │  (版本管理)      │
└────────┬────────┘       └─────────────────┘
         │ 1
         │
         │ N
┌────────▼────────┐       ┌─────────────────┐
│   executions    │──────►│ execution_steps │
│   (執行實例)     │ 1   N │  (執行步驟)      │
└────────┬────────┘       └─────────────────┘
         │
         │ N                ┌─────────────────┐
         └─────────────────►│ execution_logs  │
                            │  (執行日誌)      │
                            └─────────────────┘

┌─────────────────┐
│     agents      │ (Agent 配置)
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐
│   agent_tools   │ (Agent 工具配置)
└─────────────────┘

┌─────────────────┐
│  audit_logs     │ (審計日誌)
└─────────────────┘
```

---

## 📋 Tables 詳細設計

### 1. users (用戶表)

**用途**: 存儲平台用戶信息

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);
```

**說明**:
- UUID 作為主鍵，避免順序可預測
- email 和 username 唯一索引
- 支持軟刪除 (is_active)
- 記錄最後登入時間

---

### 2. workflows (工作流定義表)

**用途**: 存儲工作流定義

```sql
CREATE TYPE workflow_status AS ENUM ('draft', 'active', 'archived');

CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status workflow_status DEFAULT 'draft',
    current_version_id UUID,
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT name_not_empty CHECK (length(trim(name)) > 0)
);

CREATE INDEX idx_workflows_created_by ON workflows(created_by);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_tags ON workflows USING GIN(tags);
CREATE INDEX idx_workflows_metadata ON workflows USING GIN(metadata);
```

**說明**:
- 工作流支持多版本
- 使用 JSONB 存儲靈活的 metadata
- GIN 索引支持 array 和 JSONB 查詢
- created_by 外鍵防止刪除有工作流的用戶

---

### 3. workflow_versions (工作流版本表)

**用途**: 支持工作流版本管理和回滾

```sql
CREATE TABLE workflow_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    definition JSONB NOT NULL,
    change_summary TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(workflow_id, version_number),
    CONSTRAINT version_number_positive CHECK (version_number > 0)
);

-- 更新 workflows 表的外鍵
ALTER TABLE workflows
    ADD CONSTRAINT fk_current_version
    FOREIGN KEY (current_version_id)
    REFERENCES workflow_versions(id)
    ON DELETE SET NULL;

CREATE INDEX idx_workflow_versions_workflow_id ON workflow_versions(workflow_id);
CREATE INDEX idx_workflow_versions_created_at ON workflow_versions(created_at DESC);
```

**說明**:
- version_number 從 1 開始遞增
- definition 存儲完整的工作流定義 (JSON)
- 支持版本回滾
- CASCADE 刪除工作流時同時刪除所有版本

---

### 4. executions (執行實例表)

**用途**: 存儲工作流執行實例

```sql
CREATE TYPE execution_status AS ENUM (
    'pending',      -- 等待執行
    'running',      -- 執行中
    'paused',       -- 暫停
    'completed',    -- 成功完成
    'failed',       -- 失敗
    'cancelled'     -- 已取消
);

CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE RESTRICT,
    workflow_version_id UUID NOT NULL REFERENCES workflow_versions(id) ON DELETE RESTRICT,
    triggered_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status execution_status DEFAULT 'pending',
    input_data JSONB DEFAULT '{}',
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT duration_positive CHECK (duration_ms >= 0),
    CONSTRAINT retry_count_non_negative CHECK (retry_count >= 0),
    CONSTRAINT completed_after_started CHECK (completed_at IS NULL OR completed_at >= started_at)
);

CREATE INDEX idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX idx_executions_triggered_by ON executions(triggered_by);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_created_at ON executions(created_at DESC);
CREATE INDEX idx_executions_completed_at ON executions(completed_at DESC) WHERE completed_at IS NOT NULL;
```

**說明**:
- 記錄完整的執行上下文
- 支持重試機制 (retry_count)
- 計算執行時長 (duration_ms)
- 分別索引 created_at 和 completed_at

---

### 5. execution_steps (執行步驟表)

**用途**: 存儲工作流執行的每個步驟

```sql
CREATE TYPE step_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'skipped'
);

CREATE TABLE execution_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    step_name VARCHAR(255) NOT NULL,
    step_index INTEGER NOT NULL,
    step_type VARCHAR(100) NOT NULL,  -- 'agent', 'webhook', 'approval', etc.
    status step_status DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT step_index_non_negative CHECK (step_index >= 0),
    CONSTRAINT duration_positive CHECK (duration_ms >= 0)
);

CREATE INDEX idx_execution_steps_execution_id ON execution_steps(execution_id);
CREATE INDEX idx_execution_steps_status ON execution_steps(status);
CREATE INDEX idx_execution_steps_step_index ON execution_steps(execution_id, step_index);
```

**說明**:
- step_index 表示步驟順序
- 支持不同類型的步驟 (agent, webhook, approval)
- CASCADE 刪除執行時同時刪除步驟

---

### 6. execution_logs (執行日誌表)

**用途**: 存儲詳細的執行日誌

```sql
CREATE TYPE log_level AS ENUM ('debug', 'info', 'warning', 'error', 'critical');

CREATE TABLE execution_logs (
    id BIGSERIAL PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    execution_step_id UUID REFERENCES execution_steps(id) ON DELETE CASCADE,
    level log_level NOT NULL,
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_execution_logs_execution_id ON execution_logs(execution_id);
CREATE INDEX idx_execution_logs_step_id ON execution_logs(execution_step_id);
CREATE INDEX idx_execution_logs_level ON execution_logs(level);
CREATE INDEX idx_execution_logs_created_at ON execution_logs(created_at DESC);

-- 分區策略 (可選，用於大量日誌)
-- 按月分區
CREATE TABLE execution_logs_2025_11 PARTITION OF execution_logs
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

**說明**:
- BIGSERIAL 支持大量日誌
- 可選的時間分區提升查詢性能
- context 存儲額外的上下文信息

---

### 7. agents (Agent 配置表)

**用途**: 存儲 Agent 配置和定義

```sql
CREATE TYPE agent_type AS ENUM ('agent_framework', 'autogen', 'custom');
CREATE TYPE agent_status AS ENUM ('active', 'inactive', 'deprecated');

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type agent_type NOT NULL,
    status agent_status DEFAULT 'active',
    configuration JSONB NOT NULL,  -- Agent 特定配置
    system_prompt TEXT,
    model_name VARCHAR(100),  -- e.g., 'gpt-4', 'gpt-35-turbo'
    temperature DECIMAL(3, 2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT temperature_range CHECK (temperature >= 0 AND temperature <= 2),
    CONSTRAINT max_tokens_positive CHECK (max_tokens > 0)
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_type ON agents(type);
CREATE INDEX idx_agents_created_by ON agents(created_by);
```

**說明**:
- 支持不同類型的 Agent (Agent Framework, AutoGen, Custom)
- configuration 存儲 Agent 特定配置
- 溫度和 token 限制可配置

---

### 8. agent_tools (Agent 工具配置表)

**用途**: 存儲 Agent 可用的工具

```sql
CREATE TABLE agent_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    tool_type VARCHAR(100) NOT NULL,  -- 'function', 'api', 'plugin'
    configuration JSONB NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(agent_id, tool_name)
);

CREATE INDEX idx_agent_tools_agent_id ON agent_tools(agent_id);
CREATE INDEX idx_agent_tools_is_enabled ON agent_tools(is_enabled);
```

**說明**:
- 多對多關係: Agent ←→ Tools
- 每個 Agent 可以有多個 Tools
- 支持啟用/禁用工具

---

### 9. audit_logs (審計日誌表)

**用途**: 記錄所有關鍵操作的審計日誌

```sql
CREATE TYPE audit_action AS ENUM (
    'create', 'update', 'delete',
    'login', 'logout',
    'execute', 'cancel'
);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action audit_action NOT NULL,
    resource_type VARCHAR(100) NOT NULL,  -- 'workflow', 'execution', 'agent'
    resource_id UUID,
    changes JSONB,  -- 記錄變更前後的數據
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- 分區策略 (按月)
CREATE TABLE audit_logs_2025_11 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

**說明**:
- 記錄所有關鍵操作
- changes 存儲變更詳情 (before/after)
- 記錄 IP 和 User Agent 用於安全分析
- 按月分區提升性能

---

## 🔧 Database Functions & Triggers

### 1. 自動更新 updated_at

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 為所有需要的表創建 trigger
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_executions_updated_at
    BEFORE UPDATE ON executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_execution_steps_updated_at
    BEFORE UPDATE ON execution_steps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 2. 自動計算執行時長

```sql
CREATE OR REPLACE FUNCTION calculate_execution_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_ms = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)) * 1000;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_execution_duration_trigger
    BEFORE UPDATE ON executions
    FOR EACH ROW
    WHEN (NEW.completed_at IS NOT NULL AND OLD.completed_at IS NULL)
    EXECUTE FUNCTION calculate_execution_duration();

CREATE TRIGGER calculate_execution_step_duration_trigger
    BEFORE UPDATE ON execution_steps
    FOR EACH ROW
    WHEN (NEW.completed_at IS NOT NULL AND OLD.completed_at IS NULL)
    EXECUTE FUNCTION calculate_execution_duration();
```

### 3. 審計日誌自動記錄

```sql
CREATE OR REPLACE FUNCTION log_workflow_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, changes)
        VALUES (NEW.created_by, 'create', 'workflow', NEW.id, to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, changes)
        VALUES (NEW.created_by, 'update', 'workflow', NEW.id,
                jsonb_build_object('before', to_jsonb(OLD), 'after', to_jsonb(NEW)));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, changes)
        VALUES (OLD.created_by, 'delete', 'workflow', OLD.id, to_jsonb(OLD));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workflow_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION log_workflow_changes();
```

---

## 📊 索引策略總結

### 主鍵索引
- 所有表的 UUID 主鍵自動創建 B-tree 索引

### 外鍵索引
- 所有外鍵字段創建索引加速 JOIN

### 查詢優化索引
- 狀態字段 (status) - 過濾常用
- 時間字段 (created_at, completed_at) - 排序和範圍查詢
- 用戶 ID (created_by, triggered_by) - 多租戶查詢

### 特殊索引
- GIN 索引 for JSONB 和 array 字段
- 部分索引 (partial index) for 非 NULL 條件

---

## 🔒 安全考慮

### 1. Row Level Security (RLS)

```sql
-- 啟用 RLS
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

-- 策略: 用戶只能看到自己創建的工作流
CREATE POLICY user_workflows_policy ON workflows
    USING (created_by = current_setting('app.current_user_id')::UUID);

-- 策略: 超級用戶可以看到所有
CREATE POLICY admin_workflows_policy ON workflows
    USING (current_setting('app.is_superuser')::BOOLEAN = TRUE);
```

### 2. 數據加密

- 敏感字段 (如 hashed_password) 在應用層加密
- PostgreSQL 透明數據加密 (TDE) at rest
- SSL/TLS 連接加密 in transit

---

## 📈 性能優化建議

### 1. 分區策略

**execution_logs** 和 **audit_logs**:
- 按月分區
- 自動歸檔舊數據
- 定期刪除過期分區

### 2. 查詢優化

```sql
-- 添加覆蓋索引 (covering index)
CREATE INDEX idx_executions_list ON executions(workflow_id, created_at DESC)
    INCLUDE (status, triggered_by);

-- 物化視圖用於儀表板
CREATE MATERIALIZED VIEW workflow_execution_stats AS
SELECT
    workflow_id,
    COUNT(*) as total_executions,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    AVG(duration_ms) as avg_duration_ms
FROM executions
GROUP BY workflow_id;

CREATE UNIQUE INDEX ON workflow_execution_stats(workflow_id);

-- 定期刷新
REFRESH MATERIALIZED VIEW CONCURRENTLY workflow_execution_stats;
```

### 3. 連接池

- 使用 PgBouncer 管理連接池
- Transaction pooling mode
- Max connections: 100 (根據負載調整)

---

## 📝 Migration 策略

### 版本控制
- 使用 Alembic 管理 migrations
- 每個 migration 包含 upgrade 和 downgrade
- Migration 文件命名: `{revision}_{description}.py`

### 部署流程
1. 在開發環境測試 migration
2. 在 staging 環境驗證
3. 備份 production 數據庫
4. 在維護窗口執行 migration
5. 驗證數據完整性
6. 監控應用性能

---

## 🔄 未來擴展考慮

### 1. 多租戶支持
- 添加 `tenant_id` 到主要表
- 分區或 Schema-per-tenant 策略

### 2. 事件溯源
- 添加 `events` 表記錄所有狀態變更
- 支持事件重放和審計

### 3. 讀寫分離
- Read replica for 查詢密集型操作
- 主庫處理寫操作

---

**文檔版本**: v1.0.0
**最後更新**: 2025-11-20
**下次審查**: Sprint 1 開始前
