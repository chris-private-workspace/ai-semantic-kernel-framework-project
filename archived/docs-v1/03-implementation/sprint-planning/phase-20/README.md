# Phase 20: File Attachment Support

## Overview

Phase 20 為 AI 助手介面添加文件附件支援，實現類似 Claude AI / ChatGPT 的文件上傳和下載功能。

## Phase Status

| Status | Value |
|--------|-------|
| **Phase Status** | ✅ 已完成 |
| **Duration** | 2 sprints |
| **Total Story Points** | 34 pts |
| **Completed Date** | 2026-01-11 |

## Sprint Overview

| Sprint | Focus | Story Points | Status | Documents |
|--------|-------|--------------|--------|-----------|
| **Sprint 75** | 文件上傳功能 | 18 pts | ✅ 已完成 | [Plan](sprint-75-plan.md) / [Checklist](sprint-75-checklist.md) |
| **Sprint 76** | 文件下載功能 | 16 pts | ✅ 已完成 | [Plan](sprint-76-plan.md) / [Checklist](sprint-76-checklist.md) |
| **Total** | | **34 pts** | | |

---

## 問題背景

### 現狀
- AI 助手頁面只支援純文字對話
- 無法上傳文件給 Claude SDK 分析
- Claude SDK 生成的文件無法下載

### 需求
- 像 Claude AI / ChatGPT 一樣支援文件上傳
- 支援 Claude SDK 生成文件的下載
- 支援常見文件類型預覽

---

## Architecture

### 文件上傳流程
```
用戶選擇文件 → 前端上傳到後端 → 存儲到 Sandbox
                                      ↓
Claude SDK 分析 ← 後端讀取文件 ← 返回文件 ID
                                      ↓
                              返回分析結果
```

### 文件下載流程
```
Claude SDK 生成文件 → 存儲到 Sandbox → 返回文件元數據
                                              ↓
                                     前端顯示下載連結
                                              ↓
                               用戶點擊 → 下載文件
```

---

## Features

### Sprint 75: 文件上傳 (18 pts)

| Story | Description | Points |
|-------|-------------|--------|
| S75-1 | 後端文件上傳 API | 5 pts |
| S75-2 | 前端 FileUpload 組件 | 5 pts |
| S75-3 | 附件預覽組件 | 3 pts |
| S75-4 | ChatInput 整合 | 3 pts |
| S75-5 | Claude SDK 文件分析連接 | 2 pts |

### Sprint 76: 文件下載 (16 pts)

| Story | Description | Points |
|-------|-------------|--------|
| S76-1 | 後端文件下載 API | 4 pts |
| S76-2 | FileMessage 組件 | 5 pts |
| S76-3 | 文件類型渲染器 | 4 pts |
| S76-4 | ChatArea 整合 | 3 pts |

---

## Technical Details

### 支援的文件類型

**上傳 (分析用)**:
| 類型 | 擴展名 | 最大大小 |
|------|--------|----------|
| 文字 | .txt, .md, .json, .csv | 10 MB |
| 代碼 | .py, .js, .ts, .java, .c, .cpp | 10 MB |
| 文檔 | .pdf | 25 MB |
| 圖片 | .png, .jpg, .gif, .webp | 20 MB |

**下載 (生成用)**:
| 類型 | 用途 |
|------|------|
| .txt, .md | 文本報告 |
| .json, .csv | 數據導出 |
| .py, .js | 代碼文件 |
| .png, .svg | 圖表 |
| .xlsx | Excel 報告 |

### API Endpoints

```
POST   /api/v1/files/upload         # 上傳文件
GET    /api/v1/files/{id}           # 獲取文件元數據
GET    /api/v1/files/{id}/download  # 下載文件
DELETE /api/v1/files/{id}           # 刪除文件
GET    /api/v1/files                # 列出用戶文件
```

### 存儲位置

```
data/
├── uploads/           # 用戶上傳的文件
│   └── {user_id}/
│       └── {file_id}.ext
├── sandbox/           # Claude SDK 工作目錄
│   └── {session_id}/
└── outputs/           # Claude SDK 生成的文件
    └── {session_id}/
        └── {file_id}.ext
```

---

## Dependencies

### Prerequisites
- Phase 19 completed (UI Enhancement)
- Phase 17 completed (Sandbox configuration)
- Backend file storage infrastructure

### New Dependencies
- Frontend: None (use native File API)
- Backend: `python-multipart` (already installed)

---

## Verification

### Sprint 75 驗證
- [ ] 可點擊附件按鈕選擇文件
- [ ] 支援拖放上傳
- [ ] 顯示上傳進度
- [ ] 顯示附件預覽（圖片顯示縮略圖）
- [ ] 可移除附件
- [ ] 發送訊息時上傳文件到後端
- [ ] Claude SDK 能讀取上傳的文件

### Sprint 76 驗證
- [ ] Claude 生成文件時顯示在對話中
- [ ] 文件顯示圖標和名稱
- [ ] 點擊下載按鈕可下載文件
- [ ] 支援圖片預覽
- [ ] 支援代碼文件語法高亮預覽

---

**Created**: 2026-01-09
**Total Story Points**: 34 pts
