from pydantic import BaseModel, ConfigDict

from .models import HoldStatus, JobKind, TransferStatus


class FundJobRequest(BaseModel):
    job_id: str
    requester_id: str
    amount_cents: int
    take_rate_bps: int | None = None
    job_kind: JobKind = JobKind.RUN
    grading_fee_cents: int = 0


class ReleaseRequest(BaseModel):
    agent_developer_id: str


class EscrowHoldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    job_kind: JobKind
    requester_id: str
    amount_cents: int
    grading_fee_cents: int
    currency: str
    take_rate_bps: int
    status: HoldStatus
    stripe_payment_intent_id: str | None


class PayoutTransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    agent_developer_id: str
    amount_cents: int
    stripe_transfer_id: str | None
    status: TransferStatus


class ReconcileRequest(BaseModel):
    job_ids: list[str]


class ReconciliationMismatchOut(BaseModel):
    job_id: str
    reason: str
    internal_amount_cents: int
    stripe_amount_cents: int


class ReconciliationReportOut(BaseModel):
    checked_job_ids: list[str]
    mismatches: list[ReconciliationMismatchOut]
    clean: bool
