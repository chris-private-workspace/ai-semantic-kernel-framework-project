# MCP API 路由整合計劃

> **目標**: 將已實現的 MCP 架構整合到 FastAPI 主應用程式中
> **狀態**: 待用戶確認
> **日期**: 2025-12-23

---

## 1. 背景說明

### 當前狀態

MCP (Model Context Protocol) 架構在 Sprint 39-41 中已經**完整實現**，但 API 路由**尚未整合**到主應用程式。

| 組件 | 位置 | 狀態 |
|------|------|------|
| MCP Core | `backend/src/integrations/mcp/core/` | ✅ 已實現 |
| MCP Registry | `backend/src/integrations/mcp/registry/` | ✅ 已實現 |
| MCP Security | `backend/src/integrations/mcp/security/` | ✅ 已實現 |
| Azure MCP Server | `backend/src/integrations/mcp/servers/azure/` | ✅ 已實現 |
| Shell MCP Server | `backend/src/integrations/mcp/servers/shell/` | ✅ 已實現 |
| Filesystem MCP Server | `backend/src/integrations/mcp/servers/filesystem/` | ✅ 已實現 |
| SSH MCP Server | `backend/src/integrations/mcp/servers/ssh/` | ✅ 已實現 |
| LDAP MCP Server | `backend/src/integrations/mcp/servers/ldap/` | ✅ 已實現 |
| MCP API Routes | `backend/src/api/v1/mcp/routes.py` | ✅ 已實現 |
| MCP API Schemas | `backend/src/api/v1/mcp/schemas.py` | ✅ 已實現 |
| **API 路由整合** | `backend/src/api/v1/__init__.py` | ❌ **未整合** |

### 問題原因

`backend/src/api/v1/__init__.py` 中缺少 MCP 路由的導入和註冊：

```python
# 目前缺少：
from src.api.v1.mcp.routes import router as mcp_router
api_router.include_router(mcp_router)  # Phase 9: MCP Architecture
```

---

## 2. 整合計劃

### 2.1 修改文件

**文件**: `backend/src/api/v1/__init__.py`

**變更內容**:

```python
# 在導入區塊添加 (約第 64 行後):
from src.api.v1.mcp.routes import router as mcp_router

# 在路由註冊區塊添加 (約第 95 行後):
# Include sub-routers - Phase 9 (MCP Architecture)
api_router.include_router(mcp_router)  # Sprint 39-41: MCP Architecture
```

### 2.2 新增的 API 端點

整合後將啟用以下 15 個端點：

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/mcp/servers` | GET | 列出所有已註冊的 MCP Servers |
| `/api/v1/mcp/servers` | POST | 註冊新的 MCP Server |
| `/api/v1/mcp/servers/{name}` | GET | 獲取特定 Server 詳情 |
| `/api/v1/mcp/servers/{name}` | DELETE | 取消註冊 Server |
| `/api/v1/mcp/servers/{name}/connect` | POST | 連接到 Server |
| `/api/v1/mcp/servers/{name}/disconnect` | POST | 斷開 Server 連接 |
| `/api/v1/mcp/servers/{name}/tools` | GET | 列出 Server 的工具 |
| `/api/v1/mcp/tools` | GET | 列出所有可用工具 |
| `/api/v1/mcp/tools/execute` | POST | 執行工具 |
| `/api/v1/mcp/status` | GET | 獲取 Registry 狀態摘要 |
| `/api/v1/mcp/audit` | GET | 查詢審計日誌 |
| `/api/v1/mcp/connect-all` | POST | 連接所有啟用的 Servers |
| `/api/v1/mcp/disconnect-all` | POST | 斷開所有 Servers |

### 2.3 可用的 MCP Servers

| Server | 說明 | 工具數量 |
|--------|------|----------|
| `azure-mcp` | Azure 資源管理 (VM, Storage, Network, Monitor) | ~15 |
| `shell-mcp` | Shell 命令執行 (PowerShell, Bash, CMD) | ~5 |
| `filesystem-mcp` | 文件系統操作 (讀/寫/刪除) | ~6 |
| `ssh-mcp` | SSH 遠端連接 | ~4 |
| `ldap-mcp` | LDAP 目錄查詢 | ~4 |

---

## 3. 驗證步驟

### 3.1 整合後測試

```bash
# 1. 重啟後端服務
cd backend
uvicorn main:app --reload --port 8000

# 2. 驗證 MCP 端點可用
curl http://localhost:8000/api/v1/mcp/status

# 3. 列出 MCP Servers
curl http://localhost:8000/api/v1/mcp/servers

# 4. 列出所有工具
curl http://localhost:8000/api/v1/mcp/tools
```

### 3.2 預期結果

```json
// GET /api/v1/mcp/status
{
  "total_servers": 5,
  "status_counts": {
    "disconnected": 5,
    "connected": 0
  },
  "total_tools": 0,
  "servers": [...]
}
```

---

## 4. 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| 導入錯誤 | 低 | 語法檢查後再重啟服務 |
| 端點衝突 | 低 | `/mcp` 路徑未被其他模組使用 |
| 相依性問題 | 低 | MCP 模組已獨立測試通過 |

---

## 5. 回滾計劃

如果整合後出現問題，只需從 `__init__.py` 中移除新增的兩行代碼即可回滾。

---

## 6. 確認清單

請確認以下項目後，我將開始執行整合：

- [ ] 理解整合範圍（僅修改 1 個文件，新增 2 行代碼）
- [ ] 確認新增的 15 個 API 端點符合需求
- [ ] 確認 MCP Servers (Azure, Shell, Filesystem, SSH, LDAP) 符合預期
- [ ] 同意整合後進行驗證測試

---

**準備狀態**: ⏳ 等待用戶確認

