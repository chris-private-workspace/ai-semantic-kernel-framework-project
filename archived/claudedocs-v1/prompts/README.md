# AI Assistant Prompts Library
# AI 助手標準化 Prompt 庫

> **版本**: v2.0.0
> **專案**: Microsoft Agent Framework Platform (IPA)
> **更新日期**: 2025-11-20

---

## 📚 Prompt 文件清單

### 專案啟動與準備

| Prompt ID | 文件名 | 用途 | 變數支援 | 行數 |
|-----------|--------|------|----------|------|
| **PROMPT-01** | [PROJECT-ONBOARDING.md](./PROMPT-01-PROJECT-ONBOARDING.md) | 新專案/新開發者上手 | ❌ 無 | ~120 |
| **PROMPT-02** | [NEW-SPRINT-PREP.md](./PROMPT-02-NEW-SPRINT-PREP.md) | 準備開始新 Sprint Story | ✅ Sprint ID, Story ID | ~220 |
| **PROMPT-03** | [BUG-FIX-PREP.md](./PROMPT-03-BUG-FIX-PREP.md) | 準備修復 Bug | ✅ Bug ID | ~180 |

### 開發與實施

| Prompt ID | 文件名 | 用途 | 變數支援 | 行數 |
|-----------|--------|------|----------|------|
| **PROMPT-04** | [SPRINT-DEVELOPMENT.md](./PROMPT-04-SPRINT-DEVELOPMENT.md) | 執行 Sprint Story 開發 | ✅ Sprint ID, Story ID | ~170 |
| **PROMPT-05** | [TESTING-PHASE.md](./PROMPT-05-TESTING-PHASE.md) | 執行測試階段 | ✅ Story ID | ~190 |
| **PROMPT-06** | [PROGRESS-SAVE.md](./PROMPT-06-PROGRESS-SAVE.md) | 保存進度和狀態 | ✅ Sprint ID, Story ID | ~300 |

### 審查與質量

| Prompt ID | 文件名 | 用途 | 變數支援 | 行數 |
|-----------|--------|------|----------|------|
| **PROMPT-07** | [ARCHITECTURE-REVIEW.md](./PROMPT-07-ARCHITECTURE-REVIEW.md) | 架構審查和分析 | ❌ 無 | ~290 |
| **PROMPT-08** | [CODE-REVIEW.md](./PROMPT-08-CODE-REVIEW.md) | 代碼質量審查 | ✅ 文件/目錄路徑 | ~270 |

### 完成與總結

| Prompt ID | 文件名 | 用途 | 變數支援 | 行數 |
|-----------|--------|------|----------|------|
| **PROMPT-09** | [SESSION-END.md](./PROMPT-09-SESSION-END.md) | Session 結束總結 | ❌ 無 | ~260 |

---

## 🎯 設計理念 (v2.0.0)

### 核心原則

1. **AI 自主讀取**:
   - 格式: `@PROMPT-XX.md [變數]`
   - AI 自動讀取並執行,無需人工複製貼上

2. **精簡高效**:
   - Prompt 長度: 80-300 行
   - 去除冗長示範,專注執行步驟
   - 清晰的 AI 指令,而非示範性內容

3. **變數支援**:
   - 必要時支持變數 (Sprint ID, Story ID, Bug ID, 路徑)
   - 簡化的變數系統,易於使用

4. **指令式設計**:
   - 明確的步驟順序
   - 可驗證的輸出格式
   - 標準化的操作流程

5. **適中輸出**:
   - 詳細但不冗長
   - 關注可操作的建議
   - 避免過度分析

---

## 📖 使用指南

### 基本使用

```bash
# 方式 1: 無變數的 Prompt
用戶: "@PROMPT-01-PROJECT-ONBOARDING.md"
AI: 自動讀取並執行專案上手流程

# 方式 2: 帶變數的 Prompt
用戶: "@PROMPT-02-NEW-SPRINT-PREP.md Sprint-0 S0-1"
AI: 讀取 Prompt,替換變數 {SPRINT_ID}=Sprint-0, {STORY_ID}=S0-1

# 方式 3: 使用路徑變數
用戶: "@PROMPT-08-CODE-REVIEW.md backend/src/agent/"
AI: 審查指定路徑的代碼
```

### 變數語法

#### PROMPT-02: NEW-SPRINT-PREP
```
用法: @PROMPT-02-NEW-SPRINT-PREP.md {SPRINT_ID} {STORY_ID}
範例: @PROMPT-02-NEW-SPRINT-PREP.md Sprint-0 S0-1
```

#### PROMPT-04: SPRINT-DEVELOPMENT
```
用法: @PROMPT-04-SPRINT-DEVELOPMENT.md {SPRINT_ID} {STORY_ID}
範例: @PROMPT-04-SPRINT-DEVELOPMENT.md Sprint-0 S0-2
```

#### PROMPT-06: PROGRESS-SAVE
```
用法: @PROMPT-06-PROGRESS-SAVE.md {SPRINT_ID} {STORY_ID}
範例: @PROMPT-06-PROGRESS-SAVE.md Sprint-0 S0-3
```

#### PROMPT-08: CODE-REVIEW
```
用法: @PROMPT-08-CODE-REVIEW.md {FILE_PATH}
範例: @PROMPT-08-CODE-REVIEW.md backend/src/agent/
```

---

## 🔄 工作流程整合

### 完整開發週期

```yaml
階段 1: 專案上手
  - @PROMPT-01-PROJECT-ONBOARDING.md
  - 了解專案結構、技術棧、工作流程

階段 2: Sprint 準備
  - @PROMPT-02-NEW-SPRINT-PREP.md {SPRINT_ID} {STORY_ID}
  - 準備開發環境、理解 Story 需求

階段 3: 開發實施
  - @PROMPT-04-SPRINT-DEVELOPMENT.md {SPRINT_ID} {STORY_ID}
  - 執行開發任務

階段 4: 測試驗證
  - @PROMPT-05-TESTING-PHASE.md {STORY_ID}
  - 執行測試、驗證功能

階段 5: 保存進度
  - @PROMPT-06-PROGRESS-SAVE.md {SPRINT_ID} {STORY_ID}
  - 提交代碼、更新文檔

階段 6: 代碼審查
  - @PROMPT-08-CODE-REVIEW.md {PATH}
  - 審查代碼質量

階段 7: Session 結束
  - @PROMPT-09-SESSION-END.md
  - 生成工作摘要
```

---

## 📊 Prompt 特性對照

| Prompt | 變數支援 | 讀取文件 | 寫入文件 | 執行命令 | 預估時間 |
|--------|---------|---------|---------|---------|---------|
| 01 | ❌ | ✅ 多個 | ❌ | ❌ | 5-10分 |
| 02 | ✅ Sprint+Story | ✅ Sprint文檔 | ❌ | ❌ | 3-5分 |
| 03 | ✅ Bug ID | ✅ Bug報告 | ❌ | ❌ | 3-5分 |
| 04 | ✅ Sprint+Story | ✅ 技術文檔 | ✅ 代碼 | ✅ Git | 15-30分 |
| 05 | ✅ Story ID | ✅ 測試文檔 | ✅ 測試 | ✅ 測試命令 | 10-20分 |
| 06 | ✅ Sprint+Story | ✅ 狀態文件 | ✅ 狀態更新 | ✅ Git | 5-10分 |
| 07 | ❌ | ✅ 架構文檔 | ✅ 審查報告 | ❌ | 10-15分 |
| 08 | ✅ 路徑 | ✅ 代碼文件 | ✅ 審查報告 | ❌ | 5-10分 |
| 09 | ❌ | ✅ Session記錄 | ✅ 摘要文檔 | ✅ Git | 3-5分 |

---

## 🔗 與 AI-ASSISTANT-INSTRUCTIONS.md 整合

所有 Prompt 文件有效整合 Instructions 指令:

```yaml
PROMPT-01 (專案上手):
  - 概覽所有 Instructions
  - 理解工作流程
  - 熟悉專案結構

PROMPT-02/03/04 (開發準備與實施):
  - 遵循 Instruction 1 (狀態更新)
  - 遵循 Instruction 3 (Git 工作流程)

PROMPT-05 (測試):
  - 整合 Instruction 10 (代碼審查)
  - 質量保證流程

PROMPT-06 (進度保存):
  - 執行 Instruction 1 (更新狀態)
  - 執行 Instruction 3 (Git 提交)
  - 執行 Instruction 5 (Session 摘要)
  - 可選 Instruction 6 (文檔檢查)

PROMPT-07/08 (審查):
  - 對應 Instruction 9 (架構審查)
  - 對應 Instruction 10 (代碼審查)

PROMPT-09 (結束):
  - 強制執行 Instruction 10 (Session 摘要)
  - Session 結束檢查清單
```

---

## 📝 使用範例

### 範例 1: 開始新 Sprint Story

```
場景: 開始開發 Sprint 0 的 Story S0-2

步驟:
1. 用戶: "@PROMPT-02-NEW-SPRINT-PREP.md Sprint-0 S0-2"
2. AI 讀取 PROMPT-02,替換變數
3. AI 執行:
   - 讀取 sprint-status.yaml 找到 S0-2
   - 讀取 Sprint 0 計劃文檔
   - 讀取技術架構文檔
   - 輸出 Story 需求摘要和準備清單

輸出範例:
---
📋 Sprint Story 準備完成

Story: S0-2 - Azure App Service Setup
Sprint: Sprint 0
Points: 5 分
負責人: DevOps

需求摘要:
- 創建 Azure App Service Plan (Standard S1)
- 配置 staging 和 production 環境
- 設置環境變數和連接字串
- 配置自動擴展規則

技術參考:
- docs/02-architecture/technical-architecture.md#app-service
- docs/03-implementation/sprint-planning/sprint-0-mvp-revised.md

準備清單:
✅ Sprint 文檔已讀取
✅ 技術架構已理解
⏳ 需要創建 Azure Service Principal
⏳ 需要準備環境變數清單

下一步:
1. 創建 Azure Service Principal
2. 執行 @PROMPT-04-SPRINT-DEVELOPMENT.md Sprint-0 S0-2
---
```

---

### 範例 2: 執行開發任務

```
場景: 開發 Story S0-2

步驟:
1. 用戶: "@PROMPT-04-SPRINT-DEVELOPMENT.md Sprint-0 S0-2"
2. AI 執行開發流程:
   - 創建 feature branch
   - 編寫代碼
   - 執行本地測試
   - 更新文檔

(省略詳細輸出)
```

---

### 範例 3: 保存進度

```
場景: S0-2 開發完成,保存進度

步驟:
1. 用戶: "@PROMPT-06-PROGRESS-SAVE.md Sprint-0 S0-2"
2. AI 執行:
   - 使用 Instruction 1 更新 sprint-status.yaml
   - 使用 Instruction 3 Git 提交
   - 使用 Instruction 5 生成 Session 摘要
   - (可選) Instruction 6 文檔檢查

輸出:
---
✅ 進度保存完成

Sprint: Sprint-0
Story: S0-2
狀態: not-started → completed
完成點數: 5 → 10 (總計)

Git 提交:
- feat(sprint-0): complete S0-2 Azure App Service setup
- docs: update sprint status for S0-2

文檔更新:
- sprint-status.yaml (S0-2 狀態)
- session-logs/session-2025-11-20.md

下一步建議:
- 開始 S0-3: CI/CD Pipeline
- 或執行 @PROMPT-09-SESSION-END.md 結束工作
---
```

---

## 🛠️ Prompt 開發指南

### 創建新 Prompt 的標準

1. **文件命名**: `PROMPT-{NN}-{PURPOSE}.md`
2. **文件長度**: 80-300 行
3. **結構要求**:
   ```markdown
   # Prompt 標題

   ## 用途
   [簡短描述]

   ## 變數
   [如果有變數,列出變數定義]

   ## 執行步驟
   [清晰的步驟列表]

   ## 輸出格式
   [標準化輸出模板]

   ## 範例
   [使用範例]
   ```

4. **變數命名規範**:
   - 使用大寫: `{STORY_ID}`, `{SPRINT_ID}`
   - 描述性命名: `{FILE_PATH}`, `{BUG_ID}`
   - 在文檔開頭明確定義

5. **輸出格式**:
   - 使用 Markdown 格式
   - 包含狀態圖標 (✅ ❌ ⏳ ⚠️)
   - 清晰的區塊分隔

---

## 🔄 版本歷史

### v2.0.0 (2025-11-20)
- ✅ 初始版本發布
- ✅ 9 個標準 Prompt 完成
- ✅ 整合 AI-ASSISTANT-INSTRUCTIONS.md
- ✅ 適配 IPA 平台專案

---

## 📚 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md) - 核心指令文檔
- [BMAD Workflow Status](../../docs/bmm-workflow-status.yaml) - 專案階段追蹤
- [Sprint Status](../../docs/03-implementation/sprint-status.yaml) - Sprint 進度追蹤
- [Technical Architecture](../../docs/02-architecture/technical-architecture.md) - 技術架構

---

**維護者**: AI Assistant Team
**最後更新**: 2025-11-20
**反饋**: GitHub Issues
