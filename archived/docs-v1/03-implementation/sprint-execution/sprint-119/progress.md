# Sprint 119 Progress: Agent Skills + 知識管理 API

## 狀態概覽

| 項目 | 狀態 |
|------|------|
| **開始日期** | 2026-03-19 |
| **預計結束** | 2026-03-19 |
| **總點數** | 10 點 |
| **完成點數** | 10 點 |
| **進度** | 100% |
| **Phase** | Phase 38 — E2E Assembly C |
| **Branch** | `feature/phase-38-e2e-c` |

## Sprint 目標

1. ✅ ITIL Incident Management SOP Agent Skill
2. ✅ ITIL Change Management SOP Agent Skill
3. ✅ Enterprise Architecture Reference Skill
4. ✅ AgentSkillsProvider（技能註冊 + 搜索 + 上下文注入）
5. ✅ 知識庫 CRUD API（ingest + search + collection management + skills）
6. ✅ search_knowledge handler 接線到 DispatchHandlers

## User Stories 進度

| Story | 名稱 | 點數 | 狀態 | 完成度 |
|-------|------|------|------|--------|
| S119-1 | Incident Management SOP | 2 | ✅ 完成 | 100% |
| S119-2 | Change Management SOP | 2 | ✅ 完成 | 100% |
| S119-3 | EA Reference + SkillsProvider | 2 | ✅ 完成 | 100% |
| S119-4 | Knowledge CRUD API | 2 | ✅ 完成 | 100% |
| S119-5 | search_knowledge handler 接線 | 2 | ✅ 完成 | 100% |

## 完成項目詳情

### Agent Skills (6 SP)
- **新增**: `backend/src/integrations/knowledge/agent_skills.py`
  - 3 個內建 ITIL SOP Skills:
    - **Incident Management**: 事件識別→分類→診斷→升級→解決→關閉（含 P1-P4 SLA）
    - **Change Management**: 變更分類→RFC→影響評估→CAB審批→實施→驗證
    - **Enterprise Architecture**: 核心系統、技術標準、安全標準
  - `AgentSkillsProvider`: 技能註冊、列表、搜索、上下文注入
  - `get_skill_context()` — 格式化技能內容為 prompt 注入文字
  - `search_skills()` — 關鍵字搜索匹配技能

### Knowledge CRUD API (2 SP)
- **新增**: `backend/src/api/v1/knowledge/__init__.py`
- **新增**: `backend/src/api/v1/knowledge/routes.py`
  - Knowledge Base endpoints:
    - `POST /api/v1/knowledge/ingest` — 文本內容入庫
    - `POST /api/v1/knowledge/search` — 知識搜索
    - `GET /api/v1/knowledge/collections` — 集合統計
    - `DELETE /api/v1/knowledge/collections` — 刪除集合
  - Agent Skills endpoints:
    - `GET /api/v1/knowledge/skills` — 列出技能（可按類別過濾）
    - `GET /api/v1/knowledge/skills/{skill_id}` — 取得技能詳情
    - `GET /api/v1/knowledge/skills/search/query` — 搜索技能

### search_knowledge 接線 (2 SP)
- **修改**: `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py`
  - 新增 `handle_search_knowledge()` handler（RAGPipeline 委託）
  - `register_all()` 新增 search_knowledge 到 handler map
- **修改**: `backend/src/api/v1/__init__.py` — 註冊 knowledge_router

## 檔案變更清單

| 操作 | 檔案路徑 |
|------|---------|
| 新增 | `backend/src/integrations/knowledge/agent_skills.py` |
| 新增 | `backend/src/api/v1/knowledge/__init__.py` |
| 新增 | `backend/src/api/v1/knowledge/routes.py` |
| 修改 | `backend/src/integrations/knowledge/__init__.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/dispatch_handlers.py` |
| 修改 | `backend/src/api/v1/__init__.py` |

## 相關文檔

- [Phase 38 計劃](../../sprint-planning/phase-38/README.md)
- [Sprint 118 Progress](../sprint-118/progress.md)
