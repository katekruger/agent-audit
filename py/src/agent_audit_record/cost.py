"""Cost accounting, including the wasted-proposal case — spec §6.7."""

from __future__ import annotations

from dataclasses import dataclass

from opentelemetry.util.types import AnyValue

from agent_audit_record.phases import CostComponent, CostUnit

_ATTR_AMOUNT = "agent_audit.cost.amount"
_ATTR_CURRENCY = "agent_audit.cost.currency"
_ATTR_UNIT = "agent_audit.cost.unit"
_ATTR_COMPONENT = "agent_audit.cost.component"
_ATTR_WASTED = "agent_audit.cost.wasted"


@dataclass(frozen=True, slots=True)
class Cost:
    """`agent_audit.cost.*`. `wasted` is required True on a `decided` Record
    whose decision is deny/cancel/timeout — see `Decision.forbids_execution`
    and spec §6.7.
    """

    amount: float | None = None
    currency: str | None = None
    unit: CostUnit | None = None
    component: CostComponent | None = None
    wasted: bool = False

    def to_attributes(self) -> dict[str, AnyValue]:
        """Render as flat `agent_audit.cost.*` attribute keys (spec §6)."""
        attrs: dict[str, AnyValue] = {_ATTR_WASTED: self.wasted}
        if self.amount is not None:
            attrs[_ATTR_AMOUNT] = self.amount
        if self.currency is not None:
            attrs[_ATTR_CURRENCY] = self.currency
        if self.unit is not None:
            attrs[_ATTR_UNIT] = self.unit.value
        if self.component is not None:
            attrs[_ATTR_COMPONENT] = self.component.value
        return attrs
