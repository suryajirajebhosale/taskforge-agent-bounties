from services.agent_platform.exceptions import AgentNotFound, JobAlreadyAssigned, NotAssignedToJob
from services.agent_platform.models import IntegrationMode


def test_assigns_only_the_named_agent(service, make_agent):
    lead_gen_agent, _, _ = make_agent(email="a@example.com", name="LeadGen", categories=["lead_generation"])
    make_agent(email="b@example.com", name="Content", categories=["lead_generation"])

    matches = service.notify_job_funded(
        job_id="b1", agent_id=lead_gen_agent.id, category="lead_generation"
    )

    assert [m.agent_id for m in matches] == [lead_gen_agent.id]


def test_rejects_agent_in_the_wrong_category(service, make_agent):
    agent, _, _ = make_agent(categories=["content_media"])

    try:
        service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation")
        raise AssertionError("expected NotAssignedToJob")
    except NotAssignedToJob:
        pass


def test_excludes_disabled_agents(service, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"])
    service.disable_agent(agent.id)

    try:
        service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation")
        raise AssertionError("expected AgentNotFound")
    except AgentNotFound:
        pass


def test_second_agent_cannot_take_an_assigned_job(service, make_agent):
    first, _, _ = make_agent(email="a@example.com", name="A", categories=["lead_generation"])
    second, _, _ = make_agent(email="b@example.com", name="B", categories=["lead_generation"])
    service.notify_job_funded(job_id="b1", agent_id=first.id, category="lead_generation")

    try:
        service.notify_job_funded(job_id="b1", agent_id=second.id, category="lead_generation")
        raise AssertionError("expected JobAlreadyAssigned")
    except JobAlreadyAssigned:
        pass


def test_matching_notifies_webhook_agents_and_records_notified_at(service, transport, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.WEBHOOK)

    matches = service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation")

    assert matches[0].notified_at is not None
    assert len(transport.calls) == 1
    url, body = transport.calls[0]
    assert url == "https://agent.example.com/webhook"
    assert body["job_id"] == "b1"
    assert body["agent_id"] == agent.id
    assert "requirement" in body
    assert "deadline" in body
    assert "harness_hash" in body


def test_matching_leaves_poll_agents_unnotified(service, transport, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.POLL)

    matches = service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation")

    assert matches[0].notified_at is None
    assert transport.calls == []


def test_matching_is_idempotent_for_same_job(service, transport, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.WEBHOOK)

    first = service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation")
    second = service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation")

    assert [m.id for m in first] == [m.id for m in second]
    assert len(transport.calls) == 1


def test_webhook_delivery_retries_then_succeeds(service, transport, make_agent):
    transport.fail_times = 2
    agent, _, _ = make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.WEBHOOK)
    matches = service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation")

    assert matches[0].notified_at is not None
    assert matches[0].delivery_attempts == 3
    assert len(transport.calls) == 3


def test_webhook_delivery_records_failure_after_exhausting_retries(service, transport, make_agent):
    transport.always_fail = True
    agent, _, _ = make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.WEBHOOK)
    matches = service.notify_job_funded(job_id="b1", agent_id=agent.id, category="lead_generation")

    assert matches[0].notified_at is None
    assert matches[0].last_delivery_error == "webhook returned status 500"
