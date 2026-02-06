import contextlib
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from surr.app.core.config import settings
from surr.app.models.token_blacklist import TokenBlacklist

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    BEARER = "bearer"


class TokenData(BaseModel):
    username: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_token(
    data: dict[str, Any], token_type: TokenType, expires_delta: timedelta | None = None
) -> str:
    if "sub" not in data or not data["sub"]:
        msg = "JWT payload must include a non-empty 'sub' (subject) claim"
        raise ValueError(msg)

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        minutes = (
            ACCESS_TOKEN_EXPIRE_MINUTES
            if token_type == TokenType.ACCESS
            else (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60)
        )
        expire = datetime.now(UTC) + timedelta(minutes=minutes)

    to_encode.update({"exp": expire, "token_type": token_type.value})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def blacklist_token(token: str, session: AsyncSession) -> None:
    if await TokenBlacklist.exists(session, token):
        return

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp = payload.get("exp")

    if exp is None:
        msg = "Cannot blacklist token without an expiration ('exp') claim"
        raise ValueError(msg)

    expires_at = datetime.fromtimestamp(exp, UTC)
    await TokenBlacklist.create(session, token=token, expires_at=expires_at)
    await session.commit()


async def blacklist_tokens(
    access_token: str, refresh_token: str | None, session: AsyncSession
) -> None:
    await blacklist_token(token=access_token, session=session)

    if refresh_token:
        with contextlib.suppress(jwt.PyJWTError):
            await blacklist_token(token=refresh_token, session=session)


def verify_token(token: str, expected_token_type: TokenType) -> TokenData | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        token_type: str | None = payload.get("token_type")

        if username is None or token_type != expected_token_type:
            return None

        return TokenData(username=username)

    except jwt.PyJWTError:
        return None
