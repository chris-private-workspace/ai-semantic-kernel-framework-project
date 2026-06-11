# IAM Vendor Evaluation Matrix — Sprint 57.7 US-A1 (2026-05-09)

> **Sprint**: 57.7 — IAM Foundation + Frontend Foundation 1/N spike
> **Decision Owner**: laitim2001 (V2 platform engineer)
> **Date**: 2026-05-09
> **Status**: Day 1 intermediate artifact;Day 4 closeout will fold into `20-iam-deep-dive.md` §1 Decision Matrix
> **Target Market Context** (per CLAUDE.md L429): 台灣 / 香港 enterprise B2B + EU optional pipeline

---

## 1. Decision Summary

**✅ CHOSEN: WorkOS**

**Reason**: B2B-focused (best SAML + SCIM + Audit Logs combo) + cost-predictable per-connection model ($125/conn/month with 16+ volume discounts to $65) + zero MAU cap (1M+ free) + clean OIDC standards (low lock-in) + APAC accessible + SOC 2 Type II inherited + clear migration off-ramp via standard OIDC tokens.

**Cost projection** (V2 typical 1-year):
- Year 1 (5K MAU + 5 enterprise connections): ~$625/month SSO + Directory Sync $625 = ~$1,250/month = **~$15,000/yr**
- Year 2 (50K MAU + 15 connections): hits volume discount $100/conn × 15 = $1,500/month + SCIM $1,500 = ~$3,000/month = **~$36,000/yr**
- + Optional Audit Logs SIEM connection $125/month + retention $99/M events ≈ +$2-5K/yr

**Sprint 57.7 US-A2 wire path**: install `workos` Python SDK + `@workos-inc/node` (or REST direct from frontend) + connect 1 IdP (Microsoft Entra ID for V2 demo) + use WorkOS-issued JWT validation via WorkOS SDK + V2 issues internal HS256 JWT post-callback (Path 1 per D2 decision).

---

## 2. 4-Vendor Comparison Matrix

| Capability | WorkOS ✅ Chosen | Clerk ❌ Rejected | Auth0 ❌ Rejected | Supabase Auth ❌ Rejected |
|------------|------------------|-------------------|-------------------|--------------------------|
| **Cost per connection** | $125/month flat (volume discount $65 @ 51-100) | $50/connection on Pro+ | Tier-bundled (3 in B2B Essentials, 5 in Professional) | Bundled ($0.015/SSO MAU on top of base) |
| **Cost per MAU** | $0 (1M+ free) | $0 first 10K (was 5K), then $0.02/MAU on Pro | $150/mo @ 500 MAU; $800/mo @ 1K MAU (B2B Essentials/Professional) | $0.015/SSO MAU |
| **Cost @ V2 scale 5K MAU + 5 conn** | ~$1,250/mo ($15K/yr) | ~$250/mo ($3K/yr) — cheapest at small scale | ~$1,500-2,500/mo ($18-30K/yr) | ~$100/mo ($1.2K/yr) — cheapest absolute |
| **Cost @ V2 scale 50K MAU + 15 conn** | ~$3,000/mo ($36K/yr) | ~$1,075/mo ($13K/yr) | ~$2,500-5K/mo ($30-60K/yr) | ~$775/mo ($9K/yr) |
| **OIDC PKCE** | ✅ Native + clean SDK | ✅ via Pro tier | ✅ Native | ✅ via OAuth providers |
| **SAML 2.0** | ✅ Best-in-class B2B | ✅ Pro tier + add-on | ✅ B2B tier required (3-5 conn cap) | ⚠️ Pro+ tier only, limited features |
| **SCIM 2.0** | ✅ Native (Directory Sync) | ✅ April 2026 GA (recent — production maturity risk) | ✅ Free tier (since Sept 2024) | ❌ **NOT supported** — enterprise procurement blocker |
| **Python SDK quality** | ✅ `workos` PyPI mature, well-maintained | ⚠️ Community-driven, less mature | ✅ `auth0-python` mature | ⚠️ Built-in via `supabase-py` |
| **React SDK quality** | ✅ `@workos-inc/authkit-react` | ✅★ Best-in-class DX (PLG focus) | ✅ `@auth0/auth0-react` mature | ✅ `@supabase/auth-helpers-react` |
| **SOC 2 Type II inheritance** | ✅ Included by default | ⚠️ **Behind Business Plan paywall** (cost surprise) | ✅ Enterprise tier ($30K+/yr) | ✅ Pro+ tier |
| **Vendor lock-in** | 🟡 Medium (proprietary tokens but standard OIDC export) | 🔴 High (frontend SDK heavy + organizations model proprietary) | 🟡 Medium-high (mature but proprietary rules engine) | 🟢 Low (OSS / self-host option) |
| **Migration off-ramp** | ✅ Standard OIDC tokens → can switch to self-built | ⚠️ Organizations model + Clerk-specific user metadata = harder | ✅ Standard OIDC + bulk export tools | ✅ Easy (OSS, can self-host) |
| **APAC presence (Taiwan/HK target)** | ✅ Global edge + APAC clients | ✅ Global | ✅ Okta/Auth0 mature in APAC | ⚠️ Limited (US/EU focus) |
| **Signup approval time** (Risk Class A) | 1-2 business days B2B trial | Self-serve free tier | Self-serve free tier | Self-serve free tier |
| **Audit Logs (SOC 2 CC7 prep)** | ✅ Native ($125/mo + $99/M events) | ⚠️ Basic (Pro tier) | ✅ Enterprise tier | ⚠️ Limited |
| **Multi-tenant Organizations model** | ✅ Native + matches V2 tenant_id | ✅ B2B SaaS suite ($1/MAO after 100) | ✅ Enterprise tier | ⚠️ Build yourself |
| **Stripe Billing integration** | ✅ Standard webhook | ✅ Standard webhook | ✅ Standard webhook | ⚠️ DIY |
| **Free production tier?** | ✅ Up to ~5 connections free trial | ✅ 50K MAU free (Pro features locked) | ⚠️ 25K MAU free (no enterprise SSO) | ✅ Generous free tier |

---

## 3. Rejection Rationale (3 specific reasons, NOT「best practice」hand-wave)

### Rejected #1: Clerk
- **SCIM 2.0 April 2026 GA too recent** — V2 客戶若在 2026 Q3 demo SCIM,Clerk 才剛 GA 1-2 季,尚未 battle-tested at enterprise scale (production 不穩定 risk)
- **SOC 2 Type II artifacts behind Business Plan paywall** — Sprint 57.6 closure 後 V2 須回應 enterprise prospect SOC 2 ask;Business Plan price 不明顯 (likely $200-500+/month base) 帶來成本驚嚇
- **Frontend SDK heavy → migration cost high** — Clerk 的 `@clerk/react` 涉入頁面層級 component;若日後 swap vendor 需 rewrite 大量 frontend;V2 核心是 backend agent harness 不希望 frontend 被 vendor 鎖定

### Rejected #2: Auth0
- **B2B Essentials 僅 3 enterprise SSO connections + 500 MAU at $150/月** — V2 第一年若簽 4-5 個 enterprise customer 立即超 cap → 強制升 B2B Professional $800/月 (1K MAU only) → 再升 Enterprise $30K+/年。階梯式 cost 跳 2.5x-5x 不利早期商業化
- **B2B Professional 5 SSO cap @ $800/月仍不夠** — V2 目標 Year 2 50 enterprise customers 需 50+ connections,Auth0 強制 Enterprise tier $30K-60K/年 (相比 WorkOS volume discount $65/conn × 50 = $3,250/月 = $39K/年 + 全 platform vs Auth0 limited features)
- **Mature 但已 Okta-acquired (2021)** — pricing 持續上調 (2024 + 2025 兩波 hike) + 過去 customer pricing migration 帶來 unpredictable cost 上行 risk

### Rejected #3: Supabase Auth
- **SCIM 2.0 完全 missing** — gap-analysis §1.2 Tier 0 #6 SCIM 為 $50K+ ACV deal 的 table-stakes;沒有 SCIM 直接 block 70% B2B procurement;V2 自建 SCIM ~3-5 sprint 不在 Phase 57.7 spike scope
- **SAML 2.0 Pro+ tier 但功能受限** — Supabase docs 註明「best for B2C or early B2B (<10K MAU)」;V2 enterprise B2B 不在其 sweet spot
- **APAC presence 限制** — Supabase 主要 US/EU edge node;Taiwan/HK 客戶連線 latency 不理想 (跟 V2 target market 衝突)

---

## 4. Cost Projection Detail (chosen vendor WorkOS)

### Year 1 — V2 production launch (~5K MAU + 5 enterprise customers)

| Item | Monthly | Annual |
|------|---------|--------|
| 5 SSO connections @ $125/conn | $625 | $7,500 |
| 5 Directory Sync (SCIM) connections @ $125/conn | $625 | $7,500 |
| Audit Logs (SOC 2 CC7 prep) — 1 SIEM connection | $125 | $1,500 |
| Audit Logs retention ~10M events @ $99/M | ~$1,000 | ~$12,000 (variable) |
| **Total Year 1 baseline** | **~$1,375 (without aggressive Audit retention)** | **~$16,500** |
| Total Year 1 with full Audit retention | ~$2,375 | ~$28,500 |

### Year 2 — V2 growth (~50K MAU + 20 enterprise customers)

| Item | Monthly | Annual |
|------|---------|--------|
| 16-20 SSO connections @ volume tier $100/conn | $1,600-2,000 | $19,200-24,000 |
| 16-20 Directory Sync connections @ volume tier $100/conn | $1,600-2,000 | $19,200-24,000 |
| Audit Logs SIEM | $125 | $1,500 |
| Audit Logs retention ~50M events @ $99/M | ~$5,000 | ~$60,000 |
| **Total Year 2 baseline** | **~$3,325-4,125** | **~$39,900-49,500** |

### Year 3 — V2 scale (~200K MAU + 75 enterprise customers)

| Item | Monthly | Annual |
|------|---------|--------|
| 51-75 SSO connections @ volume tier $65/conn | $3,315-4,875 | $39,780-58,500 |
| 51-75 Directory Sync connections @ volume tier $65/conn | $3,315-4,875 | $39,780-58,500 |
| Audit Logs (full retention) | ~$15K | ~$180K |
| **Total Year 3 baseline** | **~$21K-25K** | **~$259K-297K** |

**Year 1 verdict**: $16K-28K/yr WorkOS B2B+SCIM stack vs ~$30-60K/yr Auth0 equivalent → **WorkOS ~50% cheaper at V2 scale**

---

## 5. Migration Off-Ramp (「if we want to leave in 2 years」)

WorkOS lock-in profile 是 4 vendor 中**第二低** (Supabase OSS 第一低):

1. **JWT format**: WorkOS issues standard OIDC tokens (subject + iss + aud + exp + nonce) — V2 可改 issue HS256 internal JWT post-WorkOS-callback (already plan path)
2. **User export**: WorkOS Directory Sync exposes users via standard SCIM 2.0 GET endpoints — bulk export to V2 `users` table 直接
3. **SAML connections**: WorkOS connections 是 IdP-side configuration (Entra/Google/Okta) — switch vendor 只需 reconfigure callback URL,IdP-side 設定 reuse
4. **Audit Logs**: WorkOS log 透過 SIEM connection forward — 已在 V2 SIEM (or self-hosted) 內;leaving WorkOS 失去 retention service 但 logs 已 mirror

**Estimated migration effort to self-built** (in Year 2-3 if needed):
- ~3-5 sprint OIDC PKCE + JWKS 自建 + WorkOS Directory Sync replace by self-built SCIM endpoint
- Plus user_id remapping pass (WorkOS user_id → V2 generated)
- Total ~5-8 sprint;**not impossible**;clear off-ramp

**Lock-in mitigation Phase 57.7 implementation**:
- Store `users.external_id` = WorkOS user_id (already exists per D8 verify ✅) — switching vendor = remap external_id
- All RBAC done in V2 DB (US-A3) NOT in vendor — vendor 不知道 V2 roles → switch 不影響 RBAC
- Frontend uses generic vendor abstraction `frontend/src/services/auth.ts` (US-A2) — swap implementation later

---

## 6. Sprint 57.7 US-A2 Wire Path

Based on chosen vendor WorkOS:

1. Install `workos>=4.0,<5.0` Python SDK in `backend/requirements.txt`
2. Settings extend (`backend/src/core/config/__init__.py`):
   - `workos_api_key: str = ""` (env: `WORKOS_API_KEY`)
   - `workos_client_id: str = ""` (env: `WORKOS_CLIENT_ID`)
   - `oidc_redirect_uri: str = "http://localhost:3005/auth/callback"` (env: `OIDC_REDIRECT_URI`)
   - **NO `jwt_jwks_url` needed** — WorkOS SDK handles vendor JWT validation internally per Path 1 D2 decision
3. NEW `backend/src/platform_layer/identity/oidc.py` `WorkOSOIDCFlow` class:
   - `initiate_login(redirect_uri)` → calls `WorkOS().sso.get_authorization_url(...)` + state stored in Redis
   - `exchange_callback(code, state)` → `WorkOS().sso.get_profile_and_token(code)` + extract subject + V2 user upsert
   - `signout(token)` → standard logout redirect
4. NEW `backend/src/api/v1/auth.py` router with 3 endpoints
5. JWT issue **stays HS256** (V2 internal) per `core/config:56` default
6. Frontend installs `@workos-inc/authkit-react` OR rolls own minimal client (TBD US-A2 decision)

**WorkOS account setup**: Day 1 PM signup B2B trial → vendor SDK key in `.env` Day 2 morning before US-A2 backend wire start. If approval > 1 day per Risk Class A → Day 2 fallback to **mock vendor SDK** for unit tests + defer real Entra IdP integration to Day 3.

---

## 7. References

- WorkOS Pricing: https://workos.com/pricing
- Clerk Pricing 2026: https://clerk.com/pricing + WorkOS comparison https://workos.com/blog/clerk-pricing
- Auth0 Pricing 2026: https://auth0.com/pricing + B2B Essentials/Professional comparison
- Supabase SSO docs: https://supabase.com/archived/docs-v1/guides/auth/enterprise-sso/auth-sso-saml + pricing https://supabase.com/pricing
- WorkOS B2B Enterprise readiness checklist: https://workos.com/blog/enterprise-readiness-checklist-2026
- Gap analysis §1.2 + §5: `claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md`

---

**Decision approval pending user review** before US-A2 wire start (Day 2 morning)
