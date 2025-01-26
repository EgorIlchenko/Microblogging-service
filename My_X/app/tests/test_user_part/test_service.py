import pytest
from fastapi import HTTPException
from sqlalchemy import and_, select

from ...api.user.service import UserServices
from ...database.models.models import Follower, Users


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_add_subscribe_success(test_db_session):
    """
    Test successfully adding a subscription.

    Steps:
        1. Add two users to the database.
        2. Call `add_subscribe` to create a subscription from one user to another.
        3. Verify the subscription is created in the database.

    Assertions:
        - The result indicates success.
        - The subscription is present in the database.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    test_db_session.add_all([new_user_1, new_user_2])
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    result = await service.add_subscribe(user=new_user_1, id=new_user_2.id)

    subscribe = await test_db_session.execute(
        select(Follower).where(
            and_(
                Follower.follower_id == new_user_1.id,
                Follower.followee_id == new_user_2.id,
            )
        )
    )

    assert result["result"] is True
    assert subscribe.fetchone() is not None


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_add_subscribe_to_yourself(test_db_session):
    """
    Test attempting to subscribe to oneself.

    Steps:
        1. Add a user to the database.
        2. Call `add_subscribe` with the user's own ID.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 409.
        - The error message indicates self-subscription is not allowed.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_db_session.add(new_user)
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.add_subscribe(user=new_user, id=new_user.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "You can't subscribe to yourself"


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_add_subscribe_to_non_existent_user(test_db_session):
    """
    Test subscribing to a non-existent user.

    Steps:
        1. Add a user to the database.
        2. Call `add_subscribe` with an invalid user ID.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 404.
        - The error message indicates the user does not exist.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_db_session.add(new_user)
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.add_subscribe(user=new_user, id=999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_delete_subscribe_success(test_db_session):
    """
    Test successfully deleting a subscription.

    Steps:
        1. Add two users and a subscription relationship to the database.
        2. Call `delete_subscribe` to remove the subscription.
        3. Verify the subscription is deleted from the database.

    Assertions:
        - The result indicates success.
        - The subscription is no longer in the database.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    follower_relationship: Follower = Follower(follower_id=1, followee_id=2)
    test_db_session.add_all([new_user_1, new_user_2, follower_relationship])
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    result = await service.delete_subscribe(user=new_user_1, id=new_user_2.id)

    subscribe = await test_db_session.execute(
        select(Follower).where(
            and_(
                Follower.follower_id == new_user_1.id,
                Follower.followee_id == new_user_2.id,
            )
        )
    )

    assert result["result"] is True
    assert subscribe.scalars().first() is None


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_delete_subscribe_to_yourself(test_db_session):
    """
    Test attempting to unsubscribe from oneself.

    Steps:
        1. Add a user to the database.
        2. Call `delete_subscribe` with the user's own ID.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 409.
        - The error message indicates self-unsubscription is not allowed.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_db_session.add(new_user)
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_subscribe(user=new_user, id=new_user.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "You can't unsubscribe from yourself"


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_delete_subscribe_to_non_existent_user(test_db_session):
    """
    Test unsubscribing from a non-existent user.

    Steps:
        1. Add a user to the database.
        2. Call `delete_subscribe` with an invalid user ID.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 404.
        - The error message indicates the user does not exist.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_db_session.add(new_user)
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_subscribe(user=new_user, id=999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_delete_a_non_existent_subscription(test_db_session):
    """
    Test deleting a non-existent subscription.

    Steps:
        1. Add two users without any subscription relationship.
        2. Call `delete_subscribe` to remove a non-existent subscription.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 404.
        - The error message indicates no existing subscription.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    test_db_session.add_all([new_user_1, new_user_2])
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_subscribe(user=new_user_1, id=new_user_2.id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "You haven't subscribed to this user yet"


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_get_my_data(test_db_session):
    """
    Test retrieving the current user's data.

    Steps:
        1. Add three users and multiple subscriptions to the database.
        2. Call `get_my_data` with the current user.
        3. Verify the response contains the correct follower and following data.

    Assertions:
        - The result indicates success.
        - The user data includes the correct number of followers and following users.
        - The follower and following names match the expected values.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    new_user_3: Users = Users(name="Test_user_3", api_key="Test_api_key_3")
    subscribe_1: Follower = Follower(follower_id=1, followee_id=2)
    subscribe_2: Follower = Follower(follower_id=2, followee_id=1)
    subscribe_3: Follower = Follower(follower_id=3, followee_id=1)
    test_db_session.add_all(
        [new_user_1, new_user_2, new_user_3, subscribe_1, subscribe_2, subscribe_3]
    )
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    result = await service.get_my_data(user=new_user_1)
    user_data = result["user"]

    assert result["result"] is True
    assert user_data["id"] == new_user_1.id
    assert len(user_data["followers"]) == 2
    assert len(user_data["following"]) == 1
    assert user_data["followers"][0]["name"] == new_user_2.name
    assert user_data["followers"][1]["name"] == new_user_3.name
    assert user_data["following"][0]["name"] == new_user_2.name


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_get_user_data_by_id_success(test_db_session):
    """
    Test retrieving data for another user by ID.

    Steps:
        1. Add three users and multiple subscriptions to the database.
        2. Call `get_user_data_by_id` with a target user's ID.
        3. Verify the response contains the correct follower and following data.

    Assertions:
        - The result indicates success.
        - The user data matches the expected values for the target user.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    new_user_3: Users = Users(name="Test_user_3", api_key="Test_api_key_3")
    subscribe_1: Follower = Follower(follower_id=1, followee_id=2)
    subscribe_2: Follower = Follower(follower_id=2, followee_id=1)
    subscribe_3: Follower = Follower(follower_id=3, followee_id=1)
    test_db_session.add_all(
        [new_user_1, new_user_2, new_user_3, subscribe_1, subscribe_2, subscribe_3]
    )
    await test_db_session.commit()

    service: UserServices = UserServices(session=test_db_session)

    result = await service.get_user_data_by_id(id=new_user_1.id)
    user_data = result["user"]

    assert result["result"] is True
    assert user_data["id"] == new_user_1.id
    assert len(user_data["followers"]) == 2
    assert len(user_data["following"]) == 1
    assert user_data["followers"][0]["name"] == new_user_2.name
    assert user_data["followers"][1]["name"] == new_user_3.name
    assert user_data["following"][0]["name"] == new_user_2.name


@pytest.mark.asyncio
@pytest.mark.UserServices
async def test_get_user_data_by_id_with_non_existent_user(test_db_session):
    """
    Test retrieving data for a non-existent user.

    Steps:
        1. Call `get_user_data_by_id` with an invalid user ID.
        2. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 404.
        - The error message indicates the user does not exist.
    """
    service: UserServices = UserServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_user_data_by_id(id=999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"
