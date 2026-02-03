from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from pwdlib import PasswordHash

from surr.app.core.config import settings

password_hash = PasswordHash.recommended()
SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    BEARER = "bearer"


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
