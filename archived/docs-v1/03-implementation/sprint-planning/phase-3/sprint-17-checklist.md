# Sprint 17 Checklist: MagenticBuilder 重構

**Sprint 目標**: 將 DynamicPlanner 遷移至 MagenticBuilder
**週期**: Week 35-36
**總點數**: 42 點
**狀態**: 待開始

---

## S17-1: MagenticBuilder 適配器 (8 點)

- [ ] 創建 `builders/magentic.py`
- [ ] MagenticBuilderAdapter 類
- [ ] participants() 支持
- [ ] with_manager() 支持

---

## S17-2: StandardMagenticManager (8 點)

- [ ] plan() 方法
- [ ] create_progress_ledger() 方法
- [ ] replan() 方法
- [ ] prepare_final_answer() 方法

---

## S17-3: Ledger 整合 (8 點)

- [ ] Task Ledger 整合
- [ ] Progress Ledger 整合
- [ ] Facts/Plan extraction

---

## S17-4: Human Intervention (8 點)

- [ ] PLAN_REVIEW 整合
- [ ] TOOL_APPROVAL 整合
- [ ] STALL 整合

---

## S17-5: API 更新 (5 點)

- [ ] planning 端點更新

---

## S17-6: 測試 (5 點)

- [ ] 覆蓋率 >= 80%

---

## 相關連結

- [Sprint 17 Plan](./sprint-17-plan.md)
- [Phase 3 Overview](./README.md)
