def decayed_pass_rate(outcomes: list[bool], decay_alpha: float) -> float:
    """Exponentially-weighted pass rate: each subsequent outcome shifts the running
    average by `decay_alpha` toward that outcome's value (1.0 pass / 0.0 fail), so
    recent outcomes count for more than old ones. `outcomes` must be in chronological
    order (oldest first). The first outcome initializes the average directly rather
    than blending against an arbitrary starting point. Returns 0.0 for an empty list."""
    if not outcomes:
        return 0.0
    average = 1.0 if outcomes[0] else 0.0
    for passed in outcomes[1:]:
        value = 1.0 if passed else 0.0
        average = decay_alpha * value + (1 - decay_alpha) * average
    return average


def stars(decayed_rate: float) -> float:
    """Maps a 0.0-1.0 decayed pass rate onto the 0-5 star scale observed live on
    trybounty.ai (e.g. a rolling ~82% pass rate reads as 4.1 stars)."""
    return round(decayed_rate * 5.0, 2)
