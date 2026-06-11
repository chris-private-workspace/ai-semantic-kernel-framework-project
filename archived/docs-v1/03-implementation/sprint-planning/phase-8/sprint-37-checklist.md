# Sprint 37 Checklist: Code Interpreter 基礎設施

**Sprint 目標**: 建立 Code Interpreter 服務層，實現基礎程式碼執行能力
**總點數**: 20 Story Points
**狀態**: 📋 計劃中
**開始日期**: TBD

---

## 前置條件檢查

### Azure 配置驗證
- [ ] Azure OpenAI 端點可訪問
- [ ] API 金鑰有效
- [ ] 模型部署 (gpt-5-nano) 可用
- [ ] Assistants API 功能已啟用
- [ ] Code Interpreter 工具可用

### 驗證命令
```bash
# 執行連接測試腳本
python scripts/test_azure_ai_agent_service.py

# 預期輸出:
# [OK] Chat completion successful!
# [OK] Found X existing assistant(s)
# [OK] Assistant created
# [OK] Code Interpreter test passed
```

---

## Story Checklist

### S37-1: AssistantManagerService 設計與實現 (8 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 確認 Azure OpenAI 配置
- [ ] 確認 openai SDK 版本 >= 1.0.0
- [ ] 設計服務接口

#### 實現任務
- [ ] 創建目錄 `backend/src/integrations/agent_framework/assistant/`
- [ ] 創建 `__init__.py`
- [ ] 創建 `models.py` - 數據模型
  - [ ] `CodeExecutionResult` 類
  - [ ] `AssistantConfig` 類
  - [ ] 類型註解完整
- [ ] 創建 `exceptions.py` - 自定義異常
  - [ ] `AssistantError` 基類
  - [ ] `ExecutionTimeoutError`
  - [ ] `AssistantNotFoundError`
- [ ] 創建 `manager.py` - AssistantManagerService
  - [ ] 構造函數支援配置注入
  - [ ] `create_assistant()` 實現
  - [ ] `execute_code()` 實現
  - [ ] `delete_assistant()` 實現
  - [ ] `list_assistants()` 實現
  - [ ] 超時處理邏輯
  - [ ] 錯誤處理和日誌

#### 驗證
- [ ] 語法檢查通過 `python -m py_compile`
- [ ] 類型檢查通過 `mypy`
- [ ] 代碼風格檢查 `black` + `isort`

---

### S37-2: CodeInterpreterAdapter 適配器實現 (5 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S37-1 完成
- [ ] 確認 Adapter Pattern 規範

#### 實現任務
- [ ] 創建 `builders/code_interpreter.py`
- [ ] 實現 `CodeInterpreterConfig` 配置類
- [ ] 實現 `ExecutionResult` 結果類
- [ ] 實現 `CodeInterpreterAdapter`
  - [ ] Lazy initialization
  - [ ] `execute()` 方法
  - [ ] `analyze_task()` 方法
  - [ ] `cleanup()` 方法
  - [ ] 屬性: `is_initialized`, `assistant_id`
- [ ] 更新 `builders/__init__.py` 導出

#### 驗證
- [ ] 與其他 Adapter 接口風格一致
- [ ] Lazy initialization 正常工作
- [ ] 資源清理正確

---

### S37-3: Code Interpreter API 端點 (4 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S37-1 和 S37-2 完成
- [ ] API 設計確認

#### 實現任務
- [ ] 創建目錄 `backend/src/api/v1/code_interpreter/`
- [ ] 創建 `__init__.py`
- [ ] 創建 `schemas.py` - Pydantic Schema
  - [ ] `ExecuteCodeRequest`
  - [ ] `AnalyzeTaskRequest`
  - [ ] `ExecutionResponse`
- [ ] 創建 `routes.py` - API 路由
  - [ ] `POST /execute` 端點
  - [ ] `POST /analyze` 端點
  - [ ] `GET /health` 端點
  - [ ] 錯誤處理
- [ ] 更新 `main.py` 註冊路由

#### 驗證
- [ ] API 端點可訪問
- [ ] 請求/響應格式正確
- [ ] OpenAPI 文檔顯示正確

---

### S37-4: 單元測試和整合測試 (3 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] 創建測試目錄結構

#### 實現任務
- [ ] 創建 `tests/unit/integrations/agent_framework/assistant/__init__.py`
- [ ] 創建 `test_manager.py`
  - [ ] test_create_assistant
  - [ ] test_execute_code_success
  - [ ] test_execute_code_timeout
  - [ ] test_execute_code_error
  - [ ] test_delete_assistant
- [ ] 創建 `test_code_interpreter.py`
  - [ ] test_adapter_lazy_init
  - [ ] test_execute
  - [ ] test_analyze_task
  - [ ] test_cleanup
- [ ] 創建 `tests/integration/test_code_interpreter_api.py`
  - [ ] test_execute_endpoint
  - [ ] test_analyze_endpoint
  - [ ] test_health_endpoint

#### 驗證
- [ ] 所有測試通過
- [ ] 覆蓋率 > 85%
- [ ] Mock 正確 (無真實 API 調用)

---

## 驗證命令

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/agent_framework/assistant/manager.py
python -m py_compile src/integrations/agent_framework/assistant/models.py
python -m py_compile src/integrations/agent_framework/builders/code_interpreter.py
python -m py_compile src/api/v1/code_interpreter/routes.py
# 預期: 無輸出 (無錯誤)

# 2. 類型檢查
mypy src/integrations/agent_framework/assistant/
mypy src/integrations/agent_framework/builders/code_interpreter.py
mypy src/api/v1/code_interpreter/
# 預期: Success

# 3. 代碼風格
black src/integrations/agent_framework/assistant/ --check
black src/integrations/agent_framework/builders/code_interpreter.py --check
black src/api/v1/code_interpreter/ --check
isort src/integrations/agent_framework/assistant/ --check
# 預期: All done! / Skipped

# 4. 運行單元測試
pytest tests/unit/integrations/agent_framework/assistant/ -v --cov=src/integrations/agent_framework/assistant
# 預期: 全部通過，覆蓋率 > 85%

# 5. 運行整合測試
pytest tests/integration/test_code_interpreter_api.py -v
# 預期: 全部通過

# 6. 真實 API 測試 (可選)
curl -X POST http://localhost:8000/api/v1/code-interpreter/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(sum(range(1, 101)))"}'
# 預期: {"success": true, "output": "...", ...}

curl http://localhost:8000/api/v1/code-interpreter/health
# 預期: {"status": "healthy", "service": "code-interpreter"}
```

---

## 完成定義

- [ ] 所有 S37 Story 完成
- [ ] AssistantManagerService 實現完成
- [ ] CodeInterpreterAdapter 適配器完成
- [ ] API 端點可用並測試通過
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] 代碼審查完成
- [ ] 語法/類型/風格檢查全部通過
- [ ] 文檔更新完成

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `src/integrations/agent_framework/assistant/__init__.py` | 新增 | 模組初始化 |
| `src/integrations/agent_framework/assistant/manager.py` | 新增 | AssistantManagerService |
| `src/integrations/agent_framework/assistant/models.py` | 新增 | 數據模型 |
| `src/integrations/agent_framework/assistant/exceptions.py` | 新增 | 自定義異常 |
| `src/integrations/agent_framework/builders/code_interpreter.py` | 新增 | CodeInterpreterAdapter |
| `src/api/v1/code_interpreter/__init__.py` | 新增 | API 模組初始化 |
| `src/api/v1/code_interpreter/routes.py` | 新增 | API 路由 |
| `src/api/v1/code_interpreter/schemas.py` | 新增 | Pydantic Schema |
| `tests/unit/integrations/agent_framework/assistant/` | 新增 | 單元測試 |
| `tests/integration/test_code_interpreter_api.py` | 新增 | 整合測試 |

---

## 備註

### Azure 配置參考
```bash
# backend/.env 設定
AZURE_OPENAI_ENDPOINT=https://azureopenaiservicechris.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_AI_PROJECT_ENDPOINT=https://azureopenaiservicechris.services.ai.azure.com/api/projects/AzureOpenAIServiceChris-project
```

### 相關文件
- Azure 連接測試腳本: `scripts/test_azure_ai_agent_service.py`
- Phase 7 LLM 服務: `src/integrations/llm/`
- 現有 Adapter 範例: `src/integrations/agent_framework/builders/`

---

**創建日期**: 2025-12-21
**上次更新**: 2025-12-21
