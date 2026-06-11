# FEAT-003: O&M Summary 頁面 - 實施計劃

> **建立日期**: 2025-11-29
> **預估總工時**: 3-4 天
> **狀態**: 📋 待開始

---

## 1. 開發階段總覽

| Phase | 任務 | 預估時間 | 依賴 |
|-------|------|----------|------|
| Phase 0 | 規劃準備 | 0.5 天 | - |
| Phase 1 | 後端 API | 1 天 | Phase 0 |
| Phase 2 | 前端組件 | 1.5 天 | Phase 1 |
| Phase 3 | I18N 和樣式 | 0.5 天 | Phase 2 |
| Phase 4 | 測試和優化 | 0.5 天 | Phase 3 |

---

## 2. Phase 0: 規劃準備 (0.5 天)

### 2.1 文檔準備 ✅
- [x] 建立功能目錄 `FEAT-003-om-summary-page/`
- [x] 撰寫 `01-requirements.md`
- [x] 撰寫 `02-technical-design.md`
- [x] 撰寫 `03-implementation-plan.md`
- [ ] 初始化 `04-progress.md`

### 2.2 環境確認
- [ ] 確認現有 O&M API 可用
- [ ] 確認 OpCo API 可用
- [ ] 確認測試數據存在

---

## 3. Phase 1: 後端 API (1 天)

### 3.1 新增 API Procedure

**任務清單：**

| # | 任務 | 預估時間 | 檔案 |
|---|------|----------|------|
| 1.1 | 定義 Zod 輸入 Schema | 15 min | `omExpense.ts` |
| 1.2 | 定義返回類型 | 30 min | `omExpense.ts` |
| 1.3 | 實現 `getSummary` procedure | 2 hr | `omExpense.ts` |
| 1.4 | 實現跨年度比較邏輯 | 1 hr | `omExpense.ts` |
| 1.5 | 實現分組匯總邏輯 | 1 hr | `omExpense.ts` |
| 1.6 | 實現計算邏輯 (Change %) | 30 min | `omExpense.ts` |
| 1.7 | 錯誤處理 | 30 min | `omExpense.ts` |

### 3.2 開發順序

```bash
# Step 1: 定義 Schema 和類型
Edit: packages/api/src/routers/omExpense.ts
# 新增 getSummaryInput schema
# 新增返回類型定義

# Step 2: 實現 procedure
Edit: packages/api/src/routers/omExpense.ts
# 實現完整的 getSummary procedure

# Step 3: 測試 API
Bash: pnpm dev
# 使用 tRPC Panel 或 Postman 測試
```

### 3.3 驗收標準
- [ ] API 可正確查詢當前年度和上年度數據
- [ ] 分組邏輯正確（Category → OpCo → Items）
- [ ] 計算邏輯正確（總和、百分比）
- [ ] 空數據處理正確
- [ ] TypeScript 類型完整

---

## 4. Phase 2: 前端組件 (1.5 天)

### 4.1 組件開發

**任務清單：**

| # | 任務 | 預估時間 | 檔案 |
|---|------|----------|------|
| 2.1 | 建立組件目錄 | 5 min | `components/om-summary/` |
| 2.2 | 實現 `OMSummaryFilters` | 1.5 hr | `OMSummaryFilters.tsx` |
| 2.3 | 實現 `OMSummaryCategoryGrid` | 2 hr | `OMSummaryCategoryGrid.tsx` |
| 2.4 | 實現 `OMSummaryDetailGrid` | 3 hr | `OMSummaryDetailGrid.tsx` |
| 2.5 | 建立組件導出 | 10 min | `index.ts` |
| 2.6 | 實現主頁面 | 2 hr | `page.tsx` |
| 2.7 | 更新側邊欄導航 | 30 min | `Sidebar.tsx` |

### 4.2 開發順序

```bash
# Step 1: 建立目錄結構
Bash: mkdir -p apps/web/src/components/om-summary

# Step 2: 建立 Filters 組件
Write: apps/web/src/components/om-summary/OMSummaryFilters.tsx

# Step 3: 建立 CategoryGrid 組件
Write: apps/web/src/components/om-summary/OMSummaryCategoryGrid.tsx

# Step 4: 建立 DetailGrid 組件
Write: apps/web/src/components/om-summary/OMSummaryDetailGrid.tsx

# Step 5: 建立導出
Write: apps/web/src/components/om-summary/index.ts

# Step 6: 建立頁面
Bash: mkdir -p apps/web/src/app/[locale]/om-summary
Write: apps/web/src/app/[locale]/om-summary/page.tsx

# Step 7: 更新導航
Edit: apps/web/src/components/layout/Sidebar.tsx
```

### 4.3 驗收標準
- [ ] 過濾器正常工作（年度、OpCo、Category）
- [ ] 類別匯總表格顯示正確
- [ ] 明細表格階層結構正確
- [ ] Loading 狀態顯示
- [ ] 空數據狀態顯示
- [ ] 導航可正常訪問頁面

---

## 5. Phase 3: I18N 和樣式 (0.5 天)

### 5.1 I18N

**任務清單：**

| # | 任務 | 預估時間 | 檔案 |
|---|------|----------|------|
| 3.1 | 新增 zh-TW 翻譯 | 30 min | `zh-TW.json` |
| 3.2 | 新增 en 翻譯 | 30 min | `en.json` |
| 3.3 | 驗證翻譯完整性 | 15 min | - |

### 5.2 樣式優化

| # | 任務 | 預估時間 | 檔案 |
|---|------|----------|------|
| 3.4 | 數字格式化（金額）| 30 min | `utils.ts` |
| 3.5 | 百分比顏色區分 | 15 min | 組件 |
| 3.6 | 響應式調整 | 1 hr | 組件 |

### 5.3 驗收標準
- [ ] 中英文切換正常
- [ ] 金額顯示千分位
- [ ] 正增長綠色、負增長紅色
- [ ] 平板尺寸顯示正常

---

## 6. Phase 4: 測試和優化 (0.5 天)

### 6.1 功能測試

| # | 測試項目 | 預期結果 |
|---|----------|----------|
| 4.1 | 預設載入 | 顯示當前年度所有數據 |
| 4.2 | 年度切換 | 數據正確更新 |
| 4.3 | OpCo 多選 | 分組顯示正確 |
| 4.4 | Category 過濾 | 只顯示選中類別 |
| 4.5 | 重置按鈕 | 恢復預設狀態 |
| 4.6 | 空數據 | 顯示友好提示 |

### 6.2 邊界情況

| # | 情況 | 處理 |
|---|------|------|
| 4.7 | 上年度無數據 | Change% 顯示 "-" |
| 4.8 | 上年度實際為 0 | Change% 顯示 "N/A" |
| 4.9 | 只選一個 OpCo | 不顯示 OpCo 分組標題 |
| 4.10 | 大量數據 | 考慮分頁或虛擬滾動 |

### 6.3 最終檢查
- [ ] ESLint 無錯誤
- [ ] TypeScript 無錯誤
- [ ] 控制台無警告
- [ ] 頁面載入時間 < 2秒

---

## 7. 風險和依賴

### 7.1 風險

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 數據量大導致載入慢 | 用戶體驗差 | 實現分頁或虛擬滾動 |
| 跨年度比對邏輯複雜 | 開發時間增加 | 先實現基本版本，後優化 |
| 多選組合過多 | UI 混亂 | 限制最多選擇數量 |

### 7.2 依賴

| 依賴項 | 狀態 | 備註 |
|--------|------|------|
| OMExpense API | ✅ 已存在 | 需新增 getSummary |
| OpCo API | ✅ 已存在 | getAll 可用 |
| shadcn/ui 組件 | ✅ 已安裝 | Table, Accordion, Select |
| 測試數據 | ⚠️ 待確認 | 需確保有跨年度數據 |

---

## 8. 交付物清單

### 8.1 後端
- [ ] `packages/api/src/routers/omExpense.ts` - getSummary procedure

### 8.2 前端
- [ ] `apps/web/src/components/om-summary/OMSummaryFilters.tsx`
- [ ] `apps/web/src/components/om-summary/OMSummaryCategoryGrid.tsx`
- [ ] `apps/web/src/components/om-summary/OMSummaryDetailGrid.tsx`
- [ ] `apps/web/src/components/om-summary/index.ts`
- [ ] `apps/web/src/app/[locale]/om-summary/page.tsx`

### 8.3 I18N
- [ ] `apps/web/src/messages/zh-TW.json` - omSummary 命名空間
- [ ] `apps/web/src/messages/en.json` - omSummary 命名空間

### 8.4 文檔
- [x] `01-requirements.md`
- [x] `02-technical-design.md`
- [x] `03-implementation-plan.md`
- [ ] `04-progress.md`

---

**下一步**: [04-progress.md](./04-progress.md) - 開始開發並記錄進度
