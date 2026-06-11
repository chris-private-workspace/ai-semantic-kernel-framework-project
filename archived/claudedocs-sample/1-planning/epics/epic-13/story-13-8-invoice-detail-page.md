# Story 13-8: 發票詳情頁面

> **建立日期**: 2026-01-18
> **狀態**: 📋 待開發
> **估點**: 8 點
> **優先級**: High
> **關聯 Epic**: Epic 13 - 文件預覽與欄位映射

---

## 1. 概述

### 1.1 背景

目前發票列表頁面 (`/invoices`) 顯示發票基本資訊，但缺少詳情頁面讓用戶查看：
- 完整的發票內容預覽
- 提取的欄位詳情
- 處理步驟與時間軸
- 審核歷史記錄

### 1.2 目標

建立發票詳情頁面 `/[locale]/(dashboard)/invoices/[id]/page.tsx`，整合 Epic 13 的預覽組件，提供完整的發票查看體驗。

### 1.3 用戶價值

- **審核員**: 快速查看發票內容和 AI 提取結果，進行準確判斷
- **管理員**: 追蹤發票處理歷程，了解系統處理情況
- **用戶**: 查看自己上傳的發票處理狀態和結果

---

## 2. 功能需求

### 2.1 頁面結構

```
/[locale]/(dashboard)/invoices/[id]/page.tsx
├── 頭部區塊 (Header)
│   ├── 返回按鈕 (← 返回列表)
│   ├── 文件名稱
│   ├── 狀態徽章 (ProcessingStatus)
│   └── 操作按鈕群組 (重試、下載、刪除)
│
├── 統計摘要卡片 (4 個)
│   ├── 處理狀態 (當前步驟、耗時)
│   ├── 信心度 (整體信心度、路由決策)
│   ├── 上傳資訊 (時間、上傳者)
│   └── 來源資訊 (Manual/Outlook/SharePoint)
│
├── 選項卡內容 (Tabs)
│   ├── Tab 1: 文件預覽
│   │   └── 整合 Story 13-1 的 PDFViewer + FieldHighlightOverlay
│   │
│   ├── Tab 2: 提取欄位
│   │   └── 整合 Story 13-2 的 ExtractedFieldsPanel
│   │
│   ├── Tab 3: 處理詳情
│   │   ├── 處理步驟時間軸
│   │   ├── 各步驟耗時統計
│   │   └── 錯誤訊息（如有）
│   │
│   └── Tab 4: 審計日誌
│       ├── 變更歷史時間軸
│       └── 操作記錄列表
│
└── 側邊資訊面板 (Optional - 桌面版)
    ├── 信心度分解詳情
    └── 相關文件推薦
```

### 2.2 核心功能

| 功能 | 優先級 | 說明 |
|------|--------|------|
| PDF 預覽 | P0 | 整合 PDFViewer 組件顯示文件 |
| 欄位高亮 | P0 | 整合 FieldHighlightOverlay 顯示欄位位置 |
| 提取欄位面板 | P0 | 整合 ExtractedFieldsPanel 顯示欄位詳情 |
| 處理時間軸 | P1 | 顯示處理步驟與耗時 |
| 審計日誌 | P1 | 顯示變更歷史 |
| 欄位內聯編輯 | P2 | 允許修正欄位值（審核權限） |
| 實時狀態更新 | P2 | 處理中發票的狀態輪詢 |

### 2.3 狀態處理

| 文件狀態 | 頁面行為 |
|----------|----------|
| PENDING | 顯示等待處理中訊息 |
| PROCESSING | 顯示進度條 + 實時更新 |
| COMPLETED | 顯示完整預覽和結果 |
| FAILED | 顯示錯誤訊息 + 重試按鈕 |
| WAITING_REVIEW | 顯示審核工具列 |

---

## 3. 技術設計

### 3.1 頁面組件結構

```typescript
// src/app/[locale]/(dashboard)/invoices/[id]/page.tsx

interface InvoiceDetailPageProps {
  params: {
    locale: string;
    id: string;
  };
}

export default async function InvoiceDetailPage({ params }: InvoiceDetailPageProps) {
  // Server Component: 獲取初始數據
  const document = await getDocument(params.id);

  return (
    <div className="container py-6">
      <InvoiceDetailHeader document={document} />
      <InvoiceDetailStats document={document} />
      <InvoiceDetailTabs document={document} />
    </div>
  );
}
```

### 3.2 新增組件

| 組件 | 位置 | 說明 |
|------|------|------|
| `InvoiceDetailHeader.tsx` | `features/invoice/` | 詳情頁頭部（標題、狀態、操作） |
| `InvoiceDetailStats.tsx` | `features/invoice/` | 統計摘要卡片 |
| `InvoiceDetailTabs.tsx` | `features/invoice/` | 選項卡容器 |
| `ProcessingTimeline.tsx` | `features/invoice/` | 處理步驟時間軸 |
| `InvoiceAuditLog.tsx` | `features/invoice/` | 審計日誌面板 |

### 3.3 復用現有組件

| 組件 | 來源 | 用途 |
|------|------|------|
| `DynamicPDFViewer` | Epic 13-1 | PDF 文件預覽 |
| `FieldHighlightOverlay` | Epic 13-1 | 欄位位置高亮 |
| `ExtractedFieldsPanel` | Epic 13-2 | 提取欄位面板 |
| `ConfidenceBadge` | `features/confidence/` | 信心度徽章 |
| `DocumentSourceBadge` | `features/document-source/` | 來源徽章 |
| `ProcessingStatus` | `features/invoice/` | 處理狀態 |

### 3.4 API 端點

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/documents/[id]` | GET | 文件詳情 |
| `/api/documents/[id]/progress` | GET | 處理進度 |
| `/api/documents/[id]/trace` | GET | 處理追蹤 |
| `/api/extraction/[id]/fields` | GET | 提取欄位 |
| `/api/confidence/[id]` | GET | 信心度詳情 |
| `/api/documents/[id]/retry` | POST | 重試處理 |

### 3.5 數據獲取策略

```typescript
// 使用 React Query 進行數據獲取
const { data: document, isLoading } = useQuery({
  queryKey: ['document', id],
  queryFn: () => fetchDocument(id),
});

// 處理中狀態自動輪詢
const { data: progress } = useQuery({
  queryKey: ['document-progress', id],
  queryFn: () => fetchProgress(id),
  refetchInterval: document?.status === 'PROCESSING' ? 3000 : false,
});
```

---

## 4. i18n 需求

### 4.1 新增翻譯 Key

在 `messages/{locale}/invoices.json` 中新增：

```json
{
  "detail": {
    "title": "發票詳情",
    "backToList": "返回列表",
    "tabs": {
      "preview": "文件預覽",
      "fields": "提取欄位",
      "processing": "處理詳情",
      "audit": "審計日誌"
    },
    "stats": {
      "status": "處理狀態",
      "confidence": "信心度",
      "uploadInfo": "上傳資訊",
      "source": "來源"
    },
    "timeline": {
      "title": "處理時間軸",
      "step": "步驟",
      "duration": "耗時",
      "status": "狀態"
    },
    "actions": {
      "retry": "重試",
      "download": "下載",
      "delete": "刪除"
    },
    "empty": {
      "noPreview": "無法預覽此文件",
      "noFields": "尚無提取欄位"
    }
  }
}
```

### 4.2 格式化需求

- 日期時間：使用 `formatDateTime()` 和 `formatRelativeTime()`
- 數字：使用 `formatNumber()` 和 `formatPercent()`
- 耗時：使用 `formatDuration()`（需新增）

---

## 5. 驗收標準

### 5.1 功能驗收

- [ ] 可從列表頁點擊進入詳情頁
- [ ] 正確顯示 PDF 預覽（支援翻頁、縮放）
- [ ] 正確顯示欄位高亮（點擊欄位可互動）
- [ ] 正確顯示提取欄位面板（搜尋、篩選、排序）
- [ ] 正確顯示處理時間軸
- [ ] 正確顯示審計日誌
- [ ] 處理中狀態有實時更新
- [ ] 失敗狀態可重試

### 5.2 i18n 驗收

- [ ] 所有文字使用翻譯系統
- [ ] 支援 en / zh-TW / zh-CN 三語言
- [ ] 日期、數字正確格式化

### 5.3 效能驗收

- [ ] 頁面初始載入 < 3 秒
- [ ] PDF 預覽載入 < 2 秒
- [ ] 選項卡切換 < 100ms

### 5.4 無障礙驗收

- [ ] 鍵盤可完整操作
- [ ] 圖片有 alt 屬性
- [ ] 顏色對比符合 WCAG 2.1 AA

---

## 6. 實施計劃

### 6.1 任務分解

| 任務 | 估時 | 依賴 |
|------|------|------|
| 1. 創建頁面基礎結構 | 2h | - |
| 2. 實現 Header 組件 | 2h | 1 |
| 3. 實現 Stats 卡片 | 2h | 1 |
| 4. 實現 Tabs 容器 | 1h | 1 |
| 5. 整合 PDF 預覽 Tab | 3h | 4, 13-1 |
| 6. 整合提取欄位 Tab | 2h | 4, 13-2 |
| 7. 實現處理時間軸 Tab | 3h | 4 |
| 8. 實現審計日誌 Tab | 2h | 4 |
| 9. 新增 i18n 翻譯 | 1h | 2-8 |
| 10. 實時狀態更新 | 2h | 5, 6 |
| 11. 測試與修復 | 2h | all |

**總計**: 約 22 小時

### 6.2 依賴項目

| 依賴 | 狀態 | 說明 |
|------|------|------|
| Story 13-1 | ✅ 已完成 | PDFViewer + FieldHighlightOverlay |
| Story 13-2 | ✅ 已完成 | ExtractedFieldsPanel |
| Epic 8 | ✅ 已完成 | 審計日誌組件 |
| Epic 17 | 🚧 進行中 | i18n 框架已就緒 |

---

## 7. 相關文件

### 7.1 代碼參考

| 文件 | 說明 |
|------|------|
| `src/app/[locale]/(dashboard)/invoices/page.tsx` | 發票列表頁（參考結構） |
| `src/components/features/invoice/` | 現有發票組件 |
| `src/components/features/document-preview/` | PDF 預覽組件 |
| `src/app/api/documents/[id]/route.ts` | 文件詳情 API |

### 7.2 文檔參考

| 文檔 | 說明 |
|------|------|
| `claudedocs/1-planning/epics/epic-13/` | Epic 13 規劃 |
| `.claude/rules/components.md` | 組件開發規範 |
| `.claude/rules/i18n.md` | 國際化規範 |

---

## 8. 風險與緩解

| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| PDF 預覽組件未完全就緒 | 阻塞開發 | 先用 placeholder，後整合 |
| 大型 PDF 載入慢 | 用戶體驗差 | 實現漸進式載入 |
| 欄位座標不準確 | 高亮錯位 | 使用 Story 13-1 的校正算法 |

---

*Story created: 2026-01-18*
*Last updated: 2026-01-18*
