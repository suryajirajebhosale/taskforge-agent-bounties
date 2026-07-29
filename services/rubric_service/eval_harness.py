"""Golden-set regression harness for rubric generation, per the Bounty Requirement/
Rubric Module PRD's Testing Decisions: a fixed set of example bounty descriptions with
expected structured-criteria shapes, re-run whenever the drafting prompt, category
templates, or model backend changes.

Running this against a *real* LLM backend (rather than the deterministic fakes this
repo's default `pytest` run uses) is a manual/CI-gated step that needs real model
credentials and is not part of the default test suite — what's verified here, in this
repo, is that the harness mechanism itself computes pass/fail and missing-field
reporting correctly. Wiring it to a live model with a real API key is a follow-up.
"""

from dataclasses import dataclass

from .category_templates import CATEGORY_TEMPLATES
from .drafter import RubricDrafter
from .requirement import BountyCategory


@dataclass(frozen=True)
class GoldenExample:
    """One golden dataset entry: a real bounty description and the minimum objective
    fields its generated Requirement is expected to cover. Not an exact-match check —
    LLM output isn't perfectly deterministic — just a floor the drafter must clear."""

    description: str
    category: BountyCategory
    expected_objective_fields: set[str]


@dataclass(frozen=True)
class GoldenResult:
    example: GoldenExample
    passed: bool
    missing_fields: set[str]
    error: str | None = None


@dataclass(frozen=True)
class EvalReport:
    results: list[GoldenResult]

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 1.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    @property
    def failures(self) -> list[GoldenResult]:
        return [r for r in self.results if not r.passed]


def evaluate_golden_set(drafter: RubricDrafter, golden_set: list[GoldenExample]) -> EvalReport:
    results: list[GoldenResult] = []
    for example in golden_set:
        template = CATEGORY_TEMPLATES[example.category]
        try:
            requirement = drafter.draft(
                bounty_description=example.description, category=example.category, template=template
            )
        except Exception as exc:  # noqa: BLE001 - a drafting failure is a failing result, not a harness crash
            results.append(GoldenResult(example=example, passed=False, missing_fields=set(), error=str(exc)))
            continue
        actual_fields = {c.field for c in requirement.objective_criteria}
        missing = example.expected_objective_fields - actual_fields
        results.append(GoldenResult(example=example, passed=not missing, missing_fields=missing))
    return EvalReport(results=results)
