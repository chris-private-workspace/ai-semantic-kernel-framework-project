# Sprint 97 技術決策

## Decision 97-1: HITLController 架構設計

### 決策

採用控制器模式 (Controller Pattern) 實現人機協作：
- HITLController 作為主控制器，協調審批流程
- ApprovalHandler 處理具體審批邏輯
- NotificationService 處理通知發送
- ApprovalStorage 處理狀態持久化

### 理由

1. **單一職責**: 各組件職責清晰分離
2. **可測試**: 各組件可獨立測試
3. **可替換**: 通知服務可輕易替換 (Teams/Email/Slack)
4. **符合 SOLID**: 開放封閉、依賴倒置原則

### 替代方案

- 單一類實現: 簡單但職責過重
- Event-driven: 複雜度高，目前需求不需要

---

## Decision 97-2: ApprovalStatus 狀態定義

### 決策

使用五態狀態機：

| 狀態 | 含義 | 下一可能狀態 |
|------|------|-------------|
| PENDING | 等待審批 | APPROVED, REJECTED, EXPIRED, CANCELLED |
| APPROVED | 已批准 | (終態) |
| REJECTED | 已拒絕 | (終態) |
| EXPIRED | 已過期 | (終態) |
| CANCELLED | 已取消 | (終態) |

### 理由

1. 涵蓋所有可能的審批結局
2. 清晰的狀態轉換路徑
3. 與企業審批流程對齊

---

## Decision 97-3: 審批持久化策略

### 決策

使用 Redis 作為審批狀態存儲：

```python
# Key 格式
approval:{request_id} -> ApprovalRequest JSON
approval_history:{request_id} -> List[ApprovalEvent] JSON

# TTL 設定
pending_ttl = 30 * 60  # 30 分鐘
completed_ttl = 7 * 24 * 60 * 60  # 7 天
```

### 理由

1. **高效**: Redis 讀寫速度快
2. **TTL**: 自動過期清理
3. **已有基礎**: 專案已使用 Redis
4. **簡單**: 不需要額外的資料庫表

### 替代方案

- PostgreSQL: 持久化更強，但審批是短暫狀態
- 內存: 不持久，重啟丟失

---

## Decision 97-4: Teams Webhook 格式

### 決策

使用 Microsoft Teams MessageCard 格式：

```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "summary": "審批請求",
  "themeColor": "FF0000",
  "title": "高風險操作審批請求",
  "sections": [{...}],
  "potentialAction": [{...}]
}
```

### 理由

1. **官方支持**: Microsoft 官方格式
2. **互動性**: 支援按鈕操作
3. **豐富展示**: 支援卡片、表格、圖片

---

## Decision 97-5: LLM QuestionGenerator 設計

### 決策

新增 LLMQuestionGenerator 類，與現有 QuestionGenerator 並存：

- QuestionGenerator: 規則式，零延遲，適合常見場景
- LLMQuestionGenerator: LLM 式，更智能，適合複雜場景

選擇策略：
1. 優先使用規則式生成
2. 缺少範本時 fallback 到 LLM

### Prompt 設計

```python
QUESTION_GENERATION_PROMPT = """
你是一個 IT 服務助手。根據以下資訊，生成適當的澄清問題。

## 意圖類別
{intent_category}

## 缺失欄位
{missing_fields}

## 已知資訊
{collected_info}

## 要求
1. 生成 1-3 個問題
2. 問題要具體、易懂
3. 提供可選答案（如適用）
4. 使用繁體中文

## 輸出格式 (JSON)
{
  "questions": [
    {
      "field": "欄位名稱",
      "question": "問題內容",
      "options": ["選項1", "選項2"]
    }
  ]
}
"""
```

### 理由

1. **漸進式**: 不影響現有功能
2. **智能補充**: 處理規則未覆蓋的場景
3. **效率控制**: 使用 Haiku 模型降低延遲

---

## Decision 97-6: 對話超時與恢復機制

### 決策

實現對話狀態持久化與恢復：

```python
# 對話超時設定
dialog_timeout = 30 * 60  # 30 分鐘無活動則超時
max_turns = 10  # 最大對話輪數

# Redis 存儲
dialog_session:{session_id} -> DialogState JSON
```

恢復機制：
1. 檢查 session_id 是否存在
2. 驗證是否超時
3. 還原 ConversationContextManager 狀態

### 理由

1. **用戶體驗**: 允許用戶中途離開後恢復
2. **資源管理**: 超時自動清理
3. **安全性**: 限制最大輪數防止濫用

---

**決策日期**: 2026-01-15
