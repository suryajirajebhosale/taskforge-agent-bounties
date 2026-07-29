from sqlalchemy.orm import Session

from .category_templates import CATEGORY_TEMPLATES
from .drafter import RubricDrafter
from .exceptions import RequirementLocked, RequirementNotApproved, RequirementNotFound
from .models import BountyRequirementRecord, RequirementStatus
from .requirement import BountyCategory, Requirement


class RubricGenerationService:
    """Draft -> review/edit -> approve -> lock, for the structured acceptance criteria
    attached to a bounty. Locking happens once the bounty is funded (called by whatever
    orchestrates funding) and makes the Requirement immutable from then on, per the PRD."""

    def __init__(self, session: Session, drafter: RubricDrafter):
        self.session = session
        self.drafter = drafter

    def generate_draft(
        self, *, bounty_id: str, bounty_description: str, category: BountyCategory
    ) -> BountyRequirementRecord:
        existing = self._find(bounty_id)
        if existing is not None and existing.locked:
            raise RequirementLocked(f"requirement for bounty {bounty_id} is locked and can no longer be redrafted")

        template = CATEGORY_TEMPLATES[category]
        requirement = self.drafter.draft(bounty_description=bounty_description, category=category, template=template)

        if existing is None:
            existing = BountyRequirementRecord(bounty_id=bounty_id, category=category.value, requirement_json={})
            self.session.add(existing)
        existing.category = category.value
        existing.requirement_json = requirement.model_dump(mode="json")
        existing.status = RequirementStatus.DRAFT
        self.session.commit()
        return existing

    def update_draft(self, *, bounty_id: str, requirement: Requirement) -> BountyRequirementRecord:
        """A requester editing the generated draft before approval. Editing an already-
        approved (but not yet locked) requirement reopens it for review — approval
        always refers to the exact criteria currently on record."""
        record = self._require(bounty_id)
        if record.locked:
            raise RequirementLocked(f"requirement for bounty {bounty_id} is locked and can no longer be edited")
        record.requirement_json = requirement.model_dump(mode="json")
        record.status = RequirementStatus.DRAFT
        self.session.commit()
        return record

    def approve(self, *, bounty_id: str) -> BountyRequirementRecord:
        record = self._require(bounty_id)
        if record.locked:
            raise RequirementLocked(f"requirement for bounty {bounty_id} is already locked")
        record.status = RequirementStatus.APPROVED
        self.session.commit()
        return record

    def lock_for_funding(self, *, bounty_id: str) -> BountyRequirementRecord:
        """Called once escrow funds the bounty. Idempotent — funding notifications may
        be retried — but only an *approved* requirement may be locked in the first
        place, so a bounty can never be funded against criteria the requester never
        signed off on."""
        record = self._require(bounty_id)
        if record.locked:
            return record
        if record.status != RequirementStatus.APPROVED:
            raise RequirementNotApproved(
                f"requirement for bounty {bounty_id} must be approved before it can be locked"
            )
        record.locked = True
        self.session.commit()
        return record

    def get_requirement(self, bounty_id: str) -> Requirement:
        return Requirement.model_validate(self._require(bounty_id).requirement_json)

    def get_record(self, bounty_id: str) -> BountyRequirementRecord:
        return self._require(bounty_id)

    def _find(self, bounty_id: str) -> BountyRequirementRecord | None:
        return self.session.get(BountyRequirementRecord, bounty_id)

    def _require(self, bounty_id: str) -> BountyRequirementRecord:
        record = self._find(bounty_id)
        if record is None:
            raise RequirementNotFound(f"no requirement drafted for bounty {bounty_id}")
        return record
