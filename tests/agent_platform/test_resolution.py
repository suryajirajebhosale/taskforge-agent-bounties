import pytest

from services.agent_platform.exceptions import SubmissionNotFound
from services.agent_platform.models import SubmissionStatus

SCHEMA: dict[str, str] = {}


def _submit(service, category, job_id, agent):
    service.notify_job_funded(job_id=job_id, agent_id=agent.id, category=category, objective_schema=SCHEMA)
    return service.submit(job_id=job_id, agent_id=agent.id, payload={})


def test_only_the_assigned_agent_can_submit(service, make_agent):
    winner_agent, _, _ = make_agent(email="w@example.com", name="Winner", categories=["lead_generation"])
    other, _, _ = make_agent(email="l@example.com", name="Other", categories=["lead_generation"])
    service.notify_job_funded(job_id="b1", agent_id=winner_agent.id, category="lead_generation", objective_schema=SCHEMA)

    from services.agent_platform.exceptions import NotAssignedToJob
    import pytest

    with pytest.raises(NotAssignedToJob):
        service.submit(job_id="b1", agent_id=other.id, payload={})


def test_fail_verdict_grades_the_assigned_submission(service, make_agent):
    agent_a, _, _ = make_agent(email="a@example.com", name="A", categories=["lead_generation"])
    submission_a = _submit(service, "lead_generation", "b1", agent_a)
    service.record_verdict(job_id="b1", submission_id=submission_a.id, passed=False)
    refreshed_a = service.session.get(type(submission_a), submission_a.id)
    assert refreshed_a.status == SubmissionStatus.GRADED
    assert refreshed_a.passed is False


def test_record_verdict_for_unknown_submission_raises(service):
    with pytest.raises(SubmissionNotFound):
        service.record_verdict(job_id="b1", submission_id="does-not-exist", passed=True)


def test_replaying_the_winning_verdict_is_idempotent(service, make_agent):
    agent, _, _ = make_agent(categories=["lead_generation"])
    submission = _submit(service, "lead_generation", "b1", agent)

    first = service.record_verdict(job_id="b1", submission_id=submission.id, passed=True)
    second = service.record_verdict(job_id="b1", submission_id=submission.id, passed=True)

    assert first.status == second.status == SubmissionStatus.GRADED
    assert second.passed is True
