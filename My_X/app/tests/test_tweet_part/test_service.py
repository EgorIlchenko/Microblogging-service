import tempfile
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, select

from ...api.tweet.schemas import TweetCreate
from ...api.tweet.service import TweetServices
from ...config.config import settings
from ...database.models.models import Follower, Like, Media, TweetMedia, Tweets, Users


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_add_new_tweet_without_media(test_db_session):
    """
    Test adding a new tweet without media.

    Steps:
        1. Create a user in the database.
        2. Call `add_new_tweet` with tweet data and no media IDs.
        3. Verify the tweet is saved in the database with correct content and user ID.

    Assertions:
        - The result indicates success.
        - The tweet is present in the database with the expected attributes.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(user)
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    tweet_data: TweetCreate = TweetCreate(tweet_data="Test_message", tweet_media_ids=[])
    result = await service.add_new_tweet(user=user, tweet=tweet_data)
    tweet = await test_db_session.get(Tweets, result["tweet_id"])

    assert result["result"] is True
    assert "tweet_id" in result
    assert tweet.content == "Test_message"
    assert tweet.user_id == user.id


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_add_new_tweet_with_media_ids(test_db_session):
    """
    Test adding a new tweet with media.

    Steps:
        1. Create a user and media files in the database.
        2. Call `add_new_tweet` with tweet data and valid media IDs.
        3. Verify the tweet and its media relationships are saved in the database.

    Assertions:
        - The result indicates success.
        - The tweet and its media attachments are correctly saved in the database.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    media_1: Media = Media(user_id=1, file_path="/media1.jpg")
    media_2: Media = Media(user_id=1, file_path="/media2.jpg")
    test_db_session.add_all([user, media_1, media_2])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    tweet_data: TweetCreate = TweetCreate(
        tweet_data="Test_message", tweet_media_ids=[1, 2]
    )
    result = await service.add_new_tweet(user=user, tweet=tweet_data)
    tweet = await test_db_session.get(Tweets, result["tweet_id"])
    tweet_media = await test_db_session.execute(
        select(TweetMedia).where(and_(TweetMedia.tweet_id == tweet.id))
    )

    assert result["result"] is True
    assert "tweet_id" in result
    assert tweet.content == "Test_message"
    assert tweet.user_id == user.id
    assert len(tweet_media.fetchall()) == 2


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_add_new_tweet_with_invalid_media_ids(test_db_session):
    """
    Test adding a new tweet with invalid media IDs.

    Steps:
        1. Create a user in the database.
        2. Call `add_new_tweet` with tweet data referencing non-existent media IDs.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 400.
        - The error message indicates inaccessible media files.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(user)
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    tweet_data: TweetCreate = TweetCreate(
        tweet_data="Test_message", tweet_media_ids=[999]
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.add_new_tweet(user=user, tweet=tweet_data)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Some media files not found or inaccessible"


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_add_media_files_success(test_db_session):
    """
    Test adding a new media file.

    Steps:
        1. Create a user in the database.
        2. Call `add_media_files` with a mock file and temporary directory.
        3. Verify the file is saved in the directory and the database.

    Assertions:
        - The result indicates success.
        - The media file is present in the database with the correct file path and user ID.
    """
    user = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(user)
    await test_db_session.commit()

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_content = b"test_image_data"
        test_file = UploadFile(
            filename="test_image.jpg",
            file=BytesIO(test_file_content),
        )

        upload_path: str = temp_dir

        service: TweetServices = TweetServices(session=test_db_session)
        response = await service.add_media_files(
            user=user, file=test_file, upload_dir=upload_path
        )

    result = await test_db_session.execute(select(Media).where(Media.id == 1))
    media_in_db = result.scalar_one_or_none()

    assert response["result"] is True
    assert "media_id" in response
    assert media_in_db is not None
    assert media_in_db.file_path == f"{settings.SAVE_PATH}test_image.jpg"
    assert media_in_db.user_id == user.id


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_del_tweet_with_media(test_db_session):
    """
    Test deleting a tweet with associated media.

    Steps:
        1. Create a user, a tweet, and media in the database.
        2. Call `del_tweet` to delete the tweet.
        3. Verify the tweet, media, and file are removed.

    Assertions:
        - The result indicates success.
        - The tweet and media are deleted from the database.
        - The media file is removed from the file system.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    media: Media = Media(user_id=1, file_path=f"{settings.SAVE_PATH}media.jpg")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    tweet_media: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    test_db_session.add_all([user, media, tweet, tweet_media])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    with patch("os.remove") as mock_remove:
        result = await service.del_tweet(user=user, id=tweet.id)

        mock_remove.assert_called_once_with(f"{settings.UPL_DIR}media.jpg")
        assert result["result"] is True

    tweet_deleted = await test_db_session.get(Tweets, tweet.id)
    media_deleted = await test_db_session.get(Media, media.id)

    assert tweet_deleted is None
    assert media_deleted is None


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_del_tweet_without_media(test_db_session):
    """
    Test deleting a tweet without associated media.

    Steps:
        1. Create a user and a tweet in the database.
        2. Call `del_tweet` to delete the tweet.
        3. Verify the tweet is removed from the database.

    Assertions:
        - The result indicates success.
        - The tweet is deleted from the database.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    test_db_session.add_all([user, tweet])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    result = await service.del_tweet(user=user, id=tweet.id)
    tweet_deleted = await test_db_session.get(Tweets, tweet.id)

    assert result["result"] is True
    assert tweet_deleted is None


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_del_tweet_not_owned_by_user(test_db_session):
    """
    Test deleting a tweet not owned by the current user.

    Steps:
        1. Create two users and a tweet owned by the second user.
        2. Attempt to delete the tweet using the first user.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 404.
        - The error message indicates the tweet is not found or not owned by the user.
    """
    user_1: Users = Users(name="Test_user_1", api_key="Test_api_key_1")
    user_2: Users = Users(name="Test_user_2", api_key="Test_api_key_2")
    tweet: Tweets = Tweets(user_id=2, content="Test_message")
    test_db_session.add_all([user_1, user_2, tweet])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.del_tweet(user=user_1, id=tweet.id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Tweet not found or not owned by the user"


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_add_like_success(test_db_session):
    """
    Test adding a like to a tweet.

    Steps:
        1. Create a user and a tweet in the database.
        2. Call `add_like` to add a like to the tweet.
        3. Verify the like is saved in the database.

    Assertions:
        - The result indicates success.
        - The like is present in the database with the correct user and tweet IDs.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    test_db_session.add_all([user, tweet])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    result = await service.add_like(user=user, id=tweet.id)
    like = await test_db_session.execute(
        select(Like).where(and_(Like.user_id == user.id, Like.tweet_id == tweet.id))
    )

    assert result["result"] is True
    assert like.fetchone() is not None


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_add_like_duplicate(test_db_session):
    """
    Test adding a duplicate like to a tweet.

    Steps:
        1. Create a user, a tweet, and an existing like in the database.
        2. Attempt to add another like to the same tweet.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 409.
        - The error message indicates a duplicate like is not allowed.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    like: Like = Like(user_id=1, tweet_id=1)
    test_db_session.add_all([user, tweet, like])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.add_like(user=user, id=tweet.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "You can't put more than 1 like"


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_del_like_success(test_db_session):
    """
    Test removing a like from a tweet.

    Steps:
        1. Create a user, a tweet, and a like in the database.
        2. Call `del_like` to remove the like.
        3. Verify the like is removed from the database.

    Assertions:
        - The result indicates success.
        - The like is no longer in the database.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    like: Like = Like(user_id=1, tweet_id=1)
    test_db_session.add_all([user, tweet, like])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    result = await service.del_like(user=user, id=tweet.id)
    likes = await test_db_session.execute(
        select(Like).where(and_(Like.tweet_id == tweet.id))
    )

    assert result == {"result": True}
    assert likes.scalars().first() is None


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_del_like_tweet_not_found(test_db_session):
    """
    Test removing a like from a non-existent tweet.

    Steps:
        1. Create a user in the database.
        2. Attempt to remove a like from a non-existent tweet.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 404.
        - The error message indicates the tweet is not found.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(user)
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.del_like(user=user, id=1)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Tweet not found"


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_del_like_not_liked(test_db_session):
    """
    Test removing a like from a tweet not liked by the user.

    Steps:
        1. Create a user and a tweet in the database.
        2. Attempt to remove a like from the tweet.
        3. Verify an HTTPException is raised.

    Assertions:
        - The exception status code is 404.
        - The error message indicates the tweet was not liked by the user.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet: Tweets = Tweets(user_id=1, content="Test_message")
    test_db_session.add_all([user, tweet])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.del_like(user=user, id=tweet.id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "You haven't liked the article yet"


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_get_tweets_success(test_db_session):
    """
    Test retrieving a list of tweets with subscriptions.

    Steps:
        1. Create users, a tweet, and associated data (likes, media) in the database.
        2. Call `get_tweets` to retrieve tweets visible to the user.
        3. Verify the returned tweets include the correct details.

    Assertions:
        - The result indicates success.
        - The returned tweets match the expected data.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    follower: Users = Users(name="Follower", api_key="FollowerApiKey")
    tweet = Tweets(user_id=2, content="Test_message")
    like: Like = Like(user_id=1, tweet_id=1)
    media: Media = Media(user_id=2, file_path="/path/to/media.jpg")
    tweet_media: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    follower_relationship: Follower = Follower(follower_id=1, followee_id=2)
    test_db_session.add_all(
        [user, follower, tweet, like, tweet_media, media, follower_relationship]
    )
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    result = await service.get_tweets(user=user)
    tweet_data = result["tweets"][0]

    assert result["result"] is True
    assert len(result["tweets"]) == 1
    assert tweet_data["id"] == tweet.id
    assert tweet_data["content"] == tweet.content
    assert tweet_data["attachments"] == [media.file_path]
    assert tweet_data["author"]["id"] == follower.id
    assert tweet_data["author"]["name"] == follower.name
    assert len(tweet_data["likes"]) == 1
    assert tweet_data["likes"][0]["user_id"] == user.id


@pytest.mark.asyncio
@pytest.mark.TweetServices
async def test_get_tweets_no_subscriptions(test_db_session):
    """
    Test retrieving tweets when the user has no subscriptions.

    Steps:
        1. Create a user and their tweet in the database.
        2. Call `get_tweets` to retrieve the user's tweets.
        3. Verify the returned tweets are correct.

    Assertions:
        - The result indicates success.
        - The returned tweets include only the user's tweets.
    """
    user: Users = Users(name="Test_user", api_key="Test_api_key")
    tweet = Tweets(user_id=1, content="Test_message")
    like: Like = Like(user_id=1, tweet_id=1)
    media: Media = Media(user_id=1, file_path="/path/to/media.jpg")
    tweet_media: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    test_db_session.add_all([user, tweet, like, tweet_media, media])
    await test_db_session.commit()

    service: TweetServices = TweetServices(session=test_db_session)

    result = await service.get_tweets(user=user)
    tweet_data = result["tweets"][0]

    assert result["result"] is True
    assert len(result["tweets"]) == 1
    assert tweet_data["id"] == tweet.id
    assert tweet_data["content"] == tweet.content
    assert tweet_data["attachments"] == [media.file_path]
    assert tweet_data["author"]["id"] == user.id
    assert tweet_data["author"]["name"] == user.name
    assert len(tweet_data["likes"]) == 1
    assert tweet_data["likes"][0]["user_id"] == user.id
