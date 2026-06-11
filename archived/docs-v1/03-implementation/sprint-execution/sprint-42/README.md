# Sprint 42: Session Management Core

## Sprint 資訊

| 項目 | 內容 |
|------|------|
| **Sprint 編號** | Sprint 42 |
| **Phase** | Phase 10 - Session Mode API |
| **總點數** | 35 點 |
| **開始日期** | 2025-12-22 |
| **目標** | 建立 Session 管理核心功能 |

## Sprint 目標

1. 建立 Session 領域模型和狀態機
2. 實現 Session 存儲層 (PostgreSQL + Redis)
3. 開發 Session 服務層
4. 建立 Session REST API

## User Stories

| Story | 名稱 | 點數 | 優先級 |
|-------|------|------|--------|
| S42-1 | Session 領域模型 | 8 | P0 |
| S42-2 | Session 存儲層 | 10 | P0 |
| S42-3 | Session 服務層 | 10 | P0 |
| S42-4 | Session REST API | 7 | P0 |

## 技術規格

### 核心模型

- **Session**: 會話實體，包含狀態機
- **Message**: 訊息實體
- **Attachment**: 附件支援
- **ToolCall**: 工具調用記錄

### 狀態機

```
CREATED → ACTIVE → SUSPENDED → ENDED
           ↓          ↑
           └──────────┘
```

### API 端點

- `POST /api/v1/sessions` - 建立 Session
- `GET /api/v1/sessions/{id}` - 取得 Session
- `PUT /api/v1/sessions/{id}` - 更新 Session
- `DELETE /api/v1/sessions/{id}` - 結束 Session
- `POST /api/v1/sessions/{id}/messages` - 發送訊息
- `GET /api/v1/sessions/{id}/messages` - 取得訊息歷史

## 相關文檔

- [Sprint 計劃](../../sprint-planning/phase-10/sprint-42-plan.md)
- [Sprint 檢查清單](../../sprint-planning/phase-10/sprint-42-checklist.md)
- [Phase 10 README](../../sprint-planning/phase-10/README.md)

---

**創建日期**: 2025-12-22
