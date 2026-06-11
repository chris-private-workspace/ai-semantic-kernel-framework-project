# Sprint 16 決策記錄

**Sprint**: 16 - GroupChatBuilder 重構
**開始日期**: 2025-12-05

---

## DEC-16-001: 架構策略選擇

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
需要決定如何將現有 GroupChatManager 遷移至 Agent Framework GroupChatBuilder。

### 選項

1. **完全替換**: 直接使用 GroupChatBuilder 替換 GroupChatManager
2. **並行架構**: 保留原有實現 + 新增適配器層
3. **漸進遷移**: 逐步將功能遷移到新 API

### 決定
選擇 **並行架構** (選項 2)

### 理由
1. 與 Sprint 13-15 保持一致的遷移策略
2. 提供向後兼容性
3. 允許漸進式測試和驗證
4. 降低遷移風險

### 影響
- 需要維護適配器層
- 代碼量增加但風險降低
- 用戶可選擇使用新舊 API

---

## DEC-16-002: API 映射策略

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
需要定義現有 API 與 Agent Framework API 的映射關係。

### 映射表

| 我們的 API | Agent Framework API |
|-----------|---------------------|
| `SpeakerSelectionMethod.AUTO` | `set_manager()` |
| `SpeakerSelectionMethod.ROUND_ROBIN` | `set_select_speakers_func()` |
| `SpeakerSelectionMethod.RANDOM` | `set_select_speakers_func()` |
| `SpeakerSelectionMethod.MANUAL` | `set_select_speakers_func()` |
| `GroupChatState` | `GroupChatStateSnapshot` |
| `GroupMessage` | `ChatMessage` |

### 決定
使用適配層轉換，保持現有 API 簽名不變。

---

## DEC-16-003: 發言者選擇實現

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
Agent Framework 提供兩種發言者選擇方式：
1. `set_manager()` - Agent 作為管理者
2. `set_select_speakers_func()` - 函數式選擇

### 決定
- **AUTO**: 使用 `set_manager()` 搭配 LLM Agent
- **ROUND_ROBIN/RANDOM/MANUAL**: 使用 `set_select_speakers_func()`

### 實現策略
```python
if method == SpeakerSelectionMethod.AUTO:
    builder.set_manager(manager_agent)
else:
    builder.set_select_speakers_func(custom_selector)
```

---

## 已解決決策

### RESOLVED-001: ManagerSelectionResponse 擴展
**問題**: 是否需要擴展 ManagerSelectionResponse 以支持額外元數據？
**狀態**: ✅ 已解決
**決定**: 在 `groupchat_orchestrator.py` 中實現完整的 ManagerSelectionRequest/Response 類，包含：
- selected_participant: 選中的參與者
- instruction: 給選中參與者的指令
- finish: 是否結束對話
- final_message: 結束時的最終消息

---

## Sprint 16 決策摘要

| 決策 ID | 主題 | 狀態 |
|---------|------|------|
| DEC-16-001 | 並行架構策略 | ✅ 已決定 |
| DEC-16-002 | API 映射策略 | ✅ 已決定 |
| DEC-16-003 | 發言者選擇實現 | ✅ 已決定 |
| RESOLVED-001 | ManagerSelectionResponse 擴展 | ✅ 已解決 |
