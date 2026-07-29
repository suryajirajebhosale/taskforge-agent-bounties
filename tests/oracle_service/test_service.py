import pytest

from packages.bounty_schemas.requirement import BountyCategory, ObjectiveCriterion, Requirement, SubjectiveCriterion
from services.oracle_service.confidence_router import RoutingConfig
from services.oracle_service.exceptions import DisputeCaseNotFound, VerdictNotFound
from services.oracle_service.judge_agent import JudgeVerdict
from services.oracle_service.models import DisputeResolution, FinalResult
from services.oracle_service.sandbox_executor import SubprocessSandboxExecutor
from services.oracle_service.service import VerificationService


def test_objective_only_bounty_passes_without_invoking_the_judge(service, judge):
    requirement = Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)])

    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.SALES_LEAD_GENERATION,
        requirement=requirement,
        payload={"lead_count": 150},
        bounty_amount_cents=1_000,
    )

    assert verdict.final_result == FinalResult.PASS
    assert verdict.confidence == 1.0
    assert judge.calls == []


def test_objective_failure_short_circuits_before_the_judge_runs(service, judge):
    requirement = Requirement(
        objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)],
        subjective_criteria=[SubjectiveCriterion(description="quality", weight=1.0)],
    )

    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.SALES_LEAD_GENERATION,
        requirement=requirement,
        payload={"lead_count": 10},
        bounty_amount_cents=1_000,
    )

    assert verdict.final_result == FinalResult.FAIL
    assert verdict.confidence == 1.0
    assert judge.calls == []


def test_subjective_criteria_invoke_the_judge(service, judge):
    requirement = Requirement(subjective_criteria=[SubjectiveCriterion(description="tone", weight=1.0)])

    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.CONTENT_MEDIA,
        requirement=requirement,
        payload={},
        bounty_amount_cents=1_000,
    )

    assert len(judge.calls) == 1
    assert verdict.final_result == FinalResult.PASS  # FakeJudge default: passed=True


def test_judge_fail_produces_a_fail_verdict_with_its_own_confidence_and_rationale(service, judge):
    judge.verdict = JudgeVerdict(passed=False, confidence=0.6, rationale="tone is off")
    requirement = Requirement(subjective_criteria=[SubjectiveCriterion(description="tone", weight=1.0)])

    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.CONTENT_MEDIA,
        requirement=requirement,
        payload={},
        bounty_amount_cents=1_000,
    )

    assert verdict.final_result == FinalResult.FAIL
    assert verdict.confidence == 0.6
    assert verdict.rationale == "tone is off"


def test_high_confidence_verdict_auto_resolves_and_notifies_downstream(service, escrow_client, agent_platform_client):
    requirement = Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=1)])

    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={"x": 5},
        bounty_amount_cents=1_000,
    )

    assert verdict.resolved
    assert not verdict.routed_to_human
    assert agent_platform_client.record_calls == [("b1", "s1", True)]
    assert escrow_client.release_calls == [("b1", "dev1")]


def test_low_confidence_routes_to_human_and_skips_downstream_calls(service, judge, escrow_client, agent_platform_client):
    judge.verdict = JudgeVerdict(passed=True, confidence=0.3, rationale="uncertain")
    requirement = Requirement(subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)])

    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={},
        bounty_amount_cents=1_000,
    )

    assert not verdict.resolved
    assert verdict.routed_to_human
    assert agent_platform_client.record_calls == []
    assert escrow_client.release_calls == []


def test_high_value_bounty_routes_to_human_even_with_full_confidence(service, escrow_client):
    requirement = Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=1)])

    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="big-bounty",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={"x": 5},
        bounty_amount_cents=999_999_999,
    )

    assert not verdict.resolved
    assert verdict.routed_to_human
    assert escrow_client.release_calls == []


def test_failed_verdict_never_triggers_escrow_release(service, escrow_client, agent_platform_client):
    requirement = Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=100)])

    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={"x": 1},
        bounty_amount_cents=1_000,
    )

    assert verdict.final_result == FinalResult.FAIL
    assert verdict.resolved  # a deterministic fail is fully confident, so it still auto-resolves
    assert agent_platform_client.record_calls == [("b1", "s1", False)]
    assert escrow_client.release_calls == []


def test_human_review_resolves_a_routed_verdict_and_notifies_downstream(service, judge, escrow_client, agent_platform_client):
    judge.verdict = JudgeVerdict(passed=True, confidence=0.3, rationale="uncertain")
    requirement = Requirement(subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)])
    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={},
        bounty_amount_cents=1_000,
    )
    assert not verdict.resolved

    resolved = service.resolve_human_review(verdict_id=verdict.id, final_result=FinalResult.PASS, reviewer="ops-1")

    assert resolved.resolved
    assert resolved.final_result == FinalResult.PASS
    assert "ops-1" in resolved.rationale
    assert agent_platform_client.record_calls == [("b1", "s1", True)]
    assert escrow_client.release_calls == [("b1", "dev1")]


def test_human_review_for_unknown_verdict_raises(service):
    with pytest.raises(VerdictNotFound):
        service.resolve_human_review(verdict_id="nope", final_result=FinalResult.PASS, reviewer="ops-1")


def test_raise_dispute_creates_an_independent_regrade(service, dispute_judge):
    requirement = Requirement(subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)])
    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={},
        bounty_amount_cents=1_000,
    )

    service.raise_dispute(verdict_id=verdict.id, raised_by="dev1", payload={}, requirement=requirement)

    assert len(dispute_judge.calls) == 1
    assert dispute_judge.calls[0]["original_rationale"] == verdict.rationale


def test_raise_dispute_for_unknown_verdict_raises(service):
    requirement = Requirement(subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)])
    with pytest.raises(VerdictNotFound):
        service.raise_dispute(verdict_id="nope", raised_by="dev1", payload={}, requirement=requirement)


def test_dispute_overturns_a_verdict_when_the_regrade_disagrees(service, judge, dispute_judge, escrow_client, agent_platform_client):
    judge.verdict = JudgeVerdict(passed=False, confidence=0.9, rationale="failed")
    requirement = Requirement(subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)])
    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={},
        bounty_amount_cents=1_000,
    )
    assert verdict.final_result == FinalResult.FAIL

    dispute_judge.verdict = JudgeVerdict(passed=True, confidence=0.95, rationale="actually fine")
    dispute = service.raise_dispute(verdict_id=verdict.id, raised_by="dev1", payload={}, requirement=requirement)
    resolved_case = service.resolve_dispute(dispute_id=dispute.id, resolved_by="ops-1")

    assert resolved_case.resolution == DisputeResolution.OVERTURNED
    refreshed = service.get_verdict(verdict.id)
    assert refreshed.final_result == FinalResult.PASS
    assert agent_platform_client.record_calls[-1] == ("b1", "s1", True)
    assert escrow_client.release_calls == [("b1", "dev1")]


def test_dispute_upholds_a_verdict_when_the_regrade_agrees(service, judge, dispute_judge, escrow_client):
    judge.verdict = JudgeVerdict(passed=False, confidence=0.9, rationale="failed")
    requirement = Requirement(subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)])
    verdict = service.grade_submission(
        submission_id="s1",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev1",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={},
        bounty_amount_cents=1_000,
    )

    dispute_judge.verdict = JudgeVerdict(passed=False, confidence=0.85, rationale="agree, still fails")
    dispute = service.raise_dispute(verdict_id=verdict.id, raised_by="dev1", payload={}, requirement=requirement)
    resolved_case = service.resolve_dispute(dispute_id=dispute.id, resolved_by="ops-1")

    assert resolved_case.resolution == DisputeResolution.UPHELD
    refreshed = service.get_verdict(verdict.id)
    assert refreshed.final_result == FinalResult.FAIL
    assert escrow_client.release_calls == []


def test_resolve_dispute_for_unknown_case_raises(service):
    with pytest.raises(DisputeCaseNotFound):
        service.resolve_dispute(dispute_id="nope", resolved_by="ops-1")


def test_get_verdict_for_unknown_id_raises(service):
    with pytest.raises(VerdictNotFound):
        service.get_verdict("nope")


def test_get_dispute_for_unknown_id_raises(service):
    with pytest.raises(DisputeCaseNotFound):
        service.get_dispute("nope")


def test_escrow_is_not_released_when_agent_platform_reports_the_submission_as_moot(
    db_session, judge, dispute_judge, routing_config, escrow_client
):
    """In a competitive bounty, Oracle's own grading of a submission as a "pass" isn't
    enough — Agent Platform's first-verified-pass-wins bookkeeping is the authority on
    whether this submission is the actual, standing winner. If another submission
    already won by the time this one is graded, Agent Platform reports it moot, and
    escrow must never be released for it, however confident this particular verdict
    was on its own."""
    from tests.oracle_service.conftest import FakeAgentPlatformClient

    already_mooted_client = FakeAgentPlatformClient(record_verdict_response={"status": "moot"})
    service = VerificationService(
        session=db_session,
        judge=judge,
        dispute_judge=dispute_judge,
        routing_config=routing_config,
        sandbox=SubprocessSandboxExecutor(),
        escrow_client=escrow_client,
        agent_platform_client=already_mooted_client,
    )
    requirement = Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=1)])

    verdict = service.grade_submission(
        submission_id="s2",
        bounty_id="b1",
        agent_id="agent1",
        agent_developer_id="dev2",
        category=BountyCategory.OTHER,
        requirement=requirement,
        payload={"x": 5},
        bounty_amount_cents=1_000,
    )

    assert verdict.final_result == FinalResult.PASS  # Oracle's own grading did pass it
    assert already_mooted_client.record_calls == [("b1", "s2", True)]
    assert escrow_client.release_calls == []  # but Agent Platform says it's moot, so no payout
