# Sprint 117: 自動記憶寫入 + 檢索注入

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 117 |
| **Phase** | 38 - E2E Assembly C: 記憶與知識組裝 |
| **Duration** | 1 day |
| **Story Points** | 10 pts |
| **Status** | ✅ 完成 |
| **Branch** | `feature/phase-38-e2e-c` |

---

## Sprint 目標

實現 Orchestrator Agent 的自動記憶寫入與檢索注入機制，讓對話結束時自動摘要存入 Long-term Memory，新對話開始時自動檢索相關記憶注入上下文。

---

## Sprint 概述

Sprint 117 為 Phase 38 的第一個 Sprint，專注於三層記憶系統的核心管線：OrchestratorMemoryManager 的實現，包括自動摘要生成、記憶檢索注入、Working Memory 到 Long-term Memory 的提升機制，以及 search_memory / search_knowledge tool 的定義。

---

## 前置條件

- ✅ Phase 37 (E2E Assembly B) 完成
- ✅ mem0 + Qdrant 記憶基礎設施就緒
- ✅ Redis Working Memory 機制就緒
- ✅ Orchestrator Agent 基礎編排能力就緒

---

## User Stories

### S117-1: 對話結束自動摘要寫入 mem0 (2 pts)

**作為** Orchestrator Agent，
**我希望** 在對話結束時自動生成結構化摘要並寫入 mem0 episodic Long-term Memory，
**以便** 跨對話記憶能力得以建立，過去處理過的問題可被未來對話召回。

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/memory_manager.py`
- 實現 `OrchestratorMemoryManager.summarise_and_store()` 方法
- 載入 L1 ConversationState → LLM 生成 JSON 摘要 → 寫入 Long-term Memory
- 低重要性對話自動跳過

---

### S117-2: 摘要 Prompt 設計 (2 pts)

**作為** 系統開發者，
**我希望** 設計結構化摘要提取 prompt，能從對話中提取問題描述、處理方式、結果、教訓、標籤與重要性，
**以便** 記憶摘要品質穩定且格式一致，可被後續語義搜索有效匹配。

**技術規格**:
- 定義 `SUMMARY_PROMPT` — 結構化摘要提取 prompt（JSON 格式輸出）
- 定義 `MEMORY_INJECTION_TEMPLATE` — 歷史記憶上下文注入模板
- 提取欄位：問題描述、處理方式、結果、教訓、標籤、重要性

---

### S117-3: 新對話記憶檢索注入 (2 pts)

**作為** Orchestrator Agent，
**我希望** 在新對話開始時自動檢索相關歷史記憶並注入上下文，
**以便** 能像資深 IT 運維主管一樣記得過去處理過的問題，提供連貫的服務體驗。

**技術規格**:
- 實現 `retrieve_relevant_memories()` — 語義搜索相關歷史記憶
- 支持 UnifiedMemoryManager.search() 和 Mem0Client.search_memory() 兩種介面
- 實現 `build_memory_context()` — 格式化記憶為 prompt 注入文字
- 最多 5 條記憶，含時間戳

---

### S117-4: search_memory 增強 + search_knowledge 定義 (2 pts)

**作為** Orchestrator Agent，
**我希望** search_memory() 支援語義搜索、時間範圍過濾與用戶篩選，並新增 search_knowledge tool 定義，
**以便** 能精準地搜索歷史記憶與企業知識庫。

**技術規格**:
- 實現 `handle_search_memory()` — 增強版 search_memory handler
- 支持 time_range 過濾（"7d"、"30d"）
- 修改 `backend/src/integrations/hybrid/orchestrator/tools.py`
- 新增 `search_knowledge` tool 定義（SYNC, viewer role）

---

### S117-5: Working → Long-term 提升機制 (2 pts)

**作為** 記憶系統，
**我希望** Working Memory (Redis) 中的重要條目能自動提升至 Long-term Memory (mem0+Qdrant)，
**以便** 重要的即時狀態不會因 TTL 過期而丟失，能被長期保存與檢索。

**技術規格**:
- 實現 `promote_working_to_longterm()` — Working Memory 重要條目提升
- 對話結束時觸發提升流程
- 結合摘要生成的重要性評分決定是否提升

---

## 相關連結

- [Phase 38 計劃](./README.md)
- [Sprint 117 Progress](../../sprint-execution/sprint-117/progress.md)
- [Sprint 118 Plan](./sprint-118-plan.md)
