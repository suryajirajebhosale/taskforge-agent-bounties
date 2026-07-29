import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RequirementStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class BountyRequirementRecord(Base):
    __tablename__ = "bounty_requirements"

    bounty_id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    requirement_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[RequirementStatus] = mapped_column(Enum(RequirementStatus), default=RequirementStatus.DRAFT, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
