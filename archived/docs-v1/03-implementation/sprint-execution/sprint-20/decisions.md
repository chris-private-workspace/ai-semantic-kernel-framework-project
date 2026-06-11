# Sprint 20 Decisions Log

**Sprint**: 20 - GroupChat 完整遷移
**Phase**: 4 - 完整重構

---

## Decision Template

```
### D20-XXX: [Decision Title]
**Date**: YYYY-MM-DD
**Context**: [Why this decision was needed]
**Options Considered**:
1. Option A: [Description]
2. Option B: [Description]
**Decision**: [What was decided]
**Rationale**: [Why this option was chosen]
**Consequences**: [Impact of this decision]
```

---

## Decisions

### D20-001: Sprint Story 執行順序
**Date**: 2025-12-06
**Context**: 需要決定 Sprint 20 各 Story 的執行順序

**Options Considered**:
1. 按 Story 編號順序執行 (S20-1 → S20-2 → ...)
2. 按依賴關係執行 (先完成適配器功能，再遷移 API)

**Decision**: 按依賴關係執行
- S20-2 (SpeakerSelector) → S20-3 (Termination) → S20-4 (Voting)
- 然後 S20-1 (API 路由重構)
- 最後 S20-5 (測試) → S20-6 (Deprecated)

**Rationale**:
- 先完成適配器的所有功能擴展
- 確保適配器功能完整後再遷移 API
- 減少返工風險

**Consequences**:
- API 遷移延後到 Sprint 中期
- 測試可以一次性覆蓋所有新功能

---

### D20-002: GroupChatBuilderAdapter 擴展策略
**Date**: 2025-12-06
**Context**: 需要決定如何將 Phase 2 的 SpeakerSelector 邏輯整合到適配器

**Options Considered**:
1. 直接在 GroupChatBuilderAdapter 中實現所有選擇邏輯
2. 保留 domain 層的 SpeakerSelector 類，適配器調用它
3. 創建新的選擇器工廠，適配器使用工廠

**Decision**: Option 2 - 保留核心邏輯，適配器調用

**Rationale**:
- Phase 2 的選擇邏輯經過測試，穩定可靠
- 減少代碼重複
- 適配器負責 API 映射，不負責業務邏輯

**Consequences**:
- domain/orchestration/groupchat/speaker_selector.py 需要保留部分代碼
- 適配器需要正確引用和調用 domain 層邏輯

---

## Pending Decisions

- [ ] D20-003: 如何處理 GroupChat 的投票系統整合
- [ ] D20-004: API 響應格式是否需要變更

---

**Last Updated**: 2025-12-06
