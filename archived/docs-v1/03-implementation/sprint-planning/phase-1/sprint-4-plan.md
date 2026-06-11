# Sprint 4: 開發者體驗

**Sprint 目標**: 建立 Agent 模板市場和開發者工具，提升開發效率
**週期**: Week 9-10 (2 週)
**Story Points**: 38 點
**MVP 功能**: F5 (學習型協作), F6 (Agent 模板市場), F7 (DevUI 整合)

---

## Sprint 概覽

### 目標
1. 建立 Agent 模板市場 (6-8 個模板)
2. 實現 Few-shot Learning 機制
3. 整合 DevUI 可視化調試工具
4. 建立模板版本管理
5. 提供完整開發者文檔

### 成功標準
- [ ] 6+ 個可用的 Agent 模板
- [ ] 模板可一鍵部署為 Agent
- [ ] Few-shot 學習可提升 Agent 準確率
- [ ] DevUI 可追蹤 Agent 執行流程
- [ ] 開發者文檔完整

---

## 系統架構

### Agent 模板市場架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Template Marketplace                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Template Registry                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │   │
│  │  │IT Triage │ │CS Helper │ │Escalation│ │ Report   │     │   │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │ Agent    │     │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │   │
│  │  │Knowledge │ │Approval  │ │Monitoring│ │ Custom   │     │   │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │ Template │     │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │  Template Engine  │                        │
│                    │  ├─ Parse         │                        │
│                    │  ├─ Validate      │                        │
│                    │  └─ Instantiate   │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Agent Runtime   │                        │
│                    │   (Agent Framework)│                       │
│                    └───────────────────┘                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Stories

### S4-1: Agent 模板市場 (13 點)

**描述**: 作為開發者，我需要一個模板市場來快速創建常用 Agent。

**驗收標準**:
- [ ] 6+ 個預置模板可用
- [ ] 模板支持分類和搜索
- [ ] 模板可一鍵實例化
- [ ] 支持自定義參數配置

**技術任務**:

1. **模板數據模型 (src/domain/templates/models.py)**
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from uuid import UUID
from enum import Enum


class TemplateCategory(str, Enum):
    IT_OPERATIONS = "it_operations"
    CUSTOMER_SERVICE = "customer_service"
    MONITORING = "monitoring"
    APPROVAL = "approval"
    REPORTING = "reporting"
    CUSTOM = "custom"


@dataclass
class TemplateParameter:
    """模板參數定義"""
    name: str
    type: str  # "string", "number", "boolean", "list", "object"
    description: str
    required: bool = True
    default: Any = None
    options: List[Any] = None  # 可選值列表


@dataclass
class AgentTemplate:
    """Agent 模板"""
    id: str
    name: str
    description: str
    category: TemplateCategory
    version: str
    author: str

    # Agent 配置
    instructions: str
    tools: List[str]  # 工具 ID 列表

    # 參數配置
    parameters: List[TemplateParameter] = field(default_factory=list)

    # 元數據
    usage_count: int = 0
    rating: float = 0.0
    tags: List[str] = field(default_factory=list)

    # 示例
    examples: List[Dict[str, Any]] = field(default_factory=list)
```

2. **預置模板定義 (templates/it_triage_agent.yaml)**
```yaml
id: it_triage_agent
name: IT 工單分類 Agent
description: 自動分類和優先級排序 IT 工單
category: it_operations
version: "1.0.0"
author: IPA Team

instructions: |
  你是一個 IT 運維專家，專門負責分類和評估 IT 工單。

  對於每個工單，你需要：
  1. 識別問題類型 (硬體/軟體/網路/安全/存取權限)
  2. 評估優先級 (P1-P4)
  3. 推薦處理團隊
  4. 估算解決時間

  優先級定義：
  - P1: 業務中斷，影響 >100 用戶
  - P2: 嚴重影響，影響 10-100 用戶
  - P3: 中等影響，影響 1-10 用戶
  - P4: 低影響，單用戶問題

  請以 JSON 格式回覆。

tools:
  - servicenow_get_incident
  - servicenow_search_similar
  - knowledge_base_search

parameters:
  - name: confidence_threshold
    type: number
    description: 分類置信度閾值
    required: false
    default: 0.8

  - name: auto_assign
    type: boolean
    description: 是否自動分配團隊
    required: false
    default: false

examples:
  - input: "無法登入 VPN，已嘗試重啟電腦"
    output:
      type: "網路"
      priority: "P3"
      team: "網路運維"
      estimated_time: "2小時"

tags:
  - it
  - triage
  - classification
```

3. **模板服務 (src/domain/templates/service.py)**
```python
from typing import List, Optional, Dict, Any
from pathlib import Path
import yaml

from .models import AgentTemplate, TemplateCategory
from src.domain.agents.service import AgentService, AgentConfig


class TemplateService:
    """Agent 模板服務"""

    def __init__(self, templates_dir: Path, agent_service: AgentService):
        self._templates_dir = templates_dir
        self._agent_service = agent_service
        self._templates: Dict[str, AgentTemplate] = {}

    def load_templates(self) -> None:
        """加載所有模板"""
        for yaml_file in self._templates_dir.glob("*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                template = self._parse_template(data)
                self._templates[template.id] = template

    def _parse_template(self, data: Dict) -> AgentTemplate:
        """解析模板數據"""
        return AgentTemplate(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=TemplateCategory(data["category"]),
            version=data["version"],
            author=data["author"],
            instructions=data["instructions"],
            tools=data.get("tools", []),
            parameters=[
                TemplateParameter(**p) for p in data.get("parameters", [])
            ],
            examples=data.get("examples", []),
            tags=data.get("tags", []),
        )

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        search: Optional[str] = None,
    ) -> List[AgentTemplate]:
        """列出模板"""
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.name.lower()
                or search_lower in t.description.lower()
                or any(search_lower in tag for tag in t.tags)
            ]

        return sorted(templates, key=lambda t: t.usage_count, reverse=True)

    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """獲取模板"""
        return self._templates.get(template_id)

    async def instantiate(
        self,
        template_id: str,
        name: str,
        parameters: Dict[str, Any],
    ) -> UUID:
        """實例化模板為 Agent"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # 驗證參數
        self._validate_parameters(template, parameters)

        # 創建 Agent
        config = AgentConfig(
            name=name,
            instructions=self._apply_parameters(template.instructions, parameters),
            tools=template.tools,
        )

        agent_id = await self._agent_service.create_agent(config)

        # 更新使用計數
        template.usage_count += 1

        return agent_id

    def _validate_parameters(
        self,
        template: AgentTemplate,
        parameters: Dict[str, Any],
    ) -> None:
        """驗證參數"""
        for param in template.parameters:
            if param.required and param.name not in parameters:
                if param.default is None:
                    raise ValueError(f"Missing required parameter: {param.name}")

    def _apply_parameters(
        self,
        instructions: str,
        parameters: Dict[str, Any],
    ) -> str:
        """應用參數到指令"""
        from string import Template
        t = Template(instructions)
        return t.safe_substitute(parameters)
```

4. **模板 API (src/api/v1/templates/routes.py)**
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.domain.templates.service import TemplateService
from src.domain.templates.models import TemplateCategory


router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    version: str
    author: str
    parameters: List[dict]
    usage_count: int
    rating: float
    tags: List[str]


class InstantiateRequest(BaseModel):
    name: str
    parameters: Dict[str, Any] = {}


class InstantiateResponse(BaseModel):
    agent_id: UUID


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    service: TemplateService = Depends(),
):
    """列出 Agent 模板"""
    cat = TemplateCategory(category) if category else None
    templates = service.list_templates(category=cat, search=search)

    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category.value,
            version=t.version,
            author=t.author,
            parameters=[vars(p) for p in t.parameters],
            usage_count=t.usage_count,
            rating=t.rating,
            tags=t.tags,
        )
        for t in templates
    ]


@router.post("/{template_id}/instantiate", response_model=InstantiateResponse)
async def instantiate_template(
    template_id: str,
    request: InstantiateRequest,
    service: TemplateService = Depends(),
):
    """實例化模板為 Agent"""
    try:
        agent_id = await service.instantiate(
            template_id=template_id,
            name=request.name,
            parameters=request.parameters,
        )
        return InstantiateResponse(agent_id=agent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

### S4-2: Few-shot 學習機制 (10 點)

**描述**: 作為業務用戶，我希望 Agent 可以從人工修正中學習改進。

**驗收標準**:
- [ ] 人工修正可記錄為學習案例
- [ ] 學習案例可用於改進 Agent 響應
- [ ] 支持案例審核和管理
- [ ] 學習效果可量化

**技術任務**:

1. **學習案例服務 (src/domain/learning/service.py)**
```python
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class LearningCase:
    """學習案例"""
    id: UUID
    execution_id: UUID
    scenario: str
    original_input: str
    original_output: str
    corrected_output: str
    feedback: str
    approved: bool
    created_at: datetime


class LearningService:
    """Few-shot 學習服務"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def record_correction(
        self,
        execution_id: UUID,
        scenario: str,
        original_input: str,
        original_output: str,
        corrected_output: str,
        feedback: str,
    ) -> UUID:
        """記錄人工修正"""
        from src.infrastructure.database.models import LearningCaseModel

        case = LearningCaseModel(
            id=uuid4(),
            execution_id=execution_id,
            scenario=scenario,
            original_input=original_input,
            original_output=original_output,
            corrected_output=corrected_output,
            feedback=feedback,
            approved=False,
            created_at=datetime.utcnow(),
        )

        self._session.add(case)
        await self._session.commit()

        return case.id

    async def get_similar_cases(
        self,
        scenario: str,
        input_text: str,
        limit: int = 5,
    ) -> List[LearningCase]:
        """獲取相似的學習案例 (用於 Few-shot)"""
        from sqlalchemy import select, text
        from src.infrastructure.database.models import LearningCaseModel

        # 使用 pg_trgm 進行相似度搜索
        query = select(LearningCaseModel).where(
            LearningCaseModel.scenario == scenario,
            LearningCaseModel.approved == True,
        ).order_by(
            text(f"similarity(original_input, :input_text) DESC")
        ).limit(limit)

        result = await self._session.execute(
            query,
            {"input_text": input_text},
        )

        return [
            LearningCase(
                id=row.id,
                execution_id=row.execution_id,
                scenario=row.scenario,
                original_input=row.original_input,
                original_output=row.original_output,
                corrected_output=row.corrected_output,
                feedback=row.feedback,
                approved=row.approved,
                created_at=row.created_at,
            )
            for row in result.scalars()
        ]

    def build_few_shot_prompt(
        self,
        base_prompt: str,
        cases: List[LearningCase],
    ) -> str:
        """構建 Few-shot Prompt"""
        examples = []
        for case in cases:
            examples.append(
                f"Input: {case.original_input}\n"
                f"Correct Output: {case.corrected_output}"
            )

        examples_text = "\n\n".join(examples)

        return f"""{base_prompt}

Here are some examples of correct responses:

{examples_text}

Now, please respond to the following input:"""

    async def approve_case(self, case_id: UUID) -> None:
        """審核通過學習案例"""
        from src.infrastructure.database.models import LearningCaseModel

        case = await self._session.get(LearningCaseModel, case_id)
        if case:
            case.approved = True
            await self._session.commit()
```

---

### S4-3: DevUI 可視化調試 (10 點)

**描述**: 作為開發者，我需要可視化工具來調試 Agent 執行流程。

**驗收標準**:
- [ ] 可追蹤 Agent 執行步驟
- [ ] 可查看每步的輸入輸出
- [ ] 可查看 LLM 調用詳情
- [ ] 支持執行回放

**技術任務**:

1. **執行追蹤服務 (src/domain/devtools/tracer.py)**
```python
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class TraceEventType(str, Enum):
    WORKFLOW_START = "workflow.start"
    WORKFLOW_END = "workflow.end"
    EXECUTOR_START = "executor.start"
    EXECUTOR_END = "executor.end"
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    TOOL_CALL = "tool.call"
    TOOL_RESULT = "tool.result"
    CHECKPOINT = "checkpoint"
    ERROR = "error"


@dataclass
class TraceEvent:
    """追蹤事件"""
    id: UUID
    execution_id: UUID
    timestamp: datetime
    event_type: TraceEventType
    executor_id: Optional[str]
    data: Dict[str, Any]
    duration_ms: Optional[int]


class ExecutionTracer:
    """執行追蹤器"""

    def __init__(self):
        self._events: Dict[UUID, List[TraceEvent]] = {}

    def start_trace(self, execution_id: UUID) -> None:
        """開始追蹤"""
        self._events[execution_id] = []

    def add_event(
        self,
        execution_id: UUID,
        event_type: TraceEventType,
        data: Dict[str, Any],
        executor_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """添加追蹤事件"""
        from uuid import uuid4

        event = TraceEvent(
            id=uuid4(),
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            executor_id=executor_id,
            data=data,
            duration_ms=duration_ms,
        )

        if execution_id in self._events:
            self._events[execution_id].append(event)

    def get_trace(self, execution_id: UUID) -> List[TraceEvent]:
        """獲取追蹤事件"""
        return self._events.get(execution_id, [])

    def get_timeline(self, execution_id: UUID) -> Dict[str, Any]:
        """獲取執行時間線"""
        events = self.get_trace(execution_id)

        return {
            "execution_id": str(execution_id),
            "total_events": len(events),
            "events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type.value,
                    "executor": e.executor_id,
                    "duration_ms": e.duration_ms,
                    "data_summary": self._summarize_data(e.data),
                }
                for e in events
            ],
        }

    def _summarize_data(self, data: Dict) -> str:
        """摘要數據"""
        if "prompt" in data:
            return f"Prompt: {data['prompt'][:100]}..."
        if "response" in data:
            return f"Response: {data['response'][:100]}..."
        if "error" in data:
            return f"Error: {data['error']}"
        return str(data)[:100]
```

2. **DevUI API (src/api/v1/devtools/routes.py)**
```python
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from typing import List
from uuid import UUID

from src.domain.devtools.tracer import ExecutionTracer, TraceEvent


router = APIRouter(prefix="/devtools", tags=["devtools"])


@router.get("/executions/{execution_id}/trace")
async def get_execution_trace(
    execution_id: UUID,
    tracer: ExecutionTracer = Depends(),
):
    """獲取執行追蹤"""
    events = tracer.get_trace(execution_id)
    return {
        "execution_id": str(execution_id),
        "events": [
            {
                "id": str(e.id),
                "timestamp": e.timestamp.isoformat(),
                "type": e.event_type.value,
                "executor_id": e.executor_id,
                "data": e.data,
                "duration_ms": e.duration_ms,
            }
            for e in events
        ],
    }


@router.get("/executions/{execution_id}/timeline")
async def get_execution_timeline(
    execution_id: UUID,
    tracer: ExecutionTracer = Depends(),
):
    """獲取執行時間線"""
    return tracer.get_timeline(execution_id)


@router.websocket("/executions/{execution_id}/stream")
async def stream_execution(
    websocket: WebSocket,
    execution_id: UUID,
    tracer: ExecutionTracer = Depends(),
):
    """實時流式追蹤執行"""
    await websocket.accept()

    try:
        # TODO: 實現實時事件推送
        while True:
            data = await websocket.receive_text()
            # 處理客戶端消息
    except WebSocketDisconnect:
        pass
```

---

### S4-4: 模板版本管理 (5 點)

**描述**: 作為開發者，我需要管理模板的不同版本。

**驗收標準**:
- [ ] 模板支持版本號
- [ ] 可查看版本歷史
- [ ] 可回滾到舊版本
- [ ] 新版本發布有審核流程

---

## 預置模板清單

| 模板 ID | 名稱 | 類別 | 描述 |
|---------|------|------|------|
| it_triage_agent | IT 工單分類 | IT Operations | 自動分類 IT 工單優先級 |
| cs_helper_agent | 客服助手 | Customer Service | 處理客戶查詢和投訴 |
| escalation_agent | 升級處理 | Approval | 處理工單升級流程 |
| report_agent | 報告生成 | Reporting | 生成執行報告和摘要 |
| knowledge_agent | 知識查詢 | IT Operations | 搜索和返回知識庫內容 |
| monitoring_agent | 監控告警 | Monitoring | 處理監控告警事件 |

---

## 時間規劃

### Week 9 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S4-1: 模板數據模型 | Backend | models.py |
| Day 2-3 | S4-1: 預置模板定義 | Backend | 6 個 YAML |
| Day 3-4 | S4-1: 模板服務 | Backend | service.py |
| Day 4-5 | S4-1: 模板 API | Backend | routes.py |

### Week 10 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S4-2: Few-shot 學習服務 | Backend | learning/service.py |
| Day 7-8 | S4-3: DevUI 追蹤服務 | Backend | tracer.py |
| Day 8-9 | S4-3: DevUI API | Backend | devtools/routes.py |
| Day 9-10 | S4-4: 版本管理 + 測試 | 全員 | 測試用例 |

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] 6+ 個模板可用
   - [ ] 模板實例化正常
   - [ ] Few-shot 學習可用
   - [ ] DevUI 追蹤可用

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 模板集成測試通過

3. **文檔完成**
   - [ ] 模板開發指南
   - [ ] DevUI 使用指南

---

## 相關文檔

- [Sprint 4 Checklist](./sprint-4-checklist.md)
- [Sprint 3 Plan](./sprint-3-plan.md) - 前置 Sprint
- [Sprint 5 Plan](./sprint-5-plan.md) - 後續 Sprint
