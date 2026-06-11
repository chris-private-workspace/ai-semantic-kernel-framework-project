# PROMPT-06: PROGRESS SAVE
# 進度保存與狀態同步

> **用途**: 保存開發進度、提交代碼、生成工作記錄
> **變數**: `{TASK_ID}` (可選)
> **預估時間**: 5-10 分鐘
> **版本**: v3.0.0

---

## 📋 執行目標

完成以下任務:
1. 檢查和提交代碼變更
2. 生成任務進度報告 (可選)
3. 執行 Git 標準工作流程
4. 生成 Session 工作摘要
5. 確保文檔一致性

---

## 🔤 變數定義

```yaml
{TASK_ID}:
  描述: 任務標識符 (可選)
  格式: 自由格式
  範例:
    - "add-user-profile-api"
    - "fix-login-redirect"
    - 不提供時，僅保存當前工作進度
```

---

## 🎯 執行步驟

### Step 1: 檢查當前狀態

```yaml
檢查項:
  1. Git 狀態:
     → git status
     → git diff

  2. 確認修改的文件
  3. 確認未追蹤的文件
  4. 確認當前分支

提取信息:
  - 修改的文件清單
  - 新增的文件清單
  - 當前分支名稱
  - 是否有未提交的更改
```

### Step 2: 執行 Git 標準工作流程

```yaml
任務: Git 提交流程

步驟:
  1. 檢查 Git 狀態:
     → git status

  2. 添加文件:
     → git add .
     (或選擇性添加特定文件)

  3. 生成 Commit Message:
     格式: {TYPE}({SCOPE}): {DESCRIPTION}

     TYPE 選擇:
       - feat: 新功能實現
       - fix: Bug 修復
       - docs: 文檔更新
       - refactor: 代碼重構
       - test: 測試相關
       - chore: 構建/配置

     SCOPE: 模組名稱 (如 agent, workflow, frontend)

     DESCRIPTION 範例:
       - "add user profile API endpoints"
       - "fix login redirect issue"
       - "update architecture documentation"

  4. 提交:
     → git commit -m "{COMMIT_MESSAGE}

     🤖 Generated with Claude Code
     Co-Authored-By: Claude <noreply@anthropic.com>"

  5. (可選) 推送:
     → git push origin {BRANCH}

輸出:
---
✅ Git 提交完成

Branch: {BRANCH_NAME}
Commit: {COMMIT_HASH}
Message: {COMMIT_MESSAGE}

Modified Files:
- {FILE_1}
- {FILE_2}
- ...

(可選) Pushed to: origin/{BRANCH}
---
```

### Step 3: 生成任務進度報告 (可選)

```yaml
如果提供了 {TASK_ID}:
  任務: 創建任務進度報告

  報告內容:
    1. 任務基本信息
    2. 完成的功能清單
    3. 技術實現要點
    4. 測試覆蓋情況
    5. 遇到的問題和解決方案
    6. 修改的文件清單
    7. 下一步行動項
```

### Step 4: 生成 Session 摘要

```yaml
任務: 生成工作 Session 摘要

摘要內容:
  1. 工作時段信息
  2. 完成的工作清單
  3. 修改的文件清單
  4. Git 提交記錄
  5. 遇到的問題和解決方案
  6. 下次工作待辦事項
```

### Step 5: 文檔一致性檢查

```yaml
檢查項目:
  1. bmm-workflow-status.yaml 是否需要更新
  2. CLAUDE.md 是否需要更新
  3. 相關技術文檔是否需要更新
  4. README.md 是否需要更新

輸出:
---
📋 文檔一致性檢查

✅ bmm-workflow-status.yaml (正常)
✅ CLAUDE.md (正常)
⚠️ 需要更新:
  - 技術架構文檔需要添加新 API 說明

建議操作:
1. 更新 technical-architecture.md 添加新 API 說明
---
```

---

## 📤 輸出格式

### 任務進度報告範本

```markdown
# 任務進度報告: {TASK_ID}

**生成時間**: {TIMESTAMP}
**生成者**: AI Assistant (PROMPT-06)

---

## 📊 基本信息

| 項目 | 內容 |
|------|------|
| **任務 ID** | {TASK_ID} |
| **任務類型** | {TASK_TYPE} |
| **完成日期** | {COMPLETION_DATE} |
| **狀態** | {STATUS} |

---

## ✅ 完成的功能

1. {FEATURE_1}
   - {DETAIL_1_1}
   - {DETAIL_1_2}

2. {FEATURE_2}
   - {DETAIL_2_1}
   - {DETAIL_2_2}

---

## 🔧 技術實現要點

### 核心實現

**{COMPONENT_1}**:
- 技術選型: {TECH_STACK}
- 實現方式: {IMPLEMENTATION_APPROACH}
- 關鍵代碼: `{FILE_PATH}:{LINE_NUMBER}`

### 技術決策

1. **決策**: {DECISION_1}
   - 原因: {REASON}
   - 影響: {IMPACT}

---

## 🧪 測試覆蓋

### 單元測試
- [x] {TEST_CASE_1}
- [x] {TEST_CASE_2}

### 集成測試
- [x] {INTEGRATION_TEST_1}

**測試覆蓋率**: {COVERAGE_PERCENTAGE}%

---

## ⚠️ 遇到的問題

### 問題 1: {PROBLEM_1_TITLE}

**描述**: {PROBLEM_DESCRIPTION}
**原因**: {ROOT_CAUSE}
**解決方案**: {SOLUTION}

---

## 📝 修改的文件

### 新增文件
```
{NEW_FILE_1}
{NEW_FILE_2}
```

### 修改文件
```
{MODIFIED_FILE_1}
{MODIFIED_FILE_2}
```

---

## 📋 下一步行動

- [ ] {ACTION_ITEM_1}
- [ ] {ACTION_ITEM_2}
- [ ] {ACTION_ITEM_3}

---

**報告生成**: PROMPT-06
**版本**: v3.0.0
```

---

### Session 摘要範本

```markdown
# Work Session 摘要: {DATE}

**生成時間**: {TIMESTAMP}
**生成者**: AI Assistant (PROMPT-06)

---

## ⏱️ 工作時段

| 項目 | 時間 |
|------|------|
| **日期** | {DATE} |
| **工作時長** | {DURATION} 小時 |

---

## ✅ 完成的工作

1. ✅ {TASK_1}
   - {SUBTASK_1_1}
   - {SUBTASK_1_2}

2. ✅ {TASK_2}
   - {SUBTASK_2_1}

---

## 📁 修改的文件

### 代碼文件
```
{CODE_FILE_1}
{CODE_FILE_2}
```

### 配置/文檔文件
```
{CONFIG_FILE_1}
{DOC_FILE_1}
```

---

## 💾 Git 提交記錄

```
{COMMIT_HASH_1} - {COMMIT_MESSAGE_1}
{COMMIT_HASH_2} - {COMMIT_MESSAGE_2}
```

**Branch**: {BRANCH_NAME}
**Pushed**: {YES/NO}

---

## ⚠️ 遇到的問題

### 問題 1: {PROBLEM_TITLE}

**現象**: {SYMPTOM}
**原因**: {ROOT_CAUSE}
**解決**: {SOLUTION}

---

## 🔄 下次工作待辦

**P0 - 緊急**:
- [ ] {TODO_P0_1}

**P1 - 高**:
- [ ] {TODO_P1_1}
- [ ] {TODO_P1_2}

**P2 - 中**:
- [ ] {TODO_P2_1}

---

**生成工具**: PROMPT-06
**版本**: v3.0.0
```

---

## 💡 使用範例

### 範例 1: 保存任務進度

```bash
場景: 完成任務，需要保存進度

用戶輸入:
"@PROMPT-06-PROGRESS-SAVE.md add-user-profile-api"

AI 執行步驟:
1. 檢查 Git 狀態
2. 提交代碼變更
3. 生成任務進度報告
4. 生成 Session 摘要
5. 文檔一致性檢查

輸出:
---
✅ 進度保存完成

任務: add-user-profile-api
狀態: 已完成

💾 Git 提交:
- Commit: feat(users): add user profile API endpoints
- Branch: feature/add-user-profile-api
- Pushed: Yes

📄 報告已生成

📋 文檔檢查:
✅ 所有文檔同步正常

⏭️ 下一步建議:
- 開始下一個任務
- 或執行 @PROMPT-09-SESSION-END.md 結束工作
---
```

---

### 範例 2: 快速保存 (無任務 ID)

```bash
場景: 臨時保存工作進度

用戶輸入:
"@PROMPT-06-PROGRESS-SAVE.md"

AI 執行:
1. 檢查 Git 狀態
2. 提交代碼 (WIP commit)
3. 生成簡化 Session 摘要

輸出:
---
✅ 進度保存完成 (快速模式)

💾 Git 提交:
- Commit: wip: save current work progress
- Branch: feature/current-work
- Files: 5 modified, 2 new

📋 Session 摘要已記錄

⏭️ 下次繼續時:
- 查看 Session 摘要了解進度
- 繼續當前任務
---
```

---

## 🔗 整合的 Instructions

此 Prompt 整合並執行以下 Instructions:

- **Instruction 3**: Git 標準工作流程
- **Instruction 5**: 生成 Session 摘要
- **Instruction 6**: 文檔一致性檢查 (可選)

---

## ⚠️ 注意事項

### Git 衝突處理

如果遇到 Git 衝突:
1. 暫停 Prompt 執行
2. 提示用戶解決衝突
3. 等待用戶確認後繼續

### 任務狀態判斷

```yaml
如果任務 100% 完成:
  - 生成完整任務報告
  - 建議開始下一個任務

如果任務部分完成:
  - 生成簡化的進度摘要
  - Git commit 使用 "wip" 前綴
  - 記錄下次繼續點

如果遇到阻塞:
  - 記錄阻塞原因
  - 建議下一步行動
```

---

## 📚 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md)
- [Prompts README](./README.md)
- [PROMPT-04: Development](./PROMPT-04-SPRINT-DEVELOPMENT.md)
- [PROMPT-09: Session End](./PROMPT-09-SESSION-END.md)

---

**版本**: v3.0.0
**更新日期**: 2025-12-01
**維護者**: AI Assistant Team
