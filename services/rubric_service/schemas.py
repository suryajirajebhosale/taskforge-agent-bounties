from pydantic import BaseModel

from .models import BountyRequirementRecord
from .requirement import BountyCategory, Requirement


class GenerateDraftRequest(BaseModel):
    bounty_id: str
    bounty_description: str
    category: BountyCategory


class UpdateDraftRequest(BaseModel):
    requirement: Requirement


class RequirementRecordOut(BaseModel):
    bounty_id: str
    category: str
    requirement: Requirement
    status: str
    locked: bool

    @classmethod
    def from_record(cls, record: BountyRequirementRecord) -> "RequirementRecordOut":
        return cls(
            bounty_id=record.bounty_id,
            category=record.category,
            requirement=Requirement.model_validate(record.requirement_json),
            status=record.status.value,
            locked=record.locked,
        )
