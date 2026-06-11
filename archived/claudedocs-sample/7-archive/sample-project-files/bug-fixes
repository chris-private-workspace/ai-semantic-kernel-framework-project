# FIX-009 當前狀態報告

**問題編號**: FIX-009
**標題**: NextAuth v4 → v5 升級與 E2E 測試認證修復
**日期**: 2025-10-29 18:35
**當前狀態**: ⚠️ 85% 完成 - MissingCSRF 錯誤待解決
**優先級**: 🔴 HIGH（阻塞所有 E2E 測試）

---

## 📊 整體進度概覽

### ✅ 已完成的工作（85%）

| 任務 | 狀態 | 完成時間 | 備註 |
|-----|------|---------|------|
| 1. 研究 NextAuth v5 升級指南 | ✅ | 2025-10-29 14:00 | 完整閱讀官方文檔 |
| 2. 升級套件到 v5 (beta.30) | ✅ | 2025-10-29 14:30 | 3 個 workspaces |
| 3. 創建 auth.ts 配置文件 | ✅ | 2025-10-29 15:00 | 258 行完整配置 |
| 4. 更新 API route handler | ✅ | 2025-10-29 15:15 | 修正導入路徑 |
| 5. 更新環境變數 | ✅ | 2025-10-29 15:30 | NEXTAUTH_* → AUTH_* |
| 6. 修正模組導入路徑 | ✅ | 2025-10-29 17:00 | `../../../` → `../../../../` |
| 7. 解決 NextRequest constructor 錯誤 | ✅ | 2025-10-29 17:30 | 移除 AUTH_URL |
| 8. 清除緩存並重啟服務器 | ✅ | 2025-10-29 18:00 | 成功啟動 |
| 9. 提交代碼到 GitHub | ✅ | 2025-10-29 18:30 | Commit e225d47, f3dc254 |

### ⚠️ 待解決的問題（15%）

| 問題 | 狀態 | 優先級 | 預估時間 |
|-----|------|-------|---------|
| **MissingCSRF 錯誤** | ⚠️ 待解決 | 🔴 HIGH | 2-4 小時 |
| 驗證 authorize 函數被調用 | ⏳ 阻塞 | 🔴 HIGH | 依賴上一項 |
| 更新登入頁面（如需） | ⏳ 待評估 | 🟡 MEDIUM | 1-2 小時 |
| 更新 E2E 測試 fixtures | ⏳ 待評估 | 🔴 HIGH | 2-3 小時 |
| 運行完整 E2E 測試驗證 | ⏳ 待執行 | 🔴 HIGH | 30 分鐘 |

---

## 🔍 當前核心問題：MissingCSRF 錯誤

### 問題描述

**錯誤信息**：
```
[auth][error] MissingCSRF: CSRF token was missing during an action signin
```

**測試結果**：
```
✅ CSRF Token: fcb2293b88e0061a2a5995fc0e26663444742af53f651482c59a602e22da3d8f

📊 登入結果:
  - 狀態: ❌ 失敗
  - HTTP 狀態碼: 302
  - 重定向 URL: http://localhost:3006/login?error=MissingCSRF
```

### 問題影響

1. **CSRF 驗證在 authorize 之前失敗**
   - ❌ `authorize` 函數從未被調用
   - ❌ 沒有看到 "🔐 Authorize 函數執行" 日誌
   - ❌ 認證邏輯完全被跳過

2. **E2E 測試完全阻塞**
   - 無法測試登入流程
   - 無法測試需要認證的功能
   - 測試通過率維持在 28.6% (2/7)

### 技術細節

**成功的部分**：
```bash
# ✅ CSRF token 可以成功獲取
curl -s http://localhost:3006/api/auth/csrf
# 返回：{"csrfToken":"041de357476e2530bbc8582e17169b33b42e9bebcdf64cb3d7030b40e980c935"}

# ✅ NextAuth v5 配置被正確載入
# 服務器日誌：🚀 NextAuth v5 配置文件正在載入...

# ✅ Next.js 編譯成功
# ✓ Compiled /api/auth/[...nextauth] in 545ms
```

**失敗的部分**：
```typescript
// 測試腳本發送的請求
const body = new URLSearchParams({
  email: 'pm@example.com',
  password: 'password123',
  csrfToken: csrfToken,              // ✅ Token 正確獲取
  callbackUrl: `${BASE_URL}/dashboard`,
  json: 'true',
});

const response = await fetch(`${BASE_URL}/api/auth/signin/credentials`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: body.toString(),
  redirect: 'manual',
});

// ❌ NextAuth 認為 CSRF token 缺失
// 服務器日誌：[auth][error] MissingCSRF: CSRF token was missing during an action signin
```

### 可能的原因分析

#### 1. CSRF Token 傳遞方式問題
**假設**：NextAuth v5 可能需要 CSRF token 同時在 Cookie 和 Body 中

**證據**：
- 測試腳本只在 body 中發送 token
- 沒有設置任何 Cookie
- NextAuth v5 可能需要驗證 Cookie 中的 token

**測試方案**：
```typescript
// 需要測試：從 /api/auth/csrf 獲取 response 時保存 Cookie
const csrfResponse = await fetch(`${BASE_URL}/api/auth/csrf`);
const cookies = csrfResponse.headers.get('set-cookie');

// 然後在登入請求中攜帶這些 Cookie
const signInResponse = await fetch(`${BASE_URL}/api/auth/signin/credentials`, {
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': cookies,  // 添加 Cookie header
  },
  body: body.toString(),
});
```

#### 2. NextAuth v5 Beta 版本問題
**假設**：v5.0.0-beta.30 可能存在 CSRF 驗證的 bug

**證據**：
- 我們已經遇到了 NextRequest constructor 問題（Issue #9922）
- Beta 版本可能有其他未發現的問題

**測試方案**：
- 檢查是否有更新的 beta 版本
- 搜索 GitHub Issues 關於 "MissingCSRF" 錯誤
- 考慮降級到更早的 beta 版本

#### 3. 瀏覽器 vs 腳本的差異
**假設**：NextAuth v5 的 CSRF 驗證依賴瀏覽器的自動 Cookie 處理

**證據**：
- 測試腳本無法自動處理 Cookie
- 真實瀏覽器會自動儲存和發送 Cookie
- NextAuth 可能設計時假設在瀏覽器環境中運行

**測試方案**：
- 直接在瀏覽器中測試登入流程
- 使用 Playwright 進行 E2E 測試（真實瀏覽器環境）
- 觀察瀏覽器的 Cookie 和 Network 請求

#### 4. auth.ts 配置缺少某些設定
**假設**：可能需要特定的 CSRF 相關配置

**需要檢查**：
```typescript
export const authConfig: NextAuthConfig = {
  // 可能需要的配置？
  cookies?: {
    csrfToken?: {
      name?: string;
      options?: CookieOption;
    };
  };

  // 或者需要特定的 trust host 設置？
  trustHost?: boolean;
};
```

---

## 🛠️ 建議的下一步行動

### 立即優先（下次會話第一件事）

#### 步驟 1：使用瀏覽器直接測試（30 分鐘）
**目的**：驗證問題是否只存在於測試腳本中

**操作**：
```bash
# 1. 確保開發服務器正在運行
pnpm dev

# 2. 在瀏覽器中訪問
http://localhost:3006/login

# 3. 使用測試用戶登入
Email: pm@example.com
Password: password123

# 4. 觀察 Network 標籤
- 查看 /api/auth/csrf 請求返回的 Cookie
- 查看 /api/auth/signin/credentials POST 請求的 Cookie
- 檢查是否有 csrfToken Cookie 被發送

# 5. 查看服務器日誌
- 尋找 "🔐 Authorize 函數執行" 日誌
- 確認是否成功重定向到 dashboard
```

**預期結果**：
- ✅ 如果成功：問題在於測試腳本的 Cookie 處理
- ❌ 如果失敗：問題更深層，需要調整配置

#### 步驟 2：修復測試腳本的 Cookie 處理（1 小時）
**前提**：如果瀏覽器測試成功

**修改 `scripts/test-auth-manually.ts`**：
```typescript
import { CookieJar } from 'tough-cookie';
import fetch, { Headers } from 'node-fetch';

const cookieJar = new CookieJar();

async function getCsrfToken(): Promise<string> {
  const response = await fetch(`${BASE_URL}/api/auth/csrf`);

  // 保存 Cookie
  const setCookieHeader = response.headers.get('set-cookie');
  if (setCookieHeader) {
    await cookieJar.setCookie(setCookieHeader, BASE_URL);
  }

  const data = await response.json();
  return data.csrfToken;
}

async function signInWithCredentials(csrfToken: string, ...): Promise<SignInResponse> {
  // 獲取 Cookie 並添加到請求中
  const cookies = await cookieJar.getCookieString(BASE_URL);

  const response = await fetch(`${BASE_URL}/api/auth/signin/credentials`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Cookie': cookies,  // ✅ 添加 Cookie
    },
    body: body.toString(),
    redirect: 'manual',
  });

  return { status: response.status, url: response.headers.get('location') };
}
```

#### 步驟 3：研究 NextAuth v5 文檔和 GitHub Issues（1 小時）
**搜索關鍵字**：
- "NextAuth v5 MissingCSRF"
- "nextauth beta CSRF token"
- "next-auth v5 credentials provider CSRF"

**需要查找的信息**：
1. NextAuth v5 的 CSRF 驗證機制文檔
2. 是否有其他開發者遇到相同問題
3. 是否有已知的解決方案或 workaround
4. 是否需要升級到更新的 beta 版本

#### 步驟 4：檢查更新的 NextAuth v5 版本（30 分鐘）
```bash
# 查看所有可用的 beta 版本
pnpm view next-auth versions --tag beta

# 如果有更新版本，升級並測試
pnpm --filter @itpm/web add next-auth@beta
pnpm --filter @itpm/api add next-auth@beta
pnpm --filter @itpm/auth add next-auth@beta

# 重啟服務器並重新測試
pnpm dev
```

### 替代方案（如果上述方法都失敗）

#### 方案 A：調整 auth.ts 配置
```typescript
export const authConfig: NextAuthConfig = {
  // 嘗試禁用 CSRF 驗證（僅用於調試）
  skipCSRFCheck: true,  // ⚠️ 不安全，僅用於定位問題

  // 或者嘗試自定義 Cookie 設置
  cookies: {
    csrfToken: {
      name: 'next-auth.csrf-token',
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: false,  // 本地開發使用 HTTP
      },
    },
  },

  // 確保 trust host 設置正確
  trustHost: true,
};
```

#### 方案 B：直接使用 Playwright E2E 測試
跳過手動測試腳本，直接修改 E2E 測試：

```typescript
// apps/web/e2e/auth.setup.ts
import { test as setup } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  // 使用真實瀏覽器進行認證
  await page.goto('http://localhost:3006/login');
  await page.fill('input[name="email"]', 'pm@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  // 等待重定向到 dashboard
  await page.waitForURL('http://localhost:3006/dashboard');

  // 保存認證狀態
  await page.context().storageState({ path: 'playwright/.auth/user.json' });
});
```

---

## 📂 重要文件清單

### 核心配置文件
| 文件路徑 | 狀態 | 最後修改 | 備註 |
|---------|------|---------|------|
| `apps/web/src/auth.ts` | ✅ 已創建 | 2025-10-29 15:00 | 258 行完整配置 |
| `apps/web/src/app/api/auth/[...nextauth]/route.ts` | ✅ 已修正 | 2025-10-29 17:00 | 路徑修正 |
| `apps/web/.env` | ✅ 已修改 | 2025-10-29 17:30 | 移除 AUTH_URL |

### 測試相關文件
| 文件路徑 | 狀態 | 備註 |
|---------|------|------|
| `scripts/test-auth-manually.ts` | ⚠️ 需修改 | 需要添加 Cookie 處理 |
| `apps/web/e2e/auth.setup.ts` | ⏳ 待創建 | E2E 認證設置 |
| `apps/web/e2e/*.spec.ts` | ⏳ 待更新 | 所有 E2E 測試 |

### 文檔文件
| 文件路徑 | 狀態 | 備註 |
|---------|------|------|
| `claudedocs/FIX-009-ROOT-CAUSE-ANALYSIS.md` | ✅ 完成 | 根本原因分析 |
| `claudedocs/FIX-009-V5-UPGRADE-PROGRESS.md` | ✅ 完成 | 升級進度記錄 |
| `claudedocs/FIX-009-CURRENT-STATUS.md` | ✅ 本文件 | 當前狀態報告 |
| `DEVELOPMENT-LOG.md` | ✅ 已更新 | 開發記錄 |

---

## 🔗 相關資源

### 官方文檔
- [NextAuth v5 Migration Guide](https://authjs.dev/getting-started/migrating-to-v5)
- [NextAuth v5 Configuration](https://authjs.dev/reference/nextjs)
- [Credentials Provider](https://authjs.dev/reference/core/providers/credentials)

### GitHub Issues
- [#9922 - NextRequest is not a constructor](https://github.com/nextauthjs/next-auth/issues/9922)
- 需要搜索：MissingCSRF 相關問題

### 測試資源
- [Playwright Authentication](https://playwright.dev/docs/auth)
- [Node Fetch Cookie Handling](https://github.com/node-fetch/node-fetch#cookies)

---

## 💡 關鍵洞察和學習

### 已解決的技術難題

1. **模組路徑計算**
   - Next.js App Router 的文件結構需要準確計算相對路徑
   - `[...nextauth]` 作為 catch-all route 增加了一層目錄深度

2. **NextAuth v5 與 Next.js 14 的兼容性**
   - AUTH_URL 環境變數在本地開發中會觸發 constructor 錯誤
   - 移除 AUTH_URL 讓 NextAuth 使用默認的請求處理機制

3. **Monorepo 套件管理**
   - 需要為每個 workspace 分別升級套件
   - `pnpm --filter` 是管理 Turborepo 的關鍵命令

### 待驗證的假設

1. **CSRF Token 需要在 Cookie 中傳遞**
   - 測試腳本只在 body 中發送可能不夠
   - 需要驗證 NextAuth v5 的具體要求

2. **瀏覽器環境 vs 腳本環境**
   - NextAuth 可能假設在瀏覽器環境中運行
   - 腳本測試可能需要模擬瀏覽器的 Cookie 處理

3. **Beta 版本的穩定性**
   - v5.0.0-beta.30 可能還有未發現的問題
   - 需要關注社區的反饋和更新

---

## 📝 下次會話檢查清單

### 開始前確認
- [ ] 閱讀本報告的「建議的下一步行動」章節
- [ ] 檢查開發服務器是否正在運行（端口 3006）
- [ ] 確認最新的 Git 狀態（應該在 commit f3dc254）
- [ ] 檢查是否有新的 NextAuth v5 beta 版本發布

### 優先執行任務
1. [ ] 使用瀏覽器直接測試登入流程（步驟 1）
2. [ ] 修復測試腳本的 Cookie 處理（步驟 2）
3. [ ] 研究 NextAuth v5 文檔和 GitHub Issues（步驟 3）
4. [ ] 檢查更新的版本（步驟 4）

### 驗證標準
- [ ] `authorize` 函數被成功調用（看到日誌）
- [ ] 登入成功並重定向到 dashboard
- [ ] E2E 測試通過率達到 100% (7/7)

---

**報告生成時間**: 2025-10-29 18:35 (UTC+8)
**預計剩餘工作時間**: 3-5 小時
**當前阻塞**: MissingCSRF 錯誤
**下次會話優先級**: 🔴 HIGH - 立即解決 CSRF 問題

---

## 🚨 緊急聯絡信息

如果需要快速定位問題，請執行以下命令：

```bash
# 1. 檢查服務器狀態
netstat -ano | findstr :3006

# 2. 查看最新的服務器日誌
# （從背景任務中查看）

# 3. 快速測試 CSRF endpoint
curl -s http://localhost:3006/api/auth/csrf

# 4. 檢查 Git 狀態
git log --oneline -5

# 5. 驗證套件版本
pnpm --filter @itpm/web list next-auth
```

**重要提醒**：
1. ⚠️ 不要中止任何 node.js 進程（背景任務正在運行）
2. ⚠️ .env 文件不在版本控制中，本地修改不會推送
3. ⚠️ 確保 AUTH_URL 保持註解狀態（不要取消註解）
