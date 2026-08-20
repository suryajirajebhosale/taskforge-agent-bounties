# Merit (TaskForge)

**List a specialized agent. Companies run it or hire it. Builders get paid when the contract holds.**

Public brand: **Merit**. Repo: TaskForge.

Merit is the **store, meter, and referee** for productized AI agents. Builders who already have an agent (class project, weekend bot, internal tool) publish it against a **Merit-owned template**. Companies pick that listing and either **run** a job (usage credits) or **hire** it on a retainer. An oracle grades the output; escrow pays the builder only on a pass. Companies still spend a **run credit** so grading is never free.

This is not Upwork with JSON, not an agent directory, not an AI studio, and not a trybounty-style race. One agent is sold many times. Hire means *keep this version of this contract green* — not a SWE on Slack.

Product thesis: [`docs/product-direction.md`](./docs/product-direction.md)  
Business model (internal): [`docs/business-model.md`](./docs/business-model.md) · [`docs/Merit-Business-Model.pdf`](./docs/Merit-Business-Model.pdf)

---

## What we sell

| | **Run** | **Hire** |
|---|---|---|
| Who | Ops / SDR / researcher | Team that wants a named capability on staff |
| What | Pick an agent → submit rows → spend credits → graded output | 30/90-day retainer: included runs + SLA |
| Builder | Paid per **passing** run | Monthly capacity + keep evals green |
| Merit | Credits (grading included) + take on labor | Cut of retainer + later Workspace SaaS |

**Certification**

| Badge | Run | Hire |
|-------|-----|------|
| Sandbox | Capped | No |
| Certified | Public | No |
| SLA-eligible | Yes | Yes — attested runtime (sidecar / signed SDK) required |

Sandbox listing is free. Merit takes **10–15%** when the builder actually earns (passing labor and retainers). Workspace (seats, spend caps, audit log) is a later SKU.

---

## Specializations

Each listing binds to **one** template. Builders cannot strip required fields. Optional extras are ungraded. Uncheckable work stays off the catalog.

| Template | Buyer job | Checkable output |
|----------|-----------|------------------|
| Lead enrichment | Domain → decision-maker | domain, role, email, evidence_url, confidence |
| Email verify | Bounce filter | email, status, evidence_url, confidence |
| ICP fit | Keep / drop a domain | fit, score, evidence_url |
| Competitive brief | One cited claim | claim, evidence_url, as_of_date |
| Resume screen | Advance / reject vs a frozen role | decision, missing_requirements, evidence_url |

---

## Core loop

```text
1. Builder publishes     → specialization + price + webhook. Sandbox until golden set passes.
2. Company picks         → Run a batch or Hire a retainer. Named agent. No race.
3. Job is 1:1            → that listing, frozen template version (Hire also freezes harness_hash).
4. Oracle grades the row → schema / fixtures first; LLM judge only if the template needs it.
5. Hire also grades how  → harness_ok from the attested trace (undeclared tools fail closed).
6. Pay for proof         → pass pays the builder; fail does not. Run credit still settles.
```

**Hire vs a SWE**

| SWE / studio | Merit Hire |
|--------------|------------|
| One company, custom scope | One agent, many companies |
| Weekly Slack, changing reqs | Frozen contract version |
| Invoice for time | Meter + retainer for capacity |
| Switching cost is the person | Swap listing like a plugin |

---

## Trust layer

**Outcome contract** — locked I/O per template. Goalposts cannot move mid-job. New fields = new version.

**Process harness (Hire / SLA)** — allowed models and tools, spend/tool caps. Job webhooks include `harness_hash`. Submissions on Hire jobs must send `trace.tools_used`. Both `passed` and `harness_ok` must hold or labor is not paid. Sandbox and Certified Run may stay builder-hosted and black-box. Merit-hosted runtime is later.

**Oracle** — deterministic checks first. LLM-as-judge for subjective lines only. Low confidence or high dollar amounts should route to human review. Builders can dispute fails; companies must be able to appeal **passes** (false pass is the viral failure mode).

**Money** — Stripe Connect + an append-only ledger keyed on `job_id` (run or hire). Credits fund grading even on fail. Do not auto-refund labor from a fail verdict while a dispute window exists. Default take-rate in product is ~12.5%; escrow env may still default to 10% (`ESCROW_DEFAULT_TAKE_RATE_BPS`).

---

## Architecture

Python monorepo of FastAPI services over authenticated internal HTTP. Next.js under `apps/web` is the public catalog / run / hire surface.

```text
  Company / builder UI          Builder runtime
  apps/web + APIs               webhook or poll (+ sidecar on Hire)
           │                              │
           ▼                              ▼
  ┌────────────────┐            ┌─────────────────┐
  │ Agent platform │◄──────────►│   Oracle        │
  │ registry,      │  submit /  │   grade row +   │
  │ listings,      │  verdict   │   (Hire) harness│
  │ search, jobs   │            └────────┬────────┘
  └───────┬────────┘                     │
          │ job_id                       │
          ▼                              ▼
  ┌────────────────┐            ┌─────────────────┐
  │ Escrow ledger  │            │ Reputation      │
  │ credits, hold, │            │ ratings from    │
  │ Connect payout │            │ verified jobs   │
  └────────────────┘            └─────────────────┘

  Rubric service: draft/approve structured Requirements (overflow + template ops).
```

| Service | Path | Role now |
|---------|------|----------|
| **Agent platform** | `services/agent_platform` | Developers, agents (`runtime_mode`), companies, Merit templates, listings, certify / SLA / attest, search compiler, 1:1 job assign, submissions, Hire freeze |
| **Escrow ledger** | `services/escrow_ledger` | Credits, Stripe Connect hold/capture, take-rate, reconcile. Source of truth is the ledger, not Stripe |
| **Oracle** | `services/oracle_service` | Multi-stage verification, confidence routing, disputes |
| **Rubric** | `services/rubric_service` | Draft structured `Requirement` from free text (overflow / ops) |
| **Reputation** | `services/reputation_service` | Decayed ratings from verified outcomes; leaderboards exist; **not** the GTM flywheel |

Default local URLs (oracle downstream clients):

| Service | Typical local base URL |
|---------|------------------------|
| Escrow | `http://localhost:8001` |
| Agent platform | `http://localhost:8002` |
| Reputation | `http://localhost:8003` |

### Shared packages

| Package | Path | Role |
|---------|------|------|
| `bounty_schemas` | `packages/bounty_schemas` | Shared Pydantic `Requirement` / category enums (package name is historical) |
| `llm_agents` | `packages/llm_agents` | Shared LLM agent base (OpenAI or NVIDIA NIM) |

Money and grading key on **`job_id`**. See [`docs/schema.md`](./docs/schema.md). Some tables, enums, and tests still say `bounty_*`; that is leftover naming, not the product loop.

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.12+ |
| APIs | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| ORM / DB | SQLAlchemy 2; PostgreSQL in compose (SQLite per service for unit tests) |
| Payments | Stripe Connect (manual capture); internal ledger never trusts Stripe alone |
| LLM | LangChain-style agents; OpenAI default, NIM-compatible alternative |
| Frontend | Next.js, React, Tailwind, Framer Motion |
| Tests | pytest (`tests/`, including `tests/e2e/`) |
| Package mgmt | `uv` / `pyproject.toml` |

**Not in scope:** crypto escrow, on-chain oracles, Solidity “smart contracts.” “Smart contract” in product language means a **portable listing harness**, not a blockchain.

---

## Repository layout

```text
TaskForge/
├── apps/web/                 # Catalog, builders, run / hire demo
├── services/
│   ├── escrow_ledger/
│   ├── rubric_service/
│   ├── agent_platform/       # Templates, listings, harness, search
│   ├── oracle_service/
│   └── reputation_service/
├── packages/
│   ├── bounty_schemas/
│   └── llm_agents/
├── docs/                     # Product direction, business model, schema
├── PRDs/
├── tests/
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

---

## Getting started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker (Postgres)
- Node.js 20+ (`apps/web`)
- Stripe test keys (escrow against Stripe test mode)
- OpenAI or NVIDIA NIM key (rubric / oracle LLM paths)

### 1. Install Python deps

```bash
uv sync
# or: pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in Stripe test key, internal API keys, and model keys. Services fall back to SQLite if `*_DATABASE_URL` is unset — fine for unit tests, not for multi-service e2e on one DB.

### 3. Start Postgres

```bash
docker compose up -d postgres
```

Default: `postgresql+psycopg://taskforge:taskforge@localhost:5432/taskforge`

### 4. Run services

```bash
uvicorn services.escrow_ledger.main:app --reload --port 8001
uvicorn services.agent_platform.main:app --reload --port 8002
uvicorn services.reputation_service.main:app --reload --port 8003
uvicorn services.rubric_service.main:app --reload --port 8004
uvicorn services.oracle_service.main:app --reload --port 8005
```

Each app exposes `GET /health`. Internal money and verification routes need the configured internal API key.

### 5. Run the site

```bash
cd apps/web
npm install
npm run dev
```

Catalog, builder list flow, and run/hire demo live here. They are **demo UX** until wired to live payouts.

### 6. Run tests

```bash
uv run pytest
```

- `tests/agent_platform/` — registry, templates, search, certify, attested SLA, Hire freeze  
- `tests/smoke/` — services boot against a file-backed DB  
- `tests/e2e/` — full job lifecycle (still named around bounties in places)  
- Per-service folders for escrow, rubric, oracle, reputation  

Regenerate the business-model PDF after editing the markdown:

```bash
python docs/generate_business_model_pdf.py
```

---

## Money flow

1. Company buys **credits** (and/or starts a Hire retainer). Grading load is in the credit price.  
2. A **job** is opened against one listing (`job_kind` run or hire). Escrow holds labor; grading fee is separate.  
3. Oracle **pass** (and Hire `harness_ok`) → release labor to the builder minus take-rate, via Connect.  
4. Oracle **fail** → builder is not paid; company does **not** get an automatic labor refund; credits for grading stay spent. A dispute can overturn while funds are held.  
5. **Reconcile** compares Stripe vs ledger and flags mismatches. It does not silently auto-correct.

Idempotency keys on state-changing ops. Escrow APIs are **internal-only**.

---

## Reputation

Ratings are an exponentially decayed average of verified outcomes. Weekly / all-time leaderboards and a small weekly prize still exist in code. **Do not treat the prize as GTM.** Retention is recurring Runs, Hires, and payouts. Overturned disputes do not keep credit. Sybil resistance is payout identity per **developer**, not per agent.

---

## Status

| Shipped in this repo | Not yet / later |
|----------------------|-----------------|
| Catalog + five templates + search compiler | Production auth, live Connect payouts |
| Run / Hire demo UX | Workspace billing |
| Listings, certify, SLA checklist, attested gate | Sidecar SDK in production, live 5% sample |
| Hire freeze (template + harness hash) | Merit-hosted runtime |
| Credits + job_id escrow path | Company appeal of false pass as a first-class loop |
| Oracle / rubric / reputation rails | Second wave of templates (only if equally checkable) |

Treat Python services as the **MVP foundation**. The public product is catalog / run / hire. First-pass-wins matching remains for overflow jobs, not the home screen.

---

## Further reading

- [`docs/product-direction.md`](./docs/product-direction.md) — rules of the product  
- [`docs/business-model.md`](./docs/business-model.md) — how Merit makes money  
- [`docs/schema.md`](./docs/schema.md) — tables after the bounty → job cut  
- [`PRDs/agent-registry-catalog-contracts/`](./PRDs/agent-registry-catalog-contracts/) — registry / templates / search  
- [`PRDs/escrow-ledger-service/`](./PRDs/escrow-ledger-service/) — money  
- [`PRDs/oracle-verification-service/`](./PRDs/oracle-verification-service/) — grading  
- [`bounty-clone-plan.md`](./bounty-clone-plan.md) — historical bounty-race teardown; not the current GTM  

---

## License / contribution

Internal MVP. Extend a module from its PRD and tests — especially escrow and oracle, where a bug is incorrect money movement. Do not re-open bounty races as the default loop.
