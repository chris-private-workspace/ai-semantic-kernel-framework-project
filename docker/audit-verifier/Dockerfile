# V2 Audit-verifier image — runs scripts/verify_audit_chain.py on a daily cron.
#
# Sprint 52.5 P0 #13 phase 2: matches the same pattern used by mock_services
# (python:3.12-slim + bind-mounted source + lazy pip install) BUT pre-installs
# asyncpg in the image to avoid a fresh pip resolve on every cron tick.
#
# Verifier deliberately depends on ONLY asyncpg + stdlib (no FastAPI / no
# SQLAlchemy / no app config) so the image stays small + boot is fast.

FROM python:3.12-slim

# Install asyncpg and supercronic (cron with proper signal handling).
# supercronic is preferred over busybox crond inside docker because it forwards
# SIGTERM to child jobs cleanly + logs to stdout (no /var/log/cron tailing).
ARG SUPERCRONIC_VERSION=v0.2.30
ARG SUPERCRONIC_SHA1=9f27ad28c5c57cd133325b2a66bba69ba2235799
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && pip install --no-cache-dir asyncpg==0.30.0 \
    && curl -fsSL -o /usr/local/bin/supercronic "${SUPERCRONIC_URL}" \
    && echo "${SUPERCRONIC_SHA1}  /usr/local/bin/supercronic" | sha1sum -c - \
    && chmod +x /usr/local/bin/supercronic \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# /scripts will be bind-mounted from backend/scripts at runtime — keep it
# bind-only so dev-mode edits to verify_audit_chain.py take effect without
# rebuilding the image.
WORKDIR /app

# Default crontab: 02:00 UTC daily.
# Tenant aaaa-...-4444 holds W1-3 audit forgery rows id=36-39 — must be
# ignored or the job exits 1 on every run. Override via $IGNORE_TENANTS env
# at compose level if your DB has additional baseline noise.
COPY docker/audit-verifier/crontab /etc/audit-verifier-crontab

# supercronic logs runs + job exit codes to stdout (docker logs picks them up).
CMD ["/usr/local/bin/supercronic", "-passthrough-logs", "/etc/audit-verifier-crontab"]
