import pytest
from sqlalchemy.orm import Session

from services.escrow_ledger.database import Base, make_engine
from services.escrow_ledger.gateways.fake import FakeStripeGateway
from services.escrow_ledger.service import EscrowLedgerService


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
def gateway():
    return FakeStripeGateway()


@pytest.fixture
def service(db_session, gateway):
    return EscrowLedgerService(session=db_session, gateway=gateway)
