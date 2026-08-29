from agent_audit_record import Cost, CostComponent, CostUnit


def test_default_cost_has_only_wasted_false() -> None:
    assert Cost().to_attributes() == {"agent_audit.cost.wasted": False}


def test_full_cost_renders_all_attributes() -> None:
    cost = Cost(
        amount=0.5,
        currency="usd",
        unit=CostUnit.USD,
        component=CostComponent.INFERENCE,
        wasted=True,
    )
    assert cost.to_attributes() == {
        "agent_audit.cost.wasted": True,
        "agent_audit.cost.amount": 0.5,
        "agent_audit.cost.currency": "usd",
        "agent_audit.cost.unit": "usd",
        "agent_audit.cost.component": "inference",
    }


def test_non_monetary_unit_with_no_currency() -> None:
    cost = Cost(amount=3, unit=CostUnit.API_CALLS)
    attrs = cost.to_attributes()
    assert attrs["agent_audit.cost.unit"] == "api_calls"
    assert "agent_audit.cost.currency" not in attrs
