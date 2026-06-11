# FIX-006: 批次處理器 documentFormat 欄位映射錯誤

> **狀態**: ✅ 已修復並驗證
> **發現日期**: 2025-12-29
> **修復日期**: 2025-12-29
> **影響範圍**: 階層式術語報告導出功能

---

## 問題描述

### 症狀
- 執行 E2E 測試（TEST-PLAN-002）後，導出的 Excel 報告僅有標題列，無任何數據
- 132 個已處理文件的 `documentFormatId` 全部為 NULL
- 階層式術語聚合查詢返回 0 筆結果

### 根本原因
`batch-processor.service.ts` 中的 `saveExtractionResult()` 方法存取了錯誤的欄位路徑：

```typescript
// ❌ 錯誤路徑（extractionResult 頂層）
documentType: extractionResult.documentType,
documentSubtype: extractionResult.documentSubtype,

// ✅ 正確路徑（extractionResult.documentFormat 子物件）
documentType: extractionResult.documentFormat?.documentType,
documentSubtype: extractionResult.documentFormat?.documentSubtype,
```

GPT Vision 服務將文件格式資訊儲存在 `extractionResult.documentFormat` 子物件中，但批次處理器錯誤地從 `extractionResult` 頂層讀取，導致所有值都是 `undefined`。

---

## 影響分析

| 影響項目 | 說明 |
|---------|------|
| **功能影響** | 階層式術語報告無法生成（Company → Format → Terms 層級結構斷裂） |
| **數據影響** | 132 個歷史文件缺少 `documentFormatId` 關聯 |
| **業務影響** | 無法按文件格式分組查看術語統計 |

---

## 修復方案

### 1. 代碼修復 (`batch-processor.service.ts`)

**修改位置**: 第 558-565 行

```typescript
// 修復前
const formatResult = await this.hierarchicalAggregation.processDocumentFormat(
  file.documentIssuerId,
  extractionResult.documentType,      // ❌ 錯誤
  extractionResult.documentSubtype,   // ❌ 錯誤
  extractionResult.formatConfidence,
  extractionResult.formatFeatures
);

// 修復後
const formatResult = await this.hierarchicalAggregation.processDocumentFormat(
  file.documentIssuerId,
  extractionResult.documentFormat?.documentType,      // ✅ 正確
  extractionResult.documentFormat?.documentSubtype,   // ✅ 正確
  extractionResult.documentFormat?.formatConfidence,
  extractionResult.documentFormat?.formatFeatures
);
```

### 2. 數據回填腳本 (`scripts/backfill-document-format-id.mjs`)

創建回填腳本修復 132 個歷史文件：

**核心功能**:
- 從 `extraction_result.documentFormat` 提取格式資訊
- 映射 GPT Vision 返回值到資料庫 Enum 值
- 查找或創建對應的 `DocumentFormat` 記錄
- 更新 `historical_files.document_format_id`

**Enum 映射**:
```javascript
const SUBTYPE_MAPPING = {
  'OCEAN': 'OCEAN_FREIGHT',
  'AIR': 'AIR_FREIGHT',
  'LAND': 'LAND_TRANSPORT',
  'WAREHOUSE': 'WAREHOUSING',
  'COURIER': 'GENERAL',
  'CUSTOMS': 'CUSTOMS_CLEARANCE',
  // ... 完整映射
};
```

---

## 執行結果

### 回填統計
```
🔧 FIX-006 Backfill Script
📦 Batch ID: d8beb4ba-3501-45f0-9a92-3cfdf2e9f1a5

📈 Backfill Results:
   ✅ Success: 120
   ⏭️ Skipped: 0
   ❌ Errors:  0

📊 Post-backfill Statistics:
   With documentFormatId:    132
   Without documentFormatId: 0
   Total files:              132

🎯 Export-ready files: 132
```

### 導出驗證
```
✅ Excel 報告已生成

統計摘要:
  - 公司數: 50
  - 格式數: 50
  - 唯一術語: 386
  - 總出現次數: 514
```

---

## 修復文件清單

| 文件 | 變更類型 | 說明 |
|------|---------|------|
| `src/services/batch-processor.service.ts` | 修改 | 修正 documentFormat 欄位路徑 |
| `scripts/backfill-document-format-id.mjs` | 新增 | 回填歷史數據腳本 |
| `claudedocs/4-changes/bug-fixes/FIX-006-*.md` | 新增 | 本文檔 |

---

## 預防措施

### 1. 單元測試建議
為 `saveExtractionResult()` 方法增加測試案例，驗證 `documentFormat` 子物件正確傳遞：

```typescript
it('should correctly map documentFormat fields', async () => {
  const mockResult = {
    documentFormat: {
      documentType: 'INVOICE',
      documentSubtype: 'OCEAN_FREIGHT',
      formatConfidence: 85,
      formatFeatures: { ... }
    }
  };
  // 驗證 processDocumentFormat 收到正確參數
});
```

### 2. 類型安全強化
考慮為 `extractionResult` 定義嚴格的 TypeScript 介面，在編譯期捕捉欄位路徑錯誤。

---

## 相關文件

- **觸發測試**: TEST-PLAN-002 (Epic 0 E2E 測試)
- **相關 Bug**: FIX-005 (GPT_VISION Missing Issuer Classification)
- **功能變更**: CHANGE-002 (Hierarchical Terms Report Export)

---

## 驗證命令

```bash
# 執行回填（如需再次運行）
node scripts/backfill-document-format-id.mjs <batchId>

# 導出階層式術語報告
node scripts/export-hierarchical-terms.ts <batchId>
```

---

*文檔建立: 2025-12-29*
*最後更新: 2025-12-29*
