from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from .models import AgentStatus, IntegrationMode, RuntimeMode, SubmissionStatus


class RegisterDeveloperRequest(BaseModel):
    email: str


class AgentDeveloperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str


class RegisterAgentRequest(BaseModel):
    name: str
    categories: list[str]
    integration_mode: IntegrationMode
    webhook_url: str | None = None
    runtime_mode: RuntimeMode = RuntimeMode.BUILDER_HOSTED


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: str
    developer_id: str
    name: str
    categories: list[str]
    integration_mode: IntegrationMode
    runtime_mode: RuntimeMode
    status: AgentStatus
    api_key_prefix: str


class RegisterAgentResponse(BaseModel):
    agent: AgentOut
    api_key: str
    """Shown once, at creation time only."""


class JobAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_id: str
    agent_id: str


class NotifyJobFundedRequest(BaseModel):
    job_id: str
    agent_id: str
    category: str
    objective_schema: dict[str, str] = {}


class RegisterCompanyRequest(BaseModel):
    email: str


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str


class CreateListingRequest(BaseModel):
    agent_id: str
    category: str
    requirement: dict | None = None
    credits_per_row: int
    badge: str = "sandbox"
    hire_monthly_cents: int | None = None
    included_runs: int | None = None
    template_id: str = "lead_enrichment"
    template_version: int | None = None
    blurb: str = ""
    harness_json: dict | None = None


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: str
    agent_id: str
    contract_id: str
    badge: str
    status: str
    credits_per_row: int
    hire_monthly_cents: int | None
    included_runs: int | None
    template_id: str
    template_version: int
    optional_fields: dict
    blurb: str
    eval_pass_rate: float
    is_legacy: bool
    harness_json: dict
    grace_ends_at: datetime | None = None

    @field_serializer("grace_ends_at")
    def _ser_grace(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None


class CertifyListingRequest(BaseModel):
    submissions: dict[str, dict]


class SlaChecklistRequest(BaseModel):
    kyc_ok: bool
    tos_ok: bool
    canary_ok: bool
    webhook_uptime_ok: bool
    notes: str = ""


class PublishSandboxRequest(BaseModel):
    email: str
    name: str
    categories: list[str]
    integration_mode: IntegrationMode
    webhook_url: str | None = None
    credits_per_row: int
    hire_monthly_cents: int | None = None
    included_runs: int | None = None
    blurb: str = ""
    requirement: dict | None = None


class PublishSandboxResponse(BaseModel):
    developer: AgentDeveloperOut
    agent: AgentOut
    api_key: str
    listing: ListingOut


class SearchListingsResponse(BaseModel):
    explanation: str
    template_id: str | None
    listings: list[ListingOut]


class CreateHireRequest(BaseModel):
    company_id: str
    listing_id: str
    period_days: int = 30


class HireOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: str
    company_id: str
    listing_id: str
    agent_id: str
    status: str
    monthly_cents: int
    included_runs: int
    runs_used: int
    template_version: int
    harness_hash: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: str
    kind: str
    company_id: str
    listing_id: str
    agent_id: str
    hire_id: str | None
    contract_id: str
    status: str
    row_count: int
    credits_charged: int
    labor_amount_cents: int
    grading_fee_cents: int


class CreateJobRequest(BaseModel):
    company_id: str
    listing_id: str
    row_count: int
    hire_id: str | None = None


class SubmitRequest(BaseModel):
    job_id: str
    payload: dict
    trace: dict | None = None


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_id: str
    agent_id: str
    status: SubmissionStatus
    passed: bool | None
    harness_ok: bool | None = None
    trace_digest: str | None = None


class RecordVerdictRequest(BaseModel):
    submission_id: str
    passed: bool
