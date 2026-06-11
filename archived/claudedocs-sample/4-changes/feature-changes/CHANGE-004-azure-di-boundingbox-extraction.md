# CHANGE-004: Azure DI BoundingBox 座標提取

> **狀態**: 📋 待審核
> **類型**: Feature Enhancement
> **影響範圍**: Epic 13 - 文件預覽與欄位映射
> **建立日期**: 2026-01-04

---

## 變更摘要

增強 Azure Document Intelligence 提取服務，從 API 響應中提取欄位的 `boundingRegions` 座標資訊，使文件預覽頁面能夠在 PDF 上高亮顯示提取欄位的位置。

---

## 變更原因

### 現況問題

1. **高亮功能已實現但無法使用**
   - `FieldHighlightOverlay.tsx` 組件已完成高亮邏輯
   - 但真實提取結果缺少 `boundingBox` 座標
   - 只有模擬數據能顯示高亮框

2. **Azure DI 已返回座標但未提取**
   - Azure Document Intelligence API 返回 `boundingRegions` 資料
   - 但 `azure-di.service.ts` 目前忽略這些資訊

### 預期效果

用戶上傳真實文件進行提取後，點擊左側欄位列表可在 PDF 預覽中看到對應位置的高亮框。

---

## 技術分析

### Azure DI 響應結構

Azure Document Intelligence 返回的欄位結構包含：

```json
{
  "fields": {
    "InvoiceId": {
      "type": "string",
      "valueString": "INV-001",
      "content": "INV-001",
      "boundingRegions": [
        {
          "pageNumber": 1,
          "polygon": [x1, y1, x2, y2, x3, y3, x4, y4]
        }
      ],
      "confidence": 0.95
    }
  }
}
```

### Polygon 說明

- `polygon` 是 8 個數字的陣列：4 個角的 (x, y) 座標
- 順序：左上 → 右上 → 右下 → 左下
- 座標單位：英寸（需轉換為像素）

### 座標轉換

```
PDF 座標 (英寸) → 像素座標
x_pixel = x_inch * page_width_pixels / page_width_inches
y_pixel = y_inch * page_height_pixels / page_height_inches
```

---

## 影響的文件

| 文件 | 變更類型 | 說明 |
|------|----------|------|
| `src/services/azure-di.service.ts` | 修改 | 提取 boundingRegions 資料 |
| `src/app/api/admin/document-preview-test/extract/route.ts` | 修改 | 傳遞 boundingBox 到響應 |
| `src/types/extracted-field.ts` | 檢查 | 確認 FieldBoundingBox 類型 |

---

## 實作方案

### 方案 A: 直接在 Service 層提取（推薦）

**優點**：
- 修改範圍小
- 座標轉換邏輯集中在一處
- 其他使用 Azure DI 的地方也能受益

**實作步驟**：
1. 修改 `AzureDIExtractionResult` 類型，增加欄位座標
2. 在解析 Azure DI 響應時提取 `boundingRegions`
3. 轉換 polygon 為 `{ page, x, y, width, height }` 格式
4. 修改 `extract/route.ts` 的 `createField()` 包含 boundingBox

### 方案 B: 在 API 層轉換

**優點**：
- 不影響現有 Service 層
- 只在需要的地方處理

**缺點**：
- 如果其他 API 也需要，會有重複代碼

---

## 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| 座標轉換精度問題 | 低 | 使用 Azure DI 原生單位，前端負責最終轉換 |
| 舊數據無 boundingBox | 無 | boundingBox 為選填欄位，不影響現有邏輯 |
| API 響應變大 | 低 | 每個欄位增加約 50 bytes |

---

## 測試計劃

1. **單元測試**：驗證 polygon → boundingBox 轉換邏輯
2. **整合測試**：上傳真實 PDF，確認返回 boundingBox
3. **UI 測試**：確認點擊欄位時高亮框位置正確

---

## 工作量估算

| 任務 | 時間估算 |
|------|----------|
| 修改 azure-di.service.ts | 1-2 小時 |
| 修改 extract/route.ts | 0.5 小時 |
| 測試和調整座標 | 1 小時 |
| **總計** | **2.5-3.5 小時** |

---

## 待確認事項

1. **座標單位**：前端是否已處理英寸→像素轉換？
2. **選擇方案**：方案 A 或 方案 B？
3. **是否需要處理圖片**：此變更只影響 PDF (Azure DI)，圖片 (GPT Vision) 另案處理？

---

## 審核記錄

| 日期 | 審核者 | 決定 | 備註 |
|------|--------|------|------|
| 2026-01-04 | - | 待審核 | 初稿 |

