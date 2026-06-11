# FEAT-010: 實施計劃

> **建立日期**: 2025-12-12
> **最後更新**: 2025-12-12

## 1. 開發階段概覽

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Schema 擴展 (SITUATION-3)                             │
│  └── 1.1 新增 5 個欄位到 Project 模型                            │
│  └── 1.2 Prisma generate + migrate                              │
│  └── 1.3 Project 表單頁新增欄位輸入                              │
│  └── 1.4 Project 列表頁新增 FY 過濾                              │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: 後端 API 開發 (SITUATION-4)                            │
│  └── 2.1 新增 importProjects procedure                          │
│  └── 2.2 新增 getByProjectCodes procedure (重複檢測用)           │
│  └── 2.3 擴展 getAll 支援 fiscalYear 過濾                        │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: 前端導入頁面開發 (SITUATION-4)                         │
│  └── 3.1 建立 /project-data-import 頁面                         │
│  └── 3.2 Excel 解析邏輯                                         │
│  └── 3.3 預覽表格組件                                            │
│  └── 3.4 導入確認和結果顯示                                      │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: i18n 和測試 (SITUATION-4)                              │
│  └── 4.1 新增翻譯鍵 (en + zh-TW)                                 │
│  └── 4.2 側邊欄新增導航項目                                      │
│  └── 4.3 測試導入 100 筆資料                                     │
│  └── 4.4 修復問題                                                │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 詳細任務分解

### Phase 1: Schema 擴展 (預估 2-3 小時)

| 任務 | 文件 | 說明 | 時間 |
|------|------|------|------|
| 1.1 | `packages/db/prisma/schema.prisma` | 新增 5 個欄位到 Project | 15 min |
| 1.2 | - | `pnpm db:generate` + `pnpm db:push` | 10 min |
| 1.3 | `apps/web/src/components/project/ProjectForm.tsx` | 新增欄位輸入控件 | 45 min |
| 1.4 | `apps/web/src/app/[locale]/projects/page.tsx` | 新增 FY 過濾器 | 30 min |
| 1.5 | `packages/api/src/routers/project.ts` | 擴展 getAll 和 create/update | 30 min |

### Phase 2: 後端 API 開發 (預估 2-3 小時)

| 任務 | 文件 | 說明 | 時間 |
|------|------|------|------|
| 2.1 | `packages/api/src/routers/project.ts` | 新增 importProjects | 60 min |
| 2.2 | `packages/api/src/routers/project.ts` | 新增 getByProjectCodes | 20 min |
| 2.3 | `packages/api/src/routers/project.ts` | 擴展 getAll fiscalYear 過濾 | 15 min |

### Phase 3: 前端導入頁面開發 (預估 3-4 小時)

| 任務 | 文件 | 說明 | 時間 |
|------|------|------|------|
| 3.1 | `apps/web/src/app/[locale]/project-data-import/page.tsx` | 導入頁面 | 90 min |
| 3.2 | 同上 | Excel 解析邏輯 | 30 min |
| 3.3 | 同上 | 預覽表格 + 錯誤標示 | 45 min |
| 3.4 | 同上 | 導入確認 + 結果顯示 | 30 min |

### Phase 4: i18n 和測試 (預估 1-2 小時)

| 任務 | 文件 | 說明 | 時間 |
|------|------|------|------|
| 4.1 | `apps/web/src/messages/*.json` | 新增翻譯鍵 | 30 min |
| 4.2 | `apps/web/src/components/layout/Sidebar.tsx` | 新增導航 | 15 min |
| 4.3 | - | 測試導入 100 筆 | 30 min |
| 4.4 | - | 修復問題 | 30 min |

## 3. 工作量估算

| Phase | 預估時間 | 複雜度 |
|-------|----------|--------|
| Phase 1: Schema 擴展 | 2-3 小時 | 中 |
| Phase 2: 後端 API | 2-3 小時 | 中 |
| Phase 3: 前端導入頁面 | 3-4 小時 | 高 |
| Phase 4: i18n 和測試 | 1-2 小時 | 低 |
| **總計** | **8-12 小時** | - |

## 4. 依賴關係

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
   │           │           │
   │           │           └── 需要 API 完成
   │           └── 需要 Schema 完成
   └── 獨立，可先開始
```

## 5. 文件變更清單

### 後端
- [ ] `packages/db/prisma/schema.prisma` - Project 模型新增欄位
- [ ] `packages/api/src/routers/project.ts` - 新增/擴展 procedures

### 前端
- [ ] `apps/web/src/app/[locale]/project-data-import/page.tsx` - 新增導入頁面
- [ ] `apps/web/src/app/[locale]/projects/page.tsx` - 新增 FY 過濾
- [ ] `apps/web/src/components/project/ProjectForm.tsx` - 新增欄位輸入
- [ ] `apps/web/src/components/layout/Sidebar.tsx` - 新增導航

### i18n
- [ ] `apps/web/src/messages/en.json` - 新增翻譯
- [ ] `apps/web/src/messages/zh-TW.json` - 新增翻譯

## 6. 風險和緩解

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| BudgetCategory 名稱不匹配 | 高 | 中 | 預覽時顯示警告，允許選擇 |
| 大量資料導入超時 | 中 | 高 | Transaction timeout 設為 5 分鐘 |
| 欄位映射錯誤 | 中 | 中 | 詳細的預覽和驗證 |
| 現有專案 projectCode 衝突 | 低 | 高 | 預覽時明確顯示更新項目 |

## 7. 測試計劃

### 7.1 單元測試
- [ ] importProjects API 驗證邏輯
- [ ] Excel 解析邏輯
- [ ] 重複檢測邏輯

### 7.2 整合測試
- [ ] 完整導入流程 (100 筆)
- [ ] FY 過濾功能
- [ ] 新欄位 CRUD

### 7.3 用戶測試
- [ ] 導入流程易用性
- [ ] 錯誤訊息清晰度
- [ ] 預覽準確性

## 8. 開發順序建議

```
Day 1 (4-5 小時):
├── Phase 1.1-1.2: Schema 擴展 + Prisma
├── Phase 1.5: API 擴展 (getAll, create, update)
└── Phase 2.1-2.3: importProjects API

Day 2 (4-5 小時):
├── Phase 3.1-3.4: 前端導入頁面
├── Phase 1.3-1.4: Project 表單和列表頁調整
└── Phase 4.1-4.4: i18n + 測試
```

## 9. Checklist

### 開始前
- [ ] 確認 Excel 模板結構
- [ ] 確認現有 BudgetCategory 資料
- [ ] 確認現有 Currency 資料
- [ ] 確認預設 Manager/Supervisor/BudgetPool

### 完成後
- [ ] 所有新欄位可正常 CRUD
- [ ] FY 過濾正常運作
- [ ] 導入 100 筆測試資料成功
- [ ] i18n 驗證通過
- [ ] TypeScript 編譯無錯誤
