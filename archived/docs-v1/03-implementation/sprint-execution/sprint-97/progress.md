# Sprint 97: HITLController + ApprovalHandler

## 概述

Sprint 97 專注於建立 **HITLController** 人機協作控制器和 **ApprovalHandler** 審批處理器，以及完整版的 **LLM QuestionGenerator**。

## 目標

1. 實現 HITLController
2. 實現 ApprovalHandler (基礎版)
3. 實現審批 Webhook (Teams 簡化版)
4. 實現 LLM QuestionGenerator
5. 多輪對話狀態管理增強

## Story Points: 30 點

---

## Story 進度

### Story 97-1: 實現 HITLController (4h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/hitl/__init__.py`
- `backend/src/integrations/orchestration/hitl/controller.py`

**完成項目**:
- [x] 創建 hitl 目錄
- [x] 創建 `__init__.py`
- [x] 定義 `ApprovalStatus` enum (PENDING, APPROVED, REJECTED, EXPIRED, CANCELLED)
- [x] 定義 `ApprovalType` enum (NONE, SINGLE, MULTI)
- [x] 定義 `ApprovalEvent` dataclass (歷史事件)
- [x] 定義 `ApprovalRequest` dataclass (審批請求)
- [x] 實現 `HITLController` 類
- [x] 實現 `request_approval()` 方法
- [x] 實現 `check_status()` 方法
- [x] 實現 `process_approval()` 方法
- [x] 實現 `cancel_approval()` 方法
- [x] 實現 `list_pending_requests()` 方法
- [x] 實現超時處理 (自動過期)
- [x] 實現回調機制 (on_approved, on_rejected, on_expired)
- [x] 實現 `InMemoryApprovalStorage` (測試用)
- [x] 實現 `MockNotificationService` (測試用)

---

### Story 97-2: 實現 ApprovalHandler (4h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/hitl/approval_handler.py`

**完成項目**:
- [x] 實現 `RedisApprovalStorage` 類
  - [x] save_session() 方法
  - [x] get_session() 方法
  - [x] delete_session() 方法
  - [x] list_pending() 方法
  - [x] TTL 管理 (pending: 30min, completed: 7days)
- [x] 實現 `ApprovalResult` dataclass
- [x] 實現 `ApprovalHandler` 類
- [x] 實現 `approve()` 方法
- [x] 實現 `reject()` 方法
- [x] 實現 `get_request_status()` 方法
- [x] 實現 `get_history()` 方法
- [x] 實現 `list_pending_by_approver()` 方法
- [x] 審批狀態持久化 (Redis)
- [x] 審批歷史記錄
- [x] 審計日誌 (audit_logger callback)

---

### Story 97-3: 實現審批 Webhook (4h, P1)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/hitl/notification.py`

**完成項目**:
- [x] 實現 `TeamsMessageCard` dataclass
- [x] 實現 `TeamsCardBuilder` 類
  - [x] with_title(), with_summary() 方法
  - [x] with_theme_color(), with_risk_level_color() 方法
  - [x] add_section(), add_fact(), add_text() 方法
  - [x] add_approve_button(), add_reject_button() 方法
  - [x] add_open_url_button() 方法
  - [x] build() 方法
- [x] 實現 `TeamsNotificationService` 類
  - [x] send_approval_request() 方法
  - [x] send_approval_result() 方法
  - [x] _build_approval_request_card() 方法
  - [x] _build_result_card() 方法
- [x] 實現 `NotificationResult` dataclass
- [x] 實現 `CompositeNotificationService` (多通道)
- [x] 實現 `EmailNotificationService` (placeholder)

**Teams Webhook 格式**:
```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "summary": "審批請求",
  "themeColor": "FF0000",
  "title": "🔴 HIGH 風險操作審批請求",
  "sections": [{
    "activityTitle": "請求 ID: abc-123...",
    "activitySubtitle": "提交者: user@example.com",
    "facts": [
      { "name": "意圖類別", "value": "incident" },
      { "name": "子意圖", "value": "etl_failure" },
      { "name": "風險等級", "value": "high" }
    ]
  }],
  "potentialAction": [
    { "@type": "HttpPOST", "name": "✅ 批准", "target": "..." },
    { "@type": "HttpPOST", "name": "❌ 拒絕", "target": "..." }
  ]
}
```

---

### Story 97-4: 實現 LLM QuestionGenerator (5h, P0)

**狀態**: ✅ 完成

**交付物**:
- 更新 `backend/src/integrations/orchestration/guided_dialog/generator.py`

**完成項目**:
- [x] 定義 `LLMClient` Protocol
- [x] 定義 `LLMQuestionConfig` dataclass
- [x] 實現 `LLMQuestionGenerator` 類
  - [x] generate() 方法 (async with timeout)
  - [x] _call_llm() 方法
  - [x] _build_prompt() 方法
  - [x] _parse_response() 方法 (JSON parsing)
  - [x] _fallback_to_templates() 方法
  - [x] get_metrics() 方法
- [x] 實現 `HybridQuestionGenerator` 類
  - [x] 優先使用範本，LLM 補充
  - [x] 支援 prefer_llm 模式
- [x] 實現 `MockLLMClient` (測試用)
- [x] 設計問題生成 Prompt (QUESTION_GENERATION_PROMPT)
- [x] 確保延遲 < 2000ms (timeout 控制)
- [x] 工廠函數: create_llm_question_generator, create_hybrid_question_generator

**Prompt 設計**:
```python
QUESTION_GENERATION_PROMPT = """
你是一個 IT 服務助手。根據以下資訊，生成適當的澄清問題。

## 意圖類別
{intent_category}

## 子意圖
{sub_intent}

## 缺失欄位
{missing_fields}

## 已知資訊
{collected_info}

## 要求
1. 生成 1-3 個問題
2. 問題要具體、易懂
3. 提供可選答案（如適用）
4. 使用繁體中文
5. 問題要針對缺失的欄位

## 輸出格式 (嚴格 JSON)
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

---

### Story 97-5: 多輪對話狀態管理增強 (3h, P0)

**狀態**: ✅ 完成

**交付物**:
- 更新 `backend/src/integrations/orchestration/guided_dialog/context_manager.py`

**完成項目**:
- [x] 定義 `DialogSessionConfig` dataclass
- [x] 定義 `DialogSessionStorage` Protocol
- [x] 實現 `RedisDialogSessionStorage` 類
  - [x] save_session() 方法
  - [x] get_session() 方法
  - [x] delete_session() 方法
  - [x] touch_session() 方法 (延長 TTL)
  - [x] session_exists() 方法
- [x] 實現 `InMemoryDialogSessionStorage` (測試用)
- [x] 實現 `PersistentConversationContextManager` 類
  - [x] create_session() 方法
  - [x] resume_session() 方法 (恢復對話)
  - [x] update_with_user_response_async() 方法
  - [x] end_session() 方法
  - [x] get_session_info() 方法
  - [x] 對話超時處理 (is_session_expired)
  - [x] 最大輪數限制 (is_max_turns_reached)
- [x] 工廠函數: create_persistent_context_manager, create_redis_dialog_storage

**對話配置**:
- timeout_minutes: 30 分鐘
- max_turns: 10 輪
- persist_history: true
- auto_expire: true

---

## 品質檢查

### 代碼品質
- [x] 類型提示完整
- [x] Docstrings 完整
- [x] 遵循專案代碼風格
- [x] 模組導出正確 (__all__)

### 測試
- [x] 單元測試實現 (`test_hitl.py`)
- [x] 測試覆蓋關鍵路徑
  - [x] TestApprovalEnums
  - [x] TestApprovalRequest
  - [x] TestHITLController
  - [x] TestApprovalHandler
  - [x] TestTeamsCardBuilder
  - [x] TestInMemoryApprovalStorage
  - [x] TestFactoryFunctions

---

## 技術決策

詳見 `decisions.md`

---

## 文件結構

```
backend/src/integrations/orchestration/hitl/
├── __init__.py          # 模組導出
├── controller.py        # HITLController 核心類
├── approval_handler.py  # ApprovalHandler + Redis 存儲
└── notification.py      # Teams Webhook 通知

backend/src/integrations/orchestration/guided_dialog/
├── generator.py         # QuestionGenerator + LLMQuestionGenerator + HybridQuestionGenerator
└── context_manager.py   # ConversationContextManager + PersistentConversationContextManager

backend/tests/unit/orchestration/
└── test_hitl.py         # 單元測試
```

---

## 完成日期

- **開始日期**: 2026-01-15
- **完成日期**: 2026-01-15
- **Story Points**: 30 / 30 完成 (100%)
