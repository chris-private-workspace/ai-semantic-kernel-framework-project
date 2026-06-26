# IPA Platform - Intelligent Process Automation

<div align="center">

![Status](https://img.shields.io/badge/Status-V2_Active-success)
![Phase](https://img.shields.io/badge/Phase-57_SaaS_Frontend-blueviolet)
![Tests](https://img.shields.io/badge/Tests-2930_backend_%2B_922_frontend-brightgreen)
![Coverage](https://img.shields.io/badge/Coverage-80%25+-green)
![License](https://img.shields.io/badge/License-Proprietary-red)

**Enterprise AI agent platform — server-side TAO/ReAct agent harness · 11+1 categories · LLM-provider-neutral**

[English](#) | [繁體中文](#)

</div>

---

## ⚡ V2 — Phase 57 (SaaS Frontend, ongoing as of 2026-06)

> **V1 (Phase 1-48) is archived and frozen** in `archived/v1-phase1-48/`.
> V2 is the active platform. The V1 sections further below are preserved
> for historical reference only.

V2 is a ground-up rebuild around an 11+1-category **server-side agent harness**
(not a patch of V1). It is **not** built on Microsoft Agent Framework — MAF was
archived with V1; V2 is **LLM-provider-neutral** (CI-enforced).

| Item | V1 (frozen) | V2 (active) |
|------|-------------|-------------|
| Architecture | MAF + Claude SDK hybrid orchestrator | TAO/ReAct agent harness · 11+1 categories · LLM-provider-neutral (CI-enforced) |
| Source location | `archived/v1-phase1-48/` (READ-ONLY) | `backend/`, `frontend/` (active V2 codebase) |
| Status | `v1-final-phase48` — MVP complete | V2 core **22/22 ✅** + SaaS Stage 1 **3/3 ✅** + Phase 57 frontend **ongoing** |
| Maturity | ~27% real alignment (audited 2026-04) | 11+1 categories all **Level 4** (Cat 9 Level 5) · multi-tenant 3-rule isolation |

### V2 references

- **Project memory / navigation** (start here): [`CLAUDE.md`](CLAUDE.md)
- **V2 vision**: [`docs/03-implementation/agent-harness-planning/00-v2-vision.md`](docs/03-implementation/agent-harness-planning/00-v2-vision.md)
- **11+1 categories spec**: [`docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md`](docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md)
- **Phase roadmap**: [`docs/03-implementation/agent-harness-planning/06-phase-roadmap.md`](docs/03-implementation/agent-harness-planning/06-phase-roadmap.md)
- **Highest-level principles** (server-side / LLM-neutrality / CC reference): [`docs/03-implementation/agent-harness-planning/10-server-side-philosophy.md`](docs/03-implementation/agent-harness-planning/10-server-side-philosophy.md)
- **V1 archive notes**: [`archived/v1-phase1-48/README.md`](archived/v1-phase1-48/README.md)

### Dev environment

```bash
# Unified dev manager (recommended) — see CLAUDE.md §Development Commands
python scripts/dev.py status              # show service status
python scripts/dev.py start               # start all (backend / frontend / infra)
python scripts/dev.py start backend       # or a single service
python scripts/dev.py logs docker -f      # tail infra logs

# Infra only (PostgreSQL / Redis / RabbitMQ)
docker compose -f docker-compose.dev.yml up -d

# Frontend (React 18 + Vite)
cd frontend && npm install && npm run dev
```

| Service | Port |
|---------|------|
| Backend (FastAPI, `backend/src/api/main.py`) | 8000 |
| Frontend (React 18 + Vite) | 3005 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| RabbitMQ | 5672 / 15672 |

---

## 📦 V1 Historical Content (frozen on 2026-04-29)

> **The sections below describe V1 as it stood at the time of archive.**
> They are preserved for historical reference only. V1 is no longer
> being developed. The badges + overview at the top now reflect **current
> V2 status**; the V1 stats below (285 story points, 6 sprints, 812 tests,
> MAF) are the V1-final snapshot.

---

## Project Overview

**IPA Platform** (Intelligent Process Automation) is an enterprise-grade AI Agent orchestration platform designed for mid-size enterprises (500-2000 employees).

### Key Stats

| Metric | Value |
|--------|-------|
| **Status** | MVP Complete |
| **Story Points** | 285/285 (100%) |
| **Sprints** | 6 Completed |
| **Tests** | 812 |
| **API Routes** | 155 |
| **Domain Modules** | 15 |

### Core Technology

- **Framework**: Microsoft Agent Framework (Preview) - unifies Semantic Kernel + AutoGen
- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18 + TypeScript + Vite
- **Database**: PostgreSQL 16 + Redis 7
- **Messaging**: RabbitMQ

---

## Core Features

### 1. AI Agent Orchestration Engine
Based on Microsoft Agent Framework with complex multi-step workflow support:
- **Sequential**: Task A → Task B → Task C
- **Parallel**: Task A + B + C simultaneously
- **Conditional**: IF-THEN-ELSE logic
- **Loop**: WHILE loops and iterations

### 2. Human-in-the-Loop Checkpoints
High-risk operations require human approval:
```yaml
checkpoints:
  - step: "delete_database"
    type: "manual"
    approvers: ["admin@company.com"]
    timeout: "2h"
```

### 3. Cross-System Integration
Connect enterprise systems for 360° unified view:
- **ServiceNow**: Ticket history and SLA status
- **Dynamics 365**: Customer and order data
- **SharePoint**: Documents and knowledge base

### 4. Few-shot Learning
Agents learn from human corrections:
- Record human decision modifications
- Generate few-shot examples
- Automatically apply improvements

### 5. Visual Workflow Editor
Drag-and-drop editor built with React Flow:
- Visual node connections
- Real-time preview
- Version management and rollback

---

## Architecture

```
Frontend (React 18 + TypeScript, port 3000)
    ↓ HTTPS
Backend (FastAPI, port 8000)
    ├─ 15 API Modules
    │   ├─ agents/          # Agent CRUD and configuration
    │   ├─ workflows/       # Workflow management
    │   ├─ executions/      # Execution lifecycle
    │   ├─ checkpoints/     # Human-in-the-loop approvals
    │   ├─ connectors/      # External system integrations
    │   ├─ triggers/        # Workflow trigger definitions
    │   ├─ routing/         # Intelligent task routing
    │   ├─ templates/       # Workflow templates
    │   ├─ prompts/         # Prompt management
    │   ├─ learning/        # Few-shot learning
    │   ├─ notifications/   # Teams/email notifications
    │   ├─ audit/           # Audit logging
    │   ├─ cache/           # LLM response caching
    │   ├─ devtools/        # Developer utilities
    │   └─ versioning/      # Version control
    │
    ├─ Domain Services
    │   ├─ Execution State Machine
    │   ├─ Checkpoint Storage
    │   └─ Intelligent Routing
    │
    └─ Infrastructure
        ├─ PostgreSQL 16 (Primary Database)
        ├─ Redis 7 (Cache + LLM Response Cache)
        └─ RabbitMQ (Message Queue)
```

### Frontend Pages

| Page | Description |
|------|-------------|
| Dashboard | Overview and metrics |
| Workflows | Workflow management |
| Agents | Agent configuration |
| Executions | Execution monitoring |
| Templates | Workflow templates |
| Analytics | Business analytics |
| Settings | System settings |

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Primary language |
| FastAPI | 0.100+ | REST API framework |
| Agent Framework | Preview | AI Agent orchestration |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.0+ | Data validation |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2+ | UI framework |
| TypeScript | 5.0+ | Type safety |
| Vite | 5.0+ | Build tool |
| Shadcn UI | Latest | Component library |
| React Flow | 11.10+ | Workflow editor |
| Zustand | Latest | State management |
| TanStack Query | 5.0+ | Data fetching |

### Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 16 | Primary database |
| Redis | 7 | Cache and session |
| RabbitMQ | 3.12+ | Message queue |
| Docker | 20.10+ | Containerization |

---

## Quick Start

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+
- **Docker**: 20.10+
- **Azure OpenAI**: API access for Agent Framework

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/laitim2001/ai-semantic-kernel-framework-project.git
cd ai-semantic-kernel-framework-project

# 2. Start infrastructure (PostgreSQL, Redis, RabbitMQ)
docker-compose up -d

# 3. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Start backend server
uvicorn main:app --reload --port 8000

# 5. Setup frontend (new terminal)
cd frontend
npm install
npm run dev
```

Access the application at http://localhost:3000

### Environment Variables

Create `.env` file:

```bash
# Database
DB_NAME=ipa_platform
DB_USER=ipa_user
DB_PASSWORD=ipa_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Azure OpenAI (for Agent Framework)
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

> See `.env.example` for the full V2 variable list (DB / Redis / RabbitMQ / Qdrant / Azure OpenAI / JWT / WorkOS OIDC / OTel / Sentry).

**Auth in local dev**: you do **not** need a WorkOS account. Leave `WORKOS_API_KEY` blank — the OIDC routes (`/api/v1/auth/login`, `/callback`) return 503, and the login page shows a "Dev login" form (`POST /api/v1/auth/dev-login`) that issues a platform-admin session against an auto-created `dev` tenant. Real SSO is only required in staging/prod.

### Health Check

```bash
curl http://localhost:8000/health
```

---

## Development Commands

### Backend

```bash
cd backend/

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Code quality
black .                    # Format code
isort .                    # Sort imports
flake8 .                   # Lint
mypy .                     # Type check

# Testing
pytest                     # All tests
pytest tests/unit/         # Unit tests only
pytest -v --cov=src        # With coverage
```

### Frontend

```bash
cd frontend/

npm install                # Install dependencies
npm run dev                # Development server
npm run build              # Production build
npm run lint               # Lint code
```

### Docker

```bash
docker-compose up -d       # Start all services
docker-compose down -v     # Stop and remove volumes
docker-compose logs -f     # View logs
```

---

## Documentation

### Key Documents

| Document | Description |
|----------|-------------|
| [CLAUDE.md](./CLAUDE.md) | AI assistant instructions |
| [Technical Architecture](./docs/02-architecture/technical-architecture.md) | System architecture |
| [PRD](./archived/docs-v1/01-planning/prd/prd-main.md) | Product requirements |
| [MVP Summary](./archived/docs-v1/03-implementation/MVP-COMPLETION-SUMMARY.md) | MVP completion report |

### Sprint Documentation

All sprint planning and execution documentation is available in:
- `archived/docs-v1/03-implementation/sprint-planning/` - Sprint plans and checklists
- `archived/docs-v1/03-implementation/sprint-execution/` - Progress and decisions

### User Guides

- [User Guide](./archived/docs-v1/user-guide/) - End user documentation
- [Admin Guide](./archived/docs-v1/admin-guide/) - Administrator documentation

---

## Project Status

### MVP Completion Summary

| Sprint | Focus | Points | Status |
|--------|-------|--------|--------|
| Sprint 0 | Infrastructure Foundation | 42 | ✅ Complete |
| Sprint 1 | Core Services | 45 | ✅ Complete |
| Sprint 2 | Integration Services | 40 | ✅ Complete |
| Sprint 3 | Advanced Features | 45 | ✅ Complete |
| Sprint 4 | Frontend Implementation | 55 | ✅ Complete |
| Sprint 5 | DevOps & QA | 35 | ✅ Complete |
| Sprint 6 | Polish & Documentation | 23 | ✅ Complete |
| **Total** | | **285** | **100%** |

### Test Coverage

| Category | Tests | Coverage |
|----------|-------|----------|
| Unit Tests | 650+ | 85%+ |
| Integration Tests | 100+ | 80%+ |
| E2E Tests | 50+ | Core flows |
| Security Tests | 12+ | OWASP Top 10 |

---

## Security

### Security Features

- **Authentication**: OAuth 2.0 + JWT with Azure AD
- **Authorization**: RBAC (Admin, User, Viewer, Agent roles)
- **Encryption**: AES-256-GCM at rest
- **API Security**: Rate limiting, CORS, Input validation
- **Audit**: Complete operation logging

### Vulnerability Reporting

Report security vulnerabilities to: security@company.com

---

## License

This project is under **Proprietary License**. Unauthorized copying, distribution, or modification is prohibited.

© 2025 Company Name. All Rights Reserved.

---

## Acknowledgments

Thanks to these open source projects:
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Microsoft Semantic Kernel](https://github.com/microsoft/semantic-kernel)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React Flow](https://reactflow.dev/)
- [Shadcn UI](https://ui.shadcn.com/)

---

<div align="center">

**Built with ❤️ by IPA Platform Team**

[⬆ Back to Top](#ipa-platform---intelligent-process-automation)

</div>
