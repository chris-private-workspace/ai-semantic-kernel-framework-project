# 🐛 Session Guide: Debug 問題排查

> **使用時機**: 遇到 Bug、錯誤或異常行為
> **目標**: 系統化排查問題根本原因
> **預計時間**: 15-60 分鐘 (視問題複雜度)

---

## 📋 Prompt 模板

```markdown
我遇到以下問題需要 Debug:

**問題描述**: [描述問題]
**復現步驟**: [如何復現]
**預期行為**: [應該如何]
**實際行為**: [實際如何]
**錯誤訊息**: [錯誤訊息]

請幫我:

1. 理解問題
   - 分析錯誤訊息
   - 識別可能的根本原因
   - 評估影響範圍

2. 系統化排查
   - 檢查相關程式碼
   - 檢查日誌
   - 執行測試驗證

3. 修復問題
   - 實作修復方案
   - 驗證修復有效
   - 更新測試防止回歸

4. 記錄修復
   - 創建 FIX-XXX.md 文檔
   - 記錄根本原因、解決方案、影響範圍

請用中文溝通。
```

---

## 🤖 AI 執行步驟

### Step 1: 理解問題 (5 分鐘)

```bash
# 1. 檢查錯誤日誌
Bash: tail -n 100 logs/error.log (如果有)

# 2. 檢查 Git 最近變更
Bash: git log --oneline -10
Bash: git diff HEAD~1

# 3. 搜尋相關程式碼
Grep: pattern="錯誤關鍵字" output_mode="files_with_matches"
Read: [相關文件]
```

### Step 2: 系統化排查 (10-30 分鐘)

使用 **5 Why Analysis**:
1. 為什麼發生這個錯誤?
2. 為什麼會出現這個原因?
3. 為什麼沒有被發現?
4. 為什麼測試沒有覆蓋?
5. 根本原因是什麼?

### Step 3: 修復問題 (10-20 分鐘)

```bash
# 修復
Edit: [修改文件]

# 驗證
Bash: pnpm typecheck
Bash: pnpm lint
Bash: pnpm test

# 手動測試
Bash: pnpm dev (驗證修復)
```

### Step 4: 記錄修復 (5 分鐘)

```bash
Write: claudedocs/4-changes/bug-fixes/FIX-XXX-[描述].md
```

---

## 📝 FIX 文檔模板

```markdown
# FIX-XXX: [Bug 簡述]

## 問題描述
[詳細描述問題，包括復現步驟]

## 根本原因
[分析根本原因 - 5 Why Analysis]

## 解決方案
[描述解決方案]

## 影響範圍
### 修改文件
- `文件路徑` - [變更說明]

### 測試驗證
- ✅ [測試項目 1]
- ✅ [測試項目 2]

## 預防措施
[如何防止類似問題再次發生]

## 相關 Issue/Commit
- Issue: #XXX
- Commit: [commit hash]
```

---

## ✅ 驗收標準

- [ ] 根本原因已識別
- [ ] 修復已實作並驗證
- [ ] 測試已更新
- [ ] FIX 文檔已創建
- [ ] Git 提交訊息清楚

---

**維護者**: AI 助手團隊
**最後更新**: 2025-11-08
