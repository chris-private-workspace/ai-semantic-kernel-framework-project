## <a id="f13-modern-web-ui"></a>13. F13: 現代化 Web UI

**功能類別**: UI/UX (用戶體驗)  
**優先級**: P0 (必須擁有)  
**估計開發時間**: 4 週  
**複雜度**: ⭐⭐⭐⭐⭐

---

### 13.1 功能概述

**定義**:
F13（現代化 Web UI）提供**直觀、響應式的前端界面**，涵蓋 8 個核心頁面，讓用戶能夠無縫管理 Workflow、Agent、Prompt 等資源。采用現代前端技術棧（React 18 + TypeScript），提供桌面級的操作體驗。

**為什麼重要**:
- **降低使用門檻**: 可視化編輯器讓非技術用戶也能構建複雜 Workflow
- **提升效率**: 拖拉式操作比手寫 YAML 快 5 倍
- **實時反饋**: 即時驗證配置錯誤，減少調試時間
- **跨平台**: 響應式設計支持桌面、平板、手機

**核心頁面**:
1. **首頁 Dashboard**: 系統概況、KPI、快速入口
2. **Workflow Builder**: 可視化流程編輯器（拖拉節點）
3. **Execution List**: 執行歷史查詢與篩選
4. **Agent Marketplace**: Agent 發現與安裝
5. **Monitoring Dashboard**: 實時監控儀表板（集成 F12）
6. **Audit Logs**: 審計日誌查詢（集成 F10）
7. **DLQ Management**: 死信隊列管理（集成 F8）
8. **Prompt Editor**: Prompt 模板編輯器（集成 F9）

**技術棧**:
- **前端框架**: React 18 + TypeScript
- **狀態管理**: Redux Toolkit + RTK Query
- **UI 組件**: Ant Design / Material-UI
- **圖表庫**: ECharts / Recharts
- **Workflow 編輯器**: ReactFlow
- **代碼編輯器**: Monaco Editor（VS Code 編輯器）
- **路由**: React Router v6
- **請求庫**: Axios + interceptors

**業務價值**:
- **用戶留存**: 友好 UI 使新用戶上手時間從 2 小時降至 15 分鐘
- **錯誤減少**: 實時驗證減少 60% 配置錯誤
- **跨部門協作**: 市場團隊可直接編輯 Prompt，無需技術支持

---

### 13.2 用戶故事

#### **US-F13-001: 首頁 Dashboard**

**User Story**:  
作為系統用戶，我希望在首頁看到系統運行概況和關鍵指標，以便快速掌握系統狀態。

**場景描述**:
- 用戶登入後進入首頁 Dashboard
- 顯示今日執行統計、成功率、平均執行時間
- 顯示近 7 天的趨勢圖表
- 顯示告警和 DLQ 消息摘要
- 快速入口：新建 Workflow、查看執行記錄、Agent 商店

**Acceptance Criteria**:
1. ✅ 顯示 4 個核心 KPI 卡片：今日執行數、成功率、平均執行時間、活躍 Agent 數
2. ✅ 顯示近 7 天執行趨勢折線圖（成功/失敗/總數）
3. ✅ 顯示 Top 5 熱門 Workflow 排行榜
4. ✅ 顯示最新 5 條 DLQ 告警（包含跳轉連結）
5. ✅ 提供快速操作按鈕：+ 新建 Workflow、查看所有執行、Agent 商店
6. ✅ 所有數據每 30 秒自動刷新
7. ✅ 響應式設計，支持桌面和平板

**UI Mockup（React 組件結構）**:

```tsx
// HomePage.tsx
import React, { useEffect } from 'react';
import { Row, Col, Card, Statistic, Button, Table, List } from 'antd';
import { Line } from '@ant-design/charts';
import { PlusOutlined, HistoryOutlined, AppstoreOutlined } from '@ant-design/icons';
import { useGetDashboardStatsQuery, useGetTrendDataQuery } from '@/api/dashboardApi';

export const HomePage: React.FC = () => {
  const { data: stats, refetch: refetchStats } = useGetDashboardStatsQuery();
  const { data: trendData } = useGetTrendDataQuery({ days: 7 });

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => refetchStats(), 30000);
    return () => clearInterval(interval);
  }, [refetchStats]);

  const trendConfig = {
    data: trendData?.data || [],
    xField: 'date',
    yField: 'count',
    seriesField: 'status',
    smooth: true,
    legend: { position: 'top' },
  };

  const topWorkflowColumns = [
    { title: 'Workflow 名稱', dataIndex: 'name', key: 'name' },
    { title: '執行次數', dataIndex: 'count', key: 'count', sorter: true },
    { title: '成功率', dataIndex: 'success_rate', key: 'success_rate', render: (v: number) => `${v}%` },
  ];

  return (
    <div className="home-page">
      <h1>儀表板</h1>

      {/* KPI Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="今日執行數" value={stats?.today_executions || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats?.success_rate || 0}
              precision={2}
              suffix="%"
              valueStyle={{ color: stats?.success_rate >= 95 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均執行時間"
              value={stats?.avg_execution_time || 0}
              suffix="秒"
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="活躍 Agent" value={stats?.active_agents || 0} />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="快速操作">
            <Button type="primary" icon={<PlusOutlined />} href="/workflows/new" style={{ marginRight: 8 }}>
              新建 Workflow
            </Button>
            <Button icon={<HistoryOutlined />} href="/executions" style={{ marginRight: 8 }}>
              查看執行記錄
            </Button>
            <Button icon={<AppstoreOutlined />} href="/agents/marketplace">
              Agent 商店
            </Button>
          </Card>
        </Col>
      </Row>

      {/* Trend Chart */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Card title="近 7 天執行趨勢">
            <Line {...trendConfig} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Top 5 熱門 Workflow">
            <Table
              dataSource={stats?.top_workflows || []}
              columns={topWorkflowColumns}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* DLQ Alerts */}
      <Row gutter={16}>
        <Col span={24}>
          <Card title="最新 DLQ 告警" extra={<a href="/dlq">查看全部</a>}>
            <List
              dataSource={stats?.recent_dlq || []}
              renderItem={(item: any) => (
                <List.Item>
                  <List.Item.Meta
                    title={<a href={`/dlq/${item.id}`}>{item.workflow_name}</a>}
                    description={`錯誤: ${item.error_message} | ${item.created_at}`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
```

**API Endpoints**:

```python
# api/dashboard.py
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from sqlalchemy import func
from typing import List

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """獲取 Dashboard 統計數據"""
    today = datetime.now().date()
    
    # Today's executions
    today_executions = db.query(func.count(WorkflowExecution.id)).filter(
        func.date(WorkflowExecution.started_at) == today
    ).scalar()
    
    # Success rate (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    total_executions = db.query(func.count(WorkflowExecution.id)).filter(
        WorkflowExecution.started_at >= week_ago
    ).scalar()
    successful_executions = db.query(func.count(WorkflowExecution.id)).filter(
        WorkflowExecution.started_at >= week_ago,
        WorkflowExecution.status == 'completed'
    ).scalar()
    success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
    
    # Average execution time
    avg_time = db.query(func.avg(
        func.extract('epoch', WorkflowExecution.completed_at - WorkflowExecution.started_at)
    )).filter(
        WorkflowExecution.started_at >= week_ago,
        WorkflowExecution.status == 'completed'
    ).scalar() or 0
    
    # Active agents
    active_agents = db.query(func.count(func.distinct(Agent.id))).filter(
        Agent.is_active == True
    ).scalar()
    
    # Top 5 workflows
    top_workflows = db.query(
        Workflow.name,
        func.count(WorkflowExecution.id).label('count'),
        (func.sum(case([(WorkflowExecution.status == 'completed', 1)], else_=0)) * 100.0 / func.count(WorkflowExecution.id)).label('success_rate')
    ).join(WorkflowExecution).filter(
        WorkflowExecution.started_at >= week_ago
    ).group_by(Workflow.id, Workflow.name).order_by(desc('count')).limit(5).all()
    
    # Recent DLQ
    recent_dlq = db.query(DLQ).order_by(desc(DLQ.created_at)).limit(5).all()
    
    return {
        "today_executions": today_executions,
        "success_rate": round(success_rate, 2),
        "avg_execution_time": round(avg_time, 2),
        "active_agents": active_agents,
        "top_workflows": [
            {"name": w.name, "count": w.count, "success_rate": round(w.success_rate, 2)}
            for w in top_workflows
        ],
        "recent_dlq": [
            {
                "id": d.id,
                "workflow_name": d.workflow.name,
                "error_message": d.error_message[:100],
                "created_at": d.created_at.isoformat()
            }
            for d in recent_dlq
        ]
    }

@router.get("/trend")
async def get_trend_data(days: int = 7, db: Session = Depends(get_db)):
    """獲取執行趨勢數據"""
    start_date = datetime.now() - timedelta(days=days)
    
    trend_data = db.query(
        func.date(WorkflowExecution.started_at).label('date'),
        WorkflowExecution.status,
        func.count(WorkflowExecution.id).label('count')
    ).filter(
        WorkflowExecution.started_at >= start_date
    ).group_by('date', WorkflowExecution.status).all()
    
    # Format for chart
    formatted_data = []
    for record in trend_data:
        formatted_data.append({
            "date": record.date.isoformat(),
            "status": record.status,
            "count": record.count
        })
    
    return {"data": formatted_data}
```

**測試策略**:

1. 單元測試：測試各 KPI 計算邏輯正確性
2. UI 測試：使用 React Testing Library 測試組件渲染和交互
3. 集成測試：測試 API 端點數據返回正確性
4. 性能測試：測試 30 秒自動刷新不影響用戶體驗
5. 響應式測試：在不同屏幕尺寸下測試佈局

---

#### **US-F13-002: Workflow Builder（流程編輯器）**

**User Story**:  
作為業務用戶，我希望通過可視化拖拉的方式編輯 Workflow，以便無需編碼即可構建複雜流程。

**場景描述**:

- 用戶在 Workflow Builder 中拖拉節點（Agent、條件判斷、循環、並行）
- 配置節點參數（輸入輸出映射、Prompt 變數、超時設置）
- 連接節點形成執行流程
- 實時驗證配置合法性
- 保存並部署 Workflow

**Acceptance Criteria**:

1. ✅ 提供節點面板：Agent 節點、條件節點、循環節點、並行節點、開始/結束節點
2. ✅ 支持拖拉節點到畫布並自動對齊
3. ✅ 支持連線節點（帶箭頭，支持刪除）
4. ✅ 點擊節點顯示屬性面板，可配置輸入/輸出/參數
5. ✅ 實時驗證：檢查循環引用、未連接節點、參數缺失
6. ✅ 支持保存草稿、發布版本、查看歷史版本
7. ✅ 支持快捷鍵：Ctrl+S 保存、Ctrl+Z 撤銷、Ctrl+Y 重做
8. ✅ 支持放大/縮小/自動佈局

**UI Mockup（ReactFlow 實現）**:

```tsx
// WorkflowBuilder.tsx
import React, { useState, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Button, Drawer, Form, Input, Select, message } from 'antd';
import { SaveOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useCreateWorkflowMutation, useUpdateWorkflowMutation } from '@/api/workflowApi';
import { AgentNode } from './nodes/AgentNode';
import { ConditionNode } from './nodes/ConditionNode';

const nodeTypes = {
  agent: AgentNode,
  condition: ConditionNode,
  // ... other custom nodes
};

export const WorkflowBuilder: React.FC<{ workflowId?: string }> = ({ workflowId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [createWorkflow] = useCreateWorkflowMutation();
  const [updateWorkflow] = useUpdateWorkflowMutation();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setDrawerVisible(true);
  }, []);

  const validateWorkflow = (): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    // Check for disconnected nodes
    const connectedNodes = new Set(edges.flatMap(e => [e.source, e.target]));
    nodes.forEach(node => {
      if (node.type !== 'start' && node.type !== 'end' && !connectedNodes.has(node.id)) {
        errors.push(`節點 "${node.data.label}" 未連接`);
      }
    });
    
    // Check for circular dependencies
    const detectCycle = (nodeId: string, visited: Set<string>, stack: Set<string>): boolean => {
      if (stack.has(nodeId)) return true;
      if (visited.has(nodeId)) return false;
      
      visited.add(nodeId);
      stack.add(nodeId);
      
      const outgoingEdges = edges.filter(e => e.source === nodeId);
      for (const edge of outgoingEdges) {
        if (detectCycle(edge.target, visited, stack)) return true;
      }
      
      stack.delete(nodeId);
      return false;
    };
    
    const visited = new Set<string>();
    const stack = new Set<string>();
    for (const node of nodes) {
      if (detectCycle(node.id, visited, stack)) {
        errors.push('檢測到循環引用');
        break;
      }
    }
    
    // Check for missing required parameters
    nodes.forEach(node => {
      if (node.type === 'agent' && !node.data.agentId) {
        errors.push(`節點 "${node.data.label}" 未選擇 Agent`);
      }
    });
    
    return { valid: errors.length === 0, errors };
  };

  const handleSave = async (publish: boolean = false) => {
    const validation = validateWorkflow();
    if (!validation.valid) {
      message.error(`驗證失敗: ${validation.errors.join(', ')}`);
      return;
    }
    
    const workflowData = {
      nodes: nodes.map(n => ({ id: n.id, type: n.type, data: n.data, position: n.position })),
      edges: edges.map(e => ({ source: e.source, target: e.target, label: e.label })),
      status: publish ? 'published' : 'draft'
    };
    
    try {
      if (workflowId) {
        await updateWorkflow({ id: workflowId, ...workflowData }).unwrap();
      } else {
        await createWorkflow(workflowData).unwrap();
      }
      message.success(publish ? 'Workflow 已發布' : 'Workflow 已保存為草稿');
    } catch (err) {
      message.error('保存失敗');
    }
  };

  return (
    <div style={{ height: '100vh' }}>
      <div style={{ padding: '16px', background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
        <Button icon={<SaveOutlined />} onClick={() => handleSave(false)} style={{ marginRight: 8 }}>
          保存草稿
        </Button>
        <Button type="primary" icon={<CheckCircleOutlined />} onClick={() => handleSave(true)}>
          發布
        </Button>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background />
      </ReactFlow>

      <Drawer
        title="節點配置"
        placement="right"
        width={400}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedNode && (
          <Form layout="vertical">
            <Form.Item label="節點名稱">
              <Input value={selectedNode.data.label} onChange={(e) => {
                setNodes(nds => nds.map(n => 
                  n.id === selectedNode.id ? { ...n, data: { ...n.data, label: e.target.value } } : n
                ));
              }} />
            </Form.Item>
            {selectedNode.type === 'agent' && (
              <Form.Item label="選擇 Agent">
                <Select
                  value={selectedNode.data.agentId}
                  onChange={(value) => {
                    setNodes(nds => nds.map(n => 
                      n.id === selectedNode.id ? { ...n, data: { ...n.data, agentId: value } } : n
                    ));
                  }}
                >
                  {/* Populate with agents from API */}
                </Select>
              </Form.Item>
            )}
            {/* Add more configuration fields based on node type */}
          </Form>
        )}
      </Drawer>
    </div>
  );
};
```

**自定義節點示例**:

```tsx
// nodes/AgentNode.tsx
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Card, Tag } from 'antd';
import { RobotOutlined } from '@ant-design/icons';

export const AgentNode = memo(({ data }: { data: any }) => {
  return (
    <Card
      size="small"
      style={{ width: 200, border: '2px solid #1890ff' }}
      title={
        <div>
          <RobotOutlined style={{ marginRight: 8 }} />
          {data.label || 'Agent 節點'}
        </div>
      }
    >
      <Handle type="target" position={Position.Top} />
      <div>
        {data.agentId ? (
          <Tag color="blue">{data.agentName}</Tag>
        ) : (
          <Tag color="red">未配置</Tag>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} />
    </Card>
  );
});
```

**API Endpoints**:

```python
# api/workflow.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

class WorkflowNode(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]
    position: Dict[str, float]

class WorkflowEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    status: str = "draft"  # draft, published

@router.post("/")
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """創建新 Workflow"""
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        definition={
            "nodes": [n.dict() for n in workflow.nodes],
            "edges": [e.dict() for e in workflow.edges]
        },
        status=workflow.status,
        version=1
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """更新 Workflow（創建新版本）"""
    old_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not old_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create new version
    new_version = old_workflow.version + 1
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        definition={
            "nodes": [n.dict() for n in workflow.nodes],
            "edges": [e.dict() for e in workflow.edges]
        },
        status=workflow.status,
        version=new_version,
        parent_id=old_workflow.id
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@router.get("/{workflow_id}/versions")
async def get_workflow_versions(workflow_id: str, db: Session = Depends(get_db)):
    """獲取 Workflow 歷史版本"""
    versions = db.query(Workflow).filter(
        (Workflow.id == workflow_id) | (Workflow.parent_id == workflow_id)
    ).order_by(desc(Workflow.version)).all()
    return versions
```

**測試策略**:

1. UI 測試：測試拖拉節點、連線、配置面板交互
2. 驗證測試：測試循環引用檢測、未連接節點檢測
3. 保存測試：測試草稿保存、版本發布、歷史版本查詢
4. 性能測試：測試包含 50+ 節點的大型 Workflow 編輯流暢度
5. 快捷鍵測試：測試 Ctrl+S、Ctrl+Z、Ctrl+Y 功能

---

#### **US-F13-003: Execution List（執行歷史）與 Agent Marketplace**

**User Story**:  
作為系統管理員，我希望查看所有 Workflow 執行歷史並按條件篩選，以便追蹤執行狀態和分析故障。同時，作為開發者，我希望從 Agent 商店發現和安裝新 Agent，以便快速擴展系統能力。

**場景描述（Execution List）**:

- 用戶進入執行歷史頁面
- 顯示所有 Workflow 執行記錄（分頁）
- 支持按 Workflow 名稱、狀態、時間範圍篩選
- 點擊執行記錄查看詳細日誌和輸入/輸出
- 支持手動重試失敗的執行

**場景描述（Agent Marketplace）**:

- 用戶瀏覽 Agent 商店
- 顯示官方和社區 Agent（帶評分、下載量、描述）
- 點擊 Agent 查看詳細說明和示例代碼
- 一鍵安裝 Agent 到系統
- 查看已安裝 Agent 列表和版本信息

**Acceptance Criteria（Execution List）**:

1. ✅ 顯示執行列表：Workflow 名稱、狀態、開始時間、執行時間、觸發方式
2. ✅ 支持狀態篩選：All / Running / Completed / Failed
3. ✅ 支持時間範圍篩選：今天、近 7 天、近 30 天、自定義範圍
4. ✅ 支持 Workflow 名稱模糊搜索
5. ✅ 點擊記錄進入詳情頁：顯示完整日誌、輸入參數、輸出結果、錯誤堆棧
6. ✅ 失敗執行提供「重試」按鈕
7. ✅ 分頁加載，每頁 50 條

**Acceptance Criteria（Agent Marketplace）**:

1. ✅ 顯示 Agent 卡片：名稱、圖標、簡短描述、評分、下載量
2. ✅ 支持分類篩選：客服、IT 運維、數據分析、辦公自動化、通用
3. ✅ 支持搜索 Agent 名稱和標籤
4. ✅ 點擊 Agent 查看詳情：完整描述、配置示例、API 文檔、評論
5. ✅ 一鍵安裝 Agent（顯示安裝進度）
6. ✅ 已安裝 Agent 顯示「已安裝」標籤和版本號
7. ✅ 支持更新 Agent 到最新版本

**UI Mockup（Execution List）**:

```tsx
// ExecutionList.tsx
import React, { useState } from 'react';
import { Table, Tag, Button, Input, Select, DatePicker, Drawer, Typography } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { useGetExecutionsQuery, useRetryExecutionMutation } from '@/api/executionApi';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Text } = Typography;

export const ExecutionList: React.FC = () => {
  const [filters, setFilters] = useState({
    status: 'all',
    workflowName: '',
    dateRange: [dayjs().subtract(7, 'day'), dayjs()],
  });
  const [selectedExecution, setSelectedExecution] = useState<any>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);

  const { data, isLoading } = useGetExecutionsQuery(filters);
  const [retryExecution] = useRetryExecutionMutation();

  const columns = [
    {
      title: 'Workflow 名稱',
      dataIndex: 'workflow_name',
      key: 'workflow_name',
      render: (text: string, record: any) => (
        <a onClick={() => { setSelectedExecution(record); setDrawerVisible(true); }}>
          {text}
        </a>
      ),
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: any = {
          running: 'processing',
          completed: 'success',
          failed: 'error',
        };
        return <Tag color={colorMap[status]}>{status.toUpperCase()}</Tag>;
      },
    },
    {
      title: '開始時間',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '執行時間',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration: number) => `${duration.toFixed(2)}s`,
    },
    {
      title: '觸發方式',
      dataIndex: 'trigger_type',
      key: 'trigger_type',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: any) => (
        record.status === 'failed' && (
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => retryExecution(record.id)}
          >
            重試
          </Button>
        )
      ),
    },
  ];

  return (
    <div>
      <h1>執行歷史</h1>
      <div style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索 Workflow 名稱"
          prefix={<SearchOutlined />}
          style={{ width: 300, marginRight: 8 }}
          onChange={(e) => setFilters({ ...filters, workflowName: e.target.value })}
        />
        <Select
          value={filters.status}
          style={{ width: 150, marginRight: 8 }}
          onChange={(status) => setFilters({ ...filters, status })}
        >
          <Select.Option value="all">全部狀態</Select.Option>
          <Select.Option value="running">Running</Select.Option>
          <Select.Option value="completed">Completed</Select.Option>
          <Select.Option value="failed">Failed</Select.Option>
        </Select>
        <RangePicker
          value={filters.dateRange as any}
          onChange={(dates: any) => setFilters({ ...filters, dateRange: dates })}
        />
      </div>

      <Table
        columns={columns}
        dataSource={data?.executions || []}
        loading={isLoading}
        pagination={{ pageSize: 50 }}
        rowKey="id"
      />

      <Drawer
        title="執行詳情"
        width={720}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedExecution && (
          <>
            <h3>輸入參數</h3>
            <pre>{JSON.stringify(selectedExecution.input, null, 2)}</pre>
            
            <h3>輸出結果</h3>
            <pre>{JSON.stringify(selectedExecution.output, null, 2)}</pre>
            
            <h3>執行日誌</h3>
            <div style={{ maxHeight: 400, overflow: 'auto' }}>
              {selectedExecution.logs?.map((log: string, i: number) => (
                <Text key={i} code style={{ display: 'block' }}>{log}</Text>
              ))}
            </div>
            
            {selectedExecution.status === 'failed' && (
              <>
                <h3>錯誤堆棧</h3>
                <pre style={{ color: 'red' }}>{selectedExecution.error_stack}</pre>
              </>
            )}
          </>
        )}
      </Drawer>
    </div>
  );
};
```

**UI Mockup（Agent Marketplace）**:

```tsx
// AgentMarketplace.tsx
import React, { useState } from 'react';
import { Card, Row, Col, Tag, Button, Input, Select, Drawer, Rate, message } from 'antd';
import { SearchOutlined, DownloadOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useGetAgentsQuery, useInstallAgentMutation } from '@/api/agentApi';

export const AgentMarketplace: React.FC = () => {
  const [filters, setFilters] = useState({ category: 'all', search: '' });
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);

  const { data: agents, isLoading } = useGetAgentsQuery(filters);
  const [installAgent, { isLoading: installing }] = useInstallAgentMutation();

  const handleInstall = async (agentId: string) => {
    try {
      await installAgent(agentId).unwrap();
      message.success('Agent 安裝成功');
    } catch (err) {
      message.error('安裝失敗');
    }
  };

  return (
    <div>
      <h1>Agent 商店</h1>
      <div style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索 Agent"
          prefix={<SearchOutlined />}
          style={{ width: 300, marginRight: 8 }}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        />
        <Select
          value={filters.category}
          style={{ width: 200 }}
          onChange={(category) => setFilters({ ...filters, category })}
        >
          <Select.Option value="all">全部分類</Select.Option>
          <Select.Option value="customer-service">客服</Select.Option>
          <Select.Option value="it-ops">IT 運維</Select.Option>
          <Select.Option value="data-analysis">數據分析</Select.Option>
          <Select.Option value="office-automation">辦公自動化</Select.Option>
        </Select>
      </div>

      <Row gutter={[16, 16]}>
        {agents?.map((agent: any) => (
          <Col span={6} key={agent.id}>
            <Card
              hoverable
              cover={<img alt={agent.name} src={agent.icon || '/default-agent-icon.png'} />}
              onClick={() => { setSelectedAgent(agent); setDrawerVisible(true); }}
            >
              <Card.Meta
                title={agent.name}
                description={
                  <>
                    <p>{agent.short_description}</p>
                    <Rate disabled value={agent.rating} style={{ fontSize: 14 }} />
                    <span style={{ marginLeft: 8 }}>{agent.downloads} 下載</span>
                    <br />
                    {agent.installed ? (
                      <Tag color="green" icon={<CheckCircleOutlined />}>已安裝</Tag>
                    ) : (
                      <Tag color="blue">可安裝</Tag>
                    )}
                  </>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Drawer
        title={selectedAgent?.name}
        width={720}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        extra={
          !selectedAgent?.installed && (
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              loading={installing}
              onClick={() => handleInstall(selectedAgent.id)}
            >
              安裝
            </Button>
          )
        }
      >
        {selectedAgent && (
          <>
            <h3>簡介</h3>
            <p>{selectedAgent.full_description}</p>
            
            <h3>配置示例</h3>
            <pre>{selectedAgent.config_example}</pre>
            
            <h3>API 文檔</h3>
            <a href={selectedAgent.api_docs_url} target="_blank" rel="noopener noreferrer">
              查看完整 API 文檔
            </a>
            
            <h3>評論</h3>
            {selectedAgent.reviews?.map((review: any, i: number) => (
              <div key={i} style={{ marginBottom: 8 }}>
                <Rate disabled value={review.rating} style={{ fontSize: 12 }} />
                <p>{review.comment}</p>
              </div>
            ))}
          </>
        )}
      </Drawer>
    </div>
  );
};
```

**API Endpoints**:

```python
# api/execution.py
@router.get("/executions")
async def get_executions(
    status: Optional[str] = None,
    workflow_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """獲取執行歷史列表"""
    query = db.query(WorkflowExecution)
    
    if status and status != 'all':
        query = query.filter(WorkflowExecution.status == status)
    if workflow_name:
        query = query.join(Workflow).filter(Workflow.name.ilike(f'%{workflow_name}%'))
    if start_date:
        query = query.filter(WorkflowExecution.started_at >= start_date)
    if end_date:
        query = query.filter(WorkflowExecution.started_at <= end_date)
    
    total = query.count()
    executions = query.order_by(desc(WorkflowExecution.started_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "executions": [
            {
                "id": e.id,
                "workflow_name": e.workflow.name,
                "status": e.status,
                "started_at": e.started_at.isoformat(),
                "duration": (e.completed_at - e.started_at).total_seconds() if e.completed_at else None,
                "trigger_type": e.trigger_type,
                "input": e.input_data,
                "output": e.output_data,
                "logs": e.logs,
                "error_stack": e.error_stack
            }
            for e in executions
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.post("/executions/{execution_id}/retry")
async def retry_execution(execution_id: str, db: Session = Depends(get_db)):
    """重試失敗的執行"""
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # Trigger new execution with same input
    new_execution = trigger_workflow(execution.workflow_id, execution.input_data)
    return {"new_execution_id": new_execution.id}

# api/agent.py
@router.get("/agents/marketplace")
async def get_marketplace_agents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """獲取 Agent 商店列表"""
    query = db.query(Agent).filter(Agent.is_public == True)
    
    if category and category != 'all':
        query = query.filter(Agent.category == category)
    if search:
        query = query.filter(Agent.name.ilike(f'%{search}%') | Agent.description.ilike(f'%{search}%'))
    
    agents = query.order_by(desc(Agent.downloads)).all()
    
    return [
        {
            "id": a.id,
            "name": a.name,
            "short_description": a.short_description,
            "icon": a.icon_url,
            "rating": a.average_rating,
            "downloads": a.downloads,
            "installed": a.is_installed,
            "category": a.category
        }
        for a in agents
    ]

@router.post("/agents/{agent_id}/install")
async def install_agent(agent_id: str, db: Session = Depends(get_db)):
    """安裝 Agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Mark as installed
    agent.is_installed = True
    agent.downloads += 1
    db.commit()
    
    return {"status": "installed", "agent_id": agent_id}
```

**測試策略**:

1. UI 測試：測試篩選、搜索、分頁、詳情抽屜
2. API 測試：測試執行列表查詢、重試功能、Agent 安裝
3. 性能測試：測試 10 萬條執行記錄的查詢性能
4. 權限測試：測試非管理員無法重試他人的執行

---

#### **US-F13-004: 集成監控、審計、DLQ、Prompt 管理頁面**

**User Story**:  
作為系統管理員，我希望在統一的 Web UI 中訪問監控儀表板、審計日誌、DLQ 管理、Prompt 編輯器，以便集中管理所有系統功能。

**場景描述**:

- 用戶從頂部導航欄訪問不同功能模塊
- **Monitoring Dashboard**：實時查看系統指標（集成 F12）
- **Audit Logs**：搜索和過濾審計日誌（集成 F10）
- **DLQ Management**：查看死信隊列並重試（集成 F8）
- **Prompt Editor**：編輯和測試 Prompt 模板（集成 F9）

**Acceptance Criteria**:

1. ✅ 頂部導航欄包含：Dashboard、Workflows、Executions、Agents、Monitoring、Audit Logs、DLQ、Prompts
2. ✅ Monitoring Dashboard 顯示實時指標圖表（ECharts），支持自定義時間範圍
3. ✅ Audit Logs 頁面支持按用戶、操作類型、時間範圍篩選
4. ✅ DLQ Management 頁面顯示失敗執行列表，支持批量重試
5. ✅ Prompt Editor 使用 Monaco Editor 編輯 YAML 模板，提供語法高亮和自動完成
6. ✅ Prompt Editor 提供預覽功能（輸入示例變量，實時渲染結果）
7. ✅ 所有頁面統一風格（Ant Design 主題），響應式佈局

**UI Mockup（Monitoring Dashboard 集成）**:

```tsx
// MonitoringPage.tsx
import React, { useState } from 'react';
import { Card, Select, DatePicker } from 'antd';
import * as echarts from 'echarts';
import { useGetMetricsQuery } from '@/api/monitoringApi';

export const MonitoringPage: React.FC = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const { data: metrics } = useGetMetricsQuery({ range: timeRange });

  const chartOption = {
    title: { text: 'Workflow 執行趨勢' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['成功', '失敗'] },
    xAxis: { type: 'category', data: metrics?.timestamps || [] },
    yAxis: { type: 'value' },
    series: [
      { name: '成功', type: 'line', data: metrics?.success_counts || [] },
      { name: '失敗', type: 'line', data: metrics?.failure_counts || [] },
    ],
  };

  return (
    <div>
      <h1>系統監控</h1>
      <Select value={timeRange} onChange={setTimeRange} style={{ marginBottom: 16 }}>
        <Select.Option value="1h">最近 1 小時</Select.Option>
        <Select.Option value="24h">最近 24 小時</Select.Option>
        <Select.Option value="7d">最近 7 天</Select.Option>
      </Select>
      <Card>
        <div ref={(ref) => ref && echarts.init(ref).setOption(chartOption)} style={{ height: 400 }} />
      </Card>
    </div>
  );
};
```

**UI Mockup（Audit Logs 集成）**:

```tsx
// AuditLogsPage.tsx
import React, { useState } from 'react';
import { Table, Input, Select, DatePicker } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useGetAuditLogsQuery } from '@/api/auditApi';

export const AuditLogsPage: React.FC = () => {
  const [filters, setFilters] = useState({ user: '', action: 'all', dateRange: null });
  const { data, isLoading } = useGetAuditLogsQuery(filters);

  const columns = [
    { title: '時間', dataIndex: 'timestamp', key: 'timestamp' },
    { title: '用戶', dataIndex: 'user', key: 'user' },
    { title: '操作', dataIndex: 'action', key: 'action' },
    { title: '資源', dataIndex: 'resource', key: 'resource' },
    { title: '變更內容', dataIndex: 'changes', key: 'changes', render: (v: any) => JSON.stringify(v) },
  ];

  return (
    <div>
      <h1>審計日誌</h1>
      <div style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索用戶"
          prefix={<SearchOutlined />}
          style={{ width: 200, marginRight: 8 }}
          onChange={(e) => setFilters({ ...filters, user: e.target.value })}
        />
        <Select
          value={filters.action}
          style={{ width: 150 }}
          onChange={(action) => setFilters({ ...filters, action })}
        >
          <Select.Option value="all">全部操作</Select.Option>
          <Select.Option value="create">創建</Select.Option>
          <Select.Option value="update">更新</Select.Option>
          <Select.Option value="delete">刪除</Select.Option>
        </Select>
      </div>
      <Table columns={columns} dataSource={data?.logs || []} loading={isLoading} rowKey="id" />
    </div>
  );
};
```

**UI Mockup（DLQ Management 集成）**:

```tsx
// DLQPage.tsx
import React from 'react';
import { Table, Button, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useGetDLQQuery, useRetryDLQMutation } from '@/api/dlqApi';

export const DLQPage: React.FC = () => {
  const { data, isLoading } = useGetDLQQuery();
  const [retryDLQ] = useRetryDLQMutation();

  const handleRetry = async (id: string) => {
    try {
      await retryDLQ(id).unwrap();
      message.success('重試已觸發');
    } catch (err) {
      message.error('重試失敗');
    }
  };

  const columns = [
    { title: 'Workflow', dataIndex: 'workflow_name', key: 'workflow_name' },
    { title: '錯誤信息', dataIndex: 'error_message', key: 'error_message' },
    { title: '失敗時間', dataIndex: 'failed_at', key: 'failed_at' },
    { title: '重試次數', dataIndex: 'retry_count', key: 'retry_count' },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: any) => (
        <Button icon={<ReloadOutlined />} onClick={() => handleRetry(record.id)}>
          重試
        </Button>
      ),
    },
  ];

  return (
    <div>
      <h1>死信隊列（DLQ）</h1>
      <Table columns={columns} dataSource={data?.dlq_items || []} loading={isLoading} rowKey="id" />
    </div>
  );
};
```

**UI Mockup（Prompt Editor 集成）**:

```tsx
// PromptEditorPage.tsx
import React, { useState } from 'react';
import { Row, Col, Card, Button, Form, Input, message } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import { useGetPromptsQuery, useUpdatePromptMutation } from '@/api/promptApi';

export const PromptEditorPage: React.FC = () => {
  const { data: prompts } = useGetPromptsQuery();
  const [selectedPrompt, setSelectedPrompt] = useState<any>(null);
  const [previewVariables, setPreviewVariables] = useState<any>({});
  const [updatePrompt] = useUpdatePromptMutation();

  const handleSave = async () => {
    try {
      await updatePrompt({ id: selectedPrompt.id, content: selectedPrompt.content }).unwrap();
      message.success('Prompt 已保存');
    } catch (err) {
      message.error('保存失敗');
    }
  };

  const renderPreview = () => {
    // Replace variables in prompt template
    let preview = selectedPrompt?.content || '';
    Object.keys(previewVariables).forEach((key) => {
      preview = preview.replace(`{${key}}`, previewVariables[key]);
    });
    return preview;
  };

  return (
    <div>
      <h1>Prompt 編輯器</h1>
      <Row gutter={16}>
        <Col span={6}>
          <Card title="Prompt 列表">
            {prompts?.map((p: any) => (
              <div key={p.id} onClick={() => setSelectedPrompt(p)} style={{ cursor: 'pointer', marginBottom: 8 }}>
                {p.name}
              </div>
            ))}
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title="編輯 Prompt"
            extra={<Button icon={<SaveOutlined />} onClick={handleSave}>保存</Button>}
          >
            <Editor
              height="400px"
              language="yaml"
              value={selectedPrompt?.content}
              onChange={(value) => setSelectedPrompt({ ...selectedPrompt, content: value })}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card title="預覽">
            <Form layout="vertical">
              <Form.Item label="customer_name">
                <Input onChange={(e) => setPreviewVariables({ ...previewVariables, customer_name: e.target.value })} />
              </Form.Item>
              {/* Add more variable inputs */}
            </Form>
            <pre>{renderPreview()}</pre>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
```

**路由配置**:

```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { HomePage } from './pages/HomePage';
import { WorkflowBuilder } from './pages/WorkflowBuilder';
import { ExecutionList } from './pages/ExecutionList';
import { AgentMarketplace } from './pages/AgentMarketplace';
import { MonitoringPage } from './pages/MonitoringPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { DLQPage } from './pages/DLQPage';
import { PromptEditorPage } from './pages/PromptEditorPage';

const { Header, Content } = Layout;

export const App = () => {
  return (
    <BrowserRouter>
      <Layout>
        <Header>
          <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['dashboard']}>
            <Menu.Item key="dashboard"><a href="/">Dashboard</a></Menu.Item>
            <Menu.Item key="workflows"><a href="/workflows">Workflows</a></Menu.Item>
            <Menu.Item key="executions"><a href="/executions">Executions</a></Menu.Item>
            <Menu.Item key="agents"><a href="/agents">Agents</a></Menu.Item>
            <Menu.Item key="monitoring"><a href="/monitoring">Monitoring</a></Menu.Item>
            <Menu.Item key="audit"><a href="/audit">Audit Logs</a></Menu.Item>
            <Menu.Item key="dlq"><a href="/dlq">DLQ</a></Menu.Item>
            <Menu.Item key="prompts"><a href="/prompts">Prompts</a></Menu.Item>
          </Menu>
        </Header>
        <Content style={{ padding: '24px' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/workflows/new" element={<WorkflowBuilder />} />
            <Route path="/workflows/:id" element={<WorkflowBuilder />} />
            <Route path="/executions" element={<ExecutionList />} />
            <Route path="/agents/marketplace" element={<AgentMarketplace />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/audit" element={<AuditLogsPage />} />
            <Route path="/dlq" element={<DLQPage />} />
            <Route path="/prompts" element={<PromptEditorPage />} />
          </Routes>
        </Content>
      </Layout>
    </BrowserRouter>
  );
};
```

**測試策略**:

1. E2E 測試：使用 Cypress 測試完整用戶流程（登入 → 創建 Workflow → 執行 → 查看日誌）
2. 路由測試：測試所有頁面導航和深層連結
3. 權限測試：測試不同角色訪問不同頁面的權限
4. 響應式測試：在桌面、平板、手機尺寸下測試所有頁面

---

### 13.3 數據庫架構（UI 特定表）

```sql
-- 用戶偏好設置表
CREATE TABLE user_preferences (
    user_id VARCHAR(100) PRIMARY KEY,
    theme VARCHAR(20) DEFAULT 'light',  -- light, dark
    language VARCHAR(10) DEFAULT 'zh-TW',  -- zh-TW, en-US, ja-JP
    dashboard_layout JSONB,  -- 自定義 Dashboard 卡片順序
    default_time_range VARCHAR(10) DEFAULT '7d',  -- 1h, 24h, 7d, 30d
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 自定義視圖表（保存用戶自定義的篩選條件）
CREATE TABLE saved_views (
    view_id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    view_name VARCHAR(200) NOT NULL,
    view_type VARCHAR(50) NOT NULL,  -- executions, agents, audit_logs
    filters JSONB NOT NULL,  -- {"status": "failed", "date_range": ["2024-01-01", "2024-12-31"]}
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, view_name, view_type)
);

-- UI 操作日誌表（追蹤用戶在 UI 上的操作）
CREATE TABLE ui_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    page VARCHAR(100) NOT NULL,  -- dashboard, workflow_builder, executions
    action VARCHAR(100) NOT NULL,  -- view, edit, delete, retry
    resource_type VARCHAR(50),  -- workflow, agent, prompt
    resource_id VARCHAR(100),
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ui_activity_user ON ui_activity_logs(user_id, timestamp DESC);
CREATE INDEX idx_saved_views_user ON saved_views(user_id, view_type);
```

---

### 13.4 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **性能** | 首屏加載時間 | <2 秒 | Lighthouse 性能評分 >90 |
| | API 響應時間 | <300ms（P95） | APM 監控 |
| | 圖表渲染時間 | <500ms（1000 數據點） | 前端性能監控 |
| **可用性** | 頁面可訪問性 | WCAG 2.1 AA 級 | 自動化 a11y 測試 |
| | 瀏覽器兼容性 | Chrome 90+, Firefox 88+, Safari 14+ | BrowserStack 測試 |
| **可擴展性** | 並發用戶數 | 100+ 並發用戶 | 負載測試 |
| | 數據表格行數 | 支持 10 萬行虛擬滾動 | 前端性能測試 |
| **安全性** | XSS 防護 | 100% 用戶輸入轉義 | 安全掃描 |
| | CSRF 防護 | 所有 POST 請求驗證 Token | 滲透測試 |

---

### 13.5 測試策略

**單元測試（React Testing Library）**:

- 測試各組件的渲染和交互（按鈕點擊、表單提交）
- 測試 Redux 狀態管理邏輯
- 測試工具函數（日期格式化、數據轉換）

**集成測試（RTK Query）**:

- 測試 API 調用和數據緩存
- 測試錯誤處理和重試邏輯

**E2E 測試（Cypress）**:

- 測試完整用戶流程：登入 → 創建 Workflow → 執行 → 查看監控
- 測試頁面導航和深層連結
- 測試表單驗證和錯誤提示

**性能測試**:

- 使用 Lighthouse 測試首屏加載時間
- 使用 React Profiler 分析組件渲染性能
- 測試大數據表格（10 萬行）的滾動流暢度

**可訪問性測試**:

- 使用 axe-core 自動化測試 WCAG 合規性
- 鍵盤導航測試（Tab、Enter、Escape）
- 屏幕閱讀器測試（NVDA、JAWS）

**跨瀏覽器測試**:

- 在 Chrome、Firefox、Safari、Edge 上測試
- 在不同屏幕尺寸（桌面、平板、手機）上測試

---

### 13.6 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| 大型 Workflow 編輯器性能問題 | 中 | 中 | 虛擬化渲染 + 節點懶加載 |
| 前端包體積過大 | 高 | 低 | 代碼分割 + 動態導入 + Tree Shaking |
| 實時數據刷新導致閃爍 | 中 | 低 | 使用樂觀更新 + 防抖 |
| 瀏覽器兼容性問題 | 低 | 中 | Polyfill + 跨瀏覽器測試 |
| 安全漏洞（XSS、CSRF） | 低 | 高 | 輸入驗證 + CSP 策略 + 定期掃描 |

---

### 13.7 未來增強（MVP 後）

1. **深色模式**: 支持深色主題切換
2. **多語言**: 支持英文、日文、西班牙文
3. **移動端應用**: 開發 iOS/Android 原生應用
4. **協作功能**: 多人實時編輯 Workflow（WebSocket）
5. **AI 助手**: 使用 AI 建議 Workflow 優化方案
6. **離線模式**: 支持離線查看和編輯（PWA）

---

**✅ F13 完成**：現代化 Web UI 功能規範已完整編寫（4 個用戶故事、8 個核心頁面、數據庫架構、NFR、測試策略）。

---
