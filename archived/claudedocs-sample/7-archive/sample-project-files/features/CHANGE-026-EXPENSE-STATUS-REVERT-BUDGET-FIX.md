# CHANGE-026: Expense 狀態回退預算回沖修復

## 變更摘要

| 項目 | 內容 |
|------|------|
| **變更編號** | CHANGE-026 |
| **變更類型** | Bug 修復 + 功能增強 |
| **影響範圍** | Expense 模組、BudgetPool、BudgetCategory |
| **優先級** | 高 (涉及財務數據正確性) |
| **預估工時** | 3-4 小時 |
| **相關模型** | Expense, BudgetPool, BudgetCategory |

## 背景說明

### 當前狀態流程
```
Draft → Submitted → Approved → Paid
         ↓           ↓         ↓
      (reject)   (revertToDraft - 有 BUG)
         ↓           ↓         ↓
       Draft       Draft     Draft
```

### 🚨 嚴重問題：預算回沖缺失

現有 `revertToDraft` API（行 736-771）存在嚴重 bug：

```typescript
// 現有代碼 - 問題所在
revertToDraft: protectedProcedure
  .input(z.object({ id: z.string().min(1) }))
  .mutation(async ({ ctx, input }) => {
    // ... 省略驗證 ...

    // 更新狀態為 Draft，並清除相關日期
    await ctx.prisma.expense.update({
      where: { id: input.id },
      data: {
        status: 'Draft',
        approvedDate: null,
        paidDate: null,
      },
    });

    // ⚠️ BUG: 沒有回沖預算！
    // 當從 Approved/Paid 退回時，應該：
    // 1. BudgetPool.usedAmount 減去 expense.totalAmount
    // 2. BudgetCategory.usedAmount 減去 expense.totalAmount

    return { success: true };
  }),
```

### 影響分析

當 Expense 被批准（Approved）時，`approve` API 會：
1. 從 `BudgetPool.usedAmount` 扣除費用金額
2. 從 `BudgetCategory.usedAmount` 扣除費用金額

但是當使用 `revertToDraft` 退回時：
- ❌ **沒有** 將金額加回 `BudgetPool.usedAmount`
- ❌ **沒有** 將金額加回 `BudgetCategory.usedAmount`

**後果**：預算使用量數據不準確，可能導致：
- 預算池顯示比實際更多的已使用金額
- 預算類別統計錯誤
- 影響後續費用審批（可能誤報預算不足）

## 需求分析

### 用戶故事
> 作為財務管理員，當我將已批准的費用退回草稿時，系統應該自動將扣除的預算金額加回預算池和預算類別，確保財務數據準確。

### 狀態轉換與預算影響
| 當前狀態 | 退回到 | 預算操作 |
|----------|--------|----------|
| Submitted | Draft | 無（尚未扣款）|
| Approved | Draft | **加回** BudgetPool + BudgetCategory |
| Paid | Draft | **加回** BudgetPool + BudgetCategory |

### 額外增強需求
用戶還希望支援分步退回：
- Paid → Approved（而不是直接到 Draft）
- Approved → Submitted
- Submitted → Draft

## 技術設計

### 修復方案

#### 修復現有 `revertToDraft` API

```typescript
// packages/api/src/routers/expense.ts

/**
 * 退回草稿狀態
 * @param id - 費用 ID
 * @returns 成功訊息
 *
 * CHANGE-026: 修復預算回沖邏輯
 * - 從 Approved/Paid 退回時，將金額加回 BudgetPool 和 BudgetCategory
 * - 使用事務確保數據一致性
 */
revertToDraft: protectedProcedure
  .input(z.object({
    id: z.string().min(1, '無效的費用ID'),
  }))
  .mutation(async ({ ctx, input }) => {
    const expense = await ctx.prisma.expense.findUnique({
      where: { id: input.id },
      include: {
        purchaseOrder: {
          include: {
            project: {
              include: {
                budgetPool: true,
              },
            },
          },
        },
      },
    });

    if (!expense) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: '找不到該費用記錄',
      });
    }

    // 如果已經是 Draft，不需要操作
    if (expense.status === 'Draft') {
      throw new TRPCError({
        code: 'PRECONDITION_FAILED',
        message: '費用已經是草稿狀態',
      });
    }

    // CHANGE-026: 判斷是否需要回沖預算
    // 只有 Approved 或 Paid 狀態才需要回沖（因為這些狀態已經扣過款）
    const needsBudgetReversal = expense.status === 'Approved' || expense.status === 'Paid';

    // 使用事務確保數據一致性
    await ctx.prisma.$transaction(async (tx) => {
      // 1. 更新費用狀態
      await tx.expense.update({
        where: { id: input.id },
        data: {
          status: 'Draft',
          approvedDate: null,
          paidDate: null,
        },
      });

      // 2. CHANGE-026: 回沖預算（如果需要）
      if (needsBudgetReversal) {
        // 2.1 回沖 BudgetPool
        const budgetPool = expense.purchaseOrder.project.budgetPool;
        await tx.budgetPool.update({
          where: { id: budgetPool.id },
          data: {
            usedAmount: {
              decrement: expense.totalAmount,
            },
          },
        });

        // 2.2 回沖 BudgetCategory（如果有）
        if (expense.budgetCategoryId) {
          await tx.budgetCategory.update({
            where: { id: expense.budgetCategoryId },
            data: {
              usedAmount: {
                decrement: expense.totalAmount,
              },
            },
          });
        }
      }
    });

    return { success: true };
  }),
```

### 新增分步退回 API（可選增強）

```typescript
/**
 * 將已支付費用退回已批准狀態
 * CHANGE-026: 新增分步退回
 */
revertToPaid → revertToApproved: protectedProcedure
  .input(z.object({ id: z.string().min(1) }))
  .mutation(async ({ ctx, input }) => {
    const expense = await ctx.prisma.expense.findUnique({
      where: { id: input.id },
    });

    if (!expense || expense.status !== 'Paid') {
      throw new TRPCError({
        code: 'PRECONDITION_FAILED',
        message: '只有已支付狀態的費用才能退回已批准',
      });
    }

    await ctx.prisma.expense.update({
      where: { id: input.id },
      data: {
        status: 'Approved',
        paidDate: null,
      },
    });

    return { success: true };
  }),

/**
 * 將已批准費用退回已提交狀態
 * CHANGE-026: 新增分步退回
 * 注意：需要回沖預算！
 */
revertToSubmitted: supervisorProcedure
  .input(z.object({ id: z.string().min(1) }))
  .mutation(async ({ ctx, input }) => {
    const expense = await ctx.prisma.expense.findUnique({
      where: { id: input.id },
      include: {
        purchaseOrder: {
          include: {
            project: {
              include: {
                budgetPool: true,
              },
            },
          },
        },
      },
    });

    if (!expense || expense.status !== 'Approved') {
      throw new TRPCError({
        code: 'PRECONDITION_FAILED',
        message: '只有已批准狀態的費用才能退回已提交',
      });
    }

    // 使用事務回沖預算 + 更新狀態
    await ctx.prisma.$transaction(async (tx) => {
      // 回沖 BudgetPool
      await tx.budgetPool.update({
        where: { id: expense.purchaseOrder.project.budgetPool.id },
        data: {
          usedAmount: { decrement: expense.totalAmount },
        },
      });

      // 回沖 BudgetCategory（如果有）
      if (expense.budgetCategoryId) {
        await tx.budgetCategory.update({
          where: { id: expense.budgetCategoryId },
          data: {
            usedAmount: { decrement: expense.totalAmount },
          },
        });
      }

      // 更新狀態
      await tx.expense.update({
        where: { id: input.id },
        data: {
          status: 'Submitted',
          approvedDate: null,
        },
      });
    });

    return { success: true };
  }),
```

## 模型關聯影響分析

### Expense 關聯
| 關聯模型 | 關係 | 退回影響 |
|----------|------|----------|
| PurchaseOrder | Many-to-One | 通過此關聯找到 Project 和 BudgetPool |
| BudgetCategory | Many-to-One (Optional) | **需回沖 usedAmount** |
| ExpenseItem | One-to-Many | 無影響（明細保持不變）|
| ChargeOutItem | One-to-Many | ⚠️ 需考慮：有轉嫁記錄的費用是否允許退回？|

### BudgetPool 影響
- `usedAmount` 需要減去退回的費用金額
- 確保 `usedAmount` 不會變成負數

### BudgetCategory 影響
- 如果費用有 `budgetCategoryId`，需回沖對應類別的 `usedAmount`

## 前端修改

### 更新退回選項顯示

```typescript
// apps/web/src/app/[locale]/expenses/page.tsx

// 判斷可用的退回選項
const getRevertOptions = (status: string) => {
  switch (status) {
    case 'Paid':
      return ['toApproved', 'toDraft'];
    case 'Approved':
      return ['toSubmitted', 'toDraft'];
    case 'Submitted':
      return ['toDraft'];
    default:
      return [];
  }
};

// 在 DropdownMenu 中顯示多個退回選項
{expense.status === 'Paid' && (
  <>
    <DropdownMenuItem onClick={() => handleRevertToApproved(expense)}>
      <RotateCcw className="h-4 w-4 mr-2" />
      {t('actions.revertToApproved')}
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => handleRevertToDraft(expense)}>
      <RotateCcw className="h-4 w-4 mr-2" />
      {t('actions.revertToDraft')}
    </DropdownMenuItem>
  </>
)}
```

### 翻譯鍵新增

```json
// apps/web/src/messages/zh-TW.json
{
  "expenses": {
    "actions": {
      "revertToDraft": "退回草稿",
      "revertToSubmitted": "退回已提交",
      "revertToApproved": "退回已批准"
    },
    "dialogs": {
      "revert": {
        "title": "退回狀態",
        "toDraftDescription": "確定要將費用 {name} 退回草稿狀態嗎？如果費用已被批准，預算將會回沖。",
        "toSubmittedDescription": "確定要將費用 {name} 退回已提交狀態嗎？預算將會回沖，需要重新審批。",
        "toApprovedDescription": "確定要將費用 {name} 退回已批准狀態嗎？支付日期將被清除。",
        "budgetWarning": "注意：此操作將回沖 {amount} 到預算池"
      }
    },
    "messages": {
      "revertSuccess": "費用狀態已退回",
      "revertError": "退回失敗",
      "budgetReverted": "已回沖 {amount} 到預算池"
    }
  }
}
```

## 測試計畫

### 單元測試
- [ ] Submitted → Draft 成功（無預算變動）
- [ ] Approved → Draft 成功 + BudgetPool 回沖
- [ ] Approved → Draft 成功 + BudgetCategory 回沖
- [ ] Paid → Draft 成功 + 預算回沖
- [ ] Paid → Approved 成功（無預算變動）
- [ ] Approved → Submitted 成功 + 預算回沖
- [ ] 預算回沖金額正確

### 整合測試
- [ ] 前端 UI 正確顯示退回選項
- [ ] 退回後預算池數據正確更新
- [ ] 退回後預算類別數據正確更新
- [ ] 對話框顯示預算回沖警告

### 迴歸測試
- [ ] 現有審批流程不受影響
- [ ] 現有刪除功能不受影響

## 實施步驟

### 階段 1：修復 Bug（優先）
1. **修改 `revertToDraft` API** (45 分鐘)
   - 添加預算回沖邏輯
   - 使用事務確保一致性
   - 添加防護（防止 usedAmount 變負數）

2. **測試修復** (30 分鐘)
   - 驗證各狀態回退的預算變動
   - 確認數據一致性

### 階段 2：功能增強（可選）
3. **新增分步退回 API** (60 分鐘)
   - `revertToApproved` (Paid → Approved)
   - `revertToSubmitted` (Approved → Submitted)

4. **前端 UI 更新** (45 分鐘)
   - 更新退回選項顯示
   - 新增確認對話框
   - 顯示預算回沖警告

5. **翻譯更新** (15 分鐘)
   - 更新 zh-TW.json
   - 更新 en.json

6. **完整測試** (30 分鐘)
   - 端到端測試
   - 預算數據驗證

## 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| 預算回沖金額錯誤 | 高 | 使用事務 + 詳細日誌 |
| usedAmount 變負數 | 中 | 添加最小值檢查 |
| 有轉嫁記錄的費用被退回 | 中 | 添加 ChargeOutItem 關聯檢查 |
| 並發問題 | 低 | 使用資料庫事務鎖定 |

## 回滾計畫

如需回滾階段 2（分步退回）：
1. 移除新增的 API
2. 移除前端新 UI
3. 保留階段 1 的 bug 修復

**不建議回滾階段 1**，因為這是關鍵的 bug 修復。

---

## 實施狀態

### ✅ 階段 1：Bug 修復（已完成）
- **完成日期**: 2025-12-15
- **修改文件**: `packages/api/src/routers/expense.ts`
- **修改內容**:
  - 修改 `revertToDraft` API（行 740-828）
  - 添加預算回沖邏輯：從 Approved/Paid 退回時回沖 BudgetPool.usedAmount
  - 添加 BudgetCategory.usedAmount 回沖支援
  - 使用事務確保數據一致性
  - 添加 Math.max(0, ...) 防止負數

### ✅ 階段 2：分步退回（已完成）
- **完成日期**: 2025-12-15
- **修改文件**:
  1. `packages/api/src/routers/expense.ts`
     - 新增 `revertToApproved` API（行 833-877）
       - 使用 `protectedProcedure`
       - 僅 Paid → Approved
       - 清除 `paidDate`
       - 無預算變動（兩者都已扣款）
     - 新增 `revertToSubmitted` API（行 879-967）
       - 使用 `supervisorProcedure`（僅 Supervisor 可執行）
       - 僅 Approved → Submitted
       - 回沖 BudgetPool.usedAmount
       - 回沖 BudgetCategory.usedAmount
       - 清除 `approvedDate`
  2. `apps/web/src/app/[locale]/expenses/page.tsx`
     - 新增狀態變量：`revertToApprovedDialogOpen`, `revertToSubmittedDialogOpen`
     - 新增 mutations：`revertToApprovedMutation`, `revertToSubmittedMutation`
     - 新增輔助函數：`canRevertToApproved`, `canRevertToSubmitted`
     - 新增處理函數：`handleRevertToApprovedClick`, `handleRevertToSubmittedClick`
     - 卡片視圖和列表視圖添加分步退回選項
     - 新增確認對話框
  3. `apps/web/src/messages/zh-TW.json`
     - `expenses.actions.revertToApproved`: "退回已批准"
     - `expenses.actions.revertToSubmitted`: "退回已提交"
     - `expenses.messages.revertToApprovedSuccess/Error`
     - `expenses.messages.revertToSubmittedSuccess/Error`
     - `expenses.dialogs.revertToApproved.*`
     - `expenses.dialogs.revertToSubmitted.*`
  4. `apps/web/src/messages/en.json`
     - 對應英文翻譯

**驗證結果**:
- ✅ i18n 驗證通過（2526 個鍵，結構一致）

---

**文檔建立日期**: 2025-12-15
**階段 1 完成日期**: 2025-12-15
**階段 2 完成日期**: 2025-12-15
**負責人**: AI Assistant
