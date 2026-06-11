# 工作流創建教程

本教程將詳細介紹如何創建和配置 IPA Platform 工作流。

---

## 目錄

1. [工作流基礎](#工作流基礎)
2. [節點類型](#節點類型)
3. [觸發方式](#觸發方式)
4. [條件分支](#條件分支)
5. [變數與參數](#變數與參數)
6. [錯誤處理](#錯誤處理)
7. [最佳實踐](#最佳實踐)

---

## 工作流基礎

### 什麼是工作流？

工作流是一系列按特定順序執行的自動化步驟，用於完成業務流程。

### 工作流組成

```
┌─────────────────────────────────────────────────────────┐
│                      工作流 (Workflow)                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   [開始] ─→ [節點1] ─→ [節點2] ─→ [條件] ─→ [結束]     │
│                                      │                  │
│                                      └─→ [節點3] ─→ ─┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 創建新工作流

1. 導航到 **工作流** 頁面
2. 點擊 **+ 新增工作流**
3. 填寫基本資訊：

```yaml
名稱: IT 票據自動處理
描述: 自動分類和分配 IT 支援票據
標籤: [IT, 自動化, 票據]
觸發方式: Webhook
```

---

## 節點類型

IPA Platform 提供多種節點類型：

### 1. 控制節點

| 節點 | 圖示 | 用途 |
|------|------|------|
| **開始節點** | ⚪ | 工作流入口點 |
| **結束節點** | ⬛ | 工作流結束點 |
| **條件節點** | 🔀 | 條件分支判斷 |
| **並行節點** | ⚡ | 並行執行多個分支 |
| **合併節點** | 🔗 | 合併並行分支 |

### 2. 動作節點

| 節點 | 用途 | 範例 |
|------|------|------|
| **HTTP 請求** | 呼叫外部 API | 呼叫 ServiceNow API |
| **數據轉換** | 處理和轉換數據 | JSON 轉換、欄位映射 |
| **日誌記錄** | 記錄執行資訊 | 偵錯訊息、審計日誌 |
| **延遲等待** | 暫停執行 | 等待 5 分鐘後繼續 |
| **變數設定** | 設定/更新變數 | 保存中間結果 |

### 3. AI Agent 節點

| 節點 | 用途 | 範例 |
|------|------|------|
| **LLM 呼叫** | 呼叫大型語言模型 | GPT-4 文本分析 |
| **Agent 執行** | 執行預配置 Agent | 客服 Agent、分析 Agent |
| **提示模板** | 使用提示模板 | 票據分類提示 |

### 4. 整合節點

| 節點 | 整合服務 | 用途 |
|------|----------|------|
| **ServiceNow** | ServiceNow | 票據管理 |
| **Dynamics 365** | Microsoft CRM | 客戶關係管理 |
| **Teams** | Microsoft Teams | 通知、審批 |
| **n8n** | n8n Workflow | 外部工作流觸發 |

### 5. 檢查點節點

| 節點 | 用途 |
|------|------|
| **人工審批** | 需要人工確認才能繼續 |
| **條件審批** | 根據條件決定是否需要審批 |

---

## 觸發方式

### 手動觸發

最簡單的觸發方式，適合測試和臨時執行。

```yaml
trigger:
  type: manual
```

### 排程觸發

使用 Cron 表達式定時執行：

```yaml
trigger:
  type: scheduled
  cron: "0 9 * * 1-5"  # 每週一至週五早上 9:00
  timezone: "Asia/Taipei"
```

**常用 Cron 表達式**:

| 表達式 | 說明 |
|--------|------|
| `0 * * * *` | 每小時整點 |
| `0 9 * * *` | 每天早上 9:00 |
| `0 9 * * 1` | 每週一早上 9:00 |
| `0 0 1 * *` | 每月 1 號午夜 |

### Webhook 觸發

透過 HTTP 請求觸發：

```yaml
trigger:
  type: webhook
  path: /webhooks/it-ticket
  method: POST
  authentication: jwt
```

**觸發範例**:
```bash
curl -X POST https://api.ipa-platform.com/webhooks/it-ticket \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "INC001234", "priority": "high"}'
```

### 事件觸發

監聽系統事件：

```yaml
trigger:
  type: event
  source: servicenow
  event_type: ticket.created
  filters:
    category: IT
    priority: [high, critical]
```

---

## 條件分支

### 簡單條件

```yaml
condition:
  name: 檢查優先級
  expression: "{{ input.priority == 'high' }}"
  branches:
    - name: 高優先級
      next: urgent_handler
    - name: 一般優先級
      next: normal_handler
```

### 多條件判斷

```yaml
condition:
  name: 票據分類
  type: switch
  expression: "{{ input.category }}"
  cases:
    - value: "hardware"
      next: hardware_team
    - value: "software"
      next: software_team
    - value: "network"
      next: network_team
  default: general_support
```

### 複合條件

```yaml
condition:
  name: VIP 客戶高優先級
  expression: |
    {{ input.priority == 'high' and input.customer_tier == 'VIP' }}
  branches:
    - name: 符合
      next: vip_express_lane
    - name: 不符合
      next: standard_queue
```

---

## 變數與參數

### 輸入參數

定義工作流接受的參數：

```yaml
inputs:
  - name: ticket_id
    type: string
    required: true
    description: 票據 ID
  - name: priority
    type: enum
    values: [low, medium, high, critical]
    default: medium
  - name: metadata
    type: object
    required: false
```

### 工作流變數

在節點間傳遞數據：

```yaml
# 設定變數
set_variable:
  name: analysis_result
  value: "{{ nodes.llm_analysis.output.classification }}"

# 使用變數
http_request:
  url: "https://api.servicenow.com/tickets"
  body:
    classification: "{{ variables.analysis_result }}"
```

### 內建變數

| 變數 | 說明 |
|------|------|
| `{{ workflow.id }}` | 工作流 ID |
| `{{ workflow.name }}` | 工作流名稱 |
| `{{ execution.id }}` | 當前執行 ID |
| `{{ execution.started_at }}` | 執行開始時間 |
| `{{ input.* }}` | 輸入參數 |
| `{{ nodes.*.output }}` | 節點輸出 |
| `{{ variables.* }}` | 工作流變數 |

---

## 錯誤處理

### 重試策略

```yaml
node:
  name: 呼叫外部 API
  type: http_request
  retry:
    max_attempts: 3
    delay_seconds: 5
    backoff_multiplier: 2  # 指數退避
    retryable_errors:
      - timeout
      - 5xx
```

### 錯誤處理節點

```yaml
node:
  name: 處理失敗
  type: error_handler
  on_error:
    - log_error
    - notify_admin
    - set_status_failed
```

### 全域錯誤處理

```yaml
workflow:
  error_handling:
    on_failure:
      - notify_team
      - create_incident
    on_timeout:
      - send_alert
      - cancel_execution
```

---

## 最佳實踐

### 1. 命名規範

```yaml
# ✅ 好的命名
workflow_name: IT-Ticket-Auto-Classification
node_name: validate-input-parameters

# ❌ 不好的命名
workflow_name: workflow1
node_name: node_a
```

### 2. 模組化設計

將複雜工作流拆分為子工作流：

```
主工作流
├── 子工作流: 數據驗證
├── 子工作流: AI 分析
└── 子工作流: 結果處理
```

### 3. 錯誤處理

- 每個外部呼叫都應有重試策略
- 設置合理的超時時間
- 記錄足夠的錯誤資訊

### 4. 效能優化

- 使用並行節點處理獨立任務
- 避免不必要的 API 呼叫
- 合理設置緩存

### 5. 安全考慮

- 不要在工作流中硬編碼敏感資訊
- 使用安全的變數存儲
- 限制 Webhook 的訪問權限

---

## 範例工作流

### IT 票據自動分類

```yaml
name: IT-Ticket-Auto-Classification
description: 使用 AI 自動分類 IT 支援票據

trigger:
  type: webhook
  path: /webhooks/it-ticket

inputs:
  - name: ticket_id
    type: string
    required: true
  - name: title
    type: string
    required: true
  - name: description
    type: string
    required: true

nodes:
  - id: start
    type: start

  - id: validate_input
    type: data_transform
    config:
      validate:
        - field: title
          min_length: 5
        - field: description
          min_length: 10

  - id: ai_classification
    type: agent
    config:
      agent_id: ticket-classifier
      input:
        title: "{{ input.title }}"
        description: "{{ input.description }}"

  - id: update_ticket
    type: http_request
    config:
      url: "{{ secrets.servicenow_url }}/api/tickets/{{ input.ticket_id }}"
      method: PATCH
      body:
        category: "{{ nodes.ai_classification.output.category }}"
        priority: "{{ nodes.ai_classification.output.priority }}"
        assigned_team: "{{ nodes.ai_classification.output.team }}"

  - id: notify_team
    type: teams_notification
    config:
      channel: "{{ nodes.ai_classification.output.team }}-tickets"
      message: |
        新票據已分配:
        - ID: {{ input.ticket_id }}
        - 類別: {{ nodes.ai_classification.output.category }}
        - 優先級: {{ nodes.ai_classification.output.priority }}

  - id: end
    type: end

edges:
  - from: start
    to: validate_input
  - from: validate_input
    to: ai_classification
  - from: ai_classification
    to: update_ticket
  - from: update_ticket
    to: notify_team
  - from: notify_team
    to: end
```

---

## 下一步

- [執行工作流](executing-workflows.md) - 了解執行和監控
- [監控與告警](monitoring.md) - 設置監控和通知
- [API 文檔](/api/openapi.yaml) - API 參考

---

*最後更新: 2025-11-26*
