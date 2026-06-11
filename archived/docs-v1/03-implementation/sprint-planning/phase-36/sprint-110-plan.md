# Sprint 110: InMemory → Redis/PostgreSQL 遷移（核心模組）

## Sprint 目標

1. 統一 Storage Backend 抽象 + InMemory/Redis/PostgreSQL 三種實作
2. StorageFactory 自動偵測環境 + graceful degradation
3. SessionStore（Dialog Sessions 遷移 adapter）
4. ApprovalStore（審批狀態遷移 adapter）
5. AuditStore（審計日誌遷移 adapter）

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 36 — E2E Assembly A1 |
| **Sprint** | 110 |
| **Story Points** | 12 點 |
| **狀態** | ✅ 完成 |

## Sprint 概述

Sprint 110 專注於將核心 InMemory 儲存遷移至 Redis/PostgreSQL。採用 **介面不變、實作替換** 策略，定義統一的 `StorageBackend` 抽象介面，提供 InMemory、Redis、PostgreSQL 三種實作。Redis 用於高頻讀寫短期狀態（sessions），PostgreSQL 用於持久化可查詢資料（approval、audit）。透過 StorageFactory 自動偵測環境並支援 graceful degradation。

## User Stories

### S110-1: Storage Backend ABC + Redis/PG 實作 (3 SP)

**作為** 後端開發者
**我希望** 有統一的 Storage Backend 抽象介面與多種後端實作
**以便** 遷移 InMemory 儲存時保持 API 向後兼容，並支援不同環境

**技術規格**:
- 新增 `backend/src/infrastructure/storage/backends/` 子目錄
- 新增 `base.py` — `StorageBackend` ABC 定義
- 新增 `memory.py` — InMemory 實作
- 新增 `redis_backend.py` — Redis 實作，用於高頻讀寫短期狀態
- 新增 `postgres_backend.py` — PostgreSQL 實作（asyncpg 直連），用於持久化資料
- 新增 `__init__.py` 模組匯出

### S110-2: StorageFactory (2 SP)

**作為** 後端開發者
**我希望** 有自動偵測環境的 Storage Factory
**以便** 根據可用的 Redis/PostgreSQL 自動選擇最佳後端，並支援 graceful degradation

**技術規格**:
- 新增 `backend/src/infrastructure/storage/backends/factory.py`
- 自動偵測 Redis/PostgreSQL 可用性
- Graceful degradation：Redis 不可用時降級為 InMemory
- 提供明確的 backend 選擇日誌

### S110-3: SessionStore (3 SP)

**作為** 平台用戶
**我希望** 對話 session 狀態持久化到 Redis
**以便** 服務重啟後 session 狀態不丟失，支援 TTL 過期

**技術規格**:
- 新增 `backend/src/infrastructure/storage/session_store.py`
- Dialog Sessions 從 InMemory dict 遷移到 Redis
- 支援 TTL 過期機制
- 預設使用 Redis backend

### S110-4: ApprovalStore (2 SP)

**作為** 平台管理員
**我希望** 審批狀態持久化到 PostgreSQL
**以便** 服務重啟後審批狀態不丟失，支援查詢與合規需求

**技術規格**:
- 新增 `backend/src/infrastructure/storage/approval_store.py`
- 審批狀態從 InMemory 遷移到 PostgreSQL
- 預設使用 PostgreSQL backend

### S110-5: AuditStore (2 SP)

**作為** 合規審計員
**我希望** 審計日誌持久化到 PostgreSQL
**以便** 支援查詢、分析與合規報告需求

**技術規格**:
- 新增 `backend/src/infrastructure/storage/audit_store.py`
- 審計日誌從 InMemory 遷移到 PostgreSQL
- 生產環境禁止 `clear()` 操作，防止誤刪審計記錄
- 預設使用 PostgreSQL backend

## 架構決策

| 決策 | 理由 |
|------|------|
| 新建 backends/ 子目錄，不修改現有 storage | 與既有 storage 共存，漸進式遷移 |
| PostgresBackend 用 asyncpg 直連 | KV 操作用原生 SQL 更高效，不走 SQLAlchemy |
| ApprovalStore/AuditStore 預設 PostgreSQL | 審批和審計資料必須持久化 |
| AuditStore 生產環境禁止 clear() | 防止誤刪審計記錄 |

## 相關連結

- [Phase 36 計劃](./README.md)
- [Sprint 110 Progress](../../sprint-execution/sprint-110/progress.md)
- [Sprint 109 Plan](./sprint-109-plan.md)
- [Sprint 111 Plan](./sprint-111-plan.md)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 12
**完成日期**: 2026-03-19
