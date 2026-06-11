# Sprint 31 Checklist: Planning API 完整遷移

**Sprint 目標**: 解決所有 P0 級別架構問題
**總點數**: 25 Story Points
**狀態**: ⏳ 待開始

---

## Story Checklist

### S31-1: Planning API 路由遷移至 PlanningAdapter (8 pts)

**狀態**: ⏳ 待開始

#### 準備工作
- [ ] 閱讀現有 planning/routes.py 代碼
- [ ] 確認 PlanningAdapter 現有功能
- [ ] 識別所有 domain.orchestration.planning 導入

#### 實現任務
- [ ] 移除 domain.orchestration.planning 導入
- [ ] 添加 PlanningAdapter 導入
- [ ] 更新 /decompose 端點
- [ ] 更新 /plan 端點
- [ ] 更新 /decide 端點
- [ ] 更新 /trial 端點
- [ ] 更新其他相關端點

#### 驗證
- [ ] 語法檢查通過 `python -m py_compile`
- [ ] 單元測試通過 `pytest tests/unit/test_planning_api.py`
- [ ] API 響應格式驗證
- [ ] 無 DeprecationWarning

---

### S31-2: AgentExecutor 適配器創建 (5 pts)

**狀態**: ⏳ 待開始

#### 準備工作
- [ ] 分析 domain/agents/service.py 現有邏輯
- [ ] 設計 AgentExecutorAdapter 接口

#### 實現任務
- [ ] 創建 builders/agent_executor.py
- [ ] 實現 AgentExecutorAdapter 類
- [ ] 導入官方 API (from agent_framework import AgentExecutor)
- [ ] 創建 self._executor 官方實例
- [ ] 更新 builders/__init__.py 導出
- [ ] 更新 domain/agents/service.py 使用適配器

#### 驗證
- [ ] 語法檢查通過
- [ ] 單元測試創建 test_agent_executor_adapter.py
- [ ] 官方 API 導入集中度檢查

---

### S31-3: Concurrent API 路由修復 (5 pts)

**狀態**: ⏳ 待開始

#### 準備工作
- [ ] 分析 concurrent/routes.py 現有導入
- [ ] 分析 concurrent/websocket.py 現有導入

#### 實現任務
- [ ] 移除 domain.workflows.executors 導入
- [ ] 添加 ConcurrentBuilderAdapter 導入
- [ ] 更新路由端點實現
- [ ] 更新 WebSocket 處理

#### 驗證
- [ ] 語法檢查通過
- [ ] 單元測試通過 `pytest tests/unit/test_concurrent_api.py`
- [ ] WebSocket 功能測試
- [ ] 13 個 API 路由驗證

---

### S31-4: 棄用代碼清理和警告更新 (4 pts)

**狀態**: ⏳ 待開始

#### 實現任務
- [ ] 更新 domain/orchestration/planning/__init__.py 棄用警告
- [ ] 更新 deprecated-modules.md 文檔
- [ ] 掃描並清理未使用的導入
- [ ] 驗證棄用警告生效

#### 驗證
- [ ] 所有棄用模組有正確警告
- [ ] 文檔更新完成
- [ ] 正常流程無 DeprecationWarning

---

### S31-5: 單元測試驗證 (3 pts)

**狀態**: ⏳ 待開始

#### 實現任務
- [ ] 運行完整測試套件
- [ ] 新增 AgentExecutorAdapter 測試
- [ ] 更新 Planning API 測試
- [ ] 驗證無回歸

#### 驗證
- [ ] `pytest tests/ -v` 全部通過
- [ ] 新增測試 > 10 個
- [ ] 測試覆蓋率維持 85%+

---

## 驗證命令

```bash
# 1. 驗證無棄用導入
grep -r "from src.domain.orchestration.planning" backend/src/api/
# 預期: 無輸出

# 2. 驗證官方 API 使用
cd backend && python scripts/verify_official_api_usage.py
# 預期: 5/5 passed + 新增 agent_executor.py

# 3. 運行測試
pytest tests/ -v --tb=short
# 預期: 全部通過

# 4. 檢查 DeprecationWarning
python -W error::DeprecationWarning -c "from src.api.v1.planning import routes"
# 預期: 無錯誤
```

---

## 完成定義

- [ ] 所有 S31 Story 完成
- [ ] Planning API 100% 使用 PlanningAdapter
- [ ] Concurrent API 100% 使用適配器
- [ ] AgentExecutorAdapter 創建完成
- [ ] 官方 API 導入集中度 > 85%
- [ ] 所有測試通過 (3,450+ tests)
- [ ] 代碼審查完成
- [ ] progress.md 更新
- [ ] decisions.md 更新

---

## 備註

**開始前檢查**:
1. 確認 Sprint 30 完成
2. 確認無阻礙問題
3. 創建 sprint-31 執行目錄

**完成後動作**:
1. 更新 bmm-workflow-status.yaml
2. 創建 Sprint 31 完成報告
3. 準備 Sprint 32
