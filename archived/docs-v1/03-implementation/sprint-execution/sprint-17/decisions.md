# Sprint 17 決策記錄

**Sprint**: 17 - MagenticBuilder 重構 (Magentic One)
**開始日期**: 2025-12-05

---

## DEC-17-001: 架構策略選擇

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
需要決定如何將現有 DynamicPlanner 遷移至 Agent Framework MagenticBuilder (Magentic One)。

### 選項

1. **完全替換**: 直接使用 MagenticBuilder 替換 DynamicPlanner
2. **並行架構**: 保留原有實現 + 新增適配器層
3. **漸進遷移**: 逐步將功能遷移到新 API

### 決定
選擇 **並行架構** (選項 2)

### 理由
1. 與 Sprint 13-16 保持一致的遷移策略
2. 提供向後兼容性
3. 允許漸進式測試和驗證
4. 降低遷移風險
5. MagenticBuilder API 較複雜，需要更多時間適應

### 影響
- 需要維護適配器層
- 代碼量增加但風險降低
- 用戶可選擇使用新舊 API

---

## DEC-17-002: Manager 實現策略

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
Agent Framework 提供兩種 Manager 選項：
1. `MagenticManagerBase` - 抽象基類
2. `StandardMagenticManager` - 默認 LLM 管理器

### 決定
- 創建 `MagenticManagerAdapter` 包裝我們的 DynamicPlanner 邏輯
- 支持 `StandardMagenticManager` 直接使用
- 提供 `CustomMagenticManager` 自定義實現

### 實現策略
```python
# 選項 1: 使用 StandardMagenticManager (推薦)
adapter.with_standard_manager(agent=manager_agent)

# 選項 2: 使用自定義 Manager
adapter.with_manager(custom_manager)
```

---

## DEC-17-003: Ledger 系統整合

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
Magentic One 使用兩個 Ledger 系統：
1. **Task Ledger**: Facts + Plan
2. **Progress Ledger**: 進度評估 (is_satisfied, is_in_loop, is_progress, next_speaker, instruction)

### 決定
- 保留 Agent Framework 的 Ledger 格式
- 創建轉換函數支持我們的 DynamicPlanner 格式
- 支持自定義 Ledger prompts

### 映射表

| Agent Framework | 我們的實現 |
|-----------------|-----------|
| Task Ledger.facts | DynamicPlanner.facts |
| Task Ledger.plan | DynamicPlanner.plan |
| Progress Ledger.is_satisfied | is_task_complete |
| Progress Ledger.is_in_loop | is_stalled |
| Progress Ledger.next_speaker | select_next_agent |
| Progress Ledger.instruction | generate_instruction |

---

## DEC-17-004: Human Intervention 整合

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
MagenticBuilder 支持三種 Human Intervention：
1. `PLAN_REVIEW` - 審核初始計劃
2. `TOOL_APPROVAL` - 批准工具調用
3. `STALL` - 處理停滯情況

### 決定
- 完整實現所有三種 Intervention
- 與現有 Checkpoint 系統整合
- 支持 `with_plan_review(enable=True)` 和 `with_stall_intervention(enable=True)`

### 實現優先級
1. PLAN_REVIEW - 最常用
2. STALL - 重要的錯誤恢復
3. TOOL_APPROVAL - 可選功能

---

## 待決策

### PENDING-001: 並發執行策略
**問題**: 是否在 Magentic 工作流中支持並發 Agent 執行？
**狀態**: 待討論
**備註**: Agent Framework 目前不支持並發，但我們的 DynamicPlanner 可能需要

---

## Sprint 17 決策摘要

| 決策 ID | 主題 | 狀態 |
|---------|------|------|
| DEC-17-001 | 並行架構策略 | ✅ 已決定 |
| DEC-17-002 | Manager 實現策略 | ✅ 已決定 |
| DEC-17-003 | Ledger 系統整合 | ✅ 已決定 |
| DEC-17-004 | Human Intervention 整合 | ✅ 已決定 |
| PENDING-001 | 並發執行策略 | ⏳ 待討論 |
