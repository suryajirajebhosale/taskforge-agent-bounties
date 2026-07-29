from packages.bounty_schemas.requirement import ObjectiveCriterion
from services.oracle_service.deterministic_checker import run_deterministic_checks


def test_all_criteria_pass():
    criteria = [ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]
    result = run_deterministic_checks({"lead_count": 150}, criteria)
    assert result.passed
    assert result.failures == []


def test_criterion_fails_comparator():
    criteria = [ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]
    result = run_deterministic_checks({"lead_count": 50}, criteria)
    assert not result.passed
    assert "lead_count" in result.failures[0]


def test_missing_field_fails():
    criteria = [ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]
    result = run_deterministic_checks({}, criteria)
    assert not result.passed
    assert "missing field" in result.failures[0]


def test_multiple_criteria_all_checked():
    criteria = [
        ObjectiveCriterion(field="lead_count", comparator=">=", value=100),
        ObjectiveCriterion(field="company_name", comparator="==", value="Acme"),
    ]
    result = run_deterministic_checks({"lead_count": 200, "company_name": "Acme"}, criteria)
    assert result.passed


def test_no_criteria_always_passes():
    result = run_deterministic_checks({}, [])
    assert result.passed


def test_incomparable_types_fail_gracefully():
    criteria = [ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]
    result = run_deterministic_checks({"lead_count": "not a number"}, criteria)
    assert not result.passed
    assert "not comparable" in result.failures[0]


def test_equality_comparator():
    criteria = [ObjectiveCriterion(field="format", comparator="==", value="mp4")]
    assert run_deterministic_checks({"format": "mp4"}, criteria).passed
    assert not run_deterministic_checks({"format": "mov"}, criteria).passed


def test_not_equal_comparator():
    criteria = [ObjectiveCriterion(field="status", comparator="!=", value="rejected")]
    assert run_deterministic_checks({"status": "approved"}, criteria).passed
    assert not run_deterministic_checks({"status": "rejected"}, criteria).passed


def test_multiple_failures_are_all_reported():
    criteria = [
        ObjectiveCriterion(field="lead_count", comparator=">=", value=100),
        ObjectiveCriterion(field="company_name", comparator="==", value="Acme"),
    ]
    result = run_deterministic_checks({"lead_count": 1, "company_name": "Other"}, criteria)
    assert len(result.failures) == 2
