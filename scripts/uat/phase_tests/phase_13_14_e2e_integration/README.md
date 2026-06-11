# Phase 13+14 E2E Integration Tests

End-to-end integration testing for the Hybrid MAF + Claude SDK Architecture.

> ⚠️ **IMPORTANT: LIVE API REQUIRED**
>
> These tests require a **LIVE** backend API with real LLM (Azure OpenAI / Claude) configured.
> **NO simulation mode is available.** Tests will fail immediately if the API is unavailable
> or LLM is not properly configured.
>
> Before running tests, ensure:
> 1. Backend server is running at `http://localhost:8000`
> 2. Azure OpenAI or Claude API credentials are configured
> 3. All Hybrid API endpoints (Phase 13+14) are implemented

## Overview

This test suite validates the complete integration between:

- **Phase 13**: Hybrid MAF + Claude SDK Core (105 pts)
  - Sprint 52: Intent Router & Context Bridge (35 pts)
  - Sprint 53: Unified Tool Executor (35 pts)
  - Sprint 54: HybridOrchestrator Refactor (35 pts)

- **Phase 14**: HITL & Approval (100 pts)
  - Sprint 55: Risk Assessment Engine (35 pts)
  - Sprint 56: Mode Switcher (35 pts)
  - Sprint 57: Unified Checkpoint (30 pts)

**Total**: 205 Story Points

---

## Architecture Flow

```
User Request
    |
IntentRouter (Phase 13)
    |
+---+---+
|       |
Workflow  Chat
|       |
HybridOrchestrator (Phase 13)
    |
RiskAssessment (Phase 14)
    |
+---+---+---+
|   |       |
Low Med  High/Critical
|   |       |
Auto Log  HITL Approval
    |
ContextBridge (Phase 13) <---> ModeSwitcher (Phase 14)
    |
UnifiedCheckpoint (Phase 14)
    |
Tool Execution (Phase 13)
    |
Response
```

---

## Test Scenarios

### Scenario 1: Intent to Risk Assessment

**File**: `scenario_intent_to_risk.py`

Tests the flow from intent detection to risk-based HITL decisions.

| # | Test Case | Description |
|---|-----------|-------------|
| 1 | Intent detection triggers risk assessment | Workflow intent auto-triggers risk evaluation |
| 2 | High-risk intent requires approval | Delete/modify operations require HITL |
| 3 | Low-risk intent auto-proceeds | Read operations execute without approval |
| 4 | Risk escalation to human | Critical actions route to human reviewer |

**Key Components**:
- `IntentRouter`: Detects workflow vs chat intent
- `RiskAssessmentEngine`: Evaluates action risk level
- `ApprovalManager`: Handles HITL approval requests

---

### Scenario 2: Mode Switch with Context Preservation

**File**: `scenario_mode_switch_context.py`

Tests mode transitions with state synchronization.

| # | Test Case | Description |
|---|-----------|-------------|
| 1 | Workflow to Chat preserves context | Context maintained on mode switch |
| 2 | Chat to Workflow maintains state | Chat history preserved during escalation |
| 3 | Context Bridge bidirectional sync | MAF <-> Claude SDK state sync |
| 4 | Graceful degradation on sync failure | Rollback available on failure |

**Key Components**:
- `ModeSwitcher`: Handles mode transitions
- `ContextBridge`: Bidirectional state synchronization
- `CheckpointStorage`: State persistence for rollback

---

### Scenario 3: Checkpoint and Recovery

**File**: `scenario_checkpoint_recovery.py`

Tests cross-framework state persistence and recovery.

| # | Test Case | Description |
|---|-----------|-------------|
| 1 | Checkpoint spans both frameworks | Single checkpoint captures MAF + Claude state |
| 2 | Recovery restores correct mode | Mode restored along with state |
| 3 | Partial state recovery | Selective restoration without side effects |
| 4 | Checkpoint versioning across switches | Version tracking across mode changes |

**Key Components**:
- `UnifiedCheckpoint`: Cross-framework checkpoint model
- `CheckpointStorage`: Multi-backend storage (Redis + PostgreSQL)
- `RecoveryEngine`: State restoration and validation

---

### Scenario 4: Full Hybrid Flow

**File**: `scenario_full_hybrid_flow.py`

Comprehensive end-to-end integration tests.

| # | Test Case | Description |
|---|-----------|-------------|
| 1 | Complete Workflow -> Chat -> Workflow cycle | Full mode transition cycle |
| 2 | Multi-step approval chain | Varying risk levels with proper handling |
| 3 | Error recovery with checkpoint | Recovery from failure using checkpoint |

**Key Components**:
- All Phase 13+14 components working together
- Real-world scenario simulation
- Error handling and recovery paths

---

## Test Execution

### Run All E2E Tests

```bash
cd scripts/uat/phase_tests
python -m phase_13_14_e2e_integration.e2e_integration_test
```

### Run Specific Scenario

```python
import asyncio
from phase_13_14_e2e_integration.e2e_integration_test import E2ETestClient
from phase_13_14_e2e_integration import scenario_intent_to_risk

async def run():
    client = E2ETestClient()
    await client.connect()
    result = await scenario_intent_to_risk.run_scenario(client)
    print(f"Result: {result.passed}/{result.passed + result.failed}")
    await client.close()

asyncio.run(run())
```

---

## Prerequisites

### Required Configuration

These tests use **LIVE API only** - no simulation mode is available.

1. **Backend Server**: Must be running at `http://localhost:8000`
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **LLM Configuration** (one of the following):
   - **Azure OpenAI**: Set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT_NAME`
   - **Claude API**: Set `ANTHROPIC_API_KEY`

3. **Dependencies**: PostgreSQL, Redis must be running
   ```bash
   docker-compose up -d
   ```

### Health Check

Before running tests, verify the backend is ready:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/hybrid/health  # Phase 13+14 specific
```

### Error Handling

If tests fail to start, you will see one of these errors:
- `APIUnavailableError`: Backend server is not running
- `LLMConfigurationError`: LLM (Azure OpenAI / Claude) is not configured

---

## File Structure

```
phase_13_14_e2e_integration/
├── __init__.py                    # Module exports
├── README.md                      # This file
├── e2e_integration_test.py        # Main test runner and client
├── scenario_intent_to_risk.py     # Scenario 1: Intent -> Risk flow
├── scenario_mode_switch_context.py # Scenario 2: Mode switching
├── scenario_checkpoint_recovery.py # Scenario 3: Checkpoint/recovery
└── scenario_full_hybrid_flow.py   # Scenario 4: Complete E2E flow
```

---

## Expected Results

| Scenario | Tests | Expected |
|----------|-------|----------|
| Scenario 1: Intent to Risk | 4 | All PASS |
| Scenario 2: Mode Switch | 4 | All PASS |
| Scenario 3: Checkpoint | 4 | All PASS |
| Scenario 4: Full Flow | 3 | All PASS |
| **Total** | **15** | **15 PASS** |

---

## Dependencies

- Python 3.12+
- `httpx` (async HTTP client)
- `base.py` (from parent directory)

---

## Related Documentation

- [Phase 13 Sprint Planning](../../../../archived/docs-v1/03-implementation/sprint-planning/phase-13/README.md)
- [Phase 14 Sprint Planning](../../../../archived/docs-v1/03-implementation/sprint-planning/phase-14/README.md)
- [Phase 13 UAT Results](../phase_13_hybrid_maf_claude_integration/)
- [Phase 14 UAT Results](../phase_14_hitl_approval/)

---

## Notes

1. **LIVE API Only**: Tests require a running backend with real LLM configured. No simulation mode is available.

2. **State Preservation**: E2E tests verify state is preserved across all mode transitions and checkpoints.

3. **Error Recovery**: Full error recovery paths are tested, including checkpoint restore.

4. **HITL Integration**: Human-in-the-loop approval flows use real API endpoints for approval decisions.

---

**Created**: 2026-01-05
**Phase**: 13+14 Integration
**Total Story Points**: 205 (105 + 100)
