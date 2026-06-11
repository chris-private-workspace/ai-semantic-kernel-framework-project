# Sprint 1 Critical 問題解決記錄

**創建日期**: 2025-11-21
**狀態**: ✅ 全部解決

## 問題總覽

在準備 S1-1 開發環境時,發現了 6 個 Critical (P0) 問題,全部已成功解決。

## 已解決問題

### 1. ✅ 數據庫 Migrations 缺失 (P0)

**問題描述**:
- `migrations/versions/` 目錄為空
- 數據庫中除了 `users` 和 `test_persistence` 表外,沒有其他表
- S1-1 開發需要 `workflows`, `workflow_versions`, `executions` 等表

**解決方案**:
1. **更新 `migrations/env.py`**: 添加所有 model imports 和 metadata 配置
2. **修復 SQLAlchemy 保留字沖突**:
   - `workflow.py`: 將 `metadata` 改為 `workflow_metadata = Column(JSONB, default=dict, name="metadata")`
   - `execution.py`: 將 `metadata` 改為 `execution_metadata = Column(JSONB, default=dict, name="metadata")`
3. **修復 circular dependency**: 手動編輯 migration 使用 3-step 建表順序
   - Step 1: 創建 `workflows` 表(不含 `current_version_id` FK)
   - Step 2: 創建 `workflow_versions` 表
   - Step 3: 添加 `workflows.current_version_id` FK

**結果**:
- ✅ 成功創建 10 個數據庫表
- ✅ 所有外鍵約束正確
- ✅ Migration 版本: `f4f52097a3de`

**涉及文件**:
- `backend/migrations/env.py`
- `backend/src/infrastructure/database/models/workflow.py`
- `backend/src/infrastructure/database/models/execution.py`
- `backend/migrations/versions/f4f52097a3de_initial_schema_users_workflows_agents_.py`

---

### 2. ✅ Backend API 無法啟動 - Auth Router 導入錯誤 (P0)

**問題描述**:
```
ImportError: cannot import name 'router' from 'src.api.v1.auth'
```

**根本原因**: `src/api/v1/auth/__init__.py` 文件為空,未導出 router

**解決方案**:
創建 `src/api/v1/auth/__init__.py`:
```python
from src.api.v1.auth.routes import router
__all__ = ["router"]
```

**涉及文件**:
- `backend/src/api/v1/auth/__init__.py`

---

### 3. ✅ Settings 配置解析錯誤 - ALLOWED_HOSTS (P0)

**問題描述**:
```
pydantic_settings.sources.SettingsError: error parsing value for field "allowed_hosts"
```

**根本原因**: `.env` 文件中 `ALLOWED_HOSTS=*` 是字符串,但 Settings 定義為 `list[str]`

**解決方案**:
更新 `.env` 文件:
```bash
ALLOWED_HOSTS=["*"]
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]
```

**涉及文件**:
- `backend/.env`

---

### 4. ✅ Settings 驗證錯誤 - OPENAI_API_KEY 欄位不存在 (P0)

**問題描述**:
```
ValidationError: Extra inputs are not permitted [type=extra_forbidden, input_value='your-openai-api-key-here']
```

**根本原因**: `config.py` 中只有 Azure OpenAI 配置,沒有標準 OpenAI API Key 欄位

**解決方案**:
在 `src/core/config.py` 中添加:
```python
# OpenAI API (for Agent Framework)
openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
```

**涉及文件**:
- `backend/src/core/config.py` (line 78-79)

---

### 5. ✅ Database Session 模塊缺失 (P0)

**問題描述**:
```
ModuleNotFoundError: No module named 'src.infrastructure.database.session'
```

**根本原因**: `src/infrastructure/database/session.py` 文件不存在

**解決方案**:
創建 `session.py` 提供 async database session 管理:
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.db_echo,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**涉及文件**:
- `backend/src/infrastructure/database/session.py` (新建)

---

### 6. ✅ Redis Cache 模塊缺失 (P0)

**問題描述**:
```
ModuleNotFoundError: No module named 'src.infrastructure.cache.redis_cache'
```

**根本原因**:
- `auth_service.py` 導入 `RedisCache`
- 但實際類名是 `CacheService` (在 `cache_service.py` 中)

**解決方案**:
創建 `redis_cache.py` 作為兼容層:
```python
from .cache_service import CacheService as RedisCache

def get_cache() -> RedisCache:
    return RedisCache()
```

**涉及文件**:
- `backend/src/infrastructure/cache/redis_cache.py` (新建)

---

### 7. ✅ Email Validator 依賴缺失 (P0)

**問題描述**:
```
ImportError: email-validator is not installed, run `pip install pydantic[email]`
```

**根本原因**: Pydantic `EmailStr` 類型需要 `email-validator` 包

**解決方案**:
```bash
docker exec ipa-backend pip install "pydantic[email]"
```

**結果**: 成功安裝 `email-validator==2.3.0`

---

## 環境驗證結果

所有問題解決後,成功驗證:

### ✅ Backend API 運行正常
```bash
$ docker logs ipa-backend | grep "Application startup"
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### ✅ Root Endpoint 正常
```json
{
  "service": "IPA Platform API",
  "version": "0.1.1",
  "status": "running"
}
```

### ✅ Health Endpoint 正常
```json
{
  "status": "healthy",
  "timestamp": "2025-11-21T04:25:45.275544",
  "service": "AI Semantic Kernel Framework",
  "version": "0.1.0",
  "environment": "development"
}
```

### ✅ OpenAPI Docs 可訪問
- URL: http://localhost:8000/docs
- Status: 200 OK

### ✅ Database Tables 完整
10 個表已創建:
- `users`
- `workflows`
- `workflow_versions`
- `agents`
- `agent_tools`
- `executions`
- `execution_steps`
- `execution_logs`
- `audit_logs`
- `alembic_version`

---

## 技術決策記錄

### 1. Circular Dependency 解決模式
使用 3-step migration pattern:
1. 創建父表(不含循環FK)
2. 創建子表(含FK到父表)
3. 添加父表的循環FK(使用 `op.create_foreign_key()`)

**優點**:
- 避免 Alembic 自動排序錯誤
- 明確控制建表順序
- 可維護性高

### 2. SQLAlchemy Reserved Word 處理
使用 `Column(name="metadata")` 保持數據庫列名不變,但 Python 屬性名改為描述性名稱

**優點**:
- 數據庫 schema 不變
- Python 代碼更清晰
- 避免與 SQLAlchemy 內部屬性沖突

### 3. Async Database Session 管理
使用 `AsyncSession` + `async_sessionmaker` + `NullPool`

**優點**:
- 完整的 async/await 支持
- 自動 commit/rollback 處理
- 適合 FastAPI async endpoints

### 4. Redis Cache 兼容層
創建 `redis_cache.py` 重新導出 `CacheService`

**優點**:
- 保持現有代碼導入路徑不變
- 未來可以輕鬆切換實現
- 符合依賴倒置原則

---

## 後續建議

### 1. 更新 requirements.txt
將 `email-validator` 添加到依賴列表:
```
pydantic[email]>=2.5.0
```

### 2. 更新 README.md
文檔化環境變數要求:
- `OPENAI_API_KEY`: Required for S1-6 Agent Service
- List 類型環境變數使用 JSON 格式

### 3. 添加 Migration 測試
創建測試確保:
- Circular dependency 正確處理
- Foreign key 約束有效
- Rollback 功能正常

### 4. 配置 Pre-commit Hook
自動檢查:
- SQLAlchemy reserved words
- Pydantic field 定義完整性
- 必要依賴已安裝

---

## 經驗教訓

### 1. 系統性問題排查
發現問題 → 修復 → 重新啟動 → 下一個問題
- **學習**: 應該先完整審查所有依賴再啟動
- **改進**: 創建環境檢查腳本 `scripts/check_env.py`

### 2. Docker 環境配置
容器內 `localhost` vs Docker 網絡主機名
- **學習**: .env 文件需要適配 Docker 環境
- **改進**: 提供 `.env.docker` 示例

### 3. Pydantic 配置管理
List 類型欄位需要 JSON 格式字符串
- **學習**: Pydantic Settings 對類型很嚴格
- **改進**: 添加配置驗證和錯誤提示

---

## 下一步

✅ **所有 Critical 問題已解決**
✅ **開發環境完全就緒**
🚀 **準備開始 S1-1: Workflow Service - Core CRUD 開發**

---

**最後更新**: 2025-11-21 12:25 (UTC+8)
**負責人**: Claude Code
**狀態**: ✅ Completed
