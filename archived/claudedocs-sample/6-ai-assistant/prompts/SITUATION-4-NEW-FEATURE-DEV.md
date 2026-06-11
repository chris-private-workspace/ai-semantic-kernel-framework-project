# 🆕 情況4: 新功能開發

> **使用時機**: 對話進行中，正在開發全新功能
> **目標**: 系統化開發，符合架構標準
> **適用場景**: 新模組開發、新功能實施

---

## 📋 Prompt 模板

```markdown
我正在開發新功能: [功能名稱]

根據: [用戶需求 / 設計文檔 / 功能規劃]

請幫我:

1. 建立功能規劃目錄
   - 在 claudedocs/1-planning/features/ 建立 FEAT-XXX-[功能名稱] 目錄
   - 建立 01-requirements.md (需求規格)
   - 建立 02-technical-design.md (技術設計)
   - 建立 03-implementation-plan.md (實施計劃)
   - 建立 04-progress.md (進度追蹤)

2. 確認規劃文檔
   - 閱讀 docs/02-architecture/architecture.md 確認架構
   - 閱讀 docs/01-planning/prd/prd.md 確認需求
   - 確認驗收標準

3. 系統化開發
   - 資料庫: 數據模型 → Migration
   - 後端: 服務層 → API → 測試
   - 前端: 組件 → 頁面 → 整合
   - 國際化: 翻譯文件 → 組件整合
   - 使用 TodoWrite 追蹤進度

4. 遵循最佳實踐
   - 參考現有實現模式
   - 使用 shadcn/ui 組件
   - 遵循三層映射系統設計
   - 遵循信心度路由機制
   - 遵循 i18n 國際化規範（參考 `.claude/rules/i18n.md`）

5. 記錄開發過程
   - 更新 04-progress.md
   - 記錄技術決策

請用中文溝通。
```

---

## 🤖 AI 執行流程

### Phase 0: 規劃準備 (必須先執行)

```bash
# 1. 確認功能編號（查看現有 FEAT 編號）
Bash: ls claudedocs/1-planning/features/

# 2. 建立功能目錄結構
Bash: mkdir -p claudedocs/1-planning/features/FEAT-XXX-功能名稱

# 3. 建立規劃文檔
Write: claudedocs/1-planning/features/FEAT-XXX-功能名稱/01-requirements.md
Write: claudedocs/1-planning/features/FEAT-XXX-功能名稱/02-technical-design.md
Write: claudedocs/1-planning/features/FEAT-XXX-功能名稱/03-implementation-plan.md
Write: claudedocs/1-planning/features/FEAT-XXX-功能名稱/04-progress.md
```

**功能目錄結構範例：**
```
claudedocs/1-planning/features/
├── FEAT-001-功能名稱/
│   ├── 01-requirements.md      # 需求規格
│   ├── 02-technical-design.md  # 技術設計
│   ├── 03-implementation-plan.md # 實施計劃
│   └── 04-progress.md          # 進度追蹤
├── FEAT-002-另一功能/
│   └── ...
└── FEAT-003-新功能/            # 新功能
    └── ...
```

**文檔內容指引：**

| 文檔 | 內容 |
|------|------|
| `01-requirements.md` | 功能概述、用戶需求、功能需求、驗收標準 |
| `02-technical-design.md` | 數據模型、API 設計、組件設計、技術架構 |
| `03-implementation-plan.md` | 開發階段、任務分解、依賴關係 |
| `04-progress.md` | 開發日誌、完成狀態、問題記錄、測試結果 |

---

### Phase 1: 資料庫開發
```bash
# 1. 數據模型（如需新增或修改）
Edit: prisma/schema.prisma
Bash: npx prisma generate
Bash: npx prisma migrate dev --name [migration-name]

# 2. 更新類型定義
Edit: src/types/index.ts

# 3. 更新 Seed（如需要）
Edit: prisma/seed.ts
Bash: npm run db:seed

# 4. 更新進度
Edit: claudedocs/1-planning/features/FEAT-XXX/04-progress.md
TodoWrite: 標記資料庫任務完成
```

### Phase 2: 後端開發
```bash
# 1. 服務層開發
Write: src/services/新功能.service.ts
Edit: src/services/index.ts (更新導出)

# 2. API Router
Write: src/app/api/新功能/route.ts

# 3. 驗證 Schema
Write: src/validations/新功能.validation.ts

# 4. 代碼品質檢查
Bash: npm run type-check
Bash: npm run lint

# 5. 更新進度
Edit: claudedocs/1-planning/features/FEAT-XXX/04-progress.md
TodoWrite: 標記後端任務完成
```

### Phase 3: 前端開發
```bash
# 1. 組件開發（使用 useTranslations）
Write: src/components/features/新功能/Component.tsx
Write: src/components/features/新功能/index.ts

# 2. 自定義 Hook
Write: src/hooks/use-新功能.ts

# 3. 頁面開發（注意 [locale] 路由）
Write: src/app/[locale]/(dashboard)/新功能/page.tsx

# 4. 國際化翻譯（必須同步更新三個語言）
Write: messages/en/新功能.json
Write: messages/zh-TW/新功能.json
Write: messages/zh-CN/新功能.json

# 5. 測試
Bash: npm run type-check
Bash: npm run lint
Bash: npm run dev (手動測試)

# 6. 更新進度
Edit: claudedocs/1-planning/features/FEAT-XXX/04-progress.md
TodoWrite: 標記前端任務完成
```

---

## 📐 開發標準 Checklist

### 規劃階段
- [ ] 功能目錄已建立 (FEAT-XXX-功能名稱/)
- [ ] 01-requirements.md 已完成
- [ ] 02-technical-design.md 已完成
- [ ] 03-implementation-plan.md 已完成
- [ ] 04-progress.md 已初始化

### 資料庫標準
- [ ] Prisma 模型遵循命名規範
- [ ] Migration 已成功執行
- [ ] Seed 資料已更新（如需要）

### 後端標準
- [ ] 服務層使用標準 JSDoc 註釋
- [ ] API 使用 Zod 驗證
- [ ] 錯誤處理完整（RFC 7807 格式）
- [ ] 三層映射系統邏輯正確
- [ ] 信心度路由機制正確

### 前端標準
- [ ] 使用 TypeScript 嚴格模式
- [ ] 使用 shadcn/ui 組件
- [ ] 響應式設計
- [ ] Loading 和 Error 狀態處理
- [ ] 使用 React Query 進行資料獲取

### 國際化 (i18n) 標準
- [ ] 所有使用者可見文字使用 useTranslations
- [ ] 翻譯文件同步更新（en, zh-TW, zh-CN）
- [ ] 使用 `@/i18n/routing` 的 Link 和 Router
- [ ] 日期/數字/貨幣使用格式化工具

### 代碼品質
- [ ] ESLint 無錯誤
- [ ] TypeScript 無錯誤
- [ ] 註解完整（複雜邏輯）

---

## 📁 功能文檔模板

### 01-requirements.md 模板
```markdown
# FEAT-XXX: [功能名稱]

> **建立日期**: YYYY-MM-DD
> **狀態**: 📋 設計中 / 🚧 開發中 / ✅ 完成
> **優先級**: High / Medium / Low

## 1. 功能概述

### 1.1 背景
[說明為什麼需要這個功能]

### 1.2 目標
[說明功能要達成的目標]

## 2. 功能需求

### 2.1 用戶故事
作為 [用戶角色]，我希望 [做什麼]，以便 [達成什麼目的]

### 2.2 功能列表
- [ ] 功能點 1
- [ ] 功能點 2

## 3. 驗收標準

### 3.1 功能驗收
- [ ] [驗收條件 1]
- [ ] [驗收條件 2]

### 3.2 技術驗收
- [ ] TypeScript 檢查通過
- [ ] ESLint 檢查通過
- [ ] 遵循三層映射系統設計

### 3.3 用戶體驗
- [ ] 響應式設計
- [ ] Loading 狀態處理
- [ ] Error 狀態處理

## 4. 相關文檔
- [系統架構](../../../docs/02-architecture/architecture.md)
- [PRD](../../../docs/01-planning/prd/prd.md)
```

### 04-progress.md 模板
```markdown
# FEAT-XXX: [功能名稱] - 開發進度

## 📊 整體進度
- [ ] Phase 0: 規劃準備
- [ ] Phase 1: 資料庫開發
- [ ] Phase 2: 後端開發
- [ ] Phase 3: 前端開發

## 📝 開發日誌

### YYYY-MM-DD
**完成項目:**
- [完成的項目]

**遇到問題:**
- [問題描述]

**下一步:**
- [下一步計劃]

## 🐛 問題追蹤
| 問題 | 狀態 | 解決方案 |
|------|------|----------|
| [問題描述] | 🔴/🟡/✅ | [解決方案] |

## ✅ 測試結果
- [ ] TypeScript 檢查通過
- [ ] ESLint 檢查通過
- [ ] 功能測試通過

---
*最後更新: YYYY-MM-DD*
```

---

## ✅ 驗收標準

功能開發完成後，應該確認：

- [ ] 所有 Phase 任務完成
- [ ] TypeScript 檢查通過
- [ ] ESLint 檢查通過
- [ ] 功能驗收標準全部滿足
- [ ] 代碼包含標準 JSDoc 註釋
- [ ] 04-progress.md 已更新完成狀態

---

## 🔗 相關文檔

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md)
- [情況2: 開發前準備](./SITUATION-2-FEATURE-DEV-PREP.md)
- [情況3: 舊功能進階/修正](./SITUATION-3-FEATURE-ENHANCEMENT.md)
- [情況5: 保存進度](./SITUATION-5-SAVE-PROGRESS.md)

### 開發規範
- [CLAUDE.md](../../../CLAUDE.md) - 開發規範
- [系統架構](../../../docs/02-architecture/architecture.md)
- [技術障礙處理](../../../.claude/rules/technical-obstacles.md)

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2026-01-18
**版本**: 1.2
