from packages.llm_agents.base import BaseLangChainAgent

from .category_templates import CategoryTemplate
from .requirement import BountyCategory, Requirement


class RubricAgent(BaseLangChainAgent):
    """Drafts a structured `Requirement` from a requester's free-text bounty
    description, seeded by the bounty's category template to reduce LLM drift and
    improve objective-criteria extraction reliability, per the Bounty Requirement/
    Rubric Module PRD. Implements the `RubricDrafter` protocol structurally."""

    def draft(self, *, job_description: str, category: BountyCategory, template: CategoryTemplate) -> Requirement:
        prompt = self._build_prompt(job_description, category, template)
        return self.generate_structured(prompt=prompt, output_schema=Requirement)

    @staticmethod
    def _build_prompt(job_description: str, category: BountyCategory, template: CategoryTemplate) -> str:
        lines = [
            f"You are drafting acceptance criteria for a bounty in the '{category.value}' category.",
            f"Guidance for this category: {template.guidance}",
        ]
        if template.suggested_objective_fields:
            lines.append(f"Consider these objective fields: {', '.join(template.suggested_objective_fields)}.")
        if template.suggested_subjective_focus:
            lines.append(f"Consider these subjective angles: {', '.join(template.suggested_subjective_focus)}.")
        lines += [
            "",
            "Bounty description, in the requester's own words:",
            job_description,
            "",
            "Produce objective_criteria (machine-checkable, each with a field, a comparator, "
            "and a target value) and subjective_criteria (a weighted rubric whose weights "
            "sum to 1.0) that together define when this bounty is complete.",
        ]
        return "\n".join(lines)
