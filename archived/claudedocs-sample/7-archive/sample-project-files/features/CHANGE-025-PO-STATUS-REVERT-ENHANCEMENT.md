# CHANGE-025: Purchase Order 狀態回退增強

## 變更摘要

| 項目 | 內容 |
|------|------|
| **變更編號** | CHANGE-025 |
| **變更類型** | 功能增強 (Enhancement) |
| **影響範圍** | Purchase Order 模組 |
| **優先級** | 中 |
| **預估工時** | 2-3 小時 |
| **相關模型** | PurchaseOrder |

## 背景說明

### 當前狀態流程
```
Draft → Submitted → Approved
         ↓
      (revertToDraft)
         ↓
       Draft
```

### 現有 `revertToDraft` API 限制
- 僅允許 `Submitted` 和 `Cancelled` 狀態退回 `Draft`
- **不支援** `Approved` 狀態的回退

### 業務需求
用戶希望已批准的採購單可以退回到上一個狀態（Approved → Submitted），以便進行修改後重新提交審批。

## 需求分析

### 用戶故事
> 作為主管（Supervisor），我希望可以將已批准的採購單退回到已提交狀態，這樣專案經理可以修改內容後重新提交審批。

### 狀態轉換規則
| 當前狀態 | 可退回到 | 操作 | 權限 |
|----------|----------|------|------|
| Draft | - | 無法退回 | - |
| Submitted | Draft | `revertToDraft` | PM/Supervisor |
| Approved | Submitted | **新增** `revertToSubmitted` | Supervisor |
| Cancelled | Draft | `revertToDraft` | PM/Supervisor |

## 技術設計

### 方案選擇

#### 方案 A: 新增 `revertToSubmitted` API (推薦)
- 新增專門的 API 處理 Approved → Submitted
- 清除 `approvedDate`
- 保持現有 `revertToDraft` 不變

#### 方案 B: 擴展現有 `revertToDraft`
- 修改 `revertToDraft` 支援多級回退
- 增加參數控制回退目標狀態

**建議採用方案 A**，原因：
1. 職責單一，易於維護
2. 權限控制更精確（Supervisor only）
3. 不影響現有功能

### API 設計

```typescript
// packages/api/src/routers/purchaseOrder.ts

/**
 * 將已批准的採購單退回已提交狀態
 * @param id - PO ID
 * @returns 成功訊息
 *
 * CHANGE-025: 新增狀態回退功能
 * - 僅 Approved 狀態可以退回 Submitted
 * - 清除 approvedDate
 * - 僅 Supervisor 可執行
 */
revertToSubmitted: supervisorProcedure
  .input(z.object({
    id: z.string().min(1, '無效的PO ID'),
    reason: z.string().optional(), // 可選：退回原因
  }))
  .mutation(async ({ ctx, input }) => {
    const po = await ctx.prisma.purchaseOrder.findUnique({
      where: { id: input.id },
    });

    if (!po) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: '找不到該採購單',
      });
    }

    // 僅 Approved 可以退回 Submitted
    if (po.status !== 'Approved') {
      throw new TRPCError({
        code: 'PRECONDITION_FAILED',
        message: `無法退回已提交狀態（當前狀態：${po.status}，僅限已批准）`,
      });
    }

    // 更新狀態為 Submitted，清除 approvedDate
    await ctx.prisma.purchaseOrder.update({
      where: { id: input.id },
      data: {
        status: 'Submitted',
        approvedDate: null,
      },
    });

    return { success: true };
  }),
```

### 前端修改

```typescript
// apps/web/src/app/[locale]/purchase-orders/page.tsx

// 修改 canRevert 函數
const canRevert = (status: string) => {
  return status === 'Submitted' || status === 'Cancelled';
};

// 新增 canRevertToSubmitted 函數
const canRevertToSubmitted = (status: string) => {
  return status === 'Approved';
};

// 在 DropdownMenu 中添加選項
{canRevertToSubmitted(po.status) && (
  <DropdownMenuItem onClick={() => handleRevertToSubmittedClick(po)}>
    <RotateCcw className="h-4 w-4 mr-2" />
    {t('actions.revertToSubmitted')}
  </DropdownMenuItem>
)}
```

### 翻譯鍵新增

```json
// apps/web/src/messages/zh-TW.json
{
  "purchaseOrders": {
    "actions": {
      "revertToSubmitted": "退回已提交"
    },
    "dialogs": {
      "revertToSubmitted": {
        "title": "退回已提交狀態",
        "description": "確定要將採購單 {poNumber} 退回已提交狀態嗎？批准日期將被清除，專案經理可以進行修改後重新提交。"
      }
    },
    "messages": {
      "revertToSubmittedSuccess": "採購單已退回已提交狀態"
    }
  }
}
```

## 模型關聯影響分析

### PurchaseOrder 關聯
| 關聯模型 | 關係 | 退回影響 |
|----------|------|----------|
| Project | Many-to-One | 無影響 |
| Vendor | Many-to-One | 無影響 |
| Quote | Many-to-One (Optional) | 無影響 |
| PurchaseOrderItem | One-to-Many | 無影響（明細保持不變）|
| Expense | One-to-Many | ⚠️ 需考慮：已有費用記錄的 PO 是否允許退回？|

### 特殊考量
1. **有費用記錄的 PO**: 建議禁止退回，因為費用已關聯到採購單
2. **通知機制**: 退回時應通知原提交者（Project Manager）

## 測試計畫

### 單元測試
- [ ] Approved → Submitted 成功
- [ ] 非 Approved 狀態嘗試退回應失敗
- [ ] approvedDate 被正確清除
- [ ] 非 Supervisor 嘗試操作應被拒絕

### 整合測試
- [ ] 前端 UI 正確顯示退回選項
- [ ] 退回後列表狀態正確更新
- [ ] 對話框確認流程正常

## 實施步驟

1. **API 層** (30 分鐘)
   - 新增 `revertToSubmitted` procedure
   - 添加權限檢查和狀態驗證

2. **前端 UI** (45 分鐘)
   - 新增 `canRevertToSubmitted` 函數
   - 添加下拉選單選項
   - 新增確認對話框

3. **翻譯** (15 分鐘)
   - 更新 zh-TW.json
   - 更新 en.json

4. **測試** (30 分鐘)
   - 手動測試各狀態轉換
   - 驗證權限控制

5. **部署** (30 分鐘)
   - 提交代碼
   - 部署到測試環境驗證

## 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| 已有費用的 PO 被退回 | 中 | 添加費用關聯檢查 |
| 權限繞過 | 低 | 使用 supervisorProcedure |
| 狀態不一致 | 低 | 使用資料庫事務 |

## 回滾計畫

如需回滾：
1. 移除 `revertToSubmitted` API
2. 移除前端相關 UI
3. 移除翻譯鍵

---

## 實施狀態

### ✅ 已完成（2025-12-15）

**修改文件清單**:

1. **`packages/api/src/routers/purchaseOrder.ts`**
   - 新增 `revertToSubmitted` API（行 631-675）
   - 使用 `supervisorProcedure` 確保僅 Supervisor 可執行
   - 僅允許 Approved → Submitted 轉換
   - 清除 `approvedDate`

2. **`apps/web/src/app/[locale]/purchase-orders/page.tsx`**
   - 新增 `revertToSubmittedDialogOpen` 和 `revertToSubmittedTarget` 狀態
   - 新增 `revertToSubmittedMutation` 調用 API
   - 新增 `canRevertToSubmitted` 輔助函數
   - 新增 `handleRevertToSubmittedClick` 處理器
   - 卡片視圖和列表視圖都添加了「退回已提交」選項
   - 新增確認對話框

3. **`apps/web/src/messages/zh-TW.json`**
   - 新增 `purchaseOrders.actions.revertToSubmitted`
   - 新增 `purchaseOrders.messages.revertToSubmittedSuccess`
   - 新增 `purchaseOrders.messages.revertToSubmittedError`
   - 新增 `purchaseOrders.dialogs.revertToSubmitted.title`
   - 新增 `purchaseOrders.dialogs.revertToSubmitted.description`

4. **`apps/web/src/messages/en.json`**
   - 新增對應的英文翻譯鍵

**驗證結果**:
- ✅ i18n 驗證通過（2516 個鍵，結構一致）
- ✅ TypeScript 類型檢查通過

---

**文檔建立日期**: 2025-12-15
**實施完成日期**: 2025-12-15
**負責人**: AI Assistant
