import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.oracle_service import main
from services.oracle_service.config import settings
from services.oracle_service.database import Base, make_engine
from services.oracle_service.judge_agent import JudgeVerdict

from .conftest import FakeAgentPlatformClient, FakeDisputeJudge, FakeEscrowClient, FakeJudge, FakeReputationClient

INTERNAL_HEADERS = {"X-Internal-Api-Key": "oracle-test-secret"}


@pytest.fixture
def client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    settings.internal_api_key = "oracle-test-secret"

    judge = FakeJudge()
    dispute_judge = FakeDisputeJudge()
    escrow_client = FakeEscrowClient()
    agent_platform_client = FakeAgentPlatformClient()
    reputation_client = FakeReputationClient()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    main.app.dependency_overrides[main.get_judge] = lambda: judge
    main.app.dependency_overrides[main.get_dispute_judge] = lambda: dispute_judge
    main.app.dependency_overrides[main.get_escrow_client] = lambda: escrow_client
    main.app.dependency_overrides[main.get_agent_platform_client] = lambda: agent_platform_client
    main.app.dependency_overrides[main.get_reputation_client] = lambda: reputation_client
    try:
        yield TestClient(main.app), judge, dispute_judge, escrow_client, agent_platform_client
    finally:
        main.app.dependency_overrides.clear()


def test_verify_endpoint_returns_a_pass_verdict_and_triggers_downstream(client):
    test_client, _, _, escrow_client, agent_platform_client = client

    resp = test_client.post(
        "/internal/verify",
        json={
            "submission_id": "s1",
            "job_id": "b1",
            "agent_id": "agent1",
            "agent_developer_id": "dev1",
            "category": "sales_lead_generation",
            "requirement": {
                "objective_criteria": [{"field": "lead_count", "comparator": ">=", "value": 100}],
                "subjective_criteria": [],
            },
            "payload": {"lead_count": 150},
            "job_amount_cents": 1000,
        },
        headers=INTERNAL_HEADERS,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["final_result"] == "pass"
    assert body["resolved"] is True
    assert escrow_client.release_calls == [("b1", "dev1")]
    assert agent_platform_client.record_calls == [("b1", "s1", True)]


def test_verify_without_internal_key_is_rejected(client):
    test_client, *_ = client

    resp = test_client.post(
        "/internal/verify",
        json={
            "submission_id": "s1",
            "job_id": "b1",
            "agent_id": "agent1",
            "agent_developer_id": "dev1",
            "category": "other",
            "requirement": {"objective_criteria": [{"field": "x", "comparator": ">=", "value": 1}], "subjective_criteria": []},
            "payload": {"x": 1},
            "job_amount_cents": 100,
        },
    )

    assert resp.status_code == 401


def test_get_verdict_over_http(client):
    test_client, *_ = client
    verify_resp = test_client.post(
        "/internal/verify",
        json={
            "submission_id": "s1",
            "job_id": "b1",
            "agent_id": "agent1",
            "agent_developer_id": "dev1",
            "category": "other",
            "requirement": {"objective_criteria": [{"field": "x", "comparator": ">=", "value": 1}], "subjective_criteria": []},
            "payload": {"x": 1},
            "job_amount_cents": 100,
        },
        headers=INTERNAL_HEADERS,
    )
    verdict_id = verify_resp.json()["id"]

    get_resp = test_client.get(f"/verdicts/{verdict_id}")

    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == verdict_id


def test_get_unknown_verdict_returns_404(client):
    test_client, *_ = client
    resp = test_client.get("/verdicts/does-not-exist")
    assert resp.status_code == 404


def test_human_review_flow_over_http(client):
    test_client, judge, _, escrow_client, _ = client
    judge.verdict = JudgeVerdict(passed=True, confidence=0.1, rationale="unsure")

    verify_resp = test_client.post(
        "/internal/verify",
        json={
            "submission_id": "s1",
            "job_id": "b1",
            "agent_id": "agent1",
            "agent_developer_id": "dev1",
            "category": "content_media",
            "requirement": {"objective_criteria": [], "subjective_criteria": [{"description": "tone", "weight": 1.0}]},
            "payload": {},
            "job_amount_cents": 100,
        },
        headers=INTERNAL_HEADERS,
    )
    body = verify_resp.json()
    assert body["resolved"] is False
    assert body["routed_to_human"] is True
    assert escrow_client.release_calls == []

    review_resp = test_client.post(
        f"/internal/verdicts/{body['id']}/human-review",
        json={"final_result": "pass", "reviewer": "ops-1"},
        headers=INTERNAL_HEADERS,
    )

    assert review_resp.status_code == 200
    assert review_resp.json()["resolved"] is True
    assert escrow_client.release_calls == [("b1", "dev1")]


def test_dispute_flow_over_http(client):
    test_client, judge, dispute_judge, escrow_client, _ = client
    judge.verdict = JudgeVerdict(passed=False, confidence=0.9, rationale="failed")
    dispute_judge.verdict = JudgeVerdict(passed=True, confidence=0.95, rationale="actually fine")

    requirement = {"objective_criteria": [], "subjective_criteria": [{"description": "tone", "weight": 1.0}]}
    verify_resp = test_client.post(
        "/internal/verify",
        json={
            "submission_id": "s1",
            "job_id": "b1",
            "agent_id": "agent1",
            "agent_developer_id": "dev1",
            "category": "content_media",
            "requirement": requirement,
            "payload": {},
            "job_amount_cents": 100,
        },
        headers=INTERNAL_HEADERS,
    )
    verdict_id = verify_resp.json()["id"]
    assert verify_resp.json()["final_result"] == "fail"

    dispute_resp = test_client.post(
        "/internal/disputes",
        json={"verdict_id": verdict_id, "raised_by": "dev1", "payload": {}, "requirement": requirement},
        headers=INTERNAL_HEADERS,
    )
    assert dispute_resp.status_code == 200
    dispute_id = dispute_resp.json()["id"]

    resolve_resp = test_client.post(
        f"/internal/disputes/{dispute_id}/resolve", json={"resolved_by": "ops-1"}, headers=INTERNAL_HEADERS
    )
    assert resolve_resp.json()["resolution"] == "overturned"

    final_verdict = test_client.get(f"/verdicts/{verdict_id}").json()
    assert final_verdict["final_result"] == "pass"
    assert escrow_client.release_calls == [("b1", "dev1")]


def test_get_unknown_dispute_returns_404(client):
    test_client, *_ = client
    resp = test_client.get("/disputes/does-not-exist")
    assert resp.status_code == 404
