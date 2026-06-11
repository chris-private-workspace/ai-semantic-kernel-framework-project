# Sprint 32 Checklist: 會話層統一與 Domain 清理

**Sprint 目標**: 解決所有 P1 級別架構問題
**總點數**: 28 Story Points
**狀態**: ⏳ 待開始
**前置條件**: Sprint 31 完成

---

## Story Checklist

### S32-1: MultiTurnAdapter 創建 (10 pts)

**狀態**: ⏳ 待開始

#### 設計階段
- [ ] 設計 MultiTurnAdapter 接口
- [ ] 設計 MultiTurnSession 數據結構
- [ ] 設計 Turn 數據結構
- [ ] 設計 SessionStorage 抽象

#### 實現任務
- [ ] 創建 multiturn/unified_adapter.py
- [ ] 實現 MultiTurnAdapter 類
- [ ] 導入官方 CheckpointStorage API
- [ ] 實現 create_session()
- [ ] 實現 add_turn()
- [ ] 實現 get_context()
- [ ] 實現 save_checkpoint()
- [ ] 實現 restore_session()
- [ ] 實現 close_session()
- [ ] 創建 InMemorySessionStorage
- [ ] 創建 RedisSessionStorage

#### 導出更新
- [ ] 更新 multiturn/__init__.py 導出
- [ ] 添加到 builders/__init__.py (如需要)

#### 驗證
- [ ] 語法檢查通過
- [ ] 創建單元測試 test_multiturn_adapter.py
- [ ] 測試覆蓋率 > 80%

---

### S32-2: GroupChat API 會話層遷移 (8 pts)

**狀態**: ⏳ 待開始

#### 準備工作
- [ ] 分析 groupchat/routes.py 現有會話邏輯
- [ ] 識別所有 domain.orchestration.multiturn 導入
- [ ] 識別所有 domain.orchestration.memory 導入

#### 實現任務
- [ ] 移除 domain.orchestration.multiturn 導入
- [ ] 移除 domain.orchestration.memory 導入
- [ ] 添加 MultiTurnAdapter 導入
- [ ] 更新 POST /sessions 端點
- [ ] 更新 GET /sessions/{id} 端點
- [ ] 更新 POST /sessions/{id}/turns 端點
- [ ] 更新 GET /sessions/{id}/context 端點
- [ ] 更新 POST /sessions/{id}/checkpoint 端點
- [ ] 更新 DELETE /sessions/{id} 端點
- [ ] 更新記憶體管理端點

#### 驗證
- [ ] 語法檢查通過
- [ ] 單元測試通過 `pytest tests/unit/test_groupchat_api.py`
- [ ] 41 個 API 路由功能驗證
- [ ] API 響應格式兼容性驗證

---

### S32-3: Domain 代碼最終清理 (5 pts)

**狀態**: ⏳ 待開始

#### 統計任務
- [ ] 統計剩餘 domain.orchestration 使用
- [ ] 記錄遷移前後代碼行數

#### 清理任務
- [ ] 清理 nested API 殘留依賴
- [ ] 更新 multiturn/ 棄用狀態
- [ ] 更新 memory/ 棄用狀態
- [ ] 更新 deprecated-modules.md

#### 驗證
- [ ] Domain 遷移進度 > 95%
- [ ] 無 API 路由直接導入 domain.orchestration
- [ ] 棄用文檔完整

---

### S32-4: 整合測試驗證 (5 pts)

**狀態**: ⏳ 待開始

#### 測試創建
- [ ] 創建 test_multiturn_adapter.py (20+ tests)
- [ ] 創建 test_groupchat_session_integration.py
- [ ] 測試完整會話生命週期
- [ ] 測試檢查點保存/恢復

#### 運行驗證
- [ ] 運行完整測試套件
- [ ] 運行 E2E GroupChat 測試
- [ ] 驗證無回歸

#### 結果記錄
- [ ] 測試結果記錄
- [ ] 覆蓋率報告

---

## 驗證命令

```bash
# 1. 驗證無 domain.orchestration.multiturn 導入
grep -r "from src.domain.orchestration.multiturn" backend/src/api/
# 預期: 無輸出

# 2. 驗證無 domain.orchestration.memory 導入
grep -r "from src.domain.orchestration.memory" backend/src/api/
# 預期: 無輸出

# 3. 統計遷移進度
find backend/src/domain/orchestration -name "*.py" | xargs wc -l

# 4. 運行 GroupChat 測試
pytest tests/unit/test_groupchat*.py -v
pytest tests/e2e/test_groupchat_workflow.py -v

# 5. 運行完整測試
pytest tests/ -v --tb=short
```

---

## 完成定義

- [ ] 所有 S32 Story 完成
- [ ] MultiTurnAdapter 100% 實現
- [ ] GroupChat API 100% 使用適配器
- [ ] Domain 遷移進度 > 95%
- [ ] 所有測試通過 (3,470+ tests)
- [ ] 新增測試 > 30 個
- [ ] 代碼審查完成
- [ ] progress.md 更新
- [ ] decisions.md 更新

---

## 備註

**開始前檢查**:
1. 確認 Sprint 31 完成
2. 確認 Planning/Concurrent API 已遷移
3. 確認無阻礙問題

**完成後動作**:
1. 更新 bmm-workflow-status.yaml
2. 創建 Sprint 32 完成報告
3. 準備 Sprint 33
