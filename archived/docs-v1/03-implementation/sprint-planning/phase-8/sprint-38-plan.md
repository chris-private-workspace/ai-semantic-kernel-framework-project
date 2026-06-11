# Sprint 38: Agent 整合與擴展

**Sprint 目標**: 將 Code Interpreter 整合到現有 Agent 工作流程，實現文件處理和結果可視化
**總點數**: 15 Story Points
**優先級**: 🟡 IMPORTANT
**前置條件**: Sprint 37 完成

---

## 背景

Sprint 37 建立了 Code Interpreter 基礎設施後，本 Sprint 將這個能力深度整合到 IPA Platform 的 Agent 系統中，讓 Agent 可以：

1. 在工作流程中動態調用 Code Interpreter
2. 處理用戶上傳的文件 (CSV, Excel, JSON 等)
3. 生成可視化結果 (圖表、報表)
4. 與其他 Agent 工具協同工作

### 整合架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Workflow                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │   Agent A   │ → │   Agent B   │ → │   Agent C   │        │
│  │  (分析任務) │   │ (Code執行)  │   │  (結果整合) │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           CodeInterpreterTool                        │    │
│  │  + execute_code() - 執行 Python 代碼                │    │
│  │  + analyze_file() - 分析上傳文件                    │    │
│  │  + generate_visualization() - 生成圖表              │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           FileStorageService                         │    │
│  │  + upload() - 上傳文件到 Azure                      │    │
│  │  + download() - 下載結果文件                        │    │
│  │  + list_files() - 列出文件                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Story 清單

### S38-1: Agent 工具擴展 - Code Interpreter 支援 (5 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 擴展
**影響範圍**: `backend/src/integrations/agent_framework/tools/`

#### 設計

```python
# 文件: backend/src/integrations/agent_framework/tools/code_interpreter_tool.py

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

from ..builders.code_interpreter import CodeInterpreterAdapter, ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具執行結果。"""
    success: bool
    output: Any
    metadata: Dict[str, Any]


class CodeInterpreterTool:
    """Code Interpreter 工具 - 供 Agent 使用。

    將 CodeInterpreterAdapter 封裝為 Agent 可調用的工具。
    遵循 Agent Framework 的 Tool 規範。

    Example:
        ```python
        tool = CodeInterpreterTool()

        # Agent 調用執行代碼
        result = await tool.run(
            action="execute",
            code="import pandas as pd; print(pd.__version__)"
        )

        # Agent 調用分析文件
        result = await tool.run(
            action="analyze",
            file_id="file-abc123",
            prompt="Summarize this data"
        )
        ```
    """

    name: str = "code_interpreter"
    description: str = "Execute Python code and analyze data files"

    def __init__(self, adapter: Optional[CodeInterpreterAdapter] = None):
        """初始化工具。

        Args:
            adapter: 可選的 CodeInterpreterAdapter 實例
        """
        self._adapter = adapter or CodeInterpreterAdapter()

    async def run(
        self,
        action: str,
        **kwargs: Any,
    ) -> ToolResult:
        """執行工具操作。

        Args:
            action: 操作類型 (execute, analyze, visualize)
            **kwargs: 操作參數

        Returns:
            ToolResult 包含執行結果
        """
        if action == "execute":
            return await self._execute_code(**kwargs)
        elif action == "analyze":
            return await self._analyze_file(**kwargs)
        elif action == "visualize":
            return await self._generate_visualization(**kwargs)
        else:
            return ToolResult(
                success=False,
                output=f"Unknown action: {action}",
                metadata={"action": action},
            )

    async def _execute_code(
        self,
        code: str,
        timeout: int = 60,
        **kwargs,
    ) -> ToolResult:
        """執行 Python 代碼。"""
        result = self._adapter.execute(code=code, timeout=timeout)
        return ToolResult(
            success=result.success,
            output=result.output,
            metadata={
                "execution_time": result.execution_time,
                "files": result.files,
            },
        )

    async def _analyze_file(
        self,
        file_id: str,
        prompt: str,
        **kwargs,
    ) -> ToolResult:
        """分析文件。"""
        # 構建分析任務
        task = f"Analyze the file with ID {file_id}. {prompt}"
        result = self._adapter.analyze_task(task=task)
        return ToolResult(
            success=result.success,
            output=result.output,
            metadata={
                "file_id": file_id,
                "execution_time": result.execution_time,
            },
        )

    async def _generate_visualization(
        self,
        data: Dict[str, Any],
        chart_type: str = "bar",
        **kwargs,
    ) -> ToolResult:
        """生成可視化。"""
        code = self._generate_chart_code(data, chart_type)
        result = self._adapter.execute(code=code)
        return ToolResult(
            success=result.success,
            output=result.output,
            metadata={
                "chart_type": chart_type,
                "files": result.files,
            },
        )

    def _generate_chart_code(
        self,
        data: Dict[str, Any],
        chart_type: str,
    ) -> str:
        """生成圖表代碼。"""
        return f"""
import matplotlib.pyplot as plt
import json

data = {json.dumps(data)}
# Generate {chart_type} chart
plt.figure(figsize=(10, 6))
plt.{chart_type}(data.keys(), data.values())
plt.title('Generated Chart')
plt.savefig('chart.png')
print('Chart saved as chart.png')
"""

    def cleanup(self) -> None:
        """清理資源。"""
        self._adapter.cleanup()
```

#### 任務清單

1. **創建工具結構**
   ```
   backend/src/integrations/agent_framework/tools/
   ├── __init__.py
   ├── base.py                    # Tool 基類
   └── code_interpreter_tool.py   # Code Interpreter 工具
   ```

2. **實現 CodeInterpreterTool**
   - 遵循 Agent Framework Tool 規範
   - 支援 execute, analyze, visualize 操作
   - 整合 CodeInterpreterAdapter

3. **註冊到 Agent 工具系統**
   - 更新工具註冊表
   - 添加工具發現機制

#### 驗收標準
- [ ] CodeInterpreterTool 類實現完成
- [ ] 遵循 Tool 規範接口
- [ ] Agent 可以調用此工具
- [ ] 所有操作類型正常工作

---

### S38-2: 文件上傳與處理功能 (5 pts)

**優先級**: 🟡 P1
**類型**: 新增
**影響範圍**: `backend/src/integrations/agent_framework/assistant/files.py`

#### 設計

```python
# 文件: backend/src/integrations/agent_framework/assistant/files.py

from typing import Optional, List, BinaryIO
from dataclasses import dataclass
from pathlib import Path
from openai import AzureOpenAI
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """文件信息。"""
    id: str
    filename: str
    bytes: int
    created_at: int
    purpose: str


class FileStorageService:
    """文件存儲服務。

    管理上傳到 Azure OpenAI 的文件，支援 Code Interpreter 文件處理。

    Example:
        ```python
        service = FileStorageService(client)

        # 上傳文件
        file_info = await service.upload(
            file=open("data.csv", "rb"),
            filename="data.csv",
            purpose="assistants"
        )

        # 列出文件
        files = await service.list_files()

        # 下載文件
        content = await service.download(file_info.id)

        # 刪除文件
        await service.delete(file_info.id)
        ```
    """

    def __init__(self, client: Optional[AzureOpenAI] = None):
        """初始化文件服務。

        Args:
            client: Azure OpenAI 客戶端
        """
        if client is None:
            from src.core.config import settings
            client = AzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )
        self._client = client

    def upload(
        self,
        file: BinaryIO,
        filename: str,
        purpose: str = "assistants",
    ) -> FileInfo:
        """上傳文件。

        Args:
            file: 文件對象
            filename: 文件名
            purpose: 文件用途 (assistants, fine-tune, etc.)

        Returns:
            FileInfo 包含文件信息
        """
        result = self._client.files.create(
            file=(filename, file),
            purpose=purpose,
        )

        logger.info(f"Uploaded file: {result.id} ({filename})")

        return FileInfo(
            id=result.id,
            filename=result.filename,
            bytes=result.bytes,
            created_at=result.created_at,
            purpose=result.purpose,
        )

    def upload_from_path(
        self,
        path: Path,
        purpose: str = "assistants",
    ) -> FileInfo:
        """從路徑上傳文件。

        Args:
            path: 文件路徑
            purpose: 文件用途

        Returns:
            FileInfo 包含文件信息
        """
        with open(path, "rb") as f:
            return self.upload(f, path.name, purpose)

    def list_files(
        self,
        purpose: Optional[str] = None,
    ) -> List[FileInfo]:
        """列出文件。

        Args:
            purpose: 可選的用途過濾

        Returns:
            FileInfo 列表
        """
        files = self._client.files.list()

        result = []
        for f in files.data:
            if purpose is None or f.purpose == purpose:
                result.append(FileInfo(
                    id=f.id,
                    filename=f.filename,
                    bytes=f.bytes,
                    created_at=f.created_at,
                    purpose=f.purpose,
                ))

        return result

    def download(self, file_id: str) -> bytes:
        """下載文件內容。

        Args:
            file_id: 文件 ID

        Returns:
            文件內容 (bytes)
        """
        content = self._client.files.content(file_id)
        return content.read()

    def delete(self, file_id: str) -> bool:
        """刪除文件。

        Args:
            file_id: 文件 ID

        Returns:
            是否刪除成功
        """
        try:
            self._client.files.delete(file_id)
            logger.info(f"Deleted file: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False
```

#### API 端點擴展

```python
# 文件: backend/src/api/v1/code_interpreter/routes.py (擴展)

from fastapi import UploadFile, File

@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """上傳文件供 Code Interpreter 使用。"""
    service = FileStorageService()
    file_info = service.upload(
        file=file.file,
        filename=file.filename,
    )
    return {
        "id": file_info.id,
        "filename": file_info.filename,
        "bytes": file_info.bytes,
    }

@router.get("/files")
async def list_files():
    """列出所有上傳的文件。"""
    service = FileStorageService()
    files = service.list_files(purpose="assistants")
    return {"files": [f.__dict__ for f in files]}

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """刪除文件。"""
    service = FileStorageService()
    success = service.delete(file_id)
    return {"success": success}
```

#### 任務清單

1. **實現 FileStorageService**
   - 文件上傳
   - 文件列表
   - 文件下載
   - 文件刪除

2. **擴展 API 端點**
   - `POST /files/upload` - 上傳文件
   - `GET /files` - 列出文件
   - `DELETE /files/{file_id}` - 刪除文件

3. **整合到 CodeInterpreterAdapter**
   - 支援帶文件的分析任務

#### 驗收標準
- [ ] FileStorageService 實現完成
- [ ] 文件上傳 API 可用
- [ ] 支援 CSV, Excel, JSON 等格式
- [ ] 文件可以被 Code Interpreter 讀取

---

### S38-3: 執行結果可視化 (3 pts)

**優先級**: 🟡 P1
**類型**: 新增
**影響範圍**: `backend/src/api/v1/code_interpreter/`

#### 設計

```python
# 文件: backend/src/api/v1/code_interpreter/visualization.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Optional
import io

router = APIRouter()


@router.get("/visualizations/{file_id}")
async def get_visualization(file_id: str):
    """獲取生成的可視化圖表。

    Args:
        file_id: 圖表文件 ID

    Returns:
        圖片文件流
    """
    service = FileStorageService()
    content = service.download(file_id)

    return StreamingResponse(
        io.BytesIO(content),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={file_id}.png"},
    )


@router.post("/visualizations/generate")
async def generate_visualization(request: VisualizationRequest):
    """生成可視化圖表。

    Args:
        request: 包含數據和圖表類型

    Returns:
        生成的圖表信息
    """
    adapter = get_adapter()

    code = f"""
import matplotlib.pyplot as plt
import json

data = {json.dumps(request.data)}
plt.figure(figsize=(10, 6))
plt.{request.chart_type}(list(data.keys()), list(data.values()))
plt.title('{request.title or "Chart"}')
plt.xlabel('{request.x_label or ""}')
plt.ylabel('{request.y_label or ""}')
plt.tight_layout()
plt.savefig('output.png', dpi=150)
print('Chart generated successfully')
"""

    result = adapter.execute(code=code)

    return {
        "success": result.success,
        "message": result.output,
        "files": result.files,
    }
```

#### 任務清單

1. **實現可視化端點**
   - `GET /visualizations/{file_id}` - 獲取圖表
   - `POST /visualizations/generate` - 生成圖表

2. **支援圖表類型**
   - bar (柱狀圖)
   - line (折線圖)
   - pie (圓餅圖)
   - scatter (散點圖)

3. **響應格式**
   - 圖片直接下載
   - Base64 編碼選項

#### 驗收標準
- [ ] 可視化 API 可用
- [ ] 支援多種圖表類型
- [ ] 圖片可以正確顯示/下載

---

### S38-4: 文檔更新和示例 (2 pts)

**優先級**: 🟢 P2
**類型**: 文檔
**影響範圍**: `docs/`, `examples/`

#### 任務清單

1. **API 文檔更新**
   - 更新 OpenAPI 文檔
   - 添加使用說明
   - 添加錯誤代碼說明

2. **示例代碼**
   - Python SDK 使用示例
   - cURL 命令示例
   - 完整工作流示例

3. **README 更新**
   - 更新功能列表
   - 添加 Code Interpreter 章節

#### 驗收標準
- [ ] API 文檔完整
- [ ] 示例代碼可運行
- [ ] README 更新

---

## 驗證命令

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/agent_framework/tools/code_interpreter_tool.py
python -m py_compile src/integrations/agent_framework/assistant/files.py

# 2. 運行測試
pytest tests/unit/integrations/agent_framework/tools/ -v
pytest tests/integration/test_file_upload.py -v

# 3. API 測試
# 上傳文件
curl -X POST http://localhost:8000/api/v1/code-interpreter/files/upload \
  -F "file=@data.csv"

# 生成圖表
curl -X POST http://localhost:8000/api/v1/code-interpreter/visualizations/generate \
  -H "Content-Type: application/json" \
  -d '{"data": {"A": 10, "B": 20, "C": 30}, "chart_type": "bar"}'

# 4. 類型檢查
mypy src/integrations/agent_framework/tools/
```

---

## 完成定義

- [ ] 所有 S38 Story 完成
- [ ] CodeInterpreterTool 整合到 Agent 系統
- [ ] 文件上傳/下載功能可用
- [ ] 可視化生成功能可用
- [ ] 文檔和示例完成
- [ ] 測試覆蓋率 > 85%

---

**創建日期**: 2025-12-21
