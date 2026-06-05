"""Category 8: Error Handling. See README.md."""

from agent_harness.error_handling._abc import (
    CircuitBreaker,
    ErrorClass,
    ErrorPolicy,
    ErrorTerminator,
)
from agent_harness.error_handling._redis_store import RedisBudgetStore
from agent_harness.error_handling.budget import (
    BudgetStore,
    InMemoryBudgetStore,
    TenantErrorBudget,
)
from agent_harness.error_handling.circuit_breaker import (
    CircuitOpenError,
    CircuitState,
    DefaultCircuitBreaker,
)
from agent_harness.error_handling.policy import DefaultErrorPolicy
from agent_harness.error_handling.retry import (
    RetryConfig,
    RetryPolicyMatrix,
    compute_backoff,
)
from agent_harness.error_handling.terminator import (
    DefaultErrorTerminator,
    TerminationDecision,
    TerminationReason,
)

__all__ = [
    "ErrorPolicy",
    "DefaultErrorPolicy",
    "CircuitBreaker",
    "DefaultCircuitBreaker",
    "CircuitOpenError",
    "CircuitState",
    "ErrorTerminator",
    "ErrorClass",
    "RetryConfig",
    "RetryPolicyMatrix",
    "compute_backoff",
    "BudgetStore",
    "InMemoryBudgetStore",
    "RedisBudgetStore",
    "TenantErrorBudget",
    "DefaultErrorTerminator",
    "TerminationDecision",
    "TerminationReason",
]
