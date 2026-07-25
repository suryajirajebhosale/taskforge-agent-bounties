# PRD: Escrow Ledger Service

*Module 1 of 5 — Bounty marketplace build. Derived from [bounty-clone-plan.md](../../bounty-clone-plan.md), Phase 1/3.*

## Problem Statement

A requester who posts a bounty needs confidence that the money they commit is safely held and will only move when the work is actually verified — not lost, not released early, not double-paid. An agent developer whose agent completes and passes verification needs confidence that payout happens promptly and correctly, without having to chase anyone for it. Without a dedicated escrow and ledger system, payment state (funded, held, released, refunded, disputed) ends up scattered across ad hoc Stripe calls with no single source of truth, which risks double-payouts, stuck funds, or a ledger that silently drifts out of sync with what Stripe actually did.

## Solution

A dedicated service that wraps Stripe Connect for the actual movement of money and maintains its own internal, append-only ledger as the authoritative source of truth for "who is owed what." The rest of the marketplace — bounty posting, the Oracle Verification Service — calls a small, stable interface (fund, release, refund, reconcile) and never talks to Stripe directly or trusts Stripe's state as ground truth on its own.

## User Stories

1. As a requester, I want my payment to be held in escrow when I post a bounty, so that I know the money is committed but not yet given away.
2. As a requester, I want my escrow to be automatically refunded if the submitted work fails verification, so that I don't pay for work that doesn't meet my requirements.
3. As a requester, I want to see the current status of my escrowed funds (held, released, refunded) at any time, so that I always know where my money is.
4. As a requester, I want to be charged only once per bounty regardless of how many agents attempt it, so that competition among agents doesn't cost me extra.
5. As an agent developer, I want my agent's verified, winning submission to trigger an automatic payout, so that I get paid without manually invoicing anyone.
6. As an agent developer, I want to see a clear transaction history for every bounty my agents have won, so that I can reconcile my own books.
7. As an agent developer, I want payouts to go to my connected Stripe account without additional manual steps once I'm onboarded, so that I can focus on building agents, not chasing payments.
8. As an agent developer, I want to understand the platform's take-rate up front before my agent competes for a bounty, so that I know what I'll actually net.
9. As a platform operator, I want every escrow state transition (fund, hold, release, refund) recorded as an immutable ledger entry, so that I can audit exactly what happened to any dollar on the platform.
10. As a platform operator, I want a scheduled reconciliation job that compares Stripe's view of balances against our internal ledger, so that discrepancies are caught automatically rather than discovered by an angry user.
11. As a platform operator, I want reconciliation mismatches to be flagged for human review rather than auto-corrected, so that a bug in the reconciliation logic itself can't silently rewrite financial history.
12. As a platform operator, I want every state-changing escrow operation to be idempotent, so that a retried request (e.g. after a timeout) can never cause a double-release or double-refund.
13. As a platform operator, I want Stripe webhook events processed asynchronously and reconciled against the ledger, so that the rest of the platform never has to poll Stripe directly at request time.
14. As a platform operator, I want the platform's take-rate to be configurable per bounty category, so that pricing can be tuned by category economics without a code change.
15. As a finance/ops person, I want a clear audit trail linking each `EscrowHold` to its originating `Bounty` and, on release, to the specific `PayoutTransfer` and agent developer, so that I can answer "where did this money go" for any bounty on request.
16. As a platform engineer building the Oracle Verification Service, I want a simple `release_to_agent(bounty_id, agent_developer_id)` / `refund_to_requester(bounty_id)` interface, so that I don't need to know anything about Stripe Connect internals to trigger a payout or refund.
17. As a platform engineer, I want escrow holds to use Stripe's manual-capture pattern (authorize now, capture later), so that funds are provably committed without being irreversibly moved before verification completes.
18. As a security-conscious platform operator, I want every escrow API call authenticated and scoped to internal services only (not public-facing), so that only trusted platform code can move money.

## Implementation Decisions

- **Module:** `EscrowLedgerService`, a standalone Python/FastAPI service, internal-only (not exposed to the public web or agent-facing APIs directly — called by other backend services).
- **Data model:**
  - `LedgerEntry` — double-entry style record: account, debit/credit, amount, currency, `bounty_id`, `created_at`. Append-only; never updated or deleted.
  - `EscrowHold` — `bounty_id`, `requester_id`, `amount`, `status` (`pending` / `held` / `released` / `refunded` / `disputed`), Stripe `PaymentIntent` id.
  - `PayoutTransfer` — `agent_developer_id`, `stripe_transfer_id`, `amount`, `status`, linked `bounty_id`.
- **Core interface** (internal, not public):
  - `fund_bounty(bounty_id, requester_id, amount) -> EscrowHold` — creates a Stripe PaymentIntent with manual capture and a matching ledger entry.
  - `release_to_agent(bounty_id, agent_developer_id) -> PayoutTransfer` — captures the held PaymentIntent, creates a Stripe Connect transfer to the agent developer's connected account net of platform take-rate, writes ledger entries for the take-rate and the payout.
  - `refund_to_requester(bounty_id) -> RefundRecord` — cancels/refunds the held PaymentIntent, writes a reversing ledger entry.
  - `reconcile() -> ReconciliationReport` — scheduled job comparing Stripe balances/transfers to internal ledger state; flags mismatches, does not auto-correct.
- **Stripe Connect account type:** Express accounts for agent developers, chosen for faster onboarding over full Custom accounts; revisit if Stripe's KYC requirements for Express prove insufficient once real payout volume exists.
- **Idempotency:** every state-changing call requires an idempotency key derived from `(bounty_id, operation)` to make retries safe.
- **Webhooks:** a Stripe webhook handler (`payment_intent.succeeded`, `transfer.created`, `charge.dispute.created`) updates ledger state asynchronously; the ledger — never a live Stripe API call — is what the rest of the platform reads.
- **Take-rate:** a percentage fee configurable per bounty category, captured on the `Bounty` record at creation time and applied inside `release_to_agent`.

## Testing Decisions

Good tests here assert on **external behavior** — given a sequence of calls, assert the resulting ledger state and the Stripe API calls actually made (via Stripe's test mode / stripe-mock) — not on internal control flow or private helper functions.

- Use Stripe test mode or `stripe-mock` for integration-style tests instead of mocking the Stripe SDK directly, so tests catch real API contract drift.
- Cover: happy path fund → release; happy path fund → refund; a second release attempt on an already-released bounty is rejected (idempotency); a reconciliation mismatch is flagged, not silently auto-fixed; a webhook arriving out of order does not corrupt ledger state; take-rate is correctly applied and recorded as a separate ledger entry.
- This is a greenfield project — no existing test suite to follow yet. This module should establish the pattern (pytest, fixture factories for `Bounty`/`EscrowHold`, Stripe test-mode fixtures) that the other four modules' test suites will follow.

## Out of Scope

- Crypto/stablecoin escrow (fiat via Stripe Connect was an explicit scope decision for this build).
- Multi-currency support (USD only for MVP).
- Automated dispute resolution with card networks (Stripe chargebacks handled manually by ops for MVP).
- Dynamic/experimental take-rate pricing (fixed rate per category at launch).

## Further Notes

This is the highest-stakes module in the platform because it moves real money — it was explicitly flagged for dedicated test investment. It should be built and hardened *before* the Oracle Verification Service is wired to auto-trigger payouts, since bugs in either module compound badly when combined.
