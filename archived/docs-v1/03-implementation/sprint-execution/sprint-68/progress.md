# Sprint 68 Progress: Sandbox Isolation + Chat History

> **Phase 17**: Agentic Chat Enhancement
> **Sprint 目標**: 實現沙盒隔離安全架構和聊天歷史持久化

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 68 |
| 計劃點數 | 21 Story Points |
| 開始日期 | 2026-01-08 |
| 完成日期 | 2026-01-08 |
| Phase | 17 - Agentic Chat Enhancement |
| 前置條件 | Phase 16 完成、ThreadManager 運作中 |

---

## Sprint 目標

1. ✅ 實現沙盒目錄隔離以保護 Agent 操作
2. ✅ 創建帶安全驗證的文件上傳 API
3. ✅ 完成聊天歷史 API 實現
4. ✅ 整合前端歷史載入功能

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S68-1 | Sandbox Directory Structure | 3 | ✅ 完成 | 100% |
| S68-2 | SandboxHook Path Validation | 5 | ✅ 完成 | 100% |
| S68-3 | File Upload API | 5 | ✅ 完成 | 100% |
| S68-4 | History API Implementation | 5 | ✅ 完成 | 100% |
| S68-5 | Frontend History Integration | 3 | ✅ 完成 | 100% |

**整體進度**: 21/21 pts (100%) ✅

---

## 架構決策

### Per-User 沙盒隔離

採用 Per-User 隔離而非 Per-Session，目錄結構如下：

```
data/
├── uploads/{user_id}/      # 用戶上傳的文件
├── sandbox/{user_id}/      # 代碼執行沙盒
├── outputs/{user_id}/      # Agent 生成的輸出
└── temp/                   # 臨時文件（無用戶隔離）
```

### Guest User ID 機制

Phase 17 使用臨時 Guest User ID（localStorage UUID）：

```typescript
const GUEST_USER_KEY = 'ipa_guest_user_id';

function getGuestUserId(): string {
  let userId = localStorage.getItem(GUEST_USER_KEY);
  if (!userId) {
    userId = `guest-${crypto.randomUUID()}`;
    localStorage.setItem(GUEST_USER_KEY, userId);
  }
  return userId;
}
```

Phase 18 認證完成後：Guest UUID → Real User ID 自動遷移

---

## 詳細進度記錄

### S68-1: Sandbox Directory Structure (3 pts)

**狀態**: ✅ 完成

**變更內容**:
- 創建 `SandboxConfig` 類別
- 實現 `get_user_dir()` 方法
- 實現 `ensure_user_dirs()` 方法
- 添加 `data/.gitkeep` 文件
- 更新 `.gitignore` 排除 `data/*`

**新增檔案**:
- `backend/src/core/sandbox_config.py`

**程式碼模式**:
```python
class SandboxConfig:
    BASE_DATA_DIR: Path = Path("data")
    UPLOADS_DIR: str = "uploads"
    SANDBOX_DIR: str = "sandbox"
    OUTPUTS_DIR: str = "outputs"

    @classmethod
    def get_user_dir(cls, user_id: str, dir_type: str) -> Path:
        return cls.BASE_DATA_DIR / dir_type / user_id

    @classmethod
    def ensure_user_dirs(cls, user_id: str) -> dict[str, Path]:
        dirs = {}
        for dir_type in [cls.UPLOADS_DIR, cls.SANDBOX_DIR, cls.OUTPUTS_DIR]:
            path = cls.get_user_dir(user_id, dir_type)
            path.mkdir(parents=True, exist_ok=True)
            dirs[dir_type] = path
        return dirs
```

---

### S68-2: SandboxHook Path Validation (5 pts)

**狀態**: ✅ 完成

**變更內容**:
- 創建 `UserSandboxHook` 類別繼承自 `SandboxHook`
- 定義允許路徑模式（用戶特定目錄）
- 定義阻擋路徑模式（backend/, frontend/, src/, docs/）
- 定義阻擋寫入的副檔名（.py, .ts, .tsx, .js）
- 實現路徑正規化防止遍歷攻擊
- 添加阻擋嘗試的日誌記錄

**新增/修改檔案**:
- `backend/src/integrations/claude_sdk/hooks/sandbox.py` (修改)
- `backend/src/integrations/claude_sdk/hooks/__init__.py` (修改)

**安全機制**:
```python
class UserSandboxHook(SandboxHook):
    def __init__(self, user_id: str):
        base = Path("data").resolve()
        user_dirs = [
            str(base / "uploads" / user_id),
            str(base / "sandbox" / user_id),
            str(base / "outputs" / user_id),
        ]

        blocked_dirs = [
            str(Path("backend").resolve()),
            str(Path("frontend").resolve()),
            str(Path("src").resolve()),
            str(Path("docs").resolve()),
        ]

        super().__init__(
            allowed_paths=user_dirs,
            blocked_patterns=blocked_dirs,
            blocked_extensions=[".py", ".ts", ".tsx", ".js", ".jsx", ".sh"],
        )
```

---

### S68-3: File Upload API (5 pts)

**狀態**: ✅ 完成

**變更內容**:
- 創建 `upload.py` 路由模組
- 實現 `POST /upload` 端點
- 實現 `GET /upload/list` 端點
- 實現 `DELETE /upload/{filename}` 端點
- 添加文件類型白名單驗證
- 添加 10MB 大小限制

**新增檔案**:
- `backend/src/api/v1/ag_ui/upload.py`

**修改檔案**:
- `backend/src/api/v1/ag_ui/__init__.py`
- `backend/src/api/v1/ag_ui/dependencies.py` (添加 `get_user_id`)

**API 端點**:
```python
ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml",
    ".pdf", ".docx", ".xlsx",
    ".png", ".jpg", ".jpeg", ".gif",
    ".log", ".html", ".css",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
) -> dict:
    # 驗證副檔名和大小
    # 儲存至用戶目錄
    ...
```

---

### S68-4: History API Implementation (5 pts)

**狀態**: ✅ 完成

**變更內容**:
- 實現 `GET /threads/{thread_id}/history` 端點
- 添加分頁支援 (offset, limit)
- 包含 tool_calls 和 approval_state
- 按 created_at 升序排序
- 添加 Redis 快取 (5 分鐘 TTL)
- 返回總數量

**修改檔案**:
- `backend/src/api/v1/ag_ui/routes.py`

**API 回應格式**:
```python
{
    "thread_id": thread_id,
    "messages": [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "tool_calls": msg.tool_calls or [],
            "approval_state": msg.approval_state,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ],
    "pagination": {
        "offset": offset,
        "limit": limit,
        "total": total,
        "has_more": offset + limit < total,
    }
}
```

---

### S68-5: Frontend History Integration (3 pts)

**狀態**: ✅ 完成

**變更內容**:
- 在 `useUnifiedChat` 添加 `loadHistory()` 方法
- 添加 `historyLoading` 狀態
- 組件掛載時自動載入歷史
- 轉換 API 回應為 ChatMessage 格式
- 處理載入狀態
- API 錯誤時回退至 localStorage

**修改檔案**:
- `frontend/src/hooks/useUnifiedChat.ts`
- `frontend/src/pages/UnifiedChat.tsx`

**新增檔案**:
- `frontend/src/utils/guestUser.ts`

**程式碼模式**:
```typescript
const loadHistory = useCallback(async () => {
  if (!threadId) return;

  setHistoryLoading(true);
  try {
    const guestId = getGuestUserId();
    const response = await fetch(`${apiUrl}/threads/${threadId}/history`, {
      headers: { 'X-Guest-Id': guestId },
    });

    if (!response.ok) throw new Error('Failed to load history');

    const data = await response.json();
    const historyMessages = data.messages.map((msg) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      toolCalls: msg.tool_calls,
      approvalState: msg.approval_state,
      timestamp: new Date(msg.created_at),
    }));

    setMessages(historyMessages);
  } catch (error) {
    console.error('Failed to load history:', error);
    // 回退至 localStorage
  } finally {
    setHistoryLoading(false);
  }
}, [threadId, apiUrl]);
```

---

## 修改的檔案總覽

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `backend/src/core/sandbox_config.py` | 沙盒目錄配置 |
| `backend/src/api/v1/ag_ui/upload.py` | 文件上傳 API |
| `frontend/src/utils/guestUser.ts` | Guest User ID 管理 |

### 修改檔案

| 檔案 | 說明 |
|------|------|
| `backend/src/integrations/claude_sdk/hooks/sandbox.py` | 添加 UserSandboxHook |
| `backend/src/integrations/claude_sdk/hooks/__init__.py` | 導出 UserSandboxHook |
| `backend/src/api/v1/ag_ui/__init__.py` | 包含 upload router |
| `backend/src/api/v1/ag_ui/dependencies.py` | 添加 get_user_id |
| `backend/src/api/v1/ag_ui/routes.py` | 實現 history 端點 |
| `frontend/src/hooks/useUnifiedChat.ts` | 添加 loadHistory |
| `.gitignore` | 添加 data/* 排除 |

---

## 測試結果

### 沙盒隔離測試

| 測試案例 | 預期結果 | 狀態 |
|----------|----------|------|
| Agent 讀取 sandbox 目錄 | 成功 | ✅ 通過 |
| Agent 讀取 backend/ | 被阻擋 | ✅ 通過 |
| Agent 寫入 outputs/ | 成功 | ✅ 通過 |
| Agent 寫入 .py 文件 | 被阻擋 | ✅ 通過 |
| 路徑遍歷攻擊 (../) | 被阻擋 | ✅ 通過 |

### 文件上傳測試

| 測試案例 | 預期結果 | 狀態 |
|----------|----------|------|
| 上傳 .txt 文件 | 成功 | ✅ 通過 |
| 上傳 .py 文件 | 被拒絕 | ✅ 通過 |
| 上傳 > 10MB 文件 | 被拒絕 | ✅ 通過 |
| 列出已上傳文件 | 返回列表 | ✅ 通過 |
| 刪除已上傳文件 | 成功 | ✅ 通過 |

### 歷史 API 測試

| 測試案例 | 預期結果 | 狀態 |
|----------|----------|------|
| 取得現有 thread 歷史 | 返回訊息 | ✅ 通過 |
| 取得不存在的 thread | 返回 404 | ✅ 通過 |
| 分頁功能 | 正常運作 | ✅ 通過 |
| 第二次請求快取命中 | 返回快取 | ✅ 通過 |

### 前端整合測試

| 測試案例 | 預期結果 | 狀態 |
|----------|----------|------|
| 頁面掛載時載入歷史 | 歷史載入 | ✅ 通過 |
| 載入中顯示 spinner | 顯示載入狀態 | ✅ 通過 |
| 載入後顯示訊息 | 訊息可見 | ✅ 通過 |
| 新對話顯示空狀態 | 空白畫面 | ✅ 通過 |

---

## 技術備註

### History 同步策略

```
Backend (PostgreSQL) = 真理來源
         ↓
    Redis Cache (5-min TTL)
         ↓
    Frontend (localStorage)

頁面載入時:
1. 檢查 localStorage 中的快取 thread_id
2. 呼叫 GET /threads/{id}/history
3. 用後端資料替換 localStorage
4. 訂閱 SSE 以獲取新訊息
```

### 沙盒與 Claude SDK 整合

```python
class ClaudeSDKClient:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.sandbox_hook = UserSandboxHook(user_id)

    async def execute_tool(self, tool_name: str, args: dict) -> ToolResult:
        # 驗證 args 中的文件路徑
        if tool_name in ("Read", "Write", "Edit", "Glob", "Grep"):
            path = args.get("file_path") or args.get("path")
            if path:
                result = self.sandbox_hook.validate_path(
                    path,
                    operation="write" if tool_name in ("Write", "Edit") else "read"
                )
                if not result.allowed:
                    return ToolResult(success=False, error=result.reason)
```

---

## 安全考量

### 路徑遍歷防護

```python
def _normalize_path(self, path: str) -> str:
    """正規化路徑以防止遍歷攻擊"""
    path = path.lstrip("/\\")
    try:
        resolved = Path(path).resolve()
        cwd = Path.cwd()
        return str(resolved.relative_to(cwd))
    except (ValueError, RuntimeError):
        return path
```

### 副檔名阻擋

- 寫入操作阻擋: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.sh`, `.bat`, `.ps1`
- 上傳 API 只允許白名單副檔名

### 用戶隔離

- 每個用戶有獨立的沙盒目錄
- 不同 Guest User 的文件相互隔離
- Phase 18 認證後自動遷移

---

## Sprint 回顧

### 成功因素
- 安全設計採用白名單策略
- 多層防護（路徑驗證 + 副檔名 + 目錄隔離）
- 後端作為歷史資料的真理來源

### 學習要點
- Per-User 隔離比 Per-Session 更適合長期使用
- Guest UUID 機制需要考慮 Phase 18 遷移

### 下一步
- Sprint 69: Claude Code 風格 UI + Dashboard 整合
- Phase 18: 認證系統 + Guest 資料遷移

---

**更新日期**: 2026-01-08
**Sprint 狀態**: ✅ 完成
