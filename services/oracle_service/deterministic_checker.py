from dataclasses import dataclass

from packages.bounty_schemas.requirement import ObjectiveCriterion

_COMPARATORS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "!=": lambda a, b: a != b,
}


@dataclass(frozen=True)
class DeterministicCheckResult:
    passed: bool
    failures: list[str]


def run_deterministic_checks(payload: dict, objective_criteria: list[ObjectiveCriterion]) -> DeterministicCheckResult:
    """Evaluates each objective criterion against the submission payload directly —
    field presence, then its comparator against the target value. No LLM involvement:
    per the PRD's testing guidance, this stage's tests use exact-match assertions, not
    accuracy/calibration thresholds."""
    failures: list[str] = []
    for criterion in objective_criteria:
        if criterion.field not in payload:
            failures.append(f"missing field '{criterion.field}'")
            continue
        actual = payload[criterion.field]
        comparator = _COMPARATORS[criterion.comparator]
        try:
            ok = comparator(actual, criterion.value)
        except TypeError:
            failures.append(
                f"field '{criterion.field}' value {actual!r} is not comparable with "
                f"{criterion.comparator} {criterion.value!r}"
            )
            continue
        if not ok:
            failures.append(f"field '{criterion.field}' = {actual!r} fails {criterion.comparator} {criterion.value!r}")
    return DeterministicCheckResult(passed=not failures, failures=failures)
