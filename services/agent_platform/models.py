import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationMode(str, enum.Enum):
    WEBHOOK = "webhook"
    POLL = "poll"


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED_FOR_GRADING = "queued_for_grading"
    MOOT = "moot"
    GRADED = "graded"


class AgentDeveloper(Base):
    __tablename__ = "agent_developers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    developer_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    categories: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    integration_mode: Mapped[IntegrationMode] = mapped_column(Enum(IntegrationMode), nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String, nullable=True)
    api_key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    api_key_prefix: Mapped[str] = mapped_column(String, nullable=False)
    """First few characters of the raw key, kept only for display (e.g. `agt_ab12`);
    the hash is what's actually checked on every request."""
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), default=AgentStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class BountyRef(Base):
    """Local read-model of a bounty, populated by `notify_bounty_funded`. This service
    doesn't own bounty data — it caches just enough (category, objective criteria shape)
    to match agents and validate submissions without a synchronous call to another
    service on every request."""

    __tablename__ = "bounty_refs"

    bounty_id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    objective_schema: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    """Maps field name -> expected type name (`string`/`integer`/`number`/`boolean`/`list`),
    mirroring `Requirement.objective_criteria` from the Bounty Requirement/Rubric Module."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class BountyMatch(Base):
    __tablename__ = "bounty_matches"
    __table_args__ = (UniqueConstraint("bounty_id", "agent_id", name="uq_bounty_matches_bounty_agent"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    bounty_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_delivery_error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    bounty_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    developer_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    """Denormalized from Agent at submit time, so per-developer rate limiting doesn't
    require a join on every check."""
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
