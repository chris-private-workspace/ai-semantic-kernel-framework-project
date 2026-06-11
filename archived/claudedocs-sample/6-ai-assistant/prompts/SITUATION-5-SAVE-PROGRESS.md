# 💾 情況5: 保存現有進度

> **使用時機**: 對話進行中，需要保存當前工作進度
> **目標**: 完整記錄進度、更新文檔、同步 GitHub
> **適用場景**: 結束工作前、里程碑達成、定期檢查點

---

## 📋 Prompt 模板

```markdown
我需要保存當前的工作進度。

當前狀態: [開發功能中 / 規劃中 / 修復進行中 / 測試中]
工作內容: [簡述當前正在做什麼]

請幫我:

1. 更新進度記錄
   - 更新 `claudedocs/3-progress/weekly/2025-WXX.md` (本週進度)
   - 更新 `claudedocs/3-progress/daily/YYYY-MM-DD.md` (每日日誌)
   - 如有進行中功能，更新 `claudedocs/1-planning/features/FEAT-XXX/04-progress.md`

2. 更新任務狀態
   - 檢查 TodoWrite 任務清單
   - 標記已完成的任務
   - 添加新發現的任務

3. 執行索引維護
   - 運行 `npm run index:check` 檢查文件同步
   - 手動檢查 `PROJECT-INDEX.md` 是否需要更新

4. 檢查代碼品質
   - 運行 `npm run type-check` (TypeScript 檢查)
   - 運行 `npm run lint` (ESLint 檢查)

5. Git 提交和推送
   - 檢查 `git status` 確認變更
   - 使用有意義的 commit message
   - 執行 `git push origin main` (或當前分支)

6. 生成進度摘要
   - 總結今日/本週完成的工作
   - 列出遇到的挑戰和解決方案
   - 記錄下次需要繼續的工作

請用中文完成所有步驟。
```

---

## 🤖 AI 執行流程

### Step 1: 更新進度記錄 (5 分鐘)

```bash
# 1. 檢查是否存在本週進度文件
Bash: ls claudedocs/3-progress/weekly/

# 2. 如果不存在，創建新文件
Write: claudedocs/3-progress/weekly/2025-WXX.md

# 3. 更新功能進度（如有進行中功能）
Edit: claudedocs/1-planning/features/FEAT-XXX/04-progress.md
```

**每週進度模板**:
```markdown
# 2025-WXX 每週進度 (MM月DD日 - MM月DD日)

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

## 功能開發進度

### FEAT-XXX: [功能名稱]
- **狀態**: 📋 設計中 / 🚧 開發中 / ✅ 完成
- **Phase**: [當前 Phase]
- **完成項目**: [列出]

### FIX-XXX: [Bug 名稱]（如有）
- **狀態**: 🔴 待修復 / 🟡 修復中 / ✅ 已修復
- **影響範圍**: [描述]

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

## 統計數據
- **代碼行數**: +XXX / -XXX
- **文件變更**: XX 個
- **Commits**: XX 次

---
*最後更新: YYYY-MM-DD*
```

---

### Step 2: 更新任務狀態 (3 分鐘)

```bash
# 1. 檢查當前 TodoWrite 狀態
# (AI 助手內部檢查)

# 2. 更新 TodoWrite
TodoWrite: [更新所有任務狀態]

# 3. 如有進行中功能，更新功能進度文件
Edit: claudedocs/1-planning/features/FEAT-XXX/04-progress.md
```

---

### Step 3: 執行索引維護 (3 分鐘)

```bash
# 1. 快速檢查索引同步
Bash: npm run index:check

# 2. 手動檢查 PROJECT-INDEX.md
Read: PROJECT-INDEX.md (檢查最後更新時間)

# 3. 如果需要，手動更新
Edit: PROJECT-INDEX.md (更新時間戳和新文件)

# 4. 如有新功能完成，更新 AI 助手指引
Edit: claudedocs/6-ai-assistant/AI-ASSISTANT-GUIDE.md (如需要)
```

---

### Step 4: 檢查代碼品質 (3 分鐘)

```bash
# 1. TypeScript 檢查
Bash: npm run type-check

# 2. ESLint 檢查
Bash: npm run lint

# 3. 如果有錯誤，記錄問題
# (不一定要立即修復，但要記錄)
```

**品質檢查結果記錄**:
```markdown
## 代碼品質

### TypeScript
- 狀態: ✅ 通過 / ❌ 有錯誤
- 錯誤數: [X]

### ESLint
- 狀態: ✅ 通過 / ❌ 有警告
- 警告數: [X]
```

---

### Step 5: Git 提交和推送 (5 分鐘)

```bash
# 1. 檢查 Git 狀態
Bash: git status

# 2. 查看變更內容
Bash: git diff --stat

# 3. 添加文件
Bash: git add .

# 4. 提交 (使用 HEREDOC 格式)
Bash: git commit -m "$(cat <<'EOF'
type(scope): 簡短描述 (不超過 50 字)

詳細描述:
- 變更 1
- 變更 2
- 變更 3

功能追蹤:
- FEAT-XXX 開發中 / 已完成
- FIX-XXX 已修復

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 5. 推送到 GitHub
Bash: git push origin main

# 6. 確認推送成功
Bash: git log --oneline -1
```

**Commit Message 規範**:
```
<type>(<scope>): <subject>

[body - optional]

[footer - optional]

Types:
- feat: 新功能
- fix: Bug 修復
- docs: 文檔更新
- style: 代碼格式
- refactor: 重構
- test: 測試
- chore: 構建/工具
```

---

### Step 6: 生成進度摘要 (5 分鐘)

**進度摘要模板**:
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

### 功能開發狀態
| 功能 | 狀態 | 當前 Phase |
|------|------|------------|
| FEAT-XXX: [名稱] | 🚧 開發中 | Phase 2 |
| FIX-XXX: [名稱] | ✅ 已修復 | - |

### 代碼變更
- **新增文件**: XX 個
  - `file1.ts` - [用途]
  - `file2.tsx` - [用途]
- **修改文件**: XX 個
  - `file3.ts` - [變更內容]
- **刪除文件**: XX 個

### 測試狀態
- TypeScript: ✅ 通過
- ESLint: ✅ 通過

## 遇到的挑戰

### 挑戰 1: [描述]
- **問題**: [具體問題]
- **嘗試方案**: [方案 1], [方案 2]
- **最終解決**: [成功方案]
- **學習**: [經驗總結]

## 技術決策
- **決策**: [決策描述]
- **選項**: A) [選項A], B) [選項B]
- **選擇**: [選擇的方案]
- **理由**: [為什麼選擇]

## 下次繼續工作

### 待完成任務
- [ ] [任務 1] - [詳細說明]
- [ ] [任務 2] - [詳細說明]

### 前置準備
- [ ] [準備 1]
- [ ] [準備 2]

### 參考資料
- [文檔 1]: `path/to/doc1.md`
- [文檔 2]: `path/to/doc2.md`

## 風險提示
- ⚠️ [風險 1] - [影響] - [建議措施]
- ⚠️ [風險 2] - [影響] - [建議措施]

## Git 狀態
- **Branch**: main
- **Last Commit**: [commit hash]
- **Commit Message**: [message]
- **Pushed**: ✅ 已推送到 GitHub

## 文檔更新
- ✅ 每週進度報告已更新
- ✅ 功能進度文件已更新（FEAT-XXX/04-progress.md）
- ✅ PROJECT-INDEX.md 已檢查/更新

## 下次開始前
**快速恢復指引**:
1. 閱讀本摘要
2. 閱讀 `claudedocs/3-progress/weekly/2025-WXX.md`
3. 檢查 TodoWrite 任務清單
4. 運行 `npm run dev` 啟動開發環境
5. 繼續 [下次要做的具體任務]
```

---

## 📁 文檔記錄位置

```
claudedocs/
├── 1-planning/
│   └── features/
│       └── FEAT-XXX-功能名稱/
│           └── 04-progress.md     # 功能開發進度
├── 3-progress/
│   ├── daily/                     # 日報
│   │   └── YYYY-MM-DD.md
│   └── weekly/                    # 週報
│       └── YYYY-WXX.md
└── 4-changes/
    ├── bug-fixes/                 # Bug 修復記錄
    │   └── FIX-XXX-描述.md
    └── feature-changes/           # 功能變更記錄
        └── CHANGE-XXX-描述.md
```

---

## 🔄 定期保存頻率建議

| 情況 | 時機 | 執行步驟 | 預估時間 |
|------|------|----------|----------|
| **每日保存** | 每天工作結束前 | Step 1-6 快速執行 | 15-20 分鐘 |
| **每週保存** | 每週五下午 | Step 1-6 完整執行 | 25-30 分鐘 |
| **里程碑保存** | 功能完成時 | Step 1-6 + 更新 CLAUDE.md | 30-45 分鐘 |
| **緊急保存** | 長時間未保存 | Step 1, 5 快速保存 | 5-10 分鐘 |

---

## 📱 快速保存 (簡化版)

**給開發人員的快速 Prompt**:

```markdown
快速保存進度:
1. 更新本週進度
2. Git 提交和推送
3. 生成簡短摘要

當前工作: [一句話描述]
```

**AI 快速執行**:
```bash
# 1. 快速保存代碼變更
git add .
git stash save "WIP: [當前工作描述]"

# 或直接提交
git add .
git commit -m "wip: [當前工作描述] - 進度保存"

# 2. 推送到遠端
git push origin main
```

---

## ✅ 驗收標準

保存進度完成後，應該確認：

### 文檔更新
- [ ] 每週進度報告存在且最新
- [ ] 功能進度文件已更新（如有進行中功能）
- [ ] PROJECT-INDEX.md 時間戳更新

### 代碼品質
- [ ] TypeScript 檢查通過
- [ ] ESLint 檢查通過（或記錄已知問題）

### Git 狀態
- [ ] 所有變更已提交
- [ ] Commit message 清晰有意義
- [ ] 已推送到 GitHub
- [ ] 無未追蹤的重要文件

### 進度摘要
- [ ] 生成完整的進度摘要
- [ ] 記錄所有挑戰和解決方案
- [ ] 列出下次繼續工作的清單
- [ ] 標註風險和注意事項

---

## 🔗 相關文檔

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md)
- [情況2: 開發前準備](./SITUATION-2-FEATURE-DEV-PREP.md)
- [情況3: 舊功能進階/修正](./SITUATION-3-FEATURE-ENHANCEMENT.md)
- [情況4: 新功能開發](./SITUATION-4-NEW-FEATURE-DEV.md)

### 開發規範
- [CLAUDE.md](../../../CLAUDE.md) - 開發規範
- [PROJECT-INDEX.md](../../../PROJECT-INDEX.md) - 項目索引
- [技術障礙處理](../../../.claude/rules/technical-obstacles.md)

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2026-01-18
**版本**: 1.2
