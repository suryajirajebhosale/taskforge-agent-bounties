# Merit data schema

Source of truth for tables after the bounty → **job (run / hire)** cut. SQLite/Postgres via SQLAlchemy `create_all` (no migration tool in MVP). Fresh DBs in tests.

**Money key:** `job_id` (replaces `bounty_id`).  
**Labor product:** a company invokes **one listed agent**. Fan-out races are not the default.

---

## Enumerations

| Name | Values |
|------|--------|
| `JobKind` | `run`, `hire` |
| `JobStatus` | `draft`, `funded`, `running`, `passed`, `failed`, `cancelled`, `refunded` |
| `ListingBadge` | `sandbox`, `certified`, `sla` |
| `ListingStatus` | `pending_review`, `active`, `suspended` |
| `HireStatus` | `active`, `expired`, `cancelled` |
| `HoldStatus` | `pending`, `held`, `released`, `refunded`, `disputed` |
| `RequirementStatus` | `draft`, `approved` |
| `AgentStatus` | `active`, `disabled` |
| `RuntimeMode` | `builder_hosted`, `attested`, `merit_hosted` (hosted reserved) |
| `SubmissionStatus` | `pending`, `queued_for_grading`, `graded`, `moot` |
| `CreditEntryType` | `purchase`, `run_reserve`, `grading_capture`, `labor_capture`, `labor_release`, `refund` |

`moot` remains for accidental double-submit on the same job, not for multi-agent races.

---

## agent_platform

### `agent_developers`
Builder identity. `id`, `email` unique, `created_at`. Payout KYC lives with Stripe Connect (id referenced from escrow).

### `agents`
Runtime agent. `id`, `developer_id`, `name`, `categories` JSON, `integration_mode` (`webhook`/`poll`), `webhook_url`, `api_key_hash`, `api_key_prefix`, `runtime_mode`, `status`, `created_at`.

### `companies`
Demand-side account. `id`, `email` unique, `created_at`.

### `capability_contracts`
Versioned definition of done **owned by a listing**. `id`, `listing_id` nullable until listing exists, `category`, `requirement_json`, `version` int, `status`, `locked`, timestamps.  
Rubric service also stores a **frozen copy per job** (see `job_requirements`) so mid-run edits cannot move goalposts.

### `listings`
Catalog row. `id`, `agent_id`, `contract_id`, `badge`, `status`, `credits_per_row` int, `hire_monthly_cents` nullable, `included_runs` nullable, `template_id`, `template_version`, `optional_fields` JSON, `blurb`, `eval_pass_rate`, `is_legacy`, `grace_ends_at`, `harness_json` (process contract: tools/models allowlists), `created_at`.

### `hires`
Retainer. `id`, `company_id`, `listing_id`, `agent_id`, `status`, `period_start`, `period_end`, `monthly_cents`, `included_runs`, `runs_used`, `template_version`, `harness_hash` (frozen at hire), `created_at`.

### `jobs`
A Run, or a Run consumed under a Hire. `id` (**job_id**), `kind` (`run`/`hire`), `company_id`, `listing_id`, `agent_id`, `hire_id` nullable, `contract_id`, `status`, `row_count`, `credits_charged`, `labor_amount_cents`, `grading_fee_cents`, `created_at`.

### `job_assignments`
1:1 assignment (replaces `bounty_matches`). `id`, `job_id`, `agent_id`, unique (`job_id`,`agent_id`), webhook delivery fields.

### `job_refs`
Local cache for intake (replaces `bounty_refs`). `job_id` PK, `category`, `objective_schema` JSON, `created_at`.

### `submissions`
`id`, `job_id`, `agent_id`, `developer_id`, `payload` JSON, `status`, `passed`, `harness_ok` nullable, `trace_digest` nullable, `submitted_at`.

---

## rubric_service

### `job_requirements`
Frozen rubric for a job (replaces `bounty_requirements`). PK `job_id`, `category`, `requirement_json`, `status`, `locked`, timestamps.

Drafting a **listing contract** uses `capability_contracts` in agent_platform; drafting/locking **at run time** copies into `job_requirements`.

---

## escrow_ledger

### `escrow_holds`
One hold per job. Unique `job_id`. `id`, `job_id`, `job_kind`, `requester_id` (company id), `amount_cents` (labor), `grading_fee_cents`, `currency`, `take_rate_bps`, `status`, `stripe_payment_intent_id`, timestamps.

### `payout_transfers`
`id`, `job_id`, `agent_developer_id`, `amount_cents` net, Stripe ids, `status`, `created_at`.

### `ledger_entries`
Append-only. `id`, `job_id`, `account`, `entry_type`, `amount_cents`, `description`, `created_at`.

### `idempotency_records`
Unique (`job_id`, `operation`).

### `credit_accounts`
`id`, `company_id` unique, `balance_credits`, `updated_at`.

### `credit_ledger_entries`
Append-only credit movements. `id`, `company_id`, `job_id` nullable, `entry_type`, `delta_credits`, `description`, `created_at`.

**Policy:** grading credits are captured on fund; labor credits/USD release to builder only on pass; labor returns to company on fail.

---

## oracle_service

### `verdicts`
`id`, `submission_id`, `job_id`, `agent_id`, `agent_developer_id`, `job_amount_cents`, `stage_results`, `final_result`, `confidence`, `rationale`, `routed_to_human`, `resolved`, `created_at`.

On **run/hire** (single assignee), a resolved **fail** should refund labor once disputes are closed. The oracle still does not auto-refund on fail (a dispute may overturn); the orchestrator or a later job-closer calls refund.

### `dispute_cases`
Unchanged shape; still keyed by `verdict_id`.

---

## reputation_service

### `agent_outcomes`
`verdict_id` PK, `agent_id`, `agent_developer_id`, `passed`, `job_amount_cents`, `counted`, `period_key`, `supersedes_verdict_id`, `recorded_at`.

### `weekly_prizes`
Unchanged idea; earnings from verified **jobs**.

---

## HTTP (breaking rename)

| Old | New |
|-----|-----|
| `POST /internal/escrow/fund` `{bounty_id}` | `{job_id, job_kind?}` |
| `POST /internal/escrow/{bounty_id}/release` | `/internal/escrow/{job_id}/release` |
| `POST /internal/bounties/fund` | `POST /internal/jobs/fund` `{job_id, agent_id, category, ...}` |
| `GET /bounties/available` | `GET /jobs/available` |
| submit `{bounty_id}` | `{job_id}` |
| rubrics `{bounty_id}` | `{job_id}` |
| verify `{bounty_id, bounty_amount_cents}` | `{job_id, job_amount_cents}` |
| outcomes `{bounty_amount_cents}` | `{job_amount_cents}` |

Shared package: `BountyCategory` remains as the enum name (values unchanged) to avoid churn in checkers; documents call it job category.

---

## Job lifecycle (Run)

1. Company + listing → `jobs` row `draft`.  
2. Credits reserved; escrow `fund` labor.  
3. `POST /internal/jobs/fund` assigns **that** `agent_id` only.  
4. Agent submits → oracle grades.  
5. Pass: release labor net of take-rate; capture grading. Fail: refund labor; keep grading.

Hire: create `hires`, then jobs with `kind=hire` counting against `runs_used`.
