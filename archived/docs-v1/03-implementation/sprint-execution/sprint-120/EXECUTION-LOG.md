# Sprint 120 Execution Log

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| **Sprint** | 120 |
| **Phase** | 33 — Production Hardening |
| **Story Points** | 40 |
| **開始日期** | 2026-02-24 |
| **狀態** | 🔄 執行中 |

## 目標

1. **Story 120-1**: 替換剩餘 InMemory 存儲類（使生產代碼中 InMemory 存儲歸零）
2. **Story 120-2**: 設計與實現 UnifiedCheckpointRegistry（統一 4 個 Checkpoint 系統）

## Story 120-1: InMemory 存儲遷移

### 研究結果

平台共有 11 個 InMemory 存儲類：

| # | 存儲類 | 所在模組 | 狀態 |
|---|--------|---------|------|
| 1 | InMemoryThreadRepository | ag_ui/thread | ✅ Sprint 119 已遷移 |
| 2 | InMemoryCache | ag_ui/thread | ✅ Sprint 119 已遷移 |
| 3 | InMemoryDialogSessionStorage | orchestration/guided_dialog | ✅ Sprint 119 已遷移 |
| 4 | InMemoryApprovalStorage | orchestration/hitl | ✅ Sprint 119 已遷移 |
| 5 | InMemoryConversationMemoryStore | domain/orchestration/memory | ✅ Sprint 119 已有 Redis/Postgres 工廠 |
| 6 | InMemoryCheckpointStorage | hybrid/switching/switcher.py | 🔄 Sprint 120 遷移中 |
| 7 | InMemoryAuditStorage | mcp/security/audit.py | 🔄 Sprint 120 遷移中 |
| 8 | InMemoryCheckpointStorage | agent_framework/multiturn | ✅ 已有 Redis/Postgres，需加工廠 |
| 9 | InMemoryStorageBackend | infrastructure/storage | ⚪ 基礎設施 fallback（保留） |
| 10 | InMemoryLock | infrastructure/distributed_lock | ⚪ 基礎設施 fallback（保留） |
| 11 | InMemoryTransport | mcp/core/transport.py | ⚪ 測試工具（保留） |

### 新建檔案

- `backend/src/integrations/hybrid/switching/redis_checkpoint.py` — RedisSwitchCheckpointStorage
- `backend/src/integrations/mcp/security/redis_audit.py` — RedisAuditStorage
- 更新 `backend/src/infrastructure/storage/storage_factories.py` — 新增 3 個工廠函數
- 更新 `switcher.py`, `audit.py` — 加入 InMemory fallback 警告

## Story 120-2: UnifiedCheckpointRegistry

### 4 個 Checkpoint 系統分析

| # | 系統 | 位置 | 後端 | 介面方法 |
|---|------|------|------|---------|
| 1 | Domain Checkpoints | domain/checkpoints/ | PostgreSQL | CheckpointRepository |
| 2 | Hybrid Checkpoint | hybrid/checkpoint/ | Memory/Redis/Postgres/FS | save/load/list/delete |
| 3 | Agent Framework | agent_framework/multiturn/ | Memory/Redis/Postgres | save/load/delete/list |
| 4 | Session Recovery | domain/sessions/ | CacheProtocol | get/set |

### 新建檔案

- `backend/src/infrastructure/checkpoint/__init__.py`
- `backend/src/infrastructure/checkpoint/protocol.py` — CheckpointProvider Protocol + CheckpointEntry
- `backend/src/infrastructure/checkpoint/unified_registry.py` — UnifiedCheckpointRegistry
- `backend/src/infrastructure/checkpoint/adapters/__init__.py`
- `backend/src/infrastructure/checkpoint/adapters/hybrid_adapter.py` — 第一個 Provider Adapter

## 變更摘要

### 新增檔案
- [ ] `backend/src/integrations/hybrid/switching/redis_checkpoint.py`
- [ ] `backend/src/integrations/mcp/security/redis_audit.py`
- [ ] `backend/src/infrastructure/checkpoint/__init__.py`
- [ ] `backend/src/infrastructure/checkpoint/protocol.py`
- [ ] `backend/src/infrastructure/checkpoint/unified_registry.py`
- [ ] `backend/src/infrastructure/checkpoint/adapters/__init__.py`
- [ ] `backend/src/infrastructure/checkpoint/adapters/hybrid_adapter.py`

### 修改檔案
- [ ] `backend/src/infrastructure/storage/storage_factories.py` (新增 3 個工廠)
- [ ] `backend/src/integrations/hybrid/switching/switcher.py` (InMemory 警告)
- [ ] `backend/src/integrations/mcp/security/audit.py` (InMemory 警告)

## 執行時間線

| 時間 | 動作 |
|------|------|
| 2026-02-24 | Sprint 120 開始執行 |
| | Story 120-1: InMemory 遷移研究完成 |
| | Story 120-1: 建立 Redis 存儲實現 |
| | Story 120-2: UnifiedCheckpointRegistry 設計與實現 |
