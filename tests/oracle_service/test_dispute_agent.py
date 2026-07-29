from packages.bounty_schemas.requirement import SubjectiveCriterion
from services.oracle_service.dispute_agent import DisputeAgent
from services.oracle_service.judge_agent import JudgeVerdict


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


def test_regrade_returns_the_models_structured_output():
    canned = JudgeVerdict(passed=True, confidence=0.9, rationale="independent: fine")
    agent = DisputeAgent(_FakeChatModel(canned))

    result = agent.regrade(
        payload={"x": 1},
        subjective_criteria=[SubjectiveCriterion(description="quality", weight=1.0)],
        original_rationale="first reviewer said it failed",
    )

    assert result == canned


def test_regrade_prompt_includes_original_rationale_for_context_only():
    canned = JudgeVerdict(passed=True, confidence=0.9, rationale="ok")
    model = _FakeChatModel(canned)
    agent = DisputeAgent(model)

    agent.regrade(
        payload={},
        subjective_criteria=[SubjectiveCriterion(description="tone", weight=1.0)],
        original_rationale="tone felt off to the first reviewer",
    )

    prompt = model.last_runnable.last_prompt
    assert "tone felt off to the first reviewer" in prompt
    assert "do not simply agree" in prompt


def test_regrade_prompt_frames_the_reviewer_as_independent():
    canned = JudgeVerdict(passed=True, confidence=0.9, rationale="ok")
    model = _FakeChatModel(canned)
    agent = DisputeAgent(model)

    agent.regrade(
        payload={}, subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)], original_rationale="r"
    )

    assert "independent" in model.last_runnable.last_prompt.lower()
