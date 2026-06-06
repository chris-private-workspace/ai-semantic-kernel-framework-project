"""
core.config — Pydantic Settings.

Sprint 49.2 expands DB-related fields. Sprint 49.3 / 49.4 will further add
RLS / OTel / LLM provider fields.

Per project rules (.claude/rules/code-quality.md): always use Pydantic
Settings (not raw os.environ) so type-safe + validation + .env support.

Modification History (newest-first):
    - 2026-05-10: Sprint 57.13 US-A1 — fix oidc_redirect_uri + frontend_base_url + cookie_secure
    - 2026-05-09: Sprint 57.7 US-A2 — add WorkOS OIDC fields (vendor route per US-A1 matrix)
    - 2026-05-06: Sprint 56.1 Day 2 — add quota_enforcement_enabled (US-2)
    - 2026-05-05: Sprint 55.5 — add chat_verification_mode (AD-Cat10-Wire-1; Option E)
    - 2026-04-30: Sprint 55.1 — add business_domain_mode (Literal mock/service)
    - 2026-04: Sprint 49.2-49.4 — DB / Redis / JWT field expansion
    - 2026-04: Initial creation (Sprint 49.1)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """V2 backend settings. Loaded from env / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Application ------------------------------------------------
    env: str = "development"
    log_level: str = "INFO"
    app_version: str = "2.0.0-alpha"

    # ---- PostgreSQL -------------------------------------------------
    # async URL format: postgresql+asyncpg://user:pwd@host:port/db
    database_url: str = "postgresql+asyncpg://ipa_v2:ipa_v2_dev@localhost:5432/ipa_v2"

    # Pool sizing (Sprint 49.2)
    db_pool_size: int = 10
    db_pool_max_overflow: int = 20
    db_pool_recycle_sec: int = 300
    db_echo: bool = False  # True only for local SQL debugging

    # ---- Redis (Sprint 49.4 wires) ----------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # ---- JWT (Sprint 49.3 wires identity) ---------------------------
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    # ---- RBAC (Sprint 57.7 US-A3 — DB-backed RBAC opt-in) ----------
    # When False (default): _require_role only checks JWT claim path
    #   (preserves Sprint 53.5+ behavior + 100+ existing tests that mock
    #   request.state.roles via SimpleNamespace stubs).
    # When True: _require_role first checks JWT claim, then falls back to
    #   RBACManager.has_role_code DB query for per-tenant custom roles.
    # Production rollout: flip True after user_roles + roles tables are
    #   populated via migration script + verify endpoint demo passes.
    # Override via env: RBAC_DB_BACKED_FALLBACK=true
    rbac_db_backed_fallback: bool = False

    # ---- WorkOS OIDC (Sprint 57.7 US-A2 — IAM Hosted vendor) -------
    # Path 1 per Day 0 D2 verify: V2 internal JWT stays HS256; vendor SDK
    # handles JWKS validation of WorkOS-issued tokens (no jwt_jwks_url
    # needed). Vendor decision rationale: see iam-vendor-matrix.md
    # (cost ~$15K/yr Year 1 / $40K/yr Year 2; B2B-best SAML+SCIM combo).
    # Empty defaults so Settings still loads in test/dev without WorkOS
    # account; OIDC routes return 503 if api_key blank.
    workos_api_key: str = ""
    workos_client_id: str = ""
    # OIDC code-exchange needs the *backend* callback (client secret lives
    # server-side) — Sprint 57.13 D-PRE-5 fix: was http://localhost:3005/auth/callback
    # which is both the V1 frontend port and a frontend path with no secret.
    # Prod: set via env to the reverse-proxy host, e.g.
    # https://app.example.com/api/v1/auth/callback.
    oidc_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"
    # Public SPA origin — /api/v1/auth/callback redirects the browser here
    # (frontend_base_url + "/auth/callback?next=...") so the SPA runs
    # authStore.bootstrap() then navigates to the originally-requested page.
    # Prod: the public SPA origin behind the reverse proxy. Override via env: FRONTEND_BASE_URL.
    frontend_base_url: str = "http://localhost:3007"
    # httpOnly auth cookies (v2_jwt + oidc_*) Secure flag. False in dev (http
    # localhost); MUST be True in prod (https). Override via env: COOKIE_SECURE=true.
    cookie_secure: bool = False

    # ---- Business domain (Sprint 55.1) ------------------------------
    # mock   → 51.0 HTTP mock_executor pathway (PoC default; backwards-compat)
    # service → 55.1+ DB-backed service classes (production)
    # Override via env: BUSINESS_DOMAIN_MODE=service
    business_domain_mode: Literal["mock", "service"] = "mock"

    # ---- Cat 10 verification wiring (Sprint 55.5 — AD-Cat10-Wire-1) -
    # disabled → inject verifier_registry=None at chat router; wrapper
    #            transparently delegates to loop.run() per
    #            correction_loop.py:99-106 (54.1 backwards-compat;
    #            byte-for-byte event stream identical to direct loop.run)
    # enabled  → inject populated VerifierRegistry; wrapper runs verifiers +
    #            self-correction loop max 2 attempts (54.1 spec)
    # Override via env: CHAT_VERIFICATION_MODE=disabled
    # Option E 2-mode post-D4+D5: no shadow/enforce mode; rely on
    # registry-presence dispatch in run_with_verification wrapper.
    # Sprint 57.83 (B-8 leg-2): default → "enabled" after a real-Azure measurement of
    # the lightweight output_quality judge showed FP rate 0% on normal prompts (bad/
    # nonsense still caught). See claudedocs/5-status/cat10-verification-real-llm-
    # measurement-20260605.md. Closes AD-Cat10-Wire-1-Production / B-8.
    chat_verification_mode: Literal["disabled", "enabled"] = "enabled"
    # Sprint 57.63 Cat 10: judge template used by the real LLMJudgeVerifier when
    # chat_verification_mode == "enabled". A template name resolved from
    # verification/templates/<name>.txt (e.g. "output_quality", "safety_review")
    # or a raw string containing the `{output}` placeholder. Final-output judge only.
    # Sprint 57.83 (B-8 leg-2): default → general "output_quality" judge (helpful/
    # complete/accurate/on-topic). Replaces the Cat 9-fitted "safety_review" default
    # which leaned unsafe (high false-positive as a general final-output judge).
    chat_verification_judge_template: str = "output_quality"

    # ---- Phase 56.1 SaaS quota (US-2) -------------------------------
    # Off by default — production rollout flips True after Redis client
    # wiring at api/main.py + load test verifies headroom.
    # When True: chat router pre-stream calls QuotaEnforcer.check_and_reserve;
    # 429 raised on cap breach with Retry-After header.
    # Day 2 ships pre-call reservation only; post-call reconciliation is
    # Phase 56.x carryover (AD-QuotaPostCall-1).
    quota_enforcement_enabled: bool = False
    quota_estimated_tokens_per_call: int = 1000  # conservative pre-call reservation

    # ---- Sprint 57.11 Cat 10 verification persistence (US-2) --------
    # When True (default): correction_loop.run_with_verification's write
    # hook best-effort INSERTs each VerificationPassed/VerificationFailed
    # event into verification_log via VerificationLogRepository. DB flake
    # is logged at WARNING but never breaks the agent loop event stream.
    # Override via env: VERIFICATION_LOG_PERSIST_ENABLED=false (kill switch).
    verification_log_persist_enabled: bool = True

    # ---- Sprint 57.84 C-15 billing Outbox drainer ------------------
    # The background poller (api/main.py _start_billing_outbox_drainer)
    # drains billing_outbox → cost_ledger. These tune the loop. The
    # enabled flag is read from os.environ directly (BILLING_OUTBOX_DRAINER_
    # ENABLED, default "true") so tests disable it without the get_settings()
    # lru_cache timing trap (mirrors AUDIT_LOG_CHAT_OBSERVER).
    billing_outbox_poll_interval_s: int = 5
    billing_outbox_batch: int = 50
    billing_outbox_max_retry: int = 8


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton. FastAPI Depends(get_settings)."""
    return Settings()


__all__ = ["Settings", "get_settings"]
