# Sprint 42 Technical Decisions: Session Management Core

## 決策記錄

| ID | 決策 | 日期 | 狀態 |
|----|------|------|------|
| D42-1 | Session 使用狀態機管理生命週期 | 2025-12-22 | ✅ 已採納 |
| D42-2 | 雙層存儲策略 (PostgreSQL + Redis) | 2025-12-22 | ✅ 已採納 |
| D42-3 | Message 使用時間序列設計 | 2025-12-22 | ✅ 已採納 |
| D42-4 | Attachment 使用 Blob 存儲 | 2025-12-22 | ✅ 已採納 |

---

## 決策詳情

### D42-1: Session 使用狀態機管理生命週期 ✅

**背景**: Session 需要管理多種狀態轉換

**選項**:
1. 簡單狀態欄位
2. 狀態機模式
3. 事件溯源模式

**決策**: 狀態機模式

**理由**:
- 明確的狀態轉換規則
- 易於擴展和維護
- 支援狀態驗證
- 與 Workflow 執行狀態機一致

**實現摘要**:
```python
class SessionStatus(str, Enum):
    CREATED = "created"     # 剛建立，尚未開始
    ACTIVE = "active"       # 進行中
    SUSPENDED = "suspended" # 暫停
    ENDED = "ended"         # 已結束

# 狀態轉換: CREATED → ACTIVE ⇄ SUSPENDED → ENDED
```

**檔案**: `backend/src/domain/sessions/models.py`

---

### D42-2: 雙層存儲策略 (PostgreSQL + Redis) ✅

**背景**: Session 需要兼顧持久化和效能

**選項**:
1. 純 PostgreSQL
2. 純 Redis
3. PostgreSQL + Redis 雙層

**決策**: 雙層存儲策略

**理由**:
- PostgreSQL: 持久化存儲，支援複雜查詢
- Redis: 快取活躍 Session，減少延遲
- 分離讀寫路徑，優化效能
- 支援水平擴展

**實現摘要**:
- `SQLAlchemySessionRepository`: PostgreSQL 持久化
- `SessionCache`: Redis 快取層，write-through 策略
- TTL: Session 7200s (2小時), Messages 3600s (1小時)

**檔案**:
- `backend/src/domain/sessions/repository.py`
- `backend/src/domain/sessions/cache.py`

---

### D42-3: Message 使用時間序列設計 ✅

**背景**: 訊息需要按時間順序排列

**選項**:
1. 簡單 list 存儲
2. 時間戳 + 序號雙索引
3. 時間序列資料庫

**決策**: 時間戳 + 序號雙索引

**理由**:
- 時間戳支援範圍查詢
- 序號保證順序一致性
- 不需要額外資料庫
- 查詢效能良好

**實現摘要**:
```python
class MessageModel(Base, UUIDMixin, TimestampMixin):
    session_id = Column(UUID, ForeignKey("sessions.id"), index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

**檔案**: `backend/src/infrastructure/database/models/session.py`

---

### D42-4: Attachment 使用 Blob 存儲 ✅

**背景**: 附件可能包含大型文件

**選項**:
1. Base64 存入資料庫
2. 本地檔案系統
3. Blob 存儲 (可配置)

**決策**: Blob 存儲抽象層

**理由**:
- 支援本地和雲端存儲
- 不影響資料庫效能
- 易於擴展至 Azure Blob / S3
- 統一的存取介面

**實現摘要**:
```python
class Attachment:
    id: str
    filename: str
    content_type: str
    size: int
    attachment_type: AttachmentType  # IMAGE, DOCUMENT, CODE, DATA, OTHER
    storage_path: str  # 實際存儲路徑 (可為本地或雲端)
```

**備註**: 實際 Blob 存儲實現將在後續 Sprint 完成，目前使用預留介面。

**檔案**: `backend/src/domain/sessions/models.py`

---

## 額外技術決策

### D42-5: 事件驅動架構 ✅

**背景**: 需要支援即時通知和審計日誌

**決策**: 實現 SessionEventPublisher 支援本地事件訂閱

**實現摘要**:
```python
class SessionEventType(str, Enum):
    SESSION_CREATED = "session.created"
    SESSION_ACTIVATED = "session.activated"
    MESSAGE_SENT = "message.sent"
    TOOL_CALL_REQUESTED = "tool_call.requested"
    # ... 等 15 種事件類型
```

**檔案**: `backend/src/domain/sessions/events.py`

---

**創建日期**: 2025-12-22
**完成日期**: 2025-12-22
**更新日期**: 2025-12-22
