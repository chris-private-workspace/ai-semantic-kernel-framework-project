# F6. Agent 市場

**分類**: 開發者體驗與生態系統  
**優先級**: P1 (應該擁有 - 加速採用)  
**開發時間**: 2 週  
**複雜度**: ⭐⭐⭐⭐ (高)  
**依賴項**: F1 (順序式編排), JSON Schema Validator, Code Sandbox (可選), Azure Blob Storage  
**風險等級**: 中等 (程式碼質量、安全漏洞、授權問題)

---

## 📑 導航

- [← 功能概覽](../prd-appendix-a-features-overview.md)
- [← F5: 基於學習的協作](./feature-05-learning.md)
- **F6: Agent 市場** ← 您在這裡
- [→ F7: DevUI 整合](./feature-07-devui.md)

---

## 6.1 功能概述

**什麼是 Agent 市場？**

Agent 市場是一個**內建模板庫**，包含 6-8 個預配置的 Agent 模板（客服、IT 支持、銷售、財務、人力資源、數據分析），開發者可以**一鍵部署**。每個模板包含完整的提示工程、輸入/輸出 JSON Schema、Python 程式碼（如需要）和示例工作流。

**為什麼這很重要**：
- **更快實現價值**: 在幾分鐘內而非幾天內部署生產就緒的 Agent
- **最佳實踐**: 由專家構建的模板，具有經過驗證的提示工程
- **學習資源**: 開發者通過示例學習，理解模式
- **一致性**: 組織內的標準化 Agent 結構
- **可擴展性**: 模板是起點，完全可自定義

**關鍵能力**：
1. **內建模板**: 6-8 個針對常見用例的精選 Agent 模板
2. **一鍵部署**: 部署模板 → 自動創建 Agent、工作流、Schema
3. **自定義**: 部署前編輯提示、Schema、程式碼
4. **版本控制**: 模板版本化 (v1.0, v1.1)，追蹤更新
5. **模板驗證**: JSON Schema 驗證、程式碼語法檢查
6. **預覽模式**: 部署前在沙盒中測試模板
7. **使用分析**: 追蹤最受歡迎的模板

**商業價值**：
- **上線速度**: 新開發者 1 小時內而非 1 週內產生價值
- **減少錯誤**: 預驗證的模板將配置錯誤減少 80%
- **知識共享**: 在整個組織範圍內捕獲和共享最佳實踐
- **降低 TCO**: 可重用模板將開發成本降低 40%
- **競爭優勢**: 豐富的生態系統吸引更多用戶使用平台

**內建模板 (MVP)**:

| 模板 ID | 名稱 | 類別 | 用例 | 複雜度 |
|------------|------|----------|----------|------------|
| `tmpl_cs_refund` | 客服退款決策 | 客戶服務 | 根據政策批准/拒絕退款請求 | ⭐⭐⭐ |
| `tmpl_it_password` | IT 密碼重置 | IT 支持 | 驗證用戶身份，重置密碼 | ⭐⭐ |
| `tmpl_sales_lead` | 銷售線索評分 | 銷售 | 基於公司特徵、行為評分線索 | ⭐⭐⭐⭐ |
| `tmpl_fin_expense` | 財務費用審批 | 財務 | 基於規則批准/拒絕費用報銷 | ⭐⭐⭐ |
| `tmpl_hr_interview` | 人力資源面試排程 | 人力資源 | 安排候選人面試，避免衝突 | ⭐⭐⭐ |
| `tmpl_data_report` | 數據報告生成器 | 數據分析 | 從結構化數據生成摘要報告 | ⭐⭐⭐⭐ |

**真實世界示例**：

```
傳統方法（從頭構建）:
1. 開發者閱讀文檔（2 小時）
2. 設計 Agent 提示（3 小時）
3. 定義輸入 JSON Schema（1 小時）
4. 編寫驗證邏輯（2 小時）
5. 使用樣本數據測試（2 小時）
6. 調試和優化（4 小時）
總計: 14 小時

使用 Agent 市場:
1. 瀏覽市場，選擇「客服退款決策」模板
2. 預覽模板（5 分鐘）
3. 點擊「部署」
4. 系統創建預配置的 Agent，包含提示、Schema、示例
5. 根據特定業務規則自定義（30 分鐘）
6. 使用樣本數據測試（15 分鐘）
總計: 50 分鐘（快 93%）
```

**架構概覽**：

```
┌──────────────────┐
│  市場 UI         │
│  (瀏覽、搜索)    │
└────────┬─────────┘
         │
         │ 1. 選擇模板
         ▼
┌──────────────────┐         ┌───────────────┐
│  模板詳情        │────────►│  模板 JSON    │
│  頁面 (預覽)     │         │  (Blob Storage)
└────────┬─────────┘         └───────────────┘
         │
         │ 2. 部署
         ▼
┌──────────────────┐
│  部署            │
│  服務            │
└────────┬─────────┘
         │
         │ 3. 創建資源
         ▼
┌──────────────────┬──────────────────┬──────────────────┐
│  Agent           │  工作流          │  JSON Schema     │
│  (agents 表)     │  (workflows)     │  (schemas)       │
└──────────────────┴──────────────────┴──────────────────┘
```

---

## 6.2 用戶故事（完整）

### **US-F6-001: 瀏覽和搜索 Agent 模板**

**優先級**: P1 (應該擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐

**用戶故事**:
- **作為** 開發者（Emily Zhang）
- **我想要** 瀏覽預構建 Agent 模板的市場，按類別篩選，並按關鍵字搜索
- **以便** 我可以快速找到與我的用例匹配的模板，而不是從頭構建

**驗收標準**:
1. ✅ **模板畫廊**: 以網格視圖顯示所有模板，包含縮略圖、名稱、描述
2. ✅ **類別篩選**: 按類別篩選（客戶服務、IT 支持、銷售、財務、人力資源、數據分析）
3. ✅ **關鍵字搜索**: 按名稱、描述、標籤搜索模板
4. ✅ **排序**: 按受歡迎程度（部署次數）、最新、名稱（A-Z）排序
5. ✅ **模板卡片**: 每張卡片顯示：
   - 模板名稱和圖標
   - 簡短描述（1-2 句話）
   - 類別徽章
   - 複雜度評級（⭐⭐⭐）
   - 部署次數
   - 版本（例如 v1.2）
6. ✅ **點擊查看詳情**: 點擊模板打開詳情頁面，包含完整信息

**市場 UI（畫廊視圖）**：

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Agent 市場                                          [搜索...] [類別 ▼]        │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 🎯 精選模板（最受歡迎）                                                       │
│                                                                               │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│ │ 🎫 客服退款      │  │ 🔑 IT 密碼       │  │ 📊 銷售線索      │           │
│ │ 決策             │  │ 重置             │  │ 評分             │           │
│ │                  │  │                  │  │                  │           │
│ │ 批准/拒絕退款    │  │ 驗證用戶並重置   │  │ 基於公司特徵評分 │           │
│ │ 請求             │  │ 密碼             │  │ 線索             │           │
│ │                  │  │                  │  │                  │           │
│ │ 類別: 客服       │  │ 類別: IT         │  │ 類別: 銷售       │           │
│ │ 複雜度: ⭐⭐⭐    │  │ 複雜度: ⭐⭐      │  │ 複雜度: ⭐⭐⭐⭐  │           │
│ │ 部署: 234        │  │ 部署: 189        │  │ 部署: 156        │           │
│ │ 版本: v1.2       │  │ 版本: v1.0       │  │ 版本: v1.3       │           │
│ │                  │  │                  │  │                  │           │
│ │ [查看詳情]       │  │ [查看詳情]       │  │ [查看詳情]       │           │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                               │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│ │ 💰 財務          │  │ 👥 人力資源面試  │  │ 📈 數據報告      │           │
│ │ 費用審批         │  │ 排程             │  │ 生成器           │           │
│ │                  │  │                  │  │                  │           │
│ │ [查看詳情]       │  │ [查看詳情]       │  │ [查看詳情]       │           │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                               │
│ 按類別篩選: [全部] [客服] [IT] [銷售] [財務] [人力資源] [數據]             │
│ 排序: [受歡迎程度 ▼]                                                         │
└───────────────────────────────────────────────────────────────────────────────┘
```

**API: 列出模板**:

```bash
GET /api/marketplace/templates?category=CS&sort=popularity&page=1

響應:
{
  "total": 6,
  "page": 1,
  "page_size": 20,
  "templates": [
    {
      "template_id": "tmpl_cs_refund",
      "name": "客服退款決策",
      "description": "根據公司政策批准或拒絕客戶退款請求",
      "category": "客戶服務",
      "complexity": 3,
      "version": "1.2",
      "deploy_count": 234,
      "tags": ["客戶服務", "退款", "政策"],
      "created_at": "2025-09-15T10:00:00Z",
      "updated_at": "2025-11-01T14:30:00Z"
    }
  ]
}
```

**完成定義**:
- [ ] 市場 UI 以網格視圖顯示所有模板
- [ ] 按類別篩選有效（客服、IT、銷售、財務、人力資源、數據）
- [ ] 關鍵字搜索按名稱/描述篩選模板
- [ ] 按受歡迎程度、最新、名稱排序有效
- [ ] 模板卡片顯示所有必需信息（名稱、類別、複雜度、部署次數、版本）
- [ ] 點擊模板打開詳情頁面

---

### **US-F6-002: 查看模板詳情和預覽**

**優先級**: P1 (應該擁有)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 開發者（Emily Zhang）
- **我想要** 查看完整的模板詳情，包括提示、輸入/輸出 Schema、程式碼示例，並在沙盒中測試它
- **以便** 我可以在部署前準確了解模板的功能

**驗收標準**:
1. ✅ **模板概覽**: 顯示名稱、描述、類別、複雜度、版本、作者
2. ✅ **提示預覽**: 顯示完整的 LLM 提示模板，包含占位符
3. ✅ **輸入 Schema**: 顯示輸入的 JSON Schema（帶示例）
4. ✅ **輸出 Schema**: 顯示輸出的 JSON Schema（帶示例）
5. ✅ **程式碼預覽**: 顯示 Python 程式碼（如果模板包含自定義邏輯）
6. ✅ **示例工作流**: 顯示使用此 Agent 的樣本工作流 YAML
7. ✅ **測試沙盒**: 交互式表單，使用樣本輸入測試 Agent
8. ✅ **部署按鈕**: 一鍵部署按鈕

**模板詳情頁面 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ ← 返回市場                客服退款決策 v1.2                    [部署]        │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 📋 概覽                                                                       │
│   類別: 客戶服務                                                              │
│   複雜度: ⭐⭐⭐ (中等)                                                        │
│   作者: IPA 團隊                                                              │
│   部署次數: 234 | 最後更新: 2025年11月1日                                    │
│                                                                               │
│   描述:                                                                       │
│   根據公司政策（30 天退貨窗口、客戶層級、產品類型）自動批准或拒絕客戶退款    │
│   請求。使用 GPT-4o 分析請求詳情並提供推理。                                 │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🤖 LLM 提示模板                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 您是一位幫助客戶退款決策的 AI 助手。                                     │ │
│ │                                                                          │ │
│ │ 公司政策:                                                                │ │
│ │ - 標準退貨: 30 天窗口                                                    │ │
│ │ - 高級客戶: 45 天窗口                                                    │ │
│ │ - 有缺陷的產品: 始終批准（無論時間）                                    │ │
│ │ - 客戶忠誠度: 考慮客戶層級和購買歷史                                    │ │
│ │                                                                          │ │
│ │ 輸入:                                                                    │ │
│ │ {input_data}                                                             │ │
│ │                                                                          │ │
│ │ 分析並以 JSON 格式提供決策:                                              │ │
│ │ {{                                                                       │ │
│ │   "decision": "Approved" 或 "Rejected",                                  │ │
│ │   "reasoning": "簡要說明",                                               │ │
│ │   "refund_amount": 數字,                                                 │ │
│ │   "follow_up_action": "字符串"                                           │ │
│ │ }}                                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📥 輸入 Schema (JSON Schema)                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ {                                                                        │ │
│ │   "type": "object",                                                      │ │
│ │   "required": ["customer_id", "product", "issue", "purchase_date"],     │ │
│ │   "properties": {                                                        │ │
│ │     "customer_id": {"type": "string"},                                   │ │
│ │     "product": {"type": "string"},                                       │ │
│ │     "issue": {"type": "string", "enum": ["defective", "not_satisfied"]},│ │
│ │     "purchase_date": {"type": "string", "format": "date"},               │ │
│ │     "customer_tier": {"type": "string", "enum": ["standard", "premium"]}│ │
│ │   }                                                                      │ │
│ │ }                                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 📤 輸出 Schema (JSON Schema)                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ {                                                                        │ │
│ │   "type": "object",                                                      │ │
│ │   "required": ["decision", "reasoning"],                                 │ │
│ │   "properties": {                                                        │ │
│ │     "decision": {"type": "string", "enum": ["Approved", "Rejected"]},   │ │
│ │     "reasoning": {"type": "string"},                                     │ │
│ │     "refund_amount": {"type": "number"},                                 │ │
│ │     "follow_up_action": {"type": "string"}                               │ │
│ │   }                                                                      │ │
│ │ }                                                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🧪 在沙盒中測試                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 客戶 ID: [CUST-5678        ]                                             │ │
│ │ 產品:     [無線耳機        ]                                             │ │
│ │ 問題:     [有缺陷 ▼]                                                     │ │
│ │ 購買日期: [2025-10-15   ]                                                │ │
│ │ 客戶層級: [高級 ▼]                                                       │ │
│ │                                                                          │ │
│ │ [運行測試]                                                               │ │
│ │                                                                          │ │
│ │ 結果:                                                                    │ │
│ │ ✓ 決策: Approved                                                         │ │
│ │   推理: 高級客戶，45 天政策內的有缺陷產品                                │ │
│ │   退款金額: $99.99                                                       │ │
│ │   後續行動: 通過電子郵件發送退貨標籤                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📝 示例工作流 (YAML)                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ workflow:                                                                │ │
│ │   id: "refund-workflow"                                                  │ │
│ │   steps:                                                                 │ │
│ │     - id: "step_1"                                                       │ │
│ │       agent: "CS.RefundDecision"                                         │ │
│ │       input:                                                             │ │
│ │         customer_id: "${workflow.input.customer_id}"                     │ │
│ │         product: "${workflow.input.product}"                             │ │
│ │         issue: "defective"                                               │ │
│ │         purchase_date: "2025-10-15"                                      │ │
│ │         customer_tier: "premium"                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [🚀 部署此模板]  [⭐ 標記為收藏]                                             │
└───────────────────────────────────────────────────────────────────────────────┘
```

**API: 獲取模板詳情**:

```bash
GET /api/marketplace/templates/tmpl_cs_refund

響應:
{
  "template_id": "tmpl_cs_refund",
  "name": "客服退款決策",
  "description": "根據公司政策批准或拒絕客戶退款請求",
  "category": "客戶服務",
  "complexity": 3,
  "version": "1.2",
  "author": "IPA 團隊",
  "prompt_template": "您是一位幫助客戶退款決策的 AI 助手...",
  "input_schema": {
    "type": "object",
    "required": ["customer_id", "product", "issue", "purchase_date"],
    "properties": {...}
  },
  "output_schema": {
    "type": "object",
    "required": ["decision", "reasoning"],
    "properties": {...}
  },
  "code": null,  // 可選的 Python 程式碼
  "example_workflow": "workflow:\n  id: \"refund-workflow\"...",
  "tags": ["客戶服務", "退款", "政策"],
  "deploy_count": 234,
  "created_at": "2025-09-15T10:00:00Z",
  "updated_at": "2025-11-01T14:30:00Z"
}
```

**沙盒測試 API**:

```bash
POST /api/marketplace/templates/tmpl_cs_refund/test
{
  "input": {
    "customer_id": "CUST-5678",
    "product": "無線耳機",
    "issue": "defective",
    "purchase_date": "2025-10-15",
    "customer_tier": "premium"
  }
}

響應:
{
  "output": {
    "decision": "Approved",
    "reasoning": "高級客戶，45 天政策內的有缺陷產品",
    "refund_amount": 99.99,
    "follow_up_action": "通過電子郵件發送退貨標籤"
  },
  "execution_time_ms": 2340,
  "tokens_used": 456,
  "cost_usd": 0.0137
}
```

**完成定義**:
- [ ] 模板詳情頁面顯示所有必需信息（提示、Schema、程式碼、示例）
- [ ] 提示模板使用語法高亮顯示
- [ ] 輸入/輸出 JSON Schema 使用可折疊部分顯示
- [ ] 沙盒測試表單允許用戶輸入樣本數據
- [ ] 測試 API 執行模板並返回結果
- [ ] 示例工作流 YAML 顯示
- [ ] 部署按鈕重定向到部署流程

---

### **US-F6-003: 一鍵部署模板**

**優先級**: P1 (應該擁有)  
**估計開發時間**: 4 天  
**複雜度**: ⭐⭐⭐⭐

**用戶故事**:
- **作為** 開發者（Emily Zhang）
- **我想要** 一鍵部署模板並自動在我的工作區創建 Agent、工作流和 Schema
- **以便** 我可以立即開始使用 Agent，無需手動配置

**驗收標準**:
1. ✅ **部署按鈕**: 點擊「部署」打開部署模態框
2. ✅ **自定義選項**: 允許用戶自定義：
   - Agent 名稱（默認: 模板名稱）
   - Agent ID（自動生成，可編輯）
   - LLM 模型（GPT-4o, GPT-4, GPT-3.5）
   - 溫度（0.0 - 1.0）
   - 最大令牌數（100 - 4000）
3. ✅ **驗證**: 部署前驗證 Agent ID 唯一性
4. ✅ **自動創建**: 系統創建：
   - `agents` 表中的 Agent 記錄
   - `schemas` 表中的輸入/輸出 Schema
   - `workflows` 表中的示例工作流（可選）
5. ✅ **成功反饋**: 顯示成功消息，包含新 Agent 的鏈接
6. ✅ **部署分析**: 追蹤每個模板的部署次數

**部署模態框 UI**:

```
┌───────────────────────────────────────────────────────────────┐
│ 部署模板: 客服退款決策                                 [關閉] │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ 🚀 將此模板部署到您的工作區                                  │
│                                                               │
│ Agent 配置:                                                   │
│                                                               │
│ Agent 名稱: *                                                 │
│ [客服退款決策 Agent                                        ]  │
│                                                               │
│ Agent ID: *                                                   │
│ [cs_refund_decision_001                                    ]  │
│ ℹ️  必須在工作區內唯一                                        │
│                                                               │
│ LLM 模型: *                                                   │
│ [GPT-4o ▼] (推薦)                                             │
│   選項: GPT-4o, GPT-4, GPT-3.5-turbo                          │
│                                                               │
│ 溫度: [0.3        ] (0.0 = 確定性，1.0 = 創造性)             │
│                                                               │
│ 最大令牌數: [2000       ] (100 - 4000)                       │
│                                                               │
│ ────────────────────────────────────────────────────────────│
│                                                               │
│ 附加選項:                                                     │
│ ☑ 創建示例工作流                                              │
│ ☐ 啟用學習（需要 F5）                                         │
│ ☐ 添加到收藏                                                  │
│                                                               │
│ ────────────────────────────────────────────────────────────│
│                                                               │
│ 將創建的內容:                                                 │
│   ✓ Agent: cs_refund_decision_001                            │
│   ✓ 輸入 Schema: cs_refund_decision_input_v1                 │
│   ✓ 輸出 Schema: cs_refund_decision_output_v1                │
│   ✓ 示例工作流: refund_workflow_001 (可選)                   │
│                                                               │
│ [取消]                                    [🚀 立即部署]       │
└───────────────────────────────────────────────────────────────┘
```

**部署成功模態框**:

```
┌───────────────────────────────────────────────────────────────┐
│ ✅ 部署成功！                                          [關閉] │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ 您的 Agent 已成功部署！                                       │
│                                                               │
│ Agent 詳情:                                                   │
│   名稱: 客服退款決策 Agent                                    │
│   ID: cs_refund_decision_001                                  │
│   狀態: ✓ 活動                                                │
│                                                               │
│ 創建的資源:                                                   │
│   ✓ Agent (agents/cs_refund_decision_001)                    │
│   ✓ 輸入 Schema (schemas/cs_refund_decision_input_v1)        │
│   ✓ 輸出 Schema (schemas/cs_refund_decision_output_v1)       │
│   ✓ 示例工作流 (workflows/refund_workflow_001)               │
│                                                               │
│ 後續步驟:                                                     │
│   1. [查看 Agent 詳情] → 配置高級設置                        │
│   2. [運行示例工作流] → 使用樣本數據測試                     │
│   3. [集成到工作流] → 添加到現有工作流                       │
│                                                               │
│ [轉到 Agent 頁面]  [運行示例]  [關閉]                        │
└───────────────────────────────────────────────────────────────┘
```

**部署 API**:

```bash
POST /api/marketplace/templates/tmpl_cs_refund/deploy
{
  "agent_name": "客服退款決策 Agent",
  "agent_id": "cs_refund_decision_001",
  "llm_model": "gpt-4o",
  "temperature": 0.3,
  "max_tokens": 2000,
  "create_example_workflow": true,
  "enable_learning": false
}

響應:
{
  "message": "模板部署成功",
  "agent_id": "cs_refund_decision_001",
  "resources_created": {
    "agent": "agents/cs_refund_decision_001",
    "input_schema": "schemas/cs_refund_decision_input_v1",
    "output_schema": "schemas/cs_refund_decision_output_v1",
    "example_workflow": "workflows/refund_workflow_001"
  },
  "deployed_at": "2025-11-18T10:30:00Z"
}
```

**部署服務實現**:

```python
class MarketplaceDeploymentService:
    """
    市場模板部署服務
    """
    
    def __init__(self, db_session, workflow_service, schema_service):
        self.db = db_session
        self.workflow_service = workflow_service
        self.schema_service = schema_service
    
    async def deploy_template(
        self,
        template_id: str,
        agent_name: str,
        agent_id: str,
        llm_model: str,
        temperature: float,
        max_tokens: int,
        create_example_workflow: bool = True,
        enable_learning: bool = False
    ) -> Dict[str, Any]:
        """
        將市場模板部署到用戶的工作區
        
        創建:
        - Agent 記錄
        - 輸入/輸出 Schema
        - 示例工作流（可選）
        """
        # 1. 加載模板
        template = await self._load_template(template_id)
        
        if not template:
            raise ValueError(f"未找到模板: {template_id}")
        
        # 2. 驗證 Agent ID 唯一性
        existing_agent = self.db.query(Agent).filter_by(agent_id=agent_id).first()
        if existing_agent:
            raise ValueError(f"Agent ID 已存在: {agent_id}")
        
        # 3. 創建 Agent
        agent = Agent(
            agent_id=agent_id,
            name=agent_name,
            description=template["description"],
            prompt_template=template["prompt_template"],
            llm_model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            input_schema_id=f"{agent_id}_input_v1",
            output_schema_id=f"{agent_id}_output_v1",
            learning_enabled=enable_learning,
            deployed_from_template=template_id,
            status="active"
        )
        self.db.add(agent)
        
        # 4. 創建輸入 Schema
        input_schema = Schema(
            schema_id=f"{agent_id}_input_v1",
            name=f"{agent_name} 輸入 Schema",
            schema_type="input",
            json_schema=template["input_schema"],
            version="1.0"
        )
        self.db.add(input_schema)
        
        # 5. 創建輸出 Schema
        output_schema = Schema(
            schema_id=f"{agent_id}_output_v1",
            name=f"{agent_name} 輸出 Schema",
            schema_type="output",
            json_schema=template["output_schema"],
            version="1.0"
        )
        self.db.add(output_schema)
        
        # 6. 創建示例工作流（可選）
        workflow_id = None
        if create_example_workflow and template.get("example_workflow"):
            workflow_yaml = template["example_workflow"].replace(
                "${agent_id}",
                agent_id
            )
            workflow = await self.workflow_service.create_workflow_from_yaml(
                workflow_yaml=workflow_yaml,
                workflow_id=f"{agent_id}_example",
                name=f"{agent_name} 示例工作流"
            )
            workflow_id = workflow.workflow_id
        
        self.db.commit()
        
        # 7. 更新模板部署次數
        await self._increment_deploy_count(template_id)
        
        logger.info(f"模板已部署: {template_id} → {agent_id}")
        
        return {
            "message": "模板部署成功",
            "agent_id": agent_id,
            "resources_created": {
                "agent": f"agents/{agent_id}",
                "input_schema": f"schemas/{agent_id}_input_v1",
                "output_schema": f"schemas/{agent_id}_output_v1",
                "example_workflow": f"workflows/{workflow_id}" if workflow_id else None
            },
            "deployed_at": datetime.utcnow().isoformat()
        }
    
    async def _load_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """從數據庫或 Blob 存儲加載模板"""
        # 從 templates 表或 Azure Blob Storage 加載
        template = self.db.query(MarketplaceTemplate).filter_by(
            template_id=template_id
        ).first()
        
        if not template:
            return None
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "prompt_template": template.prompt_template,
            "input_schema": template.input_schema,
            "output_schema": template.output_schema,
            "example_workflow": template.example_workflow
        }
    
    async def _increment_deploy_count(self, template_id: str):
        """增加模板部署次數"""
        template = self.db.query(MarketplaceTemplate).filter_by(
            template_id=template_id
        ).first()
        
        if template:
            template.deploy_count += 1
            self.db.commit()
```

**完成定義**:
- [ ] 部署按鈕打開帶有自定義選項的模態框
- [ ] 用戶可以自定義 Agent 名稱、ID、LLM 模型、溫度、最大令牌數
- [ ] 系統在部署前驗證 Agent ID 唯一性
- [ ] 系統創建 Agent、輸入 Schema、輸出 Schema、示例工作流
- [ ] 成功模態框顯示創建的資源及其鏈接
- [ ] 模板分析中的部署次數增加
- [ ] 完整部署流程的集成測試

---

### **US-F6-004: 模板使用分析**

**優先級**: P2 (很好擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 平台管理員（Michael Wong）
- **我想要** 查看顯示哪些模板最受歡迎、部署趨勢和用戶反饋的分析
- **以便** 我可以識別需要改進或添加更多模板的類別

**驗收標準**:
1. ✅ **受歡迎程度排名**: 顯示按部署次數排名的模板
2. ✅ **部署趨勢**: 圖表顯示隨時間變化的部署情況（每日/每週/每月）
3. ✅ **類別分佈**: 餅圖顯示按類別劃分的部署情況
4. ✅ **用戶反饋**: 收集並顯示模板的用戶評分（1-5 星）
5. ✅ **搜索分析**: 追蹤用戶搜索的關鍵字（識別空白）

**分析儀表板 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 市場分析                                                        [導出 CSV]    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 📊 概覽（最近 30 天）                                                         │
│   總模板數: 6                                                                 │
│   總部署次數: 1,247                                                           │
│   每個模板的平均部署次數: 208                                                │
│   用戶滿意度: 4.6/5 ⭐⭐⭐⭐⭐                                                 │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🏆 最受歡迎的模板（按部署次數）                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. 客服退款決策: 234 次部署 (18.8%)  ████████████████░░░░               │ │
│ │ 2. IT 密碼重置: 189 次部署 (15.2%)   █████████████░░░░░░░               │ │
│ │ 3. 銷售線索評分: 156 次部署 (12.5%)  ██████████░░░░░░░░░                │ │
│ │ 4. 財務費用: 145 次部署 (11.6%)      █████████░░░░░░░░░░                │ │
│ │ 5. 人力資源面試: 134 次部署 (10.7%)  ████████░░░░░░░░░░░                │ │
│ │ 6. 數據報告: 389 次部署 (31.2%)      ████████████████████                │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 📈 部署趨勢（最近 30 天）                                                     │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 60│                                                        ●              │ │
│ │   │                                                   ●───●               │ │
│ │ 50│                                              ●───●                    │ │
│ │   │                                         ●───●                         │ │
│ │ 40│                                    ●───●                              │ │
│ │   │                               ●───●                                   │ │
│ │ 30│                          ●───●                                        │ │
│ │   │                     ●───●                                             │ │
│ │ 20│                ●───●                                                  │ │
│ │   │           ●───●                                                       │ │
│ │ 10│      ●───●                                                            │ │
│ │   └────┬────┬────┬────┬────┬────┬────┬────┬────┬───                     │ │
│ │       W1   W2   W3   W4   W5   W6   W7   W8                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 🎯 類別分佈                                                                   │
│   客戶服務: 234 (18.8%)                                                      │
│   IT 支持: 189 (15.2%)                                                       │
│   數據分析: 389 (31.2%)                                                      │
│   銷售: 156 (12.5%)                                                          │
│   財務: 145 (11.6%)                                                          │
│   人力資源: 134 (10.7%)                                                      │
│                                                                               │
│ 🔍 熱門搜索關鍵字（識別空白）                                                │
│   1. "數據分析": 89 次搜索                                                   │
│   2. "客戶服務": 67 次搜索                                                   │
│   3. "電子郵件自動化": 45 次搜索 (⚠️ 無可用模板)                            │
│   4. "發票處理": 34 次搜索 (⚠️ 無可用模板)                                  │
└───────────────────────────────────────────────────────────────────────────────┘
```

**完成定義**:
- [ ] 分析儀表板顯示部署次數、趨勢、類別分佈
- [ ] 用戶評分（1-5 星）已收集並顯示
- [ ] 搜索分析識別缺失的模板
- [ ] 將分析導出為 CSV

---

## 6.3 數據庫架構

```sql
CREATE TABLE marketplace_templates (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,  -- CS, IT, Sales, Finance, HR, Data
    complexity INTEGER DEFAULT 1,  -- 1-5 星
    
    -- 模板內容
    prompt_template TEXT NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    code TEXT,  -- 可選的 Python 程式碼
    example_workflow TEXT,  -- YAML
    
    -- 元數據
    version VARCHAR(20) DEFAULT '1.0',
    author VARCHAR(100) DEFAULT 'IPA 團隊',
    tags TEXT[],
    
    -- 分析
    deploy_count INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2),  -- 1.00 - 5.00
    rating_count INTEGER DEFAULT 0,
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketplace_deployments (
    id SERIAL PRIMARY KEY,
    deployment_id VARCHAR(50) UNIQUE NOT NULL,
    template_id VARCHAR(50) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    
    -- 用戶信息
    deployed_by VARCHAR(100) NOT NULL,
    workspace_id VARCHAR(100),
    
    -- 配置
    llm_model VARCHAR(50),
    temperature DECIMAL(3,2),
    max_tokens INTEGER,
    
    -- 時間戳
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (template_id) REFERENCES marketplace_templates(template_id)
);

CREATE TABLE marketplace_ratings (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(50) NOT NULL,
    rating INTEGER NOT NULL,  -- 1-5
    comment TEXT,
    rated_by VARCHAR(100) NOT NULL,
    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (template_id) REFERENCES marketplace_templates(template_id)
);

-- 索引
CREATE INDEX idx_template_category ON marketplace_templates(category, deploy_count DESC);
CREATE INDEX idx_template_popularity ON marketplace_templates(deploy_count DESC);
CREATE INDEX idx_deployment_template ON marketplace_deployments(template_id, deployed_at DESC);
```

---

## 6.4 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **性能** | 模板列表加載時間 | < 1 秒 | 頁面加載指標 |
| | 模板詳情加載時間 | < 500ms | API 響應時間 |
| | 部署時間 | < 5 秒 | 端到端部署 |
| **可擴展性** | 總模板數 | 支持 50+ 模板 | 數據庫容量 |
| | 並發部署 | 每小時 100+ 次 | 負載測試 |
| **質量** | 模板驗證 | 100% 通過 JSON Schema 驗證 | 自動化測試 |
| | 程式碼質量 | 所有模板通過 Linting | CI/CD 檢查 |
| **可用性** | 模板發現 | 用戶在 <2 分鐘內找到模板 | 用戶測試 |
| | 部署成功率 | ≥95% | 部署指標 |

---

## 6.5 測試策略

**單元測試**:
- JSON Schema 驗證
- Agent ID 唯一性檢查
- 模板部署邏輯
- 分析計算

**集成測試**:
- 端到端部署流程
- 模板搜索和篩選
- 沙盒測試執行

**用戶驗收測試**:
- 瀏覽市場
- 部署模板
- 自定義和測試 Agent

---

## 6.6 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| 低質量模板 | 中 | 高 | 同行評審、自動化驗證、用戶評分 |
| 程式碼中的安全漏洞 | 低 | 關鍵 | 程式碼掃描、沙盒執行、安全審計 |
| 模板版本衝突 | 中 | 中 | 語義版本控制、向後兼容性檢查 |
| 授權問題 | 低 | 高 | 明確的授權條款、首選開源 |

---

## 6.7 未來增強（MVP 後）

1. **社區模板**: 允許用戶發布自定義模板
2. **模板市場**: 來自供應商的付費高級模板
3. **模板分叉**: 分叉和自定義現有模板
4. **版本更新**: 當模板更新可用時通知用戶
5. **模板集合**: 針對行業的精選模板包（醫療保健、零售、財務）
6. **A/B 測試**: 比較模板性能變體

---

**下一個功能**: [F7. DevUI 整合 →](./feature-07-devui.md)
