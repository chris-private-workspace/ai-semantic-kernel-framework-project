# ClaudeDocs - AI Assistant Documentation Directory

> **Related Rules**: See `.claude/rules/` for complete documentation standards

## Purpose

This directory is the documentation center for AI assistant (Claude) and development team collaboration, organized using a structured 7-layer classification covering the complete lifecycle from planning, development, to operations. These documents are used for:

- **Project Planning**: Phase/Sprint architecture design, feature planning, roadmaps
- **Progress Tracking**: Daily/weekly progress reports, Sprint plans
- **Change Management**: Bug fix records, feature change tracking
- **AI Collaboration**: Situation prompts, workflow guides, analysis reports
- **Knowledge Transfer**: Development experience, troubleshooting, deployment guides

---

## Project Overview - IPA Platform

### Core Goals
- **Platform Position**: Enterprise AI Agent orchestration platform (Intelligent Process Automation)
- **Core Framework**: Microsoft Agent Framework + Claude Agent SDK + AG-UI Protocol
- **Target Users**: IT Operations teams, Customer Service teams
- **Business Value**: 40%+ reduction in IT processing time, 12-month ROI > 200%

### Core Architecture - Three-tier Intent Routing System

```
┌─────────────────────────────────────────────────────────────────┐
│ TIER 1: Pattern Matcher                                          │
│ • Fast matching of known patterns using regex                    │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2: Semantic Router                                          │
│ • Semantic similarity matching using embeddings                  │
├─────────────────────────────────────────────────────────────────┤
│ TIER 3: LLM Classifier                                           │
│ • LLM-based intent classification when above tiers don't match  │
└─────────────────────────────────────────────────────────────────┘
```

### Risk Assessment Routing

| Risk Level | Handling | Description |
|------------|----------|-------------|
| LOW | AUTO_APPROVE | Auto-approve, no human intervention |
| MEDIUM | QUICK_REVIEW | Quick human confirmation |
| HIGH | FULL_REVIEW | Full human review |
| CRITICAL | MANUAL_ONLY | Must be handled manually |

---

## Directory Structure

```
claudedocs/
├── 1-planning/                  # Planning documents
│   ├── architecture/            # Architecture design docs
│   ├── epics/                   # Phase planning
│   │   ├── phase-1/             # Phase 1 Foundation
│   │   ├── phase-2/             # Phase 2 Parallel Execution
│   │   └── ... (phase-3 ~ phase-29)
│   ├── features/                # Feature planning
│   └── roadmap/                 # Product roadmap
│
├── 2-sprints/                   # Sprint documents
│   ├── phase-1/                 # Phase 1 Sprint docs
│   ├── phase-2/                 # Phase 2 Sprint docs
│   └── templates/               # Sprint templates
│
├── 3-progress/                  # Progress tracking
│   ├── daily/                   # Daily progress
│   ├── weekly/                  # Weekly progress reports
│   ├── milestones/              # Milestone records
│   └── templates/               # Progress tracking templates
│
├── 4-changes/                   # Change records
│   ├── bug-fixes/               # Bug fix records (FIX-*)
│   ├── feature-changes/         # Feature change records (CHANGE-*)
│   ├── refactoring/             # Refactoring records (REFACTOR-*)
│   └── templates/               # Change record templates
│
├── 5-status/                    # Status reports
│   ├── phase-reports/           # Phase completion reports
│   ├── testing/                 # Test documents
│   └── quality/                 # Quality reports, Code Review
│
├── 6-ai-assistant/              # AI assistant related
│   ├── analysis/                # Analysis reports
│   ├── prompts/                 # Situation prompts (SITUATION-*)
│   │   ├── SITUATION-1-PROJECT-ONBOARDING.md   # Project onboarding
│   │   ├── SITUATION-2-FEATURE-DEV-PREP.md     # Feature dev preparation
│   │   ├── SITUATION-3-FEATURE-ENHANCEMENT.md  # Feature enhancement
│   │   ├── SITUATION-4-NEW-FEATURE-DEV.md      # New feature development
│   │   ├── SITUATION-5-SAVE-PROGRESS.md        # Save progress
│   │   ├── SITUATION-6-SERVICE-STARTUP.md      # Service startup
│   │   └── SITUATION-7-NEW-ENV-SETUP.md        # New environment setup
│   ├── session-guides/          # Session guides
│   ├── changelogs/              # Change logs
│   └── handoff/                 # Phase handoff docs
│
├── 7-archive/                   # Archived documents
│   ├── phase-1-mvp/             # Phase 1 completed docs
│   └── session-logs/            # Historical session logs
│
├── CLAUDE.md                    # This file - directory index
└── README.md                    # Directory description
```

---

## Project Progress Tracking

### Phase Completion Status (2026-02-09)

| Phase | Name | Sprints | Story Points | Status |
|-------|------|---------|--------------|--------|
| Phase 1 | Foundation | 1-6 | ~90 pts | ✅ Completed |
| Phase 2 | Parallel Execution Engine | 7-12 | ~90 pts | ✅ Completed |
| Phase 3 | Official API Migration | 13-18 | ~105 pts | ✅ Completed |
| Phase 4 | Advanced Adapters | 19-24 | ~105 pts | ✅ Completed |
| Phase 5 | Connector Ecosystem | 25-27 | ~75 pts | ✅ Completed |
| Phase 6 | Enterprise Integration | 28-30 | ~75 pts | ✅ Completed |
| Phase 7 | Multi-turn & Memory | 31-33 | ~90 pts | ✅ Completed |
| Phase 8 | Code Interpreter | 34-36 | ~90 pts | ✅ Completed |
| Phase 9 | MCP Integration | 37-39 | ~90 pts | ✅ Completed |
| Phase 10 | MCP Expansion | 40-44 | ~105 pts | ✅ Completed |
| Phase 11 | Agent-Session Integration | 45-47 | ~90 pts | ✅ Completed |
| Phase 12 | Claude Agent SDK | 48-51 | 165 pts | ✅ Completed |
| Phase 13 | Hybrid Core Architecture | 52-54 | 105 pts | ✅ Completed |
| Phase 14 | Advanced Hybrid Features | 55-57 | 95 pts | ✅ Completed |
| Phase 15 | AG-UI Protocol Integration | 58-60 | 85 pts | ✅ Completed |
| Phase 16 | Unified Agentic Chat | 61-65 | 100 pts | ✅ Completed |
| Phase 17 | DevTools Backend API | 66-68 | 72 pts | ✅ Completed |
| Phase 18 | Session Management | 69-70 | 46 pts | ✅ Completed |
| Phase 19 | Autonomous Agent | 71-72 | 48 pts | ✅ Completed |
| Phase 20 | File Attachment Support | 73-76 | 60 pts | ✅ Completed |
| Phase 21 | Sandbox Security | 77-78 | 48 pts | ✅ Completed |
| Phase 22 | mem0 Core Implementation | 79-80 | 54 pts | ✅ Completed |
| Phase 23 | Performance Optimization | 81-82 | 48 pts | ✅ Completed |
| Phase 24 | Production Deployment | 83-84 | 48 pts | ✅ Completed |
| Phase 25 | Production Expansion | 85-86 | 45 pts | ✅ Completed |
| Phase 26 | DevUI Frontend | 87-89 | 42 pts | ✅ Completed |
| Phase 27 | mem0 Integration Polish | 90 | 13 pts | ✅ Completed |
| Phase 28 | Three-tier Intent Routing | 91-99 | 235 pts | ✅ Completed |
| Phase 29 | Agent Swarm Visualization | 100-106 | ~190 pts | ✅ Completed |
| Phase 30-34 | MAF RC4 Upgrade & Stabilization | 107-120 | ~300 pts | ✅ Completed |
| Phase 35-39 | Claude SDK Enhancement & Hybrid Polish | 121-135 | ~280 pts | ✅ Completed |
| Phase 40-44 | Deep Integration & Optimization | 136-152+ | ~300 pts | ✅ Completed |

**Total**: ~2500+ Story Points across 152+ Sprints (44 Phases)

### Latest Bug Fixes (Sprint 99)

| ID | Name | Status |
|----|------|--------|
| FIX-001 | HITL approval API uses wrong ID type | ✅ Fixed |
| FIX-002 | Expired approval blocks new approvals | ✅ Fixed |
| FIX-003 | Approval card disappears without history | ✅ Fixed |
| FIX-004 | No auto-scroll when approval appears | ✅ Fixed |

### Latest Feature Changes

| ID | Name | Sprint | Status |
|----|------|--------|--------|
| CHANGE-001 | HITL approval changed to inline message card | 99 | ✅ Completed |
| CHANGE-002 | Concurrency architecture improvement | 99+ | ✅ Completed |
| CHANGE-003 | Three-tier router real implementation | 99+ | ✅ Completed |
| CHANGE-004 | Swarm test page real execution mode | 107 | ✅ Completed |

---

## V9 Codebase Analysis Reference

> The V9 analysis (`docs/07-analysis/V9/`) provides the most comprehensive and verified codebase analysis available. It covers Phase 1-44 with 1,028 source files, 327,582 LOC, verified through 130 waves at 9.2/10 quality.

### Quick Access

| Need | V9 Document |
|------|-------------|
| Project overview & navigation | `V9/00-index.md` (master index) |
| Codebase statistics | `V9/00-stats.md` |
| Architecture by layer (L01-L11) | `V9/01-architecture/layer-XX-*.md` |
| Feature completeness & maturity | `V9/03-features/` + `V9/13-mock-real/` |
| Known issues (62 total, 8 CRITICAL) | `V9/05-issues/issue-registry.md` |
| API endpoint catalog (591 endpoints) | `V9/09-api-reference/` |
| Phase change history (30-44) | `V9/07-delta/` |

### Usage Notes

- V9 is baselined at Phase 44 (2026-03-31). Content may diverge as new development proceeds
- Verified numbers (endpoints, enums, ORM columns) are high-confidence; behavioral descriptions should be cross-checked against current source
- Combine V9 with `git log --since="2026-03-31"` to understand changes since the analysis baseline

---

## Documentation Naming Conventions

### Phase/Sprint Planning
```
claudedocs/1-planning/epics/
├── phase-{N}/
│   ├── README.md               # Phase overview
│   ├── architecture.md         # Technical architecture
│   └── stories.md              # User Stories list
```

### Feature Changes (CHANGE-*)
```
claudedocs/4-changes/feature-changes/
└── CHANGE-{NNN}-{description}.md
```

**Standard CHANGE document structure**:
```markdown
# CHANGE-{NNN}: {Change Title}

**Change Date**: YYYY-MM-DD
**Change Type**: Feature Improvement | New Feature | Refactoring
**Status**: ✅ Completed | 🚧 In Progress

## Change Summary
## Change Reason
## Detailed Changes
## Modified Files List
## Test Checklist
```

### Bug Fixes (FIX-*)
```
claudedocs/4-changes/bug-fixes/
└── FIX-{NNN}-{description}.md
```

**Standard FIX document structure**:
```markdown
# FIX-{NNN}: {Bug Description}

**Fix Date**: YYYY-MM-DD
**Severity**: High | Medium | Low
**Status**: ✅ Fixed | 🚧 In Progress

## Problem Description
## Root Cause Analysis
## Fix Solution
## Test Verification
```

### Progress Reports
```
claudedocs/3-progress/
├── daily/{YYYY}-{MM}/{YYYY}-{MM}-{DD}.md       # Daily report
└── weekly/{YYYY}-W{WW}.md                       # Weekly report
```

### Situation Prompts (SITUATION-*)
```
claudedocs/6-ai-assistant/prompts/
└── SITUATION-{N}-{DESCRIPTION}.md
```

---

## Tech Stack

### Core Frameworks
- **Agent Framework**: Microsoft Agent Framework (Preview)
- **AI SDK**: Claude Agent SDK
- **Backend**: Python FastAPI 0.100+
- **Frontend**: React 18 + TypeScript
- **Database**: PostgreSQL 16+
- **State Management**: Zustand (UI) + React Query (Server State)
- **Cache**: Redis 7+

### External Services
- **LLM**: Azure OpenAI GPT-4o + Claude 3.5
- **Authentication**: JWT Token
- **Message Queue**: RabbitMQ / Azure Service Bus

### Protocols & Standards
- **AG-UI Protocol**: Agent-User Interface Protocol (SSE based)
- **MCP**: Model Context Protocol (22 servers integrated)

---

## Important Document Index

### AI Assistant Workflow

| Document Path | Purpose |
|---------------|---------|
| `6-ai-assistant/prompts/SITUATION-1-PROJECT-ONBOARDING.md` | Project onboarding, new session start |
| `6-ai-assistant/prompts/SITUATION-2-FEATURE-DEV-PREP.md` | Feature development prep, task analysis |
| `6-ai-assistant/prompts/SITUATION-3-FEATURE-ENHANCEMENT.md` | Feature enhancement, code optimization |
| `6-ai-assistant/prompts/SITUATION-4-NEW-FEATURE-DEV.md` | New feature development execution |
| `6-ai-assistant/prompts/SITUATION-5-SAVE-PROGRESS.md` | Save progress, session end |
| `6-ai-assistant/prompts/SITUATION-6-SERVICE-STARTUP.md` | Service startup, environment check |
| `6-ai-assistant/prompts/SITUATION-7-NEW-ENV-SETUP.md` | New development environment setup |

### Core Documents

| Document Path | Purpose |
|---------------|---------|
| `CLAUDE.md` (root) | Project master guide |
| `docs/07-analysis/V9/00-index.md` | V9 codebase analysis master index |
| `docs/01-planning/prd/` | Product requirements docs |
| `docs/02-architecture/` | System architecture design |
| `docs/03-implementation/sprint-planning/` | Sprint planning tracking |
| `docs/api/ag-ui-api-reference.md` | AG-UI API reference |

---

## Usage Guide

### Finding Documents

| Need | Path |
|------|------|
| Phase planning | `1-planning/epics/phase-{N}/` |
| Feature changes | `4-changes/feature-changes/CHANGE-{NNN}-*` |
| Bug fixes | `4-changes/bug-fixes/FIX-{NNN}-*` |
| Test reports | `5-status/testing/` |
| Integration-gap analysis (A/B/C, 16 docs) | `5-status/README-integration-gap-abc.md` |
| Weekly reports | `3-progress/weekly/` |
| AI workflows | `6-ai-assistant/prompts/` |

### Creating New Documents

1. **Determine document type and directory**
   - New Phase → `1-planning/epics/phase-{N}/`
   - Feature change → `4-changes/feature-changes/`
   - Bug fix → `4-changes/bug-fixes/`
   - Progress report → `3-progress/`

2. **Use correct naming convention**
   - Phase: `phase-{N}` (1-28+)
   - CHANGE: `CHANGE-{NNN}-{description}.md`
   - FIX: `FIX-{NNN}-{description}.md`

3. **Follow format templates**
   - Reference templates in `4-changes/templates/`
   - Include necessary frontmatter
   - Use consistent section headings

---

## Important Conventions

1. **Naming Consistency**
   - Use UPPERCASE-WITH-DASHES format
   - Use three-digit numbers (001, 002, ...)
   - Use short English kebab-case for descriptions

2. **Language Standard**
   - Document content: English
   - Code snippets: English
   - Date format: YYYY-MM-DD

3. **Status Markers**
   - ✅ Completed
   - 🚧 In Progress
   - ⏸️ Paused/Pending
   - ❌ Cancelled
   - ⚠️ At Risk/Needs Attention

4. **Prohibited Actions**
   - ❌ Creating documents in wrong directories
   - ❌ Using inconsistent naming formats
   - ❌ Missing required frontmatter
   - ❌ Leaving outdated content unupdated

---

## Related Files

### Project-level Documents
- `CLAUDE.md` - Root project master guide
- `docs/03-implementation/sprint-planning/README.md` - Sprint status tracking

### Rule Files
- `.claude/rules/backend-python.md` - Python backend standards
- `.claude/rules/frontend-react.md` - React frontend standards
- `.claude/rules/agent-framework.md` - Agent Framework standards
- `.claude/rules/git-workflow.md` - Git workflow
- `.claude/rules/code-quality.md` - Code quality standards
- `.claude/rules/testing.md` - Testing standards

---

**Maintainer**: AI Assistant + Development Team
**Last Updated**: 2026-03-31
**Document Version**: 3.2.0
