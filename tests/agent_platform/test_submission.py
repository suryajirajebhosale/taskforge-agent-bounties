import pytest

from services.agent_platform.exceptions import (
    JobNotRegistered,
    NotAssignedToJob,
    RateLimitExceeded,
    SubmissionValidationError,
)
from services.agent_platform.models import IntegrationMode, SubmissionStatus

SCHEMA = {"lead_count": "integer", "company_name": "string"}


def test_submit_to_unregistered_bounty_raises(service, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"])

    with pytest.raises(JobNotRegistered):
        service.submit(job_id="never-funded", agent_id=agent.id, payload={})


def test_submit_without_a_prior_match_raises(service, make_agent):
    assigned, _, _ = make_agent(email="a@example.com", categories=["lead_generation"])
    other, _, _ = make_agent(email="b@example.com", categories=["lead_generation"])
    service.notify_job_funded(job_id="b1", agent_id=assigned.id, category="lead_generation", objective_schema=SCHEMA)

    with pytest.raises(NotAssignedToJob):
        service.submit(job_id="b1", agent_id=other.id, payload={"lead_count": 10, "company_name": "Acme"})


def test_submit_accepts_a_valid_payload(service, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"])
    service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation", objective_schema=SCHEMA)

    submission = service.submit(
        job_id="b1", agent_id=agent.id, payload={"lead_count": 10, "company_name": "Acme"}
    )

    assert submission.status == SubmissionStatus.QUEUED_FOR_GRADING


def test_submit_rejects_payload_missing_a_required_field(service, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"])
    service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation", objective_schema=SCHEMA)

    with pytest.raises(SubmissionValidationError) as exc_info:
        service.submit(job_id="b1", agent_id=agent.id, payload={"lead_count": 10})

    assert "company_name" in exc_info.value.errors[0]


def test_submit_rejects_payload_with_wrong_type(service, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"])
    service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation", objective_schema=SCHEMA)

    with pytest.raises(SubmissionValidationError) as exc_info:
        service.submit(job_id="b1", agent_id=agent.id, payload={"lead_count": "ten", "company_name": "Acme"})

    assert any("lead_count" in e for e in exc_info.value.errors)


def test_rate_limit_rejects_excess_submissions_from_same_agent(service, make_agent):
    # rate_limiter_config fixture caps at 3 per agent per window
    agent, _, _ = make_agent(categories=["lead_generation"])
    for i in range(3):
        service.notify_job_funded(job_id=f"b{i}", agent_id=agent.id, category="lead_generation", objective_schema=SCHEMA)
        service.submit(job_id=f"b{i}", agent_id=agent.id, payload={"lead_count": 1, "company_name": "x"})

    service.notify_job_funded(job_id="b4", agent_id=agent.id, category="lead_generation", objective_schema=SCHEMA)
    with pytest.raises(RateLimitExceeded):
        service.submit(job_id="b4", agent_id=agent.id, payload={"lead_count": 1, "company_name": "x"})


def test_rate_limit_rejects_excess_submissions_from_same_developer_across_agents(service):
    # rate_limiter_config fixture caps at 5 per developer per window
    developer = service.register_developer(email="dev@example.com")
    agents = []
    for i in range(5):
        agent, _ = service.register_agent(
            developer_id=developer.id,
            name=f"agent-{i}",
            categories=["lead_generation"],
            integration_mode=IntegrationMode.POLL,
        )
        agents.append(agent)

    for i, agent in enumerate(agents):
        service.notify_job_funded(job_id=f"b{i}", agent_id=agent.id, category="lead_generation", objective_schema=SCHEMA)
        service.submit(job_id=f"b{i}", agent_id=agent.id, payload={"lead_count": 1, "company_name": "x"})

    # a 6th agent belonging to the same developer should be blocked by the developer-level cap
    sixth_agent, _ = service.register_agent(
        developer_id=developer.id, name="agent-6", categories=["lead_generation"], integration_mode=IntegrationMode.POLL
    )
    service.notify_job_funded(job_id="b6", agent_id=sixth_agent.id, category="lead_generation", objective_schema=SCHEMA)
    with pytest.raises(RateLimitExceeded):
        service.submit(job_id="b6", agent_id=sixth_agent.id, payload={"lead_count": 1, "company_name": "x"})
