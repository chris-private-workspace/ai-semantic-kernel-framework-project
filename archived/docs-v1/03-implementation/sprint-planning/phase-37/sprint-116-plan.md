# Sprint 116: Swarm 整合 + 可觀測性接通

## Sprint 目標

1. Circuit Breaker（LLM API 宕機降級）
2. Swarm Feature Flag 啟用
3. ObservabilityBridge（G3/G4/G5 STUB 接通）
4. Circuit Breaker 全域 singleton + performance 模組匯出
5. Orchestrator 匯出更新

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 37 — E2E Assembly B |
| **Sprint** | 116 |
| **Story Points** | 12 點 |
| **狀態** | ✅ 完成 |

## Sprint 概述

Sprint 116 是 Phase 37 的最後一個 Sprint，專注於將 Swarm 整合到主流程並完成端到端可觀測性。包含 Circuit Breaker 三態轉換（CLOSED → OPEN → HALF_OPEN）與 async 函數保護、Swarm Feature Flag 啟用（SwarmExecutionConfig.enabled = True）、ObservabilityBridge（G3 Patrol / G4 Correlation / G5 RootCause STUB 接通 + protected_llm_call）、全域 singleton 與模組匯出。

## User Stories

### S116-1: Circuit Breaker (4 SP)

**作為** 後端開發者
**我希望** LLM API 呼叫有斷路器保護
**以便** LLM 服務宕機時自動降級，避免連鎖故障

**技術規格**:
- 新增 `backend/src/core/performance/circuit_breaker.py`
- `CircuitState` enum: CLOSED / OPEN / HALF_OPEN
- `CircuitBreaker` class:
  - 三態轉換: CLOSED →(failures >= threshold)→ OPEN →(timeout)→ HALF_OPEN →(success)→ CLOSED
  - `call(func, fallback=...)` — async 函數保護，支援 fallback 降級
  - `_on_success()` / `_on_failure()` — 自動狀態轉換
  - `reset()` — 手動重置
  - `get_stats()` — 統計數據
  - `asyncio.Lock` 保護狀態轉換的線程安全
- `CircuitOpenError` exception
- `get_llm_circuit_breaker()` — 全域 singleton（threshold=5, timeout=60s, recovery=2）

### S116-2: Swarm Feature Flag (2 SP)

**作為** 平台管理員
**我希望** Swarm 功能正式啟用為 first-class execution mode
**以便** Orchestrator 能透過 dispatch_swarm() 路徑執行多 Agent 協作任務

**技術規格**:
- 修改 `backend/src/integrations/hybrid/swarm_mode.py`
  - `SwarmExecutionConfig.enabled` 從 `False` → `True`
  - Swarm 作為 first-class execution mode 可用

### S116-3: ObservabilityBridge + G3/G4/G5 (4 SP)

**作為** 運維工程師
**我希望** G3/G4/G5 子系統透過統一的 ObservabilityBridge 接通
**以便** Patrol 監控、事件關聯分析、根因分析能端到端可呼叫

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/observability_bridge.py`
- `ObservabilityBridge` class:
  - `dispatch_patrol_check()` — G3 Patrol 監控檢查
  - `dispatch_correlation_analysis()` — G4 事件關聯分析
  - `dispatch_rootcause_analysis()` — G5 根因分析
  - `protected_llm_call()` — Circuit Breaker 保護的 LLM 調用
  - `get_circuit_breaker_stats()` — 斷路器健康狀態
- 每個 G3/G4/G5 dispatch 自動建立追蹤 task
- Lazy import 各 subsystem engine，不強制依賴

### S116-4: 匯出更新 (2 SP)

**作為** 後端開發者
**我希望** 所有新增模組正確匯出
**以便** 其他模組能直接 import 使用 CircuitBreaker 和 ObservabilityBridge

**技術規格**:
- 修改 `backend/src/core/performance/__init__.py`
  - 匯出 CircuitBreaker, CircuitOpenError, CircuitState, get_llm_circuit_breaker
- 修改 `backend/src/integrations/hybrid/orchestrator/__init__.py`
  - 匯出 ObservabilityBridge

## 相關連結

- [Phase 37 計劃](./README.md)
- [Sprint 115 Plan](./sprint-115-plan.md)
- [Sprint 116 Progress](../../sprint-execution/sprint-116/progress.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
