# Git 工作流程和分支策略

## 文檔目的

本文檔定義設計系統遷移項目的 Git 分支管理策略、提交規範、代碼審查流程和回滾機制，確保遷移過程安全、可追溯、可回滾。

---

## 分支架構

### 分支層次結構

```
main (生產分支)
  └── develop (開發主分支)
      └── feature/design-system-migration (遷移主分支)
          ├── poc/design-system-validation (POC 驗證分支)
          ├── phase-1/css-variables (階段 1: CSS 變數系統)
          ├── phase-2/ui-components (階段 2: UI 組件庫)
          │   ├── phase-2.1/core-components (子階段: 核心組件)
          │   ├── phase-2.2/form-components (子階段: 表單組件)
          │   └── phase-2.3/overlay-components (子階段: 浮層組件)
          ├── phase-3/page-migration (階段 3: 頁面遷移)
          │   ├── phase-3.1/auth-pages (子階段: 認證頁面)
          │   ├── phase-3.2/dashboard-pages (子階段: Dashboard)
          │   └── phase-3.3/feature-pages (子階段: 功能頁面)
          └── phase-4/advanced-features (階段 4: 進階功能)
```

---

## 分支說明

### main 分支
- **用途**: 生產環境代碼
- **保護規則**:
  - 禁止直接 push
  - 要求 PR 審查（至少 2 人批准）
  - 要求所有 CI 檢查通過
  - 要求線性歷史（squash merge）
- **合併來源**: 僅接受來自 `develop` 的 PR
- **部署**: 自動部署到 Azure 生產環境

### develop 分支
- **用途**: 開發主分支，集成所有功能
- **保護規則**:
  - 禁止直接 push
  - 要求 PR 審查（至少 1 人批准）
  - 要求 CI 檢查通過
- **合併來源**: 接受來自 feature 分支的 PR
- **部署**: 自動部署到 Azure Staging 環境

### feature/design-system-migration 分支
- **用途**: 設計系統遷移主分支，作為所有遷移工作的基礎
- **生命週期**: POC 開始 → 所有階段完成並驗證通過
- **合併來源**: 接受來自各 phase 分支的 PR
- **合併目標**: 完成後合併到 `develop`

### poc/design-system-validation 分支
- **用途**: POC 驗證專用分支
- **生命週期**: POC 開始 → POC 評估完成
- **合併目標**:
  - 如果 POC 成功 → 合併到 `feature/design-system-migration`
  - 如果 POC 失敗 → 刪除分支

### phase-N/* 分支
- **用途**: 各階段開發分支
- **命名規範**: `phase-{階段編號}/{階段名稱}`
- **生命週期**: 階段開始 → 階段驗收通過
- **合併目標**: `feature/design-system-migration`

### phase-N.M/* 子階段分支
- **用途**: 大階段的細分任務分支
- **命名規範**: `phase-{階段編號}.{子階段編號}/{子階段名稱}`
- **生命週期**: 子任務開始 → 子任務完成
- **合併目標**: 對應的 `phase-N/*` 分支

---

## 分支操作流程

### POC 階段

#### 1. 建立 POC 分支

```bash
# 從 develop 建立遷移主分支
git checkout develop
git pull origin develop
git checkout -b feature/design-system-migration

# 從遷移主分支建立 POC 分支
git checkout -b poc/design-system-validation

# 建立 checkpoint tag
git tag poc-start
git push -u origin poc/design-system-validation
git push origin poc-start
```

#### 2. POC 開發和提交

```bash
# 開發過程中頻繁提交
git add .
git commit -m "feat(poc): implement CSS variable system"

# 推送到遠端
git push origin poc/design-system-validation
```

#### 3. POC 評估和決策

**情況 A: POC 成功 ✅**

```bash
# 1. 合併 POC 到遷移主分支
git checkout feature/design-system-migration
git merge --squash poc/design-system-validation
git commit -m "feat: integrate POC - CSS variables and core components

- Implemented CSS variable system with HSL colors
- Built 8 core UI components (Button, Card, Input, etc.)
- Migrated Dashboard and Login pages successfully
- Performance impact within acceptable range (<10%)

POC Validation Results:
- All technical requirements met ✅
- Performance criteria met ✅
- Developer experience score: 8.5/10 ✅
- Visual improvement rating: ⭐⭐⭐⭐⭐

Ref: POC-EXECUTION-REPORT.md"

# 2. 建立 POC 完成 tag
git tag poc-completed
git push origin feature/design-system-migration
git push origin poc-completed

# 3. 保留 POC 分支作為參考（不刪除）
# POC 分支可用於未來回顧和文檔參考
```

**情況 B: POC 失敗 ❌**

```bash
# 1. 記錄 POC 失敗原因
# 建立 POC-FAILURE-REPORT.md 詳細記錄原因

# 2. 回到 develop 分支
git checkout develop

# 3. 刪除 POC 相關分支和 tags
git branch -D poc/design-system-validation
git branch -D feature/design-system-migration
git push origin --delete poc/design-system-validation
git push origin --delete feature/design-system-migration
git tag -d poc-start
git push origin --delete poc-start

# 4. 評估替代方案（見 POC-VALIDATION-EXECUTION-PLAN.md）
```

---

### Phase 1-4 開發流程

#### Phase 1: CSS 變數系統

```bash
# 1. 建立 Phase 1 分支
git checkout feature/design-system-migration
git pull origin feature/design-system-migration
git checkout -b phase-1/css-variables

# 2. 開發和提交
git add apps/web/src/app/globals.css
git commit -m "feat(phase-1): add complete CSS variable system

- Define all semantic color variables
- Implement light and dark mode support
- Add border radius variables"

git add apps/web/tailwind.config.ts
git commit -m "feat(phase-1): update Tailwind config for design system

- Integrate CSS variables with Tailwind theme
- Add custom color mappings
- Configure borderRadius system"

# 3. 階段完成，建立 PR
git push -u origin phase-1/css-variables

# 在 GitHub 建立 PR: phase-1/css-variables → feature/design-system-migration
# PR 標題: "[Phase 1] CSS Variables System Implementation"
# PR 模板見下文

# 4. PR 審查通過後合併
git checkout feature/design-system-migration
git merge --squash phase-1/css-variables
git commit -m "feat(phase-1): complete CSS variables system ✅

Phase 1 deliverables:
- ✅ CSS variable system (light + dark mode)
- ✅ Tailwind config integration
- ✅ ThemeProvider setup
- ✅ Theme toggle component

Acceptance criteria met:
- All CSS variables working correctly
- Theme switching smooth with no flicker
- TypeScript type checking passed
- No console errors

Ref: PHASE-1-COMPLETION-REPORT.md"

# 5. 建立階段完成 tag
git tag phase-1-completed
git push origin feature/design-system-migration
git push origin phase-1-completed

# 6. 刪除已合併的 phase 分支（可選）
git branch -d phase-1/css-variables
git push origin --delete phase-1/css-variables
```

#### Phase 2: UI 組件庫（含子階段）

**Phase 2.1: 核心組件**

```bash
# 1. 建立 Phase 2 主分支
git checkout feature/design-system-migration
git checkout -b phase-2/ui-components

# 2. 建立 Phase 2.1 子分支
git checkout -b phase-2.1/core-components

# 3. 開發核心組件
git add apps/web/src/components/ui/button.tsx
git commit -m "feat(phase-2.1): add Button component

- Implement CVA variants (default, destructive, outline, etc.)
- Add size variants (sm, default, lg, icon)
- Full TypeScript support with VariantProps
- Unit tests included"

git add apps/web/src/components/ui/card.tsx
git commit -m "feat(phase-2.1): add Card compound components

- Card root component
- CardHeader, CardTitle, CardDescription
- CardContent, CardFooter
- Consistent spacing and styling"

# 繼續開發其他核心組件...

# 4. Phase 2.1 完成，合併到 Phase 2 主分支
git push -u origin phase-2.1/core-components

# 建立 PR: phase-2.1/core-components → phase-2/ui-components
# 審查通過後合併

git checkout phase-2/ui-components
git merge --squash phase-2.1/core-components
git commit -m "feat(phase-2.1): complete core components ✅

Components delivered:
- Button, Card, Badge
- Avatar, Skeleton
- All components fully tested"

git tag phase-2.1-completed
git push origin phase-2/ui-components
git push origin phase-2.1-completed
```

**Phase 2.2 和 2.3 類似流程...**

**Phase 2 完成後合併到主分支:**

```bash
# 所有 Phase 2 子階段完成後
git checkout feature/design-system-migration
git merge --squash phase-2/ui-components
git commit -m "feat(phase-2): complete UI component library ✅

Phase 2 deliverables:
- ✅ 22+ UI components fully implemented
- ✅ All components with TypeScript types
- ✅ Unit tests for all components
- ✅ Storybook documentation (optional)

Sub-phases completed:
- ✅ Phase 2.1: Core components (Button, Card, Badge, etc.)
- ✅ Phase 2.2: Form components (Input, Select, Checkbox, etc.)
- ✅ Phase 2.3: Overlay components (Dialog, Popover, Dropdown, etc.)

Acceptance criteria met:
- All components render correctly
- Light + dark mode support
- Accessibility standards met
- Performance benchmarks passed

Ref: PHASE-2-COMPLETION-REPORT.md"

git tag phase-2-completed
git push origin feature/design-system-migration
git push origin phase-2-completed
```

#### Phase 3 和 Phase 4 遵循相同模式...

---

### 最終合併到 develop

```bash
# 所有 Phase 完成後
git checkout develop
git pull origin develop

# 建立 PR: feature/design-system-migration → develop
# PR 標題: "Design System Migration - Complete Implementation"
# 詳細的 PR description 見下文

# PR 審查通過後合併（使用 squash merge）
git merge --squash feature/design-system-migration
git commit -m "feat: complete design system migration 🎉

Migration Summary:
================
Duration: [實際天數] days
Total commits: [提交數]
Files changed: [文件數]
Lines added/removed: +[增加] -[刪除]

Phases Completed:
-----------------
✅ POC Validation (1.5 days)
✅ Phase 1: CSS Variables System (2.5 days)
✅ Phase 2: UI Component Library (4 days)
✅ Phase 3: Page Migration (6 days)
✅ Phase 4: Advanced Features (3 days)

Key Deliverables:
-----------------
- 22+ production-ready UI components
- Complete CSS variable system (light + dark mode)
- 15+ pages migrated to new design system
- Theme switching functionality
- Comprehensive test coverage (>85%)

Performance Impact:
-------------------
- Bundle size: +12% (within threshold)
- FCP: +5% (within threshold)
- LCP: +7% (within threshold)
- Lighthouse Score: 94 (target: >90) ✅

Quality Metrics:
----------------
- TypeScript: 100% type coverage
- Tests: 87% code coverage
- Accessibility: WCAG 2.1 AA compliant
- Developer experience: 8.7/10

Documentation:
--------------
- Migration guide: DESIGN-SYSTEM-MIGRATION-PLAN.md
- POC report: POC-EXECUTION-REPORT.md
- Phase completion reports: PHASE-{1-4}-COMPLETION-REPORT.md
- Component documentation: UI-COMPONENTS-GUIDE.md

Breaking Changes:
-----------------
None - fully backward compatible migration

Migration completed successfully!
Ref: MIGRATION-FINAL-REPORT.md"

# 建立最終完成 tag
git tag design-system-migration-completed
git push origin develop
git push origin design-system-migration-completed

# 刪除 feature 分支（可選，也可保留作為參考）
# git branch -d feature/design-system-migration
# git push origin --delete feature/design-system-migration
```

---

## 提交訊息規範

### Conventional Commits 格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 規範:

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Type 類型

| Type | 用途 | 範例 |
|------|------|------|
| `feat` | 新功能 | `feat(button): add destructive variant` |
| `fix` | Bug 修復 | `fix(card): correct border radius in dark mode` |
| `docs` | 文檔更新 | `docs(readme): add migration guide` |
| `style` | 代碼格式（不影響邏輯） | `style(button): format with prettier` |
| `refactor` | 重構（不改變功能） | `refactor(input): simplify variant logic` |
| `test` | 測試相關 | `test(button): add unit tests for all variants` |
| `chore` | 構建/工具配置 | `chore(deps): update tailwindcss to v3.4` |
| `perf` | 性能優化 | `perf(card): optimize re-renders` |
| `ci` | CI/CD 配置 | `ci(github): add design system validation workflow` |

### Scope 範圍

**階段級別:**
- `poc` - POC 相關
- `phase-1` - Phase 1 相關
- `phase-2` - Phase 2 相關
- `phase-3` - Phase 3 相關
- `phase-4` - Phase 4 相關

**組件級別:**
- `button`, `card`, `input`, `select`, `dialog` 等具體組件
- `theme` - 主題系統
- `css-vars` - CSS 變數
- `utils` - 工具函數

**功能級別:**
- `dashboard` - Dashboard 頁面
- `auth` - 認證相關頁面
- `budget` - 預算管理頁面
- 等等...

### 提交訊息範例

**好的提交訊息 ✅:**

```
feat(button): implement Button component with CVA

- Add all variants: default, destructive, outline, secondary, ghost, link
- Add size variants: sm, default, lg, icon
- Implement asChild prop with Radix Slot
- Add comprehensive TypeScript types
- Include unit tests

Closes #123
```

```
fix(theme): resolve hydration mismatch in ThemeProvider

The theme toggle was causing hydration errors due to server/client
theme mismatch. Added suppressHydrationWarning to <html> tag and
implemented mounted state check in ThemeToggle component.

Before: Console errors on initial load
After: Clean hydration, no warnings

Fixes #145
```

```
docs(migration): add Phase 2 completion report

Documented all deliverables, acceptance criteria results,
and lessons learned from UI component library implementation.

Ref: PHASE-2-COMPLETION-REPORT.md
```

**不好的提交訊息 ❌:**

```
update files
```

```
fix bug
```

```
wip
```

```
changes
```

---

## Pull Request 規範

### PR 標題格式

```
[階段] 簡潔描述

範例:
[POC] Design System Validation - CSS Variables and Core Components
[Phase 1] CSS Variables System Implementation
[Phase 2.1] Core UI Components (Button, Card, Badge)
[Phase 3] Dashboard and Auth Pages Migration
```

### PR 描述模板

```markdown
## 🎯 目標

[簡述此 PR 的目標和背景]

## 📦 變更內容

### 新增
- [ ] [具體新增內容]
- [ ] [具體新增內容]

### 修改
- [ ] [具體修改內容]
- [ ] [具體修改內容]

### 刪除
- [ ] [具體刪除內容]（如適用）

## ✅ 驗收標準

- [ ] 所有 TypeScript 類型檢查通過
- [ ] 所有單元測試通過 (coverage ≥ 80%)
- [ ] E2E 測試通過（如適用）
- [ ] Lighthouse 性能評分 ≥ 90
- [ ] 無 console 錯誤或警告
- [ ] 亮/暗色主題切換正常
- [ ] 響應式設計在所有斷點正常
- [ ] 無可訪問性（a11y）問題
- [ ] Code review 完成

## 🧪 測試

### 測試範圍
- [ ] 單元測試
- [ ] 整合測試
- [ ] E2E 測試
- [ ] 視覺回歸測試（如適用）

### 測試結果
```bash
[貼上測試執行結果]
```

## 📊 性能影響

| 指標 | 變更前 | 變更後 | 變化 | 狀態 |
|------|--------|--------|------|------|
| Bundle Size (JS) | - | - | - | ✅/⚠️ |
| Bundle Size (CSS) | - | - | - | ✅/⚠️ |
| FCP | - | - | - | ✅/⚠️ |
| LCP | - | - | - | ✅/⚠️ |
| Lighthouse Score | - | - | - | ✅/⚠️ |

## 📸 截圖/錄屏

### 亮色主題
[貼上截圖]

### 暗色主題
[貼上截圖]

### 響應式（如適用）
[貼上截圖]

## 🔗 相關連結

- 相關 Issue: #[issue 編號]
- 設計稿: [Figma 連結]（如適用）
- 文檔: [文檔連結]

## ⚠️ Breaking Changes

[如果有 breaking changes，詳細說明]

## 📝 備註

[任何其他需要審查者注意的事項]

## 🙋 審查者清單

- [ ] @[審查者1] - Code review
- [ ] @[審查者2] - Design review
- [ ] @[審查者3] - QA review（如適用）
```

---

## 代碼審查流程

### 審查檢查清單

#### 代碼品質
- [ ] 代碼遵循項目編碼規範
- [ ] 無重複代碼（DRY 原則）
- [ ] 函數和變數命名清晰且有意義
- [ ] 複雜邏輯有適當註解
- [ ] 無明顯的性能問題
- [ ] 錯誤處理完善

#### TypeScript
- [ ] 無 `any` 類型（除非必要且有註解說明）
- [ ] 所有組件 props 有完整類型定義
- [ ] 類型推斷正確且精確
- [ ] 無類型錯誤或警告

#### 組件設計
- [ ] 組件職責單一
- [ ] Props API 設計合理且一致
- [ ] 正確使用 `forwardRef`（如適用）
- [ ] `displayName` 已設置
- [ ] 可訪問性屬性完整（ARIA）

#### 樣式
- [ ] 使用 CSS 變數而非硬編碼顏色
- [ ] 使用語義化的 Tailwind 類名
- [ ] 正確使用 `cn()` 合併類名
- [ ] 亮/暗色主題都正確顯示
- [ ] 響應式設計實現正確

#### 測試
- [ ] 單元測試覆蓋關鍵邏輯
- [ ] 測試用例有意義且全面
- [ ] 測試可讀性好
- [ ] 無 flaky tests

#### 文檔
- [ ] README 或組件文檔已更新
- [ ] JSDoc 註解完整（如適用）
- [ ] Props 有清晰的說明
- [ ] 使用範例清晰

### 審查回饋規範

**建議使用以下前綴:**

- `[必須修改]` - 阻塞性問題，必須修復才能合併
- `[建議優化]` - 非阻塞性建議，可以考慮改進
- `[問題]` - 需要作者澄清的疑問
- `[讚賞]` - 好的實踐或優秀的代碼

**範例:**

```markdown
[必須修改] button.tsx:45 - 缺少 ARIA label
應該為 icon-only 按鈕添加 sr-only 文字或 aria-label

[建議優化] card.tsx:12 - 可以簡化條件邏輯
目前的三元嵌套可以用 switch 或 object mapping 簡化

[問題] utils.ts:23 - 為什麼使用 setTimeout?
這個 setTimeout 的用途是什麼？是否有替代方案？

[讚賞] input.tsx:50 - 優秀的錯誤處理
Error state 的處理非常完善，考慮周到！
```

---

## 回滾機制

### 分支級別回滾

#### 回滾到某個 tag

```bash
# 查看所有 tags
git tag -l

# 回滾到特定 tag
git checkout phase-1-completed

# 或者從 tag 建立新分支繼續開發
git checkout -b phase-1-hotfix phase-1-completed
```

#### 回滾最近的合併

```bash
# 查看最近的 commits
git log --oneline -10

# 回滾最近一次 merge commit
git revert -m 1 <merge-commit-hash>

# 或者使用 reset（謹慎使用，會改寫歷史）
git reset --hard <commit-before-merge>
```

### 階段級別回滾

**情況: Phase 2 出現重大問題，需要回滾**

```bash
# 1. 查看 Phase 2 之前的 tag
git tag -l

# 輸出:
# poc-completed
# phase-1-completed
# phase-2-completed  <-- 有問題的階段
# phase-2.1-completed

# 2. 從 Phase 1 完成點建立新分支
git checkout phase-1-completed
git checkout -b phase-2/ui-components-v2

# 3. 重新實現 Phase 2（使用不同方法）
# ... 開發工作 ...

# 4. 完成後合併到主分支
git checkout feature/design-system-migration
git merge --squash phase-2/ui-components-v2
git commit -m "feat(phase-2): re-implement UI components (v2)

Previous implementation had [問題描述].
This version uses [新方法說明].

Ref: PHASE-2-REIMPLEMENTATION-REPORT.md"
```

### 緊急回滾到 develop

**情況: 遷移後發現生產環境重大 bug**

```bash
# 1. 在 develop 分支查看歷史
git checkout develop
git log --oneline -20

# 2. 識別遷移前的最後一個 commit
# 假設是 abc1234

# 3. 建立臨時分支保存當前狀態
git branch backup/before-rollback

# 4. 回滾 develop 到遷移前（使用 revert 保持歷史）
git revert <migration-merge-commit-hash>

# 或者使用 reset（改寫歷史，需要 force push）
# git reset --hard abc1234
# git push -f origin develop

# 5. 修復問題後，可以重新應用遷移
```

### 文件級別回滾

**情況: 單個文件出現問題**

```bash
# 從特定 commit 恢復單個文件
git checkout <commit-hash> -- path/to/file.tsx

# 從 staging area 撤銷文件
git restore --staged path/to/file.tsx

# 從最近一次 commit 恢復文件
git restore path/to/file.tsx
```

---

## Checkpoint 和 Snapshot 策略

### 每日 Checkpoints

**每天開發結束前建立 checkpoint:**

```bash
# 1. 提交當天所有工作
git add .
git commit -m "chore: daily checkpoint - [簡述進度]

Progress:
- Completed: [已完成任務]
- In Progress: [進行中任務]
- Next: [下一步計劃]"

# 2. 建立帶日期的 tag
git tag checkpoint-$(date +%Y-%m-%d)
git push origin checkpoint-$(date +%Y-%m-%d)
```

### 階段 Snapshots

**每個階段的關鍵節點建立 snapshot:**

```bash
# 階段開始
git tag phase-2-start
git push origin phase-2-start

# 階段中期
git tag phase-2-midpoint
git push origin phase-2-midpoint

# 階段完成前（準備 PR）
git tag phase-2-pre-merge
git push origin phase-2-pre-merge

# 階段完成後
git tag phase-2-completed
git push origin phase-2-completed
```

### 自動化 Snapshot 腳本

**建立自動化腳本 `scripts/create-snapshot.sh`:**

```bash
#!/bin/bash

# Usage: ./scripts/create-snapshot.sh "snapshot description"

DESCRIPTION=$1
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TAG_NAME="snapshot-${TIMESTAMP}"

if [ -z "$DESCRIPTION" ]; then
  echo "Error: Please provide a snapshot description"
  echo "Usage: ./scripts/create-snapshot.sh \"description\""
  exit 1
fi

# Commit current changes
git add .
git commit -m "chore: snapshot - ${DESCRIPTION}"

# Create tag
git tag -a "${TAG_NAME}" -m "${DESCRIPTION}"

# Push to remote
git push origin HEAD
git push origin "${TAG_NAME}"

echo "✅ Snapshot created: ${TAG_NAME}"
echo "📝 Description: ${DESCRIPTION}"
```

**使用方式:**

```bash
chmod +x scripts/create-snapshot.sh
./scripts/create-snapshot.sh "Before refactoring Button component"
```

---

## 分支清理策略

### 已合併分支清理

```bash
# 列出所有已合併到 main 的分支
git branch --merged main

# 刪除已合併的本地分支（排除 main, develop）
git branch --merged main | grep -v "\*\|main\|develop" | xargs -n 1 git branch -d

# 刪除已合併的遠端分支
git branch -r --merged main | grep -v "\*\|main\|develop" | sed 's/origin\///' | xargs -n 1 git push origin --delete
```

### 定期清理策略

**每個 Phase 完成後:**
- ✅ 保留 Phase 主分支 (phase-N/*)
- ✅ 保留所有 tags
- ❌ 刪除子階段分支 (phase-N.M/*)（已合併且不需要參考）

**整個遷移完成後:**
- ✅ 保留 `feature/design-system-migration` 作為歷史參考
- ✅ 保留所有 tags（poc-*, phase-*-completed）
- ❌ 可選擇性刪除所有 phase 分支（如果不需要參考）

---

## Git Hooks

### Pre-commit Hook

**自動檢查代碼品質:**

建立 `.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "🔍 Running pre-commit checks..."

# 1. TypeScript 類型檢查
echo "1️⃣ TypeScript type checking..."
pnpm typecheck --filter=web
if [ $? -ne 0 ]; then
  echo "❌ TypeScript errors found. Commit aborted."
  exit 1
fi

# 2. ESLint
echo "2️⃣ Running ESLint..."
pnpm lint --filter=web
if [ $? -ne 0 ]; then
  echo "❌ ESLint errors found. Commit aborted."
  exit 1
fi

# 3. Prettier 格式檢查
echo "3️⃣ Checking code formatting..."
pnpm format:check --filter=web
if [ $? -ne 0 ]; then
  echo "❌ Code formatting issues found. Run 'pnpm format' to fix."
  exit 1
fi

# 4. 單元測試（僅針對變更的文件）
echo "4️⃣ Running tests for changed files..."
pnpm test --filter=web --bail --findRelatedTests $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx)$' | tr '\n' ' ')
if [ $? -ne 0 ]; then
  echo "❌ Tests failed. Commit aborted."
  exit 1
fi

echo "✅ All pre-commit checks passed!"
exit 0
```

**安裝:**

```bash
chmod +x .git/hooks/pre-commit
```

### Commit-msg Hook

**驗證提交訊息格式:**

建立 `.git/hooks/commit-msg`:

```bash
#!/bin/bash

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Conventional Commits 格式驗證
PATTERN="^(feat|fix|docs|style|refactor|test|chore|perf|ci)(\(.+\))?: .{1,}"

if ! echo "$COMMIT_MSG" | grep -qE "$PATTERN"; then
  echo "❌ Invalid commit message format!"
  echo ""
  echo "Commit message must follow Conventional Commits format:"
  echo "  <type>(<scope>): <subject>"
  echo ""
  echo "Examples:"
  echo "  feat(button): add destructive variant"
  echo "  fix(theme): resolve hydration mismatch"
  echo "  docs(readme): update migration guide"
  echo ""
  echo "Valid types: feat, fix, docs, style, refactor, test, chore, perf, ci"
  exit 1
fi

echo "✅ Commit message format valid"
exit 0
```

**安裝:**

```bash
chmod +x .git/hooks/commit-msg
```

---

## CI/CD 整合

### GitHub Actions Workflows

#### 1. PR 驗證 Workflow

**文件: `.github/workflows/pr-validation.yml`**

```yaml
name: PR Validation

on:
  pull_request:
    branches:
      - develop
      - feature/design-system-migration
      - 'phase-*'

jobs:
  validation:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: TypeScript type check
        run: pnpm typecheck

      - name: Lint
        run: pnpm lint

      - name: Unit tests
        run: pnpm test --filter=web --coverage

      - name: Build
        run: pnpm build --filter=web

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  lighthouse:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Build
        run: pnpm build --filter=web

      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v10
        with:
          urls: |
            http://localhost:3000
            http://localhost:3000/dashboard
            http://localhost:3000/login
          uploadArtifacts: true
          temporaryPublicStorage: true

  bundle-size:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Build
        run: pnpm build --filter=web

      - name: Analyze bundle size
        uses: AndresJz/bundle-size-action@v1
        with:
          build-script: build
          directory: apps/web/.next
```

#### 2. Visual Regression Testing

**文件: `.github/workflows/visual-regression.yml`**

```yaml
name: Visual Regression Tests

on:
  pull_request:
    branches:
      - feature/design-system-migration
      - 'phase-*'
    paths:
      - 'apps/web/src/components/**'
      - 'apps/web/src/app/**'

jobs:
  visual-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Build Storybook
        run: pnpm build-storybook --filter=web

      - name: Run Chromatic
        uses: chromaui/action@v1
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          buildScriptName: build-storybook
```

---

## 最佳實踐總結

### ✅ DO (應該做)

1. **頻繁提交**: 每完成一個小功能就提交
2. **清晰的提交訊息**: 遵循 Conventional Commits
3. **小的 PR**: 每個 PR 聚焦單一目標（≤ 500 行變更）
4. **定期 Pull**: 每天開始工作前 pull 最新代碼
5. **測試後提交**: 確保所有測試通過再提交
6. **Code Review**: 每個 PR 至少一人審查
7. **建立 Checkpoints**: 關鍵節點建立 tags
8. **文檔同步**: 代碼變更時同步更新文檔

### ❌ DON'T (不應該做)

1. **直接 Push 到主分支**: 永遠不要繞過 PR 流程
2. **Force Push**: 避免 `git push -f`（除非絕對必要）
3. **大量文件一次提交**: 避免 "mega commits"
4. **籠統的提交訊息**: 避免 "fix", "update", "changes"
5. **未測試就提交**: 提交前確保代碼可運行
6. **忽略 Code Review 意見**: 認真對待審查回饋
7. **刪除歷史 Tags**: Tags 是重要的回滾點
8. **混合多個功能**: 一個 PR 只做一件事

---

## 快速參考

### 常用命令

```bash
# 建立新分支
git checkout -b <branch-name>

# 切換分支
git checkout <branch-name>

# 查看狀態
git status

# 查看分支
git branch -a

# 查看 tags
git tag -l

# 暫存所有變更
git add .

# 提交
git commit -m "feat(scope): description"

# 推送
git push origin <branch-name>

# Pull 最新代碼
git pull origin <branch-name>

# 合併分支 (squash)
git merge --squash <branch-name>

# 建立 tag
git tag <tag-name>

# 推送 tag
git push origin <tag-name>

# 查看歷史
git log --oneline --graph --all

# 回滾到某個 commit
git reset --hard <commit-hash>

# Revert 某個 commit
git revert <commit-hash>
```

---

## 結論

本 Git 工作流程和分支策略確保設計系統遷移過程:
- ✅ **安全**: 每個階段可獨立回滾
- ✅ **可追溯**: 完整的提交歷史和 tags
- ✅ **可協作**: 清晰的分支結構和 PR 流程
- ✅ **高品質**: 自動化檢查和代碼審查
- ✅ **可維護**: 標準化的提交訊息和文檔

遵循本策略可以最大程度降低遷移風險，確保代碼庫的穩定性和可維護性。
