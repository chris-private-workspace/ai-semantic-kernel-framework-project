# PROMPT-09: SESSION END
# 工作 Session 結束

> **用途**: 工作 Session 結束時的檢查和總結
> **變數**: 無
> **預估時間**: 3-5 分鐘
> **版本**: v3.0.0

---

## 🎯 執行目標

完成以下任務:
1. 生成 Session 工作摘要
2. 檢查未保存的更改
3. 驗證文檔一致性
4. 創建下次工作待辦清單
5. 保存 Session 記錄

---

## 🎯 執行步驟

### Step 1: 檢查 Git 狀態

```yaml
執行命令:
  git status

檢查項:
  - 是否有未提交的更改
  - 是否有未追蹤的文件
  - 當前分支名稱
  - 與遠端的同步狀態

如果有未提交更改:
  ⚠️ 警告用戶保存工作
  建議: 執行 Instruction 8 (快速同步) 或 PROMPT-06
```

### Step 2: 總結本次 Session

```yaml
回顧本次 Session:
  - 工作時段 (開始時間 → 結束時間)
  - 完成的任務清單
  - 修改的文件清單
  - Git 提交記錄
  - 遇到的問題和解決方案
```

### Step 3: 執行 Instruction 6 (文檔一致性檢查)

```yaml
檢查項:
  - sprint-status.yaml 是否已更新
  - bmm-workflow-status.yaml 是否需要更新
  - Sprint 計劃文檔是否同步
  - Session 日誌是否已記錄

輸出一致性檢查結果
```

### Step 4: 創建下次工作待辦清單

```yaml
待辦事項分類:
  P0 - 緊急:
    - 阻塞當前進度的問題
    - Critical Bug 修復

  P1 - 高優先級:
    - 當前 Sprint 的 Story
    - 重要的技術債務

  P2 - 中優先級:
    - 文檔更新
    - 代碼優化

  P3 - 低優先級:
    - 探索性任務
    - 學習和研究
```

### Step 5: 生成並保存 Session 摘要

```yaml
文件路徑:
  claudedocs/session-logs/session-{DATE}.md

摘要內容:
  - Session 基本信息
  - 完成的工作
  - 修改的文件
  - Git 提交
  - 遇到的問題
  - 下次工作待辦
  - 備註
```

---

## 📤 輸出格式

```markdown
# Session 結束報告: {DATE}

**生成時間**: {TIMESTAMP}
**生成者**: AI Assistant (PROMPT-09)

---

## ⏱️ Session 信息

| 項目 | 內容 |
|------|------|
| **日期** | {DATE} |
| **開始時間** | {START_TIME} |
| **結束時間** | {END_TIME} |
| **工作時長** | {DURATION} 小時 |
| **當前 Sprint** | {SPRINT_ID} |

---

## ✅ 完成的工作

### 主要任務
1. ✅ {TASK_1}
   - {DETAIL_1_1}
   - {DETAIL_1_2}

2. ✅ {TASK_2}
   - {DETAIL_2_1}

3. ✅ {TASK_3}

### Story 進度
| Story ID | 標題 | 原狀態 | 新狀態 | 完成度 |
|----------|------|--------|--------|--------|
| {STORY_ID_1} | {TITLE_1} | {OLD_STATUS} | {NEW_STATUS} | {PROGRESS}% |
| {STORY_ID_2} | {TITLE_2} | {OLD_STATUS} | {NEW_STATUS} | {PROGRESS}% |

---

## 📁 修改的文件

### 代碼文件 ({CODE_FILE_COUNT} 個)
```
{CODE_FILE_1}
{CODE_FILE_2}
{CODE_FILE_3}
...
```

### 配置文件 ({CONFIG_FILE_COUNT} 個)
```
{CONFIG_FILE_1}
{CONFIG_FILE_2}
```

### 文檔文件 ({DOC_FILE_COUNT} 個)
```
{DOC_FILE_1}
{DOC_FILE_2}
```

---

## 💾 Git 提交記錄

```
{COMMIT_HASH_1} - {COMMIT_MESSAGE_1}
{COMMIT_HASH_2} - {COMMIT_MESSAGE_2}
{COMMIT_HASH_3} - {COMMIT_MESSAGE_3}
```

**當前分支**: {BRANCH_NAME}
**推送狀態**: {PUSHED_STATUS} (✅ Pushed / ⚠️ Not Pushed)

---

## ⚠️ Git 狀態檢查

{GIT_STATUS_CHECK_RESULT}

### 未提交的更改
{UNCOMMITTED_CHANGES}

### 未追蹤的文件
{UNTRACKED_FILES}

### 建議
{RECOMMENDATIONS}

---

## ⚠️ 遇到的問題

### 問題 1: {PROBLEM_TITLE}
**描述**: {PROBLEM_DESCRIPTION}
**影響**: {IMPACT}
**解決方案**: {SOLUTION}
**狀態**: {STATUS} (✅ 已解決 / ⏳ 進行中 / ❌ 未解決)

---

## 📋 文檔一致性檢查

{DOCUMENT_CONSISTENCY_CHECK}

### 檢查結果
- ✅ sprint-status.yaml: {STATUS}
- ✅ bmm-workflow-status.yaml: {STATUS}
- ⚠️ 需要更新: {ITEMS_TO_UPDATE}

---

## 📊 Session 統計

| 指標 | 數值 |
|------|------|
| **編碼時間** | {CODING_TIME} 小時 |
| **測試時間** | {TESTING_TIME} 小時 |
| **調試時間** | {DEBUGGING_TIME} 小時 |
| **文檔時間** | {DOCUMENTATION_TIME} 小時 |
| **新增代碼行數** | {LINES_ADDED} |
| **刪除代碼行數** | {LINES_DELETED} |
| **Git 提交數** | {COMMIT_COUNT} |

---

## 🔄 下次工作待辦

### P0 - 緊急 (必須完成)
- [ ] {TODO_P0_1}
- [ ] {TODO_P0_2}

### P1 - 高優先級 (本 Sprint)
- [ ] {TODO_P1_1}
- [ ] {TODO_P1_2}
- [ ] {TODO_P1_3}

### P2 - 中優先級 (下個 Sprint)
- [ ] {TODO_P2_1}
- [ ] {TODO_P2_2}

### P3 - 低優先級 (技術債務)
- [ ] {TODO_P3_1}

---

## 💭 Session 備註

### 技術決策
- {TECH_DECISION_NOTE}

### 學習心得
- {LEARNING_NOTE}

### 團隊溝通
- {TEAM_COMMUNICATION_NOTE}

### 其他備註
- {OTHER_NOTES}

---

## 🚀 下次 Session 準備

### 環境準備
- [ ] {ENV_PREP_1}
- [ ] {ENV_PREP_2}

### 文檔準備
- [ ] {DOC_PREP_1}
- [ ] {DOC_PREP_2}

### 建議的下次 Session 目標
{NEXT_SESSION_GOAL}

---

## 📚 相關資源

- [Sprint Status](../../docs/03-implementation/sprint-status.yaml)
- [BMAD Workflow Status](../../docs/bmm-workflow-status.yaml)
- [今日 Sprint 報告](../sprint-reports/) (如有)

---

**Session 結束時間**: {END_TIMESTAMP}
**下次 Session**: {NEXT_SESSION_DATE}
**生成工具**: PROMPT-09
**版本**: v2.0.0
```

---

## ⚠️ Session 結束檢查清單

在結束 Session 前,確保完成:

### Git 檢查
- [ ] 所有重要更改已提交
- [ ] Commit message 符合規範
- [ ] (可選) 已推送到遠端
- [ ] 無敏感信息在 Git 中

### 文檔檢查
- [ ] sprint-status.yaml 已更新
- [ ] Session 摘要已生成
- [ ] 重要決策已記錄

### 工作狀態
- [ ] 當前任務狀態已記錄
- [ ] 下次工作待辦已列出
- [ ] 已知問題已記錄

### 環境檢查
- [ ] 本地環境可正常運行
- [ ] 測試通過
- [ ] 無阻塞問題

---

## 💡 使用範例

```bash
# 結束工作 Session
用戶: "@PROMPT-09-SESSION-END.md"

AI 執行:
1. 檢查 Git 狀態
2. 總結本次 Session 工作
3. 執行文檔一致性檢查
4. 創建下次工作待辦
5. 生成並保存 Session 摘要

輸出:
---
📋 Session 結束報告

工作時長: 3.5 小時
完成任務: 3 個
Git 提交: 2 個

✅ 檢查完成:
- 所有更改已提交
- 文檔已同步
- 下次待辦已創建

⚠️ 注意事項:
- 有 1 個 P0 待辦需要下次優先處理
- Story S0-2 進度 60%,建議下次完成

Session 摘要已保存:
claudedocs/session-logs/session-2025-11-20.md

下次見! 👋
---
```

---

## 🔗 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md)
- [PROMPT-06: Progress Save](./PROMPT-06-PROGRESS-SAVE.md)
- [Instruction 6: 文檔一致性檢查](../AI-ASSISTANT-INSTRUCTIONS.md#instruction-6)

---

**版本**: v3.0.0
**更新日期**: 2025-12-01
**維護者**: AI Assistant Team

---

## 📝 強制執行策略

**重要**: 此 Prompt 應該在每個工作 Session 結束時強制執行,以確保:
- 工作進度不丟失
- 文檔保持同步
- 下次工作能夠順利開始
- 團隊成員了解最新狀態
