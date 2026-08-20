import uuid

from .base import PaymentIntentRef, StripeGateway, TransferRef


class FakeStripeGateway(StripeGateway):
    """In-memory stand-in for Stripe Connect, used in unit tests.

    Mirrors real Stripe's state rules closely enough to exercise the ledger's business
    logic (you can't capture an intent twice, you can't refund a captured intent) without
    any network calls. It is not a substitute for the stripe-test-mode integration suite
    called for in the Escrow Ledger Service PRD — that suite should run against real
    Stripe test-mode endpoints to catch API contract drift this fake cannot see.
    """

    def __init__(self) -> None:
        self._intents: dict[str, PaymentIntentRef] = {}
        self._transfers: dict[str, list[TransferRef]] = {}

    def create_payment_intent(self, *, amount_cents: int, currency: str, job_id: str) -> PaymentIntentRef:
        ref = PaymentIntentRef(id=f"pi_{uuid.uuid4().hex[:16]}", status="requires_capture")
        self._intents[ref.id] = ref
        return ref

    def capture_payment_intent(self, payment_intent_id: str) -> PaymentIntentRef:
        current = self._intents[payment_intent_id]
        if current.status != "requires_capture":
            raise ValueError(f"cannot capture payment intent in status {current.status}")
        updated = PaymentIntentRef(id=current.id, status="succeeded")
        self._intents[payment_intent_id] = updated
        return updated

    def cancel_payment_intent(self, payment_intent_id: str) -> PaymentIntentRef:
        current = self._intents[payment_intent_id]
        if current.status != "requires_capture":
            raise ValueError(f"cannot cancel payment intent in status {current.status}")
        updated = PaymentIntentRef(id=current.id, status="canceled")
        self._intents[payment_intent_id] = updated
        return updated

    def create_transfer(
        self, *, amount_cents: int, currency: str, destination_account_id: str, job_id: str
    ) -> TransferRef:
        ref = TransferRef(
            id=f"tr_{uuid.uuid4().hex[:16]}",
            destination_account_id=destination_account_id,
            amount_cents=amount_cents,
            status="paid",
        )
        self._transfers.setdefault(job_id, []).append(ref)
        return ref

    def list_transfers(self, job_id: str) -> list[TransferRef]:
        return list(self._transfers.get(job_id, []))
