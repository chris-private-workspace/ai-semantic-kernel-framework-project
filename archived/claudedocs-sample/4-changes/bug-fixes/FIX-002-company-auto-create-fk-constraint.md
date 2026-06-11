# FIX-002: 公司自動建立 FK 約束錯誤

> **建立日期**: 2025-12-27
> **完成日期**: 2025-12-27
> **狀態**: ✅ 已完成
> **優先級**: High
> **關聯 Epic**: Epic 0 - 歷史數據初始化

---

## 問題描述

在執行 Epic 0 歷史數據初始化測試（TEST-PLAN-002）時，AI 處理成功完成，但公司自動建立功能失敗，導致：

1. **資料庫約束錯誤**：
   ```
   Foreign key constraint violated on the constraint: companies_created_by_id_fkey
   ```

2. **連鎖影響**：
   - `document_issuer_id` 為 NULL（應關聯到公司）
   - `document_format_id` 為 NULL（應關聯到格式）
   - 術語聚合結果為空（依賴公司資料）
   - Excel 報告無數據（因 `aggregation.companies` 為空陣列）

---

## 重現步驟

1. 上傳 PDF 文件到歷史數據批次
2. 系統觸發 AI 處理流程
3. 處理完成後，系統嘗試自動建立公司 Profile
4. ❌ 公司建立失敗：FK 約束違反
5. ❌ 後續的發行者識別和術語聚合無法正常執行

---

## 根本原因分析

### 問題根源

`src/services/company-auto-create.service.ts` 第 94 行定義了一個錯誤的系統用戶 ID：

```typescript
/** 系統用戶 ID（用於自動建立） */
export const SYSTEM_USER_ID = 'system'  // ❌ 此用戶不存在於資料庫
```

### 資料庫狀態

資料庫中的 `users` 表只有一個用戶：

| id | email |
|----|-------|
| `dev-user-1` | admin@example.com |

### 錯誤傳遞鏈

```
SYSTEM_USER_ID = 'system'
    ↓
batch-processor.service.ts (Line 227, 508)
    ↓
identifyCompaniesFromExtraction({ createdById: 'system' })
processFileIssuerIdentification({ createdById: 'system' })
    ↓
prisma.company.create({ data: { createdById: 'system' } })
    ↓
❌ FK Constraint Violation: companies_created_by_id_fkey
```

---

## 解決方案

### 修改內容

**檔案**: `src/services/company-auto-create.service.ts`

**修改前** (Line 93-94):
```typescript
/** 系統用戶 ID（用於自動建立） */
export const SYSTEM_USER_ID = 'system'
```

**修改後** (Line 93-103):
```typescript
/**
 * 系統用戶 ID（用於自動建立）
 *
 * @description
 *   此 ID 用於 JIT（Just-in-Time）自動建立公司時的 createdById 欄位。
 *   必須對應到資料庫中已存在的用戶 ID，否則會觸發 FK 約束錯誤：
 *   `Foreign key constraint violated on the constraint: companies_created_by_id_fkey`
 *
 * @since FIX-002 - 修復公司自動建立 FK 約束問題
 */
export const SYSTEM_USER_ID = 'dev-user-1'
```

---

## 修改的檔案

| 檔案路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `src/services/company-auto-create.service.ts` | 修改 | 將 `SYSTEM_USER_ID` 從 `'system'` 改為 `'dev-user-1'` |

---

## 影響範圍

### 直接影響

| 服務 | 使用位置 | 影響 |
|------|----------|------|
| `batch-processor.service.ts` | Line 227, 508 | 公司識別和發行者識別 |
| `company-auto-create.service.ts` | 所有 JIT 建立功能 | 公司 Profile 自動建立 |

### 修復後預期結果

1. ✅ 公司自動建立成功（FK 約束滿足）
2. ✅ `document_issuer_id` 正確關聯
3. ✅ `document_format_id` 正確關聯
4. ✅ 術語聚合正常執行
5. ✅ Excel 報告包含完整數據

---

## 測試驗證

### 驗證步驟

1. 重新處理一個批次
2. 確認公司自動建立成功
3. 檢查 `companies` 表有新記錄
4. 確認 `document_issuer_id` 不為 NULL
5. 驗證 Excel 報告有數據

### 驗證 SQL

```sql
-- 確認公司已建立
SELECT COUNT(*) FROM companies WHERE source = 'AUTO_CREATED';

-- 確認文件關聯正確
SELECT id, file_name, document_issuer_id, document_format_id
FROM batch_files
WHERE document_issuer_id IS NOT NULL;
```

---

## 長期建議

### 建議改進

1. **環境變數配置**：
   將 `SYSTEM_USER_ID` 改為從環境變數讀取：
   ```typescript
   export const SYSTEM_USER_ID = process.env.SYSTEM_USER_ID || 'dev-user-1'
   ```

2. **資料庫種子**：
   確保資料庫初始化時建立系統用戶：
   ```typescript
   // prisma/seed.ts
   await prisma.user.upsert({
     where: { id: 'system' },
     create: { id: 'system', email: 'system@internal', ... },
     update: {},
   })
   ```

3. **錯誤處理增強**：
   在 JIT 建立失敗時提供更清楚的錯誤訊息

---

## 相關文檔

- [TEST-PLAN-002: Epic 0 歷史數據初始化測試](../../../claudedocs/5-status/testing/plans/TEST-PLAN-002-EPIC-0-COMPLETE.md)
- [TEST-REPORT-002: Epic 0 測試結果報告](../../../claudedocs/5-status/testing/reports/TEST-REPORT-002-EPIC-0-RESULTS.md)
- [Story 0-3: Just-in-Time 公司配置](../../../docs/04-implementation/stories/0-3-just-in-time-company-profile.md)

---

**修復者**: Claude AI Assistant
**審核者**: -
**最後更新**: 2025-12-27
