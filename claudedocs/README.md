# ClaudeDocs - IPA Platform 執行文檔

> 本資料夾用於記錄專案執行階段的所有動態文檔，與 `/docs` 的設計文檔分開管理。

---

## 文檔結構概覽

```
claudedocs/
├── 1-planning/          # 總體規劃 (開始階段)
├── 2-sprints/           # Sprint 執行文檔 (執行階段)
├── 3-progress/          # 進度追蹤 (持續監控)
├── 4-changes/           # 變更記錄 (應對變化)
├── 5-status/            # 狀態報告 (階段總結)
├── 6-ai-assistant/      # AI 助手指引 (輔助工具)
└── 7-archive/           # 歷史歸檔 (完成後)
```

---

## 各資料夾說明

### 1-planning/ - 總體規劃
| 子目錄 | 用途 |
|--------|------|
| `roadmap/` | 路線圖和時間線 |
| `epics/` | Phase 詳細規劃（本專案有 28 個 Phase） |
| `features/` | 功能規劃 (FEAT-XXX-name/) |
| `architecture/` | 架構設計決策 |

### 2-sprints/ - Sprint 執行文檔
| 子目錄 | 用途 |
|--------|------|
| `phase-{N}/` | 各 Phase 的 Sprint 文檔 |
| `templates/` | Sprint 相關模板 |

### 3-progress/ - 進度追蹤
| 子目錄 | 用途 |
|--------|------|
| `weekly/` | 每週進度記錄 |
| `daily/` | 每日開發日誌 |
| `milestones/` | 里程碑達成記錄 |
| `templates/` | 進度追蹤模板 |

### 4-changes/ - 變更記錄
| 子目錄 | 用途 | 命名規範 |
|--------|------|----------|
| `bug-fixes/` | Bug 修復記錄 | `FIX-XXX-description.md` |
| `feature-changes/` | 功能變更記錄 | `CHANGE-XXX-description.md` |
| `refactoring/` | 重構記錄 | `REFACTOR-XXX-description.md` |
| `templates/` | 變更記錄模板 | - |

### 5-status/ - 狀態報告
| 子目錄 | 用途 |
|--------|------|
| `phase-reports/` | Phase/Sprint 完成報告 |
| `testing/` | 測試報告（e2e, unit, integration） |
| `quality/` | 品質報告、Code Review |

### 6-ai-assistant/ - AI 助手指引
| 子目錄 | 用途 |
|--------|------|
| `prompts/` | 情境提示詞 (SITUATION-*) |
| `session-guides/` | 會話指引 |
| `analysis/` | AI 分析報告 |
| `changelogs/` | 變更日誌 |
| `handoff/` | 階段交接文檔 |

### 7-archive/ - 歷史歸檔
| 子目錄 | 用途 |
|--------|------|
| `phase-1-mvp/` | Phase 1 已完成文檔 |
| `session-logs/` | 歷史會話記錄 |

---

## 專案資訊

| 項目 | 內容 |
|------|------|
| **專案名稱** | IPA Platform (Intelligent Process Automation) |
| **Phase 數量** | 28 個 |
| **Sprint 數量** | 99 個 |
| **Story Points** | 2189 pts |
| **當前階段** | Phase 28 已完成 |
| **建立日期** | 2025-11-14 |

### Phase 清單 (精簡版)

| Phase | 名稱 | Sprints | 狀態 |
|-------|------|---------|------|
| Phase 1-6 | 基礎建設 + 並行執行 + API Migration + Adapters + Connectors + Enterprise | 1-30 | ✅ 已完成 |
| Phase 7-10 | Multi-turn + Code Interpreter + MCP Core + MCP Expansion | 31-44 | ✅ 已完成 |
| Phase 11-15 | Agent-Session + Claude SDK + Hybrid Architecture + AG-UI | 45-60 | ✅ 已完成 |
| Phase 16-20 | Unified Chat + DevTools + Session + Autonomous + Attachments | 61-76 | ✅ 已完成 |
| Phase 21-25 | Sandbox + mem0 + Performance + Production + Expansion | 77-86 | ✅ 已完成 |
| Phase 26-28 | DevUI + mem0 整合 + 三層意圖路由 | 87-99 | ✅ 已完成 |

---

## 使用指引

### 日常工作流程

1. **開始工作前**：查看 `3-progress/daily/` 最新日誌
2. **遇到 Bug**：在 `4-changes/bug-fixes/` 建立記錄
3. **完成功能**：更新 `3-progress/` 相關進度
4. **Session 結束**：更新 `6-ai-assistant/session-guides/`

### 文件命名規範

| 類型 | 格式 | 範例 |
|------|------|------|
| 日報 | `YYYY-MM-DD.md` | `2026-01-22.md` |
| 週報 | `YYYY-WXX.md` | `2026-W04.md` |
| Bug 修復 | `FIX-XXX-description.md` | `FIX-001-hitl-approval-wrong-id-type.md` |
| 功能變更 | `CHANGE-XXX-description.md` | `CHANGE-001-hitl-inline-approval-card.md` |
| 重構 | `REFACTOR-XXX-description.md` | `REFACTOR-001-api-structure.md` |

---

## 與 /docs 的關係

| 資料夾 | 用途 | 更新頻率 |
|--------|------|----------|
| `/docs` | 設計文檔（PRD, Architecture, Stories） | 低（設計階段） |
| `/claudedocs` | 執行文檔（進度、變更、測試） | 高（執行階段） |

**原則**：
- `/docs` 中的文檔視為「設計規格」，不應頻繁修改
- `/claudedocs` 用於記錄實際執行情況，可隨時更新
- 如發現設計與實作有重大差異，應在 `/claudedocs/4-changes/` 記錄

---

## AI 助手情境導航

根據你當前的開發情況，選擇對應的 Prompt：

| 情況 | 描述 | Prompt |
|------|------|--------|
| **專案入門** | 首次接觸或長時間未參與 | [SITUATION-1](./6-ai-assistant/prompts/SITUATION-1-PROJECT-ONBOARDING.md) |
| **功能開發準備** | 準備開發新功能 | [SITUATION-2](./6-ai-assistant/prompts/SITUATION-2-FEATURE-DEV-PREP.md) |
| **功能增強** | 增強或修正現有功能 | [SITUATION-3](./6-ai-assistant/prompts/SITUATION-3-FEATURE-ENHANCEMENT.md) |
| **新功能開發** | 執行新功能開發 | [SITUATION-4](./6-ai-assistant/prompts/SITUATION-4-NEW-FEATURE-DEV.md) |
| **保存進度** | 保存工作進度 | [SITUATION-5](./6-ai-assistant/prompts/SITUATION-5-SAVE-PROGRESS.md) |
| **服務啟動** | 啟動開發環境服務 | [SITUATION-6](./6-ai-assistant/prompts/SITUATION-6-SERVICE-STARTUP.md) |
| **新環境設置** | 設置新開發環境 | [SITUATION-7](./6-ai-assistant/prompts/SITUATION-7-NEW-ENV-SETUP.md) |

### 開發流程概覽

```
專案入門 (SITUATION-1)
    │
    ▼
準備階段 (SITUATION-2/3) ──────────────┐
    │                                   │
    ▼                                   ▼
新功能開發 (SITUATION-4)         功能增強 (SITUATION-3)
    │                                   │
    └──────────────┬────────────────────┘
                   │
                   ▼
           保存進度 (SITUATION-5)
```

---

## 快速連結

### 核心文檔
- [CLAUDE.md](./CLAUDE.md) - ClaudeDocs 目錄索引（詳細）
- [專案 CLAUDE.md](../CLAUDE.md) - 根目錄專案總指南
- [Sprint Planning](../archived/docs-v1/03-implementation/sprint-planning/README.md) - Sprint 規劃總覽

### 規則文件
- [後端 Python 規範](../.claude/rules/backend-python.md)
- [前端 React 規範](../.claude/rules/frontend-react.md)
- [Agent Framework 規範](../.claude/rules/agent-framework.md)
- [Git 工作流程](../.claude/rules/git-workflow.md)

### 最新變更
- [Bug 修復](./4-changes/bug-fixes/)
- [功能變更](./4-changes/feature-changes/)

---

*文檔建立日期：2025-11-14*
*最後更新：2026-01-22*
*版本：V3.0*
