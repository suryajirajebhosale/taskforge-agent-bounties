# Product direction — Merit

Merit is the **store, meter, and referee** for productized agents. Builders list an agent with a capability contract. Companies **run** it (usage) or **hire** it (retainer). Builders are paid when the contract holds.

This replaces the default “post a bounty, agents race, first verified pass wins” loop. Escrow, the oracle, locked requirements, reputation, and Stripe Connect remain the rails.

## Two products

| | **Run** | **Hire** |
|---|---|---|
| Buyer | Ops / SDR / researcher | Team that wants a named capability on staff |
| Action | Pick an agent → submit input → spend run credits → graded output | 30/90-day retainer: included runs + SLA + builder maintenance |
| Builder | Paid per **passing** run | Monthly capacity + keep evals green |
| Platform | Credits (grading included) + take on builder payout | Workspace SaaS + cut of retainer |

Open bounties are overflow (“no listed agent fits”) — not the home screen.

## Rules

1. **No custom Slack scope in-product.** Hire is this version of this contract. New fields = a new version.
2. **Certification gate.** Sandbox: capped runs. Certified: public Run. SLA-eligible: Hire.
3. If the buyer needs the builder weekly, that is services — do not sell it as Hire.
4. **Launch specializations:** Merit-owned templates only — lead enrichment, email verify, ICP fit, competitive brief, resume screen. New I/O = a new template version, not a custom Slack scope. Uncheckable “any agent” stays off the catalog.
5. Requesters cannot move goalposts mid-run. The published contract is the locked `Requirement`.
6. Requesters do not pay the **builder** on a failed contract. They still spend a **run credit** (grading is not free).
7. **Hire is attested.** SLA listings declare a process harness (tools/models/spend). A sidecar or signed SDK must stamp a trace. Builder is paid only if the **row** and the **harness** both pass. Sandbox/Certified Run may stay builder-hosted and black-box. Merit-hosted runtime is later.

## Monetization (target)

- Companies: run credits, hire retainers, workspace (seats, spend caps, audit log).
- Builders: free Sandbox listing; **10–15%** cut on passing runs and retainers; certification to unlock Hire / higher caps.

## Backend note

Python services historically used `bounty_id`. They now key money and grading on **`job_id`** (run or hire). See `docs/schema.md`.
