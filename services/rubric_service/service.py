from sqlalchemy.orm import Session

from .category_templates import CATEGORY_TEMPLATES
from .drafter import RubricDrafter
from .exceptions import RequirementLocked, RequirementNotApproved, RequirementNotFound
from .models import JobRequirementRecord, RequirementStatus
from .requirement import BountyCategory, Requirement


class RubricGenerationService:
    """Draft -> review/edit -> approve -> lock, for the structured acceptance criteria
    attached to a bounty. Locking happens once the bounty is funded (called by whatever
    orchestrates funding) and makes the Requirement immutable from then on, per the PRD."""

    def __init__(self, session: Session, drafter: RubricDrafter):
        self.session = session
        self.drafter = drafter

    def generate_draft(
        self, *, job_id: str, job_description: str, category: BountyCategory
    ) -> JobRequirementRecord:
        existing = self._find(job_id)
        if existing is not None and existing.locked:
            raise RequirementLocked(f"requirement for bounty {job_id} is locked and can no longer be redrafted")

        template = CATEGORY_TEMPLATES[category]
        requirement = self.drafter.draft(job_description=job_description, category=category, template=template)

        if existing is None:
            existing = JobRequirementRecord(job_id=job_id, category=category.value, requirement_json={})
            self.session.add(existing)
        existing.category = category.value
        existing.requirement_json = requirement.model_dump(mode="json")
        existing.status = RequirementStatus.DRAFT
        self.session.commit()
        return existing

    def update_draft(self, *, job_id: str, requirement: Requirement) -> JobRequirementRecord:
        """A requester editing the generated draft before approval. Editing an already-
        approved (but not yet locked) requirement reopens it for review — approval
        always refers to the exact criteria currently on record."""
        record = self._require(job_id)
        if record.locked:
            raise RequirementLocked(f"requirement for bounty {job_id} is locked and can no longer be edited")
        record.requirement_json = requirement.model_dump(mode="json")
        record.status = RequirementStatus.DRAFT
        self.session.commit()
        return record

    def approve(self, *, job_id: str) -> JobRequirementRecord:
        record = self._require(job_id)
        if record.locked:
            raise RequirementLocked(f"requirement for bounty {job_id} is already locked")
        record.status = RequirementStatus.APPROVED
        self.session.commit()
        return record

    def lock_for_funding(self, *, job_id: str) -> JobRequirementRecord:
        """Called once escrow funds the bounty. Idempotent — funding notifications may
        be retried — but only an *approved* requirement may be locked in the first
        place, so a bounty can never be funded against criteria the requester never
        signed off on."""
        record = self._require(job_id)
        if record.locked:
            return record
        if record.status != RequirementStatus.APPROVED:
            raise RequirementNotApproved(
                f"requirement for bounty {job_id} must be approved before it can be locked"
            )
        record.locked = True
        self.session.commit()
        return record

    def get_requirement(self, job_id: str) -> Requirement:
        return Requirement.model_validate(self._require(job_id).requirement_json)

    def get_record(self, job_id: str) -> JobRequirementRecord:
        return self._require(job_id)

    def _find(self, job_id: str) -> JobRequirementRecord | None:
        return self.session.get(JobRequirementRecord, job_id)

    def _require(self, job_id: str) -> JobRequirementRecord:
        record = self._find(job_id)
        if record is None:
            raise RequirementNotFound(f"no requirement drafted for bounty {job_id}")
        return record
