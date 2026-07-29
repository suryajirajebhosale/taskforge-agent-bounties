from datetime import datetime, timedelta, timezone


def week_key(dt: datetime, week_start_day: int = 6) -> str:
    """A stable string identifying the week `dt` falls in, with weeks starting on
    `week_start_day` (`datetime.weekday()` convention: Monday=0 .. Sunday=6; default
    Sunday, matching the weekly leaderboard reset observed live on trybounty.ai).
    Returns the ISO date of that week's start, e.g. "2026-07-19"."""
    dt = dt.astimezone(timezone.utc)
    days_since_start = (dt.weekday() - week_start_day) % 7
    week_start = (dt - timedelta(days=days_since_start)).date()
    return week_start.isoformat()
