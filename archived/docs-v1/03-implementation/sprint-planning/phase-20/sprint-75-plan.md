# Sprint 75: File Upload Feature

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 75 |
| **Phase** | 20 - File Attachment Support |
| **Duration** | 3-4 days |
| **Story Points** | 18 pts |
| **Status** | 待開始 |

---

## Sprint Goal

實現 AI 助手介面的文件上傳功能，讓用戶可以上傳文件給 Claude SDK 分析。

---

## User Stories

### S75-1: 後端文件上傳 API (5 pts)

**Description**: 創建文件上傳和管理的 REST API。

**Acceptance Criteria**:
- [ ] POST /api/v1/files/upload 端點
- [ ] 支援 multipart/form-data
- [ ] 文件大小限制 (text: 10MB, image: 20MB, pdf: 25MB)
- [ ] 文件類型驗證
- [ ] 用戶隔離存儲
- [ ] 返回文件 ID 和元數據

**Technical Details**:
```python
# backend/src/api/v1/files/routes.py
@router.post("/upload")
async def upload_file(
    file: UploadFile,
    user_id: str = Depends(get_current_user_id),
):
    # Validate file type and size
    # Store to data/uploads/{user_id}/{file_id}.ext
    # Return FileMetadata
```

**Files to Create**:
- `backend/src/api/v1/files/__init__.py`
- `backend/src/api/v1/files/routes.py`
- `backend/src/api/v1/files/schemas.py`
- `backend/src/domain/files/service.py`
- `backend/src/domain/files/storage.py`

---

### S75-2: 前端 FileUpload 組件 (5 pts)

**Description**: 創建文件上傳組件，支援點擊和拖放。

**Acceptance Criteria**:
- [ ] 點擊上傳
- [ ] 拖放上傳
- [ ] 上傳進度顯示
- [ ] 文件類型過濾
- [ ] 錯誤處理和提示

**Technical Details**:
```tsx
// frontend/src/components/unified-chat/FileUpload.tsx
interface FileUploadProps {
  onUpload: (files: File[]) => void;
  onProgress?: (progress: number) => void;
  accept?: string;
  maxSize?: number;
  multiple?: boolean;
  disabled?: boolean;
}
```

**Files to Create**:
- `frontend/src/components/unified-chat/FileUpload.tsx`
- `frontend/src/api/endpoints/files.ts`
- `frontend/src/hooks/useFileUpload.ts`

---

### S75-3: 附件預覽組件 (3 pts)

**Description**: 顯示已選擇/上傳的附件列表。

**Acceptance Criteria**:
- [ ] 顯示文件名和大小
- [ ] 圖片顯示縮略圖
- [ ] 顯示文件類型圖標
- [ ] 可移除附件
- [ ] 上傳中顯示進度條

**Technical Details**:
```tsx
// frontend/src/components/unified-chat/AttachmentPreview.tsx
interface AttachmentPreviewProps {
  attachments: Attachment[];
  onRemove: (id: string) => void;
  uploading?: boolean;
  progress?: number;
}

interface Attachment {
  id: string;
  file: File;
  preview?: string;  // For images
  status: 'pending' | 'uploading' | 'uploaded' | 'error';
  progress?: number;
  error?: string;
}
```

**Files to Create**:
- `frontend/src/components/unified-chat/AttachmentPreview.tsx`

---

### S75-4: ChatInput 整合 (3 pts)

**Description**: 將文件上傳整合到 ChatInput 組件。

**Acceptance Criteria**:
- [ ] 附件按鈕可用
- [ ] 顯示附件預覽區
- [ ] 發送時包含附件
- [ ] 清除已發送的附件

**Technical Details**:
```tsx
// Update ChatInput.tsx
<ChatInput
  onSend={handleSend}
  onAttach={handleAttach}
  attachments={attachments}
  onRemoveAttachment={handleRemoveAttachment}
/>
```

**Files to Modify**:
- `frontend/src/components/unified-chat/ChatInput.tsx`
- `frontend/src/pages/UnifiedChat.tsx`
- `frontend/src/types/unified-chat.ts`

---

### S75-5: Claude SDK 文件分析連接 (2 pts)

**Description**: 將上傳的文件傳遞給 Claude SDK 進行分析。

**Acceptance Criteria**:
- [ ] 文件內容包含在 Claude 請求中
- [ ] 圖片作為 base64 傳遞
- [ ] 文本文件作為內容傳遞
- [ ] 正確處理文件類型

**Technical Details**:
```python
# backend/src/integrations/claude_sdk/client.py
async def send_with_attachments(
    self,
    message: str,
    attachments: List[FileAttachment],
):
    content = [{"type": "text", "text": message}]

    for attachment in attachments:
        if attachment.is_image:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": attachment.mime_type,
                    "data": attachment.base64_data,
                }
            })
        else:
            content.append({
                "type": "text",
                "text": f"File: {attachment.name}\n{attachment.content}"
            })
```

**Files to Modify**:
- `backend/src/integrations/claude_sdk/client.py`
- `backend/src/integrations/ag_ui/bridge.py`

---

## Dependencies

### Internal
- Phase 17: Sandbox configuration (data directories)
- Phase 18: Authentication (user ID for storage)

### External
- `python-multipart` (already installed)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 大文件影響性能 | Medium | 設置合理的大小限制 |
| 惡意文件上傳 | High | 文件類型白名單 + 病毒掃描 |
| 存儲空間不足 | Medium | 定期清理 + 用戶配額 |

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] TypeScript 編譯通過
- [ ] 手動測試：上傳文件 → 發送 → Claude 能分析
- [ ] 文件正確存儲在用戶目錄

---

**Created**: 2026-01-09
**Story Points**: 18 pts
