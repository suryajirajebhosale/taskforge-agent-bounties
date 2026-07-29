from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .exceptions import OutcomeNotFound, PrizeNotFound
from .models import AgentOutcome, WeeklyPrize
from .period import week_key
from .rating import decayed_pass_rate, stars


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class LeaderboardRow:
    agent_id: str
    verified_earnings_cents: int
    rank: int


class ReputationService:
    """Computes per-agent reputation and runs the weekly/all-time leaderboard from an
    append-only outcome ledger (`AgentOutcome`), per the Reputation & Leaderboard
    Module PRD. `record_outcome` is the interface the Oracle Verification Service calls
    after every final verdict; `get_rating` is the interface the Agent SDK's matching
    reads (see `services/agent_platform/reputation.py`'s `ReputationReader` protocol)."""

    def __init__(self, session: Session, *, decay_alpha: float, weekly_prize_amount_cents: int, week_start_day: int = 6):
        self.session = session
        self.decay_alpha = decay_alpha
        self.weekly_prize_amount_cents = weekly_prize_amount_cents
        self.week_start_day = week_start_day

    # -- recording outcomes -------------------------------------------------------------

    def record_outcome(
        self,
        *,
        verdict_id: str,
        agent_id: str,
        agent_developer_id: str,
        passed: bool,
        bounty_amount_cents: int,
        occurred_at: datetime | None = None,
    ) -> AgentOutcome:
        """Idempotent per `verdict_id` — replaying the same verdict is a no-op, so a
        retried notification from Oracle can never double-count. To correct an outcome
        that was already recorded (a dispute overturning a verdict), use
        `correct_outcome` instead — this method intentionally will not update an
        existing row."""
        existing = self.session.get(AgentOutcome, verdict_id)
        if existing is not None:
            return existing

        occurred_at = occurred_at or _now()
        outcome = AgentOutcome(
            verdict_id=verdict_id,
            agent_id=agent_id,
            agent_developer_id=agent_developer_id,
            passed=passed,
            bounty_amount_cents=bounty_amount_cents,
            counted=True,
            period_key=week_key(occurred_at, self.week_start_day),
            recorded_at=occurred_at,
        )
        self.session.add(outcome)
        self.session.commit()
        return outcome

    def correct_outcome(
        self,
        *,
        verdict_id: str,
        agent_id: str,
        agent_developer_id: str,
        passed: bool,
        bounty_amount_cents: int,
    ) -> AgentOutcome:
        """Used when a dispute overturns a verdict that was already recorded: excludes
        the original entry from rating/leaderboard computations (`counted=False`,
        preserved for audit — never deleted) and records a new, corrected entry
        carrying the flipped outcome, in the *original* entry's period so a dispute
        resolved after a week rolls over still counts toward the week it happened in.
        Idempotent per corrected-entry id, so replaying a dispute resolution can't
        double-correct."""
        original = self.session.get(AgentOutcome, verdict_id)
        if original is not None and original.counted:
            original.counted = False

        corrected_id = f"{verdict_id}#corrected"
        existing_correction = self.session.get(AgentOutcome, corrected_id)
        if existing_correction is not None:
            self.session.commit()
            return existing_correction

        period_key = original.period_key if original is not None else week_key(_now(), self.week_start_day)
        corrected = AgentOutcome(
            verdict_id=corrected_id,
            agent_id=agent_id,
            agent_developer_id=agent_developer_id,
            passed=passed,
            bounty_amount_cents=bounty_amount_cents,
            counted=True,
            period_key=period_key,
            supersedes_verdict_id=verdict_id,
        )
        self.session.add(corrected)
        self.session.commit()
        return corrected

    # -- rating ---------------------------------------------------------------------------

    def get_rating(self, agent_id: str) -> float:
        """A 0-5 star rating from the agent's counted outcome history, most recent
        outcomes weighted most heavily. 0.0 for an agent with no counted outcomes yet."""
        outcomes = self._counted_outcomes_for_agent(agent_id)
        if not outcomes:
            return 0.0
        return stars(decayed_pass_rate([o.passed for o in outcomes], self.decay_alpha))

    def get_verified_count(self, agent_id: str) -> int:
        return len(self._counted_outcomes_for_agent(agent_id))

    def _counted_outcomes_for_agent(self, agent_id: str) -> list[AgentOutcome]:
        return (
            self.session.query(AgentOutcome)
            .filter_by(agent_id=agent_id, counted=True)
            .order_by(AgentOutcome.recorded_at.asc())
            .all()
        )

    # -- leaderboard --------------------------------------------------------------------

    def get_leaderboard(self, *, period: str, now: datetime | None = None) -> list[LeaderboardRow]:
        """`period` is "weekly" (current week only) or "all_time". Ranked by verified
        earnings (sum of bounty amounts for counted, passed outcomes) descending."""
        query = self.session.query(AgentOutcome).filter_by(counted=True, passed=True)
        if period == "weekly":
            query = query.filter_by(period_key=week_key(now or _now(), self.week_start_day))
        elif period != "all_time":
            raise ValueError(f"unknown leaderboard period: {period!r}")

        totals: dict[str, int] = {}
        for outcome in query.all():
            totals[outcome.agent_id] = totals.get(outcome.agent_id, 0) + outcome.bounty_amount_cents

        ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        return [LeaderboardRow(agent_id=agent_id, verified_earnings_cents=total, rank=i + 1) for i, (agent_id, total) in enumerate(ranked)]

    # -- weekly prize ---------------------------------------------------------------------

    def finalize_weekly_prize(self, *, period_key: str) -> WeeklyPrize:
        """Idempotent per `period_key`. Determines the winning *developer* — earnings
        summed across all of that developer's agents, so operating many agents doesn't
        multiply one person's shot at the prize (the sybil mitigation this module can
        actually enforce; verifying a developer's real-world identity uniqueness is
        Agent Platform/Escrow's job, not this one's). Actually paying the prize out
        (`mark_prize_paid`) requires Escrow to support a payout not tied to a bounty's
        escrow hold, which it doesn't yet — this stays unpaid until that's built."""
        existing = self.session.get(WeeklyPrize, period_key)
        if existing is not None:
            return existing

        outcomes = self.session.query(AgentOutcome).filter_by(counted=True, passed=True, period_key=period_key).all()

        developer_totals: dict[str, int] = {}
        agent_totals: dict[tuple[str, str], int] = {}
        for outcome in outcomes:
            developer_totals[outcome.agent_developer_id] = (
                developer_totals.get(outcome.agent_developer_id, 0) + outcome.bounty_amount_cents
            )
            key = (outcome.agent_developer_id, outcome.agent_id)
            agent_totals[key] = agent_totals.get(key, 0) + outcome.bounty_amount_cents

        winner_developer_id = None
        winner_agent_id = None
        total_earnings = 0
        if developer_totals:
            winner_developer_id, total_earnings = max(developer_totals.items(), key=lambda kv: kv[1])
            candidates = {
                agent_id: total for (dev_id, agent_id), total in agent_totals.items() if dev_id == winner_developer_id
            }
            winner_agent_id = max(candidates.items(), key=lambda kv: kv[1])[0]

        prize = WeeklyPrize(
            period_key=period_key,
            prize_amount_cents=self.weekly_prize_amount_cents,
            winner_agent_developer_id=winner_developer_id,
            winner_agent_id=winner_agent_id,
            total_earnings_cents=total_earnings,
        )
        self.session.add(prize)
        self.session.commit()
        return prize

    def mark_prize_paid(self, *, period_key: str) -> WeeklyPrize:
        prize = self._require_prize(period_key)
        if prize.winner_agent_developer_id is None:
            raise ValueError(f"weekly prize for {period_key} has no winner; nothing to pay")
        prize.paid_at = _now()
        self.session.commit()
        return prize

    def get_weekly_prize(self, period_key: str) -> WeeklyPrize:
        return self._require_prize(period_key)

    def _require_prize(self, period_key: str) -> WeeklyPrize:
        prize = self.session.get(WeeklyPrize, period_key)
        if prize is None:
            raise PrizeNotFound(f"no weekly prize for period {period_key}")
        return prize

    def get_outcome(self, verdict_id: str) -> AgentOutcome:
        outcome = self.session.get(AgentOutcome, verdict_id)
        if outcome is None:
            raise OutcomeNotFound(f"no outcome for verdict {verdict_id}")
        return outcome
