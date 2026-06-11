# Sprint 112 Checklist: Mock Separation + Redis Storage

## 開發任務

### Story 112-1: Mock 代碼審計
- [ ] 搜索 `backend/src/integrations/orchestration/` 中所有 `class Mock` 定義
- [ ] 搜索 `backend/src/integrations/llm/` 中所有 `class Mock` 定義
- [ ] 確認總計 18 個 Mock 類 (17 orchestration + 1 llm)
- [ ] 檢查 `orchestration/__init__.py` 中 Mock 匯出 (預期 9 個)
- [ ] 搜索生產代碼中所有 `import.*Mock` 語句
- [ ] 搜索測試代碼中所有 `import.*Mock` 語句
- [ ] 記錄每個 Mock 類的：
  - [ ] 類名和定義文件路徑
  - [ ] 對應的真實實現類
  - [ ] 被匯入位置（生產/測試）
  - [ ] 是否通過 `__init__.py` 匯出
  - [ ] 遷移風險等級
- [ ] 完成審計報告文檔
- [ ] 制定遷移順序（低風險優先）

### Story 112-2: Factory Pattern 設計
- [ ] 創建 `backend/src/core/factories.py`
- [ ] 實現 `ServiceFactory` 類
- [ ] 實現 `_registry` 類變量
- [ ] 實現 `register()` 類方法
- [ ] 實現 `create()` 類方法
- [ ] 實現 production 環境邏輯（不 fallback，直接拋異常）
- [ ] 實現 development 環境邏輯（fallback + WARNING）
- [ ] 實現 testing 環境邏輯（直接使用 Mock）
- [ ] 添加類型註解
- [ ] 添加 docstrings
- [ ] 編寫 ServiceFactory 單元測試
  - [ ] 測試 production 環境行為
  - [ ] 測試 development 環境行為
  - [ ] 測試 testing 環境行為
  - [ ] 測試未註冊服務拋出 ValueError

### Story 112-3: Mock 遷移
- [ ] **準備工作**
  - [ ] 創建 `backend/tests/mocks/` 目錄
  - [ ] 創建 `backend/tests/mocks/__init__.py`
  - [ ] 創建 `backend/tests/mocks/orchestration.py`
  - [ ] 創建 `backend/tests/mocks/llm.py`
- [ ] **Batch 1: 低風險 Mock（未被生產代碼直接引用）**
  - [ ] 識別低風險 Mock 列表
  - [ ] 複製低風險 Mock 到 `tests/mocks/orchestration.py`
  - [ ] 更新測試文件匯入路徑
  - [ ] 從原始文件刪除 Mock 類定義
  - [ ] 跑完整測試套件 — 確認通過
- [ ] **Batch 2: 中風險 Mock（被生產代碼引用，可替換為 Factory）**
  - [ ] 識別中風險 Mock 列表
  - [ ] 複製中風險 Mock 到 `tests/mocks/orchestration.py`
  - [ ] 在生產代碼中替換直接匯入為 Factory 調用
  - [ ] 從原始文件刪除 Mock 類定義
  - [ ] 跑完整測試套件 — 確認通過
- [ ] **Batch 3: 高風險 Mock（通過 __init__.py 匯出的 9 個）**
  - [ ] 識別高風險 Mock 列表
  - [ ] 複製高風險 Mock 到 `tests/mocks/`
  - [ ] 更新所有匯入路徑
  - [ ] 從 `__init__.py` 移除 Mock 匯出
  - [ ] 從原始文件刪除 Mock 類定義
  - [ ] 跑完整測試套件 — 確認通過
- [ ] **LLM Mock 遷移**
  - [ ] 複製 LLM Mock 到 `tests/mocks/llm.py`
  - [ ] 更新匯入路徑
  - [ ] 從原始文件刪除
  - [ ] 跑完整測試套件 — 確認通過
- [ ] **最終驗證**
  - [ ] `grep -rn "class Mock" backend/src/` 返回 0 結果
  - [ ] `grep -rn "Mock" backend/src/integrations/orchestration/__init__.py` 返回 0 結果
  - [ ] 所有 18 個 Mock 在 `backend/tests/mocks/` 中
  - [ ] 完整測試套件通過

### Story 112-4: InMemoryApprovalStorage → Redis
- [ ] **實現 RedisApprovalStorage**
  - [ ] 創建 `backend/src/infrastructure/storage/redis_approval_storage.py`
  - [ ] 實現 `__init__()` (Redis 連接 + TTL 配置)
  - [ ] 實現 `store_approval()` 方法
  - [ ] 實現 `get_approval()` 方法
  - [ ] 實現 `update_approval()` 方法
  - [ ] 實現 `list_pending()` 方法
  - [ ] 實現 `delete_approval()` 方法
  - [ ] 添加類型註解
  - [ ] 添加 docstrings
- [ ] **Key 結構設計**
  - [ ] `approval:{id}` → JSON 審批資料
  - [ ] `approval:pending` → Set 待處理 ID
  - [ ] `approval:user:{user_id}` → Set 用戶的審批 ID
  - [ ] TTL 設定 7 天（可配置）
- [ ] **替換配置**
  - [ ] 找到 InMemoryApprovalStorage 使用位置
  - [ ] 使用 Factory Pattern 註冊 Real/Mock 實現
  - [ ] 更新依賴注入配置
  - [ ] Production: 僅 Redis
  - [ ] Development: Redis 優先，fallback InMemory (帶 WARNING)
- [ ] **健康檢查**
  - [ ] 在 health check endpoint 添加 Redis 連接狀態
  - [ ] 實現 `ping()` 健康檢查方法
- [ ] **測試**
  - [ ] 單元測試: store/get/update/delete
  - [ ] 單元測試: list_pending
  - [ ] 單元測試: TTL 過期
  - [ ] 整合測試: 真實 Redis 讀寫
  - [ ] 整合測試: 重啟後資料恢復
  - [ ] 測試覆蓋率 > 90%

### Story 112-5: LLMServiceFactory 靜默 Fallback 移除
- [ ] 找到 LLMServiceFactory 定義文件
- [ ] 找到靜默 fallback 邏輯位置
- [ ] 修改 production 環境：拋出 RuntimeError
- [ ] 修改 development 環境：WARNING 日誌 + fallback
- [ ] 確認 WARNING 包含「NOT acceptable in production」
- [ ] 確認錯誤訊息包含環境變量提示
- [ ] 編寫單元測試
  - [ ] 測試 production 環境 LLM 不可用 → RuntimeError
  - [ ] 測試 development 環境 LLM 不可用 → WARNING + Mock
  - [ ] 測試 LLM 可用 → 正常返回 Real 實現

## 品質檢查

### 代碼品質
- [ ] Black 格式化通過 (backend)
- [ ] isort 排序通過 (backend)
- [ ] flake8 檢查通過 (backend)
- [ ] mypy 類型檢查通過 (backend)
- [ ] 無 unused imports
- [ ] 無 circular imports

### 測試
- [ ] ServiceFactory 單元測試通過
- [ ] RedisApprovalStorage 單元測試通過
- [ ] RedisApprovalStorage 整合測試通過
- [ ] LLMServiceFactory 單元測試通過
- [ ] Mock 遷移後全部現有測試通過
- [ ] 無回歸測試失敗

### 架構檢查
- [ ] `backend/src/` 中無 Mock 類定義
- [ ] `backend/src/` 中無 Mock 類匯出
- [ ] Factory Pattern 正確運作
- [ ] Redis 連接健康檢查通過

## 驗收標準

- [ ] 生產代碼中 Mock 類定義 = 0
- [ ] 生產代碼中 Mock 類匯出 = 0
- [ ] 18 個 Mock 類全在 `backend/tests/mocks/`
- [ ] ServiceFactory 根據環境正確選擇實現
- [ ] InMemoryApprovalStorage 不再是 HITL 預設
- [ ] RedisApprovalStorage 正常運作
- [ ] LLMServiceFactory 在 production 環境不靜默 fallback
- [ ] 所有測試通過
- [ ] Redis 健康檢查正常

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: TBD
