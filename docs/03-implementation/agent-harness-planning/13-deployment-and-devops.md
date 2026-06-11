# V2 部署與 DevOps 策略

**建立日期**：2026-04-23
**版本**：V2.0
**對應**：Phase 49.1 起持續使用

---

## 部署環境分層

```
┌────────────────────────────────────────┐
│ Production（生產）                      │
│ 正式服務，client 使用                    │
└──────────────┬─────────────────────────┘
               ↑ Promotion
┌────────────────────────────────────────┐
│ Staging（預備）                         │
│ Production 鏡像，pre-release 驗證        │
└──────────────┬─────────────────────────┘
               ↑ Promotion
┌────────────────────────────────────────┐
│ Integration（整合測試）                  │
│ E2E 測試環境，每日跑                     │
└──────────────┬─────────────────────────┘
               ↑ Auto deploy
┌────────────────────────────────────────┐
│ Development（開發）                      │
│ 開發者本地 Docker Compose                │
└────────────────────────────────────────┘
```

### 環境配置對比

| 環境 | DB | Redis | LLM | Worker | 用途 |
|------|----|-----|-----|--------|------|
| Dev | Postgres container | Redis container | Mock + Real（dev quota）| 1 worker | 個人開發 |
| Integration | Postgres container | Redis container | Real（test tenant）| 2 workers | E2E + integration test |
| Staging | Managed Postgres | Managed Redis | Real（prod-like）| 3-5 workers | Pre-release |
| Prod | Managed HA Postgres | Managed Redis Cluster | Real | Auto-scale 5-50 | 正式服務 |

---

## CI/CD Pipeline 設計

### Pipeline 階段

```
┌──────────────────────────────────────────────────┐
│ Stage 1: Pre-flight checks（每 PR）              │
│ - Lint（11 anti-patterns）                       │
│ - Type check（mypy strict）                      │
│ - Security scan（bandit + safety + npm audit）   │
│ - 預估時間：< 3 分鐘                             │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ Stage 2: Unit tests（每 PR）                      │
│ - pytest backend/tests/unit/                     │
│ - vitest frontend/tests/unit/                    │
│ - Coverage ≥ 80% required                        │
│ - 預估時間：< 5 分鐘                             │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ Stage 3: Integration tests（每 PR）              │
│ - Real DB / Redis（in container）                │
│ - Mock LLM                                       │
│ - 預估時間：< 15 分鐘                            │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ Stage 4: Build & Push（merge to main 後）        │
│ - Docker build backend + frontend                │
│ - Push to registry（Azure Container Registry）   │
│ - Image tag: git-sha + branch                    │
│ - 預估時間：< 8 分鐘                             │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ Stage 5: Deploy to Integration（自動）           │
│ - Apply migrations                               │
│ - Rolling update                                 │
│ - Smoke test                                     │
│ - 預估時間：< 5 分鐘                             │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ Stage 6: E2E tests（每日）                       │
│ - 跑 Playwright（前端）                          │
│ - 跑關鍵案例（APAC 銷售分析等）                   │
│ - Real LLM（cost-aware quota）                   │
│ - 預估時間：< 60 分鐘                            │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ Stage 7: Deploy to Staging（手動觸發）           │
│ - Performance baseline test                      │
│ - Security scan（DAST）                          │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ Stage 8: Deploy to Production（手動 + approval） │
│ - Canary rollout（10% → 50% → 100%）             │
│ - Auto-rollback on alerts                        │
└──────────────────────────────────────────────────┘
```

### CI 工具選型

| 用途 | 工具 |
|------|------|
| CI 平台 | **GitHub Actions** 或 **Azure DevOps Pipelines** |
| Container registry | **Azure Container Registry** |
| Secret management | **Azure Key Vault** |
| Artifact storage | **Azure Blob Storage** |
| Deployment | **Helm charts**（為將來 K8s）+ Docker Compose（當前） |

---

### Branch Protection（main）— Sprint 52.6 US-5（with 53.2 + 53.2.5 + 53.7 evolution）

> **Background**：Sprint 52.2 PR #20 + Sprint 52.5 PR #19 均使用 admin-merge bypass red CI，違反 Sprint 52.5 retrospective §AD-2 教訓。Sprint 52.6 US-5 強制設定 main branch protection rule，杜絕未來 admin-merge precedent。
>
> **2026-05-03 Sprint 53.2 update**：solo-dev policy 永久將 `required_approving_review_count: 1 → 0`（GitHub 阻擋 PR-author self-approve；solo dev 無第二 reviewer）。`enforce_admins=true` 保留。
>
> **2026-05-03 Sprint 53.2.5 update**：archive `.github/workflows/ci.yml` 後，4 條對應 status checks（Code Quality / Tests / Frontend Tests / CI Summary）permanently dropped — 它們是 V1 monolithic CI 之 jobs，已被 backend-ci.yml + frontend-ci.yml 之 jobs 涵蓋（自 d5352359 拆分以來）。**非降級，是去重**。

#### 必選 Status Checks（4 條當前 active；2026-05-03 起）

```
- Lint + Type Check + Test (with PostgreSQL 16)  # backend-ci.yml lint-and-test
- Backend E2E Tests                               # e2e-tests.yml
- E2E Test Summary                                # e2e-tests.yml aggregator
- v2-lints                                        # lint.yml (V2 lint rules)
```

#### Permanently Dropped（archived in Sprint 53.2.5）

```
- Code Quality       # was ci.yml lint job; redundant w/ backend-ci.yml lint-and-test
- Tests              # was ci.yml test job; redundant w/ backend-ci.yml lint-and-test
- Frontend Tests     # was ci.yml frontend-test job; redundant w/ frontend-ci.yml lint-and-build
- CI Summary         # was ci.yml meta aggregator; redundant w/ 4 active required checks
```

#### 必選 Options

| Option | 設定 | 理由 |
|--------|------|------|
| Require status checks before merging | ✅ | 8 條全綠 |
| Require branches to be up to date | ✅ | strict mode；防止 base 漂移 |
| Require pull request reviews | ✅（min **0** approval；2026-05-03 solo-dev policy）| 原 53.2 前=1；solo dev = no 2nd reviewer；GitHub 阻擋 author self-approve；保留 enforce_admins=true 之 audit gate |
| Restrict who can push | ✅（admin only）| 防止 force push |
| Allow force pushes | ❌ | 保留 git history |
| Allow deletions | ❌ | 防止誤刪 main |
| **Allow administrators to bypass** | **❌**（**關鍵**）| 杜絕 admin-merge norm；52.5 §AD-2 教訓 |

#### `gh api` 等價設定命令（reproducibility）

```bash
# 當前 (2026-05-04 Sprint 53.7 之後) 設定 -- 5 contexts
gh api -X PUT repos/laitim2001/ai-semantic-kernel-framework-project/branches/main/protection \
  -F required_status_checks[strict]=true \
  -f required_status_checks[contexts][]="Lint + Type Check + Test (with PostgreSQL 16)" \
  -f required_status_checks[contexts][]="Backend E2E Tests" \
  -f required_status_checks[contexts][]="E2E Test Summary" \
  -f required_status_checks[contexts][]="v2-lints" \
  -f required_status_checks[contexts][]="Frontend E2E (chromium headless)" \
  -F enforce_admins=true \
  -F required_pull_request_reviews[required_approving_review_count]=0 \
  -F required_pull_request_reviews[dismiss_stale_reviews]=false \
  -F restrictions= \
  -F allow_force_pushes=false \
  -F allow_deletions=false
```

> **Future un-do（當第 2 collaborator 加入時）**：
> ```bash
> echo '{"required_approving_review_count":1,"dismiss_stale_reviews":false,"require_code_owner_reviews":false}' \
>   | gh api -X PATCH repos/laitim2001/ai-semantic-kernel-framework-project/branches/main/protection/required_pull_request_reviews \
>   --input -
> ```

> **Note on `enforce_admins=true`**：GitHub 的 `enforce_admins` 對映 UI 「Do not allow bypassing the above settings」勾選。設 true = admin **無法** bypass red CI / missing review。Sprint 52.6 US-5 紀律核心。
>
> **2026-05-04 Sprint 53.7 chaos verification**: AI-22 chaos test 透過 dummy red PR + admin merge 嘗試實際驗證 enforce_admins 真有效。GitHub GraphQL API 拒絕 admin merge 訊息：`"5 of 5 required status checks have not succeeded: 3 expected. (mergePullRequest)"`. 證明 admin 無法繞過。完整紀錄見 `docs/03-implementation/agent-harness-execution/phase-53-7-audit-cleanup-cat9-quickwins/sprint-53-7-audit-cleanup-cat9-quickwins/chaos-test-enforce-admins.md`.

#### 違反舉證測試（Sprint 52.6 Day 4 / 後續任何 sprint 可重複）

```bash
# 1. 故意推一個 black-violator commit 到 test/ branch
git checkout -b test/branch-protection-verify
echo "x=1" >> backend/src/some_file.py  # bad indentation
git add ... && git commit -m "test: intentional black violation"
git push origin test/branch-protection-verify

# 2. 開 PR
gh pr create --title "test: branch protection lockdown" ...

# 3. 等 CI 跑紅
gh pr view <id> --json statusCheckRollup -q '.statusCheckRollup[] | select(.conclusion == "FAILURE")'

# 4. 嘗試 admin merge → 應該被擋
gh pr merge <id> --merge  # 預期失敗（required check pending OR admin bypass disabled）
gh pr merge <id> --admin --merge  # 預期失敗（enforce_admins=true）

# 5. 清理
gh pr close <id> && git push origin --delete test/branch-protection-verify
```

#### 維護紀律

- 每次新增 CI workflow 必須加進 status checks（or rule needs update）
- workflow rename 必須同步 update protection rule
- `enforce_admins=true` 不得改回 false（必要 emergency override 須 documented + audit log）
- `required_approving_review_count=0`（solo-dev policy）— 當第 2 collaborator 加入時 1-line PATCH 還原為 1

#### Changelog

| Date | Sprint | Change | Reason |
|------|------|------|------|
| 2026-05-01 | 52.6 US-5 | 8 required status checks + enforce_admins=true + review_count=1 | 杜絕 admin-merge bypass precedent |
| 2026-05-03 | 53.2 PR #48 | review_count: 1 → 0（permanent solo-dev policy） | GitHub 阻擋 PR author self-approve；solo dev = no 2nd human reviewer；replaces 3rd temp-relax bootstrap (52.6 #28 + 53.1 #39 used 2x) |
| 2026-05-03 | 53.2.5 PR #50 | 8 → 4 required checks（drop Code Quality / Tests / Frontend Tests / CI Summary） | ci.yml archived; 4 dropped 是 V1 monolithic CI 之 jobs，已被 backend-ci.yml + frontend-ci.yml 涵蓋（自 d5352359 起重複）。**非降級，是去重**。 |

---

## Docker 化規格

### Backend Dockerfile（多階段建構，**2026-04-28 review 修訂**：builder / runtime 分離）

> **Review 修訂**：原 Dockerfile 把 `build-essential + libpq-dev + curl` 留到最終 image，size 過大。改純 builder / runtime 兩階段，runtime 完全乾淨。

```dockerfile
# backend/Dockerfile

# === Stage 1: builder ===
FROM python:3.11-slim AS builder
WORKDIR /app

# 系統依賴僅在 builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python wheels 編譯到 venv，後續 copy
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# === Stage 2: runtime ===
FROM python:3.11-slim AS runtime
WORKDIR /app

# Runtime 僅需 libpq5（不含 build-essential / libpq-dev）
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Non-root user
RUN useradd --create-home --shell /bin/bash ipa \
    && mkdir -p /app && chown -R ipa:ipa /app
USER ipa

COPY --chown=ipa:ipa src ./src
COPY --chown=ipa:ipa scripts ./scripts

EXPOSE 8000

# ⭐ Healthcheck 用 python urllib（不裝 curl，省 size）
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/_internal/health', timeout=5)" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `.dockerignore`（**新增，避免污染 build context**）

```gitignore
# backend/.dockerignore
.git
.github
.venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.coverage
htmlcov
node_modules
*.log
.env
.env.*
docs
tests
```

### Frontend Dockerfile（**修訂**：non-root nginx + 健檢用 wget）

```dockerfile
# frontend/Dockerfile

# === Stage 1: deps ===
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# === Stage 2: build ===
FROM deps AS build
COPY . .
RUN npm run build

# === Stage 3: runtime（nginx-unprivileged，non-root by default）===
FROM nginxinc/nginx-unprivileged:1.25-alpine AS prod
USER nginx                                    # ⭐ non-root
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080                                   # nginx-unprivileged 預設 8080（非 80）

# ⭐ Healthcheck 用 wget（busybox 內建，不需裝 curl）
HEALTHCHECK CMD wget -q --spider http://localhost:8080/health || exit 1
```

### Image Vulnerability Scan（**2026-04-28 新增**）

CI Stage 4 加入 Trivy / Snyk scan：

```yaml
# .github/workflows/backend-ci.yml (Stage 4 後)
- name: Build Docker image
  run: docker build -t backend:${{ github.sha }} backend/

- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: backend:${{ github.sha }}
    severity: 'CRITICAL,HIGH'
    exit-code: '1'                            # CRITICAL/HIGH 直接 fail PR
    ignore-unfixed: true
```

### docker-compose.dev.yml（Phase 49 起用）

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ipa_v2
      POSTGRES_USER: ipa_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./scripts/db-init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ipa_user"]
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports: ["6379:6379"]

  qdrant:
    image: qdrant/qdrant:v1.7
    volumes:
      - qdrant_data:/qdrant/storage
    ports: ["6333:6333", "6334:6334"]

  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: ipa
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    ports: ["5672:5672", "15672:15672"]

  jaeger:
    image: jaegertracing/all-in-one:1.51
    ports: ["16686:16686", "4318:4318"]

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    volumes:
      - grafana_data:/var/lib/grafana

  backend-api:
    build: ./backend
    environment:
      DB_URL: postgresql+asyncpg://ipa_user:${DB_PASSWORD}@postgres:5432/ipa_v2
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      QDRANT_URL: http://qdrant:6333
      OTEL_ENDPOINT: http://jaeger:4318
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_started }
    ports: ["8000:8000"]
    volumes:
      - ./backend/src:/app/src  # hot reload

  agent-worker:
    build: ./backend
    command: ["python", "-m", "src.runtime.workers.runner"]
    environment: # 同 backend-api
    depends_on: { backend-api: { condition: service_started } }

  frontend:
    build:
      context: ./frontend
      target: build  # dev 模式不用 nginx
    command: npm run dev
    ports: ["3000:5173"]
    volumes:
      - ./frontend/src:/app/src

volumes:
  pg_data:
  redis_data:
  qdrant_data:
  grafana_data:
```

---

## 環境變數與 Secret 管理

### 三層 Secret 策略

```
1. Local dev:
   - .env 檔（git ignored）
   - 從 .env.example 複製

2. CI / Integration:
   - GitHub Actions secrets / Azure DevOps variable groups
   - ⭐ branch-scoped：prod secrets 僅 main 分支可用（feature branch 無法解鎖）

3. Staging / Production:
   - Azure Key Vault
   - 透過 Workload Identity 注入
   - 不在容器映像中
```

### Secret Rotation 政策（**2026-04-28 review 新增**）

| Secret 類型 | 輪換週期 | 輪換方式 |
|-----------|--------|---------|
| API keys（Azure OpenAI / Anthropic） | 90 天 | KeyVault rotation policy + dual-key overlap 7 天 |
| DB passwords | 90 天 | rolling rotation（先建新 user → 切換 → 刪舊） |
| JWT signing key | 180 天 | dual-key overlap 24 小時 |
| Encryption master key | 12 個月 | KMS auto-rotate + envelope re-encrypt batch |
| Service principal | 365 天 | Entra ID auto-rotate |
| Webhook secrets（Teams / Stripe） | 90 天 | 平台支援雙簽名期間 |

**演練**：每季跑一次 secret rotation 演練（Phase 53.4 起）。

### Secret Scanning（**新增**）

CI Stage 1 加入 secret leak detection：

```yaml
# .github/workflows/secret-scan.yml
on: [pull_request, push]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
          GITLEAKS_NOTIFY_USER_LIST: '@security-team'
```

```toml
# .gitleaks.toml（自訂 rules）
[allowlist]
paths = ['''.*\.example$''', '''docs/.*''']  # .env.example / docs 例外

[[rules]]
id = "azure-openai-key"
regex = '''[A-Za-z0-9]{32,}'''
keywords = ["AZURE_OPENAI_API_KEY"]
```

**強制**：偵測到 secret leak → PR 立即 block；如已 push 到 main，強制 force-revert + key rotation 演練。

### .env.example 範本

```bash
# Database
DB_URL=postgresql+asyncpg://ipa_user:CHANGE_ME@localhost:5432/ipa_v2
DB_PASSWORD=CHANGE_ME

# Redis
REDIS_URL=redis://:CHANGE_ME@localhost:6379
REDIS_PASSWORD=CHANGE_ME

# Qdrant
QDRANT_URL=http://localhost:6333

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=CHANGE_ME
AZURE_OPENAI_DEPLOYMENT_GPT54=gpt-5-4
AZURE_OPENAI_DEPLOYMENT_MINI=gpt-5-4-mini

# Anthropic（如公司開放）
# ANTHROPIC_API_KEY=

# Auth (Entra ID)
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# Microsoft Teams（HITL 通知）
TEAMS_WEBHOOK_URL=

# Observability
OTEL_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=ipa-backend

# Feature flags
FEATURE_VERIFICATION_ENABLED=true
FEATURE_THINKING_ENABLED=true

# Cost limits（per-tenant default）
DEFAULT_TENANT_TOKEN_QUOTA_PER_DAY=1000000
DEFAULT_TENANT_COST_QUOTA_USD_PER_DAY=50.0
```

---

## Migration 與 Rollback 策略

### Migration 規則（**2026-04-28 review 修訂**：forward-fix-only）

```python
# alembic.ini 設定 + scripts/migrate.py 包裝

# Phase 49.2 開始的所有 migration：
# 1. 必須有 upgrade()；downgrade() 僅 dev 用，production 走 forward-fix
# 2. 必須在 staging 跑過至少 1 次
# 3. 必須包含資料保護（CONCURRENTLY index、避免 lock）
# 4. 不破壞性原則：先 add column，再 backfill，再 use，最後 drop old
# 5. ⭐ Lock 時長 dry-run 檢測（見下）
# 6. ⭐ Migration 與 code release 解耦（feature flag / shadow deploy）
```

### Forward-Fix-Only 政策（**2026-04-28 review 新增**）

> **Review 發現**：原 `scripts/rollback.sh` 用 `alembic downgrade` 在 production 極危險（資料丟失）。本次明確政策。

| 場景 | 處置 |
|------|------|
| **Code bug** | Revert code commit → re-deploy（migration 不動） |
| **Migration 帶 bug 但已上 prod** | **不 downgrade**。寫新 migration 修正（forward fix） |
| **Migration 失敗（中途）** | 自動 rollback 該 transaction（PostgreSQL DDL transactional）+ alert + 不 retry |
| **Migration 完成但 code deploy 失敗** | re-deploy old code（向後相容必須由 migration 設計保證） |

```bash
# scripts/migrate-prod.sh（forward-fix-only）
set -euo pipefail

echo "Production migration policy: forward-fix-only."
echo "Downgrade is NOT supported on production."

# 1. dry-run lock detection
python scripts/migration_lock_check.py --target head --max-lock-seconds 30

# 2. 執行 upgrade（含 timeout）
alembic -c alembic.ini upgrade head

# 3. 監控確認
python scripts/post_migration_check.py
```

### Migration Lock 監控（**2026-04-28 review 新增**）

```python
# scripts/migration_lock_check.py
async def check_migration_locks(max_lock_seconds: int = 30):
    """跑 migration 前 dry-run，估算各 statement 的 lock 時長。
    若 ALTER TABLE 預估 lock 全表 > max_lock_seconds → fail；
    建議改 CONCURRENTLY 或拆分。"""

    # 從 pg_stat_activity 即時監控
    locks = await db.fetch("""
        SELECT pid, query, state, wait_event,
               EXTRACT(EPOCH FROM (now() - query_start)) AS duration_s
        FROM pg_stat_activity
        WHERE state != 'idle'
          AND wait_event_type = 'Lock'
    """)

    if any(l['duration_s'] > max_lock_seconds for l in locks):
        raise MigrationLockError(...)

# Production deploy 期間每 5 秒輪詢
```

### Migration / Deploy 解耦（**2026-04-28 review 新增**）

> 業界共識：DB schema migration 與 application deploy 必須解耦。

```
Day 0: Add new column (nullable, default NULL)
       ↓ deploy migration
       ↓ code 仍寫舊欄位（feature flag = OFF）
Day 1: Deploy new code（dual-write，feature flag = OFF）
Day 2: Enable feature flag for 1% canary
Day 3: Gradual rollout 10% / 50% / 100%
Day N: Backfill 完成，舊欄位停用
Day N+7: Drop old column（separate migration PR）
```

### Zero-downtime Migration 模式

```
Phase 1: Add new column（nullable）
Phase 2: Deploy code（同時讀寫新舊欄位，feature flag 控制）
Phase 3: Backfill 資料（batch worker，可中斷）
Phase 4: Deploy code（只用新欄位）
Phase 5: Drop old column（最少 7 天 grace period）
```

### Rollback 計畫（**修訂**：code-only rollback）

```bash
# scripts/rollback.sh（code-only，DB schema 不動）
set -euo pipefail

# 1. 檢查當前 git SHA
CURRENT=$(git rev-parse HEAD)
PREVIOUS=$(git rev-parse HEAD~1)

# 2. Revert code commit（產生新 commit，不 force-push）
git revert --no-edit $CURRENT

# 3. Re-deploy old code via CI
gh workflow run deploy.yml --ref main

# 4. 監控指標驗證（5xx / latency 是否回穩）
python scripts/post_rollback_check.py --watch-minutes 15

# ⛔ 絕對禁止：alembic downgrade
echo "If DB schema needs fixing, write a NEW forward migration."
```

---

## Observability 整合

### 監控金字塔

```
┌────────────────────────────────────────┐
│ Alerts（PagerDuty / Teams）            │ ← 最少
├────────────────────────────────────────┤
│ SLO Dashboard（Grafana）               │
├────────────────────────────────────────┤
│ Metrics（Prometheus）                  │
├────────────────────────────────────────┤
│ Distributed Traces（Jaeger）           │
├────────────────────────────────────────┤
│ Structured Logs（Loki / ELK）          │ ← 最多
└────────────────────────────────────────┘
```

### 必須監控的指標（**2026-04-28 review 修訂**：RED/USE method + 拆 LLM cost dimensions）

依 **RED method**（Rate / Errors / Duration）+ **USE method**（Utilization / Saturation / Errors）組織。

#### Service-Level（RED）

| 指標 | 維度 | 目標 |
|------|------|------|
| **Rate** | Requests/sec per endpoint | 監控趨勢 |
| **Errors** | 5xx rate per endpoint | < 0.1% |
| **Duration** | API p50 / p95 / p99 per endpoint | p99 < 1s |
| **Availability** | API uptime | > 99.9%（Enterprise） |

#### Infrastructure-Level（USE）

| 指標 | 維度 | 目標 |
|------|------|------|
| **Utilization** | CPU / Memory per pod | < 75% |
| **Saturation** | Worker queue lag | < 5s |
| **Errors** | Pod restart count | < 1/day |
| **DB** | Connection pool usage（Utilization） | < 80% |
| **DB** | Query p99（Duration） | < 50ms |
| **Redis** | Hit ratio | > 95% |

#### LLM 三軸（per-tenant × per-model × per-phase，**修訂**）

> **Review 發現**：原 LLM cost 太粗。本次拆三軸，便於 cost analysis。

| 指標 | 維度 | 目標 |
|------|------|------|
| `agent.tokens.input` | per_tenant × per_model × per_phase | per-tenant quota |
| `agent.tokens.output` | per_tenant × per_model × per_phase | per-tenant quota |
| `agent.tokens.cached` | per_tenant × per_model | hit rate > 50% |
| `agent.cost.usd` | per_tenant × per_model × per_phase | per-tenant budget |
| `cost_per_successful_task` | per_tenant × per_phase | < $0.50（中等任務） |
| `wallet_attack_detector.flagged` | per_tenant | < 1/day |

#### Agent Loop 業務指標

| 指標 | 維度 | 目標 |
|------|------|------|
| `agent.loop.turns` | per_tenant | 監控趨勢（突增 → 異常） |
| `agent.verification.pass_rate` | per_tenant | > 90% |
| `agent.compaction.rate` | per_tenant | < 10% sessions |
| `agent.hitl.queue_size` | per_tenant | gauge |
| `agent.hitl.notification_latency_ms` | per_tenant | < 60_000（Enterprise） |
| `agent.subagent.spawned_per_session` | per_tenant | 監控趨勢 |

### SLO + Error Budget（**2026-04-28 review 新增**）

> **Review 發現**：原文件只有 thresholds，無 SLO / error budget 概念。本節補。

```yaml
# slo-config.yaml（per service per environment）
slos:
  - name: api-availability-prod
    description: "Production API availability (Enterprise tier)"
    sli: |
      sum(rate(http_requests_total{status!~"5..",env="prod"}[28d]))
      / sum(rate(http_requests_total{env="prod"}[28d]))
    target: 0.999                # 99.9% over 28-day window
    error_budget_consumption_alert: 0.5    # 用掉 50% budget 即 alert
    error_budget_exhaustion_action: "freeze_non_critical_releases"

  - name: api-latency-p99
    sli: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{env="prod"}[28d])) by (le))
    target_value: "< 1.0"         # 1 second
    rolling_window: 28d

  - name: agent-loop-success-rate
    sli: sum(rate(agent_loop_completed{verification_passed="true"}[28d])) / sum(rate(agent_loop_completed[28d]))
    target: 0.95                  # 95% verification pass rate
    rolling_window: 28d
```

**Error Budget 規則**：
- 28-day rolling window
- 用掉 50% → alert engineering manager
- 用掉 75% → freeze non-critical feature releases，只允許 bug fix
- 用掉 100% → 全面凍結，召開 retro

### Trace Sampling 策略（**2026-04-28 review 新增**）

> **Review 發現**：原文件未指定 trace sampling，100% 取樣會爆。

```yaml
# otel-config.yaml
sampling:
  strategy: head_based + tail_based composite

  head_based:
    default: 1%                   # 一般請求 1% 取樣
    rules:
      - match: { http.route: "/health" }
        rate: 0%                  # health check 不採樣
      - match: { tenant.tier: "enterprise" }
        rate: 5%                  # enterprise tier 多採樣
      - match: { agent.subagent: true }
        rate: 10%                 # subagent 較複雜多採樣

  tail_based:
    rules:
      - match: { error: true }
        rate: 100%                # 錯誤 100% 採樣
      - match: { duration: "> 5s" }
        rate: 100%                # 慢請求 100% 採樣
      - match: { hitl: true }
        rate: 100%                # HITL 100% 採樣（合規）
```

### Log Retention / Cost Cap（**2026-04-28 review 新增**）

| Log Tier | Retention | Storage | 成本估算 |
|---------|----------|---------|---------|
| Hot (Loki) | 7 天 | SSD | 高 |
| Warm (S3 Standard) | 30 天 | Object | 中 |
| Cold (S3 Glacier) | 7 年（合規） | Archive | 低 |
| Audit log（特殊） | 7 年 + Object Lock WORM | Compliance tier | 中高 |

**Cost cap**：每月 logging cost > $5K → alert engineering ops；對 verbose log 自動降級為 sample。

### Alerts 配置

```yaml
# monitoring/alerts.yml
- name: high_5xx_rate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
  severity: critical
  notify: pagerduty + teams

- name: worker_queue_backlog
  expr: queue_size > 100
  severity: warning
  notify: teams

- name: tenant_cost_limit
  expr: tenant_cost_usd_today > tenant_cost_quota_today * 0.9
  severity: warning
  notify: tenant_admin + teams

- name: tripwire_fired
  expr: rate(guardrail_tripwire_total[1m]) > 0
  severity: critical
  notify: security_team
```

---

## K8s 規劃（Phase 56+）

雖然本期不部署 K8s，先預留設計：

### Helm chart 結構

```
charts/ipa-platform/
├── Chart.yaml
├── values.yaml
├── values.staging.yaml
├── values.prod.yaml
└── templates/
    ├── backend-api/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── hpa.yaml
    │   ├── pdb.yaml
    │   └── ingress.yaml
    ├── agent-worker/
    │   ├── deployment.yaml
    │   ├── hpa.yaml
    │   └── pdb.yaml
    ├── postgres/  # 或外部 managed
    ├── redis/
    └── secrets/
```

### Probe 設計

```yaml
# backend-api/deployment.yaml
livenessProbe:
  httpGet:
    path: /api/v1/_internal/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/_internal/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5

startupProbe:
  httpGet:
    path: /api/v1/_internal/health
    port: 8000
  failureThreshold: 30
  periodSeconds: 10
```

### Auto-scaling（HPA）

```yaml
# backend-api/hpa.yaml
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 }}
    - type: Resource
      resource: { name: memory, target: { type: Utilization, averageUtilization: 80 }}

# agent-worker/hpa.yaml
spec:
  minReplicas: 5
  maxReplicas: 50
  metrics:
    - type: External
      external:
        metric: { name: rabbitmq_queue_size }
        target: { type: AverageValue, averageValue: 10 }
```

---

## Disaster Recovery / Backup

### Backup 策略

| 資源 | Backup 頻率 | 保留期 | RPO | RTO |
|------|----------|------|-----|-----|
| PostgreSQL | 每小時增量 + 每日全量 | 30 天 | 1 hr | 4 hr |
| Qdrant | 每日全量 | 30 天 | 24 hr | 4 hr |
| Object storage（artifacts） | 持續複製 | 90 天 | < 1 min | < 15 min |
| Audit log | 即時複製到冷儲 | **永久** | < 1 min | N/A |
| Redis | 不 backup | N/A | N/A | 重建 |

### DR 演練

每季度執行：
1. 模擬 region 失效
2. 從 backup 還原到 DR region
3. 驗證資料完整性
4. 量測 RPO / RTO 達成度

---

## 工作流程

### Daily 開發
1. 早上 `git pull main`
2. `docker compose up -d`（背景跑依賴）
3. 開發 + 跑單元測試
4. 推 PR → CI 自動跑
5. Code review + merge
6. 自動 deploy 到 integration 環境

### Weekly 部署
1. Monday：merge accumulated PRs
2. Tuesday：promote to staging + 跑性能測試
3. Wednesday-Thursday：bug fix
4. Friday：production deploy（canary 10% → 50% → 100%）

### Incident response
1. Alert 觸發 → on-call 接收
2. 5 分鐘內 acknowledge
3. 15 分鐘內 mitigation（rollback / scale / disable feature）
4. 30 分鐘內 root cause initial assessment
5. 24 小時內完整 post-mortem

---

## 結語

Phase 49.1 起應建立：
- [ ] docker-compose.dev.yml
- [ ] .env.example
- [ ] backend Dockerfile
- [ ] frontend Dockerfile
- [ ] CI Stage 1-3（pre-flight + unit + integration）

Phase 50 起：
- [ ] CI Stage 4-6（build / push / e2e）
- [ ] OTel + Prometheus + Grafana 整合

Phase 53+：
- [ ] CI Stage 7-8（staging / prod canary）
- [ ] DR 演練

Phase 56+：
- [ ] Helm chart + K8s migration

---

## §Production App Role（Sprint 49.4 Day 5.2 補入；49.3 retro Action item #2 RESOLVED）

### 為何重要

Sprint 49.3 Day 4.2 落地 13 張 tenant-scoped 表的 RLS policies + per-request `SET LOCAL app.tenant_id`。**RLS 強制是 tenant 隔離的最後一道防線**：即使應用層 query 漏寫 `WHERE tenant_id = ?`，DB 層仍會擋下跨 tenant 讀寫。

但 **PostgreSQL `SUPERUSER` 與 `BYPASSRLS` 兩個 attribute 任何一個都會繞過 RLS**，包含 `FORCE ROW LEVEL SECURITY` 也無效。

Sprint 49.3 RLS 測試發現 dev container 預設 user `ipa_v2` 同時擁有 `rolsuper=true` 與 `rolbypassrls=true` —— 這在 dev 是 PostgreSQL image 預設，但**生產絕對不可如此**。否則：

- 應用 query bug 不會被 RLS 擋
- 應用持有 SUPERUSER 連線 = 等於沒有 RLS
- 攻擊者奪取應用 DB 憑證 = 跨 tenant 全曝光

### 生產規範（強制）

#### 規範 A — App role 屬性

生產環境**禁止**用 `postgres` / `ipa_v2` 等帶 `SUPERUSER` 或 `BYPASSRLS` 的 role 連線。應用必須用專用 app role：

```sql
-- 生產 app role 範例（在 init 時 owner role 執行）
CREATE ROLE app_ipa_v2 NOLOGIN;
ALTER ROLE app_ipa_v2 WITH NOSUPERUSER NOBYPASSRLS;

-- 授予 schema-level 權限
GRANT USAGE ON SCHEMA public TO app_ipa_v2;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_ipa_v2;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_ipa_v2;

-- 確保未來新建表也自動繼承
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_ipa_v2;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_ipa_v2;

-- 應用透過 LOGIN role 繼承 app_ipa_v2 屬性（典型管法：login user 屬於 app_ipa_v2 group）
CREATE ROLE app_ipa_v2_login LOGIN PASSWORD '<env secret>' IN ROLE app_ipa_v2;
```

關鍵屬性：
- `NOSUPERUSER` — 不可繞 RLS / 不可 ALTER SYSTEM / 不可 COPY FROM PROGRAM
- `NOBYPASSRLS` — `FORCE RLS` 對此 role 有效
- 最小權限 GRANT — 只 CRUD `public` schema 業務表
- 不授予 DDL（CREATE / ALTER / DROP TABLE）— migration 由獨立 owner role 執行

#### 規範 B — Connection string 範例

```bash
# DEV（仍可用 SUPERUSER 簡化開發）
DATABASE_URL=postgresql+asyncpg://ipa_v2:ipa_v2_dev@localhost:5432/ipa_v2

# STAGING / PROD（必須用受限 app role）
DATABASE_URL=postgresql+asyncpg://app_ipa_v2_login:${APP_DB_PASSWORD}@<host>:5432/ipa_v2
```

`APP_DB_PASSWORD` 透過 K8s Secret / Vault / AWS Secrets Manager 注入，**禁止寫入 .env file 或 Helm chart**。

#### 規範 C — Migration role 區隔

Alembic migrations 需 DDL 權限（CREATE TABLE / CREATE POLICY / ALTER）。**App role 不可有 DDL**。建議：

```sql
-- 獨立的 migration owner role（CI/CD pipeline 才知道密碼）
CREATE ROLE owner_ipa_v2 LOGIN PASSWORD '<rotated env secret>';
GRANT ALL PRIVILEGES ON SCHEMA public TO owner_ipa_v2;
```

CI/CD migration step：
```bash
# Migration step uses owner role
DATABASE_URL=postgresql+asyncpg://owner_ipa_v2:... alembic upgrade head

# Application step uses app role
DATABASE_URL=postgresql+asyncpg://app_ipa_v2_login:... uvicorn api.main:app
```

#### 規範 D — RLS 真實有效性測試

每個生產部署 release 前 CI 必須跑：

```sql
-- Test: connect as app role; try to read another tenant's row
SET LOCAL app.tenant_id = '<tenant-A-uuid>';
SELECT count(*) FROM messages;  -- 必須只看到 tenant A 的訊息

-- Test: try to bypass with SET LOCAL app.tenant_id manipulation
SELECT set_config('app.tenant_id', '<tenant-B-uuid>', false);  -- false = SESSION not LOCAL
SELECT count(*) FROM messages;  -- 仍應只看到 tenant A（如果 connection pooler 重設了 LOCAL）
```

Sprint 49.3 紅隊已驗證；生產 deploy 還要重跑一次（不同 user 不同密碼可能有差）。

#### 規範 E — Audit

監控 + 警報：

```sql
-- 警報：app role 不可有 SUPERUSER / BYPASSRLS
SELECT rolname, rolsuper, rolbypassrls
FROM pg_roles
WHERE rolname IN ('app_ipa_v2', 'app_ipa_v2_login')
  AND (rolsuper OR rolbypassrls);
-- 預期：0 rows. 任何 row 都是 critical alert.
```

Grafana / CloudWatch alarm：每小時跑一次此 query，> 0 rows → page on-call。

### Phase 49.4 status

- [x] 規範 A-E 文件化（本節）
- [ ] CI deploy gate 引入規範 E 警報（Phase 55 production cutover 前）
- [ ] App role 在 staging 環境配置（Phase 53.1+）
- [x] 49.3 retro Action item #2 RESOLVED ✅

### Cross-references

- Sprint 49.3 retro Action item #2
- `0009_rls_policies.py` — 建立 13 張表 RLS policies
- `platform_layer/middleware/tenant_context.py` — `SET LOCAL app.tenant_id` 實作
- `.claude/rules/multi-tenant-data.md` — 鐵律 1+2+3 連動

---

## §Audit Verification（Sprint 52.5 Day 4-5 P0 #13）

`audit_log` 採 per-tenant SHA-256 hash chain 確保 append-only + tamper-evident。
Hash chain 是「自證」結構 —— **驗證程式不存在 = 任何篡改都靜默成功**。
W1-3 audit 實測：用 superuser INSERT 假 `current_log_hash="f"*64` 的 row，
0 偵測。本節定義 verifier 的部署、運維與告警機制。

### 元件

```
┌────────────────────────────┐
│ docker-compose.dev.yml      │  audit_verifier service (supercronic)
│   service: audit_verifier   │
└──────────────┬──────────────┘
               │ daily 02:00 UTC
               ▼
┌────────────────────────────┐
│ scripts/verify_audit_chain  │  asyncpg + stdlib only (no FastAPI)
│   --ignore-tenant ...       │  per-tenant chain walk
│   --alert-webhook ...       │  POST tamper report on failure
└──────────────┬──────────────┘
               │ exit code
               ▼
        0 = pass  / 1 = tamper / 2 = config error
```

### Verifier CLI（`backend/scripts/verify_audit_chain.py`）

```bash
# Ad-hoc 全表驗證
DATABASE_URL=postgresql://ipa_v2:ipa_v2_dev@localhost:5432/ipa_v2 \
    python -m scripts.verify_audit_chain

# 略過 W1-3 audit 留下的 forgery 基線（tenant aaaa-...-4444 row id=36-39）
python -m scripts.verify_audit_chain \
    --ignore-tenant aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa4444

# 限定單 tenant + 部分時間窗口 + 失敗時 webhook
python -m scripts.verify_audit_chain \
    --tenant <UUID> --from-date 2026-04-01 \
    --alert-webhook https://hooks.slack.com/services/...

# Cron-friendly 單行輸出
python -m scripts.verify_audit_chain --quiet
```

兩重檢查獨立並行：
- **broken_link**：row N+1 的 `previous_log_hash` ≠ row N 的 `current_log_hash`
- **curr_hash_mismatch**：`SHA256(stored_prev || canonical_json(payload) || tenant_id || ts_ms)`
  ≠ row 的 stored `current_log_hash`

任一觸發即 exit 1 + 列出篡改起點 row id；webhook 收到 JSON payload `{tampers, summary}`。

### Docker / Cron 部署

`docker-compose.dev.yml` 已包含 `audit_verifier` service：
- Image: `python:3.12-slim` + asyncpg pre-install + supercronic
  （`docker/audit-verifier/Dockerfile`）
- Crontab: `02:00 UTC` daily（`docker/audit-verifier/crontab`）
- Bind-mount `backend/src` + `backend/scripts` (read-only) → 改 verifier 不需 rebuild
- `depends_on.postgres.condition: service_healthy` → 等 DB ready 才啟動 cron

啟動：

```bash
docker compose -f docker-compose.dev.yml up -d audit_verifier
docker logs -f ipa_v2_audit_verifier
```

手動單次驗證（不等下一個 cron tick）：

```bash
docker compose -f docker-compose.dev.yml run --rm audit_verifier \
    python -m scripts.verify_audit_chain --ignore-tenant aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa4444
```

### 告警

dev 環境：supercronic stdout 由 `docker logs ipa_v2_audit_verifier` 採集，
搭配 Loki / docker-syslog → Grafana 告警。

prod 環境：在 compose 加 `ALERT_WEBHOOK_URL` env var → verifier 失敗時 POST。
建議 webhook target：
- 內部 Slack/Teams channel `#sec-audit`
- PagerDuty service（24/7 incident response）
- SIEM ingestion endpoint（如 Splunk HEC）

Webhook 載荷範例：

```json
{
  "status": "fail",
  "tampers": [
    {
      "tenant_id": "...",
      "row_id": 39,
      "error_type": "curr_hash_mismatch",
      "expected": "abcd1234...",
      "actual": "ffffffff...",
      "operation": "tool_executed",
      "created_at": "2026-04-29T..."
    }
  ],
  "summary": {"rows": 12345, "tenants": 7, "ignored_tenants": ["aaaa..."]}
}
```

### 運維 Runbook

**篡改告警觸發 → 即時動作**：

1. 凍結相關 tenant 寫入：`UPDATE tenants SET status='frozen' WHERE id = ?`
   （或業務層 feature flag）
2. 輸出 forensics：`pg_dump -t audit_log --where "tenant_id='<UUID>'" > forensics.sql`
3. 比對 row N 的 prev_hash 與 row N-1 的 curr_hash 是否分別來源於：
   - 應用層 INSERT（檢查 connection log）
   - DB superuser INSERT（檢查 PG audit log + role assumptions）
4. 若發現是 superuser INSERT，啟動人員 access 調查 + key rotation
5. **不要直接刪除告警 row** — 保留為 evidence；若需要恢復 chain 連續性，
   記錄修補手續為新 audit row

**已知 baseline noise（不需告警）**：

| Tenant | 原因 | Source |
|--------|------|--------|
| `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa4444` | W1-3 audit 留下的 forgery rows id=36-39（驗證 verifier 確能偵測） | `claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-W1-AUDIT-HASH.md` |

部署到 staging / prod 之前需 DBA cleanup（`DELETE FROM audit_log WHERE tenant_id='aaaa...4444'`
+ 紀錄到 retrospective），或繼續用 `--ignore-tenant` 略過。

### 測試

`backend/tests/unit/scripts/test_verify_audit_chain.py`（11 cases，0.14s）保證：
- Hash compute 與 `audit_helper.compute_audit_hash` byte-identical（最關鍵）
- broken_link / curr_hash_mismatch 各自獨立偵測
- 同時被 tamper 兩處（payload 改 + curr_hash 重算 + 下一 row prev_hash 沒更新）
  → 至少 broken_link 觸發
- `--ignore-tenant` / `--from-date` / asyncpg URL normalisation 正確

### 引用

- 09-db-schema-design.md L654-717（Group 7 Audit + hash chain spec）
- 14-security-deep-dive.md §append-only / hash chain
- backend/src/infrastructure/db/audit_helper.py（canonical hash compute）
- backend/scripts/verify_audit_chain.py
- docker/audit-verifier/{Dockerfile, crontab}
- claudedocs/5-status/v2-audit-2026-04/V2-AUDIT-W1-AUDIT-HASH.md（audit source）
