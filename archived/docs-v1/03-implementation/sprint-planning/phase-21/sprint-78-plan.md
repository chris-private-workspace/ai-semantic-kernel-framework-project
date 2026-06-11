# Sprint 78 Plan: IPC 通信 + 代碼適配 + 安全驗證

## Sprint Overview

| Metric | Value |
|--------|-------|
| **Sprint Number** | 78 |
| **Phase** | Phase 21 - Sandbox Security Architecture |
| **Duration** | 1 sprint |
| **Story Points** | 17 pts |
| **Priority** | 🔴 P0 最高優先 |

---

## Sprint Goals

1. 實現 IPC 通信協議和 SSE 事件轉發
2. 適配現有代碼使用沙箱執行
3. 完成安全測試和驗證

---

## Stories

### S78-1: IPC 通信與事件轉發 (7 pts)

**Priority**: P0

**Description**:
實現主進程和沙箱進程之間的 IPC 通信協議，支援請求/響應和流式事件轉發。

**Tasks**:
1. 實現 IPC 協議類
   ```python
   # backend/src/core/sandbox/ipc.py
   class IPCProtocol:
       async def send_request(request: IPCRequest) -> IPCResponse
       async def read_events() -> AsyncGenerator[IPCEvent, None]
       def encode_message(msg: dict) -> bytes
       def decode_message(data: bytes) -> dict
   ```

2. 實現流式事件處理
   - SSE 事件類型映射
   - 事件序列化和反序列化
   - 事件隊列管理

3. 實現錯誤處理
   - 超時處理
   - 連接斷開處理
   - 錯誤響應封裝

**Acceptance Criteria**:
- [ ] 請求/響應通信正常
- [ ] 流式事件正確轉發
- [ ] 超時機制有效
- [ ] 錯誤正確處理和傳遞

**Files**:
- `backend/src/core/sandbox/ipc.py` (新建)

---

### S78-2: 現有代碼適配 (5 pts)

**Priority**: P1

**Description**:
修改現有的 API 端點和服務層，使用 SandboxOrchestrator 替代直接調用 Claude SDK。

**Tasks**:
1. 修改 chat.py
   ```python
   # backend/src/api/v1/sessions/chat.py
   # Before: 直接調用 claude_sdk.query()
   # After: 使用 orchestrator.execute()
   ```

2. 修改 Claude SDK routes
   ```python
   # backend/src/api/v1/claude_sdk/routes.py
   # 使用 orchestrator 執行請求
   ```

3. 修改 Bridge
   ```python
   # backend/src/domain/sessions/bridge.py
   # 委派執行到沙箱
   ```

4. 修改 Executor
   ```python
   # backend/src/domain/sessions/executor.py
   # 適配新接口
   ```

**Acceptance Criteria**:
- [ ] 現有 API 端點正常工作
- [ ] SSE 事件正確發送到前端
- [ ] 錯誤處理保持一致
- [ ] 無功能回歸

**Files**:
- `backend/src/api/v1/sessions/chat.py` (修改)
- `backend/src/api/v1/claude_sdk/routes.py` (修改)
- `backend/src/domain/sessions/bridge.py` (修改)
- `backend/src/domain/sessions/executor.py` (修改)

---

### S78-3: 安全測試與驗證 (5 pts)

**Priority**: P1

**Description**:
完成全面的安全測試，驗證沙箱隔離有效性。

**Tasks**:
1. 環境變量隔離測試
   - 驗證敏感環境變量不洩露
   - 測試環境變量注入防護

2. 文件系統隔離測試
   - 路徑遍歷攻擊測試
   - 符號連結攻擊測試
   - 權限邊界測試

3. 進程隔離測試
   - 進程崩潰隔離測試
   - 資源限制測試
   - 通信安全測試

4. 性能基準測試
   - 首次啟動延遲測試
   - 進程複用延遲測試
   - 並發處理測試

**Acceptance Criteria**:
- [ ] 所有安全測試通過
- [ ] 性能損耗 < 200ms（首次啟動）
- [ ] 進程崩潰不影響主應用
- [ ] 測試覆蓋率 > 80%

**Files**:
- `backend/tests/unit/core/test_sandbox_security.py` (新建)
- `backend/tests/integration/test_sandbox_e2e.py` (新建)

---

## Technical Details

### 代碼適配示例

**Before (不安全)**:
```python
# api/v1/sessions/chat.py
async def chat_stream(message: str, user_id: str):
    async for event in claude_sdk.query_stream(message):
        yield event
```

**After (安全)**:
```python
# api/v1/sessions/chat.py
async def chat_stream(message: str, user_id: str):
    orchestrator = get_sandbox_orchestrator()
    async for event in orchestrator.execute(
        user_id=user_id,
        message=message,
        attachments=[],
        session_id=session_id,
    ):
        yield event
```

### 安全測試案例

```python
# tests/unit/core/test_sandbox_security.py

def test_env_var_isolation():
    """驗證敏感環境變量不洩露到沙箱"""
    os.environ["SECRET_KEY"] = "test-secret"

    worker = SandboxWorker(user_id="test")
    restricted_env = worker._create_restricted_env()

    assert "SECRET_KEY" not in restricted_env
    assert "DB_PASSWORD" not in restricted_env

def test_path_traversal_prevention():
    """驗證路徑遍歷攻擊防護"""
    sandbox_dir = "/data/sandbox/user-123"

    # 嘗試訪問沙箱外的文件
    malicious_path = "../../etc/passwd"

    with pytest.raises(SecurityError):
        sandbox_file_access(sandbox_dir, malicious_path)

def test_process_crash_isolation():
    """驗證進程崩潰不影響主應用"""
    orchestrator = SandboxOrchestrator()

    # 強制崩潰 worker
    worker = await orchestrator._get_or_create_worker("crash-test")
    worker.process.kill()

    # 主進程應該仍然響應
    response = await orchestrator.execute(
        user_id="crash-test",
        message="test",
        attachments=[],
        session_id="test-session"
    )

    assert response is not None  # 應該自動重啟 worker
```

---

## Dependencies

- Sprint 77 完成 (Orchestrator + Worker)
- 現有 Claude SDK 整合
- 現有 API 端點

---

## Risks

| Risk | Mitigation |
|------|------------|
| 功能回歸 | 完整的整合測試 |
| 性能下降 | 進程池優化 |
| 適配遺漏 | 代碼審查檢查清單 |

---

## Verification

### 整合測試
- [ ] 完整聊天流程測試
- [ ] 文件上傳分析測試
- [ ] 多用戶並發測試

### 回歸測試
- [ ] 所有現有測試通過
- [ ] API 行為一致性驗證
- [ ] 前端無變更需求

### 安全測試
- [ ] 滲透測試清單完成
- [ ] 安全審計通過
- [ ] 文檔更新

---

**Created**: 2026-01-12
**Story Points**: 17 pts
