class AgentPlatformError(Exception):
    """Base class for all agent platform errors."""


class DeveloperNotFound(AgentPlatformError):
    pass


class AgentNotFound(AgentPlatformError):
    pass


class InvalidApiKey(AgentPlatformError):
    pass


class BountyNotRegistered(AgentPlatformError):
    """Raised when an operation references a bounty that `notify_bounty_funded` hasn't
    been called for yet."""


class NotMatchedToBounty(AgentPlatformError):
    """Raised when an agent tries to submit to a bounty it was never matched to."""


class SubmissionNotFound(AgentPlatformError):
    pass


class SubmissionValidationError(AgentPlatformError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class RateLimitExceeded(AgentPlatformError):
    pass
