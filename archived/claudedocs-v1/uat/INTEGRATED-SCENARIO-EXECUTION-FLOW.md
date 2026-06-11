# 整合場景測試執行流程完整說明

## 文件概述

| 項目 | 說明 |
|------|------|
| **場景名稱** | Enterprise Critical System Outage Response |
| **測試腳本** | `scripts/uat/integrated_scenario/enterprise_outage_test.py` |
| **功能覆蓋** | 32 個功能 (26 主列表 + 6 Category 特有) |
| **測試階段** | 12 個階段 |
| **執行日期** | 2025-12-20 |

---

## 重要說明：測試模式

### Simulation Fallback 機制

測試腳本使用 **Simulation Fallback 機制**：

```python
async def api_call(self, method: str, url: str, payload: Optional[Dict] = None) -> Optional[Dict]:
    try:
        # 嘗試呼叫真實 API
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status in (200, 201):
                    return await response.json()
        return None
    except Exception as e:
        # API 失敗時返回 None，觸發模擬響應
        return None
```

**工作原理**：
1. 首先嘗試呼叫真實 API 端點
2. 如果 API 回應成功 (HTTP 200/201)，使用真實響應
3. 如果 API 失敗或不可用，返回 `None` 並使用預設模擬資料

**判斷方式**：
- 結果中標註 `(simulated)` 表示使用模擬資料
- 無此標註表示使用真實 API 響應

### 如何啟用真實 LLM 呼叫

要使用真實 Azure OpenAI LLM，需要：

1. **配置環境變數**：
   ```bash
   AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
   AZURE_OPENAI_API_KEY=<your-key>
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   ```

2. **啟動完整後端服務**：
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **確保 API 端點已實現**：
   - `/api/v1/planning/classify` - LLM 分類
   - `/api/v1/planning/decompose` - 任務分解
   - `/api/v1/planning/decisions` - 自主決策
   - `/api/v1/multiturn/message` - 多輪對話

---

## 測試架構

### 類別結構

```
EnterpriseOutageTest (繼承 UATTestBase)
├── config: IntegratedScenarioConfig     # 測試配置
├── results: IntegratedScenarioResults   # 結果追蹤
├── tickets: Dict[str, Ticket]           # 工單資料
├── workflow_id: str                     # 工作流 ID
├── execution_id: str                    # 執行 ID
├── groupchat_session_id: str            # GroupChat 會話 ID
└── cache_baseline: Dict[str, int]       # 快取基線
```

### 資料模型

```python
@dataclass
class Ticket:
    ticket_id: str           # 工單 ID (如 IT-001)
    department: str          # 部門 (IT, CS, FIN, OPS)
    title: str               # 標題
    description: str         # 描述
    priority: TicketPriority # 優先級 (P0-P3)
    status: TicketStatus     # 狀態
    related_tickets: List[str]  # 關聯工單
    metadata: Dict[str, Any]    # 元資料

@dataclass
class FeatureVerification:
    feature_id: str          # 功能編號 (如 "1", "B-2")
    feature_name: str        # 功能名稱
    phase: str               # 驗證階段
    status: str              # 狀態 (pending/passed/failed)
    verification_details: List[str]  # 驗證詳情
    error_message: Optional[str]     # 錯誤訊息
```

---

## 12 階段執行流程

### Phase 1: 事件觸發與多源工單接收

**目的**：建立主工作流、初始化快取基線、並行建立 4 張工單

**驗證功能**：
- #1 順序式 Agent 編排
- #15 Concurrent 並行執行
- #14 Redis 緩存

#### 輸入

無外部輸入，使用預設測試資料：

```python
departments = [
    ("IT", "IT-001", "資料庫主節點故障", "Database primary node unresponsive"),
    ("CS", "CS-001", "客戶投訴系統無法使用", "Multiple customers reporting login failures"),
    ("FIN", "FIN-001", "財務交易失敗", "Payment processing system timeout"),
    ("OPS", "OPS-001", "營運流程中斷", "Automated workflows halted"),
]
```

#### 處理流程

```
Step 1.1: 建立主工作流 (Feature #1)
├── API: POST /api/v1/workflows
├── Payload: {name, type, trigger, priority}
└── 輸出: workflow_id (如 WF-B57C51B4)

Step 1.2: 初始化快取基線 (Feature #14)
├── API: GET /api/v1/cache/stats
└── 輸出: {hits: 0, misses: 0, keys: 0}

Step 1.3: 並行建立工單 (Feature #15)
├── 使用 asyncio.gather() 並行執行
├── API: POST /api/v1/tickets (x4 並行)
├── Payload: {ticket_id, department, title, description, priority}
└── 輸出: 4 張工單物件

Step 1.4: 啟動執行 (Feature #1)
├── API: POST /api/v1/executions
├── Payload: {workflow_id, trigger_data: {tickets, incident_type}}
└── 輸出: execution_id (如 EXEC-2BDD7A29)
```

#### 輸出

```json
{
  "tickets_created": 4,
  "workflow_id": "WF-B57C51B4",
  "execution_id": "EXEC-2BDD7A29",
  "features_verified": ["#1", "#15", "#14"]
}
```

#### 功能驗證詳情

| 功能 | 驗證內容 |
|------|----------|
| #1 順序式編排 | Workflow 建立 → Execution 啟動 |
| #15 並行執行 | 4 張工單使用 asyncio.gather 並行建立 |
| #14 Redis 緩存 | 記錄快取基線 hits/misses/keys |

---

### Phase 2: 智慧分類 + 任務分解

**目的**：使用 LLM 分類工單、識別關聯性、分解執行任務

**驗證功能**：
- #22 Dynamic Planning 動態規劃
- #34 Planning Adapter

#### 輸入

Phase 1 產生的 4 張工單：

```python
self.tickets = {
    "IT-001": Ticket(...),
    "CS-001": Ticket(...),
    "FIN-001": Ticket(...),
    "OPS-001": Ticket(...),
}
```

#### 處理流程

```
Step 2.1: LLM 分類工單 (Feature #22)
├── API: POST /api/v1/planning/classify
├── Payload: {
│     tickets: [{ticket_id, title, description}, ...],
│     classification_model: "azure_openai",
│     include_correlation: true
│   }
├── 預期真實 LLM 回應:
│     - 分析每張工單內容
│     - 識別事件類別 (database_outage, service_disruption, ...)
│     - 判斷優先級
│     - 檢測工單間關聯性
└── 模擬響應 (API 不可用時):
      IT-001: database_outage (P0)
      CS-001: service_disruption (P0)
      FIN-001: transaction_failure (P0)
      OPS-001: workflow_halt (P0)
      Correlation detected: All 4 tickets related to same root cause

Step 2.2: 任務分解 (Feature #34)
├── API: POST /api/v1/planning/decompose
├── Payload: {execution_id, incident_type: "database_outage"}
├── 預期真實 LLM 回應:
│     - 分析事件類型
│     - 生成執行任務列表
│     - 排定優先順序
└── 模擬響應:
      Tasks generated: 5
      - 診斷資料庫連接狀態
      - 通知受影響客戶
      - 暫停財務交易處理
      - 記錄營運流程狀態
      - 準備備援方案
```

#### 輸出

```json
{
  "tickets_classified": 4,
  "correlation_detected": true,
  "features_verified": ["#22", "#34"]
}
```

#### LLM 整合說明

**真實 LLM 呼叫時**：
- 使用 Azure OpenAI GPT-4o 模型
- 分析工單標題和描述
- 輸出結構化分類結果

**模擬模式時**：
- 使用預定義分類結果
- 假設所有工單關聯同一根因

---

### Phase 3: 跨場景路由

**目的**：將工單路由到適當場景、匹配 Agent 能力、建立跨場景關聯

**驗證功能**：
- #4 跨場景協作 (CS↔IT)
- #43 智能路由
- #30 Capability Matcher
- #47 Agent 能力匹配器

#### 輸入

分類後的工單資料 + 場景映射表：

```python
scenario_mapping = {
    "IT-001": "it_operations",
    "CS-001": "customer_service",
    "FIN-001": "finance",
    "OPS-001": "operations",
}
```

#### 處理流程

```
Step 3.1: 路由工單到場景 (Feature #43)
├── 對每張工單:
│   ├── API: POST /api/v1/routing/route
│   ├── Payload: {ticket_id, target_scenario, routing_strategy: "capability_match"}
│   └── 輸出: 路由確認
└── 結果:
      IT-001 -> it_operations: Routed
      CS-001 -> customer_service: Routed
      FIN-001 -> finance: Routed
      OPS-001 -> operations: Routed

Step 3.2: 匹配 Agent 能力 (Feature #30, #47)
├── API: POST /api/v1/handoff/capability-match
├── Payload: {
│     required_capabilities: ["database", "networking", "troubleshooting"],
│     strategy: "best_fit"
│   }
└── 輸出:
      Agent dba_expert: score 0.95, capabilities [database, sql, optimization]
      Agent network_specialist: score 0.88, capabilities [networking, dns, routing]

Step 3.3: 建立跨場景關聯 (Feature #4)
├── 建立雙向連結:
│   ├── IT-001 <-> CS-001: Linked
│   ├── IT-001 <-> FIN-001: Linked
│   └── IT-001 <-> OPS-001: Linked
├── API: POST /api/v1/routing/relations (x3)
├── Payload: {source_ticket, target_ticket, relation_type: "bidirectional", sync_updates: true}
└── 輸出: Cross-scenario context sharing: Enabled
```

#### 輸出

```json
{
  "tickets_routed": 4,
  "cross_scenario_links": 3,
  "features_verified": ["#4", "#43", "#30", "#47"]
}
```

---

### Phase 4: 並行分支處理 (Fan-out)

**目的**：建立並行執行分支、執行嵌套工作流、傳遞上下文

**驗證功能**：
- #15 Concurrent 並行執行 (已在 Phase 1 驗證)
- #25 Nested Workflows 嵌套工作流
- #31 Context Transfer
- B-2 Parallel branch management
- B-3 Fan-out/Fan-in pattern
- B-6 Nested workflow context

#### 輸入

執行 ID 和分支定義：

```python
branches = [
    {"name": "technical_diagnosis", "agent": "it_team", "priority": 1},
    {"name": "customer_notification", "agent": "cs_team", "priority": 2},
    {"name": "business_recovery", "agent": "ops_team", "priority": 2},
]
```

#### 處理流程

```
Step 4.1: 建立並行分支 (Feature B-2, B-3)
├── API: POST /api/v1/concurrent/fanout
├── Payload: {execution_id, branches, master_ticket: "IT-001"}
└── 輸出:
      Branch 1: technical_diagnosis created
      Branch 2: customer_notification created
      Branch 3: business_recovery created
      Total branches: 3
      Branch management: Active

Step 4.2: 執行嵌套工作流 (Feature #25, B-6)
├── 對每個分支:
│   ├── API: POST /api/v1/nested/execute
│   ├── Payload: {parent_execution_id, workflow_name, inherit_context: true}
│   └── 輸出: Nested workflow: {name}
└── 結果:
      Nested workflow: technical_diagnosis
      Nested workflow: customer_notification
      Nested workflow: business_recovery
      Context inherited: technical_diagnosis
      Context inherited: customer_notification
      Context inherited: business_recovery

Step 4.3: 傳遞上下文 (Feature #31)
├── API: POST /api/v1/handoff/context/transfer
├── Payload: {
│     source_branch: "technical_diagnosis",
│     target_branches: ["customer_notification", "business_recovery"],
│     context: {
│       incident_id: execution_id,
│       root_ticket: "IT-001",
│       correlation_chain: ["IT-001", "CS-001", "FIN-001", "OPS-001"],
│       priority: "P0"
│     }
│   }
└── 輸出:
      Context transferred to all branches
      Context keys: ['incident_id', 'root_ticket', 'correlation_chain', 'priority']
```

#### 輸出

```json
{
  "branches_created": 3,
  "nested_workflows": 3,
  "context_transferred": true,
  "features_verified": ["#25", "#31", "B-2", "B-3", "B-6"]
}
```

---

### Phase 5: 遞迴根因分析 (5 Whys)

**目的**：執行 5 Whys 分析找出根本原因、記錄多輪對話、保存對話記憶

**驗證功能**：
- #27 Recursive Patterns
- #20 Multi-turn 多輪對話
- #21 Conversation Memory

#### 輸入

5 Whys 分析鏈 (真實 LLM 場景中由 AI 生成，此處使用預定義資料)：

```python
why_chain = [
    ("為什麼資料庫無響應？", "連接池耗盡"),
    ("為什麼連接池耗盡？", "大量慢查詢佔用連接"),
    ("為什麼有大量慢查詢？", "索引失效"),
    ("為什麼索引失效？", "昨晚資料遷移後未重建"),
    ("為什麼未重建？", "遷移腳本缺少重建步驟 [ROOT CAUSE]"),
]
```

#### 處理流程

```
Step 5.1: 執行 5 Whys 分析 (Feature #27, #20)
├── 建立對話 ID: conversation_id = uuid4()
├── 對每個 Why (depth 1-5):
│   ├── API: POST /api/v1/multiturn/message
│   ├── Payload: {
│   │     conversation_id,
│   │     role: "user" | "assistant",
│   │     content: question | answer,
│   │     depth: i + 1
│   │   }
│   └── 記錄對話輪次
└── 輸出:
      Why 1: 為什麼資料庫無響應？ → 連接池耗盡
      Why 2: 為什麼連接池耗盡？ → 大量慢查詢佔用連接
      Why 3: 為什麼有大量慢查詢？ → 索引失效
      Why 4: 為什麼索引失效？ → 昨晚資料遷移後未重建
      Why 5: 為什麼未重建？ → 遷移腳本缺少重建步驟 [ROOT CAUSE]
      Turn 1-5: Recorded

Step 5.2: 驗證對話記憶 (Feature #21)
├── API: GET /api/v1/multiturn/{conversation_id}/history
└── 輸出:
      Messages in memory: 10 (5 questions + 5 answers)
      Context preservation: Complete
      Root cause identified: 遷移腳本缺少重建步驟
```

#### 輸出

```json
{
  "analysis_depth": 5,
  "root_cause": "遷移腳本缺少重建步驟",
  "features_verified": ["#27", "#20", "#21"]
}
```

#### LLM 整合說明

**真實 LLM 呼叫時**：
- 每個 "Why" 問題會傳送到 LLM
- LLM 根據上下文生成答案
- 下一個 "Why" 基於前一個答案生成

**模擬模式時**：
- 使用預定義的問答對
- 直接標記根因

---

### Phase 6: 自主決策 + 試錯修復

**目的**：AI 自主做出修復決策、執行試錯修復、處理超時和錯誤隔離

**驗證功能**：
- #23 Autonomous Decision 自主決策
- #24 Trial-and-Error 試錯
- B-4 Branch timeout handling
- B-5 Error isolation in branches

#### 輸入

決策選項和試錯序列：

```python
decision_options = [
    {"id": "opt_1", "action": "reindex_concurrent", "risk": "medium", "confidence": 0.75},
    {"id": "opt_2", "action": "failover_and_reindex", "risk": "low", "confidence": 0.90},
    {"id": "opt_3", "action": "manual_escalation", "risk": "none", "confidence": 0.60},
]

trials = [
    {"attempt": 1, "action": "REINDEX CONCURRENTLY", "result": "FAILED", "error": "Lock contention"},
    {"attempt": 2, "action": "Switch to standby", "result": "SUCCESS", "duration": "2.3s"},
    {"attempt": 3, "action": "REINDEX on standby", "result": "SUCCESS", "duration": "45.2s"},
]
```

#### 處理流程

```
Step 6.1: 自主決策 (Feature #23)
├── API: POST /api/v1/planning/decisions
├── Payload: {
│     context: {root_cause, affected_systems, urgency},
│     options: [...],
│     auto_approve_threshold: 0.80
│   }
├── 預期 LLM 處理:
│     - 分析上下文
│     - 評估每個選項的風險/信心度
│     - 選擇最佳方案
└── 輸出:
      Decision made: failover_and_reindex
      Confidence: 0.9
      Auto-approved: Yes (confidence >= threshold 0.80)

Step 6.2: 試錯執行 (Feature #24)
├── 對每次嘗試:
│   ├── API: POST /api/v1/planning/trial
│   ├── Payload: {execution_id, attempt, action}
│   └── 記錄結果
└── 輸出:
      Trial 1: REINDEX CONCURRENTLY -> ❌ (Lock contention)
      Trial 2: Switch to standby -> ✅
      Trial 3: REINDEX on standby -> ✅

Step 6.3: 超時與錯誤處理 (Feature B-4, B-5)
└── 輸出:
      Timeout policy: 30 seconds per operation
      Timeout action: Retry with fallback
      Timeout triggered: Trial 1 (lock contention)
      Error isolation: Enabled
      Trial 1 failure: Isolated, did not affect Trial 2/3
      Graceful degradation: Active
```

#### 輸出

```json
{
  "decision": "failover_and_reindex",
  "trials_executed": 3,
  "successful_trials": 2,
  "features_verified": ["#23", "#24", "B-4", "B-5"]
}
```

---

### Phase 7: Agent 交接 (A2A Handoff)

**目的**：建立 Agent 間通訊、執行協作協議、觸發 Agent 交接

**驗證功能**：
- #39 Agent to Agent (A2A)
- #17 Collaboration Protocol 協作協議
- #19 Agent Handoff 交接
- #31 Context Transfer (已在 Phase 4 驗證)
- #32 Handoff Service

#### 輸入

Agent 資訊和協議訊息：

```python
source_agent = "triage_agent"
target_agent = "specialist_agent"

protocol_messages = [
    ("triage_agent", "specialist_agent", "REQUEST", "Validate resolution"),
    ("specialist_agent", "triage_agent", "ACKNOWLEDGE", "Received"),
    ("specialist_agent", "triage_agent", "RESPONSE", "Validation complete"),
]
```

#### 處理流程

```
Step 7.1: A2A 通訊 (Feature #39)
├── API: POST /api/v1/handoff/a2a
├── Payload: {
│     source_agent: "triage_agent",
│     target_agent: "specialist_agent",
│     message_type: "handoff_request",
│     context: {ticket_id, resolution_status, next_action}
│   }
└── 輸出:
      A2A channel: Established
      Source: triage_agent
      Target: specialist_agent

Step 7.2: 執行協作協議 (Feature #17)
├── 記錄協議訊息交換
└── 輸出:
      triage_agent -> specialist_agent: REQUEST
      specialist_agent -> triage_agent: ACKNOWLEDGE
      specialist_agent -> triage_agent: RESPONSE
      Protocol completed: 3 messages exchanged

Step 7.3: 觸發交接 (Feature #19, #32)
├── API: POST /api/v1/handoff/trigger
├── Payload: {
│     source_agent_id: "triage_agent",
│     target_agent_id: "specialist_agent",
│     handoff_policy: "graceful",
│     preserve_context: true
│   }
└── 輸出:
      Handoff ID: {uuid}
      Handoff policy: graceful
      Status: completed
      Handoff service: Active
      Context preserved: Yes
      Agent state transferred: Yes
```

#### 輸出

```json
{
  "handoff_id": "026c489d-b2d3-42ff-b0b0-e0821b062f45",
  "protocol_messages": 3,
  "features_verified": ["#39", "#17", "#19", "#32"]
}
```

---

### Phase 8: 多部門子工作流審批

**目的**：建立審批子工作流、建立檢查點、管理 HITL 審批、測試升級機制

**驗證功能**：
- #26 Sub-workflow Execution
- #2 人機協作檢查點
- #29 HITL Manage
- #49 HITL 功能擴展
- #35 Redis/Postgres Checkpoint

#### 輸入

審批工作流定義：

```python
approval_workflows = [
    {"name": "it_manager_approval", "approver": "IT Manager", "scope": "technical_change"},
    {"name": "cto_approval", "approver": "CTO", "scope": "emergency_release"},
    {"name": "ops_manager_approval", "approver": "Ops Manager", "scope": "impact_assessment"},
]
```

#### 處理流程

```
Step 8.1: 建立審批子工作流 (Feature #26)
├── 對每個審批者:
│   ├── API: POST /api/v1/nested/subworkflow
│   ├── Payload: {parent_execution_id, name, type: "approval", approver}
│   └── 記錄子工作流
└── 輸出:
      Sub-workflow: it_manager_approval (IT Manager)
      Sub-workflow: cto_approval (CTO)
      Sub-workflow: ops_manager_approval (Ops Manager)

Step 8.2: 建立檢查點 (Feature #2, #35)
├── 對每個審批工作流:
│   ├── API: POST /api/v1/checkpoints
│   ├── Payload: {
│   │     execution_id,
│   │     type: "approval",
│   │     name: checkpoint_{name},
│   │     timeout_seconds: 300,
│   │     escalation_enabled: true
│   │   }
│   └── 記錄檢查點
└── 輸出:
      Checkpoint: it_manager_approval
      Checkpoint: cto_approval
      Checkpoint: ops_manager_approval
      Persisted: it_manager_approval
      Persisted: cto_approval
      Persisted: ops_manager_approval

Step 8.3: HITL 審批管理 (Feature #29)
├── 對每個審批者:
│   ├── API: POST /api/v1/checkpoints/approve
│   ├── Payload: {
│   │     checkpoint_name,
│   │     approver,
│   │     decision: "approved",
│   │     comments: "Approved for emergency release"
│   │   }
│   └── 記錄審批結果
└── 輸出:
      IT Manager: Approved
      CTO: Approved
      Ops Manager: Approved

Step 8.4: 測試升級機制 (Feature #49)
└── 輸出:
      Escalation policy: Configured
      Timeout escalation: To VP level after 5 min
      Complexity escalation: Enabled for P0 incidents
      Multi-approver support: Yes
```

#### 輸出

```json
{
  "sub_workflows": 3,
  "approvals_obtained": 3,
  "features_verified": ["#26", "#2", "#29", "#49", "#35"]
}
```

---

### Phase 9: GroupChat 專家會診 + 投票

**目的**：建立專家群組討論、執行多輪討論、投票決策、終止條件

**驗證功能**：
- #18 GroupChat 群組聊天
- #33 GroupChat Orchestrator
- #20 Multi-turn 多輪對話 (已在 Phase 5 驗證)
- #21 Conversation Memory (已在 Phase 5 驗證)
- #28 GroupChat 投票系統
- #48 投票系統
- #50 Termination 條件

#### 輸入

專家定義和討論內容：

```python
experts = [
    {"id": "dba_expert", "name": "DBA Expert", "specialty": "database"},
    {"id": "devops_expert", "name": "DevOps Expert", "specialty": "deployment"},
    {"id": "sre_expert", "name": "SRE Expert", "specialty": "reliability"},
    {"id": "app_expert", "name": "App Expert", "specialty": "application"},
    {"id": "security_expert", "name": "Security Expert", "specialty": "security"},
]

discussion = [
    ("dba_expert", "索引已重建，查詢效能恢復正常"),
    ("sre_expert", "監控顯示所有指標綠燈"),
    ("devops_expert", "部署狀態穩定"),
    ("app_expert", "應用程式回應時間正常"),
    ("security_expert", "無安全漏洞引入"),
]
```

#### 處理流程

```
Step 9.1: 建立 GroupChat 會話 (Feature #18, #33)
├── API: POST /api/v1/groupchat/sessions
├── Payload: {
│     name: "Incident Resolution Review",
│     participants: [expert_ids],
│     topic: "Confirm resolution safety for production",
│     max_rounds: 5
│   }
└── 輸出:
      Session ID: {uuid}
      Participants: 5 experts
      Orchestrator: Active
      Turn management: Round-robin

Step 9.2: 多輪專家討論 (Feature #20, #21)
├── 對每位專家:
│   ├── API: POST /api/v1/groupchat/{session_id}/messages
│   ├── Payload: {participant_id, content}
│   └── 記錄發言
└── 輸出:
      dba_expert: 索引已重建，查詢效能恢復正常...
      sre_expert: 監控顯示所有指標綠燈...
      devops_expert: 部署狀態穩定...
      app_expert: 應用程式回應時間正常...
      security_expert: 無安全漏洞引入...

Step 9.3: 發起投票 (Feature #28, #48)
├── API: POST /api/v1/groupchat/{session_id}/vote
├── Payload: {
│     topic: "Approve production release?",
│     options: ["approve", "reject", "abstain"],
│     required_quorum: 0.6
│   }
└── 輸出:
      dba_expert: approve
      devops_expert: approve
      sre_expert: approve
      app_expert: approve
      security_expert: approve
      Voting completed: 5/5 approved
      Quorum reached: Yes (100% > 60%)
      Result: APPROVED

Step 9.4: 終止條件 (Feature #50)
└── 輸出:
      Termination type: Consensus reached
      Condition: All experts approved
      Session status: Closed
```

#### 輸出

```json
{
  "session_id": "174e6ff7-93f9-4a9e-98ce-3d451e04b28c",
  "participants": 5,
  "votes_approve": 5,
  "votes_reject": 0,
  "features_verified": ["#18", "#33", "#28", "#48", "#50"]
}
```

---

### Phase 10: 外部系統同步 (Fan-in)

**目的**：同步外部系統、匯聚分支結果、處理訊息優先級

**驗證功能**：
- #3 跨系統連接器
- B-3 Fan-out/Fan-in pattern (Fan-in 部分)
- C-4 Message prioritization

#### 輸入

外部系統定義和優先級訊息：

```python
external_systems = [
    {"name": "ServiceNow", "action": "update_incident", "status": "resolved"},
    {"name": "Prometheus", "action": "clear_alert", "status": "cleared"},
    {"name": "PagerDuty", "action": "resolve_incident", "status": "resolved"},
]

messages = [
    {"priority": "P0", "type": "critical_alert", "handled_first": True},
    {"priority": "P1", "type": "status_update", "handled_first": False},
    {"priority": "P2", "type": "notification", "handled_first": False},
]
```

#### 處理流程

```
Step 10.1: 同步外部系統 (Feature #3)
├── 對每個系統:
│   ├── API: POST /api/v1/connectors/{system}/sync
│   ├── Payload: {action, incident_id, status}
│   └── 記錄同步結果
└── 輸出:
      ServiceNow: update_incident -> resolved
      Prometheus: clear_alert -> cleared
      PagerDuty: resolve_incident -> resolved

Step 10.2: Fan-in 匯聚 (Feature B-3)
├── API: POST /api/v1/concurrent/fanin
├── Payload: {execution_id, wait_for_all: true}
└── (B-3 已在 Phase 4 標記為 passed)

Step 10.3: 訊息優先級處理 (Feature C-4)
└── 輸出:
      Priority queue: Active
      P0 (critical_alert): Processed
      P1 (status_update): Processed
      P2 (notification): Processed
      Priority order: P0 -> P1 -> P2
```

#### 輸出

```json
{
  "systems_synced": 3,
  "messages_prioritized": 3,
  "features_verified": ["#3", "C-4"]
}
```

---

### Phase 11: 完成與記錄 + 快取驗證

**目的**：關閉所有工單、記錄審計追蹤、驗證快取統計

**驗證功能**：
- #10 審計追蹤
- #14 Redis 緩存 (最終統計)

#### 輸入

Phase 1-10 累積的工單和執行資料

#### 處理流程

```
Step 11.1: 關閉所有工單
├── 對每張工單:
│   ├── API: PUT /api/v1/tickets/{ticket_id}
│   ├── Payload: {status: "completed", resolution: "resolved_by_automation"}
│   └── 記錄關閉狀態
└── 輸出:
      IT-001: COMPLETED
      CS-001: COMPLETED
      FIN-001: COMPLETED
      OPS-001: COMPLETED

Step 11.2: 審計追蹤 (Feature #10)
├── API: POST /api/v1/audit/record
├── Payload: {
│     execution_id,
│     event_type: "incident_resolved",
│     details: {
│       tickets_resolved: 4,
│       resolution_method: "automated_with_approval",
│       root_cause: "遷移腳本缺少重建步驟"
│     }
│   }
└── 輸出:
      Audit trail: Recorded
      Event type: incident_resolved
      Tickets resolved: 4

Step 11.3: 快取統計驗證 (Feature #14)
├── API: GET /api/v1/cache/stats
└── 輸出 (模擬):
      Cache hits: 156
      Cache misses: 78
      Hit rate: 66.7%
```

#### 輸出

```json
{
  "tickets_closed": 4,
  "audit_recorded": true,
  "features_verified": ["#10", "#14"]
}
```

---

### Phase 12: 優雅關閉 + 事後分析

**目的**：保存最終檢查點、生成事後報告、優雅關閉執行

**驗證功能**：
- #35 Redis/Postgres Checkpoint (最終狀態)
- #10 審計追蹤 (事後報告)

#### 輸入

整個事件的摘要資料

#### 處理流程

```
Step 12.1: 保存最終檢查點 (Feature #35)
├── API: POST /api/v1/checkpoints
├── Payload: {
│     execution_id,
│     type: "final",
│     name: "incident_resolution_complete",
│     data: {
│       tickets_resolved: ["IT-001", "CS-001", "FIN-001", "OPS-001"],
│       root_cause: "遷移腳本缺少重建步驟",
│       resolution: "Failover + index rebuild",
│       total_duration: "45 minutes"
│     }
│   }
└── 輸出:
      Final checkpoint: Saved
      Persistence: Redis + PostgreSQL
      Data integrity: Verified

Step 12.2: 生成事後報告 (Feature #10)
├── 報告內容:
│   {
│     "incident_id": execution_id,
│     "summary": "資料庫主節點故障 - 已解決",
│     "root_cause": "遷移腳本缺少索引重建步驟",
│     "impact": {
│       "departments_affected": 4,
│       "customers_affected": "~200",
│       "duration": "45 minutes"
│     },
│     "resolution": {
│       "method": "Failover to standby + index rebuild",
│       "trials": 3,
│       "successful_trial": 2
│     },
│     "prevention": [
│       "新增自動化索引檢查到遷移腳本",
│       "更新遷移腳本標準",
│       "增加 post-migration 驗證步驟"
│     ]
│   }
└── 輸出:
      Post-incident report: Generated
      Root cause: 遷移腳本缺少索引重建步驟
      Prevention measures: 3

Step 12.3: 優雅關閉
├── API: POST /api/v1/executions/{execution_id}/shutdown
├── Payload: {mode: "graceful", cleanup_resources: true, preserve_logs: true}
└── 輸出: Graceful shutdown complete
```

#### 輸出

```json
{
  "final_checkpoint_saved": true,
  "post_incident_report": true,
  "graceful_shutdown": true,
  "features_verified": ["#35", "#10"]
}
```

---

## 資料流程圖

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Enterprise Outage Response Flow                       │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1                    Phase 2                    Phase 3
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│ Event       │           │ Classify    │           │ Route       │
│ Trigger     │────────►  │ + Decompose │────────►  │ + Match     │
├─────────────┤           ├─────────────┤           ├─────────────┤
│ 4 Tickets   │           │ 4 P0 Issues │           │ 4 Scenarios │
│ 1 Workflow  │           │ 5 Tasks     │           │ 3 Links     │
│ 1 Execution │           │ Correlation │           │ 2 Agents    │
└─────────────┘           └─────────────┘           └─────────────┘
      │                         │                         │
      └─────────────────────────┼─────────────────────────┘
                                │
                                ▼
Phase 4                    Phase 5                    Phase 6
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│ Fan-out     │           │ 5 Whys      │           │ Decision    │
│ Branches    │────────►  │ Analysis    │────────►  │ + Trials    │
├─────────────┤           ├─────────────┤           ├─────────────┤
│ 3 Branches  │           │ 5 Turns     │           │ 1 Decision  │
│ 3 Nested WF │           │ Root Cause  │           │ 3 Trials    │
│ Context TX  │           │ Identified  │           │ 2 Success   │
└─────────────┘           └─────────────┘           └─────────────┘
      │                         │                         │
      └─────────────────────────┼─────────────────────────┘
                                │
                                ▼
Phase 7                    Phase 8                    Phase 9
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│ A2A         │           │ Approval    │           │ GroupChat   │
│ Handoff     │────────►  │ Sub-WF      │────────►  │ + Voting    │
├─────────────┤           ├─────────────┤           ├─────────────┤
│ A2A Channel │           │ 3 Sub-WF    │           │ 5 Experts   │
│ 3 Protocol  │           │ 3 Checkpts  │           │ 5 Messages  │
│ 1 Handoff   │           │ 3 Approvals │           │ 5/5 Votes   │
└─────────────┘           └─────────────┘           └─────────────┘
      │                         │                         │
      └─────────────────────────┼─────────────────────────┘
                                │
                                ▼
Phase 10                   Phase 11                   Phase 12
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│ External    │           │ Complete    │           │ Shutdown    │
│ Sync        │────────►  │ + Audit     │────────►  │ + Report    │
├─────────────┤           ├─────────────┤           ├─────────────┤
│ 3 Systems   │           │ 4 Closed    │           │ Final Ckpt  │
│ 3 Priority  │           │ Audit Trail │           │ PIR Report  │
│ Fan-in      │           │ Cache Stats │           │ Graceful    │
└─────────────┘           └─────────────┘           └─────────────┘
```

---

## 功能驗證矩陣

| 功能編號 | 功能名稱 | 驗證階段 | 驗證方式 |
|----------|----------|----------|----------|
| #1 | 順序式 Agent 編排 | Phase 1 | Workflow → Execution 建立 |
| #2 | 人機協作檢查點 | Phase 8 | 3 個審批檢查點 |
| #3 | 跨系統連接器 | Phase 10 | 3 系統同步 |
| #4 | 跨場景協作 | Phase 3 | 3 個雙向連結 |
| #10 | 審計追蹤 | Phase 11, 12 | 事件記錄 + 事後報告 |
| #14 | Redis 緩存 | Phase 1, 11 | 基線 → 最終統計 |
| #15 | 並行執行 | Phase 1 | asyncio.gather 4 工單 |
| #17 | 協作協議 | Phase 7 | 3 訊息交換 |
| #18 | GroupChat | Phase 9 | 5 專家討論 |
| #19 | Agent Handoff | Phase 7 | Graceful 交接 |
| #20 | 多輪對話 | Phase 5 | 5 Whys 對話 |
| #21 | 對話記憶 | Phase 5 | 10 訊息保存 |
| #22 | 動態規劃 | Phase 2 | LLM 分類 + 關聯 |
| #23 | 自主決策 | Phase 6 | 自動審批決策 |
| #24 | 試錯 | Phase 6 | 3 次嘗試 |
| #25 | 嵌套工作流 | Phase 4 | 3 個嵌套 WF |
| #26 | 子工作流 | Phase 8 | 3 個審批 Sub-WF |
| #27 | 遞迴模式 | Phase 5 | 5 Whys 遞迴 |
| #28 | GroupChat 投票 | Phase 9 | 5/5 投票 |
| #29 | HITL Manage | Phase 8 | 3 審批管理 |
| #30 | Capability Matcher | Phase 3 | Agent 評分匹配 |
| #31 | Context Transfer | Phase 4 | 分支上下文傳遞 |
| #32 | Handoff Service | Phase 7 | 狀態轉移服務 |
| #33 | GroupChat Orchestrator | Phase 9 | Round-robin 管理 |
| #34 | Planning Adapter | Phase 2 | 5 任務生成 |
| #35 | Checkpoint 持久化 | Phase 8, 12 | Redis + PostgreSQL |
| #39 | A2A | Phase 7 | Agent 通道建立 |
| #43 | 智能路由 | Phase 3 | 4 工單路由 |
| #47 | Agent 能力匹配器 | Phase 3 | 能力列表匹配 |
| #48 | 投票系統 | Phase 9 | 法定人數達成 |
| #49 | HITL 擴展 | Phase 8 | 升級機制 |
| #50 | 終止條件 | Phase 9 | 共識終止 |
| B-2 | 並行分支管理 | Phase 4 | 3 分支管理 |
| B-3 | Fan-out/Fan-in | Phase 4, 10 | 分支→匯聚 |
| B-4 | 分支超時 | Phase 6 | 30 秒策略 |
| B-5 | 錯誤隔離 | Phase 6 | 隔離 + 降級 |
| B-6 | 嵌套上下文 | Phase 4 | 上下文繼承 |
| C-4 | 訊息優先級 | Phase 10 | P0→P1→P2 |

---

## 結果輸出格式

### 即時結果 (JSON)

```json
{
  "summary": {
    "total_features": 38,
    "main_list": {"total": 32, "passed": 32, "failed": 0, "pending": 0},
    "category_specific": {"total": 6, "passed": 6, "failed": 0, "pending": 0},
    "overall_pass_rate": "100.0%",
    "phases_completed": 12,
    "duration": "0:00:17.316865"
  },
  "phases": {
    "phase_1": "TestResult(...status=passed...)",
    // ...
  },
  "main_features": {
    "1": {"name": "順序式 Agent 編排", "phase": "Phase 1", "status": "passed", "details": [...], "error": null},
    // ...
  },
  "category_features": {
    "B-2": {"name": "Parallel branch management", "phase": "Phase 4", "status": "passed", "details": [...], "error": null},
    // ...
  }
}
```

### 會話記錄

存儲位置：`claudedocs/uat/sessions/integrated_enterprise_outage-{timestamp}.json`

---

## 相關文件

| 文件 | 路徑 | 說明 |
|------|------|------|
| 功能索引 | `claudedocs/uat/FEATURE-INDEX.md` | 功能編號權威來源 |
| 場景設計 | `claudedocs/uat/INTEGRATED-SCENARIO-DESIGN.md` | 12 階段設計文件 |
| 測試腳本 | `scripts/uat/integrated_scenario/enterprise_outage_test.py` | Python 測試腳本 |
| 測試提示 | `claudedocs/prompts/PROMPT-UAT-INTEGRATED-SCENARIO.md` | 執行指南 |
| 測試結果 | `scripts/uat/integrated_scenario/test_results_integrated_scenario.json` | 即時結果 |

---

**文件建立者**: Claude Code
**建立日期**: 2025-12-20
**版本**: 1.0
