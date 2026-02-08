from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy import select

from surr.app.models.rate_limit import RateLimit
from surr.database import SessionFactory


class DatabaseRateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window

    async def __call__(self, request: Request, session_factory: SessionFactory):
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"{request.url.path}:{client_ip}"
        now = datetime.now(UTC)

        async with session_factory() as db, db.begin():
            stmt = select(RateLimit).where(RateLimit.key == key).with_for_update()
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()

            if not record:
                # Create new record
                record = RateLimit(
                    key=key, count=1, reset_at=now + timedelta(seconds=self.window)
                )
                db.add(record)
            elif now > record.reset_at:
                # Window expired, reset counter
                record.count = 1
                record.reset_at = now + timedelta(seconds=self.window)
            else:
                # Inside window, check limit
                if record.count >= self.requests:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please try again later.",
                    )
                record.count += 1
