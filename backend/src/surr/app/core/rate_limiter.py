import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from surr.app.models.rate_limit import RateLimit
from surr.database import AsyncSessionLocal, SessionFactory

if TYPE_CHECKING:
    from collections.abc import Coroutine

logger = logging.getLogger(__name__)


class DatabaseRateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window

    async def __call__(self, request: Request, session_factory: SessionFactory):
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"{request.url.path}:{client_ip}"
        now = datetime.now(UTC)

        # Retry loop to handle the specific race condition where two requests
        # try to create the row at the same time.
        for attempt in range(3):
            try:
                async with session_factory() as db, db.begin():
                    stmt = (
                        select(RateLimit).where(RateLimit.key == key).with_for_update()
                    )
                    result = await db.execute(stmt)
                    record = result.scalar_one_or_none()

                    if not record:
                        record = RateLimit(
                            key=key,
                            count=1,
                            reset_at=now + timedelta(seconds=self.window),
                        )
                        db.add(record)
                        await db.flush()

                    elif now > record.reset_at:
                        record.count = 1
                        record.reset_at = now + timedelta(seconds=self.window)
                    else:
                        if record.count >= self.requests:
                            raise HTTPException(
                                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Too many requests. Please try again later.",
                            )
                        record.count += 1

            except IntegrityError:
                # This specific error means someone else inserted the row
                # between our 'select' and our 'insert'.
                # We simply loop again; the next select will find the new row.
                if attempt == 2:  # noqa: PLR2004
                    logger.exception(
                        "Failed to acquire rate limit lock for %s after retries.", key
                    )
                    raise
                continue

            else:
                return


async def delete_expired_rate_limits() -> Coroutine:
    """Background task to cleanup expired rate limit rows."""
    while True:
        try:
            await asyncio.sleep(600)

            async with AsyncSessionLocal() as db, db.begin():
                stmt = delete(RateLimit).where(RateLimit.reset_at < datetime.now(UTC))
                await db.execute(stmt)

        except Exception:
            logger.exception("Error cleaning rate limits")
            await asyncio.sleep(60)
