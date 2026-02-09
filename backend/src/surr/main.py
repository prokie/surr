import asyncio
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from surr.app.api.main import router as api_router
from surr.app.core.config import settings
from surr.app.core.rate_limiter import delete_expired_rate_limits

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(delete_expired_rate_limits())

    yield

    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,  # ty:ignore[invalid-argument-type]
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_METHODS,
)


app.include_router(api_router, prefix="/api")
