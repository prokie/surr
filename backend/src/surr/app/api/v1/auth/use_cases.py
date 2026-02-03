from fastapi import HTTPException, Response, status
from sqlalchemy import select

from surr.app.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    TokenType,
    blacklist_tokens,
    create_token,
    verify_password,
)
from surr.app.models.user import User
from surr.database import SessionFactory

from .schema import Token


class LoginUser:
    def __init__(self, session: SessionFactory):
        self.session = session

    async def execute(self, username: str, password: str, response: Response) -> Token:
        stmt = select(User).where(User.username == username)

        async with self.session() as db:
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
            )

        access_token = create_token(
            data={"sub": user.username}, token_type=TokenType.ACCESS
        )
        response.set_cookie(
            key="refresh_token",
            value=create_token(
                data={"sub": user.username}, token_type=TokenType.REFRESH
            ),
            httponly=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        return Token(access_token=access_token, token_type=TokenType.BEARER)


class LogoutUser:
    def __init__(self, session: SessionFactory):
        self.session = session

    async def execute(
        self, access_token: str, refresh_token: str | None, response: Response
    ) -> None:
        async with self.session() as db:
            await blacklist_tokens(access_token, refresh_token, db)
        response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
