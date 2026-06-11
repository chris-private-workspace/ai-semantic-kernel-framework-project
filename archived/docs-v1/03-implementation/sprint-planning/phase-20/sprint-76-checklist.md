# Sprint 76 Checklist: File Download Feature

## Sprint Status

| Metric | Value |
|--------|-------|
| **Total Stories** | 4 |
| **Total Points** | 16 pts |
| **Completed** | 4 |
| **In Progress** | 0 |
| **Status** | ✅ 已完成 |
| **Completed Date** | 2026-01-11 |

---

## Stories

### S76-1: 後端文件下載 API (4 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 添加 GET /{file_id} 端點 - 獲取元數據
- [ ] 添加 GET /{file_id}/download 端點 - 下載文件
- [ ] 添加 GET / 端點 - 列出文件
- [ ] 添加 DELETE /{file_id} 端點 - 刪除文件
- [ ] 實現用戶權限驗證
- [ ] 實現 session_id 過濾
- [ ] 添加相關 schemas
- [ ] 測試所有端點

**Acceptance Criteria**:
- [ ] 可獲取文件元數據
- [ ] 可下載文件
- [ ] 可列出用戶的文件
- [ ] 可刪除文件
- [ ] 用戶只能訪問自己的文件

---

### S76-2: FileMessage 組件 (5 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 創建 `FileMessage.tsx` 組件
- [ ] 實現文件圖標顯示（基於類型）
- [ ] 實現文件名和大小顯示
- [ ] 實現下載按鈕
- [ ] 實現下載中狀態
- [ ] 實現下載完成狀態
- [ ] 添加到 unified-chat/index.ts 導出

**Acceptance Criteria**:
- [ ] 顯示正確的文件類型圖標
- [ ] 顯示文件名和大小
- [ ] 下載按鈕可用
- [ ] 下載中顯示加載狀態
- [ ] 下載完成顯示成功狀態

---

### S76-3: 文件類型渲染器 (4 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 創建 `FileRenderer.tsx` 主組件
- [ ] 創建 `renderers/ImagePreview.tsx` - 圖片預覽
- [ ] 創建 `renderers/CodePreview.tsx` - 代碼預覽
- [ ] 創建 `renderers/TextPreview.tsx` - 文本預覽
- [ ] 實現文件類型判斷邏輯
- [ ] 實現預覽大小限制
- [ ] 添加展開/收起功能

**Acceptance Criteria**:
- [ ] 圖片文件顯示預覽
- [ ] 代碼文件有語法高亮
- [ ] 文本文件直接顯示
- [ ] 大文件顯示「展開」選項
- [ ] 其他文件顯示下載卡片

---

### S76-4: ChatArea 整合 (3 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 更新 `ag-ui.ts` types - 添加 files 欄位
- [ ] 更新 `useUnifiedChat.ts` - 解析 FILE_GENERATED 事件
- [ ] 更新 `MessageBubble.tsx` - 渲染文件列表
- [ ] 更新 `ChatArea.tsx` - 傳遞 onDownload 處理器
- [ ] 實現 handleDownload 函數
- [ ] 實現文件下載 API 調用
- [ ] 處理下載錯誤

**Acceptance Criteria**:
- [ ] Claude 生成文件時顯示在訊息中
- [ ] 點擊下載觸發 API
- [ ] 下載成功保存文件
- [ ] 下載失敗顯示錯誤

---

## Files Summary

### New Files (Frontend)
| File | Story | Description |
|------|-------|-------------|
| `frontend/src/components/unified-chat/FileMessage.tsx` | S76-2 | File display component |
| `frontend/src/components/unified-chat/FileRenderer.tsx` | S76-3 | Type-based renderer |
| `frontend/src/components/unified-chat/renderers/ImagePreview.tsx` | S76-3 | Image preview |
| `frontend/src/components/unified-chat/renderers/CodePreview.tsx` | S76-3 | Code preview |
| `frontend/src/components/unified-chat/renderers/TextPreview.tsx` | S76-3 | Text preview |

### Modified Files (Backend)
| File | Story | Changes |
|------|-------|---------|
| `backend/src/api/v1/files/routes.py` | S76-1 | Add download/list/delete endpoints |
| `backend/src/api/v1/files/schemas.py` | S76-1 | Add response schemas |
| `backend/src/domain/files/service.py` | S76-1 | Add service methods |
| `backend/src/integrations/claude_sdk/client.py` | S76-4 | Parse file outputs |
| `backend/src/integrations/ag_ui/bridge.py` | S76-4 | Emit FILE_GENERATED event |

### Modified Files (Frontend)
| File | Story | Changes |
|------|-------|---------|
| `frontend/src/types/ag-ui.ts` | S76-4 | Add GeneratedFile type |
| `frontend/src/hooks/useUnifiedChat.ts` | S76-4 | Handle FILE_GENERATED event |
| `frontend/src/components/unified-chat/ChatArea.tsx` | S76-4 | Pass onDownload |
| `frontend/src/components/unified-chat/MessageBubble.tsx` | S76-4 | Render files |
| `frontend/src/components/unified-chat/index.ts` | S76-2 | Export new components |
| `frontend/src/api/endpoints/files.ts` | S76-1 | Add download functions |

---

## Verification Checklist

### Functional Tests
- [ ] Claude 生成代碼文件 → 顯示在對話
- [ ] Claude 生成圖片 → 顯示預覽
- [ ] Claude 生成數據文件 → 顯示下載選項
- [ ] 點擊下載 → 文件保存到本地
- [ ] 代碼文件 → 語法高亮顯示
- [ ] 圖片文件 → 可點擊放大

### Error Handling
- [ ] 文件不存在 → 顯示錯誤
- [ ] 無權訪問 → 顯示錯誤
- [ ] 下載失敗 → 顯示重試選項
- [ ] 預覽加載失敗 → 顯示下載按鈕替代

### Edge Cases
- [ ] 大文件（>5MB）處理
- [ ] 特殊字符文件名
- [ ] 同名文件處理
- [ ] 並發下載

---

## Integration Testing

### 完整流程測試
1. 上傳文件給 Claude 分析
2. Claude 處理後生成新文件
3. 新文件顯示在對話中
4. 下載新文件到本地
5. 驗證文件內容正確

### 測試場景
```
用戶：請分析這個 CSV 文件並生成圖表
→ 上傳 data.csv
→ Claude 分析數據
→ Claude 生成 chart.png
→ 對話中顯示圖表預覽
→ 用戶點擊下載
→ 保存 chart.png 到本地
```

---

**Last Updated**: 2026-01-09
