import stripe

from .base import PaymentIntentRef, StripeGateway, TransferRef


class StripeGatewayLive(StripeGateway):
    """Real Stripe Connect implementation. Requires `settings.stripe_api_key` to be set
    to a Stripe secret key (test-mode key for the eventual stripe-test-mode integration
    suite, live key in production)."""

    def __init__(self, api_key: str) -> None:
        self._client = stripe.StripeClient(api_key)

    def create_payment_intent(self, *, amount_cents: int, currency: str, bounty_id: str) -> PaymentIntentRef:
        intent = self._client.payment_intents.create(
            params={
                "amount": amount_cents,
                "currency": currency,
                "capture_method": "manual",
                "metadata": {"bounty_id": bounty_id},
            }
        )
        return PaymentIntentRef(id=intent.id, status=intent.status)

    def capture_payment_intent(self, payment_intent_id: str) -> PaymentIntentRef:
        intent = self._client.payment_intents.capture(payment_intent_id)
        return PaymentIntentRef(id=intent.id, status=intent.status)

    def cancel_payment_intent(self, payment_intent_id: str) -> PaymentIntentRef:
        intent = self._client.payment_intents.cancel(payment_intent_id)
        return PaymentIntentRef(id=intent.id, status=intent.status)

    def create_transfer(
        self, *, amount_cents: int, currency: str, destination_account_id: str, bounty_id: str
    ) -> TransferRef:
        transfer = self._client.transfers.create(
            params={
                "amount": amount_cents,
                "currency": currency,
                "destination": destination_account_id,
                "metadata": {"bounty_id": bounty_id},
            }
        )
        return TransferRef(
            id=transfer.id,
            destination_account_id=destination_account_id,
            amount_cents=amount_cents,
            status="paid",
        )

    def list_transfers(self, bounty_id: str) -> list[TransferRef]:
        result = self._client.transfers.list(params={"limit": 100})
        return [
            TransferRef(
                id=t.id,
                destination_account_id=t.destination,
                amount_cents=t.amount,
                status="paid",
            )
            for t in result.data
            if t.metadata.get("bounty_id") == bounty_id
        ]
