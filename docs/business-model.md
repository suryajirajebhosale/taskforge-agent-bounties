# Merit — Business Model

**Confidential — internal strategy document**  
**Entity working name:** TaskForge / public brand: Merit  
**Date:** 20 August 2026  
**Status:** Operating thesis after catalog / run / hire pivot; attested harness on Hire  

---

## 1. Executive summary

Merit is a two-sided software marketplace that turns **already-built AI agents** into metered, payable labor. It is not a freelance board, not an agent directory, and not a staff-augmentation firm.

**Offer**

- **Builders** publish an agent with a *capability contract*: locked I/O **and** (for Hire) a *process harness* (allowed tools/models). Idle work from university projects, hackathons, and internal tools can earn when companies invoke it.
- **Companies** **run** a job (usage credits against that contract) or **hire** the agent on a retainer (included runs + SLA). They pick a named agent. They do not post a race.
- **Merit** is the store, meter, and referee: catalog, certification, grading (oracle), **runtime attestation on Hire**, escrow/payout, reputation.

**How we make money (both sides)**

| Side | What they pay | Why they pay |
|------|----------------|--------------|
| Companies | Run credits (grading included); hire retainers; workspace SaaS | Risk transfer, meter, audit, swappable vendors |
| Builders | 10–15% of passing runs and retainers; optional certification | Distribution, trust, payouts — not a big SaaS fee before GMV |

**What we refuse to be:** Upwork with JSON. If the buyer needs a human on Slack every week, that is services. Hire means *keep this version of this contract green*.

**90-day wedge:** a **family of checkable specializations** (enrich, verify, ICP fit, cited competitive brief, resume screen), certified catalog, run + hire, no open bounty race as the default loop. Not “any agent.”

---

## 2. Vision, mission, positioning

**Vision.** Agent labor is bought like an API: contracted, metered, replaceable, and paid only when the contract holds — with a human builder still on the hook for the product.

**Mission.** Give people who already built an agent a way to get paid without becoming salespeople; give companies a way to buy that capability without hiring a SWE to babysit a prototype.

**Category.** *Productized agent labor marketplace* (app-store economics + payroll rail), not *task bounty board*.

**Brand line.** Merit is earned, not claimed. Certification and verified outcomes are the trust layer.

**Anti-positioning**

| We are not | Why |
|------------|-----|
| Upwork / Fiverr | Supply is software with a frozen contract, not hours |
| Gitcoin / crypto bounties | Fiat, Stripe Connect, no chain |
| Agent directories | We transact and grade; listing is not the product |
| OpenAI GPT Store | We pay independent builders in cash for *jobs*, not chat |
| An AI studio / agency | We do not sell custom builds as the core SKU |
| trybounty.ai-style race boards | First-pass-wins races are overflow, not the home screen |

---

## 3. Problem

### 3.1 Companies

Repeatable work (enrich a list, score applicants, structured research) is either: slow freelance, an internal intern, or “someone’s ChatGPT.” None of those give a locked definition of done, a meter, or a vendor they can swap. Fully automated tools hallucinate with no escrow.

They will not trust auto-payout on fuzzy work. They *will* pay for a schema, a badge, and a refund of **builder** compensation on fail.

### 3.2 Builders (students, indie hackers, internal toolmakers)

Thousands of agents exist and sit idle. There is no default path from “it works in my repo” to “a company paid me.” Selling it themselves means BD, invoicing, KYC, and arguments about quality. Hiring on as a SWE recreates a job they did not want.

### 3.3 Why the old bounty-race model fails

Two-sided cold start, first-pass-wins races the grader, six categories of uncheckable work, take-rate-only-on-success while grading still costs money, and a clone of a product that already showed empty liquidity. That loop is retired as the default product.

---

## 4. Solution and products

### 4.1 Capability contract

The product is the **contract**, not the chat. Two layers, one version:

- **Outcome (all listings):** input schema, output schema, objective checks, optional subjective rubric. Mid-job goalposts cannot move. New I/O fields = new version.
- **Process / harness (SLA and Hire):** allowed models and tools, memory, spend/tool caps, PII/residency flags, live sample rate. New tool or model = new listing version. Hire pins `template_version` **and** `harness_hash`.

This is *not* a blockchain. It is a portable manifest (the listing) plus fail-closed enforcement on Hire — the same idea as a service-mesh sidecar, attached to the SKU we sell.

**Live specializations (each is its own Hire SKU)**

| Template | Buyer job | Checkable output |
|----------|-----------|------------------|
| Lead enrichment | Domain → decision-maker | domain, role, email, evidence_url, confidence |
| Email verify | Bounce filter | email, status, evidence_url, confidence |
| ICP fit | Keep / drop a domain | fit, score, evidence_url |
| Competitive brief | One cited claim | claim, evidence_url, as_of_date |
| Resume screen | Advance / reject vs a frozen role | decision, missing_requirements, evidence_url |

A builder lists **one** of these, not a generalist bot. Content-media and “AI automation” stay off the catalog until they are as checkable as the rows above.

### 4.2 Certification (listing badges)

These badges are **trust / unlock gates**, not pricing plans. Pricing (Runs / Hire / Workspace) sits on top.

| Badge | May Run | May Hire | What Merit verifies | Where the agent runs (today) |
|-------|---------|----------|---------------------|------------------------------|
| Sandbox | Capped | No | Outcome on eval fixtures + dollar cap | **Builder-hosted** webhook — black box OK |
| Certified | Public | No | Outcome on shared golden set (row-only) | **Builder-hosted** — black box OK |
| SLA-eligible | Yes | Yes | Outcome **and** process (`harness_ok`) | Builder-hosted **or** later Merit-hosted, but **must be attested** (sidecar / signed SDK) |

**Mental model:** Sandbox = prove it exists. Certified = prove the contract. SLA-eligible = prove the *how* when someone retains you.

**Where agents run (FAQ that will keep coming up):** Merit is the store, meter, and referee — not (yet) the machine. Sandbox and Certified builders keep a webhook alive on their own VPS, container platform, or any persistent agent runtime. Host choice does not change grading: Certified Run stays outcome-only. Hire may use the same host class, but attestation is mandatory. **`merit_hosted`** (Merit operates the box) is a later SKU and still does not replace the harness check. Do not mandate a sidecar on Sandbox.

### 4.3 Run (usage)

Company selects an agent, submits a batch (e.g. domains), spends **credits**. Oracle grades the **row**. **Builder is paid only on pass.** Credits for **grading always settle** (platform is not a charity on fails). Certified Run does not require a process trace.

### 4.4 Hire (retainer)

30/90-day named capability: included runs, SLA (latency, eval floor), maintenance = keep evals green / patch broken upstreams. Not custom scope. Slack only for eval-red.

Hire jobs carry **two verdicts**: `passed` (oracle vs I/O) and `harness_ok` (trace vs declared tools/models). Both must hold or labor is not paid. A live sample of traffic can later trip the same grace/legacy path as a template bump. Merit-hosted runtime (we run the harness) is a later SKU, not launch.

### 4.5 Workspace (B2B SaaS)

Seats, spend caps, audit log, private catalog of hired agents, SSO later, human-review add-on above a dollar threshold.

### 4.6 Overflow (not default)

If no listing fits, an open request can exist later. It is not GTM year one.

---

## 5. Customers and jobs-to-be-done

### 5.1 Company segments (demand)

1. **SDR / growth agencies** — enrich and refresh lists weekly (best first ICP).  
2. **In-house demand gen** — same job, procurement slower, higher ACV via Workspace + Hire.  
3. **Recruiting teams** — later category (schema-scorable, not “find me a vibe”).  
4. **Research ops** — only when citations + required fields are the contract.

**Buyer vs user.** User: operator pasting CSVs. Buyer: head of growth / finance once retainers and seats appear.

### 5.2 Builder segments (supply)

1. Students / hackathon teams (Sandbox volume).  
2. Indie hackers with one sharp agent (Certified GMV).  
3. Small studios productizing a playbook (SLA / Hire).  

**Not a target:** SWE who wants a full-time contract to *build* a bespoke agent. That is Upwork. We may later refer them out; we do not productize it as Hire.

### 5.3 Jobs-to-be-done

- Company: “Get N valid rows by Friday without hiring a contractor.”  
- Company: “Keep this enricher on staff like a vendor.”  
- Builder: “Get paid for the bot I already wrote without selling.”  

---

## 6. Value proposition and differentiation

**Companies:** locked contract, named agent, meter, refund of labor on fail, replaceability, audit trail.

**Builders:** distribution, KYC/payout, reputation, no sales cycle for small runs.

**Moat (earned, not claimed):** labeled runs + dispute outcomes + category eval sets **+ attested Hire traces**. The oracle *with calibration* is compounding. The harness hash on the job envelope is what legal/security can show. A sidecar without settlement is an enterprise control plane (not our company). The UI is not the moat.

**Bright line vs hiring a SWE**

| SWE / studio | Merit Hire |
|--------------|------------|
| One company, custom scope | One agent, many companies |
| Weekly Slack, changing reqs | Frozen contract version |
| Invoice for time | Meter + retainer for capacity |
| Switching cost is the person | Swap listing like a plugin |

If a deal violates the right column, decline or price as services (out of band).

---

## 7. Market

**TAM (conceptual):** spend on outsourced lead gen, list building, research ops, and “AI automation” contractors that could become schema-bound jobs.

**SAM:** teams that already buy data enrichment or SDR list work and will try an agent if the contract is checkable.

**SOM (year 1):** English-speaking teams buying checkable sales/research/recruiting rows; dozens of builders across the five templates; tens of companies; not a horizontal “any task.”

**Trends:** agent frameworks are cheap; buyers are burned by hallucination; Stripe Connect is a known pattern; universities produce agents as coursework.

**Honest constraint:** substitutes are “intern + Clay/Apollo + ChatGPT.” We must beat that on *ops time and dispute rate*, not on “AI.”

---

## 8. Competitive landscape

| Player | Relation | How we differ |
|--------|----------|----------------|
| trybounty.ai and bounty clones | Direct analog of our *old* loop | We sell catalog + hire, not races |
| Upwork / Fiverr | Human labor | Contract + software utilization |
| Clay, Apollo, ZoomInfo | Data vendors | We are a labor rail; we may *use* them inside agents (pass-through cost) |
| LangChain / agent hosts | Infra | We are the commercial and trust layer |
| Internal “agent mesh” / sidecar governance | Same *idea* as our Hire harness | They govern IT estates; we attach the contract to **payout** |
| Internal IT / SWE | Default alternative | We win on reuse and meter, lose on unique internal systems |
| AI agencies | Custom build | Different SKU; we can lose every custom RFP |

---

## 9. Business model (how value is captured)

### 9.1 Model type

**Hybrid:** transactional marketplace (take-rate on GMV) + SaaS (workspace) + usage (credits that fund grading).

Builders are not employees. Companies are customers. Merit is the marketplace operator and verification utility.

### 9.2 Revenue streams (in priority)

1. **Credit sales / run usage** — company prepays or pays per run. Bundle grading. Gross margin after LLM + enrichment APIs + Stripe.  
2. **Take-rate on builder labor** — 10–15% of amounts paid to builders on **pass** and of **hire** retainers.  
3. **Hire retainers** — monthly; platform cut + possible workspace attach.  
4. **Workspace SaaS** — seats / workspace fee once there is a second user or spend cap need.  
5. **Certification** — deposit or fee (spam filter more than profit center).  
6. **Human review add-on** — cost-plus on high-value runs.  
7. **Later:** oracle API for companies running *their own* agents (SaaS, decoupled from liquidity).

**Explicitly not year-one:** ads, selling customer lists, crypto, taking a cut of failed labor (we do not pay builders on fail; we *do* keep grading).

### 9.3 What each side pays (message)

- Companies: “You don’t pay the **builder** if the contract fails. You still pay **Merit** to run the referee.”  
- Builders: “Listing Sandbox is free. We take 10–15% when you actually earn.”

### 9.4 Pricing architecture

**Credits.** Internal unit. Example: 1 credit = $0.01. Enrichment row priced 8–18 credits depending on listing. Grading cost loaded into the credit price, not a surprise invoice.

**Hire.** Listing sets monthly USD (e.g. $320–$490 in the demo catalog) with included row/run budget. Overage = Run credits. SLA-eligible only.

**Workspace.** Start $0 with one seat; paid when SSO / extra seats / private catalog — e.g. $199–$799/mo illustrative, not committed.

**Take-rate.** Default 12.5% (1,250 bps) of builder labor; configurable per category later. Escrow code historically used 1,000 bps (10%).

### 9.5 Illustrative unit economics (enrichment Run)

Assumptions for a **passing** 100-row job at $0.12/row = $12 labor sticker:

- Company credits charged: $12 labor + ~$2 grading load = **$14** (example).  
- Builder net at 12.5% take: **$10.50**.  
- Platform: $1.50 take + $2 grading charge − actual LLM/API/Stripe.  
- If actual grading+data = $1.20 and Stripe ~3% of captured volume, contribution is positive.  
- **Fail:** company loses grading load (~$2); labor not paid; builder $0; we must still cover LLM. **This is why grading is never free.**

**Hire:** $490/mo, 4,000 included rows. If utilization is high, this is a discount to list price — fine if it locks a workspace and predictable eval cost. If utilization is tiny, still valuable (reserved capacity). Watch support load.

### 9.6 Cost structure

- Variable: LLM judge, drafter, embeddings, enrichment APIs, Stripe fees, sandbox compute, Connect payouts.  
- Semi-variable: human review queue, disputes, KYC reviews.  
- Fixed: engineering, eval harness, brand, campus GTM, insurance/legal.  

**Contribution margin target (steady state, enrichment):** >40% on Run credits after variable costs; take-rate is high-margin; Workspace is high-margin. **Do not** use Micro $1 jobs as the P&amp;L.

### 9.7 Capital and cash

Stripe Connect: delayed payouts, chargebacks on company cards, reserve. Credits are a liability (unearned usage) until consumed. Hire is deferred revenue. Do not spend credit float on opex.

---

## 10. Go-to-market

### 10.1 Supply first, but gated

Invite ~20 builders who already enrich leads. Shared eval set. Sandbox → Certified. Do not open listing to the internet until spam appears (it will).

Campus: clubs, ML courses — Sandbox only. Pitch: “your project can earn on a weekend,” not “quit school.”

### 10.2 Demand

Agencies first (they already resell list work). Guarantee a result with a **first-party Merit enricher** so the first 10 companies are never empty-catalog. Then introduce third-party listings as cheaper/faster alternatives.

Motion: founder-led, then content (eval pass-rates, sample contracts), then partnerships with bootcamps.

### 10.3 Why not paid ads first

CAC on a two-sided marketplace with unproven oracle will burn cash. Design partner cohort instead.

### 10.4 Retention

Companies: recurring Runs (list refresh) and Hires. Builders: payout + reputation. Do not rely on a $25 weekly prize as a flywheel.

---

## 11. Operations and trust

**Oracle:** deterministic checks first (schema, counts, dupes, URL/email validators via third parties where possible). LLM judge only for weighted subjective lines. Confidence routing: low confidence or high $ → human. Disputes: builders appeal fails; **companies must be able to appeal passes** (false pass is the viral failure mode).

**Harness (Hire):** fail closed on undeclared or denied tools. Job webhook includes `harness_hash`. Submission stores `trace_digest` and `harness_ok`. Do not run a sidecar on Sandbox.

**Eval harness:** golden set per category; block deploys on regression. Dispute outcomes feed the set. Live sample vs certified pass-rate uses the existing listing grace window.

**Payouts:** Stripe Connect Express; KYC on builder; sybil resistance on payout identity, not agent count.

**Support:** Hire customers get eval-red tickets. Sandbox builders get docs, not white-glove.

---

## 12. Legal, risk, and compliance (non-exhaustive)

Not legal advice. Engage counsel before real money.

- **Marketplace vs employer.** Builders are independent vendors; contracts, tax forms, no employee branding.  
- **Payments.** Stripe TOS, connected accounts, possible money-transmitter analysis depending on jurisdiction and who holds funds. Escrow language must match actual Stripe hold/capture.  
- **Chargebacks.** False-pass lead lists will generate them. Policy + reserves + appeal window.  
- **Data / privacy.** Lead gen = personal data. GDPR/CCPA, purpose limitation, DPA with companies, prohibit using Merit to build spam cannons in ToS.  
- **Scraping and platform ToS.** Agents that violate LinkedIn/etc. ToS create secondary liability risk — **deny-list those tools on the harness** and forbid them in ToS. Enforcement is still imperfect on unattested Run.  
- **CAN-SPAM / CASL.** We grade lists; customers send mail. Disclaim and prohibit illegal outreach.  
- **Export / sanctions.** Stripe + KYC.  
- **IP.** Builder warrants they can license the agent; company gets output license.  
- **Consumer vs B2B.** Prefer B2B; student builders still need capacity to contract.  
- **Insurance.** E&amp;O / cyber once GMV exists. Do not sell a “pass guarantee” as insurance unless priced as such.  

**Product risks:** grader/generator collusion; sandbox RCE; prompt injection against the judge; reputation farming; credit fraud.

---

## 13. Organization

Year-one functions (can be few people): product/eng (oracle + escrow), ops (KYC, disputes, review queue), GTM (agencies + campus), finance (reconcile ledger vs Stripe).

Do not staff a services delivery team. That pulls the company into an agency.

---

## 14. Metrics and targets (directional)

**North star:** weekly **verified passing rows** (or jobs) in enrichment — not “agents registered.”

**Demand:** companies with ≥1 paid run / 30d; Hire conversion; credit attach.  
**Supply:** Certified listings with ≥1 run / 30d; builder payout > $0.  
**Trust:** dispute rate, false-pass rate (company appeals), eval regression.  
**Unit:** contribution per passing run; grading cost / run; take-rate realized.  
**SaaS:** workspace logos, NRR later.

Vanity to ignore: registered agents, Sandbox listings, weekly prize engagement.

---

## 15. Financial scenarios (illustrative, not a forecast)

**Year 1 conservative.** 25 companies, $400/mo average Run spend, 5 Hires at $400/mo, 12.5% take on ~60% of spend that is labor, rest credits/grading. Revenue might be low-six-figures or less. Fine if eval data and design partners are real.

**Year 1 upside.** 80 companies, mix of Hire + Workspace, enrichment APIs negotiated. Still a seed-scale marketplace.

**Failure mode.** High fail rate + free grading + Stripe fees = negative unit economics while marketing a “pay only for results” slogan. The credit policy exists to prevent this.

Do not raise on GMV of uncapped Micro jobs.

---

## 16. Roadmap alignment

| Now | Next | Later |
|-----|------|--------|
| Catalog, five specializations, Run/Hire, listings, credits, certify, search, attested Hire gate | Live sample / sidecar SDK in production | Merit-hosted runtime, Workspace billing, oracle API |
| Checkable templates only | Company appeals, validators per template | More templates only when I/O is as checkable as these five |

Python services historically used `bounty_id` and first-pass-wins matching. The data model in `docs/schema.md` is the source of truth going forward.

---

## 17. Strategic options (keep on the table)

1. **Double down on marketplace GMV** if Certified supply and agency demand both fill.  
2. **Oracle + credits as SaaS** if liquidity stays thin but teams want a referee for *internal* agents.  
3. **Kill Hire** if every Hire ticket is custom SWE — it was a positioning leak.  
4. **Kill campus** if Sandbox quality destroys trust — keep indie Certified only.

---

## 18. FAQ (internal + site copy source)

### What are Sandbox, Certified, and SLA-eligible?

Listing badges. Sandbox = capped eval/demo. Certified = public Run after golden set. SLA-eligible = Certified + checklist + attested runtime → Hire unlocked. Not the same thing as the Runs / Hire / Workspace price cards.

### Where do Sandbox and Certified agents run?

On the **builder’s host** (webhook). Merit does not run their process at launch. Persistence (VPS, containers, always-on agent runtimes) is the builder’s ops problem; Merit grades outputs. When people ask “where do tiers run their agents?”, answer: Sandbox/Certified = builder-hosted; SLA/Hire = attested wherever they run; Merit-hosted = later.

### What’s the difference between Run and Hire?

Run = metered credits against a listed contract. Hire = 30/90-day named retainer, productized maintenance (keep evals green), frozen template + harness. No custom Slack scope in-product.

### Do companies pay if the agent fails?

Not the builder. They still spend a run credit (grading is funded). Hire labor pays only if `passed` and `harness_ok` both hold.

### What is the SLA sidecar / harness?

Declared tools, models, spend. Trace digest on Hire submissions; undeclared tools fail closed. Sandbox/Certified do not require it.

### Can builders list any agent?

No — Merit templates only at launch (five checkable specializations). Uncheckable work stays off-catalog.

### What does Merit take?

Sandbox listing free. 10–15% of passing labor and retainers. Credits fund grading. Workspace later.

### Does Merit host agents?

Not at launch. Host ≠ harness. Attestation for Hire; Merit-operated runtime reserved.

---

## 19. Summary for investors or partners

Merit sells **contracted agent labor** with a referee. Companies pay for runs, retainers, and workspace. Builders pay a take-rate when they earn. Hire is the same I/O contract **plus** a process harness that can fail closed — not a SWE on Slack, not a blockchain, not an enterprise agent mesh. The wedge is five checkable specializations, not a universal bounty board. The business works only if grading is paid, Hire stays productized and attested, and each template’s eval set becomes real IP. When asked where agents run: Sandbox/Certified on the builder’s box; Hire attested on that box (or later Merit-hosted); the referee is always Merit.

---

*End of document.*
