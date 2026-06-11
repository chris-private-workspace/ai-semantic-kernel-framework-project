# Sprint 156 Plan - 生產 API + 後處理

## Phase 45: Orchestration Core

### Sprint 目標
建立 PostProcessStep（checkpoint + 異步記憶抽取）和生產 SSE 串流 API 端點。

---

## 檔案變更

| 檔案 | 動作 | 說明 |
|------|------|------|
| `pipeline/steps/step8_postprocess.py` | NEW | PostProcessStep |
| `api/v1/orchestration/chat_schemas.py` | NEW | Pydantic schemas |
| `api/v1/orchestration/chat_routes.py` | NEW | 4 個生產端點 |
| `api/v1/orchestration/__init__.py` | MODIFY | 註冊 chat_router |
| `api/v1/__init__.py` | MODIFY | include_router |

---

**Story Points**: 22
**Status**: ✅ Completed
