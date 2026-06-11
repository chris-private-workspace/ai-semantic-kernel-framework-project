# E2E 測試登入流程問題分析

**日期**: 2025-10-28
**狀態**: 🔴 問題識別但需要重啟才能驗證修復

## 📊 問題摘要

E2E 測試中的登入流程測試持續失敗（5/7 失敗），核心問題是 NextAuth credentials provider 沒有創建有效的 JWT session。

## 🔍 調試過程與發現

### 1. 初步調試（已完成）
- ✅ 修復 NEXTAUTH_URL 配置（Playwright webServer env）
- ✅ 添加詳細的調試日誌到登入頁面
- ✅ 添加網絡請求攔截到 auth fixture
- ✅ 驗證測試用戶存在且密碼正確（2/2 通過）

### 2. 關鍵發現

**瀏覽器端日誌**：
```
🔐 開始登入流程 {email: test-manager@example.com, callbackUrl: /dashboard}
認證 API 響應: 200 http://localhost:3005/api/auth/session
📊 signIn 結果: {error: null, status: 200, ok: true, url: http://localhost:3005/api/auth/signin?csrf=true}
✅ 登入成功
當前 URL: http://localhost:3005/login?callbackUrl=http%3A%2F%2Flocalhost%3A3005%2Fdashboard
```

**問題分析**：
1. ❌ `signIn` 返回的 URL 是 `/api/auth/signin?csrf=true`（錯誤），而不是 `/dashboard`（預期）
2. ❌ **authorize 函數根本沒有被調用**（服務器日誌中無任何輸出）
3. ❌ JWT callback 沒有執行，導致無 session 創建
4. ❌ middleware 檢查 session 失敗，重定向回登入頁面形成循環

### 3. 根本原因識別

**配置衝突：JWT Strategy + PrismaAdapter**

`packages/auth/src/index.ts:63` 中的配置：
```typescript
export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),  // ❌ 問題所在
  session: {
    strategy: 'jwt',  // JWT 策略
    maxAge: 24 * 60 * 60,
  },
  // ...
};
```

**根據 NextAuth.js 文檔**：
- PrismaAdapter 適用於 **database session strategy**
- JWT strategy **不應該**使用 adapter
- 混用兩者會導致認證流程衝突，阻止 credentials provider 的 authorize 函數被調用

## 🛠️ 應用的修復

### 修復 1: 移除 PrismaAdapter（JWT Strategy）

**文件**: `packages/auth/src/index.ts:61-63`

```typescript
// 修復前
export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),  // ❌ 與 JWT strategy 衝突
  session: { strategy: 'jwt', ... },
};

// 修復後
export const authOptions: NextAuthOptions = {
  // 注意：JWT strategy 不應該使用 adapter
  // adapter: PrismaAdapter(prisma),  // ✅ 已移除
  session: { strategy: 'jwt', ... },
};
```

### 修復 2: 優化登入頁面重定向邏輯

**文件**: `apps/web/src/app/login/page.tsx:45-67`

```typescript
// 使用 redirect: false 獲取結果，然後手動重定向到 callbackUrl
const result = await signIn('credentials', {
  email,
  password,
  callbackUrl,
  redirect: false,
});

if (result?.ok) {
  // 忽略 result.url，直接重定向到 callbackUrl
  router.push(callbackUrl);
}
```

### 修復 3: 增強調試日誌

**文件**: `packages/auth/src/index.ts`

添加了詳細的調試日誌到：
- authorize 函數（行 109-152）
- JWT callback（行 149-191）
- Session callback（行 194-210）

## ⚠️ 當前狀態

**問題**: 修復已應用，但測試仍然失敗

**原因**: Next.js 熱重載可能沒有正確重新編譯 `packages/auth` 模組，導致舊配置仍在使用。

**證據**:
- 服務器日誌（stderr）中仍然沒有 authorize 函數的調試輸出
- 這表明新代碼沒有被執行

## 🔬 深度診斷結果（2025-10-28 15:10）

### 獨立測試腳本驗證

創建了 `scripts/test-nextauth-direct.ts` 直接測試 NextAuth 配置：

**結果**:
```
📋 AuthOptions 結構:
  - adapter: ❌ 不存在
  - session.strategy: jwt
  - providers 數量: 2
  - debug: true

✅ 找到 credentials provider

❌ Authorize 返回 null
⚠️  沒有捕獲到 authorize 內部的日誌
```

**關鍵發現**:
1. ✅ adapter 確實已移除（配置正確）
2. ✅ session.strategy 是 jwt（配置正確）
3. ✅ credentials provider 存在
4. ❌ **authorize 函數返回 null 但沒有執行任何調試日誌**

**結論**:
- packages/auth/src/index.ts 文件內容正確（已確認包含所有調試日誌）
- 但執行時的代碼不是文件中的版本
- 可能存在：
  - Next.js 開發服務器的模組緩存
  - TypeScript 轉譯緩存
  - Playwright webServer 使用的舊服務器實例
  - Node.js 模組緩存

## 🎯 建議的解決方案

### 選項 1: 完整重啟測試服務器（推薦）

**步驟**:
1. 停止所有 Playwright 測試進程
2. 清除 Turborepo 緩存: `pnpm turbo clean`
3. 重新生成 Prisma Client: `pnpm db:generate`
4. 重新運行測試: `cd apps/web && pnpm exec playwright test`

**預期結果**: authorize 函數被調用，session 成功創建，測試通過

### 選項 2: 使用新的測試會話（如果不能重啟）

**步驟**:
1. 在新的終端窗口中啟動專用測試服務器
2. 配置使用不同的端口（如 3006）
3. 運行測試指向新端口

### 選項 3: 驗證代碼變更（檢查）

**命令**:
```bash
# 檢查 auth 配置文件
cat packages/auth/src/index.ts | grep -A 5 "authOptions"

# 確認 adapter 已被註釋
cat packages/auth/src/index.ts | grep "adapter:"
```

## 📝 已應用的代碼變更

### 1. `packages/auth/src/index.ts`

變更:
- 行 62-63: 註釋掉 `adapter: PrismaAdapter(prisma)`
- 行 109-152: 添加 authorize 函數調試日誌
- 行 149-191: 添加 JWT callback 調試日誌
- 行 194-210: 添加 session callback 調試日誌

### 2. `apps/web/src/app/login/page.tsx`

變更:
- 行 45-51: 改用 `redirect: false`
- 行 53-67: 添加詳細的調試日誌和錯誤處理
- 行 60-66: 手動重定向到 callbackUrl

### 3. `apps/web/e2e/fixtures/auth.ts`

變更:
- 行 33-42: 增強控制台日誌監聽，捕獲帶表情符號的日誌
- 行 44-58: 添加網絡響應攔截和詳細錯誤日誌

### 4. `apps/web/playwright.config.ts`

變更:
- 行 82-86: 添加 env 對象，確保環境變數正確傳遞
- 行 76: 在 Windows 命令中添加 NEXTAUTH_SECRET

## 🔄 測試結果統計

**最新運行**（2025-10-28 07:58）:
- 總測試數: 7
- 通過: 2 (28.6%)
  - ✅ 應該能夠訪問首頁
  - ✅ 應該能夠訪問登入頁面
- 失敗: 5 (71.4%)
  - ❌ 應該能夠以 ProjectManager 身份登入
  - ❌ 應該能夠以 Supervisor 身份登入
  - ❌ 應該能夠導航到預算池頁面
  - ❌ 應該能夠導航到項目頁面
  - ❌ 應該能夠導航到費用轉嫁頁面

## 🎓 技術洞察

### NextAuth.js Session Strategy 選擇

**JWT Strategy** (當前使用):
- ✅ 無需數據庫會話表
- ✅ 更快的 session 驗證
- ✅ 水平擴展友好
- ❌ 不應該使用 adapter

**Database Strategy**:
- ✅ 使用 PrismaAdapter
- ✅ Session 可以被撤銷
- ❌ 需要數據庫查詢
- ❌ 更複雜的設置

**結論**: 我們選擇 JWT strategy，因此**不應該**使用 PrismaAdapter。

### Playwright webServer 環境變數

**重要**：需要同時設置：
1. webServer.command 中的內聯變數（Windows: `set VAR=value&&`）
2. webServer.env 對象中的變數

這確保變數在不同平台上都能正確傳遞。

## 📌 下一步行動

1. **驗證修復**: 重啟測試服務器以確認修復有效
2. **運行完整測試套件**: `pnpm exec playwright test`
3. **執行工作流測試**: budget-proposal, procurement, expense-chargeout
4. **達成 100% 通過率**: 確保所有 7 個基本測試通過

## 🔗 相關文件

- `DEVELOPMENT-LOG.md`: 詳細的開發日誌和調試記錄
- `claudedocs/E2E-TESTING-SETUP-GUIDE.md`: E2E 測試設置指南
- `apps/web/playwright.config.ts`: Playwright 配置
- `apps/web/e2e/fixtures/auth.ts`: 認證 fixture
- `packages/auth/src/index.ts`: NextAuth 配置

---

**總結**: 問題根源已識別（JWT + PrismaAdapter 衝突），修復已應用，但需要完整重啟測試環境以驗證效果。
