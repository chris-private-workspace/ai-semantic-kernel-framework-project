# Phase 8: Azure Code Interpreter 整合

**Phase 目標**: 將 Azure OpenAI Code Interpreter 功能整合到 IPA Platform，實現 Agent 程式碼執行能力

**開始日期**: 2025-12-21
**預計完成日期**: TBD
**總點數**: 35 Story Points

---

## 背景

### Azure Code Interpreter 簡介

Azure OpenAI Assistants API 提供 Code Interpreter 工具，允許 AI Agent 執行 Python 程式碼並返回結果。這為 IPA Platform 提供了以下能力：

| 能力 | 描述 | 應用場景 |
|------|------|---------|
| 動態程式碼執行 | Agent 可以編寫並執行 Python 代碼 | 數據分析、計算任務 |
| 文件處理 | 可以上傳和處理文件 | CSV 分析、報表生成 |
| 數學運算 | 複雜數學計算和科學運算 | 財務計算、統計分析 |
| 可視化 | 生成圖表和圖形 | 數據可視化、報告 |

### 已驗證的 Azure 配置

```
Azure OpenAI Endpoint: https://azureopenaiservicechris.cognitiveservices.azure.com/
Deployment: gpt-5-nano
API Version: 2024-12-01-preview
AI Foundry Project: https://azureopenaiservicechris.services.ai.azure.com/api/projects/AzureOpenAIServiceChris-project
功能驗證: ✅ Chat Completion | ✅ Assistants API | ✅ Code Interpreter
```

### 核心整合點

```
┌─────────────────────────────────────────────────────────────┐
│                    IPA Platform                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              CodeInterpreterAdapter                  │    │
│  │  + execute_code(code: str) -> ExecutionResult       │    │
│  │  + run_with_files(files: List[File]) -> Result      │    │
│  │  + create_sandbox() -> Sandbox                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              AssistantManagerService                 │    │
│  │  + create_assistant(tools) -> Assistant             │    │
│  │  + create_thread() -> Thread                         │    │
│  │  + run_with_code_interpreter() -> Run               │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Azure OpenAI (Assistants API)           │    │
│  │  + beta.assistants.create(tools=["code_interpreter"])│    │
│  │  + beta.threads.runs.create()                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Sprint 概覽

### Sprint 37: Code Interpreter 基礎設施 (20 pts)
**目標**: 建立 Code Interpreter 服務層，實現基礎程式碼執行能力

| Story | 點數 | 說明 | 優先級 |
|-------|------|------|--------|
| S37-1 | 8 | AssistantManagerService 設計與實現 | 🔴 P0 |
| S37-2 | 5 | CodeInterpreterAdapter 適配器實現 | 🔴 P0 |
| S37-3 | 4 | Code Interpreter API 端點 | 🟡 P1 |
| S37-4 | 3 | 單元測試和整合測試 | 🟡 P1 |

### Sprint 38: Agent 整合與擴展 (15 pts)
**目標**: 將 Code Interpreter 整合到現有 Agent 工作流程

| Story | 點數 | 說明 | 優先級 |
|-------|------|------|--------|
| S38-1 | 5 | Agent 工具擴展 - Code Interpreter 支援 | 🔴 P0 |
| S38-2 | 5 | 文件上傳與處理功能 | 🟡 P1 |
| S38-3 | 3 | 執行結果可視化 | 🟡 P1 |
| S38-4 | 2 | 文檔更新和示例 | 🟢 P2 |

---

## 技術設計

### 架構概覽

```
backend/src/integrations/agent_framework/
├── builders/
│   └── code_interpreter.py      # CodeInterpreterAdapter (新增)
├── assistant/                    # (新增目錄)
│   ├── __init__.py
│   ├── manager.py                # AssistantManagerService
│   ├── models.py                 # 數據模型
│   └── sandbox.py                # 沙盒執行環境
└── ...

backend/src/api/v1/
├── code_interpreter/             # (新增目錄)
│   ├── __init__.py
│   ├── routes.py                 # API 路由
│   └── schemas.py                # 請求/響應 Schema
└── ...
```

### 核心類別設計

```python
# AssistantManagerService - 管理 Azure OpenAI Assistants
class AssistantManagerService:
    """Azure OpenAI Assistants 管理服務。

    負責創建和管理 Assistants，處理 Thread 和 Run 生命週期。
    """

    def __init__(self, client: AzureOpenAI):
        self._client = client

    async def create_assistant(
        self,
        name: str,
        instructions: str,
        tools: List[str] = ["code_interpreter"],
    ) -> Assistant:
        """創建帶 Code Interpreter 的 Assistant。"""
        ...

    async def execute_code(
        self,
        assistant_id: str,
        code: str,
        timeout: int = 60,
    ) -> CodeExecutionResult:
        """執行程式碼並返回結果。"""
        ...


# CodeInterpreterAdapter - 適配器模式包裝
class CodeInterpreterAdapter:
    """Code Interpreter 適配器。

    將 Azure OpenAI Code Interpreter 功能封裝為 IPA Platform 標準接口。
    """

    def __init__(self, config: CodeInterpreterConfig):
        self._manager = AssistantManagerService(...)

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """執行任務，可能涉及程式碼生成和執行。"""
        ...

    async def analyze_data(
        self,
        data: Union[str, bytes, Path],
        prompt: str,
    ) -> AnalysisResult:
        """分析數據文件。"""
        ...
```

### API 端點設計

```yaml
# POST /api/v1/code-interpreter/execute
請求:
  code: string          # 要執行的 Python 代碼
  timeout: int          # 超時時間 (秒)

響應:
  result: string        # 執行輸出
  status: string        # success | error | timeout
  execution_time: float # 執行耗時
  files: List[File]     # 生成的文件 (圖表等)

# POST /api/v1/code-interpreter/analyze
請求:
  file: File            # 上傳的文件
  prompt: string        # 分析指令

響應:
  analysis: string      # 分析結果
  visualizations: List[File]  # 生成的可視化
```

---

## 成功標準

### 技術標準
- [ ] AssistantManagerService 實現完成
- [ ] CodeInterpreterAdapter 適配器實現
- [ ] API 端點可用並通過測試
- [ ] 整合現有 LLMService (Phase 7)
- [ ] 錯誤處理和超時機制完善

### 功能標準
- [ ] 可以執行 Python 程式碼並返回結果
- [ ] 支援文件上傳和分析
- [ ] 生成的圖表可以下載
- [ ] 與現有 Agent 工作流整合

### 質量標準
- [ ] 新增測試 > 20 個
- [ ] 測試覆蓋率維持 85%+
- [ ] Code Interpreter 執行延遲 < 30 秒 (P95)
- [ ] 無回歸錯誤

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| Code Interpreter API 限制 | 中 | 高 | 實現請求排隊和速率限制 |
| 執行超時 | 中 | 中 | 設定合理超時，提供部分結果 |
| 文件大小限制 | 低 | 中 | 前端驗證，分片上傳 |
| 安全性風險 | 中 | 高 | Azure 沙盒隔離，輸入驗證 |
| 費用控制 | 中 | 中 | Token 預算管理，使用監控 |

---

## 相關文件

- [Phase 7 完成報告](../phase-7/README.md)
- [Sprint 37 詳細計劃](./sprint-37-plan.md)
- [Sprint 37 Checklist](./sprint-37-checklist.md)
- [Azure OpenAI 連接測試腳本](../../../../scripts/test_azure_ai_agent_service.py)

---

## 依賴項

### 前置條件
- ✅ Phase 7 完成 (LLM 服務基礎設施)
- ✅ Azure OpenAI 配置驗證通過
- ✅ Assistants API 可用性確認
- ✅ Code Interpreter 功能測試通過

### 外部依賴
- Azure OpenAI API (Assistants API + Code Interpreter)
- openai Python SDK >= 1.0.0

---

## 全項目總結 (Phase 8 後)

| Phase | Sprint 範圍 | 點數 | 狀態 |
|-------|-------------|------|------|
| Phase 1 | Sprint 0-6 | 285 pts | ✅ 完成 |
| Phase 2 | Sprint 7-12 | 222 pts | ✅ 完成 |
| Phase 3 | Sprint 13-19 | 242 pts | ✅ 完成 |
| Phase 4 | Sprint 20-25 | 180 pts | ✅ 完成 |
| Phase 5 | Sprint 26-30 | 183 pts | ✅ 完成 |
| Phase 6 | Sprint 31-33 | 78 pts | ✅ 完成 |
| Phase 7 | Sprint 34-36 | 58 pts | ⏳ 進行中 |
| **Phase 8** | **Sprint 37-38** | **35 pts** | 📋 計劃中 |
| **總計** | **38 Sprints** | **1283 pts** | - |

---

**創建日期**: 2025-12-21
**上次更新**: 2025-12-21
