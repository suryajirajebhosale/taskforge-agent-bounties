import enum

from langchain_openai import ChatOpenAI

_NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"


class ModelBackend(str, enum.Enum):
    OPENAI = "openai"
    NVIDIA_NIM = "nvidia_nim"


def build_chat_model(backend: ModelBackend, *, model_name: str, api_key: str, temperature: float = 0.0) -> ChatOpenAI:
    """OpenAI is used directly. NVIDIA NIM microservices expose an OpenAI-compatible
    endpoint, so the same `ChatOpenAI` client works for both backends — just pointed at
    a different `base_url` and key — rather than pulling in a separate NIM-specific SDK
    for what is, API-shape-wise, an identical client."""
    if backend == ModelBackend.OPENAI:
        return ChatOpenAI(model=model_name, api_key=api_key, temperature=temperature)
    if backend == ModelBackend.NVIDIA_NIM:
        return ChatOpenAI(model=model_name, api_key=api_key, base_url=_NVIDIA_NIM_BASE_URL, temperature=temperature)
    raise ValueError(f"unknown model backend: {backend}")
