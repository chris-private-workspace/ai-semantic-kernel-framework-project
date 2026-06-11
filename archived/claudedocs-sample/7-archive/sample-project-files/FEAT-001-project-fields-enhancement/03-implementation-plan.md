# FEAT-001: 專案欄位擴展 - 實施計劃

> **功能編號**: FEAT-001
> **創建日期**: 2025-11-14
> **狀態**: 準備開發
> **預估工時**: 8-12 小時

---

## 📋 實施階段總覽

```
Phase 1: 資料庫與後端 (2-3h)
    ↓
Phase 2: 前端表單 (2-3h)
    ↓
Phase 3: 列表與詳情頁 (1-2h)
    ↓
Phase 4: 貨幣管理頁面 (2-3h)
    ↓
Phase 5: I18N 與測試 (1h)
    ↓
   完成
```

---

## Phase 1: 資料庫與後端 (2-3 小時)

### 任務 1.1: 創建 Currency Model 和 Migration

**檔案**: `packages/db/prisma/schema.prisma`

**步驟**:
1. 在 schema.prisma 末尾新增 Currency Model
2. 更新 Project Model（新增 4 個欄位）
3. 執行 `pnpm db:migrate dev --name add_project_fields_and_currency`
4. 驗證 Migration 檔案生成正確

**預期輸出**:
```prisma
model Currency {
  id           String   @id @default(uuid())
  code         String   @unique
  name         String
  symbol       String
  exchangeRate Float?
  active       Boolean  @default(true)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  projects     Project[]

  @@index([code])
  @@index([active])
}

model Project {
  // ... 現有欄位 ...
  projectCode  String    @unique
  globalFlag   String    @default("Region")
  priority     String    @default("Medium")
  currencyId   String?

  currency     Currency? @relation(fields: [currencyId], references: [id])

  @@index([projectCode])
  @@index([globalFlag])
  @@index([priority])
  @@index([currencyId])
}
```

**驗證檢查點**:
- [ ] Migration 檔案已生成
- [ ] `pnpm db:generate` 成功執行
- [ ] Prisma Client 類型已更新
- [ ] 無 TypeScript 錯誤

**預估時間**: 30 分鐘

---

### 任務 1.2: Seed 預設貨幣資料

**檔案**: `packages/db/prisma/seed.ts`（或在 Migration 中直接執行）

**步驟**:
1. 創建 seed 腳本或在 Migration 中插入預設貨幣
2. 插入 6 個預設貨幣（TWD, USD, EUR, CNY, JPY, HKD）
3. 執行 `pnpm db:seed` 或自動在 Migration 中執行

**預期輸出**:
```typescript
// seed.ts
const defaultCurrencies = [
  { code: 'TWD', name: '新台幣', symbol: 'NT$', exchangeRate: 1.0 },
  { code: 'USD', name: '美元', symbol: '$', exchangeRate: 30.5 },
  { code: 'EUR', name: '歐元', symbol: '€', exchangeRate: 33.2 },
  { code: 'CNY', name: '人民幣', symbol: '¥', exchangeRate: 4.3 },
  { code: 'JPY', name: '日圓', symbol: '¥', exchangeRate: 0.21 },
  { code: 'HKD', name: '港幣', symbol: 'HK$', exchangeRate: 3.9 },
];

for (const currency of defaultCurrencies) {
  await prisma.currency.create({ data: currency });
}
```

**驗證檢查點**:
- [ ] 資料庫中有 6 筆貨幣資料
- [ ] 所有貨幣的 active 狀態為 true
- [ ] 無重複的貨幣代碼

**預估時間**: 20 分鐘

---

### 任務 1.3: 更新現有專案資料（Migration）

**步驟**:
1. 在 Migration 檔案中新增更新腳本
2. 為所有現有專案設定預設值
3. 執行 Migration 並驗證

**Migration 腳本範例**:
```sql
-- 為現有專案設定預設值
DO $$
DECLARE
  twd_currency_id TEXT;
BEGIN
  SELECT id INTO twd_currency_id FROM "Currency" WHERE code = 'TWD';

  UPDATE "Project"
  SET
    "projectCode" = 'LEGACY-' || SUBSTRING(id, 1, 8),
    "globalFlag" = 'Region',
    "priority" = 'Medium',
    "currencyId" = twd_currency_id
  WHERE "projectCode" IS NULL;
END $$;
```

**驗證檢查點**:
- [ ] 所有現有專案都有 projectCode（格式: LEGACY-xxxxxxxx）
- [ ] 所有現有專案的 globalFlag 為 "Region"
- [ ] 所有現有專案的 priority 為 "Medium"
- [ ] 所有現有專案的 currencyId 為 TWD 的 ID

**預估時間**: 20 分鐘

---

### 任務 1.4: 創建 Currency Router

**檔案**: `packages/api/src/routers/currency.ts`

**步驟**:
1. 創建新檔案 `currency.ts`
2. 實作 9 個 procedures（參考技術設計文檔）
3. 在 `root.ts` 中註冊 currencyRouter

**Procedures 清單**:
- [x] create（管理員權限）
- [x] update（管理員權限）
- [x] delete（管理員權限）
- [x] getAll（含停用的）
- [x] getActive（用於表單選項）
- [x] getById
- [x] toggleActive（管理員權限）

**驗證檢查點**:
- [ ] 所有 procedures 實作完成
- [ ] Zod validation schemas 定義正確
- [ ] 管理員權限檢查正常
- [ ] 無 TypeScript 錯誤

**預估時間**: 40 分鐘

---

### 任務 1.5: 更新 Project Router

**檔案**: `packages/api/src/routers/project.ts`

**步驟**:
1. 更新 createProjectSchema（新增 4 個欄位驗證）
2. 更新 updateProjectSchema（新增 4 個欄位驗證）
3. 新增 checkCodeAvailability procedure
4. 更新 create procedure（新增唯一性檢查）
5. 更新 getAll procedure（新增篩選和排序）
6. 更新 getById procedure（包含 currency 關聯）

**驗證檢查點**:
- [ ] createProjectSchema 包含新欄位驗證
- [ ] checkCodeAvailability procedure 正常運作
- [ ] create 時檢查專案編號唯一性
- [ ] getAll 支援 globalFlag, priority, currencyId 篩選
- [ ] getAll 支援 projectCode, priority 排序
- [ ] 無 TypeScript 錯誤

**預估時間**: 50 分鐘

---

## Phase 2: 前端表單 (2-3 小時)

### 任務 2.1: 更新 ProjectForm 組件

**檔案**: `apps/web/src/components/project/ProjectForm.tsx`

**步驟**:
1. 新增 4 個欄位的狀態管理
2. 實作專案編號輸入框（含即時驗證）
3. 實作全域標誌 Select
4. 實作優先權 Select
5. 實作貨幣 Combobox
6. 載入啟用的貨幣列表（getActive）
7. 處理表單提交（包含新欄位）

**新增 UI 元素**:
```tsx
{/* 專案編號 */}
<Input
  id="projectCode"
  value={formData.projectCode}
  onChange={handleProjectCodeChange}
  className={cn(codeStatus.className)}
/>

{/* 全域標誌 */}
<Select value={formData.globalFlag} onValueChange={...}>
  <SelectItem value="RCL">🌍 RCL</SelectItem>
  <SelectItem value="Region">📍 Region</SelectItem>
</Select>

{/* 優先權 */}
<Select value={formData.priority} onValueChange={...}>
  <SelectItem value="High">🔴 高</SelectItem>
  <SelectItem value="Medium">🟡 中</SelectItem>
  <SelectItem value="Low">🟢 低</SelectItem>
</Select>

{/* 貨幣 */}
<Combobox
  options={currencies}
  value={formData.currencyId}
  onChange={...}
/>
```

**驗證檢查點**:
- [ ] 4 個新欄位全部顯示
- [ ] 專案編號即時驗證正常（debounce 500ms）
- [ ] 預設值正確（Region, Medium, TWD）
- [ ] 表單驗證正常（必填檢查）
- [ ] 提交成功後資料正確儲存
- [ ] 無 TypeScript 錯誤

**預估時間**: 60 分鐘

---

### 任務 2.2: 更新專案建立頁面

**檔案**: `apps/web/src/app/[locale]/projects/new/page.tsx`

**步驟**:
1. 確認 ProjectForm 整合正常
2. 測試建立流程
3. 驗證錯誤處理

**驗證檢查點**:
- [ ] 頁面載入正常
- [ ] 新欄位顯示正常
- [ ] 建立成功後導向正確頁面
- [ ] Toast 訊息顯示正常

**預估時間**: 10 分鐘

---

### 任務 2.3: 更新專案編輯頁面

**檔案**: `apps/web/src/app/[locale]/projects/[id]/edit/page.tsx`

**步驟**:
1. 確認現有值正確載入
2. 測試編輯流程
3. 驗證專案編號唯一性（排除自己）

**驗證檢查點**:
- [ ] 現有值正確顯示在表單中
- [ ] 編輯專案編號時唯一性驗證正常（排除自己）
- [ ] 更新成功後資料正確儲存
- [ ] Toast 訊息顯示正常

**預估時間**: 15 分鐘

---

### 任務 2.4: 實作 debounce Hook（如果不存在）

**檔案**: `apps/web/src/hooks/useDebounce.ts`（已存在，檢查是否適用）

**步驟**:
1. 檢查現有 useDebounce hook
2. 確認適用於專案編號驗證場景
3. 如需調整則更新

**驗證檢查點**:
- [ ] useDebounce hook 可正常使用
- [ ] Debounce 延遲為 500ms

**預估時間**: 5 分鐘

---

## Phase 3: 列表與詳情頁 (1-2 小時)

### 任務 3.1: 更新專案列表頁

**檔案**: `apps/web/src/app/[locale]/projects/page.tsx`

**步驟**:
1. 新增 4 個表格列（projectCode, globalFlag, priority, currency）
2. 新增 globalFlag 篩選器
3. 新增 priority 篩選器
4. 新增 projectCode 排序
5. 新增 priority 排序
6. 實作徽章（Badge）組件顯示

**新增表格列**:
```tsx
<TableHead onClick={() => handleSort('projectCode')}>
  {t('table.projectCode')}
</TableHead>
<TableHead>{t('table.globalFlag')}</TableHead>
<TableHead onClick={() => handleSort('priority')}>
  {t('table.priority')}
</TableHead>
<TableHead>{t('table.currency')}</TableHead>
```

**徽章樣式**:
- 全域標誌：RCL (default) vs Region (secondary)
- 優先權：High (destructive) vs Medium (default) vs Low (secondary)

**驗證檢查點**:
- [ ] 4 個新欄位正確顯示
- [ ] 徽章顯示樣式正確
- [ ] 篩選功能正常
- [ ] 排序功能正常
- [ ] 搜尋包含專案編號

**預估時間**: 45 分鐘

---

### 任務 3.2: 更新專案詳情頁

**檔案**: `apps/web/src/app/[locale]/projects/[id]/page.tsx`

**步驟**:
1. 新增 4 個欄位的顯示區塊
2. 調整佈局以容納新欄位
3. 測試資料顯示

**顯示格式**:
```tsx
<div className="grid grid-cols-2 gap-4">
  <div>
    <Label>{t('fields.projectCode')}</Label>
    <p className="font-mono">{project.projectCode}</p>
  </div>
  <div>
    <Label>{t('fields.globalFlag')}</Label>
    <Badge>{project.globalFlag === 'RCL' ? '🌍 RCL' : '📍 Region'}</Badge>
  </div>
  <div>
    <Label>{t('fields.priority')}</Label>
    <Badge>{getPriorityBadge(project.priority)}</Badge>
  </div>
  <div>
    <Label>{t('fields.currency')}</Label>
    <p>{project.currency?.code} - {project.currency?.name}</p>
  </div>
</div>
```

**驗證檢查點**:
- [ ] 4 個新欄位正確顯示
- [ ] 貨幣資訊完整（code + name + symbol）
- [ ] 佈局美觀且一致

**預估時間**: 15 分鐘

---

## Phase 4: 貨幣管理頁面 (2-3 小時)

### 任務 4.1: 創建貨幣列表頁

**檔案**: `apps/web/src/app/[locale]/settings/currencies/page.tsx`

**步驟**:
1. 創建頁面檔案
2. 實作列表 UI（Table）
3. 呼叫 currency.getAll API
4. 顯示貨幣資料（code, name, symbol, exchangeRate, status, projectCount）
5. 實作操作按鈕（編輯、刪除、切換狀態）

**UI 結構**:
```tsx
<DashboardLayout>
  <div className="space-y-6">
    <div className="flex justify-between">
      <h1>{t('currencies.title')}</h1>
      <Button onClick={() => router.push('/settings/currencies/new')}>
        {t('currencies.actions.create')}
      </Button>
    </div>

    <Card>
      <Table>
        <TableHeader>...</TableHeader>
        <TableBody>
          {currencies.map(currency => (
            <TableRow key={currency.id}>
              <TableCell>{currency.code}</TableCell>
              <TableCell>{currency.name}</TableCell>
              <TableCell>{currency.symbol}</TableCell>
              <TableCell>{currency.exchangeRate || '-'}</TableCell>
              <TableCell>
                <Badge>{currency.active ? '啟用' : '停用'}</Badge>
              </TableCell>
              <TableCell>{currency._count.projects}</TableCell>
              <TableCell>
                <CurrencyActions currency={currency} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  </div>
</DashboardLayout>
```

**驗證檢查點**:
- [ ] 列表正確顯示所有貨幣
- [ ] 專案使用數量正確顯示
- [ ] 啟用/停用狀態正確顯示
- [ ] 操作按鈕顯示正常

**預估時間**: 40 分鐘

---

### 任務 4.2: 創建貨幣建立頁面

**檔案**: `apps/web/src/app/[locale]/settings/currencies/new/page.tsx`

**步驟**:
1. 創建頁面檔案
2. 實作 CurrencyForm 組件（或內嵌表單）
3. 實作貨幣代碼驗證（3 字母、大寫、唯一性）
4. 呼叫 currency.create API

**表單欄位**:
- 貨幣代碼（必填、3 字母、自動大寫）
- 貨幣名稱（必填）
- 貨幣符號（必填）
- 匯率（可選）
- 啟用狀態（預設 true）

**驗證檢查點**:
- [ ] 表單顯示正常
- [ ] 貨幣代碼自動轉大寫
- [ ] 唯一性驗證正常
- [ ] 建立成功後導向列表頁
- [ ] Toast 訊息顯示正常

**預估時間**: 40 分鐘

---

### 任務 4.3: 創建貨幣編輯頁面

**檔案**: `apps/web/src/app/[locale]/settings/currencies/[id]/edit/page.tsx`

**步驟**:
1. 創建頁面檔案
2. 載入現有貨幣資料
3. 實作編輯表單
4. 呼叫 currency.update API

**驗證檢查點**:
- [ ] 現有值正確載入
- [ ] 編輯成功後資料正確更新
- [ ] Toast 訊息顯示正常

**預估時間**: 25 分鐘

---

### 任務 4.4: 實作 CurrencyActions 組件

**檔案**: `apps/web/src/components/currency/CurrencyActions.tsx`（新增）

**步驟**:
1. 創建組件檔案
2. 實作編輯按鈕
3. 實作刪除按鈕（含確認對話框）
4. 實作切換狀態按鈕

**功能**:
- 編輯：導向編輯頁面
- 刪除：檢查是否有專案使用，顯示確認對話框
- 切換狀態：呼叫 toggleActive API

**驗證檢查點**:
- [ ] 編輯按鈕正常導向
- [ ] 刪除前顯示確認對話框
- [ ] 刪除時檢查專案使用狀況
- [ ] 切換狀態成功且 UI 更新

**預估時間**: 30 分鐘

---

### 任務 4.5: 更新導航選單（Sidebar）

**檔案**: `apps/web/src/components/layout/Sidebar.tsx`

**步驟**:
1. 在「系統設定」或「設定」區塊新增「貨幣管理」連結
2. 確認權限控制（如需管理員權限）

**驗證檢查點**:
- [ ] 貨幣管理連結顯示正常
- [ ] 點擊後正確導向 /settings/currencies
- [ ] 權限控制正常（如適用）

**預估時間**: 10 分鐘

---

## Phase 5: I18N 與測試 (1 小時)

### 任務 5.1: 新增繁體中文翻譯

**檔案**: `apps/web/src/messages/zh-TW.json`

**步驟**:
1. 新增 projects.form 欄位翻譯
2. 新增 projects.table 欄位翻譯
3. 新增 projects.filters 翻譯
4. 新增完整的 currencies 命名空間

**預估新增行數**: ~80 行

**驗證檢查點**:
- [ ] 所有新文字都有翻譯
- [ ] JSON 格式正確（無語法錯誤）
- [ ] 執行 `pnpm validate:i18n` 通過

**預估時間**: 15 分鐘

---

### 任務 5.2: 新增英文翻譯

**檔案**: `apps/web/src/messages/en.json`

**步驟**:
1. 複製繁中翻譯結構
2. 翻譯為英文
3. 確保 key 結構與繁中一致

**驗證檢查點**:
- [ ] 所有 key 與繁中一致
- [ ] 英文翻譯自然且正確
- [ ] JSON 格式正確
- [ ] 執行 `pnpm validate:i18n` 通過

**預估時間**: 15 分鐘

---

### 任務 5.3: 手動測試（關鍵流程）

**測試場景**:

1. **專案建立流程**
   - [ ] 新增專案時填寫 4 個新欄位
   - [ ] 專案編號唯一性驗證正常
   - [ ] 選擇貨幣正常
   - [ ] 建立成功

2. **專案編輯流程**
   - [ ] 編輯頁面顯示現有值
   - [ ] 修改專案編號時唯一性驗證正常（排除自己）
   - [ ] 更新成功

3. **專案列表流程**
   - [ ] 4 個新欄位正確顯示
   - [ ] 篩選功能正常
   - [ ] 排序功能正常

4. **貨幣管理流程**
   - [ ] 列表頁正確顯示
   - [ ] 新增貨幣成功
   - [ ] 編輯貨幣成功
   - [ ] 切換狀態成功
   - [ ] 刪除保護正常（有專案使用時無法刪除）

5. **I18N 切換**
   - [ ] 繁中模式所有文字正確
   - [ ] 英文模式所有文字正確
   - [ ] 切換語言時無錯誤

**預估時間**: 20 分鐘

---

### 任務 5.4: 驗證代碼品質

**檢查項目**:
```bash
# TypeScript 類型檢查
pnpm typecheck

# ESLint 檢查
pnpm lint

# I18N 驗證
pnpm validate:i18n
```

**驗證檢查點**:
- [ ] 無 TypeScript 錯誤（排除 pre-existing）
- [ ] 無新增的 ESLint 錯誤
- [ ] I18N 驗證通過

**預估時間**: 10 分鐘

---

## 📊 總體時間估算

| Phase | 預估時間 | 實際時間 | 狀態 |
|-------|---------|---------|------|
| Phase 1: 資料庫與後端 | 2-3 小時 | - | ⏳ 待執行 |
| Phase 2: 前端表單 | 2-3 小時 | - | ⏳ 待執行 |
| Phase 3: 列表與詳情頁 | 1-2 小時 | - | ⏳ 待執行 |
| Phase 4: 貨幣管理頁面 | 2-3 小時 | - | ⏳ 待執行 |
| Phase 5: I18N 與測試 | 1 小時 | - | ⏳ 待執行 |
| **總計** | **8-12 小時** | **-** | **⏳ 待執行** |

---

## ✅ 完成檢查清單

### Phase 1 完成標準
- [ ] Currency Model 建立成功
- [ ] Project Model 更新成功
- [ ] Migration 執行成功
- [ ] 6 個預設貨幣已插入
- [ ] 現有專案預設值已設定
- [ ] Currency Router 實作完成
- [ ] Project Router 更新完成
- [ ] 無 TypeScript 錯誤

### Phase 2 完成標準
- [ ] ProjectForm 組件更新完成
- [ ] 4 個新欄位全部顯示
- [ ] 專案編號即時驗證正常
- [ ] 建立頁面整合正常
- [ ] 編輯頁面整合正常
- [ ] 無 TypeScript 錯誤

### Phase 3 完成標準
- [ ] 列表頁新欄位顯示正常
- [ ] 篩選功能正常
- [ ] 排序功能正常
- [ ] 詳情頁新欄位顯示正常
- [ ] 無 TypeScript 錯誤

### Phase 4 完成標準
- [ ] 貨幣列表頁完成
- [ ] 貨幣建立頁完成
- [ ] 貨幣編輯頁完成
- [ ] CurrencyActions 組件完成
- [ ] Sidebar 導航連結已新增
- [ ] 無 TypeScript 錯誤

### Phase 5 完成標準
- [ ] 繁中翻譯完成
- [ ] 英文翻譯完成
- [ ] I18N 驗證通過
- [ ] 手動測試完成（5 個場景）
- [ ] TypeScript 檢查通過
- [ ] ESLint 檢查通過

---

## 🚨 風險與應對措施

### 風險 1: Migration 執行失敗
**應對措施**:
1. 在執行 Migration 前備份資料庫
2. 在開發環境先測試 Migration
3. 準備 Rollback 腳本

### 風險 2: 專案編號唯一性衝突
**應對措施**:
1. Migration 時使用 UUID 前 8 碼（幾乎不可能重複）
2. 提供編輯功能讓使用者手動修改

### 風險 3: 現有專案的貨幣預設值不適用
**應對措施**:
1. 提供批量編輯工具（未來可擴展）
2. 通知使用者檢查並更新專案貨幣

---

## 📝 開發注意事項

### 代碼風格
- 遵循現有的代碼風格（參考 .claude.md 模式文檔）
- 使用 TypeScript 嚴格模式
- 所有新代碼添加 JSDoc 註解

### Git 提交策略
- 每個 Phase 完成後提交一次
- Commit message 使用 conventional commits 格式
- 範例: `feat(project): add 4 new fields to project form (FEAT-001)`

### 測試策略
- Phase 1-4 完成後立即手動測試
- Phase 5 進行完整的回歸測試
- E2E 測試（可選，時間允許時）

---

## 🔗 相關文檔

- [01-requirements.md](./01-requirements.md) - 需求文檔
- [02-technical-design.md](./02-technical-design.md) - 技術設計
- [04-progress.md](./04-progress.md) - 開發進度追蹤

---

**文檔維護者**: AI Assistant + 開發團隊
**最後更新**: 2025-11-14
**狀態**: ✅ 實施計劃完成，準備開發
