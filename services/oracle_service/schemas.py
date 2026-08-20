from pydantic import BaseModel

from packages.bounty_schemas.requirement import BountyCategory, Requirement

from .models import DisputeCase, FinalResult, Verdict


class GradeSubmissionRequest(BaseModel):
    submission_id: str
    job_id: str
    agent_id: str
    agent_developer_id: str
    category: BountyCategory
    requirement: Requirement
    payload: dict
    job_amount_cents: int
    code_script: str | None = None


class VerdictOut(BaseModel):
    id: str
    submission_id: str
    job_id: str
    agent_id: str
    agent_developer_id: str
    job_amount_cents: int
    final_result: FinalResult
    confidence: float
    rationale: str
    routed_to_human: bool
    resolved: bool
    stage_results: dict

    @classmethod
    def from_model(cls, verdict: Verdict) -> "VerdictOut":
        return cls(
            id=verdict.id,
            submission_id=verdict.submission_id,
            job_id=verdict.job_id,
            agent_id=verdict.agent_id,
            agent_developer_id=verdict.agent_developer_id,
            job_amount_cents=verdict.job_amount_cents,
            final_result=verdict.final_result,
            confidence=verdict.confidence,
            rationale=verdict.rationale,
            routed_to_human=verdict.routed_to_human,
            resolved=verdict.resolved,
            stage_results=verdict.stage_results,
        )


class HumanReviewRequest(BaseModel):
    final_result: FinalResult
    reviewer: str


class RaiseDisputeRequest(BaseModel):
    verdict_id: str
    raised_by: str
    payload: dict
    requirement: Requirement


class DisputeCaseOut(BaseModel):
    id: str
    verdict_id: str
    raised_by: str
    regrade_result: FinalResult
    regrade_confidence: float
    regrade_rationale: str
    resolution: str | None
    resolved_by: str | None

    @classmethod
    def from_model(cls, case: DisputeCase) -> "DisputeCaseOut":
        return cls(
            id=case.id,
            verdict_id=case.verdict_id,
            raised_by=case.raised_by,
            regrade_result=case.regrade_result,
            regrade_confidence=case.regrade_confidence,
            regrade_rationale=case.regrade_rationale,
            resolution=case.resolution.value if case.resolution else None,
            resolved_by=case.resolved_by,
        )


class ResolveDisputeRequest(BaseModel):
    resolved_by: str
