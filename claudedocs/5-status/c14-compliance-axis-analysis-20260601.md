# C-14 深度分析:企業合規軸(SOC 2 / APAC PDPA / EU CRA / EU AI Act)

**Purpose**: 盤點企業合規軸的 repo 內真實狀態 + 明確區分「已建的基礎設施」vs「0% 的合規程式」vs「需外部法規查證的部分」。**結論:合規程式本身 0%,但 audit/RLS/PII 基礎設施已相當完整(可作合規地基);法規確切要求 + 2026 截止日必須外部查證,本檔不捏造。** 本檔為 research 分析(非 sprint plan)。
**Category**: Security / Compliance
**Scope**: C 區研究分析 / C-14
**Created**: 2026-06-01
**Status**: Active(analysis;法規細節須外部查證)

**Modification History (newest-first)**:
- 2026-06-01: Initial creation — C-14 合規軸(Workflow 蒐證 + 主 session 親驗 audit_log WORM + 14-security-deep-dive 無 APAC)

**Related**:
- `integration-progress-20260531.md` §14(C-14 來源)
- `claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md`(Top 10 gaps 權威)
- `docs/03-implementation/agent-harness-planning/14-security-deep-dive.md`
- `.claude/rules/multi-tenant-data.md` §GDPR / PII
- CLAUDE.md §「V2 不是先寫一批新規劃文件」(合規領域須 thin spike)

---

## 0. 一句話結論

> **合規「程式」(SOC 2 認證 / PDPA / CRA / AI Act 對應)= 0% 實作,但合規「地基」已相當完整** —— WORM append-only audit_log + per-tenant SHA-256 hash chain(migration 0005)、PostgreSQL RLS、生產級 PIIRedactor 都已實作並測試。缺的是把地基組織成可認證的控制矩陣 + GDPR 刪除 API(目前只有 pseudocode)。**法規確切要求與 2026 截止日須外部查證,本檔只列 repo 證據,不捏造法規細節。**

---

## 1. ⚠️ 範圍紀律:本檔不捏造法規

合規分析最容易出的錯是「憑訓練知識寫法規要求」。本檔嚴守:
- ✅ **repo 內有的**:逐一 file:line 列出(§2、§3)。
- ✅ **repo 內沒有的**:標 0% + 確認方式(§4)。
- ⛔ **法規確切要求 + 截止日**:列入 §6「需外部查證」,**不從 repo 或記憶寫具體條文**。
- gap-analysis 文件提到的截止日(EU CRA「2026-09」、EU AI Act「2026-08」)是**該文件的聲稱**,本檔轉述時標明出處,**不背書為法律事實**(需法務/官方查證)。

---

## 2. ✅ 已建的合規地基(均親驗,可作認證基礎)

| 設施 | 狀態 | 證據 |
|------|------|------|
| **WORM audit_log** | ✅ append-only(UPDATE/DELETE/TRUNCATE 觸發器 raise)| `migrations/versions/0005_audit_log_append_only.py:107-118`(親驗存在)|
| **Per-tenant hash chain** | ✅ SHA-256 prev/curr_hash 鏈 | `infrastructure/db/models/audit.py:67-80` |
| **Audit chain verifier** | ✅ CLI 偵測 broken_link / payload mutation | `backend/scripts/verify_audit_chain.py:1-50` |
| **RLS tenant 隔離** | ✅ 有測試證 tenant A 看不到 B | `tests/unit/infrastructure/db/test_rls_enforcement.py:231-249` |
| **PIIRedactor** | ✅ **生產碼**(email/phone/SSN/IPv4 regex,log 序列化前套用)| `platform_layer/observability/logger.py:45-64,72-85` |
| **pii_masking flag** | ✅ 預設 True | `core/feature_flags.py:58` |
| **retention_days 欄** | ⚠️ 欄位有,**無強制邏輯** | `migrations/versions/0018_tenant_settings_extension.py:81` |

→ 這些是 SOC 2 CC(audit/access control)、GDPR(PII 處理)的**真實地基**。合規工作是「把地基組織成控制矩陣 + 補缺口」,不是從零開始。

---

## 3. ⚠️ GDPR:設計有、實作幾乎無(親驗)

| 項 | 狀態 | 證據 |
|----|------|------|
| `gdpr_delete_user` | ❌ **只有 pseudocode**(在 rule 檔,非實作)| `.claude/rules/multi-tenant-data.md:297-320`;`grep gdpr_delete_user backend/src` → 0 |
| GDPR API(`/gdpr/delete-me`、`/my-data`)| ❌ 規劃表有,backend 0 路由 | `14-security-deep-dive.md:689-690`(plan);`grep gdpr backend/src/api` → 0 |
| Qdrant `delete_by_tenant` erasure | ❌ 標 Phase 51.2 future,未實作 | `infrastructure/vector/README.md:36` |

→ **GDPR 是最尖銳的「假完整」**:`14-security-deep-dive.md:679` 標「✅ GDPR 預備」,但實際刪除路徑只有 pseudocode。這是 AP-4(Potemkin)風險點。

---

## 4. ❌ 四大合規框架:repo 內 0% 程式(親驗確認方式)

| 框架 | repo 狀態 | 確認方式 |
|------|----------|---------|
| **SOC 2** | 0% 程式(無控制矩陣 / GRC)| `grep SOC2 backend/src` → 0 source hits(只在 docs/test 字串);gap-analysis:101 ❌ open |
| **APAC PDPA**(台灣個資法 / HK PDPO)| 0% | `grep PDPA\|PIPA\|PDPO backend/src` → 0;**`14-security-deep-dive.md` 全檔 0 提及 APAC/Taiwan/HK**(親驗 grep 0)|
| **EU CRA**(SBOM/Cosign/Trivy)| 0% | `grep CRA\|SBOM\|Cosign backend/src` → 0;gap-analysis:102,279 ❌ open |
| **EU AI Act** | 0% | `grep "AI Act"\|conformity backend/src` → 0;gap-analysis:277 ❌ |

> **關鍵諷刺**(gap-analysis:53 親驗):主力市場是台灣/香港,但唯一的安全規劃文件 `14-security-deep-dive.md` **完全沒提** APAC PDPA / 個資法 / PDPO。這是 gap analysis 點名的最大盲區。

---

## 5. gap analysis 已盤點(但文件本身也是「計畫」)

`enterprise-saas-gap-analysis-20260508.md` 已系統盤點(Top 10 gaps):
- Gap #5 SOC 2 control matrix ❌(:101)
- Gap #6 SBOM/Cosign/Trivy(EU CRA)❌(:102)
- Gap #7 APAC PDPA/個資法/PDPO ❌(:103)
- Block F(APAC + EU AI Act high-risk)❌(:469)
- 提議建 `21-compliance-program.md` —— **此文件尚未建**(:442)

→ 即:連「合規規劃文件」都還沒寫。但依 CLAUDE.md 紀律,**不能直接預寫 21-compliance-program.md**,須先 thin spike。

---

## 6. 🔴 需外部查證(本檔不提供,須法務/官方來源)

以下**必須外部查證**,任何 repo/AI 給的「具體條文/截止日」都不可當法律事實:
1. **SOC 2 Type II** 確切 TSC 控制要求 + 典型審計時程/成本。
2. **EU CRA** 確切截止日(gap-analysis 稱 2026-09)+ SBOM 格式(CycloneDX vs SPDX)+ ENISA 24h 通報流程。
3. **EU AI Act** 截止日(gap-analysis 稱 2026-08)+ 「AI agent orchestration 平台」屬哪個 risk tier + conformity assessment + CE marking + EU database 註冊。
4. **台灣個資法(PIPA)** data controller 義務 + 跨境傳輸限制 + 通報時限。
5. **HK PDPO** DPP1-6 技術控制要求。
6. **Singapore PDPA**(若擴及)breach notification + 跨境框架。
7. **WorkOS(IAM vendor)** 是否提供可繼承的 SOC 2 控制(部分滿足平台合規)。

> ⚠️ 我刻意**不**在此寫上述任何具體數字/條文 —— 那需要法律專業 + 官方來源,憑記憶寫會誤導合規決策。

---

## 7. 給決策的最短建議

| 問題 | 答案 |
|------|------|
| 合規地基有嗎? | ✅ 相當好(WORM audit + hash chain + RLS + PIIRedactor 全實作)|
| 合規程式有嗎? | ❌ 0%(SOC2/PDPA/CRA/AI Act 皆無 source code)|
| 最尖銳的洞? | GDPR 刪除只有 pseudocode(AP-4 風險)+ 主力市場 APAC PDPA 在安全文件 0 提及 |
| 有硬截止嗎? | ⚠️ gap-analysis **聲稱** EU CRA 2026-09 / AI Act 2026-08 —— **須外部查證**,不可當定論 |
| 第一步? | thin spike(建議:GDPR erasure 端點,因地基最齊 + AP-4 風險最高);**禁止**預寫 21-compliance-program.md |
| 紀律? | CLAUDE.md:合規新領域 thin spike → retro → design note;法規細節找法務 |

> 不需 code(分析層)。下一步若動工:① 外部查證法規(法務)② GDPR erasure thin spike(地基最齊)。**禁止**因本盤點預寫整本合規規劃。
