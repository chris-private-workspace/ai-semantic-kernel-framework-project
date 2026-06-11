# F7. DevUI 整合

**分類**: 開發者體驗  
**優先級**: P1 (應該擁有 - 對調試至關重要)  
**開發時間**: 1.5 週  
**複雜度**: ⭐⭐⭐⭐ (高)  
**依賴項**: F1 (順序式編排), React Flow, SignalR/WebSocket, 分佈式追蹤 (可選)  
**風險等級**: 低（範圍明確，僅 UI 功能）

---

## 📑 導航

- [← 功能概覽](../prd-appendix-a-features-overview.md)
- [← F6: Agent 市場](./feature-06-marketplace.md)
- **F7: DevUI 整合** ← 您在這裡
- [✓ 所有功能完成]

---

## 7.1 功能概述

**什麼是 DevUI 整合？**

DevUI 整合在 IPA UI 中提供**面向開發者的調試工具**，使開發者能夠追蹤 Agent 執行流程、檢查 LLM 提示/響應、查看 API 調用並分析性能瓶頸——所有這些都在可視化、交互式界面中進行。

**為什麼這很重要**：
- **更快調試**: 通過可視化執行追蹤，將調試時間從數小時縮短到數分鐘
- **透明度**: 準確查看 LLM 接收（提示）和返回（響應）的內容
- **性能優化**: 識別慢步驟、API 瓶頸、重試循環
- **學習工具**: 通過檢查真實執行流程了解 Agent 的工作原理
- **故障排除**: 通過詳細的錯誤上下文快速診斷故障

**關鍵能力**：
1. **執行追蹤 API**: 後端 API 提供逐步執行詳情
2. **可視化 DAG（有向無環圖）**: React Flow 畫布顯示工作流執行路徑
3. **逐步時間線**: 所有步驟的按時間順序視圖，帶時間戳
4. **提示/響應檢查器**: 查看完整的 LLM 提示和響應（帶令牌計數）
5. **API 調用日誌**: 查看所有外部 API 調用（ServiceNow、Dynamics 等）及其延遲
6. **錯誤上下文**: 詳細的錯誤消息，帶堆棧追蹤和建議的修復
7. **實時更新**: 通過 WebSocket 實時查看執行進度

**商業價值**：
- **開發者生產力**: 調試速度提高 70%（3 小時 → 50 分鐘）
- **減少 MTTR**: 平均修復時間從 2 小時減少到 20 分鐘
- **知識轉移**: 初級開發者通過檢查執行追蹤學習更快
- **質量保證**: QA 團隊無需開發者幫助即可驗證 Agent 行為
- **成本優化**: 識別昂貴的 LLM 調用，優化令牌使用

**真實世界示例**：

```
問題: 客戶退款工作流在步驟 3（共 5 步）失敗

傳統調試（沒有 DevUI）:
1. 檢查日誌（分散在文件中）- 20 分鐘
2. 向程式碼添加調試打印 - 15 分鐘
3. 重新部署並重新運行工作流 - 10 分鐘
4. 分析新日誌 - 20 分鐘
5. 識別問題: LLM 因提示過大而超時 - 30 分鐘
總計: 95 分鐘

使用 DevUI 整合:
1. 在 UI 中打開執行追蹤 - 10 秒
2. 可視化 DAG 顯示步驟 3 標記為紅色（失敗）- 5 秒
3. 點擊步驟 3 → 查看錯誤：「LLM 超時（超過 30 秒）」 - 5 秒
4. 查看提示檢查器 → 提示為 12,000 令牌（太大）- 10 秒
5. 識別根本原因: 客戶有 500+ 條過去訂單，全部包含在上下文中 - 20 秒
總計: 50 秒（快 99%）
```

**架構概覽**：

```
┌─────────────────┐
│  工作流         │
│  執行            │
└────────┬────────┘
         │
         │ 1. 發出執行事件
         ▼
┌─────────────────┐         ┌──────────────┐
│  執行            │────────►│  數據庫      │
│  追蹤服務        │         │  (traces)    │
└────────┬────────┘         └──────────────┘
         │
         │ 2. 存儲追蹤數據
         ▼
┌─────────────────┐         ┌──────────────┐
│  追蹤 API       │◄────────│  DevUI       │
│  (REST)         │         │  (React)     │
└────────┬────────┘         └──────────────┘
         │
         │ 3. 實時更新
         ▼
┌─────────────────┐
│  WebSocket      │
│  (SignalR)      │
└─────────────────┘
```

---

## 7.2 用戶故事（完整）

### **US-F7-001: 查看可視化執行 DAG（有向無環圖）**

**優先級**: P1 (應該擁有)  
**估計開發時間**: 4 天  
**複雜度**: ⭐⭐⭐⭐

**用戶故事**:
- **作為** 開發者（Emily Zhang）
- **我想要** 查看顯示工作流執行路徑的可視化 DAG，每個步驟的狀態（待處理/運行/完成/失敗）
- **以便** 我可以快速理解工作流結構並識別哪個步驟失敗

**驗收標準**:
1. ✅ **可視化畫布**: 使用 React Flow 將工作流顯示為交互式 DAG
2. ✅ **節點狀態**: 每個節點顯示狀態指示器：
   - ⏳ 待處理（灰色）
   - ▶️ 運行中（藍色，脈動動畫）
   - ✅ 完成（綠色）
   - ❌ 失敗（紅色）
3. ✅ **執行路徑**: 突出顯示已執行的路徑（粗邊）
4. ✅ **節點詳情**: 點擊節點打開詳情面板，包含：
   - 步驟名稱、Agent ID
   - 開始時間、結束時間、持續時間
   - 輸入數據（JSON）
   - 輸出數據（JSON）
   - 錯誤消息（如果失敗）
5. ✅ **平移和縮放**: 支持平移、縮放、適合屏幕
6. ✅ **實時更新**: 工作流執行時 DAG 實時更新（通過 WebSocket）

**可視化 DAG UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 執行追蹤: refund_workflow_001 (執行 ID: exec_xyz789)                         │
│ 狀態: ❌ 在步驟 3 失敗 | 持續時間: 4m 23s | 開始: 10:30:00                  │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ [適合屏幕] [放大] [縮小] [時間線視圖] [導出]                                │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                          │ │
│ │     ┌───────────┐                                                       │ │
│ │     │  開始     │                                                       │ │
│ │     └─────┬─────┘                                                       │ │
│ │           │                                                             │ │
│ │           ▼                                                             │ │
│ │     ┌───────────────┐                                                  │ │
│ │     │  步驟 1       │  ✅                                               │ │
│ │     │  Customer360  │  (2.3s)                                          │ │
│ │     └───────┬───────┘                                                  │ │
│ │             │                                                           │ │
│ │             ▼                                                           │ │
│ │     ┌───────────────┐                                                  │ │
│ │     │  步驟 2       │  ✅                                               │ │
│ │     │  分類         │  (1.8s)                                          │ │
│ │     └───────┬───────┘                                                  │ │
│ │             │                                                           │ │
│ │             ▼                                                           │ │
│ │     ┌───────────────┐  ← 已選擇                                       │ │
│ │     │  步驟 3       │  ❌                                               │ │
│ │     │  退款         │  (30s 超時)                                      │ │
│ │     │  決策         │                                                   │ │
│ │     └───────────────┘                                                  │ │
│ │             │                                                           │ │
│ │             ▼ (未執行)                                                 │ │
│ │     ┌───────────────┐                                                  │ │
│ │     │  步驟 4       │  ⏳ (待處理)                                     │ │
│ │     │  更新工單     │                                                   │ │
│ │     └───────┬───────┘                                                  │ │
│ │             │                                                           │ │
│ │             ▼                                                           │ │
│ │     ┌───────────────┐                                                  │ │
│ │     │  結束         │                                                   │ │
│ │     └───────────────┘                                                  │ │
│ │                                                                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 步驟 3 詳情: 退款決策                                          [關閉]   │ │
│ │                                                                          │ │
│ │ 狀態: ❌ 失敗                                                            │ │
│ │ Agent: CS.RefundDecision                                                 │ │
│ │ 持續時間: 30.0s (超過超時)                                              │ │
│ │ 開始: 10:32:15 | 結束: 10:32:45                                         │ │
│ │                                                                          │ │
│ │ 錯誤:                                                                    │ │
│ │ LLM 請求在 30 秒後超時                                                  │ │
│ │                                                                          │ │
│ │ 建議的修復:                                                              │ │
│ │ - 減少提示大小（當前: 12,000 令牌）                                     │ │
│ │ - 在 Agent 配置中增加超時                                               │ │
│ │ - 檢查 Azure OpenAI 服務健康狀況                                        │ │
│ │                                                                          │ │
│ │ [查看輸入數據] [查看提示] [重試步驟] [查看日誌]                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

**React Flow DAG 組件**:

```typescript
import ReactFlow, { Node, Edge, Controls, Background } from 'reactflow';
import 'reactflow/dist/style.css';

interface ExecutionNode extends Node {
  data: {
    stepId: string;
    stepName: string;
    agentId: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    duration: number;
    error?: string;
  };
}

export const ExecutionDAG: React.FC<{ executionId: string }> = ({ executionId }) => {
  const [nodes, setNodes] = useState<ExecutionNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<ExecutionNode | null>(null);
  
  // 獲取執行追蹤
  useEffect(() => {
    fetchExecutionTrace(executionId).then(trace => {
      // 將追蹤步驟轉換為 React Flow 節點
      const flowNodes: ExecutionNode[] = trace.steps.map((step, index) => ({
        id: step.step_id,
        type: 'custom',
        position: { x: 250, y: index * 150 },
        data: {
          stepId: step.step_id,
          stepName: step.name,
          agentId: step.agent_id,
          status: step.status,
          duration: step.duration_ms / 1000,
          error: step.error
        }
      }));
      
      // 創建步驟之間的邊
      const flowEdges: Edge[] = [];
      for (let i = 0; i < flowNodes.length - 1; i++) {
        flowEdges.push({
          id: `e${i}-${i+1}`,
          source: flowNodes[i].id,
          target: flowNodes[i + 1].id,
          animated: flowNodes[i].data.status === 'completed',
          style: { stroke: flowNodes[i].data.status === 'failed' ? '#ef4444' : '#10b981' }
        });
      }
      
      setNodes(flowNodes);
      setEdges(flowEdges);
    });
  }, [executionId]);
  
  // 通過 WebSocket 實時更新
  useEffect(() => {
    const ws = new WebSocket(`wss://api.example.com/executions/${executionId}/stream`);
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      
      // 更新節點狀態
      setNodes(prevNodes => 
        prevNodes.map(node => 
          node.id === update.step_id 
            ? { ...node, data: { ...node.data, status: update.status } }
            : node
        )
      );
    };
    
    return () => ws.close();
  }, [executionId]);
  
  const onNodeClick = (event: React.MouseEvent, node: ExecutionNode) => {
    setSelectedNode(node);
  };
  
  return (
    <div style={{ height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={onNodeClick}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
      
      {selectedNode && (
        <StepDetailPanel step={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  );
};
```

**API: 獲取執行追蹤**:

```bash
GET /api/executions/{execution_id}/trace

響應:
{
  "execution_id": "exec_xyz789",
  "workflow_id": "refund_workflow_001",
  "status": "failed",
  "started_at": "2025-11-18T10:30:00Z",
  "ended_at": "2025-11-18T10:34:23Z",
  "duration_ms": 263000,
  "steps": [
    {
      "step_id": "step_1",
      "name": "獲取客戶 360 視圖",
      "agent_id": "CS.Customer360",
      "status": "completed",
      "started_at": "2025-11-18T10:30:00Z",
      "ended_at": "2025-11-18T10:30:02Z",
      "duration_ms": 2300,
      "input": {...},
      "output": {...}
    },
    {
      "step_id": "step_3",
      "name": "退款決策",
      "agent_id": "CS.RefundDecision",
      "status": "failed",
      "started_at": "2025-11-18T10:32:15Z",
      "ended_at": "2025-11-18T10:32:45Z",
      "duration_ms": 30000,
      "error": {
        "code": "LLM_TIMEOUT",
        "message": "LLM 請求在 30 秒後超時",
        "details": "Azure OpenAI API 在超時內未響應",
        "suggested_fixes": [
          "減少提示大小（當前: 12,000 令牌）",
          "在 Agent 配置中增加超時",
          "檢查 Azure OpenAI 服務健康狀況"
        ]
      }
    }
  ]
}
```

**完成定義**:
- [ ] 可視化 DAG 將工作流執行顯示為 React Flow 畫布
- [ ] 每個節點顯示狀態指示器（待處理、運行、完成、失敗）
- [ ] 點擊節點打開帶步驟信息的詳情面板
- [ ] DAG 支持平移、縮放、適合屏幕
- [ ] 通過 WebSocket 實時更新
- [ ] 失敗的節點以紅色突出顯示，帶錯誤消息
- [ ] 追蹤 API 的集成測試

---

### **US-F7-002: LLM 提示/響應檢查器**

**優先級**: P1 (應該擁有)  
**估計開發時間**: 3 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 開發者（Emily Zhang）
- **我想要** 查看發送到 Azure OpenAI 的確切 LLM 提示和接收到的響應
- **以便** 我可以調試提示工程問題並優化令牌使用

**驗收標準**:
1. ✅ **提示視圖**: 顯示完整的 LLM 提示，帶語法高亮
2. ✅ **響應視圖**: 顯示完整的 LLM 響應（JSON 或文本）
3. ✅ **令牌計數**: 顯示提示令牌、完成令牌、總令牌
4. ✅ **成本估算**: 計算並顯示成本（基於 GPT-4o 定價）
5. ✅ **模型信息**: 顯示模型名稱、溫度、最大令牌數、top_p
6. ✅ **延遲**: 顯示 LLM API 調用延遲（首令牌時間、總時間）
7. ✅ **複製按鈕**: 一鍵複製提示/響應到剪貼板

**提示檢查器 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 步驟 3: 退款決策 - LLM 提示檢查器                                    [關閉]  │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 模型配置:                                                                     │
│   模型: gpt-4o (Azure OpenAI)                                                 │
│   溫度: 0.3 | 最大令牌數: 2000 | Top P: 1.0                                  │
│                                                                               │
│ 令牌使用:                                                                     │
│   提示令牌: 12,345 ⚠️ (非常大)                                                │
│   完成令牌: 156                                                               │
│   總令牌: 12,501                                                              │
│   估計成本: $0.375 (提示: $0.370，完成: $0.005)                              │
│                                                                               │
│ 延遲:                                                                         │
│   首令牌時間: 3.2s                                                            │
│   總時間: 30.0s (超時)                                                        │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ [📝 提示] [📤 響應] [📊 令牌分析]                                            │
│                                                                               │
│ 提示 (12,345 令牌):                                                  [複製]  │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 您是一位幫助客戶退款決策的 AI 助手。                                     │ │
│ │                                                                          │ │
│ │ 公司政策:                                                                │ │
│ │ - 標準退貨: 30 天窗口                                                    │ │
│ │ - 高級客戶: 45 天窗口                                                    │ │
│ │ - 有缺陷的產品: 始終批准                                                │ │
│ │                                                                          │ │
│ │ 客戶上下文:                                                              │ │
│ │ {                                                                        │ │
│ │   "customer_id": "CUST-5678",                                            │ │
│ │   "tier": "Premium",                                                     │ │
│ │   "purchase_history": [                                                  │ │
│ │     {"order_id": "12345", "date": "2025-10-15", "amount": 99.99},      │ │
│ │     {"order_id": "12346", "date": "2025-09-20", "amount": 49.99},      │ │
│ │     ... (498 個訂單 - 問題: 上下文太多！) ...                           │ │
│ │   ]                                                                      │ │
│ │ }                                                                        │ │
│ │                                                                          │ │
│ │ 當前請求:                                                                │ │
│ │ {                                                                        │ │
│ │   "product": "無線耳機",                                                 │ │
│ │   "issue": "Defective",                                                  │ │
│ │   "purchase_date": "2025-10-15"                                          │ │
│ │ }                                                                        │ │
│ │                                                                          │ │
│ │ 以 JSON 格式提供決策...                                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ⚠️  警告: 提示非常大（12,345 令牌）                                          │
│ 建議: 將 purchase_history 限制為最後 10 個訂單（減少 95%）                  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

**令牌分析標籤**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 令牌分析                                                                      │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 提示細分 (12,345 令牌):                                                       │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 系統消息: 234 令牌 (2%)  ████                                            │ │
│ │ 公司政策: 156 令牌 (1%)  ██                                              │ │
│ │ 客戶上下文: 11,789 令牌 (95%) ████████████████████████████████          │ │
│ │   ↳ purchase_history: 11,500 令牌 (93%) ← 問題                          │ │
│ │   ↳ 其他字段: 289 令牌 (2%)                                              │ │
│ │ 當前請求: 166 令牌 (2%)  ██                                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 優化建議:                                                                     │
│   1. 將 purchase_history 限制為最後 10 個訂單（節省 11,000 令牌，-89%）     │
│   2. 從客戶上下文中刪除不必要的字段（節省 200 令牌，-2%）                   │
│   3. 使用匯總的購買統計數據而非完整列表（節省 11,300 令牌，-92%）           │
│                                                                               │
│ 優化後的令牌計數: 1,045 令牌（減少 92%）                                     │
│ 成本節省: $0.330/調用 → 每月 $12.87 @ 100 次調用/天                         │
└───────────────────────────────────────────────────────────────────────────────┘
```

**API: 獲取 LLM 調用詳情**:

```bash
GET /api/executions/{execution_id}/steps/{step_id}/llm-calls

響應:
{
  "step_id": "step_3",
  "llm_calls": [
    {
      "call_id": "llm_call_001",
      "model": "gpt-4o",
      "temperature": 0.3,
      "max_tokens": 2000,
      "top_p": 1.0,
      "prompt": "您是一位幫助客戶退款決策的 AI 助手...",
      "response": "{\"decision\": \"Approved\", ...}",
      "tokens": {
        "prompt": 12345,
        "completion": 156,
        "total": 12501
      },
      "cost_usd": 0.375,
      "latency": {
        "time_to_first_token_ms": 3200,
        "total_time_ms": 30000,
        "timed_out": true
      },
      "timestamp": "2025-11-18T10:32:15Z"
    }
  ]
}
```

**完成定義**:
- [ ] 提示檢查器顯示完整的 LLM 提示，帶語法高亮
- [ ] 響應使用 JSON 格式化顯示
- [ ] 顯示令牌計數（提示、完成、總計）
- [ ] 計算並顯示成本估算
- [ ] 令牌分析標籤顯示提示細分
- [ ] 為大提示提供優化建議
- [ ] 複製按鈕將提示/響應複製到剪貼板

---

### **US-F7-003: 逐步時間線視圖**

**優先級**: P1 (應該擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 開發者（Emily Zhang）
- **我想要** 查看所有工作流步驟的按時間順序時間線，帶時間戳、持續時間和狀態
- **以便** 我可以識別性能瓶頸並了解執行順序

**驗收標準**:
1. ✅ **時間線視圖**: 按時間順序顯示步驟（垂直時間線）
2. ✅ **時間戳**: 顯示每個步驟的開始時間、結束時間
3. ✅ **持續時間條**: 視覺條顯示每個步驟的相對持續時間
4. ✅ **狀態圖標**: 每個狀態的圖標（✅ 完成、❌ 失敗、⏳ 待處理）
5. ✅ **性能洞察**: 突出顯示最慢的步驟（>5s）
6. ✅ **展開/折疊**: 點擊步驟展開並查看輸入/輸出/錯誤
7. ✅ **導出**: 將時間線導出為 CSV 或 JSON

**時間線視圖 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 執行時間線: refund_workflow_001                         [DAG 視圖] [導出]     │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 總持續時間: 4m 23s (263 秒) | 步驟: 3/5 已完成                              │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 10:30:00 │ ✅ 步驟 1: 獲取客戶 360 視圖                 [2.3s]          │ │
│ │          │ ██                                                           │ │
│ │          │ Agent: CS.Customer360                                        │ │
│ │          │ 開始: 10:30:00 | 結束: 10:30:02                             │ │
│ │          │ [▼ 展開]                                                     │ │
│ │          │                                                              │ │
│ │ 10:30:02 │ ✅ 步驟 2: 分類問題                         [1.8s]          │ │
│ │          │ █                                                            │ │
│ │          │ Agent: CS.IssueClassifier                                   │ │
│ │          │ 開始: 10:30:02 | 結束: 10:30:04                             │ │
│ │          │ [▼ 展開]                                                     │ │
│ │          │                                                              │ │
│ │ 10:32:15 │ ❌ 步驟 3: 退款決策                  [30.0s] ⚠️ 慢         │ │
│ │          │ ███████████████████████████████████                          │ │
│ │          │ Agent: CS.RefundDecision                                     │ │
│ │          │ 開始: 10:32:15 | 結束: 10:32:45 (超時)                      │ │
│ │          │ 錯誤: LLM 請求在 30 秒後超時                                │ │
│ │          │ [▲ 折疊]                                                     │ │
│ │          │                                                              │ │
│ │          │ 輸入:                                                        │ │
│ │          │ {                                                            │ │
│ │          │   "customer_id": "CUST-5678",                                │ │
│ │          │   "product": "無線耳機",                                     │ │
│ │          │   "issue": "Defective"                                       │ │
│ │          │ }                                                            │ │
│ │          │                                                              │ │
│ │          │ 錯誤詳情:                                                    │ │
│ │          │ LLM 提示過大（12,345 令牌）                                 │ │
│ │          │ 超過 30 秒超時                                               │ │
│ │          │                                                              │ │
│ │          │ [查看 LLM 提示] [查看日誌] [重試步驟]                       │ │
│ │          │                                                              │ │
│ │ 10:32:45 │ ⏳ 步驟 4: 更新工單                      [未開始]          │ │
│ │          │ (等待步驟 3 完成)                                            │ │
│ │          │                                                              │ │
│ │ -        │ ⏳ 步驟 5: 通知客戶                      [未開始]          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 📊 性能洞察:                                                                  │
│   • 步驟 3 是瓶頸（30.0s，總時間的 95%）                                     │
│   • 建議: 優化 LLM 提示（減少令牌計數）                                      │
│   • 步驟 1-2 執行效率高（每個 <3s）                                          │
└───────────────────────────────────────────────────────────────────────────────┘
```

**完成定義**:
- [ ] 時間線視圖按時間順序顯示步驟
- [ ] 每個步驟顯示開始時間、結束時間、持續時間
- [ ] 持續時間條可視化相對時間
- [ ] 慢步驟（>5s）用警告突出顯示
- [ ] 點擊步驟展開並查看輸入/輸出/錯誤
- [ ] 將時間線導出為 CSV 或 JSON

---

### **US-F7-004: 外部 API 調用日誌**

**優先級**: P2 (很好擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐

**用戶故事**:
- **作為** 開發者（Emily Zhang）
- **我想要** 查看工作流執行期間進行的所有外部 API 調用（ServiceNow、Dynamics 365、SharePoint、OpenAI）
- **以便** 我可以調試集成問題並識別慢速外部服務

**驗收標準**:
1. ✅ **API 調用列表**: 顯示所有外部 API 調用，包含：
   - 服務名稱（ServiceNow、Dynamics 365 等）
   - HTTP 方法和端點
   - 請求標頭（已清理，無身份驗證令牌）
   - 響應狀態碼
   - 延遲（響應時間）
2. ✅ **篩選**: 按服務、狀態碼、延遲篩選
3. ✅ **排序**: 按延遲排序（識別最慢的調用）
4. ✅ **請求/響應視圖**: 點擊調用查看完整的請求/響應
5. ✅ **重試指示器**: 顯示調用是否重試（以及重試次數）

**API 調用日誌 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 外部 API 調用（步驟 1: 客戶 360 視圖）                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ [篩選: 所有服務 ▼] [狀態: 全部 ▼] [排序: 延遲 ▼]                           │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 服務         │ 方法 │ 端點                │ 狀態 │ 延遲  │ 重試││         │
│ ├──────────────┼──────┼─────────────────────┼──────┼───────┼─────┤│         │
│ │ ServiceNow   │ GET  │ /api/now/table/...  │ 200  │ 1.2s  │ -   ││         │
│ │ Dynamics 365 │ GET  │ /api/data/v9.2/...  │ 200  │ 2.8s  │ -   ││         │
│ │ SharePoint   │ GET  │ /_api/search/query  │ 200  │ 1.5s  │ -   ││         │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 點擊行查看請求/響應詳情                                                       │
└───────────────────────────────────────────────────────────────────────────────┘
```

**完成定義**:
- [ ] 為每個步驟顯示 API 調用日誌
- [ ] 按服務、狀態碼、延遲篩選
- [ ] 按延遲排序以識別最慢的調用
- [ ] 點擊調用查看完整的請求/響應
- [ ] 如果適用，顯示重試指示器

---

## 7.3 技術實現（後端）

### 7.3.1 執行追蹤服務

```python
from datetime import datetime
from typing import List, Dict, Any

class ExecutionTraceService:
    """
    用於捕獲和存儲執行追蹤數據的服務
    """
    
    def __init__(self, db_session, websocket_manager):
        self.db = db_session
        self.ws_manager = websocket_manager
    
    async def record_step_start(
        self,
        execution_id: str,
        step_id: str,
        step_name: str,
        agent_id: str,
        input_data: Dict[str, Any]
    ):
        """記錄步驟開始事件"""
        trace_event = ExecutionTraceEvent(
            execution_id=execution_id,
            step_id=step_id,
            step_name=step_name,
            agent_id=agent_id,
            event_type="step_start",
            status="running",
            input_data=input_data,
            timestamp=datetime.utcnow()
        )
        self.db.add(trace_event)
        self.db.commit()
        
        # 通過 WebSocket 發送實時更新
        await self.ws_manager.send_update(execution_id, {
            "type": "step_start",
            "step_id": step_id,
            "status": "running"
        })
    
    async def record_step_complete(
        self,
        execution_id: str,
        step_id: str,
        output_data: Dict[str, Any],
        duration_ms: int
    ):
        """記錄步驟完成"""
        # 更新追蹤事件
        trace_event = self.db.query(ExecutionTraceEvent).filter_by(
            execution_id=execution_id,
            step_id=step_id
        ).first()
        
        trace_event.status = "completed"
        trace_event.output_data = output_data
        trace_event.duration_ms = duration_ms
        trace_event.ended_at = datetime.utcnow()
        self.db.commit()
        
        # 發送實時更新
        await self.ws_manager.send_update(execution_id, {
            "type": "step_complete",
            "step_id": step_id,
            "status": "completed",
            "duration_ms": duration_ms
        })
    
    async def record_llm_call(
        self,
        execution_id: str,
        step_id: str,
        model: str,
        prompt: str,
        response: str,
        tokens: Dict[str, int],
        latency_ms: int
    ):
        """記錄 LLM API 調用"""
        llm_call = LLMCallLog(
            execution_id=execution_id,
            step_id=step_id,
            model=model,
            prompt=prompt,
            response=response,
            prompt_tokens=tokens["prompt"],
            completion_tokens=tokens["completion"],
            total_tokens=tokens["total"],
            latency_ms=latency_ms,
            timestamp=datetime.utcnow()
        )
        self.db.add(llm_call)
        self.db.commit()
```

---

## 7.4 數據庫架構

```sql
CREATE TABLE execution_trace_events (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    step_name VARCHAR(200),
    agent_id VARCHAR(100),
    
    -- 事件詳情
    event_type VARCHAR(50),  -- step_start, step_complete, step_failed
    status VARCHAR(20),  -- pending, running, completed, failed
    
    -- 數據
    input_data JSONB,
    output_data JSONB,
    error_data JSONB,
    
    -- 時間
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE llm_call_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    
    -- LLM 詳情
    model VARCHAR(50),
    temperature DECIMAL(3,2),
    max_tokens INTEGER,
    
    -- 請求/響應
    prompt TEXT,
    response TEXT,
    
    -- 令牌
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd DECIMAL(10,6),
    
    -- 性能
    latency_ms INTEGER,
    timed_out BOOLEAN DEFAULT false,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_call_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    
    -- API 詳情
    service_name VARCHAR(100),  -- ServiceNow, Dynamics365, 等
    method VARCHAR(10),  -- GET, POST, PUT, DELETE
    endpoint TEXT,
    
    -- 請求/響應
    request_headers JSONB,
    response_status INTEGER,
    response_body TEXT,
    
    -- 性能
    latency_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_trace_execution ON execution_trace_events(execution_id, step_id);
CREATE INDEX idx_llm_execution ON llm_call_logs(execution_id, step_id);
CREATE INDEX idx_api_execution ON api_call_logs(execution_id, step_id);
```

---

## 7.5 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **性能** | 追蹤 API 加載時間 | < 500ms | API 響應時間 |
| | DAG 渲染時間 | < 1 秒 | 前端指標 |
| | WebSocket 延遲 | < 100ms | 實時監控 |
| **可擴展性** | 追蹤保留 | 30 天（可配置）| 數據庫策略 |
| | 並發查看者 | 100+ 同時用戶 | 負載測試 |
| **可用性** | 查找問題的時間 | < 2 分鐘 | 用戶測試 |
| | 學習曲線 | 新開發者 <30 分鐘 | 用戶反饋 |

---

## 7.6 測試策略

**單元測試**:
- 追蹤事件記錄
- LLM 調用日誌記錄
- API 調用日誌記錄

**集成測試**:
- 端到端追蹤捕獲
- WebSocket 實時更新
- DAG 渲染

---

## 7.7 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| 大追蹤數據存儲 | 中 | 中 | 30 天保留、壓縮、歸檔 |
| 敏感數據暴露 | 低 | 高 | 清理身份驗證令牌、PII 遮罩 |
| WebSocket 連接斷開 | 中 | 低 | 自動重連、輪詢備用 |

---

## 7.8 未來增強（MVP 後）

1. **分佈式追蹤**: 與 OpenTelemetry 集成
2. **性能剖析**: 步驟執行的火焰圖
3. **比較視圖**: 並排比較兩次執行
4. **重播模式**: 使用不同輸入重播執行
5. **警報**: 對慢步驟、高錯誤率設置警報

---

**✅ 所有功能完成！** 這完成了 F1-F7 PRD 規範。
