# Sprint 23 Decisions: Nested Workflow 重構

## 決策記錄

### 決策日期: 2025-12-06

---

## 架構決策

### D23-1: NestedWorkflowAdapter 設計方向

**背景**: 需要創建適配器來統一管理嵌套工作流執行

**決策**:
- 使用官方 `WorkflowBuilder` 和 `Workflow` 組合子工作流
- 保留 Phase 2 的 `ContextPropagation` 和 `RecursiveDepthTracker` 邏輯
- 支持 GroupChat、Handoff、Concurrent 作為子工作流類型

**理由**:
1. 官方 API 提供 Workflow 組合功能
2. 上下文傳播和遞歸控制是重要的安全機制
3. 其他適配器已完成，可作為子工作流使用

---

## 待決定項目

- [ ] 子工作流執行順序的默認行為
- [ ] 錯誤傳播策略 (fail-fast vs continue)
- [ ] 上下文合併衝突解決策略

---

**Last Updated**: 2025-12-06
