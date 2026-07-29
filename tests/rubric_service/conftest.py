import pytest
from sqlalchemy.orm import Session

from services.rubric_service.database import Base, make_engine
from services.rubric_service.requirement import ObjectiveCriterion, Requirement, SubjectiveCriterion
from services.rubric_service.service import RubricGenerationService


class FakeRubricDrafter:
    """Returns a pre-set Requirement regardless of input (configurable per test), so
    the service's draft/update/approve/lock state machine can be tested without any
    LLM/LangChain involvement — the same role `FakeStripeGateway` plays for Escrow."""

    def __init__(self, requirement: Requirement | None = None):
        self.requirement = requirement or _default_requirement()
        self.calls: list[dict] = []

    def draft(self, *, bounty_description, category, template):
        self.calls.append({"bounty_description": bounty_description, "category": category, "template": template})
        return self.requirement


def _default_requirement() -> Requirement:
    return Requirement(
        objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)],
        subjective_criteria=[SubjectiveCriterion(description="leads match target market", weight=1.0)],
    )


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
def drafter():
    return FakeRubricDrafter()


@pytest.fixture
def service(db_session, drafter):
    return RubricGenerationService(session=db_session, drafter=drafter)
