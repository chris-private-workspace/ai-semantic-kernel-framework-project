# API 整合測試計劃 - 真正的 HTTP 端點呼叫

> **建立日期**: 2025-12-18
> **測試類型**: 真正的 HTTP API 整合測試 (非模擬)
> **測試框架**: httpx + pytest-asyncio
> **目標端點**: FastAPI Backend (http://localhost:8000)

---

## 1. 測試目標

### 1.1 核心目標

驗證 IPA Platform 所有主要 API 端點的功能正確性，透過**真正的 HTTP 請求**來測試，而非 Python 邏輯模擬。

### 1.2 測試範圍

| 模組 | API 前綴 | 測試重點 |
|------|----------|----------|
| Workflows | `/api/v1/workflows` | CRUD + 執行 + 驗證 |
| Agents | `/api/v1/agents` | CRUD + 運行 |
| Checkpoints | `/api/v1/checkpoints` | 審批流程 |
| Handoff | `/api/v1/handoff` | 派遣 + 能力匹配 |
| Routing | `/api/v1/routing` | 場景路由 |
| GroupChat | `/api/v1/groupchat` | 多代理協作 |

### 1.3 測試方法

```python
# 使用 httpx.AsyncClient 進行真正的 HTTP 呼叫
import httpx

async def test_endpoint():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/api/v1/workflows/", json={...})
        assert response.status_code == 201
```

---

## 2. 測試環境

### 2.1 必要條件

- FastAPI 後端服務運行中 (`uvicorn main:app --port 8000`)
- PostgreSQL 資料庫連線正常
- Redis 服務運行中 (可選，用於快取)
- Azure OpenAI 環境變數已設定 (用於 LLM 相關測試)

### 2.2 環境變數

```bash
# 必要
DATABASE_URL=postgresql://ipa_user:ipa_password@localhost:5432/ipa_platform
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM 測試需要
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### 2.3 測試執行命令

```bash
# 確保後端運行中
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 執行整合測試
python scripts/uat/api_integration_test.py
```

---

## 3. 測試案例設計

### Phase 1: Workflows API (5 測試)

#### Test 1.1: 建立工作流程
```
POST /api/v1/workflows/
Request Body:
{
  "name": "IT Ticket Triage",
  "description": "IT 工單分類工作流程",
  "type": "sequential",
  "nodes": [...],
  "edges": [...]
}
Expected: 201 Created
Verify: Response contains workflow_id, name matches
```

#### Test 1.2: 取得工作流程列表
```
GET /api/v1/workflows/
Expected: 200 OK
Verify: Response is array, contains created workflow
```

#### Test 1.3: 取得單一工作流程
```
GET /api/v1/workflows/{workflow_id}
Expected: 200 OK
Verify: Response matches created workflow
```

#### Test 1.4: 驗證工作流程
```
POST /api/v1/workflows/{workflow_id}/validate
Expected: 200 OK
Verify: Response contains validation result
```

#### Test 1.5: 刪除工作流程
```
DELETE /api/v1/workflows/{workflow_id}
Expected: 204 No Content
Verify: Subsequent GET returns 404
```

---

### Phase 2: Agents API (4 測試)

#### Test 2.1: 建立代理
```
POST /api/v1/agents/
Request Body:
{
  "name": "Triage Agent",
  "description": "工單分類代理",
  "type": "assistant",
  "model": "gpt-4o",
  "capabilities": ["classification", "routing"]
}
Expected: 201 Created
Verify: Response contains agent_id
```

#### Test 2.2: 取得代理列表
```
GET /api/v1/agents/
Expected: 200 OK
Verify: Response is array
```

#### Test 2.3: 取得單一代理
```
GET /api/v1/agents/{agent_id}
Expected: 200 OK
Verify: Response matches created agent
```

#### Test 2.4: 刪除代理
```
DELETE /api/v1/agents/{agent_id}
Expected: 204 No Content
```

---

### Phase 3: Checkpoints API (4 測試)

#### Test 3.1: 建立檢查點
```
POST /api/v1/checkpoints/
Request Body:
{
  "execution_id": "{execution_id}",
  "type": "approval",
  "approvers": ["it_manager"],
  "timeout_minutes": 30,
  "context": {
    "priority": "P1",
    "reason": "Critical issue"
  }
}
Expected: 201 Created
Verify: Response contains checkpoint_id, status is PENDING
```

#### Test 3.2: 取得待審批檢查點列表
```
GET /api/v1/checkpoints/pending
Expected: 200 OK
Verify: Response contains created checkpoint
```

#### Test 3.3: 審批檢查點
```
POST /api/v1/checkpoints/{checkpoint_id}/approve
Request Body:
{
  "approved_by": "it_manager",
  "comment": "Approved for immediate action"
}
Expected: 200 OK
Verify: Response status is APPROVED
```

#### Test 3.4: 拒絕檢查點
```
POST /api/v1/checkpoints/{checkpoint_id}/reject
Request Body:
{
  "rejected_by": "it_manager",
  "reason": "Need more information"
}
Expected: 200 OK
Verify: Response status is REJECTED
```

---

### Phase 4: Handoff API (3 測試)

#### Test 4.1: 觸發派遣
```
POST /api/v1/handoff/trigger
Request Body:
{
  "source_agent": "triage_agent",
  "target_agent": "network_expert",
  "context": {
    "ticket_id": "TKT-001",
    "priority": "P1",
    "category": "Network"
  }
}
Expected: 201 Created
Verify: Response contains handoff_id, status is INITIATED
```

#### Test 4.2: 取得派遣狀態
```
GET /api/v1/handoff/{handoff_id}/status
Expected: 200 OK
Verify: Response contains status and context
```

#### Test 4.3: 能力匹配
```
POST /api/v1/handoff/capability/match
Request Body:
{
  "required_capabilities": ["network_diagnosis", "troubleshooting"],
  "context": {"priority": "P1"}
}
Expected: 200 OK
Verify: Response contains matched agents list
```

---

### Phase 5: Routing API (2 測試)

#### Test 5.1: 場景路由
```
POST /api/v1/routing/route
Request Body:
{
  "category": "Network",
  "priority": "P1",
  "context": {
    "department": "Finance",
    "impact": "50 users"
  }
}
Expected: 200 OK
Verify: Response contains scenario and team assignment
```

#### Test 5.2: 取得場景列表
```
GET /api/v1/routing/scenarios
Expected: 200 OK
Verify: Response is array of available scenarios
```

---

### Phase 6: GroupChat API (3 測試)

#### Test 6.1: 建立 GroupChat
```
POST /api/v1/groupchat/
Request Body:
{
  "name": "IT Expert Panel",
  "participants": ["network_expert", "endpoint_expert", "helpdesk_agent"],
  "config": {
    "max_turns": 10,
    "selection_strategy": "round_robin"
  }
}
Expected: 201 Created
Verify: Response contains groupchat_id
```

#### Test 6.2: 建立會話
```
POST /api/v1/groupchat/sessions/
Request Body:
{
  "groupchat_id": "{groupchat_id}",
  "topic": "Network outage in Finance department"
}
Expected: 201 Created
Verify: Response contains session_id
```

#### Test 6.3: 取得 GroupChat 列表
```
GET /api/v1/groupchat/
Expected: 200 OK
Verify: Response contains created groupchat
```

---

### Phase 7: E2E 流程測試 (1 測試)

#### Test 7.1: 完整工單處理流程
```
流程:
1. POST /api/v1/agents/ → 建立 Triage Agent
2. POST /api/v1/workflows/ → 建立工作流程
3. POST /api/v1/workflows/{id}/execute → 執行工作流程
4. POST /api/v1/checkpoints/ → 建立審批檢查點
5. POST /api/v1/checkpoints/{id}/approve → 審批通過
6. POST /api/v1/handoff/trigger → 觸發派遣
7. GET /api/v1/handoff/{id}/status → 確認派遣完成

Expected: 所有步驟成功完成
Verify: 最終派遣狀態為 COMPLETED
```

---

## 4. 測試資料

### 4.1 測試工作流程定義

```json
{
  "name": "IT Ticket Triage Workflow",
  "description": "Complete IT ticket triage from intake to dispatch",
  "type": "sequential",
  "version": "1.0.0",
  "nodes": [
    {"id": "intake", "type": "agent", "agent": "triage_agent"},
    {"id": "route", "type": "condition"},
    {"id": "approval", "type": "checkpoint"},
    {"id": "handoff", "type": "handoff"},
    {"id": "complete", "type": "end"}
  ],
  "edges": [
    {"from": "intake", "to": "route"},
    {"from": "route", "to": "approval", "condition": "priority == 'P1'"},
    {"from": "route", "to": "handoff", "condition": "priority != 'P1'"},
    {"from": "approval", "to": "handoff"},
    {"from": "handoff", "to": "complete"}
  ]
}
```

### 4.2 測試代理定義

```json
{
  "name": "Triage Agent",
  "description": "IT ticket classification and routing agent",
  "type": "assistant",
  "model": "gpt-4o",
  "capabilities": ["classification", "routing", "prioritization"],
  "system_prompt": "You are an IT ticket triage specialist..."
}
```

### 4.3 測試工單資料

```json
{
  "id": "TKT-TEST-001",
  "title": "Network outage in Finance department",
  "description": "整層網路斷線，約50人無法連網，影響月結作業",
  "reporter": "CFO",
  "department": "Finance",
  "is_vip": true
}
```

---

## 5. 驗證標準

### 5.1 成功標準

| 項目 | 標準 |
|------|------|
| HTTP 狀態碼 | 符合 RESTful 規範 (201 Created, 200 OK, 204 No Content) |
| 回應格式 | JSON 結構正確，必要欄位存在 |
| 資料一致性 | 建立的資源可以正確讀取 |
| 錯誤處理 | 無效請求返回適當的錯誤碼和訊息 |

### 5.2 失敗標準

| 項目 | 標準 |
|------|------|
| 連線失敗 | 無法連接到 API 伺服器 |
| 狀態碼錯誤 | 收到非預期的 HTTP 狀態碼 |
| 回應異常 | JSON 解析失敗或必要欄位缺失 |
| 邏輯錯誤 | 資料不一致或業務邏輯違反 |

---

## 6. 測試執行計劃

### 6.1 執行順序

```
Phase 1: Workflows API (5 tests) → 基礎 CRUD 功能
    ↓
Phase 2: Agents API (4 tests) → 代理管理功能
    ↓
Phase 3: Checkpoints API (4 tests) → 審批流程功能
    ↓
Phase 4: Handoff API (3 tests) → 派遣功能
    ↓
Phase 5: Routing API (2 tests) → 路由功能
    ↓
Phase 6: GroupChat API (3 tests) → 協作功能
    ↓
Phase 7: E2E Flow (1 test) → 完整流程驗證
```

### 6.2 預計時間

| Phase | 測試數 | 預計時間 |
|-------|--------|----------|
| Phase 1 | 5 | ~10 秒 |
| Phase 2 | 4 | ~8 秒 |
| Phase 3 | 4 | ~8 秒 |
| Phase 4 | 3 | ~6 秒 |
| Phase 5 | 2 | ~4 秒 |
| Phase 6 | 3 | ~6 秒 |
| Phase 7 | 1 | ~15 秒 |
| **總計** | **22** | **~60 秒** |

---

## 7. 結果記錄

測試結果將記錄在:
- `claudedocs/uat/TEST-RESULT-API-INTEGRATION.md` - 結果報告
- `claudedocs/uat/sessions/api_integration_{timestamp}.json` - 詳細 JSON 結果

### 7.1 結果格式

```json
{
  "test_plan": "API Integration Test",
  "executed_at": "2025-12-18T...",
  "environment": {
    "base_url": "http://localhost:8000",
    "database": "postgresql://..."
  },
  "summary": {
    "total_tests": 22,
    "passed": 0,
    "failed": 0,
    "pass_rate": "0%"
  },
  "results": [
    {
      "test_id": 1,
      "test_name": "Create Workflow",
      "phase": "Phase 1: Workflows API",
      "method": "POST",
      "endpoint": "/api/v1/workflows/",
      "status": "PASS|FAIL",
      "http_status": 201,
      "duration_ms": 0,
      "response": {},
      "error": ""
    }
  ]
}
```

---

## 8. 附錄

### 8.1 相關文件

| 文件 | 說明 |
|------|------|
| `scripts/uat/api_integration_test.py` | 測試腳本 |
| `backend/src/api/v1/*/routes.py` | API 路由定義 |
| `claudedocs/uat/TEST-RESULT-IT-TICKET-E2E.md` | 之前的模擬測試結果 |

### 8.2 與模擬測試的區別

| 項目 | 模擬測試 | API 整合測試 |
|------|----------|--------------|
| 方法 | Python 邏輯呼叫 | HTTP 請求 |
| 工具 | 直接呼叫 service | httpx.AsyncClient |
| 範圍 | 單元測試 | 端到端測試 |
| 依賴 | 無需服務運行 | 需要 FastAPI 運行 |
| 驗證 | 函數回傳值 | HTTP 回應 |

---

**測試計劃建立完成**: 2025-12-18
**下一步**: 實作測試腳本 `scripts/uat/api_integration_test.py`
