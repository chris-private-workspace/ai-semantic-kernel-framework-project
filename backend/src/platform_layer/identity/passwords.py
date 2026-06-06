"""
File: src/platform_layer/identity/passwords.py
Purpose: bcrypt local-password hashing util — hash_password / verify_password.
Category: platform_layer / Identity (cross-cutting auth, not an 11+1 范畴 surface)
Scope: Phase 57 / Sprint 57.86 (C-12 IAM Block B/C — local credentials)

Description:
    Pure (DB-free) password hashing for local credentials. Uses bcrypt directly
    (no passlib middle layer — avoids passlib's bcrypt-4.x compat warnings).
    bcrypt's hashpw/checkpw are synchronous + CPU-bound, so both functions
    offload to a worker thread via anyio.to_thread.run_sync to keep the async
    event loop responsive under concurrent logins.

    bcrypt only considers the first 72 BYTES of the password (it truncates the
    rest). We truncate the UTF-8 bytes to 72 ourselves in BOTH hash and verify,
    so the behaviour is deterministic + version-independent (some bcrypt builds
    raise on > 72 bytes rather than truncating). The API layer additionally caps
    password fields at max_length=72 (chars). A 72-char ASCII password is 72
    bytes → unaffected; the cap is a footgun guard, not a strength policy
    (password-strength rules are an explicit 57.86 carryover).

Key Components:
    - hash_password(raw): bcrypt hash (cost=12) of the password → str
    - verify_password(raw, hashed): constant-time bcrypt compare → bool

Created: 2026-06-06 (Sprint 57.86)
Last Modified: 2026-06-06

Modification History (newest-first):
    - 2026-06-06: Initial creation (Sprint 57.86) — bcrypt hash/verify util

Related:
    - platform_layer/identity/credentials.py — CredentialsService (consumer)
    - sprint-57-86-plan.md §3.2
"""

from __future__ import annotations

import secrets

import anyio
import bcrypt

# bcrypt work factor. 12 is a common 2020s default (~250ms/hash on commodity
# hardware) — strong enough to slow brute-force, cheap enough for interactive
# login. Raise as hardware improves.
_BCRYPT_ROUNDS = 12

# bcrypt only hashes the first 72 bytes; truncate ourselves for deterministic,
# version-independent behaviour (see module docstring).
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(raw: str) -> bytes:
    """UTF-8 encode the password and truncate to bcrypt's 72-byte limit."""
    return raw.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def _hash_sync(raw: str) -> str:
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(_to_bcrypt_bytes(raw), salt).decode("ascii")


def _verify_sync(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(raw), hashed.encode("ascii"))
    except ValueError:
        # Malformed stored hash → treat as a non-match (never raise to caller).
        return False


async def hash_password(raw: str) -> str:
    """Return a bcrypt hash (cost=12) of ``raw``. Offloaded off the event loop."""
    return await anyio.to_thread.run_sync(_hash_sync, raw)


async def verify_password(raw: str, hashed: str) -> bool:
    """Return True iff ``raw`` matches the bcrypt ``hashed``. Offloaded; never raises."""
    return await anyio.to_thread.run_sync(_verify_sync, raw, hashed)


# A throwaway hash (computed once at import). Login can run a verify against it on
# the user-absent / no-password path so the response latency of "no such user"
# matches "wrong password" — i.e. timing can't be used to enumerate tenants/users.
DUMMY_HASH: str = _hash_sync(secrets.token_urlsafe(16))
