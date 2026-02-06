from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from surr.app.api.v1.auth.use_cases import RefreshAccessToken
from surr.app.core.security import oauth2_scheme

from .schema import Token, UserCreate, UserRead
from .use_cases import LoginUser, LogoutUser, RegisterUser

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    use_case: Annotated[LoginUser, Depends(LoginUser)],
) -> Token:
    return await use_case.execute(form_data.username, form_data.password, response)


@router.post("/logout")
async def logout(
    response: Response,
    use_case: Annotated[LogoutUser, Depends(LogoutUser)],
    access_token: Annotated[str, Depends(oauth2_scheme)],
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> dict[str, str]:
    return await use_case.execute(access_token, refresh_token, response)


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    use_case: Annotated[RefreshAccessToken, Depends(RefreshAccessToken)],
) -> Token:
    return await use_case.execute(request, response)


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    use_case: Annotated[RegisterUser, Depends(RegisterUser)],
) -> UserRead:
    return await use_case.execute(user_in)
