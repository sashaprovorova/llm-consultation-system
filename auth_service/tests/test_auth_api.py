import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.api.deps import get_db
from app.db.base import Base
from app.main import app

@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient( transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()
    await engine.dispose()


# проверяем полный сценарий: регистрация, логин и получение профиля
@pytest.mark.asyncio
async def test_register_login_and_me(client: AsyncClient) -> None:
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "provorova@email.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201
    assert register_response.json()["email"] == "provorova@email.com"

    login_response = await client.post(
        "/auth/login",
        data={
            "username": "provorova@email.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    me_response = await client.get(  "/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "provorova@email.com"


# проверяем, что нельзя зарегистрировать один email два раза
@pytest.mark.asyncio
async def test_duplicate_email_returns_409(client: AsyncClient) -> None:
    user_data = { "email": "duplicate@email.com", "password": "password123"}

    first_response = await client.post("/auth/register", json=user_data)
    second_response = await client.post("/auth/register", json=user_data)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


# проверяем, что неправильный пароль не даёт токен
@pytest.mark.asyncio
async def test_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={ "email": "wrongpass@email.com", "password": "password123"},
    )

    response = await client.post(
        "/auth/login",
        data={ "username": "wrongpass@email.com", "password": "wrong_password"},
    )

    assert response.status_code == 401

# проверяем, что /auth/me защищён и без токена недоступен
@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401