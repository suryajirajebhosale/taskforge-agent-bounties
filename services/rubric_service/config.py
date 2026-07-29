from pydantic_settings import BaseSettings, SettingsConfigDict

from packages.llm_agents import ModelBackend


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RUBRIC_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./rubric_service.db"
    internal_api_key: str = ""

    model_backend: ModelBackend = ModelBackend.OPENAI
    model_name: str = "gpt-4o-mini"
    model_api_key: str = ""
    model_temperature: float = 0.0


settings = Settings()
