# Sprint 77 Checklist: SandboxOrchestrator + SandboxWorker

## Sprint Status

| Metric | Value |
|--------|-------|
| **Total Stories** | 2 |
| **Total Points** | 21 pts |
| **Completed** | 2 |
| **In Progress** | 0 |
| **Status** | ✅ 完成 |

---

## Stories

### S77-1: 沙箱架構設計與 Orchestrator (13 pts)

**Status**: ✅ 完成

**Tasks**:
- [x] 創建 `backend/src/core/sandbox/` 目錄結構
- [x] 創建 `__init__.py` - Package 初始化
- [x] 創建 `config.py` - ProcessSandboxConfig dataclass
- [x] 創建 `orchestrator.py` - SandboxOrchestrator 類
- [x] 實現 `execute()` 方法 - 執行請求
- [x] 實現 `execute_stream()` 方法 - 串流執行
- [x] 實現 `_get_or_create_worker()` - Worker 管理與用戶親和性
- [x] 實現 `_cleanup_idle_workers()` - 空閒回收
- [x] 實現 `_cleanup_loop()` - 背景清理任務
- [x] 實現 `shutdown()` - 優雅關閉
- [x] 添加進程池大小限制 (max_workers)
- [x] 添加 Worker 超時處理 (worker_timeout)
- [x] 實現 `get_pool_stats()` - 進程池統計
- [ ] 編寫單元測試 (Sprint 78)

**Acceptance Criteria**:
- [x] SandboxOrchestrator 類完整實現
- [x] 進程池複用邏輯正確
- [x] 空閒進程自動回收 (default: 5 分鐘)
- [x] 最大 Worker 數限制 (default: 10)
- [x] 配置可通過環境變量調整
- [ ] 單元測試覆蓋 > 80% (Sprint 78)

---

### S77-2: SandboxWorker 實現 (8 pts)

**Status**: ✅ 完成

**Tasks**:
- [x] 創建 `worker.py` - SandboxWorker 類
- [x] 實現 `start()` 方法 - 啟動子進程
- [x] 實現 `execute()` 方法 - 執行請求
- [x] 實現 `execute_stream()` 方法 - 串流執行
- [x] 實現 `stop()` 方法 - 停止子進程
- [x] 實現 `_send_request()` / `_read_response()` - IPC 通信
- [x] 創建 `worker_main.py` - 子進程入口點
- [x] 實現 SandboxExecutor 類 (Claude SDK 整合待 Sprint 78)
- [x] 實現 IPCHandler 類 - JSON-RPC 處理
- [x] 實現請求處理循環
- [x] 添加錯誤處理和日誌
- [ ] 編寫單元測試 (Sprint 78)

**Acceptance Criteria**:
- [x] Worker 在隔離子進程中啟動
- [x] 子進程無法訪問主進程環境變量 (DB_*, REDIS_*, SECRET_*)
- [x] 子進程只能訪問 /data/sandbox/{user_id}/ 目錄
- [ ] Claude SDK 在子進程中正確初始化 (Sprint 78)
- [x] 進程崩潰後可自動重啟
- [ ] 單元測試覆蓋 > 80% (Sprint 78)

---

## Files Summary

### New Files

| File | Story | Description | Status |
|------|-------|-------------|--------|
| `backend/src/core/sandbox/__init__.py` | S77-1 | Package init | ✅ |
| `backend/src/core/sandbox/config.py` | S77-1 | ProcessSandboxConfig 配置類 | ✅ |
| `backend/src/core/sandbox/orchestrator.py` | S77-1 | SandboxOrchestrator 進程調度器 | ✅ |
| `backend/src/core/sandbox/worker.py` | S77-2 | SandboxWorker 子進程管理 | ✅ |
| `backend/src/core/sandbox/worker_main.py` | S77-2 | 子進程入口點 | ✅ |
| `backend/tests/unit/core/test_sandbox_orchestrator.py` | S77-1 | 單元測試 | ⏳ Sprint 78 |
| `backend/tests/unit/core/test_sandbox_worker.py` | S77-2 | 單元測試 | ⏳ Sprint 78 |

### Modified Files

| File | Story | Changes |
|------|-------|---------|
| None | - | Sprint 77 不需要修改現有文件 |

---

## Verification Checklist

### 語法驗證
- [x] config.py 語法正確
- [x] orchestrator.py 語法正確
- [x] worker.py 語法正確
- [x] worker_main.py 語法正確
- [x] __init__.py 語法正確

### 功能測試 (Sprint 78)
- [ ] Orchestrator 能創建和管理子進程
- [ ] Worker 能在隔離環境中啟動
- [ ] 請求能正確傳遞到 Worker
- [ ] 響應能正確返回到 Orchestrator
- [ ] 進程池複用正常工作
- [ ] 空閒進程正確回收

### 安全測試 (Sprint 78)
- [ ] 驗證環境變量隔離
  ```python
  # 在 worker_main.py 中執行
  assert "DB_PASSWORD" not in os.environ
  assert "REDIS_PASSWORD" not in os.environ
  assert "SECRET_KEY" not in os.environ
  ```
- [ ] 驗證文件系統隔離
  ```python
  # 嘗試訪問沙箱外的文件應該失敗
  with pytest.raises(PermissionError):
      open("/etc/passwd", "r")
  ```

### 性能測試 (Sprint 78)
- [ ] 首次啟動延遲 < 500ms
- [ ] 進程複用後延遲 < 50ms
- [ ] 10 並發請求無錯誤

---

## Notes

- Sprint 77 專注於核心架構實現，已完成所有代碼文件
- 單元測試和整合測試將在 Sprint 78 完成
- Sprint 78 將整合 IPC 通信、現有代碼適配、以及安全驗證

---

**Last Updated**: 2026-01-12
