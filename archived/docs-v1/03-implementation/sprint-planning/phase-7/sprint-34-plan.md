# Sprint 34: LLM 服務基礎設施

**Sprint 目標**: 創建統一的 LLM 服務層，支援 Azure OpenAI 整合
**總點數**: 20 Story Points
**優先級**: 🔴 CRITICAL

---

## 背景

為了讓 Phase 2 擴展功能（TaskDecomposer、DecisionEngine、TrialAndErrorEngine）能夠使用真正的 LLM 進行 AI 自主決策，需要首先建立一個統一的 LLM 服務層。

### 設計目標

1. **統一接口**: 定義 `LLMServiceProtocol` 供所有組件使用
2. **多實現支援**: Azure OpenAI (生產)、Mock (測試)、Cached (優化)
3. **配置靈活**: 支援環境變量和配置文件
4. **錯誤處理**: 優雅降級和重試機制

---

## Story 清單

### S34-1: LLMService 接口和 Azure OpenAI 實現 (8 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/llm/`

#### 設計

```python
# 文件: backend/src/integrations/llm/protocol.py

from typing import Protocol, Any, Dict, Optional
from abc import abstractmethod


class LLMServiceProtocol(Protocol):
    """LLM 服務協議 - 所有 LLM 實現必須遵循此接口。"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> str:
        """生成文本回應。

        Args:
            prompt: 輸入提示詞
            max_tokens: 最大生成 token 數
            temperature: 創造性參數 (0-1)

        Returns:
            生成的文本
        """
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        max_tokens: int = 2000,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """生成結構化 JSON 回應。

        Args:
            prompt: 輸入提示詞
            output_schema: 預期的 JSON Schema
            max_tokens: 最大生成 token 數

        Returns:
            解析後的 JSON 對象
        """
        ...
```

```python
# 文件: backend/src/integrations/llm/azure_openai.py

from typing import Any, Dict, Optional
from openai import AsyncAzureOpenAI
import json
import logging

from .protocol import LLMServiceProtocol
from src.core.config import settings

logger = logging.getLogger(__name__)


class AzureOpenAILLMService:
    """Azure OpenAI LLM 服務實現。

    使用 Azure OpenAI API 進行文本生成和結構化輸出。

    Example:
        ```python
        service = AzureOpenAILLMService()
        response = await service.generate("Explain quantum computing")
        print(response)
        ```
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
    ):
        """初始化 Azure OpenAI 服務。

        Args:
            endpoint: Azure OpenAI 端點 URL
            api_key: API 密鑰
            deployment_name: 部署名稱 (模型)
            api_version: API 版本
        """
        self._endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self._api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self._deployment = deployment_name or settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self._api_version = api_version

        self._client = AsyncAzureOpenAI(
            azure_endpoint=self._endpoint,
            api_key=self._api_key,
            api_version=self._api_version,
        )

        logger.info(f"AzureOpenAILLMService initialized with deployment: {self._deployment}")

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> str:
        """生成文本回應。"""
        try:
            response = await self._client.chat.completions.create(
                model=self._deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        max_tokens: int = 2000,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """生成結構化 JSON 回應。"""
        structured_prompt = f"""{prompt}

Please respond with a valid JSON object matching this schema:
{json.dumps(output_schema, indent=2)}

Respond ONLY with the JSON object, no additional text."""

        try:
            response = await self._client.chat.completions.create(
                model=self._deployment,
                messages=[{"role": "user", "content": structured_prompt}],
                max_tokens=max_tokens,
                temperature=0.3,  # 降低溫度以提高結構化輸出穩定性
                response_format={"type": "json_object"},
                **kwargs
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Structured LLM generation failed: {e}")
            raise
```

#### 任務清單

1. **創建目錄結構**
   ```
   backend/src/integrations/llm/
   ├── __init__.py
   ├── protocol.py          # LLMServiceProtocol
   ├── azure_openai.py      # Azure OpenAI 實現
   ├── mock.py              # Mock 實現 (測試用)
   ├── cached.py            # 緩存包裝器
   └── factory.py           # 服務工廠
   ```

2. **實現 LLMServiceProtocol**
   - 定義 `generate()` 方法
   - 定義 `generate_structured()` 方法
   - 添加類型註解和文檔

3. **實現 AzureOpenAILLMService**
   - 使用 `openai` SDK 的 `AsyncAzureOpenAI`
   - 支援配置注入和環境變量
   - 實現錯誤處理和日誌

4. **實現 MockLLMService**
   - 用於單元測試
   - 可配置回應內容
   - 支援延遲模擬

#### 驗收標準
- [ ] `LLMServiceProtocol` 定義完成
- [ ] `AzureOpenAILLMService` 實現完成
- [ ] `MockLLMService` 測試實現完成
- [ ] 所有代碼有完整文檔和類型註解
- [ ] 語法檢查通過

---

### S34-2: LLM 服務工廠和配置管理 (5 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/llm/factory.py`

#### 設計

```python
# 文件: backend/src/integrations/llm/factory.py

from enum import Enum
from typing import Optional
import logging

from .protocol import LLMServiceProtocol
from .azure_openai import AzureOpenAILLMService
from .mock import MockLLMService
from .cached import CachedLLMService
from src.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM 服務提供者類型。"""
    AZURE_OPENAI = "azure_openai"
    MOCK = "mock"
    CACHED = "cached"


class LLMServiceFactory:
    """LLM 服務工廠。

    負責創建和管理 LLM 服務實例。

    Example:
        ```python
        # 創建默認服務 (Azure OpenAI)
        service = LLMServiceFactory.create()

        # 創建 Mock 服務 (測試)
        service = LLMServiceFactory.create(provider=LLMProvider.MOCK)

        # 創建帶緩存的服務
        service = LLMServiceFactory.create(provider=LLMProvider.CACHED)
        ```
    """

    _instance: Optional[LLMServiceProtocol] = None

    @classmethod
    def create(
        cls,
        provider: Optional[LLMProvider] = None,
        use_cache: bool = True,
        **kwargs
    ) -> LLMServiceProtocol:
        """創建 LLM 服務實例。

        Args:
            provider: 服務提供者類型
            use_cache: 是否使用緩存包裝
            **kwargs: 傳遞給服務構造函數的參數

        Returns:
            LLM 服務實例
        """
        # 確定提供者
        if provider is None:
            provider = cls._get_default_provider()

        # 創建基礎服務
        if provider == LLMProvider.AZURE_OPENAI:
            service = AzureOpenAILLMService(**kwargs)
        elif provider == LLMProvider.MOCK:
            service = MockLLMService(**kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # 可選：包裝緩存層
        if use_cache and provider != LLMProvider.MOCK:
            service = CachedLLMService(service)

        logger.info(f"Created LLM service: {provider.value} (cached={use_cache})")
        return service

    @classmethod
    def get_singleton(cls) -> LLMServiceProtocol:
        """獲取單例 LLM 服務。

        適用於全局共享的場景。
        """
        if cls._instance is None:
            cls._instance = cls.create()
        return cls._instance

    @classmethod
    def reset_singleton(cls) -> None:
        """重置單例（主要用於測試）。"""
        cls._instance = None

    @staticmethod
    def _get_default_provider() -> LLMProvider:
        """根據環境確定默認提供者。"""
        if settings.TESTING:
            return LLMProvider.MOCK
        return LLMProvider.AZURE_OPENAI
```

#### 任務清單

1. **實現 LLMServiceFactory**
   - `create()` 方法支援多種提供者
   - `get_singleton()` 全局單例支援
   - 自動根據環境選擇提供者

2. **實現 CachedLLMService**
   - 使用 Redis 緩存 LLM 回應
   - 支援 TTL 配置
   - 緩存 key 基於 prompt hash

3. **更新 __init__.py 導出**
   ```python
   from .protocol import LLMServiceProtocol
   from .azure_openai import AzureOpenAILLMService
   from .mock import MockLLMService
   from .cached import CachedLLMService
   from .factory import LLMServiceFactory, LLMProvider

   __all__ = [
       "LLMServiceProtocol",
       "AzureOpenAILLMService",
       "MockLLMService",
       "CachedLLMService",
       "LLMServiceFactory",
       "LLMProvider",
   ]
   ```

#### 驗收標準
- [ ] `LLMServiceFactory` 創建完成
- [ ] `CachedLLMService` 緩存包裝器完成
- [ ] 環境自動切換邏輯正確
- [ ] 單例模式正常工作

---

### S34-3: LLM 服務單元測試 (4 pts)

**優先級**: 🟡 P1
**類型**: 測試
**影響範圍**: `backend/tests/unit/integrations/llm/`

#### 任務清單

1. **創建測試結構**
   ```
   backend/tests/unit/integrations/llm/
   ├── __init__.py
   ├── test_protocol.py
   ├── test_azure_openai.py
   ├── test_mock.py
   ├── test_cached.py
   └── test_factory.py
   ```

2. **測試用例**

   ```python
   # test_azure_openai.py
   import pytest
   from unittest.mock import AsyncMock, patch

   from src.integrations.llm import AzureOpenAILLMService


   class TestAzureOpenAILLMService:
       """Azure OpenAI LLM 服務測試。"""

       @pytest.fixture
       def mock_client(self):
           """創建 mock OpenAI 客戶端。"""
           with patch("src.integrations.llm.azure_openai.AsyncAzureOpenAI") as mock:
               yield mock

       @pytest.mark.asyncio
       async def test_generate_returns_text(self, mock_client):
           """測試 generate 返回文本。"""
           # Arrange
           mock_response = AsyncMock()
           mock_response.choices = [
               AsyncMock(message=AsyncMock(content="Hello, World!"))
           ]
           mock_client.return_value.chat.completions.create = AsyncMock(
               return_value=mock_response
           )

           service = AzureOpenAILLMService()

           # Act
           result = await service.generate("Say hello")

           # Assert
           assert result == "Hello, World!"

       @pytest.mark.asyncio
       async def test_generate_structured_returns_json(self, mock_client):
           """測試 generate_structured 返回 JSON。"""
           # Arrange
           mock_response = AsyncMock()
           mock_response.choices = [
               AsyncMock(message=AsyncMock(content='{"name": "test", "value": 42}'))
           ]
           mock_client.return_value.chat.completions.create = AsyncMock(
               return_value=mock_response
           )

           service = AzureOpenAILLMService()
           schema = {"name": "string", "value": "number"}

           # Act
           result = await service.generate_structured("Get data", schema)

           # Assert
           assert result == {"name": "test", "value": 42}
   ```

3. **覆蓋場景**
   - 正常生成
   - 結構化輸出
   - 錯誤處理 (API 錯誤、JSON 解析錯誤)
   - 超時處理
   - 緩存命中/未命中
   - 工廠創建

#### 驗收標準
- [ ] 測試文件創建完成
- [ ] 測試覆蓋率 > 90%
- [ ] 所有測試通過
- [ ] Mock 不依賴真實 API

---

### S34-4: 配置文件和環境變量更新 (3 pts)

**優先級**: 🟡 P1
**類型**: 配置
**影響範圍**: `backend/src/core/config.py`, `.env.example`

#### 任務清單

1. **更新 config.py**
   ```python
   # 在 Settings 類中添加

   # LLM Configuration
   LLM_PROVIDER: str = "azure_openai"
   LLM_CACHE_ENABLED: bool = True
   LLM_CACHE_TTL_SECONDS: int = 3600
   LLM_MAX_RETRIES: int = 3
   LLM_TIMEOUT_SECONDS: float = 30.0

   # Azure OpenAI (已有，確認存在)
   AZURE_OPENAI_ENDPOINT: str = ""
   AZURE_OPENAI_API_KEY: str = ""
   AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o"
   AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
   ```

2. **更新 .env.example**
   ```bash
   # LLM Configuration
   LLM_PROVIDER=azure_openai
   LLM_CACHE_ENABLED=true
   LLM_CACHE_TTL_SECONDS=3600
   LLM_MAX_RETRIES=3
   LLM_TIMEOUT_SECONDS=30.0

   # Azure OpenAI
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

3. **添加配置驗證**
   - 啟動時驗證必要配置
   - 缺失配置時提供清晰錯誤信息

#### 驗收標準
- [ ] config.py 更新完成
- [ ] .env.example 更新完成
- [ ] 配置驗證邏輯正確
- [ ] 文檔說明完整

---

## 驗證命令

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/llm/protocol.py
python -m py_compile src/integrations/llm/azure_openai.py
python -m py_compile src/integrations/llm/factory.py

# 2. 運行單元測試
pytest tests/unit/integrations/llm/ -v

# 3. 測試真實 Azure OpenAI 連接 (需要有效配置)
python -c "
import asyncio
from src.integrations.llm import LLMServiceFactory

async def test():
    service = LLMServiceFactory.create()
    result = await service.generate('Say hello')
    print(f'Response: {result}')

asyncio.run(test())
"

# 4. 類型檢查
mypy src/integrations/llm/
```

---

## 完成定義

- [ ] 所有 S34 Story 完成
- [ ] LLMServiceProtocol 定義完成
- [ ] AzureOpenAILLMService 實現完成
- [ ] MockLLMService 測試實現完成
- [ ] LLMServiceFactory 工廠完成
- [ ] CachedLLMService 緩存層完成
- [ ] 測試覆蓋率 > 90%
- [ ] 配置文件更新完成
- [ ] 文檔更新完成

---

**創建日期**: 2025-12-21
