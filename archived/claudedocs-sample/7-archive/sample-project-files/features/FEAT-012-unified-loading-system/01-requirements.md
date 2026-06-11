# FEAT-012: 統一載入特效系統

> **建立日期**: 2025-12-16
> **狀態**: ✅ 已確認，待開發
> **優先級**: High
> **類型**: 新功能 (New Feature)

---

## 1. 功能概述

### 1.1 背景
目前系統在以下場景缺乏統一的載入指示：
- 頁面跳轉時（點擊連結後到新頁面渲染完成前）
- 進入詳情/編輯頁面時
- 數據查詢載入時
- 表單提交時

這導致用戶體驗問題：
- 不確定是否成功點擊
- 不知道系統是否在處理中
- 多次重複點擊導致重複請求

### 1.2 目標
設計並實施一個統一的載入特效系統，涵蓋：
1. **頁面導航載入** - 路由切換時的全局載入指示
2. **數據載入** - API 請求時的區域載入指示
3. **操作載入** - 按鈕點擊後的載入狀態
4. **骨架屏** - 內容區域的佔位載入效果

---

## 2. 功能需求

### 2.1 載入場景分類

| 場景 | 類型 | 視覺效果 | 範例 |
|------|------|----------|------|
| 頁面跳轉 | 全局 | 頂部進度條 + 背景遮罩（可選） | 點擊側邊欄導航 |
| 進入詳情頁 | 全局 | 頂部進度條 | 點擊表格行進入詳情 |
| 列表載入 | 區域 | 骨架屏 / Spinner | 初次載入數據 |
| 表格刷新 | 區域 | 半透明遮罩 + Spinner | 切換頁碼、篩選 |
| 按鈕操作 | 元素 | 按鈕內 Spinner + 禁用 | 提交表單、刪除 |
| 下拉選單 | 元素 | 選項區 Spinner | 載入選項數據 |

### 2.2 視覺規格

#### 2.2.1 頂部進度條 (NProgress 風格)
```
位置: 頁面最頂部
高度: 3px
顏色: Primary Blue (#3B82F6) 或主題色
動畫: 漸進式填充 + 細微脈動
完成: 快速滑出 + 淡出
```

#### 2.2.2 全屏遮罩（可選）
```
背景: 半透明白色 (rgba(255,255,255,0.6))
Dark Mode: 半透明黑色 (rgba(0,0,0,0.4))
Z-index: 50
中心: Spinner 動畫
```

#### 2.2.3 區域 Spinner
```
尺寸: sm(16px), md(24px), lg(32px), xl(48px)
顏色: Primary Blue / 可配置
動畫: 旋轉 (spin animation)
```

#### 2.2.4 骨架屏 (Skeleton)
```
背景: Gray-200 (Light) / Gray-700 (Dark)
動畫: 脈動閃爍 (pulse animation)
形狀: 配合內容區塊（卡片、表格行、文字行）
```

#### 2.2.5 按鈕載入狀態
```
外觀: 小型 Spinner + 「處理中...」文字
狀態: disabled + opacity-70
游標: cursor-not-allowed
```

### 2.3 用戶體驗規則

| 規則 | 說明 |
|------|------|
| 延遲顯示 | 載入時間 < 200ms 不顯示 Spinner（避免閃爍） |
| 最小顯示 | 載入時間 > 200ms 後至少顯示 500ms（避免閃爍） |
| 防重複點擊 | 載入中禁用觸發元素 |
| 漸進增強 | 頁面骨架 → 內容填充 → 完成 |

---

## 3. 組件設計

### 3.1 組件架構

```
components/
├── ui/
│   ├── loading/
│   │   ├── GlobalProgress.tsx      # 頂部進度條 (NProgress 風格)
│   │   ├── PageLoadingOverlay.tsx  # 全屏載入遮罩
│   │   ├── Spinner.tsx             # 通用 Spinner
│   │   ├── LoadingButton.tsx       # 帶載入狀態的按鈕
│   │   ├── LoadingOverlay.tsx      # 區域載入遮罩
│   │   └── index.ts                # 統一導出
│   └── skeleton/
│       ├── Skeleton.tsx            # 基礎骨架元素
│       ├── CardSkeleton.tsx        # 卡片骨架
│       ├── TableSkeleton.tsx       # 表格骨架
│       ├── FormSkeleton.tsx        # 表單骨架
│       └── index.ts
├── layout/
│   └── NavigationProgress.tsx      # 路由導航進度條 Provider
└── providers/
    └── LoadingProvider.tsx         # 全局載入狀態管理
```

### 3.2 核心組件 API

#### 3.2.1 GlobalProgress
```tsx
// 頂部進度條，自動響應路由變化
<GlobalProgress
  color="#3B82F6"
  height={3}
  showSpinner={false}
/>
```

#### 3.2.2 Spinner
```tsx
<Spinner
  size="sm" | "md" | "lg" | "xl"
  color="primary" | "secondary" | "white"
  className="custom-class"
/>
```

#### 3.2.3 LoadingButton
```tsx
<LoadingButton
  isLoading={mutation.isPending}
  loadingText="處理中..."
  onClick={handleSubmit}
>
  提交
</LoadingButton>
```

#### 3.2.4 LoadingOverlay
```tsx
<LoadingOverlay isLoading={isLoading}>
  <DataTable ... />
</LoadingOverlay>
```

#### 3.2.5 Skeleton
```tsx
<Skeleton className="h-4 w-[200px]" />
<Skeleton className="h-12 w-full" />
<CardSkeleton count={6} />
<TableSkeleton rows={10} columns={5} />
```

### 3.3 Hook 設計

#### 3.3.1 useNavigationLoading
```tsx
// 監聽路由變化，自動顯示進度條
const { isNavigating } = useNavigationLoading();
```

#### 3.3.2 useLoadingState
```tsx
// 管理區域載入狀態
const { isLoading, startLoading, stopLoading } = useLoadingState();
```

---

## 4. 整合方案

### 4.1 路由導航整合

#### Next.js App Router 整合
```tsx
// app/[locale]/layout.tsx
import { NavigationProgress } from '@/components/layout/NavigationProgress';

export default function Layout({ children }) {
  return (
    <html>
      <body>
        <NavigationProgress />
        {children}
      </body>
    </html>
  );
}
```

#### 實現方式
- 使用 `next/navigation` 的 `usePathname` 監聽路由變化
- 開始導航時觸發進度條開始
- 頁面渲染完成後觸發進度條完成

### 4.2 數據載入整合

#### tRPC Query 整合
```tsx
// 自動骨架屏
const { data, isLoading } = api.project.getAll.useQuery({});

if (isLoading) return <TableSkeleton rows={10} columns={5} />;
return <DataTable data={data} />;
```

#### 列表刷新整合
```tsx
// 區域載入遮罩
const { data, isLoading, isFetching } = api.project.getAll.useQuery({ page });

return (
  <LoadingOverlay isLoading={isFetching && !isLoading}>
    <DataTable data={data} />
  </LoadingOverlay>
);
```

### 4.3 表單提交整合

#### Mutation 整合
```tsx
const createProject = api.project.create.useMutation();

return (
  <form onSubmit={handleSubmit}>
    {/* 表單欄位 */}
    <LoadingButton
      type="submit"
      isLoading={createProject.isPending}
      loadingText={t('submitting')}
    >
      {t('submit')}
    </LoadingButton>
  </form>
);
```

---

## 5. 驗收標準

### 5.1 功能驗收
- [ ] 頁面跳轉時顯示頂部進度條
- [ ] 列表首次載入顯示骨架屏
- [ ] 列表刷新時顯示載入遮罩
- [ ] 按鈕操作時顯示載入狀態並禁用
- [ ] 載入狀態正確結束，無殘留

### 5.2 視覺驗收
- [ ] 進度條樣式符合設計規格
- [ ] Spinner 尺寸和顏色正確
- [ ] 骨架屏佈局合理
- [ ] Dark Mode 正確支援
- [ ] 動畫流暢，無卡頓

### 5.3 用戶體驗
- [ ] 短時載入無閃爍 (<200ms)
- [ ] 載入中防止重複點擊
- [ ] 載入狀態清晰易懂
- [ ] 不影響頁面可訪問性 (ARIA)

### 5.4 技術驗收
- [ ] TypeScript 類型完整
- [ ] 組件可重用、可配置
- [ ] 無記憶體洩漏
- [ ] SSR 兼容

---

## 6. 相關參考

### 6.1 現有載入處理
- `apps/web/src/components/ui/skeleton.tsx` - shadcn/ui Skeleton（已有）
- 各頁面分散的 `isLoading` 處理

### 6.2 技術參考
- [NProgress](https://github.com/rstacruz/nprogress) - 頂部進度條靈感
- [next-nprogress-bar](https://github.com/Skyleen77/next-nprogress-bar) - Next.js 整合
- [shadcn/ui Skeleton](https://ui.shadcn.com/docs/components/skeleton) - 骨架屏基礎

---

**已確認事項** (2025-12-16):
1. ✅ 進度條顏色：使用主題 Primary 色
2. ✅ 載入模式：較輕版本（只用進度條，不用全屏遮罩）
3. ✅ 骨架屏策略：使用通用骨架組件（3-4 個），透過 props 配置適應不同場景
   - `TableSkeleton` - 適用所有列表頁
   - `CardSkeleton` - 適用所有卡片視圖
   - `FormSkeleton` - 適用所有表單頁
4. ✅ 聲音/震動反饋：不需要
