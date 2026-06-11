# Sprint 150 Checklist: Result Aggregation + Robustness + E2E

**Sprint**: 150 | **Phase**: 43 | **Story Points**: 10
**Plan**: [sprint-150-plan.md](./sprint-150-plan.md)

---

## S150-1: ResultAggregator — 多 Worker 結果整合 (4 SP)

### result_aggregator.py 新建
- [ ] `swarm/result_aggregator.py` — ResultAggregator class
- [ ] aggregate() 用 LLM 整合所有 Worker 結果
- [ ] 發射 SWARM_AGGREGATING 事件
- [ ] 結構化整合模板（問題概述 + 專家分析 + 綜合建議 + 風險）
- [ ] AggregatedResult dataclass（content, summaries, duration, tool_calls, failed）
- [ ] TEXT_DELTA 逐步串流整合結果

### SwarmModeHandler 接入
- [ ] execute() 最後呼叫 ResultAggregator.aggregate()
- [ ] 整合結果作為 SWARM_COMPLETED 事件 content
- [ ] 整合結果回傳 ExecutionHandler

### 整合 prompt
- [ ] 含原始任務、各 Worker 角色 + 結果
- [ ] 去重、歸納、標明來源、按優先級排序
- [ ] 失敗 Worker 在報告中說明

## S150-2: 錯誤處理 + Rate Limiting (3 SP)

### Worker 層
- [ ] timeout → 部分結果 + 錯誤說明
- [ ] LLM 失敗 → 重試 1 次 → FAILED
- [ ] tool 執行失敗 → 錯誤作為 tool 結果繼續
- [ ] 非預期異常 → catch + log + WorkerResult(failed)

### Swarm 層
- [ ] 全部失敗 → 錯誤訊息（不 aggregate）
- [ ] 部分失敗 → 用成功 Workers aggregate + 標明缺失
- [ ] 單 Worker → 直接用結果

### Rate Limiting
- [ ] asyncio.Semaphore 限制並行 LLM 調用
- [ ] SWARM_MAX_CONCURRENT_WORKERS 配置（預設 3）
- [ ] SWARM_WORKER_TIMEOUT_SECONDS 配置（預設 60）
- [ ] SWARM_MAX_WORKERS 配置（預設 5）
- [ ] LLM 調用間隨機延遲（避免 burst）

### 前端錯誤顯示
- [ ] 失敗 WorkerCard 紅色邊框 + 錯誤圖標
- [ ] WorkerDetailDrawer 失敗 tab 錯誤詳情
- [ ] 部分失敗黃色警告橫幅

## S150-3: Swarm 完成 UI + E2E 驗證 (3 SP)

### 完成後 UI
- [ ] AgentSwarmPanel 總結：耗時、Worker 數、成功/失敗
- [ ] 每個 Worker 貢獻一句話摘要
- [ ] 整合結果作為 Chat assistant message 顯示
- [ ] Worker 原始結果可從 Drawer 查看

### E2E 場景驗證
- [ ] 場景 1: IT 故障排查（3 workers 並行）
- [ ] 場景 2: 安全審計（2 workers）
- [ ] 場景 3: 變更評估（3 面向）
- [ ] 場景 4: 單一任務 fallback（1 worker）
- [ ] 場景 5: Worker 失敗 graceful handling

### Playwright E2E 測試
- [ ] AgentSwarmPanel 正確顯示
- [ ] WorkerCard 即時更新（THINKING → TOOL_CALL → COMPLETED）
- [ ] WorkerDetailDrawer 打開/關閉/內容更新
- [ ] Swarm 完成後整合結果顯示
- [ ] Worker 失敗 graceful handling

## 驗收測試

- [ ] ResultAggregator 整合為連貫報告
- [ ] 報告含問題概述 + 專家分析 + 建議 + 風險
- [ ] Worker 失敗 graceful fallback
- [ ] 部分失敗仍可 aggregate
- [ ] Rate limiting 正確限制
- [ ] 配置項可調
- [ ] 完成後 UI 總結
- [ ] 5 個 E2E 場景通過
- [ ] 失敗 Worker UI 區分
- [ ] TypeScript 零錯誤
- [ ] Playwright 測試通過
- [ ] `black . && isort . && flake8 .` 通過

---

**狀態**: 📋 計劃中
