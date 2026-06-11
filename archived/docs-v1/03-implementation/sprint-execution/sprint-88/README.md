# Sprint 88: 時間線可視化

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| **Sprint 編號** | 88 |
| **Phase** | 26 - DevUI 前端實現 |
| **名稱** | 時間線可視化 |
| **目標** | 實現執行事件的時間線可視化組件，包括垂直時間線、事件樹形結構和事件詳情面板 |
| **總點數** | 16 Story Points |
| **開始日期** | 2026-01-13 |
| **狀態** | ✅ 完成 |

---

## User Stories

| Story | 名稱 | 點數 | 優先級 | 狀態 |
|-------|------|------|--------|------|
| S88-1 | 時間線組件設計和實現 | 8 | P1 | ⏳ 待開始 |
| S88-2 | 事件樹形結構顯示 | 5 | P1 | ⏳ 待開始 |
| S88-3 | LLM/Tool 事件詳情面板 | 3 | P1 | ⏳ 待開始 |

---

## Story 詳情

### S88-1: 時間線組件設計和實現 (8 pts)

**描述**: 實現核心時間線可視化組件，直觀展示執行事件流程

**功能需求**:
- 垂直時間線布局
- 事件節點顯示：事件類型圖標、時間戳、持續時間條
- 事件配對顯示：LLM_REQUEST ↔ LLM_RESPONSE、TOOL_CALL ↔ TOOL_RESULT
- 持續時間可視化（條形圖）
- 滾動和縮放功能
- 懸停顯示詳情

**交付物**:
- `frontend/src/components/DevUI/Timeline.tsx`
- `frontend/src/components/DevUI/TimelineNode.tsx`
- `frontend/src/components/DevUI/DurationBar.tsx`

---

### S88-2: 事件樹形結構顯示 (5 pts)

**描述**: 實現嵌套事件的樹形結構顯示

**功能需求**:
- 支持 parent_event_id 層級結構
- 展開/收起子事件
- 縮進顯示層級關係
- 連接線顯示父子關係
- 遞歸渲染子事件

**交付物**:
- `frontend/src/components/DevUI/EventTree.tsx`
- `frontend/src/components/DevUI/TreeNode.tsx`

---

### S88-3: LLM/Tool 事件詳情面板 (3 pts)

**描述**: 實現 LLM 和工具事件的專用詳情面板

**功能需求**:
- LLM 事件面板：Prompt 顯示、Response 顯示、Token 使用量、模型名稱、耗時
- Tool 事件面板：工具名稱、參數、結果、耗時
- 複製功能（複製 prompt/result）
- JSON 格式化顯示

**交付物**:
- `frontend/src/components/DevUI/EventPanel.tsx`
- `frontend/src/components/DevUI/LLMEventPanel.tsx`
- `frontend/src/components/DevUI/ToolEventPanel.tsx`

---

## 技術規格

### 文件結構

```
frontend/src/components/DevUI/
├── Timeline.tsx         # 主時間線組件 (S88-1)
├── TimelineNode.tsx     # 時間線節點組件 (S88-1)
├── DurationBar.tsx      # 持續時間條 (S88-1)
├── EventTree.tsx        # 事件樹形結構 (S88-2)
├── TreeNode.tsx         # 樹節點組件 (S88-2)
├── EventPanel.tsx       # 事件面板工廠 (S88-3)
├── LLMEventPanel.tsx    # LLM 事件面板 (S88-3)
└── ToolEventPanel.tsx   # Tool 事件面板 (S88-3)
```

### 事件類型圖標

| 事件類型 | 圖標 | 顏色 |
|---------|------|------|
| WORKFLOW_* | ⚙️ Settings | 藍色 |
| LLM_* | 🤖 Bot | 紫色 |
| TOOL_* | 🔧 Wrench | 綠色 |
| CHECKPOINT_* | ✅ Check | 黃色 |
| ERROR | ❌ XCircle | 紅色 |
| WARNING | ⚠️ AlertTriangle | 橙色 |

### 依賴項

- React 18 + TypeScript
- Lucide React (圖標)
- Tailwind CSS (樣式)
- Sprint 87 DevUI 基礎設施

---

## 驗收標準

- [ ] 時間線正確渲染所有事件
- [ ] 事件配對邏輯正確
- [ ] 樹形結構展開/收起正常
- [ ] 事件詳情面板正確顯示
- [ ] LLM 事件面板顯示 prompt/response/token
- [ ] Tool 事件面板顯示參數和結果
- [ ] 複製功能正常
- [ ] 時間線渲染延遲 < 500ms

---

## 相關文檔

- [Sprint 88 Plan](../../sprint-planning/phase-26/sprint-88-plan.md)
- [Sprint 88 Checklist](../../sprint-planning/phase-26/sprint-88-checklist.md)
- [Phase 26 README](../../sprint-planning/phase-26/README.md)

---

**創建日期**: 2026-01-13
**更新日期**: 2026-01-13
