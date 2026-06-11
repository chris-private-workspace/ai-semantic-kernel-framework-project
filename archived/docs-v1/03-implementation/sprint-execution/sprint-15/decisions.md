# Sprint 15 Technical Decisions Log

**Sprint**: 15 - HandoffBuilder 重構
**開始日期**: 2025-12-05

---

## Decision Log

### DEC-15-001: HandoffBuilder 適配策略

**日期**: 2025-12-05
**狀態**: 待定

**背景**:
Phase 2 有自定義的 HandoffController，需要決定如何映射到 Agent Framework 的 HandoffBuilder。

**選項**:
1. **完全替換**: 直接使用 HandoffBuilder，廢棄 HandoffController
2. **適配層**: 創建適配器保持 Phase 2 API，內部使用 HandoffBuilder
3. **並行架構**: 保留 HandoffController，新增 HandoffBuilderAdapter

**決策**: **選項 3 - 並行架構** (與 Sprint 14 策略一致)

**理由**:
- 保持與 Sprint 14 ConcurrentBuilder 重構的一致性
- 允許漸進式遷移，降低風險
- HandoffBuilder API 與 Phase 2 差異較大需要適配層

**API 對比分析**:
| Phase 2 HandoffController | Agent Framework HandoffBuilder |
|---------------------------|-------------------------------|
| `HandoffPolicy` (IMMEDIATE, GRACEFUL, CONDITIONAL) | `interaction_mode` (human_in_loop, autonomous) |
| `HandoffContext` (task_id, task_state) | `ChatMessage` 對話歷史 |
| `HandoffRequest/Result` | `HandoffUserInputRequest` |
| `initiate_handoff()` | `HandoffBuilder.build().run()` |
| `execute_handoff()` | Workflow 自動執行 |

---

### DEC-15-002: HITL (Human-in-the-Loop) 整合策略

**日期**: 2025-12-05
**狀態**: 待定

**背景**:
Agent Framework 提供 HandoffUserInputRequest 處理人機互動，需要與現有 checkpoint 系統整合。

**選項**:
1. **替換 checkpoint**: 使用 HandoffUserInputRequest 替換現有 checkpoint
2. **並行系統**: 兩者並存，不同場景使用不同機制
3. **適配整合**: HandoffUserInputRequest 內部使用 checkpoint 系統

**決策**: 待分析後決定

**理由**: 需要評估現有 checkpoint 使用情況

---

## Pending Decisions

- [ ] HandoffPolicy 映射方式
- [ ] HandoffContext 傳遞機制
- [ ] API 向後兼容策略
