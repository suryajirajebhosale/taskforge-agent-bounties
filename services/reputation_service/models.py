from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AgentOutcome(Base):
    """One append-only ledger row per graded submission, keyed by the Oracle verdict
    that produced it. Never deleted — a dispute that overturns a verdict marks the
    original row `counted=False` and adds a new, corrected row (see
    `service.correct_outcome`) rather than mutating history, preserving a full audit
    trail the same way the Escrow Ledger Service's `LedgerEntry` does.

    Rating and leaderboard figures are computed on read from this table rather than
    maintained as separately-updated aggregate columns — simpler, and immune to the
    whole class of drift bugs that dual bookkeeping invites. This can be cached or
    materialized later if read volume ever demands it."""

    __tablename__ = "agent_outcomes"

    verdict_id: Mapped[str] = mapped_column(String, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_developer_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    job_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    counted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    period_key: Mapped[str] = mapped_column(String, index=True, nullable=False)
    supersedes_verdict_id: Mapped[str | None] = mapped_column(String, nullable=True)
    """Set on a corrected entry created by `correct_outcome`, pointing back at the
    original (now `counted=False`) entry it replaces, for audit traceability."""
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class WeeklyPrize(Base):
    """One row per finalized weekly leaderboard period. The winner is determined by
    *developer* (summed across all of that developer's agents), not by individual
    agent — see `service.finalize_weekly_prize` for why. `paid_at` stays null until
    Escrow supports a payout not tied to a bounty's escrow hold, which it doesn't yet."""

    __tablename__ = "weekly_prizes"

    period_key: Mapped[str] = mapped_column(String, primary_key=True)
    prize_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    winner_agent_developer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    winner_agent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    total_earnings_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
