# Sprint 76: File Download Feature

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 76 |
| **Phase** | 20 - File Attachment Support |
| **Duration** | 3-4 days |
| **Story Points** | 16 pts |
| **Status** | 待開始 |

---

## Sprint Goal

實現 AI 助手介面的文件下載功能，讓用戶可以下載 Claude SDK 生成的文件。

---

## User Stories

### S76-1: 後端文件下載 API (4 pts)

**Description**: 創建文件下載和列表的 REST API。

**Acceptance Criteria**:
- [ ] GET /api/v1/files/{id} 獲取文件元數據
- [ ] GET /api/v1/files/{id}/download 下載文件
- [ ] GET /api/v1/files 列出用戶文件
- [ ] DELETE /api/v1/files/{id} 刪除文件
- [ ] 用戶只能訪問自己的文件

**Technical Details**:
```python
# backend/src/api/v1/files/routes.py
@router.get("/{file_id}")
async def get_file_metadata(
    file_id: str,
    user_id: str = Depends(get_current_user_id),
):
    # Return FileMetadata

@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    user_id: str = Depends(get_current_user_id),
):
    # Return FileResponse

@router.get("/")
async def list_files(
    user_id: str = Depends(get_current_user_id),
    session_id: Optional[str] = None,
):
    # Return list of FileMetadata

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user_id: str = Depends(get_current_user_id),
):
    # Delete file and return success
```

**Files to Modify**:
- `backend/src/api/v1/files/routes.py`
- `backend/src/api/v1/files/schemas.py`
- `backend/src/domain/files/service.py`

---

### S76-2: FileMessage 組件 (5 pts)

**Description**: 創建在對話中顯示文件的組件。

**Acceptance Criteria**:
- [ ] 顯示文件圖標和名稱
- [ ] 顯示文件大小
- [ ] 下載按鈕
- [ ] 支援不同文件類型的圖標
- [ ] 加載狀態顯示

**Technical Details**:
```tsx
// frontend/src/components/unified-chat/FileMessage.tsx
interface FileMessageProps {
  file: GeneratedFile;
  onDownload: (fileId: string) => void;
}

interface GeneratedFile {
  id: string;
  name: string;
  size: number;
  mimeType: string;
  createdAt: string;
  downloadUrl?: string;
}
```

**Files to Create**:
- `frontend/src/components/unified-chat/FileMessage.tsx`

---

### S76-3: 文件類型渲染器 (4 pts)

**Description**: 為不同文件類型提供預覽渲染。

**Acceptance Criteria**:
- [ ] 圖片文件顯示預覽
- [ ] 代碼文件語法高亮
- [ ] 文本文件直接顯示
- [ ] PDF 顯示下載按鈕
- [ ] 其他文件顯示通用圖標

**Technical Details**:
```tsx
// frontend/src/components/unified-chat/FileRenderer.tsx
interface FileRendererProps {
  file: GeneratedFile;
  content?: string;  // For text/code preview
  preview?: string;  // For image preview (base64 or URL)
}

// Render based on file type
switch (getFileCategory(file.mimeType)) {
  case 'image':
    return <ImagePreview src={preview} alt={file.name} />;
  case 'code':
    return <CodePreview code={content} language={getLanguage(file.name)} />;
  case 'text':
    return <TextPreview content={content} />;
  default:
    return <GenericFileCard file={file} />;
}
```

**Files to Create**:
- `frontend/src/components/unified-chat/FileRenderer.tsx`
- `frontend/src/components/unified-chat/renderers/ImagePreview.tsx`
- `frontend/src/components/unified-chat/renderers/CodePreview.tsx`
- `frontend/src/components/unified-chat/renderers/TextPreview.tsx`

---

### S76-4: ChatArea 整合 (3 pts)

**Description**: 在對話區域顯示 Claude 生成的文件。

**Acceptance Criteria**:
- [ ] 解析 Claude 輸出中的文件引用
- [ ] 在訊息中顯示文件組件
- [ ] 點擊下載觸發 API 調用
- [ ] 處理下載錯誤

**Technical Details**:
```tsx
// Update ChatArea.tsx to handle file messages
{message.files?.map((file) => (
  <FileMessage
    key={file.id}
    file={file}
    onDownload={handleDownload}
  />
))}

// Update ag-ui types
interface ChatMessage {
  // ... existing fields
  files?: GeneratedFile[];
}
```

**Files to Modify**:
- `frontend/src/components/unified-chat/ChatArea.tsx`
- `frontend/src/components/unified-chat/MessageBubble.tsx`
- `frontend/src/types/ag-ui.ts`

---

## Claude SDK 文件輸出處理

### 文件輸出識別

Claude SDK 執行代碼時可能生成文件。需要從輸出中識別：

```python
# backend/src/integrations/claude_sdk/client.py
def parse_file_outputs(self, response) -> List[GeneratedFile]:
    """Parse file outputs from Claude SDK response."""
    files = []
    for output in response.outputs:
        if output.type == "file":
            files.append(GeneratedFile(
                id=output.file_id,
                name=output.filename,
                path=output.path,
                size=output.size,
                mime_type=output.mime_type,
            ))
    return files
```

### AG-UI 事件

```python
# backend/src/integrations/ag_ui/bridge.py
async def emit_file_generated(self, file: GeneratedFile):
    """Emit file generated event to frontend."""
    await self.emit_event({
        "type": "FILE_GENERATED",
        "file": {
            "id": file.id,
            "name": file.name,
            "size": file.size,
            "mimeType": file.mime_type,
            "downloadUrl": f"/api/v1/files/{file.id}/download",
        }
    })
```

---

## Dependencies

### Internal
- Sprint 75: File upload infrastructure
- Phase 17: Sandbox configuration

### External
- None (uses existing syntax highlighting if available)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 大文件下載慢 | Medium | 流式傳輸 + 進度顯示 |
| 預覽消耗內存 | Medium | 限制預覽大小 |
| 文件過期 | Low | 設置 TTL + 清理機制 |

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] TypeScript 編譯通過
- [ ] 手動測試：Claude 生成文件 → 顯示在對話 → 可下載
- [ ] 圖片和代碼文件可預覽

---

**Created**: 2026-01-09
**Story Points**: 16 pts
