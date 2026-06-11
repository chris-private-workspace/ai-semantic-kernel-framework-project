# FEAT-004: Operating Company Management - 實現計劃

## 開發階段

### Phase 0: 規劃準備 ✅
- [x] 建立功能目錄
- [x] 撰寫需求文檔
- [x] 撰寫技術設計
- [x] 撰寫實現計劃

### Phase 1: 後端確認 ✅
- [x] 確認 API Router 已完成
- [x] 確認所有 CRUD 操作可用

### Phase 2: 前端開發
- [ ] 建立列表頁面 (`/operating-companies/page.tsx`)
- [ ] 建立新增頁面 (`/operating-companies/new/page.tsx`)
- [ ] 建立編輯頁面 (`/operating-companies/[id]/edit/page.tsx`)
- [ ] 建立表單組件 (`OperatingCompanyForm.tsx`)
- [ ] 建立操作按鈕組件 (`OperatingCompanyActions.tsx`)
- [ ] 建立導出 index

### Phase 3: I18N
- [ ] 添加英文翻譯 (`en.json`)
- [ ] 添加繁中翻譯 (`zh-TW.json`)
- [ ] 驗證翻譯完整性

### Phase 4: 測試與驗證
- [ ] 列表頁面功能測試
- [ ] 新增功能測試
- [ ] 編輯功能測試
- [ ] 刪除功能測試
- [ ] 切換狀態功能測試
- [ ] TypeScript 無錯誤
- [ ] ESLint 無錯誤

## 開發順序

1. **表單組件** → 新增/編輯頁面共用
2. **操作按鈕組件** → 列表頁面使用
3. **列表頁面** → 主要入口
4. **新增頁面** → 使用表單組件
5. **編輯頁面** → 使用表單組件
6. **I18N** → 添加翻譯
7. **測試** → 驗證所有功能

## 參考文件

- Vendors 頁面: `apps/web/src/app/[locale]/vendors/`
- Users 頁面: `apps/web/src/app/[locale]/users/`
- ChargeOut Actions: `apps/web/src/components/charge-out/ChargeOutActions.tsx`
