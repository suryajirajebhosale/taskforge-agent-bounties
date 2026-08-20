from services.escrow_ledger.exceptions import InvalidHoldState


def test_purchase_and_charge_run_credits(service):
    account = service.purchase_credits(company_id="co-1", credits=100)
    assert account.balance_credits == 100
    service.charge_run_credits(company_id="co-1", job_id="j1", grading_credits=10, labor_credits=40)
    assert service._credit_account("co-1").balance_credits == 50
    service.release_labor_credits_on_fail(company_id="co-1", job_id="j1", labor_credits=40)
    assert service._credit_account("co-1").balance_credits == 90


def test_charge_run_credits_rejects_insufficient_balance(service):
    service.purchase_credits(company_id="co-2", credits=5)
    try:
        service.charge_run_credits(company_id="co-2", job_id="j2", grading_credits=10, labor_credits=40)
        raise AssertionError("expected InvalidHoldState")
    except InvalidHoldState:
        pass
