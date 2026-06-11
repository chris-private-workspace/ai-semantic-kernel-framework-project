# CHANGE-003: 歷史數據文件詳情頁

> **建立日期**: 2025-12-28
> **完成日期**: 2025-12-28
> **類型**: 功能增強
> **狀態**: ✅ 已完成
> **優先級**: High
> **關聯**: Epic 0 歷史數據初始化

---

## 1. 增強目標

### 1.1 背景

在完成 TEST-PLAN-002 歷史數據初始化測試後，用戶檢查導出的 Excel 報告發現部分術語提取結果有異常。現有的歷史數據管理頁面只顯示文件列表，無法深入查看每個文件的：

- 處理過程詳情（Processing Timeline）
- 提取結果結構（Extraction Results）
- 發行者識別信息（Issuer Identification）
- Line Items 數據（Term Data）

### 1.2 目標

在 `/admin/historical-data` 功能基礎上，新增文件詳情頁面，讓用戶可以：

1. 查看完整的處理過程時間軸
2. 檢視 extractionResult 的結構化數據
3. 驗證發行者識別方法和結果
4. 查看 Line Items 表格數據
5. 查看原始 JSON 數據進行調試

---

## 2. 設計方案

### 2.1 頁面路由

新增獨立詳情頁面：`/admin/historical-data/files/[fileId]`

### 2.2 頁面佈局

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回批次列表    文件名稱.pdf                    狀態徽章 │
├─────────────────────────────────────────────────────────┤
│ ┌───────────────────┐  ┌─────────────────────────────┐ │
│ │ 文件基本資訊       │  │ 處理時間軸                   │ │
│ │ - 文件名/大小/類型 │  │ ●──●──●──●                  │ │
│ │ - 處理方法        │  │ 上傳  檢測  處理  完成        │ │
│ │ - 處理成本        │  └─────────────────────────────┘ │
│ └───────────────────┘                                   │
├─────────────────────────────────────────────────────────┤
│ Tabs: [提取結果] [發行者識別] [Line Items] [原始 JSON]   │
├─────────────────────────────────────────────────────────┤
│ Tab 內容區域 (根據選擇的 Tab 顯示對應內容)               │
└─────────────────────────────────────────────────────────┘
```

### 2.3 組件架構

| 組件 | 用途 |
|------|------|
| `FileInfoCard` | 顯示基本文件資訊（名稱、大小、類型、狀態） |
| `ProcessingTimeline` | 處理流程時間軸（上傳→檢測→處理→完成） |
| `ExtractionResultPanel` | 提取結果摘要（invoiceData 欄位） |
| `IssuerIdentificationPanel` | 發行者識別結果（方法、信心度、匹配公司） |
| `LineItemsTable` | Line Items 表格（description、amount、quantity） |
| `RawJsonViewer` | 原始 JSON 查看器（可展開/收合的 JSON 樹狀結構） |

---

## 3. 實施內容

### 3.1 新增文件

| 文件路徑 | 用途 |
|---------|------|
| `src/app/(dashboard)/admin/historical-data/files/[fileId]/page.tsx` | 文件詳情頁面 |
| `src/app/api/admin/historical-data/files/[id]/detail/route.ts` | API 端點 |
| `src/hooks/use-historical-file-detail.ts` | React Hook |
| `src/components/features/historical-data/file-detail/FileInfoCard.tsx` | 基本資訊卡片 |
| `src/components/features/historical-data/file-detail/ProcessingTimeline.tsx` | 處理時間軸 |
| `src/components/features/historical-data/file-detail/ExtractionResultPanel.tsx` | 提取結果面板 |
| `src/components/features/historical-data/file-detail/IssuerIdentificationPanel.tsx` | 發行者識別面板 |
| `src/components/features/historical-data/file-detail/LineItemsTable.tsx` | Line Items 表格 |
| `src/components/features/historical-data/file-detail/RawJsonViewer.tsx` | JSON 查看器 |
| `src/components/features/historical-data/file-detail/index.ts` | 組件導出 |

### 3.2 修改文件

| 文件路徑 | 變更說明 |
|---------|----------|
| `src/components/features/historical-data/HistoricalFileList.tsx` | 添加「查看詳情」按鈕 |
| `src/components/features/historical-data/index.ts` | 導出新組件 |

---

## 4. 向後兼容性

- [x] 無 API 簽名變更（新增 API）
- [x] 無資料結構變更（使用現有 HistoricalFile 模型）
- [x] 無 Prisma Migration（使用現有數據）
- [x] 現有頁面功能保持不變

---

## 5. 驗收標準

### 5.1 功能驗收

- [x] 從文件列表可以點擊進入詳情頁
- [x] 詳情頁顯示完整的處理過程時間軸
- [x] 可以查看 extractionResult 的結構化數據
- [x] 可以查看發行者識別方法和結果
- [x] 可以查看 Line Items 表格
- [x] 可以查看原始 JSON 數據
- [x] 頁面支援返回批次列表

### 5.2 技術驗收

- [x] TypeScript 檢查通過
- [x] ESLint 檢查通過
- [x] 組件包含標準 JSDoc 註釋
- [x] 使用 React Query 進行資料獲取
- [x] 使用 shadcn/ui 組件

### 5.3 用戶體驗

- [x] 響應式設計
- [x] Loading 狀態處理
- [x] Error 狀態處理
- [x] 清晰的導航路徑

---

## 6. 開發進度

### 2025-12-28

**完成項目:**
- [x] Phase 1: 建立 API 端點 `/api/admin/historical-data/files/[id]/detail`
- [x] Phase 2: 建立 React Hook `useHistoricalFileDetail`
- [x] Phase 3: 建立頁面路由 `/admin/historical-data/files/[fileId]`
- [x] Phase 4: 建立 6 個組件
  - FileInfoCard
  - ProcessingTimeline
  - ExtractionResultPanel
  - IssuerIdentificationPanel
  - LineItemsTable
  - RawJsonViewer
- [x] Phase 5: 修改現有組件 (HistoricalFileList 添加查看詳情按鈕)
- [x] Phase 6: 測試驗證 (TypeScript + ESLint 檢查通過)

**修復的問題:**
1. **API 欄位名稱錯誤**: 修正 `batchName` → `name`，符合 Prisma schema
2. **函數命名衝突**: `IssuerIdentificationPanel` 中的 `formatConfidence` 函數與 prop 同名，重命名為 `formatConfidenceValue`
3. **DocumentFormat.name 可能為 null**: 添加 null 合併運算子提供預設值
4. **DocumentFormat enum 類型斷言**: 添加 `as string | null` 類型斷言

**交付成果:**
- 10 個新增文件
- 2 個修改文件
- 所有代碼品質檢查通過

---

## 7. 相關文檔

- [TEST-PLAN-002](../../5-status/testing/plans/TEST-PLAN-002-EPIC-0-COMPLETE.md) - 觸發此增強的測試計劃
- [TEST-REPORT-002](../../5-status/testing/reports/TEST-REPORT-002-EPIC-0-COMPLETE.md) - 測試報告
- [Epic 0 架構](../../1-planning/epics/epic-0/) - 歷史數據初始化 Epic

---

*實施人: AI Assistant*
*建立時間: 2025-12-28*
