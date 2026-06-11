# Sprint 7 Checklist: 並行執行引擎 (Concurrent Execution Engine)

**Sprint 目標**: 實現工作流並行執行能力，支援 Fork-Join 模式和死鎖檢測
**週期**: Week 15-16
**總點數**: 34 點
**Phase 2 功能**: P2-F1 並行執行 + P2-F2 增強閘道
**狀態**: ✅ 已完成 (34/34 點)

---

## 快速驗證命令

```bash
# 驗證並行執行模組
python -c "from src.domain.orchestration.concurrent import ConcurrentExecutor; print('OK')"

# 驗證並行 API
curl http://localhost:8000/api/v1/concurrent/status

# 執行 Fork-Join 工作流
curl -X POST http://localhost:8000/api/v1/concurrent/execute \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "uuid", "mode": "all"}'

# 運行並行執行測試
cd backend && pytest tests/unit/test_concurrent*.py tests/unit/test_gateway*.py -v

# 效能測試 - 驗證 3x 吞吐量
cd backend && pytest tests/performance/test_concurrent_throughput.py -v
```

---

## S7-1: ConcurrentExecutor 並行執行器 (13 點) ✅

### 核心執行器 (src/domain/orchestration/concurrent/)
- [ ] 創建 `executor.py`
  - [ ] ExecutionMode 枚舉
    - [ ] ALL - 等待所有完成
    - [ ] ANY - 任一完成即返回
    - [ ] MAJORITY - 多數完成
    - [ ] FIRST_SUCCESS - 首個成功
  - [ ] BranchResult 數據類
    - [ ] branch_id 屬性
    - [ ] status 屬性
    - [ ] result 屬性
    - [ ] error 屬性
    - [ ] duration_ms 屬性
  - [ ] ConcurrentExecutor 類
    - [ ] __init__() 初始化方法
    - [ ] execute_parallel() 並行執行方法
    - [ ] _execute_single_branch() 單分支執行
    - [ ] _wait_for_completion() 等待完成邏輯
    - [ ] _merge_results() 結果合併

### 狀態管理 (src/domain/orchestration/concurrent/)
- [ ] 創建 `state_manager.py`
  - [ ] ConcurrentStateManager 類
  - [ ] create_branches() 創建分支方法
  - [ ] update_branch_status() 更新狀態
  - [ ] get_branch_status() 獲取狀態
  - [ ] is_all_completed() 檢查完成
  - [ ] get_completed_count() 計算完成數
  - [ ] cleanup() 清理方法

### 超時處理
- [ ] 創建 `timeout_handler.py`
  - [ ] TimeoutHandler 類
  - [ ] set_timeout() 設置超時
  - [ ] check_timeout() 檢查超時
  - [ ] cancel_on_timeout() 超時取消
  - [ ] 支援分支級別超時
  - [ ] 支援全局超時

### 驗證標準
- [ ] Fork 後多分支並行執行
- [ ] ALL 模式等待所有分支完成
- [ ] ANY 模式首個完成即返回
- [ ] 分支執行時間統計正確
- [ ] 超時正確觸發取消

---

## S7-2: ParallelGateway 並行閘道 (8 點) ✅

### Fork 閘道 (src/domain/orchestration/gateway/)
- [ ] 創建 `parallel_fork.py`
  - [ ] ParallelForkGateway 類
  - [ ] split() 分流方法
  - [ ] validate_outgoing_edges() 驗證輸出邊
  - [ ] distribute_context() 分發上下文
  - [ ] 支援動態分支數量

### Join 閘道 (src/domain/orchestration/gateway/)
- [ ] 創建 `parallel_join.py`
  - [ ] JoinMode 枚舉
    - [ ] WAIT_ALL - 等待全部
    - [ ] WAIT_ANY - 等待任一
    - [ ] WAIT_N - 等待 N 個
  - [ ] ParallelJoinGateway 類
  - [ ] wait_and_merge() 等待合併方法
  - [ ] _check_completion() 完成檢查
  - [ ] _merge_branch_outputs() 輸出合併
  - [ ] 支援部分失敗處理

### 閘道協調
- [ ] 創建 `gateway_coordinator.py`
  - [ ] GatewayCoordinator 類
  - [ ] register_fork() 註冊 Fork
  - [ ] register_join() 註冊 Join
  - [ ] match_fork_join() 配對閘道
  - [ ] validate_structure() 結構驗證

### 驗證標準
- [ ] Fork 正確分發到多個分支
- [ ] Join 正確等待並合併結果
- [ ] Fork-Join 配對驗證正確
- [ ] 部分分支失敗時 Join 正確處理
- [ ] 上下文在 Fork/Join 間正確傳遞

---

## S7-3: DeadlockDetector 死鎖檢測 (5 點) ✅

### 死鎖檢測器 (src/domain/orchestration/concurrent/)
- [ ] 創建 `deadlock_detector.py`
  - [ ] DeadlockDetector 類
  - [ ] build_wait_graph() 建立等待圖
  - [ ] detect_cycle() 檢測循環
  - [ ] _dfs_detect() DFS 檢測算法
  - [ ] get_deadlock_info() 獲取死鎖信息

### 死鎖解決
- [ ] 創建 `deadlock_resolver.py`
  - [ ] DeadlockResolver 類
  - [ ] resolve() 解決死鎖方法
  - [ ] _select_victim() 選擇犧牲者
  - [ ] _rollback_branch() 回滾分支
  - [ ] 支援自動解決策略

### 監控整合
- [ ] 死鎖檢測定時運行
- [ ] 死鎖事件通知
- [ ] 死鎖統計記錄
- [ ] 日誌輸出

### 驗證標準
- [ ] 正確檢測循環等待死鎖
- [ ] 死鎖解決不影響其他分支
- [ ] 死鎖信息包含完整上下文
- [ ] 監控指標正確記錄

---

## S7-4: Concurrent API 路由 (8 點) ✅

### API 路由 (src/api/v1/concurrent/)
- [ ] 創建 `routes.py`
  - [ ] POST /concurrent/execute - 執行並行任務
  - [ ] GET /concurrent/{id}/status - 獲取執行狀態
  - [ ] GET /concurrent/{id}/branches - 獲取分支狀態
  - [ ] POST /concurrent/{id}/cancel - 取消執行
  - [ ] POST /concurrent/{id}/branches/{bid}/cancel - 取消特定分支
  - [ ] GET /concurrent/stats - 獲取統計數據

### 請求/響應 Schema
- [ ] 創建 `schemas.py`
  - [ ] ConcurrentExecuteRequest
    - [ ] workflow_id
    - [ ] inputs
    - [ ] mode (all/any/majority)
    - [ ] timeout_seconds
  - [ ] ConcurrentExecuteResponse
    - [ ] execution_id
    - [ ] status
    - [ ] branches
  - [ ] BranchStatusResponse
  - [ ] ConcurrentStatsResponse

### WebSocket 支援
- [ ] 創建 `websocket.py`
  - [ ] 實時分支狀態推送
  - [ ] 執行進度通知
  - [ ] 錯誤事件通知

### 驗證標準
- [ ] API 正確處理並行執行請求
- [ ] 分支狀態即時更新
- [ ] 取消操作正確執行
- [ ] WebSocket 連接穩定
- [ ] API 文檔完整

---

## 測試完成 ✅

### 單元測試
- [ ] test_concurrent_executor.py
  - [ ] test_execute_parallel_all_mode
  - [ ] test_execute_parallel_any_mode
  - [ ] test_execute_parallel_majority_mode
  - [ ] test_execute_with_timeout
  - [ ] test_branch_failure_handling
- [ ] test_parallel_gateway.py
  - [ ] test_fork_gateway_split
  - [ ] test_join_gateway_wait_all
  - [ ] test_join_gateway_wait_any
  - [ ] test_fork_join_coordination
- [ ] test_deadlock_detector.py
  - [ ] test_detect_simple_cycle
  - [ ] test_detect_complex_deadlock
  - [ ] test_no_deadlock_case
  - [ ] test_deadlock_resolution
- [ ] test_concurrent_state.py
  - [ ] test_branch_state_transitions
  - [ ] test_concurrent_updates
  - [ ] test_cleanup

### 整合測試
- [ ] test_concurrent_api.py
  - [ ] test_execute_concurrent_workflow
  - [ ] test_get_branch_status
  - [ ] test_cancel_execution
  - [ ] test_websocket_updates

### 效能測試
- [ ] test_concurrent_performance.py
  - [ ] test_throughput_improvement (目標: 3x)
  - [ ] test_latency_under_load
  - [ ] test_max_concurrent_branches

### 覆蓋率
- [ ] 單元測試覆蓋率 >= 85%
- [ ] 整合測試覆蓋主要流程

---

## 資料庫遷移 ⏳

### 遷移腳本
- [ ] 創建 `007_concurrent_execution.sql`
  - [ ] concurrent_executions 表
  - [ ] execution_branches 表
  - [ ] branch_dependencies 表
  - [ ] deadlock_events 表
  - [ ] 相關索引

### 驗證
- [ ] 遷移腳本可正確執行
- [ ] 回滾腳本可用
- [ ] 索引效能測試通過

---

## 文檔完成 ⏳

### API 文檔
- [ ] Swagger 並行執行 API 文檔
- [ ] 請求/響應範例
- [ ] 錯誤碼說明

### 開發者文檔
- [ ] 並行執行使用指南
  - [ ] Fork-Join 模式說明
  - [ ] 執行模式比較
  - [ ] 錯誤處理指南
- [ ] 閘道配置指南
  - [ ] Fork 閘道配置
  - [ ] Join 閘道配置
  - [ ] 超時設置
- [ ] 死鎖處理指南
  - [ ] 死鎖原因分析
  - [ ] 預防建議
  - [ ] 解決方案

---

## Sprint 完成標準

### 必須完成 (Must Have)
- [ ] ConcurrentExecutor 可並行執行多分支
- [ ] Fork/Join 閘道正確運作
- [ ] 死鎖檢測功能可用
- [ ] API 完整可用
- [ ] 測試覆蓋率 >= 85%

### 應該完成 (Should Have)
- [ ] 3x 吞吐量提升達成
- [ ] WebSocket 實時更新
- [ ] 文檔完整

### 可以延後 (Could Have)
- [ ] 進階死鎖解決策略
- [ ] 可視化監控面板

---

## 依賴確認

### 前置 Sprint
- [ ] Phase 1 (Sprint 1-6) 完成
  - [ ] 基礎 Workflow 執行正常
  - [ ] Agent 服務可用
  - [ ] 狀態機穩定運作

### 外部依賴
- [ ] asyncio 並發支援確認
- [ ] Redis 連接池配置 (用於狀態共享)
- [ ] PostgreSQL 行鎖支援確認

---

## Sprint 7 完成統計

| Story | 點數 | 狀態 | 測試數 |
|-------|------|------|--------|
| S7-1: ConcurrentExecutor | 13 | ✅ | 63 |
| S7-2: ParallelGateway | 8 | ✅ | 25 |
| S7-3: DeadlockDetector | 5 | ✅ | 32 |
| S7-4: Concurrent API | 8 | ✅ | 41 |
| **總計** | **34** | **✅ 完成** | **161** |

---

## 相關連結

- [Sprint 7 Plan](./sprint-7-plan.md) - 詳細計劃
- [Phase 2 Overview](./README.md) - Phase 2 概述
- [Sprint 8 Plan](./sprint-8-plan.md) - 後續 Sprint
- [Phase 1 Sprint 6](../sprint-6-checklist.md) - 前置 Sprint
