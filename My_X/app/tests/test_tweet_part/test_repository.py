from typing import List

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...api.tweet.repositoryes import (
    LikeRepository,
    MediaRepository,
    TweetMediaRepository,
    TweetRepository,
)
from ...database.models.models import Like, Media, TweetMedia, Tweets, Users


@pytest.mark.asyncio
@pytest.mark.TweetRepository
async def test_tweet_repository_get_by_id(test_db_session):
    """
    Test `TweetRepository.get_by_id`.

    Verifies that a tweet can be retrieved by its ID after being added to the database.

    Steps:
        1. Add a tweet to the repository.
        2. Retrieve the tweet using `get_by_id`.
        3. Assert that the retrieved tweet matches the expected content.

    Assertions:
        - The tweet is not `None`.
        - The tweet's content matches the added value.
    """
    repo: TweetRepository = TweetRepository(session=test_db_session)

    new_tweet = Tweets(user_id=1, content="Test_message")
    await repo.add(new_tweet)

    result = await repo.get_by_id(tweet_id=new_tweet.id)

    assert result is not None
    assert result.content == "Test_message"


@pytest.mark.asyncio
@pytest.mark.TweetRepository
async def test_tweet_repository_add(test_db_session):
    """
    Test `TweetRepository.add`.

    Ensures that a tweet is successfully inserted into the database.

    Steps:
        1. Add a tweet to the repository.
        2. Query the database for the tweet by its content.
        3. Assert that the tweet exists and matches the expected attributes.

    Assertions:
        - The tweet is present in the database.
        - The content and user ID match the added values.
    """
    repo: TweetRepository = TweetRepository(session=test_db_session)

    new_tweet: Tweets = Tweets(user_id=1, content="Test_message")
    await repo.add(new_tweet)

    result = await test_db_session.execute(
        select(Tweets).where(Tweets.content == "Test_message")
    )
    tweet = result.scalars().first()

    assert tweet is not None
    assert tweet.content == "Test_message"
    assert tweet.user_id == 1


@pytest.mark.asyncio
@pytest.mark.TweetRepository
async def test_tweet_repository_delete(test_db_session):
    """
    Test `TweetRepository.delete`.

    Confirms that a tweet is removed from the database after deletion.

    Steps:
        1. Add a tweet to the repository.
        2. Delete the tweet using `delete`.
        3. Query the database to ensure the tweet no longer exists.

    Assertions:
        - The tweet is `None` after deletion.
    """
    repo: TweetRepository = TweetRepository(session=test_db_session)

    new_tweet: Tweets = Tweets(user_id=1, content="Tweet to delete")
    await repo.add(new_tweet)

    await repo.delete(new_tweet)

    result = await test_db_session.execute(
        select(Tweets).where(Tweets.content == "Test_message")
    )
    tweet = result.scalars().first()

    assert tweet is None


@pytest.mark.asyncio
@pytest.mark.TweetRepository
async def test_tweet_repository_filter_by_field(test_db_session):
    """
    Test `TweetRepository.filter`.

    Validates that the `filter` method returns tweets matching a specific field.

    Steps:
        1. Add multiple tweets with different `user_id` values.
        2. Filter tweets by a specific `user_id`.
        3. Assert that only the tweets matching the `user_id` are returned.

    Assertions:
        - The returned tweets match the specified `user_id`.
        - The number of tweets returned is correct.
    """
    repo: TweetRepository = TweetRepository(session=test_db_session)

    new_tweet_1: Tweets = Tweets(user_id=1, content="Test_message_1")
    new_tweet_2: Tweets = Tweets(user_id=2, content="Test_message_2")
    await repo.add(new_tweet_1)
    await repo.add(new_tweet_2)

    result = await repo.filter(user_id=1)

    assert len(result) == 1
    assert result[0].content == "Test_message_1"


@pytest.mark.asyncio
@pytest.mark.TweetRepository
async def test_tweet_repository_filter_with_options(test_db_session):
    """
    Test `TweetRepository.filter` with options.

    Ensures that the `filter` method supports query options, such as eager loading relationships.

    Steps:
        1. Add a tweet and its associated author.
        2. Use `filter` with the `selectinload` option for the `author` relationship.
        3. Assert that the tweet and its author are correctly retrieved.

    Assertions:
        - The tweet includes the author's details.
        - The tweet content matches the expected value.
    """
    repo: TweetRepository = TweetRepository(session=test_db_session)

    new_tweet: Tweets = Tweets(user_id=1, content="Test_message")
    await repo.add(new_tweet)

    new_user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(new_user)
    await test_db_session.commit()

    result = await repo.filter(options=[selectinload(Tweets.author)])

    assert len(result) == 1
    assert result[0].author.name == "Test_user"
    assert result[0].content == "Test_message"


@pytest.mark.asyncio
@pytest.mark.MediaRepository
async def test_media_repository_add(test_db_session):
    """
    Test `MediaRepository.add`.

    Verifies that media is correctly added to the database.

    Steps:
        1. Add a media file to the repository.
        2. Query the database for the media file by its path.
        3. Assert that the media file exists and matches the expected attributes.

    Assertions:
        - The media file is present in the database.
        - The file path and user ID match the added values.
    """
    repo: MediaRepository = MediaRepository(session=test_db_session)

    new_media: Media = Media(file_path="http://example.com/file.jpg", user_id=1)
    await repo.add(new_media)

    result = await test_db_session.execute(
        select(Media).where(Media.file_path == "http://example.com/file.jpg")
    )
    media = result.scalars().first()

    assert media is not None
    assert media.file_path == "http://example.com/file.jpg"
    assert media.user_id == 1


@pytest.mark.asyncio
@pytest.mark.MediaRepository
async def test_media_repository_delete(test_db_session):
    """
    Test `MediaRepository.delete`.

    Confirms that media is removed from the database after deletion.

    Steps:
        1. Add a media file to the repository.
        2. Delete the media file using `delete`.
        3. Query the database to ensure the media file no longer exists.

    Assertions:
        - The media file is `None` after deletion.
    """
    repo: MediaRepository = MediaRepository(session=test_db_session)

    new_media: Media = Media(file_path="http://example.com/file.jpg", user_id=1)
    await repo.add(new_media)

    await repo.delete(new_media)

    result = await test_db_session.execute(
        select(Media).where(Media.file_path == "http://example.com/file.jpg")
    )
    deleted_media = result.scalars().first()

    assert deleted_media is None


@pytest.mark.asyncio
@pytest.mark.MediaRepository
async def test_media_repository_filter_by_field(test_db_session):
    """
    Test `MediaRepository.filter`.

    Validates that the `filter` method returns media files matching a specific field.

    Steps:
        1. Add multiple media files with different `user_id` values.
        2. Filter media files by a specific `user_id`.
        3. Assert that only the media files matching the `user_id` are returned.

    Assertions:
        - The returned media files match the specified `user_id`.
        - The number of media files returned is correct.
    """
    repo: MediaRepository = MediaRepository(session=test_db_session)

    new_media_1: Media = Media(file_path="http://example.com/file_1.jpg", user_id=1)
    new_media_2: Media = Media(file_path="http://example.com/file_2.jpg", user_id=2)
    await repo.add(new_media_1)
    await repo.add(new_media_2)

    result = await repo.filter(user_id=1)

    assert len(result) == 1
    assert result[0].file_path == "http://example.com/file_1.jpg"


@pytest.mark.asyncio
@pytest.mark.MediaRepository
async def test_media_repository_filter_with_options(test_db_session):
    """
    Test `MediaRepository.filter` with options.

    Ensures that the `filter` method supports query options, such as eager loading relationships.

    Steps:
        1. Add a media file and its associated user.
        2. Use `filter` with the `selectinload` option for the `user` relationship.
        3. Assert that the media file and its user are correctly retrieved.

    Assertions:
        - The media file includes the user's details.
        - The file path matches the expected value.
    """
    repo: MediaRepository = MediaRepository(session=test_db_session)

    new_media: Media = Media(file_path="http://example.com/file.jpg", user_id=1)
    await repo.add(new_media)

    new_user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(new_user)
    await test_db_session.commit()

    result = await repo.filter(options=[selectinload(Media.user)])

    assert len(result) == 1
    assert result[0].user.name == "Test_user"
    assert result[0].file_path == "http://example.com/file.jpg"


@pytest.mark.asyncio
@pytest.mark.MediaRepository
async def test_media_repository_filter_with_custom_filter(test_db_session):
    """
    Test `MediaRepository.filter` with a custom filter.

    Ensures that the method correctly applies custom SQLAlchemy filters to queries.

    Steps:
        1. Add two media records with distinct file paths.
        2. Use a custom filter to query for media matching a specific pattern.
        3. Assert that only the matching media is returned.

    Assertions:
        - The number of results matches the expected count.
        - The returned media's file path matches the custom filter condition.
    """
    repo = MediaRepository(session=test_db_session)

    new_media_1: Media = Media(file_path="http://example.com/file_1.jpg", user_id=1)
    new_media_2: Media = Media(file_path="http://example.com/file_2.jpg", user_id=2)
    await repo.add(new_media_1)
    await repo.add(new_media_2)

    custom_filter = Media.file_path.like("%file_1%")
    result = await repo.filter(custom_filters=[custom_filter])

    assert len(result) == 1
    assert result[0].file_path == "http://example.com/file_1.jpg"


@pytest.mark.asyncio
@pytest.mark.TweetMedia
async def test_tweet_media_repository_add_all(test_db_session):
    """
    Test `TweetMediaRepository.add_all`.

    Verifies that multiple `TweetMedia` relationships are added successfully.

    Steps:
        1. Create a list of `TweetMedia` relationships.
        2. Add them to the repository using `add_all`.
        3. Query the database to verify the relationships.

    Assertions:
        - The number of added relationships matches the expected count.
        - The relationships have the correct `tweet_id` and `media_id`.
    """
    repo: TweetMediaRepository = TweetMediaRepository(session=test_db_session)

    tweet_media_list: List[TweetMedia] = [
        TweetMedia(tweet_id=1, media_id=1),
        TweetMedia(tweet_id=1, media_id=2),
    ]

    await repo.add_all(tweet_media_list)

    result = await test_db_session.execute(
        select(TweetMedia).where(TweetMedia.tweet_id == 1)
    )
    tweet_media = result.scalars().all()

    assert len(tweet_media) == 2
    assert tweet_media[0].media_id == 1
    assert tweet_media[1].media_id == 2


@pytest.mark.asyncio
@pytest.mark.TweetMedia
async def test_tweet_media_repository_delete(test_db_session):
    """
    Test `TweetMediaRepository.delete`.

    Confirms that a `TweetMedia` relationship is removed from the database after deletion.

    Steps:
        1. Add a `TweetMedia` relationship to the repository.
        2. Delete the relationship using `delete`.
        3. Query the database to ensure the relationship no longer exists.

    Assertions:
        - The `TweetMedia` record is `None` after deletion.
    """
    repo: TweetMediaRepository = TweetMediaRepository(session=test_db_session)

    new_tweet_media: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    test_db_session.add(new_tweet_media)
    await test_db_session.commit()

    await repo.delete(new_tweet_media)

    result = await test_db_session.execute(
        select(TweetMedia).where(TweetMedia.tweet_id == 1)
    )
    deleted_tweet_media = result.scalars().first()

    assert deleted_tweet_media is None


@pytest.mark.asyncio
@pytest.mark.TweetMedia
async def test_tweet_media_repository_filter_by_field(test_db_session):
    """
    Test `TweetMediaRepository.filter` by field.

    Ensures that the `filter` method returns `TweetMedia` relationships matching a specific field.

    Steps:
        1. Add multiple `TweetMedia` relationships with different attributes.
        2. Filter by a specific `media_id`.
        3. Assert that only the matching relationships are returned.

    Assertions:
        - The result is not `None`.
        - The `media_id` of the returned relationship matches the filter condition.
    """
    repo: TweetMediaRepository = TweetMediaRepository(session=test_db_session)

    new_tweet_media_1: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    new_tweet_media_2: TweetMedia = TweetMedia(tweet_id=1, media_id=2)

    test_db_session.add(new_tweet_media_1)
    test_db_session.add(new_tweet_media_2)
    await test_db_session.commit()

    result = await repo.filter(media_id=2)

    assert result is not None
    assert result.media_id == 2


@pytest.mark.asyncio
@pytest.mark.TweetMedia
async def test_tweet_media_repository_filter_with_options(test_db_session):
    """
    Test `TweetMediaRepository.filter` with options.

    Verifies that the method supports query options like eager loading.

    Steps:
        1. Add a `TweetMedia` relationship with an associated media file.
        2. Use `filter` with the `selectinload` option for the `media` relationship.
        3. Assert that the relationship and media details are correctly loaded.

    Assertions:
        - The result is not `None`.
        - The media details are loaded and match the expected values.
    """
    repo: TweetMediaRepository = TweetMediaRepository(session=test_db_session)

    new_tweet_media: TweetMedia = TweetMedia(tweet_id=1, media_id=1)
    new_media: Media = Media(file_path="http://example.com/file.jpg", user_id=1)
    test_db_session.add(new_media)
    test_db_session.add(new_tweet_media)
    await test_db_session.commit()

    result = await repo.filter(options=[selectinload(TweetMedia.media)])

    assert result is not None
    assert result.media.file_path == "http://example.com/file.jpg"
    assert result.media_id == 1


@pytest.mark.asyncio
@pytest.mark.LikeRepository
async def test_like_repository_add(test_db_session):
    """
    Test `LikeRepository.add`.

    Ensures that a like is successfully added to the database.

    Steps:
        1. Create a `Like` object and add it to the repository.
        2. Query the database for the like.
        3. Assert that the like exists and matches the expected attributes.

    Assertions:
        - The like is present in the database.
        - The `user_id` and `tweet_id` match the expected values.
    """
    repo: LikeRepository = LikeRepository(session=test_db_session)

    new_like: Like = Like(user_id=1, tweet_id=1)
    await repo.add(new_like)

    result = await test_db_session.execute(select(Like).where(Like.tweet_id == 1))
    like = result.scalars().first()

    assert like is not None
    assert like.tweet_id == 1
    assert like.user_id == 1


@pytest.mark.asyncio
@pytest.mark.LikeRepository
async def test_like_repository_delete(test_db_session):
    """
    Test `LikeRepository.delete`.

    Verifies that a like is removed from the database after deletion.

    Steps:
        1. Add a like to the repository.
        2. Delete the like using `delete`.
        3. Query the database to ensure the like no longer exists.

    Assertions:
        - The like is `None` after deletion.
    """
    repo: LikeRepository = LikeRepository(session=test_db_session)

    new_like: Like = Like(user_id=1, tweet_id=1)
    await repo.add(new_like)

    await repo.delete(new_like)

    result = await test_db_session.execute(select(Like).where(Like.tweet_id == 1))
    deleted_like = result.scalars().first()

    assert deleted_like is None


@pytest.mark.asyncio
@pytest.mark.LikeRepository
async def test_like_repository_filter_by_field(test_db_session):
    """
    Test `LikeRepository.filter` by field.

    Confirms that the `filter` method returns likes matching specific criteria.

    Steps:
        1. Add multiple likes with different attributes.
        2. Filter by a specific `tweet_id`.
        3. Assert that only the likes matching the filter are returned.

    Assertions:
        - The result is not `None`.
        - The `tweet_id` of the returned like matches the filter condition.
    """
    repo: LikeRepository = LikeRepository(session=test_db_session)

    new_like_1: Like = Like(user_id=1, tweet_id=1)
    new_like_2: Like = Like(user_id=1, tweet_id=2)
    await repo.add(new_like_1)
    await repo.add(new_like_2)

    result = await repo.filter(tweet_id=1)

    assert result is not None
    assert result.tweet_id == 1


@pytest.mark.asyncio
@pytest.mark.LikeRepository
async def test_like_repository_filter_with_options(test_db_session):
    """
    Test `LikeRepository.filter` with options.

    Ensures that the `filter` method supports query options like eager loading.

    Steps:
        1. Add a like with an associated user.
        2. Use `filter` with the `selectinload` option for the `user` relationship.
        3. Assert that the like and user details are correctly loaded.

    Assertions:
        - The result is not `None`.
        - The user's details are loaded and match the expected values.
    """
    repo: LikeRepository = LikeRepository(session=test_db_session)

    new_like: Like = Like(user_id=1, tweet_id=1)
    await repo.add(new_like)

    new_user: Users = Users(name="Test_user", api_key="Test_api_key")
    test_db_session.add(new_user)
    await test_db_session.commit()

    result = await repo.filter(options=[selectinload(Like.user)])

    assert result is not None
    assert result.user.name == "Test_user"
    assert result.tweet_id == 1
