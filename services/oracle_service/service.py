from sqlalchemy.orm import Session

from packages.bounty_schemas.requirement import BountyCategory, Requirement

from .confidence_router import RoutingConfig, route
from .deterministic_checker import run_deterministic_checks
from .dispute_agent import DisputeAgent
from .downstream_clients import AgentPlatformClient, EscrowClient, ReputationClient
from .exceptions import DisputeCaseNotFound, VerdictNotFound
from .judge_agent import JudgeAgent
from .models import DisputeCase, DisputeResolution, FinalResult, Verdict
from .sandbox_executor import SandboxExecutor


class VerificationService:
    """Grades a submission through the category-aware pipeline (deterministic checks ->
    sandbox execution -> LLM judge), routes the result to auto-resolve or human review,
    and — once a verdict is final — notifies Agent Platform and, on a pass, triggers
    the Escrow payout. `escrow_client`/`agent_platform_client` are optional so the
    grading and routing logic can be unit-tested with no HTTP dependency at all.

    Deliberate scope boundary: this service triggers `release_to_agent` on a resolved
    PASS (unambiguous — first-verified-pass-wins), but does NOT trigger
    `refund_to_requester` on a FAIL. A single failed submission doesn't mean a
    competitive bounty is over — other agents' submissions may still be pending — and
    only a service that can see the *whole* bounty's submission state (Agent Platform)
    or a deadline-driven process (Phase 5, not yet built) can safely decide that.
    Automatically refunding on every fail would silently break the multi-agent
    competition semantics already built and tested in the Agent SDK."""

    def __init__(
        self,
        session: Session,
        *,
        judge: JudgeAgent,
        dispute_judge: DisputeAgent,
        routing_config: RoutingConfig,
        sandbox: SandboxExecutor | None = None,
        escrow_client: EscrowClient | None = None,
        agent_platform_client: AgentPlatformClient | None = None,
        reputation_client: ReputationClient | None = None,
    ):
        self.session = session
        self.judge = judge
        self.dispute_judge = dispute_judge
        self.routing_config = routing_config
        self.sandbox = sandbox
        self.escrow_client = escrow_client
        self.agent_platform_client = agent_platform_client
        self.reputation_client = reputation_client

    def grade_submission(
        self,
        *,
        submission_id: str,
        bounty_id: str,
        agent_id: str,
        agent_developer_id: str,
        category: BountyCategory,
        requirement: Requirement,
        payload: dict,
        bounty_amount_cents: int,
        code_script: str | None = None,
    ) -> Verdict:
        stage_results: dict = {}

        deterministic = run_deterministic_checks(payload, requirement.objective_criteria)
        stage_results["deterministic"] = {"passed": deterministic.passed, "failures": deterministic.failures}

        sandbox_evidence: dict = {}
        judge_verdict = None
        if deterministic.passed:
            # Deterministic checks are a hard gate: skip sandbox execution and the LLM
            # judge entirely once objective criteria have already failed — there's
            # nothing left to grade, and it avoids paying for an LLM call on a
            # foregone conclusion.
            if category == BountyCategory.AI_AUTOMATION_PRODUCT_BUILDING and code_script is not None and self.sandbox is not None:
                sandbox_result = self.sandbox.run(script=code_script, timeout_seconds=10.0)
                stage_results["sandbox"] = {
                    "passed": sandbox_result.passed,
                    "exit_code": sandbox_result.exit_code,
                    "stdout": sandbox_result.stdout,
                    "stderr": sandbox_result.stderr,
                    "timed_out": sandbox_result.timed_out,
                }
                sandbox_evidence = stage_results["sandbox"]

            if requirement.subjective_criteria:
                judge_verdict = self.judge.grade(
                    payload=payload, subjective_criteria=requirement.subjective_criteria, evidence=sandbox_evidence
                )
                stage_results["judge"] = judge_verdict.model_dump()

        final_result, confidence, rationale = self._combine(deterministic, judge_verdict)

        routing = route(confidence=confidence, bounty_amount_cents=bounty_amount_cents, config=self.routing_config)

        verdict = Verdict(
            submission_id=submission_id,
            bounty_id=bounty_id,
            agent_id=agent_id,
            agent_developer_id=agent_developer_id,
            bounty_amount_cents=bounty_amount_cents,
            stage_results=stage_results,
            final_result=final_result,
            confidence=confidence,
            rationale=rationale,
            routed_to_human=not routing.auto_resolve,
            resolved=routing.auto_resolve,
        )
        self.session.add(verdict)
        self.session.commit()

        if routing.auto_resolve:
            self._notify_downstream(verdict)
            self._record_reputation_outcome(verdict)

        return verdict

    @staticmethod
    def _combine(deterministic, judge_verdict) -> tuple[FinalResult, float, str]:
        # Deterministic checks are hard gates: failing any objective criterion is an
        # unambiguous, fully-confident fail regardless of what the judge would say.
        if not deterministic.passed:
            reasons = "; ".join(deterministic.failures)
            return FinalResult.FAIL, 1.0, f"Failed objective criteria: {reasons}"

        if judge_verdict is None:
            return FinalResult.PASS, 1.0, "All objective criteria satisfied; no subjective criteria to grade."

        result = FinalResult.PASS if judge_verdict.passed else FinalResult.FAIL
        return result, judge_verdict.confidence, judge_verdict.rationale

    def resolve_human_review(self, *, verdict_id: str, final_result: FinalResult, reviewer: str) -> Verdict:
        """A human reviewer's decision on a verdict that was routed to them instead of
        auto-resolving. Always final once recorded."""
        verdict = self._require_verdict(verdict_id)
        verdict.final_result = final_result
        verdict.rationale = f"{verdict.rationale}\n\n[Resolved by human reviewer {reviewer}]"
        verdict.resolved = True
        self.session.commit()
        self._notify_downstream(verdict)
        self._record_reputation_outcome(verdict)
        return verdict

    def raise_dispute(self, *, verdict_id: str, raised_by: str, payload: dict, requirement: Requirement) -> DisputeCase:
        """An agent developer appealing a verdict. Triggers an independent re-grade
        (`DisputeAgent`, not a re-run of the original `JudgeAgent`) — the outcome isn't
        applied until `resolve_dispute` is called."""
        verdict = self._require_verdict(verdict_id)
        regrade = self.dispute_judge.regrade(
            payload=payload, subjective_criteria=requirement.subjective_criteria, original_rationale=verdict.rationale
        )
        case = DisputeCase(
            verdict_id=verdict_id,
            raised_by=raised_by,
            regrade_result=FinalResult.PASS if regrade.passed else FinalResult.FAIL,
            regrade_confidence=regrade.confidence,
            regrade_rationale=regrade.rationale,
        )
        self.session.add(case)
        self.session.commit()
        return case

    def resolve_dispute(self, *, dispute_id: str, resolved_by: str) -> DisputeCase:
        """Applies the dispute's regrade outcome: overturns the original verdict if the
        independent re-grade disagrees with it, otherwise upholds it. A human escalation
        option is always implicit here via `resolved_by` (e.g. "system" for an automatic
        resolution, or a human reviewer's id) — per the PRD, full automation with no
        human escalation path is explicitly out of scope."""
        case = self._require_dispute(dispute_id)
        verdict = self._require_verdict(case.verdict_id)

        if case.regrade_result != verdict.final_result:
            case.resolution = DisputeResolution.OVERTURNED
            verdict.final_result = case.regrade_result
            verdict.rationale = f"{verdict.rationale}\n\n[Overturned on dispute by {resolved_by}: {case.regrade_rationale}]"
        else:
            case.resolution = DisputeResolution.UPHELD
            verdict.rationale = f"{verdict.rationale}\n\n[Upheld on dispute by {resolved_by}: {case.regrade_rationale}]"

        case.resolved_by = resolved_by
        verdict.resolved = True
        self.session.commit()
        self._notify_downstream(verdict)
        # Reputation's `record_outcome` is idempotent per verdict id — a plain re-call
        # would silently ignore the flipped outcome on an overturn, so overturns get a
        # dedicated correction call instead; an upheld dispute needs no reputation
        # change at all, since the originally recorded outcome is still correct.
        if case.resolution == DisputeResolution.OVERTURNED:
            self._correct_reputation_outcome(verdict)
        return case

    def get_verdict(self, verdict_id: str) -> Verdict:
        return self._require_verdict(verdict_id)

    def get_dispute(self, dispute_id: str) -> DisputeCase:
        return self._require_dispute(dispute_id)

    def _notify_downstream(self, verdict: Verdict) -> None:
        passed = verdict.final_result == FinalResult.PASS
        agent_platform_status = None
        if self.agent_platform_client is not None:
            response = self.agent_platform_client.record_verdict(
                bounty_id=verdict.bounty_id, submission_id=verdict.submission_id, passed=passed
            )
            agent_platform_status = response.get("status")

        # Oracle grading a submission "pass" is necessary but not sufficient to release
        # escrow: in a competitive bounty, another submission may already have won by
        # the time this one finishes grading. Agent Platform's own first-verified-pass-
        # wins bookkeeping is the authority on that — if it reports this submission as
        # moot, skip the payout even though Oracle's own verdict was a pass.
        if passed and self.escrow_client is not None and agent_platform_status != "moot":
            self.escrow_client.release_to_agent(bounty_id=verdict.bounty_id, agent_developer_id=verdict.agent_developer_id)

    def _record_reputation_outcome(self, verdict: Verdict) -> None:
        if self.reputation_client is None:
            return
        self.reputation_client.record_outcome(
            verdict_id=verdict.id,
            agent_id=verdict.agent_id,
            agent_developer_id=verdict.agent_developer_id,
            passed=verdict.final_result == FinalResult.PASS,
            bounty_amount_cents=verdict.bounty_amount_cents,
        )

    def _correct_reputation_outcome(self, verdict: Verdict) -> None:
        if self.reputation_client is None:
            return
        self.reputation_client.correct_outcome(
            verdict_id=verdict.id,
            agent_id=verdict.agent_id,
            agent_developer_id=verdict.agent_developer_id,
            passed=verdict.final_result == FinalResult.PASS,
            bounty_amount_cents=verdict.bounty_amount_cents,
        )

    def _require_verdict(self, verdict_id: str) -> Verdict:
        verdict = self.session.get(Verdict, verdict_id)
        if verdict is None:
            raise VerdictNotFound(f"no verdict {verdict_id}")
        return verdict

    def _require_dispute(self, dispute_id: str) -> DisputeCase:
        case = self.session.get(DisputeCase, dispute_id)
        if case is None:
            raise DisputeCaseNotFound(f"no dispute case {dispute_id}")
        return case
