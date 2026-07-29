"""Golden bounty descriptions for the eval harness, drawn from real examples observed
live on trybounty.ai during the initial product research (see bounty-clone-plan.md)."""

from .eval_harness import GoldenExample
from .requirement import BountyCategory

GOLDEN_DATASET: list[GoldenExample] = [
    GoldenExample(
        description="Find 100 ecommerce brands doing $1M-$25M in revenue",
        category=BountyCategory.SALES_LEAD_GENERATION,
        expected_objective_fields={"lead_count"},
    ),
    GoldenExample(
        description="Rank top structured data AI startups",
        category=BountyCategory.RESEARCH_COMPETITIVE_INTELLIGENCE,
        expected_objective_fields={"entry_count"},
    ),
    GoldenExample(
        description="Build a Chrome extension from this specification",
        category=BountyCategory.AI_AUTOMATION_PRODUCT_BUILDING,
        expected_objective_fields={"repository_url"},
    ),
    GoldenExample(
        description="Find UK software founders for payment integration outreach",
        category=BountyCategory.HIRING_RECRUITING,
        expected_objective_fields={"contact_count"},
    ),
    GoldenExample(
        description="Create three vertical promotional video advertisements",
        category=BountyCategory.CONTENT_MEDIA,
        expected_objective_fields={"deliverable_count"},
    ),
]
