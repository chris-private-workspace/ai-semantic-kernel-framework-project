# Sprint 49 Checklist: Tools & Hooks System - 工具與攔截系統

**Sprint 目標**: 實現 Claude SDK 內建工具和 Hooks 攔截系統
**週期**: Week 3-4
**總點數**: 32 點
**狀態**: 📋 計劃中 (0/32 點)

---

## 快速驗證命令

```bash
# 啟動服務
cd backend
uvicorn main:app --reload --port 8000

# 執行單元測試
pytest tests/unit/integrations/claude_sdk/tools/ -v
pytest tests/unit/integrations/claude_sdk/hooks/ -v

# 測試工具執行
python -c "
import asyncio
from src.integrations.claude_sdk.tools import Read
tool = Read()
result = asyncio.run(tool.execute(path='README.md'))
print(result.content[:200])
"

# 檢查型別
mypy src/integrations/claude_sdk/tools/
mypy src/integrations/claude_sdk/hooks/
```

---

## S49-1: Built-in File Tools (8 點) 📋

### 檔案結構
- [ ] 建立 `backend/src/integrations/claude_sdk/tools/` 目錄
- [ ] 建立 `backend/src/integrations/claude_sdk/tools/__init__.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/tools/base.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/tools/file_tools.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/tools/registry.py`

### ToolResult 類別
- [ ] `ToolResult.content` 屬性
- [ ] `ToolResult.success` 屬性 (預設 True)
- [ ] `ToolResult.error` 屬性 (可選)

### Tool 基礎類別
- [ ] `Tool.name` 抽象屬性
- [ ] `Tool.description` 抽象屬性
- [ ] `Tool.execute()` 抽象方法
- [ ] `Tool.get_schema()` 抽象方法

### Read 工具
- [ ] 接受 `path` 參數 (必要)
- [ ] 接受 `encoding` 參數 (預設 utf-8)
- [ ] 接受 `start_line` 參數 (1-indexed)
- [ ] 接受 `end_line` 參數 (包含)
- [ ] 檔案不存在時返回錯誤
- [ ] 支援內容截斷 (max_chars)
- [ ] 正確處理編碼問題

### Write 工具
- [ ] 接受 `path` 參數 (必要)
- [ ] 接受 `content` 參數 (必要)
- [ ] 接受 `encoding` 參數 (預設 utf-8)
- [ ] 接受 `create_dirs` 參數 (預設 False)
- [ ] 接受 `overwrite` 參數 (預設 True)
- [ ] `overwrite=False` 時檔案存在返回錯誤
- [ ] `create_dirs=True` 時自動建立目錄

### Edit 工具
- [ ] 接受 `path` 參數 (必要)
- [ ] 接受 `old_text` 參數 (必要)
- [ ] 接受 `new_text` 參數 (必要)
- [ ] 接受 `replace_all` 參數 (預設 False)
- [ ] 文字不存在時返回錯誤
- [ ] 正確計算替換次數

### MultiEdit 工具
- [ ] 接受 `edits` 參數 (陣列)
- [ ] 每個 edit 包含 path, old_text, new_text
- [ ] 批次執行所有編輯
- [ ] 部分失敗時返回詳細錯誤

### Glob 工具
- [ ] 接受 `pattern` 參數 (必要)
- [ ] 接受 `path` 參數 (基礎目錄)
- [ ] 接受 `exclude` 參數 (排除模式)
- [ ] 接受 `include_hidden` 參數 (預設 False)
- [ ] 支援遞迴搜尋 (**)
- [ ] 結果數量限制 (max_files)

### Grep 工具
- [ ] 接受 `pattern` 參數 (必要)
- [ ] 接受 `path` 參數 (預設當前目錄)
- [ ] 接受 `regex` 參數 (預設 False)
- [ ] 接受 `case_sensitive` 參數 (預設 True)
- [ ] 接受 `before` 參數 (上下文行數)
- [ ] 接受 `after` 參數 (上下文行數)
- [ ] 接受 `max_matches` 參數
- [ ] 正確處理二進制檔案

### 測試
- [ ] `test_read_file` 通過
- [ ] `test_read_file_not_found` 通過
- [ ] `test_read_file_with_lines` 通過
- [ ] `test_write_file` 通過
- [ ] `test_write_file_create_dirs` 通過
- [ ] `test_edit_file` 通過
- [ ] `test_edit_file_replace_all` 通過
- [ ] `test_multiedit` 通過
- [ ] `test_glob_basic` 通過
- [ ] `test_glob_exclude` 通過
- [ ] `test_grep_basic` 通過
- [ ] `test_grep_regex` 通過

---

## S49-2: Bash 和 Task 工具 (6 點) 📋

### 檔案結構
- [ ] 建立 `backend/src/integrations/claude_sdk/tools/command_tools.py`

### Bash 工具
- [ ] 接受 `command` 參數 (必要)
- [ ] 接受 `cwd` 參數 (工作目錄)
- [ ] 接受 `timeout` 參數 (預設 120 秒)
- [ ] 接受 `env` 參數 (環境變數)
- [ ] 超時處理實現
- [ ] 輸出截斷實現

### Bash 安全控制
- [ ] `DANGEROUS_PATTERNS` 列表定義
- [ ] 阻止 `rm -rf /` 模式
- [ ] 阻止 fork bomb 模式
- [ ] 阻止 `curl | bash` 模式
- [ ] `denied_commands` 黑名單支援
- [ ] `allowed_commands` 白名單支援
- [ ] `_check_security()` 方法實現

### Task 工具
- [ ] 接受 `prompt` 參數 (必要)
- [ ] 接受 `tools` 參數 (子代理工具)
- [ ] 接受 `agent_type` 參數
- [ ] 接受 `system_prompt` 參數
- [ ] 接受 `max_tokens` 參數
- [ ] 接受 `timeout` 參數
- [ ] 建立子代理並執行任務

### 測試
- [ ] `test_bash_simple_command` 通過
- [ ] `test_bash_with_cwd` 通過
- [ ] `test_bash_timeout` 通過
- [ ] `test_bash_blocks_dangerous_command` 通過
- [ ] `test_bash_whitelist` 通過
- [ ] `test_bash_blacklist` 通過
- [ ] `test_task_delegation` 通過

---

## S49-3: Hooks 基礎系統 (10 點) 📋

### 檔案結構
- [ ] 建立 `backend/src/integrations/claude_sdk/hooks/` 目錄
- [ ] 建立 `backend/src/integrations/claude_sdk/hooks/__init__.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hooks/base.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hooks/approval.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hooks/audit.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hooks/rate_limit.py`
- [ ] 建立 `backend/src/integrations/claude_sdk/hooks/sandbox.py`

### Hook 基礎類別
- [ ] `Hook.priority` 屬性 (預設 50)
- [ ] `Hook.on_session_start()` 方法
- [ ] `Hook.on_session_end()` 方法
- [ ] `Hook.on_query_start()` 方法
- [ ] `Hook.on_query_end()` 方法
- [ ] `Hook.on_tool_call()` 方法
- [ ] `Hook.on_tool_result()` 方法
- [ ] `Hook.on_error()` 方法

### HookResult 類別
- [ ] `HookResult.ALLOW` 常數
- [ ] `HookResult.reject()` 工廠方法
- [ ] `HookResult.modify()` 工廠方法
- [ ] `is_allowed` 屬性
- [ ] `is_rejected` 屬性
- [ ] `is_modified` 屬性
- [ ] `reason` 屬性 (拒絕原因)
- [ ] `modified_args` 屬性 (修改後參數)

### ApprovalHook
- [ ] `priority = 90` 設定
- [ ] `DEFAULT_WRITE_TOOLS` 預設集合
- [ ] 接受 `tools_requiring_approval` 參數
- [ ] 接受 `approval_handler` 參數
- [ ] `on_tool_call()` 檢查工具名稱
- [ ] 工具不在列表時返回 ALLOW
- [ ] 工具在列表時調用 approval_handler
- [ ] `_default_approval()` CLI 提示實現

### AuditHook
- [ ] `priority = 100` 設定
- [ ] `SENSITIVE_KEYS` 集合定義
- [ ] 接受 `log_file` 參數
- [ ] 接受 `logger` 參數
- [ ] `on_session_start()` 記錄
- [ ] `on_session_end()` 記錄
- [ ] `on_query_start()` 記錄
- [ ] `on_query_end()` 記錄
- [ ] `on_tool_call()` 記錄
- [ ] `on_tool_result()` 記錄
- [ ] `on_error()` 記錄
- [ ] `_log()` 寫入日誌
- [ ] `_sanitize_args()` 移除敏感資訊

### RateLimitHook
- [ ] `priority = 80` 設定
- [ ] 接受 `max_calls_per_minute` 參數
- [ ] 接受 `max_concurrent` 參數
- [ ] `call_times` 列表追蹤
- [ ] `active_calls` 計數器
- [ ] `on_tool_call()` 速率檢查
- [ ] `on_tool_result()` 遞減計數器
- [ ] 超過限制時返回拒絕

### SandboxHook
- [ ] `priority = 85` 設定
- [ ] `FILE_TOOLS` 集合定義
- [ ] `DEFAULT_DENIED_PATTERNS` 列表定義
- [ ] 接受 `allowed_paths` 參數
- [ ] 接受 `denied_patterns` 參數
- [ ] 路徑規範化 (os.path.abspath)
- [ ] 檢查路徑是否在允許範圍內
- [ ] 檢查路徑是否包含禁止模式
- [ ] 非檔案工具直接返回 ALLOW

### 測試
- [ ] `test_hook_priority_order` 通過
- [ ] `test_approval_hook_allows` 通過
- [ ] `test_approval_hook_rejects` 通過
- [ ] `test_audit_hook_logs_tool_call` 通過
- [ ] `test_audit_hook_sanitizes_sensitive` 通過
- [ ] `test_rate_limit_hook_allows` 通過
- [ ] `test_rate_limit_hook_blocks` 通過
- [ ] `test_sandbox_hook_allows_within` 通過
- [ ] `test_sandbox_hook_blocks_outside` 通過
- [ ] `test_sandbox_hook_blocks_denied_pattern` 通過

---

## S49-4: Web Tools 實現 (8 點) 📋

### 檔案結構
- [ ] 建立 `backend/src/integrations/claude_sdk/tools/web_tools.py`

### SearchResult 類別
- [ ] `title` 屬性
- [ ] `url` 屬性
- [ ] `snippet` 屬性

### WebSearch 工具
- [ ] 接受 `query` 參數 (必要)
- [ ] 接受 `num_results` 參數 (預設 10)
- [ ] 支援 Search API 整合預留
- [ ] 錯誤處理實現

### WebFetch 工具
- [ ] 接受 `url` 參數 (必要)
- [ ] 接受 `headers` 參數
- [ ] 接受 `method` 參數 (預設 GET)
- [ ] 接受 `timeout` 參數
- [ ] 使用 aiohttp 實現
- [ ] 內容截斷實現 (max_content_length)
- [ ] 返回狀態碼和 Content-Type
- [ ] HTTP 錯誤處理
- [ ] 超時處理

### 測試
- [ ] `test_websearch_basic` 通過
- [ ] `test_webfetch_basic` 通過
- [ ] `test_webfetch_with_headers` 通過
- [ ] `test_webfetch_timeout` 通過
- [ ] `test_webfetch_error_handling` 通過

---

## 測試完成

### 單元測試
- [ ] `tests/unit/integrations/claude_sdk/tools/test_base.py`
- [ ] `tests/unit/integrations/claude_sdk/tools/test_file_tools.py`
- [ ] `tests/unit/integrations/claude_sdk/tools/test_command_tools.py`
- [ ] `tests/unit/integrations/claude_sdk/tools/test_web_tools.py`
- [ ] `tests/unit/integrations/claude_sdk/hooks/test_base.py`
- [ ] `tests/unit/integrations/claude_sdk/hooks/test_approval.py`
- [ ] `tests/unit/integrations/claude_sdk/hooks/test_audit.py`
- [ ] `tests/unit/integrations/claude_sdk/hooks/test_rate_limit.py`
- [ ] `tests/unit/integrations/claude_sdk/hooks/test_sandbox.py`

### 整合測試
- [ ] `tests/integration/claude_sdk/test_tools.py`
- [ ] `tests/integration/claude_sdk/test_hooks.py`

### 覆蓋率
- [ ] 單元測試覆蓋率 ≥ 85%
- [ ] 整合測試覆蓋率 ≥ 70%

---

## 文檔完成

- [ ] 工具 API 文檔更新
- [ ] Hooks 使用說明
- [ ] 安全配置指南
- [ ] 工具開發指南

---

## Sprint 完成標準

- [ ] 所有 checkbox 完成
- [ ] 所有測試通過
- [ ] Code Review 完成
- [ ] 安全審查完成
- [ ] 無 Critical/High Bug
- [ ] 文檔更新完成

---

## 依賴確認

### 外部依賴
- [ ] `aiohttp` 套件安裝
- [ ] Sprint 48 Core SDK Integration 完成

### 內部依賴
- [ ] ClaudeSDKClient 可正常運作
- [ ] Session 管理可正常運作
- [ ] types.py 定義完成

---

## 完成統計表

| Story | 點數 | 狀態 | 完成日期 |
|-------|------|------|----------|
| S49-1 | 8 | 📋 | - |
| S49-2 | 6 | 📋 | - |
| S49-3 | 10 | 📋 | - |
| S49-4 | 8 | 📋 | - |
| **總計** | **32** | **0%** | - |
