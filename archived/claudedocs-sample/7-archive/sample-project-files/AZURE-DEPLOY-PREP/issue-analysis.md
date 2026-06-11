# Azure 部署問題分析報告

**創建時間**: 2025-11-21 17:00 (UTC+8)
**部署版本**: v2-register (commit: 696efa6)
**環境**: Azure App Service (app-itpm-dev-001)

---

## 問題總覽

經過用戶實際測試，發現 Azure 部署的應用程式存在以下兩個關鍵問題：

### 問題 1: 註冊 API 返回 500 錯誤 ❌
- **URL**: `https://app-itpm-dev-001.azurewebsites.net/api/auth/register`
- **HTTP 狀態**: 500 Internal Server Error
- **客戶端錯誤**: SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON

### 問題 2: Azure AD B2C 登入失敗 ❌
- **登入後跳轉**: `https://app-itpm-dev-001.azurewebsites.net/login?callbackUrl=...`
- **頁面狀態**: 404 Not Found (This page could not be found)
- **預期行為**: 應該重定向到 `/zh-TW/login` 或 `/en/login`（包含 locale 前綴）

---

## 問題 1: 註冊 API 500 錯誤

### 錯誤詳情

**前端錯誤日誌**:
```javascript
POST https://app-itpm-dev-001.azurewebsites.net/api/auth/register 500 (Internal Server Error)

❌ 註冊異常: SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

**測試請求**:
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "password123"
}
```

**預期響應**:
```json
{
  "success": false,
  "error": "密碼長度至少 8 個字元"
}
```

**實際響應**: HTML 500 錯誤頁面（Next.js 預設錯誤頁面）

### 根本原因分析

#### 主要原因: bcrypt 原生模組在 Azure Linux 環境下無法正常運行

**bcrypt 依賴鏈**:
```
apps/web/src/app/api/auth/register/route.ts
  ↓ import bcrypt from 'bcrypt'
  ↓ bcrypt 需要編譯原生 C++ 模組
  ↓ 在 Alpine Linux (Docker) 環境下編譯
  ↓ Azure App Service Linux 執行環境
  ↓ ❌ 原生模組運行時失敗
```

**證據**:
1. **本地開發環境**: bcrypt 正常工作（Windows/macOS 原生編譯）
2. **Docker 構建**: 成功通過（Alpine Linux 成功編譯）
3. **Azure 運行時**: 500 錯誤（原生模組執行失敗）

**問題文件**:
- `apps/web/src/app/api/auth/register/route.ts:166` - `await bcrypt.hash(password, BCRYPT_SALT_ROUNDS)`
- `apps/web/src/auth.ts:160` - `await bcrypt.compare(password, user.password)`

#### 次要原因: 缺少詳細的錯誤日誌

**當前狀況**:
- 500 錯誤返回 HTML 頁面（Next.js 預設行為）
- 前端無法解析 HTML 作為 JSON
- 實際錯誤訊息未暴露到前端或日誌

**影響**:
- 難以排查根本原因
- 用戶看到的是 JSON 解析錯誤，而不是實際的 bcrypt 錯誤

### 解決方案

#### ✅ 方案 A: 使用 bcryptjs（純 JavaScript 實現）- **推薦**

**優點**:
- ✅ 無原生依賴，跨平台兼容
- ✅ API 與 bcrypt 完全相同
- ✅ 在所有環境下穩定運行
- ✅ 部署簡單，無需額外編譯配置

**缺點**:
- ⚠️ 比 bcrypt 慢約 30%（但對用戶註冊場景影響可忽略）

**實施步驟**:
1. 安裝依賴: `pnpm add bcryptjs @types/bcryptjs --filter=@itpm/web`
2. 替換 import:
   - `apps/web/src/app/api/auth/register/route.ts:41`
   - `apps/web/src/auth.ts:44`
   ```typescript
   // 修改前
   import bcrypt from 'bcrypt';

   // 修改後
   import bcrypt from 'bcryptjs';
   ```
3. 測試本地註冊功能
4. 重新構建 Docker 映像並部署

**估計工作量**: 15 分鐘

---

#### 🔧 方案 B: 在 Dockerfile 中確保 bcrypt 正確編譯

**優點**:
- ✅ 保持原生性能（比 bcryptjs 快 30%）
- ✅ 不改變現有代碼

**缺點**:
- ⚠️ Dockerfile 配置複雜
- ⚠️ 可能遇到其他原生模組兼容性問題
- ⚠️ 部署時間增加（需要編譯）

**實施步驟**:
1. 修改 `docker/Dockerfile`，在 builder stage 添加：
   ```dockerfile
   # Install build dependencies for bcrypt
   RUN apk add --no-cache python3 make g++ gcc

   # Rebuild bcrypt
   RUN cd /app/apps/web && pnpm rebuild bcrypt
   ```
2. 確保生產環境安裝運行時依賴：
   ```dockerfile
   # Install runtime dependencies
   RUN apk add --no-cache libgcc libstdc++
   ```
3. 測試 Docker 映像本地運行
4. 部署到 Azure

**估計工作量**: 1-2 小時（包含測試和調試）

---

#### 🔍 方案 C: 使用 @node-rs/bcrypt（Rust 實現）

**優點**:
- ✅ 性能比 bcrypt 更快（Rust 編譯）
- ✅ 更好的跨平台兼容性
- ✅ 預編譯二進制文件

**缺點**:
- ⚠️ 需要調整 API（與 bcrypt 略有不同）
- ⚠️ 較新的庫，社區支持較少

**實施步驟**:
1. 安裝依賴: `pnpm add @node-rs/bcrypt --filter=@itpm/web`
2. 修改所有使用 bcrypt 的文件
3. 調整 API 調用方式
4. 完整測試

**估計工作量**: 30-45 分鐘

---

### 推薦方案

**優先級 1**: 方案 A (bcryptjs) - **立即實施**
- 最簡單、最穩定的解決方案
- 對用戶體驗影響微乎其微（註冊操作每個用戶只執行一次）
- 快速恢復註冊功能

**優先級 2**: 方案 B (Dockerfile 優化) - **長期改進**
- 如果需要原生性能（未來高並發場景）
- 作為技術債處理

---

## 問題 2: Azure AD B2C 登入後 404 錯誤

### 錯誤詳情

**錯誤流程**:
```
1. 用戶點擊 "使用 Microsoft 登入" 按鈕
2. 跳轉到 Azure AD B2C 登入頁面
3. 用戶成功完成 Azure AD B2C 認證
4. Azure AD B2C 重定向回應用程式
5. ❌ 應用程式返回 404 錯誤
6. URL: https://app-itpm-dev-001.azurewebsites.net/login?callbackUrl=...
```

**預期 URL**:
```
https://app-itpm-dev-001.azurewebsites.net/zh-TW/login?callbackUrl=...
或
https://app-itpm-dev-001.azurewebsites.net/en/login?callbackUrl=...
```

**實際 URL** (缺少 locale 前綴):
```
https://app-itpm-dev-001.azurewebsites.net/login?callbackUrl=...
```

### 根本原因分析

#### 主要原因: NextAuth v5 重定向 URL 缺少 locale 前綴

**架構分析**:

**當前路由結構** (next-intl):
```
apps/web/src/app/
  ├── [locale]/              # locale 參數（zh-TW / en）
  │   ├── login/
  │   │   └── page.tsx       # ✅ 實際登入頁面路徑: /zh-TW/login
  │   ├── dashboard/
  │   └── ...
```

**NextAuth 配置**:
```typescript
// apps/web/src/auth.config.ts:73-76
pages: {
  signIn: '/login',      // ❌ 缺少 locale 前綴
  error: '/login',       // ❌ 缺少 locale 前綴
}
```

**問題流程**:
```
Azure AD B2C 回調
  ↓
NextAuth 處理回調
  ↓
NextAuth 重定向到 pages.signIn
  ↓
重定向到 /login (無 locale)
  ↓
❌ Next.js 找不到 /login 頁面（只存在 /[locale]/login）
  ↓
404 錯誤
```

#### 次要原因: middleware.ts 未處理 /login 路由

**middleware 配置**:
```typescript
// apps/web/src/middleware.ts:157-168
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/projects/:path*',
    // ... 其他受保護路由
    // ❌ 沒有 '/login'
  ],
};
```

**影響**:
- `/login` 路徑不會被 middleware 處理
- next-intl 無法自動添加 locale 前綴
- 直接訪問 `/login` 會 404

#### 三方原因: Azure AD B2C Redirect URI 配置可能不正確

**Azure AD B2C 應用程式配置**:
```
Redirect URI 應該是:
https://app-itpm-dev-001.azurewebsites.net/api/auth/callback/azure-ad-b2c

當前可能配置為:
https://app-itpm-dev-001.azurewebsites.net/login
或其他錯誤的 URI
```

### 解決方案

#### ✅ 方案 A: 修改 NextAuth pages 配置支援 locale - **推薦**

**實施步驟**:

1. **修改 auth.config.ts**:
   ```typescript
   // apps/web/src/auth.config.ts:73-76
   pages: {
     signIn: '/zh-TW/login',  // ✅ 添加預設 locale
     error: '/zh-TW/login',   // ✅ 添加預設 locale
   }
   ```

2. **或使用動態 locale 檢測**:
   ```typescript
   // apps/web/src/auth.config.ts
   import { headers } from 'next/headers';

   export const authConfig: NextAuthConfig = {
     pages: {
       signIn: async () => {
         // 從 headers 檢測當前 locale
         const headersList = headers();
         const locale = headersList.get('x-next-intl-locale') || 'zh-TW';
         return `/${locale}/login`;
       },
     },
   };
   ```

3. **更新 middleware.ts 包含 login 路由**:
   ```typescript
   // apps/web/src/middleware.ts:157-168
   export const config = {
     matcher: [
       '/',              // ✅ 添加根路徑
       '/login',         // ✅ 添加 /login
       '/dashboard/:path*',
       '/projects/:path*',
       // ... 其他路由
     ],
   };
   ```

**優點**:
- ✅ 修復 404 錯誤
- ✅ 保持 next-intl 路由結構一致性
- ✅ 支援多語言登入頁面

**缺點**:
- ⚠️ 需要重啟應用程式
- ⚠️ 可能需要清除用戶 session

**估計工作量**: 20 分鐘

---

#### 🔧 方案 B: 創建無 locale 的 login 路由作為重定向

**實施步驟**:

1. **創建 /login route handler**:
   ```typescript
   // apps/web/src/app/login/route.ts
   import { redirect } from 'next/navigation';
   import { headers } from 'next/headers';

   export async function GET(request: Request) {
     const { searchParams } = new URL(request.url);
     const callbackUrl = searchParams.get('callbackUrl');

     // 檢測用戶語言偏好
     const headersList = headers();
     const acceptLanguage = headersList.get('accept-language');
     const locale = acceptLanguage?.startsWith('en') ? 'en' : 'zh-TW';

     // 重定向到帶 locale 的登入頁面
     const loginUrl = `/${locale}/login${callbackUrl ? `?callbackUrl=${encodeURIComponent(callbackUrl)}` : ''}`;
     redirect(loginUrl);
   }
   ```

**優點**:
- ✅ 不修改 NextAuth 配置
- ✅ 自動語言檢測
- ✅ 向後兼容

**缺點**:
- ⚠️ 增加一次額外的重定向
- ⚠️ 需要維護額外的路由處理器

**估計工作量**: 15 分鐘

---

#### 🔍 方案 C: 驗證和修復 Azure AD B2C Redirect URI

**實施步驟**:

1. **檢查 Azure AD B2C 應用程式配置**:
   - 登入 Azure Portal
   - 找到 Azure AD B2C 應用程式
   - 檢查 "Authentication" → "Redirect URIs"

2. **確保正確的 Redirect URI**:
   ```
   ✅ 正確的 URI:
   https://app-itpm-dev-001.azurewebsites.net/api/auth/callback/azure-ad-b2c

   ❌ 錯誤的 URI:
   https://app-itpm-dev-001.azurewebsites.net/login
   https://app-itpm-dev-001.azurewebsites.net/zh-TW/login
   ```

3. **如果 URI 錯誤，更新配置**:
   - 刪除錯誤的 URI
   - 添加正確的 URI
   - 等待 5-10 分鐘生效

4. **測試登入流程**:
   - 清除瀏覽器 cookies
   - 重新嘗試 Azure AD B2C 登入

**優點**:
- ✅ 修復根本配置問題
- ✅ 符合 NextAuth.js OAuth 流程

**缺點**:
- ⚠️ 需要 Azure Portal 訪問權限
- ⚠️ 需要等待配置生效

**估計工作量**: 10 分鐘（如果有權限）

---

### 推薦方案

**組合方案**: A + C - **最佳解決方案**

1. **首先執行方案 C**（檢查 Azure AD B2C 配置）:
   - 確保 Redirect URI 正確
   - 這是根本的配置問題

2. **然後執行方案 A**（修改 NextAuth pages 配置）:
   - 添加 locale 前綴到 pages.signIn
   - 更新 middleware.ts matcher

3. **測試完整流程**:
   - Azure AD B2C 登入
   - 本地密碼登入
   - 語言切換

**總估計工作量**: 30-40 分鐘

---

## 優先級排序

### 立即修復（今天完成）

**1. 註冊 API 500 錯誤** - **優先級: P0 (Critical)**
- **方案**: 使用 bcryptjs 替換 bcrypt
- **影響**: 阻止所有用戶註冊
- **工作量**: 15 分鐘
- **風險**: 低

**2. Azure AD B2C 登入 404 錯誤** - **優先級: P0 (Critical)**
- **方案**: 驗證 Azure AD B2C Redirect URI + 修改 NextAuth pages 配置
- **影響**: 阻止企業用戶使用 SSO 登入
- **工作量**: 30 分鐘
- **風險**: 低

### 短期改進（本週完成）

**3. 添加詳細的錯誤日誌** - **優先級: P1 (High)**
- **目標**: 捕獲和記錄 API 錯誤到 Application Insights
- **影響**: 提高問題排查效率
- **工作量**: 1 小時

**4. 創建 API 健康檢查端點** - **優先級: P1 (High)**
- **目標**: 監控關鍵功能（註冊、登入、資料庫連接）
- **影響**: 提前發現部署問題
- **工作量**: 1 小時

### 長期優化（下個 Sprint）

**5. Dockerfile bcrypt 原生編譯優化** - **優先級: P2 (Medium)**
- **目標**: 如果需要原生性能
- **影響**: 性能提升 30%（低優先級）
- **工作量**: 2 小時

**6. 完善 Azure 部署 CI/CD Pipeline** - **優先級: P2 (Medium)**
- **目標**: 自動化測試、構建、部署流程
- **影響**: 減少人工錯誤
- **工作量**: 4 小時

---

## 測試計劃

### 修復後驗證

**註冊功能測試**:
```bash
# 1. 測試無效輸入（密碼太短）
curl -X POST https://app-itpm-dev-001.azurewebsites.net/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "short"
  }'

# 預期: 400 + {"success": false, "error": "密碼長度至少 8 個字元"}

# 2. 測試有效註冊
curl -X POST https://app-itpm-dev-001.azurewebsites.net/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "newuser@example.com",
    "password": "SecurePass123"
  }'

# 預期: 201 + {"success": true, "message": "註冊成功"}

# 3. 測試重複 Email
# 再次執行步驟 2
# 預期: 400 + {"success": false, "error": "此 Email 已被註冊"}
```

**Azure AD B2C 登入測試**:
1. 清除瀏覽器 cookies
2. 訪問 https://app-itpm-dev-001.azurewebsites.net/zh-TW/login
3. 點擊 "使用 Microsoft 登入" 按鈕
4. 完成 Azure AD B2C 認證
5. 驗證重定向到 dashboard（不是 404）

**本地密碼登入測試**:
1. 使用步驟 2 創建的用戶登入
2. 驗證成功重定向到 dashboard
3. 驗證 session 正確設置

---

## 相關文件

**本地文件**:
- `claudedocs/1-planning/features/AZURE-DEPLOY-PREP/deployment-log.md` - 部署記錄
- `apps/web/src/app/api/auth/register/route.ts` - 註冊 API
- `apps/web/src/auth.ts` - NextAuth 完整配置
- `apps/web/src/auth.config.ts` - NextAuth Edge 配置
- `apps/web/src/middleware.ts` - 認證 middleware
- `docker/Dockerfile` - Docker 構建配置

**Azure Portal**:
- App Service: https://portal.azure.com/#resource/.../app-itpm-dev-001
- Application Insights: https://portal.azure.com/#resource/.../appinsights
- Azure AD B2C: https://portal.azure.com/#view/Microsoft_AAD_B2CAdmin/...

**文檔參考**:
- NextAuth.js v5: https://authjs.dev/
- next-intl: https://next-intl-docs.vercel.app/
- bcryptjs: https://www.npmjs.com/package/bcryptjs

---

**最後更新**: 2025-11-21 17:00 (UTC+8)
**報告作者**: AI Assistant
**審核狀態**: 待審核
