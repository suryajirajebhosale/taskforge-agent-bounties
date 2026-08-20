from services.rubric_service.eval_harness import GoldenExample, evaluate_golden_set
from services.rubric_service.golden_dataset import GOLDEN_DATASET
from services.rubric_service.requirement import BountyCategory, ObjectiveCriterion, Requirement


class _ScriptedDrafter:
    """Returns per-category canned requirements, so the harness can be tested against
    both passing and failing scenarios deterministically."""

    def __init__(self, responses: dict[BountyCategory, Requirement]):
        self.responses = responses

    def draft(self, *, job_description, category, template):
        return self.responses[category]


def test_evaluate_golden_set_passes_when_expected_fields_are_covered():
    golden = [
        GoldenExample(
            description="find 100 leads", category=BountyCategory.SALES_LEAD_GENERATION, expected_objective_fields={"lead_count"}
        )
    ]
    drafter = _ScriptedDrafter(
        {
            BountyCategory.SALES_LEAD_GENERATION: Requirement(
                objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]
            )
        }
    )

    report = evaluate_golden_set(drafter, golden)

    assert report.pass_rate == 1.0
    assert report.failures == []


def test_evaluate_golden_set_flags_missing_expected_fields():
    golden = [
        GoldenExample(
            description="find 100 leads",
            category=BountyCategory.SALES_LEAD_GENERATION,
            expected_objective_fields={"lead_count", "contact_email"},
        )
    ]
    drafter = _ScriptedDrafter(
        {
            BountyCategory.SALES_LEAD_GENERATION: Requirement(
                objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]
            )
        }
    )

    report = evaluate_golden_set(drafter, golden)

    assert report.pass_rate == 0.0
    assert report.failures[0].missing_fields == {"contact_email"}


def test_evaluate_golden_set_records_a_drafting_error_as_a_failure_not_a_crash():
    class _BrokenDrafter:
        def draft(self, **kwargs):
            raise RuntimeError("model timeout")

    golden = [GoldenExample(description="x", category=BountyCategory.OTHER, expected_objective_fields=set())]

    report = evaluate_golden_set(_BrokenDrafter(), golden)

    assert report.failures[0].error == "model timeout"
    assert report.pass_rate == 0.0


def test_golden_dataset_covers_every_bounty_category_except_other():
    covered = {example.category for example in GOLDEN_DATASET}
    everything_but_other = {c for c in BountyCategory if c != BountyCategory.OTHER}
    assert everything_but_other.issubset(covered)
