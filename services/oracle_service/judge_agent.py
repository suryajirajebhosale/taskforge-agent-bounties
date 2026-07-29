from pydantic import BaseModel, Field

from packages.bounty_schemas.requirement import SubjectiveCriterion
from packages.llm_agents.base import BaseLangChainAgent


class JudgeVerdict(BaseModel):
    passed: bool
    confidence: float = Field(ge=0, le=1)
    rationale: str


class JudgeAgent(BaseLangChainAgent):
    """Grades a submission's payload against a bounty's subjective_criteria, returning
    a structured verdict plus confidence and a human-readable rationale — never a bare
    pass/fail — per the Oracle Verification Service PRD."""

    def grade(
        self, *, payload: dict, subjective_criteria: list[SubjectiveCriterion], evidence: dict | None = None
    ) -> JudgeVerdict:
        prompt = self._build_prompt(payload, subjective_criteria, evidence or {})
        return self.generate_structured(prompt=prompt, output_schema=JudgeVerdict)

    @staticmethod
    def _build_prompt(payload: dict, subjective_criteria: list[SubjectiveCriterion], evidence: dict) -> str:
        lines = ["You are grading a bounty submission against a weighted rubric.", "", "Rubric:"]
        for criterion in subjective_criteria:
            lines.append(f"- (weight {criterion.weight:.2f}) {criterion.description}")
        lines += ["", f"Submission payload: {payload}"]
        if evidence:
            lines.append(f"Additional evidence from automated checks: {evidence}")
        lines += [
            "",
            "Decide whether the submission satisfies the rubric overall. Return passed "
            "(true/false), a confidence between 0 and 1, and a concise rationale.",
        ]
        return "\n".join(lines)
