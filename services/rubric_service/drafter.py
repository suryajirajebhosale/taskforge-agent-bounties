from typing import Protocol

from .category_templates import CategoryTemplate
from .requirement import BountyCategory, Requirement


class RubricDrafter(Protocol):
    """What `RubricGenerationService` needs to turn a bounty description into a draft
    `Requirement`. `RubricAgent` implements this for real via LangChain; tests use a
    fake implementation so the service's draft/approve/lock state machine can be tested
    without any LLM call, the same way `StripeGateway` is faked in the Escrow Ledger
    Service's tests."""

    def draft(self, *, bounty_description: str, category: BountyCategory, template: CategoryTemplate) -> Requirement: ...
