# Git Workflow Rules — V2

**Purpose**: Standardize commits, branches, and PRs for V2 multi-provider, multi-tenant platform.

**Category**: Version Control / Development Process
**Created**: 2025 (V1 original)
**Last Modified**: 2026-04-28
**Status**: Active

> **Modification History**
> - 2026-04-28: Rewrite for V2 — replace V1 scope set (6 generic) with 11+1 categories (23 scopes), link sprint-workflow.md, update examples
> - 2025: Initial V1 version (api/domain/infra/frontend scopes)

---

## Commit Message Format

All commits must follow Conventional Commits + co-author convention:

```
<type>(<scope>, [sprint-XX-Y]): <description>

[optional body]

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types

| Type | Use For |
|------|---------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only (no code) |
| `refactor` | Code restructure (no feature/fix) |
| `test` | Unit/integration tests only |
| `chore` | Build, CI, deps, tooling |

---

## Scopes — V2 Catalog

### 11+1 Core Categories

| Scope | Category | Phase |
|-------|---------|-------|
| `orchestrator-loop` | Orchestrator (Cat 1) | 50.1 |
| `tools` | Tool Layer (Cat 2) | 51.1 |
| `memory` | Memory (Cat 3) | 51.2 |
| `context-mgmt` | Context Management (Cat 4) | 52.1 |
| `prompt-builder` | Prompt Building (Cat 5) | 52.2 |
| `output-parser` | Output Parsing (Cat 6) | 50.1 |
| `state-mgmt` | State Management (Cat 7) | 53.1 |
| `error-handling` | Error Handling (Cat 8) | 53.2 |
| `guardrails` | Guardrails & Safety (Cat 9) | 53.3 |
| `verification` | Verification (Cat 10) | 54.1 |
| `subagent` | Subagent Orchestration (Cat 11) | 54.2 |
| `observability` | Observability / Tracing (Cat 12, cross-cutting) | 49.4+ |

### Platform / Governance / Infrastructure

| Scope | Use For |
|-------|---------|
| `platform` | Multi-tenant identity, governance, workers |
| `governance` | Risk, HITL, audit |
| `identity` | Auth, roles, RLS |
| `workers` | Celery / Temporal selection |
| `api` | FastAPI endpoints |
| `core` | Config, logging, exceptions |

### Adapters (LLM providers, frameworks)

| Scope | Use For |
|-------|---------|
| `adapters-base` | ChatClient ABC + 中性型別 |
| `adapters-azure-openai` | Azure OpenAI implementation |
| `adapters-anthropic` | Anthropic integration (Phase 50+) |
| `adapters-openai` | OpenAI integration (Phase 50+) |

### Business Domains (per 08b-business-tools-spec.md)

| Scope | Use For |
|-------|---------|
| `business-patrol` | Patrol / monitoring domain |
| `business-correlation` | Event correlation |
| `business-rootcause` | Root cause analysis |
| `business-audit` | Business audit / compliance |
| `business-incident` | Incident management |

### Frontend (per 16-frontend-design.md)

| Scope | Use For |
|-------|---------|
| `frontend-page-XX` | Specific page implementation (XX = page number) |
| `frontend-shared` | Shared components / hooks / stores |

### Cross-Cutting / Infrastructure

| Scope | Use For |
|-------|---------|
| `docs` | Planning docs, design, reference |
| `ci` | GitHub Actions, CI/CD pipelines |
| `infra` | Docker, K8s, deployment |
| `archive` | V1 archival, deprecation |
| `sprint-XX-Y` | Sprint-specific (when scope doesn't fit above) |

---

## Examples

```
feat(orchestrator-loop, sprint-50-1): implement TAO loop with async iterator
fix(guardrails, sprint-53-3): resolve tripwire false-positive on PII regex for European names
docs(api, sprint-49-1): add V2 backend README with architecture diagram
refactor(memory, sprint-51-2): extract MemoryRetrieval into separate module
test(subagent, sprint-54-2): add unit tests for SubagentDispatcher.dispatch()
chore(ci, sprint-49-1): add GitHub Actions backend-ci.yml workflow
chore(archive, sprint-49-1): move V1 (Phase 1-48) to archived/v1-phase1-48
feat(adapters-azure-openai): handle token count for vision models correctly
feat(frontend-page-02, sprint-55-2): add approval decision modal with Teams notification
docs(archive): mark V1 MSALAuthProvider deprecated (Phase 56+ removal plan)
```

---

## Branch Naming

```
feature/<scope>-<short-description>
fix/<scope>-<short-description>
refactor/<scope>-<short-description>
archive/<tag-or-reason>
```

### Examples

```
feature/sprint-49-1-v2-foundation
feature/orchestrator-loop-tao-loop
fix/guardrails-jailbreak-false-positive
refactor/memory-extract-retrieval
archive/v1-phase1-48
```

**Rules**:
- Use scope from commit message
- Lowercase, dash-separated
- ≤ 60 characters
- Create branch from `main` or release branch
- Delete after merge (keep repo clean)

---

## Before You Commit — Mandatory Checklist

### 1. Sprint Workflow (sprint-workflow.md)

- [ ] Sprint plan exists (`phase-XX-Y/sprint-XX-Y-plan.md`)
- [ ] Sprint checklist exists (`phase-XX-Y/sprint-XX-Y-checklist.md`)
- [ ] Checklist entry `[ ]` updated to `[x]` (or marked `[阻塞]`)
- [ ] File header updated (file-header-convention.md)

### 2. Code Quality (code-quality.md)

#### Backend (Python)

```bash
cd backend
black . --check
isort . --check
flake8 .
mypy . --strict
```

#### Frontend (TypeScript/React)

```bash
cd frontend
npm run lint
npm run build
```

**Failure → don't commit**. Fix and retry.

### 3. Tests (testing.md)

#### Backend

```bash
cd backend
pytest --cov=src --cov-report=term-missing
```

- ✅ New code must have ≥ 80% coverage
- ✅ Existing tests must pass
- ✅ No `@pytest.mark.skip` on tests (if broken, fix or remove)

#### Frontend

```bash
cd frontend
npm run test
```

### 4. Anti-Patterns Check (anti-patterns-checklist.md 11 points)

```
✅ AP-1 No Pipeline-disguised-as-Loop (if has LLM calls)
✅ AP-2 No side-track (traceable from api/)
✅ AP-3 No cross-directory scattering
✅ AP-4 No Potemkin features
✅ AP-5 No undocumented PoC
✅ AP-6 No "future-proof" abstraction without real use case
✅ AP-7 Context rot mitigated (if long conversation)
✅ AP-8 Via PromptBuilder (if has LLM calls)
✅ AP-9 Has verification (if output generation)
✅ AP-10 Mock and real share ABC
✅ AP-11 No version suffix; naming consistent
```

### 5. No Prohibited Imports (llm-provider-neutrality.md)

In `backend/src/agent_harness/**/*.py`:
```bash
grep -r "^import openai\|^import anthropic\|^from openai\|^from anthropic" .
# Should return empty
```

✅ **Correct**: Import via `adapters/_base/chat_client.py`

### 6. No Secrets / Binaries / Generated Files

```bash
git status
# Must NOT contain:
#  - .env (use .env.example)
#  - *.pem, *.key
#  - build/, dist/, __pycache__/, node_modules/
#  - large binary files (use Git LFS)
```

---

## Commit Message Examples (V2 Real Cases)

### 1. Archive V1

```
chore(archive, sprint-49-1): move V1 (Phase 1-48) to archived/v1-phase1-48

- Move backend/ → archived/v1-phase1-48/backend/
- Move frontend/ → archived/v1-phase1-48/frontend/
- Move infrastructure/ → archived/v1-phase1-48/infrastructure/
- Tag v1-final-phase48 (27% alignment baseline)
- Add READ-ONLY warning to archived/v1-phase1-48/README.md

See: docs/03-implementation/agent-harness-planning/03-rebirth-strategy.md §V1 Archival

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 2. Build V2 Skeleton

```
feat(core, sprint-49-1): create V2 backend directory skeleton (11 scopes + contracts)

- Create agent_harness/ with 11 scope directories
- Create _contracts/ single-source package
- Create platform/, adapters/, api/, business_domain/, infrastructure/, core/

All scopes importable; no business logic yet.

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 3. Fix Guardrails Bug

```
fix(guardrails, sprint-53-3): resolve tripwire false-positive on PII regex for European names

- Replace regex-based detection with LLM-judge + name-entity tagger
- Add test: test_pii_detector_european_names (20 case fixtures)
- Coverage: 87% → 93%

Fixes issue #456. See claudedocs/4-changes/bug-fixes/FIX-256-pii-regex-false-positive.md

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 4. Frontend Component

```
feat(frontend-page-02, sprint-55-2): build approval decision modal with Teams notification

- Component: ApprovalDecisionModal (React + Zustand)
- Integration: POST /api/v1/governance/approvals/{approval_id}/decide
- Teams webhook: POST when decision made
- Tests: 12 unit tests + 3 integration tests

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 5. Refactor Memory

```
refactor(memory, sprint-51-2): extract MemoryRetrieval into separate module

- Split memory/_abc.py into _abc.py + retrieval.py
- Improve type hints (no more `Any` in retrieval signature)
- Tests: All 24 existing tests pass; coverage 88% → 92%

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Pull Request Workflow

### PR Title

Same as commit (single commit) or summary:
```
Phase 49 Sprint 1: V1 archive + V2 foundation skeleton
```

### PR Description Template

```markdown
## Summary

- Archive V1 (Phase 1-48) to read-only baseline
- Build V2 backend directory skeleton (11 scopes + _contracts)
- Add CI pipeline (GitHub Actions)

## Plan & Checklist

- **Plan**: [sprint-49-1-plan.md](...)
- **Checklist**: [sprint-49-1-checklist.md](...)

## Anti-Pattern Checklist

- [ ] AP-1 to AP-11 (see anti-patterns-checklist.md)

## Verification

- [ ] All tests passing
- [ ] Code quality passing
- [ ] No business logic (grep agent_framework/openai/anthropic = empty)
- [ ] Sprint plan + checklist linked above

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Prohibited Actions

- ❌ **Force push to main**: FORBIDDEN
- ❌ **Commit secrets**: `.env`, `*.pem`, API keys → immediate rotation
- ❌ **Commit large binaries**: > 50 MB → use Git LFS
- ❌ **Commit unformatted code**: Will fail CI
- ❌ **Delete tests**: Talk to lead if cleanup needed
- ❌ **Scope creep without updating plan**
- ❌ **Skip sprint workflow**: Every commit must map to sprint checklist + file header update
- ❌ **Skip anti-patterns checklist**

---

## V2-Specific Rules

### LLM Provider Neutrality ⭐

- ❌ No `import openai` / `import anthropic` in `agent_harness/`
- ❌ No hardcoded model names (use `adapters/_base/chat_client.py`)
- ✅ All LLM calls via ChatClient ABC

See: `llm-provider-neutrality.md`

### Scope Isolation

- ❌ No cross-scope imports except via `_contracts/`
- ✅ Use 11+1 scope catalog above

See: `category-boundaries.md`

### Sprint Linkage

- ✅ Commit message includes scope + sprint ID
- ✅ File header has Scope: "Sprint XX.Y"
- ✅ Checklist entry marked before/after commit

---

## References

| Document | Purpose |
|----------|---------|
| sprint-workflow.md | 5-step execution + change records |
| anti-patterns-checklist.md | 11-point code review |
| category-boundaries.md | Scope isolation rules |
| llm-provider-neutrality.md | LLM SDK ban + ChatClient ABC |
| file-header-convention.md | Header format |
| code-quality.md | Lint / format / type hints |
| testing.md | Test requirements |
| CLAUDE.md §Code Standards | Overarching standards |
| 06-phase-roadmap.md | 22 sprint organization |
| 17-cross-category-interfaces.md | Contract specs |

---

**Applies To**: V2 Phase 49+ (all repositories within agent-harness-planning)
