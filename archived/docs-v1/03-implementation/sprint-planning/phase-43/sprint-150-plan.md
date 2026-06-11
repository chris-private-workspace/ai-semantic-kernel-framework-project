# Sprint 150: Result Aggregation + Robustness + E2E 完整驗證

## Sprint 目標

1. ResultAggregator：用 LLM 將多個 Worker 的結果智能整合為完整回應
2. 錯誤處理：Worker 失敗、timeout、partial results 的 graceful handling
3. Rate Limiting：多 Worker 並行調 LLM 的速率控制
4. Swarm 完成後 UI：總結面板、Worker 貢獻摘要
5. E2E 完整驗證：真實 Swarm 場景端到端測試

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 43 — Agent Swarm 完整實現 |
| **Sprint** | 150 |
| **Story Points** | 10 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S150-1: ResultAggregator — 多 Worker 結果整合 (4 SP)

**作為** Chat 使用者
**我希望** 多個 Worker 的結果被智能整合為一個連貫的回應
**以便** 我看到一個完整的分析報告，而非零散的 Worker 輸出

**技術規格**:

**改動 1: `backend/src/integrations/swarm/result_aggregator.py` — 新建**
- `ResultAggregator` class：
  ```python
  class ResultAggregator:
      def __init__(self, llm_service: LLMServiceProtocol): ...

      async def aggregate(
          self,
          original_task: str,
          worker_results: list[WorkerResult],
          event_emitter: Optional[PipelineEventEmitter] = None,
      ) -> AggregatedResult:
          """用 LLM 整合所有 Worker 結果"""
          # 1. 發射 SWARM_AGGREGATING 事件
          # 2. 建立整合 prompt：
          #    - 原始任務描述
          #    - 每個 Worker 的角色 + 子任務 + 結果
          #    - 整合指令：歸納、去重、標明各專家觀點、建議行動
          # 3. 呼叫 LLM generate() 生成整合報告
          # 4. 如果任何 Worker 失敗，在報告中說明
          # 5. 發射 TEXT_DELTA 逐步串流整合結果
          # 6. 回傳 AggregatedResult
  ```
- `AggregatedResult` dataclass：
  ```python
  @dataclass
  class AggregatedResult:
      content: str              # 整合後的完整回應
      worker_summaries: list    # 每個 Worker 的貢獻摘要
      total_duration_ms: float
      total_tool_calls: int
      failed_workers: list      # 失敗的 Worker 資訊
      metadata: dict
  ```

**改動 2: `backend/src/integrations/hybrid/swarm_mode.py` — 接入 ResultAggregator**
- SwarmModeHandler.execute() 最後呼叫 ResultAggregator.aggregate()
- 整合結果作為 SWARM_COMPLETED 事件的 content
- 整合結果也作為 ExecutionHandler 的回傳

**改動 3: 整合 prompt 設計**
- 結構化整合模板：
  ```
  ## 分析報告

  ### 問題概述
  [基於所有 Worker 的輸入，總結核心問題]

  ### 各專家分析
  #### [Worker 1 角色名]: [子任務]
  [該 Worker 的關鍵發現]

  #### [Worker 2 角色名]: [子任務]
  [該 Worker 的關鍵發現]

  ### 綜合建議
  [基於所有 Worker 結果的行動建議，按優先級排列]

  ### 風險與注意事項
  [任何 Worker 提出的風險或警告]
  ```

### S150-2: 錯誤處理 + Rate Limiting (3 SP)

**作為** 系統管理者
**我希望** Swarm 執行中的錯誤被優雅處理，不會因一個 Worker 失敗而中斷整個流程
**以便** 即使部分 Worker 失敗，也能得到有意義的部分結果

**技術規格**:

**改動 1: Worker 層錯誤處理**
- Worker 執行超時（timeout）→ 回傳部分結果 + 錯誤說明
- Worker LLM 調用失敗 → 重試 1 次 → 失敗則標記 FAILED
- Worker tool 執行失敗 → 將錯誤作為 tool 結果回傳 LLM 繼續
- Worker 非預期異常 → catch + log + 回傳 WorkerResult(status="failed")

**改動 2: Swarm 層錯誤處理**
- 所有 Worker 失敗 → 回傳錯誤訊息（不嘗試 aggregate）
- 部分 Worker 失敗 → 用成功的 Worker 結果 aggregate + 標明缺失的分析
- 單個 Worker → 直接用該 Worker 結果（不需 aggregate）

**改動 3: Rate Limiting**
- `asyncio.Semaphore(max_concurrent)` 限制同時 LLM 調用數
- 配置項：`SWARM_MAX_CONCURRENT_WORKERS`（預設 3）
- 配置項：`SWARM_WORKER_TIMEOUT_SECONDS`（預設 60）
- 配置項：`SWARM_MAX_WORKERS`（預設 5）
- 在 LLM 調用之間加入隨機延遲（0.5-2s）避免 burst

**改動 4: 前端錯誤顯示**
- 失敗的 WorkerCard 顯示紅色邊框 + 錯誤圖標
- WorkerDetailDrawer 的失敗 tab 顯示錯誤詳情
- Swarm 整體部分失敗時，顯示黃色警告橫幅

### S150-3: Swarm 完成 UI + E2E 完整驗證 (3 SP)

**作為** 開發團隊
**我希望** Swarm 完成後有完整的 UI 總結，且全部場景端到端驗證通過
**以便** 確認 Swarm 功能完整可用

**技術規格**:

**改動 1: Swarm 完成後 UI**
- SWARM_COMPLETED 後，AgentSwarmPanel 顯示總結：
  - 總耗時、Worker 數量、成功/失敗數
  - 每個 Worker 的貢獻一句話摘要
  - 總工具調用次數
- 整合結果顯示在 Chat 訊息流中（作為 assistant message）
- 各 Worker 原始結果可從 WorkerDetailDrawer 查看

**改動 2: E2E 完整驗證場景**

| # | 場景 | 輸入 | 預期 |
|---|------|------|------|
| 1 | IT 故障排查（3 workers） | 「全面排查：網路延遲 + DB 超時 + API 500」 | 3 Workers 並行分析，整合報告 |
| 2 | 安全審計（2 workers） | 「對 Web 應用做安全評估：OWASP + 基礎設施」 | 2 Workers 各自分析，整合建議 |
| 3 | 變更評估（3 workers） | 「評估資料庫升級的影響：效能、相容性、回滾」 | 3 面向分析 + 風險評估 |
| 4 | 單一任務 fallback | 「檢查 DNS 設定」 | 自動判斷 1 Worker |
| 5 | Worker 失敗 | 模擬一個 Worker timeout | 部分結果 + 失敗標記 |

**改動 3: Playwright E2E 測試**
- 測試 Swarm 模式下 AgentSwarmPanel 正確顯示
- 測試 WorkerCard 即時更新（THINKING → TOOL_CALL → COMPLETED）
- 測試 WorkerDetailDrawer 打開/關閉/內容更新
- 測試 Swarm 完成後整合結果顯示
- 測試 Worker 失敗 graceful handling

## 驗收標準

- [ ] ResultAggregator 能用 LLM 整合多 Worker 結果為連貫報告
- [ ] 整合報告含：問題概述、各專家分析、綜合建議、風險注意事項
- [ ] Worker 失敗有 graceful fallback（部分結果 + 錯誤說明）
- [ ] 部分 Worker 失敗時仍能 aggregate 成功 Workers 的結果
- [ ] Rate limiting 正確限制並行 LLM 調用數
- [ ] 配置項可調：max_concurrent, timeout, max_workers
- [ ] Swarm 完成後 UI 總結面板正確顯示
- [ ] 整合結果作為 Chat 訊息顯示
- [ ] Worker 原始結果可從 Drawer 查看
- [ ] 5 個 E2E 場景全部通過
- [ ] 失敗 Worker 在 UI 中有視覺區分
- [ ] TypeScript 零錯誤、npm run build 通過
- [ ] `black . && isort . && flake8 .` 通過
- [ ] Playwright E2E 測試通過

## 相關連結

- [Phase 43 計劃](./README.md)
- [Sprint 149 Plan](./sprint-149-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 10
