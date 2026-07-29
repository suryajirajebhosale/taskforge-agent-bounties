import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FinalResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"


class DisputeResolution(str, enum.Enum):
    UPHELD = "upheld"
    OVERTURNED = "overturned"


class Verdict(Base):
    """One grading pass over a submission. `stage_results` holds the raw output of
    every pipeline stage that ran (deterministic checks, sandbox execution, judge) for
    auditability and disputes — `final_result`/`confidence`/`rationale` are the combined
    outcome the rest of the system acts on."""

    __tablename__ = "verdicts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    submission_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    bounty_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_developer_id: Mapped[str] = mapped_column(String, nullable=False)
    bounty_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    """`agent_id`, `agent_developer_id`, and `bounty_amount_cents` are all denormalized
    so a later human-review or dispute resolution can still trigger the escrow payout
    and report the outcome to the Reputation & Leaderboard Module without needing to
    ask Agent Platform again."""
    stage_results: Mapped[dict] = mapped_column(JSON, nullable=False)
    final_result: Mapped[FinalResult] = mapped_column(Enum(FinalResult), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(String, nullable=False)
    routed_to_human: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    """True once this verdict is final and downstream services have been (or are about
    to be) notified — either auto-resolved at grading time, or completed by a human
    reviewer or a dispute resolution."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class DisputeCase(Base):
    """An agent developer's appeal of a verdict, and the independent re-grade it
    triggered. `resolution` is set once `resolve_dispute` applies the outcome."""

    __tablename__ = "dispute_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    verdict_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    raised_by: Mapped[str] = mapped_column(String, nullable=False)
    regrade_result: Mapped[FinalResult] = mapped_column(Enum(FinalResult), nullable=False)
    regrade_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    regrade_rationale: Mapped[str] = mapped_column(String, nullable=False)
    resolution: Mapped[DisputeResolution | None] = mapped_column(Enum(DisputeResolution), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
