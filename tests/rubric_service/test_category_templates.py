from services.rubric_service.category_templates import CATEGORY_TEMPLATES
from services.rubric_service.requirement import BountyCategory


def test_every_bounty_category_has_a_template():
    for category in BountyCategory:
        assert category in CATEGORY_TEMPLATES


def test_every_template_has_non_empty_guidance():
    for template in CATEGORY_TEMPLATES.values():
        assert template.guidance
