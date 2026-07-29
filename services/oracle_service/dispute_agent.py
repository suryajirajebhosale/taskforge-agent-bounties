from packages.bounty_schemas.requirement import SubjectiveCriterion
from packages.llm_agents.base import BaseLangChainAgent

from .judge_agent import JudgeVerdict


class DisputeAgent(BaseLangChainAgent):
    """Independently re-grades a disputed submission on appeal — a different prompt
    (and, in production config, a different model/temperature — see
    `settings.dispute_model_*`) from `JudgeAgent`, for genuine judge diversity rather
    than a rubber-stamp re-run, per the Oracle Verification Service PRD's dispute flow."""

    def regrade(
        self,
        *,
        payload: dict,
        subjective_criteria: list[SubjectiveCriterion],
        original_rationale: str,
        evidence: dict | None = None,
    ) -> JudgeVerdict:
        prompt = self._build_prompt(payload, subjective_criteria, original_rationale, evidence or {})
        return self.generate_structured(prompt=prompt, output_schema=JudgeVerdict)

    @staticmethod
    def _build_prompt(
        payload: dict, subjective_criteria: list[SubjectiveCriterion], original_rationale: str, evidence: dict
    ) -> str:
        lines = [
            "You are an independent second reviewer for a disputed bounty submission.",
            "A first reviewer already graded this submission. Form your own independent "
            "judgment rather than deferring to theirs.",
            "",
            "Rubric:",
        ]
        for criterion in subjective_criteria:
            lines.append(f"- (weight {criterion.weight:.2f}) {criterion.description}")
        lines += [
            "",
            f"Submission payload: {payload}",
            f"First reviewer's rationale (context only — do not simply agree with it): {original_rationale}",
        ]
        if evidence:
            lines.append(f"Additional evidence from automated checks: {evidence}")
        lines += [
            "",
            "Decide independently whether the submission satisfies the rubric. Return "
            "passed (true/false), a confidence between 0 and 1, and a concise rationale.",
        ]
        return "\n".join(lines)
