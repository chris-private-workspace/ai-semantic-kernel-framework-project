# Sprint 37 Decisions: Code Interpreter 基礎設施

**Sprint**: Sprint 37
**Phase**: Phase 8 - Azure Code Interpreter 整合
**日期**: 2025-12-21

---

## D37-1: SDK 選擇

### 背景
Azure 提供多種 SDK 訪問 AI 服務：
- `azure-ai-projects` - AI Foundry Projects SDK
- `azure-ai-agents` - AI Agents SDK
- `openai` - OpenAI SDK (支援 Azure)

### 問題
`azure-ai-projects` 和 `azure-ai-agents` 需要 `TokenCredential`（如 `DefaultAzureCredential`），不支援 API Key 直接認證。

### 決策
使用 `openai.AzureOpenAI` SDK 訪問 Azure OpenAI Assistants API。

### 理由
1. 已驗證可正常工作（`scripts/test_azure_ai_agent_service.py`）
2. 支援 API Key 認證
3. API 穩定，文檔完整
4. 與現有 Phase 7 LLM 服務保持一致

### 影響
- 正面：簡化認證，與現有代碼一致
- 負面：無法使用 Azure AI 特定功能（如果有的話）

---

## D37-2: Lazy Initialization 模式

### 背景
每次創建 Assistant 都會產生 API 調用，有延遲和成本。

### 決策
CodeInterpreterAdapter 採用 lazy initialization：
- 構造時不創建 Assistant
- 首次調用 `execute()` 或 `analyze_task()` 時創建
- 提供 `cleanup()` 方法釋放資源

### 理由
1. 避免不必要的 API 調用
2. 支援預創建但延遲初始化的場景
3. 明確的資源生命週期管理

### 代碼示例
```python
class CodeInterpreterAdapter:
    def __init__(self, config: Optional[CodeInterpreterConfig] = None):
        self._config = config or CodeInterpreterConfig()
        self._manager = AssistantManagerService()
        self._assistant_id: Optional[str] = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            assistant = self._manager.create_assistant(...)
            self._assistant_id = assistant.id
            self._initialized = True
```

---

## D37-3: 同步 vs 異步 API

### 背景
Azure OpenAI SDK 同時支援同步和異步客戶端。

### 決策
Sprint 37 先使用同步 API，後續可擴展為異步。

### 理由
1. 同步 API 更簡單，易於調試
2. Code Interpreter 本身有等待時間，同步模型足夠
3. 後續可通過 `asyncio.to_thread()` 包裝

### 影響
- API 端點使用 `def` 而非 `async def`
- 後續 Sprint 38 可以添加異步支援

---

## D37-4: 錯誤處理策略

### 背景
Code Interpreter 執行可能遇到多種錯誤：超時、API 錯誤、代碼錯誤等。

### 決策
採用分層錯誤處理：
1. 底層：捕獲所有異常，轉換為標準化結果
2. 中層：區分可重試和不可重試錯誤
3. 頂層：API 返回統一的錯誤格式

### 錯誤類型
```python
class AssistantError(Exception):
    """Assistant 服務基礎異常"""

class ExecutionTimeoutError(AssistantError):
    """執行超時"""

class AssistantNotFoundError(AssistantError):
    """Assistant 不存在"""

class CodeExecutionError(AssistantError):
    """代碼執行錯誤"""
```

---

## D37-5: Assistant 生命週期管理

### 背景
每個 CodeInterpreterAdapter 實例創建一個 Assistant，需要管理其生命週期。

### 決策
- 每個 Adapter 實例管理一個 Assistant
- 提供 `cleanup()` 方法刪除 Assistant
- API 層使用單例模式（簡化版）

### 生命週期
```
創建 Adapter → 首次使用時創建 Assistant → 使用 → cleanup() 刪除 Assistant
```

### 後續優化（Sprint 38+）
- Assistant 池化管理
- 自動清理過期 Assistant
- 使用 DI 容器管理

---

**創建日期**: 2025-12-21
**上次更新**: 2025-12-21
