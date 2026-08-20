from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .exceptions import (
    AgentNotFound,
    AttestationRequired,
    CertificationFailed,
    DeveloperNotFound,
    InvalidApiKey,
    JobAlreadyAssigned,
    JobNotRegistered,
    NotAssignedToJob,
    SlaChecklistIncomplete,
    SubmissionNotFound,
    SubmissionValidationError,
)
from .harness import check_trace, harness_hash, merge_harness
from .models import (
    Agent,
    AgentDeveloper,
    AgentStatus,
    CapabilityContract,
    Company,
    Hire,
    HireStatus,
    IntegrationMode,
    Job,
    JobAssignment,
    JobKind,
    JobRef,
    JobStatus,
    Listing,
    ListingBadge,
    ListingStatus,
    RuntimeMode,
    SlaChecklist,
    Submission,
    SubmissionStatus,
    _now,
)
from .rate_limiter import RateLimiterConfig, SubmissionRateLimiter
from .reputation import NullReputationReader, ReputationReader
from .search_compiler import CompiledSearch, compile_search_query
from .security import generate_api_key, hash_api_key, key_prefix
from .templates import current_version, get_template, live_template_ids, set_current_version, split_official_and_extras
from .validation import validate_payload
from .webhook_notifier import HttpxWebhookTransport, WebhookNotifier

GRACE_DAYS_DEFAULT = 21


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AgentPlatformService:
    """Registration, capability-based matching, and submission intake for third-party
    agent developers — the supply side of the open marketplace, per the Agent SDK &
    Submission Intake PRD."""

    def __init__(
        self,
        session: Session,
        *,
        reputation: ReputationReader | None = None,
        notifier: WebhookNotifier | None = None,
        rate_limiter_config: RateLimiterConfig | None = None,
    ):
        self.session = session
        self.reputation = reputation or NullReputationReader()
        self.notifier = notifier or WebhookNotifier(HttpxWebhookTransport())
        config = rate_limiter_config or RateLimiterConfig(
            max_per_agent=20, max_per_developer=50, window_minutes=60
        )
        self.rate_limiter = SubmissionRateLimiter(session, config)

    # -- registration -----------------------------------------------------------------

    def register_developer(self, *, email: str) -> AgentDeveloper:
        developer = AgentDeveloper(email=email)
        self.session.add(developer)
        self.session.commit()
        return developer

    def register_agent(
        self,
        *,
        developer_id: str,
        name: str,
        categories: list[str],
        integration_mode: IntegrationMode,
        webhook_url: str | None = None,
        runtime_mode: RuntimeMode = RuntimeMode.BUILDER_HOSTED,
    ) -> tuple[Agent, str]:
        """Returns `(agent, raw_api_key)`. The raw key is generated here and never
        stored — only its hash is persisted, so this is the one and only time the
        caller can see it."""
        if self._find_developer(developer_id) is None:
            raise DeveloperNotFound(f"no developer {developer_id}")
        if integration_mode == IntegrationMode.WEBHOOK and not webhook_url:
            raise ValueError("webhook_url is required when integration_mode is 'webhook'")
        if runtime_mode == RuntimeMode.MERIT_HOSTED:
            raise ValueError("merit_hosted is reserved")
        if runtime_mode not in (RuntimeMode.BUILDER_HOSTED, RuntimeMode.ATTESTED):
            raise ValueError("unknown runtime_mode")

        raw_key = generate_api_key()
        agent = Agent(
            developer_id=developer_id,
            name=name,
            categories=categories,
            integration_mode=integration_mode,
            webhook_url=webhook_url,
            runtime_mode=runtime_mode,
            api_key_hash=hash_api_key(raw_key),
            api_key_prefix=key_prefix(raw_key),
        )
        self.session.add(agent)
        self.session.commit()
        return agent, raw_key

    def attest_agent(self, agent_id: str) -> Agent:
        agent = self.session.get(Agent, agent_id)
        if agent is None:
            raise AgentNotFound(f"no agent {agent_id}")
        agent.runtime_mode = RuntimeMode.ATTESTED
        self.session.commit()
        return agent

    def disable_agent(self, agent_id: str) -> Agent:
        agent = self.session.get(Agent, agent_id)
        if agent is None:
            raise AgentNotFound(f"no agent {agent_id}")
        agent.status = AgentStatus.DISABLED
        self.session.commit()
        return agent

    def authenticate_agent(self, raw_api_key: str) -> Agent:
        agent = (
            self.session.query(Agent)
            .filter_by(api_key_hash=hash_api_key(raw_api_key), status=AgentStatus.ACTIVE)
            .one_or_none()
        )
        if agent is None:
            raise InvalidApiKey("unknown or disabled API key")
        return agent

    # -- matching -----------------------------------------------------------------------

    def notify_job_funded(
        self,
        *,
        job_id: str,
        agent_id: str,
        category: str,
        objective_schema: dict[str, str] | None = None,
    ) -> list[JobAssignment]:
        """Assign one listed agent to a funded run/hire job. Idempotent for the same
        agent; a second agent on the same job is rejected."""
        agent = self.session.get(Agent, agent_id)
        if agent is None or agent.status != AgentStatus.ACTIVE:
            raise AgentNotFound(f"no active agent {agent_id}")
        if category not in agent.categories:
            raise NotAssignedToJob(f"agent {agent_id} does not list category {category}")

        job_ref = self._find_bounty_ref(job_id)
        if job_ref is None:
            job_ref = JobRef(job_id=job_id, category=category, objective_schema=objective_schema or {})
            self.session.add(job_ref)
            self.session.commit()

        existing_any = self.session.query(JobAssignment).filter_by(job_id=job_id).all()
        for existing in existing_any:
            if existing.agent_id == agent_id:
                return [existing]
            raise JobAlreadyAssigned(f"job {job_id} is already assigned")

        match = JobAssignment(job_id=job_id, agent_id=agent.id)
        self.session.add(match)
        self.session.flush()
        if agent.integration_mode == IntegrationMode.WEBHOOK:
            self._deliver_match(agent, match)
        self.session.commit()
        return [match]

    def register_company(self, *, email: str) -> Company:
        company = Company(email=email)
        self.session.add(company)
        self.session.commit()
        return company

    def create_listing(
        self,
        *,
        agent_id: str,
        category: str,
        requirement: dict | None = None,
        credits_per_row: int,
        badge: str = "sandbox",
        hire_monthly_cents: int | None = None,
        included_runs: int | None = None,
        template_id: str = "lead_enrichment",
        template_version: int | None = None,
        blurb: str = "",
        harness_json: dict | None = None,
    ) -> Listing:
        agent = self.session.get(Agent, agent_id)
        if agent is None:
            raise AgentNotFound(f"no agent {agent_id}")
        del badge  # listings always enter Sandbox; certify / SLA are separate steps
        version = current_version(template_id) if template_version is None else template_version
        template = get_template(template_id, version)
        if category != template.category:
            raise ValueError(f"category must be {template.category} for template {template_id}")
        extras: dict = {"objective_criteria": [], "subjective_criteria": []}
        if requirement:
            _, extras = split_official_and_extras(requirement, template)
        contract = CapabilityContract(
            category=template.category, requirement_json=template.requirement, locked=True, version=version
        )
        self.session.add(contract)
        self.session.flush()
        listing = Listing(
            agent_id=agent_id,
            contract_id=contract.id,
            badge=ListingBadge.SANDBOX,
            status=ListingStatus.ACTIVE,
            credits_per_row=credits_per_row,
            hire_monthly_cents=hire_monthly_cents,
            included_runs=included_runs,
            template_id=template_id,
            template_version=version,
            optional_fields=extras,
            blurb=blurb,
            harness_json=merge_harness(harness_json),
        )
        self.session.add(listing)
        self.session.flush()
        contract.listing_id = listing.id
        self.session.commit()
        return listing

    def certify_listing(self, listing_id: str, submissions: dict[str, dict]) -> Listing:
        listing = self.session.get(Listing, listing_id)
        if listing is None:
            raise AgentNotFound(f"no listing {listing_id}")
        template = get_template(listing.template_id, listing.template_version)
        errors: list[str] = []
        passed = 0
        for fixture in template.golden_fixtures:
            got = submissions.get(fixture["id"])
            if got is None:
                errors.append(f"missing fixture {fixture['id']}")
                continue
            fixture_ok = True
            for field, expected in fixture["expected"].items():
                if got.get(field) != expected:
                    fixture_ok = False
                    errors.append(
                        f"{fixture['id']}.{field}: expected {expected!r} got {got.get(field)!r}"
                    )
            if fixture_ok:
                passed += 1
        if errors:
            listing.eval_pass_rate = passed / max(len(template.golden_fixtures), 1)
            self.session.commit()
            raise CertificationFailed(errors)
        listing.badge = ListingBadge.CERTIFIED
        listing.eval_pass_rate = 1.0
        self.session.commit()
        return listing

    def submit_sla_checklist(
        self,
        listing_id: str,
        *,
        kyc_ok: bool,
        tos_ok: bool,
        canary_ok: bool,
        webhook_uptime_ok: bool,
        notes: str = "",
    ) -> SlaChecklist:
        listing = self.session.get(Listing, listing_id)
        if listing is None:
            raise AgentNotFound(f"no listing {listing_id}")
        row = self.session.get(SlaChecklist, listing_id)
        if row is None:
            row = SlaChecklist(listing_id=listing_id)
            self.session.add(row)
        row.kyc_ok = kyc_ok
        row.tos_ok = tos_ok
        row.canary_ok = canary_ok
        row.webhook_uptime_ok = webhook_uptime_ok
        row.notes = notes
        self.session.commit()
        return row

    def promote_to_sla(self, listing_id: str) -> Listing:
        listing = self.session.get(Listing, listing_id)
        if listing is None:
            raise AgentNotFound(f"no listing {listing_id}")
        if listing.badge != ListingBadge.CERTIFIED:
            raise ValueError("SLA requires a Certified listing")
        if listing.hire_monthly_cents is None:
            raise ValueError("SLA requires a monthly hire price")
        checklist = self.session.get(SlaChecklist, listing_id)
        if checklist is None or not all(
            (checklist.kyc_ok, checklist.tos_ok, checklist.canary_ok, checklist.webhook_uptime_ok)
        ):
            raise SlaChecklistIncomplete("KYC, ToS, canary, and webhook uptime must all pass")
        agent = self.session.get(Agent, listing.agent_id)
        if agent is None or agent.runtime_mode != RuntimeMode.ATTESTED:
            raise AttestationRequired("SLA/Hire requires an attested runtime (sidecar or signed SDK)")
        listing.badge = ListingBadge.SLA
        self.session.commit()
        return listing

    def bump_catalog(self, template_id: str, version: int, *, grace_days: int = GRACE_DAYS_DEFAULT) -> None:
        set_current_version(template_id, version)
        now = _now()
        stale = self.session.query(Listing).filter_by(template_id=template_id).all()
        for listing in stale:
            if listing.template_version < version:
                listing.grace_ends_at = now + timedelta(days=grace_days)
        self.session.commit()

    def get_listing(self, listing_id: str) -> Listing:
        listing = self.session.get(Listing, listing_id)
        if listing is None:
            raise AgentNotFound(f"no listing {listing_id}")
        return listing

    def search_listings(self, query: str, *, now: datetime | None = None) -> list[Listing]:
        compiled = compile_search_query(query)
        now = now or _now()
        template_ids = [compiled.template_id] if compiled.template_id else live_template_ids()
        for tid in template_ids:
            self._expire_stale_listings(tid, now)
        q = self.session.query(Listing).filter_by(status=ListingStatus.ACTIVE, is_legacy=False)
        if compiled.template_id:
            q = q.filter_by(template_id=compiled.template_id)
        rows = q.all()
        filtered = [row for row in rows if self._matches_compiled(row, compiled)]
        filtered.sort(key=lambda row: self._search_rank(row), reverse=True)
        return filtered

    def _expire_stale_listings(self, template_id: str, now: datetime) -> None:
        latest = current_version(template_id)
        rows = self.session.query(Listing).filter_by(template_id=template_id, is_legacy=False).all()
        dirty = False
        for listing in rows:
            if listing.template_version >= latest:
                continue
            if listing.grace_ends_at is not None and _as_utc(now) >= _as_utc(listing.grace_ends_at):
                listing.is_legacy = True
                dirty = True
        if dirty:
            self.session.commit()

    def _matches_compiled(self, listing: Listing, compiled: CompiledSearch) -> bool:
        if compiled.sla_only and listing.badge != ListingBadge.SLA:
            return False
        if compiled.certified_or_better and listing.badge not in (ListingBadge.CERTIFIED, ListingBadge.SLA):
            return False
        if compiled.max_credits_per_row is not None and listing.credits_per_row > compiled.max_credits_per_row:
            return False
        if compiled.min_eval is not None and listing.eval_pass_rate < compiled.min_eval:
            return False
        return True

    def _search_rank(self, listing: Listing) -> tuple:
        rating = self.reputation.get_rating(listing.agent_id)
        recency = _as_utc(listing.created_at).timestamp() if listing.created_at else 0.0
        return (listing.eval_pass_rate, rating, -listing.credits_per_row, recency)

    def publish_sandbox(
        self,
        *,
        email: str,
        name: str,
        categories: list[str],
        integration_mode: IntegrationMode,
        webhook_url: str | None,
        credits_per_row: int,
        hire_monthly_cents: int | None = None,
        included_runs: int | None = None,
        blurb: str = "",
        requirement: dict | None = None,
    ) -> tuple[AgentDeveloper, Agent, str, Listing]:
        developer = self.register_developer(email=email)
        agent, raw_key = self.register_agent(
            developer_id=developer.id,
            name=name,
            categories=categories,
            integration_mode=integration_mode,
            webhook_url=webhook_url,
        )
        listing = self.create_listing(
            agent_id=agent.id,
            category=categories[0] if categories else get_template().category,
            requirement=requirement,
            credits_per_row=credits_per_row,
            hire_monthly_cents=hire_monthly_cents,
            included_runs=included_runs,
            blurb=blurb,
        )
        return developer, agent, raw_key, listing

    def create_hire(self, *, company_id: str, listing_id: str, period_days: int = 30) -> Hire:
        listing = self.session.get(Listing, listing_id)
        if listing is None:
            raise AgentNotFound(f"no listing {listing_id}")
        if listing.badge != ListingBadge.SLA or listing.hire_monthly_cents is None:
            raise ValueError("hire requires an SLA-eligible listing with a monthly price")
        start = _now()
        hire = Hire(
            company_id=company_id,
            listing_id=listing_id,
            agent_id=listing.agent_id,
            period_start=start,
            period_end=start + timedelta(days=period_days),
            monthly_cents=listing.hire_monthly_cents,
            included_runs=listing.included_runs or 0,
            template_version=listing.template_version,
            harness_hash=harness_hash(listing.harness_json),
        )
        self.session.add(hire)
        self.session.commit()
        return hire

    def create_job(
        self, *, company_id: str, listing_id: str, row_count: int, hire_id: str | None = None
    ) -> Job:
        frozen_listing_id = listing_id
        if hire_id:
            hire = self.session.get(Hire, hire_id)
            if hire is None:
                raise AgentNotFound(f"no hire {hire_id}")
            frozen_listing_id = hire.listing_id
        listing = self.session.get(Listing, frozen_listing_id)
        if listing is None:
            raise AgentNotFound(f"no listing {frozen_listing_id}")
        kind = JobKind.HIRE if hire_id else JobKind.RUN
        credits = row_count * listing.credits_per_row
        labor_cents = credits  # 1 credit == 1 cent in MVP
        job = Job(
            kind=kind,
            company_id=company_id,
            listing_id=frozen_listing_id,
            agent_id=listing.agent_id,
            hire_id=hire_id,
            contract_id=listing.contract_id,
            status=JobStatus.DRAFT,
            row_count=row_count,
            credits_charged=credits,
            labor_amount_cents=labor_cents,
            grading_fee_cents=max(1, row_count),
        )
        self.session.add(job)
        if hire_id:
            hire = self.session.get(Hire, hire_id)
            if hire is not None:
                hire.runs_used += 1
        self.session.commit()
        return job

    def _deliver_match(self, agent: Agent, match: JobAssignment) -> None:
        delivered, attempts, error = self.notifier.deliver(
            url=agent.webhook_url, payload=self._webhook_payload(agent, match)
        )
        match.delivery_attempts = attempts
        match.last_delivery_error = error
        if delivered:
            match.notified_at = _now()

    def available_jobs_for_agent(self, agent_id: str) -> list[JobAssignment]:
        """Bounties this agent has been matched to but hasn't submitted anything for
        yet — what a poll-mode agent's `GET /jobs/available` sees."""
        matches = self.session.query(JobAssignment).filter_by(agent_id=agent_id).all()
        submitted_job_ids = {
            s.job_id for s in self.session.query(Submission).filter_by(agent_id=agent_id).all()
        }
        return [m for m in matches if m.job_id not in submitted_job_ids]

    # -- submission -----------------------------------------------------------------------

    def submit(self, *, job_id: str, agent_id: str, payload: dict, trace: dict | None = None) -> Submission:
        agent = self.session.get(Agent, agent_id)
        if agent is None:
            raise AgentNotFound(f"no agent {agent_id}")

        bounty_ref = self._find_bounty_ref(job_id)
        if bounty_ref is None:
            raise JobNotRegistered(f"bounty {job_id} has not been registered for matching")

        match = self.session.query(JobAssignment).filter_by(job_id=job_id, agent_id=agent_id).one_or_none()
        if match is None:
            raise NotAssignedToJob(f"agent {agent_id} was never matched to bounty {job_id}")

        self.rate_limiter.check(agent_id=agent_id, developer_id=agent.developer_id)

        errors = validate_payload(payload, bounty_ref.objective_schema)
        if errors:
            raise SubmissionValidationError(errors)

        harness_ok = None
        digest = None
        job = self.session.get(Job, job_id)
        if job is not None and job.hire_id:
            listing = self.session.get(Listing, job.listing_id)
            harness = listing.harness_json if listing is not None else {}
            try:
                digest = check_trace(harness, trace)
            except ValueError as e:
                raise SubmissionValidationError([str(e)]) from e
            harness_ok = True

        submission = Submission(
            job_id=job_id,
            agent_id=agent_id,
            developer_id=agent.developer_id,
            payload=payload,
            status=SubmissionStatus.QUEUED_FOR_GRADING,
            harness_ok=harness_ok,
            trace_digest=digest,
        )
        self.session.add(submission)
        self.session.commit()
        return submission

    # -- resolution (called by the Oracle Verification Service once it grades) --------

    def record_verdict(self, *, job_id: str, submission_id: str, passed: bool) -> Submission:
        """First verified pass wins: if a winner already exists for this bounty, any
        other submission is marked moot regardless of its own verdict. Idempotent —
        replaying the same winning verdict just returns the existing winner."""
        submission = self.session.get(Submission, submission_id)
        if submission is None or submission.job_id != job_id:
            raise SubmissionNotFound(f"no submission {submission_id} for bounty {job_id}")

        existing_winner = (
            self.session.query(Submission)
            .filter_by(job_id=job_id, status=SubmissionStatus.GRADED, passed=True)
            .one_or_none()
        )
        if existing_winner is not None and existing_winner.id != submission.id:
            submission.status = SubmissionStatus.MOOT
            self.session.commit()
            return submission

        submission.status = SubmissionStatus.GRADED
        job = self.session.get(Job, job_id)
        if job is not None and job.hire_id and submission.harness_ok is not True:
            passed = False
        submission.passed = passed
        self.session.flush()

        if passed:
            others = (
                self.session.query(Submission)
                .filter(
                    Submission.job_id == job_id,
                    Submission.id != submission.id,
                    Submission.status.in_([SubmissionStatus.PENDING, SubmissionStatus.QUEUED_FOR_GRADING]),
                )
                .all()
            )
            for other in others:
                other.status = SubmissionStatus.MOOT

        self.session.commit()
        return submission

    # -- internals -----------------------------------------------------------------------

    def _find_developer(self, developer_id: str) -> AgentDeveloper | None:
        return self.session.get(AgentDeveloper, developer_id)

    def _find_bounty_ref(self, job_id: str) -> JobRef | None:
        return self.session.get(JobRef, job_id)

    def _webhook_payload(self, agent: Agent, match: JobAssignment) -> dict:
        requirement: dict = {}
        deadline = None
        listing_hash = ""
        job = self.session.get(Job, match.job_id)
        if job is not None:
            contract = self.session.get(CapabilityContract, job.contract_id)
            if contract is not None:
                requirement = contract.requirement_json
            listing = self.session.get(Listing, job.listing_id)
            if listing is not None:
                listing_hash = harness_hash(listing.harness_json)
            if job.hire_id:
                hire = self.session.get(Hire, job.hire_id)
                if hire is not None:
                    deadline = hire.period_end.isoformat()
                    listing_hash = hire.harness_hash or listing_hash
        else:
            ref = self._find_bounty_ref(match.job_id)
            if ref is not None:
                requirement = ref.objective_schema
        return {
            "job_id": match.job_id,
            "agent_id": agent.id,
            "requirement": requirement,
            "deadline": deadline,
            "harness_hash": listing_hash,
        }
