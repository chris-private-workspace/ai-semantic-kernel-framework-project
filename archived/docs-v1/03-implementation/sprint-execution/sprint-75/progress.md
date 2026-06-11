# Sprint 75 Progress: File Upload Feature

> **Phase 20**: File Attachment Support
> **Sprint 目標**: 實現 AI 助手介面的文件上傳功能

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 75 |
| 計劃點數 | 18 Story Points |
| 完成點數 | 18 Story Points |
| 開始日期 | 2026-01-09 |
| 完成日期 | 2026-01-09 |
| Phase | 20 - File Attachment Support |
| 前置條件 | Sprint 74 完成, Bug Fixes 完成 |

---

## Bug Fixes (Pre-Sprint)

| Bug | 狀態 | 說明 |
|-----|------|------|
| S75-BF-1 | ✅ | 用戶隔離修復 |
| S75-BF-2 | ✅ | 重新登入後對話記錄消失 |
| S75-BF-3 | ✅ | 重新登入後訊息不載入 |
| S75-BF-4 | ✅ | 切換對話時 AI 回覆跑到錯誤對話 |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S75-1 | 後端文件上傳 API | 5 | ✅ 完成 | 100% |
| S75-2 | 前端 FileUpload 組件 | 5 | ✅ 完成 | 100% |
| S75-3 | 附件預覽組件 | 3 | ✅ 完成 | 100% |
| S75-4 | ChatInput 整合 | 3 | ✅ 完成 | 100% |
| S75-5 | Claude SDK 文件分析連接 | 2 | ✅ 完成 | 100% |

**整體進度**: 18/18 pts (100%) ✅

---

## 詳細進度記錄

### S75-1: 後端文件上傳 API (5 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `backend/src/api/v1/files/__init__.py`
- [x] 創建 `backend/src/api/v1/files/schemas.py` - FileUploadResponse, FileMetadata
- [x] 創建 `backend/src/domain/files/__init__.py`
- [x] 創建 `backend/src/domain/files/storage.py` - FileStorage class
- [x] 創建 `backend/src/domain/files/service.py` - FileService class
- [x] 創建 `backend/src/api/v1/files/routes.py` - POST /upload endpoint
- [x] 添加文件類型驗證 (whitelist)
- [x] 添加文件大小驗證
- [x] 添加用戶隔離存儲邏輯
- [x] 註冊路由到 api/v1/__init__.py
- [x] 創建 `backend/src/api/v1/auth/dependencies.py` - get_current_user_id

**新增檔案**:
- `backend/src/api/v1/files/__init__.py` - Package init
- `backend/src/api/v1/files/schemas.py` - Pydantic schemas (FileMetadata, FileUploadResponse, etc.)
- `backend/src/api/v1/files/routes.py` - API routes (POST /upload, GET /, GET /{id}, DELETE /{id})
- `backend/src/domain/files/__init__.py` - Package init
- `backend/src/domain/files/storage.py` - FileStorage class
- `backend/src/domain/files/service.py` - FileService class
- `backend/src/api/v1/auth/dependencies.py` - get_current_user_id helper

**API 端點**:
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/files/upload` | Upload file |
| GET | `/api/v1/files/` | List user files |
| GET | `/api/v1/files/{file_id}` | Get file metadata |
| GET | `/api/v1/files/{file_id}/content` | Download file |
| DELETE | `/api/v1/files/{file_id}` | Delete file |

---

### S75-2: 前端 FileUpload 組件 (5 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `frontend/src/api/endpoints/files.ts` - API client
- [x] 創建 `frontend/src/hooks/useFileUpload.ts` - upload logic
- [x] 創建 `frontend/src/components/unified-chat/FileUpload.tsx` 組件
- [x] 實現點擊上傳功能
- [x] 實現拖放上傳功能
- [x] 實現進度條顯示
- [x] 添加文件類型過濾
- [x] 添加錯誤處理
- [x] 更新 `frontend/src/api/endpoints/index.ts` 導出

**新增檔案**:
- `frontend/src/api/endpoints/files.ts` - Files API client with XHR progress tracking
- `frontend/src/hooks/useFileUpload.ts` - useFileUpload hook for attachment management
- `frontend/src/components/unified-chat/FileUpload.tsx` - FileUpload, AttachButton, HiddenFileInput

**FileUpload 組件功能**:
- 點擊選擇文件
- 拖放上傳
- 文件類型過濾
- 錯誤提示

**useFileUpload Hook API**:
```typescript
interface UseFileUploadReturn {
  attachments: Attachment[];
  isUploading: boolean;
  addFiles: (files: File[]) => void;
  removeAttachment: (id: string) => void;
  uploadAll: () => Promise<void>;
  clearAttachments: () => void;
  getUploadedFileIds: () => string[];
}
```

---

### S75-3: 附件預覽組件 (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `frontend/src/components/unified-chat/AttachmentPreview.tsx` 組件
- [x] 實現文件名和大小顯示
- [x] 實現圖片縮略圖預覽
- [x] 實現文件類型圖標
- [x] 實現移除按鈕
- [x] 實現上傳中進度顯示
- [x] 創建 CompactAttachmentPreview for ChatInput

**新增檔案**:
- `frontend/src/components/unified-chat/AttachmentPreview.tsx`

**組件結構**:
- `AttachmentPreview` - 完整預覽列表
- `AttachmentItem` - 單個附件項目
- `CompactAttachmentPreview` - ChatInput 用的緊湊版

---

### S75-4: ChatInput 整合 (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 更新 `frontend/src/types/unified-chat.ts` - 添加 Attachment 類型
- [x] 更新 `frontend/src/components/unified-chat/ChatInput.tsx` - 整合 CompactAttachmentPreview
- [x] 更新 `frontend/src/pages/UnifiedChat.tsx` - 添加 useFileUpload hook
- [x] 實現 handleAttach 處理器
- [x] 發送時包含附件 ID 列表
- [x] 發送後清除附件

**修改檔案**:
- `frontend/src/types/unified-chat.ts` - 添加 Attachment, AttachmentStatus 類型
- `frontend/src/components/unified-chat/ChatInput.tsx` - 整合 CompactAttachmentPreview
- `frontend/src/pages/UnifiedChat.tsx` - 添加 useFileUpload 和 attachment handlers
- `frontend/src/components/unified-chat/index.ts` - 導出新組件

**新增類型**:
```typescript
type AttachmentStatus = 'pending' | 'uploading' | 'uploaded' | 'error';

interface Attachment {
  id: string;
  file: File;
  preview?: string;
  status: AttachmentStatus;
  progress?: number;
  error?: string;
  serverFileId?: string;
}
```

---

### S75-5: Claude SDK 文件分析連接 (2 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 更新 `backend/src/integrations/claude_sdk/client.py` - 添加 send_with_attachments
- [x] 更新 `backend/src/integrations/claude_sdk/query.py` - 添加 execute_query_with_attachments
- [x] 更新 `backend/src/integrations/ag_ui/bridge.py` - RunAgentInput 添加 file_ids

**修改檔案**:
- `backend/src/integrations/claude_sdk/client.py` - 添加 `send_with_attachments` 方法
- `backend/src/integrations/claude_sdk/query.py` - 添加 `build_content_with_attachments` 和 `execute_query_with_attachments`
- `backend/src/integrations/ag_ui/bridge.py` - RunAgentInput 添加 `file_ids` 欄位

**Claude API 整合**:
```python
# Image attachment format
{
    "type": "image",
    "source": {
        "type": "base64",
        "media_type": "image/png",
        "data": "<base64_data>",
    },
}

# Text file attachment format
{
    "type": "text",
    "text": "--- File: filename ---\n<content>\n--- End of filename ---",
}
```

---

## 新增/修改檔案總覽

### 新增檔案 (Backend - 7 files)

| 檔案 | Story | 說明 |
|------|-------|------|
| `backend/src/api/v1/files/__init__.py` | S75-1 | Package init |
| `backend/src/api/v1/files/routes.py` | S75-1 | File API routes |
| `backend/src/api/v1/files/schemas.py` | S75-1 | Pydantic schemas |
| `backend/src/domain/files/__init__.py` | S75-1 | Package init |
| `backend/src/domain/files/service.py` | S75-1 | File service |
| `backend/src/domain/files/storage.py` | S75-1 | File storage |
| `backend/src/api/v1/auth/dependencies.py` | S75-1 | Auth dependencies |

### 新增檔案 (Frontend - 4 files)

| 檔案 | Story | 說明 |
|------|-------|------|
| `frontend/src/api/endpoints/files.ts` | S75-2 | Files API client |
| `frontend/src/hooks/useFileUpload.ts` | S75-2 | Upload hook |
| `frontend/src/components/unified-chat/FileUpload.tsx` | S75-2 | Upload component |
| `frontend/src/components/unified-chat/AttachmentPreview.tsx` | S75-3 | Preview component |

### 修改檔案

| 檔案 | Story | 說明 |
|------|-------|------|
| `backend/src/api/v1/__init__.py` | S75-1 | Register files router |
| `backend/src/integrations/claude_sdk/client.py` | S75-5 | Add send_with_attachments |
| `backend/src/integrations/claude_sdk/query.py` | S75-5 | Add attachment query |
| `backend/src/integrations/ag_ui/bridge.py` | S75-5 | Add file_ids to RunAgentInput |
| `frontend/src/pages/UnifiedChat.tsx` | S75-4 | Attachment state |
| `frontend/src/components/unified-chat/ChatInput.tsx` | S75-4 | Connect handlers |
| `frontend/src/components/unified-chat/index.ts` | S75-2,3 | Export new components |
| `frontend/src/types/unified-chat.ts` | S75-4 | Attachment types |
| `frontend/src/api/endpoints/index.ts` | S75-2 | Export files API |

---

## 技術備註

### 文件類型與大小限制

| 類別 | MIME Types | 最大大小 |
|------|-----------|----------|
| 文本 | text/*, .md, .json, .csv, code files | 10MB |
| 圖片 | image/jpeg, image/png, image/gif, image/webp | 20MB |
| PDF | application/pdf | 25MB |

### 存儲路徑結構

```
backend/data/uploads/
└── {user_id}/
    └── {file_id}.{ext}
```

### 上傳流程

```
[用戶選擇文件]
    │
    ▼
addFiles() → useFileUpload
    │
    ▼
uploadAll() → XHR with progress
    │
    ▼
POST /api/v1/files/upload
    │
    ▼
FileService.upload_file()
    │
    ├── validate_file() - 類型/大小檢查
    │
    └── storage.save_file() - 存儲到用戶目錄
    │
    ▼
返回 FileUploadResponse
    │
    ▼
更新 attachment.serverFileId
```

---

## 驗證清單

### 功能測試
- [x] 後端 API 路由註冊成功
- [x] TypeScript 編譯通過 (前端)
- [x] Python 導入成功 (後端)

### 待手動測試
- [ ] 可選擇單個文件上傳
- [ ] 可選擇多個文件上傳
- [ ] 可拖放上傳
- [ ] 上傳進度正確顯示
- [ ] 圖片顯示縮略圖
- [ ] 可移除已選擇的附件
- [ ] 發送訊息時附件一起發送
- [ ] Claude 能分析上傳的圖片
- [ ] Claude 能分析上傳的文本文件

### 錯誤處理
- [ ] 超過大小限制時顯示錯誤
- [ ] 不支援的文件類型顯示錯誤
- [ ] 上傳失敗時顯示錯誤

---

**更新日期**: 2026-01-09
**Sprint 狀態**: ✅ 完成
**Phase 20 狀態**: Sprint 75 完成，待 Sprint 76
