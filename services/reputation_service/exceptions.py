class ReputationError(Exception):
    """Base class for all reputation & leaderboard errors."""


class OutcomeNotFound(ReputationError):
    pass


class PrizeNotFound(ReputationError):
    pass
