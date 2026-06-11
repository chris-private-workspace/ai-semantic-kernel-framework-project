# Sprint 25 Checklist: 清理、測試、文檔

## ⏳ Sprint 狀態 - 待開始

> **狀態**: 待開始
> **點數**: 0/21 pts (0%)
> **目標**: 移除棄用代碼、完善測試、更新文檔

---

## Quick Verification Commands

```bash
# 代碼行數統計
cd backend
find src/domain -name "*.py" | xargs wc -l | tail -1

# 官方 API 使用驗證
python scripts/verify_official_api_usage.py

# 測試覆蓋率
pytest tests/ --cov=src --cov-report=term-missing

# 無 deprecated 警告
grep -r "DeprecationWarning" src/domain/

# 運行所有測試
pytest tests/ -v
```

---

## Story Breakdown

### S25-1: 移除 Deprecated 代碼 (8 points) ⏳

#### 完全刪除清單

**GroupChat 模組**
- [ ] 刪除 `domain/orchestration/groupchat/manager.py`
- [ ] 刪除 `domain/orchestration/groupchat/speaker_selector.py`
- [ ] 刪除 `domain/orchestration/groupchat/termination.py`
- [ ] 刪除 `domain/orchestration/groupchat/voting.py`
- [ ] 刪除 `domain/orchestration/groupchat/__init__.py`
- [ ] 刪除整個目錄 `domain/orchestration/groupchat/`

**Handoff 模組**
- [ ] 刪除 `domain/orchestration/handoff/controller.py`
- [ ] 刪除 `domain/orchestration/handoff/capability_matcher.py`
- [ ] 刪除 `domain/orchestration/handoff/context_transfer.py`
- [ ] 刪除 `domain/orchestration/handoff/trigger.py`
- [ ] 刪除 `domain/orchestration/handoff/__init__.py`
- [ ] 刪除整個目錄 `domain/orchestration/handoff/`

**Collaboration 模組**
- [ ] 刪除整個目錄 `domain/orchestration/collaboration/`

**Concurrent 模組**
- [ ] 刪除 `domain/workflows/executors/concurrent.py`
- [ ] 刪除 `domain/workflows/executors/concurrent_state.py`
- [ ] 刪除 `domain/workflows/executors/parallel_gateway.py`

#### 部分保留清單

**Nested 模組**
- [ ] 保留 `context_propagation.py`
- [ ] 保留 `recursive_handler.py`
- [ ] 刪除其他冗餘文件

**Planning 模組**
- [ ] 保留 `task_decomposer.py`
- [ ] 保留 `decision_engine.py`
- [ ] 刪除 `dynamic_planner.py`

**Memory 模組**
- [ ] 保留後端實現文件
- [ ] 刪除舊接口層

**Multi-turn 模組**
- [ ] 保留 `session_manager.py`
- [ ] 刪除舊狀態存儲

#### 刪除步驟

- [ ] Step 1: 確認無其他代碼引用
  ```bash
  grep -r "from domain.orchestration.groupchat" src/
  grep -r "from domain.orchestration.handoff" src/
  # 預期: 0 結果
  ```
- [ ] Step 2: 運行測試確保無影響
- [ ] Step 3: 執行刪除
- [ ] Step 4: 重新運行測試

#### 驗證

- [ ] 所有 deprecated 代碼已刪除
- [ ] 沒有斷開的 import 引用
- [ ] 所有測試通過
- [ ] 代碼行數減少 > 4,000 行

---

### S25-2: 完善測試覆蓋 (5 points) ⏳

#### 覆蓋率檢查

| 適配器 | 當前 | 目標 | 狀態 |
|--------|------|------|------|
| GroupChatBuilderAdapter | | 80% | ⏳ |
| GroupChatVotingAdapter | | 80% | ⏳ |
| HandoffBuilderAdapter | | 80% | ⏳ |
| HandoffPolicyAdapter | | 80% | ⏳ |
| ConcurrentBuilderAdapter | | 80% | ⏳ |
| NestedWorkflowAdapter | | 80% | ⏳ |
| PlanningAdapter | | 80% | ⏳ |
| MultiTurnAdapter | | 80% | ⏳ |
| RedisMemoryStorage | | 80% | ⏳ |
| RedisCheckpointStorage | | 80% | ⏳ |

#### 測試補充任務

- [ ] 補充邊界測試
- [ ] 補充錯誤處理測試
- [ ] 補充性能測試
- [ ] 補充回歸測試
- [ ] 運行覆蓋率報告

#### 驗證

- [ ] 整體覆蓋率 > 80%
- [ ] 所有適配器覆蓋率 > 80%
- [ ] 無測試失敗

---

### S25-3: 更新所有文檔 (5 points) ⏳

#### 核心文檔

- [ ] 更新 `CLAUDE.md`
  - [ ] 更新架構圖
  - [ ] 更新開發命令
  - [ ] 更新官方 API 使用說明
- [ ] 更新 `README.md`
  - [ ] 更新功能列表
  - [ ] 更新快速開始指南

#### 架構文檔

- [ ] 更新 `docs/02-architecture/technical-architecture.md`
  - [ ] 更新系統架構圖
  - [ ] 更新組件說明
  - [ ] 移除已刪除模組的說明
- [ ] 更新 `docs/02-architecture/data-flow.md`
  - [ ] 更新數據流程圖
  - [ ] 更新 API 調用路徑

#### 遷移指南確認

- [ ] `groupchat-migration.md` 存在
- [ ] `handoff-migration.md` 存在
- [ ] `concurrent-migration.md` 存在
- [ ] `memory-migration.md` 存在
- [ ] `nested-workflow-migration.md` 存在
- [ ] `planning-migration.md` 存在
- [ ] `multiturn-migration.md` 存在

#### API 文檔

- [ ] 更新 API 端點文檔
- [ ] 更新請求/響應範例
- [ ] 更新錯誤碼說明

#### 驗證

- [ ] 所有文檔更新完成
- [ ] 無過時的架構說明
- [ ] 遷移指南完整

---

### S25-4: 最終驗證 (3 points) ⏳

#### 代碼驗證

- [ ] 運行官方 API 使用驗證
  ```bash
  python scripts/verify_official_api_usage.py
  # 預期: 所有檢查通過
  ```
- [ ] 確認無 domain/orchestration 直接使用
  ```bash
  grep -r "from domain.orchestration" src/api/
  # 預期: 0 結果
  ```
- [ ] 代碼行數統計
  ```bash
  find src/domain -name "*.py" | xargs wc -l | tail -1
  # 預期: < 3,000 行
  ```

#### 測試驗證

- [ ] 所有測試通過
- [ ] 覆蓋率 > 80%

#### 性能驗證

- [ ] 性能基準測試通過
- [ ] 無明顯性能退化 (< 10%)

#### 文檔驗證

- [ ] 所有文檔鏈接有效
- [ ] 代碼範例可執行
- [ ] 架構圖與代碼一致

#### 產出最終報告

- [ ] 創建 Phase 4 完成報告
- [ ] 更新 `bmm-workflow-status.yaml`
- [ ] 記錄所有改善指標

---

## Sprint Completion Criteria

### 最終目標確認

- [ ] 自行實現代碼 < 3,000 行
- [ ] 官方 API 使用率 > 80%
- [ ] 測試覆蓋率 > 80%
- [ ] 無 deprecated 警告
- [ ] 文檔 100% 更新

### 代碼審查重點

- [ ] 無殘留的未使用代碼
- [ ] 無斷開的引用
- [ ] 測試完整
- [ ] 文檔準確

---

## Final Checklist

- [ ] S25-1: 移除 Deprecated 代碼 ⏳
- [ ] S25-2: 完善測試覆蓋 ⏳
- [ ] S25-3: 更新所有文檔 ⏳
- [ ] S25-4: 最終驗證 ⏳
- [ ] 所有目標達成
- [ ] 代碼審查完成
- [ ] 更新 bmm-workflow-status.yaml
- [ ] **Phase 4 完成** ✅

---

## Post-Sprint Actions

1. **更新 bmm-workflow-status.yaml** - 標記 Phase 4 完成
2. **創建完成報告** - 記錄所有改善指標
3. **Git Commit** - 最終提交
4. **通知團隊** - Phase 4 重構完成

---

## Phase 4 完成確認

### 完成統計

| Sprint | 名稱 | 點數 | 狀態 |
|--------|------|------|------|
| Sprint 20 | GroupChat 遷移 | 34 | ⏳ |
| Sprint 21 | Handoff 遷移 | 32 | ⏳ |
| Sprint 22 | Concurrent & Memory | 28 | ⏳ |
| Sprint 23 | Nested Workflow | 35 | ⏳ |
| Sprint 24 | Planning & Multi-turn | 30 | ⏳ |
| Sprint 25 | 清理、測試、文檔 | 21 | ⏳ |
| **總計** | | **180** | |

### 最終指標

| 指標 | Phase 3 後 | Phase 4 後 | 改善 |
|------|-----------|-----------|------|
| 自行實現代碼 | 19,844 行 | < 3,000 行 | -85% |
| 官方 API 使用率 | 2.4% | > 80% | +3,233% |
| 重複功能 | 60-70% | < 5% | -90% |
| 測試覆蓋率 | 分散 | > 80% | 統一 |

---

**創建日期**: 2025-12-06
**最後更新**: 2025-12-06
**版本**: 1.0
