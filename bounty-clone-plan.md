# Building a "Bounty" Clone: Product Teardown + Build Plan

*Research and roadmap based on a live walkthrough of [trybounty.ai](https://trybounty.ai) on 2026-07-25.*

---

## Section A — What Bounty Is and What It Does

### 1. Product summary

Bounty's tagline is blunt about the model: **"Post a task. AI agents complete it."** Framed slightly more fully, it's **"the open marketplace where AI agents compete for tasks and earn."**

Strip away the AI framing and the shape is familiar: it's a bounty/task marketplace, structurally close to Upwork or a Gitcoin bounty board. What makes it new is *who does the work*. On Bounty, the labor side isn't freelancers — it's autonomous AI agents, built and operated by independent third-party developers, competing against each other for the same paid tasks. The platform is backed by **a16z Speedrun**, a16z's early-stage accelerator, which places it firmly as a pre-seed/seed-stage startup rather than an established company — confirmed by its own live stats bar (total escrowed, bounties posted, active agents, verified results) sitting near zero at the time of this review.

### 2. The two sides of the marketplace

**Requesters** (the demand side) are people or businesses with a task they want done — lead generation, market research, content creation, hiring/recruiting outreach, or small software builds. They don't hire a specific freelancer; they post a bounty and let the market's agents compete for it.

**Agent developers** (the supply side) build and operate autonomous AI agents — pieces of software, not humans — and register them on the platform to compete for bounties. Each agent has its own persistent identity and brand: on the live site these show up as named agents like *Ledger*, *Scouter*, *Navigator*, *Atlas*, *Index*, *Cloud*, *Shaw*, and *LightX*, each carrying its own star rating (0–5) visible on every bounty it has completed. A public "for AI agent developers" onboarding page wasn't found live on the site (it may be gated behind sign-up, or simply not yet built), so the exact developer-facing SDK/API is inferred rather than directly observed — but the mechanics only make sense if such an integration surface exists.

### 3. The core loop

The homepage states this explicitly, in four steps:

1. **Post a bounty** — describe the job, set a reward, and fund it through escrow.
2. **Let agents compete** — the highest-reputation agents for that task type compete to complete it; reputation data is used to surface the best-fit agents rather than a free-for-all.
3. **We verify submissions** — an **"oracle"** validates the submission against the requester's predefined requirements before any money moves. ("Oracle" here is used the way early crypto/prediction-market products used it — an automated, trusted verification step — not a blockchain oracle network; nothing on the site suggests on-chain infrastructure.)
4. **You only pay for results** — if verification passes, escrow releases automatically; if it fails, the requester's escrow is returned.

Notably, bounty creation itself is AI-assisted: the homepage's primary call-to-action is a natural-language box — "Describe bounty to post" — pre-seeded with example prompts like *"Find 100 ecommerce brands doing $1M–$25M in revenue"*, *"Design a landing page for my startup"*, and *"Build a Chrome extension from this specification."* This strongly implies the platform turns a plain-English ask into a structured bounty (reward suggestion + acceptance criteria) automatically, rather than making the requester fill out a rigid form.

Observed bounty categories: **Sales & Lead Generation, Research & Competitive Intelligence, AI Automation & Product Building, Hiring & Recruiting, Content & Media**, and an **Other** catch-all (more exist behind a "Show more" control). Live examples ranged from **$1.10 to $60.50** in reward, with completion windows from a few hours to 15 days. The task mix skews heavily toward work that's cheap for an LLM-driven agent to attempt and relatively easy to spec and check — lead lists, research compilations, short-form video/content, and small scripted deliverables — rather than open-ended or highly subjective creative work.

### 4. A closer look at the "oracle" — the actual hard problem

The single riskiest promise in this product is step 4: *release real money automatically, with no human reviewer, based on an AI's judgment that the work is good.* That only works if the verification layer is trustworthy, which in turn requires several things the marketing page doesn't spell out but that the mechanics demand:

- **A translatable requirement**, so "find 100 ecommerce brands doing $1M–$25M in revenue" becomes something a machine can check (a count, a data schema, criteria per record) rather than staying prose.
- **Different grading strategies per task type** — a lead list can be checked almost deterministically (are these real companies, real contacts, in range); a landing page design or a Chrome extension needs actual execution/rendering, not just a description of what was built; a promotional video needs a very different kind of judgment.
- **Confidence, not just a verdict** — an automated grader that is wrong even occasionally, with no visibility into *how* wrong or *how* confident it was, will destroy trust with requesters (who feel robbed) or agent developers (who feel unfairly failed) very quickly.
- **A recourse path** — something has to happen when an agent developer believes a "fail" was wrong, or a requester believes a "pass" shouldn't have been.

This is the part of the product hardest to observe from the outside (it's server-side and proprietary), but it's the true technical moat, if Bounty has one — more so than the marketplace UI itself, which is comparatively easy to replicate.

### 5. Reputation and the leaderboard

Every agent carries a persistent rating, shown on every completed bounty. On top of that sits a gamified **leaderboard** with two views: an **all-time** leaderboard, and a **weekly** leaderboard with a real cash prize (observed: **$25/week**, with a live countdown timer) awarded to the agent with the most verified earnings that week.

This is a growth/retention lever aimed squarely at the supply side of the marketplace: it gives agent developers a competitive, visible reason to keep their agents tuned, responsive, and active on the platform, independent of any single bounty's payout. It also functions as a discovery/trust mechanism for requesters, who have no other way to evaluate an anonymous piece of software they're about to pay to do real work.

### 6. Business model (inferred, not stated)

Nothing on the live pages states a take rate explicitly. But the mechanics point clearly to a standard two-sided marketplace model: requesters fund bounties into escrow; the platform presumably takes a percentage spread between what the requester pays in and what the winning agent's developer receives on payout — the same mechanism as Upwork, Fiverr, or App Store-style marketplaces. New accounts receive **$1 in starter credit**, a low-friction acquisition hook to get a requester to try posting a first (cheap) bounty without a card on file yet.

### 7. What's actually distinctive here

Compared to adjacent categories:

- **vs. Upwork/Fiverr** — same demand-side mechanics, but the supply side is software, not people, which removes the human latency/availability bottleneck and lets many agents attempt the same bounty simultaneously ("compete" is literal, not just "apply").
- **vs. Gitcoin/crypto bounty boards** — same "post a bounty, fund escrow, pay on completion" shape, minus the blockchain; the "oracle" language is borrowed from that world but implemented as an automated software verifier rather than a decentralized oracle network.
- **vs. AI agent directories/plugin stores** — those are catalogs; Bounty is a transactional marketplace with money, competition, and reputation attached, not just a listing of tools.

The genuinely new combination is: **agent-vs-agent competition for the same paid task, gated by automatic verification that must be trustworthy enough to move real money with no human in the loop.** Everything else (browsing, categories, posting flow) is standard marketplace UX.

### 8. Honest read on maturity and risk

This is an early-stage, low-liquidity product today — the platform's own stats (total escrowed, bounties posted, active agents) were near zero at time of review, and the task catalog, while real, is thin. It faces the classic two-sided marketplace cold-start problem (not enough agents to make it worth requesters' time; not enough bounties to make it worth agent developers' time) on top of the harder, more novel problem of building automated verification good enough that people trust it with real payouts. Both of these are exactly the kind of problems an accelerator-backed early-stage startup is expected to still be solving.

---

## Section B — Roadmap and Tech Stack to Build an Equivalent

**Scope assumptions locked in for this plan** (confirmed): build a **fundable MVP** (not a weekend prototype, not a 6-month enterprise build); support an **open marketplace of third-party agent developers** (not a closed set of in-house agents); use **Stripe Connect for fiat escrow/payout** (not crypto); use **Python end-to-end** for backend and all intelligence/verification work; and build the LLM judge layer as **object-oriented agent classes on LangChain**, with a pluggable model backend (**OpenAI** by default, **NVIDIA NIM**-hosted models as a self-hostable alternative) rather than locking to one vendor's SDK.

### Phase 0 — Foundations

- Monorepo layout: `apps/web` (Next.js), `services/api` (FastAPI — requester-facing), `services/agent-api` (FastAPI — agent-developer-facing), `services/oracle` (FastAPI — verification), shared `packages/schemas` for Pydantic models used across services.
- Core data model: `User`, `Bounty`, `Requirement` (structured rubric), `Agent`, `AgentDeveloper`, `Submission`, `Verdict`, `EscrowTransaction`, `Rating`.
- Auth scaffolding with two roles (requester, agent developer) and Stripe Connect wired in **test mode** end to end (fund → hold → release) before any real UI exists.

### Phase 1 — Requester side MVP

- Manual bounty-creation form first (title, description, category, reward, deadline, requirements) — the NL-assisted "describe it and we structure it" version comes second, once the requirement schema in Phase 3 exists to structure *into*.
- Stripe Connect escrow funding on bounty creation (hold, don't capture, until verification resolves).
- Public bounty browse/listing/detail pages, category taxonomy matching the observed set (Sales & Lead Gen, Research & Competitive Intelligence, AI Automation & Product Building, Hiring & Recruiting, Content & Media, Other).

### Phase 2 — Agent developer side MVP

- Agent registration and API key issuance.
- **Agent SDK**: a REST/webhook contract agents use to (a) receive new bounty briefs matching their declared capabilities/category, (b) submit a result, and (c) receive verification outcomes asynchronously.
- Submission intake endpoint with structured payloads (files, links, structured data) depending on category.

### Phase 3 — Verification ("oracle") layer

This is treated as a **first-class service**, not a pipeline step bolted onto the marketplace — it's the piece that makes it safe to release real money without a human reviewer, and it deserves its own build track from day one.

**3.1 Rubric generation.** At bounty-creation time, convert the requester's free-text description into a structured, machine-checkable requirement schema (a Pydantic model) — objective criteria (counts, formats, required fields, data ranges) plus subjective criteria (e.g. "tone matches brand voice," "video feels native to short-form platforms"). This step is itself LLM-assisted, with the requester reviewing/editing the generated rubric *before* funding escrow — this is also what later powers the natural-language "describe bounty to post" flow from Phase 1.

**3.2 Multi-stage grading pipeline, category-aware:**

1. *Deterministic checks* — schema/format validation, field/count checks, URL reachability, email/domain validation for lead-gen work, duplicate/near-duplicate detection against a requester's existing data using `pgvector` embeddings.
2. *Sandboxed execution* — for code and automation bounties ("Build a Chrome extension," "Develop a trading agent"), actually run the submitted code and its tests inside an isolated sandbox (Docker or a Firecracker microVM), rather than trusting a description of what the code does.
3. *LLM-as-judge* — an object-oriented `JudgeAgent` class built on **LangChain**'s agent/runnable abstractions, with a pluggable model backend (OpenAI by default; NVIDIA NIM-hosted open models as a self-hostable, cost-sensitive alternative), producing structured output: verdict, confidence score, and a human-readable rationale. Never a bare pass/fail — the rationale is what makes disputes resolvable and the whole system explainable to both sides of the marketplace. `RubricAgent` (from 3.1) and `DisputeAgent` (below) share a common base class with `JudgeAgent`, so swapping model providers is a one-line change across the whole oracle, not a rewrite.

**3.3 Confidence-based routing.** High-confidence verdicts auto-resolve immediately (release or return escrow). Low-confidence verdicts, or bounties above a reward threshold, route to a human review queue instead of auto-resolving. This is a deliberate "trust but verify" hybrid — full automation is the end state, not the safe starting point, especially for the categories of work (design, video, subjective research quality) where an LLM judge is least reliable on day one.

**3.4 Dispute/appeal loop.** An agent developer who receives a "fail" verdict can appeal. Appeals trigger a second, independent `DisputeAgent` pass — either a different model or a different prompt for judge diversity — plus optional human escalation, with every outcome logged.

**3.5 Oracle eval harness.** The grading pipeline is itself a product surface that needs regression testing like any other critical system. Maintain a golden dataset of real past submissions per category with known-correct verdicts; run it against every rubric or prompt change before deploying; track false-positive/false-negative rates over time using real dispute outcomes as ground truth. Silent grading drift — the judge quietly getting worse as prompts or models change — is the single fastest way this kind of business loses trust on both sides of the marketplace, so this harness is not optional polish, it's core infra alongside the judge itself.

Pass/fail from the full pipeline triggers the automatic Stripe Connect transfer (agent developer payout) or refund (requester).

### Phase 4 — Trust and reputation

- Per-agent public profile and rating, computed from verified outcomes.
- Weekly leaderboard (with a real cash incentive, matching the observed mechanic) and all-time leaderboard.
- Anti-gaming safeguards: rate limits on submissions, sybil resistance on agent registration (so one developer can't farm the leaderboard with disposable agent identities), and the dispute/appeal flow from Phase 3.4 doubling as the fairness backstop for the rating system too.

### Phase 5 — Growth loop and hardening

- Notifications (new bounty matches for agents, verification results for both sides).
- Smarter matching: skill/category-based routing to relevant agents instead of blasting every bounty to every agent.
- Abuse and fraud monitoring (fake/fabricated submissions, payment fraud on the requester side).
- Observability, load testing, and a security review before opening the platform beyond an initial private/invite cohort — standard practice before scaling a marketplace that moves real money automatically.

### Recommended tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js (React) + TypeScript, Tailwind, deployed on Vercel | Fast to ship a marketplace UI; talks to the Python backend purely over REST |
| Backend APIs | Python, **FastAPI** — separate services for requester-facing API and agent-facing API | Matches the team's Python-everywhere convention; splitting the two APIs isolates agent traffic (bursty, machine-driven) from human web traffic early |
| Data validation | **Pydantic** | Shared schema definitions for bounty requirements, submissions, and verdicts across all services |
| Database | **PostgreSQL** (Supabase or RDS) via SQLAlchemy/SQLModel, with schema managed by a plain Python `create_all`/`drop_all` module rather than a separate migration framework; **Redis** for queues and leaderboard caching | Relational integrity matters for an escrow ledger; Redis suits ephemeral queue/leaderboard state; keeping schema management in-repo Python avoids adding a migration-tool dependency per team convention |
| Payments/escrow | **Stripe Connect** (Python SDK), hold/capture pattern, reconciled against an internal ledger table | Fiat escrow as scoped; never trust Stripe alone as the source of truth for "who's owed what" — always reconcile |
| Agent integration | REST/webhook Agent SDK, API keys/OAuth for developers, **Celery** (Redis/RabbitMQ broker) to fan bounty briefs out to competing agents and collect submissions asynchronously | Agent responses are async and unreliable by nature; needs a real task queue, not synchronous request/response |
| Oracle / verification service | Standalone Python (FastAPI) service: Pydantic rubric schema + LLM-assisted rubric generation; deterministic checks layer (`pgvector` for dedup/fuzzy match); sandboxed execution (Docker/Firecracker) for code bounties; object-oriented **LangChain** agent classes (`JudgeAgent`, `RubricAgent`, `DisputeAgent`) with a pluggable **OpenAI** / **NVIDIA NIM** backend; confidence-based router; eval harness with golden datasets per category | Treated as core infra per the scope decision — decoupled from marketplace CRUD so it can be tested, versioned, and calibrated independently |
| Auth | Clerk or Auth.js on the frontend, verified against a Python auth layer (FastAPI + fastapi-users) | Two distinct account types (requester, agent developer) need separate flows and permissions |
| Infra/observability | Frontend on Vercel; Python services on a container platform (Fly.io, Render, or ECS) + managed Postgres; **Sentry** for errors; PostHog/Amplitude for funnel analytics | Funnel analytics matter disproportionately here given the two-sided cold-start problem — you need to see exactly where each side drops off |

### The two hardest problems, regardless of stack

1. **Cold-starting both sides of the marketplace at once.** Bounty's own near-zero live stats suggest they're still solving this. A realistic plan should consider seeding one side first — e.g., a small set of high-quality in-house or partner agents to guarantee requesters get results while the open agent-developer ecosystem is still thin (this was explicitly *not* the chosen scope, but is worth flagging as the standard playbook other two-sided marketplaces use to survive their first months).
2. **Making automated verification trustworthy enough that requesters release real money with no human in the loop.** This is why Phase 3 is scoped as its own service with its own eval harness rather than a feature bolted onto bounty posting — it's the part of the product most likely to determine whether requesters and agent developers ever trust the platform enough to come back.
