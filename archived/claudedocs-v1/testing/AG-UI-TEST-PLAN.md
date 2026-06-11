# AG-UI 功能測試計劃

> **版本**: 1.0
> **創建日期**: 2026-01-22
> **目的**: 系統性驗證 /chat 頁面的所有 AG-UI 功能

---

## 測試環境準備

### 前置條件
```bash
# 1. 啟動所有服務
python scripts/dev.py start

# 2. 確認服務狀態
python scripts/dev.py status

# 3. 訪問測試頁面
# http://localhost:3005/chat
```

### 測試帳號
- 使用已註冊的測試帳號登入
- 或使用 Guest 模式 (如支援)

---

## Phase A: 基礎功能測試

### A1. Agentic Chat (AG-UI #1) - SSE Streaming

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| 基本對話 | 輸入 "Hello, what can you do?" | 收到流式響應 | ⬜ |
| 中文對話 | 輸入 "你好，請介紹你自己" | 收到中文流式響應 | ⬜ |
| 長對話 | 連續發送 5+ 條消息 | 對話歷史正確顯示 | ⬜ |
| 取消流 | 發送消息後點擊取消 | 流式傳輸停止 | ⬜ |
| 連接狀態 | 觀察狀態欄 | 顯示 Connected/Disconnected | ⬜ |

**測試命令**:
```
測試輸入 1: "Hello, what can you do?"
測試輸入 2: "Please explain how AI agents work"
```

### A2. Tool Rendering (AG-UI #2)

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| Tool Call 顯示 | 請求執行工具操作 | 顯示 ToolCallCard | ⬜ |
| 參數顯示 | 觀察 Tool Call 詳情 | 顯示工具名稱和參數 | ⬜ |
| 執行狀態 | 觀察狀態變化 | pending → executing → completed | ⬜ |
| 結果顯示 | 等待工具完成 | 顯示執行結果 | ⬜ |

**測試命令**:
```
測試輸入: "Search the web for latest AI news"
測試輸入: "Read the file package.json"
```

### A3. Human-in-the-Loop (AG-UI #3)

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| 低風險審批 | 觸發低風險工具 | 顯示 InlineApproval | ⬜ |
| 高風險對話框 | 觸發高風險工具 | 彈出 ApprovalDialog | ⬜ |
| 批准操作 | 點擊 Approve | 工具繼續執行 | ⬜ |
| 拒絕操作 | 點擊 Reject | 工具執行取消 | ⬜ |
| 風險標籤 | 觀察風險指示 | 顯示 RiskBadge (low/medium/high) | ⬜ |

**測試命令**:
```
測試輸入: "Write a test file to /tmp/test.txt"  (high risk)
測試輸入: "Execute the command: ls -la"  (high risk)
```

---

## Phase B: 進階功能測試

### B1. Generative UI (AG-UI #4)

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| 動態 UI 渲染 | 後端發送 ui_component | ChatArea 中顯示組件 | ⬜ |
| Form 組件 | 請求創建表單 | 顯示 DynamicForm | ⬜ |
| Chart 組件 | 請求創建圖表 | 顯示 DynamicChart | ⬜ |
| Card 組件 | 請求創建卡片 | 顯示 DynamicCard | ⬜ |
| Table 組件 | 請求創建表格 | 顯示 DynamicTable | ⬜ |

**測試命令**:
```
測試輸入: "Create a form to collect user feedback"
測試輸入: "Show a chart of monthly sales data"
測試輸入: "Display a table of recent orders"
```

### B2. Tool-based UI (AG-UI #5)

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| DynamicForm 提交 | 填寫並提交表單 | 觸發 onSubmit 事件 | ⬜ |
| DynamicTable 排序 | 點擊表格標題排序 | 數據重新排序 | ⬜ |
| DynamicTable 選擇 | 點擊表格行 | 觸發 onRowSelect | ⬜ |
| DynamicChart 互動 | 點擊數據點 | 觸發 onDataPointClick | ⬜ |

### B3. Shared State (AG-UI #6)

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| STATE_SNAPSHOT | 開始新會話 | 接收完整狀態快照 | ⬜ |
| STATE_DELTA | 狀態變更 | 接收增量更新 | ⬜ |
| 狀態同步 | 多次操作後檢查 | 前後端狀態一致 | ⬜ |
| 版本控制 | 觀察版本號 | 版本遞增正確 | ⬜ |

### B4. Predictive Updates (AG-UI #7)

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| Optimistic Update | 發送請求 | 立即顯示預測狀態 | ⬜ |
| 確認成功 | 後端確認 | 預測狀態確認 | ⬜ |
| 回滾 | 後端拒絕 | 狀態回滾到原始 | ⬜ |
| 衝突處理 | 觸發衝突 | 顯示衝突提示 | ⬜ |

---

## Phase C: 雙模式測試

### C1. Chat Mode

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| 模式切換 | 點擊 Chat 按鈕 | 切換到 Chat 模式 | ⬜ |
| 佈局 | 觀察頁面佈局 | 全寬 ChatArea，無 SidePanel | ⬜ |
| 狀態欄 | 觀察 StatusBar | 顯示 Mode: Chat | ⬜ |

### C2. Workflow Mode

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| 模式切換 | 點擊 Workflow 按鈕 | 切換到 Workflow 模式 | ⬜ |
| 佈局 | 觀察頁面佈局 | ChatArea + WorkflowSidePanel | ⬜ |
| StepProgress | 觸發工作流 | 顯示步驟進度 | ⬜ |
| ToolCallTracker | 執行工具 | SidePanel 顯示工具追蹤 | ⬜ |
| CheckpointList | 創建檢查點 | SidePanel 顯示檢查點 | ⬜ |

**測試命令**:
```
測試輸入: "Run a multi-step analysis workflow"
測試輸入: "Execute the data processing pipeline"
```

---

## Phase D: 整合測試

### D1. SSE 連接穩定性

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| 長時間連接 | 保持連接 5+ 分鐘 | 連接穩定 | ⬜ |
| 自動重連 | 短暫中斷網路 | 自動重新連接 | ⬜ |
| 錯誤恢復 | 後端返回錯誤 | 顯示錯誤並可恢復 | ⬜ |

### D2. 多 Thread 測試

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| 創建 Thread | 點擊新對話 | 創建新 Thread | ⬜ |
| 切換 Thread | 選擇不同 Thread | 消息正確切換 | ⬜ |
| Thread 持久化 | 刷新頁面 | Thread 列表保留 | ⬜ |

### D3. 文件附件 (Sprint 75-76)

| 測試項目 | 步驟 | 預期結果 | 狀態 |
|---------|------|---------|------|
| 文件上傳 | 附加文件 | 顯示附件預覽 | ⬜ |
| 帶附件發送 | 發送帶附件消息 | 消息和文件正確處理 | ⬜ |
| 文件下載 | 點擊生成的文件 | 文件正確下載 | ⬜ |

---

## 測試報告模板

### 測試執行記錄

| 日期 | 測試人員 | Phase | 通過/失敗 | 備註 |
|------|---------|-------|----------|------|
| 2026-01-xx | | A | /10 | |
| 2026-01-xx | | B | /15 | |
| 2026-01-xx | | C | /8 | |
| 2026-01-xx | | D | /7 | |

### 已知問題追蹤

| ID | 問題描述 | 嚴重程度 | 狀態 |
|----|---------|---------|------|
| | | | |

---

## 自動化測試 (可選)

### Playwright E2E 測試腳本位置
```
backend/tests/e2e/ag_ui/test_full_flow.py
```

### 執行自動化測試
```bash
cd backend
pytest tests/e2e/ag_ui/ -v
```

---

**Last Updated**: 2026-01-22
