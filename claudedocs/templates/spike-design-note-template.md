# Spike-Extract Design Note Template

**Source**: 2026-05-08 doc-level rolling discipline (per CLAUDE.md §⛔ 禁止反模式 + SITUATION-V2-SESSION-START.md §6.5 + `feedback_doc_growth_follows_runtime.md`)

**Use this template when**: Sprint Day 4 closeout extracting design note from spike retrospective. **不**用於預寫規劃文件。

---

## File header (use Markdown frontmatter)

```yaml
---
title: <doc number>-<topic> design note
purpose: Spike-extract design note from Sprint XX.Y; documents verified runtime invariants for <topic>
category: V2 extension docs (post-22-sprint era)
created: YYYY-MM-DD (Sprint XX.Y Day 4 closeout)
sprint_source: XX.Y
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active / Superseded by ZZ-doc-name
---
```

---

## 8-Point Quality Gate Checklist（reviewer 必逐點通過）

每個 design note 提交時，author 自查 + reviewer 驗證 8 條：

- [ ] **1. Section header 對應 spike user story**
  - ❌ Generic「OIDC overview」/「Authentication design」
  - ✅「US-A2: OIDC PKCE Flow as wired in Sprint 57.7」

- [ ] **2. 每個技術 claim 有 file:line**
  - ❌「we use RS256」/「JWT validated via JWKS」
  - ✅「`JWTManager.encode()` at `backend/src/platform_layer/identity/jwt.py:42-58`」

- [ ] **3. Decision rationale 含比較矩陣**
  - ❌「We chose WorkOS as best practice」
  - ✅ 三/四欄 vendor matrix + Cost / SCIM / SAML / Decision + 否決原因
  - ✅ 我們選 X 的具體 reason（不是「best practice」）

- [ ] **4. Verification command（reproducible）**
  - ❌ 無
  - ✅`pytest tests/integration/auth/test_oidc_flow.py::test_real_entra_callback`
  - ✅ 或具體 manual reproduce step（curl + expected response）

- [ ] **5. Test fixture reference**
  - ✅ Link 到實際 test data / mock setup file
  - ✅ 若是 real-LLM 測試，標明 `pytest -m real_llm` 與 cost 估算

- [ ] **6. Open invariant 明確分界**
  - ✅「Verified in this spike: A, B, C」
  - ✅「Deferred to Phase XX.Y (NOT verified): D, E, F」
  - ❌ 將 deferred 內容寫入主 section 偽裝 verified

- [ ] **7. Rollback / fallback 路徑**
  - ✅「若此設計後續證明錯，revert API routes at auth.py + DB column external_id；估 1-2 day」
  - ✅ 識別 sentinel / fallback 是否已存在
  - ❌ 假設「不會錯」

- [ ] **8. Cross-reference 17.md single-source**
  - ✅ 任何新 contract 必須在 `17-cross-category-interfaces.md` 對應 §section 登記
  - ✅ 若新增 ABC，標明 owner category
  - ❌ 在 design note 平行定義 contract 違反 single-source

---

## 推薦 Doc Structure（≈ 200-500 行 typical outcome；非 cap）

```markdown
# <doc-number>-<topic> Design Note (Sprint XX.Y extract)

## 0. Spike Summary
- Sprint scope: <user stories>
- Verified period: YYYY-MM-DD ~ YYYY-MM-DD
- Calibration: bottom-up X hr / committed Y hr / actual Z hr / ratio R
- Verification: pytest +N / Vitest +M / Playwright +K

## 1. Decision Matrix（vendor / approach 比較）
[3-4 column comparison table + chosen reason + rejected reasons]

## 2. Verified Invariants（每 invariant 一節）

### 2.1 <Invariant name>
- **Implementation**: `file:line` reference
- **Behavior**: 1-2 sentences
- **Verification**: `pytest ...` reproduce
- **Test fixture**: `tests/.../fixture.json`

### 2.2 ...

## 3. Cross-Category Contracts（若有新 contract）
- Contract NN: <name>
- Owner category: <range>
- Registered at: `17-cross-category-interfaces.md` §X.Y
- Interface signature: <ABC code snippet>

## 4. Open Invariants (deferred to Phase XX.Y)
- [ ] Deferred 1: <reason>
- [ ] Deferred 2: <reason>

## 5. Rollback / Fallback
- If this design proves wrong: revert <file> + DB column <name>
- Estimated rollback effort: ~N hours
- Sentinel / fallback already in place: <yes/no + ref>

## 6. References
- Sprint plan: `phase-XX-Y/sprint-XX-Y-plan.md`
- Sprint retrospective: `agent-harness-execution/sprint-XX-Y/retrospective.md`
- Related contracts: `17-cross-category-interfaces.md` §...
- Related rules: `.claude/rules/...`

## Modification History
- YYYY-MM-DD: Initial extract from Sprint XX.Y closeout (Day 4)
```

---

## 反面範例（14.md L109-200 風格 — 禁用）

```markdown
## OIDC Authentication Flow
We use Microsoft Entra ID as primary IdP.
JWT tokens are signed with RS256 and validated against JWKS endpoint.
RBAC permissions follow YAML schema below: [200 lines pseudo-code YAML]
```

**為何禁**：每行 0 個 file:line / 0 個 verification / 0 個 decision matrix / 0 個 deferred 分界。Verified ratio 接近 0%。

---

## 正面範例（spike-extract 風格）

請參考下次 Sprint 57.7 closeout 產出的 `20-iam-deep-dive.md`（live example）。

---

**維護**：本 template 隨 V2 演進；當有 3+ design note 採用後，據實踐回饋擴充本 template。
