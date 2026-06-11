# 🔧 情況2: 開發新功能/修復前準備

> **使用時機**: 準備開發新功能或修復舊功能前
> **目標**: 驗證架構支援，制定實施計劃
> **適用場景**: 開始新功能開發、接到新任務、設計階段

---

## 📋 Prompt 模板

```markdown
我需要 [開發新功能 / 修復舊功能]: [功能/Bug 描述]

請幫我:

1. 快速回顧專案現況
   - 閱讀 `claudedocs/1-planning/features/` 了解進行中的功能
   - 檢查當前 Git 分支和最近提交
   - 閱讀最新的每週進度報告

2. 驗證架構支援
   - 閱讀 `docs/02-architecture/architecture.md`
   - 檢查 `prisma/schema.prisma` 相關數據模型
   - 檢查 `src/app/api/` 相關 API
   - 檢查 `src/app/[locale]/(dashboard)/` 相關頁面
   - 檢查 `messages/` 是否需要新增翻譯

3. 制定實施計劃
   - 識別需要修改的文件
   - 評估架構變更需求
   - 列出前置任務和依賴
   - 估算工作量

4. 創建任務清單
   - 使用 TodoWrite 創建任務清單
   - 分解為可執行的小任務
   - 標註優先級和依賴關係

請用中文回答。
```

---

## 🤖 AI 執行步驟

### 階段 1: 理解需求 (3 分鐘)
```bash
# 讀取相關文檔
Bash: ls claudedocs/1-planning/features/
Read: claudedocs/3-progress/weekly/[最新].md
Read: claudedocs/3-progress/daily/[最新].md

# 檢查 Git 狀態
Bash: git status
Bash: git log --oneline -5
Bash: git branch
```

### 階段 2: 驗證架構 (5 分鐘)
```bash
# 檢查數據模型
Read: prisma/schema.prisma

# 檢查相關 API
Grep: pattern="相關關鍵字" path="src/app/api/"

# 檢查相關服務
Grep: pattern="相關關鍵字" path="src/services/"

# 檢查相關頁面/組件
Glob: pattern="**/*[相關名稱]*.tsx"
Read: [找到的相關文件]
```

### 階段 3: 制定計劃 (5 分鐘)
```markdown
# 實施計劃

## 需求分析
- **功能**: [描述]
- **功能編號**: FEAT-XXX / FIX-XXX
- **驗收標準**: [列出]

## 架構評估
- **數據模型**: ✅ 支援 / ⚠️ 需修改 / ❌ 需新增
- **API**: ✅ 可用 / ⚠️ 需擴展 / ❌ 需新增
- **服務層**: ✅ 可用 / ⚠️ 需擴展 / ❌ 需新增
- **前端組件**: ✅ 可重用 / ⚠️ 需調整 / ❌ 需新建

## 三層映射系統影響評估
- **Universal Mapping**: [是否需要更新通用映射]
- **Forwarder Override**: [是否涉及特定 Forwarder 映射]
- **LLM Classification**: [是否需要調整 AI 分類邏輯]

## 信心度路由影響
- **AUTO_APPROVE (≥90%)**: [影響評估]
- **QUICK_REVIEW (70-89%)**: [影響評估]
- **FULL_REVIEW (<70%)**: [影響評估]

## 文件變更清單
### 資料庫
- [ ] `prisma/schema.prisma` - [變更描述]
- [ ] 遷移文件 - [變更描述]

### 服務層
- [ ] `src/services/xxx.service.ts` - [變更描述]

### API 層
- [ ] `src/app/api/xxx/route.ts` - [變更描述]

### 前端
- [ ] `src/app/[locale]/(dashboard)/xxx/page.tsx` - [變更描述]
- [ ] `src/components/features/xxx/` - [變更描述]
- [ ] `src/hooks/use-xxx.ts` - [變更描述]

### 國際化 (i18n)
- [ ] `messages/en/xxx.json` - [新增/更新翻譯]
- [ ] `messages/zh-TW/xxx.json` - [新增/更新翻譯]
- [ ] `messages/zh-CN/xxx.json` - [新增/更新翻譯]

### 測試
- [ ] `tests/xxx.test.ts` - [測試計劃]

## 工作量估算
- **資料庫**: X 小時
- **服務層**: X 小時
- **API 層**: X 小時
- **前端開發**: X 小時
- **測試**: X 小時
- **總計**: X 小時 (~X 天)

## 風險評估
- ⚠️ [識別的風險] → [緩解措施]
```

---

## 📁 功能規劃目錄結構

如果是新功能，需建立功能規劃目錄：

```
claudedocs/1-planning/features/
├── FEAT-001-功能名稱/
│   ├── 01-requirements.md      # 需求規格
│   ├── 02-technical-design.md  # 技術設計
│   ├── 03-implementation-plan.md # 實施計劃
│   └── 04-progress.md          # 進度追蹤
├── FEAT-002-另一功能/
│   └── ...
```

如果是 Bug 修復，記錄到：
```
claudedocs/4-changes/bug-fixes/FIX-XXX-描述.md
```

如果是功能增強，記錄到：
```
claudedocs/4-changes/feature-changes/CHANGE-XXX-描述.md
```

---

## 📐 開發規範提醒

### 代碼品質
```bash
# 開發完成後必須執行
npm run type-check   # TypeScript 檢查
npm run lint         # ESLint 檢查
```

### 文件頭部註釋（必須）
```typescript
/**
 * @fileoverview [功能描述]
 * @module src/services/[module-name]
 * @since FEAT-XXX [功能名稱]
 * @lastModified YYYY-MM-DD
 */
```

### 禁止事項
- ❌ 使用 `any` 類型
- ❌ 跳過錯誤處理
- ❌ 硬編碼敏感資訊
- ❌ 擅自偏離設計規格（參考 `.claude/rules/technical-obstacles.md`）

---

## ✅ 驗收標準

開發前準備完成後，應該確認：

- [ ] 已理解功能需求或問題描述
- [ ] 已驗證架構支援程度
- [ ] 已識別需要修改的文件
- [ ] 已評估三層映射系統影響
- [ ] 已評估 i18n 翻譯需求（需新增哪些翻譯）
- [ ] 已創建 TodoWrite 任務清單
- [ ] 已建立功能規劃目錄（新功能）或變更記錄（修復/增強）

---

## 🔗 相關文檔

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md)
- [情況3: 舊功能進階/修正](./SITUATION-3-FEATURE-ENHANCEMENT.md)
- [情況4: 新功能開發](./SITUATION-4-NEW-FEATURE-DEV.md)
- [情況5: 保存進度](./SITUATION-5-SAVE-PROGRESS.md)

### 架構文檔
- [CLAUDE.md](../../../CLAUDE.md) - 開發規範
- [系統架構](../../../docs/02-architecture/architecture.md)
- [PRD 產品需求](../../../docs/01-planning/prd/prd.md)
- [技術障礙處理](../../../.claude/rules/technical-obstacles.md)

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2026-01-18
**版本**: 1.2
