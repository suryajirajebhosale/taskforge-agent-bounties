"""Smoke tests: does each service actually boot against a real (file-backed, not
in-memory) database and answer a request? These exist to catch wiring problems that
purely in-memory unit tests can mask — e.g. a db_admin script that silently no-ops, or
an app that only works because a fixture built its schema a different way than
production would."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_escrow_ledger_service_boots_against_a_real_db_file(tmp_path):
    from services.escrow_ledger import db_admin, main
    from services.escrow_ledger.database import make_engine

    db_path = tmp_path / "escrow_smoke.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)
    assert db_path.exists()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    try:
        client = TestClient(main.app)
        resp = client.get("/health")
    finally:
        main.app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "escrow_ledger"}


def test_agent_platform_service_boots_against_a_real_db_file(tmp_path):
    from services.agent_platform import db_admin, main
    from services.agent_platform.database import make_engine

    db_path = tmp_path / "agent_platform_smoke.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)
    assert db_path.exists()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    try:
        client = TestClient(main.app)
        resp = client.get("/health")
    finally:
        main.app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "agent_platform"}


def test_rubric_service_boots_against_a_real_db_file(tmp_path):
    from services.rubric_service import db_admin, main
    from services.rubric_service.database import make_engine

    db_path = tmp_path / "rubric_service_smoke.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)
    assert db_path.exists()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    try:
        client = TestClient(main.app)
        resp = client.get("/health")
    finally:
        main.app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "rubric_service"}


def test_oracle_service_boots_against_a_real_db_file(tmp_path):
    from services.oracle_service import db_admin, main
    from services.oracle_service.database import make_engine

    db_path = tmp_path / "oracle_service_smoke.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)
    assert db_path.exists()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    try:
        client = TestClient(main.app)
        resp = client.get("/health")
    finally:
        main.app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "oracle_service"}


def test_reputation_service_boots_against_a_real_db_file(tmp_path):
    from services.reputation_service import db_admin, main
    from services.reputation_service.database import make_engine

    db_path = tmp_path / "reputation_service_smoke.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)
    assert db_path.exists()

    def override_get_db():
        session = Session(bind=engine)
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    try:
        client = TestClient(main.app)
        resp = client.get("/health")
    finally:
        main.app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "reputation_service"}


def test_escrow_ledger_service_can_actually_fund_a_bounty_against_the_real_db_file(tmp_path):
    """Goes one step further than a bare health check: proves the schema created by
    db_admin is actually usable for a real write, not just present."""
    from services.escrow_ledger import db_admin
    from services.escrow_ledger.database import make_engine
    from services.escrow_ledger.gateways.fake import FakeStripeGateway
    from services.escrow_ledger.service import EscrowLedgerService

    db_path = tmp_path / "escrow_smoke_write.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)

    session = Session(bind=engine)
    service = EscrowLedgerService(session=session, gateway=FakeStripeGateway())
    hold = service.fund_bounty(bounty_id="smoke-1", requester_id="req1", amount_cents=1_000)

    assert hold.status.value == "held"
    session.close()


def test_rubric_service_can_actually_draft_a_requirement_against_the_real_db_file(tmp_path):
    from services.rubric_service import db_admin
    from services.rubric_service.database import make_engine
    from services.rubric_service.requirement import BountyCategory
    from services.rubric_service.service import RubricGenerationService

    db_path = tmp_path / "rubric_smoke_write.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)

    session = Session(bind=engine)

    class _FakeDrafter:
        def draft(self, *, bounty_description, category, template):
            from services.rubric_service.requirement import ObjectiveCriterion, Requirement

            return Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)])

    service = RubricGenerationService(session=session, drafter=_FakeDrafter())
    record = service.generate_draft(
        bounty_id="smoke-1", bounty_description="find leads", category=BountyCategory.SALES_LEAD_GENERATION
    )

    assert record.status.value == "draft"
    session.close()


def test_oracle_service_can_actually_grade_a_submission_against_the_real_db_file(tmp_path):
    from packages.bounty_schemas.requirement import BountyCategory, ObjectiveCriterion, Requirement
    from services.oracle_service import db_admin
    from services.oracle_service.confidence_router import RoutingConfig
    from services.oracle_service.database import make_engine
    from services.oracle_service.service import VerificationService

    db_path = tmp_path / "oracle_smoke_write.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)

    session = Session(bind=engine)

    class _UnusedJudge:
        def grade(self, **kwargs):
            raise AssertionError("objective-only requirement should never invoke the judge")

    service = VerificationService(
        session=session,
        judge=_UnusedJudge(),
        dispute_judge=_UnusedJudge(),
        routing_config=RoutingConfig(confidence_threshold=0.8, auto_resolve_amount_cents_ceiling=100_000),
    )
    verdict = service.grade_submission(
        submission_id="smoke-1",
        bounty_id="smoke-bounty-1",
        agent_id="agent1",
        agent_developer_id="smoke-dev-1",
        category=BountyCategory.SALES_LEAD_GENERATION,
        requirement=Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]),
        payload={"lead_count": 150},
        bounty_amount_cents=1_000,
    )

    assert verdict.final_result.value == "pass"
    session.close()


def test_reputation_service_can_actually_record_an_outcome_against_the_real_db_file(tmp_path):
    from services.reputation_service import db_admin
    from services.reputation_service.database import make_engine
    from services.reputation_service.service import ReputationService

    db_path = tmp_path / "reputation_smoke_write.db"
    engine = make_engine(f"sqlite:///{db_path}")
    db_admin.create_all(engine)

    session = Session(bind=engine)
    service = ReputationService(session=session, decay_alpha=0.3, weekly_prize_amount_cents=2_500, week_start_day=6)
    service.record_outcome(
        verdict_id="smoke-1", agent_id="smoke-agent-1", agent_developer_id="smoke-dev-1", passed=True, bounty_amount_cents=500
    )

    assert service.get_rating("smoke-agent-1") == 5.0
    session.close()
