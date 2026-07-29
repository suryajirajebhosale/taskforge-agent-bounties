class RubricError(Exception):
    """Base class for all rubric module errors."""


class RequirementNotFound(RubricError):
    pass


class RequirementLocked(RubricError):
    """Raised when an operation would modify a Requirement after its bounty was funded."""


class RequirementNotApproved(RubricError):
    """Raised when funding tries to lock a Requirement the requester never approved."""
