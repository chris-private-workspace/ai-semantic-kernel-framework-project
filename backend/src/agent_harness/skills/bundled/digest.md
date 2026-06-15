---
name: digest
description: Compute the canonical SHA-256 digest by running this skill's bundled script.
---

# Digest

This skill ships a bundled executable script that computes a canonical SHA-256 digest.

When the user asks for the canonical digest (or to "run the digest skill"):

1. Call `run_skill_script("digest")` to execute the bundled script in the sandbox.
2. Read the hex digest the script prints to `stdout` and report it exactly.

Do not compute the digest yourself — always run the bundled script and report its output.
