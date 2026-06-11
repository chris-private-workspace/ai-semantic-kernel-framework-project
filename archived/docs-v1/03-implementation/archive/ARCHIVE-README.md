# Archive Directory

**封存日期**: 2025-11-29
**封存原因**: Sprint 規劃重構 - 從 Semantic Kernel 遷移到 Microsoft Agent Framework

## 封存內容

### sprint-planning-v1/
原始的 Sprint Planning 文件（基於 Semantic Kernel 概念）：
- sprint-0-infrastructure-foundation.md
- sprint-0-local-development.md
- sprint-0-mvp-revised.md
- sprint-1-core-services.md
- sprint-2-integrations.md
- sprint-3-security-observability.md
- sprint-4-ui-frontend.md
- sprint-5-testing-launch.md

### sprint-execution-v1/
原始的 Sprint 執行記錄和文件：
- sprint-0/ 至 sprint-5/ - 各 Sprint 的執行記錄
- sprint-status.yaml - Sprint 狀態追蹤
- sprint-summaries/ - Sprint 摘要
- gap-analysis-report.md - 差距分析報告
- remediation-plan.md - 修復計劃
- mvp-*.md - MVP 相關文件

## 為什麼封存？

1. **技術框架錯誤**: 原規劃基於 Semantic Kernel API，但項目應使用 Microsoft Agent Framework
2. **API 差異顯著**: Agent Framework 使用完全不同的架構模式（WorkflowBuilder, Executor 等）
3. **需要重新規劃**: 根據實際 Agent Framework 架構重新制定 Sprint 計劃

## 新規劃參考

新的 Sprint Planning 將基於：
- `docs/00-discovery/` - 產品探索
- `docs/01-planning/` - 產品規劃
- `docs/02-architecture/` - 技術架構
- `reference/agent-framework/` - Microsoft Agent Framework 源碼參考

---

**注意**: 此目錄內容僅供歷史參考，不應在新開發中使用。
