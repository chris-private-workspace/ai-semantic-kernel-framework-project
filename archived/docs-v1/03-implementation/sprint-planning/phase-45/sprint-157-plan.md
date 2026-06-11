# Sprint 157 Plan - 前端改版

## Phase 45: Orchestration Core

### Sprint 目標
建立 OrchestratorChat 新頁面（複製自 UnifiedChat），新增 pipeline SSE hook 和視覺組件。

---

## 檔案變更

| 檔案 | 動作 | 說明 |
|------|------|------|
| `pages/OrchestratorChat.tsx` | NEW | 從 UnifiedChat 複製的新頁面 |
| `hooks/useOrchestratorPipeline.ts` | NEW | SSE hook (8 步狀態 + 暫停/恢復) |
| `components/unified-chat/PipelineProgressPanel.tsx` | NEW | 8 步視覺進度 |
| `components/unified-chat/GuidedDialogPanel.tsx` | NEW | 引導對話問題面板 |
| `App.tsx` | MODIFY | 加入 /orchestrator-chat 路由 |

---

**Story Points**: 20
**Status**: ✅ Completed
