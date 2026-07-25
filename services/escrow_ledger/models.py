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


class EscrowHold(Base):
    """One escrow hold per bounty. Source of truth for what state a bounty's funds are in."""

    __tablename__ = "escrow_holds"
    __table_args__ = (UniqueConstraint("bounty_id", name="uq_escrow_holds_bounty_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    bounty_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    requester_id: Mapped[str] = mapped_column(String, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
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
    bounty_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
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
    bounty_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    account: Mapped[str] = mapped_column(String, nullable=False)
    entry_type: Mapped[LedgerEntryType] = mapped_column(Enum(LedgerEntryType), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class IdempotencyRecord(Base):
    """Guards fund/release/refund against duplicate execution on retry.

    Keyed on (bounty_id, operation) rather than a client-supplied key, since each
    operation is meaningful at most once per bounty by construction.
    """

    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("bounty_id", "operation", name="uq_idempotency_bounty_operation"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    bounty_id: Mapped[str] = mapped_column(String, nullable=False)
    operation: Mapped[str] = mapped_column(String, nullable=False)
    result_id: Mapped[str] = mapped_column(String, nullable=False)
    """id of the EscrowHold or PayoutTransfer produced by the original call, returned on replay."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
