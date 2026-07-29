from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class SupportsStructuredOutput(Protocol):
    """The one piece of LangChain's `BaseChatModel` interface this package actually
    depends on. Kept this narrow (rather than typing against `BaseChatModel` directly)
    so tests can supply a minimal double instead of fighting LangChain's own fake-model
    tool-calling machinery — the same way `StripeGateway` and `WebhookTransport`
    elsewhere in this codebase are narrow, test-friendly interfaces rather than full
    third-party SDK surfaces."""

    def with_structured_output(self, schema: type): ...


class BaseLangChainAgent:
    """Common base for every LLM-backed agent in the platform — `RubricAgent` here
    today, `JudgeAgent` and `DisputeAgent` in the Oracle Verification Service once it
    exists. Wraps a chat model behind `generate_structured`, so switching model
    providers (OpenAI vs. NVIDIA NIM) is a configuration change made once via
    `model_factory.build_chat_model`, not a rewrite in every subclass."""

    def __init__(self, model: SupportsStructuredOutput):
        self.model = model

    def generate_structured(self, *, prompt: str, output_schema: type[T]) -> T:
        structured_model = self.model.with_structured_output(output_schema)
        result = structured_model.invoke(prompt)
        if not isinstance(result, output_schema):
            raise TypeError(
                f"model returned {type(result).__name__}, expected {output_schema.__name__} "
                "— structured output did not conform to the requested schema"
            )
        return result
