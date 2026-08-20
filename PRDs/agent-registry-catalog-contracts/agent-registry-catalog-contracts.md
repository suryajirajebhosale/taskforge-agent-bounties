# PRD: Agent registry, catalog search, contracts, review, and maintenance

*Merit marketplace — catalog / run / hire. Locked in design review 19 August 2026.*

**Triage:** needs-triage

## Problem Statement

Builders already have agents (class projects, side work) but cannot sell them as a product: there is no standard way to register, no shared definition of “done,” no fair review, and no rule for what happens when Merit changes the job spec. Companies cannot find an agent to hire with a sentence of English without landing on incompatible one-off schemas. If Hire means “keep customizing on Slack,” Merit is staff-aug, not a store. Agents also run on the builder’s machine today; companies that retain an agent will later need a stronger runtime story without blocking launch.

## Solution

Merit owns **category templates** (launch: lead enrichment). A builder registers as a **developer**, an **agent** (runtime identity: webhook or poll, API key, `runtime_mode`), and one or more **listings** (template version + price + badge). Companies search in English; an LLM **compiles** that into filters and a published ranking on that template’s catalog — not a vibe ranking of bios. **Certified** means passing the shared golden set. **SLA / Hire** adds a human ops/KYC/canary checklist. New customers get the latest template; **active Hires stay frozen** on the listing version they bought until the period ends. Launch runtime is **builder-hosted**; Hire/SLA later requires Merit-hosted or attested runtime. The oracle still grades frozen requirements; escrow still moves on `job_id`.

## User Stories

1. As a builder, I want to create a developer account, so that listings and payouts attach to me, not a disposable bot identity.
2. As a builder, I want to register an agent with a name, categories, and webhook or poll mode, so that Merit can assign jobs without hosting my process.
3. As a builder, I want a one-time API key at agent creation, so that only my runtime can submit results.
4. As a builder, I want the publish UI to feel like one wizard while still creating developer, agent, and listing records, so that campus users are not blocked by three dashboards.
5. As a builder, I want to create a listing against an official template version, so that companies and the oracle share one definition of done.
6. As a builder, I want to set credits-per-row and optional Hire monthly price on a listing, so that I can sell Run and Hire without rewriting the agent.
7. As a builder, I want my listing to start as Sandbox, so that I can take capped runs before I am trusted.
8. As a builder, I want to declare `runtime_mode = builder_hosted` at launch, so that we can require a stronger mode for SLA later without a schema rewrite.
9. As a builder, I want webhook delivery with retries when a job is assigned, so that a brief outage does not silently drop work.
10. As a builder using poll mode, I want `GET /jobs/available` to show only jobs assigned to my agent, so that I do not scrape the whole market.
11. As a builder, I want to rotate or disable an agent, so that a leaked key cannot keep earning.
12. As a builder, I cannot remove required template fields, so that I cannot sell a listing that the oracle cannot grade.
13. As a builder, I want optional extra fields on a listing that are stored but ungraded, so that I can experiment without forking the official contract.
14. As a company, I want to describe who I want to hire in plain English, so that I do not need to know template IDs.
15. As a company, I want search to pick the matching official template first, so that I am not shown incompatible agents.
16. As a company, I want results filtered by badge, max price, min eval pass-rate, and Hire eligibility, so that I can constrain risk and budget.
17. As a company, I want a published ranking (eval, rating, price, recency) — not bio embeddings — so that a witty description cannot beat a 94% eval agent.
18. As a company, I want a short explanation of why each listing matched, so that I trust the compiler.
19. As a company, I want to open a listing and see input/output, template version, badge, and runtime mode, so that I know what I am buying.
20. As a company, I want to Run against that frozen contract, so that goalposts cannot move mid-job.
21. As a company, I want to Hire only SLA-eligible listings, so that retainers are not student laptops with no KYC.
22. As a platform operator, I want a golden dataset per template version, so that Certified is objective.
23. As a builder, I want to trigger certification and see per-fixture pass/fail diffs, so that I can fix the agent without arguing with a human.
24. As a builder, I want retries on certification after code changes, so that one fail is not a ban.
25. As a platform operator, I want a deploy gate when fixtures or the judge change, so that Certified does not silently drift.
26. As a platform operator, I want SLA promotion to require KYC, ToS, a live canary job, and webhook uptime — not a taste review — so that Hire is a vendor bar.
27. As a builder, I want a ticket (not a model debate) when the SLA checklist fails, so that I know what ops item to fix.
28. As a platform operator, I want to bump a template to vN+1 with a changelog, so that the market can move together.
29. As a builder, I want a grace window (14–30 days) to recertify on vN+1, so that I am not unpublished overnight.
30. As a company with an active Hire, I want my retainer to stay on the frozen listing + template version I bought, so that a Merit bump does not change my contract mid-period.
31. As a company starting a new Run or Hire after a bump, I want the latest template by default, so that I am not sold a sunset schema.
32. As a builder, I want to publish a new listing version for vN+1 rather than mutate the frozen Hire version, so that existing customers are not surprised.
33. As a company, I want legacy listings after grace to drop out of search but remain on a direct link as legacy, so that bookmarks do not 404 while the catalog stays clean.
34. As a builder, I want “maintenance” defined as keeping evals green on versions I still sell (including my own scraper breakages), so that I am not on the hook for open-ended features.
35. As a platform operator, I want to refuse custom Slack scope on Hire, so that we do not become an agency.
36. As a company, I want the agent to run on the builder’s infrastructure at launch, so that Merit can ship without a container platform.
37. As a company on SLA/Hire (future), I want runtime that is Merit-hosted or attested, so that I am not depending on an unaudited laptop.
38. As a builder (future), I want a path to attach Merit-hosted or attested runtime without recreating my listings from scratch.
39. As an agent runtime, I want a clear job payload (job id, frozen requirement, input rows, deadline), so that I can complete work without scraping the UI.
40. As an agent runtime, I want to POST a structured submission and get validation errors immediately, so that I do not wait for a full oracle cycle on schema mistakes.
41. As a platform operator, I want only the assigned agent to submit to a job, so that races cannot hijack a Hire.
42. As a company, I want the oracle to grade the frozen requirement, so that payout still depends on proof.
43. As a builder, I want a fail verdict with rationale and fixture ids, so that I can improve the agent.
44. As a builder, I want to dispute a job fail without that being the same path as a certification fail, so that live jobs and onboarding stay separate.
45. As a company, I want to appeal a false pass on a Run (follow-on if not fully in this slice), so that a bad list cannot silently drain credits.
46. As a platform operator, I want payout KYC on the developer, not per agent, so that sybil listings cannot multiply prize or Hire eligibility.
47. As a finance operator, I want labor still held through a fail until dispute window/close, so that an overturn can still pay.
48. As a search quality owner, I want listing blurbs for display only, so that ranking stays on checkable attributes.
49. As a campus builder, I want Sandbox caps, so that I can earn eval data without taking unlimited company risk.
50. As a platform operator, I want to log compiler queries (NL → filters) without storing unnecessary personal data from pasted lists, so that we can improve search without becoming a data broker.

## Implementation Decisions

- **Runtime launch:** Builder-hosted only (`runtime_mode = builder_hosted`). Merit assigns a job; the builder’s process executes; submission is pushed to intake. Oracle sandbox remains a grader for submitted artifacts, not the agent host.
- **Runtime later (explicitly phased):** SLA/Hire requires `merit_hosted` or `attested` runtime. Field exists on the agent (or Hire-eligible listing) from this PRD so the later cut is not a rewrite.
- **Identity model:** Three records — developer, agent, listing. UI may wizard them in one flow.
- **Contracts:** Merit-owned category templates. Launch template is sales/lead enrichment with a fixed required I/O. Builders cannot strip required fields. Optional extras are ungraded until promoted into an official template version.
- **Search:** LLM is a query compiler: natural language → template selection + structured filters + sort. Ranking formula is published (eval pass-rate, rating, price, recency). Match explanation is returned. Semantic ranking of marketing blurbs is forbidden as the primary ranker.
- **Review:** Certified = automated golden-set pass for that template version (same family of pipeline as the oracle, fixtures not live customer data). SLA/Hire = Certified plus human checklist (payout KYC, ToS/abuse, canary job, webhook availability). Humans do not re-score subjective quality for promotion.
- **Versioning:** Dual-run. New Runs/Hires default to latest template. Active Hire pins `listing_id` + `template_version`. Grace window (configurable, default in the 14–30 day range) for recertification after a bump; then non-recertified listings are excluded from search and marked legacy on direct URL.
- **Maintenance definition:** Keep evals green on versions still sold. Template changelog is Merit’s. Custom scope is out of product.
- **Job assignment:** One agent per job (already the post-bounty API). Second assignee rejected.
- **Modules to build or extend:**
  - Agent registry (developer, agent including runtime_mode, listing, keys, webhook/poll).
  - Template catalog (versions, required fields, golden fixtures, grace/sunset).
  - Search compiler (NL → filters/rank/explanation).
  - Certification (golden-set runner + SLA checklist state machine).
  - Job runtime A (assign + intake; existing agent platform).
  - Hire version freeze (retainer pin + bump notifications).
- **Consume, don’t fork:** Oracle grades frozen requirement; escrow/credits stay on job id; reputation stays on verified outcomes.
- **Hosted runtime (C):** Not implemented in this PRD; only the mode enum and Hire eligibility rule that will require it later.

## Testing Decisions

Good tests assert **external behavior**: given a registration, search query, fixture pack, or template bump, assert badges, assignment, freeze, and search inclusion — not prompt text or private helpers.

- **Agent registry:** Wizard still yields three records; webhook without URL rejected; poll agent sees only assigned jobs; second agent cannot bind an already assigned job; key shown once.
- **Template catalog:** Listing missing a required field rejected; optional extra stored and not used in golden-set pass/fail; vN+1 bump records changelog and starts grace.
- **Search compiler:** Fixture NL queries compile to expected template + filters; ranking prefers higher eval over richer blurb; explanation present; unknown template intent returns a clear empty state.
- **Certification:** Golden-set pass → Certified; fail returns fixture-level errors and stays Sandbox; SLA checklist incomplete cannot Hire; canary failure blocks SLA.
- **Hire freeze:** Active hire still grades against pinned version after a bump; new hire uses latest; after grace, old listing omitted from compiled search.
- **Prior art:** Agent platform registration, assignment, webhook retry tests; oracle/rubric golden-set harness pattern (accuracy thresholds for LLM stages, exact asserts for deterministic stages).

Modules under test for this PRD: registry, template catalog, search compiler, certification, hire freeze. Hosted runtime is not tested here.

## Out of Scope

- Merit-hosted or attested runtime implementation (phase C).
- Additional official templates beyond lead enrichment (the versioning machinery must allow them).
- Custom per-company contracts and Slack feature work as Hire.
- Embedding/blurb-primary search.
- Human taste grading as the Certified bar.
- Instant force-upgrade of active Hires onto a new template.
- gRPC/MCP agent protocols.
- Company appeal of false pass (may follow; not required to ship registry + search + cert).
- Changing escrow’s “no auto-refund on fail” behavior (dispute window still applies).

## Further Notes

This PRD replaces the bounty-race onboarding story for supply and discovery. Existing escrow, oracle, and reputation services remain the money and proof rails. Campus listings stay Sandbox-capped until Certified. “You decide” defaults used where the builder deferred: three-record registry, template ownership, compiler search, hybrid review, dual-run versioning, A-then-C runtime.
