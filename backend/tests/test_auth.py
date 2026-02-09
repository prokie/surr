import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from surr.app.core.security import get_password_hash
from surr.app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession) -> None:
    hashed_pw = get_password_hash("securepassword")
    user = User(username="testuser", hashed_password=hashed_pw)
    db_session.add(user)
    await db_session.flush()

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
    await db_session.flush()

    response = await client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient, db_session: AsyncSession) -> None:
    payload = {"username": "newuser", "password": "securepassword123"}

    response = await client.post("/api/auth/signup", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["username"] == payload["username"]
    assert "password" not in data

    # Verify user was actually created in DB
    stmt = select(User).where(User.username == payload["username"])
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None


@pytest.mark.asyncio
async def test_signup_rate_limit(client: AsyncClient) -> None:
    payload = {"username": "spammer", "password": "password123"}

    # Send 5 allowed requests (assuming limit is 5)
    for i in range(5):
        payload["username"] = f"spammer_{i}"
        response = await client.post("/api/auth/signup", json=payload)
        assert response.status_code == 201

    # Send 6th request - should fail
    payload["username"] = "spammer_blocked"
    response = await client.post("/api/auth/signup", json=payload)

    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]
