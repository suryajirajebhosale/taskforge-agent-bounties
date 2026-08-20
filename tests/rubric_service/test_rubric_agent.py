from services.rubric_service.category_templates import CATEGORY_TEMPLATES
from services.rubric_service.requirement import BountyCategory, ObjectiveCriterion, Requirement
from services.rubric_service.rubric_agent import RubricAgent


class _FakeStructuredRunnable:
    def __init__(self, result):
        self._result = result
        self.last_prompt: str | None = None

    def invoke(self, prompt: str):
        self.last_prompt = prompt
        return self._result


class _FakeChatModel:
    def __init__(self, result):
        self._result = result
        self.last_runnable: _FakeStructuredRunnable | None = None

    def with_structured_output(self, schema: type):
        self.last_runnable = _FakeStructuredRunnable(self._result)
        return self.last_runnable


def test_draft_returns_the_models_structured_output():
    canned = Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=50)])
    model = _FakeChatModel(canned)
    agent = RubricAgent(model)

    result = agent.draft(
        job_description="find 50 leads",
        category=BountyCategory.SALES_LEAD_GENERATION,
        template=CATEGORY_TEMPLATES[BountyCategory.SALES_LEAD_GENERATION],
    )

    assert result == canned


def test_draft_prompt_includes_category_guidance_and_description():
    canned = Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=1)])
    model = _FakeChatModel(canned)
    agent = RubricAgent(model)
    template = CATEGORY_TEMPLATES[BountyCategory.SALES_LEAD_GENERATION]

    agent.draft(
        job_description="find 50 leads in fintech",
        category=BountyCategory.SALES_LEAD_GENERATION,
        template=template,
    )

    prompt = model.last_runnable.last_prompt
    assert "find 50 leads in fintech" in prompt
    assert template.guidance in prompt
    assert "sales_lead_generation" in prompt


def test_draft_prompt_includes_suggested_objective_fields():
    canned = Requirement(objective_criteria=[ObjectiveCriterion(field="x", comparator=">=", value=1)])
    model = _FakeChatModel(canned)
    agent = RubricAgent(model)
    template = CATEGORY_TEMPLATES[BountyCategory.SALES_LEAD_GENERATION]

    agent.draft(job_description="find leads", category=BountyCategory.SALES_LEAD_GENERATION, template=template)

    prompt = model.last_runnable.last_prompt
    for expected_field in template.suggested_objective_fields:
        assert expected_field in prompt
