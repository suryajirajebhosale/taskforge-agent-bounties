from collections.abc import Generator

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy.orm import Session

from . import schemas
from .config import settings
from .database import SessionLocal
from .exceptions import OutcomeNotFound, PrizeNotFound
from .service import ReputationService

app = FastAPI(
    title="Reputation & Leaderboard Module",
    description="Per-agent reputation and the weekly/all-time leaderboard, computed from Oracle-reported outcomes.",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "reputation_service"}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_service(db: Session = Depends(get_db)) -> ReputationService:
    return ReputationService(
        session=db,
        decay_alpha=settings.decay_alpha,
        weekly_prize_amount_cents=settings.weekly_prize_amount_cents,
        week_start_day=settings.week_start_day,
    )


def require_internal_caller(x_internal_api_key: str = Header(default="")) -> None:
    if not settings.internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="missing or invalid internal API key")


@app.post("/internal/outcomes", response_model=schemas.OutcomeOut, dependencies=[Depends(require_internal_caller)])
def record_outcome(body: schemas.RecordOutcomeRequest, service: ReputationService = Depends(get_service)):
    outcome = service.record_outcome(
        verdict_id=body.verdict_id,
        agent_id=body.agent_id,
        agent_developer_id=body.agent_developer_id,
        passed=body.passed,
        job_amount_cents=body.job_amount_cents,
    )
    return schemas.OutcomeOut.from_model(outcome)


@app.post(
    "/internal/outcomes/{verdict_id}/correct",
    response_model=schemas.OutcomeOut,
    dependencies=[Depends(require_internal_caller)],
)
def correct_outcome(verdict_id: str, body: schemas.CorrectOutcomeRequest, service: ReputationService = Depends(get_service)):
    outcome = service.correct_outcome(
        verdict_id=verdict_id,
        agent_id=body.agent_id,
        agent_developer_id=body.agent_developer_id,
        passed=body.passed,
        job_amount_cents=body.job_amount_cents,
    )
    return schemas.OutcomeOut.from_model(outcome)


@app.get("/internal/outcomes/{verdict_id}", response_model=schemas.OutcomeOut, dependencies=[Depends(require_internal_caller)])
def get_outcome(verdict_id: str, service: ReputationService = Depends(get_service)):
    try:
        outcome = service.get_outcome(verdict_id)
    except OutcomeNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return schemas.OutcomeOut.from_model(outcome)


@app.get("/agents/{agent_id}/rating", response_model=schemas.RatingOut)
def get_rating(agent_id: str, service: ReputationService = Depends(get_service)):
    return schemas.RatingOut(
        agent_id=agent_id, rating=service.get_rating(agent_id), verified_count=service.get_verified_count(agent_id)
    )


@app.get("/leaderboard", response_model=list[schemas.LeaderboardRowOut])
def get_leaderboard(period: str = Query(default="weekly"), service: ReputationService = Depends(get_service)):
    try:
        rows = service.get_leaderboard(period=period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return [schemas.LeaderboardRowOut.from_row(r) for r in rows]


@app.post(
    "/internal/weekly-prize/finalize",
    response_model=schemas.WeeklyPrizeOut,
    dependencies=[Depends(require_internal_caller)],
)
def finalize_weekly_prize(body: schemas.FinalizeWeeklyPrizeRequest, service: ReputationService = Depends(get_service)):
    prize = service.finalize_weekly_prize(period_key=body.period_key)
    return schemas.WeeklyPrizeOut.from_model(prize)


@app.get("/weekly-prize/{period_key}", response_model=schemas.WeeklyPrizeOut)
def get_weekly_prize(period_key: str, service: ReputationService = Depends(get_service)):
    try:
        prize = service.get_weekly_prize(period_key)
    except PrizeNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return schemas.WeeklyPrizeOut.from_model(prize)


@app.post(
    "/internal/weekly-prize/{period_key}/mark-paid",
    response_model=schemas.WeeklyPrizeOut,
    dependencies=[Depends(require_internal_caller)],
)
def mark_prize_paid(period_key: str, service: ReputationService = Depends(get_service)):
    try:
        prize = service.mark_prize_paid(period_key=period_key)
    except PrizeNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return schemas.WeeklyPrizeOut.from_model(prize)
