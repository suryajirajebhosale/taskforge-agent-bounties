import pytest
from sqlalchemy.orm import Session

from services.agent_platform.database import Base, make_engine
from services.agent_platform.rate_limiter import RateLimiterConfig
from services.agent_platform.service import AgentPlatformService
from services.agent_platform.webhook_notifier import WebhookNotifier


class FakeWebhookTransport:
    """In-memory transport for testing matching/delivery without real HTTP calls.
    Set `fail_times` to simulate N consecutive failures before succeeding, or
    `always_fail=True` to simulate a permanently broken endpoint."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.fail_times = 0
        self.always_fail = False

    def post(self, url: str, json_body: dict) -> int:
        self.calls.append((url, json_body))
        if self.always_fail:
            return 500
        if self.fail_times > 0:
            self.fail_times -= 1
            return 500
        return 200


class FakeReputationReader:
    """Test double letting a test assign explicit ratings per agent, unlike
    NullReputationReader which treats everyone as equal."""

    def __init__(self):
        self.ratings: dict[str, float] = {}

    def get_rating(self, agent_id: str) -> float:
        return self.ratings.get(agent_id, 0.0)


@pytest.fixture
def db_session():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def transport():
    return FakeWebhookTransport()


@pytest.fixture
def notifier(transport):
    # backoff_seconds has 3 entries (so up to 3 attempts) with no real sleeping in tests
    return WebhookNotifier(transport, backoff_seconds=[0, 0, 0], sleep_fn=lambda s: None)


@pytest.fixture
def reputation():
    # FakeReputationReader behaves exactly like NullReputationReader (0.0 for every
    # agent) until a test assigns specific ratings, so it's a safe default everywhere.
    return FakeReputationReader()


@pytest.fixture
def rate_limiter_config():
    return RateLimiterConfig(max_per_agent=3, max_per_developer=5, window_minutes=60)


@pytest.fixture
def service(db_session, notifier, reputation, rate_limiter_config):
    return AgentPlatformService(
        session=db_session,
        reputation=reputation,
        notifier=notifier,
        rate_limiter_config=rate_limiter_config,
    )


@pytest.fixture
def make_agent(service):
    """Registers a developer + one agent for them in one call. Returns (agent, raw_key, developer)."""

    from services.agent_platform.models import IntegrationMode

    def _make(
        *,
        email: str = "dev@example.com",
        name: str = "TestAgent",
        categories: list[str] | None = None,
        integration_mode: IntegrationMode = IntegrationMode.POLL,
        webhook_url: str | None = None,
    ):
        developer = service.register_developer(email=email)
        if integration_mode == IntegrationMode.WEBHOOK and webhook_url is None:
            webhook_url = "https://agent.example.com/webhook"
        agent, raw_key = service.register_agent(
            developer_id=developer.id,
            name=name,
            categories=categories or ["lead_generation"],
            integration_mode=integration_mode,
            webhook_url=webhook_url,
        )
        return agent, raw_key, developer

    return _make
