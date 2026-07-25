class EscrowError(Exception):
    """Base class for all escrow ledger errors."""


class BountyAlreadyFunded(EscrowError):
    pass


class HoldNotFound(EscrowError):
    pass


class InvalidHoldState(EscrowError):
    """Raised when an operation is attempted against a hold that isn't in the required state
    and no idempotent replay applies (e.g. trying to refund an already-released hold)."""
