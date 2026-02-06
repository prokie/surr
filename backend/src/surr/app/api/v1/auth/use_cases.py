from fastapi import HTTPException, Request, Response, status
from sqlalchemy import select

from surr.app.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    TokenType,
    blacklist_token,
    blacklist_tokens,
    create_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from surr.app.models import TokenBlacklist
from surr.app.models.user import User
from surr.database import SessionFactory

from .schema import Token

# We verify against this when the user is not found to simulate the
# computational time of a real password check, mitigating timing attacks.
DUMMY_HASH = get_password_hash("dummy_password_for_timing_protection")


class LoginUser:
    def __init__(self, session: SessionFactory):
        self.session = session

    async def execute(self, username: str, password: str, response: Response) -> Token:
        stmt = select(User).where(User.username == username)

        async with self.session() as db:
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

        # To prevent timing attacks, we always verify the password.
        # If the user exists, we use their hash. If not, we use the dummy hash.
        target_hash = user.hashed_password if user else DUMMY_HASH
        is_password_valid = verify_password(password, target_hash)

        if not user or not is_password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
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
    ) -> dict[str, str]:
        async with self.session() as db:
            await blacklist_tokens(access_token, refresh_token, db)
        response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")

        return {"message": "Successfully logged out"}


class RefreshAccessToken:
    def __init__(self, session: SessionFactory):
        self.session = session

    async def execute(self, request: Request, response: Response) -> Token:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
            )

        token_data = verify_token(refresh_token, TokenType.REFRESH)
        if not token_data or not token_data.username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        stmt = select(User).where(User.username == token_data.username)

        async with self.session() as db:
            if await TokenBlacklist.exists(db, refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been blacklisted",
                )

            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
                )

            await blacklist_token(refresh_token, db)
            await db.commit()

        new_access_token = create_token(
            data={"sub": user.username}, token_type=TokenType.ACCESS
        )
        new_refresh_token = create_token(
            data={"sub": user.username}, token_type=TokenType.REFRESH
        )

        # 6. Set new cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return Token(access_token=new_access_token, token_type=TokenType.BEARER)
