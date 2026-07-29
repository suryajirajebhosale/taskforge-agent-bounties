from pydantic_settings import BaseSettings, SettingsConfigDict

from packages.llm_agents import ModelBackend


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ORACLE_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./oracle_service.db"
    internal_api_key: str = ""

    judge_model_backend: ModelBackend = ModelBackend.OPENAI
    judge_model_name: str = "gpt-4o-mini"
    judge_model_api_key: str = ""
    judge_model_temperature: float = 0.0

    dispute_model_backend: ModelBackend = ModelBackend.OPENAI
    dispute_model_name: str = "gpt-4o"
    dispute_model_api_key: str = ""
    dispute_model_temperature: float = 0.2
    """Slightly higher than the primary judge's, for judge diversity on appeal per the PRD."""

    default_confidence_threshold: float = 0.85
    auto_resolve_amount_cents_ceiling: int = 50_000
    """Bounties at or above this amount always go to human review, regardless of confidence."""

    escrow_base_url: str = "http://localhost:8001"
    escrow_internal_api_key: str = ""
    agent_platform_base_url: str = "http://localhost:8002"
    agent_platform_internal_api_key: str = ""
    reputation_base_url: str = "http://localhost:8003"
    reputation_internal_api_key: str = ""


settings = Settings()
