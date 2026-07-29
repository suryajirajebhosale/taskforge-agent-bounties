from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .exceptions import RateLimitExceeded
from .models import Submission


@dataclass(frozen=True)
class RateLimiterConfig:
    max_per_agent: int
    max_per_developer: int
    window_minutes: int


class SubmissionRateLimiter:
    """Sliding-window submission caps, per agent and per developer (so one developer
    can't bypass the per-agent cap by registering many disposable agents). Backed
    directly by the `submissions` table rather than Redis — fine at MVP volume, and
    avoids pulling in infra this service doesn't otherwise need yet."""

    def __init__(self, session: Session, config: RateLimiterConfig):
        self.session = session
        self.config = config

    def check(self, *, agent_id: str, developer_id: str) -> None:
        since = datetime.now(timezone.utc) - timedelta(minutes=self.config.window_minutes)

        agent_count = (
            self.session.query(Submission)
            .filter(Submission.agent_id == agent_id, Submission.submitted_at >= since)
            .count()
        )
        if agent_count >= self.config.max_per_agent:
            raise RateLimitExceeded(
                f"agent {agent_id} exceeded {self.config.max_per_agent} submissions "
                f"per {self.config.window_minutes}m"
            )

        developer_count = (
            self.session.query(Submission)
            .filter(Submission.developer_id == developer_id, Submission.submitted_at >= since)
            .count()
        )
        if developer_count >= self.config.max_per_developer:
            raise RateLimitExceeded(
                f"developer {developer_id} exceeded {self.config.max_per_developer} submissions "
                f"per {self.config.window_minutes}m"
            )
