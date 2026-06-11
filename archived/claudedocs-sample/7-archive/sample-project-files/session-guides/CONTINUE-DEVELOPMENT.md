# 🔄 Session Guide: 繼續開發工作

> **使用時機**: 繼續上次未完成的開發工作
> **目標**: 快速恢復上下文，繼續高效開發
> **預計時間**: 5-10 分鐘

---

## 📋 Prompt 模板

```markdown
我需要繼續上次的開發工作。

請幫我:

1. 恢復上下文
   - 檢查 Git 狀態 (`git status`, `git branch`)
   - 閱讀最新的每週進度 (`claudedocs/3-progress/weekly/2025-WXX.md`)
   - 檢查 TodoWrite 任務清單

2. 確認當前任務
   - 查看進行中的任務
   - 確認任務優先級
   - 識別阻礙

3. 繼續開發
   - 根據任務清單繼續執行
   - 更新 TodoWrite 狀態
   - 記錄遇到的問題

請用中文溝通。
```

---

## 🤖 AI 執行步驟

### Step 1: 恢復上下文 (3 分鐘)

```bash
# Git 狀態
Bash: git status
Bash: git branch
Bash: git log --oneline -5

# 最新進度
Read: claudedocs/3-progress/weekly/2025-WXX.md (最新)

# 檢查 TodoWrite (AI 內部)
```

### Step 2: 確認任務 (2 分鐘)

**輸出範例**:
```markdown
## 當前狀態

### Git
- Branch: feature/epic-9-sprint-1
- 未提交變更: 3 個文件
- 最後提交: "feat: 創建 AI Service 基礎架構"

### 進行中任務
- [進行中] 實作 BudgetAI Service
  - 已完成: 基礎架構、OpenAI 客戶端
  - 待完成: generateBudgetSuggestion 方法、單元測試

### 待辦任務 (優先級排序)
1. [P0] 完成 BudgetAI Service 實作
2. [P0] 撰寫 BudgetAI 單元測試
3. [P1] 創建 tRPC Router (aiSuggestion)
4. [P1] 實作前端 AI 建議組件

### 已知問題
- Azure OpenAI API 金鑰尚未設定
```

### Step 3: 繼續開發

直接根據任務清單繼續執行，AI 助手會:
- 使用適當的工具 (Read, Edit, Write, Bash)
- 更新 TodoWrite 狀態
- 記錄問題到文檔

---

## ✅ 驗收標準

- [ ] Git 狀態已確認
- [ ] TodoWrite 任務清單已檢視
- [ ] 當前任務已明確
- [ ] 已識別任何阻礙

---

## 🔗 相關文檔

- [SITUATION-3: 舊功能進階](../prompts/SITUATION-3-FEATURE-ENHANCEMENT.md)
- [SITUATION-4: 新功能開發](../prompts/SITUATION-4-NEW-FEATURE-DEV.md)
- [START-NEW-EPIC Session Guide](./START-NEW-EPIC.md)

---

**維護者**: AI 助手團隊
**最後更新**: 2025-11-08
