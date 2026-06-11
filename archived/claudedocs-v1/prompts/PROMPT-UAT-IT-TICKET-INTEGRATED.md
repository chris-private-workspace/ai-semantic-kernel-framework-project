# UAT 測試任務：IT 工單完整生命週期整合測試

---

## 測試範圍
- **測試 ID**: `integrated-[YYYYMMDD_HHMMSS]`
- **流程名稱**: IT 工單完整生命週期 (Category A 功能整合版)
- **測試類型**: 端到端整合測試
- **涵蓋功能**: 9 個 Category A 功能 (#1, #14, #17, #20, #21, #35, #36, #39, #49)

---

## 必讀文件 (請依序閱讀)

1. **測試腳本**: `scripts/uat/it_ticket_integrated_test.py`
   - 了解 7 個整合階段的實現邏輯
   - 理解功能如何整合到各階段

2. **項目配置**: `CLAUDE.md`
   - API 使用規範
   - 環境變數配置

3. **API 架構**: `backend/src/api/v1/`
   - 各模組 API 實現細節

---

## 參考文件 (測試時查閱)

- `claudedocs/uat/sessions/` - 歷史測試結果參考
- `backend/src/integrations/agent_framework/` - Agent Framework 適配器

---

## 🔴 測試環境強制要求

### Critical 要求

| 要求 | 檢查方式 | 不符合後果 |
|------|----------|------------|
| **真實 Azure OpenAI** | 檢查初始化訊息顯示 "真實 Azure OpenAI" | 測試無效，必須重新執行 |
| **FastAPI 後端** | `curl http://localhost:8000/health` 回傳 `healthy` | 測試無法執行 |
| **PostgreSQL** | `docker-compose ps` 顯示 postgres 運行中 | API 無法運作 |
| **Redis** | `docker-compose ps` 顯示 redis 運行中 | 快取功能無法測試 |

### 環境準備

```bash
# 1. 啟動所有服務
docker-compose up -d

# 2. 等待服務就緒 (約 10-15 秒)
sleep 15

# 3. 驗證服務狀態
docker-compose ps
curl http://localhost:8000/health

# 4. 驗證 Azure OpenAI 配置 (可選)
python scripts/test_azure_openai_connection.py

# 5. 啟動後端 (如果不是使用 docker)
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 環境變數確認

```bash
# 必須設置的環境變數
AZURE_OPENAI_ENDPOINT=https://[resource].openai.azure.com/
AZURE_OPENAI_API_KEY=[your-key]
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o  # 或其他部署名稱
```

---

## 測試流程：7 階段整合設計

### 🔑 核心設計原則
> **功能整合測試**: 9 個 Category A 功能不是獨立測試，而是整合到真實業務流程的相應階段中

### 階段與功能對應表

| 階段 | 名稱 | 整合功能 | 驗證重點 |
|------|------|----------|----------|
| **Phase 1** | 工單接收與建立 | #35 (基準線) | Workflow 創建、快取基準 |
| **Phase 2** | 智慧分類 + 任務分解 | #20, #21, #35 | 真實 LLM 分類、任務分解、計劃生成 |
| **Phase 3** | 路由決策 | - | 場景查詢、能力匹配 |
| **Phase 4** | 人機協作審批 | #14, #39 | Checkpoint 創建、HITL 機制、審批流程 |
| **Phase 5** | Agent 派遣 | - | Handoff 創建、狀態追蹤 |
| **Phase 6** | 工單處理 + 多輪對話 | #1, #17 | GroupChat、多輪對話、投票系統 |
| **Phase 7** | 完成與驗證 | #35, #36, #49 | 快取統計、快取失效、優雅關閉 |

### 功能整合詳情

#### #1 Multi-turn conversation sessions → Phase 6
- 在 GroupChat 專家討論中整合
- 驗證多輪對話會話創建和管理

#### #14 HITL with escalation → Phase 4
- 在高優先級工單審批流程中整合
- 驗證人機協作介入機制

#### #17 Voting system → Phase 6
- 在專家解決方案決策中整合
- 驗證投票會話創建

#### #20 Decompose complex tasks → Phase 2
- 在工單分類後的處理中整合
- 驗證複雜任務分解為子任務

#### #21 Plan step generation → Phase 2
- 在任務分解後的執行規劃中整合
- 驗證使用真實 LLM 生成執行計劃

#### #35 Redis LLM caching → 全程
- Phase 1: 建立基準線
- Phase 2: 驗證 LLM 呼叫後的快取
- Phase 7: 最終統計驗證

#### #36 Cache invalidation → Phase 7
- 在工單完成後的清理中整合
- 驗證快取清除功能

#### #39 Checkpoint state persistence → Phase 4
- 在審批流程中整合
- 驗證 Checkpoint 創建和持久化

#### #49 Graceful shutdown → Phase 7
- 在流程結束時整合
- 驗證系統優雅關閉能力

---

## 測試執行

### 執行命令

```bash
python scripts/uat/it_ticket_integrated_test.py
```

### 預期執行時間
- 正常情況: 90-120 秒
- 主要耗時: Phase 2 (LLM 分類) 和 Phase 6 (多輪對話)

### 執行過程觀察重點

1. **初始化訊息**
   ```
   ✅ AgentExecutorAdapter 初始化成功 (真實 Azure OpenAI)
   ```
   - 必須看到 "真實 Azure OpenAI"，否則測試無效

2. **LLM 呼叫**
   - 觀察每個 LLM 呼叫的 Tokens 和成本
   - 記錄實際回應內容

3. **功能驗證訊息**
   ```
   ✅ #XX [功能名稱] - [驗證詳情]
   ```

4. **最終摘要**
   - 確認 7/7 階段通過
   - 確認 11/11 功能驗證通過

---

## 結果報告要求

### 報告必須包含的內容

#### 1. 測試概覽表
```markdown
| 項目 | 數值 |
|------|------|
| 測試 ID | [值] |
| 總執行時間 | [值] |
| 整體狀態 | PASS/FAIL |
| 階段通過率 | X/7 |
| 功能驗證率 | X/11 |
| LLM 模式 | 真實 Azure OpenAI |
```

#### 2. 各階段詳情

每個階段必須提供：

```markdown
### Phase X: [階段名稱]

**目的**: [階段目標]

**整合功能**: [功能 IDs]

| 步驟 | 操作 | 結果 |
|------|------|------|
| X.1 | [操作] | ✅/⚠️/❌ |

**輸入**:
[實際輸入資料]

**處理**:
[執行的 API 呼叫和操作]

**LLM 響應** (如有):
[實際 LLM 回應內容]

**輸出**:
[該階段的輸出結果]

**功能驗證**:
- ✅ #XX [功能名稱]: [驗證詳情]
```

#### 3. 功能驗證摘要表
```markdown
| 功能 ID | 功能名稱 | 驗證階段 | 狀態 |
|---------|----------|----------|------|
| #1 | Multi-turn sessions | Phase 6 | ✅/❌ |
| ... | ... | ... | ... |
```

#### 4. LLM 使用統計
```markdown
| 指標 | 數值 |
|------|------|
| 總呼叫次數 | [值] |
| 總 Token 數 | [值] |
| 預估成本 | $[值] |
```

#### 5. 創建的資源清單
```markdown
| 資源類型 | ID |
|----------|-----|
| Workflow | [UUID] |
| Execution | [UUID] |
| ... | ... |
```

---

## 🚨 強制完成檢查（不可跳過）

### ✅ 測試準備
- [ ] Docker 服務全部運行中
- [ ] FastAPI 健康檢查通過 (`healthy`)
- [ ] 確認將使用真實 Azure OpenAI (非 mock)

### ✅ 測試執行
- [ ] 完整執行 `it_ticket_integrated_test.py`
- [ ] 觀察到 "真實 Azure OpenAI" 初始化訊息
- [ ] 7 個階段全部執行 (無跳過)
- [ ] 記錄所有 LLM 實際回應

### ✅ 結果驗證
- [ ] 確認整體狀態為 PASSED
- [ ] 確認 11/11 功能驗證通過
- [ ] JSON 結果已保存到 `claudedocs/uat/sessions/`

### ✅ 報告輸出
- [ ] 提供包含「階段說明 + 實際執行內容」的整合報告
- [ ] 報告包含每個階段的輸入/處理/輸出
- [ ] 報告包含 LLM 實際回應內容
- [ ] 報告包含功能驗證結果

---

## ⛔ 禁止事項

1. **禁止使用 Mock LLM**
   - 不可使用模擬或假資料
   - 必須是真實 Azure OpenAI 呼叫

2. **禁止跳過階段**
   - 即使某階段有警告，也必須繼續執行
   - 所有 7 個階段必須完整執行

3. **禁止只顯示階段說明**
   - 報告必須同時包含：
     - 階段說明 (做什麼)
     - 實際執行內容 (怎麼做、得到什麼)

4. **禁止使用舊版測試腳本**
   - 必須使用 `it_ticket_integrated_test.py`
   - 不可使用 `it_ticket_lifecycle_test.py` (15 階段舊版)

---

## 常見問題處理

### Q1: 看到 "模擬模式" 而非 "真實 Azure OpenAI"
**原因**: Azure OpenAI 環境變數未設置或錯誤
**解決**:
```bash
# 檢查環境變數
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_KEY
echo $AZURE_OPENAI_DEPLOYMENT_NAME
```

### Q2: API 健康檢查失敗
**原因**: 後端服務未啟動
**解決**:
```bash
docker-compose up -d
# 或
cd backend && uvicorn main:app --reload
```

### Q3: 某階段返回 4xx 錯誤
**說明**: 某些 4xx 錯誤是預期的業務邏輯 (如 404 表示資源不存在)
**處理**: 繼續執行，在報告中標記為 ⚠️

### Q4: LLM 呼叫超時
**原因**: 網路問題或 Azure OpenAI 服務延遲
**解決**: 重新執行測試，或增加超時設置

---

## 結果存放位置

```
claudedocs/uat/
├── sessions/
│   └── integrated_integrated-[timestamp].json  # 測試結果 JSON
└── reports/
    └── integrated-[timestamp]-report.md        # 人類可讀報告 (手動創建)
```

---

**最後更新**: 2025-12-19
**適用測試腳本版本**: it_ticket_integrated_test.py v1.0
