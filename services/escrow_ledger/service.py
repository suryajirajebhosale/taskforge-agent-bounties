from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from .config import settings
from .exceptions import HoldNotFound, InvalidHoldState
from .gateways.base import StripeGateway
from .models import EscrowHold, HoldStatus, IdempotencyRecord, LedgerEntry, LedgerEntryType, PayoutTransfer, TransferStatus


@dataclass(frozen=True)
class ReconciliationMismatch:
    bounty_id: str
    reason: str
    internal_amount_cents: int
    stripe_amount_cents: int


@dataclass(frozen=True)
class ReconciliationReport:
    checked_bounty_ids: list[str] = field(default_factory=list)
    mismatches: list[ReconciliationMismatch] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.mismatches


class EscrowLedgerService:
    """Escrow + payout logic for one bounty at a time. Stripe is reached only through
    `gateway`; the `LedgerEntry` rows this class writes are the platform's own source
    of truth for who is owed what, per the Escrow Ledger Service PRD."""

    def __init__(self, session: Session, gateway: StripeGateway):
        self.session = session
        self.gateway = gateway

    def fund_bounty(
        self, *, bounty_id: str, requester_id: str, amount_cents: int, take_rate_bps: int | None = None
    ) -> EscrowHold:
        existing = self._find_hold(bounty_id)
        if existing is not None:
            return existing  # idempotent replay: funding a bounty twice is a no-op, not an error

        intent = self.gateway.create_payment_intent(amount_cents=amount_cents, currency="usd", bounty_id=bounty_id)
        hold = EscrowHold(
            bounty_id=bounty_id,
            requester_id=requester_id,
            amount_cents=amount_cents,
            take_rate_bps=take_rate_bps if take_rate_bps is not None else settings.default_take_rate_bps,
            status=HoldStatus.HELD,
            stripe_payment_intent_id=intent.id,
        )
        self.session.add(hold)
        self._write_ledger_pair(
            bounty_id=bounty_id,
            debit_account=f"requester:{requester_id}",
            credit_account="escrow:held",
            amount_cents=amount_cents,
            description="Bounty funded into escrow",
        )
        self.session.commit()
        return hold

    def release_to_agent(self, *, bounty_id: str, agent_developer_id: str) -> PayoutTransfer:
        replay = self._get_idempotent_result(bounty_id, "release")
        if replay is not None:
            return self.session.get(PayoutTransfer, replay.result_id)

        hold = self._require_hold(bounty_id)
        if hold.status != HoldStatus.HELD:
            raise InvalidHoldState(f"cannot release bounty {bounty_id}: hold is {hold.status.value}, not held")

        self.gateway.capture_payment_intent(hold.stripe_payment_intent_id)

        take_amount = hold.amount_cents * hold.take_rate_bps // 10_000
        net_amount = hold.amount_cents - take_amount
        transfer_ref = self.gateway.create_transfer(
            amount_cents=net_amount,
            currency=hold.currency,
            destination_account_id=agent_developer_id,
            bounty_id=bounty_id,
        )

        payout = PayoutTransfer(
            bounty_id=bounty_id,
            agent_developer_id=agent_developer_id,
            amount_cents=net_amount,
            stripe_transfer_id=transfer_ref.id,
            status=TransferStatus.COMPLETED,
        )
        self.session.add(payout)
        hold.status = HoldStatus.RELEASED

        if take_amount > 0:
            self._write_ledger_pair(
                bounty_id=bounty_id,
                debit_account="escrow:held",
                credit_account="platform:revenue",
                amount_cents=take_amount,
                description="Platform take-rate",
            )
        self._write_ledger_pair(
            bounty_id=bounty_id,
            debit_account="escrow:held",
            credit_account=f"agent_developer:{agent_developer_id}",
            amount_cents=net_amount,
            description="Bounty payout to agent developer",
        )

        self.session.flush()  # assign payout.id before recording idempotency
        self._record_idempotent_result(bounty_id, "release", payout.id)
        self.session.commit()
        return payout

    def refund_to_requester(self, *, bounty_id: str) -> EscrowHold:
        hold = self._require_hold(bounty_id)

        replay = self._get_idempotent_result(bounty_id, "refund")
        if replay is not None:
            return hold

        if hold.status != HoldStatus.HELD:
            raise InvalidHoldState(f"cannot refund bounty {bounty_id}: hold is {hold.status.value}, not held")

        self.gateway.cancel_payment_intent(hold.stripe_payment_intent_id)
        hold.status = HoldStatus.REFUNDED

        self._write_ledger_pair(
            bounty_id=bounty_id,
            debit_account="escrow:held",
            credit_account=f"requester:{hold.requester_id}",
            amount_cents=hold.amount_cents,
            description="Escrow refunded to requester",
        )

        self.session.flush()
        self._record_idempotent_result(bounty_id, "refund", hold.id)
        self.session.commit()
        return hold

    def reconcile(self, bounty_ids: list[str]) -> ReconciliationReport:
        """Compares our payout ledger against Stripe's own view of transfers for each
        bounty. Mismatches are reported, never auto-corrected — per the PRD, a bug in
        this method itself must not be able to silently rewrite financial history."""
        mismatches: list[ReconciliationMismatch] = []
        for bounty_id in bounty_ids:
            internal_total = sum(
                p.amount_cents
                for p in self.session.query(PayoutTransfer).filter_by(bounty_id=bounty_id).all()
            )
            stripe_total = sum(t.amount_cents for t in self.gateway.list_transfers(bounty_id))
            if internal_total != stripe_total:
                mismatches.append(
                    ReconciliationMismatch(
                        bounty_id=bounty_id,
                        reason="internal payout total does not match Stripe transfer total",
                        internal_amount_cents=internal_total,
                        stripe_amount_cents=stripe_total,
                    )
                )
        return ReconciliationReport(checked_bounty_ids=bounty_ids, mismatches=mismatches)

    def _write_ledger_pair(
        self, *, bounty_id: str, debit_account: str, credit_account: str, amount_cents: int, description: str
    ) -> None:
        self.session.add(
            LedgerEntry(
                bounty_id=bounty_id,
                account=debit_account,
                entry_type=LedgerEntryType.DEBIT,
                amount_cents=amount_cents,
                description=description,
            )
        )
        self.session.add(
            LedgerEntry(
                bounty_id=bounty_id,
                account=credit_account,
                entry_type=LedgerEntryType.CREDIT,
                amount_cents=amount_cents,
                description=description,
            )
        )

    def _find_hold(self, bounty_id: str) -> EscrowHold | None:
        return self.session.query(EscrowHold).filter_by(bounty_id=bounty_id).one_or_none()

    def _require_hold(self, bounty_id: str) -> EscrowHold:
        hold = self._find_hold(bounty_id)
        if hold is None:
            raise HoldNotFound(f"no escrow hold for bounty {bounty_id}")
        return hold

    def _get_idempotent_result(self, bounty_id: str, operation: str) -> IdempotencyRecord | None:
        return (
            self.session.query(IdempotencyRecord)
            .filter_by(bounty_id=bounty_id, operation=operation)
            .one_or_none()
        )

    def _record_idempotent_result(self, bounty_id: str, operation: str, result_id: str) -> None:
        self.session.add(IdempotencyRecord(bounty_id=bounty_id, operation=operation, result_id=result_id))
