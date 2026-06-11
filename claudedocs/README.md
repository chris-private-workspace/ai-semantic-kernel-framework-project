# ClaudeDocs — 執行文檔快速導覽（V2）

> 本資料夾記錄專案執行階段的動態文檔，與 `/docs` 的設計文檔分開管理。
> **詳細放置規則 + 完整索引**：[`claudedocs/CLAUDE.md`](./CLAUDE.md)（2026-06-12 V2 重寫版）。

---

## 文檔結構

```
claudedocs/
├── 1-planning/          # 活躍規劃（next-phase-candidates / harness-deepening-proposal / gap analyses）
├── 2-sprints/           # （僅模板；sprint plan/checklist 在 docs/03-implementation/agent-harness-planning/）
├── 3-progress/          # 日/週進度（sprint progress.md 在 agent-harness-execution/）
├── 4-changes/           # 變更記錄：bug-fixes(FIX) / feature-changes(CHANGE) / refactoring(REFACTOR) / templates
├── 5-status/            # 狀態/分析快照 → 總索引 5-status/README.md（7 主題群）
├── 6-ai-assistant/      # SITUATION-1..7 prompts + 分析
├── 7-archive/           # 歷史歸檔
└── templates/           # spike-design-note-template.md（sprint-workflow.md §5.5 引用）
```

## 最常用入口

| 需求 | 入口 |
|------|------|
| 下一步做什麼 / pending 清單 | `1-planning/next-phase-candidates.md` |
| Harness 深化路線圖 | `1-planning/harness-deepening-proposal-20260610.md` |
| 5-status 某分析講什麼 | `5-status/README.md`（每檔 1 行索引）|
| 修 bug / 變更 / 重構記錄 | `4-changes/{bug-fixes,feature-changes,refactoring}/` |
| Sprint 截圖等工件 | ❌ 不在這裡 → `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-XX/artifacts/` |
| V1 時期文件 | `archived/claudedocs-v1/` |

---

**Last Updated**: 2026-06-12（REFACTOR-007 docs-reorg：V1 遺留歸檔 + 5-status 索引化 + sprint 工件遷移）
