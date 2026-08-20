import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.agent_platform import main
from services.agent_platform.config import settings
from services.agent_platform.database import Base, make_engine


@pytest.fixture
def client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    settings.internal_api_key = "test-secret"

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    try:
        yield TestClient(main.app)
    finally:
        main.app.dependency_overrides.clear()


INTERNAL_HEADERS = {"X-Internal-Api-Key": "test-secret"}


def _register_agent(client, categories=("lead_generation",), integration_mode="poll"):
    dev_resp = client.post("/developers", json={"email": "dev@example.com"})
    developer_id = dev_resp.json()["id"]

    agent_resp = client.post(
        f"/developers/{developer_id}/agents",
        json={"name": "Scout", "categories": list(categories), "integration_mode": integration_mode},
    )
    body = agent_resp.json()
    return body["agent"]["id"], body["api_key"]


def test_register_and_authenticate_flow(client):
    agent_id, api_key = _register_agent(client)

    resp = client.get("/jobs/available", headers={"Authorization": f"Bearer {api_key}"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_missing_bearer_token_is_rejected(client):
    resp = client.get("/jobs/available")
    assert resp.status_code == 401


def test_fund_match_submit_flow_over_http(client):
    agent_id, api_key = _register_agent(client)

    fund_resp = client.post(
        "/internal/jobs/fund",
        json={"job_id": "b1", "agent_id": agent_id, "category": "lead_generation", "objective_schema": {"lead_count": "integer"}},
        headers=INTERNAL_HEADERS,
    )
    assert fund_resp.status_code == 200
    assert len(fund_resp.json()) == 1

    available_resp = client.get("/jobs/available", headers={"Authorization": f"Bearer {api_key}"})
    assert len(available_resp.json()) == 1
    assert available_resp.json()[0]["job_id"] == "b1"

    submit_resp = client.post(
        "/submissions",
        json={"job_id": "b1", "payload": {"lead_count": 5}},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "queued_for_grading"


def test_internal_endpoints_reject_missing_key(client):
    resp = client.post("/internal/jobs/fund", json={"job_id": "b1", "category": "lead_generation"})
    assert resp.status_code == 401


def test_submit_with_invalid_payload_returns_422(client):
    agent_id, api_key = _register_agent(client)
    client.post(
        "/internal/jobs/fund",
        json={"job_id": "b1", "agent_id": agent_id, "category": "lead_generation", "objective_schema": {"lead_count": "integer"}},
        headers=INTERNAL_HEADERS,
    )

    resp = client.post(
        "/submissions",
        json={"job_id": "b1", "payload": {}},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert resp.status_code == 422


def test_record_verdict_over_http(client):
    agent_id, api_key = _register_agent(client)
    client.post(
        "/internal/jobs/fund",
        json={"job_id": "b1", "agent_id": agent_id, "category": "lead_generation", "objective_schema": {}},
        headers=INTERNAL_HEADERS,
    )
    submit_resp = client.post(
        "/submissions", json={"job_id": "b1", "payload": {}}, headers={"Authorization": f"Bearer {api_key}"}
    )
    submission_id = submit_resp.json()["id"]

    verdict_resp = client.post(
        "/internal/jobs/b1/verdict",
        json={"submission_id": submission_id, "passed": True},
        headers=INTERNAL_HEADERS,
    )
    assert verdict_resp.status_code == 200
    assert verdict_resp.json()["passed"] is True
