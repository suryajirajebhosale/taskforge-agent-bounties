from pydantic import BaseModel

from .models import JobRequirementRecord
from .requirement import BountyCategory, Requirement


class GenerateDraftRequest(BaseModel):
    job_id: str
    job_description: str
    category: BountyCategory


class UpdateDraftRequest(BaseModel):
    requirement: Requirement


class RequirementRecordOut(BaseModel):
    job_id: str
    category: str
    requirement: Requirement
    status: str
    locked: bool

    @classmethod
    def from_record(cls, record: JobRequirementRecord) -> "RequirementRecordOut":
        return cls(
            job_id=record.job_id,
            category=record.category,
            requirement=Requirement.model_validate(record.requirement_json),
            status=record.status.value,
            locked=record.locked,
        )
