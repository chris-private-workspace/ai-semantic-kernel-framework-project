# FIX-018: Hierarchical Term Aggregation Fallback Mode

> **Bug ID**: FIX-018
> **狀態**: ✅ 已修復
> **修復日期**: 2026-01-05
> **影響範圍**: Term Export 功能
> **相關 Story**: Epic 0 - 歷史數據初始化

---

## 問題描述

### 症狀
- Historical Data 頁面的 "Export Hierarchical Terms" 功能產出空白 Excel
- API `/api/admin/historical-data/batches/{batchId}/hierarchical-terms` 回傳空陣列
- 而 `/api/admin/historical-data/batches/{batchId}/term-stats` 顯示有 223+ 術語存在

### 影響批次
- Batch ID: `0fdc7e9b-44ca-4eb9-9d33-8ed18f016a3c`
- 批次名稱: `TEST-PLAN-003-CHANGE-005-2026-01-05`
- 文件數量: 131 個 COMPLETED 文件

---

## 根本原因分析

### 查詢邏輯問題

`hierarchical-term-aggregation.service.ts` 原本的查詢要求文件**同時**具有：
- `documentIssuerId` (發行方 ID)
- `documentFormatId` (文件格式 ID)

```typescript
// 原始查詢 - 要求兩個 ID 都存在
const files = await prisma.historicalFile.findMany({
  where: {
    batchId,
    status: 'COMPLETED',
    documentIssuerId: { not: null },
    documentFormatId: { not: null },  // ← 問題：這個欄位為 NULL
  },
  // ...
});
```

### 數據現況

| 欄位 | 有值的文件數 | 百分比 |
|------|-------------|--------|
| documentIssuerId | 131 | 100% |
| documentFormatId | 0 | 0% |

**結論**: 所有 131 個文件都有 `documentIssuerId`，但**沒有任何文件**有 `documentFormatId`。

### 為什麼 documentFormatId 為 NULL？

1. **Story 0.9 (Document Format Identification)** 尚未完整實作
2. GPT Vision 的 `extractionResult` 中沒有 `documentFormat` 物件
3. 批次配置 `formatsIdentified: 0` 證實格式識別未執行

---

## 修復方案

### FIX-018: 實作 Fallback 模式

當沒有文件具有 `documentFormatId` 時，fallback 到只使用 `documentIssuerId` 進行聚合。

### 修改文件

**`src/services/hierarchical-term-aggregation.service.ts`**

```typescript
// FIX-018: 先嘗試標準查詢
let files = await prisma.historicalFile.findMany({
  where: {
    batchId,
    status: 'COMPLETED',
    documentIssuerId: { not: null },
    documentFormatId: { not: null },
  },
  include: { documentIssuer: true, documentFormat: true },
});

// FIX-018: 如果沒有文件有 documentFormatId，則 fallback
const useFallbackMode = files.length === 0;
if (useFallbackMode) {
  console.log(`[HierarchicalAggregation] Using fallback mode (no documentFormatId)`);
  files = await prisma.historicalFile.findMany({
    where: {
      batchId,
      status: 'COMPLETED',
      documentIssuerId: { not: null },
    },
    include: { documentIssuer: true, documentFormat: true },
  });
}

// FIX-018: 建立虛擬格式物件
const DEFAULT_FORMAT_PREFIX = 'default-format-';
const formatId = file.documentFormatId || `${DEFAULT_FORMAT_PREFIX}${issuerId}`;
const formatData = file.documentFormat || {
  id: formatId,
  documentType: 'INVOICE',
  documentSubtype: 'GENERAL',
  name: 'Default Format',
  fileCount: 0,
};
```

### 聚合結構變化

**標準模式** (有 documentFormatId):
```
Company → DocumentFormat → Terms
```

**Fallback 模式** (無 documentFormatId):
```
Company → Default Format (虛擬) → Terms
```

---

## 驗證結果

### 測試腳本
`scripts/debug-format-issue.mjs`

### 驗證輸出
```
Step 1: 標準查詢 (有兩個 ID): 0 個檔案
Step 2: Fallback 查詢 (只有 IssuerId): 131 個檔案
        使用 Fallback 模式: ✅ 是

📊 FIX-018 Fallback 聚合結果預覽:
  公司數: 56
  唯一術語數: 319
  術語出現總次數: 521

✅ FIX-018 驗證結果:
  🎉 成功！Fallback 模式能夠提取術語
```

---

## 技術債務

| 項目 | 說明 |
|------|------|
| 待實作 | Story 0.9 - Document Format Identification |
| 影響 | 目前所有文件使用虛擬 "Default Format" |
| 優先級 | 中 - 不影響術語提取功能，但缺少格式分類能力 |

---

## 相關文件

- `src/services/hierarchical-term-aggregation.service.ts` - 主要修復文件
- `scripts/debug-format-issue.mjs` - 驗證腳本
- `docs/04-implementation/stories/0-9-document-format-term-reorganization.md` - Story 規格

---

**修復者**: Claude AI Assistant
**審核日期**: 2026-01-05
