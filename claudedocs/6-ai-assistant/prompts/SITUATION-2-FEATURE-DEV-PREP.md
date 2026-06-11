# 🔧 情況2: 開發新功能/修復前準備

> **使用時機**: 準備開發新功能或修復舊功能前
> **目標**: 驗證架構支援，制定實施計劃
> **適用場景**: 開始 Sprint, 接到新任務, 設計階段

---

## 📋 Prompt 模板

```markdown
我需要 [開發新功能 / 修復舊功能]: [功能/Bug 描述]

請幫我:

1. 快速回顧專案現況
   - 閱讀 `docs/bmm-workflow-status.yaml`
   - 檢查當前 Git 分支和最近提交
   - 閱讀最新的每週進度報告 (如有)

2. 驗證架構支援
   - 檢查 `backend/src/domain/` 相關業務邏輯
   - 檢查 `backend/src/api/v1/` 相關 API
   - 檢查 `backend/src/integrations/` 相關整合 (如有)

3. 制定實施計劃
   - 識別需要修改的文件
   - 評估架構變更需求
   - 列出前置任務和依賴
   - 估算工作量

4. 創建任務清單
   - 使用 TodoWrite 創建任務清單
   - 分解為可執行的小任務
   - 標註優先級和依賴關係

請用中文回答。
```

---

## 🤖 AI 執行步驟

### 階段 1: 理解需求 (3 分鐘)
```bash
# 讀取相關文檔
Read: docs/bmm-workflow-status.yaml
Read: archived/docs-v1/03-implementation/sprint-execution/sprint-XX/story-XX.md (如果是 Sprint 任務)
Read: claudedocs/3-progress/weekly/最新.md (如有)

# 檢查 Git 狀態
Bash: git status
Bash: git log --oneline -5
```

### 階段 2: 驗證架構 (5 分鐘)
```bash
# 檢查相關業務邏輯
Glob: pattern="backend/src/domain/[相關模組]/**/*.py"
Read: [找到的相關文件]

# 檢查相關 API
Grep: pattern="相關關鍵字" path="backend/src/api/v1/"

# 檢查相關測試
Glob: pattern="backend/tests/unit/[相關模組]/**/*.py"
```

### 階段 3: 制定計劃 (5 分鐘)
```markdown
# 實施計劃

## 需求分析
- **功能**: [描述]
- **用戶故事**: [如果有]
- **驗收標準**: [列出]

## 架構評估
- **業務邏輯**: ✅ 支援 / ⚠️ 需修改 / ❌ 需新增
- **API**: ✅ 可用 / ⚠️ 需擴展 / ❌ 需新增
- **測試**: ✅ 覆蓋 / ⚠️ 需補充 / ❌ 需新增

## 文件變更清單
### 後端
- [ ] `backend/src/domain/xxx/` - [變更描述]
- [ ] `backend/src/api/v1/xxx/` - [變更描述]

### 測試
- [ ] `backend/tests/unit/xxx/` - [測試計劃]

## 工作量估算
- **業務邏輯**: X 小時
- **API 開發**: X 小時
- **測試**: X 小時
- **總計**: X 小時 (~X 天)

## 風險評估
- ⚠️ [識別的風險] → [緩解措施]
```

---

## ✅ 驗收標準

開發準備完成後，應該確認:

1. **需求理解**
   - 清楚功能目標和驗收標準
   - 了解相關的現有模組和代碼

2. **架構評估**
   - 確認架構是否支援功能需求
   - 識別需要新增或修改的組件

3. **計劃制定**
   - 有明確的文件變更清單
   - 有合理的工作量估算

4. **任務分解**
   - TodoWrite 已創建任務清單
   - 任務可獨立執行

---

## 🔗 相關文檔

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md)
- [情況3: 功能增強/修正](./SITUATION-3-FEATURE-ENHANCEMENT.md)
- [情況4: 新功能開發](./SITUATION-4-NEW-FEATURE-DEV.md)
- [情況5: 保存進度](./SITUATION-5-SAVE-PROGRESS.md)

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2025-12-27
**版本**: 2.0
