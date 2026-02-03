from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

from .schema import Token, UserRead
from .use_cases import LoginUser

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=UserRead)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    use_case: Annotated[LoginUser, Depends(LoginUser)],
) -> Token:
    return await use_case.execute(form_data.username, form_data.password, response)
