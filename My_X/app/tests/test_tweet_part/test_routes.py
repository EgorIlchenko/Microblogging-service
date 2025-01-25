import os
import tempfile
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import UploadFile
from sqlalchemy import and_, select

from ...config.config import settings
from ...database.models.models import Follower, Like, Media, TweetMedia, Tweets, Users


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_create_tweet_without_media(client, test_postgresql_db_session):
    """
    Test creating a tweet without media.

    Steps:
        1. Create a user and authenticate using their API key.
        2. Send a POST request to create a tweet with no media.
        3. Query the database to verify the tweet is created.

    Assertions:
        - The response status is 200.
        - The tweet is saved in the database with the correct user ID and content.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_postgresql_db_session.add(user)
    await test_postgresql_db_session.commit()

    response = await client.post(
        "/api/tweets",
        json={"tweet_data": "Hello, world!", "tweet_media_ids": []},
        headers={"api-key": "Test_api_key"},
    )
    response_data = response.json()

    tweet = await test_postgresql_db_session.get(Tweets, response_data["tweet_id"])

    assert response.status_code == 200
    assert response_data["result"] is True
    assert "tweet_id" in response_data
    assert tweet is not None
    assert tweet.user_id == user.id
    assert tweet.content == "Hello, world!"


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_create_tweet_with_media(client, test_postgresql_db_session):
    """
    Test creating a tweet with media attachments.

    Steps:
        1. Create a user and media files in the database.
        2. Send a POST request to create a tweet with attached media.
        3. Verify the tweet and its media relationships in the database.

    Assertions:
        - The response status is 200.
        - The tweet and its media attachments are saved correctly.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    media_1: Media = Media(user_id=1, file_path="/media1.jpg")
    media_2: Media = Media(user_id=1, file_path="/media2.jpg")
    test_postgresql_db_session.add_all([user, media_1, media_2])
    await test_postgresql_db_session.commit()

    response = await client.post(
        "/api/tweets",
        json={"tweet_data": "Hello, world!", "tweet_media_ids": [1, 2]},
        headers={"api-key": "Test_api_key"},
    )
    response_data = response.json()

    result_tweet_media = await test_postgresql_db_session.execute(
        select(TweetMedia).where(and_(TweetMedia.tweet_id == response_data["tweet_id"]))
    )
    tweet = await test_postgresql_db_session.get(Tweets, response_data["tweet_id"])
    tweet_media = result_tweet_media.scalars().all()

    assert response.status_code == 200
    assert response_data["result"] is True
    assert "tweet_id" in response_data
    assert tweet is not None
    assert tweet_media is not None
    assert tweet.user_id == user.id
    assert tweet_media[0].media_id == media_1.id
    assert tweet_media[1].media_id == media_2.id


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_create_tweet_with_invalid_media(client, test_postgresql_db_session):
    """
    Test creating a tweet with non-existent media.

    Steps:
        1. Create a user and authenticate using their API key.
        2. Send a POST request to create a tweet referencing invalid media IDs.
        3. Verify the response contains an appropriate error message.

    Assertions:
        - The response status is 400.
        - The error message indicates that media files are inaccessible.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_postgresql_db_session.add(user)
    await test_postgresql_db_session.commit()

    response = await client.post(
        "/api/tweets",
        json={"tweet_data": "Hello, world!", "tweet_media_ids": [1]},
        headers={"api-key": "Test_api_key"},
    )
    response_data = response.json()

    assert response.status_code == 400
    assert response_data["result"] is False
    assert response_data["error_type"] == "HTTPException"
    assert (
        response_data["error_message"] == "Some media files not found or inaccessible"
    )


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_post_new_media_success(client, test_postgresql_db_session, monkeypatch):
    """
    Test uploading a new media file.

    Steps:
        1. Override the upload directory to a temporary folder.
        2. Create a user and authenticate using their API key.
        3. Send a POST request to upload a media file.
        4. Verify the file is saved in the directory and the database.

    Assertions:
        - The response status is 200.
        - The media file is saved in the specified directory.
        - The media record is created in the database with the correct path.
    """
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(settings, "UPL_DIR", temp_dir)

    user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_postgresql_db_session.add(user)
    await test_postgresql_db_session.commit()

    file_content = b"test_image_data"
    file = UploadFile(
        filename="test_image.jpg",
        file=BytesIO(file_content),
    )

    response = await client.post(
        "/api/medias",
        files={"file": (file.filename, file.file)},
        headers={"api-key": user.api_key},
    )
    response_data = response.json()

    if file.filename is None:
        file.filename = "default_file.jpeg"

    saved_file_path = os.path.join(temp_dir, file.filename)

    media = await test_postgresql_db_session.get(Media, user.id)

    assert os.path.exists(saved_file_path)
    assert response.status_code == 200
    assert response_data["result"] is True
    assert "media_id" in response_data
    assert media is not None
    assert media.file_path == f"{settings.SAVE_PATH}{file.filename}"


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_del_tweet_with_media(client, test_postgresql_db_session):
    """
    Test deleting a tweet with media attachments.

    Steps:
        1. Create a user, a tweet, and associated media in the database.
        2. Send a DELETE request to remove the tweet.
        3. Verify the tweet, media, and files are deleted.

    Assertions:
        - The response status is 200.
        - The tweet and media are removed from the database.
        - The associated media file is deleted from the file system.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    media: Media = Media(user_id=1, file_path=f"{settings.SAVE_PATH}media.jpg")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    tweet_media: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    test_postgresql_db_session.add_all([user, media, tweet, tweet_media])
    await test_postgresql_db_session.commit()

    with patch("os.remove") as mock_remove:
        response = await client.delete(
            f"/api/tweets/{tweet.id}",
            headers={"api-key": user.api_key},
        )
        response_data = response.json()

        tweet_deleted = await test_postgresql_db_session.get(Tweets, tweet.id)
        media_deleted = await test_postgresql_db_session.get(Media, media.id)

        mock_remove.assert_called_once_with(f"{settings.UPL_DIR}media.jpg")
        assert response_data["result"] is True
        assert tweet_deleted is None
        assert media_deleted is None


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_del_tweet_without_media(client, test_postgresql_db_session):
    """
    Test deleting a tweet without media.

    Steps:
        1. Create a user and a tweet in the database.
        2. Send a DELETE request to remove the tweet.
        3. Verify the tweet is removed from the database.

    Assertions:
        - The response status is 200.
        - The tweet is no longer in the database.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    test_postgresql_db_session.add_all([user, tweet])
    await test_postgresql_db_session.commit()

    response = await client.delete(
        f"/api/tweets/{tweet.id}",
        headers={"api-key": user.api_key},
    )
    response_data = response.json()

    tweet_deleted = await test_postgresql_db_session.get(Tweets, tweet.id)

    assert response_data["result"] is True
    assert tweet_deleted is None


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_del_tweet_not_owned_by_user(client, test_postgresql_db_session):
    """
    Test deleting a tweet not owned by the current user.

    Steps:
        1. Create two users and a tweet owned by the second user.
        2. Attempt to delete the tweet using the first user's API key.
        3. Verify the response contains a "not found or unauthorized" error.

    Assertions:
        - The response status is 404.
        - The error message indicates the tweet is not found or not owned by the user.
    """
    user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    tweet: Tweets = Tweets(user_id=2, content="Test_message")
    test_postgresql_db_session.add_all([user_1, user_2, tweet])
    await test_postgresql_db_session.commit()

    response = await client.delete(
        f"/api/tweets/{tweet.id}",
        headers={"api-key": user_1.api_key},
    )
    response_data = response.json()

    assert response.status_code == 404
    assert response_data["error_message"] == "Tweet not found or not owned by the user"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_put_like_success(client, test_postgresql_db_session):
    """
    Test adding a like to a tweet.

    Steps:
        1. Create a user and a tweet in the database.
        2. Send a POST request to like the tweet.
        3. Verify the like is saved in the database.

    Assertions:
        - The response status is 200.
        - The like is correctly added to the database.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    test_postgresql_db_session.add_all([user, tweet])
    await test_postgresql_db_session.commit()

    response = await client.post(
        f"/api/tweets/{tweet.id}/likes",
        headers={"api-key": user.api_key},
    )
    response_data = response.json()

    like = await test_postgresql_db_session.execute(
        select(Like).where(and_(Like.user_id == user.id, Like.tweet_id == tweet.id))
    )

    assert response.status_code == 200
    assert response_data["result"] is True
    assert like is not None


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_put_like_duplicate(client, test_postgresql_db_session):
    """
    Test adding a duplicate like to a tweet.

    Steps:
        1. Create a user, a tweet, and an existing like in the database.
        2. Attempt to like the tweet again.
        3. Verify the response contains a conflict error.

    Assertions:
        - The response status is 409.
        - The error message indicates a duplicate like is not allowed.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    like: Like = Like(user_id=1, tweet_id=1)
    test_postgresql_db_session.add_all([user, tweet, like])
    await test_postgresql_db_session.commit()

    response = await client.post(
        f"/api/tweets/{tweet.id}/likes",
        headers={"api-key": user.api_key},
    )
    response_data = response.json()

    assert response.status_code == 409
    assert response_data["error_message"] == "You can't put more than 1 like"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_delete_like_success(client, test_postgresql_db_session):
    """
    Test removing a like from a tweet.

    Steps:
        1. Create a user, a tweet, and a like in the database.
        2. Send a DELETE request to remove the like.
        3. Verify the like is removed from the database.

    Assertions:
        - The response status is 200.
        - The like is no longer in the database.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    like: Like = Like(user_id=1, tweet_id=1)
    test_postgresql_db_session.add_all([user, tweet, like])
    await test_postgresql_db_session.commit()

    response = await client.delete(
        f"/api/tweets/{tweet.id}/likes",
        headers={"api-key": user.api_key},
    )
    response_data = response.json()

    result = await test_postgresql_db_session.execute(
        select(Like).where(and_(Like.tweet_id == tweet.id))
    )
    likes = result.scalar_one_or_none()

    assert response.status_code == 200
    assert response_data["result"] is True
    assert likes is None


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_delete_like_not_found(client, test_postgresql_db_session):
    """
    Test removing a like that does not exist.

    Steps:
        1. Create a user and authenticate using their API key.
        2. Send a DELETE request to remove a non-existent like.
        3. Verify the response contains a "not found" error.

    Assertions:
        - The response status is 404.
        - The error message indicates the like is not found.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_postgresql_db_session.add(user)
    await test_postgresql_db_session.commit()

    response = await client.delete(
        "/api/tweets/1/likes",
        headers={"api-key": user.api_key},
    )
    response_data = response.json()

    assert response.status_code == 404
    assert response_data["error_message"] == "Tweet not found"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_delete_like_not_liked(client, test_postgresql_db_session):
    """
    Test removing a like from a tweet the user has not liked.

    Steps:
        1. Create a user and a tweet in the database.
        2. Attempt to remove a like from the tweet.
        3. Verify the response contains a "not liked" error.

    Assertions:
        - The response status is 404.
        - The error message indicates the user has not liked the tweet.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    test_postgresql_db_session.add_all([user, tweet])
    await test_postgresql_db_session.commit()

    response = await client.delete(
        f"/api/tweets/{tweet.id}/likes",
        headers={"api-key": user.api_key},
    )
    response_data = response.json()

    assert response.status_code == 404
    assert response_data["error_message"] == "You haven't liked the article yet"
    assert response_data["result"] is False


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_get_list_tweets_success(client, test_postgresql_db_session):
    """
    Test retrieving a list of tweets.

    Steps:
        1. Create a user, a tweet, and associated data (media, likes) in the database.
        2. Send a GET request to fetch the list of tweets.
        3. Verify the response contains the tweet with the correct details.

    Assertions:
        - The response status is 200.
        - The response contains the expected tweet and its relationships.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    follower: Users = Users(name="Follower", api_key="FollowerApiKey")
    tweet = Tweets(user_id=2, content="Test_message")
    like: Like = Like(user_id=1, tweet_id=1)
    media: Media = Media(user_id=2, file_path="/path/to/media.jpg")
    tweet_media: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    follower_relationship: Follower = Follower(follower_id=1, followee_id=2)
    test_postgresql_db_session.add_all(
        [user, follower, tweet, like, tweet_media, media, follower_relationship]
    )
    await test_postgresql_db_session.commit()

    response = await client.get(
        "/api/tweets",
        headers={"api-key": user.api_key},
    )
    response_data = response.json()
    tweet_data = response_data["tweets"][0]

    assert response.status_code == 200
    assert response_data["result"] is True
    assert len(response_data["tweets"]) == 1
    assert tweet_data["id"] == tweet.id
    assert tweet_data["content"] == tweet.content
    assert tweet_data["attachments"] == [media.file_path]
    assert tweet_data["author"]["id"] == follower.id
    assert tweet_data["author"]["name"] == follower.name
    assert len(tweet_data["likes"]) == 1
    assert tweet_data["likes"][0]["user_id"] == user.id


@pytest.mark.asyncio
@pytest.mark.tweet_routes
async def test_get_list_tweets_no_subscriptions(client, test_postgresql_db_session):
    """
    Test retrieving tweets when the user has no subscriptions.

    Steps:
        1. Create a user and a tweet in the database.
        2. Send a GET request to fetch tweets.
        3. Verify the response contains only the user's tweet.

    Assertions:
        - The response status is 200.
        - The response contains the user's tweet and related details.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet = Tweets(user_id=1, content="Test_message")
    like: Like = Like(user_id=1, tweet_id=1)
    media: Media = Media(user_id=1, file_path="/path/to/media.jpg")
    tweet_media: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    test_postgresql_db_session.add_all([user, tweet, like, tweet_media, media])
    await test_postgresql_db_session.commit()

    response = await client.get(
        "/api/tweets",
        headers={"api-key": user.api_key},
    )
    response_data = response.json()
    tweet_data = response_data["tweets"][0]

    assert response.status_code == 200
    assert response_data["result"] is True
    assert len(response_data["tweets"]) == 1
    assert tweet_data["id"] == tweet.id
    assert tweet_data["content"] == tweet.content
    assert tweet_data["attachments"] == [media.file_path]
    assert tweet_data["author"]["id"] == user.id
    assert tweet_data["author"]["name"] == user.name
    assert len(tweet_data["likes"]) == 1
    assert tweet_data["likes"][0]["user_id"] == user.id
