from datetime import datetime, timezone

import pytest

from services.reputation_service.exceptions import OutcomeNotFound, PrizeNotFound
from services.reputation_service.period import week_key

OCCURRED_AT = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
PERIOD = week_key(OCCURRED_AT, week_start_day=6)


def test_record_outcome_creates_a_ledger_row(service):
    outcome = service.record_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=1000)
    assert outcome.counted is True
    assert outcome.passed is True


def test_record_outcome_is_idempotent_per_verdict(service):
    service.record_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=1000)
    replay = service.record_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=False, job_amount_cents=999)

    assert replay.passed is True  # replay ignored, original stands
    assert replay.job_amount_cents == 1000


def test_get_rating_for_unknown_agent_is_zero(service):
    assert service.get_rating("ghost") == 0.0
    assert service.get_verified_count("ghost") == 0


def test_get_rating_reflects_recorded_outcomes(service):
    service.record_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=100)
    service.record_outcome(verdict_id="v2", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=100)

    assert service.get_rating("a1") == 5.0
    assert service.get_verified_count("a1") == 2


def test_get_rating_drops_after_a_string_of_fails(service):
    for i in range(5):
        service.record_outcome(verdict_id=f"v{i}", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=100)
    for i in range(5, 10):
        service.record_outcome(verdict_id=f"v{i}", agent_id="a1", agent_developer_id="d1", passed=False, job_amount_cents=100)

    assert service.get_rating("a1") < 5.0


def test_correct_outcome_excludes_the_original_from_rating(service):
    service.record_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=100)
    assert service.get_rating("a1") == 5.0

    service.correct_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=False, job_amount_cents=100)

    assert service.get_rating("a1") == 0.0  # original pass excluded, corrected fail counted instead
    assert service.get_verified_count("a1") == 1  # still one counted outcome, not two


def test_correct_outcome_preserves_the_original_row_for_audit(service):
    service.record_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=100)
    service.correct_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=False, job_amount_cents=100)

    original = service.get_outcome("v1")
    assert original.counted is False
    assert original.passed is True  # untouched, just excluded

    corrected = service.get_outcome("v1#corrected")
    assert corrected.counted is True
    assert corrected.passed is False
    assert corrected.supersedes_verdict_id == "v1"


def test_correct_outcome_is_idempotent(service):
    service.record_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=100)
    first = service.correct_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=False, job_amount_cents=100)
    second = service.correct_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=False, job_amount_cents=100)

    assert first.verdict_id == second.verdict_id
    assert service.get_verified_count("a1") == 1


def test_get_outcome_for_unknown_verdict_raises(service):
    with pytest.raises(OutcomeNotFound):
        service.get_outcome("nope")


def test_leaderboard_all_time_ranks_by_verified_earnings(service):
    service.record_outcome(verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=500)
    service.record_outcome(verdict_id="v2", agent_id="a2", agent_developer_id="d2", passed=True, job_amount_cents=1000)
    service.record_outcome(verdict_id="v3", agent_id="a3", agent_developer_id="d3", passed=False, job_amount_cents=99_999)

    rows = service.get_leaderboard(period="all_time")

    assert [r.agent_id for r in rows] == ["a2", "a1"]
    assert rows[0].verified_earnings_cents == 1000
    assert rows[0].rank == 1
    assert rows[1].rank == 2


def test_leaderboard_weekly_only_counts_the_current_period(service):
    from datetime import timedelta

    last_week = OCCURRED_AT - timedelta(days=7)

    service.record_outcome(
        verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=500, occurred_at=OCCURRED_AT
    )
    service.record_outcome(
        verdict_id="v2", agent_id="a2", agent_developer_id="d2", passed=True, job_amount_cents=1000, occurred_at=last_week
    )

    weekly = service.get_leaderboard(period="weekly", now=OCCURRED_AT)
    assert [r.agent_id for r in weekly] == ["a1"]

    all_time = service.get_leaderboard(period="all_time")
    assert {r.agent_id for r in all_time} == {"a1", "a2"}


def test_leaderboard_rejects_an_unknown_period(service):
    with pytest.raises(ValueError):
        service.get_leaderboard(period="monthly")


def test_finalize_weekly_prize_picks_the_top_developer(service):
    service.record_outcome(
        verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=1000, occurred_at=OCCURRED_AT
    )
    service.record_outcome(
        verdict_id="v2", agent_id="a2", agent_developer_id="d2", passed=True, job_amount_cents=500, occurred_at=OCCURRED_AT
    )

    prize = service.finalize_weekly_prize(period_key=PERIOD)

    assert prize.winner_agent_developer_id == "d1"
    assert prize.winner_agent_id == "a1"
    assert prize.total_earnings_cents == 1000


def test_finalize_weekly_prize_groups_earnings_by_developer_not_agent(service):
    """Sybil mitigation: a developer running two agents shouldn't be able to split
    earnings across them to dodge behind a single top developer — their combined total
    is what competes, and only one of their agents is credited as the winner."""
    service.record_outcome(
        verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=400, occurred_at=OCCURRED_AT
    )
    service.record_outcome(
        verdict_id="v2", agent_id="a1b", agent_developer_id="d1", passed=True, job_amount_cents=400, occurred_at=OCCURRED_AT
    )
    service.record_outcome(
        verdict_id="v3", agent_id="a2", agent_developer_id="d2", passed=True, job_amount_cents=700, occurred_at=OCCURRED_AT
    )

    prize = service.finalize_weekly_prize(period_key=PERIOD)

    assert prize.winner_agent_developer_id == "d1"  # 400 + 400 = 800 > d2's 700
    assert prize.total_earnings_cents == 800
    assert prize.winner_agent_id in ("a1", "a1b")


def test_finalize_weekly_prize_is_idempotent(service):
    service.record_outcome(
        verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=1000, occurred_at=OCCURRED_AT
    )
    first = service.finalize_weekly_prize(period_key=PERIOD)

    service.record_outcome(
        verdict_id="v2", agent_id="a2", agent_developer_id="d2", passed=True, job_amount_cents=5000, occurred_at=OCCURRED_AT
    )
    second = service.finalize_weekly_prize(period_key=PERIOD)

    assert first.winner_agent_developer_id == second.winner_agent_developer_id == "d1"
    assert second.total_earnings_cents == 1000  # unaffected by the later outcome


def test_finalize_weekly_prize_with_no_outcomes_has_no_winner(service):
    prize = service.finalize_weekly_prize(period_key="2099-01-04")
    assert prize.winner_agent_developer_id is None
    assert prize.total_earnings_cents == 0


def test_mark_prize_paid_requires_a_winner(service):
    prize = service.finalize_weekly_prize(period_key="2099-01-04")
    with pytest.raises(ValueError):
        service.mark_prize_paid(period_key=prize.period_key)


def test_mark_prize_paid_sets_paid_at(service):
    service.record_outcome(
        verdict_id="v1", agent_id="a1", agent_developer_id="d1", passed=True, job_amount_cents=1000, occurred_at=OCCURRED_AT
    )
    service.finalize_weekly_prize(period_key=PERIOD)

    paid = service.mark_prize_paid(period_key=PERIOD)
    assert paid.paid_at is not None


def test_get_weekly_prize_for_unknown_period_raises(service):
    with pytest.raises(PrizeNotFound):
        service.get_weekly_prize("does-not-exist")
