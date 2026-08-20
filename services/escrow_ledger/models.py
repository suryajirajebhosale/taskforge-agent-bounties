import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class HoldStatus(str, enum.Enum):
    PENDING = "pending"
    HELD = "held"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class LedgerEntryType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class JobKind(str, enum.Enum):
    RUN = "run"
    HIRE = "hire"


class CreditEntryType(str, enum.Enum):
    PURCHASE = "purchase"
    RUN_RESERVE = "run_reserve"
    GRADING_CAPTURE = "grading_capture"
    LABOR_CAPTURE = "labor_capture"
    LABOR_RELEASE = "labor_release"


class EscrowHold(Base):
    """One escrow hold per job. Source of truth for labor funds on a run or hire job."""

    __tablename__ = "escrow_holds"
    __table_args__ = (UniqueConstraint("job_id", name="uq_escrow_holds_job_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    job_kind: Mapped[JobKind] = mapped_column(Enum(JobKind), default=JobKind.RUN, nullable=False)
    requester_id: Mapped[str] = mapped_column(String, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    grading_fee_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="usd", nullable=False)
    take_rate_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[HoldStatus] = mapped_column(Enum(HoldStatus), default=HoldStatus.PENDING, nullable=False)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class PayoutTransfer(Base):
    """Records a Stripe Connect transfer to an agent developer for a won bounty."""

    __tablename__ = "payout_transfers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    agent_developer_id: Mapped[str] = mapped_column(String, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    """Net amount paid out, after the platform take-rate has been deducted."""
    stripe_transfer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[TransferStatus] = mapped_column(Enum(TransferStatus), default=TransferStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class LedgerEntry(Base):
    """Append-only double-entry ledger row. Never updated or deleted after creation."""

    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    account: Mapped[str] = mapped_column(String, nullable=False)
    entry_type: Mapped[LedgerEntryType] = mapped_column(Enum(LedgerEntryType), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class IdempotencyRecord(Base):
    """Guards fund/release/refund against duplicate execution on retry.

    Keyed on (job_id, operation) rather than a client-supplied key, since each
    operation is meaningful at most once per bounty by construction.
    """

    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("job_id", "operation", name="uq_idempotency_job_operation"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String, nullable=False)
    operation: Mapped[str] = mapped_column(String, nullable=False)
    result_id: Mapped[str] = mapped_column(String, nullable=False)
    """id of the EscrowHold or PayoutTransfer produced by the original call, returned on replay."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CreditAccount(Base):
    __tablename__ = "credit_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    company_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    balance_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class CreditLedgerEntry(Base):
    __tablename__ = "credit_ledger_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    company_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    job_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    entry_type: Mapped[CreditEntryType] = mapped_column(Enum(CreditEntryType), nullable=False)
    delta_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
