"""Bundled executable script for the 'digest' skill (Sprint 57.118 demo).

Computes a canonical SHA-256 digest at RUNTIME and prints it. The value is not
something a language model can fabricate, so a drive-through that reports this exact
digest proves the sandbox actually executed the script (vs the model reciting a value).
Run via the run_skill_script("digest") tool — NOT imported as a module.
"""

import hashlib

CANONICAL_INPUT = b"agent-harness-bundled-skill"

print(hashlib.sha256(CANONICAL_INPUT).hexdigest())
