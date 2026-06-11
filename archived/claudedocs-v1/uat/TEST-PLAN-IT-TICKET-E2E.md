# IT 工單分類到派遣 E2E 測試計劃

> **文件版本**: 1.0
> **建立日期**: 2025-12-18
> **測試環境**: Azure OpenAI gpt-5.2 (2024-12-01-preview)
> **狀態**: ✅ 已執行 (2025-12-18 17:11)
> **測試結果**: [TEST-RESULT-IT-TICKET-E2E.md](./TEST-RESULT-IT-TICKET-E2E.md)

---

## 1. 測試目標

驗證 IPA Platform 完整 IT 工單處理工作流程，從工單接收到派遣完成的端到端整合，確保所有元件能夠與真實 Azure OpenAI LLM 正確協作。

### 1.1 主要驗證項目

| 項目 | 說明 |
|------|------|
| **LLM 整合** | AgentExecutorAdapter 與 Azure OpenAI gpt-5.2 正確整合 |
| **智慧分類** | Agent 能正確分類工單優先級 (P1-P4) 和類別 |
| **路由決策** | ScenarioRouter 能正確路由到對應團隊 |
| **人機協作** | Checkpoint 審批流程正確運作 |
| **Agent 派遣** | Handoff 機制能正確傳遞上下文 |
| **多專家協作** | GroupChat 能協調多 Agent 討論 |
| **狀態追蹤** | Execution 狀態機正確轉換 |

---

## 2. 測試架構

### 2.1 工作流程階段

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IT 工單完整生命週期                               │
└─────────────────────────────────────────────────────────────────────┘

階段 1: 工單接收與建立
    ├─ Workflow API 觸發執行
    └─ Execution 狀態建立 (PENDING → RUNNING)

階段 2: 智慧分類 (LLM Agent)
    ├─ AgentExecutorAdapter 呼叫 Azure OpenAI
    ├─ 自動分類: 類別、優先級、建議團隊
    └─ 上下文分析 (使用者角色、歷史工單)

階段 3: 路由決策
    ├─ ScenarioRouter 跨場景路由
    ├─ CapabilityMatcher 能力匹配
    └─ Routing Relations 建立 (追蹤鏈)

階段 4: 人機協作審批 (High Priority)
    ├─ Checkpoint 建立
    ├─ 通知審批人
    ├─ 審批/拒絕處理
    └─ 執行恢復或終止

階段 5: Agent 派遣 (Handoff)
    ├─ HandoffTrigger 觸發
    ├─ 上下文傳遞
    └─ 目標 Agent 接收工單

階段 6: 工單處理
    ├─ GroupChat 多專家協作 (複雜問題)
    ├─ 診斷資訊收集
    └─ 解決方案生成

階段 7: 完成與記錄
    ├─ Execution 狀態 → COMPLETED
    ├─ LLM 統計 (tokens, cost)
    └─ 審計日誌更新
```

### 2.2 元件依賴關係

```
                    ┌─────────────────┐
                    │   API Layer     │
                    │  (FastAPI)      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼───────┐ ┌───▼────┐ ┌───────▼────────┐
    │  Workflow API   │ │Checkpoint│ │   Handoff API  │
    │  /workflows/    │ │   API   │ │   /handoff/    │
    └─────────┬───────┘ └───┬────┘ └───────┬────────┘
              │             │              │
    ┌─────────▼─────────────▼──────────────▼────────┐
    │              Domain Layer                      │
    │  WorkflowService | CheckpointService | Router │
    └─────────────────────┬─────────────────────────┘
                          │
    ┌─────────────────────▼─────────────────────────┐
    │           Integration Layer                    │
    │  AgentExecutorAdapter | GroupChatAdapter      │
    │  HandoffAdapter | CapabilityMatcher           │
    └─────────────────────┬─────────────────────────┘
                          │
    ┌─────────────────────▼─────────────────────────┐
    │           Microsoft Agent Framework            │
    │  (Official API: agent_framework package)       │
    └─────────────────────┬─────────────────────────┘
                          │
    ┌─────────────────────▼─────────────────────────┐
    │              Azure OpenAI                      │
    │  Model: gpt-5.2 | API: 2024-12-01-preview     │
    └───────────────────────────────────────────────┘
```

---

## 3. 測試案例設計

### 3.1 測試矩陣 (15 個測試案例)

| # | 測試案例 | 階段 | 使用的 API/Adapter | 驗證重點 | 預期結果 |
|---|----------|------|-------------------|----------|----------|
| 1 | 建立 IT 工單工作流程定義 | 1 | `WorkflowService` | Workflow 定義正確建立 | workflow_id 回傳 |
| 2 | 觸發工作流程執行 | 1 | `ExecutionService` | Execution 狀態轉換 | status: RUNNING |
| 3 | P1 緊急工單分類 | 2 | `AgentExecutorAdapter` + LLM | 正確識別為 P1 | priority: P1 |
| 4 | P2 高優先工單分類 | 2 | `AgentExecutorAdapter` + LLM | 正確識別為 P2 | priority: P2 |
| 5 | P3 一般工單分類 | 2 | `AgentExecutorAdapter` + LLM | 正確識別為 P3 | priority: P3 |
| 6 | 含上下文的 VIP 分類 | 2 | `AgentExecutorAdapter` + Context | VIP 使用者優先級提升 | priority: P1/P2 |
| 7 | 場景路由 (IT → Network) | 3 | `ScenarioRouter` | 正確路由到網路團隊 | team: network-team |
| 8 | 能力匹配找到專家 | 3 | `CapabilityMatcher` | 找到具備技能的 Agent | matched_agents > 0 |
| 9 | P1 工單建立檢查點 | 4 | `CheckpointService` | Checkpoint 正確建立 | checkpoint_id 回傳 |
| 10 | 審批人核准流程 | 4 | `CheckpointService.approve` | 執行正確恢復 | status: APPROVED |
| 11 | 審批人拒絕流程 | 4 | `CheckpointService.reject` | 執行正確終止 | status: REJECTED |
| 12 | Handoff 觸發派遣 | 5 | `HandoffBuilderAdapter` | 上下文完整傳遞 | handoff_id 回傳 |
| 13 | 派遣完成確認 | 5 | `HandoffService` | 狀態正確更新 | status: COMPLETED |
| 14 | 多專家 GroupChat 協作 | 6 | `GroupChatBuilderAdapter` | 3 位專家協作討論 | responses: 3 |
| 15 | 完整流程 E2E | 全部 | 全部元件 | 端到端完整驗證 | 全部階段通過 |

### 3.2 測試資料設計

#### 3.2.1 測試工單定義

```python
test_tickets = [
    {
        "id": "TKT-E2E-001",
        "title": "整層網路斷線 - 財務部",
        "description": "財務部全體同事無法連網，影響月結作業，約 50 人受影響",
        "reporter": {
            "name": "陳財務長",
            "email": "cfo@company.com",
            "department": "Finance",
            "role": "CFO",
            "vip": True
        },
        "created_at": "2025-12-18T09:00:00Z",
        "expected": {
            "priority": "P1",
            "category": "Network",
            "team": "network-team",
            "needs_approval": True,
            "sla_hours": 1
        }
    },
    {
        "id": "TKT-E2E-002",
        "title": "VPN 連線緩慢",
        "description": "從家裡連 VPN 速度很慢，約 5 分鐘才能登入，已經持續三天",
        "reporter": {
            "name": "王工程師",
            "email": "engineer.wang@company.com",
            "department": "Engineering",
            "role": "Engineer",
            "vip": False
        },
        "created_at": "2025-12-18T10:30:00Z",
        "expected": {
            "priority": "P2",
            "category": "Network",
            "team": "network-team",
            "needs_approval": False,
            "sla_hours": 4
        }
    },
    {
        "id": "TKT-E2E-003",
        "title": "電腦開不了機",
        "description": "按電源鍵沒反應，30 分鐘後有重要客戶會議",
        "reporter": {
            "name": "李經理",
            "email": "manager.lee@company.com",
            "department": "Sales",
            "role": "Manager",
            "vip": False
        },
        "created_at": "2025-12-18T08:30:00Z",
        "expected": {
            "priority": "P1",
            "category": "Hardware",
            "team": "endpoint-team",
            "needs_approval": True,
            "sla_hours": 1
        }
    },
    {
        "id": "TKT-E2E-004",
        "title": "申請安裝 VS Code",
        "description": "需要安裝 VS Code 進行開發工作，目前電腦沒有",
        "reporter": {
            "name": "張實習生",
            "email": "intern.zhang@company.com",
            "department": "Engineering",
            "role": "Intern",
            "vip": False
        },
        "created_at": "2025-12-18T14:00:00Z",
        "expected": {
            "priority": "P3",
            "category": "Software",
            "team": "helpdesk",
            "needs_approval": False,
            "sla_hours": 24
        }
    }
]
```

#### 3.2.2 測試 Agent 定義

```python
test_agents = {
    "triage_agent": {
        "name": "IT Triage Agent",
        "instructions": """You are an IT support triage specialist.
Analyze the ticket and determine:
1. Priority (P1=Critical, P2=High, P3=Medium, P4=Low)
2. Category (Network, Hardware, Software, Account, Other)
3. Suggested Team (network-team, endpoint-team, helpdesk, security-team)
4. Needs Approval (true for P1, false otherwise)

Consider:
- VIP users should have priority elevated
- Business impact affects priority
- Time sensitivity is critical

Respond in JSON format.""",
        "capabilities": ["ticket_classification", "priority_assignment"]
    },
    "network_expert": {
        "name": "Network Expert Agent",
        "instructions": "You are a network infrastructure expert. Diagnose network issues and suggest solutions.",
        "capabilities": ["network_diagnosis", "vpn_troubleshooting", "connectivity_analysis"]
    },
    "endpoint_expert": {
        "name": "Endpoint Expert Agent",
        "instructions": "You are an endpoint/hardware expert. Diagnose hardware and device issues.",
        "capabilities": ["hardware_diagnosis", "device_troubleshooting", "power_issues"]
    },
    "helpdesk_agent": {
        "name": "Helpdesk Agent",
        "instructions": "You are a helpdesk support agent. Handle general IT requests and software installations.",
        "capabilities": ["software_installation", "account_management", "general_support"]
    }
}
```

#### 3.2.3 測試工作流程定義

```python
it_triage_workflow = {
    "name": "IT Ticket Triage Workflow",
    "description": "Complete IT ticket triage from intake to dispatch",
    "nodes": [
        {
            "id": "intake",
            "type": "agent",
            "agent": "triage_agent",
            "next": "route_decision"
        },
        {
            "id": "route_decision",
            "type": "condition",
            "conditions": [
                {"if": "priority == 'P1'", "then": "approval_checkpoint"},
                {"if": "priority == 'P2'", "then": "capability_match"},
                {"else": "direct_dispatch"}
            ]
        },
        {
            "id": "approval_checkpoint",
            "type": "checkpoint",
            "approvers": ["it_manager"],
            "timeout_minutes": 30,
            "next_on_approve": "capability_match",
            "next_on_reject": "escalate"
        },
        {
            "id": "capability_match",
            "type": "capability_match",
            "next": "handoff"
        },
        {
            "id": "handoff",
            "type": "handoff",
            "next": "complete"
        },
        {
            "id": "direct_dispatch",
            "type": "direct_assign",
            "next": "complete"
        },
        {
            "id": "escalate",
            "type": "escalate",
            "next": "complete"
        },
        {
            "id": "complete",
            "type": "end"
        }
    ]
}
```

---

## 4. 測試環境配置

### 4.1 Azure OpenAI 配置

```bash
AZURE_OPENAI_ENDPOINT=https://chris-mj48nnoz-eastus2.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=<configured>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.2
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

### 4.2 模型特性

| 項目 | 值 |
|------|-----|
| Model | gpt-5.2-2025-12-11 |
| Max Tokens Parameter | `max_completion_tokens` (非 `max_tokens`) |
| Temperature | 不支援 (reasoning model) |
| Response Format | 支援 JSON mode |

### 4.3 Backend 服務

```bash
# 確保服務運行
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Health Check
curl http://localhost:8000/health
```

---

## 5. 測試執行計劃

### 5.1 執行順序

```
Phase 1: 基礎元件測試 (Test 1-2)
    └─ 驗證 Workflow 和 Execution 基礎功能

Phase 2: LLM 分類測試 (Test 3-6)
    └─ 驗證 Agent 分類準確度

Phase 3: 路由測試 (Test 7-8)
    └─ 驗證路由和能力匹配

Phase 4: 人機協作測試 (Test 9-11)
    └─ 驗證 Checkpoint 審批流程

Phase 5: 派遣測試 (Test 12-13)
    └─ 驗證 Handoff 機制

Phase 6: 協作測試 (Test 14)
    └─ 驗證 GroupChat 多專家協作

Phase 7: 完整 E2E 測試 (Test 15)
    └─ 端到端完整流程驗證
```

### 5.2 預估資源消耗

| 項目 | 預估值 |
|------|--------|
| 測試案例數 | 15 個 |
| LLM 呼叫次數 | ~25-30 次 |
| 預估 Tokens | 8,000-12,000 |
| 預估成本 | ~$0.10-0.15 USD |
| 執行時間 | ~3-5 分鐘 |

---

## 6. 驗收標準

### 6.1 功能驗收

| 驗證項目 | 成功標準 | 權重 |
|----------|----------|------|
| LLM 整合 | Azure OpenAI 正確回應 | 必要 |
| 分類準確度 | 4/4 工單優先級正確 (100%) | 必要 |
| 路由正確性 | 團隊分配與預期一致 | 必要 |
| 審批流程 | P1 工單觸發 Checkpoint | 必要 |
| 審批回應 | Approve/Reject 正確處理 | 必要 |
| 派遣完整性 | Handoff 包含完整上下文 | 必要 |
| 狀態追蹤 | 所有狀態轉換正確記錄 | 必要 |
| 協作功能 | GroupChat 產出綜合建議 | 重要 |
| 執行完成 | 最終狀態為 COMPLETED | 必要 |

### 6.2 效能驗收

| 指標 | 目標值 |
|------|--------|
| 單次 LLM 回應時間 | < 10 秒 |
| 完整流程執行時間 | < 60 秒 |
| API 回應時間 | < 500ms |
| 錯誤率 | < 5% |

### 6.3 通過門檻

- **必要項目**: 100% 通過
- **重要項目**: ≥ 80% 通過
- **整體通過率**: ≥ 90% (14/15)

---

## 7. 風險評估

### 7.1 已知風險

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Azure OpenAI API 限流 | 測試中斷 | 加入重試機制和延遲 |
| LLM 回應不穩定 | 分類結果不一致 | 多次驗證取多數 |
| 網路延遲 | 超時錯誤 | 增加 timeout 設定 |
| Token 超限 | API 錯誤 | 控制輸入長度 |

### 7.2 回退計劃

如果真實 LLM 測試失敗：
1. 檢查 Azure OpenAI 連線狀態
2. 驗證 API Key 和 Endpoint
3. 降級為 Mock 模式完成功能驗證
4. 記錄問題並另行排程重測

---

## 8. 測試輸出

### 8.1 輸出檔案

| 檔案 | 位置 | 內容 |
|------|------|------|
| 測試結果 JSON | `claudedocs/uat/sessions/it_ticket_e2e_YYYYMMDD_HHMMSS.json` | 完整測試結果 |
| 測試報告 MD | `claudedocs/uat/TEST-RESULT-IT-TICKET-E2E.md` | 人類可讀報告 |
| 執行日誌 | Console output | 即時執行狀態 |

### 8.2 結果結構

```json
{
  "test_plan": "IT Ticket E2E Workflow",
  "executed_at": "2025-12-18T...",
  "environment": {
    "azure_model": "gpt-5.2",
    "api_version": "2024-12-01-preview"
  },
  "summary": {
    "total_tests": 15,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "pass_rate": "0%"
  },
  "metrics": {
    "total_duration_ms": 0,
    "total_llm_calls": 0,
    "total_tokens": 0,
    "total_cost": 0.0
  },
  "results": [
    {
      "test_id": 1,
      "test_name": "...",
      "phase": "...",
      "status": "PASS|FAIL|SKIP",
      "duration_ms": 0,
      "llm_tokens": 0,
      "details": {}
    }
  ]
}
```

---

## 9. 附錄

### 9.1 相關文件

- `claudedocs/uat/sessions/e2e_llm_integration_*.json` - 基礎 LLM 測試結果
- `backend/src/integrations/agent_framework/CLAUDE.md` - Adapter 規範
- `backend/src/domain/CLAUDE.md` - Domain 服務說明

### 9.2 測試腳本位置

```
scripts/uat/
├── e2e_llm_integration.py      # 基礎 LLM 整合測試 (已完成)
├── it_ticket_e2e_workflow.py   # IT 工單 E2E 測試 (待建立)
└── run_all_scenarios.py        # UAT 場景測試
```

---

**文件狀態**: ✅ 已執行
**執行時間**: 2025-12-18 17:11:38
**測試結果**: 11/15 通過 (73.3%)
**詳細報告**: [TEST-RESULT-IT-TICKET-E2E.md](./TEST-RESULT-IT-TICKET-E2E.md)
