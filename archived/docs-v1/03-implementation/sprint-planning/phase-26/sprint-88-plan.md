# Sprint 88: 時間線可視化

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 88 |
| **Phase** | 26 - DevUI 前端實現 |
| **Duration** | 5-7 days |
| **Story Points** | 16 pts |
| **Status** | ✅ 完成 |
| **Priority** | 🟡 P1 高優先 |

---

## Sprint Goal

實現執行事件的時間線可視化組件，包括垂直時間線、事件樹形結構和事件詳情面板。

---

## Prerequisites

- Sprint 87 完成（DevUI 核心頁面）

---

## User Stories

### S88-1: 時間線組件設計和實現 (8 pts)

**Description**: 實現核心時間線可視化組件，直觀展示執行事件流程

**Acceptance Criteria**:
- [ ] 垂直時間線布局
- [ ] 事件節點顯示：
  - 事件類型圖標
  - 時間戳
  - 持續時間條
- [ ] 事件配對顯示：
  - LLM_REQUEST ↔ LLM_RESPONSE
  - TOOL_CALL ↔ TOOL_RESULT
  - WORKFLOW_START ↔ WORKFLOW_END
- [ ] 持續時間可視化（條形圖）
- [ ] 滾動和縮放功能
- [ ] 懸停顯示詳情

**API Endpoints**:
```
GET /api/v1/devtools/traces/{execution_id}/timeline
```

**Files to Create**:
- `frontend/src/components/DevUI/Timeline.tsx`
- `frontend/src/components/DevUI/TimelineNode.tsx`
- `frontend/src/components/DevUI/DurationBar.tsx`

---

### S88-2: 事件樹形結構顯示 (5 pts)

**Description**: 實現嵌套事件的樹形結構顯示

**Acceptance Criteria**:
- [ ] 支持 parent_event_id 層級結構
- [ ] 展開/收起子事件
- [ ] 縮進顯示層級關係
- [ ] 連接線顯示父子關係
- [ ] 遞歸渲染子事件

**事件層級示例**:
```
WORKFLOW_START
├── EXECUTOR_START
│   ├── LLM_REQUEST
│   └── LLM_RESPONSE
│   └── TOOL_CALL
│       └── TOOL_RESULT
└── EXECUTOR_END
WORKFLOW_END
```

**Files to Create**:
- `frontend/src/components/DevUI/EventTree.tsx`
- `frontend/src/components/DevUI/TreeNode.tsx`

---

### S88-3: LLM/Tool 事件詳情面板 (3 pts)

**Description**: 實現 LLM 和工具事件的專用詳情面板

**Acceptance Criteria**:
- [ ] LLM 事件面板：
  - Prompt 顯示 (折疊長文本)
  - Response 顯示
  - Token 使用量
  - 模型名稱
  - 耗時
- [ ] Tool 事件面板：
  - 工具名稱
  - 參數 (JSON 格式化)
  - 結果
  - 耗時
- [ ] 複製功能（複製 prompt/result）
- [ ] JSON 格式化顯示

**Files to Create**:
- `frontend/src/components/DevUI/EventPanel.tsx`
- `frontend/src/components/DevUI/LLMEventPanel.tsx`
- `frontend/src/components/DevUI/ToolEventPanel.tsx`

---

## UI 設計參考

### 時間線樣式

```
時間軸                    事件                          持續時間
──────────────────────────────────────────────────────────────
10:00:00.000  ●────────  WORKFLOW_START                 0ms
10:00:00.050  │  ●──     LLM_REQUEST
10:00:02.150  │  ●──     LLM_RESPONSE              2100ms ████████
10:00:02.200  │  ●──     TOOL_CALL
10:00:02.350  │  ●──     TOOL_RESULT                150ms ██
10:00:02.400  ●────────  WORKFLOW_END               2400ms
──────────────────────────────────────────────────────────────
```

### 事件類型圖標

| 事件類型 | 圖標 | 顏色 |
|---------|------|------|
| WORKFLOW_* | ⚙️ | 藍色 |
| LLM_* | 🤖 | 紫色 |
| TOOL_* | 🔧 | 綠色 |
| CHECKPOINT_* | ✅ | 黃色 |
| ERROR | ❌ | 紅色 |
| WARNING | ⚠️ | 橙色 |

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] 時間線正確渲染
- [ ] 事件配對邏輯正確
- [ ] 樹形結構展開/收起正常
- [ ] 單元測試覆蓋率 > 80%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| 時間線渲染延遲 | < 500ms |
| 事件面板載入 | < 200ms |
| 複製功能成功率 | 100% |

---

**Created**: 2026-01-13
**Story Points**: 16 pts
