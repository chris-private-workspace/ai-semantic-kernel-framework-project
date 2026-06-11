# Phase 9: MCP Architecture & Tool Execution Layer

> **目標**: 建立統一的 MCP (Model Context Protocol) 架構，為 Agent 提供真正的執行能力

---

## Phase 概述

### 背景

IPA Platform 的 Agent 需要具備真正的「執行能力」來完成企業自動化任務：
- 查詢和管理 Azure 資源 (VM, App Services, etc.)
- 執行 PowerShell/Bash 腳本進行系統診斷
- 讀寫配置文件和日誌
- 查詢 LDAP/AD 獲取用戶信息
- SSH 連接到遠端伺服器

### 為什麼選擇 MCP?

Microsoft Agent Framework 原生支援 MCP (Model Context Protocol)，提供：
1. **標準化接口** - 統一的工具調用協議
2. **安全隔離** - 每個 MCP Server 有獨立的權限控制
3. **可重用性** - 一個 MCP Server 可被多個 Agent 共用
4. **生態系統** - 可以使用社區現有的 MCP Servers

### 架構設計

```
┌─────────────────────────────────────────────────────────────────┐
│                     IPA Platform                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐                                           │
│  │   Agent Layer    │                                           │
│  │  (LLM Reasoning) │                                           │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              MCP Client (統一接口)                        │   │
│  │  • 工具發現 (Tool Discovery)                             │   │
│  │  • 請求路由 (Request Routing)                            │   │
│  │  • 權限檢查 (Permission Check)                           │   │
│  │  • 審計日誌 (Audit Logging)                              │   │
│  └────────┬───────────────────────────────────────────────┬─┘   │
│           │                                               │      │
│           ▼                                               ▼      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │  Azure MCP     │  │  Shell MCP     │  │  Other MCP     │     │
│  │  Server        │  │  Server        │  │  Servers       │     │
│  │                │  │                │  │                │     │
│  │ • az vm        │  │ • PowerShell   │  │ • Filesystem   │     │
│  │ • az webapp    │  │ • Bash         │  │ • SSH          │     │
│  │ • az storage   │  │ • CMD          │  │ • LDAP         │     │
│  │ • az network   │  │                │  │ • Database     │     │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘     │
│          │                   │                   │               │
└──────────┼───────────────────┼───────────────────┼───────────────┘
           │                   │                   │
           ▼                   ▼                   ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │    Azure     │   │   Local/     │   │   External   │
    │   Cloud      │   │   Remote     │   │   Systems    │
    │  Resources   │   │   Systems    │   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
```

---

## Sprint 規劃

| Sprint | 名稱 | 點數 | 主要內容 |
|--------|------|------|---------|
| Sprint 39 | MCP Core Framework | 40 pts | MCP Client 架構、工具註冊、權限系統 |
| Sprint 40 | Azure MCP Server | 35 pts | Azure CLI 封裝、資源管理、監控 |
| Sprint 41 | Execution MCP Servers | 35 pts | Shell、Filesystem、SSH、LDAP |

**Phase 9 總計**: 110 Story Points

---

## 關鍵設計決策

### 1. MCP 標準遵循

遵循 [Model Context Protocol](https://modelcontextprotocol.io/) 規範：
- JSON-RPC 2.0 通訊協議
- 標準 Tool Schema 格式
- Resource 和 Prompt 支援

### 2. 安全分級

```
┌─────────────────────────────────────────────────────────────────┐
│ Level 1: 只讀操作 (自動執行)                                     │
│ ─────────────────────────────                                   │
│ • Get-AzVM, az vm list, 讀取日誌, 查詢 LDAP                     │
│ • 風險: 低                                                       │
│ • 審批: 不需要                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Level 2: 低風險寫操作 (需要 Agent 確認)                          │
│ ─────────────────────────────────────                           │
│ • 重啟服務, 清理臨時文件, 發送通知                               │
│ • 風險: 中                                                       │
│ • 審批: Agent 自行確認，記錄審計日誌                             │
├─────────────────────────────────────────────────────────────────┤
│ Level 3: 高風險操作 (需要人工審批)                               │
│ ─────────────────────────────────                               │
│ • 刪除資源, 修改安全組, 變更生產配置                             │
│ • 風險: 高                                                       │
│ • 審批: Human-in-the-loop checkpoint                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3. 審計追蹤

所有 MCP 操作都記錄：
- 時間戳
- 操作者 (Agent/User)
- 工具和參數
- 執行結果
- 風險等級

---

## 依賴關係

### 前置條件
- Phase 8 完成 (Code Interpreter)
- Azure 訂閱和服務主體配置
- 網路連接 (到 Azure、LDAP Server 等)

### 技術依賴
- `mcp` Python SDK
- `azure-cli` 或 `azure-mgmt-*` SDK
- `paramiko` (SSH)
- `ldap3` (LDAP)
- `aiofiles` (Async File IO)

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| MCP 協議複雜性 | 中 | 高 | 階段性實現，先核心後擴展 |
| Azure 權限配置 | 高 | 中 | 完整的權限文檔和測試環境 |
| 安全漏洞 | 低 | 高 | 嚴格的權限分級和審計 |
| 性能瓶頸 | 中 | 中 | 連接池、快取、異步執行 |

---

## 交付物

### 代碼產物
```
backend/src/integrations/mcp/
├── __init__.py
├── client.py              # MCP Client 核心
├── registry.py            # 工具註冊表
├── permissions.py         # 權限系統
├── audit.py              # 審計日誌
│
├── servers/
│   ├── __init__.py
│   ├── azure/            # Azure MCP Server
│   ├── shell/            # Shell MCP Server
│   ├── filesystem/       # Filesystem MCP Server
│   ├── ssh/              # SSH MCP Server
│   └── ldap/             # LDAP MCP Server
│
└── schemas/
    ├── __init__.py
    └── tool_schemas.py   # MCP Tool Schema 定義
```

### 文檔產物
- MCP 架構設計文檔
- 各 MCP Server 使用指南
- 安全配置指南
- API 參考文檔

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
