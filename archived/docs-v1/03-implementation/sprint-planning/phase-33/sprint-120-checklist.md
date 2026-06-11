# Sprint 120 Checklist: InMemory 完成 + Checkpoint 統一設計

## 開發任務

### Story 120-1: 替換剩餘 InMemory 存儲類
- [ ] 執行 `grep -r "InMemory" backend/src/` 確認完整清單
- [ ] 列出 Sprint 119 後剩餘的 InMemory 存儲類
- [ ] 遷移 InMemoryEventStore → Redis Streams / PostgreSQL
  - [ ] 分析現有介面與資料結構
  - [ ] 選擇目標存儲（Redis Streams 或 PostgreSQL）
  - [ ] 實現新存儲後端
  - [ ] 更新 Factory / DI 配置
  - [ ] 驗證事件讀寫正常
- [ ] 遷移 InMemoryTaskQueue → Redis List / Sorted Set
  - [ ] 分析現有介面與資料結構
  - [ ] 實現 Redis-based Task Queue
  - [ ] 更新 Factory / DI 配置
  - [ ] 驗證任務入列 / 出列正常
- [ ] 遷移 InMemoryConversationHistory → PostgreSQL
  - [ ] 分析現有介面與資料結構
  - [ ] 設計 PostgreSQL Schema（如需 Alembic migration）
  - [ ] 實現 PostgreSQL 存儲後端
  - [ ] 更新 Factory / DI 配置
  - [ ] 驗證對話歷史讀寫正常
- [ ] 遷移 InMemoryToolRegistry → Redis Hash
  - [ ] 分析現有介面與資料結構
  - [ ] 實現 Redis Hash 存儲後端
  - [ ] 更新 Factory / DI 配置
  - [ ] 驗證工具註冊 / 查詢正常
- [ ] 遷移其他殘留 InMemory 類（如有）
  - [ ] 逐一確認並遷移
- [ ] 最終驗證
  - [ ] `grep -r "InMemory" backend/src/` 確認生產代碼中 0 個殘留
  - [ ] 測試檔案中的 InMemory 使用不受影響（允許 mock 用途）
- [ ] 編寫單元測試
  - [ ] 各新存儲後端的 CRUD 測試
  - [ ] TTL / 過期測試
  - [ ] 序列化 / 反序列化測試
- [ ] 編寫整合測試
  - [ ] 完整業務流程測試（遷移前後行為一致）

### Story 120-2: UnifiedCheckpointRegistry 設計 + 實現
- [ ] 分析 4 個 Checkpoint 系統
  - [ ] 找出各系統的檔案位置
  - [ ] 記錄各系統的介面方法
  - [ ] 記錄各系統的資料結構
  - [ ] 比對差異，找出公共介面
- [ ] 定義 CheckpointProvider Protocol
  - [ ] `provider_name` 屬性
  - [ ] `save_checkpoint()` 方法
  - [ ] `load_checkpoint()` 方法
  - [ ] `list_checkpoints()` 方法
  - [ ] `delete_checkpoint()` 方法
- [ ] 實現 UnifiedCheckpointRegistry
  - [ ] `register_provider()` 方法
  - [ ] `save()` 統一保存方法
  - [ ] `load()` 統一載入方法
  - [ ] `list_all()` 列出所有 providers 的 checkpoints
  - [ ] `cleanup_expired()` 過期清理方法
  - [ ] 存儲後端整合（Redis + PostgreSQL）
- [ ] 接入第 1 個 Checkpoint 系統
  - [ ] 選擇最簡單的系統作為第一個接入目標
  - [ ] 實現該系統的 CheckpointProvider adapter
  - [ ] 驗證 save / load / list / delete 正常
  - [ ] 確認不影響原有功能
- [ ] 編寫設計文件
  - [ ] 4 個系統的差異分析
  - [ ] 統一方案設計圖
  - [ ] 遷移計劃（Sprint 121 完成剩餘 3 個）
- [ ] 編寫單元測試
  - [ ] Registry 註冊 / 反註冊測試
  - [ ] save / load 功能測試
  - [ ] cleanup_expired 測試
  - [ ] 多 Provider 場景測試

## 品質檢查

### 代碼品質
- [ ] 類型提示完整
- [ ] Docstrings 完整（所有 public class 和 method）
- [ ] 遵循專案代碼風格（Black + isort）
- [ ] 模組導出正確（`__all__`）
- [ ] 無 hardcoded 值

### 測試
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] 所有現有測試不因遷移而失敗
- [ ] `grep -r "InMemory" backend/src/` 生產代碼結果為 0

### 文檔
- [ ] Checkpoint 統一設計文件完成
- [ ] 各遷移存儲類的配置說明更新

## 驗收標準

- [ ] 生產代碼中 InMemory 存儲類為 0（排除測試 mock）
- [ ] UnifiedCheckpointRegistry 基本實現完成
- [ ] 至少 1 個 Checkpoint 系統通過 Registry 正常運作
- [ ] 設計文件記錄完整
- [ ] 所有測試通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: 待定
