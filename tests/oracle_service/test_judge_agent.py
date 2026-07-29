from packages.bounty_schemas.requirement import SubjectiveCriterion
from services.oracle_service.judge_agent import JudgeAgent, JudgeVerdict


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


def test_grade_returns_the_models_structured_output():
    canned = JudgeVerdict(passed=True, confidence=0.9, rationale="great work")
    agent = JudgeAgent(_FakeChatModel(canned))

    result = agent.grade(payload={"x": 1}, subjective_criteria=[SubjectiveCriterion(description="quality", weight=1.0)])

    assert result == canned


def test_grade_prompt_includes_rubric_and_payload():
    canned = JudgeVerdict(passed=True, confidence=0.9, rationale="ok")
    model = _FakeChatModel(canned)
    agent = JudgeAgent(model)

    agent.grade(
        payload={"lead_count": 10},
        subjective_criteria=[SubjectiveCriterion(description="tone matches brand", weight=1.0)],
    )

    prompt = model.last_runnable.last_prompt
    assert "tone matches brand" in prompt
    assert "lead_count" in prompt


def test_grade_includes_evidence_when_provided():
    canned = JudgeVerdict(passed=True, confidence=0.9, rationale="ok")
    model = _FakeChatModel(canned)
    agent = JudgeAgent(model)

    agent.grade(
        payload={},
        subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)],
        evidence={"sandbox": "exit code 0"},
    )

    assert "sandbox" in model.last_runnable.last_prompt


def test_grade_omits_evidence_section_when_none_given():
    canned = JudgeVerdict(passed=True, confidence=0.9, rationale="ok")
    model = _FakeChatModel(canned)
    agent = JudgeAgent(model)

    agent.grade(payload={}, subjective_criteria=[SubjectiveCriterion(description="x", weight=1.0)])

    assert "Additional evidence" not in model.last_runnable.last_prompt
