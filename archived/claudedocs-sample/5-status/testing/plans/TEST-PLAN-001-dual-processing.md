# TEST-PLAN-001: 歷史文件數據初始化 - 雙重處理架構測試

> **狀態**: 📝 草稿
> **建立日期**: 2025-12-27
> **關聯變更**: CHANGE-001 Native PDF 雙重處理架構增強
> **測試人員**: [待指定]
> **優先級**: P0 - 必須測試

---

## 測試目標

驗證 CHANGE-001 實作的 **DUAL_PROCESSING** 模式是否正確運作，確保：

1. **Native PDF** 使用雙重處理（GPT Vision 分類 + Azure DI 數據）
2. **Scanned PDF / Image** 維持 GPT Vision 完整處理
3. 所有文件類型都能正確輸出 `documentIssuer` 和 `documentFormat`
4. Story 0.8（文件發行者識別）和 Story 0.9（文件格式術語重組）功能正常運作

---

## 前置條件

### 環境準備

- [ ] 本地開發環境已啟動 (`npm run dev`)
- [ ] PostgreSQL 資料庫已運行 (`docker-compose up -d`)
- [ ] 已執行 Prisma 遷移 (`npx prisma migrate dev`)
- [ ] 已執行 Prisma Generate (`npx prisma generate`)

### 外部服務

- [ ] Azure Document Intelligence API Key 有效
- [ ] Azure OpenAI (GPT-4o Vision) API Key 有效
- [ ] 網絡連接正常

### 測試數據

- [ ] 準備 Native PDF 測試文件（至少 3 份不同發行者）
- [ ] 準備 Scanned PDF 測試文件（至少 2 份）
- [ ] 準備 Image 測試文件（JPG/PNG，至少 2 份）

---

## 測試範圍

### 包含

1. **文件類型檢測** - `file-detection.service.ts`
2. **處理路由決策** - `processing-router.service.ts`
3. **GPT Vision 分類** - `gpt-vision.service.ts` → `classifyDocument()`
4. **Azure DI 數據提取** - `azure-di.service.ts`
5. **雙重處理整合** - `batch-processor.service.ts` → `DUAL_PROCESSING`
6. **發行者識別** - `document-issuer.service.ts`
7. **格式分類** - `document-format.service.ts`

### 排除

- UI 介面測試（本次僅測試後端處理流程）
- 三層映射系統測試（Tier 1/2/3）
- 審核工作流測試

---

## 測試場景

### 場景 1: Native PDF 雙重處理流程

**目標**: 驗證 Native PDF 使用 DUAL_PROCESSING 模式

| 步驟 | 操作 | 預期結果 | 實際結果 | 狀態 |
|------|------|---------|---------|------|
| 1.1 | 上傳一份 Native PDF 發票 | 文件成功上傳，返回文件 ID | | ⏳ |
| 1.2 | 觸發批次處理 | 開始處理，顯示處理狀態 | | ⏳ |
| 1.3 | 檢查處理方法 | `processingMethod = DUAL_PROCESSING` | | ⏳ |
| 1.4 | 驗證 Phase 1 (GPT Vision) | 日誌顯示 "[DUAL_PROCESSING] Phase 1: GPT Vision classification..." | | ⏳ |
| 1.5 | 驗證 Phase 2 (Azure DI) | 日誌顯示 "[DUAL_PROCESSING] Phase 2: Azure DI data extraction..." | | ⏳ |
| 1.6 | 檢查 documentIssuer | 返回 `{ name, identificationMethod, confidence }` | | ⏳ |
| 1.7 | 檢查 documentFormat | 返回 `{ documentType, documentSubtype }` | | ⏳ |
| 1.8 | 檢查 invoiceData | 返回發票欄位（vendorName, customerName, lineItems） | | ⏳ |

**測試數據**:
- 文件: `test-native-invoice-001.pdf`
- 預期發行者: [根據測試文件填寫]
- 預期文件類型: INVOICE

---

### 場景 2: Scanned PDF 完整 GPT Vision 處理

**目標**: 驗證 Scanned PDF 維持 GPT_VISION 模式

| 步驟 | 操作 | 預期結果 | 實際結果 | 狀態 |
|------|------|---------|---------|------|
| 2.1 | 上傳一份 Scanned PDF 發票 | 文件成功上傳 | | ⏳ |
| 2.2 | 觸發批次處理 | 開始處理 | | ⏳ |
| 2.3 | 檢查處理方法 | `processingMethod = GPT_VISION` | | ⏳ |
| 2.4 | 檢查 documentIssuer | 正確識別發行者 | | ⏳ |
| 2.5 | 檢查 documentFormat | 正確分類文件類型 | | ⏳ |
| 2.6 | 檢查 extractedData | 包含完整提取數據 | | ⏳ |

---

### 場景 3: Image 文件處理

**目標**: 驗證 Image 使用 GPT_VISION 模式

| 步驟 | 操作 | 預期結果 | 實際結果 | 狀態 |
|------|------|---------|---------|------|
| 3.1 | 上傳一份 JPG 發票圖片 | 文件成功上傳 | | ⏳ |
| 3.2 | 觸發批次處理 | 開始處理 | | ⏳ |
| 3.3 | 檢查處理方法 | `processingMethod = GPT_VISION` | | ⏳ |
| 3.4 | 檢查 documentIssuer | 正確識別發行者 | | ⏳ |
| 3.5 | 檢查完整輸出 | 包含所有必要欄位 | | ⏳ |

---

### 場景 4: 發行者識別驗證 (Story 0.8)

**目標**: 驗證所有文件類型都能正確識別發行者

| 步驟 | 操作 | 預期結果 | 實際結果 | 狀態 |
|------|------|---------|---------|------|
| 4.1 | 處理帶有明顯 LOGO 的 PDF | `identificationMethod = LOGO` | | ⏳ |
| 4.2 | 處理帶有標題的 PDF | `identificationMethod = HEADER` | | ⏳ |
| 4.3 | 驗證公司匹配 | 正確匹配或創建 Company 記錄 | | ⏳ |
| 4.4 | 驗證信心度 | `confidence` 在 0-100 範圍內 | | ⏳ |

---

### 場景 5: 文件格式分類驗證 (Story 0.9)

**目標**: 驗證文件類型和子類型正確分類

| 步驟 | 操作 | 預期結果 | 實際結果 | 狀態 |
|------|------|---------|---------|------|
| 5.1 | 處理 Ocean Freight Invoice | `documentType = INVOICE`, `documentSubtype = OCEAN` | | ⏳ |
| 5.2 | 處理 Air Freight Invoice | `documentType = INVOICE`, `documentSubtype = AIR` | | ⏳ |
| 5.3 | 處理 Debit Note | `documentType = DEBIT_NOTE` | | ⏳ |
| 5.4 | 驗證 DocumentFormat 創建 | 在 Company 下創建對應格式記錄 | | ⏳ |

---

### 場景 6: 錯誤處理驗證

**目標**: 驗證錯誤情況的處理

| 步驟 | 操作 | 預期結果 | 實際結果 | 狀態 |
|------|------|---------|---------|------|
| 6.1 | GPT Vision 分類失敗 | 記錄警告，繼續 Azure DI 處理 | | ⏳ |
| 6.2 | Azure DI 處理失敗 | 拋出錯誤，標記文件為失敗 | | ⏳ |
| 6.3 | 上傳損壞的 PDF | 正確處理錯誤，不崩潰 | | ⏳ |
| 6.4 | API 超時 | 重試或正確報錯 | | ⏳ |

---

### 場景 7: 成本驗證

**目標**: 驗證處理成本符合預期

| 步驟 | 操作 | 預期結果 | 實際結果 | 狀態 |
|------|------|---------|---------|------|
| 7.1 | 處理 1 頁 Native PDF | 成本 ≈ $0.02 | | ⏳ |
| 7.2 | 處理 1 頁 Scanned PDF | 成本 ≈ $0.03 | | ⏳ |
| 7.3 | 處理 5 頁 Native PDF | 成本 ≈ $0.10 | | ⏳ |

---

## 測試數據需求

### 必要測試文件

| 類型 | 文件名建議 | 特徵 | 用途 |
|------|-----------|------|------|
| Native PDF | `native-invoice-maersk.pdf` | 有 LOGO、發票結構 | 場景 1, 4.1 |
| Native PDF | `native-invoice-dhl.pdf` | 有標題、Air Freight | 場景 1, 5.2 |
| Native PDF | `native-debit-note.pdf` | Debit Note 類型 | 場景 5.3 |
| Scanned PDF | `scanned-invoice-01.pdf` | 掃描版發票 | 場景 2 |
| Scanned PDF | `scanned-invoice-02.pdf` | 不同發行者 | 場景 2 |
| Image | `photo-invoice-01.jpg` | 拍照發票 | 場景 3 |
| Image | `photo-invoice-02.png` | PNG 格式 | 場景 3 |
| Corrupted | `corrupted-file.pdf` | 損壞文件 | 場景 6.3 |

**存放位置**: `uploads/test-samples/` (不提交 Git)

---

## 測試執行方式

### 方式 A: 透過 API 直接測試

```bash
# 1. 上傳文件
curl -X POST http://localhost:3000/api/v1/documents/upload \
  -F "file=@test-native-invoice.pdf" \
  -H "Authorization: Bearer {token}"

# 2. 觸發批次處理
curl -X POST http://localhost:3000/api/v1/batch/process \
  -H "Content-Type: application/json" \
  -d '{"fileIds": ["file-id-1", "file-id-2"]}'

# 3. 查詢處理結果
curl http://localhost:3000/api/v1/documents/{id}/extraction-result
```

### 方式 B: 透過 UI 測試

1. 訪問 `http://localhost:3000/batch-upload`
2. 選擇多個測試文件上傳
3. 觀察處理進度
4. 檢查結果頁面

### 方式 C: 單元測試腳本

```bash
# 執行處理相關單元測試
npm run test -- --grep "batch-processor"
npm run test -- --grep "gpt-vision"
npm run test -- --grep "processing-router"
```

---

## 日誌檢查點

測試時需要在控制台確認以下日誌：

### Native PDF 處理

```
[DUAL_PROCESSING] Starting dual processing for: {filename}
[DUAL_PROCESSING] Phase 1: GPT Vision classification...
[DUAL_PROCESSING] Classification complete: issuer={name}, type={type}
[DUAL_PROCESSING] Phase 2: Azure DI data extraction...
[DUAL_PROCESSING] Data extraction complete: {pages} pages
```

### Scanned PDF / Image 處理

```
[GPT_VISION] Processing with GPT Vision: {filename}
[GPT_VISION] Extraction complete: {pages} pages
```

---

## 風險與緩解

| 風險 | 影響 | 可能性 | 緩解措施 |
|------|------|--------|---------|
| Azure API 限流 | 測試中斷 | 中 | 使用測試配額，分批測試 |
| 測試數據不足 | 覆蓋率不夠 | 中 | 收集多種發行者的真實發票 |
| GPT Vision 回應不穩定 | 結果不一致 | 低 | 多次測試取平均 |
| 網絡問題 | 超時錯誤 | 低 | 確保穩定網絡 |

---

## 測試結果摘要

| 項目 | 結果 |
|------|------|
| 總場景數 | 7 |
| 總測試步驟 | 36 |
| 通過 | - |
| 失敗 | - |
| 阻塞 | - |
| 通過率 | -% |

---

## 發現的問題

| 問題編號 | 描述 | 嚴重度 | 狀態 |
|---------|------|--------|------|
| - | - | - | - |

---

## 結論與建議

[待測試完成後填寫]

---

## 附錄：API 響應範例

### 預期的 DUAL_PROCESSING 輸出

```json
{
  "method": "DUAL_PROCESSING",
  "fileName": "test-invoice.pdf",
  "processedAt": "2025-12-27T10:00:00.000Z",
  "pages": 1,
  "invoiceData": {
    "vendorName": "Maersk Line",
    "customerName": "ABC Trading Co",
    "invoiceNumber": "INV-2025-001",
    "invoiceDate": "2025-12-20",
    "totalAmount": 5000.00,
    "currency": "USD",
    "lineItems": [
      {
        "description": "Ocean Freight - HKG to LAX",
        "amount": 4500.00
      },
      {
        "description": "Terminal Handling Charge",
        "amount": 500.00
      }
    ]
  },
  "documentIssuer": {
    "name": "Maersk Line",
    "identificationMethod": "LOGO",
    "confidence": 95
  },
  "documentFormat": {
    "documentType": "INVOICE",
    "documentSubtype": "OCEAN"
  },
  "classificationSuccess": true,
  "confidence": 92
}
```

---

**建立者**: AI Assistant
**最後更新**: 2025-12-27
