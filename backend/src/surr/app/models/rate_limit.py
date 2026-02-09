from datetime import datetime  # noqa: TC003
from typing import ClassVar

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RateLimit(Base):
    __tablename__ = "rate_limits"
    __table_args__: ClassVar[dict] = {"prefixes": ["UNLOGGED"]}

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    reset_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    count: Mapped[int] = mapped_column(default=0, nullable=False)
