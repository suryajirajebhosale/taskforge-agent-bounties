import pytest
from pydantic import BaseModel

from packages.llm_agents.base import BaseLangChainAgent


class Greeting(BaseModel):
    text: str


class WrongType(BaseModel):
    number: int


class _FakeStructuredRunnable:
    """Stands in for what `ChatOpenAI(...).with_structured_output(schema)` returns:
    something with an `.invoke(prompt)` method. Returns a fixed object regardless of
    prompt, or a caller-supplied one, so tests can control exactly what the "model"
    said without needing a real API key or LangChain's fake-model internals."""

    def __init__(self, result):
        self._result = result
        self.last_prompt: str | None = None

    def invoke(self, prompt: str):
        self.last_prompt = prompt
        return self._result


class _FakeChatModel:
    def __init__(self, result):
        self._result = result

    def with_structured_output(self, schema: type):
        return _FakeStructuredRunnable(self._result)


def test_generate_structured_returns_the_parsed_object():
    model = _FakeChatModel(Greeting(text="hello"))
    agent = BaseLangChainAgent(model)

    result = agent.generate_structured(prompt="say hi", output_schema=Greeting)

    assert result == Greeting(text="hello")


def test_generate_structured_passes_the_prompt_through_unmodified():
    runnable_holder = {}

    class TrackingModel:
        def with_structured_output(self, schema):
            runnable = _FakeStructuredRunnable(Greeting(text="hi"))
            runnable_holder["runnable"] = runnable
            return runnable

    agent = BaseLangChainAgent(TrackingModel())
    agent.generate_structured(prompt="a very specific prompt", output_schema=Greeting)

    assert runnable_holder["runnable"].last_prompt == "a very specific prompt"


def test_generate_structured_rejects_a_result_of_the_wrong_type():
    model = _FakeChatModel(WrongType(number=1))
    agent = BaseLangChainAgent(model)

    with pytest.raises(TypeError):
        agent.generate_structured(prompt="say hi", output_schema=Greeting)
