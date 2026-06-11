# CHANGE-002: 階層式術語報告匯出功能

> **建立日期**: 2025-12-27
> **完成日期**: 2025-12-27
> **狀態**: ✅ 實作完成
> **優先級**: Medium
> **關聯 Epic**: Epic 0 - 歷史數據初始化

---

## 1. 變更概述

### 背景

歷史數據初始化流程（Epic 0）的核心目標是：
1. 處理歷史文件並提取內容
2. 識別發行公司（Document Issuer）
3. 分類文件格式（Document Format）
4. 記錄所有術語（Terms）
5. **生成報告作為建立三層映射規則的初始數據基礎**

目前系統已完成：
- ✅ UI 組件：`CompanyFormatTree.tsx` 顯示 Company → Format → Terms 樹狀結構
- ✅ API 端點：`GET /api/v1/batches/:batchId/hierarchical-terms`
- ✅ 服務層：`hierarchical-term-aggregation.service.ts`
- ❌ **缺失**：報告匯出功能

### 目標

設計並實現「階層式術語報告匯出」功能，讓用戶可以將處理完成的批次數據匯出為結構化報告（Excel 格式），作為後續建立映射規則的參考文件。

---

## 2. 功能需求

### 2.1 匯出格式

**Excel 格式** (`.xlsx`)，包含以下工作表：

#### 工作表 1：摘要 (Summary)

| 欄位 | 說明 |
|------|------|
| 批次 ID | 批次唯一識別碼 |
| 批次名稱 | 用戶設定的批次名稱 |
| 處理時間 | 批次開始和完成時間 |
| 公司數量 | 識別的公司總數 |
| 格式數量 | 識別的文件格式總數 |
| 唯一術語數 | 不重複的術語總數 |
| 術語出現次數 | 術語總出現次數 |
| 報告產生時間 | 匯出時間戳 |

#### 工作表 2：公司列表 (Companies)

| 欄位 | 說明 |
|------|------|
| 公司 ID | 公司唯一識別碼 |
| 公司名稱 | 主要名稱 |
| 名稱變體 | 其他識別名稱（逗號分隔） |
| 文件數量 | 該公司的文件總數 |
| 格式數量 | 該公司的格式總數 |
| 術語數量 | 該公司的唯一術語數 |

#### 工作表 3：格式列表 (Formats)

| 欄位 | 說明 |
|------|------|
| 格式 ID | 格式唯一識別碼 |
| 所屬公司 | 公司名稱 |
| 文件類型 | INVOICE, DEBIT_NOTE, CREDIT_NOTE 等 |
| 文件子類型 | OCEAN_FREIGHT, AIR_FREIGHT 等 |
| 格式名稱 | 格式描述性名稱 |
| 文件數量 | 該格式的文件數 |
| 術語數量 | 該格式的唯一術語數 |

#### 工作表 4：術語列表 (Terms)

| 欄位 | 說明 |
|------|------|
| 序號 | 按頻率排序的序號 |
| 公司名稱 | 所屬公司 |
| 格式類型 | 文件類型/子類型 |
| 術語 | 正規化後的術語 |
| 出現頻率 | 在該格式中出現的次數 |
| 範例 | 原始術語範例（最多 3 個） |
| 建議分類 | 預留欄位（供手動填寫或後續 AI 分類） |

### 2.2 使用場景

```
批次處理完成 → 用戶進入批次詳情頁
    → 點擊「匯出術語報告」按鈕
    → 選擇匯出選項（可選）
    → 下載 Excel 報告
```

### 2.3 匯出選項（可選功能）

| 選項 | 預設值 | 說明 |
|------|--------|------|
| 最小術語頻率 | 1 | 只匯出出現次數 ≥ N 的術語 |
| 最大術語數/格式 | 500 | 每個格式最多匯出 N 個術語 |
| 包含範例 | 是 | 是否包含原始術語範例 |

---

## 3. 技術設計

### 3.1 新增文件

#### 3.1.1 Excel 生成器

**路徑**: `src/lib/reports/hierarchical-terms-excel.ts`

```typescript
/**
 * @fileoverview 階層式術語報告 Excel 生成器
 * @module src/lib/reports/hierarchical-terms-excel
 * @since Epic 0 - CHANGE-002
 */

import ExcelJS from 'exceljs';
import type { HierarchicalTermAggregation } from '@/types/document-format';

export interface HierarchicalTermsReportData {
  batch: {
    id: string;
    name: string;
    startedAt: Date | null;
    completedAt: Date | null;
  };
  aggregation: HierarchicalTermAggregation;
  generatedAt: Date;
  generatedBy: string;
}

export async function generateHierarchicalTermsExcel(
  data: HierarchicalTermsReportData
): Promise<Buffer>;
```

#### 3.1.2 API 端點

**路徑**: `src/app/api/v1/batches/[batchId]/hierarchical-terms/export/route.ts`

```typescript
/**
 * GET /api/v1/batches/:batchId/hierarchical-terms/export
 * 匯出階層式術語報告
 *
 * @query format - 匯出格式（預設 xlsx）
 * @query minTermFrequency - 最小術語頻率（預設 1）
 * @query maxTermsPerFormat - 每格式最大術語數（預設 500）
 *
 * @returns Excel 文件（Content-Disposition: attachment）
 */
export async function GET(request: NextRequest, { params }) {
  // 1. 驗證批次存在且已完成
  // 2. 獲取階層式術語聚合數據
  // 3. 生成 Excel 報告
  // 4. 返回文件下載響應
}
```

#### 3.1.3 前端匯出按鈕組件

**路徑**: `src/components/features/historical-data/HierarchicalTermsExportButton.tsx`

```typescript
/**
 * @component HierarchicalTermsExportButton
 * @description 階層式術語報告匯出按鈕
 */
interface HierarchicalTermsExportButtonProps {
  batchId: string;
  batchName?: string;
  disabled?: boolean;
}

export function HierarchicalTermsExportButton(props) {
  // 匯出邏輯
}
```

### 3.2 整合位置

#### 批次詳情頁整合

在 `src/app/(dashboard)/admin/historical-data/page.tsx` 的批次詳情區塊中，新增「匯出術語報告」按鈕：

```tsx
{selectedBatch && selectedBatch.status === 'COMPLETED' && (
  <HierarchicalTermsExportButton
    batchId={selectedBatch.id}
    batchName={selectedBatch.name}
  />
)}
```

### 3.3 數據流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 用戶點擊「匯出術語報告」                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ GET /api/v1/batches/:batchId/hierarchical-terms/export          │
│ ├── 驗證批次狀態 (COMPLETED)                                     │
│ ├── 調用 aggregateTermsHierarchically()                         │
│ └── 調用 generateHierarchicalTermsExcel()                       │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 返回 Excel 文件                                                  │
│ Content-Type: application/vnd.openxmlformats-officedocument...  │
│ Content-Disposition: attachment; filename="術語報告-{批次名}.xlsx"│
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 影響範圍

### 4.1 新增文件

| 文件路徑 | 類型 | 說明 |
|----------|------|------|
| `src/lib/reports/hierarchical-terms-excel.ts` | 服務 | Excel 生成器 |
| `src/app/api/v1/batches/[batchId]/hierarchical-terms/export/route.ts` | API | 匯出端點 |
| `src/components/features/historical-data/HierarchicalTermsExportButton.tsx` | 組件 | 匯出按鈕 |

### 4.2 修改文件

| 文件路徑 | 修改內容 |
|----------|----------|
| `src/app/(dashboard)/admin/historical-data/page.tsx` | 添加匯出按鈕 |
| `src/lib/reports/index.ts` | 導出新生成器 |

### 4.3 依賴

- `exceljs` - 已安裝，用於 Excel 生成
- `@/types/document-format` - 類型定義
- `@/services/hierarchical-term-aggregation.service` - 數據聚合

---

## 5. 驗收標準

### 5.1 功能驗收

- [ ] 批次詳情頁顯示「匯出術語報告」按鈕（僅已完成批次）
- [ ] 點擊按鈕可下載 Excel 文件
- [ ] Excel 包含 4 個工作表：摘要、公司、格式、術語
- [ ] 術語按出現頻率降序排列
- [ ] 文件名包含批次名稱和日期

### 5.2 數據驗收

- [ ] 摘要數據準確反映批次統計
- [ ] 公司列表包含所有識別的公司
- [ ] 格式列表正確關聯到公司
- [ ] 術語列表包含正規化術語和原始範例

### 5.3 性能驗收

- [ ] 大批次（1000+ 文件）匯出時間 < 30 秒
- [ ] Excel 文件大小合理（< 10MB）

---

## 6. 實現步驟

### Step 1: 創建 Excel 生成器 (30 min)
- 建立 `hierarchical-terms-excel.ts`
- 實現 4 個工作表的生成邏輯
- 添加樣式和格式化

### Step 2: 創建 API 端點 (20 min)
- 建立 `export/route.ts`
- 實現參數驗證和錯誤處理
- 設置正確的響應標頭

### Step 3: 創建前端組件 (20 min)
- 建立 `HierarchicalTermsExportButton.tsx`
- 處理載入狀態和錯誤

### Step 4: 整合到批次詳情頁 (10 min)
- 添加匯出按鈕到頁面
- 條件顯示（僅已完成批次）

### Step 5: 測試驗證 (20 min)
- 功能測試
- 數據驗證
- 邊界條件測試

**預估總時間**: 100 分鐘

---

## 7. 相關文件

| 文件 | 說明 |
|------|------|
| `src/services/hierarchical-term-aggregation.service.ts` | 術語聚合服務 |
| `src/app/api/v1/batches/[batchId]/hierarchical-terms/route.ts` | 現有聚合 API |
| `src/lib/reports/excel-generator.ts` | 現有 Excel 模板參考 |
| `src/components/features/format-analysis/CompanyFormatTree.tsx` | 現有樹狀 UI |

---

**設計者**: Claude AI Assistant
**設計日期**: 2025-12-27
