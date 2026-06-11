# Sprint 119 Checklist: InMemory Storage 遷移（前 4 個關鍵存儲）

## 開發任務

### Story 119-1: 替換前 4 個關鍵 InMemory 存儲類
- [ ] 定義 StorageBackend Protocol (`backend/src/infrastructure/storage/protocol.py`)
  - [ ] `get()` 方法
  - [ ] `set()` 方法（含 TTL 支持）
  - [ ] `delete()` 方法
  - [ ] `exists()` 方法
  - [ ] `list_keys()` 方法（Pattern matching）
- [ ] 實現 RedisStorageBackend (`backend/src/infrastructure/storage/redis_backend.py`)
  - [ ] Redis 連線管理（連線池）
  - [ ] JSON 序列化 / 反序列化
  - [ ] 自定義 encoder（支持 datetime、Enum 等）
  - [ ] TTL 管理
  - [ ] Key prefix 隔離
  - [ ] 錯誤處理與重試
- [ ] 遷移 InMemoryApprovalStorage → Redis
  - [ ] 分析現有介面與資料結構
  - [ ] 實現 RedisApprovalStorage
  - [ ] 更新 Factory / DI 配置
  - [ ] 驗證 HITL 審批流程正常
- [ ] 遷移 SessionStorage → Redis
  - [ ] 分析現有介面與資料結構
  - [ ] 實現 RedisSessionStorage
  - [ ] 添加 Session TTL（過期清理）
  - [ ] 更新 Factory / DI 配置
  - [ ] 驗證 Session 管理正常
- [ ] 遷移 StateStorage → Redis + PostgreSQL
  - [ ] 分析現有介面與資料結構
  - [ ] 實現 RedisStateStorage（熱資料）
  - [ ] 實現 PostgreSQL 持久化（冷資料，如需要）
  - [ ] 更新 Factory / DI 配置
  - [ ] 驗證 Agent 狀態管理正常
- [ ] 遷移 CacheStorage → Redis
  - [ ] 分析現有介面與資料結構
  - [ ] 實現 RedisCacheStorage
  - [ ] 更新 Factory / DI 配置
  - [ ] 驗證快取機制正常
- [ ] 環境感知配置
  - [ ] 環境變量 `STORAGE_BACKEND=redis|memory`
  - [ ] Redis 不可用時自動降級為 InMemory + 告警日誌
  - [ ] 配置文件更新
- [ ] 編寫單元測試
  - [ ] StorageBackend Protocol 測試
  - [ ] RedisStorageBackend 測試（含 mock Redis）
  - [ ] 各存儲類遷移後測試
- [ ] 編寫整合測試
  - [ ] 真實 Redis 環境測試（需 Redis 服務）
  - [ ] 重啟後資料持久化驗證

### Story 119-2: ContextSynchronizer 升級為 Redis Distributed Lock
- [ ] 分析現有 2 份 ContextSynchronizer 實現
  - [ ] 找出 2 份實現的檔案位置
  - [ ] 比對功能差異
  - [ ] 確定統一方案
- [ ] 實現 RedisDistributedLock (`backend/src/infrastructure/distributed_lock/redis_lock.py`)
  - [ ] Lock acquire（blocking + timeout）
  - [ ] Lock release（確保原子性）
  - [ ] Context manager 介面
  - [ ] Lock 續約機制（防止長任務 lock 過期）
  - [ ] 錯誤處理（TimeoutError、ConnectionError）
- [ ] 統一 ContextSynchronizer 為單一實現
  - [ ] 合併 2 份實現的功能
  - [ ] 注入 RedisDistributedLock
  - [ ] 降級機制：Redis 不可用時回退 asyncio.Lock
  - [ ] 更新所有引用點
  - [ ] 刪除重複實現
- [ ] 編寫單元測試
  - [ ] RedisDistributedLock 功能測試
  - [ ] Lock timeout 測試
  - [ ] Lock 競爭測試（模擬多進程）
  - [ ] 降級機制測試
- [ ] 編寫整合測試
  - [ ] 多進程並發測試
  - [ ] Redis 斷線恢復測試

## 品質檢查

### 代碼品質
- [ ] 類型提示完整
- [ ] Docstrings 完整（所有 public 方法）
- [ ] 遵循專案代碼風格（Black + isort）
- [ ] 無 hardcoded 配置值（全部使用環境變量）
- [ ] 無 console.log / print 語句

### 測試
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過（需 Redis 環境）
- [ ] 所有現有測試不因遷移而失敗
- [ ] 重啟持久化驗證測試通過

### 安全
- [ ] Redis 連線使用密碼認證
- [ ] 敏感資料在 Redis 中加密存儲（如需要）
- [ ] 無敏感資訊出現在日誌中

## 驗收標準

- [ ] 4 個 InMemory 存儲類全部替換為 Redis/PostgreSQL
- [ ] ContextSynchronizer 統一為 1 份，使用 Redis Distributed Lock
- [ ] 重啟服務後所有存儲資料不丟失
- [ ] 所有現有 API 端點行為不變
- [ ] Redis 不可用時能降級為 InMemory 並記錄告警
- [ ] 測試套件全部通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: 待定
