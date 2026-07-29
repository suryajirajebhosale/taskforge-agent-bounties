import pytest

from services.agent_platform.exceptions import SubmissionNotFound
from services.agent_platform.models import SubmissionStatus

SCHEMA: dict[str, str] = {}


def _submit(service, category, bounty_id, agent):
    service.notify_bounty_funded(bounty_id=bounty_id, category=category, objective_schema=SCHEMA)
    return service.submit(bounty_id=bounty_id, agent_id=agent.id, payload={})


def test_first_pass_marks_other_pending_submissions_moot(service, make_agent):
    winner_agent, _, _ = make_agent(email="w@example.com", name="Winner", categories=["lead_generation"])
    loser_agent, _, _ = make_agent(email="l@example.com", name="Loser", categories=["lead_generation"])

    winning_submission = _submit(service, "lead_generation", "b1", winner_agent)
    losing_submission = _submit(service, "lead_generation", "b1", loser_agent)

    service.record_verdict(bounty_id="b1", submission_id=winning_submission.id, passed=True)

    refreshed_loser = service.session.get(type(losing_submission), losing_submission.id)
    assert refreshed_loser.status == SubmissionStatus.MOOT


def test_late_arriving_pass_after_winner_is_marked_moot(service, make_agent):
    winner_agent, _, _ = make_agent(email="w@example.com", name="Winner", categories=["lead_generation"])
    latecomer_agent, _, _ = make_agent(email="l@example.com", name="Latecomer", categories=["lead_generation"])

    winning_submission = _submit(service, "lead_generation", "b1", winner_agent)
    late_submission = _submit(service, "lead_generation", "b1", latecomer_agent)

    service.record_verdict(bounty_id="b1", submission_id=winning_submission.id, passed=True)
    # the late submission also happens to pass grading, but a winner already exists
    result = service.record_verdict(bounty_id="b1", submission_id=late_submission.id, passed=True)

    assert result.status == SubmissionStatus.MOOT


def test_fail_verdict_does_not_moot_other_submissions(service, make_agent):
    agent_a, _, _ = make_agent(email="a@example.com", name="A", categories=["lead_generation"])
    agent_b, _, _ = make_agent(email="b@example.com", name="B", categories=["lead_generation"])

    submission_a = _submit(service, "lead_generation", "b1", agent_a)
    submission_b = _submit(service, "lead_generation", "b1", agent_b)

    service.record_verdict(bounty_id="b1", submission_id=submission_a.id, passed=False)

    refreshed_a = service.session.get(type(submission_a), submission_a.id)
    refreshed_b = service.session.get(type(submission_b), submission_b.id)
    assert refreshed_a.status == SubmissionStatus.GRADED
    assert refreshed_a.passed is False
    assert refreshed_b.status == SubmissionStatus.QUEUED_FOR_GRADING  # untouched


def test_record_verdict_for_unknown_submission_raises(service):
    with pytest.raises(SubmissionNotFound):
        service.record_verdict(bounty_id="b1", submission_id="does-not-exist", passed=True)


def test_replaying_the_winning_verdict_is_idempotent(service, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"])
    submission = _submit(service, "lead_generation", "b1", agent)

    first = service.record_verdict(bounty_id="b1", submission_id=submission.id, passed=True)
    second = service.record_verdict(bounty_id="b1", submission_id=submission.id, passed=True)

    assert first.status == second.status == SubmissionStatus.GRADED
    assert second.passed is True
