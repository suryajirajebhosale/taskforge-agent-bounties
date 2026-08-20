from collections.abc import Generator

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.orm import Session

from . import schemas
from .config import settings
from .database import SessionLocal
from .exceptions import (
    AgentNotFound,
    AttestationRequired,
    CertificationFailed,
    DeveloperNotFound,
    InvalidApiKey,
    JobAlreadyAssigned,
    JobNotRegistered,
    NotAssignedToJob,
    RateLimitExceeded,
    SlaChecklistIncomplete,
    SubmissionNotFound,
    SubmissionValidationError,
)
from .models import Agent
from .search_compiler import compile_search_query
from .service import AgentPlatformService
from .templates import get_template, list_templates

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
            runtime_mode=body.runtime_mode,
        )
    except DeveloperNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return schemas.RegisterAgentResponse(agent=agent, api_key=raw_key)


@app.post("/agents/{agent_id}/attest", response_model=schemas.AgentOut)
def attest_agent(agent_id: str, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.attest_agent(agent_id)
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# -- agent-facing: discovery and submission --------------------------------------------


@app.get("/jobs/available", response_model=list[schemas.JobAssignmentOut])
def available_bounties(agent: Agent = Depends(require_agent), service: AgentPlatformService = Depends(get_service)):
    return service.available_jobs_for_agent(agent.id)


@app.post("/submissions", response_model=schemas.SubmissionOut)
def submit(
    body: schemas.SubmitRequest,
    agent: Agent = Depends(require_agent),
    service: AgentPlatformService = Depends(get_service),
):
    try:
        return service.submit(job_id=body.job_id, agent_id=agent.id, payload=body.payload, trace=body.trace)
    except JobNotRegistered as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except NotAssignedToJob as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    except SubmissionValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors) from e


# -- internal: called by whatever funds bounties, and by the Oracle Verification Service --


@app.post(
    "/internal/jobs/fund", response_model=list[schemas.JobAssignmentOut], dependencies=[Depends(require_internal_caller)]
)
def notify_job_funded(body: schemas.NotifyJobFundedRequest, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.notify_job_funded(
            job_id=body.job_id,
            agent_id=body.agent_id,
            category=body.category,
            objective_schema=body.objective_schema,
        )
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except JobAlreadyAssigned as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except NotAssignedToJob as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@app.post(
    "/internal/jobs/{job_id}/verdict",
    response_model=schemas.SubmissionOut,
    dependencies=[Depends(require_internal_caller)],
)
def record_verdict(job_id: str, body: schemas.RecordVerdictRequest, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.record_verdict(job_id=job_id, submission_id=body.submission_id, passed=body.passed)
    except SubmissionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/companies", response_model=schemas.CompanyOut)
def register_company(body: schemas.RegisterCompanyRequest, service: AgentPlatformService = Depends(get_service)):
    return service.register_company(email=body.email)


@app.post("/listings", response_model=schemas.ListingOut)
def create_listing(body: schemas.CreateListingRequest, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.create_listing(
            agent_id=body.agent_id,
            category=body.category,
            requirement=body.requirement,
            credits_per_row=body.credits_per_row,
            badge=body.badge,
            hire_monthly_cents=body.hire_monthly_cents,
            included_runs=body.included_runs,
            template_id=body.template_id,
            template_version=body.template_version,
            blurb=body.blurb,
            harness_json=body.harness_json,
        )
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/listings/{listing_id}/certify", response_model=schemas.ListingOut)
def certify_listing(
    listing_id: str, body: schemas.CertifyListingRequest, service: AgentPlatformService = Depends(get_service)
):
    try:
        return service.certify_listing(listing_id, body.submissions)
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except CertificationFailed as e:
        raise HTTPException(status_code=422, detail=e.errors) from e


@app.post("/listings/{listing_id}/sla-checklist")
def sla_checklist(
    listing_id: str, body: schemas.SlaChecklistRequest, service: AgentPlatformService = Depends(get_service)
):
    try:
        row = service.submit_sla_checklist(
            listing_id,
            kyc_ok=body.kyc_ok,
            tos_ok=body.tos_ok,
            canary_ok=body.canary_ok,
            webhook_uptime_ok=body.webhook_uptime_ok,
            notes=body.notes,
        )
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {
        "listing_id": row.listing_id,
        "kyc_ok": row.kyc_ok,
        "tos_ok": row.tos_ok,
        "canary_ok": row.canary_ok,
        "webhook_uptime_ok": row.webhook_uptime_ok,
    }


@app.post("/listings/{listing_id}/promote-sla", response_model=schemas.ListingOut)
def promote_sla(listing_id: str, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.promote_to_sla(listing_id)
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except SlaChecklistIncomplete as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except AttestationRequired as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/listings/search", response_model=schemas.SearchListingsResponse)
def search_listings(q: str = "", service: AgentPlatformService = Depends(get_service)):
    compiled = compile_search_query(q)
    listings = service.search_listings(q)
    return schemas.SearchListingsResponse(
        explanation=compiled.explanation,
        template_id=compiled.template_id,
        listings=listings,
    )


@app.get("/listings/{listing_id}", response_model=schemas.ListingOut)
def get_listing(listing_id: str, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.get_listing(listing_id)
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/templates")
def list_all_templates():
    return [_template_body(t) for t in list_templates()]


@app.get("/templates/{template_id}")
def read_template(template_id: str, version: int | None = None):
    try:
        template = get_template(template_id, version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return _template_body(template)


def _template_body(template) -> dict:
    return {
        "id": template.id,
        "version": template.version,
        "title": template.title,
        "category": template.category,
        "input_fields": list(template.input_fields),
        "required_fields": list(template.required_fields),
        "requirement": template.requirement,
        "changelog": template.changelog,
    }


@app.post("/publish", response_model=schemas.PublishSandboxResponse)
def publish_sandbox(body: schemas.PublishSandboxRequest, service: AgentPlatformService = Depends(get_service)):
    try:
        developer, agent, raw_key, listing = service.publish_sandbox(
            email=body.email,
            name=body.name,
            categories=body.categories,
            integration_mode=body.integration_mode,
            webhook_url=body.webhook_url,
            credits_per_row=body.credits_per_row,
            hire_monthly_cents=body.hire_monthly_cents,
            included_runs=body.included_runs,
            blurb=body.blurb,
            requirement=body.requirement,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return schemas.PublishSandboxResponse(
        developer=developer, agent=agent, api_key=raw_key, listing=listing
    )


@app.post("/hires", response_model=schemas.HireOut)
def create_hire(body: schemas.CreateHireRequest, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.create_hire(
            company_id=body.company_id, listing_id=body.listing_id, period_days=body.period_days
        )
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/jobs", response_model=schemas.JobOut)
def create_run_job(body: schemas.CreateJobRequest, service: AgentPlatformService = Depends(get_service)):
    try:
        return service.create_job(
            company_id=body.company_id,
            listing_id=body.listing_id,
            row_count=body.row_count,
            hire_id=body.hire_id,
        )
    except AgentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
