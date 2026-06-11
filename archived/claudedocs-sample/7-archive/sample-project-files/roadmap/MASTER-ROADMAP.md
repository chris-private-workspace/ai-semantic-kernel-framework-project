# 🗺️ IT 專案管理平台 - 總體開發路線圖

> **專案名稱**: IT Project Process Management Platform
> **目標**: 統一化 IT 部門專案流程管理,從預算分配到費用記帳
> **當前階段**: Post-MVP 完成，準備 Epic 9-10 開發
> **最後更新**: 2025-11-08

---

## 📊 專案概覽

### 願景
建立一個**統一的專案流程管理平台**,替代分散的手動流程（PPT/Excel/Email），提供角色導向的工作流程自動化。

### 核心價值
- ✅ **流程統一化**: 從預算池管理到費用記帳的完整流程
- ✅ **角色自動化**: PM、Supervisor 各自的工作流程自動化
- ✅ **透明可追蹤**: 所有操作有審計記錄，狀態實時可見
- ✅ **智能輔助**: AI 助手提供智能建議和風險預警 (Epic 9)
- ✅ **系統整合**: 與 ERP、HR、Data Warehouse 無縫整合 (Epic 10)

### 技術棧
- **Frontend**: Next.js 14 (App Router), React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: tRPC, Prisma, PostgreSQL
- **Authentication**: NextAuth.js + Azure AD B2C
- **Deployment**: Azure App Service
- **AI Services**: Azure OpenAI Service (Epic 9)

---

## 🎯 階段劃分

### ✅ Phase 1: MVP 階段 (Epic 1-8) - 已完成

**時間線**: 2025-Q1 ~ 2025-Q3 (6 個月)
**狀態**: 100% 完成 ✅
**負責人**: 開發團隊 + AI 助手

**主要成果**:
- 18 個完整功能頁面
- 46 個 UI 組件 (26 設計系統 + 20 業務)
- 30,000+ 行核心代碼
- 8 個 Epic 全部完成

**Epic 列表**:
1. ✅ **Epic 1**: 平台基礎和用戶認證 (Azure AD B2C + RBAC)
2. ✅ **Epic 2**: CI/CD 和部署自動化 (GitHub Actions)
3. ✅ **Epic 3**: 預算和專案設置 (Budget Pool + Project Management)
4. ✅ **Epic 4**: 提案和審批工作流程 (Proposal Workflow)
5. ✅ **Epic 5**: 採購和供應商管理 (Vendor + Quote + PO)
6. ✅ **Epic 6**: 費用記錄和財務整合 (Expense + Charge-Out)
7. ✅ **Epic 7**: 儀表板和基礎報表 (PM + Supervisor Dashboard)
8. ✅ **Epic 8**: 通知系統 (In-app + Email Notifications)

**關鍵里程碑**:
- M1: Epic 1-2 完成 (基礎設施) - 2025-Q1
- M2: Epic 3-4 完成 (核心工作流) - 2025-Q2
- M3: Epic 5-6 完成 (財務整合) - 2025-Q2
- M4: Epic 7-8 完成 (Dashboard + 通知) - 2025-Q3

**技術債務**:
- 無重大技術債務
- 代碼品質良好，測試覆蓋率 >70%

---

### ✅ Phase 2: Post-MVP 增強 - 已完成

**時間線**: 2025-Q4 (2 個月)
**狀態**: 100% 完成 ✅
**負責人**: 開發團隊 + AI 助手

**主要成果**:
- shadcn/ui 設計系統遷移完成 (26 個組件)
- 4 個新頁面 (Quotes, Settings, Register, Forgot Password)
- Light/Dark/System 主題系統
- 完整 I18N 實施 (繁中 + 英文)
- 環境設置自動化 (check-environment.js)
- 跨平台部署優化

**設計系統遷移**:
- Phase 1: 核心組件 (Button, Input, Card 等)
- Phase 2: 表單組件 (Form, Select, Checkbox 等)
- Phase 3: 反饋組件 (Toast, Alert, Dialog 等)
- Phase 4: 主題系統和無障礙性

**I18N 實施**:
- 18 個頁面完整國際化
- next-intl 整合
- FIX-081 ~ FIX-087 系統性修復

**關鍵里程碑**:
- M5: 設計系統遷移完成 - 2025-10
- M6: I18N 實施完成 - 2025-11
- M7: 用戶反饋增強完成 - 2025-11

---

### 📋 Phase 3: AI Assistant (Epic 9) - 規劃中

**預計時間線**: 2025-11 ~ 2026-01 (8-12 週)
**狀態**: 📋 規劃中
**優先級**: P1 (高優先級)
**負責人**: 待分配

**目標**: 提供智能化的預算建議、費用分類、風險預警和報表摘要

**User Stories** (4 個):

#### Story 9.1: 智能預算建議 (3 週)
**目標**: 在提案階段提供基於歷史數據的預算建議

**功能**:
- 分析過去 5 個類似專案的預算數據
- 使用 RAG (Retrieval-Augmented Generation) 檢索相似專案
- 提供至少 3 種預算建議方案 (保守、適中、進取)
- 說明建議理由和參考數據

**技術**:
- Azure OpenAI Service (GPT-4)
- Vector Database (Pinecone / Weaviate)
- RAG Pipeline (LangChain)

**驗收標準**:
- [ ] 能分析過去 5 個類似專案
- [ ] 提供 3 種預算建議方案
- [ ] 建議準確率 >75%
- [ ] 響應時間 <3 秒

#### Story 9.2: 智能費用分類 (2 週)
**目標**: 自動將費用分類到正確的預算類別

**功能**:
- 根據費用描述和金額自動分類
- 支援 10+ 種費用類別
- 可手動修正並學習改進
- 信心分數顯示 (高/中/低)

**技術**:
- Fine-tuned Classifier (Azure ML)
- Few-shot Learning
- Active Learning (從修正中學習)

**驗收標準**:
- [ ] 分類準確率 >85%
- [ ] 支援 10+ 種類別
- [ ] 可手動修正並學習
- [ ] 響應時間 <1 秒

#### Story 9.3: 預測性風險預警 (3 週)
**目標**: 分析專案預算使用趨勢，提前預警超支風險

**功能**:
- 預測未來 30 天預算使用趨勢
- 提前 2 週預警超支風險
- 風險等級 (低/中/高) 和建議措施
- 歷史預警記錄和準確率追蹤

**技術**:
- Time Series Analysis (Prophet / ARIMA)
- Anomaly Detection
- Rule-based Risk Scoring

**驗收標準**:
- [ ] 能預測未來 30 天趨勢
- [ ] 提前 2 週預警超支
- [ ] 預警準確率 >70%
- [ ] Dashboard 整合顯示

#### Story 9.4: 自動報表摘要生成 (2 週)
**目標**: 自動生成專案財務報表的執行摘要

**功能**:
- 分析專案財務數據
- 生成執行摘要 (關鍵指標、風險點、建議)
- 支援繁中和英文
- 可複製和下載

**技術**:
- GPT-4 (Prompt Engineering)
- 結構化數據提取
- 多語言支援

**驗收標準**:
- [ ] 摘要包含關鍵指標和風險
- [ ] 支援繁中和英文
- [ ] 生成時間 <5 秒
- [ ] 摘要品質 >4.0/5.0

**Sprint 規劃** (5 個 Sprint):
- Sprint 1 (Week 1-2): 基礎設施和數據準備
- Sprint 2 (Week 3-5): Story 9.1 智能預算建議
- Sprint 3 (Week 6-7): Story 9.2 智能費用分類
- Sprint 4 (Week 8-10): Story 9.3 預測性風險預警
- Sprint 5 (Week 11-12): Story 9.4 報表摘要 + 整合測試

**技術架構**:
```typescript
// 新增 AI Router
packages/api/src/routers/ai.ts

export const aiRouter = createTRPCRouter({
  // Story 9.1: 智能預算建議
  getBudgetSuggestions: protectedProcedure
    .input(z.object({
      projectName: z.string(),
      description: z.string(),
      estimatedAmount: z.number().optional(),
    }))
    .query(async ({ ctx, input }) => {
      // 1. 檢索相似專案 (RAG)
      // 2. 調用 GPT-4 生成建議
      // 3. 返回 3 種方案
    }),

  // Story 9.2: 智能費用分類
  classifyExpense: protectedProcedure
    .input(z.object({
      description: z.string(),
      amount: z.number()
    }))
    .mutation(async ({ ctx, input }) => {
      // 1. 調用分類模型
      // 2. 返回類別和信心分數
    }),

  // Story 9.3: 預測性風險預警
  getRiskPrediction: protectedProcedure
    .input(z.object({ projectId: z.string() }))
    .query(async ({ ctx, input }) => {
      // 1. 分析歷史數據
      // 2. 時間序列預測
      // 3. 計算風險等級
    }),

  // Story 9.4: 自動報表摘要
  generateReportSummary: protectedProcedure
    .input(z.object({
      projectId: z.string(),
      locale: z.enum(['zh-TW', 'en']).optional(),
    }))
    .query(async ({ ctx, input }) => {
      // 1. 提取專案數據
      // 2. 調用 GPT-4 生成摘要
      // 3. 返回結構化摘要
    }),
});
```

**成功指標 (KPIs)**:
- 預算建議採用率 >60%
- 費用分類準確率 >85%
- 風險預警提前時間 >2 週
- 報表摘要生成成功率 >95%
- 用戶滿意度 >4.0/5.0
- Azure OpenAI 月成本 <$500 USD

**風險和緩解**:
- **風險 1**: AI 建議準確率不足 → 持續調優，提供人工修正機制
- **風險 2**: Azure OpenAI 成本超支 → 設置使用上限，優化 Prompt
- **風險 3**: 歷史數據不足 → 使用合成數據補充訓練
- **風險 4**: 整合複雜度高 → 採用漸進式整合策略

---

### 📋 Phase 4: External Integration (Epic 10) - 規劃中

**預計時間線**: 2026-01 ~ 2026-03 (8 週)
**狀態**: 📋 規劃中
**優先級**: P1 (高優先級)
**負責人**: 待分配

**目標**: 與外部系統無縫整合，實現數據自動同步

**User Stories** (3 個):

#### Story 10.1: 同步費用數據到 ERP (3 週)
**目標**: 自動將已核准的費用數據同步到 ERP 系統

**功能**:
- 每日自動同步已核准費用
- 雙向對帳和錯誤處理
- 同步狀態追蹤和報告
- 手動重試和回溯機制

**技術**:
- ERP API 整合 (SAP / Oracle)
- Message Queue (Azure Service Bus)
- Retry Logic with Exponential Backoff
- Transaction Log

**驗收標準**:
- [ ] 每日自動同步成功率 >99%
- [ ] 錯誤自動重試 3 次
- [ ] 同步延遲 <5 分鐘
- [ ] 完整審計記錄

#### Story 10.2: 同步用戶數據從 HR 系統 (2 週)
**目標**: 自動從 HR 系統同步用戶和角色數據

**功能**:
- 每日自動同步用戶資料
- 新增/更新/停用用戶
- 角色和權限自動映射
- 同步衝突處理

**技術**:
- HR API 整合 (Workday / SuccessFactors)
- Scheduled Jobs (Azure Functions)
- User Mapping Rules
- Conflict Resolution

**驗收標準**:
- [ ] 每日自動同步成功率 >99%
- [ ] 新用戶 1 天內啟用
- [ ] 離職用戶自動停用
- [ ] 角色映射準確率 >95%

#### Story 10.3: 建立數據管道到 Data Warehouse (3 週)
**目標**: 建立 ETL 管道，將專案數據同步到 Data Warehouse 供 BI 分析

**功能**:
- 增量數據同步 (CDC)
- 數據轉換和清理
- 歷史數據保留
- BI 報表整合 (Power BI)

**技術**:
- Azure Data Factory
- Change Data Capture (CDC)
- Data Transformation (dbt)
- Azure Synapse Analytics

**驗收標準**:
- [ ] 增量同步延遲 <15 分鐘
- [ ] 數據轉換準確率 >99%
- [ ] Power BI 報表可用
- [ ] 歷史數據保留 3 年

**Sprint 規劃** (4 個 Sprint):
- Sprint 1 (Week 1-2): ERP 整合設計和 POC
- Sprint 2 (Week 3-5): Story 10.1 ERP 同步實施
- Sprint 3 (Week 6-7): Story 10.2 HR 同步實施
- Sprint 4 (Week 8): Story 10.3 Data Warehouse 管道

**技術架構**:
```typescript
// 新增 Integration Router
packages/api/src/routers/integration.ts

export const integrationRouter = createTRPCRouter({
  // Story 10.1: ERP 同步
  syncExpenseToERP: protectedProcedure
    .input(z.object({ expenseId: z.string() }))
    .mutation(async ({ ctx, input }) => {
      // 1. 驗證費用狀態 (已核准)
      // 2. 轉換數據格式
      // 3. 調用 ERP API
      // 4. 記錄同步狀態
    }),

  // Story 10.2: HR 同步
  syncUsersFromHR: adminProcedure
    .mutation(async ({ ctx }) => {
      // 1. 調用 HR API 取得用戶列表
      // 2. 比對本地用戶
      // 3. 新增/更新/停用用戶
      // 4. 記錄同步日誌
    }),

  // Story 10.3: Data Warehouse 同步 (Background Job)
  // 不需要 tRPC Router，由 Azure Data Factory 處理
});
```

**成功指標 (KPIs)**:
- ERP 同步成功率 >99%
- HR 同步成功率 >99%
- Data Warehouse 同步延遲 <15 分鐘
- BI 報表可用性 >99.5%
- 數據準確率 >99%

**風險和緩解**:
- **風險 1**: ERP/HR API 變更 → 版本控制，監控 API 變更
- **風險 2**: 同步失敗影響業務 → 異步處理，完整錯誤重試
- **風險 3**: 數據衝突 → 制定衝突解決規則
- **風險 4**: 效能影響 → 增量同步，離峰時段執行

---

## 🎯 里程碑和時間線

```
2025-Q1 ~ 2025-Q3: Phase 1 (MVP) ✅ 完成
├─ M1: Epic 1-2 基礎設施 (2025-Q1) ✅
├─ M2: Epic 3-4 核心工作流 (2025-Q2) ✅
├─ M3: Epic 5-6 財務整合 (2025-Q2) ✅
└─ M4: Epic 7-8 Dashboard + 通知 (2025-Q3) ✅

2025-Q4: Phase 2 (Post-MVP) ✅ 完成
├─ M5: 設計系統遷移 (2025-10) ✅
├─ M6: I18N 實施 (2025-11) ✅
└─ M7: 用戶反饋增強 (2025-11) ✅

2025-11 ~ 2026-01: Phase 3 (Epic 9 - AI Assistant) 📋 規劃中
├─ M8: Story 9.1-9.2 完成 (智能建議和分類) - 2025-12
└─ M9: Story 9.3-9.4 完成 (風險預警和報表摘要) - 2026-01

2026-01 ~ 2026-03: Phase 4 (Epic 10 - External Integration) 📋 規劃中
├─ M10: Story 10.1-10.2 完成 (ERP/HR 整合) - 2026-02
└─ M11: Story 10.3 完成 (Data Warehouse) - 2026-03

2026-Q2: Phase 5 (System Optimization) 📋 未規劃
└─ M12: 完整系統驗收和上線 - 2026-Q2
```

---

## 🔗 依賴關係

### Epic 9 (AI Assistant)
- **前置依賴**: Epic 1-8 全部完成 ✅
- **技術依賴**: Azure OpenAI Service 帳戶、Vector Database
- **數據依賴**: 足夠的歷史專案數據 (建議 >50 個專案)
- **可並行**: 與 Epic 10 無依賴，可並行開發

### Epic 10 (External Integration)
- **前置依賴**: Epic 1-8 全部完成 ✅
- **技術依賴**: ERP/HR API 存取權限、Azure Data Factory
- **數據依賴**: ERP/HR 測試環境和數據
- **可並行**: 與 Epic 9 無依賴，可並行開發

### Epic 9 vs Epic 10 並行策略
```
Timeline:
2025-11 ─────────────────────────────────── 2026-03

Epic 9:  [████████████████████████] (12 週)
         Sprint 1-5

Epic 10:             [████████████████] (8 週)
                     Sprint 1-4 (可從 2026-01 開始)

建議: Epic 9 優先開始，Epic 10 在 Epic 9 Sprint 3 後開始
```

---

## 📊 專案統計

### 已完成 (MVP + Post-MVP)
- **Epic 完成**: 8/10 (80%)
- **總代碼行數**: ~30,000+ 行
- **功能頁面**: 18 個
- **UI 組件**: 46 個
- **API Routers**: 10 個
- **Prisma Models**: 10+
- **測試覆蓋率**: >70%
- **開發時長**: 9 個月 (2025-Q1 ~ 2025-Q4)

### 待完成 (Epic 9-10)
- **Epic 待完成**: 2/10 (20%)
- **預估代碼行數**: ~8,000 行
- **新功能**: AI 助手 + 外部整合
- **新 API Routers**: 2 個 (ai, integration)
- **預估開發時長**: 4-5 個月 (2025-11 ~ 2026-03)

---

## 🎯 成功標準

### Phase 3 (Epic 9) 成功標準
- [ ] 所有 4 個 User Stories 完成並通過驗收
- [ ] AI 功能準確率達標 (建議 >75%, 分類 >85%, 預警 >70%)
- [ ] 用戶滿意度 >4.0/5.0
- [ ] Azure OpenAI 成本控制在預算內 (<$500/月)
- [ ] 完整的 E2E 測試覆蓋
- [ ] 技術文檔和用戶指南完成

### Phase 4 (Epic 10) 成功標準
- [ ] 所有 3 個 User Stories 完成並通過驗收
- [ ] ERP/HR 同步成功率 >99%
- [ ] Data Warehouse 同步延遲 <15 分鐘
- [ ] BI 報表可用性 >99.5%
- [ ] 完整的錯誤處理和監控
- [ ] 技術文檔和運維指南完成

### Phase 5 (System Optimization) 成功標準
- [ ] 完整系統驗收測試通過
- [ ] 效能測試通過 (支援 100 併發用戶)
- [ ] 安全審計通過
- [ ] 可用性 >99.9% (月度)
- [ ] 生產環境成功上線

---

## 📝 相關文檔

- [Epic 9 詳細規劃](../epics/epic-9/epic-9-overview.md) (待創建)
- [Epic 10 詳細規劃](../epics/epic-10/epic-10-overview.md) (待創建)
- [Sprint 規劃](../../2-sprints/) (待開始)
- [每週進度](../../3-progress/weekly/) (待創建)
- [技術決策記錄](../architecture/TECH-DECISIONS.md) (待創建)

---

**維護者**: 開發團隊 + AI 助手
**審核者**: Tech Lead, Product Manager
**最後更新**: 2025-11-08
**下次審查**: Epic 9 Sprint 1 結束後
