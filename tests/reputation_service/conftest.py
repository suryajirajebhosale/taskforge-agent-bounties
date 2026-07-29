import pytest
from sqlalchemy.orm import Session

from services.reputation_service.database import Base, make_engine
from services.reputation_service.service import ReputationService


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
def service(db_session):
    return ReputationService(session=db_session, decay_alpha=0.3, weekly_prize_amount_cents=2_500, week_start_day=6)
