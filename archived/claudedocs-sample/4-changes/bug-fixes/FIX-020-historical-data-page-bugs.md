# FIX-020: 歷史數據管理頁面問題

> **Bug ID**: FIX-020
> **發現日期**: 2025-12-24
> **修復日期**: 2025-12-24
> **狀態**: ✅ 已修復
> **發現方式**: 功能測試 - 歷史文件數據初始化（Epic 0 - Story 0.1, 0.2）

---

## Bug 1: 批次列表不顯示（數據結構不匹配）

### 問題描述
頁面顯示「尚無批次」，但 API 實際返回了批次數據。

### 根本原因
- **API 返回結構**: `{ success: true, data: [...批次數組...], meta: {...} }`
- **頁面代碼期望**: `batchesData?.data?.batches` (期望 `data.batches`)
- **實際結構**: `batchesData?.data` 直接是數組

### 影響範圍
- 批次列表無法顯示
- 「開始處理」按鈕無法出現
- 成本估算對話框無法觸發

### 修復方案
修改 `src/app/(dashboard)/admin/historical-data/page.tsx` 中的數據訪問路徑：

```typescript
// 修復前
const batches = batchesData?.data?.batches || []
const batch = batchesData?.data?.batches?.find((b: HistoricalBatch) => b.id === batchId)

// 修復後
const batches = batchesData?.data || []
const batch = batchesData?.data?.find((b: HistoricalBatch) => b.id === batchId)
```

### 修復位置
- Line 199: `handleStartProcessing` 函數中的 batch 查找
- Line 343: `batches` 變量賦值
- Line 376: `ProcessingConfirmDialog` 的 `batchName` prop

---

## Bug 2: onStartProcessing 回調未傳遞

### 問題描述
「開始處理」按鈕不顯示，因為 `HistoricalBatchList` 組件沒有收到 `onStartProcessing` 回調。

### 根本原因
`page.tsx` 中沒有實現 `handleStartProcessing` 函數，也沒有傳遞給 `HistoricalBatchList` 組件。

### 修復方案
在 `page.tsx` 中添加完整的處理邏輯：

1. **導入必要組件和類型**:
```typescript
import { ProcessingConfirmDialog } from '@/components/features/historical-data'
import { estimateBatchCost, type BatchCostEstimation, type FileForCostEstimation } from '@/services/cost-estimation.service'
import { type HistoricalBatch } from '@/hooks/use-historical-data'
```

2. **添加狀態變量**:
```typescript
const [processingDialogOpen, setProcessingDialogOpen] = useState(false)
const [processingBatchId, setProcessingBatchId] = useState<string | null>(null)
const [costEstimation, setCostEstimation] = useState<BatchCostEstimation | null>(null)
const [isStartingProcess, setIsStartingProcess] = useState(false)
```

3. **實現 handleStartProcessing**:
   - 獲取批次詳情
   - 計算成本估算
   - 打開確認對話框

4. **實現 handleConfirmProcessing**:
   - 調用處理 API
   - 顯示成功/失敗提示
   - 刷新批次列表

5. **傳遞回調給組件**:
```typescript
<HistoricalBatchList
  batches={batches}
  isLoading={isLoadingBatches}
  onSelectBatch={setSelectedBatchId}
  onDeleteBatch={handleDeleteBatch}
  onStartProcessing={handleStartProcessing}
/>
```

6. **渲染確認對話框**:
```typescript
<ProcessingConfirmDialog
  open={processingDialogOpen}
  onOpenChange={setProcessingDialogOpen}
  costEstimation={costEstimation}
  onConfirm={handleConfirmProcessing}
  isProcessing={isStartingProcess}
  batchName={...}
/>
```

---

## 驗證結果

修復後功能正常：

| 功能 | 狀態 |
|------|------|
| 批次列表顯示 | ✅ 正確顯示 5 個批次 |
| 「開始處理」按鈕 | ✅ 所有待處理批次都顯示按鈕 |
| 成本估算對話框 | ✅ 正確顯示 Azure DI 成本預估 |
| 取消按鈕 | ✅ 正常關閉對話框 |

---

## 優先級
**高** - 影響核心批量處理功能
