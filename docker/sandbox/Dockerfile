# V2 Sandbox image — short-lived containers run user-supplied Python code
# under hard isolation per execution.
#
# Sprint 52.5 P0 #17: replaces SubprocessSandbox (W4P-3 audit found it
# decorative on Windows — resource.setrlimit is POSIX-only, network_blocked
# was a `# noqa: ARG002` doc-only flag, agent listed C:/ from inside).
#
# Per-container hardening (set at `docker run` time, NOT in this image):
#   --memory <limit>     enforce RSS cap (kills OOM)
#   --cpus <fraction>    fair-share CPU
#   --network none       no egress (or `bridge` if network_blocked=False)
#   --read-only          rootfs read-only; only /tmp writable (tmpfs)
#   --cap-drop ALL       no Linux capabilities at all
#   --user 65534:65534   run as nobody (defined below for clarity)
#   --pids-limit 64      cap process count
#
# These options can't be set in the image; they're DockerSandbox.execute()'s
# job. The image's only contributions are:
#   - python:3.12-slim base (minimal attack surface)
#   - non-root user (defence in depth)
#   - working dir /sandbox owned by that user

FROM python:3.12-slim

# Drop most binary surface; we only need cpython + stdlib.
# (The image is tiny enough already at python:3.12-slim ~125 MB.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# UID 65534 = nobody. Sandbox child code never elevates.
RUN useradd --uid 65534 --no-create-home --shell /bin/false sandbox \
    || true  # tolerate distros where uid 65534 already exists as nobody

# numpy: LLM-generated analysis code reaches for numpy by default. Without it,
# python_sandbox runs but every numpy script fails ModuleNotFoundError (FIX-033
# drive-through 2026-06-18). Installed as root (before USER drop); read-only
# runtime rootfs still allows import from system site-packages.
RUN pip install --no-cache-dir numpy

# /sandbox holds the user code at runtime, mounted at exec time.
WORKDIR /sandbox

# No CMD: every `docker run` invocation supplies the python entrypoint
# explicitly via `python -c <code>` or `python /sandbox/main.py`.
# This keeps the image agnostic of how DockerSandbox feeds code in.
USER 65534:65534
