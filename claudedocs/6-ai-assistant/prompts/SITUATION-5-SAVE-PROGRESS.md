# 💾 情況5: 保存現有進度

> **使用時機**: 對話進行中，需要保存當前工作進度
> **目標**: 完整記錄進度，更新文檔，同步 GitHub
> **適用場景**: 結束工作前, 里程碑達成, 定期檢查點

---

## 📋 Prompt 模板

```markdown
我需要保存當前的工作進度。

當前狀態: [開發功能中 / 規劃中 / 修復進行中 / 測試中]
工作內容: [簡述當前正在做什麼]

請幫我完成以下步驟:

1. 更新進度記錄
   - 更新 `claudedocs/3-progress/weekly/2025-WXX.md` (本週進度)
   - 更新 `DEVELOPMENT-LOG.md` (如有)

2. 更新任務狀態
   - 檢查 TodoWrite 任務清單
   - 標記已完成的任務
   - 添加新發現的任務

3. 檢查代碼品質
   - 運行 pytest (測試)
   - 運行 black/isort (格式化)
   - 運行 flake8 (lint)

4. Git 提交和推送
   - 檢查 git status 確認變更
   - 使用有意義的 commit message
   - 執行 git push

5. 生成進度摘要
   - 總結完成的工作
   - 記錄下次需要繼續的工作

請用中文完成所有步驟。
```

---

## 🤖 AI 執行流程

### Step 1: 更新進度記錄 (3 分鐘)

```bash
# 1. 檢查是否存在本週進度文件
Bash: ls claudedocs/3-progress/weekly/

# 2. 如果不存在，創建新文件
Write: claudedocs/3-progress/weekly/2025-WXX.md
```

**每週進度模板**:
```markdown
# 2025-WXX 每週進度 (X月X日 - X月X日)

## 本週目標
- [列出本週計劃完成的目標]

## 完成情況
### 已完成
- ✅ [任務 1] - [簡述]
- ✅ [任務 2] - [簡述]

### 進行中
- ⏳ [任務 3] - [進度 XX%]

### 未開始
- ⏸️ [任務 4] - [原因]

## 遇到的挑戰
### 挑戰 1: [描述]
- **問題**: [詳細說明]
- **解決方案**: [如何解決]
- **學習**: [經驗總結]

## 技術決策
- **決策 1**: [描述] → [選擇的方案] → [理由]

## 下週計劃
- [ ] [任務 1]
- [ ] [任務 2]

## 風險提示
- ⚠️ [風險 1] - [緩解措施]
```

### Step 2: 更新任務狀態 (2 分鐘)

```bash
# 1. 檢查當前 TodoWrite 狀態
# (AI 助手內部檢查)

# 2. 更新 TodoWrite
TodoWrite: [更新所有任務狀態]

# 3. 如果有 Sprint checklist，更新
Edit: archived/docs-v1/03-implementation/sprint-execution/sprint-XX/checklist.md
```

### Step 3: 檢查代碼品質 (3 分鐘)

```bash
# 1. 運行測試
Bash: cd backend && pytest tests/unit/ -v --tb=short

# 2. 格式化代碼
Bash: cd backend && black . && isort .

# 3. Lint 檢查
Bash: cd backend && flake8 src/

# 4. 類型檢查 (可選)
Bash: cd backend && mypy src/
```

### Step 4: Git 提交和推送 (3 分鐘)

```bash
# 1. 檢查 Git 狀態
Bash: git status

# 2. 查看變更內容
Bash: git diff --stat

# 3. 添加文件
Bash: git add .

# 4. 提交 (使用 HEREDOC 格式)
Bash: git commit -m "$(cat <<'EOF'
type(scope): 簡短描述

詳細描述:
- 變更 1
- 變更 2

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 5. 推送到 GitHub
Bash: git push origin main

# 6. 確認推送成功
Bash: git log --oneline -1
```

### Step 5: 生成進度摘要 (3 分鐘)

```markdown
# 📊 進度保存摘要

## 時間
- **日期**: YYYY-MM-DD
- **時間**: HH:MM

## 工作內容
### 本次會話完成
- ✅ [完成項 1] - [詳細說明]
- ✅ [完成項 2] - [詳細說明]
- ⏳ [進行中項目] - [當前狀態]

### 代碼變更
- **新增文件**: XX 個
  - `file1.py` - [用途]
  - `file2.py` - [用途]
- **修改文件**: XX 個
  - `file3.py` - [變更內容]

### 測試狀態
- pytest: ✅ 通過
- black/isort: ✅ 通過
- flake8: ✅ 通過

## 下次繼續工作
### 待完成任務
- [ ] [任務 1] - [詳細說明]
- [ ] [任務 2] - [詳細說明]

## Git 狀態
- **Branch**: main
- **Last Commit**: [commit hash]
- **Pushed**: ✅ 已推送到 GitHub
```

---

## 📝 Commit Message 格式

### 標準格式

```
<type>(<scope>): <description>

[optional body]

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Type 類型

| Type | 使用場景 |
|------|----------|
| `feat` | 新功能 |
| `fix` | Bug 修復 |
| `docs` | 文檔更新 |
| `refactor` | 代碼重構 |
| `test` | 測試相關 |
| `chore` | 雜項維護 |

### 範例

```bash
# 新功能
feat(sessions): Add streaming chat support

# Bug 修復
fix(api): Handle null response in tool execution

# 文檔更新
docs: Update Phase 11 API documentation

# 重構
refactor(domain): Extract session state machine
```

---

## ✅ 驗收標準

保存進度完成後，應該確認:

### 文檔更新
- [ ] 每週進度報告存在且最新
- [ ] TodoWrite 狀態反映實際進度

### 代碼品質
- [ ] pytest 測試通過
- [ ] black/isort 格式化通過
- [ ] flake8 無錯誤

### Git 狀態
- [ ] 所有變更已提交
- [ ] Commit message 清晰有意義
- [ ] 已推送到 GitHub

### 進度摘要
- [ ] 生成完整的進度摘要
- [ ] 列出下次繼續工作的清單

---

## 🔄 定期保存頻率建議

### 每日保存 (推薦)
- **時機**: 每天工作結束前
- **內容**: 快速保存，更新任務狀態
- **時間**: 10-15 分鐘

### 每週保存 (必須)
- **時機**: 每週五下午
- **內容**: 完整保存，生成每週報告
- **時間**: 20-30 分鐘

### 里程碑保存 (重要)
- **時機**: Sprint 結束, Story 完成
- **內容**: 全面保存，生成階段報告
- **時間**: 30-60 分鐘

---

## 📱 快速保存 (簡化版)

**給開發人員的快速 Prompt**:

```markdown
快速保存進度:
1. 運行測試和格式化
2. Git 提交和推送
3. 生成簡短摘要

當前工作: [一句話描述]
```

---

## 🔗 相關文檔

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md)
- [情況2: 開發前準備](./SITUATION-2-FEATURE-DEV-PREP.md)
- [情況3: 舊功能進階/修正](./SITUATION-3-FEATURE-ENHANCEMENT.md)
- [情況4: 新功能開發](./SITUATION-4-NEW-FEATURE-DEV.md)

### Git 規範
- `.claude/rules/git-workflow.md` - Git 工作流程規則

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2025-12-27
**版本**: 2.0
