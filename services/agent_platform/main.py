from collections.abc import Generator

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.orm import Session

from . import schemas
from .config import settings
from .database import SessionLocal
from .exceptions import (
    AgentNotFound,
    BountyNotRegistered,
    DeveloperNotFound,
    InvalidApiKey,
    NotMatchedToBounty,
    RateLimitExceeded,
    SubmissionNotFound,
    SubmissionValidationError,
)
from .models import Agent
from .service import AgentPlatformService

app = FastAPI(
    title="Agent SDK & Submission Intake",
    description="Registration, capability-based bounty matching, and submission intake for third-party agent developers.",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent_platform"}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_service(db: Session = Depends(get_db)) -> AgentPlatformService:
    return AgentPlatformService(session=db)


def require_internal_caller(x_internal_api_key: str = Header(default="")) -> None:
    if not settings.internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="missing or invalid internal API key")


def require_agent(
    authorization: str = Header(default=""), service: AgentPlatformService = Depends(get_service)
) -> Agent:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    raw_key = authorization.removeprefix("Bearer ").strip()
    try:
        return service.authenticate_agent(raw_key)
    except InvalidApiKey as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


# -- developer-facing: registration ---------------------------------------------------


@app.post("/developers", response_model=schemas.AgentDeveloperOut)
def register_developer(body: schemas.RegisterDeveloperRequest, service: AgentPlatformService = Depends(get_service)):
    return service.register_developer(email=body.email)


@app.post("/developers/{developer_id}/agents", response_model=schemas.RegisterAgentResponse)
def register_agent(
    developer_id: str, body: schemas.RegisterAgentRequest, service: AgentPlatformService = Depends(get_service)
):
    try:
        agent, raw_key = service.register_agent(
            developer_id=developer_id,
            name=body.name,
            categories=body.categories,
            integration_mode=body.integration_mode,
            webhook_url=body.webhook_url,
        )
    except DeveloperNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return schemas.RegisterAgentResponse(agent=agent, api_key=raw_key)


# -- agent-facing: discovery and submission --------------------------------------------


@app.get("/bounties/available", response_model=list[schemas.BountyMatchOut])
def available_bounties(agent: Agent = Depends(require_agent), service: AgentPlatformService = Depends(get_service)):
    return service.available_bounties_for_agent(agent.id)


@app.post("/submissions", response_model=schemas.SubmissionOut)
def submit(
    body: schemas.SubmitRequest,
    agent: Agent = Depends(require_agent),
    service: AgentPlatformService = Depends(get_service),
):
    try:
        return service.submit(bounty_id=body.bounty_id, agent_id=agent.id, payload=body.payload)
    except BountyNotRegistered as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except NotMatchedToBounty as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    except SubmissionValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors) from e


# -- internal: called by whatever funds bounties, and by the Oracle Verification Service --


@app.post(
    "/internal/bounties/fund", response_model=list[schemas.BountyMatchOut], dependencies=[Depends(require_internal_caller)]
)
def notify_bounty_funded(body: schemas.NotifyBountyFundedRequest, service: AgentPlatformService = Depends(get_service)):
    return service.notify_bounty_funded(
        bounty_id=body.bounty_id, category=body.category, objective_schema=body.objective_schema
    )


@app.post(
    "/internal/bounties/{bounty_id}/verdict",
    response_model=schemas.SubmissionOut,
    dependencies=[Depends(require_internal_caller)],
)
def record_verdict(bounty_id: str, body: schemas.RecordVerdictRequest, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.record_verdict(bounty_id=bounty_id, submission_id=body.submission_id, passed=body.passed)
    except SubmissionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
