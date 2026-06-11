# UAT 測試任務：類別 B - 批次處理並行場景測試

---

## 必讀文件 (請依序閱讀)
1. `claudedocs/uat/test_plans/CATEGORY-B-CONCURRENT-PLAN.md` - 測試計劃詳情
2. `scripts/uat/category_b_concurrent/concurrent_batch_test.py` - 測試腳本
3. `CLAUDE.md` - 項目配置與 API 規範

## 參考文件 (執行時查閱)
- `claudedocs/uat/FEATURE-INDEX.md` - 功能索引
- `claudedocs/uat/sessions/` - 歷史測試結果
- `backend/src/api/v1/concurrent/` - Concurrent API 實現
- `backend/src/api/v1/nested/` - Nested Workflow API 實現
- `backend/src/integrations/agent_framework/builders/concurrent.py` - ConcurrentBuilderAdapter

## 測試範圍
- **測試類別**: Category B - 批次處理並行場景
- **功能編號**: #15, B-2, B-3, B-4, B-5, B-6 (Category B 特有功能)
- **功能分類**: 核心編排
- **測試類型**: 整合流程測試
- **目標覆蓋率**: 62% → 74%

### 涵蓋功能清單
| 編號 | 功能名稱 | 測試階段 | 備註 |
|------|----------|----------|------|
| #15 | Concurrent Execution | Phase 2 | 主列表功能 |
| B-2 | Parallel Branch Management | Phase 3 | Category B 特有 |
| B-3 | Fan-out/Fan-in Pattern | Phase 4 | Category B 特有 |
| B-4 | Branch Timeout Handling | Phase 5 | Category B 特有 |
| B-5 | Error Isolation in Branches | Phase 5 | Category B 特有 |
| B-6 | Nested Workflow Context | Phase 6 | Category B 特有 |

> **注意**: B-2 至 B-6 為 Category B 並行測試特有功能，不在主功能列表中

---

## 🔴 MUST (強制要求)
1. 所有 AI/LLM 呼叫**必須使用真實 Azure OpenAI**，絕不可 mock/simulation
2. 執行前**必須**確認環境健康：`curl http://localhost:8000/health`
3. **必須**完整執行 6 個階段，不可跳過
4. **必須**記錄並行執行的時間效能指標
5. **必須**驗證錯誤隔離機制確實生效
6. **必須**提供包含「階段說明 + 實際執行內容」的整合報告

## 🟡 SHOULD (應該做)
1. 執行前檢查 Docker 服務：`docker-compose ps`
2. 記錄每個並行任務的獨立耗時
3. 比較並行執行 vs 串行執行的效能差異
4. 驗證超時分支不影響其他分支
5. 確認子工作流正確繼承父級上下文

## 🟢 MAY (可以做)
1. 調整並行任務數量測試擴展性
2. 測試不同 `max_concurrency` 設定的影響
3. 分析 Fan-out/Fan-in 的彙總策略效果

## ⛔ MUST NOT (禁止)
1. **禁止**使用 mock、simulation 或假資料
2. **禁止**跳過任何測試階段
3. **禁止**只提供說明而省略實際執行內容
4. **禁止**忽略超時或錯誤隔離的驗證
5. **禁止**省略效能指標記錄
6. **禁止**未經確認環境就開始執行測試

---

## 測試執行

### 環境檢查
```bash
docker-compose ps                        # 確認服務運行
curl http://localhost:8000/health        # 確認 API 健康
curl http://localhost:8000/api/v1/concurrent/status  # 確認並行 API 可用
```

### 執行命令
```bash
python scripts/uat/category_b_concurrent/concurrent_batch_test.py
```

### 測試流程
```
Phase 1: Setup Batch
  ├─ 創建 3 張測試票單
  └─ 初始化並行執行器

Phase 2: Concurrent Classification (#15)
  ├─ 並行分類 3 張票單
  ├─ 記錄執行時間
  └─ 驗證效能提升

Phase 3: Parallel Branches (#22)
  ├─ 啟動分類分支
  ├─ 啟動診斷分支
  └─ 驗證分支獨立性

Phase 4: Fan-out/Fan-in (#23)
  ├─ 分發到 3 個分析 Agent
  ├─ 等待所有結果
  └─ 彙總分析報告

Phase 5: Timeout & Error Handling (#24, #25)
  ├─ 設定短超時分支
  ├─ 模擬錯誤分支
  └─ 驗證隔離機制

Phase 6: Nested Context (#28)
  ├─ 啟動子工作流
  ├─ 傳遞批次上下文
  └─ 驗證上下文傳遞
```

---

## 效能基準 (必須記錄)

| 測試項目 | 預期指標 | 實際結果 |
|---------|---------|----------|
| 3 票單並行分類 | < 單一票單 × 1.5 | [ ] |
| Fan-out 到 3 Agent | < 單一 Agent × 2 | [ ] |
| 錯誤隔離響應 | < 100ms | [ ] |
| 超時檢測精確度 | ±500ms | [ ] |

---

## 🚨 強制完成檢查（不可跳過）

### 1. 環境驗證
- [ ] 確認使用**真實 Azure OpenAI**
- [ ] API 健康檢查通過 (`healthy`)
- [ ] Concurrent API 可用

### 2. 測試執行
- [ ] 6 個階段全部執行完成
- [ ] 6 個功能全部驗證 (#15, B-2, B-3, B-4, B-5, B-6)

### 3. 報告輸出（必須同時包含）
- [ ] **各階段說明**：每階段的目的
- [ ] **實際輸入**：測試票單、並行配置
- [ ] **處理過程**：API 呼叫、並行執行狀態
- [ ] **LLM 響應**：分類結果、診斷結果（完整）
- [ ] **效能指標**：並行 vs 串行時間比較
- [ ] **功能驗證**：每個功能 PASS/FAIL

### 4. 特殊驗證
- [ ] 並行執行確實提升效能
- [ ] 超時分支正確標記且不影響其他分支
- [ ] 錯誤被正確隔離
- [ ] 子工作流正確繼承上下文

### 5. 異常處理
- [ ] 如有失敗 → 記錄具體錯誤和影響範圍
- [ ] 如效能未達標 → 分析瓶頸原因

---

**⛔ 未完成以上所有檢查項目，禁止回報測試完成。**
