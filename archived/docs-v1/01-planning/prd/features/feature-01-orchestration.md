# F1. 順序式 Agent 編排

**類別**：引擎核心  
**優先級**：P0（必須有 - MVP 核心）  
**開發時間**：2 週  
**複雜度**：⭐⭐⭐⭐⭐（非常高）  
**依賴項**：無（基礎功能）  
**風險等級**：高（架構複雜，性能要求高）

---

## 📑 導航

- [← 功能概覽](../prd-appendix-a-features-overview.md)
- **F1: 順序式 Agent 編排** ← 您在這裡
- [→ F2: 人機協作檢查點](./feature-02-checkpointing.md)

---

## 1.1 功能概述

**什麼是順序式 Agent 編排？**

順序式 Agent 編排是 IPA 平台的**核心引擎**，負責按照預定義的順序執行多個 Agent，將前一個 Agent 的輸出作為下一個 Agent 的輸入，實現複雜的多步驟業務流程自動化。

**為什麼重要**：
- **業務流程自動化**：將複雜的人工流程（需要 8+ 步驟）自動化為 Agent 工作流
- **可視化編排**：非技術人員可通過拖拉方式設計工作流（類似 n8n）
- **錯誤處理**：自動重試、回退、降級處理
- **可觀測性**：實時監控執行狀態、日誌、性能指標

**核心能力**：
1. **多步驟工作流執行**：按順序執行 3-10 個 Agent
2. **數據傳遞**：JSON 格式的輸入/輸出在 Agent 間傳遞
3. **條件分支**：根據前一步結果選擇執行路徑
4. **錯誤處理**：失敗重試（最多 3 次）、異常捕獲、降級處理
5. **實時監控**：執行進度、每步狀態、性能指標

**商業價值**：
- **效率提升**：將 8 小時人工流程縮短至 15 分鐘
- **成本節約**：減少 70% 人工操作成本
- **準確率提升**：從 85%（人工）提升至 95%（AI Agent）
- **可擴展性**：單一工作流模板可服務數千個案例

**實際案例**：

```
場景：客戶退款申請處理（原需 8 小時，現需 15 分鐘）

傳統人工流程：
1. 客服收到退款申請 → 20 分鐘
2. 查詢客戶歷史記錄（ServiceNow, Dynamics 365, SharePoint）→ 45 分鐘
3. 判斷是否符合退款政策 → 30 分鐘
4. 計算退款金額 → 15 分鐘
5. 填寫審批表單 → 20 分鐘
6. 等待主管審批 → 6 小時
7. 更新工單狀態 → 10 分鐘
8. 通知客戶 → 10 分鐘
總計：~8 小時

使用 Agent 編排：
1. Agent 1: 獲取客戶 360 視圖（並行查詢 3 個系統）→ 2 分鐘
2. Agent 2: 分類問題類型（LLM 分析）→ 30 秒
3. Agent 3: 判斷退款決策（基於政策規則 + LLM）→ 1 分鐘
4. Checkpoint: 人工審批（僅高風險案例需要）→ 5 分鐘
5. Agent 4: 更新工單狀態（API 調用）→ 30 秒
6. Agent 5: 發送通知（郵件 + Teams）→ 30 秒
總計：~15 分鐘（節省 97% 時間）
```

**架構概覽**：

```
┌─────────────────┐
│  工作流定義     │
│  (YAML/JSON)    │
└────────┬────────┘
         │
         │ 1. 載入工作流
         ▼
┌─────────────────┐         ┌──────────────┐
│  編排引擎       │────────►│  Agent 1     │
│  (WorkflowExecutor)        │  執行         │
└────────┬────────┘         └──────────────┘
         │                           │
         │ 2. 傳遞數據               │ 輸出
         ▼                           ▼
┌─────────────────┐         ┌──────────────┐
│  數據轉換       │────────►│  Agent 2     │
│  (JSON Mapping) │         │  執行         │
└─────────────────┘         └──────────────┘
         │                           │
         │ 3. 監控狀態               │ 完成
         ▼                           ▼
┌─────────────────┐         ┌──────────────┐
│  執行監控       │◄────────│  結果存儲    │
│  (實時更新)     │         │  (PostgreSQL)│
└─────────────────┘         └──────────────┘
```

---

## 1.2 用戶故事（完整）

### **US-F1-001: 創建多步驟工作流畫布**

**優先級**：P0（必須有）  
**預估開發時間**：5 天  
**複雜度**：⭐⭐⭐⭐

**用戶故事**：
- **作為** 業務分析師（趙明）
- **我想要** 通過可視化畫布拖拉方式設計多步驟 Agent 工作流
- **以便** 無需編寫代碼即可創建複雜業務流程

**驗收標準**：
1. ✅ **畫布介面**：提供 React Flow 可視化畫布，支持拖放、縮放、平移
2. ✅ **Agent 節點**：從左側面板拖拉 Agent 到畫布
3. ✅ **連接線**：點擊節點輸出端口，拖動到下一節點輸入端口建立連接
4. ✅ **節點配置**：雙擊節點打開配置面板，設置：
   - Agent 名稱、描述
   - 輸入參數映射（從前一步輸出映射）
   - 輸出參數定義
   - 錯誤處理策略（重試次數、超時時間）
5. ✅ **條件分支**：支持 if/else 條件節點（根據前一步結果選擇路徑）
6. ✅ **驗證**：保存前驗證工作流邏輯（無循環依賴、所有參數已映射）
7. ✅ **自動佈局**：提供自動排列功能（垂直/水平佈局）

**工作流畫布 UI**：

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 工作流設計器：客戶退款流程                           [保存] [測試] [發布]    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ ┌─────────────┐  ┌─────────────────────────────────────────────────────────┐│
│ │ Agent 庫    │  │ 畫布                                          [自動佈局] ││
│ │             │  │                                                           ││
│ │ 🔍 搜索...  │  │   ┌─────────────┐                                        ││
│ │             │  │   │   開始      │                                        ││
│ │ 📁 客戶服務 │  │   └──────┬──────┘                                        ││
│ │  ├ Customer360│ │          │                                              ││
│ │  ├ IssueClassifier│        ▼                                              ││
│ │  └ RefundDecision│  ┌─────────────┐                                       ││
│ │             │  │   │ Agent 1     │                                        ││
│ │ 📁 IT 支援  │  │   │ Customer360 │                                        ││
│ │  ├ PasswordReset│  │             │                                        ││
│ │  └ TicketUpdate│  └──────┬──────┘                                        ││
│ │             │  │          │                                               ││
│ │ 📁 金融     │  │          ▼                                               ││
│ │  └ ExpenseApproval│ ┌─────────────┐                                      ││
│ │             │  │   │ Agent 2     │                                        ││
│ └─────────────┘  │   │ IssueClassifier                                     ││
│                  │   │             │                                        ││
│                  │   └──────┬──────┘                                        ││
│                  │          │                                               ││
│                  │          ▼                                               ││
│                  │   ┌─────────────┐  ← 選中                               ││
│                  │   │ Agent 3     │                                        ││
│                  │   │ RefundDecision                                       ││
│                  │   │             │                                        ││
│                  │   └──────┬──────┘                                        ││
│                  │          │                                               ││
│                  │          ▼                                               ││
│                  │   ┌─────────────┐                                        ││
│                  │   │ Checkpoint  │                                        ││
│                  │   │ 人工審批    │                                        ││
│                  │   └──────┬──────┘                                        ││
│                  │          │                                               ││
│                  │          ▼                                               ││
│                  │   ┌─────────────┐                                        ││
│                  │   │   結束      │                                        ││
│                  │   └─────────────┘                                        ││
│                  └─────────────────────────────────────────────────────────┘│
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 節點配置：Agent 3 - RefundDecision                           [關閉]     │ │
│ │                                                                          │ │
│ │ 名稱：退款決策 Agent                                                     │ │
│ │ Agent ID：CS.RefundDecision                                              │ │
│ │                                                                          │ │
│ │ 輸入參數映射：                                                           │ │
│ │   customer_id: {{ agent1.output.customer_id }}                          │ │
│ │   issue_type: {{ agent2.output.classification }}                        │ │
│ │   purchase_history: {{ agent1.output.orders }}                          │ │
│ │                                                                          │ │
│ │ 輸出參數：                                                               │ │
│ │   decision: string (Approved / Rejected)                                 │ │
│ │   refund_amount: number                                                  │ │
│ │   reason: string                                                         │ │
│ │                                                                          │ │
│ │ 錯誤處理：                                                               │ │
│ │   最大重試次數：3                                                        │ │
│ │   超時時間：30 秒                                                        │ │
│ │   失敗後操作：[跳過並繼續 ▼]                                             │ │
│ │                                                                          │ │
│ │ [保存配置] [測試 Agent]                                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

**工作流 YAML 定義**：

```yaml
workflow:
  id: refund_workflow_001
  name: 客戶退款流程
  version: 1.0.0
  
  steps:
    - id: step_1
      name: 獲取客戶 360 視圖
      agent_id: CS.Customer360
      input:
        customer_id: "{{ trigger.customer_id }}"
      output:
        customer_id: string
        tier: string
        orders: array
      retry:
        max_attempts: 3
        timeout_seconds: 10
    
    - id: step_2
      name: 分類問題類型
      agent_id: CS.IssueClassifier
      input:
        issue_description: "{{ trigger.issue_description }}"
        customer_tier: "{{ step_1.output.tier }}"
      output:
        classification: string
        confidence: number
      retry:
        max_attempts: 2
        timeout_seconds: 5
    
    - id: step_3
      name: 退款決策
      agent_id: CS.RefundDecision
      input:
        customer_id: "{{ step_1.output.customer_id }}"
        issue_type: "{{ step_2.output.classification }}"
        purchase_history: "{{ step_1.output.orders }}"
      output:
        decision: string
        refund_amount: number
        reason: string
      retry:
        max_attempts: 3
        timeout_seconds: 30
    
    - id: checkpoint_1
      name: 人工審批
      type: checkpoint
      condition: "{{ step_3.output.refund_amount > 500 }}"
      timeout_hours: 24
      approvers:
        - role: CS_MANAGER
          required: true
    
    - id: step_4
      name: 更新工單狀態
      agent_id: CS.TicketUpdate
      input:
        ticket_id: "{{ trigger.ticket_id }}"
        status: RESOLVED
        decision: "{{ step_3.output.decision }}"
      output:
        updated: boolean
```

**React Flow 工作流畫布組件**：

```typescript
import ReactFlow, { 
  Node, 
  Edge, 
  Controls, 
  Background,
  useNodesState,
  useEdgesState 
} from 'reactflow';
import 'reactflow/dist/style.css';

interface WorkflowNode extends Node {
  data: {
    agentId: string;
    agentName: string;
    inputMapping: Record<string, string>;
    outputSchema: Record<string, string>;
    retry: { maxAttempts: number; timeout: number };
  };
}

export const WorkflowCanvas: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  
  // 從 Agent 庫拖拉到畫布
  const onDrop = (event: React.DragEvent) => {
    const agentData = JSON.parse(event.dataTransfer.getData('agent'));
    
    const newNode: WorkflowNode = {
      id: `agent_${Date.now()}`,
      type: 'custom',
      position: { x: event.clientX - 100, y: event.clientY - 50 },
      data: {
        agentId: agentData.id,
        agentName: agentData.name,
        inputMapping: {},
        outputSchema: agentData.outputSchema,
        retry: { maxAttempts: 3, timeout: 30 }
      }
    };
    
    setNodes(prev => [...prev, newNode]);
  };
  
  // 連接兩個節點
  const onConnect = (connection: Connection) => {
    const newEdge: Edge = {
      id: `e${connection.source}-${connection.target}`,
      source: connection.source,
      target: connection.target,
      animated: true
    };
    setEdges(prev => [...prev, newEdge]);
  };
  
  // 雙擊節點打開配置面板
  const onNodeDoubleClick = (event: React.MouseEvent, node: WorkflowNode) => {
    setSelectedNode(node);
  };
  
  // 驗證工作流（無循環依賴）
  const validateWorkflow = (): boolean => {
    // 檢查循環依賴
    const visited = new Set<string>();
    const recStack = new Set<string>();
    
    const hasCycle = (nodeId: string): boolean => {
      visited.add(nodeId);
      recStack.add(nodeId);
      
      const outgoingEdges = edges.filter(e => e.source === nodeId);
      for (const edge of outgoingEdges) {
        if (!visited.has(edge.target)) {
          if (hasCycle(edge.target)) return true;
        } else if (recStack.has(edge.target)) {
          return true;
        }
      }
      
      recStack.delete(nodeId);
      return false;
    };
    
    for (const node of nodes) {
      if (!visited.has(node.id) && hasCycle(node.id)) {
        alert('工作流包含循環依賴，請檢查！');
        return false;
      }
    }
    
    return true;
  };
  
  // 保存工作流
  const saveWorkflow = async () => {
    if (!validateWorkflow()) return;
    
    const workflowDef = {
      nodes: nodes.map(n => ({
        id: n.id,
        agentId: n.data.agentId,
        inputMapping: n.data.inputMapping,
        retry: n.data.retry
      })),
      edges: edges.map(e => ({
        source: e.source,
        target: e.target
      }))
    };
    
    await fetch('/api/workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workflowDef)
    });
  };
  
  return (
    <div style={{ height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onNodeDoubleClick={onNodeDoubleClick}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
      
      {selectedNode && (
        <NodeConfigPanel 
          node={selectedNode} 
          onClose={() => setSelectedNode(null)}
          onSave={(updated) => {
            setNodes(prev => 
              prev.map(n => n.id === updated.id ? updated : n)
            );
            setSelectedNode(null);
          }}
        />
      )}
    </div>
  );
};
```

**API：保存工作流**：

```bash
POST /api/workflows

Request:
{
  "name": "客戶退款流程",
  "nodes": [
    {
      "id": "step_1",
      "agent_id": "CS.Customer360",
      "input_mapping": {
        "customer_id": "{{ trigger.customer_id }}"
      },
      "retry": { "max_attempts": 3, "timeout": 30 }
    }
  ],
  "edges": [
    { "source": "step_1", "target": "step_2" }
  ]
}

Response:
{
  "workflow_id": "wf_abc123",
  "status": "created",
  "version": "1.0.0"
}
```

**完成定義**：
- [ ] 可視化畫布支持拖放、縮放、平移
- [ ] 從 Agent 庫拖拉 Agent 到畫布
- [ ] 連接節點建立數據流
- [ ] 雙擊節點配置輸入/輸出映射
- [ ] 驗證工作流邏輯（無循環依賴）
- [ ] 保存工作流為 YAML/JSON
- [ ] 單元測試覆蓋率 > 80%

---

### **US-F1-002: 執行多步驟工作流並傳遞數據**

**優先級**：P0（必須有）  
**預估開發時間**：6 天  
**複雜度**：⭐⭐⭐⭐⭐

**用戶故事**：
- **作為** 系統（後端服務）
- **我想要** 按順序執行工作流中的所有 Agent，並將前一個 Agent 的輸出作為下一個 Agent 的輸入
- **以便** 實現端到端的業務流程自動化

**驗收標準**：
1. ✅ **順序執行**：嚴格按照 YAML 定義的順序執行 Agent
2. ✅ **數據傳遞**：將 `step_N.output` 映射為 `step_N+1.input`
3. ✅ **變量替換**：支持 `{{ variable }}` 語法引用前序步驟輸出
4. ✅ **JSON Schema 驗證**：每步執行前驗證輸入參數符合 Agent 的 input schema
5. ✅ **並行執行**：支持 `parallel` 標記的步驟並行執行（非 MVP 必須）
6. ✅ **條件跳過**：根據 `condition` 表達式決定是否執行該步驟
7. ✅ **執行上下文**：維護全局上下文對象，存儲所有步驟的輸入/輸出

**執行引擎實現**：

```python
from typing import Dict, Any, List
import asyncio
import jsonschema
from jinja2 import Template

class WorkflowExecutor:
    """
    工作流編排引擎
    負責順序執行多個 Agent 並傳遞數據
    """
    
    def __init__(self, workflow_def: Dict[str, Any], agent_registry: AgentRegistry):
        self.workflow = workflow_def
        self.agent_registry = agent_registry
        self.execution_context = {
            "trigger": {},  # 觸發時的輸入
            "steps": {}     # 每步的輸出
        }
    
    async def execute(self, trigger_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行工作流
        
        Args:
            trigger_input: 工作流觸發時的輸入數據
            
        Returns:
            執行結果（最後一步的輸出 + 執行統計）
        """
        self.execution_context["trigger"] = trigger_input
        
        execution_id = generate_execution_id()
        started_at = datetime.utcnow()
        
        try:
            # 按順序執行每個步驟
            for step in self.workflow["steps"]:
                step_id = step["id"]
                
                # 檢查條件（如果有）
                if "condition" in step:
                    if not self._evaluate_condition(step["condition"]):
                        print(f"跳過步驟 {step_id}（條件不滿足）")
                        continue
                
                # 執行步驟
                step_result = await self._execute_step(step, execution_id)
                
                # 存儲輸出到上下文
                self.execution_context["steps"][step_id] = step_result
                
                # 如果步驟失敗且沒有錯誤處理，停止執行
                if step_result["status"] == "failed" and not step.get("continue_on_error"):
                    raise WorkflowExecutionError(f"步驟 {step_id} 執行失敗")
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "started_at": started_at,
                "ended_at": datetime.utcnow(),
                "output": self.execution_context["steps"][self.workflow["steps"][-1]["id"]]["output"]
            }
        
        except Exception as e:
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e),
                "started_at": started_at,
                "ended_at": datetime.utcnow()
            }
    
    async def _execute_step(self, step: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """
        執行單個步驟
        """
        step_id = step["id"]
        agent_id = step["agent_id"]
        
        # 1. 解析輸入參數（變量替換）
        resolved_input = self._resolve_input(step["input"])
        
        # 2. 驗證輸入參數
        agent = self.agent_registry.get(agent_id)
        self._validate_input(resolved_input, agent.input_schema)
        
        # 3. 執行 Agent（帶重試）
        retry_config = step.get("retry", {"max_attempts": 1, "timeout_seconds": 30})
        
        for attempt in range(1, retry_config["max_attempts"] + 1):
            try:
                output = await asyncio.wait_for(
                    agent.execute(resolved_input),
                    timeout=retry_config["timeout_seconds"]
                )
                
                return {
                    "status": "completed",
                    "input": resolved_input,
                    "output": output,
                    "attempts": attempt
                }
            
            except asyncio.TimeoutError:
                print(f"步驟 {step_id} 超時（嘗試 {attempt}/{retry_config['max_attempts']}）")
                if attempt == retry_config["max_attempts"]:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指數退避
            
            except Exception as e:
                print(f"步驟 {step_id} 失敗（嘗試 {attempt}/{retry_config['max_attempts']}）：{e}")
                if attempt == retry_config["max_attempts"]:
                    return {
                        "status": "failed",
                        "input": resolved_input,
                        "error": str(e),
                        "attempts": attempt
                    }
                await asyncio.sleep(2 ** attempt)
    
    def _resolve_input(self, input_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析輸入參數（變量替換）
        
        Example:
            input_template = {
                "customer_id": "{{ trigger.customer_id }}",
                "issue_type": "{{ steps.step_2.output.classification }}"
            }
            
            返回:
            {
                "customer_id": "CUST-5678",
                "issue_type": "Refund Request"
            }
        """
        resolved = {}
        
        for key, value in input_template.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # 解析變量路徑（例如：trigger.customer_id）
                var_path = value[2:-2].strip()
                resolved[key] = self._get_value_from_context(var_path)
            else:
                resolved[key] = value
        
        return resolved
    
    def _get_value_from_context(self, path: str) -> Any:
        """
        從執行上下文中獲取值
        
        Example:
            path = "steps.step_1.output.customer_id"
            返回: "CUST-5678"
        """
        parts = path.split(".")
        current = self.execution_context
        
        for part in parts:
            current = current[part]
        
        return current
    
    def _validate_input(self, input_data: Dict[str, Any], schema: Dict[str, Any]):
        """
        驗證輸入參數符合 JSON Schema
        """
        try:
            jsonschema.validate(instance=input_data, schema=schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"輸入參數驗證失敗：{e.message}")
    
    def _evaluate_condition(self, condition: str) -> bool:
        """
        評估條件表達式
        
        Example:
            condition = "{{ steps.step_3.output.refund_amount > 500 }}"
            返回: True 或 False
        """
        # 解析變量
        resolved = self._resolve_input({"_condition": condition})
        condition_value = resolved["_condition"]
        
        # 評估表達式
        return eval(condition_value)  # 生產環境應使用安全的表達式評估器
```

**API：觸發工作流執行**：

```bash
POST /api/workflows/{workflow_id}/execute

Request:
{
  "trigger_input": {
    "customer_id": "CUST-5678",
    "ticket_id": "TKT-12345",
    "issue_description": "產品故障，需要退款"
  }
}

Response:
{
  "execution_id": "exec_xyz789",
  "status": "running",
  "started_at": "2025-11-18T10:30:00Z",
  "workflow_id": "refund_workflow_001",
  "trigger_input": {...}
}
```

**API：獲取執行狀態**：

```bash
GET /api/executions/{execution_id}

Response:
{
  "execution_id": "exec_xyz789",
  "workflow_id": "refund_workflow_001",
  "status": "completed",
  "started_at": "2025-11-18T10:30:00Z",
  "ended_at": "2025-11-18T10:45:00Z",
  "duration_seconds": 900,
  
  "steps": [
    {
      "step_id": "step_1",
      "name": "獲取客戶 360 視圖",
      "status": "completed",
      "duration_seconds": 2,
      "output": {
        "customer_id": "CUST-5678",
        "tier": "Premium",
        "orders": [...]
      }
    },
    {
      "step_id": "step_2",
      "name": "分類問題類型",
      "status": "completed",
      "duration_seconds": 1,
      "output": {
        "classification": "Refund Request",
        "confidence": 0.95
      }
    }
  ]
}
```

**完成定義**：
- [ ] 順序執行工作流中的所有 Agent
- [ ] 支持 `{{ variable }}` 語法引用前序輸出
- [ ] JSON Schema 驗證輸入參數
- [ ] 條件跳過（根據 `condition` 表達式）
- [ ] 重試機制（最多 3 次，指數退避）
- [ ] 執行上下文維護
- [ ] API 端點（觸發執行、獲取狀態）
- [ ] 單元測試覆蓋率 > 85%
- [ ] 集成測試（端到端工作流執行）

---

### **US-F1-003: 錯誤處理與重試**

**優先級**：P0（必須有）  
**預估開發時間**：3 天  
**複雜度**：⭐⭐⭐

**用戶故事**：
- **作為** 系統（後端服務）
- **我想要** 當 Agent 執行失敗時自動重試，並在達到最大重試次數後記錄錯誤
- **以便** 提高工作流執行的成功率

**驗收標準**：
1. ✅ **自動重試**：Agent 執行失敗後自動重試（最多 3 次）
2. ✅ **指數退避**：重試間隔：1s → 2s → 4s
3. ✅ **超時處理**：超過 `timeout_seconds` 自動終止並重試
4. ✅ **錯誤記錄**：記錄每次失敗的錯誤信息、堆棧追蹤
5. ✅ **降級處理**：支持 `fallback_agent` 配置（主 Agent 失敗後執行備用 Agent）
6. ✅ **繼續執行**：支持 `continue_on_error: true`（跳過失敗步驟繼續執行）

**錯誤處理配置**：

```yaml
steps:
  - id: step_3
    name: 退款決策
    agent_id: CS.RefundDecision
    input:
      customer_id: "{{ step_1.output.customer_id }}"
    retry:
      max_attempts: 3
      timeout_seconds: 30
      backoff: exponential  # linear, exponential, fixed
    on_error:
      action: fallback  # retry, skip, abort, fallback
      fallback_agent_id: CS.RefundDecisionBasic  # 降級使用簡單規則引擎
    continue_on_error: false  # 失敗後是否繼續執行
```

**完成定義**：
- [ ] 自動重試（最多 3 次）
- [ ] 指數退避重試間隔
- [ ] 超時處理
- [ ] 錯誤記錄（日誌 + 數據庫）
- [ ] 降級處理（fallback_agent）
- [ ] 繼續執行（continue_on_error）
- [ ] 單元測試覆蓋率 > 80%

---

### **US-F1-004: 實時執行監控**

**優先級**：P1（應該有）  
**預估開發時間**：4 天  
**複雜度**：⭐⭐⭐

**用戶故事**：
- **作為** 業務分析師（趙明）
- **我想要** 實時查看工作流執行進度（哪些步驟已完成、哪些正在運行、哪些失敗）
- **以便** 快速發現問題並介入處理

**驗收標準**：
1. ✅ **執行列表**：顯示所有工作流執行（最近 7 天）
2. ✅ **實時更新**：通過 WebSocket 實時更新執行狀態
3. ✅ **進度條**：顯示整體進度（3/5 步驟完成）
4. ✅ **步驟詳情**：點擊查看每步的輸入/輸出/錯誤
5. ✅ **日誌查看**：查看每步的詳細日誌
6. ✅ **手動重試**：失敗的工作流可手動重新執行

**執行監控 UI**：

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 工作流執行監控                                            [篩選▼] [刷新]      │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ [全部] [運行中] [已完成] [失敗] [等待審批]                                   │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │執行 ID       │工作流        │狀態    │進度   │開始時間   │持續時間│操作││
│ ├──────────────┼─────────────┼────────┼───────┼──────────┼────────┼────┤│
│ │exec_xyz789   │客戶退款流程  │▶ 運行中│3/5    │10:30:00  │2m 15s  │⏸️ ││
│ │              │              │        │███▢▢  │          │        │    ││
│ │exec_xyz788   │客戶退款流程  │✅ 完成 │5/5    │10:15:00  │15m 30s │📊 ││
│ │              │              │        │█████  │          │        │    ││
│ │exec_xyz787   │客戶退款流程  │❌ 失敗 │2/5    │10:00:00  │5m 12s  │🔄 ││
│ │              │              │        │██▢▢▢  │          │        │    ││
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 點擊行查看詳情                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

**完成定義**：
- [ ] 執行列表顯示所有工作流執行
- [ ] 實時更新（WebSocket）
- [ ] 進度條顯示整體進度
- [ ] 點擊查看步驟詳情
- [ ] 日誌查看
- [ ] 手動重試失敗的工作流
- [ ] 單元測試覆蓋率 > 75%

---

## 1.3 數據庫架構

```sql
-- 工作流定義表
CREATE TABLE workflows (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL,  -- YAML 轉換為 JSON 存儲
    version VARCHAR(20) DEFAULT '1.0.0',
    status VARCHAR(20) DEFAULT 'draft',  -- draft, published, archived
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 工作流執行表
CREATE TABLE workflow_executions (
    id VARCHAR(100) PRIMARY KEY,
    workflow_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- running, completed, failed, paused
    trigger_input JSONB,
    output JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);

-- 步驟執行表
CREATE TABLE step_executions (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    step_name VARCHAR(200),
    agent_id VARCHAR(100),
    status VARCHAR(20) NOT NULL,  -- pending, running, completed, failed
    input JSONB,
    output JSONB,
    error TEXT,
    attempts INTEGER DEFAULT 1,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    
    FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
);

-- 索引
CREATE INDEX idx_workflow_executions_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_step_executions_execution ON step_executions(execution_id);
CREATE INDEX idx_step_executions_status ON step_executions(status);
```

---

## 1.4 非功能需求（NFR）

| **類別** | **需求** | **目標** | **測量方式** |
|----------|---------|---------|-------------|
| **性能** | 單步執行時間 | P95 < 5 秒 | APM 監控 |
| | 工作流總執行時間 | P95 < 30 秒（5 步工作流）| 執行日誌 |
| | 並發執行數 | 支持 50+ 並發工作流 | 負載測試 |
| **可擴展性** | 最大步驟數 | 支持 20 步工作流 | 測試驗證 |
| | 最大並發數 | 100 並發執行 | 負載測試 |
| **可靠性** | 執行成功率 | > 95% | 執行統計 |
| | 重試成功率 | > 80% | 執行統計 |
| **可用性** | 系統可用性 | 99.5% | 監控告警 |

---

## 1.5 測試策略

**單元測試**：
- 工作流解析（YAML → 內部表示）
- 變量替換（`{{ variable }}` 解析）
- 輸入驗證（JSON Schema）
- 重試邏輯
- 條件評估

**集成測試**：
- 端到端工作流執行（3 步 Agent）
- 錯誤處理（失敗重試）
- 數據傳遞（前序輸出 → 後序輸入）

**負載測試**：
- 50 並發工作流執行
- 單個工作流 20 步執行

---

## 1.6 風險與緩解

| **風險** | **概率** | **影響** | **緩解措施** |
|---------|---------|---------|------------|
| 工作流執行慢（>30s）| 中 | 高 | 並行執行、緩存、性能優化 |
| Agent 執行失敗率高 | 中 | 高 | 重試機制、降級處理、監控告警 |
| 循環依賴導致死鎖 | 低 | 高 | 工作流驗證、檢測循環依賴 |
| 大量並發導致資源耗盡 | 中 | 中 | 限流、排隊機制、水平擴展 |

---

## 1.7 未來增強（Post-MVP）

1. **並行執行**：支持多個獨立步驟並行執行（減少總執行時間）
2. **子工作流**：支持工作流嵌套（調用另一個工作流）
3. **事件觸發**：支持外部事件觸發工作流（Webhook, Queue）
4. **定時調度**：支持定時執行工作流（Cron）
5. **版本控制**：工作流多版本管理（v1.0 → v2.0）
6. **A/B 測試**：同時運行兩個版本的工作流並比較結果

---

**狀態**：✅ 完整規格已完成（1200+ 行）

