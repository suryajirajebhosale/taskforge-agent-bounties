from collections.abc import Generator

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.orm import Session

from . import schemas
from .config import settings
from .database import SessionLocal
from .exceptions import HoldNotFound, InvalidHoldState
from .gateways.base import StripeGateway
from .gateways.stripe_live import StripeGatewayLive
from .service import EscrowLedgerService

app = FastAPI(
    title="Escrow Ledger Service",
    description="Internal-only service: escrow funding, release, refund, and reconciliation for bounties.",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "escrow_ledger"}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_gateway() -> StripeGateway:
    return StripeGatewayLive(settings.stripe_api_key)


def get_service(db: Session = Depends(get_db), gateway: StripeGateway = Depends(get_gateway)) -> EscrowLedgerService:
    return EscrowLedgerService(session=db, gateway=gateway)


def require_internal_caller(x_internal_api_key: str = Header(default="")) -> None:
    if not settings.internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="missing or invalid internal API key")


@app.post("/internal/escrow/fund", response_model=schemas.EscrowHoldOut, dependencies=[Depends(require_internal_caller)])
def fund_job(body: schemas.FundJobRequest, service: EscrowLedgerService = Depends(get_service)):
    return service.fund_job(
        job_id=body.job_id,
        requester_id=body.requester_id,
        amount_cents=body.amount_cents,
        take_rate_bps=body.take_rate_bps,
        job_kind=body.job_kind,
        grading_fee_cents=body.grading_fee_cents,
    )


@app.post(
    "/internal/escrow/{job_id}/release",
    response_model=schemas.PayoutTransferOut,
    dependencies=[Depends(require_internal_caller)],
)
def release_to_agent(job_id: str, body: schemas.ReleaseRequest, service: EscrowLedgerService = Depends(get_service)):
    try:
        return service.release_to_agent(job_id=job_id, agent_developer_id=body.agent_developer_id)
    except HoldNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidHoldState as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@app.post(
    "/internal/escrow/{job_id}/refund",
    response_model=schemas.EscrowHoldOut,
    dependencies=[Depends(require_internal_caller)],
)
def refund_to_requester(job_id: str, service: EscrowLedgerService = Depends(get_service)):
    try:
        return service.refund_to_requester(job_id=job_id)
    except HoldNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidHoldState as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@app.post(
    "/internal/escrow/reconcile",
    response_model=schemas.ReconciliationReportOut,
    dependencies=[Depends(require_internal_caller)],
)
def reconcile(body: schemas.ReconcileRequest, service: EscrowLedgerService = Depends(get_service)):
    report = service.reconcile(body.job_ids)
    return schemas.ReconciliationReportOut(
        checked_job_ids=report.checked_job_ids,
        mismatches=[schemas.ReconciliationMismatchOut(**m.__dict__) for m in report.mismatches],
        clean=report.clean,
    )
