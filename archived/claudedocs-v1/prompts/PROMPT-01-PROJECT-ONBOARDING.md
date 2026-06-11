# PROMPT-01: PROJECT ONBOARDING
# 專案上手指南

> **用途**: 新專案或新開發者快速上手 IPA 平台
> **變數**: 無
> **預估時間**: 5-10 分鐘
> **版本**: v3.0.0

---

## 📋 執行目標

幫助 AI 助手或新開發者快速理解:
1. 專案背景和目標
2. 技術架構和技術棧
3. 專案結構和關鍵文檔
4. 開發工作流程和規範
5. 可用的 AI 助手指令和 Prompts
6. MVP 完成狀態和後續開發方向

---

## 🎯 執行步驟

### Step 1: 讀取專案核心文檔

按順序讀取以下文檔:

```yaml
必讀文檔 (MUST READ):
  1. CLAUDE.md
     - 專案概述和開發指南
     - AI 助手快速參考

  2. docs/bmm-workflow-status.yaml
     - 專案當前階段
     - 工作流程狀態
     - 歷史重大事件

  3. docs/03-implementation/sprint-planning/README.md
     - Sprint 計劃總覽
     - 14 個 MVP 功能概述
     - 技術架構摘要

  4. docs/01-planning/prd/prd-main.md
     - 產品需求文檔
     - 核心功能列表

  5. docs/02-architecture/technical-architecture.md
     - 技術架構設計
     - 技術選型決策

選讀文檔 (RECOMMENDED):
  6. docs/00-discovery/product-brief/product-brief.md
     - 產品定位和願景

  7. docs/03-implementation/MVP-COMPLETION-SUMMARY.md
     - MVP 完成報告 (如存在)

  8. claudedocs/AI-ASSISTANT-INSTRUCTIONS.md
     - AI 助手指令手冊
```

### Step 2: 提取關鍵信息

從文檔中提取以下關鍵信息:

```yaml
專案基本信息:
  - 專案名稱: IPA Platform (Intelligent Process Automation)
  - 專案定位: 企業級 AI Agent 編排管理平台
  - 核心價值主張: LLM 智能決策、跨系統關聯分析、人機協作學習
  - 目標用戶: IT 運維團隊 (500-2000 人企業)、客戶服務團隊

技術架構:
  - 前端技術棧: React 18 + TypeScript + Tailwind CSS
  - 後端技術棧: Python FastAPI + Pydantic
  - 數據庫: PostgreSQL 16
  - 緩存: Redis 7
  - 消息隊列: RabbitMQ (開發) / Azure Service Bus (生產)
  - 核心框架: Microsoft Agent Framework (Preview)
  - LLM: Azure OpenAI GPT-4o

當前狀態:
  - 專案階段: Phase 4 - Production Deployment Ready
  - MVP 狀態: 已完成 (285/285 pts, 100%)
  - 已完成 Sprint: Sprint 0-6 全部完成
  - 下一個里程碑: 生產部署

已完成功能模組:
  - API 模組: 15 個 (agents, workflows, executions, checkpoints, etc.)
  - 業務模組: 14 個 (domain services)
  - 前端頁面: 7 個主要頁面
```

### Step 3: 分析專案結構

掃描專案目錄結構,理解組織方式:

```
📁 專案根目錄
├── 📁 backend/                 # Python FastAPI 後端
│   ├── 📁 src/
│   │   ├── 📁 api/v1/         # 15 個 API 路由模組
│   │   │   ├── agents/        # Agent 管理
│   │   │   ├── workflows/     # 工作流管理
│   │   │   ├── executions/    # 執行管理
│   │   │   ├── checkpoints/   # 檢查點管理
│   │   │   ├── connectors/    # 連接器 (ServiceNow, Dynamics365, SharePoint)
│   │   │   ├── triggers/      # 觸發器 (Webhook)
│   │   │   ├── prompts/       # Prompt 模板管理
│   │   │   ├── audit/         # 審計日誌
│   │   │   ├── notifications/ # Teams 通知
│   │   │   ├── routing/       # 場景路由
│   │   │   ├── templates/     # Agent 模板市場
│   │   │   ├── learning/      # 學習型協作
│   │   │   ├── cache/         # LLM 緩存管理
│   │   │   ├── devtools/      # 開發者工具
│   │   │   └── versioning/    # 版本管理
│   │   ├── 📁 domain/         # 14 個業務領域模組
│   │   ├── 📁 infrastructure/ # 數據庫/緩存/消息基礎設施
│   │   └── 📁 core/           # 核心配置
│   ├── 📁 tests/              # 測試套件 (unit/integration/e2e)
│   ├── 📁 prompts/            # Prompt YAML 模板
│   ├── main.py                # FastAPI 入口
│   └── requirements.txt       # Python 依賴
│
├── 📁 frontend/                # React TypeScript 前端
│   ├── 📁 src/
│   │   ├── 📁 components/     # UI 組件
│   │   │   ├── layout/        # 佈局組件 (AppLayout, Sidebar, Header)
│   │   │   ├── ui/            # 基礎 UI (Button, Card, Badge)
│   │   │   └── shared/        # 共享組件 (LoadingSpinner, StatusBadge)
│   │   ├── 📁 pages/          # 頁面組件
│   │   │   ├── dashboard/     # 儀表板
│   │   │   ├── workflows/     # 工作流管理
│   │   │   ├── agents/        # Agent 管理
│   │   │   ├── approvals/     # 審批管理
│   │   │   ├── audit/         # 審計日誌
│   │   │   └── templates/     # 模板市場
│   │   ├── 📁 hooks/          # React Hooks
│   │   ├── 📁 services/       # API 服務
│   │   └── 📁 types/          # TypeScript 類型
│   └── package.json
│
├── 📁 docs/                    # 專案文檔
│   ├── 📁 00-discovery/       # Phase 0: 探索階段
│   ├── 📁 01-planning/        # Phase 1: 規劃階段
│   ├── 📁 02-architecture/    # Phase 2: 架構階段
│   ├── 📁 03-implementation/  # Phase 3: 實施階段
│   │   ├── 📁 sprint-planning/    # Sprint 0-6 計劃文檔
│   │   ├── 📁 sprint-execution/   # Sprint 執行追蹤
│   │   ├── 📁 architecture-designs/ # 架構設計文檔
│   │   └── 📁 archive/            # 歷史文檔存檔
│   └── 📁 04-review/          # Phase 4: 審查階段
│
├── 📁 claudedocs/              # AI 助手系統
│   ├── AI-ASSISTANT-INSTRUCTIONS.md  # 核心指令手冊
│   ├── 📁 prompts/                   # 9 個標準化 Prompt
│   ├── 📁 sprint-reports/            # Sprint 報告 (歷史)
│   └── 📁 session-logs/              # Session 記錄 (歷史)
│
├── 📁 deploy/                  # 部署配置
├── 📁 infrastructure/          # 基礎設施配置
├── 📁 scripts/                 # 工具腳本
├── 📁 reference/               # 參考文檔
│   └── 📁 agent-framework/    # Agent Framework 文檔
│
├── docker-compose.yml          # 本地開發環境
├── .env.example               # 環境變量模板
└── CLAUDE.md                  # 專案 AI 助手指南
```

### Step 4: 理解開發工作流程

總結開發工作流程:

```yaml
Git 工作流程:
  主分支: main
  分支命名規範:
    - Feature: feature/sprint-{N}-{story-id}-{description}
    - Bugfix: bugfix/{bug-id}-{description}
    - Hotfix: hotfix/{issue-id}-{description}
  Commit message 格式: <type>(<scope>): <description>
  Types: feat, fix, docs, refactor, test, chore

開發環境啟動:
  1. Docker 服務: docker-compose up -d
  2. 後端 API: cd backend && uvicorn main:app --reload --port 8000
  3. 前端 UI: cd frontend && npm run dev
  4. 健康檢查: curl http://localhost:8000/health

代碼品質標準:
  - 格式化: Black (line-length: 100)
  - 導入排序: isort (profile: black)
  - Lint: flake8
  - 類型檢查: mypy (strict mode)
  - 測試覆蓋率: >= 80%
```

### Step 5: 列出可用工具和指令

總結可用的 AI 助手工具:

```yaml
Instructions (AI-ASSISTANT-INSTRUCTIONS.md):
  日常開發:
    - Instruction 1: 更新專案狀態文件
    - Instruction 3: Git 標準工作流程
    - Instruction 8: 快速進度同步

  品質保證:
    - Instruction 6: 文檔一致性檢查
    - Instruction 9: 架構審查
    - Instruction 10: 代碼審查

  Sprint 管理:
    - Instruction 2: 生成 Sprint 完成報告
    - Instruction 5: 生成 Session 摘要
    - Instruction 7: 完整 Sprint 結束流程

  發布流程:
    - Instruction 4: 創建 Pull Request

Prompts (claudedocs/prompts/):
  準備階段:
    - PROMPT-01: 專案上手 (當前使用中)
    - PROMPT-02: 新開發任務準備
    - PROMPT-03: Bug 修復準備

  開發階段:
    - PROMPT-04: 開發執行
    - PROMPT-05: 測試執行

  完成階段:
    - PROMPT-06: 進度保存
    - PROMPT-09: Session 結束

  審查階段:
    - PROMPT-07: 架構審查
    - PROMPT-08: 代碼審查
```

---

## 📤 輸出格式

生成結構化的專案上手報告:

```markdown
# IPA 平台專案上手報告
生成時間: {TIMESTAMP}

## 📊 專案概覽

**專案名稱**: IPA Platform (Intelligent Process Automation)
**專案定位**: 企業級 AI Agent 編排管理平台
**目標用戶**: 中型企業 IT 運維團隊 (500-2000 人)

**核心價值**:
- LLM 智能決策，自適應場景
- 跨系統關聯分析，統一視圖
- 人機協作學習，越用越智能

---

## 🏗️ 技術架構

### 前端技術棧
- 框架: React 18 + TypeScript
- UI 庫: Tailwind CSS + Shadcn UI
- 狀態管理: React Query + Context

### 後端技術棧
- 語言/框架: Python FastAPI
- API 風格: RESTful
- 認證方式: JWT

### 數據庫
- 主數據庫: PostgreSQL 16
- 緩存: Redis 7
- 消息隊列: RabbitMQ / Azure Service Bus

### 核心框架
- 框架名稱: Microsoft Agent Framework
- 版本: Preview
- 特殊考慮: API 可能變更，需監控 Release Notes

---

## 📍 當前狀態

**專案階段**: Phase 4 - Production Deployment Ready

**MVP 完成狀態**: ✅ 已完成

| Sprint | 名稱 | 狀態 | Points |
|--------|------|------|--------|
| Sprint 0 | 基礎設施 | ✅ 完成 | 45/45 |
| Sprint 1 | 核心引擎 | ✅ 完成 | 42/42 |
| Sprint 2 | 工作流 & 檢查點 | ✅ 完成 | 40/40 |
| Sprint 3 | 集成 & 可靠性 | ✅ 完成 | 38/38 |
| Sprint 4 | 開發者體驗 | ✅ 完成 | 40/40 |
| Sprint 5 | 前端 UI | ✅ 完成 | 45/45 |
| Sprint 6 | 打磨 & 發布 | ✅ 完成 | 35/35 |
| **總計** | | | **285/285 (100%)** |

**下一個里程碑**: 生產部署

---

## 📁 專案結構

### 文檔目錄 (docs/)
```
docs/
├── 00-discovery/        # 探索階段文檔
├── 01-planning/         # 規劃階段文檔
├── 02-architecture/     # 架構階段文檔
├── 03-implementation/   # 實施階段文檔
│   ├── sprint-planning/     # Sprint 0-6 計劃
│   ├── sprint-execution/    # 執行追蹤
│   └── architecture-designs/ # 架構設計
└── 04-review/           # 審查階段文檔
```

### AI 助手文檔 (claudedocs/)
```
claudedocs/
├── AI-ASSISTANT-INSTRUCTIONS.md  # 核心指令
├── prompts/                      # 9 個 Prompt 文件
├── sprint-reports/               # Sprint 報告 (歷史)
└── session-logs/                 # Session 記錄 (歷史)
```

### 代碼目錄
```
backend/                # 後端 API (15 個模組, 155+ 路由)
frontend/               # 前端 UI (7 個頁面)
deploy/                 # 部署配置
infrastructure/         # 基礎設施
scripts/                # 工具腳本
```

---

## 🔄 開發工作流程

### 本地開發環境啟動

```bash
# 1. 啟動 Docker 服務
docker-compose up -d

# 2. 啟動後端 API
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. 啟動前端 (另一終端)
cd frontend
npm run dev

# 4. 驗證服務
curl http://localhost:8000/health  # 後端健康檢查
# 前端: http://localhost:3000
```

### Git 工作流程

1. **分支命名規範**:
   - Feature: `feature/{task-id}-{description}`
   - Bugfix: `bugfix/{bug-id}-{description}`
   - Hotfix: `hotfix/{issue-id}-{description}`

2. **Commit Message 格式**:
   ```
   <type>(<scope>): <description>
   ```
   Types: feat, fix, docs, refactor, test, chore

3. **PR 流程**:
   - 創建 feature branch
   - 完成開發和測試
   - 提交 PR
   - Code review
   - 合併到 main

---

## 🛠️ 可用的 AI 助手工具

### Instructions 指令

**日常開發**:
- `Instruction 1`: 更新專案狀態文件
- `Instruction 3`: Git 提交標準流程
- `Instruction 8`: 快速進度同步

**品質保證**:
- `Instruction 6`: 文檔一致性檢查
- `Instruction 9`: 架構審查
- `Instruction 10`: 代碼審查

**Sprint 管理**:
- `Instruction 2`: 生成 Sprint 完成報告
- `Instruction 5`: 生成 Session 摘要
- `Instruction 7`: 完整 Sprint 結束流程

### Prompts 提示詞

**準備階段**:
- `@PROMPT-01`: 專案上手 (當前使用中)
- `@PROMPT-02 {TaskID}`: 準備新開發任務
- `@PROMPT-03 {BugID}`: 準備修復 Bug

**開發階段**:
- `@PROMPT-04 {TaskID}`: 執行開發任務
- `@PROMPT-05 {TaskID}`: 執行測試

**完成階段**:
- `@PROMPT-06 {TaskID}`: 保存進度
- `@PROMPT-09`: Session 結束

**審查階段**:
- `@PROMPT-07`: 架構審查
- `@PROMPT-08 {Path}`: 代碼審查

---

## 🎯 建議的下一步

### 如果是新開發者:
1. ✅ 閱讀完整的技術架構文檔
2. ✅ 設置本地開發環境 (docker-compose up -d)
3. ✅ 運行並熟悉現有功能
4. ✅ 閱讀代碼品質標準和規範

### 如果是 AI 助手:
1. ✅ 已完成專案上手
2. ⏳ 準備好協助開發工作
3. ⏳ 可以執行以下操作:
   - 回答專案相關問題
   - 執行 Instructions 指令
   - 使用其他 Prompts 協助開發
   - 生成文檔和報告
   - 協助 Bug 修復和功能增強

### MVP 後階段建議任務:
1. 🔧 手動測試和功能驗證
2. 🔧 性能優化和調優
3. 🔧 安全審計和加固
4. 🔧 生產部署準備
5. 🔧 用戶文檔編寫

---

## 📚 重要文檔快速鏈接

| 文檔 | 路徑 | 用途 |
|------|------|------|
| 專案指南 | `CLAUDE.md` | AI 助手快速參考 |
| 工作流程狀態 | `docs/bmm-workflow-status.yaml` | 階段追蹤 |
| Sprint 計劃總覽 | `docs/03-implementation/sprint-planning/README.md` | Sprint 規劃 |
| PRD | `docs/01-planning/prd/prd-main.md` | 產品需求 |
| 技術架構 | `docs/02-architecture/technical-architecture.md` | 架構設計 |
| AI 指令 | `claudedocs/AI-ASSISTANT-INSTRUCTIONS.md` | 助手指令 |
| Prompts 庫 | `claudedocs/prompts/` | Prompt 文件 |

---

## ✅ 上手檢查清單

完成以下檢查項,確認已充分理解專案:

專案理解:
- [ ] 了解專案背景和目標 (企業級 AI Agent 平台)
- [ ] 理解核心功能和價值主張 (LLM 智能、跨系統、人機協作)
- [ ] 知道目標用戶是誰 (IT 運維團隊)

技術架構:
- [ ] 了解前端技術棧 (React 18 + TypeScript)
- [ ] 了解後端技術棧 (Python FastAPI)
- [ ] 了解數據庫和雲服務選型 (PostgreSQL, Redis, Azure)
- [ ] 理解核心框架 (Microsoft Agent Framework)

當前狀態:
- [ ] 知道專案 MVP 已完成 (285/285 pts)
- [ ] 了解 6 個 Sprint 的交付內容
- [ ] 清楚下一個里程碑 (生產部署)

工作流程:
- [ ] 理解 Git 工作流程
- [ ] 知道如何啟動本地開發環境
- [ ] 知道如何使用 AI 助手工具

準備就緒:
- [ ] 可以開始協助開發工作
- [ ] 知道如何獲取幫助
- [ ] 知道下一步要做什麼

---

**完成時間**: {COMPLETION_TIME}
**生成者**: AI Assistant (PROMPT-01)
```

---

## 💡 使用提示

### 何時使用此 Prompt

- ✅ 新專案啟動時
- ✅ 新 AI 助手加入專案時
- ✅ 新開發者加入團隊時
- ✅ 專案發生重大變更後
- ✅ 需要全面回顧專案狀態時
- ✅ MVP 完成後進入新階段時

### 預期效果

執行此 Prompt 後,AI 助手應該能夠:
- 回答關於專案的基本問題
- 理解專案當前狀態 (MVP 已完成)
- 知道如何使用其他 Prompts 和 Instructions
- 提供專案相關的建議和指導
- 協助後續開發和維護工作

---

## 🔗 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md)
- [Prompts README](./README.md)
- [PROMPT-02: New Task Prep](./PROMPT-02-NEW-SPRINT-PREP.md)
- [PROMPT-04: Development](./PROMPT-04-SPRINT-DEVELOPMENT.md)

---

**版本**: v3.0.0
**更新日期**: 2025-12-01
**維護者**: AI Assistant Team
