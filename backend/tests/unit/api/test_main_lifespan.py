"""
File: backend/tests/unit/api/test_main_lifespan.py
Purpose: Verify api.main._lifespan() autoloads .env via python-dotenv on startup.
Category: tests / api boundary
Scope: Sprint 57.6 US-2 (R2 / closes AD-Reality-2 + 57.5 D-20)

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
        assert mock_load.call_count == 1, (
            f"Expected load_dotenv called once on startup, got {mock_load.call_count}"
        )
