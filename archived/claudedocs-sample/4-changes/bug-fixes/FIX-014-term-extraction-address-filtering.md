# FIX-014: 術語提取地址過濾

> **狀態**: ✅ 已完成
> **日期**: 2025-12-30
> **影響**: Epic 0 - 歷史數據初始化
> **優先級**: 高

---

## 問題描述

### 現象
在 TEST-PLAN-003 執行後，階層式術語報告（hierarchical-terms-report.xlsx）中發現大量地址、公司名稱、收件人資訊被錯誤地當作「術語」提取：

**錯誤提取的內容範例**:
- `BO STREET WARD 13 DISTRICT 4 HO CHI MINH CITY`（地址）
- `BANGKOK THAILAND`（城市國家）
- `SHANGHAI CHINA`（城市國家）
- `NGUYEN VAN A`（人名）
- `P O BOX 12345`（郵政信箱）

**正確的術語應該是**:
- `EXPRESS WORLDWIDE NONDOC`
- `FUEL SURCHARGE`
- `DUTIES & TAXES`
- `HANDLING FEE`
- `FREIGHT CHARGE`

### 根本原因
Azure Document Intelligence 和 GPT Vision 從發票中提取的 `lineItems` 陣列包含混合數據：
- 運費項目（正確的術語來源）
- 地址區塊
- 交易方資訊（發件人/收件人）
- 公司/個人名稱

三個術語聚合服務（`term-aggregation.service.ts`、`batch-term-aggregation.service.ts`、`hierarchical-term-aggregation.service.ts`）直接提取 `lineItems` 中的 `description`、`name`、`chargeType` 欄位，未過濾地址類內容。

---

## 修復方案

### 解決策略
新增 `isAddressLikeTerm()` 函數，使用多層檢測邏輯過濾地址類術語：

1. **地址關鍵字檢測**（使用 `\b` 詞邊界確保精確匹配）
2. **地理位置名稱檢測**（主要城市和國家）
3. **地址模式正則匹配**（郵遞區號、街道號碼等）

### 修改的文件

#### 1. `src/services/term-aggregation.service.ts`
- 新增 `ADDRESS_KEYWORDS` 常數（35+ 地址關鍵字）
- 新增 `LOCATION_NAMES` 常數（60+ 城市/國家名稱）
- 新增 `ADDRESS_PATTERNS` 常數（5 個正則表達式）
- 新增並導出 `isAddressLikeTerm()` 函數
- 在 `extractTermsFromResult()` 中應用過濾

```typescript
export function isAddressLikeTerm(term: string): boolean {
  const upperTerm = term.toUpperCase().trim();

  // 1. 檢查地址關鍵字
  for (const keyword of ADDRESS_KEYWORDS) {
    const regex = new RegExp(`\\b${keyword}\\b`, 'i');
    if (regex.test(upperTerm)) {
      return true;
    }
  }

  // 2. 檢查地理位置名稱
  for (const location of LOCATION_NAMES) {
    const regex = new RegExp(`\\b${location}\\b`, 'i');
    if (regex.test(upperTerm)) {
      return true;
    }
  }

  // 3. 檢查地址模式
  for (const pattern of ADDRESS_PATTERNS) {
    if (pattern.test(upperTerm)) {
      return true;
    }
  }

  return false;
}
```

#### 2. `src/services/batch-term-aggregation.service.ts`
- 導入 `isAddressLikeTerm` 函數
- 在 `extractTermsFromExtractionResult()` 中應用過濾
- 對 `description`、`name`、`chargeType` 三個欄位都進行過濾

#### 3. `src/services/hierarchical-term-aggregation.service.ts`
- 導入 `isAddressLikeTerm` 函數
- 在 `aggregateTermsHierarchically()` 中應用過濾
- 在 `getCompanyTermAggregation()` 中應用過濾
- 在 `getFormatTermAggregation()` 中應用過濾

---

## 地址檢測規則

### ADDRESS_KEYWORDS（地址關鍵字）
```
STREET, ROAD, AVENUE, BOULEVARD, LANE, DRIVE, COURT, PLACE,
FLOOR, UNIT, BUILDING, SUITE, ROOM, TOWER, BLOCK,
DISTRICT, WARD, PROVINCE, STATE, CITY, TOWN, VILLAGE, COUNTY,
P O BOX, PO BOX, POSTAL, ZIP,
ATTENTION, ATTN, C/O, CARE OF
```

### LOCATION_NAMES（地理位置名稱）
```
// 主要城市
HONG KONG, SINGAPORE, BANGKOK, TOKYO, OSAKA, SEOUL,
SHANGHAI, BEIJING, SHENZHEN, TAIPEI, KUALA LUMPUR,
HO CHI MINH, HANOI, JAKARTA, MANILA, MUMBAI, NEW DELHI

// 國家
CHINA, JAPAN, KOREA, VIETNAM, THAILAND, INDONESIA,
MALAYSIA, PHILIPPINES, INDIA, TAIWAN, USA, UK
```

### ADDRESS_PATTERNS（地址正則模式）
```regex
/^\d{4,6}$/           # 純數字郵遞區號
/^\d+[A-Z]?\s/        # 街道號碼開頭
/\d{5,6}$/            # 結尾郵遞區號
/^[A-Z]{2}\d{1,2}\s/  # 英國郵遞區號格式
/FLOOR\s*\d+/i        # 樓層編號
```

---

## 驗證結果

### 測試腳本: `scripts/test-fix-005.ts`

```
=== FIX-005 isAddressLikeTerm 函數驗證 ===

✅ "BO STREET WARD 13 DISTRICT 4" → true (expected: true)
✅ "HO CHI MINH CITY VIETNAM" → true (expected: true)
✅ "123 NGUYEN HUE STREET" → true (expected: true)
✅ "BANGKOK THAILAND" → true (expected: true)
✅ "TOKYO JAPAN" → true (expected: true)
✅ "SINGAPORE 049483" → true (expected: true)
✅ "EXPRESS WORLDWIDE NONDOC" → false (expected: false)
✅ "FUEL SURCHARGE" → false (expected: false)
✅ "DUTIES & TAXES" → false (expected: false)
✅ "FREIGHT CHARGE" → false (expected: false)

=== 測試結果 ===
通過: 20/20
失敗: 0/20

✅ FIX-005 地址過濾邏輯運作正常！
```

---

## 影響範圍

### 直接影響
- 新批次的術語聚合將自動過濾地址類內容
- 術語報告品質顯著提升

### 不影響
- 現有已處理批次的數據（需重新聚合才會生效）
- 文件發行方識別邏輯
- OCR/AI 提取結果

---

## 後續建議

1. **重新聚合現有批次**（可選）：
   - 若需更新現有報告，可呼叫術語重新聚合 API

2. **擴展地址檢測規則**（低優先）：
   - 根據實際使用情況，可增加更多地理位置名稱
   - 可增加更多語言的地址關鍵字

3. **監控術語品質**：
   - 定期檢查術語報告，確認無新的地址類術語混入

---

## 相關文件

- `src/services/term-aggregation.service.ts`
- `src/services/batch-term-aggregation.service.ts`
- `src/services/hierarchical-term-aggregation.service.ts`
- `scripts/test-fix-005.ts`
- `claudedocs/5-status/testing/reports/TEST-REPORT-003-*.md`

---

**維護者**: Development Team
**建立日期**: 2025-12-30
**版本**: 1.0.0
