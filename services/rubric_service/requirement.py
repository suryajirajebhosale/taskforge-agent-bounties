"""Re-exports the shared bounty requirement schema. The canonical definition lives in
`packages/bounty_schemas/requirement.py` (also consumed directly by the Oracle
Verification Service); this module exists so existing imports of
`services.rubric_service.requirement` keep working unchanged."""

from packages.bounty_schemas.requirement import (
    BountyCategory,
    Comparator,
    ObjectiveCriterion,
    Requirement,
    SubjectiveCriterion,
)

__all__ = ["BountyCategory", "Comparator", "ObjectiveCriterion", "Requirement", "SubjectiveCriterion"]
