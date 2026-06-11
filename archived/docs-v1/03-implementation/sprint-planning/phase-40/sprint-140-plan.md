# Sprint 140: Knowledge 管理 + Memory 檢視 + 導航

## Sprint 目標

1. Knowledge 管理頁面 — 知識庫上傳、搜索、技能管理
2. Memory 檢視頁面 — 記憶搜索、使用者記憶瀏覽
3. MemoryHint 內聯組件 — 在 Chat 輸入框上方顯示相關記憶提示
4. 最終路由 + 導航 + 整合 — 新增知識庫和記憶系統路由，完成 Sidebar 導航

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 40 — Frontend Enhancement: E2E Workflow UI |
| **Sprint** | 140 |
| **Story Points** | 8 點 |
| **狀態** | 📋 計劃中 |

## Sprint 概述

Sprint 140 是 Phase 40 的最後一個 Sprint，專注於建立知識庫管理和記憶系統的前端入口。包含 Knowledge 管理頁面（文檔上傳、語義搜索、技能列表）、Memory 檢視頁面（記憶搜索、使用者記憶瀏覽）、MemoryHint 內聯組件（在 Chat 輸入框上方顯示「找到相關記憶」提示）、以及最終的路由整合和 Sidebar 導航完善，確保 Phase 40 所有新頁面都有完整的導航入口。

## User Stories

### S140-1: Knowledge 管理頁面 (3 SP)

**作為** 前端使用者
**我希望** 有一個知識庫管理頁面來上傳文檔和搜索知識
**以便** 我能管理 Agent 可使用的知識資源，並驗證知識檢索的效果

**技術規格**:
- 新增 `frontend/src/api/endpoints/knowledge.ts`
  - `uploadDocument(file, metadata)` — POST /knowledge/documents（multipart/form-data）
  - `searchKnowledge(query, options)` — POST /knowledge/search
  - `getDocuments(filters)` — GET /knowledge/documents
  - `deleteDocument(id)` — DELETE /knowledge/documents/{id}
  - `getSkills()` — GET /knowledge/skills
  - `getKnowledgeStatus()` — GET /knowledge/status（Qdrant 服務狀態）
- 新增 `frontend/src/hooks/useKnowledge.ts`
  - `useKnowledgeSearch(query)` — 語義搜索 hook（React Query）
  - `useDocuments(filters)` — 文檔列表查詢 hook
  - `useUploadDocument()` — 文檔上傳 mutation hook
  - `useDeleteDocument()` — 文檔刪除 mutation hook
  - `useSkills()` — 技能列表查詢 hook
  - `useKnowledgeStatus()` — 服務狀態查詢 hook
- 新增 `frontend/src/pages/knowledge/KnowledgePage.tsx`
  - Tab 導航：文檔管理 | 語義搜索 | 技能列表
  - **文檔管理 Tab**:
    - 文檔上傳區（拖拽上傳 + 點擊上傳）
    - 支援格式：PDF、TXT、MD、DOCX
    - 已上傳文檔列表（名稱、大小、上傳時間、狀態）
    - 操作：刪除
  - **語義搜索 Tab**:
    - 搜索輸入框 + 搜索按鈕
    - 搜索結果列表（相關片段、相似度分數、來源文檔）
    - 結果高亮顯示匹配關鍵詞
  - **技能列表 Tab**:
    - Agent 可用技能列表（名稱、描述、狀態）
  - 服務狀態指示器：Qdrant 不可用時顯示警告提示
  - 使用 Shadcn UI Tabs + Card + Table + Input + Button 組件

### S140-2: Memory 檢視頁面 (2 SP)

**作為** 前端使用者
**我希望** 有一個記憶檢視頁面來查看系統儲存的記憶
**以便** 我能了解 Agent 記住了什麼、搜索特定記憶、並驗證記憶系統的運作

**技術規格**:
- 新增 `frontend/src/api/endpoints/memory.ts`
  - `searchMemories(query, userId)` — POST /memory/search
  - `getUserMemories(userId, options)` — GET /memory/users/{userId}
  - `getMemoryStats()` — GET /memory/stats
  - `deleteMemory(id)` — DELETE /memory/{id}
- 新增 `frontend/src/hooks/useMemory.ts`
  - `useMemorySearch(query, userId)` — 記憶搜索 hook（React Query）
  - `useUserMemories(userId)` — 使用者記憶列表 hook
  - `useMemoryStats()` — 記憶統計 hook
  - `useDeleteMemory()` — 記憶刪除 mutation hook
- 新增 `frontend/src/pages/memory/MemoryPage.tsx`
  - 記憶搜索區塊：搜索輸入框 + User ID 篩選
  - 搜索結果列表（記憶內容、建立時間、相關度分數）
  - 使用者記憶列表（按時間排序，可展開查看完整內容）
  - 記憶統計儀表板（總記憶數、使用者數、最近更新時間）
  - 操作：刪除記憶
  - 使用 Shadcn UI Card + Input + Table + Badge 組件

### S140-3: MemoryHint 內聯組件 (1 SP)

**作為** 前端使用者
**我希望** 在 Chat 輸入框上方看到相關記憶提示
**以便** 我能知道 Agent 是否找到了與當前對話相關的歷史記憶

**技術規格**:
- 新增 `frontend/src/components/unified-chat/MemoryHint.tsx`
  - Props: `{ memories: MemoryItem[]; isVisible: boolean; }`
  - 顯示位置：Chat 輸入框上方
  - 顯示格式：「找到 {count} 條相關記憶」+ 可展開列表
  - 每條記憶顯示：內容摘要（前 100 字）、建立時間
  - 可展開/摺疊（預設摺疊，只顯示提示文字）
  - 可關閉（點擊 X 隱藏提示）
  - 淡入動畫效果
  - 使用 Shadcn UI Alert + Collapsible + Button 組件

### S140-4: 最終路由 + 導航 + 整合 (2 SP)

**作為** 前端使用者
**我希望** Sidebar 導航包含知識庫和記憶系統入口
**以便** 我能方便地存取所有 Phase 40 新增的功能頁面

**技術規格**:
- 修改 `frontend/src/App.tsx`
  - 新增路由 `/knowledge` → `KnowledgePage`
  - 新增路由 `/memory` → `MemoryPage`
  - Lazy import 新增頁面組件
  - 驗證所有 Phase 40 路由正確運作（/sessions, /tasks, /knowledge, /memory）
- 修改 `frontend/src/components/layout/Sidebar.tsx`
  - 新增「知識庫」導航項目（圖標：BookOpen 或 Database icon，路由 `/knowledge`）
  - 新增「記憶系統」導航項目（圖標：Brain 或 Lightbulb icon，路由 `/memory`）
  - 確認完整 Sidebar 導航順序：
    1. Dashboard（已有）
    2. AI 助手 / Chat（已有，Sprint 138 增強）
    3. Sessions 管理（Sprint 138 新增）
    4. 任務中心（Sprint 139 新增）
    5. 知識庫（Sprint 140 新增）
    6. 記憶系統（Sprint 140 新增）
    7. 工作流（已有）
    8. Agents（已有）
    9. 審批中心（已有）
    10. 審計日誌（已有）
    11. DevUI（已有）

## 檔案變更清單

### 新增檔案
| 檔案路徑 | 用途 |
|----------|------|
| `frontend/src/api/endpoints/knowledge.ts` | Knowledge API client |
| `frontend/src/api/endpoints/memory.ts` | Memory API client |
| `frontend/src/hooks/useKnowledge.ts` | Knowledge 管理 React Query hooks |
| `frontend/src/hooks/useMemory.ts` | Memory 管理 React Query hooks |
| `frontend/src/pages/knowledge/KnowledgePage.tsx` | 知識庫管理頁面 |
| `frontend/src/pages/memory/MemoryPage.tsx` | 記憶檢視頁面 |
| `frontend/src/components/unified-chat/MemoryHint.tsx` | 記憶提示內聯組件 |

### 修改檔案
| 檔案路徑 | 修改內容 |
|----------|---------|
| `frontend/src/App.tsx` | 新增 /knowledge, /memory 路由 |
| `frontend/src/components/layout/Sidebar.tsx` | 新增知識庫、記憶系統導航項目 |

## 驗收標準

- [ ] Knowledge API client 能正確呼叫所有 /knowledge 端點
- [ ] 知識庫頁面能上傳文檔（拖拽 + 點擊）
- [ ] 知識庫頁面能進行語義搜索並顯示結果
- [ ] 知識庫頁面 Qdrant 不可用時顯示警告提示
- [ ] Memory API client 能正確呼叫所有 /memory 端點
- [ ] 記憶頁面能搜索和瀏覽使用者記憶
- [ ] MemoryHint 在 Chat 輸入框上方正確顯示記憶提示
- [ ] MemoryHint 可展開查看記憶摘要、可關閉
- [ ] Sidebar 包含知識庫和記憶系統導航入口
- [ ] 所有 Phase 40 路由正確運作（/sessions, /tasks, /knowledge, /memory）
- [ ] 所有新增組件使用 TypeScript + Shadcn UI
- [ ] 所有新增程式碼通過 ESLint 檢查
- [ ] npm run build 無錯誤

## 相關連結

- [Phase 40 計劃](./README.md)
- [Sprint 138 Plan](./sprint-138-plan.md)
- [Sprint 139 Plan](./sprint-139-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 8
