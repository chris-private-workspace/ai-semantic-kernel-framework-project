# Sprint 4: UI & Frontend Development - 詳細規劃

**版本**: 1.0  
**創建日期**: 2025-11-19  
**Sprint 期間**: 2026-01-20 至 2026-01-31 (2週)  
**團隊規模**: 8人

---

## 📋 Sprint 目標

構建完整的 Web UI 和用戶體驗，實現核心功能的前端界面。

### 核心目標
1. ✅ 實現 React 18 應用架構
2. ✅ 構建 Design System（基於 Shadcn UI）
3. ✅ 實現 Dashboard 和實時指標
4. ✅ 構建拖拽式工作流編輯器
5. ✅ 實現執行監控視圖
6. ✅ 響應式設計（桌面 + 平板）

### 成功標準
- 用戶可以在 UI 中創建和管理工作流
- Dashboard 顯示實時系統狀態
- 工作流編輯器支持拖拽和配置
- 所有頁面響應式設計
- Lighthouse 性能得分 ≥ 90

---

## 📊 Story Points 分配

**總計劃點數**: 42

**按優先級分配**:
- P0 (Critical): 34 點 (81%)
- P1 (High): 8 點 (19%)

---

## 🎯 Sprint Backlog

### S4-1: React App Initialization
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Frontend Lead  
**依賴**: S0-3 (CI/CD Pipeline)

#### 描述

初始化 React 18 應用，配置 Vite、TypeScript、路由、狀態管理。

#### 驗收標準
- [ ] Vite + React 18 + TypeScript 配置完成
- [ ] React Router 6 路由配置
- [ ] TanStack Query 數據獲取配置
- [ ] Zustand 全局狀態管理
- [ ] Axios 配置（API 客戶端）
- [ ] 環境變量配置（.env）

#### 技術實現細節

**1. 項目初始化**

```bash
# 創建 Vite 項目
npm create vite@latest ipa-platform-frontend -- --template react-ts

# 安裝依賴
npm install react-router-dom @tanstack/react-query axios zustand
npm install -D @types/node

# 安裝 UI 庫
npm install @radix-ui/react-slot class-variance-authority clsx tailwind-merge
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**2. 項目結構**

```
src/
├── api/                  # API 客戶端
│   ├── client.ts
│   ├── workflows.ts
│   ├── executions.ts
│   └── auth.ts
├── components/           # 通用組件
│   ├── ui/              # Shadcn UI 組件
│   ├── layout/          # 佈局組件
│   └── shared/          # 共享組件
├── features/            # 功能模塊
│   ├── workflows/
│   ├── executions/
│   ├── agents/
│   └── dashboard/
├── hooks/               # 自定義 hooks
├── lib/                 # 工具函數
├── store/               # Zustand stores
├── types/               # TypeScript 類型
├── App.tsx
└── main.tsx
```

**3. API 客戶端配置**

```typescript
// src/api/client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器：添加 JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 響應攔截器：處理錯誤
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 過期，跳轉到登錄頁
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**4. React Query 配置**

```typescript
// src/lib/react-query.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 分鐘
      cacheTime: 1000 * 60 * 10, // 10 分鐘
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// src/main.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/react-query';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

**5. 路由配置**

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { LoginPage } from './features/auth/LoginPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { WorkflowListPage } from './features/workflows/WorkflowListPage';
import { WorkflowEditorPage } from './features/workflows/WorkflowEditorPage';
import { ExecutionDetailPage } from './features/executions/ExecutionDetailPage';
import { ProtectedRoute } from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/workflows" element={<WorkflowListPage />} />
          <Route path="/workflows/new" element={<WorkflowEditorPage />} />
          <Route path="/workflows/:id/edit" element={<WorkflowEditorPage />} />
          <Route path="/executions/:id" element={<ExecutionDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

**6. 全局狀態管理（Zustand）**

```typescript
// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

interface AuthState {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      login: (user, token) => {
        set({ user, token });
        localStorage.setItem('access_token', token);
      },
      logout: () => {
        set({ user: null, token: null });
        localStorage.removeItem('access_token');
      },
      isAuthenticated: () => !!get().token,
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

#### 子任務

1. [ ] 初始化 Vite 項目
2. [ ] 配置 TypeScript
3. [ ] 設置項目結構
4. [ ] 配置 API 客戶端（Axios）
5. [ ] 配置 React Query
6. [ ] 配置路由（React Router）
7. [ ] 配置全局狀態（Zustand）
8. [ ] 編寫基礎組件（ProtectedRoute）

---

### S4-2: Design System Implementation (Shadcn UI)
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Frontend Lead + Frontend Engineer  
**依賴**: S4-1 (React App Initialization)

#### 描述

實現基於 Shadcn UI 的 Design System，構建可重用的 UI 組件庫。

#### 驗收標準
- [ ] Tailwind CSS 配置完成
- [ ] 實現核心 UI 組件（Button, Input, Card, Modal, Table）
- [ ] 組件有統一的主題和樣式
- [ ] 組件支持暗色模式
- [ ] Storybook 文檔

#### 技術實現細節

**1. Tailwind CSS 配置**

```typescript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

**2. Button 組件**

```typescript
// src/components/ui/Button.tsx
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
```

**3. Card 組件**

```typescript
// src/components/ui/Card.tsx
import * as React from 'react';
import { cn } from '@/lib/utils';

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('rounded-lg border bg-card text-card-foreground shadow-sm', className)}
      {...props}
    />
  )
);
Card.displayName = 'Card';

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />
  )
);
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-2xl font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
);
CardTitle.displayName = 'CardTitle';

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
);
CardContent.displayName = 'CardContent';

export { Card, CardHeader, CardTitle, CardContent };
```

**4. Modal (Dialog) 組件**

```typescript
// src/components/ui/Dialog.tsx
import * as React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

const Dialog = DialogPrimitive.Root;
const DialogTrigger = DialogPrimitive.Trigger;

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      'fixed inset-0 z-50 bg-background/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
      className
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        'fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg',
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

export { Dialog, DialogTrigger, DialogContent };
```

**5. Table 組件**

```typescript
// src/components/ui/Table.tsx
import * as React from 'react';
import { cn } from '@/lib/utils';

const Table = React.forwardRef<HTMLTableElement, React.HTMLAttributes<HTMLTableElement>>(
  ({ className, ...props }, ref) => (
    <div className="relative w-full overflow-auto">
      <table ref={ref} className={cn('w-full caption-bottom text-sm', className)} {...props} />
    </div>
  )
);
Table.displayName = 'Table';

const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <thead ref={ref} className={cn('[&_tr]:border-b', className)} {...props} />
));
TableHeader.displayName = 'TableHeader';

const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tbody ref={ref} className={cn('[&_tr:last-child]:border-0', className)} {...props} />
));
TableBody.displayName = 'TableBody';

const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
  ({ className, ...props }, ref) => (
    <tr
      ref={ref}
      className={cn(
        'border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted',
        className
      )}
      {...props}
    />
  )
);
TableRow.displayName = 'TableRow';

const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <td ref={ref} className={cn('p-4 align-middle [&:has([role=checkbox])]:pr-0', className)} {...props} />
  )
);
TableCell.displayName = 'TableCell';

export { Table, TableHeader, TableBody, TableRow, TableCell };
```

#### 子任務

1. [ ] 配置 Tailwind CSS
2. [ ] 創建 Button 組件
3. [ ] 創建 Input 組件
4. [ ] 創建 Card 組件
5. [ ] 創建 Modal (Dialog) 組件
6. [ ] 創建 Table 組件
7. [ ] 配置暗色模式切換
8. [ ] 設置 Storybook（可選）

---

### S4-3: Authentication UI
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Frontend Engineer  
**依賴**: S4-2 (Design System), S0-7 (Auth Framework)

#### 描述

實現登錄、登出、會話管理的前端界面。

#### 驗收標準
- [ ] 登錄頁面 UI
- [ ] OAuth 2.0 登錄流程
- [ ] JWT token 管理
- [ ] 自動刷新 token
- [ ] 登出功能

#### 技術實現細節

**1. 登錄頁面**

```typescript
// src/features/auth/LoginPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { useAuthStore } from '@/store/authStore';
import { login as apiLogin } from '@/api/auth';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiLogin(email, password);
      login(response.user, response.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center text-2xl">IPA Platform</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>
          
          <div className="mt-4 text-center">
            <Button variant="outline" onClick={() => window.location.href = '/api/auth/azure'}>
              Login with Azure AD
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

**2. Auth API**

```typescript
// src/api/auth.ts
import { apiClient } from './client';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
    roles: string[];
  };
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await apiClient.post('/api/auth/login', { email, password });
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/auth/logout');
}

export async function refreshToken(): Promise<LoginResponse> {
  const response = await apiClient.post('/api/auth/refresh');
  return response.data;
}
```

#### 子任務

1. [ ] 創建登錄頁面
2. [ ] 實現表單驗證
3. [ ] 集成 OAuth 2.0 流程
4. [ ] 實現 token 刷新邏輯
5. [ ] 實現登出功能
6. [ ] 編寫 E2E 測試

---

### S4-4: Dashboard Implementation
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Frontend Engineer  
**依賴**: S4-2 (Design System), S2-8 (Admin Dashboard APIs)

#### 描述

實現主 Dashboard，顯示實時系統指標和統計數據。

#### 驗收標準
- [ ] 顯示工作流/執行統計
- [ ] 實時更新執行狀態
- [ ] 顯示成功率和錯誤率
- [ ] 近 7 天執行趨勢圖
- [ ] 快速操作按鈕

#### 技術實現細節

```typescript
// src/features/dashboard/DashboardPage.tsx
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { getStatistics, getRealtimeMetrics } from '@/api/statistics';

export function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
    refetchInterval: 60000, // 每分鐘刷新
  });

  const { data: realtime } = useQuery({
    queryKey: ['realtime'],
    queryFn: getRealtimeMetrics,
    refetchInterval: 5000, // 每 5 秒刷新
  });

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Workflows</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{stats?.workflows.total || 0}</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Running Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-blue-500">
              {realtime?.running_executions || 0}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-green-500">
              {stats?.executions.success_rate || 0}%
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Today's Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{stats?.executions.today || 0}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

### S4-5: Workflow List View
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Frontend Engineer  
**依賴**: S4-2 (Design System), S1-1 (Workflow Service)

#### 描述

實現工作流列表視圖，支持搜索、過濾、排序。

#### 驗收標準
- [ ] 顯示工作流列表（名稱、狀態、創建時間）
- [ ] 搜索功能
- [ ] 按狀態過濾
- [ ] 分頁
- [ ] 創建/編輯/刪除操作

---

### S4-6: Workflow Editor UI (React Flow)
**Story Points**: 13  
**優先級**: P0 - Critical  
**負責人**: Frontend Lead + Frontend Engineer  
**依賴**: S4-2 (Design System), S1-1 (Workflow Service)

#### 描述

構建拖拽式工作流編輯器，使用 React Flow 庫。

#### 驗收標準
- [ ] 可視化工作流編輯器
- [ ] 拖拽添加步驟
- [ ] 連接步驟（定義執行順序）
- [ ] 配置每個步驟的參數
- [ ] 保存和發布工作流

#### 技術實現細節

```bash
npm install reactflow
```

```typescript
// src/features/workflows/WorkflowEditor.tsx
import { useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

export function WorkflowEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div style={{ height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}
```

---

### S4-7: Execution Monitoring View
**Story Points**: 8  
**優先級**: P1 - High  
**負責人**: Frontend Engineer  
**依賴**: S4-2 (Design System), S1-3 (Execution Service)

#### 描述

創建執行詳情視圖，顯示步驟進度和日誌。

#### 驗收標準
- [ ] 顯示執行狀態
- [ ] 步驟進度可視化
- [ ] 實時日誌流
- [ ] 錯誤信息顯示
- [ ] 取消/重試操作

---

### S4-8: Agent Configuration UI
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: Frontend Engineer  
**依賴**: S4-2 (Design System), S1-6 (Agent Service)

#### 描述

構建 Agent 配置界面，選擇 LLM 模型和工具。

#### 驗收標準
- [ ] 選擇 LLM 模型（GPT-4o, GPT-3.5）
- [ ] 配置 prompt template
- [ ] 選擇可用工具
- [ ] 設置 max_tokens 等參數

---

### S4-9: Responsive Design
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: Frontend Team  
**依賴**: S4-4, S4-5, S4-6, S4-7 (所有頁面)

#### 描述

確保所有視圖響應式設計，支持桌面和平板。

#### 驗收標準
- [ ] 桌面（≥1024px）最佳顯示
- [ ] 平板（768px-1023px）正常顯示
- [ ] 觸摸操作優化
- [ ] Lighthouse 性能得分 ≥ 90

---

### S4-10: E2E Testing Setup (Playwright)
**Story Points**: 3  
**優先級**: P1 - High  
**負責人**: QA Engineer  
**依賴**: S4-3, S4-4 (登錄和 Dashboard)

#### 描述

設置 Playwright E2E 測試框架，編寫關鍵用戶流程測試。

#### 驗收標準
- [ ] Playwright 配置完成
- [ ] 測試：登錄流程
- [ ] 測試：創建工作流
- [ ] 測試：執行工作流
- [ ] CI/CD 集成

#### 技術實現細節

```bash
npm install -D @playwright/test
npx playwright install
```

```typescript
// tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test('should login successfully', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  
  await page.fill('input[type="email"]', 'test@example.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  await expect(page).toHaveURL('http://localhost:3000/dashboard');
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

---

## 📈 Sprint 4 Metrics

### Velocity Tracking
- **計劃點數**: 42
- **最複雜任務**: S4-6 (Workflow Editor - 13 points)

### Risk Register
- 🔴 工作流編輯器複雜度可能超出估算
- 🟡 React Flow 學習曲線
- 🟡 實時更新性能問題

### Definition of Done
- [ ] 所有代碼已合併到 main
- [ ] UI 組件有單元測試
- [ ] E2E 測試通過
- [ ] 響應式設計驗證
- [ ] Lighthouse 性能 ≥ 90

---

**文檔狀態**: ✅ 已完成  
**上次更新**: 2025-11-19  
**下次審查**: Sprint 4 開始前 (2026-01-20)