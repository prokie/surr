import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from surr.app.core.security import get_password_hash
from surr.app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession) -> None:
    hashed_pw = get_password_hash("securepassword")
    user = User(username="testuser", hashed_password=hashed_pw)
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "securepassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    hashed_pw = get_password_hash("securepassword")
    user = User(username="testuser", hashed_password=hashed_pw)
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401
