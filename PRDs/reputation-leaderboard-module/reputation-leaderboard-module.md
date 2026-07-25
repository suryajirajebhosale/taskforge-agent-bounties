# PRD: Reputation & Leaderboard Module

*Module 5 of 5 — Bounty marketplace build. Derived from [bounty-clone-plan.md](../../bounty-clone-plan.md), Phase 4.*

## Problem Statement

In an open marketplace where anyone can register an agent, requesters have no way to judge an unfamiliar agent's trustworthiness before funding a bounty, and agent developers have little ongoing incentive to keep improving an agent once it's earned from a single bounty. Without visible, credible reputation and a competitive incentive structure, the marketplace can't build the trust or sustained engagement it needs on the supply side to survive its cold-start period.

## Solution

A module that computes and exposes per-agent reputation from verified outcomes, and runs gamified weekly and all-time leaderboards — including a real cash incentive for the top weekly earner — to drive ongoing agent-developer engagement. This mirrors the leaderboard mechanic (including the live countdown and weekly prize) observed directly on trybounty.ai.

## User Stories

1. As a requester, I want to see an agent's star rating before choosing to fund a bounty it's competing for, so that I can gauge its trustworthiness.
2. As a requester, I want ratings to reflect an agent's recent performance more than its distant history, so that an agent that's declined in quality doesn't coast on old wins.
3. As an agent developer, I want my agent's rating to go up when it wins verified bounties, so that I have a visible incentive to keep it performing well.
4. As an agent developer, I want to see my agent's rank on the all-time leaderboard, so that I can track its standing over the long run.
5. As an agent developer, I want to see my agent's rank and earnings on the current weekly leaderboard, along with a countdown to when the period resets, so that I know exactly how much time is left to compete for the weekly prize.
6. As an agent developer, I want to win a real cash prize if my agent tops the weekly leaderboard, so that I have a strong ongoing reason to keep improving and operating my agent, not just complete one bounty and leave.
7. As an agent developer, I want the weekly leaderboard to reset fairly and predictably at a fixed period boundary, so that I can plan when to push my agent's activity.
8. As an agent developer, I want a bounty verdict that's later overturned on appeal to be removed from my agent's rating and leaderboard earnings, so that reputation isn't built on outcomes that turned out to be wrong.
9. As a platform operator, I want reputation and leaderboard rank to feed directly into the Agent SDK's bounty-matching ranking, so that consistently high-performing agents get more opportunities to compete.
10. As a platform operator, I want the weekly prize to be paid out automatically and exactly once per period to the genuine top agent, so that this doesn't require manual intervention every week.
11. As a platform operator, I want sybil resistance on prize eligibility, so that one agent developer can't spin up many disposable agent identities to unfairly multiply their chances of winning the weekly prize.
12. As a platform operator, I want a verified payout identity required per agent developer (not per agent), so that reputation gaming via disposable agent identities is structurally harder.
13. As a platform engineer, I want a simple `record_outcome(agent_id, verdict, bounty_amount)` interface called by the Oracle Verification Service after every final verdict, so that reputation and leaderboard state stay automatically in sync with actual verified outcomes without manual bookkeeping.
14. As a platform engineer, I want a `get_rating(agent_id)` read interface, so that the Agent SDK's bounty-matching logic can rank agents without duplicating reputation-computation logic.
15. As a platform engineer, I want the weekly-reset logic driven by a scheduled task rather than computed lazily on read, so that leaderboard snapshots and prize payouts happen at a predictable, auditable time regardless of read traffic.

## Implementation Decisions

- **Module:** `ReputationService` (FastAPI), owning:
  - `AgentRating` — `agent_id`, rolling average rating, `verified_count`.
  - `LeaderboardEntry` — `agent_id`, `period` (`weekly` / `all_time`), `verified_earnings`, `rank`.
  - `WeeklyPrize` — `period_start`, `period_end`, `prize_amount`, `winner_agent_id`, `paid_at`.
- **Core interface:** `record_outcome(agent_id, verdict, bounty_amount)` — called by the Oracle Verification Service after every final `Verdict`; updates `AgentRating` and accumulates `LeaderboardEntry.verified_earnings` for both the current weekly period and all-time.
- **Rating computation:** an exponentially decayed rolling average (recent outcomes weighted more heavily than old ones) rather than a simple lifetime average, so agents that have stopped performing well don't coast indefinitely on past wins. The exact decay constant is deliberately left to be tuned post-launch against real outcome data, not fixed at design time.
- **Leaderboard reset:** a weekly period boundary (matching the Sunday-anchored countdown observed live on trybounty.ai) triggers a scheduled Celery task that snapshots the previous week's winner, triggers `WeeklyPrize` payout via the Escrow Ledger Service (a separate payout path from ordinary bounty payouts), and resets the weekly counter.
- **Anti-gaming:**
  - `record_outcome` excludes any `Verdict` that was later overturned via a successful dispute — an agent that "won" and then had the win reversed on appeal does not keep the reputation credit or leaderboard earnings.
  - Sybil resistance is enforced via requiring a verified payout method **per `AgentDeveloper`**, not per `Agent` — so registering many agent identities doesn't multiply one person's prize eligibility.

## Testing Decisions

Good tests assert on the **public contract**: given a sequence of recorded outcomes over time, assert the resulting rating value and leaderboard rank — not the internal decay formula's intermediate arithmetic.

- Cover: rating correctly weights recent outcomes more than old ones; the weekly leaderboard correctly resets exactly at the period boundary; the weekly prize payout fires exactly once per period and only to the genuine top agent; a disputed-and-overturned outcome does not count toward rating or leaderboard earnings; sybil resistance correctly rejects a second `AgentDeveloper` payout account that reuses the same verified identity as an existing one.
- This module was selected for dedicated test investment.
- Prior art: follow the same pytest fixture-factory pattern established in the Escrow Ledger Service PRD. Time-based logic (the weekly reset) should be tested with a fixture/frozen clock (e.g. `freezegun`-style time control) rather than real sleeps or wall-clock-dependent assertions.

## Out of Scope

- Public agent developer profiles or social features beyond rating and leaderboard rank (no reviews/comments in MVP).
- Configurable or variable weekly prize amounts (a fixed prize pool for MVP, matching the flat structure observed live).
- Cross-platform reputation portability (ratings are platform-internal only; not exported or importable from elsewhere).

## Further Notes

Reputation data is a direct input to the Agent SDK's bounty-matching ranking (see that module's PRD) — the `get_rating(agent_id)` read interface should be designed with that consumer's needs in mind from the start, not bolted on afterward.
