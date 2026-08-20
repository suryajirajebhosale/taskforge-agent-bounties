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


class RuntimeMode(str, enum.Enum):
    BUILDER_HOSTED = "builder_hosted"
    MERIT_HOSTED = "merit_hosted"
    ATTESTED = "attested"


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
    runtime_mode: Mapped[RuntimeMode] = mapped_column(
        Enum(RuntimeMode), default=RuntimeMode.BUILDER_HOSTED, nullable=False
    )
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), default=AgentStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class JobRef(Base):
    """Local read-model of a bounty, populated by `notify_job_funded`. This service
    doesn't own bounty data — it caches just enough (category, objective criteria shape)
    to match agents and validate submissions without a synchronous call to another
    service on every request."""

    __tablename__ = "job_refs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    objective_schema: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    """Maps field name -> expected type name (`string`/`integer`/`number`/`boolean`/`list`),
    mirroring `Requirement.objective_criteria` from the Bounty Requirement/Rubric Module."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class JobAssignment(Base):
    __tablename__ = "job_assignments"
    __table_args__ = (UniqueConstraint("job_id", "agent_id", name="uq_job_assignments_job_agent"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_delivery_error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    developer_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    """Denormalized from Agent at submit time, so per-developer rate limiting doesn't
    require a join on every check."""
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    harness_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    trace_digest: Mapped[str | None] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ListingBadge(str, enum.Enum):
    SANDBOX = "sandbox"
    CERTIFIED = "certified"
    SLA = "sla"


class ListingStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class JobKind(str, enum.Enum):
    RUN = "run"
    HIRE = "hire"


class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    FUNDED = "funded"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class HireStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CapabilityContract(Base):
    __tablename__ = "capability_contracts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    listing_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    requirement_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String, default="approved", nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    agent_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    contract_id: Mapped[str] = mapped_column(String, nullable=False)
    badge: Mapped[ListingBadge] = mapped_column(Enum(ListingBadge), default=ListingBadge.SANDBOX, nullable=False)
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.ACTIVE, nullable=False)
    credits_per_row: Mapped[int] = mapped_column(Integer, nullable=False)
    hire_monthly_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    included_runs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    template_id: Mapped[str] = mapped_column(String, default="lead_enrichment", nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    optional_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    blurb: Mapped[str] = mapped_column(String, default="", nullable=False)
    eval_pass_rate: Mapped[float] = mapped_column(default=0.0, nullable=False)
    is_legacy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    grace_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    harness_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Hire(Base):
    __tablename__ = "hires"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    company_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    listing_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[HireStatus] = mapped_column(Enum(HireStatus), default=HireStatus.ACTIVE, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    monthly_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    included_runs: Mapped[int] = mapped_column(Integer, nullable=False)
    runs_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    harness_hash: Mapped[str] = mapped_column(String, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class SlaChecklist(Base):
    __tablename__ = "sla_checklists"

    listing_id: Mapped[str] = mapped_column(String, primary_key=True)
    kyc_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tos_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canary_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    webhook_uptime_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str] = mapped_column(String, default="", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    kind: Mapped[JobKind] = mapped_column(Enum(JobKind), default=JobKind.RUN, nullable=False)
    company_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    listing_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    hire_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    contract_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.DRAFT, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credits_charged: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    labor_amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    grading_fee_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
