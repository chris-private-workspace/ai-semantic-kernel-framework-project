# FIX-015: Export Script Address Filtering

> **Bug ID**: FIX-015
> **建立日期**: 2025-12-31
> **完成日期**: 2025-12-31
> **狀態**: ✅ 已完成
> **關聯**: FIX-013, FIX-014

---

## 問題描述

`scripts/export-hierarchical-terms.ts` 匯出腳本直接讀取數據庫的原始數據，沒有應用 FIX-005 和 FIX-005.1 中實現的地址過濾邏輯（`isAddressLikeTerm` 函數）。

導致匯出的 Excel 報告（如 `TEST-PLAN-004-hierarchical-terms-2025-12-30.xlsx`）仍然包含大量地址相關術語，與服務層的聚合結果不一致。

---

## 根本原因

`export-hierarchical-terms.ts` 是一個獨立腳本，繞過了 API 和服務層直接使用 Prisma 讀取數據庫。術語提取邏輯沒有調用 `isAddressLikeTerm` 函數：

**問題代碼** (第 267-274 行):
```typescript
for (const item of extractionResult.invoiceData.lineItems) {
  const term = item.description || item.productCode || 'Unknown';
  if (term && term !== 'Unknown') {  // ❌ 缺少地址過濾
    const formatTerms = companyTerms.get(companyId)!.get(formatName)!;
    formatTerms.set(term, (formatTerms.get(term) || 0) + 1);
  }
}
```

---

## 解決方案

將 `term-aggregation.service.ts` 中的地址過濾邏輯複製到匯出腳本中，包括：

1. **ADDRESS_KEYWORDS** - 地址相關關鍵字
2. **LOCATION_NAMES** - 國家和城市名稱
3. **ADDRESS_PATTERNS** - 地址格式正則表達式
4. **CURRENCY_CODES** - 貨幣代碼（例外情況）
5. **isAddressLikeTerm()** - 過濾函數

然後在術語提取時應用過濾：

```typescript
for (const item of extractionResult.invoiceData.lineItems) {
  const term = item.description || item.productCode || 'Unknown';
  // FIX-005.2: 應用地址過濾邏輯
  if (term && term !== 'Unknown' && !isAddressLikeTerm(term)) {
    const formatTerms = companyTerms.get(companyId)!.get(formatName)!;
    formatTerms.set(term, (formatTerms.get(term) || 0) + 1);
  }
}
```

---

## 修改的文件

| 文件 | 變更 |
|------|------|
| `scripts/export-hierarchical-terms.ts` | 添加地址過濾常數和函數，在術語提取時應用過濾 |

---

## 驗證結果

### 過濾前後比較 (Batch: 335b5cc9)

| 指標 | 過濾前 | 過濾後 | 減少 |
|------|--------|--------|------|
| 唯一術語 | 386 | 354 | 32 (8.3%) |
| 總出現次數 | 526 | 484 | 42 (8.0%) |
| 公司數 | 53 | 53 | 0 |
| 格式數 | 53 | 53 | 0 |

### 匯出文件

- **過濾前**: `TEST-PLAN-004-hierarchical-terms-2025-12-30.xlsx` (386 terms)
- **過濾後**: `TEST-PLAN-004-hierarchical-terms-2025-12-31-filtered.xlsx` (354 terms)

---

## 技術說明

### 為什麼不直接導入服務層函數？

`export-hierarchical-terms.ts` 是一個 standalone script，使用 `ts-node` 直接運行。導入服務層模組會引入以下問題：

1. **Path Aliases**: 腳本無法解析 `@/services` 等路徑別名
2. **Module Resolution**: 需要複雜的 tsconfig 配置
3. **Dependencies**: 可能引入不必要的服務層依賴

因此選擇**複製過濾邏輯**而非導入，這是一種務實的解決方案。

### 維護注意事項

如果 `term-aggregation.service.ts` 中的過濾邏輯有更新（如添加新的地址關鍵字），需要同步更新 `export-hierarchical-terms.ts`。

建議：如果未來有更多腳本需要此過濾邏輯，可以考慮：
1. 創建一個 shared utilities 模組
2. 使用 `tsconfig-paths` 解決路徑別名問題
3. 重構為 monorepo 結構

---

**相關文檔**:
- [FIX-005: Term Aggregation Address Filtering](./FIX-005-term-aggregation-address-filtering.md)
- [FIX-005.1: Currency Code Exception](./FIX-005.1-currency-code-exception.md)
