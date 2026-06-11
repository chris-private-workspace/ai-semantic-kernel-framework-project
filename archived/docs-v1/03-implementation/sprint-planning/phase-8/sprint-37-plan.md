# Sprint 37: Code Interpreter 基礎設施

**Sprint 目標**: 建立 Code Interpreter 服務層，實現基礎程式碼執行能力
**總點數**: 20 Story Points
**優先級**: 🔴 CRITICAL

---

## 背景

Azure OpenAI Assistants API 的 Code Interpreter 功能已在本項目中驗證成功。本 Sprint 將這個能力整合到 IPA Platform 中，讓 Agent 能夠執行 Python 程式碼。

### 已驗證配置

```python
# scripts/test_azure_ai_agent_service.py 驗證結果
PROJECT_ENDPOINT = "https://azureopenaiservicechris.services.ai.azure.com/api/projects/AzureOpenAIServiceChris-project"
AZURE_OPENAI_ENDPOINT = "https://azureopenaiservicechris.cognitiveservices.azure.com/"
MODEL_DEPLOYMENT = "gpt-5-nano"
API_VERSION = "2024-12-01-preview"

# 測試結果:
# ✅ Chat Completion: 成功
# ✅ Assistants API: 成功
# ✅ Code Interpreter: 成功 (計算 sum(range(1,101)) = 5050)
```

---

## Story 清單

### S37-1: AssistantManagerService 設計與實現 (8 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/agent_framework/assistant/`

#### 設計

```python
# 文件: backend/src/integrations/agent_framework/assistant/manager.py

from typing import List, Optional, Dict, Any
from openai import AzureOpenAI
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeExecutionResult:
    """程式碼執行結果。"""
    status: str  # "success" | "error" | "timeout"
    output: str  # 執行輸出或錯誤訊息
    execution_time: float  # 執行耗時 (秒)
    files: List[Dict[str, Any]]  # 生成的文件


class AssistantManagerService:
    """Azure OpenAI Assistants 管理服務。

    負責創建和管理 Assistants，處理 Thread 和 Run 生命週期。
    專門設計用於 Code Interpreter 功能。

    Example:
        ```python
        manager = AssistantManagerService(client)

        # 創建 Assistant
        assistant = await manager.create_assistant(
            name="Data Analyst",
            instructions="You are a data analysis assistant.",
        )

        # 執行程式碼
        result = await manager.execute_code(
            assistant_id=assistant.id,
            code="print(sum(range(1, 101)))"
        )
        print(result.output)  # "5050"

        # 清理
        await manager.delete_assistant(assistant.id)
        ```
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: str = "2024-12-01-preview",
    ):
        """初始化 Assistant Manager。

        Args:
            endpoint: Azure OpenAI 端點
            api_key: API 金鑰
            deployment: 模型部署名稱
            api_version: API 版本
        """
        from src.core.config import settings

        self._endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self._api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self._deployment = deployment or settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self._api_version = api_version

        self._client = AzureOpenAI(
            azure_endpoint=self._endpoint,
            api_key=self._api_key,
            api_version=self._api_version,
        )

        logger.info(f"AssistantManagerService initialized: {self._deployment}")

    def create_assistant(
        self,
        name: str,
        instructions: str,
        tools: Optional[List[Dict[str, str]]] = None,
    ):
        """創建帶 Code Interpreter 的 Assistant。

        Args:
            name: Assistant 名稱
            instructions: 系統指令
            tools: 工具列表，默認包含 code_interpreter

        Returns:
            Assistant 對象
        """
        if tools is None:
            tools = [{"type": "code_interpreter"}]

        assistant = self._client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=self._deployment,
            tools=tools,
        )

        logger.info(f"Created assistant: {assistant.id} ({name})")
        return assistant

    def execute_code(
        self,
        assistant_id: str,
        code: str,
        timeout: int = 60,
    ) -> CodeExecutionResult:
        """執行程式碼並返回結果。

        Args:
            assistant_id: Assistant ID
            code: 要執行的 Python 程式碼
            timeout: 超時時間 (秒)

        Returns:
            CodeExecutionResult 包含執行結果
        """
        start_time = time.time()

        try:
            # 創建 Thread
            thread = self._client.beta.threads.create()

            # 發送程式碼執行請求
            prompt = f"Execute this Python code and return the result:\n```python\n{code}\n```"
            self._client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt,
            )

            # 運行 Assistant
            run = self._client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id,
            )

            # 等待完成
            while run.status in ["queued", "in_progress"]:
                if time.time() - start_time > timeout:
                    return CodeExecutionResult(
                        status="timeout",
                        output=f"Execution timed out after {timeout} seconds",
                        execution_time=time.time() - start_time,
                        files=[],
                    )
                time.sleep(1)
                run = self._client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                )

            execution_time = time.time() - start_time

            if run.status == "completed":
                # 獲取響應
                messages = self._client.beta.threads.messages.list(
                    thread_id=thread.id
                )

                output = ""
                files = []

                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if content.type == "text":
                                output = content.text.value
                            elif content.type == "image_file":
                                files.append({
                                    "type": "image",
                                    "file_id": content.image_file.file_id,
                                })
                        break

                return CodeExecutionResult(
                    status="success",
                    output=output,
                    execution_time=execution_time,
                    files=files,
                )
            else:
                error_msg = "Unknown error"
                if hasattr(run, 'last_error') and run.last_error:
                    error_msg = str(run.last_error)

                return CodeExecutionResult(
                    status="error",
                    output=error_msg,
                    execution_time=execution_time,
                    files=[],
                )

        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return CodeExecutionResult(
                status="error",
                output=str(e),
                execution_time=time.time() - start_time,
                files=[],
            )

    def delete_assistant(self, assistant_id: str) -> bool:
        """刪除 Assistant。

        Args:
            assistant_id: 要刪除的 Assistant ID

        Returns:
            是否刪除成功
        """
        try:
            self._client.beta.assistants.delete(assistant_id)
            logger.info(f"Deleted assistant: {assistant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete assistant {assistant_id}: {e}")
            return False

    def list_assistants(self, limit: int = 20):
        """列出所有 Assistants。

        Args:
            limit: 返回數量限制

        Returns:
            Assistants 列表
        """
        return self._client.beta.assistants.list(limit=limit)
```

#### 任務清單

1. **創建目錄結構**
   ```
   backend/src/integrations/agent_framework/assistant/
   ├── __init__.py
   ├── manager.py          # AssistantManagerService
   ├── models.py           # 數據模型 (CodeExecutionResult 等)
   └── exceptions.py       # 自定義異常
   ```

2. **實現 AssistantManagerService**
   - `create_assistant()` - 創建帶 code_interpreter 的 Assistant
   - `execute_code()` - 執行程式碼
   - `delete_assistant()` - 刪除 Assistant
   - `list_assistants()` - 列出所有 Assistants

3. **實現數據模型**
   - `CodeExecutionResult` - 執行結果
   - `AssistantConfig` - 配置選項
   - `ExecutionContext` - 執行上下文

4. **錯誤處理**
   - 超時處理
   - API 錯誤處理
   - 資源清理

#### 驗收標準
- [ ] AssistantManagerService 類實現完成
- [ ] 可以創建帶 Code Interpreter 的 Assistant
- [ ] 可以執行 Python 程式碼並獲取結果
- [ ] 超時機制正常工作
- [ ] 錯誤處理完善
- [ ] 資源可以正確清理

---

### S37-2: CodeInterpreterAdapter 適配器實現 (5 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/agent_framework/builders/code_interpreter.py`

#### 設計

```python
# 文件: backend/src/integrations/agent_framework/builders/code_interpreter.py

from typing import Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
import logging

from ..assistant.manager import AssistantManagerService, CodeExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class CodeInterpreterConfig:
    """Code Interpreter 配置。"""
    assistant_name: str = "IPA-CodeInterpreter"
    instructions: str = "You are a Python code execution assistant. Execute code accurately and return results."
    timeout: int = 60
    max_retries: int = 3


@dataclass
class ExecutionResult:
    """統一執行結果格式。"""
    success: bool
    output: str
    execution_time: float
    files: list = field(default_factory=list)
    error: Optional[str] = None


class CodeInterpreterAdapter:
    """Code Interpreter 適配器。

    將 Azure OpenAI Code Interpreter 功能封裝為 IPA Platform 標準接口。
    遵循 Adapter Pattern，與其他 Builder Adapters 保持一致的使用方式。

    Example:
        ```python
        adapter = CodeInterpreterAdapter()

        # 執行程式碼
        result = await adapter.execute("print(2 + 2)")
        print(result.output)  # "4"

        # 執行數據分析任務
        result = await adapter.analyze_task(
            "Calculate the factorial of 10"
        )
        print(result.output)  # "3628800"

        # 清理資源
        await adapter.cleanup()
        ```

    Note:
        - 使用 Azure OpenAI Assistants API
        - 每個 Adapter 實例管理一個 Assistant
        - 使用後應調用 cleanup() 釋放資源
    """

    def __init__(
        self,
        config: Optional[CodeInterpreterConfig] = None,
        manager: Optional[AssistantManagerService] = None,
    ):
        """初始化 Code Interpreter 適配器。

        Args:
            config: 配置選項
            manager: 可選的 AssistantManagerService 實例
        """
        self._config = config or CodeInterpreterConfig()
        self._manager = manager or AssistantManagerService()
        self._assistant_id: Optional[str] = None
        self._initialized = False

        logger.info("CodeInterpreterAdapter created")

    def _ensure_initialized(self) -> None:
        """確保 Assistant 已初始化。"""
        if not self._initialized:
            assistant = self._manager.create_assistant(
                name=self._config.assistant_name,
                instructions=self._config.instructions,
            )
            self._assistant_id = assistant.id
            self._initialized = True
            logger.info(f"CodeInterpreterAdapter initialized with assistant: {self._assistant_id}")

    def execute(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """執行 Python 程式碼。

        Args:
            code: 要執行的 Python 代碼
            timeout: 可選的超時時間 (秒)

        Returns:
            ExecutionResult 包含執行結果
        """
        self._ensure_initialized()

        result = self._manager.execute_code(
            assistant_id=self._assistant_id,
            code=code,
            timeout=timeout or self._config.timeout,
        )

        return ExecutionResult(
            success=(result.status == "success"),
            output=result.output,
            execution_time=result.execution_time,
            files=result.files,
            error=result.output if result.status == "error" else None,
        )

    def analyze_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """執行分析任務。

        讓 AI 生成並執行程式碼來完成分析任務。

        Args:
            task: 任務描述
            context: 可選的上下文信息

        Returns:
            ExecutionResult 包含分析結果
        """
        self._ensure_initialized()

        # 構建提示詞
        prompt = f"Task: {task}\n"
        if context:
            prompt += f"Context: {context}\n"
        prompt += "\nWrite and execute Python code to complete this task. Return the result."

        # 通過 Thread 執行
        result = self._manager.execute_code(
            assistant_id=self._assistant_id,
            code=prompt,  # 這裡實際上是任務描述，Assistant 會自動生成代碼
            timeout=self._config.timeout,
        )

        return ExecutionResult(
            success=(result.status == "success"),
            output=result.output,
            execution_time=result.execution_time,
            files=result.files,
            error=result.output if result.status == "error" else None,
        )

    def cleanup(self) -> bool:
        """清理資源，刪除 Assistant。

        Returns:
            是否清理成功
        """
        if self._assistant_id:
            success = self._manager.delete_assistant(self._assistant_id)
            if success:
                self._assistant_id = None
                self._initialized = False
            return success
        return True

    @property
    def is_initialized(self) -> bool:
        """檢查是否已初始化。"""
        return self._initialized

    @property
    def assistant_id(self) -> Optional[str]:
        """獲取當前 Assistant ID。"""
        return self._assistant_id
```

#### 任務清單

1. **實現 CodeInterpreterAdapter**
   - Lazy initialization (首次使用時創建 Assistant)
   - `execute()` - 直接執行程式碼
   - `analyze_task()` - 執行分析任務
   - `cleanup()` - 資源清理

2. **配置模型**
   - `CodeInterpreterConfig` - 配置選項
   - `ExecutionResult` - 統一結果格式

3. **整合到 builders 模組**
   - 更新 `__init__.py` 導出
   - 與其他 Adapter 保持一致風格

#### 驗收標準
- [ ] CodeInterpreterAdapter 類實現完成
- [ ] 遵循 Adapter Pattern
- [ ] 與其他 Builder Adapters 保持一致接口風格
- [ ] Lazy initialization 正常工作
- [ ] 資源清理正確

---

### S37-3: Code Interpreter API 端點 (4 pts)

**優先級**: 🟡 P1
**類型**: 新增
**影響範圍**: `backend/src/api/v1/code_interpreter/`

#### 設計

```python
# 文件: backend/src/api/v1/code_interpreter/routes.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from src.integrations.agent_framework.builders.code_interpreter import (
    CodeInterpreterAdapter,
    CodeInterpreterConfig,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/code-interpreter", tags=["code-interpreter"])


# 請求/響應 Schema
class ExecuteCodeRequest(BaseModel):
    """程式碼執行請求。"""
    code: str = Field(..., description="要執行的 Python 代碼")
    timeout: Optional[int] = Field(60, description="超時時間 (秒)")


class AnalyzeTaskRequest(BaseModel):
    """分析任務請求。"""
    task: str = Field(..., description="任務描述")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class ExecutionResponse(BaseModel):
    """執行響應。"""
    success: bool
    output: str
    execution_time: float
    files: List[Dict[str, Any]] = []
    error: Optional[str] = None


# 單例 Adapter (簡化版，生產環境應使用 DI)
_adapter: Optional[CodeInterpreterAdapter] = None


def get_adapter() -> CodeInterpreterAdapter:
    """獲取 CodeInterpreterAdapter 實例。"""
    global _adapter
    if _adapter is None:
        _adapter = CodeInterpreterAdapter()
    return _adapter


@router.post("/execute", response_model=ExecutionResponse)
async def execute_code(request: ExecuteCodeRequest):
    """執行 Python 程式碼。

    Args:
        request: 執行請求

    Returns:
        執行結果
    """
    try:
        adapter = get_adapter()
        result = adapter.execute(
            code=request.code,
            timeout=request.timeout,
        )

        return ExecutionResponse(
            success=result.success,
            output=result.output,
            execution_time=result.execution_time,
            files=result.files,
            error=result.error,
        )
    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/analyze", response_model=ExecutionResponse)
async def analyze_task(request: AnalyzeTaskRequest):
    """執行分析任務。

    Args:
        request: 分析請求

    Returns:
        分析結果
    """
    try:
        adapter = get_adapter()
        result = adapter.analyze_task(
            task=request.task,
            context=request.context,
        )

        return ExecutionResponse(
            success=result.success,
            output=result.output,
            execution_time=result.execution_time,
            files=result.files,
            error=result.error,
        )
    except Exception as e:
        logger.error(f"Task analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/health")
async def health_check():
    """健康檢查。"""
    return {"status": "healthy", "service": "code-interpreter"}
```

#### 任務清單

1. **創建 API 結構**
   ```
   backend/src/api/v1/code_interpreter/
   ├── __init__.py
   ├── routes.py           # API 路由
   └── schemas.py          # Pydantic Schema
   ```

2. **實現端點**
   - `POST /execute` - 執行程式碼
   - `POST /analyze` - 執行分析任務
   - `GET /health` - 健康檢查

3. **註冊路由**
   - 更新 `main.py` 註冊新路由
   - 添加 OpenAPI 文檔說明

#### 驗收標準
- [ ] API 端點可訪問
- [ ] 請求/響應格式正確
- [ ] 錯誤處理完善
- [ ] OpenAPI 文檔完整

---

### S37-4: 單元測試和整合測試 (3 pts)

**優先級**: 🟡 P1
**類型**: 測試
**影響範圍**: `backend/tests/unit/integrations/agent_framework/assistant/`

#### 任務清單

1. **創建測試結構**
   ```
   backend/tests/unit/integrations/agent_framework/assistant/
   ├── __init__.py
   ├── test_manager.py
   └── test_code_interpreter.py

   backend/tests/integration/
   └── test_code_interpreter_api.py
   ```

2. **測試用例**
   - AssistantManagerService 單元測試
   - CodeInterpreterAdapter 單元測試
   - API 端點整合測試

3. **Mock 策略**
   - Mock AzureOpenAI 客戶端
   - Mock Assistants API 響應

#### 驗收標準
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] 無真實 API 調用 (全部 Mock)

---

## 驗證命令

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/agent_framework/assistant/manager.py
python -m py_compile src/integrations/agent_framework/builders/code_interpreter.py
python -m py_compile src/api/v1/code_interpreter/routes.py

# 2. 運行單元測試
pytest tests/unit/integrations/agent_framework/assistant/ -v

# 3. 運行整合測試
pytest tests/integration/test_code_interpreter_api.py -v

# 4. 測試真實 API (需要有效配置)
curl -X POST http://localhost:8000/api/v1/code-interpreter/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(sum(range(1, 101)))"}'

# 5. 類型檢查
mypy src/integrations/agent_framework/assistant/
mypy src/integrations/agent_framework/builders/code_interpreter.py
```

---

## 完成定義

- [ ] 所有 S37 Story 完成
- [ ] AssistantManagerService 實現完成
- [ ] CodeInterpreterAdapter 適配器完成
- [ ] API 端點可用
- [ ] 測試覆蓋率 > 85%
- [ ] 文檔更新完成

---

**創建日期**: 2025-12-21
