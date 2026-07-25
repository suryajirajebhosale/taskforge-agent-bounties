from services.escrow_ledger.gateways.base import TransferRef


def test_reconcile_reports_no_mismatch_when_ledger_matches_stripe(service):
    service.fund_bounty(bounty_id="b1", requester_id="req1", amount_cents=10_000, take_rate_bps=1000)
    service.release_to_agent(bounty_id="b1", agent_developer_id="dev1")

    report = service.reconcile(["b1"])

    assert report.clean
    assert report.mismatches == []


def test_reconcile_flags_a_mismatch_instead_of_fixing_it(service, gateway, db_session):
    service.fund_bounty(bounty_id="b1", requester_id="req1", amount_cents=10_000, take_rate_bps=1000)
    service.release_to_agent(bounty_id="b1", agent_developer_id="dev1")

    # Simulate Stripe's records disagreeing with ours (e.g. a manual adjustment on
    # Stripe's side that our internal ledger doesn't know about).
    gateway._transfers["b1"].append(
        TransferRef(id="tr_manual_adjustment", destination_account_id="dev1", amount_cents=500, status="paid")
    )

    report = service.reconcile(["b1"])

    assert not report.clean
    assert len(report.mismatches) == 1
    mismatch = report.mismatches[0]
    assert mismatch.bounty_id == "b1"
    assert mismatch.internal_amount_cents == 9_000
    assert mismatch.stripe_amount_cents == 9_500

    # Reconciliation must not have silently "corrected" our records.
    from services.escrow_ledger.models import PayoutTransfer

    payouts = db_session.query(PayoutTransfer).filter_by(bounty_id="b1").all()
    assert sum(p.amount_cents for p in payouts) == 9_000


def test_reconcile_handles_multiple_bounties_independently(service):
    service.fund_bounty(bounty_id="b1", requester_id="req1", amount_cents=10_000)
    service.release_to_agent(bounty_id="b1", agent_developer_id="dev1")
    service.fund_bounty(bounty_id="b2", requester_id="req2", amount_cents=2_000)
    service.release_to_agent(bounty_id="b2", agent_developer_id="dev2")

    report = service.reconcile(["b1", "b2"])

    assert report.clean
    assert set(report.checked_bounty_ids) == {"b1", "b2"}
