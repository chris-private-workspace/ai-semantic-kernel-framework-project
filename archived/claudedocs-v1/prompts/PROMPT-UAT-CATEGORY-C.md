# UAT 測試任務：類別 C - 獨立進階測試場景

---

## 必讀文件 (請依序閱讀)
1. `claudedocs/uat/test_plans/CATEGORY-C-ADVANCED-PLAN.md` - 測試計劃詳情
2. `scripts/uat/category_c_advanced/advanced_workflow_test.py` - 測試腳本
3. `CLAUDE.md` - 項目配置與 API 規範

## 參考文件 (執行時查閱)
- `claudedocs/uat/FEATURE-INDEX.md` - 功能索引
- `claudedocs/uat/sessions/` - 歷史測試結果
- `backend/src/api/v1/nested/` - Nested Workflow API 實現
- `backend/src/api/v1/connectors/` - Connectors API 實現
- `backend/src/api/v1/routing/` - Routing API 實現

## 測試範圍
- **測試類別**: Category C - 獨立進階測試場景
- **功能編號**: #26, #27, #34, C-4 (C-4 為 Category C 特有功能)
- **功能分類**: 核心編排、整合、智能路由
- **測試類型**: 獨立場景測試
- **目標覆蓋率**: 74% → 82%

### 涵蓋功能清單
| 編號 | 功能名稱 | 測試場景 | 備註 |
|------|----------|----------|------|
| #26 | Sub-workflow Composition | 文件審批流程 | 主列表功能 |
| #27 | Recursive Execution | 問題根因分析 (5 Whys) | 主列表功能 |
| #34 | External Connector Updates | ServiceNow 同步 | 主列表功能 |
| C-4 | Message Prioritization | 緊急事件處理 | Category C 特有 |

> **注意**: C-4 為 Category C 進階測試特有功能，主列表 #37 為「主動巡檢模式」

---

## 🔴 MUST (強制要求)
1. 所有 AI/LLM 呼叫**必須使用真實 Azure OpenAI**，絕不可 mock/simulation
2. 執行前**必須**確認環境健康：`curl http://localhost:8000/health`
3. **必須**完整執行 4 個測試場景，不可跳過
4. **必須**驗證遞迴執行的深度限制和終止條件
5. **必須**記錄子工作流的組合和結果彙總
6. **必須**提供包含「場景說明 + 實際執行內容」的整合報告

## 🟡 SHOULD (應該做)
1. 執行前檢查 Docker 服務：`docker-compose ps`
2. 記錄遞迴分析的每一層深度
3. 驗證外部連接器的重試機制
4. 測試消息優先級的搶占行為
5. 確認子工作流組合策略正確應用

## 🟢 MAY (可以做)
1. 調整遞迴最大深度測試邊界情況
2. 測試不同組合策略 (all_required, any_one, majority)
3. 分析優先級隊列的公平性

## ⛔ MUST NOT (禁止)
1. **禁止**使用 mock、simulation 或假資料（外部連接器除外）
2. **禁止**跳過任何測試場景
3. **禁止**只提供說明而省略實際執行內容
4. **禁止**忽略遞迴深度限制的驗證
5. **禁止**省略子工作流組合結果
6. **禁止**未經確認環境就開始執行測試

> **注意**: 功能 #34 (External Connector) 可使用 Mock ServiceNow 響應，因需要外部系統配合

---

## 測試執行

### 環境檢查
```bash
docker-compose ps                        # 確認服務運行
curl http://localhost:8000/health        # 確認 API 健康
curl http://localhost:8000/api/v1/nested/status    # 確認 Nested API 可用
curl http://localhost:8000/api/v1/routing/status   # 確認 Routing API 可用
```

### 執行命令
```bash
python scripts/uat/category_c_advanced/advanced_workflow_test.py
```

### 測試場景

#### Scenario 1: 文件審批流程 (#26 Sub-workflow Composition)
```
主工作流: 文件審批
├── 子工作流 1: 部門主管審批
├── 子工作流 2: 財務審核
├── 子工作流 3: 法務審查
└── 組合結果 → 最終決策
```
**驗證點**: 子工作流組合、獨立執行、組合策略、結果彙總

#### Scenario 2: 問題根因分析 (#27 Recursive Execution)
```
問題: 系統響應緩慢
├── Why 1: 資料庫查詢慢
│   ├── Why 2: 缺少索引
│   │   ├── Why 3: 新功能未優化
│   │   │   ├── Why 4: 開發時間緊迫
│   │   │   │   └── Why 5: 需求變更太頻繁 (根因)
```
**驗證點**: 遞迴執行、深度限制、終止條件、路徑追蹤

#### Scenario 3: ServiceNow 同步 (#34 External Connector)
```
IPA 票單狀態變更 → 觸發連接器 → 同步到 ServiceNow → 確認成功
```
**驗證點**: 連接器觸發、資料格式轉換、同步狀態追蹤、重試機制

#### Scenario 4: 緊急事件處理 (C-4 Message Prioritization)
```
消息隊列:
├── 低優先級: 一般查詢 (priority: 1)
├── 中優先級: 功能請求 (priority: 5)
├── 高優先級: 系統告警 (priority: 8)
└── 緊急: 安全事件 (priority: 10) ← 優先處理
```
**驗證點**: 優先級排序、高優先級優先、搶占機制、公平性

---

## 🚨 強制完成檢查（不可跳過）

### 1. 環境驗證
- [ ] 確認使用**真實 Azure OpenAI**
- [ ] API 健康檢查通過 (`healthy`)
- [ ] Nested 和 Routing API 可用

### 2. 測試執行
- [ ] 4 個場景全部執行完成
- [ ] 4 個功能全部驗證 (#26, #27, #34, C-4)

### 3. 報告輸出（必須同時包含）
- [ ] **各場景說明**：業務背景和測試目的
- [ ] **實際輸入**：測試資料、配置參數
- [ ] **處理過程**：API 呼叫、執行流程
- [ ] **LLM 響應**：分析結果、決策結果（完整）
- [ ] **實際輸出**：子工作流結果、遞迴路徑、優先級順序
- [ ] **功能驗證**：每個功能 PASS/FAIL

### 4. 特殊驗證
- [ ] **#26**: 子工作流正確組合且結果正確彙總
- [ ] **#27**: 遞迴深度限制有效且終止條件正確觸發
- [ ] **#34**: 連接器正確觸發且重試機制有效
- [ ] **C-4**: 高優先級確實優先處理且搶占機制有效

### 5. 異常處理
- [ ] 如有失敗 → 記錄具體錯誤和影響範圍
- [ ] 如遞迴未終止 → 分析終止條件問題
- [ ] 如優先級失效 → 分析隊列處理邏輯

---

**⛔ 未完成以上所有檢查項目，禁止回報測試完成。**
