# Sprint 76 Progress: File Download Feature

> **Phase 20**: File Attachment Support
> **Sprint 目標**: 實現 AI 助手介面的文件下載功能

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 76 |
| 計劃點數 | 16 Story Points |
| 完成點數 | 16 Story Points |
| 開始日期 | 2026-01-09 |
| 完成日期 | 2026-01-09 |
| Phase | 20 - File Attachment Support |
| 前置條件 | Sprint 75 完成 |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S76-1 | 後端文件下載 API | 4 | ✅ 完成 | 100% |
| S76-2 | FileMessage 組件 | 5 | ✅ 完成 | 100% |
| S76-3 | 文件類型渲染器 | 4 | ✅ 完成 | 100% |
| S76-4 | ChatArea 整合 | 3 | ✅ 完成 | 100% |

**整體進度**: 16/16 pts (100%) ✅

---

## 詳細進度記錄

### S76-1: 後端文件下載 API (4 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 添加 session_id 過濾到 list 端點
- [x] 添加 GET /{file_id}/download 端點 (別名)
- [x] 更新 FileMetadata schema 添加 session_id 欄位
- [x] 更新前端 files.ts API client

**修改檔案**:
- `backend/src/api/v1/files/routes.py` - 添加 session_id 過濾和 /download 端點
- `backend/src/api/v1/files/schemas.py` - 添加 session_id 欄位
- `backend/src/domain/files/service.py` - 支援 session_id 過濾
- `frontend/src/api/endpoints/files.ts` - 添加下載功能

**新增 API 函數**:
```typescript
// files.ts 新增函數
filesApi.download(fileId)         // 下載文件到本地
filesApi.getDownloadUrl(fileId)   // 獲取下載 URL
filesApi.getContentText(fileId)   // 獲取文本內容
filesApi.getContentBlob(fileId)   // 獲取 Blob 內容
filesApi.listWithSession(sessionId) // 按 session 過濾
```

---

### S76-2: FileMessage 組件 (5 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `FileMessage.tsx` 組件
- [x] 實現文件圖標顯示（基於類型）
- [x] 實現文件名和大小顯示
- [x] 實現下載按鈕
- [x] 實現下載中/成功/錯誤狀態
- [x] 創建 `FileMessageList` 組件
- [x] 創建 `CompactFileMessage` 組件
- [x] 添加到 unified-chat/index.ts 導出

**新增檔案**:
- `frontend/src/components/unified-chat/FileMessage.tsx`

**組件結構**:
```tsx
// FileMessage - 完整文件卡片
interface FileMessageProps {
  file: GeneratedFile;
  onDownload: (fileId: string) => Promise<void>;
}

// FileMessageList - 文件列表
interface FileMessageListProps {
  files: GeneratedFile[];
  onDownload: (fileId: string) => Promise<void>;
}

// CompactFileMessage - 緊湊版（內聯顯示）
interface CompactFileMessageProps {
  file: GeneratedFile;
  onDownload: (fileId: string) => Promise<void>;
}
```

---

### S76-3: 文件類型渲染器 (4 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `FileRenderer.tsx` 主組件
- [x] 創建 `renderers/ImagePreview.tsx` - 圖片預覽
- [x] 創建 `renderers/CodePreview.tsx` - 代碼預覽
- [x] 創建 `renderers/TextPreview.tsx` - 文本預覽
- [x] 實現文件類型判斷邏輯
- [x] 實現預覽大小限制
- [x] 添加展開/收起功能

**新增檔案**:
- `frontend/src/components/unified-chat/FileRenderer.tsx`
- `frontend/src/components/unified-chat/renderers/index.ts`
- `frontend/src/components/unified-chat/renderers/ImagePreview.tsx`
- `frontend/src/components/unified-chat/renderers/CodePreview.tsx`
- `frontend/src/components/unified-chat/renderers/TextPreview.tsx`

**預覽功能**:

| 文件類型 | 渲染器 | 功能 |
|----------|--------|------|
| 圖片 | ImagePreview | 縮略圖 + 全屏放大 + 縮放 |
| 代碼 | CodePreview | 語法高亮 + 行號 + 複製 |
| 文本 | TextPreview | 搜索 + 展開/收起 |
| PDF/其他 | GenericFileCard | 下載按鈕 |

---

### S76-4: ChatArea 整合 (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 更新 `ag-ui.ts` types - 添加 GeneratedFile 和 files 欄位
- [x] 更新 `MessageBubble.tsx` - 渲染文件列表
- [x] 更新 `MessageList.tsx` - 傳遞 onDownload
- [x] 更新 `ChatArea.tsx` - 傳遞 onDownload 處理器
- [x] 更新 `unified-chat.ts` types - ChatAreaProps 添加 onDownload
- [x] 實現 handleDownload 函數
- [x] 連接 filesApi.download

**修改檔案**:
- `frontend/src/types/ag-ui.ts` - 添加 GeneratedFile, ChatMessage.files
- `frontend/src/types/unified-chat.ts` - ChatAreaProps.onDownload
- `frontend/src/components/ag-ui/chat/MessageBubble.tsx` - 渲染 FileMessageList
- `frontend/src/components/unified-chat/MessageList.tsx` - 傳遞 onDownload
- `frontend/src/components/unified-chat/ChatArea.tsx` - 接收傳遞 onDownload
- `frontend/src/pages/UnifiedChat.tsx` - handleDownload + filesApi

**整合流程**:
```
UnifiedChat (handleDownload)
    ↓ onDownload
ChatArea
    ↓ onDownload
MessageList
    ↓ onDownload
MessageBubble
    ↓ files prop
FileMessageList
    ↓ onDownload
FileMessage (handleDownload → filesApi.download)
```

---

## 新增/修改檔案總覽

### 新增檔案 (Frontend - 6 files)

| 檔案 | Story | 說明 |
|------|-------|------|
| `frontend/src/components/unified-chat/FileMessage.tsx` | S76-2 | 文件顯示組件 |
| `frontend/src/components/unified-chat/FileRenderer.tsx` | S76-3 | 類型渲染器 |
| `frontend/src/components/unified-chat/renderers/index.ts` | S76-3 | 渲染器導出 |
| `frontend/src/components/unified-chat/renderers/ImagePreview.tsx` | S76-3 | 圖片預覽 |
| `frontend/src/components/unified-chat/renderers/CodePreview.tsx` | S76-3 | 代碼預覽 |
| `frontend/src/components/unified-chat/renderers/TextPreview.tsx` | S76-3 | 文本預覽 |

### 修改檔案 (Backend - 3 files)

| 檔案 | Story | 說明 |
|------|-------|------|
| `backend/src/api/v1/files/routes.py` | S76-1 | 添加 download 端點 |
| `backend/src/api/v1/files/schemas.py` | S76-1 | 添加 session_id |
| `backend/src/domain/files/service.py` | S76-1 | 支援 session_id 過濾 |

### 修改檔案 (Frontend - 7 files)

| 檔案 | Story | 說明 |
|------|-------|------|
| `frontend/src/api/endpoints/files.ts` | S76-1 | 添加下載函數 |
| `frontend/src/types/ag-ui.ts` | S76-4 | GeneratedFile, files 欄位 |
| `frontend/src/types/unified-chat.ts` | S76-4 | ChatAreaProps.onDownload |
| `frontend/src/components/ag-ui/chat/MessageBubble.tsx` | S76-4 | 渲染文件 |
| `frontend/src/components/unified-chat/MessageList.tsx` | S76-4 | 傳遞 onDownload |
| `frontend/src/components/unified-chat/ChatArea.tsx` | S76-4 | 傳遞 onDownload |
| `frontend/src/pages/UnifiedChat.tsx` | S76-4 | handleDownload |

---

## 技術備註

### 文件類型判斷

```typescript
function getFileType(mimeType: string, filename?: string): FileType {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType === 'application/pdf') return 'pdf';
  // Code files by extension
  const codeExtensions = ['.py', '.js', '.ts', ...];
  if (filename && codeExtensions.includes(ext)) return 'code';
  if (mimeType.startsWith('text/')) return 'text';
  return 'other';
}
```

### 下載流程

```
[用戶點擊下載]
    │
    ▼
FileMessage.handleDownload()
    │
    ▼
filesApi.download(fileId)
    │
    ▼
fetch(getDownloadUrl(fileId))
    │
    ▼
response.blob() → createObjectURL → <a download>
    │
    ▼
[文件保存到本地]
```

### 預覽大小限制

| 渲染器 | 預設行數 | 可展開 |
|--------|----------|--------|
| CodePreview | 20 行 | ✅ |
| TextPreview | 30 行 | ✅ |
| ImagePreview | - | 全屏放大 |

---

## 驗證清單

### 功能測試
- [x] 後端 API 路由正確
- [x] TypeScript 編譯通過 (前端)
- [x] Python 導入成功 (後端)

### 待手動測試
- [ ] Claude 生成代碼文件 → 顯示在對話
- [ ] Claude 生成圖片 → 顯示預覽
- [ ] Claude 生成數據文件 → 顯示下載選項
- [ ] 點擊下載 → 文件保存到本地
- [ ] 代碼文件 → 語法高亮顯示
- [ ] 圖片文件 → 可點擊放大

### 錯誤處理
- [ ] 文件不存在 → 顯示錯誤
- [ ] 無權訪問 → 顯示錯誤
- [ ] 下載失敗 → 顯示重試選項

---

**更新日期**: 2026-01-09
**Sprint 狀態**: ✅ 完成
**Phase 20 狀態**: Sprint 75-76 完成
