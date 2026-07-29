import pytest
from sqlalchemy.orm import Session

from services.oracle_service.confidence_router import RoutingConfig
from services.oracle_service.database import Base, make_engine
from services.oracle_service.judge_agent import JudgeVerdict
from services.oracle_service.sandbox_executor import SubprocessSandboxExecutor
from services.oracle_service.service import VerificationService


class FakeJudge:
    """Returns a fixed JudgeVerdict regardless of input (mutable after construction so
    a test can change its mind mid-scenario), so the service's grading/routing/dispute
    logic can be tested with no LangChain/LLM involvement."""

    def __init__(self, verdict: JudgeVerdict | None = None):
        self.verdict = verdict or JudgeVerdict(passed=True, confidence=0.95, rationale="looks good")
        self.calls: list[dict] = []

    def grade(self, *, payload, subjective_criteria, evidence=None):
        self.calls.append({"payload": payload, "subjective_criteria": subjective_criteria, "evidence": evidence})
        return self.verdict


class FakeDisputeJudge:
    def __init__(self, verdict: JudgeVerdict | None = None):
        self.verdict = verdict or JudgeVerdict(passed=True, confidence=0.9, rationale="independent review: looks good")
        self.calls: list[dict] = []

    def regrade(self, *, payload, subjective_criteria, original_rationale, evidence=None):
        self.calls.append(
            {
                "payload": payload,
                "subjective_criteria": subjective_criteria,
                "original_rationale": original_rationale,
                "evidence": evidence,
            }
        )
        return self.verdict


class FakeEscrowClient:
    def __init__(self):
        self.release_calls: list[tuple[str, str]] = []

    def release_to_agent(self, *, bounty_id, agent_developer_id):
        self.release_calls.append((bounty_id, agent_developer_id))
        return {"status": "released"}


class FakeAgentPlatformClient:
    """Defaults to reporting the submission as the standing winner ("graded"); set
    `record_verdict_response={"status": "moot"}` to simulate another submission having
    already won the bounty by the time this one's verdict comes in."""

    def __init__(self, record_verdict_response: dict | None = None):
        self.record_calls: list[tuple[str, str, bool]] = []
        self._response = record_verdict_response or {"status": "graded"}

    def record_verdict(self, *, bounty_id, submission_id, passed):
        self.record_calls.append((bounty_id, submission_id, passed))
        return self._response


class FakeReputationClient:
    def __init__(self):
        self.record_calls: list[tuple[str, str, str, bool, int]] = []
        self.correct_calls: list[tuple[str, str, str, bool, int]] = []

    def record_outcome(self, *, verdict_id, agent_id, agent_developer_id, passed, bounty_amount_cents):
        self.record_calls.append((verdict_id, agent_id, agent_developer_id, passed, bounty_amount_cents))
        return {"status": "recorded"}

    def correct_outcome(self, *, verdict_id, agent_id, agent_developer_id, passed, bounty_amount_cents):
        self.correct_calls.append((verdict_id, agent_id, agent_developer_id, passed, bounty_amount_cents))
        return {"status": "corrected"}


@pytest.fixture
def db_session():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def judge():
    return FakeJudge()


@pytest.fixture
def dispute_judge():
    return FakeDisputeJudge()


@pytest.fixture
def escrow_client():
    return FakeEscrowClient()


@pytest.fixture
def agent_platform_client():
    return FakeAgentPlatformClient()


@pytest.fixture
def reputation_client():
    return FakeReputationClient()


@pytest.fixture
def routing_config():
    return RoutingConfig(confidence_threshold=0.8, auto_resolve_amount_cents_ceiling=100_000)


@pytest.fixture
def service(db_session, judge, dispute_judge, routing_config, escrow_client, agent_platform_client, reputation_client):
    return VerificationService(
        session=db_session,
        judge=judge,
        dispute_judge=dispute_judge,
        routing_config=routing_config,
        sandbox=SubprocessSandboxExecutor(),
        escrow_client=escrow_client,
        agent_platform_client=agent_platform_client,
        reputation_client=reputation_client,
    )
