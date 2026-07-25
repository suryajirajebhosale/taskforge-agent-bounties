from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ESCROW_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./escrow.db"
    stripe_api_key: str = ""
    internal_api_key: str = ""
    """Shared secret required on every request via the X-Internal-Api-Key header. This
    service is never exposed publicly, but the header check keeps that true even if
    network isolation is ever misconfigured."""
    default_take_rate_bps: int = 1000
    """Platform take-rate in basis points (1000 = 10%) applied when no category-specific rate is set."""


settings = Settings()
