# Sprint 9: GroupChat & Multi-turn - Decisions Log

記錄 Sprint 9 開發過程中的重要技術和架構決策。

---

## 決策記錄

### D9-1: GroupChat 訊息類型設計

**日期**: 2025-12-05
**決策者**: Development Team
**狀態**: 待定

**背景**:
GroupChat 需要支援多種訊息類型以滿足複雜對話場景。

**選項**:
1. 簡單的 USER/AGENT/SYSTEM 三類型
2. 擴展類型包含 FUNCTION_CALL/FUNCTION_RESULT
3. 完整的訊息類型體系（含 metadata）

**決策**: 待 S9-1 實現時確定

**理由**: 需要評估與現有系統的整合需求

---

### D9-2: 發言者選擇策略架構

**日期**: 2025-12-05
**決策者**: Development Team
**狀態**: 待定

**背景**:
需要支援 6 種發言者選擇策略：AUTO, ROUND_ROBIN, RANDOM, MANUAL, PRIORITY, EXPERTISE

**選項**:
1. 策略模式 (Strategy Pattern)
2. 函數映射表
3. 混合模式

**決策**: 待 S9-2 實現時確定

**理由**: 需要考慮可擴展性和性能

---

### D9-3: 對話記憶存儲策略

**日期**: 2025-12-05
**決策者**: Development Team
**狀態**: 待定

**背景**:
對話記憶需要支援短期、長期和工作記憶三種類型。

**選項**:
1. 全 Redis 方案（快速但容量有限）
2. 分層存儲（Redis + PostgreSQL）
3. 純 PostgreSQL（持久但較慢）

**決策**: 待 S9-4 實現時確定

**理由**: 需要平衡性能和持久性需求

---

## 待決事項

- [ ] WebSocket 實現方式（FastAPI 原生 vs Socket.IO）
- [ ] LLM 選擇發言者的 prompt 設計
- [ ] 投票結果的持久化策略
- [ ] 對話摘要的觸發時機

---

## 相關連結

- [Progress Log](./progress.md)
- [Issues Log](./issues.md)
- [Sprint 9 Checklist](../../sprint-planning/phase-2/sprint-9-checklist.md)
