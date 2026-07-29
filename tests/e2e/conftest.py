"""Cross-service end-to-end fixtures.

These tests exercise all four services — Escrow Ledger, Agent SDK / Submission Intake,
Bounty Requirement/Rubric Module, and the Oracle Verification Service — together, over
their real HTTP contracts (each app's own TestClient, wired to the others via
`starlette.testclient.TestClient`, which is itself an `httpx.Client` subclass — see
`oracle_client` below). No internal Python calls jump between services' code; Oracle's
downstream HTTP clients talk to the real Escrow and Agent Platform apps in-process, the
same way independently deployed services would talk to each other over the network.

Oracle now plays the orchestrator role for grading -> payout: it calls Agent Platform's
`record_verdict` and, on a confirmed (non-moot) pass, Escrow's `release_to_agent`,
itself. What's still missing (and each test's docstring calls this out inline) is
refunding a requester when a bounty's *last* competing submission fails — that decision
needs visibility into a bounty's entire submission state across all agents, which is
Agent Platform's job, not Oracle's (see `VerificationService`'s docstring) — so failure-
path tests still call Escrow's refund endpoint directly, standing in for that
not-yet-built piece.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.agent_platform import main as agent_main
from services.agent_platform.database import Base as AgentBase
from services.agent_platform.database import make_engine as make_agent_engine
from services.escrow_ledger import main as escrow_main
from services.escrow_ledger.database import Base as EscrowBase
from services.escrow_ledger.database import make_engine as make_escrow_engine
from services.escrow_ledger.gateways.fake import FakeStripeGateway
from services.oracle_service import main as oracle_main
from services.oracle_service.database import Base as OracleBase
from services.oracle_service.database import make_engine as make_oracle_engine
from services.oracle_service.downstream_clients import HttpAgentPlatformClient, HttpEscrowClient, HttpReputationClient
from services.reputation_service import main as reputation_main
from services.reputation_service.database import Base as ReputationBase
from services.reputation_service.database import make_engine as make_reputation_engine
from services.rubric_service import main as rubric_main
from services.rubric_service.database import Base as RubricBase
from services.rubric_service.database import make_engine as make_rubric_engine


@pytest.fixture
def escrow_client():
    engine = make_escrow_engine("sqlite:///:memory:")
    EscrowBase.metadata.create_all(engine)
    escrow_main.settings.internal_api_key = "escrow-test-secret"
    gateway = FakeStripeGateway()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    def override_get_gateway():
        return gateway

    escrow_main.app.dependency_overrides[escrow_main.get_db] = override_get_db
    escrow_main.app.dependency_overrides[escrow_main.get_gateway] = override_get_gateway
    try:
        yield TestClient(escrow_main.app)
    finally:
        escrow_main.app.dependency_overrides.clear()


@pytest.fixture
def agent_client():
    engine = make_agent_engine("sqlite:///:memory:")
    AgentBase.metadata.create_all(engine)
    agent_main.settings.internal_api_key = "agent-test-secret"

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    agent_main.app.dependency_overrides[agent_main.get_db] = override_get_db
    try:
        yield TestClient(agent_main.app)
    finally:
        agent_main.app.dependency_overrides.clear()


@pytest.fixture
def rubric_client():
    from tests.rubric_service.conftest import FakeRubricDrafter

    engine = make_rubric_engine("sqlite:///:memory:")
    RubricBase.metadata.create_all(engine)
    rubric_main.settings.internal_api_key = "rubric-test-secret"
    drafter = FakeRubricDrafter()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    def override_get_drafter():
        return drafter

    rubric_main.app.dependency_overrides[rubric_main.get_db] = override_get_db
    rubric_main.app.dependency_overrides[rubric_main.get_drafter] = override_get_drafter
    try:
        yield TestClient(rubric_main.app)
    finally:
        rubric_main.app.dependency_overrides.clear()


@pytest.fixture
def reputation_client():
    engine = make_reputation_engine("sqlite:///:memory:")
    ReputationBase.metadata.create_all(engine)
    reputation_main.settings.internal_api_key = "reputation-test-secret"

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    reputation_main.app.dependency_overrides[reputation_main.get_db] = override_get_db
    try:
        yield TestClient(reputation_main.app)
    finally:
        reputation_main.app.dependency_overrides.clear()


@pytest.fixture
def oracle_client(escrow_client, agent_client, reputation_client):
    """Oracle's judge/dispute-judge are faked (no real LLM calls), but its downstream
    clients are real `Http*Client` instances pointed at the *other fixtures'* live
    TestClients — so a verdict genuinely flows through Oracle's own HTTP-calling code
    into the real Escrow, Agent Platform, and Reputation apps, not a shortcut back into
    this test file. Tests that want to check the resulting rating/leaderboard state
    query the `reputation_client` fixture directly."""
    from tests.oracle_service.conftest import FakeDisputeJudge, FakeJudge

    engine = make_oracle_engine("sqlite:///:memory:")
    OracleBase.metadata.create_all(engine)
    oracle_main.settings.internal_api_key = "oracle-test-secret"

    judge = FakeJudge()
    dispute_judge = FakeDisputeJudge()
    escrow_downstream = HttpEscrowClient(base_url="unused", internal_api_key="escrow-test-secret", client=escrow_client)
    agent_platform_downstream = HttpAgentPlatformClient(
        base_url="unused", internal_api_key="agent-test-secret", client=agent_client
    )
    reputation_downstream = HttpReputationClient(
        base_url="unused", internal_api_key="reputation-test-secret", client=reputation_client
    )

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    oracle_main.app.dependency_overrides[oracle_main.get_db] = override_get_db
    oracle_main.app.dependency_overrides[oracle_main.get_judge] = lambda: judge
    oracle_main.app.dependency_overrides[oracle_main.get_dispute_judge] = lambda: dispute_judge
    oracle_main.app.dependency_overrides[oracle_main.get_escrow_client] = lambda: escrow_downstream
    oracle_main.app.dependency_overrides[oracle_main.get_agent_platform_client] = lambda: agent_platform_downstream
    oracle_main.app.dependency_overrides[oracle_main.get_reputation_client] = lambda: reputation_downstream
    try:
        yield TestClient(oracle_main.app), judge, dispute_judge
    finally:
        oracle_main.app.dependency_overrides.clear()


ESCROW_HEADERS = {"X-Internal-Api-Key": "escrow-test-secret"}
AGENT_INTERNAL_HEADERS = {"X-Internal-Api-Key": "agent-test-secret"}
RUBRIC_INTERNAL_HEADERS = {"X-Internal-Api-Key": "rubric-test-secret"}
ORACLE_INTERNAL_HEADERS = {"X-Internal-Api-Key": "oracle-test-secret"}
