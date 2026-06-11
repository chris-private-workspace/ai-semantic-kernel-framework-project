# FEAT-006: Project Summary Tab - 實施計劃

> **建立日期**: 2025-12-05
> **狀態**: 📋 設計中
> **預計工時**: 3-4 天

---

## 1. 開發階段

### Phase 1: 數據模型擴展 (0.5 天)

#### 任務清單
- [ ] 1.1 更新 `schema.prisma` 添加 Project 新欄位
- [ ] 1.2 新增 `ProjectChargeOutOpCo` 中間表
- [ ] 1.3 更新 `OperatingCompany` 模型反向關係
- [ ] 1.4 執行 `pnpm db:generate` 生成 Prisma Client
- [ ] 1.5 執行 `pnpm db:migrate` 創建遷移
- [ ] 1.6 驗證本地資料庫 Schema

#### 輸出物
- `packages/db/prisma/schema.prisma` (更新)
- `packages/db/prisma/migrations/[timestamp]_feat_006_project_summary_fields/` (新增)

---

### Phase 2: API 開發 (1 天)

#### 任務清單
- [ ] 2.1 更新 `project.ts` 的 create/update input schema
- [ ] 2.2 實現 `project.getProjectSummary` API
- [ ] 2.3 實現 `project.getProjectCategories` API
- [ ] 2.4 更新 `project.getById` 包含新關係
- [ ] 2.5 處理 `chargeOutOpCos` 多對多關係的 CRUD
- [ ] 2.6 單元測試（如有時間）

#### 輸出物
- `packages/api/src/routers/project.ts` (更新)

#### API 實現細節

```typescript
// 2.2 getProjectSummary 返回結構
interface ProjectSummaryResult {
  categorySummary: {
    categoryId: string;
    categoryName: string;
    budgetTotal: number;
    projectCount: number;
  }[];
  detailData: {
    opCoId: string;
    opCoName: string;
    categories: {
      categoryId: string;
      categoryName: string;
      projects: {
        id: string;
        name: string;
        description: string | null;
        approvedBudget: number | null;
        projectCategory: string | null;
        projectType: string;
        expenseType: string;
        probability: string;
        team: string | null;
        personInCharge: string | null;
      }[];
      subtotal: number;
    }[];
    subtotal: number;
  }[];
  grandTotal: {
    budgetTotal: number;
    projectCount: number;
  };
}
```

---

### Phase 3: 前端組件開發 (1.5 天)

#### 任務清單
- [ ] 3.1 創建 `components/summary/SummaryTabs.tsx`
- [ ] 3.2 創建 `components/project-summary/ProjectSummaryFilters.tsx`
- [ ] 3.3 創建 `components/project-summary/ProjectSummaryCategoryGrid.tsx`
- [ ] 3.4 創建 `components/project-summary/ProjectSummaryDetailGrid.tsx`
- [ ] 3.5 創建 `components/project-summary/index.ts` 導出
- [ ] 3.6 更新 `components/project/ProjectForm.tsx` 添加新欄位

#### 輸出物
- `apps/web/src/components/summary/` (新增目錄)
- `apps/web/src/components/project-summary/` (新增目錄)
- `apps/web/src/components/project/ProjectForm.tsx` (更新)

---

### Phase 4: 頁面整合 (0.5 天)

#### 任務清單
- [ ] 4.1 重構 `om-summary/page.tsx` 添加 Tab 結構
- [ ] 4.2 整合 ProjectSummary 組件
- [ ] 4.3 實現 Tab 切換狀態管理
- [ ] 4.4 添加 URL query param 支援 (`?tab=project`)

#### 輸出物
- `apps/web/src/app/[locale]/om-summary/page.tsx` (更新)

---

### Phase 5: I18N 和測試 (0.5 天)

#### 任務清單
- [ ] 5.1 添加 `zh-TW.json` 翻譯鍵
- [ ] 5.2 添加 `en.json` 翻譯鍵
- [ ] 5.3 執行 `pnpm validate:i18n` 驗證
- [ ] 5.4 手動測試所有功能
- [ ] 5.5 修復發現的問題

#### 輸出物
- `apps/web/src/messages/zh-TW.json` (更新)
- `apps/web/src/messages/en.json` (更新)

---

## 2. 文件變更清單

### 後端 (packages/)

| 檔案路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `packages/db/prisma/schema.prisma` | 更新 | 新增 Project 欄位和 ProjectChargeOutOpCo |
| `packages/api/src/routers/project.ts` | 更新 | 新增 API 和更新 schema |

### 前端 (apps/web/)

| 檔案路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `apps/web/src/components/summary/` | 新增 | Tab 組件目錄 |
| `apps/web/src/components/project-summary/` | 新增 | Project Summary 組件目錄 |
| `apps/web/src/components/project/ProjectForm.tsx` | 更新 | 新增表單欄位 |
| `apps/web/src/app/[locale]/om-summary/page.tsx` | 更新 | 重構為 Tab 結構 |
| `apps/web/src/messages/zh-TW.json` | 更新 | 新增翻譯 |
| `apps/web/src/messages/en.json` | 更新 | 新增翻譯 |

### 測試

| 檔案路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `packages/api/src/routers/project.test.ts` | 新增/更新 | API 測試（可選） |

---

## 3. 依賴關係

```
Phase 1 (Schema)
    ↓
Phase 2 (API)
    ↓
Phase 3 (Components) ←──→ Phase 5 (I18N) [可並行]
    ↓
Phase 4 (Page Integration)
    ↓
Phase 5 (Testing)
```

---

## 4. 風險評估

### 高風險
| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 無 | - | - |

### 中風險
| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Azure Schema 同步問題 | 部署後功能異常 | 使用 Health API 診斷，提前測試 |
| 多對多關係 CRUD 複雜 | 開發時間增加 | 參考現有模式，逐步實現 |

### 低風險
| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| I18N 鍵重複 | 翻譯顯示錯誤 | 執行 validate:i18n 檢查 |

---

## 5. 測試計劃

### 單元測試
- [ ] API: `getProjectSummary` 返回正確數據結構
- [ ] API: `getProjectCategories` 返回唯一值
- [ ] API: Project CRUD 包含新欄位

### 整合測試
- [ ] Tab 切換正常工作
- [ ] 篩選器功能正常
- [ ] 數據正確分組和計算

### 手動測試清單
- [ ] 創建新 Project 包含所有新欄位
- [ ] 編輯 Project 更新新欄位
- [ ] Project Summary Tab 顯示正確數據
- [ ] 篩選器過濾結果正確
- [ ] Category Grid 匯總計算正確
- [ ] Detail Grid 分組顯示正確
- [ ] 響應式設計（mobile/tablet/desktop）
- [ ] 中英文切換顯示正確

---

## 6. 部署計劃

### 本地測試完成後
1. 執行 `pnpm lint` 和 `pnpm typecheck`
2. 提交代碼到 Git
3. 根據 SITUATION-7 部署到 Azure 公司環境
4. 使用 Health API 驗證 Schema 同步
5. 在 Azure 環境進行 E2E 測試

### Azure 部署前檢查清單
- [ ] 本地所有測試通過
- [ ] Schema 遷移已創建
- [ ] 新 API 已實現並測試
- [ ] I18N 翻譯已完成
- [ ] 無 TypeScript/ESLint 錯誤

---

## 7. 回滾計劃

如果部署後發現嚴重問題：

1. **Schema 回滾**: 新欄位都是可選的，不影響現有功能
2. **UI 回滾**: Tab 可快速隱藏，回到純 OM Summary
3. **API 回滾**: 新 API 獨立，不影響現有 API

---

**最後更新**: 2025-12-05
**作者**: AI Assistant
