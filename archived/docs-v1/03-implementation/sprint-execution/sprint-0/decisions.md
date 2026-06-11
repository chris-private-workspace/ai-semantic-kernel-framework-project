# Sprint 0 Decisions

重要決策記錄，包含技術選型、架構決策和開發方向。

---

## Decision #1: 使用 Microsoft Agent Framework 而非 Semantic Kernel

- **日期**: 2024-11-30
- **背景**: 專案需要選擇 AI Agent 編排框架
- **選項**:
  1. **Semantic Kernel** - Microsoft 的 LLM 編排 SDK
     - 優點: 成熟、文檔完善
     - 缺點: 缺少 Agent 協作和 Checkpoint 原生支持
  2. **Microsoft Agent Framework** - 新的統一 Agent 框架
     - 優點: 原生支持 Human-in-the-loop、Checkpoint、多 Agent 協作
     - 缺點: Preview 版本，API 可能變更
- **決定**: 選擇 Microsoft Agent Framework
- **原因**:
  - 原生支持 MVP 所需的核心功能 (F1-F14)
  - 統一了 Semantic Kernel + AutoGen 的能力
  - 專為企業級 Agent 編排設計
- **影響**:
  - 需要監控 Agent Framework 版本更新
  - 需要準備 API 變更的遷移計劃

---

## Decision #2: 本地開發優先策略

- **日期**: 2024-11-30
- **背景**: MVP 開發期間的雲端資源使用策略
- **選項**:
  1. **完全雲端開發** - 所有服務都使用 Azure
     - 優點: 環境一致
     - 缺點: 成本高，需要網路連接
  2. **本地開發優先** - 本地模擬大部分服務
     - 優點: 成本低，開發快速
     - 缺點: 可能有環境差異
- **決定**: 本地開發優先，僅使用 Azure OpenAI API
- **原因**:
  - 降低開發成本
  - Docker Compose 可模擬 PostgreSQL、Redis、RabbitMQ
  - Azure OpenAI API 成本可控 (~$50-200 整個 MVP)
- **影響**:
  - 需要確保 Docker 環境與 Azure 環境相容
  - 部署前需要集成測試

---

## Decision #3: Sprint 執行追蹤結構

- **日期**: 2024-11-30
- **背景**: 需要追蹤每個 Sprint 的開發進度和問題
- **選項**:
  1. **單一狀態文件** - 使用 sprint-status.yaml
  2. **分離追蹤結構** - 每個 Sprint 獨立文件夾
- **決定**: 建立 `sprint-execution/` 分離追蹤結構
- **原因**:
  - 更好的組織和可讀性
  - 可追蹤每日進度、問題、決策
  - 方便 Sprint 回顧
- **影響**:
  - 需要維護額外的文件
  - 提供更完整的開發歷史

---

## Decision Template

```markdown
## Decision #X: 決策標題

- **日期**: YYYY-MM-DD
- **背景**: 為什麼需要這個決策
- **選項**:
  1. 選項 A
     - 優點: ...
     - 缺點: ...
  2. 選項 B
     - 優點: ...
     - 缺點: ...
- **決定**: 選擇的選項
- **原因**: 為什麼選擇這個
- **影響**: 對後續開發的影響
```

---

## 決策統計

| 類別 | 數量 |
|------|------|
| 框架選擇 | 1 |
| 開發策略 | 1 |
| 流程改進 | 1 |
| **總計** | **3** |
