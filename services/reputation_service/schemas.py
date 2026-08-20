from pydantic import BaseModel

from .models import AgentOutcome, WeeklyPrize
from .service import LeaderboardRow


class RecordOutcomeRequest(BaseModel):
    verdict_id: str
    agent_id: str
    agent_developer_id: str
    passed: bool
    job_amount_cents: int


class CorrectOutcomeRequest(BaseModel):
    agent_id: str
    agent_developer_id: str
    passed: bool
    job_amount_cents: int


class OutcomeOut(BaseModel):
    verdict_id: str
    agent_id: str
    agent_developer_id: str
    passed: bool
    job_amount_cents: int
    counted: bool
    period_key: str
    supersedes_verdict_id: str | None

    @classmethod
    def from_model(cls, outcome: AgentOutcome) -> "OutcomeOut":
        return cls(
            verdict_id=outcome.verdict_id,
            agent_id=outcome.agent_id,
            agent_developer_id=outcome.agent_developer_id,
            passed=outcome.passed,
            job_amount_cents=outcome.job_amount_cents,
            counted=outcome.counted,
            period_key=outcome.period_key,
            supersedes_verdict_id=outcome.supersedes_verdict_id,
        )


class RatingOut(BaseModel):
    agent_id: str
    rating: float
    verified_count: int


class LeaderboardRowOut(BaseModel):
    agent_id: str
    verified_earnings_cents: int
    rank: int

    @classmethod
    def from_row(cls, row: LeaderboardRow) -> "LeaderboardRowOut":
        return cls(agent_id=row.agent_id, verified_earnings_cents=row.verified_earnings_cents, rank=row.rank)


class FinalizeWeeklyPrizeRequest(BaseModel):
    period_key: str


class WeeklyPrizeOut(BaseModel):
    period_key: str
    prize_amount_cents: int
    winner_agent_developer_id: str | None
    winner_agent_id: str | None
    total_earnings_cents: int
    paid_at: str | None

    @classmethod
    def from_model(cls, prize: WeeklyPrize) -> "WeeklyPrizeOut":
        return cls(
            period_key=prize.period_key,
            prize_amount_cents=prize.prize_amount_cents,
            winner_agent_developer_id=prize.winner_agent_developer_id,
            winner_agent_id=prize.winner_agent_id,
            total_earnings_cents=prize.total_earnings_cents,
            paid_at=prize.paid_at.isoformat() if prize.paid_at else None,
        )
