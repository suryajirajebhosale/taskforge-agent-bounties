from services.oracle_service.confidence_router import RoutingConfig, route

CONFIG = RoutingConfig(confidence_threshold=0.8, auto_resolve_amount_cents_ceiling=100_000)


def test_high_confidence_low_amount_auto_resolves():
    decision = route(confidence=0.95, job_amount_cents=1_000, config=CONFIG)
    assert decision.auto_resolve


def test_low_confidence_routes_to_human():
    decision = route(confidence=0.5, job_amount_cents=1_000, config=CONFIG)
    assert not decision.auto_resolve
    assert "confidence" in decision.reason


def test_high_value_bounty_routes_to_human_regardless_of_confidence():
    decision = route(confidence=1.0, job_amount_cents=100_000, config=CONFIG)
    assert not decision.auto_resolve
    assert "amount" in decision.reason


def test_confidence_exactly_at_threshold_auto_resolves():
    decision = route(confidence=0.8, job_amount_cents=1_000, config=CONFIG)
    assert decision.auto_resolve


def test_amount_exactly_at_ceiling_routes_to_human():
    decision = route(confidence=1.0, job_amount_cents=100_000, config=CONFIG)
    assert not decision.auto_resolve


def test_amount_just_below_ceiling_can_auto_resolve():
    decision = route(confidence=1.0, job_amount_cents=99_999, config=CONFIG)
    assert decision.auto_resolve
