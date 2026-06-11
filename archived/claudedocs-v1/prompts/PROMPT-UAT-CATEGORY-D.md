# UAT 測試任務：類別 D - Planning & Cross-Scenario 測試

---

## 必讀文件 (請依序閱讀)
1. `claudedocs/uat/P1-FEATURE-TEST-STRATEGY.md` - P1 功能測試策略
2. `scripts/uat/category_d_planning/planning_decision_test.py` - 測試腳本
3. `CLAUDE.md` - 項目配置與 API 規範

## 參考文件 (執行時查閱)
- `claudedocs/uat/FEATURE-INDEX.md` - 功能索引
- `claudedocs/uat/UAT-FEATURE-MAPPING-V2.md` - 功能映射分析
- `claudedocs/uat/sessions/` - 歷史測試結果
- `backend/src/api/v1/routing/` - Routing API 實現
- `backend/src/api/v1/handoff/` - Handoff API 實現
- `backend/src/api/v1/planning/` - Planning API 實現

## 測試範圍
- **測試類別**: Category D - Planning & Cross-Scenario 測試
- **功能編號**: #4, #17, #23, #24, #39 (全為主列表 P1 核心功能)
- **功能分類**: P1 核心功能
- **測試類型**: 獨立場景測試
- **優先級**: 最高 (P1)

### 涵蓋功能清單
| # | 功能名稱 | 測試場景 | API 端點 |
|---|----------|----------|----------|
| 4 | 跨場景協作 (CS<->IT) | Scenario 1 | `/routing/route`, `/routing/relations` |
| 17 | Collaboration Protocol | Scenario 3 | `/handoff/collaborate` |
| 23 | Autonomous Decision | Scenario 4 | `/planning/decisions` |
| 24 | Trial-and-Error 試錯 | Scenario 5 | `/planning/trial` |
| 39 | Agent to Agent (A2A) | Scenario 2 | `/handoff/trigger` |

---

## 🔴 MUST (強制要求)
1. 所有 AI/LLM 呼叫**必須使用真實 Azure OpenAI**，絕不可 mock/simulation
2. 執行前**必須**確認環境健康：`curl http://localhost:8000/health`
3. **必須**完整執行 5 個測試場景，不可跳過
4. **必須**驗證跨場景上下文傳遞
5. **必須**驗證 A2A 通訊協議
6. **必須**驗證自主決策的閾值機制
7. **必須**驗證試錯重試機制
8. **必須**提供包含「場景說明 + 實際執行內容」的整合報告

## 🟡 SHOULD (應該做)
1. 執行前檢查 Docker 服務：`docker-compose ps`
2. 記錄決策過程和選項評估
3. 驗證協作協議的消息流
4. 測試試錯機制的回退策略
5. 確認 A2A 通訊的上下文完整性

## 🟢 MAY (可以做)
1. 調整自主決策的自動審批閾值
2. 測試不同的試錯回退策略
3. 分析跨場景協作的效能

## ⛔ MUST NOT (禁止)
1. **禁止**使用 mock、simulation 或假資料
2. **禁止**跳過任何測試場景
3. **禁止**只提供說明而省略實際執行內容
4. **禁止**忽略決策閾值驗證
5. **禁止**省略試錯統計資訊
6. **禁止**未經確認環境就開始執行測試

---

## 測試執行

### 環境檢查
```bash
docker-compose ps                        # 確認服務運行
curl http://localhost:8000/health        # 確認 API 健康
curl http://localhost:8000/api/v1/routing/status   # 確認 Routing API 可用
curl http://localhost:8000/api/v1/handoff/status   # 確認 Handoff API 可用
curl http://localhost:8000/api/v1/planning/status  # 確認 Planning API 可用
```

### 執行命令
```bash
python scripts/uat/category_d_planning/planning_decision_test.py
```

### 測試場景

#### Scenario 1: 跨場景協作 (#4 Cross-Scenario Collaboration)
```
IT Operations 票單
├── Step 1: 建立 IT 票單
├── Step 2: 路由到 Customer Service 場景
├── Step 3: 驗證執行鏈
└── Step 4: 驗證關聯關係
```
**驗證點**: 跨場景路由、上下文傳遞、執行鏈追蹤、關聯建立

#### Scenario 2: Agent to Agent 通訊 (#39 A2A)
```
Source Agent (Triage) → Target Agent (Specialist)
├── Step 1: 定義 Source/Target Agent
├── Step 2: 觸發 A2A Handoff
├── Step 3: 驗證上下文傳遞
└── Step 4: 驗證 Target Agent 確認
```
**驗證點**: Agent 識別、Handoff 觸發、上下文保持、確認機制

#### Scenario 3: 協作協議 (#17 Collaboration Protocol)
```
Multi-Agent 協作流程
├── Step 1: 配置協作協議
├── Step 2: 觸發多 Agent 協作
├── Step 3: 驗證協議執行 (REQUEST/RESPONSE/ACKNOWLEDGE)
└── Step 4: 驗證協作共識
```
**驗證點**: 協議配置、消息類型、共識機制、參與者確認

#### Scenario 4: 自主決策 (#23 Autonomous Decision)
```
決策流程
├── Step 1: 提交決策請求
├── Step 2: 獲取決策選項 (confidence scores)
├── Step 3: 自動/手動審批
└── Step 4: 驗證決策執行
```
**驗證點**: 決策選項、信心分數、自動審批閾值、審計追蹤

#### Scenario 5: 試錯機制 (#24 Trial-and-Error)
```
試錯流程
├── Step 1: 啟動試錯執行
├── Step 2: 模擬失敗場景
├── Step 3: 驗證重試機制
├── Step 4: 獲取洞察與建議
└── Step 5: 驗證統計資訊
```
**驗證點**: 重試策略、回退機制、學習洞察、統計追蹤

---

## 🚨 強制完成檢查（不可跳過）

### 1. 環境驗證
- [ ] 確認使用**真實 Azure OpenAI**
- [ ] API 健康檢查通過 (`healthy`)
- [ ] Routing、Handoff、Planning API 可用

### 2. 測試執行
- [ ] 5 個場景全部執行完成
- [ ] 5 個 P1 功能全部驗證 (#4, #17, #23, #24, #39)

### 3. 報告輸出（必須同時包含）
- [ ] **各場景說明**：業務背景和測試目的
- [ ] **實際輸入**：測試資料、配置參數
- [ ] **處理過程**：API 呼叫、執行流程
- [ ] **LLM 響應**：分析結果、決策結果（完整）
- [ ] **實際輸出**：路由結果、決策選項、試錯統計
- [ ] **功能驗證**：每個功能 PASS/FAIL

### 4. 特殊驗證
- [ ] **#4**: 跨場景上下文正確傳遞
- [ ] **#17**: 協作協議消息流正確
- [ ] **#23**: 自主決策閾值機制有效
- [ ] **#24**: 試錯重試機制和回退正確
- [ ] **#39**: A2A 通訊上下文完整

### 5. 異常處理
- [ ] 如有失敗 → 記錄具體錯誤和影響範圍
- [ ] 如決策被拒絕 → 分析拒絕原因
- [ ] 如試錯達到上限 → 分析失敗模式

---

**⛔ 未完成以上所有檢查項目，禁止回報測試完成。**
