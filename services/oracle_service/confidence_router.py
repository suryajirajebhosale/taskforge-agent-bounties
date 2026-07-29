from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingConfig:
    confidence_threshold: float
    auto_resolve_amount_cents_ceiling: int
    """Bounties at or above this amount always route to human review, regardless of confidence."""


@dataclass(frozen=True)
class RoutingDecision:
    auto_resolve: bool
    reason: str


def route(*, confidence: float, bounty_amount_cents: int, config: RoutingConfig) -> RoutingDecision:
    """"Trust but verify": full automation is the end state, not the safe default —
    high-value bounties and low-confidence verdicts both get a human in the loop
    instead of auto-resolving, per the Oracle Verification Service PRD."""
    if bounty_amount_cents >= config.auto_resolve_amount_cents_ceiling:
        return RoutingDecision(auto_resolve=False, reason="bounty amount at or above the human-review ceiling")
    if confidence < config.confidence_threshold:
        return RoutingDecision(auto_resolve=False, reason="confidence below the auto-resolve threshold")
    return RoutingDecision(auto_resolve=True, reason="confidence and amount both within auto-resolve bounds")
