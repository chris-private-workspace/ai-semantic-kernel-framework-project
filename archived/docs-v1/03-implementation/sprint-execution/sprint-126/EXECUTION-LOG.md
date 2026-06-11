# Sprint 126 Execution Log

## Sprint Overview

| Attribute | Value |
|-----------|-------|
| **Sprint** | 126 |
| **Phase** | 34 — Feature Expansion |
| **Story Points** | 30 |
| **Start Date** | 2026-02-25 |
| **End Date** | 2026-02-25 |
| **Status** | Completed |

## Goals

1. **Story 126-1**: IT Incident Handler + PatternMatcher rules (ServiceNow INC Webhook)
2. **Story 126-2**: IncidentAnalyzer + ActionRecommender (LLM-assisted root cause analysis)
3. **Story 126-3**: IncidentExecutor + HITL approval + ServiceNow writeback
4. **Story 126-4**: Unit tests + E2E tests (124 tests total)

## Story 126-1: Incident Handler + Pattern Rules

### New Files

- `src/integrations/orchestration/input/incident_handler.py` — IncidentHandler (InputProcessorProtocol)
- `src/integrations/orchestration/input/incident_rules.yaml` — 30+ IT incident pattern rules

### Key Classes

| Class | Responsibility |
|-------|---------------|
| ServiceNowINCEvent | Pydantic model for INC webhook payload |
| IncidentSubCategory | NETWORK, SERVER, APPLICATION, DATABASE, SECURITY, STORAGE, PERFORMANCE, AUTHENTICATION, OTHER |
| IncidentHandler | process(), can_handle(), get_source_type() — maps INC to RoutingRequest |

### Design Decisions

- Reuses existing WebhookAuthConfig and ServiceNowWebhookReceiver for auth
- Priority mapping: "1"->CRITICAL, "2"->HIGH, "3"->MEDIUM, "4"->LOW
- Classification uses category field + regex fallback on short_description
- Supports Chinese descriptions (伺服器當機, 資料庫, 防火牆, etc.)

## Story 126-2: IncidentAnalyzer + ActionRecommender

### New Files

- `src/integrations/incident/__init__.py` — Module exports
- `src/integrations/incident/types.py` — Core data types (~250 LOC)
- `src/integrations/incident/prompts.py` — LLM prompt templates
- `src/integrations/incident/analyzer.py` — IncidentAnalyzer (~350 LOC)
- `src/integrations/incident/recommender.py` — ActionRecommender (~300 LOC)

### Key Classes

| Class | Responsibility |
|-------|---------------|
| IncidentContext | Incident context dataclass (number, severity, category, etc.) |
| RemediationAction | Action with type, confidence, risk level, MCP tool mapping |
| IncidentAnalysis | Analysis result with root cause, correlations, recommendations |
| IncidentAnalyzer | Correlation + RootCause + LLM enhanced analysis |
| ActionRecommender | Rule-based + LLM action suggestion, ranked by confidence/risk |

### Design Decisions

- LLM enhancement is optional (graceful fallback to rule-based)
- Confidence merging: RCA weight 0.4 + LLM weight 0.6
- 8 category templates with per-severity confidence adjustment (P1 +0.10, P4 -0.05)
- Deduplication of actions by title (case-insensitive)
- MCP param substitution uses {cmdb_ci}, {caller_id} placeholders

## Story 126-3: IncidentExecutor

### New Files

- `src/integrations/incident/executor.py` — IncidentExecutor (~400 LOC)

### Key Classes

| Class | Responsibility |
|-------|---------------|
| IncidentExecutor | Auto-execute LOW risk, HITL for HIGH+, ServiceNow writeback |
| ExecutionResult | Execution outcome with status, output, approval_request_id |

### Auto-Remediation Action Library

| Action | Risk | Auto/HITL |
|--------|------|-----------|
| Restart application service | AUTO | Auto |
| Clear disk space | AUTO | Auto |
| AD account unlock | AUTO | Auto |
| Scale VM resources | MEDIUM | HITL (configurable) |
| Network ACL change | HIGH | HITL |
| Firewall rule change | CRITICAL | HITL |

### Design Decisions

- Simulation mode: operates without external executors (shell/LDAP)
- First successful auto-execute skips remaining actions
- ServiceNow writeback is non-blocking (failure doesn't break execution)
- MEDIUM risk configurable via `auto_execute_medium` flag

## Story 126-4: Tests

### Test Results Summary

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_types.py` | 31 | PASSED |
| `test_analyzer.py` | 17 | PASSED |
| `test_recommender.py` | 17 | PASSED |
| `test_executor.py` | 19 | PASSED |
| `test_incident_handler.py` | 34 | PASSED |
| `test_incident_pipeline.py` | 6 | PASSED |
| **Total** | **124** | **ALL PASSED** |

### E2E Scenarios Covered

1. P4 Disk Space → Auto-Cleanup → Resolved
2. P1 Critical Security → HITL Approval → Awaiting
3. Auth Lockout → AD Unlock → Resolved
4. LLM Unavailable → Rule-Based Fallback
5. Multiple Concurrent Incidents
6. ServiceNow Writeback Failure → Graceful Degradation

## Modified Files

- `src/integrations/orchestration/input/__init__.py` — Add IncidentHandler exports
- `src/api/v1/orchestration/webhook_routes.py` — Add INC webhook endpoint
- `src/api/v1/orchestration/schemas.py` — Add incident webhook schemas

## File Inventory

### New Files (17 files)

| # | Path | LOC | Story |
|---|------|-----|-------|
| 1 | `src/integrations/incident/__init__.py` | ~50 | 126-2 |
| 2 | `src/integrations/incident/types.py` | ~250 | 126-2 |
| 3 | `src/integrations/incident/prompts.py` | ~150 | 126-2 |
| 4 | `src/integrations/incident/analyzer.py` | ~350 | 126-2 |
| 5 | `src/integrations/incident/recommender.py` | ~300 | 126-2 |
| 6 | `src/integrations/incident/executor.py` | ~400 | 126-3 |
| 7 | `src/integrations/orchestration/input/incident_handler.py` | ~350 | 126-1 |
| 8 | `src/integrations/orchestration/input/incident_rules.yaml` | ~250 | 126-1 |
| 9 | `tests/unit/integrations/incident/__init__.py` | ~1 | 126-4 |
| 10 | `tests/unit/integrations/incident/test_types.py` | ~400 | 126-4 |
| 11 | `tests/unit/integrations/incident/test_analyzer.py` | ~370 | 126-4 |
| 12 | `tests/unit/integrations/incident/test_recommender.py` | ~330 | 126-4 |
| 13 | `tests/unit/integrations/incident/test_executor.py` | ~550 | 126-4 |
| 14 | `tests/unit/integrations/orchestration/test_incident_handler.py` | ~340 | 126-4 |
| 15 | `tests/e2e/test_incident_pipeline.py` | ~490 | 126-4 |
| 16 | `docs/.../sprint-126/EXECUTION-LOG.md` | — | docs |
| 17 | `docs/.../sprint-126/sprint-126-status.md` | — | docs |

## Notes

- All rootcause types use actual class names: `RootCauseHypothesis` (not `Hypothesis`), `AnalysisStatus` (not `RCAStatus`)
- Correlation types: `TIME`, `DEPENDENCY`, `SEMANTIC`, `CAUSAL` (not TEMPORAL/TOPOLOGICAL)
- `Recommendation` requires `estimated_effort` field
- `RootCauseAnalysis` requires `event_id`, `started_at`, `completed_at` fields
- `HistoricalCase` requires `description`, `occurred_at`, `resolved_at` fields
