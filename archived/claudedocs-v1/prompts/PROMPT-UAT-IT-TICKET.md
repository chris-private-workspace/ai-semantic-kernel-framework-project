# UAT 測試任務：IT 工單完整生命週期整合測試

---

## 必讀文件 (請依序閱讀)
1. `scripts/uat/it_ticket_integrated_test.py` - 測試腳本實現
2. `CLAUDE.md` - 項目配置與 API 規範
3. `claudedocs/uat/sessions/` - 歷史測試結果參考 (如有)

## 參考文件 (執行時查閱)
- `backend/src/api/v1/` - API 實現細節
- `backend/src/integrations/agent_framework/` - Agent Framework 適配器

## 測試要求
1. **🔴 強制使用真實 Azure OpenAI** - 絕不可使用 mock/simulation
2. 執行前確認後端服務運行中：`curl http://localhost:8000/health`
3. 執行前確認 Docker 服務運行中：`docker-compose ps`
4. 完整執行 7 個階段，不可跳過任何階段
5. 9 個 Category A 功能必須在對應階段中**整合驗證**（非獨立測試）

## 執行命令
```bash
python scripts/uat/it_ticket_integrated_test.py
```

請執行測試並提供完整報告。

---

## 🚨 強制完成檢查（不可跳過）

### 1. 環境驗證
- [ ] 確認初始化訊息顯示 "真實 Azure OpenAI"
- [ ] API 健康檢查返回 `healthy`

### 2. 測試執行
- [ ] 7/7 階段全部執行完成
- [ ] 11/11 功能驗證通過

### 3. 報告輸出（必須包含）
- [ ] **各階段詳情**：每階段的目的、輸入、處理、輸出
- [ ] **LLM 實際響應**：真實 AI 回應內容（非只顯示 "已完成"）
- [ ] **功能驗證結果**：9 個功能在哪個階段如何被驗證
- [ ] **統計摘要**：執行時間、LLM 呼叫次數、Token 數、成本

### 4. 結果保存
- [ ] JSON 結果已自動保存至 `claudedocs/uat/sessions/`

---

## ⛔ 禁止事項
- 禁止使用 mock 或模擬 LLM
- 禁止跳過任何測試階段
- 禁止只提供階段說明而不提供實際執行內容
- 禁止使用舊版 15 階段測試腳本 (`it_ticket_lifecycle_test.py`)

**⛔ 未完成以上所有步驟，禁止回報測試完成。**
