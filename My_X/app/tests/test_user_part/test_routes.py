import pytest
from sqlalchemy import and_, select

from ...database.models.models import Follower, Users


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_add_subscribe_success(client, test_postgresql_db_session):
    """
    Test successfully subscribing to another user.

    Steps:
        1. Add two users to the database.
        2. Send a POST request to subscribe the first user to the second.
        3. Verify the subscription is created in the database.

    Assertions:
        - The response status is 200.
        - The subscription is present in the database.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    test_postgresql_db_session.add_all([new_user_1, new_user_2])
    await test_postgresql_db_session.commit()

    response = await client.post(
        f"/api/users/{new_user_2.id}/follow",
        headers={"api-key": new_user_1.api_key},
    )
    response_data = response.json()

    result = await test_postgresql_db_session.execute(
        select(Follower).where(
            and_(
                Follower.follower_id == new_user_1.id,
                Follower.followee_id == new_user_2.id,
            )
        )
    )
    subscribe = result.scalar_one_or_none()

    assert response.status_code == 200
    assert response_data["result"] is True
    assert subscribe is not None


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_add_subscribe_to_yourself(client, test_postgresql_db_session):
    """
    Test attempting to subscribe to oneself.

    Steps:
        1. Add a user to the database.
        2. Send a POST request to subscribe the user to themselves.
        3. Verify the response contains a conflict error.

    Assertions:
        - The response status is 409.
        - The error message indicates self-subscription is not allowed.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_postgresql_db_session.add(new_user)
    await test_postgresql_db_session.commit()

    response = await client.post(
        f"/api/users/{new_user.id}/follow",
        headers={"api-key": new_user.api_key},
    )
    response_data = response.json()

    assert response.status_code == 409
    assert response_data["error_message"] == "You can't subscribe to yourself"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_add_subscribe_to_non_existent_user(client, test_postgresql_db_session):
    """
    Test subscribing to a non-existent user.

    Steps:
        1. Add a user to the database.
        2. Send a POST request to subscribe the user to a non-existent ID.
        3. Verify the response contains a "user not found" error.

    Assertions:
        - The response status is 404.
        - The error message indicates the user does not exist.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_postgresql_db_session.add(new_user)
    await test_postgresql_db_session.commit()

    response = await client.post(
        "/api/users/999/follow",
        headers={"api-key": new_user.api_key},
    )
    response_data = response.json()

    assert response.status_code == 404
    assert response_data["error_message"] == "User not found"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_delete_subscribe_success(client, test_postgresql_db_session):
    """
    Test successfully unsubscribing from another user.

    Steps:
        1. Add two users and a subscription relationship to the database.
        2. Send a DELETE request to unsubscribe the first user from the second.
        3. Verify the subscription is removed from the database.

    Assertions:
        - The response status is 200.
        - The subscription is no longer in the database.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    follower_relationship: Follower = Follower(follower_id=1, followee_id=2)
    test_postgresql_db_session.add_all([new_user_1, new_user_2, follower_relationship])
    await test_postgresql_db_session.commit()

    response = await client.delete(
        f"/api/users/{new_user_2.id}/follow",
        headers={"api-key": new_user_1.api_key},
    )
    response_data = response.json()

    result = await test_postgresql_db_session.execute(
        select(Follower).where(
            and_(
                Follower.follower_id == new_user_1.id,
                Follower.followee_id == new_user_2.id,
            )
        )
    )
    subscribe = result.scalar_one_or_none()

    assert response.status_code == 200
    assert response_data["result"] is True
    assert subscribe is None


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_delete_subscribe_to_yourself(client, test_postgresql_db_session):
    """
    Test attempting to unsubscribe from oneself.

    Steps:
        1. Add a user to the database.
        2. Send a DELETE request to unsubscribe the user from themselves.
        3. Verify the response contains a conflict error.

    Assertions:
        - The response status is 409.
        - The error message indicates self-unsubscription is not allowed.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_postgresql_db_session.add(new_user)
    await test_postgresql_db_session.commit()

    response = await client.delete(
        f"/api/users/{new_user.id}/follow",
        headers={"api-key": new_user.api_key},
    )
    response_data = response.json()

    assert response.status_code == 409
    assert response_data["error_message"] == "You can't unsubscribe from yourself"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_delete_subscribe_to_non_existent_user(
    client, test_postgresql_db_session
):
    """
    Test unsubscribing from a non-existent user.

    Steps:
        1. Add a user to the database.
        2. Send a DELETE request to unsubscribe the user from a non-existent ID.
        3. Verify the response contains a "user not found" error.

    Assertions:
        - The response status is 404.
        - The error message indicates the user does not exist.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_postgresql_db_session.add(new_user)
    await test_postgresql_db_session.commit()

    response = await client.delete(
        "/api/users/999/follow",
        headers={"api-key": new_user.api_key},
    )
    response_data = response.json()

    assert response.status_code == 404
    assert response_data["error_message"] == "User not found"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_delete_a_non_existent_subscription(client, test_postgresql_db_session):
    """
    Test deleting a non-existent subscription.

    Steps:
        1. Add two users to the database without any subscription relationship.
        2. Send a DELETE request to remove a non-existent subscription.
        3. Verify the response contains a "not subscribed" error.

    Assertions:
        - The response status is 404.
        - The error message indicates there is no existing subscription.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    test_postgresql_db_session.add_all([new_user_1, new_user_2])
    await test_postgresql_db_session.commit()

    response = await client.delete(
        f"/api/users/{new_user_2.id}/follow",
        headers={"api-key": new_user_1.api_key},
    )
    response_data = response.json()

    assert response.status_code == 404
    assert response_data["error_message"] == "You haven't subscribed to this user yet"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_get_me_data(client, test_postgresql_db_session):
    """
    Test retrieving the current user's data.

    Steps:
        1. Add three users and multiple subscriptions to the database.
        2. Send a GET request with the current user's API key.
        3. Verify the response contains the correct follower and following data.

    Assertions:
        - The response status is 200.
        - The user data includes the correct number of followers and following users.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    new_user_3: Users = Users(name="Test_user_3", api_key="Test_api_key_3")
    subscribe_1: Follower = Follower(follower_id=1, followee_id=2)
    subscribe_2: Follower = Follower(follower_id=2, followee_id=1)
    subscribe_3: Follower = Follower(follower_id=3, followee_id=1)
    test_postgresql_db_session.add_all(
        [new_user_1, new_user_2, new_user_3, subscribe_1, subscribe_2, subscribe_3]
    )
    await test_postgresql_db_session.commit()

    response = await client.get(
        "/api/users/me",
        headers={"api-key": new_user_1.api_key},
    )
    response_data = response.json()

    user_data = response_data["user"]

    assert response_data["result"] is True
    assert user_data["id"] == new_user_1.id
    assert len(user_data["followers"]) == 2
    assert len(user_data["following"]) == 1
    assert user_data["followers"][0]["name"] == new_user_2.name
    assert user_data["followers"][1]["name"] == new_user_3.name
    assert user_data["following"][0]["name"] == new_user_2.name


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_get_user_data_by_id_success(client, test_postgresql_db_session):
    """
    Test retrieving another user's data by ID.

    Steps:
        1. Add three users and multiple subscriptions to the database.
        2. Send a GET request with a target user's ID.
        3. Verify the response contains the correct follower and following data.

    Assertions:
        - The response status is 200.
        - The user data matches the expected values for the target user.
    """
    new_user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    new_user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    new_user_3: Users = Users(name="Test_user_3", api_key="Test_api_key_3")
    subscribe_1: Follower = Follower(follower_id=1, followee_id=2)
    subscribe_2: Follower = Follower(follower_id=2, followee_id=1)
    subscribe_3: Follower = Follower(follower_id=3, followee_id=1)
    test_postgresql_db_session.add_all(
        [new_user_1, new_user_2, new_user_3, subscribe_1, subscribe_2, subscribe_3]
    )
    await test_postgresql_db_session.commit()

    response = await client.get(
        f"/api/users/{new_user_2.id}",
        headers={"api-key": new_user_1.api_key},
    )
    response_data = response.json()

    user_data = response_data["user"]

    assert response_data["result"] is True
    assert user_data["id"] == new_user_2.id
    assert len(user_data["followers"]) == 1
    assert len(user_data["following"]) == 1
    assert user_data["followers"][0]["name"] == new_user_1.name
    assert user_data["following"][0]["name"] == new_user_1.name


@pytest.mark.asyncio
@pytest.mark.user_routes
async def test_get_user_data_by_id_with_non_existent_user(
    client, test_postgresql_db_session
):
    """
    Test retrieving data for a non-existent user.

    Steps:
        1. Add a user to the database.
        2. Send a GET request with a non-existent user ID.
        3. Verify the response contains a "user not found" error.

    Assertions:
        - The response status is 404.
        - The error message indicates the user does not exist.
    """
    new_user: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    test_postgresql_db_session.add(new_user)
    await test_postgresql_db_session.commit()

    response = await client.get(
        "/api/users/999",
        headers={"api-key": new_user.api_key},
    )
    response_data = response.json()

    assert response.status_code == 404
    assert response_data["error_message"] == "User not found"
    assert response_data["result"] is False
