# UAT 測試快速參考 Prompt

以下是可直接複製使用的測試 prompt 模板。

---

## 🎫 IT 工單整合測試 (推薦)

```
# UAT 測試任務：IT 工單完整生命週期整合測試

## 必讀文件
1. scripts/uat/it_ticket_integrated_test.py (測試腳本)
2. CLAUDE.md (項目配置)

## 🔴 強制要求
- 所有 AI 呼叫必須使用**真實 Azure OpenAI** (不可 mock)
- 後端服務必須運行於 http://localhost:8000
- Docker 服務 (PostgreSQL, Redis) 必須正常運行

## 環境檢查
```bash
docker-compose ps
curl http://localhost:8000/health
```

## 測試執行
```bash
python scripts/uat/it_ticket_integrated_test.py
```

## 報告要求
執行完成後，必須提供**整合報告**，包含：
1. **階段說明**: 每個階段的目的和整合的功能
2. **實際執行內容**: 每個階段的輸入、處理、輸出
3. **LLM 響應**: 真實 AI 回應內容
4. **功能驗證**: 11 個功能的驗證結果

## 🚨 強制檢查
- [ ] 確認使用真實 Azure OpenAI
- [ ] 7/7 階段全部執行
- [ ] 11/11 功能驗證通過
- [ ] 報告包含階段說明 + 實際內容

⛔ 禁止：使用 mock、跳過階段、只顯示說明不顯示內容
```

---

## 🔧 單一功能測試

```
# UAT 測試任務：[功能名稱] 驗證

## 測試資訊
- Feature ID: #[XX]
- Feature 名稱: [功能名稱]

## 必讀文件
1. [相關 story 文件]
2. [相關測試計劃]

## 🔴 強制要求
- 使用真實 Azure OpenAI (不可 mock)
- 確保環境正常運行

## 測試執行
[測試步驟或命令]

## 預期結果
[描述成功標準]

## 報告要求
1. 測試輸入
2. 實際輸出
3. LLM 響應 (如有)
4. 測試結論 (PASS/FAIL)

## 🚨 強制檢查
- [ ] 確認使用真實 LLM
- [ ] 記錄完整輸入/輸出
- [ ] 提供測試結論
```

---

## 🔄 回歸測試

```
# UAT 回歸測試：[修復項目] 驗證

## 測試背景
- 原始問題: [描述]
- 修復內容: [描述]

## 測試步驟
1. 確認原始問題已修復
2. 確認相關功能無副作用

## 驗證結果
- [ ] 原始問題已修復
- [ ] 無副作用發現
```

---

## 📊 通用報告格式

```markdown
## 測試報告：[測試名稱]

### 概覽
| 項目 | 數值 |
|------|------|
| 測試 ID | [值] |
| 執行時間 | [值] |
| 整體狀態 | PASS/FAIL |
| LLM 模式 | 真實 Azure OpenAI |

### 階段 X: [階段名稱]

**目的**: [做什麼]

**輸入**:
[實際輸入資料]

**處理**:
[執行的操作]

**LLM 響應**:
[實際 AI 回應]

**輸出**:
[結果資料]

**驗證**: ✅ PASS / ❌ FAIL

### 功能驗證摘要
| 功能 | 狀態 |
|------|------|
| #XX [名稱] | ✅/❌ |

### LLM 統計
- 呼叫次數: [值]
- Token 數: [值]
- 成本: $[值]
```

---

## ⚡ 一行指令

```bash
# IT 工單整合測試
python scripts/uat/it_ticket_integrated_test.py

# 檢查環境
docker-compose ps && curl http://localhost:8000/health

# 查看測試結果
ls -la claudedocs/uat/sessions/
```

---

**提示**: 複製上方的 prompt 模板，替換 `[...]` 中的內容即可使用。
