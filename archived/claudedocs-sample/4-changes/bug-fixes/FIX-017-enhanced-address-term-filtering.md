# FIX-017: Enhanced Address Term Filtering

> **Bug ID**: FIX-017
> **狀態**: ✅ 已完成
> **修復日期**: 2025-12-31
> **影響範圍**: Epic 0 - 歷史數據初始化
> **相關文件**: `src/services/term-aggregation.service.ts`

---

## 問題描述

### 發現來源
TEST-PLAN-005 E2E 測試期間，用戶在 DHL 文件提取結果中發現大量非 line item 資料被錯誤地提取為術語。

### 錯誤提取的資料類型

| 類型 | 範例 | 來源 |
|------|------|------|
| 機場代碼 + 城市 | `HKG, HONG KONG` | 發貨/收貨地址區塊 |
| 機場代碼 + 城市 | `BLR, BANGALORE` | 發貨/收貨地址區塊 |
| 機場代碼 + 城市 | `SGN, HO CHI MINH CITY` | 發貨/收貨地址區塊 |
| 機場代碼 + 城市 | `SIN, SINGAPORE` | 發貨/收貨地址區塊 |
| 聯絡人姓名 | `KATHY LAM` | 聯絡人欄位 |
| 聯絡人姓名 | `Quach Thi Thien Nhi` | 聯絡人欄位 |
| 聯絡人姓名 | `NGUYEN VAN ANH` | 聯絡人欄位 |
| 公司名稱 | `RICOH ASIA PACIFIC OPERATIONS LIMITED` | 公司資訊區塊 |
| 公司名稱 | `DHL EXPRESS PTE LTD` | 發票抬頭 |
| 建築物名稱 | `E.Town Central, 11 Doan Van` | 地址欄位 |
| 建築物名稱 | `CENTRAL PLAZA TOWER` | 地址欄位 |

### 根本原因
`isAddressLikeTerm` 函數的過濾邏輯存在以下缺口：

1. **缺少 IATA 機場代碼識別** - 未能識別以機場代碼開頭的地址區塊
2. **缺少人名模式識別** - 未能識別聯絡人姓名格式
3. **缺少公司名稱模式識別** - 未能識別常見公司名稱後綴

---

## 解決方案

### 新增過濾邏輯

#### 1. IATA 機場代碼過濾
新增 `AIRPORT_CODES` 常數並檢測以機場代碼開頭的術語：

```typescript
// FIX-006: Check if term starts with airport code
const AIRPORT_CODES = [
  // Greater China
  'HKG', 'PEK', 'PVG', 'SHA', 'CAN', 'SZX', 'CTU', 'KMG', 'XIY', 'HGH',
  // Southeast Asia
  'SIN', 'BKK', 'KUL', 'CGK', 'MNL', 'SGN', 'HAN', 'DAD', 'CXR', 'PQC',
  // South Asia
  'BLR', 'DEL', 'BOM', 'MAA', 'CCU', 'HYD', 'COK', 'AMD', 'GOI', 'PNQ',
  // East Asia
  'NRT', 'HND', 'KIX', 'ICN', 'GMP', 'PUS', 'CJU',
  // Oceania
  'SYD', 'MEL', 'BNE', 'PER', 'ADL', 'CBR',
  // Taiwan
  'TPE', 'KHH', 'RMQ',
  // Others
  'DXB', 'DOH', 'AUH', 'SVO', 'CDG', 'LHR', 'FRA', 'AMS', 'JFK', 'LAX',
];

for (const code of AIRPORT_CODES) {
  const startsWithCode = new RegExp(`^${code}(?:[,\\s\\n]|$)`, 'i');
  if (startsWithCode.test(upperTerm)) {
    return true;
  }
}
```

#### 2. 人名模式過濾
檢測 2-4 個單詞、全字母、不含運費關鍵字的術語：

```typescript
// FIX-006: Check for person name patterns
const words = upperTerm.split(/\s+/).filter((w) => w.length > 1);
if (words.length >= 2 && words.length <= 4) {
  const allWordsAreNames = words.every((word) => {
    return /^[A-Z]+(?:-[A-Z]+)?$/i.test(word);
  });
  const freightKeywords = [
    'FREIGHT', 'CHARGE', 'FEE', 'SURCHARGE', 'HANDLING', 'CUSTOMS',
    'DUTY', 'TAX', 'IMPORT', 'EXPORT', 'CLEARANCE', 'DOCUMENT', 'EXPRESS',
    'DELIVERY', 'SHIPPING', 'TRANSPORT', 'CARGO', 'AIR', 'SEA', 'OCEAN',
    'FUEL', 'SECURITY', 'INSURANCE', 'PICKUP', 'COLLECT', 'PREPAID',
  ];
  const hasFreightKeyword = words.some((w) => freightKeywords.includes(w));
  if (allWordsAreNames && !hasFreightKeyword && upperTerm.length < 30) {
    return true;
  }
}
```

#### 3. 公司/建築物名稱模式過濾
檢測常見公司名稱後綴和建築物名稱：

```typescript
// FIX-006: Check for company/building name patterns
const companyPatterns = [
  /\bLIMITED\b/i,
  /\bLTD\b/i,
  /\bCO\.\s*LTD\b/i,
  /\bCORP(?:ORATION)?\b/i,
  /\bINC(?:ORPORATED)?\b/i,
  /\bPTE\b/i,
  /\bPVT\b/i,
  /\bGMBH\b/i,
  /\bSDN\s*BHD\b/i,
  /\bS\.?A\.?\b/,
  /\bOPERATIONS\b/i,
  /\bCENTRAL\b/i,
  /\bPLAZA\b/i,
  /\bCENTRE\b/i,
  /\bCENTER\b/i,
];
for (const pattern of companyPatterns) {
  if (pattern.test(upperTerm)) {
    return true;
  }
}
```

---

## 測試驗證

### 測試腳本
建立 `scripts/test-fix-006.mjs` 進行驗證，包含 23 個測試案例。

### 測試結果
```
======================================================================
FIX-006 - Enhanced Address Term Filtering Test
======================================================================

✅ PASS: "HKG, HONG KONG\nRICOH ASIA PACIFIC OPERATIONS..."
   Expected: true, Got: true (airport code + company name)

✅ PASS: "KATHY LAM"
   Expected: true, Got: true (person name)

✅ PASS: "Quach Thi Thien Nhi"
   Expected: true, Got: true (person name (Vietnamese))

✅ PASS: "BLR, BANGALORE"
   Expected: true, Got: true (airport code + city)

✅ PASS: "EXPRESS WORLDWIDE NONDOC"
   Expected: false, Got: false (valid freight service)

✅ PASS: "FREIGHT CHARGES"
   Expected: false, Got: false (valid freight charge)

... (23 test cases total)

======================================================================
Results: 23 passed, 0 failed (100% success rate)
======================================================================
```

### 測試案例分類

| 類別 | 預期結果 | 數量 | 通過 |
|------|----------|------|------|
| 應過濾（地址類） | `true` | 12 | 12 ✅ |
| 不應過濾（運費類） | `false` | 11 | 11 ✅ |

---

## 修改文件

| 文件 | 變更類型 | 說明 |
|------|----------|------|
| `src/services/term-aggregation.service.ts` | 修改 | 增強 `isAddressLikeTerm` 函數 |
| `scripts/test-fix-006.mjs` | 新增 | FIX-006 測試腳本 |

---

## 向後相容性

✅ **完全向後相容**

- 所有有效的運費術語（如 `EXPRESS WORLDWIDE NONDOC`, `FREIGHT CHARGES`, `FUEL SURCHARGE`）仍正確通過過濾
- 含貨幣代碼的價格行（如 `FREIGHT CHARGES USD 65.00`）仍正確保留
- 現有 FIX-005 和 FIX-005.1 的過濾邏輯不受影響

---

## 相關修復歷史

| 修復 | 日期 | 說明 |
|------|------|------|
| FIX-013 | 2025-12-29 | 初始地址過濾功能 |
| FIX-013.1 | 2025-12-29 | 新增貨幣代碼例外處理 |
| FIX-015 | 2025-12-30 | Excel 導出腳本地址過濾 |
| **FIX-017** | **2025-12-31** | **機場代碼、人名、公司名過濾** |

---

## 後續建議

1. **重新執行 TEST-PLAN-005** - 等待 Azure DI 配額恢復後，重新處理失敗的文件
2. **監控過濾效果** - 在下次批次處理後檢查術語聚合結果
3. **持續優化** - 如發現新的錯誤提取模式，持續擴充過濾邏輯

---

*文檔建立: 2025-12-31*
*最後更新: 2025-12-31*
