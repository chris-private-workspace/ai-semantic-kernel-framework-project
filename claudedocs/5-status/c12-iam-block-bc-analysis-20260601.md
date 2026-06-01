# C-12 深度分析:IAM Block B/C —— 前端已 ship,後端是有意 Phase 58+ 缺口

**Purpose**: 釐清 IAM Block B(invites + 自助 tenant 註冊)/ Block C(MFA TOTP + WebAuthn)的真實狀態。**結論:這不是「壞掉」,是有意的 Phase 58+ deferred 缺口** —— 前端 3 頁(invite/register/mfa)已用 mockup-fidelity ship 並帶 AP-2 demo banner + fixture fallback,後端端點刻意不存在(預期 501)。本檔為 research 分析(非 sprint plan)。
**Category**: Platform / Identity (IAM)
**Scope**: C 區研究分析 / C-12
**Created**: 2026-06-01
**Status**: Active(analysis;對應 3 個 Phase 58 ADs)

**Modification History (newest-first)**:
- 2026-06-01: Initial creation — C-12 IAM Block B/C(Workflow 蒐證 + 主 session 親驗 backend 無 invites/mfa 檔 + main.py router 清單)

**Related**:
- `integration-progress-20260531.md` §12(C-12 來源)
- `docs/03-implementation/agent-harness-planning/20-iam-deep-dive.md`(IAM 權威)
- `docs/.../phase-57-frontend-saas/sprint-57-23-plan.md`(3 ADs 出處)
- CLAUDE.md §V2 不是「先寫一批新規劃文件」(Block 開發須 thin spike)

---

## 0. 一句話結論

> **Block B/C 是「前端 ship + 後端有意缺」的 intentional gap,不是 regression。** 前端 invite/register/mfa 3 頁已用 mockup-fidelity 完成(Sprint 57.23),呼叫的後端端點(`/invites/{token}`、`/tenants/register`、`/mfa/verify`)**刻意不存在** → 前端收 501 → 顯示 fixture + AP-2 banner。這是 V2「前後端同 sprint 但後端 defer」的標準 interim debt,有 3 個明確 AD 追蹤,等 Phase 58+ IAM Block B/C 補後端。

---

## 1. 已實作 vs 缺口(親驗 backend 檔案存在性)

### ✅ Block A 已實作(Sprint 57.7)
| 能力 | 證據 |
|------|------|
| HS256 JWT(encode/decode/verify)| `platform_layer/identity/jwt.py:103-246` |
| `get_current_tenant` / `get_current_user_id` / RBAC role deps | `platform_layer/identity/auth.py:62-186` |
| WorkOS OIDC(login/callback/signout)| `platform_layer/identity/oidc.py` |
| DB-backed RBAC hybrid path | `platform_layer/identity/rbac.py` |
| auth 路由:`/auth/{login,callback,me,dev-login,logout}` | `api/v1/auth.py:128,224,321,375,439` |

### ❌ Block B/C 後端缺(親驗:0 檔)
| 缺口 | 前端呼叫 | 後端證據 |
|------|---------|---------|
| invites | `pages/auth/invite/index.tsx:69,90`(GET `/invites/{token}` + POST `/accept`)| **`git ls-files backend/src/api/**` grep invite → 0 檔**(親驗)|
| MFA | `pages/auth/mfa/index.tsx:106,127`(POST `/mfa/verify`)| **0 檔**(同上)|
| 自助註冊 | `pages/auth/register/index.tsx:130`(POST `/tenants/register`)| auth.py 無此路由;main.py router 清單無 invites/mfa(親驗 `main.py:59-71`)|

> 親驗指令:`git ls-files "backend/src/api/**" | grep -iE "invite|mfa|register"` → **空**(僅 business_domain/_register_all.py 不相關)。確認 invites/mfa backend 完全不存在。

---

## 2. 這是有意設計(3 個 AD + AP-2 banner 證明)

- **3 個 Phase 58 AD**(`sprint-57-23-plan.md:244-246`):
  - `AD-Auth-Register-Backend-IAM-Block-B-Phase58`
  - `AD-Auth-Invite-Backend-IAM-Block-B-Phase58`
  - `AD-Auth-MFA-Backend-IAM-Block-C-Phase58`
- **前端有 fixture fallback + AP-2 demo banner**(`invite/index.tsx:48-53,153-162`;`mfa/index.tsx:191-199`;`register/index.tsx:181-188`)→ 501 是**已知且預期**,非 bug。
- `sprint-57-23-plan.md:55,372` 明述「backend register/invite/mfa endpoints stub 501; full wire → Phase 58+」。

→ 對齊 CLAUDE.md Mockup-Fidelity 鐵律:後端缺的 widget 用 fixture + banner,後續 sprint 補。**這是排程中的 interim debt,不是缺陷。**

---

## 3. Block B/C 完整缺口清單(來自 20-iam-deep-dive.md §4 Open Invariants)

| 缺口 | 證據 | Block |
|------|------|-------|
| invites 端點 + 服務 | `20-iam-deep-dive.md` + 0 backend 檔 | B |
| 自助 tenant 註冊 | `sprint-57-23-plan.md:372` | B |
| MFA TOTP 註冊(totp_secrets 表 + recovery codes)| `20-iam-deep-dive.md:142`;無 migration | C |
| WebAuthn(webauthn_credentials 表)| `sprint-57-23-plan.md:56` | C |
| SAML 2.0 | `20-iam-deep-dive.md:141` | 進階 |
| SCIM 2.0 | `20-iam-deep-dive.md:144` | 進階 |
| Refresh token rotation | `20-iam-deep-dive.md:143` | 進階 |
| 全 DB-only RBAC 強制(`rbac.has_permission()` 現 stub return False)| `rbac.py:147-165` | 進階 |
| PKCE code_verifier | `oidc.py:14` | 進階 |
| `/auth/recovery` 頁 | `sprint-57-23-plan.md:367`(AD-Auth-Recovery-Page-Phase58)| C |
| **AdminTenants schema 擴充**(9 欄缺 5)| `sprint-57-44-plan.md:213` BLOCKING | 相關 |

---

## 4. 紀律警示:Block B/C 必須 thin spike,不能預寫規劃文件

CLAUDE.md §「V2 不是『先寫一批新規劃文件』」明令:IAM 新領域**必須先 1 個 thin vertical spike → retrospective → extract design note**,禁止因 gap analysis 預寫多份新文件。

→ ∴ C-12 的後續**不應**「先寫 Block B 完整規劃」,而應挑**最小一個垂直切片**(建議:invites,因它最自包含——一張 invites 表 + 2 端點 + 既有 JWT/tenant 設施)做 spike,retrospective 後才 extract design note。

---

## 5. 給決策的最短建議

| 問題 | 答案 |
|------|------|
| Block B/C 是 bug 嗎? | ❌ 有意 Phase 58+ deferred;前端 ship + 後端 stub 501 + 3 AD 追蹤 |
| 前端要改嗎? | ❌ 前端已 mockup-fidelity ship + AP-2 banner;補後端後接線即可 |
| 最小切入點? | **invites 垂直 spike**(1 表 + 2 端點 + 復用既有 JWT/tenant);最自包含 |
| 紀律? | thin spike → retro → design note;**禁止**預寫 Block B 完整規劃文件 |
| 依賴? | 復用 Block A(JWT/tenant/RBAC 已實作);MFA(Block C)較重(TOTP secret 儲存 + recovery codes)|
| 急嗎? | 視商業:自助註冊/invites 是 SaaS onboarding 前提;MFA 是企業安全要求。但無外部硬截止(對比 C-14 有法規截止)|

> 後續若動工:從 invites spike 開 plan+checklist(走 V2 workflow);**不**預寫整個 Block B 規劃。
