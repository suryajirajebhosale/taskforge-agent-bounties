from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentIntentRef:
    id: str
    status: str
    """One of: requires_capture, succeeded, canceled."""


@dataclass(frozen=True)
class TransferRef:
    id: str
    destination_account_id: str
    amount_cents: int
    status: str


class StripeGateway(ABC):
    """Everything the escrow ledger needs from Stripe Connect, behind a small interface.

    Kept narrow on purpose: the ledger service should never import the `stripe` package
    directly, so business logic can be tested against `FakeStripeGateway` without any
    network access, while `StripeGatewayLive` carries all the real API-specific detail.
    """

    @abstractmethod
    def create_payment_intent(self, *, amount_cents: int, currency: str, job_id: str) -> PaymentIntentRef: ...

    @abstractmethod
    def capture_payment_intent(self, payment_intent_id: str) -> PaymentIntentRef: ...

    @abstractmethod
    def cancel_payment_intent(self, payment_intent_id: str) -> PaymentIntentRef: ...

    @abstractmethod
    def create_transfer(
        self, *, amount_cents: int, currency: str, destination_account_id: str, job_id: str
    ) -> TransferRef: ...

    @abstractmethod
    def list_transfers(self, job_id: str) -> list[TransferRef]: ...
