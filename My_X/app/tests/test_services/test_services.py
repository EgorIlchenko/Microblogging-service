import pytest
from fastapi import HTTPException

from ...api.services.services import get_current_user
from ...database.models.models import Users


@pytest.mark.asyncio
@pytest.mark.Services
async def test_get_current_user_valid_key(test_db_session):
    """
    Test `get_current_user` with a valid API key.

    This test verifies that the function correctly retrieves a user when provided with a
    valid API key.

    Args:
        test_db_session (AsyncSession): A test database session provided by the `test_db_session`
        fixture.

    Steps:
        1. Create and commit a new user with a known API key.
        2. Call `get_current_user` with the valid API key.
        3. Assert that the returned user matches the created user.

    Assertions:
        - The returned user's ID, name, and API key match the created user's attributes.
    """
    new_user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(new_user)
    await test_db_session.commit()

    result = await get_current_user(api_key="Test_api_key", session=test_db_session)

    assert result.id == new_user.id
    assert result.name == new_user.name
    assert result.api_key == new_user.api_key


@pytest.mark.asyncio
@pytest.mark.Services
async def test_get_current_user_invalid_key(test_db_session):
    """
    Test `get_current_user` with an invalid API key.

    This test verifies that the function raises an HTTPException when provided with an
    invalid API key.

    Args:
        test_db_session (AsyncSession): A test database session provided by the `test_db_session`
        fixture.

    Steps:
        1. Create and commit a new user with a known API key.
        2. Call `get_current_user` with an invalid API key.
        3. Assert that an HTTPException is raised with the expected status code and detail.

    Assertions:
        - The raised exception has a status code of 401 (Unauthorized).
        - The raised exception's detail message is "Invalid API Key".
    """
    new_user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(new_user)
    await test_db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(api_key="Wrong_api_key", session=test_db_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid API Key"
