# Sprint 94 技術決策記錄

## 決策列表

### D94-1: GuidedDialogEngine 架構設計

**決策**: 採用組合模式整合 Router + ContextManager + Generator

**選項**:
1. 組合模式 (Router + ContextManager + Generator) (選擇)
2. 繼承模式擴展 BusinessIntentRouter
3. 裝飾器模式包裝 Router

**選擇**: 選項 1

**理由**:
- 職責分離：各組件專注單一職責
- 可測試性：各組件可獨立單元測試
- 靈活性：組件可獨立替換或擴展
- 維護性：修改不影響其他組件

---

### D94-2: 增量更新策略 (核心決策)

**決策**: 基於規則的增量更新，不重新調用 LLM 分類

**選項**:
1. 規則增量更新 (選擇)
2. 每次回答重新 LLM 分類
3. 混合模式 (規則優先，複雜時 LLM)

**選擇**: 選項 1

**理由**:
- 效能：避免重複 LLM 調用，延遲 < 10ms
- 成本：零額外 API 成本
- 一致性：首次分類結果作為真實來源
- 可預測：規則結果確定，易於測試和調試

**關鍵限制**:
- `sub_intent` 只能細化，不能改變 `intent_category`
- 增量更新只更新已收集資訊，不重新判斷意圖

---

### D94-3: Sub-Intent 細化規則

**決策**: 使用條件匹配規則進行 sub_intent 細化

**細化規則表**:

| 原 sub_intent | 觸發條件 | 新 sub_intent |
|--------------|----------|---------------|
| `general_incident` | affected_system=ETL + symptom=報錯 | `etl_failure` |
| `general_incident` | affected_system=網路 + symptom=斷線 | `network_failure` |
| `general_incident` | affected_system=資料庫 + symptom=效能 | `database_performance` |
| `general_incident` | symptom=當機/掛 | `system_down` |
| `general_request` | request_type=帳號 | `account_request` |
| `general_request` | request_type=權限 | `access_request` |
| `general_request` | request_type=軟體 | `software_request` |
| `general_change` | change_type=部署 | `release_deployment` |
| `general_change` | change_type=配置 | `configuration_update` |

**理由**:
- 明確：規則清晰，易於理解
- 可擴展：新規則可輕鬆添加
- 可審計：規則執行可追蹤
- 效能：簡單條件匹配，無額外成本

---

### D94-4: 問題生成策略

**決策**: 基於缺失欄位的模板化問題生成

**選項**:
1. 模板問題生成 (選擇)
2. LLM 動態生成問題
3. 預定義問題池 + 隨機選擇

**選擇**: 選項 1

**理由**:
- 效能：無 API 調用
- 一致性：相同缺失欄位生成相同問題
- 可控：問題內容可預先審核
- 中文支援：模板直接使用繁體中文

**問題模板**:

| 缺失欄位 | 問題模板 |
|---------|---------|
| `affected_system` | 「請問是哪個系統有問題？」 |
| `symptom_type` | 「請描述具體的問題症狀」 |
| `urgency` | 「這個問題的緊急程度如何？是否影響業務？」 |
| `error_message` | 「有看到任何錯誤訊息嗎？」 |
| `requester` | 「請問申請人是誰？」 |
| `request_type` | 「請問您需要申請什麼？」 |
| `justification` | 「請說明申請的原因或業務需求」 |

---

### D94-5: 對話歷史管理

**決策**: 維護結構化對話歷史，包含提取資訊

**歷史記錄結構**:
```python
{
    "role": "user" | "assistant",
    "content": str,
    "timestamp": datetime,
    "extracted": Dict[str, Any],  # 從此回覆提取的欄位
    "context_snapshot": Dict[str, Any],  # 當時的上下文快照
}
```

**理由**:
- 可追蹤：完整記錄對話過程
- 可調試：可重建任意時點的狀態
- 可分析：支援對話品質分析
- 可審計：滿足企業合規需求

---

### D94-6: 完整度重新計算策略

**決策**: 合併已收集資訊後重新計算完整度

**計算公式**:
```
completeness_score = len(present_required_fields) / len(all_required_fields)
is_sufficient = completeness_score >= threshold
```

**資訊來源優先級**:
1. 首次路由提取的欄位
2. 用戶回答提取的欄位 (增量)
3. 用戶回答中的關鍵字匹配

**理由**:
- 準確：基於實際收集的資訊
- 累積：多輪對話逐步完善
- 一致：使用相同的 CompletenessChecker 規則

---

### D94-7: MockGuidedDialogEngine 設計

**決策**: 提供完整 Mock 實現用於測試

**Mock 行為**:
- `generate_questions()`: 返回固定問題列表
- `process_response()`: 基於輸入長度判斷完整度
- 不進行實際的 LLM 調用

**理由**:
- 測試友好：不依賴外部服務
- 快速：測試執行時間 < 1ms
- 可控：行為可預測，易於斷言

---

**創建日期**: 2026-01-15
**更新日期**: 2026-01-15
