import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.rubric_service import main
from services.rubric_service.config import settings
from services.rubric_service.database import Base, make_engine

from .conftest import FakeRubricDrafter


@pytest.fixture
def client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    settings.internal_api_key = "rubric-test-secret"
    drafter = FakeRubricDrafter()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    def override_get_drafter():
        return drafter

    main.app.dependency_overrides[main.get_db] = override_get_db
    main.app.dependency_overrides[main.get_drafter] = override_get_drafter
    try:
        yield TestClient(main.app)
    finally:
        main.app.dependency_overrides.clear()


INTERNAL_HEADERS = {"X-Internal-Api-Key": "rubric-test-secret"}


def test_draft_approve_lock_flow_over_http(client):
    draft_resp = client.post(
        "/rubrics/draft",
        json={"bounty_id": "b1", "bounty_description": "find 100 leads", "category": "sales_lead_generation"},
    )
    assert draft_resp.status_code == 200
    assert draft_resp.json()["status"] == "draft"
    assert draft_resp.json()["locked"] is False

    get_resp = client.get("/rubrics/b1")
    assert get_resp.status_code == 200
    assert get_resp.json()["requirement"]["objective_criteria"][0]["field"] == "lead_count"

    approve_resp = client.post("/rubrics/b1/approve")
    assert approve_resp.json()["status"] == "approved"

    lock_resp = client.post(f"/internal/rubrics/b1/lock", headers=INTERNAL_HEADERS)
    assert lock_resp.status_code == 200
    assert lock_resp.json()["locked"] is True


def test_lock_without_approval_returns_409(client):
    client.post(
        "/rubrics/draft", json={"bounty_id": "b1", "bounty_description": "find leads", "category": "sales_lead_generation"}
    )

    resp = client.post("/internal/rubrics/b1/lock", headers=INTERNAL_HEADERS)
    assert resp.status_code == 409


def test_lock_without_internal_key_is_rejected(client):
    client.post(
        "/rubrics/draft", json={"bounty_id": "b1", "bounty_description": "find leads", "category": "sales_lead_generation"}
    )
    client.post("/rubrics/b1/approve")

    resp = client.post("/internal/rubrics/b1/lock")
    assert resp.status_code == 401


def test_update_after_lock_returns_409(client):
    client.post(
        "/rubrics/draft", json={"bounty_id": "b1", "bounty_description": "find leads", "category": "sales_lead_generation"}
    )
    client.post("/rubrics/b1/approve")
    client.post("/internal/rubrics/b1/lock", headers=INTERNAL_HEADERS)

    resp = client.put(
        "/rubrics/b1",
        json={"requirement": {"objective_criteria": [{"field": "x", "comparator": ">=", "value": 1}], "subjective_criteria": []}},
    )
    assert resp.status_code == 409


def test_get_unknown_bounty_returns_404(client):
    resp = client.get("/rubrics/does-not-exist")
    assert resp.status_code == 404
