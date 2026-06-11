# Sprint 110 Checklist: InMemory → Redis/PostgreSQL 遷移（核心模組）

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 12 點 |
| **狀態** | ✅ 完成 |

---

## 開發任務

### S110-1: Storage Backend ABC + Redis/PG 實作 (3 SP)
- [x] 新增 `backend/src/infrastructure/storage/backends/` 子目錄
- [x] 新增 `backend/src/infrastructure/storage/backends/__init__.py`
- [x] 新增 `backend/src/infrastructure/storage/backends/base.py` — StorageBackend ABC
- [x] 新增 `backend/src/infrastructure/storage/backends/memory.py` — InMemory 實作
- [x] 新增 `backend/src/infrastructure/storage/backends/redis_backend.py` — Redis 實作
- [x] 新增 `backend/src/infrastructure/storage/backends/postgres_backend.py` — PostgreSQL 實作（asyncpg）
- [x] 定義統一 KV 介面（get, set, delete, list, clear）

### S110-2: StorageFactory (2 SP)
- [x] 新增 `backend/src/infrastructure/storage/backends/factory.py`
- [x] 實作自動偵測 Redis 可用性
- [x] 實作自動偵測 PostgreSQL 可用性
- [x] 實作 graceful degradation（降級為 InMemory）
- [x] 提供明確的 backend 選擇日誌

### S110-3: SessionStore (3 SP)
- [x] 新增 `backend/src/infrastructure/storage/session_store.py`
- [x] Dialog Sessions 遷移到 Redis backend
- [x] 實作 TTL 過期機制
- [x] 保持 API 向後兼容

### S110-4: ApprovalStore (2 SP)
- [x] 新增 `backend/src/infrastructure/storage/approval_store.py`
- [x] 審批狀態遷移到 PostgreSQL backend
- [x] 確保服務重啟後審批狀態不丟失

### S110-5: AuditStore (2 SP)
- [x] 新增 `backend/src/infrastructure/storage/audit_store.py`
- [x] 審計日誌遷移到 PostgreSQL backend
- [x] 生產環境禁止 `clear()` 操作
- [x] 支援查詢與合規需求

## 驗證標準

- [x] StorageBackend ABC 定義統一介面
- [x] InMemory / Redis / PostgreSQL 三種實作皆可用
- [x] StorageFactory 自動偵測環境並選擇最佳 backend
- [x] Graceful degradation 正確（Redis 不可用時降級 InMemory）
- [x] SessionStore 使用 Redis backend
- [x] ApprovalStore / AuditStore 使用 PostgreSQL backend
- [x] 所有新增檔案模組匯出正確

## 相關連結

- [Phase 36 計劃](./README.md)
- [Sprint 110 Progress](../../sprint-execution/sprint-110/progress.md)
- [Sprint 110 Plan](./sprint-110-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
