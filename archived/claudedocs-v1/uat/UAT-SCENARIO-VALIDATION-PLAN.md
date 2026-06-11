# UAT Scenario Validation Plan - IPA Platform
# 場景化功能驗證計劃

> **專案**: IPA - Intelligent Process Automation Platform
> **版本**: v0.2.0
> **計劃建立日期**: 2025-12-18
> **計劃狀態**: 進行中

---

## 一、計劃概述

### 1.1 目的

透過 4 個核心業務場景，系統性驗證 IPA Platform 的 50+ 功能模組是否：
1. 能夠獨立正常運作
2. 能夠相互連接協作
3. 能夠滿足實際業務需求

### 1.2 驗證範圍

```
┌────────────────────────────────────────────────────────────────┐
│  Layer 4: 業務場景層 (Business Scenarios) - 本計劃核心         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 場景 1   │ │ 場景 2   │ │ 場景 3   │ │ 場景 4   │          │
│  │ IT 工單  │ │ 多Agent  │ │ 報表生成 │ │ 自主規劃 │          │
│  │ 智能分派 │ │ 協作分析 │ │ 自動化   │ │ 複雜任務 │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
├────────────────────────────────────────────────────────────────┤
│  Layer 3: 編排模式層 (Orchestration Patterns)                   │
│  Sequential | Parallel | GroupChat | Nested | Handoff | Planning│
├────────────────────────────────────────────────────────────────┤
│  Layer 2: 核心能力層 (Core Capabilities)                        │
│  Checkpoint | Memory | Routing | Speaker | Capability | Voting  │
├────────────────────────────────────────────────────────────────┤
│  Layer 1: 基礎設施層 (Infrastructure)                           │
│  Agent | Workflow | Execution | Connector | Trigger | Template  │
└────────────────────────────────────────────────────────────────┘
```

---

## 二、4 個核心驗證場景

### 場景 1: IT 工單智能分派 (IT Ticket Triage)

| 項目 | 內容 |
|------|------|
| **場景 ID** | SCENARIO-001 |
| **場景名稱** | IT 工單智能分派 |
| **業務描述** | 當用戶提交 IT 支援工單時，系統自動分析問題類型，分派給適當的處理 Agent，必要時升級給人工審批 |
| **模板文件** | `backend/templates/scenarios/it_ticket_triage.yaml` |
| **驗證腳本** | `scripts/uat/scenario_001_it_triage.py` |

**涉及功能 (16 項)**:
- Layer 1: Agent 管理, Workflow 定義, Trigger (Webhook), Template
- Layer 2: Checkpoint, Routing, Capability Matcher, Audit, Notification
- Layer 3: Sequential, Handoff, Planning

**測試案例**:
| TC-ID | 案例名稱 | 輸入 | 預期輸出 |
|-------|----------|------|----------|
| TC-001-01 | 簡單工單直接分派 | P4 密碼重置請求 | 直接分派到 IT 服務台 |
| TC-001-02 | 中等工單智能路由 | P3 軟體安裝問題 | 路由到應用支援團隊 |
| TC-001-03 | 複雜工單人工審批 | P1 網路中斷 | 觸發 Checkpoint 人工審批 |
| TC-001-04 | 升級工單交接 | 多次未解決工單 | Handoff 到專家 Agent |

---

### 場景 2: 多 Agent 協作分析 (Multi-Agent Collaboration)

| 項目 | 內容 |
|------|------|
| **場景 ID** | SCENARIO-002 |
| **場景名稱** | 多 Agent 協作分析 |
| **業務描述** | 對複雜的業務問題進行多角度分析，多個專家 Agent 協作討論，最後綜合產出報告 |
| **模板文件** | `backend/templates/scenarios/multi_agent_collaboration.yaml` |
| **驗證腳本** | `scripts/uat/scenario_002_collaboration.py` |

**涉及功能 (14 項)**:
- Layer 1: Agent 管理, Template, DevTools
- Layer 2: Memory, Speaker 選擇, Voting, Termination, Audit
- Layer 3: GroupChat, Multi-turn, Parallel

**測試案例**:
| TC-ID | 案例名稱 | 輸入 | 預期輸出 |
|-------|----------|------|----------|
| TC-002-01 | 3 Agent 基本討論 | 簡單分析任務 | 完成 3 輪討論並產出結論 |
| TC-002-02 | 輪流發言模式 | Round-robin 設定 | 按順序輪流發言 |
| TC-002-03 | 專長發言模式 | Expertise 設定 | 根據問題領域選擇發言者 |
| TC-002-04 | 投票達成共識 | 需要決策的問題 | 投票並記錄結果 |
| TC-002-05 | 對話記憶持久化 | 長對話 | Memory 正確保存歷史 |

---

### 場景 3: 自動化報表生成 (Automated Report Generation)

| 項目 | 內容 |
|------|------|
| **場景 ID** | SCENARIO-003 |
| **場景名稱** | 自動化報表生成 |
| **業務描述** | 定期從多個數據源收集信息，並行處理後生成綜合報表 |
| **模板文件** | `backend/templates/scenarios/automated_reporting.yaml` |
| **驗證腳本** | `scripts/uat/scenario_003_reporting.py` |

**涉及功能 (12 項)**:
- Layer 1: Connector, Trigger, Notification, Template, Dashboard
- Layer 2: Cache, Audit
- Layer 3: Parallel, Fork-Join, Sequential

**測試案例**:
| TC-ID | 案例名稱 | 輸入 | 預期輸出 |
|-------|----------|------|----------|
| TC-003-01 | 單數據源報表 | 單一數據庫查詢 | 生成簡單報表 |
| TC-003-02 | 多數據源並行 | 3 個數據源 | Fork-Join 並行收集 |
| TC-003-03 | 緩存命中測試 | 重複查詢 | LLM Cache 命中 |
| TC-003-04 | 定時觸發測試 | Cron 表達式 | 定時執行報表生成 |
| TC-003-05 | 報表通知測試 | 完成報表 | 發送通知 |

---

### 場景 4: 複雜任務自主規劃 (Autonomous Task Planning)

| 項目 | 內容 |
|------|------|
| **場景 ID** | SCENARIO-004 |
| **場景名稱** | 複雜任務自主規劃 |
| **業務描述** | 用戶提出高層次目標，系統自動分解為子任務，動態分配資源，並在執行過程中自我調整 |
| **模板文件** | `backend/templates/scenarios/autonomous_planning.yaml` |
| **驗證腳本** | `scripts/uat/scenario_004_planning.py` |

**涉及功能 (15 項)**:
- Layer 1: Agent 管理, Workflow 定義, Template
- Layer 2: Capability Matcher, Checkpoint, Memory
- Layer 3: Planning (TaskDecomposer), Nested Workflow, Trial-and-Error, Handoff, Sequential

**測試案例**:
| TC-ID | 案例名稱 | 輸入 | 預期輸出 |
|-------|----------|------|----------|
| TC-004-01 | 基本任務分解 | 簡單目標 | 分解為 3+ 子任務 |
| TC-004-02 | 嵌套工作流執行 | 包含子流程的任務 | 正確執行嵌套流程 |
| TC-004-03 | 關鍵節點審批 | 重要決策點 | 觸發 Checkpoint |
| TC-004-04 | 失敗重試測試 | 可能失敗的任務 | Trial-and-Error 重試 |
| TC-004-05 | 動態調整測試 | 執行中變更 | 重新規劃任務 |

---

## 三、驗證階段規劃

### 階段 1: 單元功能驗證 (Layer 1-2)

| 項目 | 內容 |
|------|------|
| **目標** | 驗證基礎設施和核心能力正常運作 |
| **預估時間** | 1-2 週 |
| **負責人** | AI Assistant |
| **狀態** | 待開始 |

**驗證清單**:
```yaml
Layer 1 (基礎設施):
  - [ ] Agent CRUD 操作
  - [ ] Workflow 定義和執行
  - [ ] Trigger (Webhook) 觸發
  - [ ] Template 實例化
  - [ ] Connector 連接測試
  - [ ] Dashboard 數據顯示
  - [ ] Notification 發送

Layer 2 (核心能力):
  - [ ] Checkpoint 創建和審批
  - [ ] Memory 讀寫
  - [ ] Routing 條件判斷
  - [ ] Speaker 選擇器
  - [ ] Capability Matcher
  - [ ] Voting 投票
  - [ ] Termination 條件
  - [ ] Cache 命中率
  - [ ] Audit 日誌記錄
```

---

### 階段 2: 編排模式驗證 (Layer 3)

| 項目 | 內容 |
|------|------|
| **目標** | 驗證各種編排模式正常運作 |
| **預估時間** | 2-3 週 |
| **負責人** | AI Assistant |
| **狀態** | 待開始 |

**驗證清單**:
```yaml
Sequential 順序執行:
  - [ ] A → B → C 順序執行
  - [ ] 中間失敗回滾

Parallel 並行執行:
  - [ ] Fork-Join (ALL mode)
  - [ ] Fork-Join (ANY mode)
  - [ ] 死鎖檢測

GroupChat 群組聊天:
  - [ ] 多 Agent 對話
  - [ ] Speaker 輪流選擇
  - [ ] Speaker 專長選擇
  - [ ] Voting 投票
  - [ ] Termination 條件

Handoff 智能交接:
  - [ ] 立即交接
  - [ ] 優雅交接
  - [ ] 條件觸發交接

Nested 嵌套工作流:
  - [ ] 子工作流執行
  - [ ] 上下文傳播
  - [ ] 遞歸深度限制

Planning 動態規劃:
  - [ ] 任務分解
  - [ ] 動態調整
  - [ ] Trial-and-Error
```

---

### 階段 3: 端到端場景驗證 (Layer 4)

| 項目 | 內容 |
|------|------|
| **目標** | 驗證完整業務場景 |
| **預估時間** | 2-3 週 |
| **負責人** | AI Assistant |
| **狀態** | 待開始 |

**驗證清單**:
```yaml
場景 1 - IT 工單智能分派:
  - [ ] TC-001-01: 簡單工單直接分派
  - [ ] TC-001-02: 中等工單智能路由
  - [ ] TC-001-03: 複雜工單人工審批
  - [ ] TC-001-04: 升級工單交接

場景 2 - 多 Agent 協作分析:
  - [ ] TC-002-01: 3 Agent 基本討論
  - [ ] TC-002-02: 輪流發言模式
  - [ ] TC-002-03: 專長發言模式
  - [ ] TC-002-04: 投票達成共識
  - [ ] TC-002-05: 對話記憶持久化

場景 3 - 自動化報表生成:
  - [ ] TC-003-01: 單數據源報表
  - [ ] TC-003-02: 多數據源並行
  - [ ] TC-003-03: 緩存命中測試
  - [ ] TC-003-04: 定時觸發測試
  - [ ] TC-003-05: 報表通知測試

場景 4 - 複雜任務自主規劃:
  - [ ] TC-004-01: 基本任務分解
  - [ ] TC-004-02: 嵌套工作流執行
  - [ ] TC-004-03: 關鍵節點審批
  - [ ] TC-004-04: 失敗重試測試
  - [ ] TC-004-05: 動態調整測試
```

---

## 四、功能覆蓋矩陣

下表顯示每個場景覆蓋的功能模組：

| 功能 | 場景 1 | 場景 2 | 場景 3 | 場景 4 | 覆蓋數 |
|------|:------:|:------:|:------:|:------:|:------:|
| **Layer 1** |||||
| Agent 管理 | ✅ | ✅ | | ✅ | 3 |
| Workflow 定義 | ✅ | | | ✅ | 2 |
| Trigger | ✅ | | ✅ | | 2 |
| Template | ✅ | ✅ | ✅ | ✅ | 4 |
| Connector | | | ✅ | | 1 |
| Dashboard | | | ✅ | | 1 |
| DevTools | | ✅ | | | 1 |
| Notification | ✅ | | ✅ | | 2 |
| **Layer 2** |||||
| Checkpoint | ✅ | | | ✅ | 2 |
| Memory | | ✅ | | ✅ | 2 |
| Routing | ✅ | | | | 1 |
| Speaker 選擇 | | ✅ | | | 1 |
| Capability Matcher | ✅ | | | ✅ | 2 |
| Voting | | ✅ | | | 1 |
| Termination | | ✅ | | | 1 |
| Cache | | | ✅ | | 1 |
| Audit | ✅ | ✅ | ✅ | | 3 |
| **Layer 3** |||||
| Sequential | ✅ | | ✅ | ✅ | 3 |
| Parallel | | ✅ | ✅ | | 2 |
| Fork-Join | | | ✅ | | 1 |
| GroupChat | | ✅ | | | 1 |
| Multi-turn | | ✅ | | | 1 |
| Handoff | ✅ | | | ✅ | 2 |
| Nested | | | | ✅ | 1 |
| Planning | ✅ | | | ✅ | 2 |
| Trial-and-Error | | | | ✅ | 1 |

**統計**:
- 場景 1 覆蓋: 10 項功能
- 場景 2 覆蓋: 10 項功能
- 場景 3 覆蓋: 8 項功能
- 場景 4 覆蓋: 11 項功能
- **總覆蓋**: 25 項獨立功能 (某些功能被多場景覆蓋)

---

## 五、文件清單

### 場景模板文件
```
backend/templates/scenarios/
├── it_ticket_triage.yaml           # 場景 1: IT 工單智能分派
├── multi_agent_collaboration.yaml  # 場景 2: 多 Agent 協作分析
├── automated_reporting.yaml        # 場景 3: 自動化報表生成
└── autonomous_planning.yaml        # 場景 4: 複雜任務自主規劃
```

### UAT 驗證腳本
```
scripts/uat/
├── __init__.py
├── base.py                         # 基礎測試類
├── scenario_001_it_triage.py       # 場景 1 驗證腳本
├── scenario_002_collaboration.py   # 場景 2 驗證腳本
├── scenario_003_reporting.py       # 場景 3 驗證腳本
├── scenario_004_planning.py        # 場景 4 驗證腳本
└── run_all_scenarios.py            # 執行所有場景測試
```

### 文檔文件
```
claudedocs/uat/
├── UAT-MASTER-LOG.md               # 主追蹤記錄 (已存在)
├── UAT-SCENARIO-VALIDATION-PLAN.md # 本計劃文件
├── checklists/                     # 測試清單 (已存在)
├── sessions/                       # 測試會話記錄 (已存在)
├── issues/                         # 問題記錄 (已存在)
└── fixes/                          # 修復記錄 (已存在)

docs/
├── 02-architecture/
│   └── technical-architecture.md   # 更新功能分層圖
└── 04-user-guide/
    └── scenario-user-guide.md      # 場景使用指南
```

---

## 六、執行進度追蹤

### 整體進度

| 階段 | 目標 | 狀態 | 完成度 |
|------|------|------|--------|
| 文件準備 | 創建計劃和模板文件 | ✅ 完成 | 100% |
| 驗證腳本 | 創建 UAT 驗證腳本 | ✅ 完成 | 100% |
| 階段 1 | Layer 1-2 單元驗證 | ⏳ 待開始 | 0% |
| 階段 2 | Layer 3 編排模式驗證 | ⏳ 待開始 | 0% |
| 階段 3 | Layer 4 場景驗證 | ⏳ 待開始 | 0% |

### 當前任務

| 任務 | 狀態 | 負責人 | 完成日期 |
|------|------|--------|----------|
| 創建 UAT 場景驗證計劃 | ✅ 完成 | AI Assistant | 2025-12-18 |
| 創建場景 1 模板 | ✅ 完成 | AI Assistant | 2025-12-18 |
| 創建場景 2 模板 | ✅ 完成 | AI Assistant | 2025-12-18 |
| 創建場景 3 模板 | ✅ 完成 | AI Assistant | 2025-12-18 |
| 創建場景 4 模板 | ✅ 完成 | AI Assistant | 2025-12-18 |
| 創建 UAT 驗證腳本 | ✅ 完成 | AI Assistant | 2025-12-18 |
| 更新技術架構文檔 | ⏳ 待開始 | AI Assistant | - |
| 創建場景使用指南 | ⏳ 待開始 | AI Assistant | - |

### 已創建文件

**場景模板 (4 個)**:
- ✅ `backend/templates/scenarios/it_ticket_triage.yaml`
- ✅ `backend/templates/scenarios/multi_agent_collaboration.yaml`
- ✅ `backend/templates/scenarios/automated_reporting.yaml`
- ✅ `backend/templates/scenarios/autonomous_planning.yaml`

**驗證腳本 (6 個)**:
- ✅ `scripts/uat/__init__.py`
- ✅ `scripts/uat/base.py`
- ✅ `scripts/uat/scenario_001_it_triage.py`
- ✅ `scripts/uat/scenario_002_collaboration.py`
- ✅ `scripts/uat/scenario_003_reporting.py`
- ✅ `scripts/uat/scenario_004_planning.py`
- ✅ `scripts/uat/run_all_scenarios.py`

---

## 七、如何執行 UAT 測試

### 執行所有場景測試
```bash
# 確保後端服務已啟動
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 執行所有場景測試
python -m scripts.uat.run_all_scenarios

# 執行並保存報告
python -m scripts.uat.run_all_scenarios --save-report
```

### 執行單一場景測試
```bash
# 場景 1: IT 工單智能分派
python -m scripts.uat.scenario_001_it_triage

# 場景 2: 多 Agent 協作分析
python -m scripts.uat.scenario_002_collaboration

# 場景 3: 自動化報表生成
python -m scripts.uat.scenario_003_reporting

# 場景 4: 複雜任務自主規劃
python -m scripts.uat.scenario_004_planning
```

### 指定測試參數
```bash
# 指定 API URL
python -m scripts.uat.run_all_scenarios --base-url http://api.example.com:8000

# 指定特定場景
python -m scripts.uat.run_all_scenarios --scenario 1 --scenario 2

# JSON 格式輸出
python -m scripts.uat.run_all_scenarios --json
```

---

## 八、版本歷史

| 版本 | 日期 | 變更內容 |
|------|------|----------|
| v1.0.0 | 2025-12-18 | 初始建立場景化驗證計劃 |
| v1.1.0 | 2025-12-18 | 完成 4 個場景模板和 7 個驗證腳本 |

---

**維護者**: AI Assistant
**最後更新**: 2025-12-18
