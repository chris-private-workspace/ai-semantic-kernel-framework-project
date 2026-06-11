# Sprint 157 Checklist - 前端改版

## Reference
- Plan: [sprint-157-plan.md](sprint-157-plan.md)
- Phase: 45 (Orchestration Core)

---

## OrchestratorChat 頁面
- [x] 從 UnifiedChat.tsx 複製為 OrchestratorChat.tsx
- [x] 重命名 export
- [x] App.tsx 加入 /orchestrator-chat 路由

## useOrchestratorPipeline hook
- [x] SSE fetch 連接 POST /orchestration/chat
- [x] 8 步狀態追蹤 (PipelineStep[])
- [x] DIALOG_REQUIRED 事件 → dialogPause 狀態
- [x] HITL_REQUIRED 事件 → hitlPause 狀態
- [x] AGENT_THINKING / AGENT_COMPLETE 事件
- [x] TEXT_DELTA 串流文本累積
- [x] resumeApproval() 動作
- [x] respondDialog() 動作

## PipelineProgressPanel
- [x] 8 步列表 + 狀態圖標 (pending/running/completed/paused/error)
- [x] 延遲顯示
- [x] 路由 badge

## GuidedDialogPanel
- [x] 問題表單
- [x] 欄位輸入
- [x] 提交到 /orchestration/chat/dialog-respond

## 驗證
- [x] TypeScript 零錯誤
- [x] UnifiedChat.tsx 完全未修改
