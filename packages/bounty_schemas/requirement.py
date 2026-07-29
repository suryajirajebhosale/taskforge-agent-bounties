import enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BountyCategory(str, enum.Enum):
    SALES_LEAD_GENERATION = "sales_lead_generation"
    RESEARCH_COMPETITIVE_INTELLIGENCE = "research_competitive_intelligence"
    AI_AUTOMATION_PRODUCT_BUILDING = "ai_automation_product_building"
    HIRING_RECRUITING = "hiring_recruiting"
    CONTENT_MEDIA = "content_media"
    OTHER = "other"


Comparator = Literal[">=", "<=", "==", ">", "<", "!="]


class ObjectiveCriterion(BaseModel):
    field: str
    comparator: Comparator
    value: int | float | str | bool


class SubjectiveCriterion(BaseModel):
    description: str
    weight: float = Field(gt=0, le=1)


class Requirement(BaseModel):
    """The structured, machine-checkable definition of "done" for a bounty. Produced as
    a draft by the Rubric Module's `RubricAgent`, then reviewed/edited and approved by
    the requester before a bounty can be funded. Consumed in full (both objective and
    subjective criteria) by the Oracle Verification Service's grading pipeline — the
    reason this lives in a shared package rather than inside the Rubric Module itself,
    so both services depend on one authoritative definition instead of drifting copies."""

    objective_criteria: list[ObjectiveCriterion] = Field(default_factory=list)
    subjective_criteria: list[SubjectiveCriterion] = Field(default_factory=list)

    @model_validator(mode="after")
    def _at_least_one_criterion(self) -> "Requirement":
        if not self.objective_criteria and not self.subjective_criteria:
            raise ValueError("a Requirement must have at least one objective or subjective criterion")
        return self

    @model_validator(mode="after")
    def _subjective_weights_sum_to_one(self) -> "Requirement":
        if self.subjective_criteria:
            total = sum(c.weight for c in self.subjective_criteria)
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"subjective_criteria weights must sum to 1.0, got {total}")
        return self

    def objective_schema(self) -> dict[str, str]:
        """Field -> expected type name, in the shape the Agent SDK's submission
        validator expects (see `validate_payload` in the Agent SDK & Submission Intake
        service) — the bridge between what a requester asked for and what an agent's
        submission gets checked against."""
        type_names = {int: "integer", float: "number", str: "string", bool: "boolean"}
        return {c.field: type_names.get(type(c.value), "string") for c in self.objective_criteria}
