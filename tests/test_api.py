import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.escrow_ledger import main
from services.escrow_ledger.config import settings
from services.escrow_ledger.database import Base, make_engine
from services.escrow_ledger.gateways.fake import FakeStripeGateway


@pytest.fixture
def client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    gateway = FakeStripeGateway()
    settings.internal_api_key = "test-secret"

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    def override_get_gateway():
        return gateway

    main.app.dependency_overrides[main.get_db] = override_get_db
    main.app.dependency_overrides[main.get_gateway] = override_get_gateway
    try:
        yield TestClient(main.app)
    finally:
        main.app.dependency_overrides.clear()


HEADERS = {"X-Internal-Api-Key": "test-secret"}


def test_fund_release_flow_over_http(client):
    fund_resp = client.post(
        "/internal/escrow/fund",
        json={"job_id": "b1", "requester_id": "req1", "amount_cents": 10_000, "take_rate_bps": 1000},
        headers=HEADERS,
    )
    assert fund_resp.status_code == 200
    assert fund_resp.json()["status"] == "held"

    release_resp = client.post(
        "/internal/escrow/b1/release", json={"agent_developer_id": "dev1"}, headers=HEADERS
    )
    assert release_resp.status_code == 200
    assert release_resp.json()["amount_cents"] == 9_000


def test_requests_without_internal_key_are_rejected(client):
    resp = client.post(
        "/internal/escrow/fund",
        json={"job_id": "b1", "requester_id": "req1", "amount_cents": 10_000},
    )
    assert resp.status_code == 401


def test_release_on_unknown_bounty_returns_404(client):
    resp = client.post("/internal/escrow/nope/release", json={"agent_developer_id": "dev1"}, headers=HEADERS)
    assert resp.status_code == 404


def test_release_twice_returns_409_on_wrong_state(client):
    client.post(
        "/internal/escrow/fund",
        json={"job_id": "b1", "requester_id": "req1", "amount_cents": 5_000},
        headers=HEADERS,
    )
    client.post("/internal/escrow/b1/refund", headers=HEADERS)

    resp = client.post("/internal/escrow/b1/release", json={"agent_developer_id": "dev1"}, headers=HEADERS)
    assert resp.status_code == 409
