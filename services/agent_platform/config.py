from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENT_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./agent_platform.db"
    internal_api_key: str = ""
    """Shared secret required on internal endpoints (bounty funding notifications, verdict
    callbacks) — the same pattern used by the Escrow Ledger Service."""

    max_submissions_per_agent_per_window: int = 20
    max_submissions_per_developer_per_window: int = 50
    rate_limit_window_minutes: int = 60

    webhook_backoff_seconds: list[float] = [0, 1, 5]
    """Delay before each delivery attempt (first entry is typically 0 = try immediately)."""


settings = Settings()
