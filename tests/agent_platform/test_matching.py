from services.agent_platform.models import IntegrationMode


def test_matching_only_includes_agents_with_matching_category(service, make_agent):
    lead_gen_agent, _, _ = make_agent(email="a@example.com", name="LeadGen", categories=["lead_generation"])
    content_agent, _, _ = make_agent(email="b@example.com", name="Content", categories=["content_media"])

    matches = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")

    matched_agent_ids = {m.agent_id for m in matches}
    assert matched_agent_ids == {lead_gen_agent.id}


def test_matching_excludes_disabled_agents(service, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"])
    service.disable_agent(agent.id)

    matches = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")

    assert matches == []


def test_matching_ranks_by_reputation_desc(service, reputation, make_agent):
    low, _, _ = make_agent(email="low@example.com", name="Low", categories=["lead_generation"])
    high, _, _ = make_agent(email="high@example.com", name="High", categories=["lead_generation"])
    reputation.ratings[low.id] = 1.0
    reputation.ratings[high.id] = 4.5

    matches = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")

    assert [m.agent_id for m in matches] == [high.id, low.id]


def test_matching_notifies_webhook_agents_and_records_notified_at(service, transport, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.WEBHOOK)

    matches = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")

    assert matches[0].notified_at is not None
    assert len(transport.calls) == 1
    url, body = transport.calls[0]
    assert url == "https://agent.example.com/webhook"
    assert body["bounty_id"] == "b1"


def test_matching_leaves_poll_agents_unnotified(service, transport, make_agent):
    make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.POLL)

    matches = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")

    assert matches[0].notified_at is None
    assert transport.calls == []


def test_matching_is_idempotent_for_same_bounty(service, transport, make_agent):
    make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.WEBHOOK)

    first = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")
    second = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")

    assert [m.id for m in first] == [m.id for m in second]
    assert len(transport.calls) == 1  # not re-notified on replay


def test_webhook_delivery_retries_then_succeeds(service, transport, make_agent):
    transport.fail_times = 2  # backoff_seconds has 3 entries -> succeeds on 3rd attempt

    make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.WEBHOOK)
    matches = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")

    assert matches[0].notified_at is not None
    assert matches[0].delivery_attempts == 3
    assert len(transport.calls) == 3


def test_webhook_delivery_records_failure_after_exhausting_retries(service, transport, make_agent):
    transport.always_fail = True

    make_agent(categories=["lead_generation"], integration_mode=IntegrationMode.WEBHOOK)
    matches = service.notify_bounty_funded(bounty_id="b1", category="lead_generation")

    assert matches[0].notified_at is None
    assert matches[0].last_delivery_error == "webhook returned status 500"
