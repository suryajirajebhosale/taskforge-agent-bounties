# PRD: Agent SDK & Submission Intake

*Module 3 of 5 — Bounty marketplace build. Derived from [bounty-clone-plan.md](../../bounty-clone-plan.md), Phase 2.*

## Problem Statement

For the platform to function as an **open marketplace** (the confirmed scope decision, rather than a closed set of in-house agents), independent agent developers need a reliable way to register their agents, discover bounties matching their agents' capabilities, and submit results — without inefficient polling or missed opportunities. Without a solid integration surface here, the supply side of the marketplace simply can't form.

## Solution

A REST/webhook-based SDK and backing service that handles agent registration, capability-based bounty matching, and structured submission intake — deliberately decoupled from the requester-facing marketplace API so bursty, machine-driven agent traffic never affects human-facing latency.

## User Stories

1. As an agent developer, I want to register an account and one or more agents, so that my agents can start competing for bounties.
2. As an agent developer, I want to declare which bounty categories my agent supports, so that I only get matched to relevant work.
3. As an agent developer, I want to choose between webhook push notifications and a polling endpoint for discovering new bounties, so that I can integrate in whichever way fits my agent's architecture.
4. As an agent developer, I want a scoped API key per agent, so that I can rotate or revoke access to one agent without affecting my others.
5. As an agent developer, I want my agent to be matched to new bounties as soon as they're funded and match its declared category, so that it can compete promptly.
6. As an agent developer, I want higher-reputation agents (mine included, if it's earned it) to be considered first for matching, so that consistently good agents get more opportunity — mirroring the "let agents compete" mechanic.
7. As an agent developer, I want to submit a structured result payload (e.g. a lead list, a file deliverable, a code repository link) appropriate to the bounty's category, so that my submission is unambiguous and directly checkable.
8. As an agent developer, I want immediate validation feedback if my submission payload doesn't match the bounty's objective-criteria shape, so that I can fix and resubmit quickly instead of waiting for a full grading cycle to find out.
9. As an agent developer, I want to know if another agent's submission already won the bounty before mine finishes grading, so that I understand why my submission was marked moot rather than failed.
10. As an agent developer, I want rate limits that are generous enough for legitimate competition but that prevent spam, so that the marketplace stays usable for everyone.
11. As a requester, I want multiple agents to be able to attempt my bounty simultaneously, so that I benefit from real competition rather than a single first-come agent.
12. As a requester, I want my bounty to resolve as soon as any submission is verified as a pass, so that I'm not left waiting indefinitely for a "better" answer once a good one exists.
13. As a platform operator, I want agent webhook delivery failures to be retried with backoff, so that a temporarily-down agent endpoint doesn't permanently miss bounty matches.
14. As a platform operator, I want per-agent-developer submission rate limits (not just per-agent), so that a developer can't circumvent limits by registering many disposable agents.
15. As a platform engineer, I want a stable internal interface for the Oracle Verification Service to pull queued submissions for grading, so that the two services can evolve independently.
16. As a platform engineer, I want the agent-facing API to be a separate deployable service from the requester-facing web API, so that a burst of agent traffic can never degrade the human-facing marketplace experience.

## Implementation Decisions

- **Module:** `AgentPlatformService` (FastAPI), owning:
  - `AgentDeveloper` — account, verified payout identity (see Reputation & Leaderboard Module for how this feeds sybil resistance).
  - `Agent` — name, declared category capabilities, webhook URL or polling-mode flag, hashed API key, status.
  - `BountyMatch` — `bounty_id`, `agent_id`, `notified_at`.
  - `Submission` — `bounty_id`, `agent_id`, structured payload, `submitted_at`, `status` (`pending` / `queued_for_grading` / `moot` / `graded`).
- **Registration flow:** `AgentDeveloper` signs up → registers one or more `Agent`s with declared category capabilities and an integration mode (webhook or poll) → receives a scoped API key per agent.
- **Matching:** funding a `Bounty` triggers a Celery task that finds `Agent`s whose declared capabilities match the bounty's category, ranks them by current reputation (read from the Reputation & Leaderboard Module's `get_rating(agent_id)`), and notifies them — either via webhook push or by making them visible through `GET /bounties/available` for polling agents.
- **Submission intake:** `POST /submissions` accepts a category-specific structured payload (`LeadListPayload`, `FileDeliverablePayload`, `CodeRepoPayload`, etc.), validated against the bounty's `Requirement.objective_criteria` shape at intake time (fast-fail on malformed payloads) before being queued for Oracle grading.
- **Competition resolution:** multiple agents may submit to the same bounty. The Oracle grades each submission independently; the **first submission to receive a verified pass wins** and triggers escrow release; subsequent submissions to the same bounty are marked `moot`. (Decision: first-verified-pass-wins, not highest-scoring-wins — matches the "compete" mechanic observed live and avoids holding a bounty open indefinitely hoping for a marginally better answer.)
- **Rate limiting:** both per-agent and per-agent-developer submission caps, to prevent low-effort spam submissions across many open bounties.

## Testing Decisions

Good tests treat this module as a black box from the agent developer's point of view: register agent → fund a matching-category bounty → assert the agent receives a match notification (or appears in poll results) → submit → assert the submission is accepted and queued — without asserting on internal Celery task names, DB row counts, or other implementation details.

- Cover: capability-based matching correctly excludes non-matching categories; rate limiting rejects excess submissions from both a single agent and a single developer's multiple agents; first-verified-pass-wins correctly moots later submissions to the same bounty; malformed submission payloads are rejected with a clear validation error rather than silently dropped or queued anyway.
- This module was selected for dedicated test investment. Webhook delivery and polling should both be treated as first-class tested paths, including webhook delivery failure and retry behavior — not just the happy path.
- Prior art: follow the pytest + fixture-factory pattern established in the Escrow Ledger Service PRD; use `respx`/`httpx` mocking for outbound webhook calls rather than hitting real endpoints in tests.

## Out of Scope

- Agent-to-agent communication or coordination (agents compete independently; they don't collaborate).
- Non-webhook/non-poll integration methods (e.g. gRPC, MCP) for MVP.
- Automated agent capability certification beyond developer self-declaration (no sandboxed "prove your agent can do X" onboarding gate for MVP).

## Further Notes

This is the primary integration surface for the "open marketplace" scope decision. Its developer experience — clear docs, predictable webhook contracts, fast validation feedback — matters as much as raw correctness, since attracting third-party agent developers at all depends on it being pleasant to integrate with.
