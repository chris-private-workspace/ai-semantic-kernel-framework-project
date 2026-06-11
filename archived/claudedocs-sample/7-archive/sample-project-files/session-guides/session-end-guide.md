# AI Assistant Session 結束指引

> 本指引用於每次 AI 助手 Session 結束時的標準流程

---

## Session 結束檢查清單

### 1. 任務完成確認
- [ ] 所有 TodoWrite 任務已更新狀態
- [ ] 進行中的任務已記錄進度
- [ ] 未完成任務已標註原因

### 2. 變更記錄
- [ ] 所有 Bug 修復已記錄到 `claudedocs/4-changes/bug-fixes/`
- [ ] 所有功能變更已記錄到 `claudedocs/4-changes/feature-changes/`
- [ ] 重構工作已記錄到 `claudedocs/4-changes/refactoring/`

### 3. 進度更新
- [ ] 更新日報 `claudedocs/3-progress/daily/YYYY-MM-DD.md`
- [ ] 更新 Sprint 狀態（如適用）
- [ ] 記錄任何阻礙或風險

### 4. 程式碼品質
- [ ] `npm run type-check` 通過
- [ ] `npm run lint` 通過
- [ ] 無未處理的錯誤

### 5. Git 狀態
- [ ] 所有變更已 commit（如適用）
- [ ] Commit message 符合規範
- [ ] 無未追蹤的重要檔案

---

## Session 總結模板

```markdown
## Session 總結 - SESSION-YYYYMMDD-XX

### 完成項目
1. 項目 1
2. 項目 2

### 未完成項目
1. 項目 1 - 原因：___

### 遇到的問題
1. 問題 1 - 解決方案：___

### 下次 Session 建議
1. 建議 1
2. 建議 2

### Session 統計
- 開始時間：HH:MM
- 結束時間：HH:MM
- 總時長：X 小時
```

---

## 交接文件

如果任務需要延續到下一個 Session，請建立交接文件：

路徑：`claudedocs/6-ai-assistant/handoff/`

命名：`HANDOFF-YYYYMMDD-description.md`

---

## 緊急情況處理

### 如果 Session 突然中斷
1. 記錄最後的工作狀態
2. 保存任何未 commit 的變更
3. 建立交接文件說明中斷點

### 如果發現嚴重問題
1. 立即記錄問題
2. 評估是否需要回滾
3. 通知相關人員

---

*指引版本：1.0*
*最後更新：2025-12-21*
