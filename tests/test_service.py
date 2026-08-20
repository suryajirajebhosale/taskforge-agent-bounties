import pytest

from services.escrow_ledger.exceptions import HoldNotFound, InvalidHoldState
from services.escrow_ledger.models import HoldStatus, LedgerEntry


def test_fund_job_creates_a_held_escrow(service):
    hold = service.fund_job(job_id="b1", requester_id="req1", amount_cents=5_000)

    assert hold.status == HoldStatus.HELD
    assert hold.amount_cents == 5_000
    assert hold.stripe_payment_intent_id is not None


def test_funding_the_same_bounty_twice_is_idempotent(service, gateway):
    first = service.fund_job(job_id="b1", requester_id="req1", amount_cents=5_000)
    second = service.fund_job(job_id="b1", requester_id="req1", amount_cents=5_000)

    assert first.id == second.id
    # only one payment intent should exist for this bounty
    assert len(gateway._intents) == 1


def test_release_to_agent_pays_out_net_of_take_rate(service, db_session):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=10_000, take_rate_bps=1000)  # 10%

    payout = service.release_to_agent(job_id="b1", agent_developer_id="dev1")

    assert payout.amount_cents == 9_000  # 10,000 - 10% take
    assert payout.agent_developer_id == "dev1"

    hold = service._require_hold("b1")
    assert hold.status == HoldStatus.RELEASED


def test_release_writes_take_rate_and_payout_ledger_entries(service, db_session):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=10_000, take_rate_bps=1000)
    service.release_to_agent(job_id="b1", agent_developer_id="dev1")

    entries = db_session.query(LedgerEntry).filter_by(job_id="b1").all()
    accounts = {e.account: e.amount_cents for e in entries}

    assert accounts["platform:revenue"] == 1_000
    assert accounts["agent_developer:dev1"] == 9_000


def test_release_with_zero_take_rate_does_not_write_a_zero_revenue_entry(service, db_session):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=10_000, take_rate_bps=0)
    service.release_to_agent(job_id="b1", agent_developer_id="dev1")

    entries = db_session.query(LedgerEntry).filter_by(job_id="b1", account="platform:revenue").all()
    assert entries == []


def test_double_release_is_idempotent_not_duplicated(service, gateway):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=10_000)

    first = service.release_to_agent(job_id="b1", agent_developer_id="dev1")
    second = service.release_to_agent(job_id="b1", agent_developer_id="dev1")

    assert first.id == second.id
    assert len(gateway.list_transfers("b1")) == 1  # never called Stripe a second time


def test_refund_to_requester_returns_escrow(service):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=5_000)

    hold = service.refund_to_requester(job_id="b1")

    assert hold.status == HoldStatus.REFUNDED


def test_refund_writes_a_reversing_ledger_entry(service, db_session):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=5_000)
    service.refund_to_requester(job_id="b1")

    entries = db_session.query(LedgerEntry).filter_by(job_id="b1", account="requester:req1").all()
    credit_entries = [e for e in entries if e.entry_type.value == "credit"]
    assert sum(e.amount_cents for e in credit_entries) == 5_000


def test_double_refund_is_idempotent(service):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=5_000)

    first = service.refund_to_requester(job_id="b1")
    second = service.refund_to_requester(job_id="b1")

    assert first.status == second.status == HoldStatus.REFUNDED


def test_cannot_release_an_already_refunded_bounty(service):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=5_000)
    service.refund_to_requester(job_id="b1")

    with pytest.raises(InvalidHoldState):
        service.release_to_agent(job_id="b1", agent_developer_id="dev1")


def test_cannot_refund_an_already_released_bounty(service):
    service.fund_job(job_id="b1", requester_id="req1", amount_cents=5_000)
    service.release_to_agent(job_id="b1", agent_developer_id="dev1")

    with pytest.raises(InvalidHoldState):
        service.refund_to_requester(job_id="b1")


def test_release_on_unknown_bounty_raises_hold_not_found(service):
    with pytest.raises(HoldNotFound):
        service.release_to_agent(job_id="does-not-exist", agent_developer_id="dev1")


def test_refund_on_unknown_bounty_raises_hold_not_found(service):
    with pytest.raises(HoldNotFound):
        service.refund_to_requester(job_id="does-not-exist")
