# FIX-016: IssuerIdentifierAdapter 欄位映射錯誤

> **日期**: 2026-01-05
> **狀態**: ✅ 已修復
> **嚴重度**: Medium
> **發現於**: CHANGE-005 實施過程

---

## 問題描述

`issuer-identifier-adapter.ts` 中的 `convertToLegacyRequest()` 方法存在兩個問題：

1. **欄位名稱不正確**: 目標類型期望 `name: string`（必填），但源類型是 `name?: string`（可選）
2. **空值處理不足**: 當 `issuerIdentification.name` 為 undefined 時，仍會創建無效的 `documentIssuer` 物件

## 根本原因

```typescript
// 問題代碼
documentIssuer: extractionResult.issuerIdentification
  ? {
      name: extractionResult.issuerIdentification.name,  // 可能為 undefined
      // ...
    }
  : undefined
```

`issuerIdentification` 物件存在但 `name` 屬性為 undefined 時，會創建一個不符合類型約束的物件。

## 修復方案

```typescript
// 修復後代碼
const issuerInfo = extractionResult.issuerIdentification;
const documentIssuer =
  issuerInfo?.name  // 確保 name 存在才創建物件
    ? {
        name: issuerInfo.name,
        identificationMethod: issuerInfo.method,
        confidence: issuerInfo.confidence,
        rawText: issuerInfo.rawText,
      }
    : undefined;
```

## 修改文件

| 文件 | 行號 | 變更 |
|------|------|------|
| `src/services/unified-processor/adapters/issuer-identifier-adapter.ts` | 118-136 | 增加 `issuerInfo?.name` 空值檢查 |

## 驗證

```bash
npm run type-check 2>&1 | grep "issuer-identifier-adapter"
# 輸出: No errors
```

## 相關變更

- [CHANGE-005: 統一管道步驟重排序](../feature-changes/CHANGE-005-unified-pipeline-step-reorder.md)

---

**修復日期**: 2026-01-05
**開發者**: AI Assistant (Claude)
