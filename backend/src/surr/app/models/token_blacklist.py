from datetime import datetime  # noqa: TC003

from sqlalchemy import DateTime, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TokenBlacklist(Base):
    """Model for blacklisted JWT tokens."""

    __tablename__ = "token_blacklist"

    id: Mapped[int] = mapped_column(
        "id",
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    @classmethod
    async def read_by_id(
        cls, session: AsyncSession, token_id: int
    ) -> TokenBlacklist | None:
        stmt = select(cls).where(cls.id == token_id)
        return await session.scalar(stmt)

    @classmethod
    async def create(
        cls, session: AsyncSession, token: str, expires_at: datetime
    ) -> TokenBlacklist:
        blacklist_entry = cls(token=token, expires_at=expires_at)
        session.add(blacklist_entry)
        await session.flush()

        new = await cls.read_by_id(session, blacklist_entry.id)
        if not new:
            msg = "TokenBlacklist creation failed"
            raise RuntimeError(msg)
        return new
