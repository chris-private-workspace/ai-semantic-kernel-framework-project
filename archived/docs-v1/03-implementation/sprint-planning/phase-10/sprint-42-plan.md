# Sprint 42: Session Management Core

> **目標**: 實現 Session 管理核心功能，建立互動式對話基礎設施

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 42 |
| 總點數 | 35 Story Points |
| 預計時間 | 2 週 |
| 前置條件 | Phase 9 完成 |
| 狀態 | 📋 計劃中 |

---

## Stories

### S42-1: Session 領域模型 (8 pts)

**描述**: 實現 Session 和 Message 的核心領域模型

**功能需求**:
1. Session 生命週期管理
2. 對話訊息模型
3. 附件模型
4. 工具調用記錄

**技術設計**:

```python
# domain/sessions/models.py

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class SessionStatus(Enum):
    """Session 狀態"""
    CREATED = "created"      # 已創建，尚未連接
    ACTIVE = "active"        # 活躍中
    SUSPENDED = "suspended"  # 暫停 (連接中斷)
    ENDED = "ended"          # 已結束


class MessageRole(Enum):
    """訊息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AttachmentType(Enum):
    """附件類型"""
    IMAGE = "image"
    DOCUMENT = "document"
    CODE = "code"
    DATA = "data"
    OTHER = "other"


@dataclass
class Attachment:
    """附件模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    content_type: str = ""
    size: int = 0
    storage_path: str = ""
    attachment_type: AttachmentType = AttachmentType.OTHER
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_upload(
        cls,
        filename: str,
        content_type: str,
        size: int,
        storage_path: str
    ) -> "Attachment":
        """從上傳創建附件"""
        attachment_type = cls._detect_type(content_type)
        return cls(
            filename=filename,
            content_type=content_type,
            size=size,
            storage_path=storage_path,
            attachment_type=attachment_type
        )

    @staticmethod
    def _detect_type(content_type: str) -> AttachmentType:
        """檢測附件類型"""
        if content_type.startswith("image/"):
            return AttachmentType.IMAGE
        elif content_type in ["application/pdf", "text/plain", "application/msword"]:
            return AttachmentType.DOCUMENT
        elif content_type in ["text/python", "application/javascript", "text/x-python"]:
            return AttachmentType.CODE
        elif content_type in ["text/csv", "application/json", "application/xml"]:
            return AttachmentType.DATA
        else:
            return AttachmentType.OTHER


@dataclass
class ToolCall:
    """工具調用記錄"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, approved, rejected, completed, failed
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class Message:
    """對話訊息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    role: MessageRole = MessageRole.USER
    content: str = ""
    attachments: List[Attachment] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_attachment(self, attachment: Attachment) -> None:
        """添加附件"""
        self.attachments.append(attachment)

    def add_tool_call(self, tool_call: ToolCall) -> None:
        """添加工具調用"""
        self.tool_calls.append(tool_call)


@dataclass
class SessionConfig:
    """Session 配置"""
    max_messages: int = 100
    max_attachments: int = 10
    max_attachment_size: int = 10 * 1024 * 1024  # 10MB
    timeout_minutes: int = 60
    enable_code_interpreter: bool = True
    enable_mcp_tools: bool = True
    allowed_tools: List[str] = field(default_factory=list)  # 空 = 所有


@dataclass
class Session:
    """Session 模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    agent_id: str = ""
    status: SessionStatus = SessionStatus.CREATED
    config: SessionConfig = field(default_factory=SessionConfig)
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化後處理"""
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(
                minutes=self.config.timeout_minutes
            )

    def activate(self) -> None:
        """激活 Session"""
        if self.status in [SessionStatus.CREATED, SessionStatus.SUSPENDED]:
            self.status = SessionStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def suspend(self) -> None:
        """暫停 Session"""
        if self.status == SessionStatus.ACTIVE:
            self.status = SessionStatus.SUSPENDED
            self.updated_at = datetime.utcnow()

    def end(self) -> None:
        """結束 Session"""
        self.status = SessionStatus.ENDED
        self.ended_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """檢查是否過期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def add_message(self, message: Message) -> None:
        """添加訊息"""
        message.session_id = self.id
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        self._extend_expiry()

    def _extend_expiry(self) -> None:
        """延長過期時間"""
        self.expires_at = datetime.utcnow() + timedelta(
            minutes=self.config.timeout_minutes
        )

    def get_conversation_history(
        self,
        limit: int = None,
        include_system: bool = False
    ) -> List[Message]:
        """獲取對話歷史"""
        messages = self.messages
        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]
        if limit:
            messages = messages[-limit:]
        return messages
```

**驗收標準**:
- [ ] Session 狀態機正確運作
- [ ] Message 支援多種角色
- [ ] Attachment 類型正確檢測
- [ ] ToolCall 記錄完整
- [ ] 測試覆蓋率 > 90%

---

### S42-2: Session 存儲層 (10 pts)

**描述**: 實現 Session 和 Message 的持久化存儲

**功能需求**:
1. PostgreSQL 存儲
2. Redis 快取
3. 分頁查詢
4. 全文搜索 (可選)

**技術設計**:

```python
# infrastructure/database/models/session.py

from sqlalchemy import Column, String, Enum, DateTime, JSON, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from .base import Base

class SessionModel(Base):
    """Session 數據庫模型"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)
    status = Column(
        Enum("created", "active", "suspended", "ended", name="session_status"),
        nullable=False,
        default="created"
    )
    config = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=False, default=dict)

    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan")


class MessageModel(Base):
    """Message 數據庫模型"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(
        Enum("user", "assistant", "system", "tool", name="message_role"),
        nullable=False
    )
    content = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=False, default=list)
    tool_calls = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False)
    metadata = Column(JSON, nullable=False, default=dict)

    session = relationship("SessionModel", back_populates="messages")


class AttachmentModel(Base):
    """Attachment 數據庫模型"""
    __tablename__ = "attachments"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    attachment_type = Column(String(50), nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    metadata = Column(JSON, nullable=False, default=dict)
```

```python
# domain/sessions/repository.py

from typing import Optional, List
from abc import ABC, abstractmethod

class SessionRepository(ABC):
    """Session 存儲抽象"""

    @abstractmethod
    async def create(self, session: Session) -> Session:
        """創建 Session"""
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Optional[Session]:
        """獲取 Session"""
        pass

    @abstractmethod
    async def update(self, session: Session) -> Session:
        """更新 Session"""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """刪除 Session"""
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Session]:
        """列出用戶的 Sessions"""
        pass

    @abstractmethod
    async def add_message(self, session_id: str, message: Message) -> Message:
        """添加訊息"""
        pass

    @abstractmethod
    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
        before_id: Optional[str] = None
    ) -> List[Message]:
        """獲取訊息"""
        pass


class SQLAlchemySessionRepository(SessionRepository):
    """SQLAlchemy 實現"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, session: Session) -> Session:
        """創建 Session"""
        db_session = SessionModel(
            id=session.id,
            user_id=session.user_id,
            agent_id=session.agent_id,
            status=session.status.value,
            config=asdict(session.config),
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at,
            metadata=session.metadata
        )
        self._db.add(db_session)
        await self._db.commit()
        return session

    async def get(self, session_id: str) -> Optional[Session]:
        """獲取 Session"""
        result = await self._db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        if db_session is None:
            return None
        return self._to_domain(db_session)

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
        before_id: Optional[str] = None
    ) -> List[Message]:
        """獲取訊息"""
        query = select(MessageModel).where(
            MessageModel.session_id == session_id
        )

        if before_id:
            # 獲取 before_id 的創建時間
            before_msg = await self._db.execute(
                select(MessageModel.created_at).where(MessageModel.id == before_id)
            )
            before_time = before_msg.scalar_one_or_none()
            if before_time:
                query = query.where(MessageModel.created_at < before_time)

        query = query.order_by(MessageModel.created_at.desc()).limit(limit)
        result = await self._db.execute(query)
        messages = result.scalars().all()

        return [self._message_to_domain(m) for m in reversed(messages)]
```

```python
# domain/sessions/cache.py

from typing import Optional
import json
from redis.asyncio import Redis

class SessionCache:
    """Session Redis 快取"""

    def __init__(self, redis: Redis, ttl: int = 3600):
        self._redis = redis
        self._ttl = ttl

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def get(self, session_id: str) -> Optional[Session]:
        """從快取獲取"""
        data = await self._redis.get(self._key(session_id))
        if data is None:
            return None
        return Session(**json.loads(data))

    async def set(self, session: Session) -> None:
        """設置快取"""
        data = json.dumps(asdict(session), default=str)
        await self._redis.setex(
            self._key(session.id),
            self._ttl,
            data
        )

    async def delete(self, session_id: str) -> None:
        """刪除快取"""
        await self._redis.delete(self._key(session_id))

    async def extend(self, session_id: str) -> None:
        """延長過期時間"""
        await self._redis.expire(self._key(session_id), self._ttl)
```

**驗收標準**:
- [ ] Session CRUD 操作正常
- [ ] Message 分頁查詢正常
- [ ] Redis 快取正常
- [ ] 過期 Session 自動清理
- [ ] 測試覆蓋率 > 85%

---

### S42-3: Session 服務層 (10 pts)

**描述**: 實現 Session 業務邏輯服務

**功能需求**:
1. Session 生命週期管理
2. 訊息處理
3. 與 Agent 整合
4. 事件發布

**技術設計**:

```python
# domain/sessions/service.py

from typing import Optional, List, AsyncIterator
from dataclasses import asdict

class SessionService:
    """Session 服務"""

    def __init__(
        self,
        repository: SessionRepository,
        cache: SessionCache,
        agent_service: AgentService,
        event_publisher: EventPublisher
    ):
        self._repository = repository
        self._cache = cache
        self._agent_service = agent_service
        self._events = event_publisher

    async def create_session(
        self,
        user_id: str,
        agent_id: str,
        config: Optional[SessionConfig] = None
    ) -> Session:
        """創建新 Session"""
        # 驗證 Agent 存在
        agent = await self._agent_service.get(agent_id)
        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")

        # 創建 Session
        session = Session(
            user_id=user_id,
            agent_id=agent_id,
            config=config or SessionConfig()
        )

        # 添加系統訊息
        system_message = Message(
            role=MessageRole.SYSTEM,
            content=agent.system_prompt
        )
        session.add_message(system_message)

        # 持久化
        await self._repository.create(session)
        await self._cache.set(session)

        # 發布事件
        await self._events.publish("session.created", {
            "session_id": session.id,
            "user_id": user_id,
            "agent_id": agent_id
        })

        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """獲取 Session"""
        # 先查快取
        session = await self._cache.get(session_id)
        if session:
            return session

        # 查資料庫
        session = await self._repository.get(session_id)
        if session:
            await self._cache.set(session)
        return session

    async def activate_session(self, session_id: str) -> Session:
        """激活 Session"""
        session = await self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        if session.is_expired():
            raise ValueError("Session has expired")

        session.activate()
        await self._repository.update(session)
        await self._cache.set(session)

        await self._events.publish("session.activated", {
            "session_id": session_id
        })

        return session

    async def end_session(self, session_id: str) -> Session:
        """結束 Session"""
        session = await self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        session.end()
        await self._repository.update(session)
        await self._cache.delete(session_id)

        await self._events.publish("session.ended", {
            "session_id": session_id
        })

        return session

    async def send_message(
        self,
        session_id: str,
        content: str,
        attachments: List[Attachment] = None
    ) -> AsyncIterator[str]:
        """
        發送訊息並獲取回覆 (串流)

        Yields:
            str: 回覆內容片段
        """
        session = await self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session is not active: {session.status}")

        # 創建用戶訊息
        user_message = Message(
            role=MessageRole.USER,
            content=content,
            attachments=attachments or []
        )
        await self._repository.add_message(session_id, user_message)

        # 獲取對話歷史
        history = await self._repository.get_messages(session_id, limit=50)

        # 調用 Agent
        agent = await self._agent_service.get(session.agent_id)
        assistant_content = ""

        async for chunk in self._invoke_agent(agent, history):
            assistant_content += chunk
            yield chunk

        # 保存助手回覆
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=assistant_content
        )
        await self._repository.add_message(session_id, assistant_message)

        # 更新快取
        await self._cache.extend(session_id)

    async def _invoke_agent(
        self,
        agent: Agent,
        history: List[Message]
    ) -> AsyncIterator[str]:
        """調用 Agent 獲取回覆"""
        # 構建 LLM 請求
        messages = [
            {"role": m.role.value, "content": m.content}
            for m in history
        ]

        # 串流調用
        async for chunk in self._agent_service.stream_completion(
            agent_id=agent.id,
            messages=messages
        ):
            yield chunk

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
        before_id: Optional[str] = None
    ) -> List[Message]:
        """獲取訊息歷史"""
        return await self._repository.get_messages(
            session_id,
            limit=limit,
            before_id=before_id
        )

    async def cleanup_expired_sessions(self) -> int:
        """清理過期 Sessions"""
        count = await self._repository.cleanup_expired()
        return count
```

**驗收標準**:
- [ ] Session 創建/激活/結束正常
- [ ] 訊息發送和接收正常
- [ ] 串流回覆正常
- [ ] 事件發布正常
- [ ] 測試覆蓋率 > 85%

---

### S42-4: Session REST API (7 pts)

**描述**: 實現 Session 管理 REST API

**功能需求**:
1. Session CRUD 端點
2. Message 查詢端點
3. 文件上傳端點
4. 認證和授權

**技術設計**:

```python
# api/v1/sessions/routes.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Optional

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """創建新 Session"""
    session = await service.create_session(
        user_id=current_user.id,
        agent_id=request.agent_id,
        config=request.config
    )
    return SessionResponse.from_domain(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """獲取 Session"""
    session = await service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 權限檢查
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return SessionResponse.from_domain(session)


@router.delete("/{session_id}", status_code=204)
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """結束 Session"""
    session = await service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await service.end_session(session_id)


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """獲取訊息歷史"""
    session = await service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await service.get_messages(
        session_id,
        limit=limit,
        before_id=before_id
    )
    return [MessageResponse.from_domain(m) for m in messages]


@router.post("/{session_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    session_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    storage: AttachmentStorage = Depends(get_attachment_storage)
):
    """上傳附件"""
    session = await service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 驗證文件大小
    if file.size > session.config.max_attachment_size:
        raise HTTPException(status_code=413, detail="File too large")

    # 存儲文件
    attachment = await storage.store(session_id, file)

    return AttachmentResponse.from_domain(attachment)


@router.get("/{session_id}/attachments/{attachment_id}")
async def download_attachment(
    session_id: str,
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    storage: AttachmentStorage = Depends(get_attachment_storage)
):
    """下載附件"""
    attachment = await storage.get(session_id, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return FileResponse(
        attachment.storage_path,
        filename=attachment.filename,
        media_type=attachment.content_type
    )
```

```python
# api/v1/sessions/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CreateSessionRequest(BaseModel):
    """創建 Session 請求"""
    agent_id: str
    config: Optional[SessionConfigSchema] = None


class SessionConfigSchema(BaseModel):
    """Session 配置"""
    max_messages: int = Field(100, ge=10, le=1000)
    max_attachments: int = Field(10, ge=1, le=50)
    max_attachment_size: int = Field(10 * 1024 * 1024, ge=1024)
    timeout_minutes: int = Field(60, ge=5, le=1440)
    enable_code_interpreter: bool = True
    enable_mcp_tools: bool = True


class SessionResponse(BaseModel):
    """Session 響應"""
    id: str
    user_id: str
    agent_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]

    @classmethod
    def from_domain(cls, session: Session) -> "SessionResponse":
        return cls(
            id=session.id,
            user_id=session.user_id,
            agent_id=session.agent_id,
            status=session.status.value,
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at
        )


class MessageResponse(BaseModel):
    """Message 響應"""
    id: str
    role: str
    content: str
    attachments: List[AttachmentResponse] = []
    tool_calls: List[ToolCallResponse] = []
    created_at: datetime


class AttachmentResponse(BaseModel):
    """Attachment 響應"""
    id: str
    filename: str
    content_type: str
    size: int
    attachment_type: str
    uploaded_at: datetime
```

**驗收標準**:
- [ ] 所有 CRUD 端點正常
- [ ] 文件上傳/下載正常
- [ ] 認證和授權正確
- [ ] 錯誤處理完整
- [ ] API 文檔完整

---

## 技術規格

### 依賴套件

```bash
pip install websockets python-multipart aiofiles
```

### 文件結構

```
backend/src/
├── api/v1/sessions/
│   ├── __init__.py
│   ├── routes.py
│   └── schemas.py
│
├── domain/sessions/
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   ├── repository.py
│   ├── cache.py
│   └── events.py
│
└── infrastructure/
    ├── database/models/
    │   └── session.py
    └── storage/
        └── attachments.py
```

### 數據庫遷移

```sql
-- 創建 sessions 表
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(36) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'created',
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    ended_at TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- 創建 messages 表
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    attachments JSONB NOT NULL DEFAULT '[]',
    tool_calls JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- 創建 attachments 表
CREATE TABLE attachments (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id VARCHAR(36) REFERENCES messages(id),
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    attachment_type VARCHAR(50) NOT NULL,
    uploaded_at TIMESTAMP NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_attachments_session_id ON attachments(session_id);
```

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| Session 洩漏 | 中 | 高 | 定時清理任務 |
| 存儲空間不足 | 中 | 中 | 附件大小限制、TTL |
| 並發寫入衝突 | 低 | 中 | 樂觀鎖、事務 |

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
