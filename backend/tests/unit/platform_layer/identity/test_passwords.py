"""
File: backend/tests/unit/platform_layer/identity/test_passwords.py
Purpose: bcrypt hash/verify util unit tests (Sprint 57.86 / US-1).
Category: Tests / Unit (platform_layer.identity — C-12 IAM credentials)
Created: 2026-06-06 (Sprint 57.86 Day 2)

Pure (no DB): hash≠raw + bcrypt format, verify round-trip, wrong-password,
distinct-salts, the 72-byte boundary, malformed-hash → False, and DUMMY_HASH
format (the constant-time-miss sentinel).
"""

from __future__ import annotations

from platform_layer.identity.passwords import DUMMY_HASH, hash_password, verify_password

# asyncio_mode=auto (pyproject) auto-detects async tests.


async def test_hash_then_verify_round_trip() -> None:
    raw = "correct horse battery staple"
    hashed = await hash_password(raw)
    assert hashed != raw
    assert hashed.startswith("$2b$12$")  # bcrypt cost=12
    assert await verify_password(raw, hashed) is True


async def test_wrong_password_fails() -> None:
    hashed = await hash_password("right-password")
    assert await verify_password("wrong-password", hashed) is False


async def test_same_password_two_hashes_differ_but_both_verify() -> None:
    h1 = await hash_password("samepw")
    h2 = await hash_password("samepw")
    assert h1 != h2  # distinct salts
    assert await verify_password("samepw", h1) is True
    assert await verify_password("samepw", h2) is True


async def test_72_char_password_verifies() -> None:
    pw = "a" * 72  # 72 ASCII bytes — bcrypt's exact limit
    hashed = await hash_password(pw)
    assert await verify_password(pw, hashed) is True


async def test_verify_malformed_hash_returns_false() -> None:
    # A non-bcrypt stored value must never raise — just fail to verify.
    assert await verify_password("anything", "not-a-bcrypt-hash") is False


def test_dummy_hash_is_bcrypt_format() -> None:
    assert DUMMY_HASH.startswith("$2b$12$")
