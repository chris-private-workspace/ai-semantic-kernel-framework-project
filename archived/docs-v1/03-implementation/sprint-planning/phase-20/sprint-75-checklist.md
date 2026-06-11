# Sprint 75 Checklist: File Upload Feature

## Sprint Status

| Metric | Value |
|--------|-------|
| **Total Stories** | 5 |
| **Total Points** | 18 pts |
| **Completed** | 5 |
| **In Progress** | 0 |
| **Status** | ✅ 已完成 |
| **Completed Date** | 2026-01-11 |

---

## Bug Fixes (Pre-Sprint)

### S75-BF-1: 用戶隔離修復 ✅

**Status**: ✅ 已完成 (2026-01-09)

**Issue**: 不同用戶看到相同的對話記錄
**Root Cause**: `useChatThreads` 使用固定 localStorage key，沒有用戶隔離
**Fix**: 將 key 改為 `ipa_chat_threads_{userId}`

---

### S75-BF-2: 重新登入後對話記錄消失 ✅

**Status**: ✅ 已完成 (2026-01-09)

**Issue**: 同一用戶重新登入後看不到之前的對話記錄
**Root Cause**: Race condition - 當 `storageKey` 改變時，兩個 useEffect 同時觸發。`setThreads` 是異步的，新值要到下一個渲染週期才生效，但保存 effect 在當前週期執行時用的是舊的空數組。
**Fix (v2)**: 使用 `useRef` 追蹤載入狀態：
- `isLoadingRef`: 載入中為 true，阻止所有保存
- `lastLoadedKeyRef`: 追蹤已載入的 key，必須匹配 storageKey
- `setTimeout(0)` 確保 refs 在 React 處理狀態更新後才更新

**Verification**: 使用 Playwright 測試：創建對話 → 登出 → 重新登入 → 對話記錄保留 ✓

---

### S75-BF-3: 重新登入後訊息不載入 ✅

**Status**: ✅ 已完成 (2026-01-09)

**Issue**: 重新登入後左側顯示對話記錄，但點擊無反應，右側聊天區域不顯示訊息
**Root Cause**: "Load messages on mount" useEffect 的依賴數組是空的 `[]`，只在組件掛載時運行一次。但此時 `activeThreadId` 還是 `null`（通過另一個 useEffect 從 localStorage 恢復），所以訊息不會被載入。
**Fix**: 將 useEffect 的依賴改為 `[activeThreadId]`，讓它在 activeThreadId 改變時運行，包括從 localStorage 恢復時。

**Verification**: 使用 Playwright 測試：
- 頁面載入：訊息自動載入 ✓
- 登出 → 重新登入：對話記錄和訊息都保留 ✓
- 點擊對話記錄：訊息正確載入 ✓

---

### S75-BF-4: 切換對話時 AI 回覆跑到錯誤對話 ✅

**Status**: ✅ 已完成 (2026-01-09)

**Issue**: 在對話中發送訊息，AI 回覆前切換到另一個對話，AI 回覆會出現在當前（錯誤的）對話視窗
**Root Cause**: 切換對話時沒有取消正在進行的 SSE streaming，導致 AI 回覆繼續寫入到新的 activeThreadId 對應的對話中
**Fix**: 在 `handleSelectThread` 和 `handleNewThread` 中添加 `cancelStream()` 調用：
```typescript
const handleSelectThread = useCallback((threadId: string) => {
  if (isStreaming) {
    cancelStream();  // 取消正在進行的 streaming
  }
  // ... 切換對話邏輯
}, [isStreaming, cancelStream, ...]);
```

**Verification**: 使用 Playwright 測試：
- 發送長訊息（請 AI 寫故事）→ AI 開始回覆 → 立即切換對話 ✓
- 切換後的對話不會出現原對話的 AI 回覆 ✓
- 切回原對話：用戶訊息保留，AI 回覆被取消（預期行為）✓

---

## Stories

### S75-1: 後端文件上傳 API (5 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 創建 `backend/src/api/v1/files/` 目錄結構
- [ ] 創建 `schemas.py` - FileUploadResponse, FileMetadata
- [ ] 創建 `backend/src/domain/files/storage.py` - FileStorage class
- [ ] 創建 `backend/src/domain/files/service.py` - FileService class
- [ ] 創建 `routes.py` - POST /upload endpoint
- [ ] 添加文件類型驗證 (whitelist)
- [ ] 添加文件大小驗證
- [ ] 添加用戶隔離存儲邏輯
- [ ] 註冊路由到 main.py
- [ ] 測試 API 端點

**Acceptance Criteria**:
- [ ] POST /api/v1/files/upload 可用
- [ ] 支援 multipart/form-data
- [ ] 文件大小限制正確執行
- [ ] 文件類型白名單正確執行
- [ ] 文件存儲在正確的用戶目錄

---

### S75-2: 前端 FileUpload 組件 (5 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 創建 `frontend/src/api/endpoints/files.ts` - API client
- [ ] 創建 `frontend/src/hooks/useFileUpload.ts` - upload logic
- [ ] 創建 `FileUpload.tsx` 組件
- [ ] 實現點擊上傳功能
- [ ] 實現拖放上傳功能
- [ ] 實現進度條顯示
- [ ] 添加文件類型過濾
- [ ] 添加錯誤處理

**Acceptance Criteria**:
- [ ] 可點擊選擇文件
- [ ] 可拖放文件
- [ ] 顯示上傳進度
- [ ] 過濾不支援的文件類型
- [ ] 顯示錯誤訊息

---

### S75-3: 附件預覽組件 (3 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 創建 `AttachmentPreview.tsx` 組件
- [ ] 實現文件名和大小顯示
- [ ] 實現圖片縮略圖預覽
- [ ] 實現文件類型圖標
- [ ] 實現移除按鈕
- [ ] 實現上傳中進度顯示

**Acceptance Criteria**:
- [ ] 顯示文件名和大小
- [ ] 圖片顯示縮略圖
- [ ] 其他文件顯示圖標
- [ ] 可點擊移除
- [ ] 上傳中顯示進度

---

### S75-4: ChatInput 整合 (3 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 更新 `unified-chat.ts` types - 添加 attachment 相關類型
- [ ] 更新 `ChatInput.tsx` - 連接 onAttach
- [ ] 更新 `UnifiedChat.tsx` - 添加 attachment state 管理
- [ ] 實現 handleAttach 處理器
- [ ] 實現 handleRemoveAttachment 處理器
- [ ] 發送時包含附件 ID 列表
- [ ] 發送後清除附件

**Acceptance Criteria**:
- [ ] 附件按鈕顯示並可點擊
- [ ] 附件預覽區顯示
- [ ] 發送時包含附件
- [ ] 發送後清除附件列表

---

### S75-5: Claude SDK 文件分析連接 (2 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 更新 `claude_sdk/client.py` - 添加附件處理
- [ ] 實現圖片 base64 編碼
- [ ] 實現文本文件內容讀取
- [ ] 更新 `ag_ui/bridge.py` - 傳遞附件
- [ ] 測試 Claude 能讀取文件內容

**Acceptance Criteria**:
- [ ] Claude 能分析圖片
- [ ] Claude 能分析文本文件
- [ ] 文件類型正確識別

---

## Files Summary

### New Files (Backend)
| File | Story | Description |
|------|-------|-------------|
| `backend/src/api/v1/files/__init__.py` | S75-1 | Package init |
| `backend/src/api/v1/files/routes.py` | S75-1 | File API routes |
| `backend/src/api/v1/files/schemas.py` | S75-1 | Pydantic schemas |
| `backend/src/domain/files/__init__.py` | S75-1 | Package init |
| `backend/src/domain/files/service.py` | S75-1 | File service |
| `backend/src/domain/files/storage.py` | S75-1 | File storage |

### New Files (Frontend)
| File | Story | Description |
|------|-------|-------------|
| `frontend/src/api/endpoints/files.ts` | S75-2 | Files API client |
| `frontend/src/hooks/useFileUpload.ts` | S75-2 | Upload hook |
| `frontend/src/components/unified-chat/FileUpload.tsx` | S75-2 | Upload component |
| `frontend/src/components/unified-chat/AttachmentPreview.tsx` | S75-3 | Preview component |

### Modified Files
| File | Story | Changes |
|------|-------|---------|
| `backend/main.py` | S75-1 | Register files router |
| `backend/src/integrations/claude_sdk/client.py` | S75-5 | Add attachment support |
| `backend/src/integrations/ag_ui/bridge.py` | S75-5 | Pass attachments |
| `frontend/src/pages/UnifiedChat.tsx` | S75-4 | Attachment state |
| `frontend/src/components/unified-chat/ChatInput.tsx` | S75-4 | Connect handlers |
| `frontend/src/components/unified-chat/index.ts` | S75-2 | Export new components |
| `frontend/src/types/unified-chat.ts` | S75-4 | Attachment types |

---

## Verification Checklist

### Functional Tests
- [ ] 可選擇單個文件上傳
- [ ] 可選擇多個文件上傳
- [ ] 可拖放上傳
- [ ] 上傳進度正確顯示
- [ ] 圖片顯示縮略圖
- [ ] 可移除已選擇的附件
- [ ] 發送訊息時附件一起發送
- [ ] Claude 能分析上傳的圖片
- [ ] Claude 能分析上傳的文本文件

### Error Handling
- [ ] 超過大小限制時顯示錯誤
- [ ] 不支援的文件類型顯示錯誤
- [ ] 上傳失敗時顯示錯誤
- [ ] 網絡錯誤時有重試選項

---

**Last Updated**: 2026-01-09
