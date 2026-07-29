from sqlalchemy.orm import Session

from .exceptions import (
    AgentNotFound,
    BountyNotRegistered,
    DeveloperNotFound,
    InvalidApiKey,
    NotMatchedToBounty,
    SubmissionNotFound,
    SubmissionValidationError,
)
from .models import (
    Agent,
    AgentDeveloper,
    AgentStatus,
    BountyMatch,
    BountyRef,
    IntegrationMode,
    Submission,
    SubmissionStatus,
    _now,
)
from .rate_limiter import RateLimiterConfig, SubmissionRateLimiter
from .reputation import NullReputationReader, ReputationReader
from .security import generate_api_key, hash_api_key, key_prefix
from .validation import validate_payload
from .webhook_notifier import HttpxWebhookTransport, WebhookNotifier


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
    ) -> tuple[Agent, str]:
        """Returns `(agent, raw_api_key)`. The raw key is generated here and never
        stored — only its hash is persisted, so this is the one and only time the
        caller can see it."""
        if self._find_developer(developer_id) is None:
            raise DeveloperNotFound(f"no developer {developer_id}")
        if integration_mode == IntegrationMode.WEBHOOK and not webhook_url:
            raise ValueError("webhook_url is required when integration_mode is 'webhook'")

        raw_key = generate_api_key()
        agent = Agent(
            developer_id=developer_id,
            name=name,
            categories=categories,
            integration_mode=integration_mode,
            webhook_url=webhook_url,
            api_key_hash=hash_api_key(raw_key),
            api_key_prefix=key_prefix(raw_key),
        )
        self.session.add(agent)
        self.session.commit()
        return agent, raw_key

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

    def notify_bounty_funded(
        self, *, bounty_id: str, category: str, objective_schema: dict[str, str] | None = None
    ) -> list[BountyMatch]:
        """Registers a funded bounty for matching and immediately matches every active
        agent whose declared capabilities include `category`, ranked by reputation
        (highest first) then registration order. Webhook-mode agents are notified now;
        poll-mode agents discover the match via `available_bounties_for_agent`."""
        bounty_ref = self._find_bounty_ref(bounty_id)
        if bounty_ref is None:
            bounty_ref = BountyRef(bounty_id=bounty_id, category=category, objective_schema=objective_schema or {})
            self.session.add(bounty_ref)
            self.session.commit()

        candidates = (
            self.session.query(Agent)
            .filter(Agent.status == AgentStatus.ACTIVE)
            .order_by(Agent.created_at.asc())
            .all()
        )
        capable = [a for a in candidates if category in a.categories]
        ranked = sorted(capable, key=lambda a: self.reputation.get_rating(a.id), reverse=True)

        matches: list[BountyMatch] = []
        for agent in ranked:
            existing = (
                self.session.query(BountyMatch).filter_by(bounty_id=bounty_id, agent_id=agent.id).one_or_none()
            )
            if existing is not None:
                matches.append(existing)
                continue
            match = BountyMatch(bounty_id=bounty_id, agent_id=agent.id)
            self.session.add(match)
            self.session.flush()
            if agent.integration_mode == IntegrationMode.WEBHOOK:
                self._deliver_match(agent, match)
            matches.append(match)

        self.session.commit()
        return matches

    def _deliver_match(self, agent: Agent, match: BountyMatch) -> None:
        delivered, attempts, error = self.notifier.deliver(
            url=agent.webhook_url, payload={"bounty_id": match.bounty_id, "agent_id": agent.id}
        )
        match.delivery_attempts = attempts
        match.last_delivery_error = error
        if delivered:
            match.notified_at = _now()

    def available_bounties_for_agent(self, agent_id: str) -> list[BountyMatch]:
        """Bounties this agent has been matched to but hasn't submitted anything for
        yet — what a poll-mode agent's `GET /bounties/available` sees."""
        matches = self.session.query(BountyMatch).filter_by(agent_id=agent_id).all()
        submitted_bounty_ids = {
            s.bounty_id for s in self.session.query(Submission).filter_by(agent_id=agent_id).all()
        }
        return [m for m in matches if m.bounty_id not in submitted_bounty_ids]

    # -- submission -----------------------------------------------------------------------

    def submit(self, *, bounty_id: str, agent_id: str, payload: dict) -> Submission:
        agent = self.session.get(Agent, agent_id)
        if agent is None:
            raise AgentNotFound(f"no agent {agent_id}")

        bounty_ref = self._find_bounty_ref(bounty_id)
        if bounty_ref is None:
            raise BountyNotRegistered(f"bounty {bounty_id} has not been registered for matching")

        match = self.session.query(BountyMatch).filter_by(bounty_id=bounty_id, agent_id=agent_id).one_or_none()
        if match is None:
            raise NotMatchedToBounty(f"agent {agent_id} was never matched to bounty {bounty_id}")

        self.rate_limiter.check(agent_id=agent_id, developer_id=agent.developer_id)

        errors = validate_payload(payload, bounty_ref.objective_schema)
        if errors:
            raise SubmissionValidationError(errors)

        submission = Submission(
            bounty_id=bounty_id,
            agent_id=agent_id,
            developer_id=agent.developer_id,
            payload=payload,
            status=SubmissionStatus.QUEUED_FOR_GRADING,
        )
        self.session.add(submission)
        self.session.commit()
        return submission

    # -- resolution (called by the Oracle Verification Service once it grades) --------

    def record_verdict(self, *, bounty_id: str, submission_id: str, passed: bool) -> Submission:
        """First verified pass wins: if a winner already exists for this bounty, any
        other submission is marked moot regardless of its own verdict. Idempotent —
        replaying the same winning verdict just returns the existing winner."""
        submission = self.session.get(Submission, submission_id)
        if submission is None or submission.bounty_id != bounty_id:
            raise SubmissionNotFound(f"no submission {submission_id} for bounty {bounty_id}")

        existing_winner = (
            self.session.query(Submission)
            .filter_by(bounty_id=bounty_id, status=SubmissionStatus.GRADED, passed=True)
            .one_or_none()
        )
        if existing_winner is not None and existing_winner.id != submission.id:
            submission.status = SubmissionStatus.MOOT
            self.session.commit()
            return submission

        submission.status = SubmissionStatus.GRADED
        submission.passed = passed
        self.session.flush()

        if passed:
            others = (
                self.session.query(Submission)
                .filter(
                    Submission.bounty_id == bounty_id,
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

    def _find_bounty_ref(self, bounty_id: str) -> BountyRef | None:
        return self.session.get(BountyRef, bounty_id)
