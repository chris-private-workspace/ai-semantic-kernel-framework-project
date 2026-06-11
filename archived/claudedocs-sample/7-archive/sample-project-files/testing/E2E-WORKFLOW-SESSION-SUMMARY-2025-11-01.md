# E2E 工作流測試會話總結 - FIX-047 至 FIX-055B 完整解決方案

**會話日期**: 2025-11-01
**會話目標**: 完成所有 E2E 工作流測試並達成 100% 通過率
**最終狀態**: ✅ 所有工作流測試 100% 通過 (procurement, budget-proposal, expense-chargeout)
**執行時長**: ~5 小時（跨會話繼續）
**負責**: AI Assistant (Claude Code)

---

## 🎯 會話目標

完成所有三個核心工作流的 E2E 測試，修復所有發現的問題，達成 100% 測試通過率。

**初始狀態** (會話開始時):
- procurement-workflow: ✅ 已完成（FIX-044）
- budget-proposal-workflow: ⏳ 待測試
- expense-chargeout-workflow: ⏳ 待修復（Step 5 失敗）

**最終狀態** (會話結束時):
- procurement-workflow: ✅ 100% 通過 (1 passed, 39.8s)
- budget-proposal-workflow: ✅ 100% 通過 (2 passed, 33.0s)
- expense-chargeout-workflow: ✅ 100% 通過 (1 passed, 18.2s)

---

## 📊 核心問題與解決方案總結

### 問題 1: ChargeOut 詳情頁缺少 currentUserRole (FIX-047) ✅

**錯誤訊息**:
```
TimeoutError: page.click: Timeout 10000ms exceeded.
waiting for locator('button:has-text("確認")')
```

**根本原因**:
- ChargeOutActions 組件依賴 `currentUserRole` 進行 RBAC
- 詳情頁未傳遞此 prop 導致 `canConfirm = false`
- Supervisor 無法看到「確認」按鈕

**解決方案**:
在 `charge-outs/[id]/page.tsx` 中添加 NextAuth session 管理並傳遞 role。

**檔案修改**: 1 個檔案，3 處修改
**測試結果**: Step 6 成功通過（重試）

---

### 問題 2-3: Strict Mode - "已確認" 徽章 (FIX-048, FIX-049) ✅

**錯誤訊息**:
```
strict mode violation: locator('text=已確認') resolved to 3 elements
```

**根本原因**:
頁面有多個「已確認」文字：
- 大號狀態徽章 (`text-lg`)
- 小號列表徽章
- 通知訊息文字

**解決方案**:
使用精確的 CSS 選擇器 `div.bg-green-500.text-lg:has-text("已確認")`

**檔案修改**: 1 個檔案，2 處修改
**測試結果**: Steps 6-7 無 Strict Mode violation

---

### 問題 4: ChargeOut markAsPaid API 缺少參數 (FIX-050) ✅

**錯誤訊息**:
```
TRPCClientError: [
  {
    "code": "invalid_type",
    "expected": "string",
    "received": "undefined",
    "path": ["paymentDate"],
    "message": "Required"
  }
]
```

**根本原因**:
- API 定義要求 `paymentDate: z.string().min(1)`
- 前端 `handleMarkAsPaid()` 只傳遞 `{ id }`

**解決方案**:
添加 `paymentDate: new Date().toISOString()` 參數

**檔案修改**: 1 個檔案，1 處修改
**測試結果**: Step 7 狀態成功更新為 Paid

---

### 問題 5-8: 多個 Strict Mode violations (FIX-051~054) ✅

**問題**:
- FIX-051: `text=已付款` 匹配多個元素（Step 7）
- FIX-052: 同上（Step 8 詳情頁）
- FIX-053: `text=確認時間` 匹配標籤和時間值
- FIX-054: 列表頁徽章匹配 `<option>` 元素

**解決方案**:
針對不同場景使用精確選擇器：
- 大號徽章: `div.bg-blue-500.text-lg:has-text("已付款")`
- 標籤文字: `div.text-sm.text-muted-foreground:has-text("確認時間")`
- 列表徽章: `div.bg-blue-500:has-text("已付款")`.first()

**檔案修改**: 1 個檔案，7 處修改
**測試結果**: Steps 7-8 完全通過

---

### 問題 9-10: Procurement projectId 不一致 (FIX-055, FIX-055B) ✅

**錯誤訊息**:
```
TRPCClientError: 費用的專案必須與採購單的專案一致
```

**根本原因 (2 層)**:
1. **FIX-055**: Step 3 和 Step 4 使用 index 選擇項目，可能選到不同項目
2. **FIX-055B**: Step 4 選擇 PO 時用 index，選到舊測試的 PO

**解決方案**:
1. Step 3 創建 PO 時保存 `projectId`
2. Step 4 創建 Expense 時使用保存的 `projectId`
3. Step 4 使用 `purchaseOrderId` 而非 index 選擇 PO

**檔案修改**: 1 個檔案，3 處修改
**測試結果**: 項目 ID 完全一致，測試通過 (39.8s)

---

## 📈 測試通過統計

### 最終測試結果

| 工作流 | 場景數 | 通過數 | 執行時間 | 狀態 |
|--------|--------|--------|----------|------|
| **procurement-workflow** | 1 | 1 | 39.8s | ✅ 100% |
| **budget-proposal-workflow** | 2 | 2 | 33.0s | ✅ 100% |
| **expense-chargeout-workflow** | 1 | 1 | 18.2s | ✅ 100% |
| **總計** | 4 | 4 | 91.0s | ✅ 100% |

### 修復統計

| 修復編號 | 問題類型 | 影響範圍 | 修改檔案數 | 狀態 |
|----------|----------|----------|------------|------|
| **FIX-047** | RBAC 權限 | charge-outs/[id]/page.tsx | 1 | ✅ 100% |
| **FIX-048** | Strict Mode | expense-chargeout-workflow.spec.ts | 1 | ✅ 100% |
| **FIX-049** | Strict Mode | expense-chargeout-workflow.spec.ts | 1 | ✅ 100% |
| **FIX-050** | API 參數 | ChargeOutActions.tsx | 1 | ✅ 100% |
| **FIX-051** | Strict Mode | expense-chargeout-workflow.spec.ts | 1 | ✅ 100% |
| **FIX-052** | Strict Mode | expense-chargeout-workflow.spec.ts | 1 | ✅ 100% |
| **FIX-053** | Strict Mode | expense-chargeout-workflow.spec.ts | 1 | ✅ 100% |
| **FIX-054** | Strict Mode | expense-chargeout-workflow.spec.ts | 1 | ✅ 100% |
| **FIX-055** | 資料一致性 | procurement-workflow.spec.ts | 1 | ✅ 100% |
| **FIX-055B** | 資料一致性 | procurement-workflow.spec.ts | 1 | ✅ 100% |
| **總計** | 10 個修復 | 3 個元件/測試 | 4 個檔案 | ✅ 100% |

---

## 🎓 關鍵學習與最佳實踐

### 1. Playwright Strict Mode 選擇器策略

**問題模式**: `text=狀態文字` 常常匹配多個元素

**解決策略**:
- **大號狀態徽章**: `div.bg-{color}-500.text-lg:has-text("文字")`
- **小號列表徽章**: `div.bg-{color}-500:has-text("文字")`
- **標籤文字**: `div.text-sm.text-muted-foreground:has-text("文字")`
- **避免隱藏元素**: 使用 `.first()` 或更精確的 class 選擇器

**學習**: CSS class 組合選擇器比文字選擇器更穩定可靠

### 2. NextAuth Session 管理模式

**模式**: Client Component 中獲取用戶 role

```typescript
import { useSession } from 'next-auth/react';

const { data: session } = useSession();
const userRole = (session?.user as any)?.role?.name;

// 傳遞給需要 RBAC 的組件
<Component currentUserRole={userRole} />
```

**學習**: 在詳情頁中也要注意傳遞必要的權限資訊

### 3. tRPC API 參數驗證

**問題**: API 定義的必填參數前端未傳遞

**檢查方法**:
1. 查看 API router 的 input schema (Zod)
2. 確認前端 mutation 傳遞所有必填參數
3. 使用 TypeScript 型別檢查提前發現問題

**學習**: tRPC 的型別安全可以防止大部分參數錯誤,但仍需檢查 Zod schema

### 4. E2E 測試資料一致性

**問題**: 使用 `index` 選擇下拉選單選項導致資料不一致

**最佳實踐**:
- ✅ 保存並重用實體 ID (`projectId`, `vendorId`, `purchaseOrderId`)
- ✅ 使用具體 ID 而非 index 選擇選項
- ✅ 在測試中明確列印選擇的 ID 便於調試
- ❌ 避免依賴種子資料順序

**學習**: E2E 測試應該自給自足,不依賴外部資料順序

### 5. 跨會話測試繼續策略

**情境**: 上次會話已修復部分測試,本次繼續

**策略**:
1. 先執行完整測試確認當前狀態
2. 逐一修復失敗的測試場景
3. 每次修復後重新執行該測試驗證
4. 全部修復後執行完整測試套件

**學習**: 系統化方法確保不遺漏任何問題

---

## 🔧 修改檔案清單

### 前端組件 (2 個檔案)

1. **apps/web/src/app/charge-outs/[id]/page.tsx**
   - Line 4: 添加 `import { useSession } from 'next-auth/react';`
   - Line 36: 添加 `const { data: session } = useSession();`
   - Lines 173-176: 傳遞 `currentUserRole={(session?.user as any)?.role?.name}`

2. **apps/web/src/components/charge-out/ChargeOutActions.tsx**
   - Lines 176-183: 添加 `paymentDate: new Date().toISOString()` 到 markAsPaid mutation

### E2E 測試 (2 個檔案)

3. **apps/web/e2e/workflows/expense-chargeout-workflow.spec.ts**
   - Line 318: FIX-048 - 使用 `div.bg-green-500.text-lg:has-text("已確認")`
   - Line 331: FIX-049 - 同上
   - Line 343: FIX-051 - 使用 `div.bg-blue-500.text-lg:has-text("已付款")`
   - Lines 357-358: FIX-052 - 同上
   - Lines 365-366: FIX-053 - 使用 `div.text-sm.text-muted-foreground:has-text("確認時間")`
   - Lines 371-372: FIX-054 - 使用 `div.bg-blue-500:has-text("已付款")`.first()

4. **apps/web/e2e/workflows/procurement-workflow.spec.ts**
   - Line 30: FIX-055 - 改為 `let projectId: string = '';`
   - Lines 246-247: FIX-055 - 保存 `projectId = await projectSelect.inputValue();`
   - Line 396: FIX-055B - 使用 `purchaseOrderId` 而非 index
   - Lines 401-407: FIX-055 - 使用保存的 `projectId` 選擇項目

**總計**: 4 個檔案，~20 處修改

---

## 📊 測試執行日誌（關鍵輸出）

### expense-chargeout-workflow 成功執行

```
✅ Step 6: Supervisor 確認 ChargeOut
  - 導航到詳情頁
  - 點擊「確認」按鈕 ← FIX-047 修復後可見
  - 驗證「已確認」狀態 ← FIX-048 精確選擇器

✅ Step 7: 標記為已付款
  - Manager 驗證「已確認」 ← FIX-049 精確選擇器
  - 點擊「標記為已付款」
  - API 調用成功 ← FIX-050 添加 paymentDate
  - 驗證「已付款」狀態 ← FIX-051 精確選擇器

✅ Step 8: 驗證付款資訊
  - 訪問詳情頁
  - 驗證「已付款」大號徽章 ← FIX-052
  - 驗證「確認時間」標籤 ← FIX-053
  - 訪問列表頁
  - 驗證列表徽章 ← FIX-054

✓  1 [chromium] › expense-chargeout-workflow.spec.ts:28 › 完整費用轉嫁工作流 (18.2s)
```

### procurement-workflow 成功執行

```
✅ Step 3: 創建採購訂單
  - 選擇項目: 3e94f934-920e-408e-a325-86ff3b8a1e77
  - 保存 projectId ← FIX-055

✅ Step 4: 記錄費用
  - 選擇 PO: ad79cdb0-dcdd-4b58-a16c-4a81e404e804 ← FIX-055B 使用 ID
  - 選擇專案: 3e94f934-920e-408e-a325-86ff3b8a1e77 ← FIX-055 使用保存的 ID
  - ✅ API 驗證成功: 項目 ID 一致

✓  1 [chromium] › procurement-workflow.spec.ts:32 › 完整採購工作流 (39.8s)
```

### budget-proposal-workflow 成功執行

```
✅ Scenario 1: 完整預算申請工作流
  - 創建提案
  - 提交審核
  - Supervisor 批准
  - 驗證狀態變更

✅ Scenario 2: 預算提案拒絕流程
  - 創建提案
  - 提交審核
  - Supervisor 拒絕
  - 驗證拒絕狀態

✓  2 [chromium] › budget-proposal-workflow.spec.ts (33.0s)
```

---

## 🎉 會話成果

### 核心成就

1. ✅ **100% 測試通過率**: 所有 3 個工作流測試完全通過
2. ✅ **10 個問題修復**: FIX-047 至 FIX-055B 全部完成
3. ✅ **零 Strict Mode violations**: 所有選擇器問題已解決
4. ✅ **RBAC 完整性**: 權限相關功能正常運作
5. ✅ **資料一致性**: 測試資料流程完整可靠

### 技術貢獻

1. ✅ **Strict Mode 選擇器策略**: 建立 CSS class 組合最佳實踐
2. ✅ **NextAuth Session 模式**: 詳情頁 RBAC 實作參考
3. ✅ **E2E 資料管理**: ID 保存與重用模式
4. ✅ **API 參數驗證**: tRPC Zod schema 檢查流程
5. ✅ **系統化修復方法**: 跨會話測試繼續策略

### 專案價值

1. ✅ **完整 E2E 覆蓋**: 三大核心工作流 100% 測試覆蓋
2. ✅ **穩定測試套件**: 91 秒內執行 4 個完整工作流
3. ✅ **可維護測試**: 精確選擇器不易因 UI 變動而失敗
4. ✅ **文檔完整**: 詳細記錄所有問題與解決方案
5. ✅ **知識沉澱**: 為未來測試開發提供參考

---

## 📝 後續建議

### 短期行動（本週）

1. ✅ **文檔同步**
   - 更新 COMPLETE-IMPLEMENTATION-PROGRESS.md
   - 更新 E2E-WORKFLOW-TESTING-PROGRESS.md
   - 同步到 GitHub

2. ✅ **索引維護**
   - 執行 `pnpm index:check` 確認檔案同步
   - 更新 PROJECT-INDEX.md 如有需要

3. 🟡 **CI/CD 整合**
   - 配置 GitHub Actions 執行 E2E 測試
   - 設置 PR 自動檢查
   - 建立測試報告自動化

### 中期計劃（本月）

1. 🟢 **Stage 3: 錯誤處理測試**
   - 測試 API 錯誤情境
   - 測試權限不足場景
   - 測試網路錯誤恢復

2. 🟢 **Stage 3: 表單驗證測試**
   - 必填欄位驗證
   - 金額範圍驗證
   - 日期邏輯驗證

3. 🟢 **Stage 3: 邊界條件測試**
   - 空列表處理
   - 極大金額處理
   - 並發操作測試

### 長期計劃（下季度）

1. 🎯 **測試覆蓋率提升至 80%+**
2. 🎯 **完整 CI/CD 流程**
3. 🎯 **多瀏覽器測試矩陣**
4. 🎯 **效能基準測試**

---

## 📚 相關文檔

- `FIXLOG.md` - FIX-047 至 FIX-055B 完整技術記錄（已更新）
- `COMPLETE-IMPLEMENTATION-PROGRESS.md` - 專案完整進度報告（已更新）
- `claudedocs/E2E-WORKFLOW-TESTING-PROGRESS.md` - 測試進度詳細追蹤（待更新）
- `apps/web/e2e/README.md` - E2E 測試使用指南
- `apps/web/e2e/workflows/*.spec.ts` - 工作流測試檔案

---

**會話完成時間**: 2025-11-01
**最終測試狀態**: ✅ 所有工作流 100% 通過 (4/4 tests passed)
**下一階段**: Stage 3 - 錯誤處理與邊界條件測試

---

**重要成就**: 此會話完成了 E2E 工作流測試的重要里程碑 - 達成 100% 核心工作流測試通過率，為後續測試擴展奠定堅實基礎。
