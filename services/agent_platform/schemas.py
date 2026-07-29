from pydantic import BaseModel, ConfigDict

from .models import AgentStatus, IntegrationMode, SubmissionStatus


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


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    developer_id: str
    name: str
    categories: list[str]
    integration_mode: IntegrationMode
    status: AgentStatus
    api_key_prefix: str


class RegisterAgentResponse(BaseModel):
    agent: AgentOut
    api_key: str
    """Shown once, at creation time only."""


class BountyMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    bounty_id: str
    agent_id: str


class NotifyBountyFundedRequest(BaseModel):
    bounty_id: str
    category: str
    objective_schema: dict[str, str] = {}


class SubmitRequest(BaseModel):
    bounty_id: str
    payload: dict


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    bounty_id: str
    agent_id: str
    status: SubmissionStatus
    passed: bool | None


class RecordVerdictRequest(BaseModel):
    submission_id: str
    passed: bool
