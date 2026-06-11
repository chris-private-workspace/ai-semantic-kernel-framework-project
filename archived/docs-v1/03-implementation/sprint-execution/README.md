# Sprint Execution Tracking

Sprint 執行追蹤系統，用於記錄每個 Sprint 的開發進度、問題和決策。

## 目錄結構

```
sprint-execution/
├── README.md                    # 本文件
├── sprint-0/                    # Sprint 0: 基礎設施建設
│   ├── progress.md              # 每日進度追蹤
│   ├── issues.md                # 問題與解決方案
│   ├── decisions.md             # 重要決策記錄
│   └── retrospective.md         # Sprint 回顧
├── sprint-1/                    # Sprint 1: Agent Framework 核心
├── sprint-2/                    # Sprint 2: Workflow & Checkpoint
├── sprint-3/                    # Sprint 3: 整合與可靠性
├── sprint-4/                    # Sprint 4: 開發者體驗
├── sprint-5/                    # Sprint 5: 前端 UI
└── sprint-6/                    # Sprint 6: 打磨 & 發布
```

## 工作流程

### 1. Sprint 開始前
1. 閱讀 `sprint-planning/sprint-X-plan.md` 了解目標和任務
2. 檢查 `sprint-planning/sprint-X-checklist.md` 確認驗收標準
3. 在 `sprint-execution/sprint-X/progress.md` 建立初始狀態

### 2. 開發過程中
1. **每日更新** `progress.md` 記錄完成的任務
2. **遇到問題** 記錄到 `issues.md`，包含解決方案
3. **重要決策** 記錄到 `decisions.md`，說明原因和影響

### 3. Sprint 結束
1. 完成 `retrospective.md` 回顧
2. 更新 `sprint-status.yaml` 狀態
3. 準備下一個 Sprint

## 關鍵原則

| 原則 | 說明 |
|------|------|
| 📖 **以 Planning 為準** | 始終以 `sprint-planning/` 文檔為開發依據 |
| 🔄 **定期更新進度** | 每完成一個任務就更新 `progress.md` |
| ✅ **遵循驗收標準** | 嚴格按照 checklist 驗證完成度 |
| 🔍 **Mid-Sprint Check** | 每週中期檢查進度對齊 |
| 📝 **PROMPT-06 保存** | 使用 PROMPT-06 自動化保存進度 |

## 文件模板

### progress.md
```markdown
# Sprint X Progress

## 狀態概覽
- **開始日期**: YYYY-MM-DD
- **預計結束**: YYYY-MM-DD
- **當前進度**: X/Y 點完成

## Day 1 (YYYY-MM-DD)
### 完成項目
- [x] 任務描述

### 進行中
- [ ] 任務描述

### 待處理
- [ ] 任務描述

### 備註
特別說明事項
```

### issues.md
```markdown
# Sprint X Issues

## Issue #1: 問題標題
- **日期**: YYYY-MM-DD
- **嚴重度**: High/Medium/Low
- **狀態**: Open/Resolved
- **描述**: 問題詳細描述
- **解決方案**: 如何解決
- **影響**: 對 Sprint 的影響
```

### decisions.md
```markdown
# Sprint X Decisions

## Decision #1: 決策標題
- **日期**: YYYY-MM-DD
- **背景**: 為什麼需要這個決策
- **選項**:
  1. 選項 A - 優缺點
  2. 選項 B - 優缺點
- **決定**: 選擇的選項
- **原因**: 為什麼選擇這個
- **影響**: 對後續開發的影響
```

## 相關連結

- [Sprint Planning](../sprint-planning/README.md)
- [Sprint Status](../sprint-status.yaml)
- [PROMPT-06 Progress Save](../../../claudedocs/prompts/PROMPT-06-PROGRESS-SAVE.md)
