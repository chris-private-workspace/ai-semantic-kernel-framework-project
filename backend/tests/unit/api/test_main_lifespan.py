"""
File: backend/tests/unit/api/test_main_lifespan.py
Purpose: Verify api.main._lifespan() startup wiring (.env autoload + pricing loader).
Category: tests / api boundary
Scope: Sprint 57.6 US-2 (R2 / closes AD-Reality-2 + 57.5 D-20) + FIX-022 (§5.1 H1)

Description:
    Sprint 57.5 reality check found AZURE_OPENAI_API_KEY etc. were not loaded
    from .env when uvicorn started, causing real_llm chat mode to 503. Fix is
    to call load_dotenv() at the top of api.main._lifespan() so process env
    populates before settings / adapter initialization.

    This test pins the regression: patch `api.main.load_dotenv`, drive the
    FastAPI lifespan via TestClient context-manager enter/exit, assert the
    patched function was called exactly once on startup.

Created: 2026-05-08 (Sprint 57.6 Day 1)

Modification History:
    - 2026-06-07: FIX-028 — add test_lifespan_wires_sla_recorder (sla-report 500 regression)
    - 2026-05-31: FIX-022 — add test_lifespan_wires_pricing_loader_from_yaml (§5.1 H1)
    - 2026-05-08: Sprint 57.6 US-2 — initial creation (closes AD-Reality-2)

Related:
    - backend/src/api/main.py L72-86 — `_lifespan()` calling load_dotenv()
    - backend/requirements.txt — `python-dotenv>=1.0,<2.0`
    - 57.5 reality check D-20 — `0 dotenv import` in backend/src baseline
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_lifespan_calls_load_dotenv_on_startup() -> None:
    """`_lifespan` startup must invoke `load_dotenv` so .env populates os.environ."""
    # Import inside test so patch target resolves to api.main's binding (not the
    # original dotenv.load_dotenv); api.main does `from dotenv import load_dotenv`
    # which creates a module-level name we patch.
    from api.main import create_app

    with patch("api.main.load_dotenv") as mock_load:
        app = create_app()
        # Driving TestClient context-manager triggers FastAPI lifespan startup.
        with TestClient(app):
            pass
        # Lifespan startup must have called load_dotenv exactly once.
        assert (
            mock_load.call_count == 1
        ), f"Expected load_dotenv called once on startup, got {mock_load.call_count}"


def test_lifespan_wires_pricing_loader_from_yaml() -> None:
    """`_lifespan` startup must install the PricingLoader (FIX-022 §5.1 H1).

    Before FIX-022 nothing called set_pricing_loader(), so the chat router's
    `if pricing_loader is not None` guard was always False → CostLedgerService
    never constructed → cost_ledger rows never written for real LLM calls. This
    pins the startup wiring: after lifespan startup the loader must be present and
    must have parsed config/llm_pricing.yml (a known key resolves).
    """
    from api.main import create_app
    from platform_layer.billing.pricing import (
        maybe_get_pricing_loader,
        reset_pricing_loader,
    )

    # Clean slate so a prior test's loader cannot mask a regression here.
    reset_pricing_loader()
    try:
        app = create_app()
        assert maybe_get_pricing_loader() is None  # not wired until startup runs
        with TestClient(app):
            loader = maybe_get_pricing_loader()
            assert loader is not None, "lifespan startup did not install PricingLoader"
            # Proves the yaml was actually parsed (gpt-5.4 is a known azure key).
            assert (
                loader.get_llm_pricing("azure_openai", "gpt-5.4") is not None
            ), "PricingLoader installed but config/llm_pricing.yml not loaded"
    finally:
        reset_pricing_loader()


def test_lifespan_wires_sla_recorder() -> None:
    """`_lifespan` startup must install the SLAMetricRecorder (FIX-028).

    Before FIX-028 nothing in backend/src called set_sla_recorder() (only the 2
    test files did), so the singleton stayed None in production. The report
    endpoint's STRICT get_sla_recorder() then raised RuntimeError on the
    cache-miss generate path → GET /admin/tenants/{id}/sla-report 500'd, while
    pytest stayed green because tests inject their own recorder (AP-10 mock/real
    divergence; twin of FIX-022). This pins the startup wiring.
    """
    from api.main import create_app
    from platform_layer.observability.sla_monitor import (
        maybe_get_sla_recorder,
        reset_sla_recorder,
    )

    # Clean slate so a prior test's recorder cannot mask a regression here.
    reset_sla_recorder()
    try:
        app = create_app()
        assert maybe_get_sla_recorder() is None  # not wired until startup runs
        with TestClient(app):
            assert (
                maybe_get_sla_recorder() is not None
            ), "lifespan startup did not install SLAMetricRecorder"
    finally:
        reset_sla_recorder()
