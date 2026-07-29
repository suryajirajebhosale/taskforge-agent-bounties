import pytest

from services.rubric_service.exceptions import RequirementLocked, RequirementNotApproved, RequirementNotFound
from services.rubric_service.models import RequirementStatus
from services.rubric_service.requirement import BountyCategory, ObjectiveCriterion, Requirement

CATEGORY = BountyCategory.SALES_LEAD_GENERATION


def test_generate_draft_creates_a_draft_record(service):
    record = service.generate_draft(bounty_id="b1", bounty_description="find leads", category=CATEGORY)
    assert record.status == RequirementStatus.DRAFT
    assert record.locked is False


def test_generate_draft_passes_the_category_template_to_the_drafter(service, drafter):
    service.generate_draft(bounty_id="b1", bounty_description="find leads", category=CATEGORY)
    assert drafter.calls[0]["category"] == CATEGORY


def test_regenerating_a_draft_overwrites_the_previous_one(service, drafter):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    new_requirement = Requirement(objective_criteria=[ObjectiveCriterion(field="different_field", comparator=">=", value=1)])
    drafter.requirement = new_requirement

    service.generate_draft(bounty_id="b1", bounty_description="v2", category=CATEGORY)

    assert service.get_requirement("b1") == new_requirement


def test_update_draft_replaces_the_requirement(service):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    edited = Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=999)])

    service.update_draft(bounty_id="b1", requirement=edited)

    assert service.get_requirement("b1") == edited


def test_update_draft_for_unknown_bounty_raises(service):
    edited = Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=1)])
    with pytest.raises(RequirementNotFound):
        service.update_draft(bounty_id="nope", requirement=edited)


def test_approve_transitions_status(service):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    record = service.approve(bounty_id="b1")
    assert record.status == RequirementStatus.APPROVED


def test_approve_unknown_bounty_raises(service):
    with pytest.raises(RequirementNotFound):
        service.approve(bounty_id="nope")


def test_lock_requires_approval_first(service):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    with pytest.raises(RequirementNotApproved):
        service.lock_for_funding(bounty_id="b1")


def test_lock_succeeds_after_approval(service):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    service.approve(bounty_id="b1")

    record = service.lock_for_funding(bounty_id="b1")

    assert record.locked is True


def test_lock_is_idempotent(service):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    service.approve(bounty_id="b1")

    first = service.lock_for_funding(bounty_id="b1")
    second = service.lock_for_funding(bounty_id="b1")

    assert first.locked is True
    assert second.locked is True


def test_locked_requirement_cannot_be_edited(service):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    service.approve(bounty_id="b1")
    service.lock_for_funding(bounty_id="b1")
    edited = Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=1)])

    with pytest.raises(RequirementLocked):
        service.update_draft(bounty_id="b1", requirement=edited)


def test_locked_requirement_cannot_be_redrafted(service):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    service.approve(bounty_id="b1")
    service.lock_for_funding(bounty_id="b1")

    with pytest.raises(RequirementLocked):
        service.generate_draft(bounty_id="b1", bounty_description="v2", category=CATEGORY)


def test_locked_requirement_cannot_be_reapproved(service):
    service.generate_draft(bounty_id="b1", bounty_description="v1", category=CATEGORY)
    service.approve(bounty_id="b1")
    service.lock_for_funding(bounty_id="b1")

    with pytest.raises(RequirementLocked):
        service.approve(bounty_id="b1")


def test_get_requirement_for_unknown_bounty_raises(service):
    with pytest.raises(RequirementNotFound):
        service.get_requirement("nope")
