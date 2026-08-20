from packages.bounty_schemas.requirement import BountyCategory, ObjectiveCriterion, Requirement
from services.oracle_service.eval_harness import GoldenSubmission, evaluate_golden_set
from services.oracle_service.golden_dataset import GOLDEN_DATASET


def test_evaluate_golden_set_reports_perfect_accuracy_when_pipeline_matches_labels(service):
    report = evaluate_golden_set(service, GOLDEN_DATASET)

    assert report.accuracy == 1.0
    assert report.false_positive_rate == 0.0
    assert report.false_negative_rate == 0.0


def test_evaluate_golden_set_flags_a_false_positive(service):
    golden = [
        GoldenSubmission(
            description="pipeline will pass this, but the label says it should have failed",
            category=BountyCategory.OTHER,
            requirement=Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=1)]),
            payload={"x": 5},
            job_amount_cents=1_000,
            expected_pass=False,
        )
    ]

    report = evaluate_golden_set(service, golden)

    assert report.accuracy == 0.0
    assert report.false_positive_rate == 1.0
    assert report.false_negative_rate == 0.0


def test_evaluate_golden_set_flags_a_false_negative(service):
    golden = [
        GoldenSubmission(
            description="pipeline will fail this, but the label says it should have passed",
            category=BountyCategory.OTHER,
            requirement=Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=100)]),
            payload={"x": 1},
            job_amount_cents=1_000,
            expected_pass=True,
        )
    ]

    report = evaluate_golden_set(service, golden)

    assert report.accuracy == 0.0
    assert report.false_negative_rate == 1.0
    assert report.false_positive_rate == 0.0


def test_golden_dataset_covers_both_pass_and_fail_expectations():
    expectations = {g.expected_pass for g in GOLDEN_DATASET}
    assert expectations == {True, False}
