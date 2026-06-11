# CHANGE-007: /forwarders → /companies 路徑重構

> **變更類型**: Feature Change / 路徑重構
> **影響範圍**: 系統級別
> **預估文件數**: 64+ 個文件
> **風險等級**: 中高
> **狀態**: ✅ 已完成

---

## 1. 變更概述

將系統中所有 `/forwarders` 路徑統一改為 `/companies`，包括：
- 頁面路由 (UI)
- API 端點
- 組件引用
- 導航配置

### 背景

- 原始設計使用「Forwarder（貨代商）」命名
- REFACTOR-001 已開始將內部模型重命名為「Company（公司）」
- 但 URL 路徑仍使用 `/forwarders`，造成命名不一致

---

## 2. 影響範圍統計

| 類別 | 數量 | 動作 |
|------|------|------|
| 頁面路由 | 4 | 目錄遷移 |
| API 端點 | 11 | 目錄遷移 |
| 組件文件 | 15+ | 更新引用 |
| Hooks | 2 | 已 deprecated，維持 |
| 型別定義 | 1 | 維持（內部使用） |
| 服務層 | 12+ | 更新 API 調用 |
| 其他引用 | 20+ | 更新路徑引用 |
| **總計** | **64+** | |

---

## 3. 衝突分析

### ⚠️ 重要發現：/api/companies 已存在

現有 `/api/companies/` 端點：
```
src/app/api/companies/route.ts
src/app/api/companies/[id]/route.ts
src/app/api/companies/[id]/activate/route.ts
src/app/api/companies/[id]/deactivate/route.ts
src/app/api/companies/check-code/route.ts
src/app/api/companies/list/route.ts
```

### ✅ 已確認的差異

| 項目 | `/api/forwarders` | `/api/companies` |
|------|-------------------|------------------|
| 來源 | Epic 2 原始實現 | REFACTOR-001 重構 |
| 服務層 | `forwarder.service.ts` | `company.service.ts` |
| 類型支援 | 僅 Forwarder | 多種 (FORWARDER, EXPORTER, CARRIER) |
| Schema | `ForwardersQuerySchema` | `CompaniesQuerySchema` |
| Logo 上傳 | ✅ 支援 | ❓ 需確認 |

### 獨有端點分析

**僅存在於 `/api/forwarders`**：
- `/api/forwarders/identify` - 識別 Forwarder
- `/api/forwarders/[id]/rules` - 規則列表
- `/api/forwarders/[id]/rules/[ruleId]` - 規則詳情
- `/api/forwarders/[id]/stats` - 統計資料
- `/api/forwarders/[id]/documents` - 文件列表

**重複端點**（兩邊都有）：
- `/route.ts` (列表 + 創建)
- `/[id]/route.ts` (詳情)
- `/[id]/activate/route.ts`
- `/[id]/deactivate/route.ts`
- `/check-code/route.ts`
- `/list/route.ts`

### 遷移決策

**保留 `/api/companies`** 作為主要端點，因為：
1. 是 REFACTOR-001 的新實現
2. 支援多種公司類型
3. 代碼更新

**需要遷移的獨有功能**：
- `identify` → 移到 `/api/companies/identify`
- `[id]/rules` → 移到 `/api/companies/[id]/rules`
- `[id]/stats` → 移到 `/api/companies/[id]/stats`
- `[id]/documents` → 移到 `/api/companies/[id]/documents`

**需要刪除的重複端點**：
- `/api/forwarders/route.ts`
- `/api/forwarders/[id]/route.ts`
- `/api/forwarders/[id]/activate/route.ts`
- `/api/forwarders/[id]/deactivate/route.ts`
- `/api/forwarders/check-code/route.ts`
- `/api/forwarders/list/route.ts`

---

## 4. 遷移策略

### Phase 1: 預備檢查 ✅
- [x] 確認 `/api/companies` 與 `/api/forwarders` 的功能差異
- [x] 確認資料模型（Prisma）的對應關係
- [x] 決定是**合併**還是**遷移**

### Phase 2: API 層遷移
**需遷移的端點**：
```
/api/forwarders/identify            → /api/companies/identify ⚠️ (不存在於 companies)
/api/forwarders/[id]/rules          → /api/companies/[id]/rules ⚠️ (不存在於 companies)
/api/forwarders/[id]/rules/[ruleId] → /api/companies/[id]/rules/[ruleId] ⚠️
/api/forwarders/[id]/stats          → /api/companies/[id]/stats ⚠️
/api/forwarders/[id]/documents      → /api/companies/[id]/documents ⚠️
```

**動作**：
- 已存在於 companies 的端點：刪除 forwarders 版本
- 不存在於 companies 的端點：移動到 companies 目錄

### Phase 3: 頁面路由遷移
**需遷移的頁面**：
```
src/app/(dashboard)/forwarders/page.tsx                         → companies/
src/app/(dashboard)/forwarders/new/page.tsx                     → companies/new/
src/app/(dashboard)/forwarders/[id]/page.tsx                    → companies/[id]/
src/app/(dashboard)/forwarders/[id]/rules/[ruleId]/test/page.tsx → companies/[id]/rules/[ruleId]/test/
```

**動作**：將整個 `forwarders` 目錄重命名為 `companies`

### Phase 4: 組件引用更新
**需更新的文件**：
```
# 導航
src/components/layout/Sidebar.tsx                    - href: '/forwarders' → '/companies'

# 組件內部
src/components/features/forwarders/ForwarderForm.tsx          - API 路徑
src/components/features/forwarders/ForwarderList.tsx          - Link href
src/components/features/forwarders/ForwarderDetailView.tsx    - Link href
src/components/features/forwarders/ForwarderActions.tsx       - API 路徑
src/components/features/forwarders/ForwarderRulesTable.tsx    - API 路徑

# 其他頁面
src/app/(dashboard)/forwarders/new/page.tsx          - 返回連結
```

### Phase 5: Hooks 更新
**需更新的文件**：
```
src/hooks/use-company-detail.ts    - API 路徑已修復 ✅
src/hooks/use-companies.ts         - 檢查 API 路徑
```

### Phase 6: 服務層引用更新
**需檢查的文件**：
```
src/services/identification/identification.service.ts
src/services/company-auto-create.service.ts
src/components/features/review/ReviewFilters.tsx
```

---

## 5. 詳細遷移文件清單

### 5.1 需遷移目錄（整個目錄重命名）

```
src/app/(dashboard)/forwarders/    → src/app/(dashboard)/companies/
src/app/api/forwarders/            → src/app/api/companies/  (部分合併)
```

### 5.2 需更新路徑引用的文件

| 文件 | 行號 | 當前值 | 目標值 |
|------|------|--------|--------|
| `Sidebar.tsx` | ~111 | `href: '/forwarders'` | `href: '/companies'` |
| `ForwarderForm.tsx` | 多處 | `/api/forwarders` | `/api/companies` |
| `ForwarderList.tsx` | 多處 | `/forwarders` | `/companies` |
| `ForwarderDetailView.tsx` | ~94,117,171 | `/forwarders` | `/companies` |
| `ForwarderActions.tsx` | 多處 | `/api/forwarders` | `/api/companies` |
| `use-company-detail.ts` | ~180,265,321,377,420 | `/api/forwarders` | `/api/companies` ✅ 已修復 |
| `ReviewFilters.tsx` | ~某處 | `/api/forwarders/list` | `/api/companies/list` |

### 5.3 不需要更新的文件（維持向後兼容）

```
src/hooks/use-forwarders.ts         # deprecated alias
src/hooks/use-forwarder-detail.ts   # deprecated alias
src/types/forwarder.ts              # 內部型別，維持命名
src/services/forwarder.service.ts   # 服務層，維持命名
```

---

## 6. 實施步驟

### Step 1: 遷移 API 目錄 (15 min)
```bash
# 移動不存在於 companies 的端點
# - /api/forwarders/identify
# - /api/forwarders/[id]/rules
# - /api/forwarders/[id]/stats
# - /api/forwarders/[id]/documents

# 刪除重複的端點
# - /api/forwarders/route.ts (已有 /api/companies/route.ts)
# - /api/forwarders/[id]/route.ts
# - etc.
```

### Step 2: 遷移頁面目錄 (5 min)
```bash
# 重命名目錄
mv src/app/(dashboard)/forwarders src/app/(dashboard)/companies
```

### Step 3: 更新 Sidebar (2 min)
```typescript
// src/components/layout/Sidebar.tsx
{ name: '公司管理', href: '/companies', icon: Building2 }
```

### Step 4: 更新組件引用 (15 min)
批量更新所有 `/forwarders` → `/companies` 引用

### Step 5: 更新服務層引用 (10 min)
檢查並更新所有 API 調用路徑

### Step 6: 測試驗證 (15 min)
- [ ] 訪問 /companies 列表頁
- [ ] 訪問 /companies/new 新增頁
- [ ] 訪問 /companies/[id] 詳情頁（所有 Tab）
- [ ] 測試規則測試頁面
- [ ] 驗證 Sidebar 導航

---

## 7. 驗證清單

### 功能驗證
- [ ] `/companies` - 公司列表頁正常顯示
- [ ] `/companies/new` - 新增公司表單正常運作
- [ ] `/companies/[id]` - 公司詳情頁正常顯示
- [ ] `/companies/[id]` - 「總覽」Tab 正常
- [ ] `/companies/[id]` - 「規則」Tab 正常（API 200）
- [ ] `/companies/[id]` - 「統計」Tab 正常（API 200）
- [ ] `/companies/[id]` - 「文件」Tab 正常（API 200）
- [ ] `/companies/[id]/rules/[ruleId]/test` - 規則測試頁正常

### API 驗證
- [ ] `GET /api/companies` - 列表 API 正常
- [ ] `POST /api/companies` - 創建 API 正常
- [ ] `GET /api/companies/[id]` - 詳情 API 正常
- [ ] `GET /api/companies/[id]/rules` - 規則列表 API 正常
- [ ] `GET /api/companies/[id]/stats` - 統計 API 正常
- [ ] `GET /api/companies/[id]/documents` - 文件列表 API 正常

### 導航驗證
- [ ] Sidebar「公司管理」連結指向 `/companies`
- [ ] 所有返回按鈕指向正確路徑
- [ ] 所有內部連結正常運作

---

## 8. 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| API 衝突導致功能異常 | 中 | 高 | 先檢查確認再遷移 ✅ 已確認 |
| 遺漏引用更新 | 中 | 中 | 使用全局搜索確認 |
| 快取問題 | 低 | 低 | 清除瀏覽器快取測試 |

---

## 9. 回滾計劃

如果遷移後出現問題：
1. Git revert 所有變更
2. 或手動將 `companies` 目錄重命名回 `forwarders`
3. 恢復 Sidebar 路徑

---

## 10. 已確認決策

| 問題 | 決策 |
|------|------|
| API 衝突問題 | ✅ 保留 `/api/companies`，刪除重複的 `/api/forwarders` 端點 |
| 向後兼容 | ✅ **不需要**，直接刪除 `/forwarders` 路徑 |
| 獨有功能 | ✅ 遷移到 `/api/companies` |

---

**建立日期**: 2026-01-12
**狀態**: 📝 待審核
