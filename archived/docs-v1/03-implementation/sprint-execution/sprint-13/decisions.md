# Sprint 13 Decisions Log

**Sprint**: 13 - 基礎設施準備
**記錄目的**: 追蹤所有重要的架構和實現決策

---

## Decision Template

```
### [DECISION-XX] 決策標題
**日期**: YYYY-MM-DD
**狀態**: 提議 | 已採納 | 已廢棄
**影響範圍**: 低 | 中 | 高

**背景**:
描述決策的背景和需要解決的問題

**選項**:
1. 選項 A - 描述
2. 選項 B - 描述

**決定**:
最終採用的方案

**理由**:
選擇該方案的原因

**影響**:
該決定對系統的影響
```

---

## Decisions

### [DECISION-01] 適配層架構設計
**日期**: 2025-12-05
**狀態**: 已採納
**影響範圍**: 高

**背景**:
Phase 2 實現了完全自定義的並行執行、群組聊天、動態規劃等功能，但這些實現沒有使用 Microsoft Agent Framework 的官方 API。需要決定如何整合官方 API。

**選項**:
1. 直接替換 - 完全刪除自定義實現，直接使用官方 API
2. 適配層 - 建立適配層包裝官方 API，保持現有介面不變
3. 並行運行 - 自定義和官方實現並存

**決定**:
採用選項 2 - 建立適配層 (`src/integrations/agent_framework/`)

**理由**:
- 隔離 Agent Framework API 變更的影響
- 保持現有 API 端點向後兼容
- 允許漸進式遷移
- 便於未來版本升級

**影響**:
- 需要為每個官方 Builder 創建對應的 Adapter
- 現有 API 路由層不需要大幅修改
- 測試可以針對適配層進行

---

### [DECISION-02] CheckpointStorage 實現策略
**日期**: 2025-12-05
**狀態**: 已採納
**影響範圍**: 中

**背景**:
Agent Framework 提供 CheckpointStorage 抽象介面，需要決定如何實現。

**選項**:
1. 純 PostgreSQL - 所有檢查點直接存到資料庫
2. 純 Redis - 所有檢查點存到 Redis
3. 混合方案 - Redis 緩存 + PostgreSQL 持久化

**決定**:
採用選項 3 - 混合方案

**理由**:
- Redis 提供快速讀取，適合頻繁訪問的活動檢查點
- PostgreSQL 提供持久化和事務支持
- 符合現有基礎設施架構

**影響**:
- 需要實現 `PostgresCheckpointStorage` 類
- 需要實現 `RedisCheckpointCache` 類
- 需要實現 `CachedCheckpointStorage` 組合類

---

### [DECISION-03] 模組目錄結構
**日期**: 2025-12-05
**狀態**: 已採納
**影響範圍**: 中

**背景**:
需要決定 Agent Framework 整合模組的目錄結構。

**選項**:
1. 扁平結構 - 所有文件在同一目錄
2. 分層結構 - 按功能分子目錄

**決定**:
採用選項 2 - 分層結構

```
backend/src/integrations/agent_framework/
├── __init__.py           # 統一導出
├── base.py               # 基礎類
├── exceptions.py         # 異常定義
├── workflow.py           # WorkflowAdapter
├── checkpoint.py         # CheckpointStorage
└── builders/             # 各種 Builder 適配器
    ├── __init__.py
    ├── concurrent.py     # ConcurrentBuilderAdapter
    ├── groupchat.py      # GroupChatBuilderAdapter
    ├── handoff.py        # HandoffBuilderAdapter
    ├── magentic.py       # MagenticBuilderAdapter
    └── workflow_executor.py  # WorkflowExecutorAdapter
```

**理由**:
- 清晰的職責分離
- 便於導航和維護
- 支持漸進式添加新適配器

**影響**:
- Sprint 13 只建立基礎結構
- Sprint 14-18 逐步添加各個 Builder 適配器

---

## Pending Decisions

_暫無待定決策_

---

## 相關文件

- [Sprint 13 Progress](./progress.md)
- [Phase 3 Refactoring Plan](../../../../claudedocs/PHASE3-REFACTORING-PLAN.md)
