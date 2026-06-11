# AI Assistant Instructions for IPA Platform
# 智能流程自動化平台 - AI 助手操作指令手冊

> **版本**: v3.0.0
> **專案**: Microsoft Agent Framework Platform (IPA)
> **更新日期**: 2025-12-01
> **適用 AI**: Claude Code, GitHub Copilot, 其他 AI 助手
> **專案階段**: MVP 完成 (285/285 points across 6 Sprints)

---

## 📋 目錄

1. [核心指令清單](#核心指令清單)
2. [快速參考卡](#快速參考卡)
3. [環境變數設定](#環境變數設定)
4. [詳細指令說明](#詳細指令說明)
5. [使用範例](#使用範例)
6. [錯誤處理](#錯誤處理)

---

## 核心指令清單

### 專案管理指令

| 指令 ID | 指令名稱 | 用途 | 預估時間 |
|---------|----------|------|----------|
| **Instruction 1** | 更新專案工作流程狀態 | 更新 BMAD Workflow YAML | 3-5 分鐘 |
| **Instruction 2** | 生成任務完成報告 | 記錄任務完成情況 | 5-8 分鐘 |
| **Instruction 3** | Git 標準工作流程 | 提交代碼到 Git | 2-3 分鐘 |
| **Instruction 4** | 創建 Pull Request | 創建並推送 PR | 3-5 分鐘 |
| **Instruction 5** | 生成 Session 摘要 | 記錄工作 Session | 2-3 分鐘 |

### 質量保證指令

| 指令 ID | 指令名稱 | 用途 | 預估時間 |
|---------|----------|------|----------|
| **Instruction 6** | 文檔一致性檢查 | 檢查文檔同步狀態 | 3-5 分鐘 |
| **Instruction 7** | 完整任務結束流程 | 任務完成所有步驟 | 15-20 分鐘 |
| **Instruction 8** | 快速進度同步 | 快速提交小改動 | 1-2 分鐘 |

### 審查與分析指令

| 指令 ID | 指令名稱 | 用途 | 預估時間 |
|---------|----------|------|----------|
| **Instruction 9** | 架構審查 | 審查技術架構決策 | 10-15 分鐘 |
| **Instruction 10** | 代碼審查 | 審查代碼質量 | 5-10 分鐘 |

### UAT 測試指令

| 指令 ID | 指令名稱 | 用途 | 預估時間 |
|---------|----------|------|----------|
| **Instruction 11** | UAT 會話管理 | 開始/結束 UAT 測試會話 | 5-15 分鐘 |
| **Instruction 12** | UAT 問題記錄 | 記錄 UAT 發現的問題 | 3-5 分鐘 |
| **Instruction 13** | UAT 問題修復 | 修復並驗證 UAT 問題 | 10-30 分鐘 |

---

## 快速參考卡

### 使用場景決策樹

```
問：我該用哪個指令?

├─ 📝 日常快速提交 (小改動, <30分鐘工作)
│  └─ → 使用 Instruction 8 (快速進度同步)
│
├─ 🎯 完成一個開發任務
│  └─ → 使用 Instruction 2 + Instruction 3
│
├─ ✅ 大型功能全部完成
│  └─ → 使用 Instruction 7 (完整結束流程)
│
├─ 🔍 檢查文檔是否同步
│  └─ → 使用 Instruction 6 (文檔一致性檢查)
│
├─ 🚀 準備發 PR
│  └─ → 使用 Instruction 4 (創建 Pull Request)
│
├─ 📊 每日工作結束
│  └─ → 使用 Instruction 5 (生成 Session 摘要)
│
└─ 🧪 UAT 測試
   ├─ 開始測試 → 使用 @PROMPT-10-UAT-SESSION.md start
   ├─ 發現問題 → 使用 @PROMPT-11-UAT-ISSUE.md
   ├─ 修復問題 → 使用 @PROMPT-12-UAT-FIX.md
   └─ 結束測試 → 使用 @PROMPT-10-UAT-SESSION.md end
```

### 組合使用指南

```yaml
日常開發流程:
  1. 開始工作: @PROMPT-04 (Development Execution)
  2. 完成任務: Instruction 2 (生成完成報告)
  3. 提交代碼: Instruction 3 (Git 工作流程)
  4. 結束工作: Instruction 5 (Session 摘要)

大型功能結束流程:
  1. 檢查文檔: Instruction 6 (一致性檢查)
  2. 完整結束: Instruction 7 (完整結束流程)
  3. 創建 PR: Instruction 4 (Pull Request)

UAT 測試流程:
  1. 開始測試: @PROMPT-10-UAT-SESSION.md start {MODULE}
  2. 測試功能: 按 checklist 逐項測試
  3. 記錄問題: @PROMPT-11-UAT-ISSUE.md {MODULE} {DESCRIPTION}
  4. 修復問題: @PROMPT-12-UAT-FIX.md {ISSUE_ID}
  5. 驗證修復: 重新測試確認
  6. 結束測試: @PROMPT-10-UAT-SESSION.md end
```

---

## 環境變數設定

在執行指令前,AI 應自動讀取以下專案配置:

```yaml
# 專案基本信息
PROJECT_NAME: "IPA - Intelligent Process Automation Platform"
PROJECT_PATH: "C:\ai-semantic-kernel-framework-project"
DOCS_PATH: "docs/"
CLAUDEDOCS_PATH: "claudedocs/"

# 工作流程追蹤文件
WORKFLOW_STATUS_FILE: "docs/bmm-workflow-status.yaml"

# 專案狀態 (Phase 6 完成, UAT Ready)
PROJECT_STATUS: "Phase 6 Complete - UAT Ready"
TOTAL_SPRINTS: 6
TOTAL_POINTS: "285/285"
BACKEND_TESTS: 812
API_ROUTES: 155

# Git 配置
GIT_BRANCH_PREFIX: "feature/"
GIT_MAIN_BRANCH: "main"
GIT_REMOTE: "origin"
GITHUB_REPO: "https://github.com/laitim2001/ai-semantic-kernel-framework-project.git"

# 文檔標準
COMMIT_MESSAGE_FORMAT: "type(scope): description"
COMMIT_TYPES: ["feat", "fix", "docs", "refactor", "test", "chore"]
```

---

## 詳細指令說明

### Instruction 1: 更新專案工作流程狀態

**用途**: 更新 `bmm-workflow-status.yaml` 文件,記錄當前專案的工作流程狀態

**執行步驟**:
1. 讀取 `docs/bmm-workflow-status.yaml`
2. 確認當前工作階段和進度
3. 更新以下字段:
   - `updated`: 當前日期時間
   - `current_phase`: 當前工作階段
   - 相關任務狀態
4. 保存文件

**參數**:
- `phase`: 工作階段 (例如: "implementation", "testing")
- `task_id`: 任務標識符 (自由格式)
- `new_status`: 新狀態 ("in-progress", "completed", "blocked")

**使用範例**:
```
用戶: "請使用 Instruction 1 更新狀態,add-caching-feature 任務已完成"
AI: 執行指令,更新 bmm-workflow-status.yaml
```

**輸出格式**:
```yaml
✅ 狀態更新完成

任務: add-caching-feature
狀態: in-progress → completed
更新時間: 2025-12-01 14:30:00
```

---

### Instruction 2: 生成任務完成報告

**用途**: 當完成一個開發任務時,生成完成報告

**執行步驟**:
1. 收集任務完成信息
2. 生成完成報告,包括:
   - 任務基本信息
   - 完成的功能清單
   - 技術實現要點
   - 測試覆蓋情況
   - 遇到的問題和解決方案
3. 將報告保存到 `claudedocs/task-reports/task-{ID}.md`

**參數**:
- `task_id`: 任務標識符 (必需)

**使用範例**:
```
用戶: "請使用 Instruction 2 生成 add-user-profile-api 的完成報告"
```

**輸出模板**:
```markdown
# 任務完成報告: {Task ID}

## 基本信息
- **Task ID**: add-user-profile-api
- **標題**: 新增用戶配置 API
- **負責人**: Backend Team
- **完成日期**: 2025-12-01

## 完成的功能
1. GET /api/v1/users/{id}/profile
2. PUT /api/v1/users/{id}/profile
3. ...

## 技術實現要點
- 使用 Pydantic 進行數據驗證
- 添加 Redis 緩存層
- ...

## 測試覆蓋
- [x] 單元測試
- [x] API 端點測試
- ...

## 問題與解決
### 問題 1: 緩存失效策略
**解決**: ...

## 下一步行動
- [ ] 與前端整合測試
```

---

### Instruction 3: Git 標準工作流程

**用途**: 標準化的 Git commit 流程

**執行步驟**:
1. 檢查 Git 狀態: `git status`
2. 查看未提交的更改: `git diff`
3. 添加文件: `git add .` 或指定文件
4. 生成 commit message (遵循 Conventional Commits)
5. 提交: `git commit -m "message"`
6. (可選) 推送: `git push origin <branch>`

**Commit Message 格式**:
```
<type>(<scope>): <description>

[optional body]

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type 類型**:
- `feat`: 新功能
- `fix`: Bug 修復
- `docs`: 文檔更新
- `refactor`: 代碼重構
- `test`: 測試相關
- `chore`: 構建/工具配置

**使用範例**:
```
用戶: "請使用 Instruction 3 提交代碼,完成用戶配置 API"
AI: 生成 commit: "feat(backend): add user profile API endpoints"
```

---

### Instruction 4: 創建 Pull Request

**用途**: 創建並推送 Pull Request

**執行步驟**:
1. 確認當前分支
2. 確保所有更改已提交
3. 推送到遠端: `git push origin <branch>`
4. 生成 PR 標題和描述
5. 使用 GitHub CLI 創建 PR

**PR 標題格式**:
```
{Feature}: {簡短描述}
```

**PR 描述模板**:
```markdown
## 更改摘要
- 新增用戶配置 API
- 添加緩存層支持
- 創建單元測試

## 測試清單
- [x] 單元測試通過
- [x] API 端點測試
- [x] 本地環境驗證

## 相關文檔
- [技術架構](docs/02-architecture/technical-architecture.md)

## Review 注意事項
- 確認緩存策略是否合適
- 檢查錯誤處理邏輯
```

**使用範例**:
```
用戶: "請使用 Instruction 4 創建 PR,完成用戶配置功能"
```

---

### Instruction 5: 生成 Session 摘要

**用途**: 記錄每個工作 Session 的內容

**執行步驟**:
1. 總結本次 Session 完成的工作
2. 記錄修改的文件清單
3. 記錄遇到的問題和解決方案
4. 列出下次工作的待辦事項
5. 保存到 `claudedocs/session-logs/session-{date}.md`

**使用範例**:
```
用戶: "請使用 Instruction 5 生成 Session 摘要"
```

**輸出模板**:
```markdown
# Work Session 摘要: 2025-12-01

## 工作時段
- **開始時間**: 14:00
- **結束時間**: 17:30
- **工作時長**: 3.5 小時

## 完成的工作
1. ✅ 完成用戶配置 API
2. ✅ 添加 Redis 緩存層
3. ✅ 編寫單元測試

## 修改的文件
- `backend/src/api/v1/users/routes.py` (更新)
- `backend/src/domain/users/service.py` (新增)
- `backend/tests/unit/test_users.py` (新增)

## 遇到的問題
### 問題 1: Redis 連接超時
**原因**: 連接池配置不當
**解決**: 調整連接池參數

## Git 提交記錄
- `feat(backend): add user profile API endpoints`
- `test(backend): add unit tests for user service`

## 下次工作待辦
- [ ] 與前端整合測試
- [ ] 添加 API 文檔
- [ ] 性能優化

## 備註
- Redis 版本需要 >= 7.0
```

---

### Instruction 6: 文檔一致性檢查

**用途**: 檢查關鍵文檔是否保持同步

**執行步驟**:
1. 檢查以下文檔:
   - `bmm-workflow-status.yaml`
   - 計劃文檔
   - README.md
   - CLAUDE.md
2. 驗證數據一致性:
   - 專案狀態是否匹配
   - 任務狀態是否同步
3. 生成檢查報告

**使用範例**:
```
用戶: "請使用 Instruction 6 檢查文檔一致性"
```

**輸出格式**:
```yaml
📋 文檔一致性檢查報告

✅ bmm-workflow-status.yaml
  - 更新時間: 2025-12-01
  - 當前階段: MVP Complete
  - 狀態: 正常

✅ CLAUDE.md
  - 專案狀態: MVP Complete
  - 狀態: 正常

⚠️ 需要更新
  - README.md 未反映最新功能

建議操作:
1. 更新 README.md 添加新功能說明
```

---

### Instruction 7: 完整任務結束流程

**用途**: 大型任務完成時執行所有必要步驟

**執行步驟**:
1. **文檔一致性檢查** (Instruction 6)
2. **生成任務完成報告**:
   - 總結所有完成的功能
   - 記錄技術實現
   - 測試覆蓋情況
3. **更新狀態文件**:
   - 更新 `bmm-workflow-status.yaml`
4. **Git 提交** (Instruction 3)
5. **創建 PR** (Instruction 4) (可選)
6. **生成 Session 摘要** (Instruction 5)

**使用範例**:
```
用戶: "用戶管理功能全部完成,請執行 Instruction 7"
```

**預估時間**: 15-20 分鐘

---

### Instruction 8: 快速進度同步

**用途**: 快速提交小改動,不需要完整流程

**執行步驟**:
1. 檢查 Git 狀態
2. 生成簡短的 commit message
3. 提交並推送

**使用範例**:
```
用戶: "修復了一個小 bug,請快速同步"
AI: 執行 Instruction 8
→ git add .
→ git commit -m "fix: resolve user profile validation issue"
→ git push
```

**預估時間**: 1-2 分鐘

---

### Instruction 9: 架構審查

**用途**: 審查技術架構文檔和決策

**執行步驟**:
1. 讀取 `docs/02-architecture/technical-architecture.md`
2. 審查架構決策:
   - 技術選型合理性
   - 架構模式適用性
   - 可擴展性考慮
   - 安全性考慮
3. 對照 PRD 需求檢查覆蓋度
4. 生成審查報告

**使用範例**:
```
用戶: "請使用 Instruction 9 審查當前架構"
```

**輸出格式**:
```markdown
# 架構審查報告

## 審查範圍
- Technical Architecture
- 審查日期: 2025-12-01

## 架構優勢
✅ 使用 Azure App Service 簡化部署
✅ Agent Framework 原生支持多 Agent 協作
✅ 混合監控方案平衡成本和功能

## 潛在風險
⚠️ Redis 單點故障風險
⚠️ Service Bus 成本可能較高
⚠️ Agent Framework Preview 版本穩定性

## 改進建議
1. 考慮 Redis Cluster 提高可用性
2. 評估 Service Bus 替代方案
3. 準備 Agent Framework 升級計劃
```

---

### Instruction 10: 代碼審查

**用途**: 審查代碼質量和最佳實踐

**執行步驟**:
1. 讀取指定路徑的代碼文件
2. 審查代碼質量:
   - 代碼風格和規範
   - 錯誤處理
   - 安全性問題
   - 性能考慮
   - 測試覆蓋
3. 生成審查建議

**參數**:
- `file_path`: 要審查的文件或目錄路徑

**使用範例**:
```
用戶: "請使用 Instruction 10 審查 backend/src/ 目錄"
```

---

## 使用範例

### 範例 1: 日常開發流程

```
# 場景: 開發者完成了一個小功能

用戶: "我完成了用戶配置 API,請幫我提交"

AI 執行:
1. Instruction 8 (快速進度同步)
   → git add backend/src/api/v1/users/
   → git commit -m "feat(backend): add user profile API endpoints"
   → git push origin feature/user-profile

輸出:
✅ 快速同步完成
提交: feat(backend): add user profile API endpoints
推送: feature/user-profile → origin
```

---

### 範例 2: 任務完成

```
# 場景: 完成一個完整的開發任務

用戶: "用戶配置 API 任務完成了,請執行完整流程"

AI 執行:
1. Instruction 2 (生成完成報告)
   → 創建 task-reports/task-user-profile-api.md

2. Instruction 3 (Git 提交)
   → git commit -m "feat(backend): complete user profile API"

3. Instruction 5 (Session 摘要)
   → 創建 session-logs/session-2025-12-01.md

輸出:
✅ 任務完成流程執行完畢
📄 生成報告: task-reports/task-user-profile-api.md
💾 Git 提交: feat(backend): complete user profile API
📋 Session 摘要: session-logs/session-2025-12-01.md
```

---

### 範例 3: 大型功能全部完成

```
# 場景: 用戶管理模塊的所有功能都完成了

用戶: "用戶管理模塊全部完成,請執行完整結束流程"

AI 執行 Instruction 7:
1. Instruction 6 (文檔一致性檢查)
2. 生成功能完成報告
3. 更新 bmm-workflow-status.yaml
4. Instruction 3 (Git 提交)
5. Instruction 4 (創建 PR)
6. Instruction 5 (Session 摘要)

預估時間: 15-20 分鐘

輸出:
✅ 完整結束流程完成
📄 功能報告: task-reports/user-management-complete.md
🔄 PR 創建: User Management Module Complete
📋 下一步: 準備下個功能開發
```

---

## 錯誤處理

### 常見錯誤和解決方案

#### 錯誤 1: Git 衝突

**錯誤訊息**:
```
error: Your local changes to the following files would be overwritten by merge
```

**解決步驟**:
1. 檢查衝突文件: `git status`
2. 選擇處理方式:
   - Stash 本地更改: `git stash`
   - Commit 本地更改: `git add . && git commit`
3. 拉取遠端更新: `git pull`
4. 解決衝突後重新執行指令

---

#### 錯誤 2: YAML 文件格式錯誤

**錯誤訊息**:
```
YAML parsing error: Invalid YAML format
```

**解決步驟**:
1. 使用 YAML 驗證器檢查語法
2. 檢查縮進是否正確 (使用空格,不用 Tab)
3. 檢查特殊字符是否需要引號
4. 恢復到上一個有效版本: `git checkout HEAD -- <file>`

---

#### 錯誤 3: 文檔路徑不存在

**錯誤訊息**:
```
FileNotFoundError: No such file or directory
```

**解決步驟**:
1. 檢查環境變數配置中的路徑
2. 確認當前工作目錄
3. 使用絕對路徑重新執行

---

## 附錄

### A. Commit Message 範例

```bash
# 新功能
feat(backend): add user profile API endpoints
feat(frontend): create agent list component
feat(api): implement workflow execution service

# Bug 修復
fix(api): resolve null reference in agent service
fix(frontend): handle empty state in dashboard

# 文檔更新
docs(readme): update installation instructions
docs(api): add API documentation

# 重構
refactor(backend): extract database connection logic
refactor(frontend): improve component structure

# 測試
test(backend): add unit tests for agent service
test(e2e): add end-to-end workflow tests

# 構建/配置
chore(ci): update GitHub Actions workflow
chore(deps): upgrade FastAPI to 0.104.0
```

---

### B. 快捷鍵對照表

| 操作 | 快捷指令 |
|------|----------|
| 更新工作流程狀態 | `!ins1 <task_id> <status>` |
| 生成完成報告 | `!ins2 <task_id>` |
| Git 提交 | `!ins3 <message>` |
| 快速同步 | `!ins8` |
| 文檔檢查 | `!ins6` |

---

### C. 相關文檔鏈接

- [BMAD Workflow 文檔](../docs/bmm-workflow-status.yaml)
- [計劃文檔](../archived/docs-v1/03-implementation/sprint-planning/)
- [技術架構文檔](../docs/02-architecture/technical-architecture.md)
- [PRD 文檔](../archived/docs-v1/01-planning/prd/prd-main.md)
- [專案主文檔](../CLAUDE.md)

---

## 更新日誌

### v3.0.0 (2025-12-01)
- 🔄 完全移除 sprint-status.yaml 相關引用
- 🔄 更新所有指令以適應 MVP 完成後的工作流程
- 🔄 將 Sprint Story 概念改為通用任務概念
- 🔄 更新環境變數配置
- 🔄 更新所有範例和模板
- 🔄 與 PROMPT v3.0.0 系列同步

### v2.0.0 (2025-11-20)
- ✅ 初始版本發布
- ✅ 10 個核心指令完成
- ✅ 整合 BMAD 工作流程
- ✅ 適配 IPA 平台專案結構

---

**文檔維護者**: AI Assistant Team
**反饋渠道**: GitHub Issues
