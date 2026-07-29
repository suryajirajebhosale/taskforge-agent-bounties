from services.reputation_service.rating import decayed_pass_rate, stars


def test_empty_outcomes_returns_zero():
    assert decayed_pass_rate([], decay_alpha=0.15) == 0.0


def test_all_passes_stays_at_one():
    assert decayed_pass_rate([True, True, True], decay_alpha=0.15) == 1.0


def test_all_fails_stays_at_zero():
    assert decayed_pass_rate([False, False, False], decay_alpha=0.15) == 0.0


def test_recent_outcomes_are_weighted_more_heavily():
    mostly_pass_then_fail = decayed_pass_rate([True] * 10 + [False], decay_alpha=0.3)
    mostly_fail_then_pass = decayed_pass_rate([False] * 10 + [True], decay_alpha=0.3)
    assert mostly_pass_then_fail > mostly_fail_then_pass


def test_first_outcome_initializes_the_average_directly():
    assert decayed_pass_rate([False], decay_alpha=0.15) == 0.0
    assert decayed_pass_rate([True], decay_alpha=0.15) == 1.0


def test_stars_maps_full_pass_rate_to_five_stars():
    assert stars(1.0) == 5.0


def test_stars_maps_zero_pass_rate_to_zero_stars():
    assert stars(0.0) == 0.0


def test_stars_rounds_to_two_decimals():
    assert stars(0.821234) == 4.11
