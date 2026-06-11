# FIX-004: 術語聚合欄位名稱錯誤

> **狀態**: ✅ 已修復
> **日期**: 2025-12-27
> **優先級**: 高
> **影響範圍**: Epic 0 - 階層式術語報告匯出

---

## 問題描述

### 症狀
Excel 報告匯出後，所有數據均顯示為 **0**：
- Total Companies: 0
- Total Formats: 0
- Total Unique Terms: 0
- Total Occurrences: 0

### 根本原因
術語聚合服務中的欄位名稱與實際 Azure Document Intelligence 回傳的 JSON 結構不匹配。

**錯誤代碼** (兩個服務都有此問題):
```typescript
// 錯誤：使用 invoiceData?.items
const items =
  result.lineItems ??
  result.items ??
  result.invoiceData?.items ??      // ❌ 錯誤欄位名稱
  result.extractedData?.lineItems ??
  [];
```

**正確代碼**:
```typescript
// 正確：使用 invoiceData?.lineItems
const items =
  result.lineItems ??
  result.items ??
  result.invoiceData?.lineItems ??  // ✅ 正確欄位名稱
  result.extractedData?.lineItems ??
  [];
```

### 實際數據結構
Azure Document Intelligence 回傳的 JSON 結構：
```json
{
  "invoiceData": {
    "lineItems": [
      { "description": "CLEARANCE FEE", ... },
      { "description": "LSS", ... }
    ]
  }
}
```

---

## 修復內容

### FIX-004: batch-term-aggregation.service.ts

**文件路徑**: `src/services/batch-term-aggregation.service.ts`
**修改行數**: 約第 70 行

```diff
 const items =
   result.lineItems ??
   result.items ??
-  result.invoiceData?.items ??
+  result.invoiceData?.lineItems ??
   result.extractedData?.lineItems ??
   [];
```

### FIX-004b: hierarchical-term-aggregation.service.ts

**文件路徑**: `src/services/hierarchical-term-aggregation.service.ts`
**修改行數**: 約第 85 行

```diff
 const items =
   result.lineItems ??
   result.items ??
-  result.invoiceData?.items ??
+  result.invoiceData?.lineItems ??
   result.extractedData?.lineItems ??
   [];
```

---

## 驗證結果

### 測試批次
- **Batch ID**: `6198eff9-8d55-4235-905e-49f58ebbd8ac`
- **Batch Name**: `TEST-PLAN-002 E2E 完整測試 2025-12-27`
- **File Count**: 5 個已完成的文件

### 修復前 (ALL ZEROS)
| 指標 | 值 |
|------|-----|
| Total Companies | 0 |
| Total Formats | 0 |
| Total Unique Terms | 0 |
| Total Occurrences | 0 |

### 修復後 (正確數據)
| 指標 | 值 |
|------|-----|
| Total Companies | 5 ✅ |
| Total Formats | 5 ✅ |
| Total Unique Terms | 27 ✅ |
| Total Occurrences | 27 ✅ |

### 提取的術語示例
- CLEARANCE FEE
- LSS
- VGM
- CFS
- DOC FEE
- HANDLING CHARGE
- TERMINAL CHARGE
- ... (共 27 個獨特術語)

---

## 受影響的功能

| 功能 | 服務 | 狀態 |
|------|------|------|
| Term Stats API | batch-term-aggregation.service.ts | ✅ 已修復 |
| Excel Export API | hierarchical-term-aggregation.service.ts | ✅ 已修復 |
| Hierarchical Terms Report | hierarchical-terms-excel.ts | ✅ 現可正常運作 |

---

## 測試腳本

以下腳本用於驗證修復：

1. `scripts/test-fix-004b.ts` - 驗證術語提取邏輯
2. `scripts/test-hierarchical-aggregation.ts` - 驗證階層聚合結構
3. `scripts/setup-formats-and-test.ts` - 設置 DocumentFormat 並驗證
4. `scripts/test-excel-export.ts` - 模擬 Excel 報告內容

---

## 教訓與建議

### 根本原因分析
1. Azure Document Intelligence 的 JSON 結構使用 `lineItems` 作為欄位名稱
2. 開發時可能參考了舊版 API 或其他文檔，誤用了 `items`
3. 缺乏針對實際數據結構的單元測試

### 預防措施
1. **增加類型定義**：為 `ExtractionResultJson` 介面添加嚴格的 TypeScript 類型
2. **添加單元測試**：針對真實 JSON 結構的術語提取測試
3. **代碼審查**：確保所有使用 extractionResult 的地方都使用一致的欄位名稱

---

**修復者**: Claude Code
**審核者**: Development Team
**完成日期**: 2025-12-27
