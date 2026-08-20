from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.reputation_service import main
from services.reputation_service.config import settings
from services.reputation_service.database import Base, make_engine
from services.reputation_service.period import week_key

INTERNAL_HEADERS = {"X-Internal-Api-Key": "reputation-test-secret"}


@pytest.fixture
def client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    settings.internal_api_key = "reputation-test-secret"

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


def test_record_outcome_and_get_rating_over_http(client):
    resp = client.post(
        "/internal/outcomes",
        json={"verdict_id": "v1", "agent_id": "a1", "agent_developer_id": "d1", "passed": True, "job_amount_cents": 100},
        headers=INTERNAL_HEADERS,
    )
    assert resp.status_code == 200

    rating_resp = client.get("/agents/a1/rating")
    assert rating_resp.status_code == 200
    assert rating_resp.json()["rating"] == 5.0
    assert rating_resp.json()["verified_count"] == 1


def test_record_outcome_without_internal_key_is_rejected(client):
    resp = client.post(
        "/internal/outcomes",
        json={"verdict_id": "v1", "agent_id": "a1", "agent_developer_id": "d1", "passed": True, "job_amount_cents": 100},
    )
    assert resp.status_code == 401


def test_correct_outcome_over_http(client):
    client.post(
        "/internal/outcomes",
        json={"verdict_id": "v1", "agent_id": "a1", "agent_developer_id": "d1", "passed": True, "job_amount_cents": 100},
        headers=INTERNAL_HEADERS,
    )

    resp = client.post(
        "/internal/outcomes/v1/correct",
        json={"agent_id": "a1", "agent_developer_id": "d1", "passed": False, "job_amount_cents": 100},
        headers=INTERNAL_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is False

    rating_resp = client.get("/agents/a1/rating")
    assert rating_resp.json()["rating"] == 0.0


def test_leaderboard_endpoint(client):
    client.post(
        "/internal/outcomes",
        json={"verdict_id": "v1", "agent_id": "a1", "agent_developer_id": "d1", "passed": True, "job_amount_cents": 500},
        headers=INTERNAL_HEADERS,
    )

    resp = client.get("/leaderboard?period=all_time")

    assert resp.status_code == 200
    assert resp.json()[0]["agent_id"] == "a1"


def test_leaderboard_rejects_bad_period(client):
    resp = client.get("/leaderboard?period=nonsense")
    assert resp.status_code == 400


def test_finalize_and_pay_weekly_prize_over_http(client):
    client.post(
        "/internal/outcomes",
        json={"verdict_id": "v1", "agent_id": "a1", "agent_developer_id": "d1", "passed": True, "job_amount_cents": 500},
        headers=INTERNAL_HEADERS,
    )
    period = week_key(datetime.now(timezone.utc), week_start_day=settings.week_start_day)

    finalize_resp = client.post("/internal/weekly-prize/finalize", json={"period_key": period}, headers=INTERNAL_HEADERS)
    assert finalize_resp.status_code == 200
    assert finalize_resp.json()["winner_agent_developer_id"] == "d1"

    get_resp = client.get(f"/weekly-prize/{period}")
    assert get_resp.status_code == 200

    pay_resp = client.post(f"/internal/weekly-prize/{period}/mark-paid", headers=INTERNAL_HEADERS)
    assert pay_resp.status_code == 200
    assert pay_resp.json()["paid_at"] is not None


def test_get_unknown_weekly_prize_returns_404(client):
    resp = client.get("/weekly-prize/does-not-exist")
    assert resp.status_code == 404


def test_get_unknown_outcome_returns_404(client):
    resp = client.get("/internal/outcomes/nope", headers=INTERNAL_HEADERS)
    assert resp.status_code == 404
