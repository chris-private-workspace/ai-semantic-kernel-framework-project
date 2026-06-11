# IPA Platform 場景用戶指南

**版本**: 1.0.0
**日期**: 2025-12-18
**適用版本**: IPA Platform v0.2.0

---

## 目錄

1. [概述](#概述)
2. [場景 1: IT 工單智能分派](#場景-1-it-工單智能分派)
3. [場景 2: 多 Agent 協作分析](#場景-2-多-agent-協作分析)
4. [場景 3: 自動化報表生成](#場景-3-自動化報表生成)
5. [場景 4: 複雜任務自主規劃](#場景-4-複雜任務自主規劃)
6. [常見問題](#常見問題)

---

## 概述

IPA Platform 提供四個核心業務場景，展示平台的智能自動化能力。每個場景都經過完整設計和驗證，可以直接使用或作為客製化的基礎。

### 場景能力矩陣

| 場景 | 主要能力 | 複雜度 | 適用場景 |
|------|----------|--------|----------|
| IT 工單分派 | 順序處理、路由、審批 | 中等 | IT 服務管理 |
| 多 Agent 協作 | 群組對話、投票、記憶 | 高 | 研究分析、決策支援 |
| 自動化報表 | 並行處理、數據整合 | 中等 | 定期報告、數據彙總 |
| 自主規劃 | 任務分解、動態調整 | 高 | 專案管理、複雜任務 |

---

## 場景 1: IT 工單智能分派

### 業務目標

自動化 IT 工單的接收、分類、路由和分派流程，減少人工處理時間，提升服務效率。

### 使用流程

```
1. 接收工單
   └─ ServiceNow/Email/API 觸發

2. 智能分類
   └─ AI Agent 分析工單內容
   └─ 判定類型 (硬體/軟體/網路/帳戶)
   └─ 評估複雜度 (簡單/中等/複雜)

3. 智能路由
   └─ 簡單工單 → 自動分派
   └─ 中等工單 → 建議分派，等待確認
   └─ 複雜工單 → 人工審批

4. 執行分派
   └─ 通知指派人員
   └─ 更新工單狀態
   └─ 記錄分派決策
```

### 快速開始

#### 步驟 1: 建立分類 Agent

```bash
# 透過 API 建立 Agent
POST /api/v1/agents
{
  "name": "ticket-classifier",
  "type": "classifier",
  "description": "IT 工單分類 Agent",
  "capabilities": ["text_analysis", "classification"]
}
```

#### 步驟 2: 建立路由規則

```bash
# 設定路由條件
POST /api/v1/routing/rules
{
  "name": "ticket-routing",
  "conditions": [
    {
      "field": "complexity",
      "operator": "equals",
      "value": "simple",
      "action": "auto_assign"
    },
    {
      "field": "complexity",
      "operator": "equals",
      "value": "complex",
      "action": "require_approval"
    }
  ]
}
```

#### 步驟 3: 設定審批流程

```bash
# 建立檢查點
POST /api/v1/checkpoints
{
  "name": "complex-ticket-approval",
  "type": "approval",
  "timeout_minutes": 60,
  "approvers": ["it-manager@company.com"],
  "escalation_policy": {
    "enabled": true,
    "escalate_after_minutes": 30,
    "escalate_to": ["it-director@company.com"]
  }
}
```

#### 步驟 4: 建立完整工作流

```bash
# 組裝工作流
POST /api/v1/workflows
{
  "name": "it-ticket-triage",
  "description": "IT 工單智能分派工作流",
  "trigger": {
    "type": "webhook",
    "source": "servicenow"
  },
  "steps": [
    {"agent": "ticket-classifier", "type": "classify"},
    {"type": "routing", "rules": "ticket-routing"},
    {"type": "checkpoint", "condition": "complexity == 'complex'"},
    {"agent": "ticket-assigner", "type": "assign"}
  ]
}
```

### 進階設定

#### 自訂分類類別

```yaml
# backend/templates/scenarios/it_ticket_triage.yaml
classification:
  categories:
    - name: hardware
      keywords: ["電腦", "印表機", "螢幕", "鍵盤"]
      priority: medium
    - name: software
      keywords: ["安裝", "更新", "錯誤", "當機"]
      priority: high
    - name: network
      keywords: ["網路", "連線", "VPN", "Wi-Fi"]
      priority: high
    - name: account
      keywords: ["密碼", "帳號", "權限", "登入"]
      priority: low
```

#### 設定 SLA 追蹤

```yaml
sla_rules:
  simple:
    resolution_hours: 4
    escalation_hours: 2
  medium:
    resolution_hours: 8
    escalation_hours: 4
  complex:
    resolution_hours: 24
    escalation_hours: 12
```

---

## 場景 2: 多 Agent 協作分析

### 業務目標

組織多個專業 Agent 進行協作討論，透過投票機制達成共識，產出綜合分析報告。

### 使用流程

```
1. 任務輸入
   └─ 定義分析主題
   └─ 指定參與 Agent

2. GroupChat 討論
   └─ 各 Agent 輪流發言
   └─ 記錄所有觀點
   └─ Speaker 選擇協調

3. 投票共識
   └─ 提出決策選項
   └─ 各 Agent 投票
   └─ 統計結果

4. 綜合報告
   └─ 彙總各方觀點
   └─ 呈現投票結果
   └─ 產出最終建議
```

### 快速開始

#### 步驟 1: 建立專家 Agent 群組

```bash
# 建立市場分析師
POST /api/v1/agents
{
  "name": "market-analyst",
  "type": "analyst",
  "capabilities": ["market_analysis", "trend_detection"],
  "personality": "數據導向，注重市場趨勢"
}

# 建立技術專家
POST /api/v1/agents
{
  "name": "tech-expert",
  "type": "analyst",
  "capabilities": ["technical_analysis", "feasibility"],
  "personality": "技術導向，注重可行性"
}

# 建立財務顧問
POST /api/v1/agents
{
  "name": "financial-advisor",
  "type": "analyst",
  "capabilities": ["financial_analysis", "risk_assessment"],
  "personality": "風險意識，注重投資回報"
}
```

#### 步驟 2: 設定 GroupChat

```bash
# 建立群組對話
POST /api/v1/groupchat
{
  "name": "investment-analysis",
  "participants": [
    "market-analyst",
    "tech-expert",
    "financial-advisor"
  ],
  "speaker_selection": {
    "strategy": "round_robin",
    "max_turns": 3
  },
  "termination": {
    "type": "max_messages",
    "value": 12
  }
}
```

#### 步驟 3: 設定投票機制

```bash
# 建立投票策略
POST /api/v1/voting
{
  "name": "investment-decision",
  "strategy": "majority",
  "options": ["強烈建議", "建議", "中性", "不建議", "強烈不建議"],
  "tie_breaker": "moderator"
}
```

#### 步驟 4: 執行協作分析

```bash
# 啟動分析任務
POST /api/v1/groupchat/investment-analysis/execute
{
  "topic": "評估投資新創公司 XYZ 的可行性",
  "context": {
    "company": "XYZ Tech",
    "industry": "AI/ML",
    "funding_round": "Series B",
    "requested_amount": 5000000
  },
  "deliverables": ["analysis_report", "voting_result", "recommendation"]
}
```

### 進階設定

#### 自訂發言選擇策略

```yaml
speaker_selection:
  strategies:
    round_robin:
      description: "輪流發言"
    expertise_based:
      description: "根據專業度選擇"
      criteria: ["topic_relevance", "capability_match"]
    moderator_controlled:
      description: "主持人指定"
      moderator_agent: "discussion-moderator"
```

#### 設定記憶持久化

```yaml
memory:
  type: "conversation"
  storage: "redis"
  retention_days: 30
  summary_enabled: true
  summary_interval: 5  # 每 5 條訊息產生摘要
```

---

## 場景 3: 自動化報表生成

### 業務目標

自動從多個數據源收集資料，並行處理後合併生成標準化報表。

### 使用流程

```
1. 報表請求
   └─ 定義報表類型
   └─ 設定時間範圍
   └─ 指定數據源

2. 並行數據採集
   └─ 同時查詢多個系統
   └─ ServiceNow / D365 / 內部 DB
   └─ 快取已獲取數據

3. Fork-Join 處理
   └─ 分支處理各數據源
   └─ 數據清洗和轉換
   └─ 合併結果

4. 報表輸出
   └─ 生成結構化報表
   └─ 支援多種格式 (PDF/Excel/JSON)
   └─ 自動分發
```

### 快速開始

#### 步驟 1: 設定數據連接器

```bash
# 設定 ServiceNow 連接器
POST /api/v1/connectors
{
  "name": "servicenow",
  "type": "servicenow",
  "config": {
    "instance": "your-instance.service-now.com",
    "auth_type": "oauth2",
    "client_id": "{{SERVICENOW_CLIENT_ID}}",
    "client_secret": "{{SERVICENOW_CLIENT_SECRET}}"
  }
}

# 設定 Dynamics 365 連接器
POST /api/v1/connectors
{
  "name": "dynamics365",
  "type": "dynamics365",
  "config": {
    "environment": "https://your-org.crm.dynamics.com",
    "auth_type": "oauth2"
  }
}
```

#### 步驟 2: 定義數據採集任務

```bash
# 建立數據採集工作流
POST /api/v1/workflows
{
  "name": "weekly-report-data",
  "type": "parallel",
  "tasks": [
    {
      "name": "ticket-stats",
      "connector": "servicenow",
      "query": "incident?sysparm_query=opened_at>=javascript:gs.daysAgo(7)"
    },
    {
      "name": "sales-data",
      "connector": "dynamics365",
      "query": "opportunities?$filter=createdon ge @{addDays(utcNow(),-7)}"
    },
    {
      "name": "user-metrics",
      "connector": "internal_db",
      "query": "SELECT * FROM user_activity WHERE date >= NOW() - INTERVAL 7 DAY"
    }
  ],
  "join_strategy": "wait_all",
  "timeout_minutes": 10
}
```

#### 步驟 3: 設定報表模板

```bash
# 建立報表模板
POST /api/v1/templates
{
  "name": "weekly-executive-report",
  "type": "report",
  "format": ["pdf", "excel"],
  "sections": [
    {
      "title": "IT 服務摘要",
      "data_source": "ticket-stats",
      "charts": ["bar", "pie"]
    },
    {
      "title": "銷售績效",
      "data_source": "sales-data",
      "charts": ["line", "table"]
    },
    {
      "title": "用戶活躍度",
      "data_source": "user-metrics",
      "charts": ["area"]
    }
  ]
}
```

#### 步驟 4: 設定定時執行

```bash
# 設定排程觸發器
POST /api/v1/triggers
{
  "name": "weekly-report-schedule",
  "type": "schedule",
  "cron": "0 9 * * MON",  # 每週一早上 9 點
  "workflow": "weekly-report-generation",
  "notifications": {
    "on_complete": ["executive-team@company.com"],
    "on_failure": ["it-admin@company.com"]
  }
}
```

### 進階設定

#### 快取策略

```yaml
cache:
  enabled: true
  strategy: "tiered"
  levels:
    L1:
      type: "memory"
      ttl_seconds: 300
    L2:
      type: "redis"
      ttl_seconds: 3600
    L3:
      type: "database"
      ttl_seconds: 86400
```

#### 錯誤處理

```yaml
error_handling:
  retry:
    max_attempts: 3
    backoff: "exponential"
    initial_delay_ms: 1000
  fallback:
    strategy: "use_cached"
    max_age_hours: 24
  alerts:
    on_failure: true
    channels: ["email", "teams"]
```

---

## 場景 4: 複雜任務自主規劃

### 業務目標

接收高層次目標，自動分解為可執行的子任務，動態調整執行計畫，自主完成複雜任務。

### 使用流程

```
1. 目標輸入
   └─ 定義高層次目標
   └─ 設定約束條件
   └─ 指定可用資源

2. 任務分解
   └─ AI 分析目標
   └─ 識別子任務
   └─ 建立依賴關係

3. 資源匹配
   └─ 能力匹配
   └─ 負載均衡
   └─ 分配 Agent

4. 執行與調整
   └─ 嵌套工作流執行
   └─ 監控進度
   └─ 動態重規劃

5. 完成回報
   └─ 彙總結果
   └─ 學習記錄
```

### 快速開始

#### 步驟 1: 定義可用能力

```bash
# 註冊 Agent 能力
POST /api/v1/capabilities/register
{
  "agent": "dev-agent",
  "capabilities": [
    {
      "name": "code_development",
      "proficiency": 0.9,
      "languages": ["python", "javascript"]
    },
    {
      "name": "code_review",
      "proficiency": 0.85
    }
  ]
}

POST /api/v1/capabilities/register
{
  "agent": "test-agent",
  "capabilities": [
    {
      "name": "unit_testing",
      "proficiency": 0.95
    },
    {
      "name": "integration_testing",
      "proficiency": 0.8
    }
  ]
}
```

#### 步驟 2: 提交高層目標

```bash
# 建立規劃任務
POST /api/v1/planning/goals
{
  "goal": "開發並部署新的用戶認證模組",
  "constraints": {
    "deadline": "2025-01-15",
    "budget_hours": 40,
    "quality_standard": "production"
  },
  "context": {
    "existing_system": "legacy_auth",
    "target_framework": "oauth2",
    "test_coverage_required": 80
  }
}
```

#### 步驟 3: 查看分解計畫

```bash
# 獲取分解結果
GET /api/v1/planning/goals/{goal_id}/plan

# 回應範例
{
  "goal_id": "goal-123",
  "decomposition": {
    "tasks": [
      {
        "id": "task-1",
        "name": "設計認證架構",
        "estimated_hours": 4,
        "dependencies": [],
        "assigned_agent": null
      },
      {
        "id": "task-2",
        "name": "實作 OAuth2 流程",
        "estimated_hours": 16,
        "dependencies": ["task-1"],
        "required_capabilities": ["code_development"]
      },
      {
        "id": "task-3",
        "name": "撰寫單元測試",
        "estimated_hours": 8,
        "dependencies": ["task-2"],
        "required_capabilities": ["unit_testing"]
      },
      {
        "id": "task-4",
        "name": "整合測試",
        "estimated_hours": 6,
        "dependencies": ["task-3"],
        "required_capabilities": ["integration_testing"]
      },
      {
        "id": "task-5",
        "name": "部署上線",
        "estimated_hours": 4,
        "dependencies": ["task-4"],
        "requires_approval": true
      }
    ]
  }
}
```

#### 步驟 4: 執行規劃

```bash
# 啟動執行
POST /api/v1/planning/goals/{goal_id}/execute
{
  "auto_assign": true,
  "checkpoint_on_critical": true,
  "replan_on_failure": true
}
```

#### 步驟 5: 監控進度

```bash
# 查看執行狀態
GET /api/v1/planning/goals/{goal_id}/status

# 回應範例
{
  "goal_id": "goal-123",
  "status": "in_progress",
  "progress": {
    "completed_tasks": 2,
    "total_tasks": 5,
    "percentage": 40
  },
  "current_task": {
    "id": "task-3",
    "name": "撰寫單元測試",
    "assigned_agent": "test-agent",
    "started_at": "2025-12-18T10:30:00Z"
  },
  "timeline": {
    "estimated_completion": "2025-12-20T18:00:00Z",
    "on_schedule": true
  }
}
```

### 進階設定

#### 動態重規劃觸發條件

```yaml
replan_triggers:
  task_failure:
    enabled: true
    max_retries: 2
    replan_after_retries: true
  resource_unavailable:
    enabled: true
    wait_minutes: 30
    replan_if_timeout: true
  external_event:
    enabled: true
    events: ["requirement_change", "deadline_change"]
  progress_delay:
    enabled: true
    threshold_percentage: 20  # 進度落後 20% 時觸發
```

#### 能力匹配策略

```yaml
capability_matching:
  strategy: "best_fit"
  alternatives:
    - "first_fit"
    - "round_robin"
    - "least_loaded"
  weight_factors:
    proficiency: 0.5
    availability: 0.3
    load_balance: 0.2
```

---

## 常見問題

### Q1: 如何選擇適合的場景？

根據您的業務需求：

| 需求 | 建議場景 |
|------|----------|
| 簡化重複性流程 | 場景 1: IT 工單分派 |
| 需要多方觀點分析 | 場景 2: 多 Agent 協作 |
| 定期數據彙整 | 場景 3: 自動化報表 |
| 複雜專案管理 | 場景 4: 自主規劃 |

### Q2: 可以組合多個場景嗎？

可以。IPA Platform 支援場景組合，例如：
- 場景 1 + 場景 3: 工單分派後自動生成週報
- 場景 2 + 場景 4: 協作討論後執行規劃

### Q3: 如何自訂場景模板？

1. 複製現有模板: `backend/templates/scenarios/`
2. 修改配置參數
3. 透過 API 註冊新模板:
   ```bash
   POST /api/v1/templates
   {
     "name": "custom-scenario",
     "based_on": "it_ticket_triage",
     "customizations": {...}
   }
   ```

### Q4: 審批流程可以跳過嗎？

可以在工作流設定中調整：
```yaml
checkpoints:
  enabled: false  # 完全停用
  # 或
  auto_approve:
    conditions:
      - complexity: "simple"
      - risk_score: "< 0.3"
```

### Q5: 如何處理執行失敗？

IPA Platform 提供多層保護：
1. **自動重試**: 可配置重試次數和間隔
2. **回退策略**: 使用快取或備用數據
3. **人工介入**: 透過 Checkpoint 等待處理
4. **通知告警**: Email/Teams 即時通知

---

## 相關文檔

- [快速入門指南](./quick-start.md)
- [工作流建立指南](./creating-workflows.md)
- [監控與告警](./monitoring.md)
- [技術架構](../02-architecture/technical-architecture.md)
- [UAT 驗證計畫](../../claudedocs/uat/UAT-SCENARIO-VALIDATION-PLAN.md)

---

**最後更新**: 2025-12-18
**維護團隊**: IPA Platform Team
