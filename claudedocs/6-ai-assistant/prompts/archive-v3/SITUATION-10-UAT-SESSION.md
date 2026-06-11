# 🎯 情況10: UAT 測試 - 用戶驗收測試會話

> **使用時機**: 進行 Phase 或 Sprint 的用戶驗收測試時
> **目標**: 驗證功能是否符合需求規格
> **適用場景**: Phase 完成驗收、Sprint 結束驗收、功能驗收

---

## 📋 Prompt 模板 (給開發人員)

```markdown
你好！我需要進行 UAT 測試。

**測試範圍**:
- Phase/Sprint: [Phase X / Sprint XX]
- 測試項目: [要測試的功能列表]

**驗收標準** (如有):
- [標準 1]
- [標準 2]

請幫我：

1. 準備測試環境
   - 確認服務運行正常
   - 準備測試數據

2. 執行測試場景
   - 按照驗收標準測試
   - 記錄測試結果

3. 問題追蹤
   - 記錄發現的問題
   - 評估問題嚴重程度

4. 生成測試報告
   - 總結測試結果
   - 給出驗收建議

請用中文回答。
```

---

## 🤖 AI 助手執行步驟

### Step 1: 準備測試環境 (2 分鐘)

```bash
# 1. 確認服務狀態
Bash: docker-compose ps

# 2. 啟動服務 (如需要)
Bash: docker-compose up -d

# 3. 確認後端健康
Bash: curl http://localhost:8000/health

# 4. 確認 API 可用
Bash: curl http://localhost:8000/api/v1/
```

### Step 2: 了解測試範圍 (2 分鐘)

```bash
# 1. 閱讀相關 Sprint 文檔
Read: archived/docs-v1/03-implementation/sprint-execution/sprint-XX/

# 2. 閱讀相關 Phase 文檔
Read: archived/docs-v1/03-implementation/sprint-planning/phase-XX/

# 3. 了解功能規格
Read: archived/docs-v1/01-planning/prd/features/[相關功能].md (如有)
```

### Step 3: 執行測試場景 (主要時間)

```bash
# 1. 運行自動化測試
Bash: cd backend && pytest tests/unit/ -v --tb=short

# 2. 運行整合測試 (如有)
Bash: cd backend && pytest tests/integration/ -v --tb=short

# 3. 運行 E2E 測試 (如有)
Bash: cd backend && pytest tests/e2e/ -v --tb=short

# 4. 手動 API 測試
Bash: curl -X POST http://localhost:8000/api/v1/... -H "Content-Type: application/json" -d '{...}'
```

### Step 4: 生成 UAT 報告 (3 分鐘)

```markdown
# 🎯 UAT 測試報告

## 測試摘要
- **測試日期**: YYYY-MM-DD
- **測試範圍**: Phase X / Sprint XX
- **測試環境**: 本地開發環境
- **測試人員**: AI 助手 + 開發者

---

## 📊 測試結果總覽

| 類別 | 總數 | 通過 | 失敗 | 跳過 | 通過率 |
|------|------|------|------|------|--------|
| 單元測試 | X | X | X | X | X% |
| 整合測試 | X | X | X | X | X% |
| E2E 測試 | X | X | X | X | X% |
| 手動測試 | X | X | X | X | X% |
| **總計** | **X** | **X** | **X** | **X** | **X%** |

---

## ✅ 功能驗收

### 核心功能
| 功能 | 狀態 | 說明 |
|------|------|------|
| [功能 1] | ✅ 通過 | [說明] |
| [功能 2] | ⚠️ 部分通過 | [問題說明] |
| [功能 3] | ❌ 未通過 | [問題說明] |

### API 端點驗證
| 端點 | 方法 | 狀態 | 備註 |
|------|------|------|------|
| `/api/v1/xxx` | GET | ✅ | 正常運作 |
| `/api/v1/xxx` | POST | ✅ | 正常運作 |

---

## 🐛 發現的問題

### 高優先級 (必須修復)
| ID | 描述 | 影響 | 狀態 |
|----|------|------|------|
| UAT-001 | [問題描述] | [影響說明] | 待修復 |

### 中優先級 (建議修復)
| ID | 描述 | 影響 | 狀態 |
|----|------|------|------|
| UAT-002 | [問題描述] | [影響說明] | 待修復 |

### 低優先級 (可延後)
| ID | 描述 | 影響 | 狀態 |
|----|------|------|------|
| UAT-003 | [問題描述] | [影響說明] | 已記錄 |

---

## 📈 測試覆蓋

### 代碼覆蓋率
- **整體覆蓋率**: X%
- **Domain 層**: X%
- **API 層**: X%
- **Infrastructure**: X%

### 未覆蓋區域
- [未覆蓋模組/功能 1]
- [未覆蓋模組/功能 2]

---

## 🎯 驗收結論

### 驗收狀態: ✅ 通過 / ⚠️ 有條件通過 / ❌ 未通過

### 結論說明
[總體評價和說明]

### 後續建議
1. [建議 1]
2. [建議 2]

---

## 📎 附件
- 測試日誌: [位置]
- 錯誤截圖: [位置] (如有)
```

---

## 📋 UAT 測試場景範例

### IPA Platform 常見測試場景

```yaml
# Phase 11: Agent-Session Integration
session_test_scenarios:
  - name: "Session 創建和激活"
    steps:
      - POST /sessions 創建會話
      - 驗證返回 session_id
      - 驗證 status = "created"
    expected: 會話成功創建

  - name: "Chat 發送和回應"
    steps:
      - POST /sessions/{id}/chat 發送訊息
      - 驗證返回 assistant 回應
      - 驗證 tool_calls 處理
    expected: 正常對話流程

  - name: "Streaming 回應"
    steps:
      - POST /sessions/{id}/chat/stream
      - 驗證 SSE 事件格式
      - 驗證 content_delta 事件
    expected: 串流正常運作

  - name: "Tool 審批流程"
    steps:
      - 設定 approval_mode = "manual"
      - 觸發 tool_call
      - POST /tool-calls/{id}/approve
    expected: 審批流程正常
```

---

## ✅ 驗收標準

AI 助手完成 UAT 後應提供：

1. **環境確認**
   - 服務正常運行
   - 測試環境就緒

2. **測試執行**
   - 所有測試場景已執行
   - 測試結果已記錄

3. **問題追蹤**
   - 問題已分類和記錄
   - 提供問題嚴重程度評估

4. **驗收報告**
   - 完整的測試報告
   - 明確的驗收建議

---

## 🔗 相關文檔

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md)
- [情況5: 測試執行](./SITUATION-5-TESTING.md)
- [情況7: 架構審查](./SITUATION-7-ARCHITECTURE-REVIEW.md)

### 測試資源
- `scripts/uat/` - UAT 測試腳本
- `archived/docs-v1/03-implementation/sprint-execution/` - Sprint 執行記錄

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2025-12-24
**版本**: 2.0
