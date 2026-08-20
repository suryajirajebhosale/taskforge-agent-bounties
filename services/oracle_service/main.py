from collections.abc import Generator

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.orm import Session

from packages.llm_agents import build_chat_model

from . import schemas
from .config import settings
from .confidence_router import RoutingConfig
from .database import SessionLocal
from .dispute_agent import DisputeAgent
from .downstream_clients import (
    AgentPlatformClient,
    EscrowClient,
    HttpAgentPlatformClient,
    HttpEscrowClient,
    HttpReputationClient,
    ReputationClient,
)
from .exceptions import DisputeCaseNotFound, VerdictNotFound
from .judge_agent import JudgeAgent
from .sandbox_executor import SandboxExecutor, SubprocessSandboxExecutor
from .service import VerificationService

app = FastAPI(
    title="Oracle Verification Service",
    description="Grades bounty submissions against their Requirement and drives escrow payout on a verified pass.",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "oracle_service"}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_judge() -> JudgeAgent:
    model = build_chat_model(
        settings.judge_model_backend,
        model_name=settings.judge_model_name,
        api_key=settings.judge_model_api_key,
        temperature=settings.judge_model_temperature,
    )
    return JudgeAgent(model)


def get_dispute_judge() -> DisputeAgent:
    model = build_chat_model(
        settings.dispute_model_backend,
        model_name=settings.dispute_model_name,
        api_key=settings.dispute_model_api_key,
        temperature=settings.dispute_model_temperature,
    )
    return DisputeAgent(model)


def get_sandbox() -> SandboxExecutor:
    return SubprocessSandboxExecutor()


def get_routing_config() -> RoutingConfig:
    return RoutingConfig(
        confidence_threshold=settings.default_confidence_threshold,
        auto_resolve_amount_cents_ceiling=settings.auto_resolve_amount_cents_ceiling,
    )


def get_escrow_client() -> EscrowClient:
    return HttpEscrowClient(settings.escrow_base_url, settings.escrow_internal_api_key)


def get_agent_platform_client() -> AgentPlatformClient:
    return HttpAgentPlatformClient(settings.agent_platform_base_url, settings.agent_platform_internal_api_key)


def get_reputation_client() -> ReputationClient:
    return HttpReputationClient(settings.reputation_base_url, settings.reputation_internal_api_key)


def get_service(
    db: Session = Depends(get_db),
    judge: JudgeAgent = Depends(get_judge),
    dispute_judge: DisputeAgent = Depends(get_dispute_judge),
    sandbox: SandboxExecutor = Depends(get_sandbox),
    routing_config: RoutingConfig = Depends(get_routing_config),
    escrow_client: EscrowClient = Depends(get_escrow_client),
    agent_platform_client: AgentPlatformClient = Depends(get_agent_platform_client),
    reputation_client: ReputationClient = Depends(get_reputation_client),
) -> VerificationService:
    return VerificationService(
        session=db,
        judge=judge,
        dispute_judge=dispute_judge,
        routing_config=routing_config,
        sandbox=sandbox,
        escrow_client=escrow_client,
        agent_platform_client=agent_platform_client,
        reputation_client=reputation_client,
    )


def require_internal_caller(x_internal_api_key: str = Header(default="")) -> None:
    if not settings.internal_api_key or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="missing or invalid internal API key")


@app.post("/internal/verify", response_model=schemas.VerdictOut, dependencies=[Depends(require_internal_caller)])
def verify(body: schemas.GradeSubmissionRequest, service: VerificationService = Depends(get_service)):
    verdict = service.grade_submission(
        submission_id=body.submission_id,
        job_id=body.job_id,
        agent_id=body.agent_id,
        agent_developer_id=body.agent_developer_id,
        category=body.category,
        requirement=body.requirement,
        payload=body.payload,
        job_amount_cents=body.job_amount_cents,
        code_script=body.code_script,
    )
    return schemas.VerdictOut.from_model(verdict)


@app.get("/verdicts/{verdict_id}", response_model=schemas.VerdictOut)
def get_verdict(verdict_id: str, service: VerificationService = Depends(get_service)):
    try:
        verdict = service.get_verdict(verdict_id)
    except VerdictNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return schemas.VerdictOut.from_model(verdict)


@app.post(
    "/internal/verdicts/{verdict_id}/human-review",
    response_model=schemas.VerdictOut,
    dependencies=[Depends(require_internal_caller)],
)
def human_review(verdict_id: str, body: schemas.HumanReviewRequest, service: VerificationService = Depends(get_service)):
    try:
        verdict = service.resolve_human_review(verdict_id=verdict_id, final_result=body.final_result, reviewer=body.reviewer)
    except VerdictNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return schemas.VerdictOut.from_model(verdict)


# Note: in a full deployment, raising a dispute would sit behind an agent-developer-
# authenticated gateway (Agent Platform owns that identity, not this service) — gated
# behind the shared internal key here for consistency with the rest of this MVP.
@app.post("/internal/disputes", response_model=schemas.DisputeCaseOut, dependencies=[Depends(require_internal_caller)])
def raise_dispute(body: schemas.RaiseDisputeRequest, service: VerificationService = Depends(get_service)):
    try:
        case = service.raise_dispute(
            verdict_id=body.verdict_id, raised_by=body.raised_by, payload=body.payload, requirement=body.requirement
        )
    except VerdictNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return schemas.DisputeCaseOut.from_model(case)


@app.get("/disputes/{dispute_id}", response_model=schemas.DisputeCaseOut)
def get_dispute(dispute_id: str, service: VerificationService = Depends(get_service)):
    try:
        case = service.get_dispute(dispute_id)
    except DisputeCaseNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return schemas.DisputeCaseOut.from_model(case)


@app.post(
    "/internal/disputes/{dispute_id}/resolve",
    response_model=schemas.DisputeCaseOut,
    dependencies=[Depends(require_internal_caller)],
)
def resolve_dispute(dispute_id: str, body: schemas.ResolveDisputeRequest, service: VerificationService = Depends(get_service)):
    try:
        case = service.resolve_dispute(dispute_id=dispute_id, resolved_by=body.resolved_by)
    except DisputeCaseNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return schemas.DisputeCaseOut.from_model(case)
