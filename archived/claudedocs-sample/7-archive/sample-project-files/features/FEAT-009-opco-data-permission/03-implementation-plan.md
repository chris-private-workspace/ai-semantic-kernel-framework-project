# FEAT-009: Operating Company 數據權限管理 - 實施計劃

> **建立日期**: 2025-12-12
> **版本**: 1.0
> **狀態**: 📋 待開發

## 1. 開發階段

### Phase 1: 數據模型建立 (預估 1-2 小時)

| 任務 | 說明 | 依賴 |
|------|------|------|
| T-1.1 | 更新 Prisma Schema 新增 UserOperatingCompany model | - |
| T-1.2 | 更新 User model 新增關聯 | T-1.1 |
| T-1.3 | 更新 OperatingCompany model 新增關聯 | T-1.1 |
| T-1.4 | 執行 `pnpm db:generate` 生成 Prisma Client | T-1.3 |
| T-1.5 | 執行 `pnpm db:migrate` 建立 migration | T-1.4 |
| T-1.6 | 驗證本地數據庫結構正確 | T-1.5 |

### Phase 2: 後端 API 開發 (預估 2-3 小時)

| 任務 | 說明 | 依賴 |
|------|------|------|
| T-2.1 | 實現 `getUserPermissions` procedure | Phase 1 |
| T-2.2 | 實現 `setUserPermissions` procedure | Phase 1 |
| T-2.3 | 實現 `getForCurrentUser` procedure | Phase 1 |
| T-2.4 | 為 Admin 角色添加特殊處理（預設全權限） | T-2.3 |
| T-2.5 | 添加向後兼容邏輯（無權限用戶的處理） | T-2.3 |
| T-2.6 | API 單元測試 | T-2.5 |

### Phase 3: 前端權限管理 UI (預估 3-4 小時)

| 任務 | 說明 | 依賴 |
|------|------|------|
| T-3.1 | 建立 `OpCoPermissionSelector` 組件 | Phase 2 |
| T-3.2 | 更新用戶編輯頁面，新增權限設定區塊 | T-3.1 |
| T-3.3 | 實現權限儲存邏輯 | T-3.2 |
| T-3.4 | 添加成功/失敗 Toast 提示 | T-3.3 |
| T-3.5 | 添加 i18n 翻譯鍵 (en + zh-TW) | T-3.4 |
| T-3.6 | 測試權限設定功能 | T-3.5 |

### Phase 4: OM Summary 權限整合 (預估 1-2 小時)

| 任務 | 說明 | 依賴 |
|------|------|------|
| T-4.1 | 修改 OM Summary 頁面使用 `getForCurrentUser` API | Phase 2 |
| T-4.2 | 確認 OpCo 選擇器只顯示授權的選項 | T-4.1 |
| T-4.3 | 添加無權限用戶的提示訊息 | T-4.2 |
| T-4.4 | 測試不同角色用戶的顯示效果 | T-4.3 |

### Phase 5: 測試與文檔 (預估 1-2 小時)

| 任務 | 說明 | 依賴 |
|------|------|------|
| T-5.1 | 完整功能測試 | Phase 4 |
| T-5.2 | 驗證其他頁面不受影響 | T-5.1 |
| T-5.3 | 更新 04-progress.md 記錄開發過程 | T-5.2 |
| T-5.4 | 更新 CLAUDE.md 相關文檔 | T-5.3 |
| T-5.5 | Git commit 和 push | T-5.4 |

## 2. 任務分解詳情

### Phase 1 詳細任務

```bash
# T-1.1 ~ T-1.3: 更新 Prisma Schema
Edit: packages/db/prisma/schema.prisma
- 新增 UserOperatingCompany model
- 更新 User model 新增 operatingCompanyPermissions 關聯
- 更新 OperatingCompany model 新增 userPermissions 關聯

# T-1.4: 生成 Prisma Client
Bash: pnpm db:generate

# T-1.5: 建立 Migration
Bash: pnpm db:migrate --name feat009_user_opco_permission

# T-1.6: 驗證數據庫
Bash: pnpm db:studio
```

### Phase 2 詳細任務

```typescript
// T-2.1 ~ T-2.5: 更新 operatingCompany.ts
// 位置: packages/api/src/routers/operatingCompany.ts

// 新增 procedures:
// - getUserPermissions
// - setUserPermissions
// - getForCurrentUser

// 處理邏輯:
// - Admin (roleId >= 3): 返回所有 OpCo
// - 其他用戶: 查詢 UserOperatingCompany 表
// - 向後兼容: 無權限記錄時返回所有（或空，根據策略）
```

### Phase 3 詳細任務

```tsx
// T-3.1: 新建組件
// 位置: apps/web/src/components/user/OpCoPermissionSelector.tsx

// T-3.2: 更新用戶編輯頁面
// 位置: apps/web/src/app/[locale]/users/[id]/edit/page.tsx
// - 新增 OpCo 權限設定 Card

// T-3.5: 更新翻譯
// 位置: apps/web/src/messages/en.json
// 位置: apps/web/src/messages/zh-TW.json
```

### Phase 4 詳細任務

```tsx
// T-4.1: 修改 OM Summary 頁面
// 位置: apps/web/src/app/[locale]/om-summary/page.tsx

// 修改前:
const { data: opCos } = api.operatingCompany.getAll.useQuery();

// 修改後:
const { data: opCos } = api.operatingCompany.getForCurrentUser.useQuery();
```

## 3. 時間估算

| 階段 | 預估時間 | 累計時間 |
|------|---------|---------|
| Phase 1: 數據模型 | 1-2 小時 | 1-2 小時 |
| Phase 2: 後端 API | 2-3 小時 | 3-5 小時 |
| Phase 3: 前端 UI | 3-4 小時 | 6-9 小時 |
| Phase 4: OM Summary 整合 | 1-2 小時 | 7-11 小時 |
| Phase 5: 測試與文檔 | 1-2 小時 | 8-13 小時 |
| **總計** | **8-13 小時** | **約 1.5-2 天** |

## 4. 依賴關係圖

```
Phase 1 (Schema)
     ↓
Phase 2 (API)
     ↓
   ┌─┴─┐
   ↓   ↓
Phase 3  Phase 4
(UI)     (OM Summary)
   └─┬─┘
     ↓
Phase 5 (Test & Docs)
```

## 5. 風險評估

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| Migration 執行失敗 | 低 | 高 | 先在本地測試，使用 transaction |
| 向後兼容問題 | 中 | 中 | 初期採用寬鬆策略，無權限=全權限 |
| UI 複雜度增加 | 低 | 低 | 使用現有組件模式 |
| 測試覆蓋不足 | 中 | 中 | 編寫詳細測試案例 |

## 6. 檢查清單

### 開發前
- [ ] 確認 Git 分支乾淨
- [ ] 確認本地開發環境正常
- [ ] 閱讀相關現有代碼

### 開發中
- [ ] 每個 Phase 完成後驗證
- [ ] 頻繁 commit 保存進度
- [ ] 記錄遇到的問題

### 開發後
- [ ] 完整功能測試
- [ ] TypeScript 無錯誤
- [ ] ESLint 無錯誤
- [ ] 翻譯完整
- [ ] 文檔更新
- [ ] Code review（如適用）

## 7. 回滾計劃

如果部署後發現問題：
1. **API 層**: 可以快速修改向後兼容邏輯
2. **Migration**: 編寫反向 migration（刪除 UserOperatingCompany 表）
3. **前端**: 可以先隱藏 UI，維持原有行為
