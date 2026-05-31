"""
File: backend/src/platform_layer/billing/cost_ledger.py
Purpose: CostLedgerService — record LLM/tool cost ledger entries + monthly aggregate.
Category: Phase 56 SaaS Stage 1 (platform_layer.billing)
Scope: Sprint 56.3 / Day 3 / US-3 + US-4.

Description:
    Source-of-truth for per-event chargeable platform activity.
    Methods:
        - record_llm_call: 1 entry per LoopCompleted (Day 3 simplification —
          input/output token split deferred to Phase 56.x audit cycle per
          AD-Cost-Ledger-Token-Split candidate;LoopCompleted carries only
          combined `total_tokens` per Day 0 D2 finding)
        - record_tool_call: 1 entry per ToolCallExecuted event
        - aggregate(month): SUM total_cost_usd grouped by cost_type+sub_type

    LLM Provider Neutrality preserved — pricing read from
    `config/llm_pricing.yml` via PricingLoader;no openai/anthropic SDK import.

Provider/model attribution (Sprint 57.2):
    record_llm_call accepts `provider`+`model` from the caller; the chat router
    now sources both truthfully from the LoopCompleted accumulator (event.provider
    + event.model, populated by AgentLoop from ChatResponse.model +
    adapter.model_info().provider). Unknown (provider, model) → record at zero
    cost (observable anomaly) per get_llm_pricing → None.

    FIX-022 §6.2 caveat: the deployment/model/pricing identities are currently
    mismatched (.env deployment gpt-5.2 vs config.model_name default gpt-4o vs
    llm_pricing.yml keys {gpt-4o-mini, gpt-5.4}); only gpt-5.4 is priced, so
    gpt-4o / gpt-5.2 calls write $0 rows until the real model + USD pricing is
    aligned in llm_pricing.yml (deferred follow-up).

Key Components:
    - AggregatedSlice / AggregatedUsage: dataclasses
    - CostLedgerService: record_llm_call / record_tool_call / aggregate
    - get_cost_ledger / set_cost_ledger / reset_cost_ledger: hooks

Created: 2026-05-06 (Sprint 56.3 Day 3)
Last Modified: 2026-05-31

Modification History:
    - 2026-05-31: FIX-022 §6.2 — correct stale attribution docstring + pricing caveat
    - 2026-05-06: Initial creation (Sprint 56.3 Day 3 / US-3 + US-4)

Related:
    - sprint-56-3-plan.md §US-3 + §US-4
    - 15-saas-readiness.md §Billing - Cost Ledger 整合
    - infrastructure/db/models/cost_ledger.py (CostLedger ORM)
    - platform_layer/billing/pricing.py (PricingLoader)
    - .claude/rules/multi-tenant-data.md (3 鐵律)
    - .claude/rules/llm-provider-neutrality.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select

from infrastructure.db.models.cost_ledger import CostLedger
from platform_layer.billing.pricing import PricingLoader

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class AggregatedSlice:
    """One cost_type+sub_type aggregate slice."""

    quantity: Decimal
    total_cost_usd: Decimal
    entry_count: int


@dataclass(frozen=True)
class AggregatedUsage:
    """Per-tenant per-month cost aggregate.

    `by_type` maps cost_type → sub_type → AggregatedSlice. e.g.:
        by_type["llm"]["azure_openai_gpt-5.4_total"] → AggregatedSlice(...)
        by_type["tool"]["salesforce_query"] → AggregatedSlice(...)
    """

    tenant_id: UUID
    month: str
    total_cost_usd: Decimal
    by_type: dict[str, dict[str, AggregatedSlice]] = field(default_factory=dict)


class CostLedgerService:
    """Append-only Cost Ledger writer + monthly aggregate reader."""

    def __init__(
        self,
        db: "AsyncSession",
        pricing_loader: PricingLoader,
    ) -> None:
        self._db = db
        self._pricing = pricing_loader

    async def record_llm_call(
        self,
        *,
        tenant_id: UUID,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
        session_id: UUID | None = None,
    ) -> list[CostLedger]:
        """Record two ledger entries for an LLM call (input + output split).

        Sprint 57.2 closes AD-Cost-Ledger-Token-Split + AD-Cost-Ledger-
        Provider-Attribution. Replaces 56.3 D2 single-entry combined-token
        simplification (avg pricing → real input/output split pricing).
        Provider/model now sourced truthfully from LoopCompleted accumulator
        (chat router observer reads event.provider + event.model populated by
        AgentLoop from ChatResponse.model + adapter.model_info().provider).

        Pricing:
          - billable_input = max(input_tokens - cached_input_tokens, 0)
            × pricing.input_per_million / 1M
          - cached_input = cached_input_tokens × pricing.cached_input_per_million / 1M
          - output = output_tokens × pricing.output_per_million / 1M

        Returns list of 2 CostLedger entries (`{provider}_{model}_input` +
        `{provider}_{model}_output` sub_types) for monthly aggregate
        granularity. Both entries share session_id for per-session
        reconciliation.
        """
        pricing = self._pricing.get_llm_pricing(provider, model)
        if pricing is None:
            # Unknown provider/model — record at zero cost; surfaces as
            # observable anomaly in monthly report (sub_type still recorded).
            input_unit_cost = Decimal("0")
            output_unit_cost = Decimal("0")
            input_total_cost = Decimal("0")
            output_total_cost = Decimal("0")
        else:
            input_per_m = Decimal(str(pricing.input_per_million))
            output_per_m = Decimal(str(pricing.output_per_million))
            cached_per_m = Decimal(str(pricing.cached_input_per_million))
            input_unit_cost = input_per_m / Decimal("1000000")
            output_unit_cost = output_per_m / Decimal("1000000")

            # Input portion: cached portion at cached rate, remainder at input rate.
            billable_input = max(input_tokens - cached_input_tokens, 0)
            billable_input_cost = Decimal(billable_input) * input_unit_cost
            cached_cost = Decimal(cached_input_tokens) * cached_per_m / Decimal("1000000")
            input_total_cost = billable_input_cost + cached_cost

            # Output portion: full at output rate.
            output_total_cost = Decimal(output_tokens) * output_unit_cost

        input_entry = CostLedger(
            tenant_id=tenant_id,
            cost_type="llm",
            sub_type=f"{provider}_{model}_input",
            quantity=Decimal(input_tokens),
            unit="tokens",
            unit_cost_usd=input_unit_cost,
            total_cost_usd=input_total_cost,
            session_id=session_id,
        )
        output_entry = CostLedger(
            tenant_id=tenant_id,
            cost_type="llm",
            sub_type=f"{provider}_{model}_output",
            quantity=Decimal(output_tokens),
            unit="tokens",
            unit_cost_usd=output_unit_cost,
            total_cost_usd=output_total_cost,
            session_id=session_id,
        )
        self._db.add(input_entry)
        self._db.add(output_entry)
        await self._db.flush()
        return [input_entry, output_entry]

    async def record_tool_call(
        self,
        *,
        tenant_id: UUID,
        tool_name: str,
        session_id: UUID | None = None,
    ) -> CostLedger:
        """Record one ledger entry for a tool execute."""
        tool_pricing = self._pricing.get_tool_pricing(tool_name)
        unit_cost = Decimal(str(tool_pricing.per_call))
        entry = CostLedger(
            tenant_id=tenant_id,
            cost_type="tool",
            sub_type=tool_name,
            quantity=Decimal("1"),
            unit="call",
            unit_cost_usd=unit_cost,
            total_cost_usd=unit_cost,
            session_id=session_id,
        )
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def aggregate(
        self,
        *,
        tenant_id: UUID,
        month: str,
    ) -> AggregatedUsage:
        """SUM total_cost_usd grouped by (cost_type, sub_type) for the month.

        `month` is 'YYYY-MM'. Filters `recorded_at` between [month-01 UTC,
        next-month-01 UTC). All CostLedger queries scoped by tenant_id per
        multi-tenant 鐵律 2.
        """
        year, mo = month.split("-")
        start = datetime(int(year), int(mo), 1, tzinfo=timezone.utc)
        if int(mo) == 12:
            end = datetime(int(year) + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(int(year), int(mo) + 1, 1, tzinfo=timezone.utc)

        stmt = (
            select(
                CostLedger.cost_type,
                CostLedger.sub_type,
                func.sum(CostLedger.quantity).label("quantity_sum"),
                func.sum(CostLedger.total_cost_usd).label("cost_sum"),
                func.count(CostLedger.id).label("entry_count"),
            )
            .where(CostLedger.tenant_id == tenant_id)
            .where(CostLedger.recorded_at >= start)
            .where(CostLedger.recorded_at < end)
            .group_by(CostLedger.cost_type, CostLedger.sub_type)
        )
        result = await self._db.execute(stmt)
        rows = result.all()

        by_type: dict[str, dict[str, AggregatedSlice]] = {}
        total = Decimal("0")
        for row in rows:
            cost_type = str(row.cost_type)
            sub_type = str(row.sub_type)
            slice_quantity = Decimal(row.quantity_sum or 0)
            slice_cost = Decimal(row.cost_sum or 0)
            entry_count = int(row.entry_count or 0)
            by_type.setdefault(cost_type, {})[sub_type] = AggregatedSlice(
                quantity=slice_quantity,
                total_cost_usd=slice_cost,
                entry_count=entry_count,
            )
            total += slice_cost
        return AggregatedUsage(
            tenant_id=tenant_id,
            month=month,
            total_cost_usd=total,
            by_type=by_type,
        )


# Module-level singleton — reset hook per testing.md §Module-level Singleton Reset Pattern.
_service: CostLedgerService | None = None


def get_cost_ledger() -> CostLedgerService:
    """FastAPI Depends accessor (strict — raises if uninitialised)."""
    if _service is None:
        raise RuntimeError(
            "CostLedgerService not initialised; call set_cost_ledger() at "
            "app startup or in test fixture"
        )
    return _service


def maybe_get_cost_ledger() -> CostLedgerService | None:
    """FastAPI Depends accessor (lenient — returns None if uninitialised)."""
    return _service


def set_cost_ledger(service: CostLedgerService | None) -> None:
    """Install singleton (app startup or tests fixture)."""
    global _service
    _service = service


def reset_cost_ledger() -> None:
    """Test isolation hook (per testing.md §Module-level Singleton Reset Pattern)."""
    global _service
    _service = None


__all__ = [
    "AggregatedSlice",
    "AggregatedUsage",
    "CostLedgerService",
    "get_cost_ledger",
    "maybe_get_cost_ledger",
    "reset_cost_ledger",
    "set_cost_ledger",
]
