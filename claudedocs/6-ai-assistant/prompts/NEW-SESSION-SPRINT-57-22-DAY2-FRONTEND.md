# 新 Session Prompt — Sprint 57.22 Day 2 前端 Mockup-Fidelity Audit 繼續

> **用法**：整份 copy 到新 session 對話框第一條訊息。AI 助手讀完即可對齊上下文，無需問「你是誰、現在哪個 sprint」。

---

## 你正在加入什麼

**IPA Platform V2** — Phase 49+ V2 重構期間（22 sprint / 5.5 個月）+ Phase 56+ SaaS Frontend 18/N + 當前 Sprint 57.22 **AD-Mockup-Fidelity-Comprehensive-Audit** in-flight。

**3 大最高指導原則**（不可違反）：
1. **Server-Side First** — 多租戶、企業 API、HITL
2. **LLM Provider Neutrality** — `agent_harness/**` 禁 `import openai`/`anthropic`
3. **CC 參考但 Server-Side 重新設計** — 不照搬

**權威排序**：`docs/03-implementation/agent-harness-planning/` 21 docs > 根 CLAUDE.md > `.claude/rules/` > V1 文件。

---

## 必讀順序（新 session 第 1 件事）

1. **本 prompt**（你正在讀）
2. **CLAUDE.md**（根目錄）— V2 11+1 範疇 + 5 大核心約束 + Frontend Mockup-Fidelity Hard Constraint
3. **`.claude/rules/sprint-workflow.md`** — Day 0 三-prong + calibration matrix（最後 1 row = `frontend-mockup-fidelity-audit` 0.85）
4. **`.claude/rules/multi-tenant-data.md`** — tenant_id 三鐵律
5. **`.claude/rules/anti-patterns-checklist.md`** — 11 條 PR 自檢
6. **`memory/MEMORY.md`** + **`memory/feedback_frontend_mockup_fidelity_hard_constraint.md`** — 2026-05-17 user directive
7. **當前 sprint 三文件**：
   - Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-22-plan.md`
   - Checklist: 同目錄 `sprint-57-22-checklist.md`
   - Progress: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-22/progress.md`
8. **Audit 主文件**：`claudedocs/4-changes/sprint-57-22-mockup-fidelity-audit/AUDIT-REPORT-COMPREHENSIVE.md`（~600L，Day 1 12 units 已 populated）

---

## 當前 Sprint 座標

| 項目 | 值 |
|------|-----|
| **Sprint** | 57.22 / Day 1 已完成 / Day 2 待開始 |
| **Phase 累計** | V2 22/22 ✅ + SaaS Stage 1 3/3 ✅ + SaaS Frontend 18/N + 57.22 audit in flight |
| **Branch** | `feature/sprint-57-22-mockup-fidelity-audit` |
| **Base** | main `e99ad7c9`（Sprint 57.21 closeout PR #154 merge）|
| **Sprint 57.21 HEAD** | `678222d2`（PR #152 squash merge）|
| **Sprint type** | Pure audit（zero production code changes）|

---

## 前端整體進度（Phase 57+ 18/N + 57.22 audit）

### 已 ship 18 sprints（Phase 57.1 → 57.21）

| Sprint | 主題 | 狀態 |
|--------|------|------|
| 57.1 | Cost + SLA Dashboards | ✅ ship；但 Sprint 57.22 Day 1 audit 發現 backend HTTP 500 for dev tenant |
| 57.3 | Tenant Settings | ✅ ship |
| 57.4 | Admin Tenants List | ✅ ship |
| 57.7 | IAM Foundation (WorkOS) + Auth Pages | ✅ ship；**Sprint 57.22 Day 1 audit 發現 100% legacy 架構 + mockup 0% fidelity** |
| 57.8 | AppShell V2 + Chat-V2 first ship | ✅ ship |
| 57.9 | Governance 3 pages | ✅ ship |
| 57.10 | Convention Codify | PIVOTED ✅ |
| 57.11 | Verification Real Ship | ✅ ship |
| 57.12 | Agent Harness UI Suite（Memory + Subagent Tree）| ✅ ship；**Sprint 57.22 Day 1 audit 發現 /memory 架構與 mockup 完全不對** |
| 57.13 | Frontend Foundation 1/N COMPLETE | ✅ ship |
| 57.14 | E2E Sweep | ✅ ship |
| 57.15 | Inline Style Sweep | ✅ ship |
| 57.16 | Inline Style Round 2 | ✅ ship |
| 57.17 | Tailwind v4 Directive Hotfix | ✅ ship |
| 57.18 | Mockup Integration Foundation（cp design-mockups + tokens + 6 categories + 18 PROP stubs）| ✅ ship |
| 57.19 | Mockup Operations Port Round 1（11 USs）+ 9-page DRIFT-REPORT | ✅ ship |
| 57.20 | Mockup Direct Port Foundation（shell rewrite + /overview + /chat-v2 token migration）| ✅ ship |
| 57.21 | ChatV2 Mockup Fidelity Phase-1（Turn Block Model + SessionList + 3-col shell + Inspector 4-tab + Composer scaffolding）| ✅ ship |

### Sprint 57.22 in flight（Day 1 完成）

**目的**：因 mockup-fidelity 嚴重 gap，誠實 audit ~40 routes，量化 drift severity + rebuild hour estimate，產出 Phase 57.23+ priority matrix。

**Day 1 完成（12 units）**：

| Group | Routes | 結果 |
|-------|--------|------|
| Auth 6 | login / callback / register / invite / mfa / expired | **4 ZERO routes + 1 15% fidelity legacy + 1 partial** |
| Operations dashboards 5 | overview / cost-dashboard / sla-dashboard / memory / verification | **2 HTTP-500 backend + /overview 60% fidelity + /memory 完全不同架構 + /verification 部分** |
| Chat-v2 page-level 1 | chat-v2 | **75% Phase-1 baseline**（Sprint 57.21 baseline + 3 D-DAY4-6/7/8 fixes in-sprint）|

**Day 1 actual ~2.5 hr vs target 5-6 hr**（顯著 under — 4 missing + 2 HTTP-500 = 快速判定）。

**12 NEW carryover ADs 已 catalog**（Phase 57.23+）：
- 🔴 AD-Auth-Page-Full-Rebuild-Round-2 (TOP)
- AD-AuthShell-Mockup-Refactor / AD-WorkOS-Multi-IdP-Phase58
- AD-Auth-{Register,Invite,MFA,Expired,Callback}-Full-Build-Phase58
- AD-Mockup-Card-Primitive-Phase58 / AD-Mockup-Typography-Scale-Phase58
- AD-Cost/SLA-Dashboard-Full-Rebuild + Backend-Dev-Tenant-500
- AD-Memory-Page-Full-Rebuild / Scope-Role-Session / Time-Travel-Phase58

---

## Day 2 待做工作（17 sub-units）

### Chat-v2 Phase-2 widgets 6

從 `reference/design-mockups/page-chat.jsx`（533L）對照當前 `frontend/src/features/chat_v2/`：

- **Memory Block 5th type**（Phase-1 已 ship 4 types: thinking/tool/verification/subagent_fork）
- **HITL FourAction**（Approve / Approve-with-edits / Reject / Escalate-to-L2）— 當前 2-action（Approve/Reject）
- **Composer Richness**（3 disabled buttons 📎/🧠/🛠️ → real UX）
- **Inspector Trace tab**（Cat 12 OTel spans live feed; 當前 ComingSoonInspectorTab placeholder）
- **Inspector Memory tab**（Cat 3 memory.recent per-session feed; 當前 ComingSoonInspectorTab placeholder）
- **Inspector SubagentTree tab**（Cat 11 AD-Subagent-RealList-Phase58; 當前 ComingSoonInspectorTab placeholder）

### Governance 4

從 `reference/design-mockups/page-governance.jsx` 對照當前 `frontend/src/features/governance/`：

- approvals / redaction / loop-debug / audit-log

### Operations Platform 7

從 `reference/design-mockups/page-platform.jsx` + `page-platform2.jsx` 對照：

- orchestrator / subagents / state-inspector / compaction / workflows / error-policy / rbac

### Day 2 工作流程（per unit）

1. **Mockup screenshot** via Playwright MCP at 1440×900（mockup http server `http://localhost:8080/#<route>`）
2. **Production screenshot** via Playwright MCP at 1440×900（dev server `http://localhost:3007/`）
3. **Side-by-side diff matrix**（Strict 1:1 ±2px ≥95% bar）
4. **Severity 評定**：ZERO route / HTTP-500 / STRUCTURAL FAIL / COSMETIC / PASS
5. **Rebuild hour estimate** + per-unit carryover ADs
6. **AUDIT-REPORT-COMPREHENSIVE.md 追加 Unit 13-29**

---

## Day 3-4 預期

- **Day 3**：Admin 10（tenants list / tenant-settings / feature-flags / quotas / hitl-policies / members / danger-zone / tenant-onboarding / pricing / domain-detail）+ Misc 7（models / tools / sse / devui / a11y-audit / incidents / subagent-tree / jit-retrieval / cache-manager）
- **Day 4**：Priority matrix（P0/P1/P2/P3）+ Sprint 57.23+ first-execution-sprint scope-class proposal（NEW `frontend-mockup-strict-rebuild` 0.55-0.65）+ Σ rebuild hours per group + retrospective Q1-Q7 + memory snapshot + MEMORY.md +1 + CLAUDE.md V2 status sync + sprint-workflow.md calibration matrix +1 row + SITUATION update + push + closeout PR

---

## 紀律必守（V2 9 項）

1. **Server-Side First** ✅
2. **LLM Provider Neutrality** ✅（audit 不動 backend）
3. **CC Reference 不照搬** ✅
4. **17.md Single-source** ✅
5. **11+1 範疇歸屬** N/A（audit-only）
6. **04 anti-patterns** ✅（AP 11/11 PASS by definition）
7. **Sprint workflow** ✅（Day 0 三-prong + plan + checklist 全有）
8. **File header convention** ✅
9. **Multi-tenant** ✅（pure frontend audit, 0 backend）

---

## 🔴 Frontend Mockup-Fidelity Hard Constraint（2026-05-17 user directive）

**所有 frontend 頁面必須完全跟隨 `reference/design-mockups/` 1:1**：
- ❌ 不可用 shadcn 預設值替代 mockup 的 padding/radius/shadow/color 如果視覺不一致
- ❌ 不可用「production 簡化版」名義裁剪 widget / 改 layout
- ❌ 不可因 backend 沒有就改 mockup widget — data 用 fixture，同 sprint 或後續 sprint 加 backend
- ✅ Tailwind arbitrary values escape hatch 允許（per STYLE.md §3）
- ✅ shadcn primitives 允許（Dialog / Sheet / Tabs / DropdownMenu / Command）當 mockup interaction 模式直接對應
- ✅ recharts 允許但配色必須匹配 mockup

詳見 `memory/feedback_frontend_mockup_fidelity_hard_constraint.md`。

---

## 🔴 Anti-Stop Rule（2026-05-16 user directive）

**Tool result is progress signal NOT turn boundary**。Stop only on:
- (a) ambiguous strategy（多個有效方法 / 用戶意圖不明 / 新 sprint 方向）
- (b) irreversible destructive action ahead（git push / reset --hard / force / 刪 production / 改 shared infra / 改 CI / 發外部訊息）
- (c) explicit user 停/wait signal

**NOT trigger**: tool result return / Write/Edit/Read 在已對齊 scope 內 / sprint plan 內的下一步 / batch parallel tool calls。Karpathy §1「不清楚就停下」preserved 但限真 ambiguous decision。

詳見 `memory/feedback_tool_result_is_not_turn_boundary.md`。

---

## Rolling Planning 紀律自檢

✅ Sprint 57.23 plan **未起草**（rolling — 等 Sprint 57.22 Day 4 收尾才寫）
✅ Sprint 57.22 Day 0 三-prong + plan + checklist 全有（NOT 跳步直接 code）
✅ Day 2/3/4 checkbox 全標 🚧 未動（沒刪除）
✅ Phase 57.23+ carryover ADs 描述 generic 不綁 sprint 編號

---

## 🚨 Critical Constraint

- **DO NOT stop any node.js process** — running claude code process；嚴禁 kill `:3007` dev server / `:8080` mockup server
- **Confirmation on Destructive Only**：git push / reset --hard / force / 刪 production / shared infra / CI / external messages 前必問
- **Never Delete Tests / Docs / Unchecked items**
- **Language**：繁體中文 with user, English in code/docstrings

---

## 開發環境

| Service | URL | 用途 |
|---------|-----|------|
| Mockup http server | `http://localhost:8080/` | `python -m http.server` from `reference/design-mockups/`（hash-based routing `#<route>`）|
| Production dev server | `http://localhost:3007/` | `cd frontend && npm run dev`（Sprint 57.20 V3 shell + dark default + Geist font wired）|
| Backend FastAPI | `http://localhost:8000/` | `python -m uvicorn main:app --reload`（Cat 1 sessions / Cat 3 memory / Cat 7 state / Cat 11 subagents / Cat 9 governance / Cat 12 obs）|
| Playwright MCP | n/a | Side-by-side mockup vs prod screenshot at 1440×900 |

---

## 開始 Day 2 前的 1 件事

確認 Day 1 commit SHA：

```bash
git log feature/sprint-57-22-mockup-fidelity-audit --oneline -5
```

確認 working tree 乾淨後，直接開始 Day 2 Chat-v2 Phase-2 widgets audit。

---

## 今天的任務（請更新此行）

**今天：Sprint 57.22 Day 2 — Chat-v2 Phase-2 widgets 6 + Governance 4 + Operations Platform 7（17 sub-units）audit；目標 ~5-6 hr 完成 AUDIT-REPORT-COMPREHENSIVE.md Unit 13-29 with diff matrix + severity + rebuild hour estimate**

---

**Last Updated**: 2026-05-18（Sprint 57.22 Day 1 完成後）
**Prompt Author**: Claude Code AI 助手
**Next Update**: Sprint 57.22 Day 4 收尾後 → 新 prompt for Sprint 57.23+ first execution sprint
