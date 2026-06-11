# Sprint 44: Session Features

> **目標**: 完善 Session 功能，實現文件交互、歷史記錄和進階功能

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 44 |
| 總點數 | 30 Story Points |
| 預計時間 | 2 週 |
| 前置條件 | Sprint 43 完成 |
| 狀態 | 📋 計劃中 |

---

## Stories

### S44-1: 文件分析功能 (10 pts)

**描述**: 實現在 Session 中上傳文件並讓 Agent 分析

**功能需求**:
1. 多格式文件支援
2. 文件內容提取
3. 與對話上下文整合
4. 使用 Code Interpreter 分析

**技術設計**:

```python
# domain/sessions/file_analyzer.py

from typing import List, Dict, Any, Optional
from pathlib import Path
import mimetypes

from .models import Attachment, AttachmentType
from ...integrations.agent_framework.assistant.code_interpreter import CodeInterpreterTool

class FileAnalyzer:
    """文件分析器"""

    SUPPORTED_TYPES = {
        AttachmentType.IMAGE: [".png", ".jpg", ".jpeg", ".gif", ".webp"],
        AttachmentType.DOCUMENT: [".pdf", ".docx", ".doc", ".txt", ".md"],
        AttachmentType.CODE: [".py", ".js", ".ts", ".java", ".go", ".rs"],
        AttachmentType.DATA: [".csv", ".json", ".xml", ".xlsx", ".xls"],
    }

    def __init__(self, code_interpreter: CodeInterpreterTool):
        self._code_interpreter = code_interpreter

    async def analyze(
        self,
        attachment: Attachment,
        analysis_request: str = None
    ) -> Dict[str, Any]:
        """
        分析文件

        Args:
            attachment: 附件對象
            analysis_request: 分析請求描述

        Returns:
            分析結果
        """
        # 1. 根據類型選擇分析方法
        if attachment.attachment_type == AttachmentType.IMAGE:
            return await self._analyze_image(attachment, analysis_request)
        elif attachment.attachment_type == AttachmentType.DOCUMENT:
            return await self._analyze_document(attachment, analysis_request)
        elif attachment.attachment_type == AttachmentType.CODE:
            return await self._analyze_code(attachment, analysis_request)
        elif attachment.attachment_type == AttachmentType.DATA:
            return await self._analyze_data(attachment, analysis_request)
        else:
            return await self._analyze_generic(attachment, analysis_request)

    async def _analyze_image(
        self,
        attachment: Attachment,
        request: str
    ) -> Dict[str, Any]:
        """分析圖片"""
        # 使用多模態 LLM 分析圖片
        return {
            "type": "image_analysis",
            "description": "Image analysis result",
            "details": {}
        }

    async def _analyze_document(
        self,
        attachment: Attachment,
        request: str
    ) -> Dict[str, Any]:
        """分析文檔"""
        # 提取文本
        content = await self._extract_text(attachment)

        # 使用 Code Interpreter 或 LLM 分析
        if request:
            result = await self._code_interpreter.execute(
                code=f'''
# 分析文檔內容
content = """{content[:5000]}"""

# 根據請求進行分析
analysis_request = "{request}"
# ... 分析邏輯
'''
            )
            return {
                "type": "document_analysis",
                "content_preview": content[:500],
                "analysis": result
            }

        return {
            "type": "document_analysis",
            "content_preview": content[:500],
            "word_count": len(content.split()),
            "char_count": len(content)
        }

    async def _analyze_data(
        self,
        attachment: Attachment,
        request: str
    ) -> Dict[str, Any]:
        """分析數據文件"""
        # 使用 Code Interpreter 分析
        code = f'''
import pandas as pd

# 讀取數據
df = pd.read_csv("{attachment.storage_path}")

# 基本統計
summary = {{
    "shape": df.shape,
    "columns": list(df.columns),
    "dtypes": df.dtypes.to_dict(),
    "describe": df.describe().to_dict()
}}

summary
'''
        result = await self._code_interpreter.execute(code=code)

        return {
            "type": "data_analysis",
            "result": result
        }

    async def _analyze_code(
        self,
        attachment: Attachment,
        request: str
    ) -> Dict[str, Any]:
        """分析代碼文件"""
        content = await self._read_file(attachment.storage_path)

        return {
            "type": "code_analysis",
            "language": self._detect_language(attachment.filename),
            "lines": len(content.split("\n")),
            "content_preview": content[:1000]
        }

    async def _extract_text(self, attachment: Attachment) -> str:
        """提取文本內容"""
        ext = Path(attachment.filename).suffix.lower()

        if ext == ".pdf":
            return await self._extract_pdf_text(attachment.storage_path)
        elif ext in [".docx", ".doc"]:
            return await self._extract_docx_text(attachment.storage_path)
        elif ext in [".txt", ".md"]:
            return await self._read_file(attachment.storage_path)
        else:
            return ""

    async def _read_file(self, path: str) -> str:
        """讀取文件"""
        import aiofiles
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()

    @staticmethod
    def _detect_language(filename: str) -> str:
        """檢測程式語言"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
        }
        ext = Path(filename).suffix.lower()
        return ext_map.get(ext, "unknown")
```

**驗收標準**:
- [ ] 支援多種文件格式
- [ ] 文件內容正確提取
- [ ] 與 Code Interpreter 整合
- [ ] 分析結果正確返回
- [ ] 測試覆蓋率 > 85%

---

### S44-2: 文件生成功能 (8 pts)

**描述**: 實現讓 Agent 生成文件並提供下載

**功能需求**:
1. 代碼文件生成
2. 報告文件生成
3. 數據文件導出
4. 下載連結管理

**技術設計**:

```python
# domain/sessions/file_generator.py

from typing import Optional
import uuid
from pathlib import Path
from datetime import datetime, timedelta

from .models import Attachment, AttachmentType
from ...infrastructure.storage.attachments import AttachmentStorage

class FileGenerator:
    """文件生成器"""

    def __init__(
        self,
        storage: AttachmentStorage,
        download_url_prefix: str = "/api/v1/downloads"
    ):
        self._storage = storage
        self._url_prefix = download_url_prefix

    async def generate_file(
        self,
        session_id: str,
        content: str,
        filename: str,
        content_type: str = "text/plain"
    ) -> Attachment:
        """
        生成文件

        Returns:
            Attachment: 生成的附件對象
        """
        # 1. 創建附件
        attachment = Attachment(
            filename=filename,
            content_type=content_type,
            size=len(content.encode("utf-8")),
            attachment_type=self._detect_type(filename)
        )

        # 2. 存儲內容
        storage_path = await self._storage.store_content(
            session_id=session_id,
            attachment_id=attachment.id,
            content=content,
            filename=filename
        )
        attachment.storage_path = storage_path

        return attachment

    async def generate_code_file(
        self,
        session_id: str,
        code: str,
        filename: str,
        language: str = "python"
    ) -> Attachment:
        """生成代碼文件"""
        content_type = self._get_code_content_type(language)
        return await self.generate_file(
            session_id=session_id,
            content=code,
            filename=filename,
            content_type=content_type
        )

    async def generate_report(
        self,
        session_id: str,
        title: str,
        content: str,
        format: str = "md"
    ) -> Attachment:
        """生成報告文件"""
        filename = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.{format}"

        if format == "md":
            content_type = "text/markdown"
        elif format == "html":
            content_type = "text/html"
        else:
            content_type = "text/plain"

        return await self.generate_file(
            session_id=session_id,
            content=content,
            filename=filename,
            content_type=content_type
        )

    async def generate_data_export(
        self,
        session_id: str,
        data: list,
        filename: str,
        format: str = "csv"
    ) -> Attachment:
        """生成數據導出文件"""
        import json
        import csv
        from io import StringIO

        if format == "json":
            content = json.dumps(data, indent=2, ensure_ascii=False)
            content_type = "application/json"
        elif format == "csv":
            if data and isinstance(data[0], dict):
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                content = output.getvalue()
            else:
                content = "\n".join([",".join(map(str, row)) for row in data])
            content_type = "text/csv"
        else:
            content = str(data)
            content_type = "text/plain"

        return await self.generate_file(
            session_id=session_id,
            content=content,
            filename=filename,
            content_type=content_type
        )

    def get_download_url(
        self,
        session_id: str,
        attachment_id: str,
        expires_in: int = 3600
    ) -> str:
        """
        獲取下載 URL

        Args:
            expires_in: 過期時間 (秒)

        Returns:
            下載 URL
        """
        # 生成帶簽名的下載 URL
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        token = self._generate_download_token(
            session_id=session_id,
            attachment_id=attachment_id,
            expires_at=expires_at
        )

        return f"{self._url_prefix}/{attachment_id}?token={token}"

    def _detect_type(self, filename: str) -> AttachmentType:
        """檢測文件類型"""
        ext = Path(filename).suffix.lower()
        if ext in [".py", ".js", ".ts", ".java"]:
            return AttachmentType.CODE
        elif ext in [".csv", ".json", ".xml"]:
            return AttachmentType.DATA
        elif ext in [".md", ".txt", ".html"]:
            return AttachmentType.DOCUMENT
        else:
            return AttachmentType.OTHER

    @staticmethod
    def _get_code_content_type(language: str) -> str:
        """獲取代碼內容類型"""
        type_map = {
            "python": "text/x-python",
            "javascript": "application/javascript",
            "typescript": "application/typescript",
            "java": "text/x-java",
        }
        return type_map.get(language, "text/plain")
```

**驗收標準**:
- [ ] 代碼文件生成正常
- [ ] 報告文件生成正常
- [ ] 數據導出正常
- [ ] 下載 URL 有效
- [ ] 測試覆蓋率 > 85%

---

### S44-3: 對話歷史管理 (7 pts)

**描述**: 實現對話歷史的高級管理功能

**功能需求**:
1. 歷史搜索
2. 書籤/收藏
3. 對話導出
4. 上下文摘要

**技術設計**:

```python
# domain/sessions/history_manager.py

from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Session, Message
from .repository import SessionRepository

class HistoryManager:
    """對話歷史管理器"""

    def __init__(self, repository: SessionRepository):
        self._repository = repository

    async def search_messages(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索訊息

        Args:
            user_id: 用戶 ID
            query: 搜索關鍵字
            session_id: 限定 Session (可選)
            limit: 返回數量限制

        Returns:
            匹配的訊息列表
        """
        return await self._repository.search_messages(
            user_id=user_id,
            query=query,
            session_id=session_id,
            limit=limit
        )

    async def add_bookmark(
        self,
        session_id: str,
        message_id: str,
        note: str = ""
    ) -> Dict[str, Any]:
        """添加書籤"""
        return await self._repository.add_bookmark(
            session_id=session_id,
            message_id=message_id,
            note=note
        )

    async def remove_bookmark(
        self,
        session_id: str,
        message_id: str
    ) -> bool:
        """移除書籤"""
        return await self._repository.remove_bookmark(
            session_id=session_id,
            message_id=message_id
        )

    async def list_bookmarks(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出書籤"""
        return await self._repository.list_bookmarks(
            user_id=user_id,
            session_id=session_id
        )

    async def export_conversation(
        self,
        session_id: str,
        format: str = "json"
    ) -> str:
        """
        導出對話

        Args:
            format: 導出格式 (json, markdown, txt)

        Returns:
            導出內容
        """
        messages = await self._repository.get_messages(session_id, limit=1000)

        if format == "json":
            return self._export_as_json(messages)
        elif format == "markdown":
            return self._export_as_markdown(messages)
        else:
            return self._export_as_text(messages)

    async def generate_summary(
        self,
        session_id: str,
        max_messages: int = 50
    ) -> str:
        """
        生成對話摘要

        Uses LLM to summarize the conversation.
        """
        messages = await self._repository.get_messages(session_id, limit=max_messages)

        # 使用 LLM 生成摘要
        summary_prompt = self._build_summary_prompt(messages)
        # ... 調用 LLM

        return "Conversation summary..."

    def _export_as_json(self, messages: List[Message]) -> str:
        """導出為 JSON"""
        import json
        data = [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _export_as_markdown(self, messages: List[Message]) -> str:
        """導出為 Markdown"""
        lines = ["# Conversation Export\n"]
        for m in messages:
            role = m.role.value.upper()
            time = m.created_at.strftime("%Y-%m-%d %H:%M")
            lines.append(f"## {role} ({time})\n")
            lines.append(f"{m.content}\n")
        return "\n".join(lines)

    def _export_as_text(self, messages: List[Message]) -> str:
        """導出為純文本"""
        lines = []
        for m in messages:
            role = m.role.value.upper()
            lines.append(f"[{role}]: {m.content}")
        return "\n\n".join(lines)
```

**驗收標準**:
- [ ] 歷史搜索正常
- [ ] 書籤功能正常
- [ ] 導出格式正確
- [ ] 摘要生成有用
- [ ] 測試覆蓋率 > 85%

---

### S44-4: Session 進階功能 (5 pts)

**描述**: 實現 Session 的進階功能

**功能需求**:
1. Session 克隆/分支
2. Session 標籤
3. Session 統計
4. 使用量追蹤

**技術設計**:

```python
# domain/sessions/advanced.py

from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import Session, SessionConfig
from .service import SessionService
from .repository import SessionRepository

class AdvancedSessionFeatures:
    """進階 Session 功能"""

    def __init__(
        self,
        service: SessionService,
        repository: SessionRepository
    ):
        self._service = service
        self._repository = repository

    async def clone_session(
        self,
        session_id: str,
        include_messages: bool = True,
        message_limit: int = 50
    ) -> Session:
        """
        克隆 Session

        Args:
            session_id: 原始 Session ID
            include_messages: 是否包含訊息
            message_limit: 訊息數量限制

        Returns:
            新的 Session
        """
        original = await self._service.get_session(session_id)
        if original is None:
            raise ValueError(f"Session not found: {session_id}")

        # 創建新 Session
        new_session = await self._service.create_session(
            user_id=original.user_id,
            agent_id=original.agent_id,
            config=original.config
        )

        # 複製訊息
        if include_messages:
            messages = await self._repository.get_messages(
                session_id,
                limit=message_limit
            )
            for msg in messages:
                msg.id = None  # 重置 ID
                msg.session_id = new_session.id
                await self._repository.add_message(new_session.id, msg)

        return new_session

    async def add_tags(
        self,
        session_id: str,
        tags: List[str]
    ) -> Session:
        """添加標籤"""
        session = await self._service.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        existing_tags = session.metadata.get("tags", [])
        session.metadata["tags"] = list(set(existing_tags + tags))

        await self._repository.update(session)
        return session

    async def remove_tags(
        self,
        session_id: str,
        tags: List[str]
    ) -> Session:
        """移除標籤"""
        session = await self._service.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        existing_tags = session.metadata.get("tags", [])
        session.metadata["tags"] = [t for t in existing_tags if t not in tags]

        await self._repository.update(session)
        return session

    async def get_session_stats(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """獲取 Session 統計"""
        session = await self._service.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        messages = await self._repository.get_messages(session_id, limit=1000)

        # 計算統計
        user_messages = [m for m in messages if m.role.value == "user"]
        assistant_messages = [m for m in messages if m.role.value == "assistant"]

        return {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "duration_minutes": (
                (session.ended_at or datetime.utcnow()) - session.created_at
            ).total_seconds() / 60,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "total_tokens": sum(
                len(m.content.split()) * 1.3  # 粗略估計
                for m in messages
            ),
            "attachments_count": sum(len(m.attachments) for m in messages),
            "tool_calls_count": sum(len(m.tool_calls) for m in messages),
        }

    async def get_usage_summary(
        self,
        user_id: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """獲取使用量摘要"""
        sessions = await self._repository.list_by_user(
            user_id=user_id,
            limit=1000
        )

        # 過濾日期
        if start_date:
            sessions = [s for s in sessions if s.created_at >= start_date]
        if end_date:
            sessions = [s for s in sessions if s.created_at <= end_date]

        return {
            "user_id": user_id,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s.status.value == "active"]),
            "agents_used": list(set(s.agent_id for s in sessions)),
        }
```

**驗收標準**:
- [ ] Session 克隆正常
- [ ] 標籤管理正常
- [ ] 統計數據準確
- [ ] 使用量追蹤正常
- [ ] 測試覆蓋率 > 85%

---

## 技術規格

### 文件結構

```
backend/src/domain/sessions/
├── file_analyzer.py    # 文件分析
├── file_generator.py   # 文件生成
├── history_manager.py  # 歷史管理
└── advanced.py         # 進階功能
```

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| 大文件分析效能 | 中 | 中 | 分塊處理、背景任務 |
| 存儲空間不足 | 中 | 中 | 清理策略、配額限制 |
| 導出數據量過大 | 低 | 中 | 分頁導出、壓縮 |

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
