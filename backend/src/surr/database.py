import logging
from collections.abc import Iterator  # noqa: TC003
from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from surr.app.core.config import settings

logger = logging.getLogger(__name__)


engine = create_async_engine(
    settings.POSTGRES_ASYNC_URI, echo=False, pool_pre_ping=True
)


AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False)


def get_session() -> Iterator[async_sessionmaker]:
    try:
        yield AsyncSessionLocal
    except SQLAlchemyError:
        logger.exception("Database error occurred")
        raise


SessionFactory = Annotated[async_sessionmaker, Depends(get_session)]
