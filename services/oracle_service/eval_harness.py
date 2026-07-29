"""Golden-set regression harness for the grading pipeline, per the Oracle Verification
Service PRD's Testing Decisions: a golden dataset of real (anonymized) past submissions
with known-correct verdicts, re-run on every prompt/rubric-template/model change, with
false-positive/false-negative rates tracked over time.

Running this against a live LLM judge (rather than the deterministic fakes this repo's
default `pytest` run uses) is a manual/CI-gated step needing real model credentials —
what's verified in this repo's own tests is that the harness itself computes accuracy/
FP/FN correctly. Wiring it to a live model with real credentials, and gating deploys on
a regression threshold, is a follow-up once the service has production traffic to build
a real golden dataset from.
"""

from dataclasses import dataclass

from packages.bounty_schemas.requirement import BountyCategory, Requirement

from .service import VerificationService


@dataclass(frozen=True)
class GoldenSubmission:
    description: str
    category: BountyCategory
    requirement: Requirement
    payload: dict
    bounty_amount_cents: int
    expected_pass: bool
    code_script: str | None = None


@dataclass(frozen=True)
class GoldenRunResult:
    golden: GoldenSubmission
    actual_pass: bool
    correct: bool
    is_false_positive: bool
    is_false_negative: bool


@dataclass(frozen=True)
class EvalReport:
    results: list[GoldenRunResult]

    @property
    def accuracy(self) -> float:
        if not self.results:
            return 1.0
        return sum(1 for r in self.results if r.correct) / len(self.results)

    @property
    def false_positive_rate(self) -> float:
        negatives = [r for r in self.results if not r.golden.expected_pass]
        if not negatives:
            return 0.0
        return sum(1 for r in negatives if r.is_false_positive) / len(negatives)

    @property
    def false_negative_rate(self) -> float:
        positives = [r for r in self.results if r.golden.expected_pass]
        if not positives:
            return 0.0
        return sum(1 for r in positives if r.is_false_negative) / len(positives)


def evaluate_golden_set(service: VerificationService, golden_set: list[GoldenSubmission]) -> EvalReport:
    """Grades every golden example through the real pipeline and compares against the
    known-correct label. `service` should have no `escrow_client`/`agent_platform_client`
    configured for eval runs — grading golden examples must never trigger real payouts."""
    results: list[GoldenRunResult] = []
    for golden in golden_set:
        verdict = service.grade_submission(
            submission_id=f"golden-{id(golden)}",
            bounty_id=f"golden-bounty-{id(golden)}",
            agent_id="golden-agent",
            agent_developer_id="golden-agent-developer",
            category=golden.category,
            requirement=golden.requirement,
            payload=golden.payload,
            bounty_amount_cents=golden.bounty_amount_cents,
            code_script=golden.code_script,
        )
        actual_pass = verdict.final_result.value == "pass"
        correct = actual_pass == golden.expected_pass
        results.append(
            GoldenRunResult(
                golden=golden,
                actual_pass=actual_pass,
                correct=correct,
                is_false_positive=actual_pass and not golden.expected_pass,
                is_false_negative=(not actual_pass) and golden.expected_pass,
            )
        )
    return EvalReport(results=results)
