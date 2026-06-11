# POC 驗證執行計劃

## 文檔目的

本文檔提供設計系統遷移 POC (Proof of Concept) 驗證階段的詳細執行計劃，包含具體操作步驟、驗收標準、決策矩陣和風險評估。

## POC 目標

### 主要目標
1. **技術可行性驗證**: 確認 demo 項目的設計系統可以成功整合到當前項目
2. **視覺效果評估**: 評估新設計系統的視覺改善程度
3. **開發體驗測試**: 測試新組件系統的開發效率和易用性
4. **性能影響評估**: 測量設計系統對應用性能的影響
5. **風險識別**: 發現潛在的技術障礙和整合問題

### 成功標準
- ✅ CSS 變數系統成功運行，支持亮/暗色主題切換
- ✅ 5-8 個核心 UI 組件完全可用，符合設計規範
- ✅ Dashboard 和 Login 頁面成功遷移，視覺效果符合預期
- ✅ 無重大性能退化（頁面加載時間增加 < 10%）
- ✅ TypeScript 類型檢查通過，無 tRPC 整合問題
- ✅ 開發團隊對新系統的易用性評分 ≥ 8/10

---

## POC 執行時間表

### 總時長: 1.5 天 (12 小時)

```
Day 1 (上午): 環境準備和設計系統建立 (4 小時)
Day 1 (下午): 核心組件開發 (2 小時)
Day 2 (上午): 頁面遷移 (4 小時)
Day 2 (下午): 測試、評估和決策 (2 小時)
```

---

## Day 1 上午: 環境準備和設計系統建立 (4 小時)

### Task 1.1: 建立 POC 分支 (15 分鐘)

**操作步驟:**
```bash
# 1. 確認當前在 main 分支且代碼最新
git checkout main
git pull origin main

# 2. 建立 POC 分支
git checkout -b feature/design-system-poc

# 3. 建立 checkpoint（用於快速回滾）
git tag poc-start

# 4. 推送分支到遠端
git push -u origin feature/design-system-poc
```

**驗收標準:**
- ✅ 新分支 `feature/design-system-poc` 已建立
- ✅ Tag `poc-start` 已建立作為回滾點
- ✅ 分支已推送到遠端倉庫

---

### Task 1.2: 複製 demo 項目的設計系統文件 (30 分鐘)

**操作步驟:**

#### Step 1: 複製 globals.css 的 CSS 變數系統

```bash
# 從 demo 項目複製 CSS 變數定義到暫存文件
# 文件位置: /tmp/demo-project/app/globals.css
```

**目標文件:** `apps/web/src/app/globals.css`

**需要複製的內容:**
1. Tailwind directives
2. CSS 變數定義 (`:root` 和 `.dark`)
3. 基礎樣式重置

**修改內容 (保留當前項目的):**
```css
/* 保留現有項目特定的全局樣式 */
/* 例如: 自定義字體、特殊動畫等 */
```

#### Step 2: 建立 `lib/utils.ts` 工具文件

**文件位置:** `apps/web/src/lib/utils.ts`

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

#### Step 3: 更新 Tailwind 配置

**文件位置:** `apps/web/tailwind.config.ts`

需要添加的配置:
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"], // 添加 dark mode 支持
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}", // 添加 features 目錄
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

**驗收標準:**
- ✅ `apps/web/src/app/globals.css` 已更新 CSS 變數系統
- ✅ `apps/web/src/lib/utils.ts` 已建立 `cn()` 工具函數
- ✅ `apps/web/tailwind.config.ts` 已更新 theme 配置
- ✅ 執行 `pnpm dev` 無錯誤，樣式系統正常加載

---

### Task 1.3: 安裝必要依賴 (15 分鐘)

**操作步驟:**

```bash
# 在項目根目錄執行
cd C:\ai-it-project-process-management-webapp

# 安裝核心依賴到 apps/web
pnpm add class-variance-authority clsx tailwind-merge --filter=web

# 安裝 Tailwind 動畫插件
pnpm add -D tailwindcss-animate --filter=web

# 安裝 next-themes (主題切換)
pnpm add next-themes --filter=web

# 驗證依賴安裝
pnpm list --filter=web | grep -E "(class-variance-authority|clsx|tailwind-merge|tailwindcss-animate|next-themes)"
```

**package.json 預期更新:**

`apps/web/package.json` 應包含:
```json
{
  "dependencies": {
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "next-themes": "^0.2.1",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "tailwindcss-animate": "^1.0.7"
  }
}
```

**驗收標準:**
- ✅ 所有依賴成功安裝
- ✅ `pnpm dev` 啟動無錯誤
- ✅ TypeScript 類型檢查通過: `pnpm typecheck --filter=web`

---

### Task 1.4: 建立 ThemeProvider (30 分鐘)

**文件位置:** `apps/web/src/components/theme-provider.tsx`

```typescript
"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { type ThemeProviderProps } from "next-themes/dist/types";

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
```

**整合到 Root Layout:**

**文件位置:** `apps/web/src/app/layout.tsx`

```typescript
import { ThemeProvider } from "@/components/theme-provider";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-TW" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

**建立主題切換按鈕組件:**

**文件位置:** `apps/web/src/components/theme-toggle.tsx`

```typescript
"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  // 避免 hydration mismatch
  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">切換主題</span>
    </Button>
  );
}
```

**驗收標準:**
- ✅ ThemeProvider 成功整合到 Root Layout
- ✅ ThemeToggle 組件可以正常切換亮/暗色主題
- ✅ 無 hydration mismatch 警告
- ✅ 主題切換時 CSS 變數正確更新

---

## Day 1 下午: 核心組件開發 (2 小時)

### Task 1.5: 建立 5-8 個核心 UI 組件 (2 小時)

**優先級排序:**

| 優先級 | 組件 | 預估時間 | 依賴 |
|--------|------|----------|------|
| P1 | Button | 15 分鐘 | - |
| P1 | Card | 15 分鐘 | - |
| P1 | Input | 15 分鐘 | - |
| P1 | Label | 10 分鐘 | - |
| P2 | Badge | 10 分鐘 | - |
| P2 | Select | 20 分鐘 | Radix UI |
| P2 | Dialog | 20 分鐘 | Radix UI |
| P2 | Dropdown Menu | 15 分鐘 | Radix UI |

**總計: 8 個組件，約 2 小時**

---

#### 組件 1: Button (15 分鐘)

**文件位置:** `apps/web/src/components/ui/button.tsx`

```typescript
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
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
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
```

**測試文件:** `apps/web/src/components/ui/button.test.tsx`

```typescript
import { render, screen } from "@testing-library/react";
import { Button } from "./button";

describe("Button", () => {
  it("renders with default variant", () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole("button", { name: /click me/i });
    expect(button).toBeInTheDocument();
  });

  it("renders with different variants", () => {
    const { container } = render(<Button variant="destructive">Delete</Button>);
    expect(container.firstChild).toHaveClass("bg-destructive");
  });

  it("renders with different sizes", () => {
    const { container } = render(<Button size="sm">Small</Button>);
    expect(container.firstChild).toHaveClass("h-9");
  });
});
```

**驗收標準:**
- ✅ 組件渲染正常，所有 variants 和 sizes 正確顯示
- ✅ TypeScript 類型檢查通過
- ✅ 測試通過: `pnpm test button.test.tsx --filter=web`
- ✅ Storybook 預覽正常（如果有配置）

---

#### 組件 2: Card (15 分鐘)

**文件位置:** `apps/web/src/components/ui/card.tsx`

```typescript
import * as React from "react";

import { cn } from "@/lib/utils";

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
));
Card.displayName = "Card";

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
```

**驗收標準:**
- ✅ Card 及所有子組件渲染正常
- ✅ 複合組件（Card + CardHeader + CardContent + CardFooter）正常工作
- ✅ TypeScript 類型檢查通過

---

#### 組件 3-8: 其他核心組件

**剩餘組件:**
- Input
- Label
- Badge
- Select (Radix UI)
- Dialog (Radix UI)
- Dropdown Menu (Radix UI)

**執行策略:**
1. 從 demo 項目複製對應組件文件
2. 調整 import 路徑以符合當前項目結構
3. 執行 TypeScript 類型檢查和測試
4. 在測試頁面驗證組件渲染

**驗收標準 (所有組件):**
- ✅ 8 個核心組件全部建立完成
- ✅ 所有組件 TypeScript 類型檢查通過
- ✅ 所有組件在測試頁面正常渲染
- ✅ 亮/暗色主題下樣式正確

---

## Day 2 上午: 頁面遷移 (4 小時)

### Task 2.1: 遷移 Dashboard 頁面 (2 小時)

**目標頁面:** `apps/web/src/app/dashboard/page.tsx`

#### Step 1: 分析現有 Dashboard 結構 (30 分鐘)

**操作步驟:**
```bash
# 讀取現有 Dashboard 代碼
cat apps/web/src/app/dashboard/page.tsx

# 識別需要替換的組件:
# - 自定義 Card → 新 UI Card
# - 自定義 Button → 新 UI Button
# - 自定義 Badge → 新 UI Badge
# - 顏色類名 (bg-blue-500 → bg-primary)
```

#### Step 2: 建立遷移對照表

**顏色系統對照:**
```typescript
// 舊系統 → 新系統
"bg-blue-500" → "bg-primary"
"text-blue-600" → "text-primary"
"bg-gray-100" → "bg-muted"
"text-gray-600" → "text-muted-foreground"
"bg-white" → "bg-card"
"border-gray-200" → "border"
"bg-red-500" → "bg-destructive"
"bg-green-500" → "bg-success" (需要添加到 CSS 變數)
"bg-yellow-500" → "bg-warning" (需要添加到 CSS 變數)
```

**組件對照:**
```typescript
// 舊組件 → 新組件
<div className="rounded-lg border bg-white p-6">
  → <Card><CardContent>...</CardContent></Card>

<button className="bg-blue-500 text-white px-4 py-2 rounded">
  → <Button>...</Button>

<span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
  → <Badge>...</Badge>
```

#### Step 3: 執行遷移 (1 小時)

**遷移清單:**

1. **Import 新組件:**
```typescript
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
```

2. **替換所有舊組件為新組件**

3. **更新顏色類名**

4. **統一間距系統:**
```typescript
// 使用 Tailwind 的間距 scale
"p-4" → "p-4" (保持)
"m-2" → "m-2" (保持)
"gap-4" → "gap-4" (保持)
```

5. **統一 border radius:**
```typescript
"rounded-lg" → "rounded-lg" (使用 var(--radius))
"rounded-md" → "rounded-md"
"rounded-sm" → "rounded-sm"
```

#### Step 4: 測試和驗證 (30 分鐘)

**測試清單:**
```bash
# 1. TypeScript 類型檢查
pnpm typecheck --filter=web

# 2. 啟動開發服務器
pnpm dev

# 3. 訪問 Dashboard 頁面
# http://localhost:3000/dashboard

# 4. 視覺檢查清單:
# ✅ 所有 Card 組件正常渲染
# ✅ Button 樣式正確
# ✅ Badge 顏色和樣式正確
# ✅ 間距統一
# ✅ 主題切換正常（亮/暗色）
# ✅ 無 console 錯誤
# ✅ 無佈局破壞

# 5. 響應式測試
# ✅ Mobile (375px)
# ✅ Tablet (768px)
# ✅ Desktop (1920px)

# 6. 功能測試
# ✅ 所有按鈕可點擊
# ✅ 導航正常
# ✅ tRPC 數據加載正常
```

**驗收標準:**
- ✅ Dashboard 頁面遷移完成，無視覺破壞
- ✅ 所有 UI 組件正確使用新設計系統
- ✅ 亮/暗色主題切換正常
- ✅ TypeScript 無錯誤
- ✅ 所有功能正常運行
- ✅ 響應式佈局正確

---

### Task 2.2: 遷移 Login 頁面 (2 小時)

**目標頁面:** `apps/web/src/app/login/page.tsx` (或相關認證頁面)

**執行步驟與 Dashboard 類似:**

1. **分析現有結構** (30 分鐘)
2. **建立遷移對照表** (15 分鐘)
3. **執行遷移** (1 小時)
4. **測試和驗證** (15 分鐘)

**特殊注意事項:**
- Form 組件需要特別處理
- Input 組件的 error state 樣式
- Azure AD B2C 認證流程不能受影響

**驗收標準:**
- ✅ Login 頁面遷移完成
- ✅ Form 樣式和驗證正常
- ✅ Azure AD B2C 認證流程正常
- ✅ Error 狀態樣式正確
- ✅ 亮/暗色主題切換正常

---

## Day 2 下午: 測試、評估和決策 (2 小時)

### Task 3.1: 性能測試 (30 分鐘)

**測試工具:**
- Lighthouse (Chrome DevTools)
- Next.js Build Analyzer
- Bundle Size Analysis

**測試步驟:**

```bash
# 1. 建立生產構建
pnpm build --filter=web

# 2. 啟動生產服務器
pnpm start --filter=web

# 3. Lighthouse 測試
# 在 Chrome DevTools 中運行 Lighthouse
# 測試頁面: Dashboard, Login

# 4. Bundle Size 分析
pnpm add -D @next/bundle-analyzer --filter=web
```

**性能指標對照:**

| 指標 | POC 前 | POC 後 | 變化 | 閾值 |
|------|--------|--------|------|------|
| First Contentful Paint (FCP) | - | - | - | < +10% |
| Largest Contentful Paint (LCP) | - | - | - | < +10% |
| Total Blocking Time (TBT) | - | - | - | < +10% |
| Cumulative Layout Shift (CLS) | - | - | - | < +5% |
| JavaScript Bundle Size | - | - | - | < +15% |
| CSS Bundle Size | - | - | - | < +10% |

**驗收標準:**
- ✅ 所有性能指標在可接受範圍內
- ✅ Lighthouse Performance Score ≥ 90
- ✅ Bundle size 增加 < 15%

---

### Task 3.2: 功能測試 (30 分鐘)

**測試清單:**

#### Dashboard 頁面
```typescript
// 測試文件: apps/web/src/app/dashboard/page.test.tsx

describe("Dashboard POC", () => {
  it("renders all cards correctly", () => {
    // 測試所有統計卡片
  });

  it("loads data via tRPC", () => {
    // 測試 tRPC 數據加載
  });

  it("theme toggle works", () => {
    // 測試主題切換
  });

  it("navigation works", () => {
    // 測試導航連結
  });
});
```

#### Login 頁面
```typescript
// 測試文件: apps/web/src/app/login/page.test.tsx

describe("Login POC", () => {
  it("renders login form", () => {
    // 測試表單渲染
  });

  it("validates input fields", () => {
    // 測試表單驗證
  });

  it("Azure AD B2C flow works", () => {
    // 測試認證流程
  });
});
```

**執行測試:**
```bash
# 運行所有測試
pnpm test --filter=web

# E2E 測試 (Playwright)
pnpm test:e2e --filter=web
```

**驗收標準:**
- ✅ 所有單元測試通過
- ✅ E2E 測試通過
- ✅ 無 regression bugs
- ✅ tRPC 整合正常

---

### Task 3.3: 開發體驗評估 (30 分鐘)

**評估維度:**

1. **組件易用性** (1-10 分)
   - 新組件 API 是否直觀？
   - Props 是否容易理解？
   - TypeScript 類型提示是否完整？

2. **開發效率** (1-10 分)
   - 開發速度是否提升？
   - 代碼重複是否減少？
   - 樣式調整是否更快？

3. **學習曲線** (1-10 分)
   - 團隊成員能快速上手嗎？
   - 文檔是否充足？
   - 範例是否清晰？

4. **維護性** (1-10 分)
   - 代碼是否更易維護？
   - 樣式是否更統一？
   - 修改是否更安全？

**評估表格:**

| 評估項 | 得分 (1-10) | 備註 |
|--------|-------------|------|
| 組件易用性 | | |
| 開發效率 | | |
| 學習曲線 | | |
| 維護性 | | |
| **總平均分** | | |

**目標:** 總平均分 ≥ 8.0

---

### Task 3.4: 視覺效果評估 (30 分鐘)

**對比截圖:**

準備以下頁面的前後對比截圖:
1. Dashboard - 亮色主題
2. Dashboard - 暗色主題
3. Login - 亮色主題
4. Login - 暗色主題

**評估清單:**

| 評估項 | 改善程度 | 備註 |
|--------|----------|------|
| 整體視覺協調性 | ⭐⭐⭐⭐⭐ | |
| 顏色系統一致性 | ⭐⭐⭐⭐⭐ | |
| 間距和對齊 | ⭐⭐⭐⭐⭐ | |
| 字體和排版 | ⭐⭐⭐⭐⭐ | |
| 暗色主題品質 | ⭐⭐⭐⭐⭐ | |
| 響應式設計 | ⭐⭐⭐⭐⭐ | |
| 動畫和過渡 | ⭐⭐⭐⭐⭐ | |

**⭐ 評分標準:**
- ⭐ - 沒有改善
- ⭐⭐ - 輕微改善
- ⭐⭐⭐ - 中等改善
- ⭐⭐⭐⭐ - 顯著改善
- ⭐⭐⭐⭐⭐ - 極大改善

**目標:** 平均 ≥ ⭐⭐⭐⭐ (顯著改善)

---

## 決策矩陣

### GO / NO-GO 決策標準

#### 必要條件 (所有必須滿足才能 GO):

| # | 條件 | 狀態 | 備註 |
|---|------|------|------|
| 1 | CSS 變數系統運行正常，無 console 錯誤 | ☐ | |
| 2 | 核心組件全部可用且通過測試 | ☐ | |
| 3 | Dashboard 和 Login 頁面遷移成功 | ☐ | |
| 4 | TypeScript 類型檢查 100% 通過 | ☐ | |
| 5 | tRPC 整合無問題，數據加載正常 | ☐ | |
| 6 | Azure AD B2C 認證流程正常 | ☐ | |
| 7 | 無 critical bugs 或 blockers | ☐ | |

#### 性能條件 (至少滿足 80%):

| # | 條件 | 狀態 | 備註 |
|---|------|------|------|
| 8 | FCP / LCP 性能退化 < 10% | ☐ | |
| 9 | Bundle size 增加 < 15% | ☐ | |
| 10 | Lighthouse Performance Score ≥ 90 | ☐ | |
| 11 | 無明顯的視覺延遲或卡頓 | ☐ | |

#### 品質條件 (至少滿足 80%):

| # | 條件 | 狀態 | 備註 |
|---|------|------|------|
| 12 | 視覺效果評估 ≥ ⭐⭐⭐⭐ | ☐ | |
| 13 | 開發體驗評分 ≥ 8.0 | ☐ | |
| 14 | 響應式設計在所有斷點正常 | ☐ | |
| 15 | 亮/暗色主題切換流暢無閃爍 | ☐ | |

---

### 決策結果

#### ✅ GO - 繼續完整遷移

**條件:**
- 必要條件: 7/7 滿足 (100%)
- 性能條件: ≥ 3/4 滿足 (≥ 75%)
- 品質條件: ≥ 3/4 滿足 (≥ 75%)

**後續行動:**
1. 將 POC 分支合併到 `feature/design-system-migration`
2. 開始執行 Phase 1: 設計系統基礎建設
3. 按照遷移計劃逐階段執行
4. 每個階段完成後進行驗收

---

#### 🔶 CONDITIONAL GO - 有條件繼續

**條件:**
- 必要條件: 7/7 滿足 (100%)
- 性能條件: 2-3/4 滿足 (50-75%)
- 品質條件: 2-3/4 滿足 (50-75%)

**後續行動:**
1. 識別並解決未滿足的條件
2. 進行有針對性的優化（例如: bundle size 優化、性能調整）
3. 重新測試評估
4. 如果優化後滿足 GO 條件，繼續遷移
5. 如果無法優化到 GO 標準，考慮調整方案或 NO-GO

---

#### ❌ NO-GO - 不繼續遷移

**條件:**
- 必要條件: < 7/7 滿足 (< 100%)
- **或** 性能條件: < 2/4 滿足 (< 50%)
- **或** 品質條件: < 2/4 滿足 (< 50%)

**後續行動:**
1. 詳細記錄所有未滿足的條件和原因
2. 分析根本原因（技術障礙、設計不匹配、性能問題等）
3. 評估替代方案:
   - **方案 B1**: 調整遷移範圍（僅遷移部分組件）
   - **方案 B2**: 調整設計系統（修改 demo 設計系統以符合需求）
   - **方案 B3**: 保持現狀（優化現有設計系統）
4. 回滾 POC 分支:
   ```bash
   git checkout main
   git branch -D feature/design-system-poc
   git push origin --delete feature/design-system-poc
   ```
5. 編寫 POC 失敗報告（包含原因分析和建議）

---

## 風險和應對策略

### 已識別風險

| 風險 | 機率 | 影響 | 應對策略 |
|------|------|------|----------|
| TypeScript 類型錯誤 | 中 | 高 | 逐步遷移，每個組件單獨驗證 |
| tRPC 整合問題 | 低 | 高 | POC 階段重點測試 API 調用 |
| 性能退化 | 中 | 中 | 持續監控 bundle size 和 Lighthouse |
| 暗色主題問題 | 中 | 低 | 提前測試所有 CSS 變數 |
| Azure AD B2C 認證異常 | 低 | 高 | 完整測試認證流程 |
| 開發團隊學習曲線 | 中 | 中 | 提供培訓和文檔 |
| 時間超支 | 中 | 中 | 嚴格按時間表執行，必要時調整範圍 |

---

## POC 檢查清單

### Day 1 上午檢查清單

- [ ] Task 1.1: POC 分支建立完成
  - [ ] 分支 `feature/design-system-poc` 已建立
  - [ ] Tag `poc-start` 已建立
  - [ ] 分支已推送到遠端

- [ ] Task 1.2: 設計系統文件複製完成
  - [ ] `globals.css` 已更新 CSS 變數
  - [ ] `lib/utils.ts` 已建立 `cn()` 函數
  - [ ] `tailwind.config.ts` 已更新 theme 配置

- [ ] Task 1.3: 依賴安裝完成
  - [ ] `class-variance-authority` 已安裝
  - [ ] `clsx` 已安裝
  - [ ] `tailwind-merge` 已安裝
  - [ ] `tailwindcss-animate` 已安裝
  - [ ] `next-themes` 已安裝
  - [ ] `pnpm dev` 啟動無錯誤

- [ ] Task 1.4: ThemeProvider 建立完成
  - [ ] `components/theme-provider.tsx` 已建立
  - [ ] Root Layout 已整合 ThemeProvider
  - [ ] `components/theme-toggle.tsx` 已建立
  - [ ] 主題切換功能正常

### Day 1 下午檢查清單

- [ ] Task 1.5: 核心 UI 組件建立完成
  - [ ] Button 組件完成
  - [ ] Card 組件完成
  - [ ] Input 組件完成
  - [ ] Label 組件完成
  - [ ] Badge 組件完成
  - [ ] Select 組件完成
  - [ ] Dialog 組件完成
  - [ ] Dropdown Menu 組件完成
  - [ ] 所有組件 TypeScript 通過
  - [ ] 所有組件在測試頁面正常渲染

### Day 2 上午檢查清單

- [ ] Task 2.1: Dashboard 頁面遷移完成
  - [ ] 組件替換完成
  - [ ] 顏色系統更新完成
  - [ ] TypeScript 無錯誤
  - [ ] 功能測試通過
  - [ ] 視覺檢查通過
  - [ ] 響應式測試通過
  - [ ] 主題切換正常

- [ ] Task 2.2: Login 頁面遷移完成
  - [ ] 組件替換完成
  - [ ] Form 樣式正確
  - [ ] 驗證流程正常
  - [ ] Azure AD B2C 認證正常
  - [ ] 視覺檢查通過

### Day 2 下午檢查清單

- [ ] Task 3.1: 性能測試完成
  - [ ] Lighthouse 測試完成
  - [ ] Bundle size 分析完成
  - [ ] 所有性能指標在可接受範圍

- [ ] Task 3.2: 功能測試完成
  - [ ] 單元測試全部通過
  - [ ] E2E 測試全部通過
  - [ ] tRPC 整合測試通過

- [ ] Task 3.3: 開發體驗評估完成
  - [ ] 評估表格填寫完成
  - [ ] 總平均分 ≥ 8.0

- [ ] Task 3.4: 視覺效果評估完成
  - [ ] 對比截圖準備完成
  - [ ] 評估清單填寫完成
  - [ ] 平均評分 ≥ ⭐⭐⭐⭐

- [ ] 決策矩陣評估完成
  - [ ] 必要條件檢查完成
  - [ ] 性能條件檢查完成
  - [ ] 品質條件檢查完成
  - [ ] GO / NO-GO 決策已做出

---

## 產出文檔

### POC 完成後需要產出的文檔:

1. **POC 執行報告** (`claudedocs/POC-EXECUTION-REPORT.md`)
   - 執行時間表實際 vs 預估
   - 所有檢查清單完成狀態
   - 性能測試結果
   - 功能測試結果
   - 開發體驗評估結果
   - 視覺效果評估結果

2. **決策文檔** (`claudedocs/POC-DECISION.md`)
   - GO / NO-GO 決策結果
   - 決策依據和理由
   - 未滿足條件的詳細說明（如果有）
   - 後續行動計劃

3. **技術問題記錄** (`claudedocs/POC-TECHNICAL-ISSUES.md`)
   - POC 過程中遇到的所有技術問題
   - 解決方案和 workarounds
   - 未解決的問題和建議

4. **視覺對比報告** (`claudedocs/POC-VISUAL-COMPARISON.md`)
   - 前後對比截圖
   - 視覺改善說明
   - 設計系統應用示例

---

## 附錄

### 附錄 A: 常見問題和解決方案

#### 問題 1: CSS 變數在暗色模式下不生效

**症狀:** 切換到暗色主題後，某些元素顏色沒有改變

**原因:** `.dark` 類沒有正確應用到 `<html>` 元素

**解決方案:**
```typescript
// layout.tsx
<html lang="zh-TW" suppressHydrationWarning>
  // suppressHydrationWarning 防止 next-themes 的 hydration 警告
```

---

#### 問題 2: TypeScript 類型錯誤 - VariantProps

**症狀:** `VariantProps<typeof buttonVariants>` 類型錯誤

**原因:** `class-variance-authority` 版本不匹配

**解決方案:**
```bash
pnpm add class-variance-authority@^0.7.0 --filter=web
```

---

#### 問題 3: Radix UI 組件樣式覆蓋失敗

**症狀:** 自定義樣式無法覆蓋 Radix UI 默認樣式

**原因:** CSS 優先級問題

**解決方案:**
```typescript
// 使用 cn() 合併類名
<Dialog.Content className={cn("bg-background p-6", className)} />
```

---

### 附錄 B: 回滾步驟

如果 POC 失敗需要回滾:

```bash
# 1. 切換到 main 分支
git checkout main

# 2. 刪除本地 POC 分支
git branch -D feature/design-system-poc

# 3. 刪除遠端 POC 分支
git push origin --delete feature/design-system-poc

# 4. 刪除 POC tag
git tag -d poc-start
git push origin --delete poc-start

# 5. 清理依賴（如果需要）
pnpm install
```

---

### 附錄 C: 參考資源

- **shadcn/ui 文檔**: https://ui.shadcn.com
- **Radix UI 文檔**: https://www.radix-ui.com
- **Tailwind CSS 文檔**: https://tailwindcss.com
- **Next.js 主題文檔**: https://github.com/pacocoursey/next-themes
- **Class Variance Authority**: https://cva.style

---

## 結論

本 POC 驗證執行計劃提供了詳細的步驟、驗收標準和決策框架，確保設計系統遷移的技術可行性和業務價值得到充分驗證。

**關鍵成功因素:**
1. 嚴格按照時間表執行
2. 每個檢查點都進行驗收
3. 及早發現和解決問題
4. 基於數據做出 GO / NO-GO 決策
5. 詳細記錄所有發現和問題

**下一步:**
- 獲得利益相關者批准開始 POC
- 分配資源和時間
- 執行 POC
- 基於結果做出決策
