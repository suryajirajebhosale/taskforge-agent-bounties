from dataclasses import dataclass, field

from .requirement import BountyCategory


@dataclass(frozen=True)
class CategoryTemplate:
    guidance: str
    suggested_objective_fields: list[str] = field(default_factory=list)
    suggested_subjective_focus: list[str] = field(default_factory=list)


CATEGORY_TEMPLATES: dict[BountyCategory, CategoryTemplate] = {
    BountyCategory.SALES_LEAD_GENERATION: CategoryTemplate(
        guidance="Specify an exact minimum count and the required fields per lead (e.g. company name, contact email).",
        suggested_objective_fields=["lead_count", "company_name", "contact_email"],
        suggested_subjective_focus=["how closely each lead matches the target market description"],
    ),
    BountyCategory.RESEARCH_COMPETITIVE_INTELLIGENCE: CategoryTemplate(
        guidance="Specify the minimum number of sources/entries and what fields each entry must include.",
        suggested_objective_fields=["entry_count", "source_url"],
        suggested_subjective_focus=["depth and relevance of the research", "accuracy of claims made"],
    ),
    BountyCategory.AI_AUTOMATION_PRODUCT_BUILDING: CategoryTemplate(
        guidance="Specify what the delivered code/automation must actually do, checkable by running it, not just describing it.",
        suggested_objective_fields=["repository_url", "test_pass_count"],
        suggested_subjective_focus=["code quality and adherence to the spec"],
    ),
    BountyCategory.HIRING_RECRUITING: CategoryTemplate(
        guidance="Specify the minimum number of qualified candidates/contacts and the required fields per contact.",
        suggested_objective_fields=["contact_count", "candidate_name", "contact_email"],
        suggested_subjective_focus=["how well each candidate matches the role description"],
    ),
    BountyCategory.CONTENT_MEDIA: CategoryTemplate(
        guidance="Specify the exact deliverable count and format; subjective criteria should cover tone, originality, and brand fit.",
        suggested_objective_fields=["deliverable_count", "format"],
        suggested_subjective_focus=["tone matches brand voice", "originality"],
    ),
    BountyCategory.OTHER: CategoryTemplate(
        guidance="Describe concrete, checkable criteria wherever possible; fall back to a clear subjective rubric otherwise.",
    ),
}
