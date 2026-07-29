from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REPUTATION_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./reputation_service.db"
    internal_api_key: str = ""

    decay_alpha: float = 0.15
    """How much each new outcome shifts an agent's running pass-rate average (0-1).
    Lower = smoother, slower-changing rating; higher = more reactive to recent
    performance. Deliberately left tunable rather than fixed — the PRD calls out that
    the right decay constant should be tuned post-launch against real outcome data."""

    weekly_prize_amount_cents: int = 2_500  # $25/week, matching the amount observed live on trybounty.ai
    week_start_day: int = 6
    """Python's `datetime.weekday()` convention: Monday=0 .. Sunday=6. Default Sunday,
    matching the weekly leaderboard reset observed live."""


settings = Settings()
