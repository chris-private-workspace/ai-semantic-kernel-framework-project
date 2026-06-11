# MCP API 整合 Checklist

**目標**: 將已實現的 MCP 架構整合到 FastAPI 主應用程式中
**點數**: 2 Story Points (小型整合任務)
**狀態**: ✅ 代碼完成 (需完整環境測試)
**前置條件**: Sprint 39-41 MCP 架構已實現
**日期**: 2025-12-23

---

## 前置條件檢查

### MCP 架構完成確認
- [x] MCP Core 已實現 (`backend/src/integrations/mcp/core/`)
  - [x] `types.py` - 類型定義
  - [x] `protocol.py` - 協議處理器
  - [x] `transport.py` - 傳輸層
  - [x] `client.py` - MCP 客戶端
- [x] MCP Registry 已實現 (`backend/src/integrations/mcp/registry/`)
  - [x] `server_registry.py` - Server 註冊表
  - [x] `config_loader.py` - 配置載入器
- [x] MCP Security 已實現 (`backend/src/integrations/mcp/security/`)
  - [x] `permissions.py` - 權限系統
  - [x] `audit.py` - 審計日誌
- [x] MCP Servers 已實現 (`backend/src/integrations/mcp/servers/`)
  - [x] `azure/` - Azure MCP Server
  - [x] `shell/` - Shell MCP Server
  - [x] `filesystem/` - Filesystem MCP Server
  - [x] `ssh/` - SSH MCP Server
  - [x] `ldap/` - LDAP MCP Server
- [x] MCP API 已實現 (`backend/src/api/v1/mcp/`)
  - [x] `routes.py` - 15+ REST 端點
  - [x] `schemas.py` - Pydantic schemas

### 當前問題
- [x] MCP 路由未在 `backend/src/api/v1/__init__.py` 中註冊 ✅ 已解決

---

## 整合任務 Checklist

### 步驟 1: 語法驗證
- [x] 驗證 MCP routes 語法正確 ✅
  ```bash
  cd backend
  python -m py_compile src/api/v1/mcp/routes.py    # OK
  python -m py_compile src/api/v1/mcp/schemas.py   # OK
  ```
- [x] 驗證 MCP integrations 語法正確 ✅
  ```bash
  python -m py_compile src/integrations/mcp/registry/__init__.py  # OK
  python -m py_compile src/integrations/mcp/security/__init__.py  # OK
  ```

### 步驟 2: 修改 API Router
- [x] 編輯 `backend/src/api/v1/__init__.py` ✅
- [x] 添加導入語句 (line 55) ✅
  ```python
  from src.api.v1.mcp.routes import router as mcp_router
  ```
- [x] 添加路由註冊 (line 99-100) ✅
  ```python
  # Include sub-routers - Phase 9 (MCP Architecture)
  api_router.include_router(mcp_router)  # Sprint 39-41: MCP Architecture
  ```
- [x] 更新文件頭部註釋，添加 MCP 說明 (line 37) ✅

### 步驟 3: 驗證導入
- [x] 驗證修改後的 `__init__.py` 語法正確 ✅
  ```bash
  python -m py_compile src/api/v1/__init__.py  # OK
  ```
- [ ] 驗證主應用程式可以啟動 (需啟動服務)
  ```bash
  python -c "from main import app; print('OK')"
  ```

### 步驟 4: 功能測試
- [ ] 啟動後端服務
  ```bash
  uvicorn main:app --reload --port 8000
  ```
- [ ] 測試 MCP status 端點
  ```bash
  curl http://localhost:8000/api/v1/mcp/status
  ```
  預期結果: 返回 JSON 包含 `total_servers`, `status_counts`, `total_tools`

- [ ] 測試 MCP servers 端點
  ```bash
  curl http://localhost:8000/api/v1/mcp/servers
  ```
  預期結果: 返回空列表 `[]` 或已註冊的 servers

- [ ] 測試 MCP tools 端點
  ```bash
  curl http://localhost:8000/api/v1/mcp/tools
  ```
  預期結果: 返回 `{"tools": [], "total": 0}` 或已連接 servers 的工具

### 步驟 5: Phase 9 測試驗證
- [ ] 重新執行 Phase 9 MCP 測試
  ```bash
  cd scripts/uat/phase_tests/phase_9_mcp_architecture
  python test_real_mcp.py
  ```
- [ ] 確認 MCP Servers 端點返回 200
- [ ] 確認 MCP Tools 端點返回 200

---

## 驗收標準

- [x] `backend/src/api/v1/__init__.py` 正確修改 ✅
- [ ] 後端服務可以正常啟動 (需完整環境)
- [ ] `/api/v1/mcp/status` 返回 200 (需啟動服務)
- [ ] `/api/v1/mcp/servers` 返回 200 (需啟動服務)
- [ ] `/api/v1/mcp/tools` 返回 200 (需啟動服務)
- [ ] Phase 9 MCP 測試通過 (需啟動服務)

---

## 回滾計劃

如果整合失敗，執行以下步驟：

1. [ ] 從 `__init__.py` 移除新增的 2 行代碼
2. [ ] 重啟後端服務
3. [ ] 確認其他 API 正常工作

---

## 完成簽核

- [x] 整合完成 (代碼層面) ✅
- [ ] 測試通過 (需完整環境)
- [x] 文檔更新 ✅

**完成日期**: 2025-12-23
**執行者**: Claude Code

---

**準備狀態**: ✅ 代碼整合完成，待完整環境測試

### 備註
- 當前電腦未安裝完整依賴 (`agent_framework` 等)
- 語法驗證全部通過
- 需要在有完整環境的機器上測試 API 端點

