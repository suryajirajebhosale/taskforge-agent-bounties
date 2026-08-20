class AgentPlatformError(Exception):
    """Base class for all agent platform errors."""


class DeveloperNotFound(AgentPlatformError):
    pass


class AgentNotFound(AgentPlatformError):
    pass


class InvalidApiKey(AgentPlatformError):
    pass


class JobNotRegistered(AgentPlatformError):
    """Raised when an operation references a job that `notify_job_funded` hasn't
    been called for yet."""


class NotAssignedToJob(AgentPlatformError):
    """Raised when an agent tries to submit to a job it was never assigned to."""


class JobAlreadyAssigned(AgentPlatformError):
    """A run/hire job already has a listed agent; a second assignee is not allowed."""


class SubmissionNotFound(AgentPlatformError):
    pass


class SubmissionValidationError(AgentPlatformError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class RateLimitExceeded(AgentPlatformError):
    pass


class TemplateNotFound(AgentPlatformError):
    pass


class CertificationFailed(AgentPlatformError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class SlaChecklistIncomplete(AgentPlatformError):
    pass


class AttestationRequired(AgentPlatformError):
    pass
