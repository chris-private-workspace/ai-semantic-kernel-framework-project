# Phase 15 AG-UI UAT 測試規格

## 1. 測試目標

- 驗證 7 個 AG-UI 功能的界面表現
- 確認 SSE 串流的穩定性和延遲
- 測試 HITL 審批工作流的完整性
- 驗證狀態同步的準確性和衝突解決

## 2. 測試範圍

| Feature | 功能名稱 | 優先級 | 測試場景數 |
|---------|----------|--------|------------|
| 1 | Agentic Chat | P0 | 5 |
| 2 | Tool Rendering | P0 | 4 |
| 3 | Human-in-the-Loop | P0 | 5 |
| 4 | Generative UI | P1 | 3 |
| 5 | Tool-based UI | P1 | 6 |
| 6 | Shared State | P1 | 5 |
| 7 | Predictive State | P2 | 4 |
| **總計** | | | **32** |

### 優先級定義

- **P0 (Critical)**: 必須 100% 通過，阻擋發布
- **P1 (High)**: 必須 ≥90% 通過，可部分降級
- **P2 (Medium)**: 建議 ≥80% 通過，不阻擋發布

## 3. 測試環境

### 3.1 本地開發環境

| 組件 | 地址 | 說明 |
|------|------|------|
| Backend API | `http://localhost:8000` | FastAPI + Uvicorn |
| Frontend | `http://localhost:3000` | React + Vite |
| PostgreSQL | `localhost:5432` | 資料持久化 |
| Redis | `localhost:6379` | 快取 + 狀態存儲 |

### 3.2 瀏覽器支援

| 瀏覽器 | 版本 | 狀態 |
|--------|------|------|
| Chrome | 120+ | 主要測試 |
| Edge | 120+ | 次要測試 |
| Firefox | 120+ | 兼容性測試 |
| Safari | 17+ | 選擇性測試 |

## 4. 測試前置條件

### 4.1 服務啟動檢查

```bash
# 檢查後端健康
curl http://localhost:8000/health

# 檢查 AG-UI 端點
curl http://localhost:8000/api/v1/ag-ui/health
```

### 4.2 資料準備

- 至少一個測試 Thread ID
- 測試用 Tool 定義 (calculate, search, file_operation)
- 審批測試用的高風險 Tool 配置

## 5. 驗收標準

### 5.1 功能性驗收

| 指標 | P0 標準 | P1 標準 | P2 標準 |
|------|---------|---------|---------|
| 測試通過率 | 100% | ≥90% | ≥80% |
| 關鍵功能覆蓋 | 100% | 100% | ≥90% |

### 5.2 效能驗收

| 指標 | 目標值 | 容許範圍 |
|------|--------|----------|
| SSE 事件延遲 | < 100ms | < 200ms |
| 狀態同步延遲 | < 50ms | < 100ms |
| 樂觀更新回滾 | < 100ms | < 200ms |
| UI 組件渲染 | < 200ms | < 500ms |
| SSE 連接穩定性 | > 99.5% | > 99% |

### 5.3 UI/UX 驗收

- [ ] 串流文字有打字效果
- [ ] 工具調用有清晰的視覺區分
- [ ] 審批對話框有風險等級顯示
- [ ] 進度指示器動畫流暢
- [ ] 表單驗證有即時反饋
- [ ] 狀態衝突有明確提示

## 6. 測試工具

### 6.1 前端測試

- **Playwright**: E2E 自動化測試
- **Chrome DevTools**: Network/Performance 分析
- **React DevTools**: 組件狀態檢查

### 6.2 後端測試

- **pytest**: API 單元測試
- **httpx**: 異步 HTTP 客戶端
- **SSE Client**: 串流事件驗證

### 6.3 監控工具

- **Network Tab**: SSE 連接監控
- **Console**: 事件日誌
- **StateDebugger**: 內建狀態調試器

## 7. 測試執行流程

```
1. 環境準備
   ├── 啟動 Docker 服務
   ├── 啟動後端 API
   └── 啟動前端開發服務器

2. 冒煙測試
   ├── 健康檢查
   ├── SSE 連接測試
   └── 基本對話測試

3. 功能測試
   ├── Feature 1: Agentic Chat
   ├── Feature 2: Tool Rendering
   ├── Feature 3: Human-in-the-Loop
   ├── Feature 4: Generative UI
   ├── Feature 5: Tool-based UI
   ├── Feature 6: Shared State
   └── Feature 7: Predictive State

4. 整合測試
   ├── 完整對話流程
   ├── 多功能組合場景
   └── 錯誤恢復測試

5. 效能測試
   ├── 延遲測量
   ├── 連接穩定性
   └── 並發測試

6. 報告生成
   ├── 測試結果彙總
   ├── 缺陷記錄
   └── 改進建議
```

## 8. 測試報告

測試完成後，使用 `uat-report-template.md` 模板生成報告，包含：

- 測試執行摘要
- 各功能測試結果
- 效能數據
- 發現的問題
- 改進建議

## 9. 相關文檔

- [詳細測試場景](./uat-test-scenarios.md)
- [測試驗收清單](./uat-checklist.md)
- [報告模板](./uat-report-template.md)
