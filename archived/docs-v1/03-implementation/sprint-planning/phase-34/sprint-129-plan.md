# Sprint 129: D365 MCP Server

## 概述

Sprint 129 實現 Dynamics 365 MCP Server，讓 IPA Agent 能存取企業 ERP/CRM 系統資料，支援業務流程自動化場景。

## 目標

1. 實現 D365 MCP Server（CRUD + 查詢）
2. 支援 D365 核心實體（Accounts, Contacts, Cases, Work Orders）
3. 建立 OData 查詢建構器
4. 整合認證（Azure AD OAuth）

## Story Points: 25 點

## 前置條件

- ⬜ Sprint 128 完成
- ⬜ D365 測試環境可用
- ⬜ Azure AD App Registration 配置就緒

## 任務分解

### Story 129-1: D365 API Client (2 天, P2)

**交付物**:
- `src/integrations/mcp/servers/d365/client.py` — D365ApiClient
- OAuth 認證流程（Client Credentials）
- OData 查詢建構器

**核心能力**:

| 操作 | D365 API |
|------|----------|
| 查詢實體 | GET /api/data/v9.2/{entity}?$filter=... |
| 取得記錄 | GET /api/data/v9.2/{entity}({id}) |
| 建立記錄 | POST /api/data/v9.2/{entity} |
| 更新記錄 | PATCH /api/data/v9.2/{entity}({id}) |
| 刪除記錄 | DELETE /api/data/v9.2/{entity}({id}) |

### Story 129-2: D365 MCP Server (3 天, P2)

**MCP Tools**:

| Tool | 說明 |
|------|------|
| `query_entities` | OData 查詢（$filter, $select, $top） |
| `get_record` | 取得單筆記錄 |
| `create_record` | 建立新記錄 |
| `update_record` | 更新記錄 |
| `list_entity_types` | 列出可用實體類型 |
| `get_entity_metadata` | 取得實體 schema |

**檔案結構**:
```
src/integrations/mcp/servers/d365/
├── __init__.py
├── __main__.py
├── server.py            # D365MCPServer
├── client.py            # D365ApiClient
├── auth.py              # OAuth 認證
└── tools/
    ├── __init__.py
    ├── query.py          # 查詢 tools
    └── crud.py           # CRUD tools
```

### Story 129-3: 測試與驗證 (2 天, P2)

**測試範圍**:

| 測試 | 範圍 |
|------|------|
| `test_d365_client.py` | API client CRUD |
| `test_d365_auth.py` | OAuth 認證流程 |
| `test_d365_server.py` | MCP Server tools |
| `test_odata_builder.py` | OData 查詢建構 |

## 依賴

- 改善提案 Phase D P2: D365 MCP Server
- Azure AD OAuth 配置
