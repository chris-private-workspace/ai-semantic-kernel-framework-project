# Sprint 119: Agent Skills + 知識管理

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 119 |
| **Phase** | 38 - E2E Assembly C: 記憶與知識組裝 |
| **Duration** | 1 day |
| **Story Points** | 10 pts |
| **Status** | ✅ 完成 |
| **Branch** | `feature/phase-38-e2e-c` |

---

## Sprint 目標

實現 MAF Agent Skills 打包（ITIL SOP）、AgentSkillsProvider 技能管理、知識庫 CRUD API，以及 search_knowledge handler 接線到 DispatchHandlers。

---

## Sprint 概述

Sprint 119 為 Phase 38 的第三個 Sprint，專注於結構化知識（Agent Skills）與知識管理 API 的實現。將 ITIL Incident Management、Change Management、Enterprise Architecture 三大 SOP 打包為 Agent Skills，建構 AgentSkillsProvider 進行技能註冊與搜索，並提供完整的知識庫 CRUD REST API 和 search_knowledge handler 的 DispatchHandlers 接線。

---

## 前置條件

- ✅ Sprint 118 完成（RAG Pipeline）
- ✅ MAF RC4 Agent Skills API 就緒 (FileAgentSkillsProvider)
- ✅ RAGPipeline 可用於 search_knowledge handler

---

## User Stories

### S119-1: ITIL Incident Management SOP Agent Skill (2 pts)

**作為** Orchestrator Agent，
**我希望** 能存取 ITIL Incident Management SOP 作為結構化知識，
**以便** 處理事件時能依循標準流程：事件識別→分類→診斷→升級→解決→關閉（含 P1-P4 SLA）。

**技術規格**:
- 新增 `backend/src/integrations/knowledge/agent_skills.py`
- 內建 Incident Management Skill：事件識別→分類→診斷→升級→解決→關閉
- 含 P1-P4 SLA 定義

---

### S119-2: ITIL Change Management SOP Agent Skill (2 pts)

**作為** Orchestrator Agent，
**我希望** 能存取 Change Management SOP 作為結構化知識，
**以便** 處理變更請求時能依循標準流程：變更分類→RFC→影響評估→CAB審批→實施→驗證。

**技術規格**:
- 內建 Change Management Skill：變更分類→RFC→影響評估→CAB審批→實施→驗證
- 包含標準變更、一般變更、緊急變更分類

---

### S119-3: Enterprise Architecture Reference + AgentSkillsProvider (2 pts)

**作為** Orchestrator Agent，
**我希望** 能存取企業架構參考資料，並透過 AgentSkillsProvider 統一管理所有技能的註冊、列表、搜索與上下文注入，
**以便** 回答涉及核心系統、技術標準、安全標準的問題時有據可依。

**技術規格**:
- 內建 Enterprise Architecture Skill：核心系統、技術標準、安全標準
- 實現 `AgentSkillsProvider`: 技能註冊、列表、搜索、上下文注入
- `get_skill_context()` — 格式化技能內容為 prompt 注入文字
- `search_skills()` — 關鍵字搜索匹配技能

---

### S119-4: 知識庫 CRUD API (2 pts)

**作為** 知識管理員，
**我希望** 透過 REST API 進行知識庫的文本入庫、搜索、集合管理，以及技能的列表和查詢，
**以便** 管理企業知識庫內容與查看索引狀態。

**技術規格**:
- 新增 `backend/src/api/v1/knowledge/__init__.py`
- 新增 `backend/src/api/v1/knowledge/routes.py`
- Knowledge Base endpoints:
  - `POST /api/v1/knowledge/ingest` — 文本內容入庫
  - `POST /api/v1/knowledge/search` — 知識搜索
  - `GET /api/v1/knowledge/collections` — 集合統計
  - `DELETE /api/v1/knowledge/collections` — 刪除集合
- Agent Skills endpoints:
  - `GET /api/v1/knowledge/skills` — 列出技能（可按類別過濾）
  - `GET /api/v1/knowledge/skills/{skill_id}` — 取得技能詳情
  - `GET /api/v1/knowledge/skills/search/query` — 搜索技能

---

### S119-5: search_knowledge handler 接線 (2 pts)

**作為** Orchestrator Agent，
**我希望** search_knowledge tool 能透過 DispatchHandlers 正確路由至 RAGPipeline 執行知識檢索，
**以便** 在對話中自主調用 search_knowledge 時能取得真實的知識庫搜索結果。

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
  - 新增 `handle_search_knowledge()` handler（RAGPipeline 委託）
  - `register_all()` 新增 search_knowledge 到 handler map
- 修改 `backend/src/api/v1/__init__.py` — 註冊 knowledge_router

---

## 相關連結

- [Phase 38 計劃](./README.md)
- [Sprint 119 Progress](../../sprint-execution/sprint-119/progress.md)
- [Sprint 118 Plan](./sprint-118-plan.md)
- [Sprint 120 Plan](./sprint-120-plan.md)
