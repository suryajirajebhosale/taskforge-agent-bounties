from pydantic import BaseModel, ConfigDict

from .models import HoldStatus, TransferStatus


class FundBountyRequest(BaseModel):
    bounty_id: str
    requester_id: str
    amount_cents: int
    take_rate_bps: int | None = None


class ReleaseRequest(BaseModel):
    agent_developer_id: str


class EscrowHoldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bounty_id: str
    requester_id: str
    amount_cents: int
    currency: str
    take_rate_bps: int
    status: HoldStatus
    stripe_payment_intent_id: str | None


class PayoutTransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bounty_id: str
    agent_developer_id: str
    amount_cents: int
    stripe_transfer_id: str | None
    status: TransferStatus


class ReconcileRequest(BaseModel):
    bounty_ids: list[str]


class ReconciliationMismatchOut(BaseModel):
    bounty_id: str
    reason: str
    internal_amount_cents: int
    stripe_amount_cents: int


class ReconciliationReportOut(BaseModel):
    checked_bounty_ids: list[str]
    mismatches: list[ReconciliationMismatchOut]
    clean: bool
