# TEST-REPORT-003: CHANGE-005 統一管道步驟重排序 E2E 測試報告

> **建立日期**: 2026-01-05
> **測試計劃**: TEST-PLAN-003-EPIC-0-FULL-FEATURE
> **關聯變更**: CHANGE-005 (統一管道步驟重排序)
> **狀態**: ⚠️ 部分通過

---

## 1. 測試概述

### 1.1 測試目標

驗證 CHANGE-005 實施後的完整歷史數據初始化流程：
- ISSUER_IDENTIFICATION (Step 3) → FORMAT_MATCHING (Step 4) → CONFIG_FETCHING (Step 5) → AZURE_DI_EXTRACTION (Step 6)
- GPT Vision 發行者識別與 Azure DI 數據提取的分離
- DUAL_PROCESSING 模式的回退機制

### 1.2 測試批次資訊

| 項目 | 數值 |
|------|------|
| **批次 ID** | `ab950af1-01f0-4adc-b81f-b16c78c9f526` |
| **批次名稱** | TEST-PLAN-003-CHANGE-005-2026-01-05 |
| **總檔案數** | 132 |
| **測試日期** | 2026-01-05 |
| **測試環境** | Development (localhost:3010) |

---

## 2. 測試結果摘要

### 2.1 整體結果

| 指標 | 數值 | 狀態 |
|------|------|------|
| **總處理檔案** | 132 | - |
| **成功檔案** | 92 (69.7%) | ⚠️ |
| **失敗檔案** | 40 (30.3%) | ❌ |
| **總成本** | $2.74 | ✅ |
| **處理時間** | ~20.6 分鐘 | ✅ |

### 2.2 識別結果

| 識別類型 | 數量 | 狀態 | 說明 |
|----------|------|------|------|
| **發行者識別** | 0 | ❌ | GPT Vision 失敗導致無法執行 |
| **格式識別** | 0 | ❌ | 依賴發行者識別，無法執行 |
| **公司識別** | 0 | ❌ | 依賴發行者識別，無法執行 |
| **術語聚合** | 193 unique terms | ✅ | 正常運作 |

### 2.3 處理方法分佈

| 處理方法 | 成功 | 失敗 | 說明 |
|----------|------|------|------|
| **DUAL_PROCESSING** | 92 | 0 | GPT Vision 失敗 → 自動回退至 Azure DI |
| **GPT_VISION** | 0 | 40 | 完全失敗，無回退選項 |

---

## 3. 關鍵發現

### 3.1 ⚠️ GPT Vision PDF 轉換失敗（阻塞性問題）

**錯誤訊息**:
```
TypeError: intentState.renderTasks is not iterable
Cannot read properties of undefined (reading 'canvas')
Unable to load font data at: standard_fonts/LiberationSans-Regular.ttf
```

**根本原因**: `pdfjs-dist` 函式庫在 Next.js 伺服器環境中存在相容性問題，無法正確執行 PDF 頁面渲染為圖片的操作。

**影響範圍**:
- 所有需要 GPT Vision 處理的檔案
- CHANGE-005 的核心功能（發行者識別）無法驗證
- 格式識別和公司自動建立功能連帶無法執行

### 3.2 ✅ DUAL_PROCESSING 回退機制正常運作

當 GPT Vision 失敗時，DUAL_PROCESSING 模式成功回退至僅使用 Azure DI 進行數據提取：
- 92 個 DUAL_PROCESSING 檔案全部成功提取 invoiceData
- Azure DI 提取信心度維持 100%
- 術語聚合正常執行（193 unique terms）

### 3.3 ✅ CHANGE-005 步驟順序已正確實施

從日誌確認處理步驟順序：
1. `[Step 1] FILE_VALIDATION` - ✅
2. `[Step 2] FILE_TYPE_DETECTION` - ✅
3. `[Step 3] ISSUER_IDENTIFICATION` - ⚠️ GPT Vision 失敗
4. `[Step 4] FORMAT_MATCHING` - ⏭️ 跳過（依賴 Step 3）
5. `[Step 5] CONFIG_FETCHING` - ⏭️ 跳過（依賴 Step 4）
6. `[Step 6] AZURE_DI_EXTRACTION` - ✅ 回退執行

---

## 4. 測試案例結果

### 4.1 Phase 1: 文件上傳與元數據偵測

| 測試案例 | 結果 | 說明 |
|----------|------|------|
| TC-1.1 批次建立 | ✅ 通過 | 批次成功建立，ID 正確分配 |
| TC-1.2 檔案上傳 | ✅ 通過 | 132 檔案全部成功上傳 |
| TC-1.3 元數據偵測 | ✅ 通過 | 檔案類型正確識別 |

### 4.2 Phase 2: 智能處理路由

| 測試案例 | 結果 | 說明 |
|----------|------|------|
| TC-2.1 Native PDF 路由 | ✅ 通過 | 正確路由至 DUAL_PROCESSING |
| TC-2.2 Scanned PDF 路由 | ✅ 通過 | 正確路由至 GPT_VISION |
| TC-2.3 Image 路由 | ✅ 通過 | 正確路由至 GPT_VISION |

### 4.3 Phase 3: 發行者識別 (CHANGE-005 重點)

| 測試案例 | 結果 | 說明 |
|----------|------|------|
| TC-3.1 GPT Vision 執行 | ❌ 失敗 | pdfjs-dist 錯誤阻塞 |
| TC-3.2 發行者名稱提取 | ❌ 未執行 | 依賴 TC-3.1 |
| TC-3.3 公司匹配 | ❌ 未執行 | 依賴 TC-3.2 |
| TC-3.4 公司自動建立 | ❌ 未執行 | 依賴 TC-3.3 |

### 4.4 Phase 4-5: 格式識別與數據提取

| 測試案例 | 結果 | 說明 |
|----------|------|------|
| TC-4.1 格式匹配 | ❌ 未執行 | 依賴發行者識別 |
| TC-4.2 格式自動建立 | ❌ 未執行 | 依賴發行者識別 |
| TC-5.1 Azure DI 提取 | ✅ 通過 | 92 檔案成功提取 |
| TC-5.2 invoiceData 結構 | ✅ 通過 | 數據結構正確 |

### 4.5 Phase 6: 術語聚合

| 測試案例 | 結果 | 說明 |
|----------|------|------|
| TC-6.1 術語提取 | ✅ 通過 | 193 unique terms |
| TC-6.2 術語統計 | ✅ 通過 | 正確統計頻率 |
| TC-6.3 BatchTermMapping | ✅ 通過 | 記錄正確建立 |

---

## 5. 問題追蹤

### 5.1 阻塞性問題

| 編號 | 問題 | 嚴重度 | 狀態 | 建議修復 |
|------|------|--------|------|----------|
| **BUG-001** | pdfjs-dist 在 Next.js 伺服器環境中 PDF 渲染失敗 | 🔴 Critical | Open | 需要調查 pdfjs-dist 版本或替代方案 |

### 5.2 已修復問題（本次測試前）

| 編號 | 問題 | 狀態 |
|------|------|------|
| FIX-005 | IssuerIdentifierAdapter 欄位映射錯誤 | ✅ 已修復 |

---

## 6. 結論與建議

### 6.1 測試結論

| 項目 | 結果 |
|------|------|
| **CHANGE-005 步驟順序** | ✅ 正確實施 |
| **DUAL_PROCESSING 回退** | ✅ 正常運作 |
| **發行者識別功能** | ❌ 無法驗證（GPT Vision 失敗） |
| **術語聚合功能** | ✅ 正常運作 |
| **整體測試** | ⚠️ 部分通過 |

### 6.2 建議

1. **🔴 優先修復 pdfjs-dist 問題**
   - 調查 pdfjs-dist 版本相容性
   - 考慮使用 `pdf-lib` 或 `pdf2pic` 等替代方案
   - 確保 Next.js 伺服器環境中的 Canvas 支援

2. **待 GPT Vision 修復後重新執行測試**
   - 完整驗證 CHANGE-005 發行者識別流程
   - 驗證公司自動建立功能
   - 驗證格式識別與匹配功能

3. **考慮新增錯誤處理**
   - 在 GPT Vision 失敗時提供更清晰的錯誤訊息
   - 考慮對 GPT_VISION 專用模式新增回退選項

---

## 7. 附件

### 7.1 相關文件

| 文件 | 路徑 |
|------|------|
| 測試計劃 | `claudedocs/5-status/testing/plans/TEST-PLAN-003-EPIC-0-FULL-FEATURE.md` |
| CHANGE-005 文檔 | `claudedocs/4-changes/feature-changes/CHANGE-005-unified-pipeline-step-reorder.md` |
| FIX-005 文檔 | `claudedocs/4-changes/bug-fixes/FIX-005-issuer-identifier-field-mapping.md` |

### 7.2 錯誤日誌摘錄

```
[GPT Vision] PDF-to-image conversion failed: TypeError: intentState.renderTasks is not iterable
[GPT Vision] PDF-to-image conversion failed: Cannot read properties of undefined (reading 'canvas')
[GPT Vision] Warning: Unable to load font data at: standard_fonts/LiberationSans-Regular.ttf
```

---

**報告生成日期**: 2026-01-05
**測試執行者**: AI Assistant (Claude)
**審核狀態**: 待審核
