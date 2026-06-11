# ClaudeDocs - AI 文件提取專案執行文檔

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
| `epics/` | Epic 詳細規劃（本專案有 12 個 Epic） |
| `features/` | 功能規劃 (FEAT-XXX-name/) |
| `architecture/` | 架構設計決策 |

### 2-sprints/ - Sprint 執行文檔
| 子目錄 | 用途 |
|--------|------|
| `current/` | 當前進行中的 Sprint |
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
| `phase-reports/` | 階段/Sprint 完成報告 |
| `testing/` | 測試報告（e2e, unit, integration） |
| `quality/` | 品質報告、Code Review |

### 6-ai-assistant/ - AI 助手指引
| 子目錄 | 用途 |
|--------|------|
| `prompts/` | Prompt 模板 |
| `session-guides/` | 會話指引 |
| `analysis/` | AI 分析報告 |
| `handoff/` | 階段交接文檔 |

### 7-archive/ - 歷史歸檔
| 子目錄 | 用途 |
|--------|------|
| `completed-epics/` | 已完成 Epic 的文檔 |
| `session-logs/` | 歷史會話記錄 |

---

## 專案資訊

| 項目 | 內容 |
|------|------|
| **專案名稱** | AI Document Extraction |
| **Epic 數量** | 12 個 |
| **Story 數量** | 83 個 |
| **當前階段** | 測試階段 |
| **建立日期** | 2025-12-21 |

### Epic 清單

| Epic | 名稱 | 狀態 |
|------|------|------|
| Epic 1 | 用戶認證與存取控制 | ✅ 已完成 |
| Epic 2 | 手動發票上傳與 AI 處理 | ✅ 已完成 |
| Epic 3 | 發票審核與修正工作流 | ✅ 已完成 |
| Epic 4 | 映射規則管理與自動學習 | ✅ 已完成 |
| Epic 5 | Forwarder 配置管理 | ✅ 已完成 |
| Epic 6 | 多城市數據隔離 | ✅ 已完成 |
| Epic 7 | 報表儀表板與成本追蹤 | ✅ 已完成 |
| Epic 8 | 審計追溯與合規 | ✅ 已完成 |
| Epic 9 | 自動化文件獲取 | ✅ 已完成 |
| Epic 10 | n8n 工作流整合 | ✅ 已完成 |
| Epic 11 | 對外 API 服務 | ✅ 已完成 |
| Epic 12 | 系統管理與監控 | ✅ 已完成 |

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
| 日報 | `YYYY-MM-DD.md` | `2025-12-21.md` |
| 週報 | `YYYY-WXX.md` | `2025-W51.md` |
| Bug 修復 | `FIX-XXX-description.md` | `FIX-001-auth-session-error.md` |
| 功能變更 | `CHANGE-XXX-description.md` | `CHANGE-001-add-dark-mode.md` |
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

*文檔建立日期：2025-12-21*
