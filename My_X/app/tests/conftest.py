import os
import re
import subprocess

import pytest
import pytest_asyncio
import sentry_sdk
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..database.database import Base, get_session
from ..main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(autouse=True, scope="function")
async def test_db_session():
    """
    Async test fixture to provide a database session for testing.

    This fixture creates the database schema before each test and drops it after.
    It yields a session object for interacting with the test database.

    Yields:
        AsyncSession: A database session for the test context.
    """
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def pg_tmp_url():
    """
    Fixture to start and manage a temporary PostgreSQL instance using `pg_tmp`.

    This fixture starts a `pg_tmp` process, extracts the database URL, and yields it.
    The PostgreSQL instance is stopped after the test session ends.

    Yields:
        str: A temporary PostgreSQL database URL.

    Raises:
        RuntimeError: If `pg_tmp` fails to start or the output cannot be parsed.
    """
    proc = subprocess.Popen(
        ["pg_tmp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to start pg_tmp: {stderr}")

    match = re.search(r"(postgresql:///.+)", stdout)
    if not match:
        raise RuntimeError(f"Could not parse pg_tmp output: {stdout}")
    pg_url = match.group(1)
    print(f"Using pg_url: {pg_url}")
    yield pg_url

    try:
        subprocess.run(["pg_tmp", "stop"], check=True)
    except subprocess.CalledProcessError:
        print("Warning: pg_tmp stop failed, possibly already stopped.")


@pytest_asyncio.fixture(scope="function")
async def test_postgresql_db_session(pg_tmp_url):
    """
    Async test fixture to provide a session connected to a temporary PostgreSQL instance.

    This fixture sets up the database schema, yields a session, and tears down the schema
    after the test.

    Args:
        pg_tmp_url (str): A PostgreSQL URL provided by the `pg_tmp_url` fixture.

    Yields:
        AsyncSession: A session object for interacting with the test database.
    """
    test_engine = create_async_engine(
        pg_tmp_url.replace("postgresql://", "postgresql+asyncpg://"), echo=False
    )
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_postgresql_db_session):
    """
    Async test fixture to provide a test client for the FastAPI application.

    Overrides the database session dependency with a test session and provides an `AsyncClient`
    for sending HTTP requests to the application.

    Args:
        test_postgresql_db_session (AsyncSession): A test database session provided by the
        `test_postgresql_db_session` fixture.

    Yields:
        AsyncClient: An HTTP client for testing the application.
    """

    async def override_get_session():
        yield test_postgresql_db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        base_url="http://test", transport=ASGITransport(app)
    ) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def disable_sentry():
    """
    Fixture to disable Sentry error tracking during tests.

    This fixture initializes Sentry with a `None` DSN and flushes any queued events
    after the session ends.
    """
    sentry_sdk.init(dsn=None)
    yield
    sentry_sdk.flush()


@pytest.fixture(scope="session", autouse=True)
def isolate_environment():
    """
    Fixture to isolate the environment during tests.

    This fixture temporarily removes specific environment variables (e.g., database-related)
    and restores them after the test session ends.

    Yields:
        None
    """
    original_env = os.environ.copy()
    for key in ["DATABASE_URL", "DB_HOST", "DB_PORT"]:
        os.environ.pop(key, None)
    yield
    os.environ.update(original_env)
