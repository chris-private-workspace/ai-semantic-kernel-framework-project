# Sprint 81 技術決策記錄

## Sprint 資訊

| 項目 | 內容 |
|------|------|
| **Sprint** | 81 |
| **Phase** | 23 |
| **主題** | Claude 主導的多 Agent 協調 |

---

## 決策記錄

### D81-1: Claude Orchestrator 架構設計

**日期**: 2026-01-12

**背景**:
需要實現 Claude 主導的多 Agent 協調，讓 Claude 能夠分析任務、選擇合適的 Agent、並協調執行。

**決策**:
採用分層架構設計：
1. **ClaudeCoordinator**: 高層協調器，負責整體流程
2. **TaskAllocator**: 任務分配器，負責子任務創建和執行
3. **ContextManager**: 上下文管理器，負責跨 Agent 數據傳遞

**理由**:
- 關注點分離：每個組件有明確職責
- 可測試性：每個組件可獨立測試
- 可擴展性：易於添加新的執行模式

**執行模式**:
| 模式 | 適用場景 | 說明 |
|------|---------|------|
| SEQUENTIAL | 有依賴關係 | 按順序執行，前一個完成後執行下一個 |
| PARALLEL | 獨立任務 | 同時執行所有子任務 |
| PIPELINE | 數據流處理 | 前一個輸出作為下一個輸入 |
| HYBRID | 複雜任務 | 混合使用以上模式 |

---

### D81-2: A2A 消息協議設計

**日期**: 2026-01-12

**背景**:
需要標準化 Agent 間通信協議，支援 Agent 發現、能力宣告和消息路由。

**決策**:
設計 A2AMessage 標準消息格式：
```python
@dataclass
class A2AMessage:
    message_id: str
    from_agent: str
    to_agent: str
    type: MessageType
    payload: Dict[str, Any]
    correlation_id: Optional[str]  # 追蹤對話鏈
    ttl_seconds: int = 300
    priority: MessagePriority = NORMAL
    retry_count: int = 0
    max_retries: int = 3
```

**消息類型**:
- TASK_REQUEST / TASK_RESPONSE: 任務請求和響應
- STATUS_UPDATE / HEARTBEAT: 狀態更新和心跳
- CAPABILITY_QUERY / CAPABILITY_RESPONSE: 能力查詢
- REGISTER / UNREGISTER: Agent 註冊和取消註冊

**理由**:
- 完整性：支援所有 A2A 通信場景
- 可靠性：內建重試和超時機制
- 可追蹤性：correlation_id 支援對話追蹤

---

### D81-3: Agent 發現機制

**日期**: 2026-01-12

**背景**:
需要動態發現和選擇合適的 Agent 來處理任務。

**決策**:
實現 AgentDiscoveryService 支援：
1. **能力匹配**: 根據所需能力查找 Agent
2. **可用性評分**: 根據負載計算可用性
3. **技能評分**: 支援 Agent 技能熟練度評分
4. **元數據過濾**: 支援自定義過濾條件

**查詢策略**:
```python
@dataclass
class DiscoveryQuery:
    required_capabilities: List[str]
    required_tags: List[str]
    min_availability: float = 0.1
    max_results: int = 10
    include_busy: bool = False
    metadata_filters: Dict[str, Any]
```

**匹配評分算法**:
- 能力匹配: 40%
- 標籤匹配: 20%
- 可用性: 30%
- 技能熟練度: 10%

---

### D81-4: 任務複雜度評估策略

**日期**: 2026-01-12

**背景**:
需要根據任務複雜度選擇合適的執行模式。

**決策**:
| 需求數量 | 複雜度 | 執行模式 | 可並行 |
|---------|-------|---------|--------|
| ≤1 | SIMPLE | SEQUENTIAL | 否 |
| 2-3 | MODERATE | PARALLEL | 是 |
| 4-6 | COMPLEX | HYBRID | 是 |
| >6 | CRITICAL | SEQUENTIAL | 否 |

**理由**:
- CRITICAL 任務需要謹慎處理，避免並行風險
- MODERATE 任務最適合並行處理
- COMPLEX 任務需要混合策略

---

### D81-5: Claude + MAF 融合架構 (已決策)

**日期**: 2026-01-12

**背景**:
需要在 MAF Workflow 中插入 Claude 決策點，讓 Claude 可以動態修改 Workflow 執行路徑。

**決策**:
選擇方案 3 - 創建獨立的 `ClaudeMAFFusion` 模組：

1. **ClaudeDecisionEngine**: Claude 決策引擎
   - 在決策點分析上下文
   - 選擇最佳執行路徑
   - 支援路徑選擇、跳過步驟、修改參數、中止執行

2. **DynamicWorkflow**: 動態工作流
   - 支援運行時添加/移除/修改步驟
   - 記錄所有修改歷史

3. **ClaudeMAFFusion**: 融合協調器
   - `execute_with_claude_decisions()`: 執行帶決策點的工作流
   - `modify_workflow()`: 動態修改工作流
   - 統一管理工作流和執行狀態

**決策類型**:
```python
class DecisionType(str, Enum):
    ROUTE_SELECTION = "route_selection"  # 選擇執行路徑
    SKIP_STEP = "skip_step"              # 跳過當前步驟
    ABORT = "abort"                      # 中止執行
    CONTINUE = "continue"                # 繼續執行
```

**理由**:
- **保持 MAF 層純淨**: 不修改現有 MAF Builders
- **關注點分離**: 融合邏輯獨立於兩個框架
- **易於測試**: 可單獨測試 Claude 決策邏輯
- **向後兼容**: 不影響現有功能

---

## 總結

Sprint 81 完成了三個核心功能：

1. **Claude Orchestrator** (S81-1): 多 Agent 協調框架
2. **A2A Protocol** (S81-2): Agent 間通信協議
3. **Claude + MAF Fusion** (S81-3): 深度整合框架

所有決策已執行並驗證成功。

---

**最後更新**: 2026-01-12
**Sprint 狀態**: 已完成
