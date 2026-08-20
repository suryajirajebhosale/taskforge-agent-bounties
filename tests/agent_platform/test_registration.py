import pytest

from services.agent_platform.exceptions import AgentNotFound, DeveloperNotFound, InvalidApiKey
from services.agent_platform.models import AgentStatus, IntegrationMode, RuntimeMode


def test_register_developer_creates_a_record(service):
    developer = service.register_developer(email="dev@example.com")
    assert developer.id is not None
    assert developer.email == "dev@example.com"


def test_register_agent_returns_agent_and_raw_key_once(make_agent):
    agent, raw_key, _ = make_agent()
    assert agent.id is not None
    assert raw_key.startswith("agt_")
    # the raw key is never stored — only its hash and a display prefix
    assert agent.runtime_mode == RuntimeMode.BUILDER_HOSTED


def test_merit_hosted_runtime_is_reserved(service):
    developer = service.register_developer(email="hosted@example.com")
    with pytest.raises(ValueError, match="merit_hosted"):
        service.register_agent(
            developer_id=developer.id,
            name="Hosted",
            categories=["sales_lead_generation"],
            integration_mode=IntegrationMode.POLL,
            runtime_mode=RuntimeMode.MERIT_HOSTED,
        )


def test_register_agent_for_unknown_developer_raises(service):
    with pytest.raises(DeveloperNotFound):
        service.register_agent(
            developer_id="does-not-exist",
            name="Ghost",
            categories=["lead_generation"],
            integration_mode=IntegrationMode.POLL,
        )


def test_register_webhook_agent_without_url_raises(service):
    developer = service.register_developer(email="dev@example.com")
    with pytest.raises(ValueError):
        service.register_agent(
            developer_id=developer.id,
            name="NoUrl",
            categories=["lead_generation"],
            integration_mode=IntegrationMode.WEBHOOK,
        )


def test_authenticate_agent_with_valid_key_succeeds(service, make_agent):
    agent, raw_key, _ = make_agent()
    authenticated = service.authenticate_agent(raw_key)
    assert authenticated.id == agent.id


def test_authenticate_agent_with_invalid_key_raises(service):
    with pytest.raises(InvalidApiKey):
        service.authenticate_agent("agt_totally-made-up")


def test_authenticate_disabled_agent_raises(service, make_agent):
    agent, raw_key, _ = make_agent()
    service.disable_agent(agent.id)

    with pytest.raises(InvalidApiKey):
        service.authenticate_agent(raw_key)


def test_disable_unknown_agent_raises(service):
    with pytest.raises(AgentNotFound):
        service.disable_agent("does-not-exist")
