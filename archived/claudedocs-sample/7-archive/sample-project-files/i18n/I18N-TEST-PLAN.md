# i18n 多語言功能測試計劃

> **文檔版本**: 1.0
> **創建日期**: 2025-11-03
> **狀態**: 規劃階段
> **測試範圍**: 繁體中文 (zh-TW) ↔ 英文 (en) 雙向切換

---

## 📋 目錄

1. [測試總覽](#測試總覽)
2. [測試環境](#測試環境)
3. [測試策略](#測試策略)
4. [單元測試](#單元測試)
5. [集成測試](#集成測試)
6. [E2E測試](#e2e測試)
7. [性能測試](#性能測試)
8. [可訪問性測試](#可訪問性測試)
9. [測試數據](#測試數據)
10. [測試時間表](#測試時間表)

---

## 測試總覽

### 測試目標

- ✅ **功能正確性**: 所有UI文本正確翻譯，無遺漏
- ✅ **語言切換**: 切換語言無需刷新，狀態保持
- ✅ **數據完整性**: 翻譯文件結構完整，key一致
- ✅ **性能標準**: 首屏加載不受影響（<100ms增量）
- ✅ **UI穩定性**: 不同語言不破壞佈局
- ✅ **SEO優化**: hreflang標籤正確生成
- ✅ **可訪問性**: WCAG 2.1 AA級別合規

### 測試範圍

根據影響範圍分析報告，測試覆蓋：
- **80個文件** 需要翻譯處理
- **2735個中文字符串** 需要驗證翻譯
- **18個頁面** 需要完整E2E測試
- **63個組件** 需要單元/集成測試

---

## 測試環境

### 環境配置

| 環境 | 用途 | 語言設定 |
|------|------|----------|
| **本地開發** | 開發和快速驗證 | zh-TW, en |
| **CI/CD** | 自動化測試 | zh-TW, en |
| **Staging** | UAT測試 | zh-TW, en |
| **Production** | 生產監控 | zh-TW, en |

### 瀏覽器兼容性測試

| 瀏覽器 | 版本 | 優先級 |
|--------|------|--------|
| Chrome | 最新 | P0 |
| Firefox | 最新 | P1 |
| Safari | 最新 | P1 |
| Edge | 最新 | P1 |
| Mobile Safari | iOS 15+ | P0 |
| Mobile Chrome | Android 10+ | P0 |

---

## 測試策略

### 測試金字塔

```
        /\
       /  \      E2E 測試 (20%)
      /----\     - 關鍵用戶流程
     /      \    - 語言切換場景
    /--------\
   /          \  集成測試 (30%)
  /------------\ - 組件翻譯驗證
 /              \- API響應本地化
/----------------\
  單元測試 (50%)
  - 翻譯文件完整性
  - i18n工具函數
  - 格式化函數
```

### 測試階段

#### Phase 1: 準備階段 (1天)
- [ ] 建立測試基礎設施
- [ ] 創建測試數據集
- [ ] 配置測試環境

#### Phase 2: 開發中測試 (實施期間)
- [ ] 單元測試 (TDD方式)
- [ ] 組件快照測試
- [ ] 翻譯完整性自動檢查

#### Phase 3: 集成測試 (1天)
- [ ] 路由導航測試
- [ ] 語言切換集成測試
- [ ] API本地化測試

#### Phase 4: E2E測試 (2天)
- [ ] 關鍵業務流程測試
- [ ] 跨頁面語言一致性測試
- [ ] 錯誤處理場景測試

#### Phase 5: 性能與可訪問性測試 (1天)
- [ ] 首屏加載性能測試
- [ ] 語言切換性能測試
- [ ] WCAG 2.1 AA級別測試

---

## 單元測試

### 1. 翻譯文件完整性測試

**測試文件**: `tests/i18n/translation-completeness.test.ts`

```typescript
import en from '@/messages/en.json';
import zhTW from '@/messages/zh-TW.json';

describe('Translation Completeness', () => {
  // Test 1: 所有語言的 key 必須一致
  it('should have same keys in all languages', () => {
    const enKeys = getAllKeys(en);
    const zhKeys = getAllKeys(zhTW);

    expect(enKeys.sort()).toEqual(zhKeys.sort());
  });

  // Test 2: 沒有空翻譯
  it('should not have empty translations', () => {
    const checkEmpty = (obj: any, path: string = '') => {
      Object.entries(obj).forEach(([key, value]) => {
        const currentPath = path ? `${path}.${key}` : key;

        if (typeof value === 'object') {
          checkEmpty(value, currentPath);
        } else {
          expect(value, `Empty translation at ${currentPath}`).not.toBe('');
        }
      });
    };

    checkEmpty(en);
    checkEmpty(zhTW);
  });

  // Test 3: 所有佔位符格式正確
  it('should have valid placeholder syntax', () => {
    const validatePlaceholders = (obj: any) => {
      Object.values(obj).forEach(value => {
        if (typeof value === 'object') {
          validatePlaceholders(value);
        } else if (typeof value === 'string') {
          // {name}, {count} 等格式
          const placeholders = value.match(/\{[^}]+\}/g) || [];
          placeholders.forEach(placeholder => {
            expect(placeholder).toMatch(/^\{[a-zA-Z0-9_]+\}$/);
          });
        }
      });
    };

    validatePlaceholders(en);
    validatePlaceholders(zhTW);
  });

  // Test 4: 中英文佔位符一致
  it('should have matching placeholders between languages', () => {
    const getPlaceholders = (str: string) => {
      return (str.match(/\{[^}]+\}/g) || []).sort();
    };

    const comparePlaceholders = (enObj: any, zhObj: any, path: string = '') => {
      Object.keys(enObj).forEach(key => {
        const currentPath = path ? `${path}.${key}` : key;
        const enValue = enObj[key];
        const zhValue = zhObj[key];

        if (typeof enValue === 'object') {
          comparePlaceholders(enValue, zhValue, currentPath);
        } else if (typeof enValue === 'string') {
          const enPlaceholders = getPlaceholders(enValue);
          const zhPlaceholders = getPlaceholders(zhValue);

          expect(enPlaceholders, `Placeholder mismatch at ${currentPath}`).toEqual(zhPlaceholders);
        }
      });
    };

    comparePlaceholders(en, zhTW);
  });

  // Test 5: 翻譯長度合理（英文通常比中文長20-30%）
  it('should have reasonable translation length', () => {
    const checkLength = (enObj: any, zhObj: any, path: string = '') => {
      Object.keys(enObj).forEach(key => {
        const currentPath = path ? `${path}.${key}` : key;
        const enValue = enObj[key];
        const zhValue = zhObj[key];

        if (typeof enValue === 'object') {
          checkLength(enValue, zhValue, currentPath);
        } else if (typeof enValue === 'string' && typeof zhValue === 'string') {
          // 英文翻譯不應該過短或過長（允許+-50%）
          const ratio = enValue.length / zhValue.length;
          expect(ratio, `Translation length ratio suspicious at ${currentPath}`).toBeGreaterThan(0.5);
          expect(ratio, `Translation length ratio suspicious at ${currentPath}`).toBeLessThan(2.5);
        }
      });
    };

    checkLength(en, zhTW);
  });
});
```

### 2. i18n 工具函數測試

**測試文件**: `tests/i18n/utils.test.ts`

```typescript
import {formatDate, formatCurrency, formatNumber} from '@/lib/i18n';

describe('i18n Utility Functions', () => {
  describe('formatDate', () => {
    const testDate = new Date('2025-11-03T10:30:00');

    it('should format date in zh-TW locale', () => {
      const formatted = formatDate(testDate, 'zh-TW', {dateStyle: 'long'});
      expect(formatted).toBe('2025年11月3日');
    });

    it('should format date in en locale', () => {
      const formatted = formatDate(testDate, 'en', {dateStyle: 'long'});
      expect(formatted).toBe('November 3, 2025');
    });
  });

  describe('formatCurrency', () => {
    it('should format currency in zh-TW locale', () => {
      const formatted = formatCurrency(1000, 'zh-TW', 'TWD');
      expect(formatted).toBe('NT$1,000');
    });

    it('should format currency in en locale', () => {
      const formatted = formatCurrency(1000, 'en', 'TWD');
      expect(formatted).toBe('TWD 1,000');
    });
  });

  describe('formatNumber', () => {
    it('should format number in zh-TW locale', () => {
      const formatted = formatNumber(1234567.89, 'zh-TW');
      expect(formatted).toBe('1,234,567.89');
    });

    it('should format number in en locale', () => {
      const formatted = formatNumber(1234567.89, 'en');
      expect(formatted).toBe('1,234,567.89');
    });
  });
});
```

### 3. 組件快照測試

**測試文件**: `tests/components/LocaleSwitcher.test.tsx`

```typescript
import {render, screen, fireEvent} from '@testing-library/react';
import {LocaleSwitcher} from '@/components/i18n/LocaleSwitcher';
import {NextIntlClientProvider} from 'next-intl';

describe('LocaleSwitcher Component', () => {
  const mockRouter = {
    push: jest.fn(),
    replace: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render language options', () => {
    render(
      <NextIntlClientProvider locale="zh-TW" messages={{}}>
        <LocaleSwitcher />
      </NextIntlClientProvider>
    );

    expect(screen.getByText('繁體中文')).toBeInTheDocument();
    expect(screen.getByText('English')).toBeInTheDocument();
  });

  it('should change language when option selected', async () => {
    render(
      <NextIntlClientProvider locale="zh-TW" messages={{}}>
        <LocaleSwitcher />
      </NextIntlClientProvider>
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, {target: {value: 'en'}});

    expect(mockRouter.replace).toHaveBeenCalledWith(
      expect.anything(),
      {locale: 'en'}
    );
  });

  it('should match snapshot for zh-TW', () => {
    const {container} = render(
      <NextIntlClientProvider locale="zh-TW" messages={{}}>
        <LocaleSwitcher />
      </NextIntlClientProvider>
    );

    expect(container).toMatchSnapshot();
  });

  it('should match snapshot for en', () => {
    const {container} = render(
      <NextIntlClientProvider locale="en" messages={{}}>
        <LocaleSwitcher />
      </NextIntlClientProvider>
    );

    expect(container).toMatchSnapshot();
  });
});
```

---

## 集成測試

### 1. 路由導航測試

**測試文件**: `tests/integration/routing.test.tsx`

```typescript
describe('i18n Routing Integration', () => {
  it('should redirect to default locale when accessing root', async () => {
    const response = await fetch('http://localhost:3000/');
    expect(response.redirected).toBe(true);
    expect(response.url).toContain('/zh-TW');
  });

  it('should serve English content at /en route', async () => {
    const response = await fetch('http://localhost:3000/en/dashboard');
    const html = await response.text();
    expect(html).toContain('Dashboard'); // 英文標題
    expect(html).not.toContain('儀表板'); // 不含中文
  });

  it('should serve Chinese content at /zh-TW route', async () => {
    const response = await fetch('http://localhost:3000/zh-TW/dashboard');
    const html = await response.text();
    expect(html).toContain('儀表板'); // 中文標題
    expect(html).not.toContain('Dashboard'); // 不含英文
  });

  it('should return 404 for unsupported locale', async () => {
    const response = await fetch('http://localhost:3000/fr/dashboard');
    expect(response.status).toBe(404);
  });
});
```

### 2. API本地化測試

**測試文件**: `tests/integration/api-i18n.test.ts`

```typescript
describe('API Localization', () => {
  it('should return localized error messages based on Accept-Language', async () => {
    // 中文錯誤訊息
    const zhResponse = await fetch('http://localhost:3000/api/trpc/project.getById', {
      headers: {'Accept-Language': 'zh-TW'},
      body: JSON.stringify({id: 'invalid-id'}),
    });
    const zhError = await zhResponse.json();
    expect(zhError.message).toContain('找不到專案');

    // 英文錯誤訊息
    const enResponse = await fetch('http://localhost:3000/api/trpc/project.getById', {
      headers: {'Accept-Language': 'en'},
      body: JSON.stringify({id: 'invalid-id'}),
    });
    const enError = await enResponse.json();
    expect(enError.message).toContain('Project not found');
  });
});
```

---

## E2E測試

### 測試場景優先級

根據 `I18N-IMPACT-ANALYSIS.md` Top 20 複雜文件，我們設計以下E2E測試場景：

#### P0 - 核心業務流程 (必須100%通過)

**場景1: 完整專案管理流程**
```typescript
// apps/web/e2e/i18n/project-workflow.spec.ts
test('Project Management Workflow - zh-TW to en switch', async ({page}) => {
  // 1. 登入（中文）
  await page.goto('/zh-TW/login');
  await expect(page.locator('h1')).toContainText('登入系統');

  await page.fill('input[name="email"]', 'pm@itpm.local');
  await page.fill('input[name="password"]', 'pm123');
  await page.click('button[type="submit"]');

  // 2. 儀表板（中文）
  await expect(page).toHaveURL('/zh-TW/dashboard');
  await expect(page.locator('h1')).toContainText('儀表板');

  // 3. 切換到英文
  await page.click('[data-testid="locale-switcher"]');
  await page.click('[data-testid="locale-en"]');

  // 4. 驗證儀表板已切換到英文
  await expect(page).toHaveURL('/en/dashboard');
  await expect(page.locator('h1')).toContainText('Dashboard');

  // 5. 導航到專案列表（英文）
  await page.click('a[href="/en/projects"]');
  await expect(page.locator('h1')).toContainText('Projects');

  // 6. 創建新專案（英文）
  await page.click('button:has-text("Create Project")');
  await expect(page).toHaveURL('/en/projects/new');

  // 7. 填寫表單（驗證所有欄位標籤為英文）
  await expect(page.locator('label:has-text("Project Name")')).toBeVisible();
  await expect(page.locator('label:has-text("Description")')).toBeVisible();
  await expect(page.locator('label:has-text("Budget Pool")')).toBeVisible();

  // 8. 提交表單並驗證成功訊息為英文
  await page.fill('input[name="name"]', 'Test Project');
  await page.fill('textarea[name="description"]', 'Test Description');
  await page.selectOption('select[name="budgetPoolId"]', {index: 1});
  await page.click('button[type="submit"]');

  await expect(page.locator('[role="alert"]')).toContainText('Project created successfully');

  // 9. 切換回中文
  await page.click('[data-testid="locale-switcher"]');
  await page.click('[data-testid="locale-zh-TW"]');

  // 10. 驗證專案列表為中文
  await expect(page).toHaveURL('/zh-TW/projects');
  await expect(page.locator('h1')).toContainText('專案管理');
});
```

**場景2: 預算提案審批流程**
```typescript
// apps/web/e2e/i18n/proposal-workflow.spec.ts
test('Proposal Approval Workflow - Language Consistency', async ({page}) => {
  // 作為 PM 提交提案（中文）
  await loginAs(page, 'pm', 'zh-TW');
  await createProposal(page, {
    name: '測試提案',
    amount: 50000,
  });

  await expect(page.locator('[role="alert"]')).toContainText('提案已提交審核');

  // 作為 Supervisor 審核（英文）
  await loginAs(page, 'supervisor', 'en');
  await page.goto('/en/proposals');

  await expect(page.locator('h1')).toContainText('Budget Proposals');

  // 點擊第一個待審核提案
  await page.click('tr:has-text("Pending Approval") >> button:has-text("Review")');

  // 驗證審批按鈕為英文
  await expect(page.locator('button:has-text("Approve")')).toBeVisible();
  await expect(page.locator('button:has-text("Reject")')).toBeVisible();
  await expect(page.locator('button:has-text("Request More Info")')).toBeVisible();

  // 批准提案
  await page.click('button:has-text("Approve")');
  await page.fill('textarea[name="comment"]', 'Approved');
  await page.click('button:has-text("Confirm")');

  await expect(page.locator('[role="alert"]')).toContainText('Proposal approved successfully');
});
```

**場景3: 費用記錄與審批**
```typescript
// apps/web/e2e/i18n/expense-workflow.spec.ts
test('Expense Recording and Approval - Bilingual', async ({page}) => {
  // PM 記錄費用（中文）
  await loginAs(page, 'pm', 'zh-TW');
  await page.goto('/zh-TW/expenses/new');

  await expect(page.locator('h1')).toContainText('新增費用記錄');

  await page.fill('input[name="description"]', '辦公用品採購');
  await page.fill('input[name="amount"]', '15000');
  await page.selectOption('select[name="purchaseOrderId"]', {index: 1});
  await page.click('button[type="submit"]');

  await expect(page.locator('[role="alert"]')).toContainText('費用記錄已建立');

  // Supervisor 審核（英文）
  await loginAs(page, 'supervisor', 'en');
  await page.goto('/en/expenses');

  await expect(page.locator('tr:has-text("Pending Approval")')).toBeVisible();

  await page.click('tr:has-text("Pending Approval") >> a:has-text("View")');
  await page.click('button:has-text("Approve")');

  await expect(page.locator('[role="alert"]')).toContainText('Expense approved');
});
```

#### P1 - 輔助功能流程

**場景4: 供應商管理**
```typescript
// apps/web/e2e/i18n/vendor-management.spec.ts
test('Vendor Management - Create and Edit', async ({page}) => {
  await loginAs(page, 'admin', 'zh-TW');

  // 創建供應商（中文）
  await page.goto('/zh-TW/vendors/new');
  await expect(page.locator('label:has-text("供應商名稱")')).toBeVisible();

  await page.fill('input[name="name"]', '測試供應商');
  await page.fill('input[name="contactName"]', '張三');
  await page.fill('input[name="email"]', 'vendor@test.com');
  await page.click('button:has-text("儲存")');

  // 切換到英文並編輯
  await page.click('[data-testid="locale-switcher"]');
  await page.click('[data-testid="locale-en"]');

  await page.click('button:has-text("Edit")');
  await expect(page.locator('label:has-text("Vendor Name")')).toBeVisible();
});
```

**場景5: 報價單管理**
```typescript
// apps/web/e2e/i18n/quote-management.spec.ts
test('Quote Management - Upload and Compare', async ({page}) => {
  await loginAs(page, 'pm', 'en');

  // 上傳報價單（英文）
  await page.goto('/en/quotes/new');
  await expect(page.locator('h1')).toContainText('Upload Quote');

  await page.selectOption('select[name="vendorId"]', {index: 1});
  await page.selectOption('select[name="projectId"]', {index: 1});
  await page.fill('input[name="amount"]', '80000');

  // 上傳文件
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles('test-files/quote.pdf');

  await page.click('button:has-text("Upload")');

  await expect(page.locator('[role="alert"]')).toContainText('Quote uploaded successfully');
});
```

#### P2 - 設定與管理頁面

**場景6: 用戶設定**
```typescript
// apps/web/e2e/i18n/user-settings.spec.ts
test('User Settings - Language Preference Persistence', async ({page, context}) => {
  await loginAs(page, 'pm', 'zh-TW');

  // 進入設定頁面
  await page.goto('/zh-TW/settings');
  await expect(page.locator('h1')).toContainText('系統設定');

  // 切換語言偏好到英文
  await page.click('button:has-text("語言設定")');
  await page.selectOption('select[name="locale"]', 'en');
  await page.click('button:has-text("儲存變更")');

  await expect(page.locator('[role="alert"]')).toContainText('設定已更新');

  // 重新加載頁面，驗證語言偏好持久化
  await page.reload();
  await expect(page).toHaveURL('/en/settings');
  await expect(page.locator('h1')).toContainText('Settings');

  // 打開新標籤頁，驗證語言偏好生效
  const newPage = await context.newPage();
  await newPage.goto('http://localhost:3000/dashboard');
  await expect(newPage).toHaveURL('/en/dashboard');
  await expect(newPage.locator('h1')).toContainText('Dashboard');
});
```

### E2E測試執行策略

```bash
# 運行所有 i18n E2E 測試
pnpm test:e2e:i18n

# 運行特定場景
pnpm test:e2e:i18n --grep "Project Management Workflow"

# 生成測試報告
pnpm test:e2e:i18n --reporter=html

# Headless模式（CI/CD）
pnpm test:e2e:i18n --headed=false

# Debug模式
pnpm test:e2e:i18n --debug
```

---

## 性能測試

### 1. 首屏加載性能

**測試工具**: Lighthouse CI

**測試指標**:
| 指標 | 目標 | 容許增量 |
|------|------|----------|
| FCP (First Contentful Paint) | < 1.5s | +100ms |
| LCP (Largest Contentful Paint) | < 2.5s | +150ms |
| TBT (Total Blocking Time) | < 300ms | +50ms |
| CLS (Cumulative Layout Shift) | < 0.1 | +0.02 |
| Speed Index | < 3.0s | +200ms |

**測試腳本**:
```bash
# 測試中文首頁性能
lighthouse http://localhost:3000/zh-TW/dashboard \
  --only-categories=performance \
  --output=json \
  --output-path=./lighthouse-zh-TW.json

# 測試英文首頁性能
lighthouse http://localhost:3000/en/dashboard \
  --only-categories=performance \
  --output=json \
  --output-path=./lighthouse-en.json

# 對比分析
node scripts/compare-lighthouse-results.js
```

### 2. 語言切換性能

**測試場景**:
```typescript
// tests/performance/locale-switching.perf.ts
test('Measure locale switching performance', async ({page}) => {
  await page.goto('/zh-TW/dashboard');

  // 測量切換到英文的時間
  const startTime = Date.now();

  await page.click('[data-testid="locale-switcher"]');
  await page.click('[data-testid="locale-en"]');
  await page.waitForURL('/en/dashboard');

  const switchTime = Date.now() - startTime;

  // 語言切換應該在300ms內完成
  expect(switchTime).toBeLessThan(300);

  // 驗證內容已更新
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

### 3. Bundle Size 分析

**測試腳本**:
```bash
# 構建並分析 bundle size
ANALYZE=true pnpm build

# 檢查翻譯文件大小
du -h apps/web/src/messages/*.json

# 驗證按需加載
# zh-TW.json 只在訪問中文頁面時加載
# en.json 只在訪問英文頁面時加載
```

**目標**:
- 單個語言包 < 50KB (gzipped)
- 總 bundle size 增加 < 100KB

---

## 可訪問性測試

### WCAG 2.1 AA 級別測試

**測試工具**: axe-core + Playwright

```typescript
// tests/a11y/locale-switcher.a11y.ts
import {injectAxe, checkA11y} from 'axe-playwright';

test('LocaleSwitcher meets WCAG 2.1 AA', async ({page}) => {
  await page.goto('/zh-TW/dashboard');
  await injectAxe(page);

  // 檢查整個頁面的可訪問性
  await checkA11y(page);

  // 檢查語言切換器
  await checkA11y(page, '[data-testid="locale-switcher"]', {
    detailedReport: true,
    detailedReportOptions: {html: true},
  });
});
```

### 鍵盤導航測試

```typescript
test('Can switch language using keyboard only', async ({page}) => {
  await page.goto('/zh-TW/dashboard');

  // Tab 到語言切換器
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab');
  // ... 直到焦點在語言切換器上

  // Enter 打開下拉選單
  await page.keyboard.press('Enter');

  // 方向鍵選擇英文
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');

  // 驗證語言已切換
  await expect(page).toHaveURL('/en/dashboard');
});
```

---

## 測試數據

### 測試用戶

| 角色 | Email | 密碼 | 權限 |
|------|-------|------|------|
| Admin | admin@itpm.local | admin123 | 全部 |
| Supervisor | supervisor@itpm.local | super123 | 審核 |
| PM | pm@itpm.local | pm123 | 專案管理 |

### 測試專案

| 專案名稱 | 預算池 | 狀態 |
|----------|--------|------|
| Test Project 測試專案 | FY2025 IT Budget | InProgress |
| English Test Project | FY2025 IT Budget | Draft |

### 測試翻譯字符串

```json
{
  "testStrings": {
    "short": "儲存",
    "medium": "新增專案",
    "long": "專案管理系統 - IT部門預算流程管理平台",
    "withPlaceholder": "歡迎回來，{name}",
    "withNumber": "共有 {count} 個專案",
    "withDate": "創建於 {date}",
    "withCurrency": "總預算：{amount}"
  }
}
```

---

## 測試時間表

### Phase 1: 測試準備 (1天)

| 時間 | 任務 | 負責人 | 輸出 |
|------|------|--------|------|
| 09:00-10:00 | 建立測試環境 | DevOps | 測試環境配置文檔 |
| 10:00-12:00 | 創建測試數據 | QA | 測試數據腳本 |
| 13:00-15:00 | 配置 Playwright | QA | E2E測試框架 |
| 15:00-17:00 | 編寫測試工具函數 | Dev | 測試輔助函數庫 |

### Phase 2: 單元測試 (實施期間，持續進行)

- 每個功能開發完成後，立即編寫對應的單元測試
- TDD (Test-Driven Development) 方式
- 目標覆蓋率：>80%

### Phase 3: 集成測試 (1天)

| 時間 | 任務 | 覆蓋範圍 |
|------|------|----------|
| 09:00-11:00 | 路由導航測試 | 所有頁面路由 |
| 11:00-13:00 | 語言切換集成測試 | 18個頁面 |
| 14:00-16:00 | API本地化測試 | 10個tRPC路由 |
| 16:00-17:00 | 測試結果分析 | 生成報告 |

### Phase 4: E2E測試 (2天)

**Day 1**:
- 09:00-12:00: P0 核心流程測試（專案、提案、費用）
- 13:00-17:00: P1 輔助功能測試（供應商、報價單、採購單）

**Day 2**:
- 09:00-12:00: P2 管理頁面測試（用戶、設定、通知）
- 13:00-15:00: 跨瀏覽器測試
- 15:00-17:00: 錯誤場景測試

### Phase 5: 性能與可訪問性測試 (1天)

| 時間 | 任務 | 工具 |
|------|------|------|
| 09:00-11:00 | 首屏加載性能測試 | Lighthouse |
| 11:00-13:00 | 語言切換性能測試 | Custom Script |
| 14:00-15:00 | Bundle Size 分析 | webpack-bundle-analyzer |
| 15:00-17:00 | WCAG 2.1 AA 測試 | axe-core |

---

## 測試通過標準

### 必須通過 (Blocker)

- ✅ **翻譯完整性**: 100% 的翻譯 key 在所有語言中存在
- ✅ **P0 E2E測試**: 100% 通過
- ✅ **路由功能**: 所有語言路由正常工作
- ✅ **語言切換**: 無刷新切換成功率 100%
- ✅ **性能退化**: < 10% FCP增量

### 應該通過 (Major)

- ⚠️ **P1 E2E測試**: > 95% 通過
- ⚠️ **可訪問性**: 0 WCAG AA級別錯誤
- ⚠️ **跨瀏覽器**: Chrome/Safari/Firefox 100%兼容
- ⚠️ **單元測試覆蓋率**: > 80%

### 建議通過 (Minor)

- 📝 **P2 E2E測試**: > 90% 通過
- 📝 **Bundle Size**: < 100KB 增加
- 📝 **鍵盤導航**: 所有功能可用鍵盤操作

---

## 缺陷管理

### 缺陷優先級

| 級別 | 定義 | 響應時間 | 修復時間 |
|------|------|----------|----------|
| **P0 - Blocker** | 核心功能無法使用 | 立即 | 1天內 |
| **P1 - Critical** | 重要功能受影響 | 4小時 | 3天內 |
| **P2 - Major** | 輔助功能問題 | 1天 | 1週內 |
| **P3 - Minor** | UI/UX小問題 | 3天 | 下個版本 |

### 缺陷報告模板

```markdown
**缺陷標題**: [i18n] 專案列表頁面英文翻譯缺失

**優先級**: P1 - Critical

**重現步驟**:
1. 切換語言到英文
2. 導航到專案列表頁面
3. 點擊「新增專案」按鈕

**預期結果**: 按鈕文本顯示 "Create Project"

**實際結果**: 按鈕文本仍顯示 "新增專案"

**受影響文件**: apps/web/src/app/projects/page.tsx:172

**環境**:
- 瀏覽器: Chrome 120
- OS: Windows 11
- 語言: en

**截圖**: [附件]

**建議修復**: 將硬編碼文本替換為 `t('projects.createNew')`
```

---

## 測試報告

### 測試總結報告模板

```markdown
# i18n 測試總結報告

**測試週期**: 2025-11-10 ~ 2025-11-15
**測試負責人**: QA Team
**測試版本**: v1.0.0-i18n

## 執行總結

| 測試類型 | 計劃 | 執行 | 通過 | 失敗 | 通過率 |
|---------|------|------|------|------|--------|
| 單元測試 | 150 | 150 | 145 | 5 | 96.7% |
| 集成測試 | 50 | 50 | 48 | 2 | 96.0% |
| E2E測試 | 30 | 30 | 28 | 2 | 93.3% |
| 性能測試 | 10 | 10 | 10 | 0 | 100% |
| 可訪問性測試 | 20 | 20 | 19 | 1 | 95.0% |
| **總計** | **260** | **260** | **250** | **10** | **96.2%** |

## 缺陷總結

| 優先級 | 新增 | 已修復 | 遺留 |
|--------|------|--------|------|
| P0 | 2 | 2 | 0 |
| P1 | 5 | 4 | 1 |
| P2 | 3 | 2 | 1 |
| **總計** | **10** | **8** | **2** |

## 風險評估

### 已緩解風險
✅ 翻譯完整性問題 - 建立自動化檢查工具
✅ 性能退化風險 - 性能測試全部通過
✅ 跨瀏覽器兼容性 - 測試通過

### 遺留風險
⚠️ P1缺陷1個 - 部分錯誤訊息未翻譯（已排期修復）
⚠️ P2缺陷1個 - 設定頁面英文排版問題（UI調整中）

## 結論與建議

**測試結論**: ✅ 建議發布
- 核心功能100%通過
- 性能指標符合要求
- 遺留缺陷不影響主要功能

**改進建議**:
1. 增加更多邊界場景測試
2. 建立翻譯質量Review流程
3. 添加自動化翻譯更新檢測
```

---

## 附錄

### A. 測試工具安裝

```bash
# Playwright E2E
pnpm add -D @playwright/test

# axe-core 可訪問性測試
pnpm add -D axe-playwright

# Lighthouse CI
pnpm add -D @lhci/cli

# Jest
pnpm add -D jest @types/jest ts-jest

# Testing Library
pnpm add -D @testing-library/react @testing-library/jest-dom
```

### B. 測試腳本配置

**package.json**:
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:i18n": "playwright test e2e/i18n",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:debug": "playwright test --debug",
    "test:a11y": "playwright test e2e/a11y",
    "test:perf": "lighthouse-ci autorun",
    "test:all": "pnpm test && pnpm test:e2e && pnpm test:a11y"
  }
}
```

### C. CI/CD 集成

**GitHub Actions**:
```yaml
name: i18n Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: pnpm install

      - name: Run unit tests
        run: pnpm test

      - name: Run E2E tests
        run: pnpm test:e2e:i18n

      - name: Run accessibility tests
        run: pnpm test:a11y

      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

---

**文檔維護者**: QA Team + AI Assistant
**最後更新**: 2025-11-03
**版本**: 1.0
**狀態**: ✅ 規劃完成，等待實施
