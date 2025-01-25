import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...api.user.repositoryes import FollowerRepository, UserRepository
from ...database.models.models import Follower, Users


@pytest.mark.asyncio
@pytest.mark.UserRepository
async def test_user_repository_get_by_api_key(test_db_session):
    """
    Test `UserRepository.get_by_api_key`.

    Ensures that a user can be retrieved by their API key.

    Steps:
        1. Add a user to the database with a specific API key.
        2. Call `get_by_api_key` with the user's API key.
        3. Verify the returned user matches the expected data.

    Assertions:
        - The returned user is not `None`.
        - The user's name matches the expected value.
    """
    repo: UserRepository = UserRepository(session=test_db_session)

    new_user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(new_user)
    await test_db_session.commit()

    result = await repo.get_by_api_key(api_key=new_user.api_key)

    assert result is not None
    assert result.name == "Test_user"


@pytest.mark.asyncio
@pytest.mark.UserRepository
async def test_user_repository_get_by_id(test_db_session):
    """
    Test `UserRepository.get_by_id`.

    Ensures that a user can be retrieved by their ID.

    Steps:
        1. Add a user to the database.
        2. Call `get_by_id` with the user's ID.
        3. Verify the returned user matches the expected data.

    Assertions:
        - The returned user is not `None`.
        - The user's name matches the expected value.
    """
    repo: UserRepository = UserRepository(session=test_db_session)

    new_user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(new_user)
    await test_db_session.commit()

    result = await repo.get_by_id(user_id=new_user.id)

    assert result is not None
    assert result.name == "Test_user"


@pytest.mark.asyncio
@pytest.mark.FollowerRepository
async def test_follower_repository_add(test_db_session):
    """
    Test `FollowerRepository.add`.

    Ensures that a follower relationship is added to the database.

    Steps:
        1. Add two users to the database.
        2. Create a follower relationship and call `add`.
        3. Verify the follower relationship is saved in the database.

    Assertions:
        - The follower relationship is present in the database.
        - The follower and followee IDs match the expected values.
    """
    repo: FollowerRepository = FollowerRepository(session=test_db_session)

    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    test_db_session.add_all([new_user_1, new_user_2])
    await test_db_session.commit()

    new_follow: Follower = Follower(
        follower_id=new_user_2.id, followee_id=new_user_1.id
    )
    await repo.add(new_follow)

    result = await test_db_session.execute(select(Follower).where(Follower.id == 1))
    result = result.scalar_one_or_none()

    assert result is not None
    assert result.follower_id == 2
    assert result.followee_id == 1


@pytest.mark.asyncio
@pytest.mark.FollowerRepository
async def test_follower_repository_delete(test_db_session):
    """
    Test `FollowerRepository.delete`.

    Ensures that a follower relationship is removed from the database.

    Steps:
        1. Add two users and a follower relationship to the database.
        2. Call `delete` to remove the relationship.
        3. Verify the relationship is no longer in the database.

    Assertions:
        - The follower relationship is `None` after deletion.
    """
    repo: FollowerRepository = FollowerRepository(session=test_db_session)

    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    follower_relationship: Follower = Follower(follower_id=2, followee_id=1)
    test_db_session.add_all([new_user_1, new_user_2, follower_relationship])
    await test_db_session.commit()

    await repo.delete(follower_relationship)

    result = await test_db_session.execute(select(Follower).where(Follower.id == 1))
    result = result.scalar_one_or_none()

    assert result is None


@pytest.mark.asyncio
@pytest.mark.FollowerRepository
async def test_follower_repository_get_subscribe(test_db_session):
    """
    Test `FollowerRepository.get_subscribe`.

    Ensures that a specific follower relationship can be retrieved by its fields.

    Steps:
        1. Add two users and a follower relationship to the database.
        2. Call `get_subscribe` with the follower and followee IDs.
        3. Verify the returned relationship matches the expected data.

    Assertions:
        - The returned relationship is not `None`.
        - The follower and followee IDs match the expected values.
    """
    repo: FollowerRepository = FollowerRepository(session=test_db_session)

    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    follower_relationship: Follower = Follower(follower_id=2, followee_id=1)
    test_db_session.add_all([new_user_1, new_user_2, follower_relationship])
    await test_db_session.commit()

    result = await repo.get_subscribe(
        follower_id=new_user_2.id, followee_id=new_user_1.id
    )

    assert result is not None
    assert result.follower_id == 2
    assert result.followee_id == 1


@pytest.mark.asyncio
@pytest.mark.FollowerRepository
async def test_follower_repository_filter_by_field(test_db_session):
    """
    Test `FollowerRepository.filter` by specific fields.

    Ensures that follower relationships can be filtered by fields such as ID.

    Steps:
        1. Add two users and a follower relationship to the database.
        2. Call `filter` with a specific ID.
        3. Verify the returned relationships match the expected data.

    Assertions:
        - The number of returned relationships matches the expected count.
        - The follower and followee IDs match the expected values.
    """
    repo: FollowerRepository = FollowerRepository(session=test_db_session)

    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    follower_relationship: Follower = Follower(follower_id=2, followee_id=1)
    test_db_session.add_all([new_user_1, new_user_2, follower_relationship])
    await test_db_session.commit()

    result = await repo.filter(id=1)

    assert len(result) == 1
    assert result[0].follower_id == 2
    assert result[0].followee_id == 1


@pytest.mark.asyncio
@pytest.mark.FollowerRepository
async def test_follower_repository_filter_with_options(test_db_session):
    """
    Test `FollowerRepository.filter` with query options.

    Ensures that the `filter` method supports query options such as eager loading.

    Steps:
        1. Add two users and a follower relationship to the database.
        2. Call `filter` with the `selectinload` option for the `follower` relationship.
        3. Verify the returned relationships include the loaded follower data.

    Assertions:
        - The number of returned relationships matches the expected count.
        - The follower data is loaded and matches the expected values.
    """
    repo: FollowerRepository = FollowerRepository(session=test_db_session)

    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    follower_relationship: Follower = Follower(follower_id=2, followee_id=1)
    test_db_session.add_all([new_user_1, new_user_2, follower_relationship])
    await test_db_session.commit()

    result = await repo.filter(options=[selectinload(Follower.follower)])

    assert len(result) == 1
    assert result[0].follower_id == 2
    assert result[0].followee_id == 1
    assert result[0].follower.name == "Test_user_2"
