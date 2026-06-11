# i18n 實施檢查清單

> **文檔版本**: 1.0
> **創建日期**: 2025-11-03
> **狀態**: 準備實施
> **預計時間**: 10-16個工作日

---

## 📋 總覽

基於全面的項目分析和測試計劃，本檢查清單提供了詳細的實施步驟和驗收標準。

### 關鍵統計數據

根據 `I18N-IMPACT-ANALYSIS.md`：
- **總文件數**: 120
- **需處理文件**: 80 (66.67%)
- **總字符串**: 2735
- **複雜文件**: 41個 (>30個字符串)

### 時間估算

| 階段 | 工作日 | 關鍵里程碑 |
|------|--------|------------|
| Phase 1: 基礎設施 | 1-2天 | next-intl配置完成 |
| Phase 2: 翻譯文件 | 2-3天 | 所有翻譯內容準備完成 |
| Phase 3: 組件遷移 | 3-5天 | 80個文件遷移完成 |
| Phase 4: 後端整合 | 1-2天 | User locale持久化 |
| Phase 5: UI增強 | 1天 | 語言切換器完成 |
| Phase 6: 測試優化 | 2-3天 | 所有測試通過 |
| **總計** | **10-16天** | **生產環境部署** |

---

## Phase 1: 基礎設施搭建 (1-2天)

### Day 1: 核心配置

#### ✅ 任務 1.1: 安裝依賴
- [ ] 安裝 next-intl
  ```bash
  cd apps/web
  pnpm add next-intl
  ```
- [ ] 驗證安裝
  ```bash
  pnpm list next-intl
  ```
- **驗收標準**: `package.json` 包含 `next-intl` 依賴

#### ✅ 任務 1.2: 創建 i18n 配置文件
- [ ] 創建 `src/i18n/routing.ts`
  ```typescript
  import {defineRouting} from 'next-intl/routing';
  import {createNavigation} from 'next-intl/navigation';

  export const routing = defineRouting({
    locales: ['en', 'zh-TW'],
    defaultLocale: 'zh-TW',
    localePrefix: 'as-needed'
  });

  export const {Link, redirect, usePathname, useRouter} = createNavigation(routing);
  ```
- [ ] 創建 `src/i18n/request.ts`
  ```typescript
  import {getRequestConfig} from 'next-intl/server';
  import {routing} from './routing';

  export default getRequestConfig(async ({requestLocale}) => {
    let locale = await requestLocale;

    if (!locale || !routing.locales.includes(locale as any)) {
      locale = routing.defaultLocale;
    }

    return {
      locale,
      messages: (await import(`../messages/${locale}.json`)).default
    };
  });
  ```
- **驗收標準**: 文件創建成功，無TypeScript錯誤

#### ✅ 任務 1.3: 配置 middleware.ts
- [ ] 創建 `middleware.ts` 在根目錄
  ```typescript
  import createMiddleware from 'next-intl/middleware';
  import {routing} from './src/i18n/routing';

  export default createMiddleware(routing);

  export const config = {
    matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
  };
  ```
- [ ] 測試 middleware
  ```bash
  pnpm dev
  # 訪問 http://localhost:3000
  # 應該重定向到 http://localhost:3000/zh-TW
  ```
- **驗收標準**: 根路徑自動重定向到 `/zh-TW`

#### ✅ 任務 1.4: 更新 Next.js 配置
- [ ] 修改 `next.config.mjs`
  ```javascript
  import createNextIntlPlugin from 'next-intl/plugin';

  const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

  export default withNextIntl({
    // 現有配置...
  });
  ```
- **驗收標準**: `pnpm build` 成功

#### ✅ 任務 1.5: 創建翻譯文件模板
- [ ] 創建 `src/messages/` 目錄
- [ ] 創建 `src/messages/zh-TW.json`
  ```json
  {
    "common": {
      "save": "儲存",
      "cancel": "取消"
    }
  }
  ```
- [ ] 創建 `src/messages/en.json`
  ```json
  {
    "common": {
      "save": "Save",
      "cancel": "Cancel"
    }
  }
  ```
- [ ] 創建 `src/messages/index.ts`
  ```typescript
  export type Messages = typeof import('./zh-TW.json');
  ```
- **驗收標準**: 翻譯文件結構正確

#### ✅ 任務 1.6: 修改 app 目錄結構
- [ ] 創建 `src/app/[locale]/` 目錄
- [ ] 移動所有現有頁面到 `[locale]` 目錄下
  ```bash
  # 示例
  mv src/app/dashboard src/app/[locale]/dashboard
  mv src/app/projects src/app/[locale]/projects
  # ... 移動所有頁面
  ```
- [ ] 保留 `api/` 目錄在 `app/` 根目錄
- **驗收標準**: 目錄結構符合 `[locale]` 路由

#### ✅ 任務 1.7: 創建新的根 Layout
- [ ] 創建 `src/app/[locale]/layout.tsx`
  ```typescript
  import {NextIntlClientProvider} from 'next-intl';
  import {getMessages} from 'next-intl/server';
  import {notFound} from 'next/navigation';
  import {routing} from '@/i18n/routing';

  export function generateStaticParams() {
    return routing.locales.map((locale) => ({locale}));
  }

  export default async function LocaleLayout({
    children,
    params: {locale}
  }: {
    children: React.ReactNode;
    params: {locale: string};
  }) {
    if (!routing.locales.includes(locale as any)) {
      notFound();
    }

    const messages = await getMessages();

    return (
      <html lang={locale}>
        <body>
          <NextIntlClientProvider messages={messages}>
            {children}
          </NextIntlClientProvider>
        </body>
      </html>
    );
  }
  ```
- **驗收標準**: 應用可以正常運行

#### ✅ 任務 1.8: 測試基礎路由
- [ ] 訪問 `/` → 應重定向到 `/zh-TW`
- [ ] 訪問 `/zh-TW/dashboard` → 正常顯示
- [ ] 訪問 `/en/dashboard` → 正常顯示
- [ ] 訪問 `/fr/dashboard` → 顯示 404
- **驗收標準**: 所有路由測試通過

---

## Phase 2: 翻譯文件建立 (2-3天)

### Day 2-3: 提取和翻譯文本

#### ✅ 任務 2.1: 分析現有文本
- [ ] 運行分析腳本
  ```bash
  node scripts/analyze-i18n-scope.js
  ```
- [ ] 查看 `I18N-IMPACT-ANALYSIS.md`
- [ ] 識別Top 20高優先級文件
- **驗收標準**: 了解所有需要翻譯的文本

#### ✅ 任務 2.2: 建立翻譯模塊結構
- [ ] `common` - 通用按鈕和標籤
- [ ] `navigation` - 導航菜單
- [ ] `auth` - 登入/註冊
- [ ] `dashboard` - 儀表板
- [ ] `projects` - 專案管理
- [ ] `proposals` - 預算提案
- [ ] `budgetPools` - 預算池
- [ ] `vendors` - 供應商
- [ ] `quotes` - 報價單
- [ ] `purchaseOrders` - 採購單
- [ ] `expenses` - 費用記錄
- [ ] `settings` - 系統設定
- [ ] `errors` - 錯誤訊息
- [ ] `validation` - 表單驗證
- **驗收標準**: 翻譯文件結構清晰

#### ✅ 任務 2.3: 完成 common 模塊 (~100個字符串)
- [ ] 按鈕: save, cancel, delete, edit, create, submit, etc.
- [ ] 狀態: loading, success, error, pending, etc.
- [ ] 操作: search, filter, export, import, etc.
- **驗收標準**: common 模塊100%完成

#### ✅ 任務 2.4: 完成 navigation 模塊 (~20個字符串)
- [ ] 主要菜單項
- [ ] 子菜單項
- [ ] 麵包屑導航
- **驗收標準**: navigation 模塊100%完成

#### ✅ 任務 2.5: 完成 auth 模塊 (~30個字符串)
- [ ] 登入頁面
- [ ] 註冊頁面
- [ ] 忘記密碼頁面
- [ ] 錯誤訊息
- **驗收標準**: auth 模塊100%完成

#### ✅ 任務 2.6-2.13: 完成業務模塊 (~2000個字符串)
- [ ] dashboard (~60個)
- [ ] projects (~250個)
- [ ] proposals (~200個)
- [ ] budgetPools (~150個)
- [ ] vendors (~100個)
- [ ] quotes (~100個)
- [ ] purchaseOrders (~150個)
- [ ] expenses (~200個)
- **驗收標準**: 所有業務模塊100%完成

#### ✅ 任務 2.14: 完成 errors 模塊 (~50個字符串)
- [ ] HTTP錯誤 (404, 500, etc.)
- [ ] 業務錯誤
- [ ] 網路錯誤
- **驗收標準**: errors 模塊100%完成

#### ✅ 任務 2.15: 完成 validation 模塊 (~30個字符串)
- [ ] 必填欄位驗證
- [ ] 格式驗證 (email, phone, etc.)
- [ ] 範圍驗證
- **驗收標準**: validation 模塊100%完成

#### ✅ 任務 2.16: 翻譯質量審查
- [ ] 運行完整性測試
  ```bash
  pnpm test tests/i18n/translation-completeness.test.ts
  ```
- [ ] 檢查佔位符一致性
- [ ] 檢查長度合理性
- **驗收標準**: 所有翻譯測試通過

---

## Phase 3: 組件遷移 (3-5天)

### 優先級分組

#### P0: 核心認證與佈局 (Day 4)

##### ✅ 任務 3.1: 登入/註冊頁面
- [ ] `app/[locale]/login/page.tsx`
  - 替換所有硬編碼中文
  - 使用 `useTranslations('auth')`
  - 測試中英文切換
- [ ] `app/[locale]/register/page.tsx`
- [ ] `app/[locale]/forgot-password/page.tsx`
- **驗收標準**: 登入流程中英文完整

##### ✅ 任務 3.2: 主要佈局組件
- [ ] `components/layout/sidebar.tsx`
  - 導航菜單翻譯
  - 使用 `useTranslations('navigation')`
- [ ] `components/layout/top-bar.tsx`
  - 頂部欄翻譯
  - 集成語言切換器
- [ ] `app/[locale]/layout.tsx`
  - Meta標籤本地化
- **驗收標準**: 佈局組件中英文切換流暢

##### ✅ 任務 3.3: 儀表板頁面
- [ ] `app/[locale]/dashboard/page.tsx` (61個字符串)
- [ ] `app/[locale]/dashboard/pm/page.tsx` (54個字符串)
- [ ] `app/[locale]/dashboard/supervisor/page.tsx` (60個字符串)
- **驗收標準**: 儀表板數據和圖表標籤正確翻譯

#### P1: 核心業務頁面 (Day 5-6)

##### ✅ 任務 3.4: 專案管理 (最複雜，優先處理)
- [ ] `app/[locale]/projects/page.tsx` (89個字符串)
- [ ] `app/[locale]/projects/[id]/page.tsx` (96個字符串)
- [ ] `app/[locale]/projects/new/page.tsx`
- [ ] `app/[locale]/projects/[id]/edit/page.tsx`
- [ ] `components/project/ProjectForm.tsx`
- **驗收標準**: 專案CRUD流程完整測試

##### ✅ 任務 3.5: 預算提案
- [ ] `app/[locale]/proposals/page.tsx`
- [ ] `app/[locale]/proposals/[id]/page.tsx`
- [ ] `app/[locale]/proposals/new/page.tsx`
- [ ] `components/proposal/ProposalForm.tsx`
- [ ] `components/proposal/ProposalActions.tsx`
- [ ] `components/proposal/CommentSection.tsx`
- **驗收標準**: 提案審批流程中英文正確

##### ✅ 任務 3.6: 預算池管理
- [ ] `app/[locale]/budget-pools/page.tsx` (59個字符串)
- [ ] `app/[locale]/budget-pools/[id]/page.tsx` (60個字符串)
- [ ] `app/[locale]/budget-pools/new/page.tsx`
- [ ] `app/[locale]/budget-pools/[id]/edit/page.tsx`
- **驗收標準**: 預算池數據和圖表正確

#### P2: 輔助功能頁面 (Day 7)

##### ✅ 任務 3.7: 供應商管理
- [ ] `app/[locale]/vendors/page.tsx`
- [ ] `app/[locale]/vendors/[id]/page.tsx`
- [ ] `app/[locale]/vendors/new/page.tsx`
- [ ] `app/[locale]/vendors/[id]/edit/page.tsx`
- **驗收標準**: 供應商CRUD正常

##### ✅ 任務 3.8: 報價單管理
- [ ] `app/[locale]/quotes/page.tsx`
- [ ] `app/[locale]/quotes/new/page.tsx` (56個字符串)
- [ ] `app/[locale]/quotes/[id]/edit/page.tsx` (53個字符串)
- **驗收標準**: 報價單上傳和編輯流程正確

##### ✅ 任務 3.9: 採購單管理
- [ ] `app/[locale]/purchase-orders/page.tsx`
- [ ] `app/[locale]/purchase-orders/[id]/page.tsx` (67個字符串)
- [ ] `components/purchase-order/PurchaseOrderForm.tsx` (73個字符串)
- **驗收標準**: 採購單生成和查看正常

##### ✅ 任務 3.10: 費用記錄
- [ ] `app/[locale]/expenses/page.tsx` (60個字符串)
- [ ] `app/[locale]/expenses/[id]/page.tsx` (57個字符串)
- [ ] `app/[locale]/expenses/new/page.tsx`
- [ ] `components/expense/ExpenseForm.tsx` (89個字符串)
- **驗收標準**: 費用記錄和審批流程正確

#### P3: 管理頁面 (Day 8)

##### ✅ 任務 3.11: 用戶管理
- [ ] `app/[locale]/users/page.tsx`
- [ ] `app/[locale]/users/new/page.tsx`
- [ ] `app/[locale]/users/[id]/edit/page.tsx`
- **驗收標準**: 用戶CRUD正常

##### ✅ 任務 3.12: 系統設定
- [ ] `app/[locale]/settings/page.tsx` (65個字符串)
- **驗收標準**: 語言偏好設定功能完整

##### ✅ 任務 3.13: 通知中心
- [ ] `app/[locale]/notifications/page.tsx`
- [ ] `components/notification/NotificationBell.tsx`
- [ ] `components/notification/NotificationDropdown.tsx`
- **驗收標準**: 通知訊息正確翻譯

---

## Phase 4: 後端整合 (1-2天)

### Day 9: 數據庫和API

#### ✅ 任務 4.1: 更新 Prisma Schema
- [ ] 修改 `packages/db/prisma/schema.prisma`
  ```prisma
  model User {
    // ...現有欄位
    locale        String    @default("zh-TW")
  }
  ```
- [ ] 創建遷移
  ```bash
  pnpm db:migrate -- --name add_user_locale
  ```
- [ ] 執行遷移
  ```bash
  pnpm db:migrate
  ```
- **驗收標準**: User表包含locale欄位

#### ✅ 任務 4.2: 更新 Settings API
- [ ] 修改 `packages/api/src/routers/user.ts`
  ```typescript
  updateSettings: protectedProcedure
    .input(z.object({
      locale: z.enum(['zh-TW', 'en']).optional(),
      // ... 其他設定
    }))
    .mutation(async ({ctx, input}) => {
      return ctx.prisma.user.update({
        where: {id: ctx.session.user.id},
        data: {locale: input.locale},
      });
    })
  ```
- **驗收標準**: 語言偏好可以保存到數據庫

#### ✅ 任務 4.3: 實現語言偏好持久化
- [ ] 修改 `middleware.ts`
  ```typescript
  // 從數據庫讀取用戶語言偏好
  // 優先級: URL > 用戶設定 > Cookie > 默認
  ```
- [ ] 測試流程:
  1. 用戶在設定頁面選擇英文
  2. 重新加載頁面 → 應自動顯示英文
  3. 打開新標籤頁 → 應自動顯示英文
- **驗收標準**: 語言偏好在不同會話中保持

#### ✅ 任務 4.4: 錯誤訊息本地化
- [ ] 創建 `packages/api/src/lib/errors.ts`
  ```typescript
  export const getErrorMessage = (key: string, locale: string) => {
    const messages = {
      'zh-TW': {...},
      'en': {...}
    };
    return messages[locale]?.[key] || messages['zh-TW'][key];
  };
  ```
- [ ] 更新所有 tRPC 錯誤拋出
  ```typescript
  throw new TRPCError({
    code: 'NOT_FOUND',
    message: getErrorMessage('project.notFound', ctx.locale)
  });
  ```
- **驗收標準**: API錯誤訊息根據語言返回

#### ✅ 任務 4.5: Email 通知本地化
- [ ] 修改 `packages/api/src/lib/email.ts`
  ```typescript
  const getEmailTemplate = (type: string, locale: string, data: any) => {
    const templates = {
      'zh-TW': {...},
      'en': {...}
    };
    // ...
  };
  ```
- [ ] 測試:
  - 中文用戶收到中文Email
  - 英文用戶收到英文Email
- **驗收標準**: Email模板根據用戶語言發送

---

## Phase 5: UI增強 (1天)

### Day 10: 語言切換器和UX優化

#### ✅ 任務 5.1: 創建 LocaleSwitcher 組件
- [ ] 創建 `components/i18n/LocaleSwitcher.tsx`
  ```typescript
  'use client';

  import {useLocale, useTranslations} from 'next-intl';
  import {useRouter, usePathname} from '@/i18n/routing';
  import {Select} from '@/components/ui/select';

  export function LocaleSwitcher() {
    const t = useTranslations('settings');
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();

    const handleChange = (newLocale: string) => {
      router.replace(pathname, {locale: newLocale});
    };

    return (
      <Select value={locale} onChange={(e) => handleChange(e.target.value)}>
        <option value="zh-TW">{t('languages.zhTW')}</option>
        <option value="en">{t('languages.en')}</option>
      </Select>
    );
  }
  ```
- **驗收標準**: 組件可以正常切換語言

#### ✅ 任務 5.2: 集成到 TopBar
- [ ] 修改 `components/layout/top-bar.tsx`
  - 在右上角添加語言切換器
  - 確保響應式設計（移動端）
- **驗收標準**: TopBar包含語言切換器

#### ✅ 任務 5.3: 集成到 Settings 頁面
- [ ] 修改 `app/[locale]/settings/page.tsx`
  - 添加語言偏好選項
  - 連接到 API 保存設定
- **驗收標準**: 設定頁面可以保存語言偏好

#### ✅ 任務 5.4: 添加切換動畫
- [ ] 使用 Framer Motion 或 CSS Transition
- [ ] 淡入淡出效果
- **驗收標準**: 切換過程流暢

#### ✅ 任務 5.5: 狀態保持優化
- [ ] 確保表單數據在切換後保留
- [ ] 確保滾動位置保持
- [ ] 確保篩選條件保持
- **驗收標準**: 切換後用戶狀態不丟失

#### ✅ 任務 5.6: 移動端優化
- [ ] 測試手機瀏覽器
- [ ] 測試平板瀏覽器
- [ ] 確保觸控體驗良好
- **驗收標準**: 移動端體驗流暢

---

## Phase 6: 測試與優化 (2-3天)

### Day 11: 自動化測試

#### ✅ 任務 6.1: 單元測試
- [ ] 運行翻譯完整性測試
  ```bash
  pnpm test tests/i18n/translation-completeness.test.ts
  ```
- [ ] 運行工具函數測試
  ```bash
  pnpm test tests/i18n/utils.test.ts
  ```
- [ ] 組件快照測試
  ```bash
  pnpm test tests/components/LocaleSwitcher.test.tsx
  ```
- **驗收標準**: 100%測試通過

#### ✅ 任務 6.2: 集成測試
- [ ] 路由導航測試
  ```bash
  pnpm test tests/integration/routing.test.tsx
  ```
- [ ] API本地化測試
  ```bash
  pnpm test tests/integration/api-i18n.test.ts
  ```
- **驗收標準**: 所有集成測試通過

### Day 12: E2E測試

#### ✅ 任務 6.3: 關鍵業務流程E2E
- [ ] 專案管理流程
  ```bash
  pnpm test:e2e e2e/i18n/project-workflow.spec.ts
  ```
- [ ] 預算提案流程
  ```bash
  pnpm test:e2e e2e/i18n/proposal-workflow.spec.ts
  ```
- [ ] 費用記錄流程
  ```bash
  pnpm test:e2e e2e/i18n/expense-workflow.spec.ts
  ```
- **驗收標準**: P0測試100%通過

#### ✅ 任務 6.4: 輔助功能E2E
- [ ] 供應商管理
- [ ] 報價單管理
- [ ] 採購單管理
- **驗收標準**: P1測試>95%通過

#### ✅ 任務 6.5: 跨瀏覽器測試
- [ ] Chrome (最新版本)
- [ ] Firefox (最新版本)
- [ ] Safari (最新版本)
- [ ] Edge (最新版本)
- [ ] Mobile Safari (iOS 15+)
- [ ] Mobile Chrome (Android 10+)
- **驗收標準**: 所有瀏覽器測試通過

### Day 13: 性能與可訪問性

#### ✅ 任務 6.6: 性能測試
- [ ] 首屏加載測試
  ```bash
  lighthouse http://localhost:3000/zh-TW/dashboard --output=json
  lighthouse http://localhost:3000/en/dashboard --output=json
  ```
  - FCP < 1.5s (+100ms 容許)
  - LCP < 2.5s (+150ms 容許)
  - TBT < 300ms (+50ms 容許)
- [ ] 語言切換性能測試
  ```bash
  pnpm test tests/performance/locale-switching.perf.ts
  ```
  - 切換時間 < 300ms
- [ ] Bundle Size 分析
  ```bash
  ANALYZE=true pnpm build
  ```
  - 單個語言包 < 50KB (gzipped)
  - 總增加 < 100KB
- **驗收標準**: 所有性能指標達標

#### ✅ 任務 6.7: 可訪問性測試
- [ ] WCAG 2.1 AA測試
  ```bash
  pnpm test:a11y
  ```
  - 0個AA級別錯誤
- [ ] 鍵盤導航測試
  - 所有功能可用鍵盤操作
- [ ] 屏幕閱讀器測試
  - NVDA / JAWS / VoiceOver
- **驗收標準**: 無可訪問性阻塞問題

#### ✅ 任務 6.8: 翻譯質量審查
- [ ] 檢查翻譯遺漏
  - 運行自動化檢查腳本
- [ ] 檢查長文本排版
  - 英文文本不破壞佈局
- [ ] 檢查上下文適當性
  - 翻譯符合業務場景
- **驗收標準**: 無翻譯質量問題

#### ✅ 任務 6.9: 修復缺陷
- [ ] 修復所有P0缺陷
- [ ] 修復所有P1缺陷
- [ ] 評估P2缺陷是否需要修復
- **驗收標準**: P0/P1缺陷清零

---

## 部署準備

### ✅ 任務 7.1: 文檔更新
- [ ] 更新 README.md
  - 添加多語言功能說明
- [ ] 更新 DEVELOPMENT-SETUP.md
  - 添加翻譯文件管理指南
- [ ] 創建翻譯貢獻指南
  - `docs/TRANSLATION-GUIDE.md`
- **驗收標準**: 文檔完整更新

### ✅ 任務 7.2: 環境變量配置
- [ ] 添加到 `.env.example`
  ```bash
  NEXT_PUBLIC_DEFAULT_LOCALE=zh-TW
  NEXT_PUBLIC_SUPPORTED_LOCALES=zh-TW,en
  ```
- [ ] 更新各環境配置
  - 開發環境
  - Staging環境
  - 生產環境
- **驗收標準**: 所有環境配置正確

### ✅ 任務 7.3: CI/CD 更新
- [ ] 更新 GitHub Actions
  - 添加i18n測試步驟
  - 添加翻譯完整性檢查
- [ ] 添加部署前檢查
  - 翻譯文件必須完整
  - 所有測試必須通過
- **驗收標準**: CI/CD流程包含i18n檢查

### ✅ 任務 7.4: Staging 部署
- [ ] 部署到Staging環境
- [ ] 完整UAT測試
  - 中文流程
  - 英文流程
  - 切換流程
- [ ] 性能監控
  - 首屏加載時間
  - API響應時間
- **驗收標準**: Staging環境穩定

### ✅ 任務 7.5: 生產部署
- [ ] 生產環境部署
- [ ] 監控部署過程
- [ ] 驗證關鍵流程
  - 登入/登出
  - 專案管理
  - 提案審批
- [ ] 設置錯誤監控
  - Sentry / LogRocket
- **驗收標準**: 生產環境運行正常

---

## 驗收標準總結

### 必須達成 (Blocker)

- ✅ 翻譯完整性100%
  - 所有語言的key完全一致
  - 無空翻譯
  - 佔位符一致

- ✅ 核心功能100%翻譯
  - 登入/登出流程
  - 專案CRUD
  - 提案審批流程
  - 費用記錄流程

- ✅ 語言切換功能完整
  - 無刷新切換
  - 狀態保持
  - 偏好持久化

- ✅ 性能不退化
  - FCP增量 < 100ms
  - 切換時間 < 300ms
  - Bundle增加 < 100KB

- ✅ P0 E2E測試100%通過

### 應該達成 (Major)

- ⚠️ 輔助功能翻譯完整
  - 供應商、報價單、採購單

- ⚠️ 可訪問性合規
  - 0個WCAG AA錯誤

- ⚠️ 跨瀏覽器兼容
  - Chrome/Safari/Firefox 100%

- ⚠️ P1 E2E測試>95%通過

### 建議達成 (Minor)

- 📝 管理頁面翻譯
  - 用戶管理、通知中心

- 📝 Email模板本地化

- 📝 P2 E2E測試>90%通過

---

## 風險緩解清單

### 技術風險

#### 風險1: 工作量超出預期
- **緩解措施**:
  - [ ] 分階段實施，優先核心頁面
  - [ ] 每日進度跟蹤
  - [ ] 必要時調整人力

#### 風險2: 翻譯遺漏或錯誤
- **緩解措施**:
  - [ ] 建立自動化檢查工具
  - [ ] Code Review流程檢查翻譯
  - [ ] 測試階段發現問題

#### 風險3: 性能退化
- **緩解措施**:
  - [ ] 持續性能監控
  - [ ] Bundle size限制
  - [ ] 按需加載翻譯

#### 風險4: UI破版
- **緩解措施**:
  - [ ] 預留30%文本擴展空間
  - [ ] 響應式設計
  - [ ] 跨瀏覽器測試

### 組織風險

#### 風險5: 翻譯質量參差
- **緩解措施**:
  - [ ] 建立翻譯指南
  - [ ] 翻譯Review流程
  - [ ] 使用專業翻譯工具輔助

#### 風險6: 測試覆蓋不足
- **緩解措施**:
  - [ ] 完整的測試計劃
  - [ ] 自動化測試優先
  - [ ] UAT用戶參與測試

---

## 每日檢查點

### 每日結束前

- [ ] 更新進度跟蹤表
- [ ] 提交代碼到版本控制
- [ ] 運行測試套件
- [ ] 記錄遇到的問題
- [ ] 計劃明天任務

### 每週檢查點

- [ ] 審查本週完成情況
- [ ] 調整下週計劃
- [ ] 風險評估
- [ ] 團隊同步會議

---

## 完成標誌

當以下所有條件滿足時，i18n實施完成：

✅ **功能完整**:
- [ ] 所有頁面和組件支援雙語
- [ ] 語言切換功能正常
- [ ] 語言偏好持久化

✅ **質量保證**:
- [ ] 翻譯完整性100%
- [ ] 所有自動化測試通過
- [ ] 性能指標達標

✅ **部署就緒**:
- [ ] 文檔完整更新
- [ ] CI/CD流程更新
- [ ] 生產環境部署成功

✅ **用戶驗收**:
- [ ] UAT測試通過
- [ ] 無P0/P1缺陷
- [ ] 用戶反饋良好

---

**文檔維護者**: Development Team + AI Assistant
**最後更新**: 2025-11-03
**版本**: 1.0
**狀態**: ✅ 準備開始實施
