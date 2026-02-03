from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    """ORM model for users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        "id",
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    @classmethod
    async def read_by_id(cls, session: AsyncSession, user_id: int) -> User | None:
        stmt = select(cls).where(cls.id == user_id)
        return await session.scalar(stmt)

    @classmethod
    async def create(cls, session: AsyncSession, username: str, password: str) -> User:
        user = User(username=username, hashed_password=password)
        session.add(user)
        await session.flush()

        new = await cls.read_by_id(session, user.id)
        if not new:
            msg = "User creation failed"
            raise RuntimeError(msg)
        return new
