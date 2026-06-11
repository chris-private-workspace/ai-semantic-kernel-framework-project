# FEAT-012: 統一載入特效系統 - 技術設計

> **建立日期**: 2025-12-16
> **狀態**: ✅ 已確認，待開發

---

## 1. 技術架構

### 1.1 架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Pages     │  │  Components │  │    Data Fetching    │ │
│  │  (Routes)   │  │   (UI)      │  │  (tRPC Queries)     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                     │             │
│         ▼                ▼                     ▼             │
├─────────────────────────────────────────────────────────────┤
│                    Loading System Layer                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  LoadingProvider                         ││
│  │  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐  ││
│  │  │ Navigation  │ │    Data      │ │    Action       │  ││
│  │  │  Loading    │ │   Loading    │ │   Loading       │  ││
│  │  └──────┬──────┘ └──────┬───────┘ └───────┬─────────┘  ││
│  │         │               │                  │            ││
│  │         ▼               ▼                  ▼            ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │              Visual Components                      │││
│  │  │  GlobalProgress | Spinner | Skeleton | LoadingBtn  │││
│  │  └─────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心模組

| 模組 | 職責 | 文件路徑 |
|------|------|----------|
| LoadingProvider | 全局載入狀態管理 | `providers/LoadingProvider.tsx` |
| NavigationProgress | 路由導航進度條 | `layout/NavigationProgress.tsx` |
| GlobalProgress | 頂部進度條 UI | `ui/loading/GlobalProgress.tsx` |
| Spinner | 通用旋轉指示器 | `ui/loading/Spinner.tsx` |
| LoadingButton | 帶載入狀態按鈕 | `ui/loading/LoadingButton.tsx` |
| LoadingOverlay | 區域載入遮罩 | `ui/loading/LoadingOverlay.tsx` |
| Skeleton | 骨架屏基礎組件 | `ui/skeleton/` |

---

## 2. 組件詳細設計

### 2.1 GlobalProgress (頂部進度條)

```tsx
// apps/web/src/components/ui/loading/GlobalProgress.tsx

'use client';

import { useEffect, useState } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { cn } from '@/lib/utils';

interface GlobalProgressProps {
  color?: string;
  height?: number;
  showSpinner?: boolean;
}

export function GlobalProgress({
  color = 'hsl(var(--primary))',
  height = 3,
  showSpinner = false,
}: GlobalProgressProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [progress, setProgress] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // 路由變化時觸發
    setIsVisible(true);
    setProgress(0);

    // 模擬進度
    const timer1 = setTimeout(() => setProgress(30), 100);
    const timer2 = setTimeout(() => setProgress(60), 200);
    const timer3 = setTimeout(() => setProgress(80), 400);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [pathname, searchParams]);

  useEffect(() => {
    if (progress >= 80) {
      // 頁面載入完成
      const timer = setTimeout(() => {
        setProgress(100);
        setTimeout(() => setIsVisible(false), 200);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [progress]);

  if (!isVisible) return null;

  return (
    <div
      className={cn(
        'fixed top-0 left-0 right-0 z-[9999]',
        'transition-opacity duration-200',
        progress === 100 ? 'opacity-0' : 'opacity-100'
      )}
    >
      {/* Progress Bar */}
      <div
        className="h-[3px] transition-all duration-300 ease-out"
        style={{
          width: `${progress}%`,
          height: `${height}px`,
          backgroundColor: color,
          boxShadow: `0 0 10px ${color}, 0 0 5px ${color}`,
        }}
      />

      {/* Optional Spinner */}
      {showSpinner && progress < 100 && (
        <div className="fixed top-4 right-4">
          <Spinner size="sm" />
        </div>
      )}
    </div>
  );
}
```

### 2.2 Spinner (旋轉指示器)

```tsx
// apps/web/src/components/ui/loading/Spinner.tsx

import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'secondary' | 'white' | 'muted';
  className?: string;
}

const sizeClasses = {
  xs: 'h-3 w-3',
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12',
};

const colorClasses = {
  primary: 'text-primary',
  secondary: 'text-secondary',
  white: 'text-white',
  muted: 'text-muted-foreground',
};

export function Spinner({
  size = 'md',
  color = 'primary',
  className,
}: SpinnerProps) {
  return (
    <Loader2
      className={cn(
        'animate-spin',
        sizeClasses[size],
        colorClasses[color],
        className
      )}
    />
  );
}
```

### 2.3 LoadingButton (載入按鈕)

```tsx
// apps/web/src/components/ui/loading/LoadingButton.tsx

import { forwardRef } from 'react';
import { Button, ButtonProps } from '@/components/ui/button';
import { Spinner } from './Spinner';
import { cn } from '@/lib/utils';

interface LoadingButtonProps extends ButtonProps {
  isLoading?: boolean;
  loadingText?: string;
  spinnerPosition?: 'left' | 'right';
}

export const LoadingButton = forwardRef<HTMLButtonElement, LoadingButtonProps>(
  (
    {
      isLoading = false,
      loadingText,
      spinnerPosition = 'left',
      disabled,
      children,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <Button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          isLoading && 'cursor-not-allowed opacity-70',
          className
        )}
        {...props}
      >
        {isLoading ? (
          <>
            {spinnerPosition === 'left' && (
              <Spinner size="sm" color="white" className="mr-2" />
            )}
            {loadingText || children}
            {spinnerPosition === 'right' && (
              <Spinner size="sm" color="white" className="ml-2" />
            )}
          </>
        ) : (
          children
        )}
      </Button>
    );
  }
);

LoadingButton.displayName = 'LoadingButton';
```

### 2.4 LoadingOverlay (區域遮罩)

```tsx
// apps/web/src/components/ui/loading/LoadingOverlay.tsx

import { cn } from '@/lib/utils';
import { Spinner } from './Spinner';

interface LoadingOverlayProps {
  isLoading: boolean;
  children: React.ReactNode;
  blur?: boolean;
  spinnerSize?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingOverlay({
  isLoading,
  children,
  blur = false,
  spinnerSize = 'lg',
  className,
}: LoadingOverlayProps) {
  return (
    <div className={cn('relative', className)}>
      {children}

      {isLoading && (
        <div
          className={cn(
            'absolute inset-0 z-10 flex items-center justify-center',
            'bg-background/60 dark:bg-background/70',
            blur && 'backdrop-blur-sm'
          )}
        >
          <Spinner size={spinnerSize} />
        </div>
      )}
    </div>
  );
}
```

### 2.5 骨架屏組件

```tsx
// apps/web/src/components/ui/skeleton/CardSkeleton.tsx

import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardHeader, CardContent } from '@/components/ui/card';

interface CardSkeletonProps {
  count?: number;
  showImage?: boolean;
}

export function CardSkeleton({ count = 1, showImage = false }: CardSkeletonProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardHeader>
          <CardContent>
            {showImage && <Skeleton className="h-32 w-full mb-4" />}
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-2/3" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// apps/web/src/components/ui/skeleton/TableSkeleton.tsx

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableSkeleton({ rows = 5, columns = 4 }: TableSkeletonProps) {
  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex gap-4 p-4 bg-muted/50 rounded-t-lg">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4 p-4 border-b">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={colIndex}
              className={cn(
                'h-4 flex-1',
                colIndex === 0 && 'max-w-[200px]'
              )}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

// apps/web/src/components/ui/skeleton/FormSkeleton.tsx

interface FormSkeletonProps {
  fields?: number;
}

export function FormSkeleton({ fields = 4 }: FormSkeletonProps) {
  return (
    <div className="space-y-6">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" /> {/* Label */}
          <Skeleton className="h-10 w-full" /> {/* Input */}
        </div>
      ))}
      <Skeleton className="h-10 w-32" /> {/* Submit Button */}
    </div>
  );
}
```

---

## 3. 全局整合

### 3.1 Layout 整合

```tsx
// apps/web/src/app/[locale]/layout.tsx

import { GlobalProgress } from '@/components/ui/loading/GlobalProgress';
import { Suspense } from 'react';

export default function LocaleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {/* 全局進度條 - 需要 Suspense 包裹以支援 useSearchParams */}
      <Suspense fallback={null}>
        <GlobalProgress />
      </Suspense>

      {children}
    </>
  );
}
```

### 3.2 頁面使用模式

```tsx
// 範例: projects/page.tsx

'use client';

import { api } from '@/lib/trpc';
import { TableSkeleton } from '@/components/ui/skeleton';
import { LoadingOverlay } from '@/components/ui/loading';

export default function ProjectsPage() {
  const { data, isLoading, isFetching } = api.project.getAll.useQuery({});

  // 首次載入 → 骨架屏
  if (isLoading) {
    return <TableSkeleton rows={10} columns={6} />;
  }

  // 刷新時 → 載入遮罩
  return (
    <LoadingOverlay isLoading={isFetching && !isLoading}>
      <ProjectTable data={data} />
    </LoadingOverlay>
  );
}
```

### 3.3 表單使用模式

```tsx
// 範例: projects/new/page.tsx

'use client';

import { LoadingButton } from '@/components/ui/loading';

export default function NewProjectPage() {
  const createProject = api.project.create.useMutation();

  return (
    <form onSubmit={handleSubmit}>
      {/* 表單欄位 */}

      <LoadingButton
        type="submit"
        isLoading={createProject.isPending}
        loadingText={t('submitting')}
      >
        {t('create')}
      </LoadingButton>
    </form>
  );
}
```

---

## 4. 依賴項

### 4.1 現有依賴（無需安裝）
- `lucide-react` - Loader2 圖標
- `tailwindcss` - 動畫 (animate-spin, animate-pulse)
- `@/components/ui/skeleton` - shadcn/ui Skeleton

### 4.2 可選依賴
- 無需安裝額外依賴，使用現有技術棧

---

## 5. 文件結構

```
apps/web/src/
├── components/
│   ├── ui/
│   │   ├── loading/
│   │   │   ├── GlobalProgress.tsx    # 頂部進度條
│   │   │   ├── Spinner.tsx           # 通用 Spinner
│   │   │   ├── LoadingButton.tsx     # 載入按鈕
│   │   │   ├── LoadingOverlay.tsx    # 區域載入遮罩
│   │   │   └── index.ts              # 統一導出
│   │   └── skeleton/
│   │       ├── CardSkeleton.tsx      # 卡片骨架
│   │       ├── TableSkeleton.tsx     # 表格骨架
│   │       ├── FormSkeleton.tsx      # 表單骨架
│   │       └── index.ts
│   └── ...
├── app/
│   └── [locale]/
│       └── layout.tsx                # 整合 GlobalProgress
└── messages/
    ├── en.json                       # loading.* 翻譯
    └── zh-TW.json
```

---

## 6. I18N 翻譯鍵

```json
{
  "loading": {
    "loading": "載入中...",
    "submitting": "提交中...",
    "saving": "儲存中...",
    "deleting": "刪除中...",
    "processing": "處理中...",
    "pleaseWait": "請稍候..."
  }
}
```

---

## 7. 測試要點

### 7.1 單元測試
- Spinner 尺寸和顏色正確渲染
- LoadingButton 載入狀態正確顯示
- LoadingOverlay 遮罩正確顯示/隱藏

### 7.2 整合測試
- 路由切換觸發進度條
- 數據載入顯示骨架屏
- 表單提交按鈕禁用

### 7.3 性能測試
- 無記憶體洩漏
- 動畫流暢 (60fps)
- SSR 兼容
