# Microsoft Agent Framework - 完整功能列表

> **更新日期**: 2025-12-06
> **IPA Platform 狀態**: MVP Complete (Phase 1-2), Phase 3 進行中

## 狀態說明

| 標記 | 說明 |
|------|------|
| ✅ | 已實現 - 功能已完成並通過測試 |
| 🔄 | 進行中 - Sprint 19 待整合官方 API |
| 📋 | 已規劃 - 在規劃文件中但尚未實現 |
| ⏳ | 未規劃 - 未在當前版本範圍內 |
| 🔗 | 使用官方 API - 直接調用 agent-framework 套件 |

---

## 1. 核心 Agent 功能

### 1.1 ChatAgent / ChatClientAgent ✅🔗
主要的 Agent 抽象類別，用於建立基於 LLM 的智能代理。支援工具調用、上下文管理、串流回應等功能。
> **IPA 實現**: `backend/src/domain/agents/service.py`

### 1.2 Multi-Turn Conversations (多輪對話) ✅
透過 AgentThread 管理對話狀態，支援跨多次互動保持上下文。不同的後端服務（Azure AI、OpenAI）使用統一的介面抽象。
> **IPA 實現**: `backend/src/domain/orchestration/multiturn/`

### 1.3 Streaming Responses (串流回應) 📋
支援即時串流輸出，透過 `run_stream()` 或 `run_streaming()` 方法逐步接收回應內容。
> **IPA 狀態**: 未實現，規劃中

### 1.4 Agent as Tool (Agent 作為工具) 📋
將 Agent 轉換為可調用的工具，支援階層式 Agent 架構。透過 `as_tool()` 方法實現 Agent 間的嵌套調用。
> **IPA 狀態**: 未實現

### 1.5 Agent as MCP Server ⏳
透過 `as_mcp_server()` 方法將 Agent 公開為 MCP 伺服器，讓其他 MCP 相容的客戶端可以調用。
> **IPA 狀態**: 未規劃

### 1.6 Custom Agents (自訂 Agent) ✅
透過繼承 `AIAgent` 基類或實作 `AgentProtocol` 協議，建立完全自訂行為的 Agent。
> **IPA 實現**: `backend/src/domain/agents/schemas.py`

---

## 2. 工具整合 (Tools Integration)

### 2.1 Function Tools (函數工具) ✅
使用帶有類型註解的 Python 函數或 .NET 方法作為工具，框架自動處理 schema 生成和調用。
> **IPA 實現**: `backend/src/domain/agents/tools/`

### 2.2 MCP Tools - MCPStdioTool ⏳
透過標準輸入/輸出連接本地 MCP 伺服器進程，支援本地工具整合。
> **IPA 狀態**: 未規劃

### 2.3 MCP Tools - MCPStreamableHTTPTool ⏳
透過 HTTP 和 Server-Sent Events (SSE) 連接遠端 MCP 伺服器。
> **IPA 狀態**: 未規劃

### 2.4 MCP Tools - MCPWebsocketTool ⏳
透過 WebSocket 連接 MCP 伺服器，支援雙向即時通訊。
> **IPA 狀態**: 未規劃

### 2.5 HostedMCPTool ⏳
連接 Azure 託管的 MCP 伺服器，如 Microsoft Learn MCP API。
> **IPA 狀態**: 未規劃 (需要 Azure 依賴)

### 2.6 HostedCodeInterpreterTool ⏳
Azure AI 託管的程式碼執行工具，允許 Agent 執行 Python 程式碼進行數據分析。
> **IPA 狀態**: 未規劃 (需要 Azure 依賴)

### 2.7 HostedFileSearchTool ⏳
Azure AI 託管的文件搜尋工具，支援向量儲存庫的語義搜尋。
> **IPA 狀態**: 未規劃 (需要 Azure 依賴)

### 2.8 HostedWebSearchTool ⏳
託管的網頁搜尋工具，提供即時網路資訊檢索能力。
> **IPA 狀態**: 未規劃

### 2.9 Bing Grounding Tool ⏳
透過 Bing 搜尋 API 提供即時網路資訊，用於 Agent 回應的事實根據。
> **IPA 狀態**: 未規劃 (需要 Azure 依賴)

### 2.10 Azure AI Search Integration ⏳
整合 Azure AI Search 進行企業級搜尋，支援向量搜尋和全文搜尋。
> **IPA 狀態**: 未規劃 (需要 Azure 依賴)

### 2.11 OpenAPI Tools 📋
任何具有 OpenAPI 規範的 REST API 都可以自動匯入為可調用的工具。
> **IPA 狀態**: 規劃中 - 可透過 Connectors 實現

---

## 3. Workflow 工作流程

### 3.1 Graph-based Workflows (圖形化工作流程) ✅
使用有向圖連接多個執行器（Executors）和邊緣（Edges），定義複雜的多步驟任務流程。
> **IPA 實現**: `backend/src/integrations/agent_framework/workflow.py`

### 3.2 Executors (執行器) ✅
工作流程的基本處理單元，可以是 Agent、函數或子工作流程。支援類型安全的輸入/輸出。
> **IPA 實現**: `backend/src/domain/workflows/executors/`

### 3.3 AgentExecutor ✅
將 ChatAgent 包裝為工作流程執行器，支援輸入/輸出轉換。
> **IPA 實現**: `backend/src/domain/workflows/executors/`

### 3.4 FunctionExecutor ✅
將普通函數包裝為工作流程執行器。
> **IPA 實現**: `backend/src/domain/workflows/executors/`

### 3.5 Edges (邊緣) ✅
定義執行器之間的數據流動，支援條件路由。
> **IPA 實現**: `backend/src/integrations/agent_framework/builders/edge_routing.py`

### 3.6 Type-based Routing (類型路由) ✅
基於消息類型自動路由到相應的執行器，確保類型安全。
> **IPA 實現**: `backend/src/integrations/agent_framework/builders/edge_routing.py`

### 3.7 Workflow Nesting (工作流程嵌套) ✅🔄
工作流程可以嵌套組合，建立更複雜的處理邏輯。
> **IPA 實現**: `backend/src/domain/orchestration/nested/`
> **Sprint 19**: 需整合官方 `WorkflowExecutor` API

### 3.8 Workflow as Agent 📋
透過 `as_agent()` 方法將工作流程包裝為 Agent，使用統一的調用介面。
> **IPA 狀態**: 未實現

### 3.9 Checkpointing (檢查點) ✅
保存工作流程狀態，支援長時間運行進程的恢復和重啟。包含 InMemoryCheckpointStore 和 CosmosCheckpointStore。
> **IPA 實現**: `backend/src/domain/checkpoints/`, `backend/src/integrations/agent_framework/checkpoint.py`

### 3.10 Human-in-the-Loop (人機協作) ✅
透過 RequestResponseExecutor 暫停工作流程等待人工審核或輸入。
> **IPA 實現**: `backend/src/domain/workflows/executors/approval.py`, `backend/src/integrations/agent_framework/builders/handoff_hitl.py`

### 3.11 Time-Travel (時間旅行) 📋
回溯到之前的檢查點狀態，用於調試和錯誤恢復。
> **IPA 狀態**: 規劃中

### 3.12 Workflow Context (工作流程上下文) ✅
執行器之間共享狀態的機制，支援跨步驟數據傳遞。
> **IPA 實現**: `backend/src/domain/orchestration/nested/context_propagation.py`

---

## 4. 多 Agent 編排模式 (Orchestration Patterns)

### 4.1 Sequential Orchestration (順序編排) ✅
Agent 按順序執行，每個階段建立在前一階段的輸出之上。
> **IPA 實現**: `backend/src/domain/workflows/service.py`

### 4.2 Concurrent Orchestration (並行編排) ✅🔄
多個 Agent 同時執行（Fan-out），結果由聚合器合併（Fan-in）。
> **IPA 實現**: `backend/src/domain/workflows/executors/concurrent.py`
> **Sprint 19**: 需整合官方 `ConcurrentBuilder` API
> **Builder**: `backend/src/integrations/agent_framework/builders/concurrent.py`

### 4.3 Handoff Orchestration (移交編排) ✅🔄
根據輸入將任務路由到專門的 Agent，支援智能任務分配。
> **IPA 實現**: `backend/src/domain/orchestration/handoff/`
> **Sprint 19**: 需整合官方 `HandoffBuilder` API
> **Builder**: `backend/src/integrations/agent_framework/builders/handoff.py`

### 4.4 Group Chat Orchestration (群聊編排) ✅🔄
多個 Agent 在共享對話中協作，由管理者協調發言順序。
> **IPA 實現**: `backend/src/domain/orchestration/groupchat/`
> **Sprint 19**: 需整合官方 `GroupChatBuilder` API
> **Builder**: `backend/src/integrations/agent_framework/builders/groupchat.py`

### 4.5 Magentic Orchestration (Magentic 編排) ✅🔄
基於 Magentic-One 系統的複雜多 Agent 協作模式，由 Magentic 管理者動態規劃和協調專業 Agent。
> **IPA 實現**: `backend/src/domain/orchestration/planning/`
> **Sprint 19**: 需整合官方 `MagenticBuilder` API
> **Builder**: `backend/src/integrations/agent_framework/builders/magentic.py`

### 4.6 Reflection Orchestration (反思編排) 📋
透過 Actor-Critic 模式實現自我改進，Agent 可以反覆精煉輸出。
> **IPA 狀態**: 未實現

---

## 5. Agent 記憶體與上下文 (Memory & Context)

### 5.1 AgentThread (Agent 執行緒) ✅
狀態管理機制，跨多次調用保持對話歷史和上下文。支援序列化以持久化儲存。
> **IPA 實現**: `backend/src/domain/orchestration/multiturn/session_manager.py`

### 5.2 Context Providers (上下文提供者) ✅
動態注入額外上下文到 Agent，支援 `invoking` 和 `invoked` 兩個擴展點。
> **IPA 實現**: `backend/src/domain/orchestration/multiturn/context_manager.py`

### 5.3 Chat Message Store (聊天訊息儲存) ✅
可替換的聊天歷史儲存機制，支援自訂後端（如 Cosmos DB）。
> **IPA 實現**: `backend/src/domain/orchestration/memory/`

### 5.4 InMemoryChatMessageStore ✅
內建的記憶體聊天歷史儲存，支援聊天歷史縮減器控制上下文大小。
> **IPA 實現**: `backend/src/domain/orchestration/memory/in_memory.py`

### 5.5 Mem0 Integration (Mem0 整合) ⏳
整合 Mem0 服務實現跨執行緒的長期記憶，支援使用者偏好記憶。
> **IPA 狀態**: 未規劃

### 5.6 Whiteboard Memory (白板記憶) 📋
從對話中捕獲最相關的資訊，即使聊天歷史被截斷也能保持關鍵上下文。
> **IPA 狀態**: 規劃中

---

## 6. Middleware (中介軟體)

### 6.1 Agent Middleware 📋
攔截 Agent 請求/回應的處理管道，支援自訂邏輯注入。
> **IPA 狀態**: 規劃中

### 6.2 Function Middleware 📋
攔截工具/函數調用的中介軟體。
> **IPA 狀態**: 規劃中

### 6.3 Chat Middleware 📋
攔截聊天客戶端層級的請求/回應。
> **IPA 狀態**: 規劃中

### 6.4 常見中介軟體用例
- 認證驗證 ✅ (`backend/src/api/v1/` 各模組的認證)
- 日誌記錄 ✅ (`backend/src/domain/audit/logger.py`)
- 速率限制 📋
- 內容過濾 📋
- 快取 ✅ (`backend/src/infrastructure/cache/llm_cache.py`)
- 異常處理 ✅ (`backend/src/integrations/agent_framework/exceptions.py`)

---

## 7. 模型客戶端 (Model Clients)

### 7.1 OpenAIChatClient ✅🔗
連接 OpenAI API 或相容的本地模型（如透過 Ollama、vLLM）。
> **IPA 實現**: 透過 agent-framework 套件使用

### 7.2 AzureAIAgentClient 📋
連接 Azure AI Foundry 服務，支援託管 Agent 功能。
> **IPA 狀態**: 規劃中 (可選的 Azure 整合)

### 7.3 AzureOpenAIResponsesClient / AzureOpenAIChatClient ✅🔗
連接 Azure OpenAI 服務。
> **IPA 實現**: 透過 agent-framework 套件使用，配置在 `backend/src/core/config.py`

### 7.4 GitHub Models 📋
透過 GitHub Models 服務使用各種 LLM 模型。
> **IPA 狀態**: 規劃中

### 7.5 多模型支援 ✅
支援多種 LLM 提供者，透過統一的 IChatClient 介面抽象。
> **IPA 實現**: 透過配置切換不同模型端點

---

## 8. 可觀測性 (Observability)

### 8.1 OpenTelemetry Integration ✅
內建 OpenTelemetry 整合，遵循 GenAI Semantic Conventions 標準。
> **IPA 實現**: `backend/requirements.txt` 包含 opentelemetry 套件

### 8.2 Distributed Tracing (分散式追蹤) ✅
追蹤 Agent 操作、工具調用和多 Agent 工作流程。
> **IPA 實現**: `backend/src/domain/devtools/tracer.py`

### 8.3 Metrics (指標) ✅
Agent 效能和使用量指標收集。
> **IPA 實現**: `backend/src/core/performance/`

### 8.4 Logging (日誌) ✅
結構化日誌輸出，支援各種日誌後端。
> **IPA 實現**: 使用 structlog，`backend/src/domain/audit/logger.py`

### 8.5 Azure Monitor Integration ⏳
匯出遙測數據到 Azure Application Insights。
> **IPA 狀態**: 未規劃 (需要 Azure 依賴)

### 8.6 Aspire Dashboard Support ⏳
支援 .NET Aspire Dashboard 進行本地開發調試。
> **IPA 狀態**: 不適用 (IPA 使用 Python)

---

## 9. Agent 互操作性 (Interoperability)

### 9.1 A2A Protocol (Agent-to-Agent 協議) ✅
Agent 間通訊的標準協議，支援跨運行時環境的 Agent 協作。
> **IPA 實現**: `backend/src/domain/orchestration/collaboration/protocol.py`

### 9.2 AG-UI Protocol ⏳
Agent 與 UI 之間的通訊協議，支援串流回應和互動式對話。
> **IPA 狀態**: 未規劃

### 9.3 MCP (Model Context Protocol) ⏳
開放標準協議，定義 Agent 如何與外部工具和服務互動。
> **IPA 狀態**: 未規劃

### 9.4 OpenAPI Integration ✅
自動從 OpenAPI 規範生成工具定義。
> **IPA 實現**: 透過 Connectors (`backend/src/domain/connectors/`)

---

## 10. 開發者工具 (Developer Tools)

### 10.1 DevUI ⏳
互動式開發者 UI，用於 Agent 開發、測試和工作流程調試。
> **IPA 狀態**: 未規劃

### 10.2 AF Labs ⏳
實驗性功能套件，包含基準測試、強化學習和研究計畫。
> **IPA 狀態**: 未規劃

### 10.3 Declarative Agent Definitions 📋
透過 YAML 或 JSON 配置定義 Agent，支援版本控制。
> **IPA 狀態**: 規劃中 - 透過 Templates 功能

### 10.4 VS Code AI Toolkit Extension ⏳
Visual Studio Code 擴展整合，提供開發時支援。
> **IPA 狀態**: 不適用 (外部工具)

---

## 11. 部署與整合 (Deployment & Integration)

### 11.1 ASP.NET Core Integration ⏳
與 .NET 託管模式無縫整合，支援 REST API 部署。
> **IPA 狀態**: 不適用 (IPA 使用 Python)

### 11.2 FastAPI Integration (Python) ✅
FastAPI 整合支援 Agent 的 HTTP 服務部署。
> **IPA 實現**: `backend/main.py`, `backend/src/api/`

### 11.3 Azure Container Apps ✅
容器化部署到 Azure Container Apps。
> **IPA 實現**: `docker-compose.yaml`, `Dockerfile`

### 11.4 Azure AI Foundry ⏳
深度整合 Azure AI Foundry 服務，包含可觀測性、持久性和合規性。
> **IPA 狀態**: 未規劃 (可選)

### 11.5 CI/CD Compatibility ✅
支援 GitHub Actions 和 Azure DevOps 的 CI/CD 流程。
> **IPA 實現**: `.github/workflows/` (規劃中)

---

## 12. 安全性與企業功能 (Security & Enterprise)

### 12.1 Azure Identity Integration ✅
支援 Azure CLI、Managed Identity 等多種認證方式。
> **IPA 實現**: `backend/requirements.txt` 包含 azure-identity

### 12.2 Role-based Access Control 📋
透過 Azure RBAC 控制資源存取。
> **IPA 狀態**: 規劃中

### 12.3 Entra ID Security 📋
Azure Entra ID（前 Azure AD）安全認證。
> **IPA 狀態**: 規劃中

### 12.4 Content Safety 📋
內容安全過濾和審核功能。
> **IPA 狀態**: 規劃中

---

## 13. 訊息與內容類型 (Messages & Content)

### 13.1 ChatMessage ✅🔗
統一的訊息類型，支援多種內容類型。
> **IPA 實現**: 透過 agent-framework 套件使用

### 13.2 TextContent ✅🔗
純文字內容。
> **IPA 實現**: 透過 agent-framework 套件使用

### 13.3 UriContent / ImageContent 📋
圖片和 URI 內容，支援多模態輸入。
> **IPA 狀態**: 規劃中

### 13.4 ToolCallContent ✅🔗
工具調用請求和結果。
> **IPA 實現**: 透過 agent-framework 套件使用

### 13.5 Annotations 📋
回應中的註解，如來源引用、連結等。
> **IPA 狀態**: 規劃中

---

## 14. 錯誤處理 (Error Handling)

### 14.1 AgentError ✅
Agent 層級的錯誤類型。
> **IPA 實現**: `backend/src/integrations/agent_framework/exceptions.py`

### 14.2 ToolExecutionError ✅
工具執行失敗的錯誤類型。
> **IPA 實現**: `backend/src/integrations/agent_framework/exceptions.py`

### 14.3 WorkflowError / ExecutorError ✅
工作流程和執行器層級的錯誤類型。
> **IPA 實現**: `backend/src/integrations/agent_framework/exceptions.py`

---

## 15. 遷移支援 (Migration Support)

### 15.1 Semantic Kernel Migration Guide ⏳
從 Semantic Kernel 遷移的官方指南。
> **IPA 狀態**: 不適用 (新項目)

### 15.2 AutoGen Migration Guide ⏳
從 AutoGen 遷移的官方指南。
> **IPA 狀態**: 不適用 (新項目)

---

## 16. 語言支援 (Language Support)

### 16.1 Python ✅
完整的 Python 實作，透過 `pip install agent-framework --pre` 安裝。
> **IPA 實現**: 使用 Python 作為主要語言

### 16.2 .NET (C#) ⏳
完整的 .NET 實作，透過 NuGet 套件 `Microsoft.Agents.AI` 安裝。
> **IPA 狀態**: 未使用

### 16.3 TypeScript/JavaScript ⏳
Azure AI Agents 客戶端程式庫支援。
> **IPA 狀態**: 前端使用 TypeScript

---

## 17. 套件結構 (Package Structure)

### Python 套件
- `agent-framework` (主套件) ✅ 已安裝 v1.0.0b251204
- `agent-framework-core` ✅ 已安裝
- `agent-framework-openai` 📋 可選
- `agent-framework-azure` 📋 可選
- `agent-framework-workflows` 📋 可選
- `agent-framework-ag-ui` ⏳ 未使用
- `agent-framework-devui` ⏳ 未使用
- `agent-framework-lab` ⏳ 未使用

### .NET 套件
- `Microsoft.Agents.AI` ⏳ 不適用
- `Microsoft.Agents.AI.OpenAI` ⏳ 不適用
- `Microsoft.Agents.AI.AzureAI` ⏳ 不適用
- `Microsoft.Agents.Workflows` ⏳ 不適用

---

## 統計摘要

| 類別 | 總數 | ✅ 已實現 | 🔄 進行中 | 📋 已規劃 | ⏳ 未規劃 |
|------|------|----------|----------|----------|----------|
| 1. 核心 Agent | 6 | 3 | 0 | 2 | 1 |
| 2. 工具整合 | 11 | 2 | 0 | 1 | 8 |
| 3. Workflow | 12 | 10 | 1 | 1 | 0 |
| 4. 編排模式 | 6 | 4 | 4 | 1 | 0 |
| 5. 記憶體 | 6 | 4 | 0 | 1 | 1 |
| 6. Middleware | 4+ | 3 | 0 | 3 | 0 |
| 7. 模型客戶端 | 5 | 3 | 0 | 2 | 0 |
| 8. 可觀測性 | 6 | 4 | 0 | 0 | 2 |
| 9. 互操作性 | 4 | 2 | 0 | 0 | 2 |
| 10. 開發工具 | 4 | 0 | 0 | 1 | 3 |
| 11. 部署整合 | 5 | 3 | 0 | 0 | 2 |
| 12. 安全企業 | 4 | 1 | 0 | 3 | 0 |
| 13. 訊息類型 | 5 | 3 | 0 | 2 | 0 |
| 14. 錯誤處理 | 3 | 3 | 0 | 0 | 0 |
| **總計** | **~85** | **~45 (53%)** | **5 (6%)** | **~17 (20%)** | **~18 (21%)** |

---

## Sprint 19 待整合項目

以下 5 個 Builder 需要整合官方 Microsoft Agent Framework API：

| Builder | 文件位置 | 狀態 |
|---------|---------|------|
| ConcurrentBuilder | `builders/concurrent.py` | 🔄 待整合 |
| HandoffBuilder | `builders/handoff.py` | 🔄 待整合 |
| GroupChatBuilder | `builders/groupchat.py` | 🔄 待整合 |
| MagenticBuilder | `builders/magentic.py` | 🔄 待整合 |
| WorkflowExecutor | `builders/workflow_executor.py` | 🔄 待整合 |

整合完成後執行驗證：
```bash
cd backend && python scripts/verify_official_api_usage.py
# 預期: 5/5 checks passed
```
