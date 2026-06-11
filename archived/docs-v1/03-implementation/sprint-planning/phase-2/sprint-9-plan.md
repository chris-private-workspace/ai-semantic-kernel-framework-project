# Sprint 9: 群組協作模式 (GroupChat & Multi-turn Conversation)

**Sprint 目標**: 實現多 Agent 群組聊天和多輪對話能力，支援複雜協作場景

**週期**: Week 19-20 (2 週)
**Story Points**: 42 點
**前置條件**: Sprint 7 (Concurrent) + Sprint 8 (Handoff) 完成

---

## Sprint 概述

### 核心交付物

| ID | 功能 | 優先級 | Story Points | 狀態 |
|----|------|--------|--------------|------|
| P2-F5 | GroupChat 群組聊天 | 🟡 中 | 21 | 待開發 |
| P2-F6 | Multi-turn Conversation 多輪對話 | 🟡 中 | 13 | 待開發 |
| P2-F7 | Conversation Memory 對話記憶 | 🟡 中 | 8 | 待開發 |

### 與 Microsoft Agent Framework 對照

```python
# Microsoft Agent Framework GroupChat API
from autogen import GroupChat, GroupChatManager

# 建立群組聊天
group_chat = GroupChat(
    agents=[agent1, agent2, agent3],
    messages=[],
    max_round=10,
    speaker_selection_method="auto"  # auto, manual, random, round_robin
)

# 管理群組聊天
manager = GroupChatManager(groupchat=group_chat, llm_config=llm_config)

# 發起對話
user_proxy.initiate_chat(manager, message="協作完成這個任務...")
```

---

## User Stories

### Story 9-1: GroupChat Manager 基礎架構 (8 點)

**作為** 系統架構師
**我希望** 建立群組聊天管理器
**以便** 多個 Agent 可以在同一個對話中協作

#### 技術規格

```python
# backend/src/domain/orchestration/groupchat/manager.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import asyncio
from uuid import UUID, uuid4

class SpeakerSelectionMethod(str, Enum):
    """發言者選擇策略"""
    AUTO = "auto"           # LLM 自動選擇下一位發言者
    ROUND_ROBIN = "round_robin"  # 輪流發言
    RANDOM = "random"       # 隨機選擇
    MANUAL = "manual"       # 人工指定
    PRIORITY = "priority"   # 按優先級選擇
    EXPERTISE = "expertise" # 按專業能力選擇


class MessageType(str, Enum):
    """訊息類型"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"


@dataclass
class GroupMessage:
    """群組訊息"""
    id: UUID
    group_id: UUID
    sender_id: str  # agent_id 或 "user" 或 "system"
    sender_name: str
    content: str
    message_type: MessageType
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "group_id": str(self.group_id),
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "reply_to": str(self.reply_to) if self.reply_to else None
        }


@dataclass
class GroupChatConfig:
    """群組聊天配置"""
    max_rounds: int = 10
    max_messages_per_round: int = 5
    speaker_selection_method: SpeakerSelectionMethod = SpeakerSelectionMethod.AUTO
    allow_repeat_speaker: bool = True
    termination_conditions: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    enable_voting: bool = False
    consensus_threshold: float = 0.7


@dataclass
class GroupChatState:
    """群組聊天狀態"""
    group_id: UUID
    current_round: int = 0
    messages: List[GroupMessage] = field(default_factory=list)
    active_agents: List[str] = field(default_factory=list)
    current_speaker: Optional[str] = None
    is_terminated: bool = False
    termination_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class GroupChatManager:
    """
    群組聊天管理器

    負責協調多個 Agent 在群組中的對話，包括：
    - 發言者選擇
    - 訊息路由
    - 輪次管理
    - 終止條件檢測
    """

    def __init__(
        self,
        group_id: UUID,
        agents: List[Any],  # List of Agent instances
        config: GroupChatConfig,
        llm_service: Any,
        memory_store: "ConversationMemoryStore"
    ):
        self.group_id = group_id
        self.agents = {agent.id: agent for agent in agents}
        self.agent_list = agents
        self.config = config
        self.llm_service = llm_service
        self.memory_store = memory_store

        self.state = GroupChatState(
            group_id=group_id,
            active_agents=[agent.id for agent in agents]
        )

        self._speaker_selector = self._create_speaker_selector()
        self._termination_checker = TerminationChecker(config.termination_conditions)
        self._round_robin_index = 0

    def _create_speaker_selector(self) -> "SpeakerSelector":
        """建立發言者選擇器"""
        return SpeakerSelector(
            method=self.config.speaker_selection_method,
            agents=self.agent_list,
            llm_service=self.llm_service
        )

    async def start_conversation(
        self,
        initial_message: str,
        initiator: str = "user"
    ) -> GroupChatState:
        """
        開始群組對話

        Args:
            initial_message: 初始訊息
            initiator: 發起者 ID

        Returns:
            最終的群組聊天狀態
        """
        self.state.started_at = datetime.utcnow()

        # 添加初始訊息
        initial_msg = GroupMessage(
            id=uuid4(),
            group_id=self.group_id,
            sender_id=initiator,
            sender_name=initiator,
            content=initial_message,
            message_type=MessageType.USER,
            timestamp=datetime.utcnow()
        )
        self.state.messages.append(initial_msg)
        await self.memory_store.add_message(initial_msg)

        # 執行對話輪次
        while not self.state.is_terminated:
            await self._execute_round()

            # 檢查終止條件
            if self._should_terminate():
                break

        self.state.ended_at = datetime.utcnow()
        return self.state

    async def _execute_round(self) -> None:
        """執行一輪對話"""
        self.state.current_round += 1

        if self.state.current_round > self.config.max_rounds:
            self.state.is_terminated = True
            self.state.termination_reason = "max_rounds_reached"
            return

        messages_in_round = 0

        while messages_in_round < self.config.max_messages_per_round:
            # 選擇下一位發言者
            next_speaker = await self._speaker_selector.select_next(
                state=self.state,
                allow_repeat=self.config.allow_repeat_speaker
            )

            if not next_speaker:
                break

            self.state.current_speaker = next_speaker

            # 獲取 Agent 回應
            agent = self.agents.get(next_speaker)
            if not agent:
                continue

            response = await self._get_agent_response(agent)

            if response:
                # 添加訊息
                msg = GroupMessage(
                    id=uuid4(),
                    group_id=self.group_id,
                    sender_id=next_speaker,
                    sender_name=agent.name,
                    content=response,
                    message_type=MessageType.AGENT,
                    timestamp=datetime.utcnow()
                )
                self.state.messages.append(msg)
                await self.memory_store.add_message(msg)
                messages_in_round += 1

                # 檢查是否應該終止
                if self._termination_checker.should_terminate(response):
                    self.state.is_terminated = True
                    self.state.termination_reason = "termination_condition_met"
                    return

    async def _get_agent_response(self, agent: Any) -> Optional[str]:
        """獲取 Agent 的回應"""
        # 構建上下文
        context = self._build_context_for_agent(agent)

        try:
            response = await asyncio.wait_for(
                agent.generate_response(context),
                timeout=self.config.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            return f"[{agent.name} 回應超時]"
        except Exception as e:
            return f"[{agent.name} 發生錯誤: {str(e)}]"

    def _build_context_for_agent(self, agent: Any) -> Dict[str, Any]:
        """為 Agent 構建對話上下文"""
        # 獲取最近的訊息作為上下文
        recent_messages = self.state.messages[-20:]  # 最近 20 條訊息

        return {
            "group_id": str(self.group_id),
            "current_round": self.state.current_round,
            "participants": [a.name for a in self.agent_list],
            "messages": [msg.to_dict() for msg in recent_messages],
            "agent_role": agent.role if hasattr(agent, 'role') else None,
            "instructions": self._get_group_instructions()
        }

    def _get_group_instructions(self) -> str:
        """獲取群組對話指令"""
        return """
        你正在參與一個多 Agent 群組討論。請：
        1. 根據你的專業領域提供見解
        2. 回應其他 Agent 的觀點
        3. 保持討論聚焦在主題上
        4. 當達成共識或完成任務時，明確表示 "TERMINATE"
        """

    def _should_terminate(self) -> bool:
        """檢查是否應該終止對話"""
        # 達到最大輪次
        if self.state.current_round >= self.config.max_rounds:
            self.state.termination_reason = "max_rounds_reached"
            return True

        # 沒有活躍的 Agent
        if not self.state.active_agents:
            self.state.termination_reason = "no_active_agents"
            return True

        return False

    async def add_message(
        self,
        content: str,
        sender_id: str,
        sender_name: str,
        message_type: MessageType = MessageType.USER
    ) -> GroupMessage:
        """手動添加訊息到群組"""
        msg = GroupMessage(
            id=uuid4(),
            group_id=self.group_id,
            sender_id=sender_id,
            sender_name=sender_name,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow()
        )
        self.state.messages.append(msg)
        await self.memory_store.add_message(msg)
        return msg

    def get_transcript(self) -> List[Dict[str, Any]]:
        """獲取對話記錄"""
        return [msg.to_dict() for msg in self.state.messages]

    def get_summary(self) -> Dict[str, Any]:
        """獲取對話摘要"""
        return {
            "group_id": str(self.group_id),
            "total_rounds": self.state.current_round,
            "total_messages": len(self.state.messages),
            "participants": list(self.agents.keys()),
            "duration_seconds": (
                (self.state.ended_at - self.state.started_at).total_seconds()
                if self.state.ended_at and self.state.started_at
                else None
            ),
            "termination_reason": self.state.termination_reason,
            "is_terminated": self.state.is_terminated
        }
```

#### 驗收標準
- [ ] GroupChatManager 可以管理多個 Agent 的對話
- [ ] 支援最大輪次限制
- [ ] 支援超時處理
- [ ] 訊息正確記錄和追蹤
- [ ] 單元測試覆蓋率 > 85%

---

### Story 9-2: 發言者選擇策略 (5 點)

**作為** 系統架構師
**我希望** 實現多種發言者選擇策略
**以便** 適應不同的協作場景

#### 技術規格

```python
# backend/src/domain/orchestration/groupchat/speaker_selector.py

from abc import ABC, abstractmethod
from typing import List, Optional, Any
import random

class SpeakerSelector:
    """
    發言者選擇器

    根據配置的策略選擇下一位發言者
    """

    def __init__(
        self,
        method: SpeakerSelectionMethod,
        agents: List[Any],
        llm_service: Any = None
    ):
        self.method = method
        self.agents = agents
        self.llm_service = llm_service
        self._round_robin_index = 0

        # 策略映射
        self._strategies = {
            SpeakerSelectionMethod.AUTO: self._select_auto,
            SpeakerSelectionMethod.ROUND_ROBIN: self._select_round_robin,
            SpeakerSelectionMethod.RANDOM: self._select_random,
            SpeakerSelectionMethod.MANUAL: self._select_manual,
            SpeakerSelectionMethod.PRIORITY: self._select_by_priority,
            SpeakerSelectionMethod.EXPERTISE: self._select_by_expertise,
        }

    async def select_next(
        self,
        state: GroupChatState,
        allow_repeat: bool = True
    ) -> Optional[str]:
        """
        選擇下一位發言者

        Args:
            state: 當前群組狀態
            allow_repeat: 是否允許連續發言

        Returns:
            下一位發言者的 ID，或 None 如果沒有合適的發言者
        """
        strategy = self._strategies.get(self.method)
        if not strategy:
            raise ValueError(f"Unknown selection method: {self.method}")

        selected = await strategy(state)

        # 檢查是否允許重複發言
        if not allow_repeat and selected == state.current_speaker:
            # 嘗試選擇其他人
            available = [a.id for a in self.agents if a.id != selected]
            if available:
                selected = random.choice(available)
            else:
                selected = None

        return selected

    async def _select_auto(self, state: GroupChatState) -> Optional[str]:
        """
        自動選擇 - 使用 LLM 決定誰最適合回應
        """
        if not self.llm_service:
            return await self._select_round_robin(state)

        # 構建提示
        prompt = self._build_selection_prompt(state)

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                max_tokens=50
            )

            # 解析回應，找出被選中的 Agent
            selected_name = self._parse_selection_response(response)

            # 找到對應的 Agent ID
            for agent in self.agents:
                if agent.name.lower() == selected_name.lower():
                    return agent.id

            # 如果找不到，使用 round robin
            return await self._select_round_robin(state)

        except Exception:
            return await self._select_round_robin(state)

    def _build_selection_prompt(self, state: GroupChatState) -> str:
        """構建選擇提示"""
        agents_info = "\n".join([
            f"- {agent.name}: {getattr(agent, 'description', 'No description')}"
            for agent in self.agents
        ])

        recent_messages = state.messages[-5:] if state.messages else []
        messages_text = "\n".join([
            f"{msg.sender_name}: {msg.content[:100]}..."
            for msg in recent_messages
        ])

        return f"""
        根據以下對話，選擇最適合回應的 Agent。

        可用的 Agents:
        {agents_info}

        最近的對話:
        {messages_text}

        請回答應該由哪個 Agent 發言（只需回答 Agent 名稱）:
        """

    def _parse_selection_response(self, response: str) -> str:
        """解析 LLM 的選擇回應"""
        # 簡單解析：取第一行或第一個名稱
        lines = response.strip().split('\n')
        return lines[0].strip()

    async def _select_round_robin(self, state: GroupChatState) -> Optional[str]:
        """輪流選擇"""
        if not self.agents:
            return None

        agent = self.agents[self._round_robin_index % len(self.agents)]
        self._round_robin_index += 1
        return agent.id

    async def _select_random(self, state: GroupChatState) -> Optional[str]:
        """隨機選擇"""
        if not self.agents:
            return None
        return random.choice(self.agents).id

    async def _select_manual(self, state: GroupChatState) -> Optional[str]:
        """手動選擇 - 返回 None，等待外部指定"""
        return None

    async def _select_by_priority(self, state: GroupChatState) -> Optional[str]:
        """按優先級選擇"""
        # 根據 Agent 的優先級屬性排序
        sorted_agents = sorted(
            self.agents,
            key=lambda a: getattr(a, 'priority', 0),
            reverse=True
        )

        # 選擇還沒有在本輪發言的最高優先級 Agent
        current_round_speakers = set(
            msg.sender_id for msg in state.messages
            if msg.timestamp and state.started_at
            and (msg.timestamp - state.started_at).seconds < 60 * state.current_round
        )

        for agent in sorted_agents:
            if agent.id not in current_round_speakers:
                return agent.id

        # 如果都發言過了，返回最高優先級
        return sorted_agents[0].id if sorted_agents else None

    async def _select_by_expertise(self, state: GroupChatState) -> Optional[str]:
        """按專業能力選擇"""
        if not state.messages:
            return await self._select_round_robin(state)

        # 分析最後一條訊息的主題
        last_message = state.messages[-1]
        topic_keywords = self._extract_keywords(last_message.content)

        # 找到最匹配的 Agent
        best_match = None
        best_score = 0

        for agent in self.agents:
            expertise = getattr(agent, 'expertise', [])
            score = len(set(topic_keywords) & set(expertise))

            if score > best_score:
                best_score = score
                best_match = agent.id

        return best_match or await self._select_round_robin(state)

    def _extract_keywords(self, text: str) -> List[str]:
        """從文本中提取關鍵詞"""
        # 簡單實現：分詞並過濾
        words = text.lower().split()
        # 過濾常見詞
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'for'}
        return [w for w in words if w not in stop_words and len(w) > 2]
```

#### 驗收標準
- [ ] 實現 6 種發言者選擇策略
- [ ] AUTO 策略正確使用 LLM 選擇
- [ ] ROUND_ROBIN 確保公平輪流
- [ ] EXPERTISE 能根據專業匹配
- [ ] 單元測試覆蓋所有策略

---

### Story 9-3: 終止條件檢測器 (3 點)

**作為** 系統架構師
**我希望** 實現對話終止條件檢測
**以便** 在適當時機結束群組對話

#### 技術規格

```python
# backend/src/domain/orchestration/groupchat/termination.py

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import re


class TerminationConditionType(str, Enum):
    """終止條件類型"""
    KEYWORD = "keyword"           # 關鍵詞觸發
    CONSENSUS = "consensus"       # 達成共識
    MAX_ROUNDS = "max_rounds"     # 最大輪次
    MAX_MESSAGES = "max_messages" # 最大訊息數
    TIMEOUT = "timeout"           # 超時
    TASK_COMPLETE = "task_complete"  # 任務完成
    NO_PROGRESS = "no_progress"   # 無進展


@dataclass
class TerminationCondition:
    """終止條件"""
    type: TerminationConditionType
    value: Any  # 根據類型不同，值的意義不同
    description: str = ""


class TerminationChecker:
    """
    終止條件檢測器

    檢測對話是否應該終止
    """

    DEFAULT_TERMINATION_KEYWORDS = [
        "TERMINATE",
        "任務完成",
        "討論結束",
        "達成共識",
        "END_DISCUSSION"
    ]

    def __init__(self, conditions: List[str] = None):
        self.conditions = conditions or []
        self._keyword_pattern = self._compile_keyword_pattern()

        # 追蹤進展
        self._message_hashes: List[int] = []
        self._no_progress_count = 0

    def _compile_keyword_pattern(self) -> re.Pattern:
        """編譯關鍵詞正則表達式"""
        keywords = self.DEFAULT_TERMINATION_KEYWORDS + self.conditions
        pattern = "|".join(re.escape(kw) for kw in keywords)
        return re.compile(pattern, re.IGNORECASE)

    def should_terminate(self, message: str) -> bool:
        """
        檢查是否應該終止

        Args:
            message: 最新的訊息內容

        Returns:
            是否應該終止
        """
        # 檢查終止關鍵詞
        if self._check_keyword_termination(message):
            return True

        # 檢查無進展
        if self._check_no_progress(message):
            return True

        return False

    def _check_keyword_termination(self, message: str) -> bool:
        """檢查關鍵詞終止"""
        return bool(self._keyword_pattern.search(message))

    def _check_no_progress(self, message: str, threshold: int = 3) -> bool:
        """
        檢查是否無進展（訊息重複）

        Args:
            message: 訊息內容
            threshold: 連續重複次數閾值

        Returns:
            是否應該終止
        """
        msg_hash = hash(message.strip().lower())

        if msg_hash in self._message_hashes[-10:]:
            self._no_progress_count += 1
        else:
            self._no_progress_count = 0

        self._message_hashes.append(msg_hash)

        return self._no_progress_count >= threshold

    def check_consensus(
        self,
        messages: List[Dict[str, Any]],
        threshold: float = 0.7
    ) -> bool:
        """
        檢查是否達成共識

        Args:
            messages: 最近的訊息列表
            threshold: 共識閾值 (0-1)

        Returns:
            是否達成共識
        """
        if len(messages) < 3:
            return False

        # 簡單實現：檢查最近訊息中贊同的比例
        agreement_keywords = ['同意', '贊成', 'agree', 'yes', '沒問題', 'ok', '可以']

        recent = messages[-5:]
        agreements = 0

        for msg in recent:
            content = msg.get('content', '').lower()
            if any(kw in content for kw in agreement_keywords):
                agreements += 1

        return agreements / len(recent) >= threshold

    def check_task_completion(
        self,
        messages: List[Dict[str, Any]],
        task_description: str
    ) -> bool:
        """
        檢查任務是否完成

        Args:
            messages: 訊息列表
            task_description: 任務描述

        Returns:
            是否完成
        """
        completion_indicators = [
            '完成', 'completed', 'done', '已解決',
            'resolved', 'finished', '任務完成'
        ]

        # 檢查最後幾條訊息
        for msg in messages[-3:]:
            content = msg.get('content', '').lower()
            if any(ind in content for ind in completion_indicators):
                return True

        return False

    def reset(self) -> None:
        """重置檢測器狀態"""
        self._message_hashes.clear()
        self._no_progress_count = 0
```

#### 驗收標準
- [ ] 支援關鍵詞終止檢測
- [ ] 支援無進展檢測
- [ ] 支援共識檢測
- [ ] 支援任務完成檢測
- [ ] 可自定義終止條件

---

### Story 9-4: Multi-turn Session Manager (8 點)

**作為** 系統架構師
**我希望** 實現多輪對話會話管理
**以便** 支援跨訊息的上下文保持

#### 技術規格

```python
# backend/src/domain/orchestration/conversation/session_manager.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
import asyncio


class SessionStatus(str, Enum):
    """會話狀態"""
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ERROR = "error"


@dataclass
class ConversationTurn:
    """對話輪次"""
    turn_id: UUID
    user_input: str
    agent_response: str
    agent_id: str
    timestamp: datetime
    processing_time_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": str(self.turn_id),
            "user_input": self.user_input,
            "agent_response": self.agent_response,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata
        }


@dataclass
class ConversationSession:
    """對話會話"""
    session_id: UUID
    user_id: str
    workflow_id: Optional[UUID]
    status: SessionStatus
    turns: List[ConversationTurn] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False


class MultiTurnSessionManager:
    """
    多輪對話會話管理器

    負責：
    - 會話生命週期管理
    - 上下文維護
    - 輪次追蹤
    - 會話持久化
    """

    def __init__(
        self,
        memory_store: "ConversationMemoryStore",
        session_timeout_minutes: int = 30,
        max_turns_per_session: int = 50
    ):
        self.memory_store = memory_store
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.max_turns = max_turns_per_session

        # 活躍會話快取
        self._active_sessions: Dict[UUID, ConversationSession] = {}

    async def create_session(
        self,
        user_id: str,
        workflow_id: Optional[UUID] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """
        建立新的對話會話

        Args:
            user_id: 用戶 ID
            workflow_id: 關聯的工作流 ID
            initial_context: 初始上下文

        Returns:
            新建的會話
        """
        session = ConversationSession(
            session_id=uuid4(),
            user_id=user_id,
            workflow_id=workflow_id,
            status=SessionStatus.ACTIVE,
            context=initial_context or {},
            expires_at=datetime.utcnow() + self.session_timeout
        )

        self._active_sessions[session.session_id] = session
        await self.memory_store.save_session(session)

        return session

    async def get_session(
        self,
        session_id: UUID,
        auto_refresh: bool = True
    ) -> Optional[ConversationSession]:
        """
        獲取會話

        Args:
            session_id: 會話 ID
            auto_refresh: 是否自動刷新過期時間

        Returns:
            會話物件，如果不存在或已過期則返回 None
        """
        # 先從快取查找
        session = self._active_sessions.get(session_id)

        if not session:
            # 從存儲加載
            session = await self.memory_store.load_session(session_id)
            if session:
                self._active_sessions[session_id] = session

        if not session:
            return None

        # 檢查過期
        if session.is_expired:
            session.status = SessionStatus.EXPIRED
            await self._cleanup_session(session_id)
            return None

        # 自動刷新
        if auto_refresh:
            session.expires_at = datetime.utcnow() + self.session_timeout
            session.updated_at = datetime.utcnow()

        return session

    async def add_turn(
        self,
        session_id: UUID,
        user_input: str,
        agent_response: str,
        agent_id: str,
        processing_time_ms: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """
        添加對話輪次

        Args:
            session_id: 會話 ID
            user_input: 用戶輸入
            agent_response: Agent 回應
            agent_id: 處理的 Agent ID
            processing_time_ms: 處理時間（毫秒）
            metadata: 額外元數據

        Returns:
            新建的輪次
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")

        # 檢查輪次限制
        if session.turn_count >= self.max_turns:
            session.status = SessionStatus.COMPLETED
            raise ValueError(f"Session {session_id} has reached max turns")

        turn = ConversationTurn(
            turn_id=uuid4(),
            user_input=user_input,
            agent_response=agent_response,
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            processing_time_ms=processing_time_ms,
            metadata=metadata or {}
        )

        session.turns.append(turn)
        session.updated_at = datetime.utcnow()

        # 持久化
        await self.memory_store.save_turn(session_id, turn)

        return turn

    async def update_context(
        self,
        session_id: UUID,
        context_updates: Dict[str, Any],
        merge: bool = True
    ) -> None:
        """
        更新會話上下文

        Args:
            session_id: 會話 ID
            context_updates: 上下文更新
            merge: 是否合併（True）或覆蓋（False）
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")

        if merge:
            session.context.update(context_updates)
        else:
            session.context = context_updates

        session.updated_at = datetime.utcnow()
        await self.memory_store.save_session(session)

    async def get_conversation_history(
        self,
        session_id: UUID,
        max_turns: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取對話歷史

        Args:
            session_id: 會話 ID
            max_turns: 最大輪次數（None 表示全部）

        Returns:
            對話歷史列表
        """
        session = await self.get_session(session_id, auto_refresh=False)
        if not session:
            return []

        turns = session.turns
        if max_turns:
            turns = turns[-max_turns:]

        return [turn.to_dict() for turn in turns]

    async def pause_session(self, session_id: UUID) -> None:
        """暫停會話"""
        session = await self.get_session(session_id)
        if session:
            session.status = SessionStatus.PAUSED
            await self.memory_store.save_session(session)

    async def resume_session(self, session_id: UUID) -> Optional[ConversationSession]:
        """恢復會話"""
        session = await self.get_session(session_id)
        if session and session.status == SessionStatus.PAUSED:
            session.status = SessionStatus.ACTIVE
            session.expires_at = datetime.utcnow() + self.session_timeout
            await self.memory_store.save_session(session)
        return session

    async def end_session(
        self,
        session_id: UUID,
        reason: str = "user_ended"
    ) -> None:
        """
        結束會話

        Args:
            session_id: 會話 ID
            reason: 結束原因
        """
        session = await self.get_session(session_id, auto_refresh=False)
        if session:
            session.status = SessionStatus.COMPLETED
            session.metadata['end_reason'] = reason
            session.updated_at = datetime.utcnow()
            await self.memory_store.save_session(session)
            await self._cleanup_session(session_id)

    async def _cleanup_session(self, session_id: UUID) -> None:
        """清理會話"""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

    async def get_active_sessions(
        self,
        user_id: Optional[str] = None
    ) -> List[ConversationSession]:
        """
        獲取活躍會話列表

        Args:
            user_id: 篩選特定用戶的會話

        Returns:
            活躍會話列表
        """
        sessions = list(self._active_sessions.values())

        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]

        # 過濾過期的
        active = []
        for session in sessions:
            if session.is_expired:
                await self._cleanup_session(session.session_id)
            elif session.status == SessionStatus.ACTIVE:
                active.append(session)

        return active

    def build_prompt_context(
        self,
        session: ConversationSession,
        max_history: int = 10
    ) -> str:
        """
        構建提示上下文

        Args:
            session: 會話
            max_history: 最大歷史輪次

        Returns:
            格式化的上下文字串
        """
        history = session.turns[-max_history:] if session.turns else []

        context_parts = []

        # 添加會話上下文
        if session.context:
            context_parts.append(f"Session Context: {session.context}")

        # 添加對話歷史
        for turn in history:
            context_parts.append(f"User: {turn.user_input}")
            context_parts.append(f"Assistant: {turn.agent_response}")

        return "\n".join(context_parts)
```

#### 驗收標準
- [ ] 支援會話建立、獲取、更新、結束
- [ ] 自動過期處理
- [ ] 輪次限制
- [ ] 上下文正確維護
- [ ] 對話歷史可追溯

---

### Story 9-5: Conversation Memory Store (5 點)

**作為** 系統架構師
**我希望** 實現對話記憶存儲
**以便** 持久化和檢索對話歷史

#### 技術規格

```python
# backend/src/domain/orchestration/conversation/memory_store.py

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from abc import ABC, abstractmethod
import json
import hashlib


class ConversationMemoryStore(ABC):
    """對話記憶存儲抽象基類"""

    @abstractmethod
    async def add_message(self, message: "GroupMessage") -> None:
        """添加訊息"""
        pass

    @abstractmethod
    async def get_messages(
        self,
        group_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List["GroupMessage"]:
        """獲取訊息"""
        pass

    @abstractmethod
    async def save_session(self, session: "ConversationSession") -> None:
        """保存會話"""
        pass

    @abstractmethod
    async def load_session(self, session_id: UUID) -> Optional["ConversationSession"]:
        """加載會話"""
        pass

    @abstractmethod
    async def save_turn(self, session_id: UUID, turn: "ConversationTurn") -> None:
        """保存對話輪次"""
        pass


class RedisConversationMemoryStore(ConversationMemoryStore):
    """
    基於 Redis 的對話記憶存儲

    使用 Redis 實現快速的會話存儲和檢索
    """

    def __init__(
        self,
        redis_client: Any,
        key_prefix: str = "conv_memory:",
        message_ttl_hours: int = 24,
        session_ttl_hours: int = 48
    ):
        self.redis = redis_client
        self.prefix = key_prefix
        self.message_ttl = timedelta(hours=message_ttl_hours)
        self.session_ttl = timedelta(hours=session_ttl_hours)

    def _message_key(self, group_id: UUID) -> str:
        return f"{self.prefix}messages:{group_id}"

    def _session_key(self, session_id: UUID) -> str:
        return f"{self.prefix}session:{session_id}"

    def _turn_key(self, session_id: UUID) -> str:
        return f"{self.prefix}turns:{session_id}"

    async def add_message(self, message: "GroupMessage") -> None:
        """添加訊息到 Redis List"""
        key = self._message_key(message.group_id)

        # 序列化訊息
        message_json = json.dumps(message.to_dict(), default=str)

        # 添加到列表
        await self.redis.rpush(key, message_json)

        # 設置過期時間
        await self.redis.expire(
            key,
            int(self.message_ttl.total_seconds())
        )

    async def get_messages(
        self,
        group_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """從 Redis 獲取訊息"""
        key = self._message_key(group_id)

        # 獲取範圍
        start = offset
        end = offset + limit - 1

        messages_json = await self.redis.lrange(key, start, end)

        return [json.loads(msg) for msg in messages_json]

    async def save_session(self, session: "ConversationSession") -> None:
        """保存會話到 Redis Hash"""
        key = self._session_key(session.session_id)

        session_data = {
            "session_id": str(session.session_id),
            "user_id": session.user_id,
            "workflow_id": str(session.workflow_id) if session.workflow_id else None,
            "status": session.status.value,
            "context": json.dumps(session.context),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "metadata": json.dumps(session.metadata),
            "turn_count": session.turn_count
        }

        await self.redis.hset(key, mapping=session_data)
        await self.redis.expire(
            key,
            int(self.session_ttl.total_seconds())
        )

    async def load_session(
        self,
        session_id: UUID
    ) -> Optional["ConversationSession"]:
        """從 Redis 加載會話"""
        key = self._session_key(session_id)

        session_data = await self.redis.hgetall(key)
        if not session_data:
            return None

        # 加載輪次
        turns = await self._load_turns(session_id)

        # 重建會話物件
        return ConversationSession(
            session_id=UUID(session_data["session_id"]),
            user_id=session_data["user_id"],
            workflow_id=UUID(session_data["workflow_id"]) if session_data.get("workflow_id") else None,
            status=SessionStatus(session_data["status"]),
            turns=turns,
            context=json.loads(session_data.get("context", "{}")),
            created_at=datetime.fromisoformat(session_data["created_at"]),
            updated_at=datetime.fromisoformat(session_data["updated_at"]),
            expires_at=datetime.fromisoformat(session_data["expires_at"]) if session_data.get("expires_at") else None,
            metadata=json.loads(session_data.get("metadata", "{}"))
        )

    async def save_turn(
        self,
        session_id: UUID,
        turn: "ConversationTurn"
    ) -> None:
        """保存對話輪次"""
        key = self._turn_key(session_id)

        turn_json = json.dumps(turn.to_dict(), default=str)
        await self.redis.rpush(key, turn_json)
        await self.redis.expire(
            key,
            int(self.session_ttl.total_seconds())
        )

    async def _load_turns(self, session_id: UUID) -> List["ConversationTurn"]:
        """加載會話的所有輪次"""
        key = self._turn_key(session_id)

        turns_json = await self.redis.lrange(key, 0, -1)

        turns = []
        for turn_json in turns_json:
            turn_data = json.loads(turn_json)
            turns.append(ConversationTurn(
                turn_id=UUID(turn_data["turn_id"]),
                user_input=turn_data["user_input"],
                agent_response=turn_data["agent_response"],
                agent_id=turn_data["agent_id"],
                timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                processing_time_ms=turn_data["processing_time_ms"],
                metadata=turn_data.get("metadata", {})
            ))

        return turns

    async def search_by_content(
        self,
        query: str,
        session_ids: Optional[List[UUID]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        按內容搜索對話

        注意：這是簡單實現，生產環境應使用全文搜索引擎
        """
        results = []

        # 如果沒有指定會話，搜索所有
        if not session_ids:
            # 獲取所有會話 key
            pattern = f"{self.prefix}session:*"
            keys = await self.redis.keys(pattern)
            session_ids = [UUID(k.split(":")[-1]) for k in keys]

        query_lower = query.lower()

        for session_id in session_ids:
            turns = await self._load_turns(session_id)

            for turn in turns:
                if (query_lower in turn.user_input.lower() or
                    query_lower in turn.agent_response.lower()):
                    results.append({
                        "session_id": str(session_id),
                        "turn": turn.to_dict()
                    })

                    if len(results) >= limit:
                        return results

        return results

    async def get_session_summary(
        self,
        session_id: UUID
    ) -> Dict[str, Any]:
        """獲取會話摘要"""
        session = await self.load_session(session_id)
        if not session:
            return {}

        total_user_tokens = sum(
            len(t.user_input.split()) for t in session.turns
        )
        total_agent_tokens = sum(
            len(t.agent_response.split()) for t in session.turns
        )
        avg_response_time = (
            sum(t.processing_time_ms for t in session.turns) / len(session.turns)
            if session.turns else 0
        )

        return {
            "session_id": str(session_id),
            "user_id": session.user_id,
            "status": session.status.value,
            "turn_count": session.turn_count,
            "total_user_tokens": total_user_tokens,
            "total_agent_tokens": total_agent_tokens,
            "avg_response_time_ms": avg_response_time,
            "duration_minutes": (
                (session.updated_at - session.created_at).total_seconds() / 60
                if session.updated_at and session.created_at else 0
            ),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }


class PostgresConversationMemoryStore(ConversationMemoryStore):
    """
    基於 PostgreSQL 的對話記憶存儲

    適用於需要複雜查詢和長期存儲的場景
    """

    def __init__(self, db_session: Any):
        self.db = db_session

    async def add_message(self, message: "GroupMessage") -> None:
        """添加訊息到資料庫"""
        query = """
            INSERT INTO conversation_messages
            (id, group_id, sender_id, sender_name, content, message_type, timestamp, metadata, reply_to)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        await self.db.execute(
            query,
            message.id,
            message.group_id,
            message.sender_id,
            message.sender_name,
            message.content,
            message.message_type.value,
            message.timestamp,
            json.dumps(message.metadata),
            message.reply_to
        )

    async def get_messages(
        self,
        group_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """從資料庫獲取訊息"""
        query = """
            SELECT * FROM conversation_messages
            WHERE group_id = $1
            ORDER BY timestamp ASC
            LIMIT $2 OFFSET $3
        """
        rows = await self.db.fetch_all(query, group_id, limit, offset)
        return [dict(row) for row in rows]

    async def save_session(self, session: "ConversationSession") -> None:
        """保存會話到資料庫"""
        query = """
            INSERT INTO conversation_sessions
            (session_id, user_id, workflow_id, status, context, created_at, updated_at, expires_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (session_id) DO UPDATE SET
                status = EXCLUDED.status,
                context = EXCLUDED.context,
                updated_at = EXCLUDED.updated_at,
                expires_at = EXCLUDED.expires_at,
                metadata = EXCLUDED.metadata
        """
        await self.db.execute(
            query,
            session.session_id,
            session.user_id,
            session.workflow_id,
            session.status.value,
            json.dumps(session.context),
            session.created_at,
            session.updated_at,
            session.expires_at,
            json.dumps(session.metadata)
        )

    async def load_session(
        self,
        session_id: UUID
    ) -> Optional["ConversationSession"]:
        """從資料庫加載會話"""
        query = "SELECT * FROM conversation_sessions WHERE session_id = $1"
        row = await self.db.fetch_one(query, session_id)

        if not row:
            return None

        # 加載輪次
        turns_query = """
            SELECT * FROM conversation_turns
            WHERE session_id = $1
            ORDER BY timestamp ASC
        """
        turn_rows = await self.db.fetch_all(turns_query, session_id)

        turns = [
            ConversationTurn(
                turn_id=UUID(r["turn_id"]),
                user_input=r["user_input"],
                agent_response=r["agent_response"],
                agent_id=r["agent_id"],
                timestamp=r["timestamp"],
                processing_time_ms=r["processing_time_ms"],
                metadata=json.loads(r.get("metadata", "{}"))
            )
            for r in turn_rows
        ]

        return ConversationSession(
            session_id=UUID(row["session_id"]),
            user_id=row["user_id"],
            workflow_id=UUID(row["workflow_id"]) if row.get("workflow_id") else None,
            status=SessionStatus(row["status"]),
            turns=turns,
            context=json.loads(row.get("context", "{}")),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            expires_at=row.get("expires_at"),
            metadata=json.loads(row.get("metadata", "{}"))
        )

    async def save_turn(
        self,
        session_id: UUID,
        turn: "ConversationTurn"
    ) -> None:
        """保存對話輪次到資料庫"""
        query = """
            INSERT INTO conversation_turns
            (turn_id, session_id, user_input, agent_response, agent_id, timestamp, processing_time_ms, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        await self.db.execute(
            query,
            turn.turn_id,
            session_id,
            turn.user_input,
            turn.agent_response,
            turn.agent_id,
            turn.timestamp,
            turn.processing_time_ms,
            json.dumps(turn.metadata)
        )
```

#### 驗收標準
- [ ] Redis 存儲實現完整
- [ ] PostgreSQL 存儲實現完整
- [ ] 支援 TTL 過期
- [ ] 支援內容搜索
- [ ] 支援會話摘要

---

### Story 9-6: GroupChat API 路由 (5 點)

**作為** 前端開發者
**我希望** 有完整的 GroupChat API
**以便** 在 UI 中實現群組對話功能

#### 技術規格

```python
# backend/src/api/v1/groupchat/routes.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/groupchat", tags=["GroupChat"])


# ============ Schemas ============

class CreateGroupChatRequest(BaseModel):
    """建立群組聊天請求"""
    name: str = Field(..., description="群組名稱")
    agent_ids: List[UUID] = Field(..., description="參與的 Agent ID 列表")
    workflow_id: Optional[UUID] = Field(None, description="關聯的工作流 ID")
    config: Optional[dict] = Field(default_factory=dict, description="群組配置")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Technical Discussion",
                "agent_ids": ["uuid1", "uuid2", "uuid3"],
                "workflow_id": "uuid4",
                "config": {
                    "max_rounds": 10,
                    "speaker_selection_method": "auto"
                }
            }
        }


class SendMessageRequest(BaseModel):
    """發送訊息請求"""
    content: str = Field(..., description="訊息內容")
    sender_name: str = Field(default="user", description="發送者名稱")


class GroupChatResponse(BaseModel):
    """群組聊天回應"""
    group_id: UUID
    name: str
    status: str
    participants: List[str]
    message_count: int
    current_round: int
    created_at: datetime


class MessageResponse(BaseModel):
    """訊息回應"""
    id: UUID
    sender_id: str
    sender_name: str
    content: str
    message_type: str
    timestamp: datetime


class GroupChatSummaryResponse(BaseModel):
    """群組聊天摘要回應"""
    group_id: UUID
    total_rounds: int
    total_messages: int
    participants: List[str]
    duration_seconds: Optional[float]
    termination_reason: Optional[str]


# ============ Routes ============

@router.post("/", response_model=GroupChatResponse)
async def create_group_chat(
    request: CreateGroupChatRequest,
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """
    建立新的群組聊天

    - **name**: 群組名稱
    - **agent_ids**: 參與的 Agent ID 列表
    - **workflow_id**: 可選，關聯的工作流
    - **config**: 可選，群組配置
    """
    try:
        group = await groupchat_service.create_group(
            name=request.name,
            agent_ids=request.agent_ids,
            workflow_id=request.workflow_id,
            config=request.config
        )

        return GroupChatResponse(
            group_id=group.group_id,
            name=group.name,
            status="created",
            participants=[a.name for a in group.agents],
            message_count=0,
            current_round=0,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{group_id}", response_model=GroupChatResponse)
async def get_group_chat(
    group_id: UUID,
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """獲取群組聊天詳情"""
    group = await groupchat_service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return GroupChatResponse(
        group_id=group.group_id,
        name=group.name,
        status=group.state.status if group.state else "unknown",
        participants=[a.name for a in group.agents],
        message_count=len(group.state.messages) if group.state else 0,
        current_round=group.state.current_round if group.state else 0,
        created_at=group.created_at
    )


@router.post("/{group_id}/start")
async def start_group_conversation(
    group_id: UUID,
    request: SendMessageRequest,
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """
    開始群組對話

    發送初始訊息並啟動 Agent 對話
    """
    try:
        result = await groupchat_service.start_conversation(
            group_id=group_id,
            initial_message=request.content,
            initiator=request.sender_name
        )

        return {
            "status": "completed" if result.is_terminated else "in_progress",
            "rounds_completed": result.current_round,
            "messages": [msg.to_dict() for msg in result.messages],
            "termination_reason": result.termination_reason
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{group_id}/message", response_model=MessageResponse)
async def send_message(
    group_id: UUID,
    request: SendMessageRequest,
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """發送訊息到群組"""
    try:
        message = await groupchat_service.add_user_message(
            group_id=group_id,
            content=request.content,
            sender_name=request.sender_name
        )

        return MessageResponse(
            id=message.id,
            sender_id=message.sender_id,
            sender_name=message.sender_name,
            content=message.content,
            message_type=message.message_type.value,
            timestamp=message.timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{group_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    group_id: UUID,
    limit: int = 50,
    offset: int = 0,
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """獲取群組訊息列表"""
    messages = await groupchat_service.get_messages(
        group_id=group_id,
        limit=limit,
        offset=offset
    )

    return [
        MessageResponse(
            id=msg["id"],
            sender_id=msg["sender_id"],
            sender_name=msg["sender_name"],
            content=msg["content"],
            message_type=msg["message_type"],
            timestamp=msg["timestamp"]
        )
        for msg in messages
    ]


@router.get("/{group_id}/transcript")
async def get_transcript(
    group_id: UUID,
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """獲取完整對話記錄"""
    transcript = await groupchat_service.get_transcript(group_id)
    return {"transcript": transcript}


@router.get("/{group_id}/summary", response_model=GroupChatSummaryResponse)
async def get_summary(
    group_id: UUID,
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """獲取群組對話摘要"""
    summary = await groupchat_service.get_summary(group_id)
    return GroupChatSummaryResponse(**summary)


@router.post("/{group_id}/terminate")
async def terminate_group_chat(
    group_id: UUID,
    reason: str = "manual_termination",
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """終止群組對話"""
    await groupchat_service.terminate(group_id, reason)
    return {"status": "terminated", "reason": reason}


@router.websocket("/{group_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    group_id: UUID,
    groupchat_service: GroupChatService = Depends(get_groupchat_service)
):
    """
    WebSocket 連接用於實時對話

    客戶端可以：
    - 發送訊息
    - 接收 Agent 回應
    - 接收狀態更新
    """
    await websocket.accept()

    try:
        # 註冊連接
        await groupchat_service.register_websocket(group_id, websocket)

        while True:
            # 接收客戶端訊息
            data = await websocket.receive_json()

            if data.get("type") == "message":
                # 處理用戶訊息
                await groupchat_service.handle_websocket_message(
                    group_id=group_id,
                    content=data.get("content", ""),
                    sender=data.get("sender", "user")
                )
            elif data.get("type") == "terminate":
                # 終止對話
                await groupchat_service.terminate(group_id, "websocket_request")
                break

    except WebSocketDisconnect:
        await groupchat_service.unregister_websocket(group_id, websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


# ============ Multi-turn Session Routes ============

@router.post("/sessions/", response_model=dict)
async def create_session(
    user_id: str,
    workflow_id: Optional[UUID] = None,
    initial_context: Optional[dict] = None,
    session_service: MultiTurnSessionManager = Depends(get_session_manager)
):
    """建立新的對話會話"""
    session = await session_service.create_session(
        user_id=user_id,
        workflow_id=workflow_id,
        initial_context=initial_context
    )

    return {
        "session_id": str(session.session_id),
        "user_id": session.user_id,
        "status": session.status.value,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: UUID,
    session_service: MultiTurnSessionManager = Depends(get_session_manager)
):
    """獲取會話詳情"""
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return {
        "session_id": str(session.session_id),
        "user_id": session.user_id,
        "status": session.status.value,
        "turn_count": session.turn_count,
        "context": session.context,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None
    }


@router.post("/sessions/{session_id}/message")
async def send_session_message(
    session_id: UUID,
    message: str,
    session_service: MultiTurnSessionManager = Depends(get_session_manager),
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    在會話中發送訊息並獲取回應
    """
    import time

    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # 構建上下文
    context = session_service.build_prompt_context(session)

    # 獲取 Agent 回應
    start_time = time.time()
    response = await agent_service.process_message(
        message=message,
        context=context,
        session_id=session_id
    )
    processing_time = int((time.time() - start_time) * 1000)

    # 記錄輪次
    turn = await session_service.add_turn(
        session_id=session_id,
        user_input=message,
        agent_response=response,
        agent_id="default_agent",
        processing_time_ms=processing_time
    )

    return {
        "turn_id": str(turn.turn_id),
        "response": response,
        "processing_time_ms": processing_time,
        "turn_count": session.turn_count + 1
    }


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: UUID,
    max_turns: Optional[int] = None,
    session_service: MultiTurnSessionManager = Depends(get_session_manager)
):
    """獲取會話歷史"""
    history = await session_service.get_conversation_history(
        session_id=session_id,
        max_turns=max_turns
    )

    return {"history": history}


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: UUID,
    reason: str = "user_ended",
    session_service: MultiTurnSessionManager = Depends(get_session_manager)
):
    """結束會話"""
    await session_service.end_session(session_id, reason)
    return {"status": "ended", "reason": reason}
```

#### 驗收標準
- [ ] 完整的 CRUD API
- [ ] WebSocket 實時通訊
- [ ] 多輪會話 API
- [ ] API 文檔完整
- [ ] 錯誤處理正確

---

### Story 9-7: 投票與共識機制 (5 點)

**作為** 系統架構師
**我希望** 實現群組投票和共識機制
**以便** 多 Agent 可以民主決策

#### 技術規格

```python
# backend/src/domain/orchestration/groupchat/voting.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum


class VoteType(str, Enum):
    """投票類型"""
    APPROVE_REJECT = "approve_reject"    # 贊成/反對
    MULTIPLE_CHOICE = "multiple_choice"   # 多選一
    RANKING = "ranking"                   # 排序
    WEIGHTED = "weighted"                 # 加權投票


class VoteResult(str, Enum):
    """投票結果"""
    PASSED = "passed"
    REJECTED = "rejected"
    TIE = "tie"
    NO_QUORUM = "no_quorum"
    PENDING = "pending"


@dataclass
class Vote:
    """單次投票"""
    voter_id: str
    voter_name: str
    choice: Any  # 根據投票類型不同
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None


@dataclass
class VotingSession:
    """投票會話"""
    session_id: UUID
    group_id: UUID
    topic: str
    vote_type: VoteType
    options: List[str]
    votes: Dict[str, Vote] = field(default_factory=dict)  # voter_id -> Vote
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    required_quorum: float = 0.5  # 法定人數比例
    pass_threshold: float = 0.5   # 通過門檻
    result: VoteResult = VoteResult.PENDING
    result_details: Dict[str, Any] = field(default_factory=dict)


class VotingManager:
    """
    投票管理器

    管理群組中的投票和共識達成
    """

    def __init__(self):
        self._sessions: Dict[UUID, VotingSession] = {}

    def create_voting_session(
        self,
        group_id: UUID,
        topic: str,
        vote_type: VoteType = VoteType.APPROVE_REJECT,
        options: List[str] = None,
        deadline_minutes: Optional[int] = None,
        required_quorum: float = 0.5,
        pass_threshold: float = 0.5
    ) -> VotingSession:
        """
        建立投票會話

        Args:
            group_id: 群組 ID
            topic: 投票主題
            vote_type: 投票類型
            options: 選項列表（多選時需要）
            deadline_minutes: 截止時間（分鐘）
            required_quorum: 法定人數比例
            pass_threshold: 通過門檻

        Returns:
            新建的投票會話
        """
        if vote_type == VoteType.APPROVE_REJECT:
            options = ["approve", "reject"]
        elif not options:
            raise ValueError("Options required for non-approve/reject votes")

        deadline = None
        if deadline_minutes:
            deadline = datetime.utcnow() + timedelta(minutes=deadline_minutes)

        session = VotingSession(
            session_id=uuid4(),
            group_id=group_id,
            topic=topic,
            vote_type=vote_type,
            options=options,
            deadline=deadline,
            required_quorum=required_quorum,
            pass_threshold=pass_threshold
        )

        self._sessions[session.session_id] = session
        return session

    def cast_vote(
        self,
        session_id: UUID,
        voter_id: str,
        voter_name: str,
        choice: Any,
        weight: float = 1.0,
        reason: Optional[str] = None
    ) -> Vote:
        """
        投票

        Args:
            session_id: 投票會話 ID
            voter_id: 投票者 ID
            voter_name: 投票者名稱
            choice: 選擇
            weight: 投票權重
            reason: 投票理由

        Returns:
            投票記錄
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Voting session {session_id} not found")

        # 檢查截止時間
        if session.deadline and datetime.utcnow() > session.deadline:
            raise ValueError("Voting deadline has passed")

        # 檢查選項有效性
        if session.vote_type == VoteType.APPROVE_REJECT:
            if choice not in ["approve", "reject"]:
                raise ValueError("Choice must be 'approve' or 'reject'")
        elif session.vote_type == VoteType.MULTIPLE_CHOICE:
            if choice not in session.options:
                raise ValueError(f"Invalid choice: {choice}")
        elif session.vote_type == VoteType.RANKING:
            if not isinstance(choice, list) or set(choice) != set(session.options):
                raise ValueError("Ranking must include all options")

        vote = Vote(
            voter_id=voter_id,
            voter_name=voter_name,
            choice=choice,
            weight=weight,
            reason=reason
        )

        session.votes[voter_id] = vote
        return vote

    def calculate_result(
        self,
        session_id: UUID,
        total_eligible_voters: int
    ) -> Dict[str, Any]:
        """
        計算投票結果

        Args:
            session_id: 投票會話 ID
            total_eligible_voters: 總有資格投票人數

        Returns:
            投票結果詳情
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Voting session {session_id} not found")

        # 檢查法定人數
        participation_rate = len(session.votes) / total_eligible_voters
        if participation_rate < session.required_quorum:
            session.result = VoteResult.NO_QUORUM
            session.result_details = {
                "participation_rate": participation_rate,
                "required_quorum": session.required_quorum,
                "votes_received": len(session.votes),
                "voters_needed": int(total_eligible_voters * session.required_quorum)
            }
            return session.result_details

        # 根據投票類型計算結果
        if session.vote_type == VoteType.APPROVE_REJECT:
            result = self._calculate_approve_reject(session)
        elif session.vote_type == VoteType.MULTIPLE_CHOICE:
            result = self._calculate_multiple_choice(session)
        elif session.vote_type == VoteType.RANKING:
            result = self._calculate_ranking(session)
        elif session.vote_type == VoteType.WEIGHTED:
            result = self._calculate_weighted(session)
        else:
            result = {"error": "Unknown vote type"}

        session.result_details = result
        return result

    def _calculate_approve_reject(self, session: VotingSession) -> Dict[str, Any]:
        """計算贊成/反對投票結果"""
        approve_weight = 0.0
        reject_weight = 0.0

        for vote in session.votes.values():
            if vote.choice == "approve":
                approve_weight += vote.weight
            else:
                reject_weight += vote.weight

        total_weight = approve_weight + reject_weight
        approve_ratio = approve_weight / total_weight if total_weight > 0 else 0

        if approve_ratio >= session.pass_threshold:
            session.result = VoteResult.PASSED
        elif approve_ratio == 0.5:
            session.result = VoteResult.TIE
        else:
            session.result = VoteResult.REJECTED

        return {
            "result": session.result.value,
            "approve_count": sum(1 for v in session.votes.values() if v.choice == "approve"),
            "reject_count": sum(1 for v in session.votes.values() if v.choice == "reject"),
            "approve_weight": approve_weight,
            "reject_weight": reject_weight,
            "approve_ratio": approve_ratio,
            "pass_threshold": session.pass_threshold
        }

    def _calculate_multiple_choice(self, session: VotingSession) -> Dict[str, Any]:
        """計算多選投票結果"""
        choice_weights: Dict[str, float] = {opt: 0.0 for opt in session.options}
        choice_counts: Dict[str, int] = {opt: 0 for opt in session.options}

        for vote in session.votes.values():
            choice_weights[vote.choice] += vote.weight
            choice_counts[vote.choice] += 1

        # 找出獲勝選項
        winner = max(choice_weights.items(), key=lambda x: x[1])
        total_weight = sum(choice_weights.values())
        winner_ratio = winner[1] / total_weight if total_weight > 0 else 0

        if winner_ratio >= session.pass_threshold:
            session.result = VoteResult.PASSED
        else:
            # 檢查是否有平局
            max_weight = winner[1]
            tied = [opt for opt, w in choice_weights.items() if w == max_weight]
            if len(tied) > 1:
                session.result = VoteResult.TIE
            else:
                session.result = VoteResult.REJECTED

        return {
            "result": session.result.value,
            "winner": winner[0],
            "winner_ratio": winner_ratio,
            "choice_weights": choice_weights,
            "choice_counts": choice_counts
        }

    def _calculate_ranking(self, session: VotingSession) -> Dict[str, Any]:
        """計算排序投票結果（Borda Count）"""
        scores: Dict[str, float] = {opt: 0.0 for opt in session.options}
        n_options = len(session.options)

        for vote in session.votes.values():
            for rank, option in enumerate(vote.choice):
                # Borda count: 最高排名得分最多
                score = (n_options - rank) * vote.weight
                scores[option] += score

        # 排序結果
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        session.result = VoteResult.PASSED

        return {
            "result": session.result.value,
            "ranking": [{"option": opt, "score": score} for opt, score in ranked],
            "winner": ranked[0][0] if ranked else None
        }

    def _calculate_weighted(self, session: VotingSession) -> Dict[str, Any]:
        """計算加權投票結果"""
        # 與多選類似，但權重更重要
        return self._calculate_multiple_choice(session)

    def get_voting_status(self, session_id: UUID) -> Dict[str, Any]:
        """獲取投票狀態"""
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": str(session.session_id),
            "topic": session.topic,
            "vote_type": session.vote_type.value,
            "options": session.options,
            "votes_count": len(session.votes),
            "deadline": session.deadline.isoformat() if session.deadline else None,
            "result": session.result.value,
            "is_open": session.result == VoteResult.PENDING and (
                not session.deadline or datetime.utcnow() < session.deadline
            )
        }


class ConsensusBuilder:
    """
    共識建立器

    幫助群組達成共識的工具
    """

    def __init__(self, voting_manager: VotingManager):
        self.voting_manager = voting_manager

    async def propose_and_vote(
        self,
        group_id: UUID,
        proposal: str,
        agents: List[Any],
        deadline_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        提案並進行投票

        Args:
            group_id: 群組 ID
            proposal: 提案內容
            agents: 參與投票的 Agent 列表
            deadline_minutes: 投票截止時間

        Returns:
            投票結果
        """
        # 建立投票會話
        session = self.voting_manager.create_voting_session(
            group_id=group_id,
            topic=proposal,
            vote_type=VoteType.APPROVE_REJECT,
            deadline_minutes=deadline_minutes
        )

        # 收集 Agent 投票
        for agent in agents:
            try:
                # 請 Agent 對提案進行投票
                vote_decision = await self._get_agent_vote(agent, proposal)

                self.voting_manager.cast_vote(
                    session_id=session.session_id,
                    voter_id=agent.id,
                    voter_name=agent.name,
                    choice=vote_decision["choice"],
                    reason=vote_decision.get("reason")
                )
            except Exception as e:
                # 記錄投票失敗但繼續
                pass

        # 計算結果
        result = self.voting_manager.calculate_result(
            session_id=session.session_id,
            total_eligible_voters=len(agents)
        )

        return {
            "proposal": proposal,
            "result": result,
            "consensus_reached": session.result == VoteResult.PASSED
        }

    async def _get_agent_vote(
        self,
        agent: Any,
        proposal: str
    ) -> Dict[str, Any]:
        """獲取 Agent 對提案的投票"""
        prompt = f"""
        請對以下提案進行投票：

        提案：{proposal}

        請回答：
        1. 你的投票（approve 或 reject）
        2. 投票理由

        請以 JSON 格式回答：{{"choice": "approve/reject", "reason": "..."}}
        """

        response = await agent.generate_response({"prompt": prompt})

        # 解析回應
        import json
        try:
            return json.loads(response)
        except:
            # 簡單解析
            if "approve" in response.lower():
                return {"choice": "approve", "reason": response}
            else:
                return {"choice": "reject", "reason": response}

    def check_implicit_consensus(
        self,
        messages: List[Dict[str, Any]],
        threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        檢查隱式共識

        通過分析對話內容判斷是否達成共識

        Args:
            messages: 訊息列表
            threshold: 共識閾值

        Returns:
            共識分析結果
        """
        if len(messages) < 3:
            return {"consensus": False, "confidence": 0.0}

        agreement_indicators = [
            '同意', '贊成', '沒問題', '可以', '好的',
            'agree', 'yes', 'ok', 'sounds good', 'approved'
        ]

        disagreement_indicators = [
            '不同意', '反對', '不行', '有問題',
            'disagree', 'no', 'not', 'reject', 'opposed'
        ]

        recent = messages[-10:]
        agreement_count = 0
        disagreement_count = 0

        for msg in recent:
            content = msg.get('content', '').lower()

            if any(ind in content for ind in agreement_indicators):
                agreement_count += 1
            if any(ind in content for ind in disagreement_indicators):
                disagreement_count += 1

        total = len(recent)
        agreement_ratio = agreement_count / total if total > 0 else 0

        return {
            "consensus": agreement_ratio >= threshold and disagreement_count == 0,
            "confidence": agreement_ratio,
            "agreement_count": agreement_count,
            "disagreement_count": disagreement_count,
            "messages_analyzed": total
        }
```

#### 驗收標準
- [ ] 支援 4 種投票類型
- [ ] 正確計算投票結果
- [ ] 支援加權投票
- [ ] 隱式共識檢測
- [ ] 法定人數驗證

---

### Story 9-8: 前端 GroupChat 組件 (3 點)

**作為** 前端開發者
**我希望** 有群組對話 UI 組件
**以便** 用戶可以視覺化地參與群組對話

#### 技術規格

```typescript
// frontend/src/components/groupchat/GroupChatPanel.tsx

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Send, Users, Settings, StopCircle } from 'lucide-react';

interface Message {
  id: string;
  sender_id: string;
  sender_name: string;
  content: string;
  message_type: string;
  timestamp: string;
}

interface Participant {
  id: string;
  name: string;
  role: string;
  isActive: boolean;
}

interface GroupChatPanelProps {
  groupId: string;
  initialMessages?: Message[];
  participants: Participant[];
  onSendMessage: (content: string) => Promise<void>;
  onTerminate: () => Promise<void>;
  isLoading?: boolean;
}

export const GroupChatPanel: React.FC<GroupChatPanelProps> = ({
  groupId,
  initialMessages = [],
  participants,
  onSendMessage,
  onTerminate,
  isLoading = false,
}) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自動滾動到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isSending) return;

    setIsSending(true);
    try {
      await onSendMessage(inputValue);
      setInputValue('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getAvatarColor = (senderId: string) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-orange-500',
      'bg-pink-500',
    ];
    const index = senderId.charCodeAt(0) % colors.length;
    return colors[index];
  };

  return (
    <Card className="h-full flex flex-col">
      {/* Header */}
      <CardHeader className="border-b pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            <h3 className="font-semibold">群組對話</h3>
            <Badge variant="secondary">{participants.length} 參與者</Badge>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="icon">
              <Settings className="h-4 w-4" />
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={onTerminate}
            >
              <StopCircle className="h-4 w-4 mr-1" />
              終止
            </Button>
          </div>
        </div>

        {/* 參與者列表 */}
        <div className="flex gap-2 mt-2 flex-wrap">
          {participants.map((p) => (
            <Badge
              key={p.id}
              variant={p.isActive ? 'default' : 'outline'}
              className="flex items-center gap-1"
            >
              <span className={`w-2 h-2 rounded-full ${p.isActive ? 'bg-green-400' : 'bg-gray-400'}`} />
              {p.name}
            </Badge>
          ))}
        </div>
      </CardHeader>

      {/* Messages */}
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.message_type === 'user' ? 'justify-end' : ''
            }`}
          >
            {message.message_type !== 'user' && (
              <Avatar className={getAvatarColor(message.sender_id)}>
                <AvatarFallback>
                  {message.sender_name.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
            )}

            <div
              className={`max-w-[70%] ${
                message.message_type === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              } rounded-lg p-3`}
            >
              {message.message_type !== 'user' && (
                <p className="text-xs font-semibold mb-1">
                  {message.sender_name}
                </p>
              )}
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <p className="text-xs opacity-60 mt-1">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <Avatar className="bg-gray-400">
              <AvatarFallback>...</AvatarFallback>
            </Avatar>
            <div className="bg-muted rounded-lg p-3">
              <div className="flex gap-1">
                <span className="animate-bounce">●</span>
                <span className="animate-bounce delay-100">●</span>
                <span className="animate-bounce delay-200">●</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </CardContent>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="輸入訊息..."
            disabled={isSending}
          />
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim() || isSending}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};


// frontend/src/components/groupchat/ParticipantSelector.tsx

interface ParticipantSelectorProps {
  availableAgents: Array<{
    id: string;
    name: string;
    description: string;
    capabilities: string[];
  }>;
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
  maxParticipants?: number;
}

export const ParticipantSelector: React.FC<ParticipantSelectorProps> = ({
  availableAgents,
  selectedIds,
  onSelectionChange,
  maxParticipants = 10,
}) => {
  const toggleAgent = (agentId: string) => {
    if (selectedIds.includes(agentId)) {
      onSelectionChange(selectedIds.filter(id => id !== agentId));
    } else if (selectedIds.length < maxParticipants) {
      onSelectionChange([...selectedIds, agentId]);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium">選擇參與的 Agents</span>
        <span className="text-xs text-muted-foreground">
          {selectedIds.length}/{maxParticipants}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {availableAgents.map((agent) => (
          <div
            key={agent.id}
            onClick={() => toggleAgent(agent.id)}
            className={`p-3 border rounded-lg cursor-pointer transition-colors ${
              selectedIds.includes(agent.id)
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50'
            }`}
          >
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedIds.includes(agent.id)}
                onChange={() => {}}
                className="pointer-events-none"
              />
              <div>
                <p className="font-medium text-sm">{agent.name}</p>
                <p className="text-xs text-muted-foreground line-clamp-1">
                  {agent.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### 驗收標準
- [ ] 訊息列表正確顯示
- [ ] 支援發送訊息
- [ ] 參與者列表可視化
- [ ] 載入狀態指示
- [ ] 響應式設計

---

## 測試計劃

### 單元測試

```python
# tests/unit/test_groupchat_manager.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.orchestration.groupchat.manager import (
    GroupChatManager,
    GroupChatConfig,
    SpeakerSelectionMethod,
    MessageType
)


@pytest.fixture
def mock_agents():
    """建立模擬 Agents"""
    agents = []
    for i in range(3):
        agent = MagicMock()
        agent.id = f"agent_{i}"
        agent.name = f"Agent {i}"
        agent.generate_response = AsyncMock(return_value=f"Response from Agent {i}")
        agents.append(agent)
    return agents


@pytest.fixture
def groupchat_manager(mock_agents):
    """建立 GroupChatManager"""
    config = GroupChatConfig(
        max_rounds=3,
        speaker_selection_method=SpeakerSelectionMethod.ROUND_ROBIN
    )
    memory_store = MagicMock()
    memory_store.add_message = AsyncMock()

    return GroupChatManager(
        group_id=uuid4(),
        agents=mock_agents,
        config=config,
        llm_service=None,
        memory_store=memory_store
    )


@pytest.mark.asyncio
async def test_start_conversation(groupchat_manager, mock_agents):
    """測試開始對話"""
    state = await groupchat_manager.start_conversation(
        initial_message="Hello, let's discuss.",
        initiator="user"
    )

    assert state.current_round > 0
    assert len(state.messages) > 1  # 至少有初始訊息 + Agent 回應
    assert state.started_at is not None


@pytest.mark.asyncio
async def test_round_robin_speaker_selection(groupchat_manager, mock_agents):
    """測試輪流發言"""
    state = await groupchat_manager.start_conversation(
        initial_message="Test",
        initiator="user"
    )

    # 檢查 Agent 是否輪流發言
    agent_messages = [
        msg for msg in state.messages
        if msg.message_type == MessageType.AGENT
    ]

    speaker_sequence = [msg.sender_id for msg in agent_messages[:3]]
    expected = ["agent_0", "agent_1", "agent_2"]
    assert speaker_sequence == expected


@pytest.mark.asyncio
async def test_max_rounds_termination(groupchat_manager):
    """測試最大輪次終止"""
    groupchat_manager.config.max_rounds = 2

    state = await groupchat_manager.start_conversation(
        initial_message="Test",
        initiator="user"
    )

    assert state.is_terminated
    assert state.termination_reason == "max_rounds_reached"


@pytest.mark.asyncio
async def test_keyword_termination(groupchat_manager, mock_agents):
    """測試關鍵詞終止"""
    # 設置一個 Agent 返回終止關鍵詞
    mock_agents[0].generate_response = AsyncMock(
        return_value="我們已經達成共識。TERMINATE"
    )

    state = await groupchat_manager.start_conversation(
        initial_message="Test",
        initiator="user"
    )

    assert state.is_terminated
    assert state.termination_reason == "termination_condition_met"


# tests/unit/test_session_manager.py

@pytest.mark.asyncio
async def test_create_session():
    """測試建立會話"""
    memory_store = MagicMock()
    memory_store.save_session = AsyncMock()

    manager = MultiTurnSessionManager(
        memory_store=memory_store,
        session_timeout_minutes=30
    )

    session = await manager.create_session(
        user_id="user_123",
        initial_context={"topic": "test"}
    )

    assert session.user_id == "user_123"
    assert session.context == {"topic": "test"}
    assert session.status == SessionStatus.ACTIVE


@pytest.mark.asyncio
async def test_session_expiration():
    """測試會話過期"""
    memory_store = MagicMock()
    memory_store.save_session = AsyncMock()
    memory_store.load_session = AsyncMock(return_value=None)

    manager = MultiTurnSessionManager(
        memory_store=memory_store,
        session_timeout_minutes=0  # 立即過期
    )

    session = await manager.create_session(user_id="user_123")

    # 等待一小段時間
    import asyncio
    await asyncio.sleep(0.1)

    # 嘗試獲取應該返回 None
    retrieved = await manager.get_session(session.session_id)
    assert retrieved is None or retrieved.status == SessionStatus.EXPIRED


@pytest.mark.asyncio
async def test_add_turn():
    """測試添加對話輪次"""
    memory_store = MagicMock()
    memory_store.save_session = AsyncMock()
    memory_store.save_turn = AsyncMock()
    memory_store.load_session = AsyncMock()

    manager = MultiTurnSessionManager(memory_store=memory_store)
    session = await manager.create_session(user_id="user_123")

    # 設置 load_session 返回我們的 session
    memory_store.load_session = AsyncMock(return_value=session)

    turn = await manager.add_turn(
        session_id=session.session_id,
        user_input="Hello",
        agent_response="Hi there!",
        agent_id="agent_1",
        processing_time_ms=100
    )

    assert turn.user_input == "Hello"
    assert turn.agent_response == "Hi there!"
    assert session.turn_count == 1
```

### 整合測試

```python
# tests/integration/test_groupchat_api.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_and_start_groupchat(client: AsyncClient, test_agents):
    """測試建立並開始群組對話"""
    # 建立群組
    response = await client.post(
        "/api/v1/groupchat/",
        json={
            "name": "Test Group",
            "agent_ids": [str(a.id) for a in test_agents[:3]],
            "config": {
                "max_rounds": 3,
                "speaker_selection_method": "round_robin"
            }
        }
    )
    assert response.status_code == 200
    group_data = response.json()
    group_id = group_data["group_id"]

    # 開始對話
    response = await client.post(
        f"/api/v1/groupchat/{group_id}/start",
        json={"content": "讓我們討論這個問題"}
    )
    assert response.status_code == 200
    result = response.json()

    assert "messages" in result
    assert len(result["messages"]) > 1


@pytest.mark.asyncio
async def test_multiturn_session_flow(client: AsyncClient):
    """測試多輪會話流程"""
    # 建立會話
    response = await client.post(
        "/api/v1/groupchat/sessions/",
        params={"user_id": "test_user"}
    )
    assert response.status_code == 200
    session_data = response.json()
    session_id = session_data["session_id"]

    # 發送多輪訊息
    for i in range(3):
        response = await client.post(
            f"/api/v1/groupchat/sessions/{session_id}/message",
            params={"message": f"第 {i+1} 輪訊息"}
        )
        assert response.status_code == 200
        assert "response" in response.json()

    # 獲取歷史
    response = await client.get(
        f"/api/v1/groupchat/sessions/{session_id}/history"
    )
    assert response.status_code == 200
    history = response.json()["history"]
    assert len(history) == 3
```

---

## 資料庫遷移

```sql
-- migrations/versions/009_groupchat_tables.sql

-- 群組聊天表
CREATE TABLE group_chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    workflow_id UUID REFERENCES workflows(id),
    config JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'created',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 群組參與者表
CREATE TABLE group_chat_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES group_chats(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(group_id, agent_id)
);

-- 群組訊息表
CREATE TABLE group_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES group_chats(id) ON DELETE CASCADE,
    sender_id VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    reply_to UUID REFERENCES group_chat_messages(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 對話會話表
CREATE TABLE conversation_sessions (
    session_id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    workflow_id UUID REFERENCES workflows(id),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- 對話輪次表
CREATE TABLE conversation_turns (
    turn_id UUID PRIMARY KEY,
    session_id UUID REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
    user_input TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    processing_time_ms INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 投票會話表
CREATE TABLE voting_sessions (
    session_id UUID PRIMARY KEY,
    group_id UUID REFERENCES group_chats(id),
    topic TEXT NOT NULL,
    vote_type VARCHAR(50) NOT NULL,
    options JSONB NOT NULL,
    required_quorum DECIMAL(3,2) DEFAULT 0.5,
    pass_threshold DECIMAL(3,2) DEFAULT 0.5,
    result VARCHAR(50) DEFAULT 'pending',
    result_details JSONB DEFAULT '{}',
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 投票記錄表
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES voting_sessions(session_id) ON DELETE CASCADE,
    voter_id VARCHAR(255) NOT NULL,
    voter_name VARCHAR(255) NOT NULL,
    choice JSONB NOT NULL,
    weight DECIMAL(5,2) DEFAULT 1.0,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, voter_id)
);

-- 索引
CREATE INDEX idx_group_messages_group_id ON group_chat_messages(group_id);
CREATE INDEX idx_group_messages_created_at ON group_chat_messages(created_at);
CREATE INDEX idx_conversation_sessions_user_id ON conversation_sessions(user_id);
CREATE INDEX idx_conversation_sessions_status ON conversation_sessions(status);
CREATE INDEX idx_conversation_turns_session_id ON conversation_turns(session_id);
```

---

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 訊息風暴 | 高 | 實施發言限制和流量控制 |
| Agent 回應超時 | 中 | 設置合理超時，降級處理 |
| 上下文過長 | 中 | 實施訊息摘要和滑動窗口 |
| 並發競爭 | 中 | 使用鎖機制和樂觀並發控制 |
| 存儲爆發 | 低 | TTL 過期和定期清理 |

---

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] API 文檔更新
- [ ] 資料庫遷移腳本準備完成
- [ ] 前端組件實現並測試
- [ ] 程式碼審查完成
- [ ] 效能測試通過（50 並發對話）

---

**下一步**: [Sprint 10 - 動態規劃引擎](./sprint-10-plan.md)
