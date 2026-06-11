# Sprint 5: 前端 UI

**Sprint 目標**: 建立現代化 React 前端界面和監控儀表板
**週期**: Week 11-12 (2 週)
**Story Points**: 45 點
**MVP 功能**: F12 (監控儀表板), F13 (現代 Web UI)

---

## Sprint 概覽

### 目標
1. 建立 React 18 + TypeScript 前端架構
2. 實現核心頁面 (Dashboard, Workflows, Agents)
3. 建立監控儀表板
4. 實現審批工作台
5. 建立統一設計系統

### 成功標準
- [ ] Dashboard 可顯示關鍵指標
- [ ] 工作流列表和詳情頁面可用
- [ ] Agent 管理頁面可用
- [ ] 審批工作台可處理待審批項目
- [ ] 頁面加載時間 < 2 秒

---

## 技術架構

### 前端技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| React | 18+ | UI 框架 |
| TypeScript | 5+ | 類型安全 |
| Vite | 5+ | 構建工具 |
| TailwindCSS | 3+ | 樣式框架 |
| Shadcn/ui | - | UI 組件庫 |
| TanStack Query | 5+ | 數據獲取 |
| React Router | 6+ | 路由 |
| Zustand | 4+ | 狀態管理 |
| Recharts | 2+ | 圖表 |

### 架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Application                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                       App Shell                              │ │
│  │  ┌──────────┐  ┌─────────────────────────────────────────┐  │ │
│  │  │ Sidebar  │  │              Main Content               │  │ │
│  │  │          │  │  ┌─────────────────────────────────┐   │  │ │
│  │  │ ◉ Dash   │  │  │         Page Component          │   │  │ │
│  │  │ ◯ Work   │  │  │                                 │   │  │ │
│  │  │ ◯ Agent  │  │  │                                 │   │  │ │
│  │  │ ◯ Aprv   │  │  │                                 │   │  │ │
│  │  │ ◯ Audit  │  │  └─────────────────────────────────┘   │  │ │
│  │  └──────────┘  └─────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      State Layer                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │ │
│  │  │ TanStack │  │ Zustand  │  │  React   │  │  Local   │    │ │
│  │  │  Query   │  │  Store   │  │ Context  │  │ Storage  │    │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                      ┌───────▼───────┐                           │
│                      │   API Client  │                           │
│                      │   (Fetch)     │                           │
│                      └───────┬───────┘                           │
│                              │                                    │
└──────────────────────────────┼────────────────────────────────────┘
                               │
                       ┌───────▼───────┐
                       │  Backend API  │
                       │  (FastAPI)    │
                       └───────────────┘
```

---

## User Stories

### S5-1: 前端架構設置 (8 點)

**描述**: 作為開發者，我需要建立前端基礎架構。

**驗收標準**:
- [ ] Vite + React + TypeScript 項目創建
- [ ] TailwindCSS + Shadcn/ui 配置
- [ ] 路由結構配置
- [ ] API 客戶端封裝
- [ ] 基礎佈局組件

**技術任務**:

1. **項目結構**
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Shadcn 組件
│   │   ├── layout/          # 佈局組件
│   │   └── shared/          # 共享組件
│   ├── pages/
│   │   ├── dashboard/
│   │   ├── workflows/
│   │   ├── agents/
│   │   ├── approvals/
│   │   └── audit/
│   ├── hooks/               # 自定義 Hooks
│   ├── lib/                 # 工具函數
│   ├── api/                 # API 客戶端
│   ├── store/               # 狀態管理
│   └── types/               # 類型定義
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

2. **API 客戶端 (src/api/client.ts)**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

interface ApiResponse<T> {
  data: T;
  error?: string;
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API Error');
  }

  const data = await response.json();
  return { data };
}

export const api = {
  get: <T>(endpoint: string) => fetchApi<T>(endpoint),
  post: <T>(endpoint: string, body: unknown) =>
    fetchApi<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(endpoint: string, body: unknown) =>
    fetchApi<T>(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
  delete: <T>(endpoint: string) =>
    fetchApi<T>(endpoint, { method: 'DELETE' }),
};
```

3. **佈局組件 (src/components/layout/AppLayout.tsx)**
```tsx
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export function AppLayout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

---

### S5-2: Dashboard 頁面 (10 點)

**描述**: 作為業務用戶，我需要一個儀表板來查看系統概覽。

**驗收標準**:
- [ ] 顯示關鍵業務指標
- [ ] 顯示執行統計圖表
- [ ] 顯示最近執行列表
- [ ] 顯示待審批數量

**技術任務**:

1. **Dashboard 頁面 (src/pages/dashboard/DashboardPage.tsx)**
```tsx
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/api/client';
import { StatsCards } from './components/StatsCards';
import { ExecutionChart } from './components/ExecutionChart';
import { RecentExecutions } from './components/RecentExecutions';
import { PendingApprovals } from './components/PendingApprovals';

interface DashboardStats {
  total_workflows: number;
  total_executions: number;
  success_rate: number;
  pending_approvals: number;
  llm_cost_today: number;
}

export function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get<DashboardStats>('/dashboard/stats'),
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <StatsCards stats={stats?.data} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>執行統計</CardTitle>
          </CardHeader>
          <CardContent>
            <ExecutionChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>待審批項目</CardTitle>
          </CardHeader>
          <CardContent>
            <PendingApprovals />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>最近執行</CardTitle>
        </CardHeader>
        <CardContent>
          <RecentExecutions />
        </CardContent>
      </Card>
    </div>
  );
}
```

2. **統計卡片 (src/pages/dashboard/components/StatsCards.tsx)**
```tsx
import { Card, CardContent } from '@/components/ui/card';
import {
  PlayCircle,
  CheckCircle,
  Clock,
  DollarSign,
} from 'lucide-react';

interface StatsCardsProps {
  stats?: {
    total_workflows: number;
    total_executions: number;
    success_rate: number;
    pending_approvals: number;
    llm_cost_today: number;
  };
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: '總執行數',
      value: stats?.total_executions || 0,
      icon: PlayCircle,
      color: 'text-blue-500',
    },
    {
      title: '成功率',
      value: `${((stats?.success_rate || 0) * 100).toFixed(1)}%`,
      icon: CheckCircle,
      color: 'text-green-500',
    },
    {
      title: '待審批',
      value: stats?.pending_approvals || 0,
      icon: Clock,
      color: 'text-orange-500',
    },
    {
      title: '今日 LLM 成本',
      value: `$${(stats?.llm_cost_today || 0).toFixed(2)}`,
      icon: DollarSign,
      color: 'text-purple-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{card.title}</p>
                <p className="text-2xl font-bold">{card.value}</p>
              </div>
              <card.icon className={`h-8 w-8 ${card.color}`} />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

---

### S5-3: 工作流管理頁面 (10 點)

**描述**: 作為開發者，我需要管理工作流的頁面。

**驗收標準**:
- [ ] 工作流列表頁面
- [ ] 工作流詳情頁面
- [ ] 工作流執行觸發
- [ ] 執行歷史查看

---

### S5-4: Agent 管理頁面 (8 點)

**描述**: 作為開發者，我需要管理 Agent 的頁面。

**驗收標準**:
- [ ] Agent 列表頁面
- [ ] Agent 詳情頁面
- [ ] 從模板創建 Agent
- [ ] Agent 測試運行

---

### S5-5: 審批工作台 (9 點)

**描述**: 作為業務用戶，我需要審批工作台來處理待審批項目。

**驗收標準**:
- [ ] 待審批列表
- [ ] 審批詳情查看
- [ ] 批准/拒絕操作
- [ ] 提供反饋

**技術任務**:

1. **審批頁面 (src/pages/approvals/ApprovalsPage.tsx)**
```tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { api } from '@/api/client';

interface Checkpoint {
  id: string;
  execution_id: string;
  workflow_name: string;
  step: number;
  status: string;
  created_at: string;
  content: string;
}

export function ApprovalsPage() {
  const queryClient = useQueryClient();
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<Checkpoint | null>(null);
  const [feedback, setFeedback] = useState('');

  const { data: checkpoints, isLoading } = useQuery({
    queryKey: ['pending-checkpoints'],
    queryFn: () => api.get<Checkpoint[]>('/checkpoints/pending'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) =>
      api.post(`/checkpoints/${id}/approve`, { feedback }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-checkpoints'] });
      setSelectedCheckpoint(null);
      setFeedback('');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) =>
      api.post(`/checkpoints/${id}/reject`, { reason: feedback }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-checkpoints'] });
      setSelectedCheckpoint(null);
      setFeedback('');
    },
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">審批工作台</h1>

      <div className="grid gap-4">
        {checkpoints?.data.map((checkpoint) => (
          <Card key={checkpoint.id}>
            <CardHeader>
              <CardTitle className="text-lg">
                {checkpoint.workflow_name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-500">
                    Step {checkpoint.step} · {checkpoint.created_at}
                  </p>
                </div>
                <Button onClick={() => setSelectedCheckpoint(checkpoint)}>
                  查看詳情
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog
        open={!!selectedCheckpoint}
        onOpenChange={() => setSelectedCheckpoint(null)}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>審批詳情</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded">
              <pre className="whitespace-pre-wrap">
                {selectedCheckpoint?.content}
              </pre>
            </div>

            <Textarea
              placeholder="提供反饋 (可選)"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />

            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => rejectMutation.mutate(selectedCheckpoint!.id)}
              >
                拒絕
              </Button>
              <Button
                onClick={() => approveMutation.mutate(selectedCheckpoint!.id)}
              >
                批准
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

---

## 頁面清單

| 頁面 | 路由 | 優先級 | 描述 |
|------|------|--------|------|
| Dashboard | / | P0 | 系統概覽和關鍵指標 |
| Workflows | /workflows | P0 | 工作流列表和管理 |
| Workflow Detail | /workflows/:id | P0 | 工作流詳情和執行 |
| Agents | /agents | P0 | Agent 列表和管理 |
| Agent Detail | /agents/:id | P1 | Agent 詳情和測試 |
| Templates | /templates | P1 | 模板市場 |
| Approvals | /approvals | P0 | 審批工作台 |
| Audit | /audit | P1 | 審計日誌查詢 |
| Settings | /settings | P2 | 系統設置 |

---

## 時間規劃

### Week 11 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S5-1: 項目設置 + 路由 | Frontend | 基礎架構 |
| Day 2-3 | S5-1: 佈局組件 + API 客戶端 | Frontend | 共享組件 |
| Day 3-4 | S5-2: Dashboard 統計卡片 | Frontend | StatsCards |
| Day 4-5 | S5-2: Dashboard 圖表 | Frontend | ExecutionChart |

### Week 12 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S5-3: 工作流頁面 | Frontend | WorkflowsPage |
| Day 7-8 | S5-4: Agent 頁面 | Frontend | AgentsPage |
| Day 8-9 | S5-5: 審批工作台 | Frontend | ApprovalsPage |
| Day 9-10 | 集成測試 + 優化 | 全員 | E2E 測試 |

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] 所有 P0 頁面可用
   - [ ] API 集成正常
   - [ ] 響應式設計

2. **性能要求**
   - [ ] 首屏加載 < 2 秒
   - [ ] 頁面切換 < 500ms
   - [ ] Lighthouse 分數 > 80

3. **測試完成**
   - [ ] 組件測試覆蓋
   - [ ] E2E 測試主要流程

---

## 相關文檔

- [Sprint 5 Checklist](./sprint-5-checklist.md)
- [Sprint 4 Plan](./sprint-4-plan.md) - 前置 Sprint
- [Sprint 6 Plan](./sprint-6-plan.md) - 後續 Sprint
- [UI/UX 設計規格](../../01-planning/ui-ux/)
