# 多語言功能實施計劃 (i18n Implementation Plan)

> **文檔版本**: 1.0
> **創建日期**: 2025-11-03
> **狀態**: 規劃階段
> **目標語言**: 繁體中文 (zh-TW) + 英文 (en) + 未來擴展

---

## 📋 目錄

1. [需求概述](#需求概述)
2. [技術方案選擇](#技術方案選擇)
3. [架構設計](#架構設計)
4. [實施階段](#實施階段)
5. [文件結構](#文件結構)
6. [開發規範](#開發規範)
7. [測試策略](#測試策略)
8. [部署考量](#部署考量)

---

## 需求概述

### 功能目標
- ✅ 支援繁體中文 (zh-TW) 和英文 (en) 雙語切換
- ✅ 用戶可以在系統設置中選擇偏好語言
- ✅ 語言設置持久化（存儲在用戶 Profile 或 Cookie）
- ✅ 所有 UI 文本、錯誤訊息、表單驗證訊息均支援多語言
- ✅ 日期、數字、貨幣格式化根據語言自動調整
- ✅ 易於擴展其他語言（如簡體中文、日文等）

### 非功能需求
- ⚡ **性能**: 翻譯文件按需加載，不影響首屏加載速度
- 🔒 **類型安全**: TypeScript 完整支援，翻譯 key 自動補全
- 🧩 **可維護性**: 翻譯文件結構化管理，易於添加和修改
- 📦 **Bundle Size**: 僅加載當前語言的翻譯文件
- 🎨 **UI/UX**: 語言切換無需刷新頁面，即時生效

---

## 技術方案選擇

### 推薦方案: next-intl

**選擇理由:**
1. ✅ **Next.js 14+ 原生支援** - 完美支援 App Router 和 Server Components
2. ✅ **零配置 i18n routing** - 自動處理 /en, /zh-TW 路由
3. ✅ **TypeScript 類型安全** - 翻譯 key 自動補全和類型檢查
4. ✅ **Server & Client Components** - 同時支援服務端和客戶端組件
5. ✅ **性能優化** - 翻譯僅在服務端渲染時載入，客戶端 bundle 更小
6. ✅ **Rich formatting** - 支援複數、日期、數字、貨幣格式化
7. ✅ **成熟穩定** - 社區活躍，文檔完善

**對比其他方案:**

| 方案 | Next.js 14 支援 | TypeScript | Bundle Size | Server Components | 學習曲線 |
|------|----------------|------------|-------------|-------------------|----------|
| **next-intl** | ✅ 原生 | ✅ 完整 | 🟢 小 | ✅ 完整 | 🟢 低 |
| react-i18next | ⚠️ 需配置 | ✅ 良好 | 🟡 中 | ⚠️ 部分 | 🟡 中 |
| next-translate | ⚠️ 需配置 | ✅ 良好 | 🟢 小 | ❌ 有限 | 🟡 中 |
| i18next | ⚠️ 需配置 | ⚠️ 需插件 | 🔴 大 | ❌ 不支援 | 🔴 高 |

---

## 架構設計

### 1. 文件結構

```
apps/web/
├── src/
│   ├── i18n/
│   │   ├── config.ts                    # i18n 配置文件
│   │   ├── request.ts                   # Server-side i18n 請求處理
│   │   └── routing.ts                   # 路由配置
│   │
│   ├── messages/                        # 翻譯文件目錄
│   │   ├── en.json                      # 英文翻譯
│   │   ├── zh-TW.json                   # 繁體中文翻譯
│   │   └── index.ts                     # 翻譯文件類型定義
│   │
│   ├── app/
│   │   ├── [locale]/                    # 語言路由包裝
│   │   │   ├── layout.tsx               # 根 Layout (包含語言提供者)
│   │   │   ├── dashboard/
│   │   │   ├── projects/
│   │   │   ├── proposals/
│   │   │   └── ...                      # 所有現有頁面
│   │   │
│   │   └── api/                         # API 路由 (不受語言路由影響)
│   │       ├── auth/
│   │       └── trpc/
│   │
│   ├── components/
│   │   ├── i18n/
│   │   │   ├── LocaleSwitcher.tsx       # 語言切換器組件
│   │   │   └── ClientProvider.tsx       # 客戶端 i18n Provider
│   │   └── ...
│   │
│   └── lib/
│       └── i18n.ts                      # i18n 工具函數
│
├── middleware.ts                        # Next.js 中間件 (處理語言路由)
└── next.config.mjs                      # Next.js 配置 (添加 i18n 設定)
```

### 2. 翻譯文件結構

**messages/zh-TW.json** (繁體中文)
```json
{
  "common": {
    "save": "儲存",
    "cancel": "取消",
    "delete": "刪除",
    "edit": "編輯",
    "create": "新增",
    "search": "搜尋",
    "filter": "篩選",
    "export": "匯出",
    "loading": "載入中...",
    "error": "發生錯誤",
    "success": "操作成功"
  },
  "navigation": {
    "dashboard": "首頁",
    "projects": "專案管理",
    "proposals": "預算提案",
    "budgetPools": "預算池",
    "vendors": "供應商管理",
    "quotes": "報價單管理",
    "purchaseOrders": "採購單管理",
    "expenses": "費用記錄",
    "users": "用戶管理",
    "settings": "系統設定"
  },
  "dashboard": {
    "title": "儀表板",
    "welcome": "歡迎回來，{name}",
    "stats": {
      "totalProjects": "總專案數",
      "activeProjects": "進行中專案",
      "totalBudget": "總預算",
      "usedBudget": "已使用預算"
    }
  },
  "projects": {
    "title": "專案管理",
    "createNew": "新增專案",
    "editProject": "編輯專案",
    "projectName": "專案名稱",
    "description": "專案描述",
    "status": "狀態",
    "manager": "專案經理",
    "supervisor": "審核主管",
    "budgetPool": "預算池",
    "startDate": "開始日期",
    "endDate": "結束日期",
    "statuses": {
      "draft": "草稿",
      "inProgress": "進行中",
      "completed": "已完成",
      "archived": "已歸檔"
    },
    "validation": {
      "nameRequired": "請輸入專案名稱",
      "managerRequired": "請選擇專案經理",
      "budgetPoolRequired": "請選擇預算池"
    }
  },
  "auth": {
    "login": "登入",
    "logout": "登出",
    "email": "Email",
    "password": "密碼",
    "rememberMe": "記住我",
    "forgotPassword": "忘記密碼？",
    "signIn": "登入帳號",
    "signUp": "註冊帳號",
    "errors": {
      "invalidCredentials": "Email 或密碼錯誤",
      "emailRequired": "請輸入 Email",
      "passwordRequired": "請輸入密碼",
      "emailInvalid": "Email 格式不正確"
    }
  },
  "settings": {
    "title": "系統設定",
    "profile": "個人資料",
    "language": "語言設定",
    "selectLanguage": "選擇語言",
    "languages": {
      "en": "English",
      "zhTW": "繁體中文"
    }
  },
  "errors": {
    "notFound": "找不到頁面",
    "unauthorized": "未授權訪問",
    "serverError": "伺服器錯誤",
    "networkError": "網路連接錯誤"
  }
}
```

**messages/en.json** (英文)
```json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "create": "Create",
    "search": "Search",
    "filter": "Filter",
    "export": "Export",
    "loading": "Loading...",
    "error": "An error occurred",
    "success": "Operation successful"
  },
  "navigation": {
    "dashboard": "Dashboard",
    "projects": "Projects",
    "proposals": "Budget Proposals",
    "budgetPools": "Budget Pools",
    "vendors": "Vendors",
    "quotes": "Quotes",
    "purchaseOrders": "Purchase Orders",
    "expenses": "Expenses",
    "users": "Users",
    "settings": "Settings"
  },
  "dashboard": {
    "title": "Dashboard",
    "welcome": "Welcome back, {name}",
    "stats": {
      "totalProjects": "Total Projects",
      "activeProjects": "Active Projects",
      "totalBudget": "Total Budget",
      "usedBudget": "Used Budget"
    }
  },
  "projects": {
    "title": "Projects",
    "createNew": "Create Project",
    "editProject": "Edit Project",
    "projectName": "Project Name",
    "description": "Description",
    "status": "Status",
    "manager": "Project Manager",
    "supervisor": "Supervisor",
    "budgetPool": "Budget Pool",
    "startDate": "Start Date",
    "endDate": "End Date",
    "statuses": {
      "draft": "Draft",
      "inProgress": "In Progress",
      "completed": "Completed",
      "archived": "Archived"
    },
    "validation": {
      "nameRequired": "Please enter project name",
      "managerRequired": "Please select project manager",
      "budgetPoolRequired": "Please select budget pool"
    }
  },
  "auth": {
    "login": "Login",
    "logout": "Logout",
    "email": "Email",
    "password": "Password",
    "rememberMe": "Remember me",
    "forgotPassword": "Forgot password?",
    "signIn": "Sign In",
    "signUp": "Sign Up",
    "errors": {
      "invalidCredentials": "Invalid email or password",
      "emailRequired": "Please enter email",
      "passwordRequired": "Please enter password",
      "emailInvalid": "Invalid email format"
    }
  },
  "settings": {
    "title": "Settings",
    "profile": "Profile",
    "language": "Language",
    "selectLanguage": "Select Language",
    "languages": {
      "en": "English",
      "zhTW": "繁體中文"
    }
  },
  "errors": {
    "notFound": "Page not found",
    "unauthorized": "Unauthorized access",
    "serverError": "Server error",
    "networkError": "Network connection error"
  }
}
```

### 3. 組件使用示例

**Server Component 使用:**
```tsx
import {useTranslations} from 'next-intl';

export default function ProjectsPage() {
  const t = useTranslations('projects');

  return (
    <div>
      <h1>{t('title')}</h1>
      <Button>{t('createNew')}</Button>
    </div>
  );
}
```

**Client Component 使用:**
```tsx
'use client';

import {useTranslations} from 'next-intl';

export default function ProjectForm() {
  const t = useTranslations('projects');

  return (
    <form>
      <Label>{t('projectName')}</Label>
      <Input placeholder={t('projectName')} />
    </form>
  );
}
```

**動態參數:**
```tsx
const t = useTranslations('dashboard');

<p>{t('welcome', {name: user.name})}</p>
// 輸出: "歡迎回來，張三" (zh-TW) 或 "Welcome back, John" (en)
```

---

## 實施階段

### Phase 1: 基礎設施搭建 (1-2 天)

#### 任務清單:
- [ ] 1.1 安裝 next-intl 依賴
- [ ] 1.2 創建 i18n 配置文件
- [ ] 1.3 設置 middleware.ts 處理語言路由
- [ ] 1.4 更新 next.config.mjs 配置
- [ ] 1.5 創建翻譯文件模板 (en.json, zh-TW.json)
- [ ] 1.6 修改 app 目錄結構為 [locale] 路由
- [ ] 1.7 創建 LocaleSwitcher 組件

#### 技術細節:

**1. 安裝依賴**
```bash
pnpm add next-intl
```

**2. middleware.ts**
```typescript
import createMiddleware from 'next-intl/middleware';
import {routing} from './src/i18n/routing';

export default createMiddleware(routing);

export const config = {
  // 匹配所有路徑，除了 API、靜態資源、圖片
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
};
```

**3. i18n/routing.ts**
```typescript
import {defineRouting} from 'next-intl/routing';
import {createNavigation} from 'next-intl/navigation';

export const routing = defineRouting({
  locales: ['en', 'zh-TW'],
  defaultLocale: 'zh-TW',
  localePrefix: 'as-needed' // /zh-TW 可省略，/en 必須
});

export const {Link, redirect, usePathname, useRouter, getPathname} = createNavigation(routing);
```

**4. i18n/request.ts**
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

**5. app/[locale]/layout.tsx**
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

### Phase 2: 翻譯文件建立 (2-3 天)

#### 任務清單:
- [ ] 2.1 分析所有頁面，提取需翻譯的文本
- [ ] 2.2 建立翻譯 key 命名規範
- [ ] 2.3 完成 common 模塊翻譯（按鈕、標籤等通用文本）
- [ ] 2.4 完成 navigation 模塊翻譯（導航菜單）
- [ ] 2.5 完成 auth 模塊翻譯（登入、註冊頁面）
- [ ] 2.6 完成 dashboard 模塊翻譯
- [ ] 2.7 完成 projects 模塊翻譯
- [ ] 2.8 完成 proposals 模塊翻譯
- [ ] 2.9 完成 budgetPools 模塊翻譯
- [ ] 2.10 完成 vendors 模塊翻譯
- [ ] 2.11 完成 quotes 模塊翻譯
- [ ] 2.12 完成 purchaseOrders 模塊翻譯
- [ ] 2.13 完成 expenses 模塊翻譯
- [ ] 2.14 完成 errors 模塊翻譯（錯誤訊息）
- [ ] 2.15 完成 validation 模塊翻譯（表單驗證訊息）

#### 翻譯 Key 命名規範:
```
{模塊}.{功能}.{元素}

示例:
- projects.createNew           // 新增專案按鈕
- projects.form.nameLabel      // 表單欄位標籤
- projects.validation.nameRequired  // 驗證錯誤訊息
- projects.statuses.inProgress // 狀態選項
```

### Phase 3: 組件遷移 (3-5 天)

#### 任務優先級:

**P0 - 核心頁面 (必須先完成):**
- [ ] 3.1 登入/註冊頁面 (apps/web/src/app/login, register)
- [ ] 3.2 儀表板 (apps/web/src/app/dashboard)
- [ ] 3.3 導航組件 (Sidebar, TopBar)
- [ ] 3.4 系統設定頁面 (apps/web/src/app/settings)

**P1 - 主要功能頁面:**
- [ ] 3.5 專案管理 (apps/web/src/app/projects)
- [ ] 3.6 預算提案 (apps/web/src/app/proposals)
- [ ] 3.7 預算池管理 (apps/web/src/app/budget-pools)

**P2 - 輔助功能頁面:**
- [ ] 3.8 供應商管理 (apps/web/src/app/vendors)
- [ ] 3.9 報價單管理 (apps/web/src/app/quotes)
- [ ] 3.10 採購單管理 (apps/web/src/app/purchase-orders)
- [ ] 3.11 費用記錄 (apps/web/src/app/expenses)

**P3 - 管理頁面:**
- [ ] 3.12 用戶管理 (apps/web/src/app/users)
- [ ] 3.13 通知中心 (apps/web/src/app/notifications)

#### 遷移步驟 (以 projects/page.tsx 為例):

**Before (硬編碼中文):**
```tsx
export default function ProjectsPage() {
  return (
    <div>
      <h1>專案管理</h1>
      <Button>新增專案</Button>
      <Input placeholder="搜尋專案名稱..." />
    </div>
  );
}
```

**After (使用 i18n):**
```tsx
import {useTranslations} from 'next-intl';

export default function ProjectsPage() {
  const t = useTranslations('projects');
  const common = useTranslations('common');

  return (
    <div>
      <h1>{t('title')}</h1>
      <Button>{t('createNew')}</Button>
      <Input placeholder={t('searchPlaceholder')} />
    </div>
  );
}
```

### Phase 4: 後端整合 (1-2 天)

#### 任務清單:
- [ ] 4.1 更新 User model 添加 locale 欄位
- [ ] 4.2 創建數據庫遷移
- [ ] 4.3 更新 Settings API 保存語言偏好
- [ ] 4.4 更新 tRPC 錯誤訊息支援多語言
- [ ] 4.5 Email 通知模板支援多語言

#### 數據庫 Schema 更新:

**prisma/schema.prisma**
```prisma
model User {
  id            String    @id @default(uuid())
  email         String    @unique
  name          String?
  locale        String    @default("zh-TW") // 新增欄位
  // ... 其他欄位
}
```

**Migration:**
```bash
pnpm db:migrate -- --name add_user_locale
```

#### tRPC Error Messages:

**packages/api/src/lib/errors.ts**
```typescript
export const getErrorMessage = (key: string, locale: string) => {
  const messages = {
    'zh-TW': {
      'project.notFound': '找不到專案',
      'proposal.unauthorized': '無權限訪問此提案',
      // ...
    },
    'en': {
      'project.notFound': 'Project not found',
      'proposal.unauthorized': 'Unauthorized to access this proposal',
      // ...
    }
  };

  return messages[locale]?.[key] || messages['zh-TW'][key];
};
```

### Phase 5: UI 增強 (1 天)

#### 任務清單:
- [ ] 5.1 創建 LocaleSwitcher 組件（下拉選單）
- [ ] 5.2 將語言切換器集成到 TopBar
- [ ] 5.3 將語言選項添加到 Settings 頁面
- [ ] 5.4 添加語言切換動畫效果
- [ ] 5.5 語言切換時保持當前頁面狀態

#### LocaleSwitcher 組件:

**components/i18n/LocaleSwitcher.tsx**
```tsx
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

### Phase 6: 測試與優化 (2-3 天)

#### 任務清單:
- [ ] 6.1 創建 i18n 測試工具函數
- [ ] 6.2 單元測試：翻譯文件完整性檢查
- [ ] 6.3 E2E 測試：語言切換功能
- [ ] 6.4 E2E 測試：每個語言的關鍵頁面截圖對比
- [ ] 6.5 性能測試：翻譯文件加載時間
- [ ] 6.6 Bundle size 分析：確保不影響首屏加載
- [ ] 6.7 修復翻譯缺失問題
- [ ] 6.8 優化長文本排版
- [ ] 6.9 測試 RTL 語言支援（為未來擴展做準備）

#### 測試示例:

**tests/i18n/translation-completeness.test.ts**
```typescript
import en from '@/messages/en.json';
import zhTW from '@/messages/zh-TW.json';

describe('Translation Completeness', () => {
  it('should have same keys in all languages', () => {
    const enKeys = getAllKeys(en);
    const zhKeys = getAllKeys(zhTW);

    expect(enKeys).toEqual(zhKeys);
  });

  it('should not have empty translations', () => {
    const allTranslations = {...en, ...zhTW};

    Object.entries(allTranslations).forEach(([key, value]) => {
      expect(value).not.toBe('');
    });
  });
});
```

---

## 開發規範

### 1. 翻譯 Key 設計原則

**✅ Good:**
```typescript
t('projects.createNew')           // 清晰、具體
t('common.save')                  // 通用按鈕
t('projects.validation.nameRequired')  // 驗證訊息
```

**❌ Bad:**
```typescript
t('btn1')                         // 不清楚
t('projects.new')                 // 模糊
t('error')                        // 太通用
```

### 2. 組件使用規範

**Server Component:**
```tsx
import {useTranslations} from 'next-intl';

export default function Page() {
  const t = useTranslations('namespace');
  return <h1>{t('key')}</h1>;
}
```

**Client Component:**
```tsx
'use client';

import {useTranslations} from 'next-intl';

export default function ClientComponent() {
  const t = useTranslations('namespace');
  return <Button>{t('save')}</Button>;
}
```

### 3. 日期格式化

```tsx
import {useFormatter} from 'next-intl';

function DateDisplay({date}: {date: Date}) {
  const format = useFormatter();

  return (
    <div>
      <p>{format.dateTime(date, {dateStyle: 'long'})}</p>
      {/* zh-TW: "2025年11月3日" */}
      {/* en: "November 3, 2025" */}
    </div>
  );
}
```

### 4. 數字和貨幣格式化

```tsx
import {useFormatter} from 'next-intl';

function PriceDisplay({amount}: {amount: number}) {
  const format = useFormatter();

  return (
    <div>
      <p>{format.number(amount, {style: 'currency', currency: 'TWD'})}</p>
      {/* zh-TW: "NT$1,000" */}
      {/* en: "TWD 1,000" */}
    </div>
  );
}
```

---

## 測試策略

### 1. 自動化測試

**翻譯文件完整性:**
```bash
# 檢查所有語言的翻譯 key 是否一致
pnpm test:i18n:completeness
```

**E2E 語言切換測試:**
```typescript
// apps/web/e2e/i18n/locale-switching.spec.ts
test('should switch language from zh-TW to en', async ({page}) => {
  await page.goto('/dashboard');

  // 驗證默認語言是繁體中文
  await expect(page.locator('h1')).toContainText('儀表板');

  // 切換到英文
  await page.click('[data-testid="locale-switcher"]');
  await page.click('[data-testid="locale-en"]');

  // 驗證語言已切換
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

### 2. 手動測試檢查清單

- [ ] 所有頁面在兩種語言下顯示正常
- [ ] 語言切換器在所有頁面可見且功能正常
- [ ] 表單驗證錯誤訊息正確翻譯
- [ ] Toast 通知訊息正確翻譯
- [ ] 日期、數字、貨幣格式化正確
- [ ] 長文本不會破壞佈局
- [ ] 導航菜單在兩種語言下對齊正確

---

## 部署考量

### 1. 環境變量

```bash
# .env
NEXT_PUBLIC_DEFAULT_LOCALE=zh-TW
NEXT_PUBLIC_SUPPORTED_LOCALES=zh-TW,en
```

### 2. SEO 優化

**app/[locale]/layout.tsx**
```tsx
export async function generateMetadata({params: {locale}}) {
  const t = await getTranslations({locale, namespace: 'metadata'});

  return {
    title: t('title'),
    description: t('description'),
    alternates: {
      canonical: `/${locale}`,
      languages: {
        'zh-TW': '/zh-TW',
        'en': '/en',
      }
    }
  };
}
```

### 3. CDN 緩存策略

- 翻譯文件可以長期緩存（1年）
- 使用 Content-Based Hashing 自動失效
- next.config.mjs 已配置自動優化

---

## 時間估算

| 階段 | 任務 | 估算時間 | 依賴 |
|------|------|----------|------|
| Phase 1 | 基礎設施搭建 | 1-2 天 | - |
| Phase 2 | 翻譯文件建立 | 2-3 天 | Phase 1 |
| Phase 3 | 組件遷移 | 3-5 天 | Phase 2 |
| Phase 4 | 後端整合 | 1-2 天 | Phase 3 |
| Phase 5 | UI 增強 | 1 天 | Phase 4 |
| Phase 6 | 測試與優化 | 2-3 天 | Phase 5 |
| **總計** | | **10-16 天** | |

---

## 風險與挑戰

### 技術風險

| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| 翻譯不完整導致顯示錯誤 | 高 | 建立自動化測試檢查翻譯完整性 |
| 長文本破壞 UI 佈局 | 中 | 設計時預留 30% 文本擴展空間 |
| 語言切換性能問題 | 低 | next-intl 已優化，Server Components 僅在服務端加載翻譯 |
| 現有代碼遷移工作量大 | 高 | 分階段遷移，優先核心頁面 |

### 組織風險

| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| 翻譯質量參差不齊 | 中 | 建立翻譯審核流程 |
| 開發團隊學習曲線 | 低 | 提供詳細文檔和示例 |
| 未來擴展其他語言困難 | 低 | 設計時考慮擴展性 |

---

## 未來擴展

### 支援更多語言

**添加簡體中文 (zh-CN):**
1. 創建 `messages/zh-CN.json`
2. 更新 `i18n/routing.ts` 添加 `'zh-CN'` 到 `locales`
3. 無需修改組件代碼

**添加日文 (ja):**
1. 創建 `messages/ja.json`
2. 更新 `i18n/routing.ts` 添加 `'ja'` 到 `locales`
3. 測試日期/數字格式化

### 專業翻譯服務整合

可考慮整合以下服務提升翻譯質量:
- **Crowdin**: 專業翻譯管理平台
- **Lokalise**: 團隊協作翻譯工具
- **Google Translate API**: 機器翻譯輔助（需人工校對）

---

## 參考資源

- [next-intl 官方文檔](https://next-intl-docs.vercel.app/)
- [Next.js 國際化指南](https://nextjs.org/docs/app/building-your-application/routing/internationalization)
- [CLDR 語言數據](http://cldr.unicode.org/)
- [Unicode Common Locale Data Repository](https://github.com/unicode-org/cldr)

---

**文檔維護者**: AI Assistant
**最後更新**: 2025-11-03
**狀態**: ✅ 規劃完成，等待開始實施
