class OracleError(Exception):
    """Base class for all oracle verification errors."""


class VerdictNotFound(OracleError):
    pass


class DisputeCaseNotFound(OracleError):
    pass
