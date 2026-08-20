from collections.abc import Generator

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.orm import Session

from packages.llm_agents import build_chat_model

from . import schemas
from .config import settings
from .database import SessionLocal
from .drafter import RubricDrafter
from .exceptions import RequirementLocked, RequirementNotApproved, RequirementNotFound
from .rubric_agent import RubricAgent
from .service import RubricGenerationService

app = FastAPI(
    title="Bounty Requirement/Rubric Module",
    description="Turns a requester's free-text bounty description into a structured, approvable Requirement.",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "rubric_service"}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_drafter() -> RubricDrafter:
    model = build_chat_model(
        settings.model_backend,
        model_name=settings.model_name,
        api_key=settings.model_api_key,
        temperature=settings.model_temperature,
    )
    return RubricAgent(model)


def get_service(db: Session = Depends(get_db), drafter: RubricDrafter = Depends(get_drafter)) -> RubricGenerationService:
    return RubricGenerationService(session=db, drafter=drafter)


def require_internal_caller(x_internal_api_key: str = Header(default="")) -> None:
    if not settings.internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="missing or invalid internal API key")


@app.post("/rubrics/draft", response_model=schemas.RequirementRecordOut)
def generate_draft(body: schemas.GenerateDraftRequest, service: RubricGenerationService = Depends(get_service)):
    try:
        record = service.generate_draft(
            job_id=body.job_id, job_description=body.job_description, category=body.category
        )
    except RequirementLocked as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return schemas.RequirementRecordOut.from_record(record)


@app.put("/rubrics/{job_id}", response_model=schemas.RequirementRecordOut)
def update_draft(job_id: str, body: schemas.UpdateDraftRequest, service: RubricGenerationService = Depends(get_service)):
    try:
        record = service.update_draft(job_id=job_id, requirement=body.requirement)
    except RequirementNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RequirementLocked as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return schemas.RequirementRecordOut.from_record(record)


@app.post("/rubrics/{job_id}/approve", response_model=schemas.RequirementRecordOut)
def approve(job_id: str, service: RubricGenerationService = Depends(get_service)):
    try:
        record = service.approve(job_id=job_id)
    except RequirementNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RequirementLocked as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return schemas.RequirementRecordOut.from_record(record)


@app.get("/rubrics/{job_id}", response_model=schemas.RequirementRecordOut)
def get_rubric(job_id: str, service: RubricGenerationService = Depends(get_service)):
    try:
        record = service.get_record(job_id)
    except RequirementNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return schemas.RequirementRecordOut.from_record(record)


@app.post(
    "/internal/rubrics/{job_id}/lock",
    response_model=schemas.RequirementRecordOut,
    dependencies=[Depends(require_internal_caller)],
)
def lock_for_funding(job_id: str, service: RubricGenerationService = Depends(get_service)):
    try:
        record = service.lock_for_funding(job_id=job_id)
    except RequirementNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RequirementNotApproved as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return schemas.RequirementRecordOut.from_record(record)
