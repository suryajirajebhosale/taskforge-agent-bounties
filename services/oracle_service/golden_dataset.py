"""Golden examples for the eval harness. These use objective-only requirements so the
default (LLM-free) `pytest` run can exercise the harness deterministically end to end —
see `eval_harness.py`'s module docstring for how this extends once real judged examples
with live model credentials are available."""

from packages.bounty_schemas.requirement import BountyCategory, ObjectiveCriterion, Requirement

from .eval_harness import GoldenSubmission

GOLDEN_DATASET: list[GoldenSubmission] = [
    GoldenSubmission(
        description="lead-gen: meets minimum count, should pass",
        category=BountyCategory.SALES_LEAD_GENERATION,
        requirement=Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]),
        payload={"lead_count": 120},
        bounty_amount_cents=2_000,
        expected_pass=True,
    ),
    GoldenSubmission(
        description="lead-gen: below minimum count, should fail",
        category=BountyCategory.SALES_LEAD_GENERATION,
        requirement=Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]),
        payload={"lead_count": 40},
        bounty_amount_cents=2_000,
        expected_pass=False,
    ),
    GoldenSubmission(
        description="lead-gen: missing required field, should fail",
        category=BountyCategory.SALES_LEAD_GENERATION,
        requirement=Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)]),
        payload={},
        bounty_amount_cents=2_000,
        expected_pass=False,
    ),
    GoldenSubmission(
        description="research: entry count exactly at threshold, should pass",
        category=BountyCategory.RESEARCH_COMPETITIVE_INTELLIGENCE,
        requirement=Requirement(objective_criteria=[ObjectiveCriterion(field="entry_count", comparator=">=", value=10)]),
        payload={"entry_count": 10},
        bounty_amount_cents=1_500,
        expected_pass=True,
    ),
]
