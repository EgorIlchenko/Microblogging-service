import os
import shutil
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...config.config import logger, settings
from ...database.models.models import Like, Media, TweetMedia, Tweets, Users
from ..user.repositoryes import FollowerRepository
from .repositoryes import (
    LikeRepository,
    MediaRepository,
    TweetMediaRepository,
    TweetRepository,
)
from .schemas import TweetCreate


class TweetServices:
    """
    Service layer for managing tweets, media files, likes, and user interactions.

    This class provides methods to handle business logic for tweets and their associated data.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the TweetServices instance with the required repositories.

        Args:
            session (AsyncSession): The database session for interacting with the database.
        """
        self.tweet_repo = TweetRepository(session)
        self.media_repo = MediaRepository(session)
        self.tm_repo = TweetMediaRepository(session)
        self.like_repo = LikeRepository(session)
        self.follow_repo = FollowerRepository(session)

    async def add_new_tweet(self, user: Users, tweet: TweetCreate):
        """
        Create a new tweet with optional media attachments.

        Args:
            user (Users): The currently authenticated user creating the tweet.
            tweet (TweetCreate): The data for the new tweet.

        Returns:
            dict: A dictionary containing the result status and the new tweet ID.

        Raises:
            HTTPException: If media files are inaccessible or an error occurs during creation.
        """
        logger.info("Создание нового твита для пользователя: %s", user.id)
        media_files: List = []

        if tweet.tweet_media_ids:
            logger.debug("Проверка доступности медиа-файлов: %s", tweet.tweet_media_ids)
            media_files = await self.media_repo.filter(
                custom_filters=[
                    Media.id.in_(tweet.tweet_media_ids),
                    Media.user_id == user.id,
                ]
            )

            if len(media_files) != len(tweet.tweet_media_ids):
                logger.warning(
                    "Некоторые медиа-файлы не найдены или недоступны: %s",
                    tweet.tweet_media_ids,
                )
                raise HTTPException(
                    status_code=400, detail="Some media files not found or inaccessible"
                )

        new_tweet: Tweets = Tweets(content=tweet.tweet_data, user_id=user.id)

        await self.tweet_repo.add(new_tweet)
        logger.info("Новый твит создан с ID: %s", new_tweet.id)

        if media_files:
            logger.debug("Привязка медиа-файлов к твиту ID: %s", new_tweet.id)
            tweet_media_entries: List[TweetMedia] = [
                TweetMedia(tweet_id=new_tweet.id, media_id=media.id)
                for media in media_files
            ]
            await self.tm_repo.add_all(tweet_media_entries)

        return {"result": True, "tweet_id": new_tweet.id}

    async def add_media_files(
        self, user: Users, file: UploadFile, upload_dir: Optional[str] = None
    ):
        """
        Upload a media file and associate it with the authenticated user.

        Args:
            user (Users): The currently authenticated user uploading the media file.
            file (UploadFile): The media file to upload.
            upload_dir (str, optional): The directory for storing the uploaded file.

        Returns:
            dict: A dictionary containing the result status and the new media ID.

        Raises:
            HTTPException: If an error occurs during the file upload or database operation.
        """
        logger.info("Добавление медиа-файла для пользователя: %s", user.id)
        if upload_dir is None:
            upload_dir = settings.UPL_DIR
        logger.debug("Используемая директория для загрузки: %s", upload_dir)

        if file.filename is None:
            file.filename = "default_file.jpeg"

        file_path: str = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info("Медиа-файл загружен: %s", file_path)

        path_to_image: str = f"{settings.SAVE_PATH}{file.filename}"

        new_media: Media = Media(file_path=path_to_image, user_id=user.id)

        await self.media_repo.add(new_media)
        logger.info("Медиа-файл добавлен в базу данных с ID: %s", new_media.id)

        return {"result": True, "media_id": new_media.id}

    async def del_tweet(self, user: Users, id: int):
        """
        Delete a tweet and its associated media files.

        Args:
            user (Users): The currently authenticated user attempting to delete the tweet.
            id (int): The ID of the tweet to delete.

        Returns:
            dict: A dictionary indicating the success of the operation.

        Raises:
            HTTPException: If the tweet is not found or not owned by the user.
            FileNotFoundError: If a media file linked to the tweet cannot be found.
        """
        logger.info("Удаление твита ID: %s для пользователя: %s", id, user.id)
        tweets = await self.tweet_repo.filter(
            id=id, user_id=user.id, options=[selectinload(Tweets.media)]
        )

        if not tweets:
            logger.warning("Твит ID %s не найден или недоступен.", id)
            raise HTTPException(
                status_code=404, detail="Tweet not found or not owned by the user"
            )

        tweet = tweets[0]
        media_files = tweet.media

        await self.tweet_repo.delete(tweet)
        logger.info("Твит ID %s удалён.", id)

        for tweet_media in media_files:
            media = tweet_media.media
            remaining_link = await self.tm_repo.filter(media_id=media.id)
            if remaining_link is None:
                file_name = os.path.basename(media.file_path)
                file_path = os.path.join(settings.UPL_DIR, file_name)

                if file_path is None:
                    logger.error("Файл медиа отсутствует в системе.")
                    raise FileNotFoundError("File not found")

                os.remove(file_path)
                logger.info("Файл медиа удалён: %s", file_path)

                await self.media_repo.delete(media)
                logger.debug("Медиа удалено из базы данных с ID: %s", media.id)

        return {"result": True}

    async def add_like(self, user: Users, id: int):
        """
        Add a like to a tweet.

        Args:
            user (Users): The currently authenticated user liking the tweet.
            id (int): The ID of the tweet to like.

        Returns:
            dict: A dictionary indicating the success of the operation.

        Raises:
            HTTPException: If the tweet is not found or the user has already liked the tweet.
        """
        logger.info("Добавление лайка к твиту ID: %s от пользователя: %s", id, user.id)
        tweet = await self.tweet_repo.get_by_id(id)

        if not tweet:
            logger.warning("Твит ID %s не найден.", id)
            raise HTTPException(status_code=404, detail="Tweet not found")

        like = await self.like_repo.filter(tweet_id=id, user_id=user.id)

        if like:
            logger.warning("Пользователь уже поставил лайк на твит ID: %s", id)
            raise HTTPException(
                status_code=409, detail="You can't put more than 1 like"
            )

        new_like: Like = Like(
            tweet_id=id,
            user_id=user.id,
        )

        await self.like_repo.add(new_like)
        logger.info("Лайк добавлен к твиту ID: %s от пользователя: %s", id, user.id)

        return {"result": True}

    async def del_like(self, user: Users, id: int):
        """
        Remove a like from a tweet.

        Args:
            user (Users): The currently authenticated user unliking the tweet.
            id (int): The ID of the tweet to remove the like from.

        Returns:
            dict: A dictionary indicating the success of the operation.

        Raises:
            HTTPException: If the tweet or the like is not found.
        """
        logger.info("Удаление лайка с твита ID: %s от пользователя: %s", id, user.id)
        tweet = await self.tweet_repo.get_by_id(id)

        if not tweet:
            logger.warning("Твит ID %s не найден.", id)
            raise HTTPException(status_code=404, detail="Tweet not found")

        like = await self.like_repo.filter(tweet_id=id, user_id=user.id)

        if not like:
            logger.warning(
                "Лайк не найден для твита ID: %s и пользователя: %s", id, user.id
            )
            raise HTTPException(
                status_code=404, detail="You haven't liked the article yet"
            )

        await self.like_repo.delete(like)
        logger.info("Лайк удалён с твита ID: %s от пользователя: %s", id, user.id)

        return {"result": True}

    async def get_tweets(
        self, user: Users, limit: Optional[int] = None, offset: Optional[int] = None
    ):
        """
        Retrieve a paginated list of tweets for the authenticated user.

        Args:
            user (Users): The currently authenticated user retrieving the tweets.
            limit (Optional[int]): Number of tweets to return.
            offset (Optional[int]): Number of tweets to skip.

        Returns:
            dict: A dictionary containing the result status and a paginated list of tweets.

        Raises:
            HTTPException: If an error occurs while retrieving tweets.
        """
        logger.info("Получение твитов для пользователя: %s", user.id)
        tweets_list: List = []

        if (offset is not None) and (limit is not None):
            offset = (offset - 1) * limit

        subscribers = await self.follow_repo.filter(follower_id=user.id)

        if not subscribers:
            following_list: List = [user.id]
            logger.debug("Пользователь %s не подписан ни на кого.", user.id)
        else:
            following_list = [subscriber.followee_id for subscriber in subscribers]
            following_list.append(user.id)
        logger.debug("Список подписок пользователя %s: %s", user.id, following_list)

        tweets = await self.tweet_repo.filter(
            limit=limit,
            offset=offset,
            custom_filters=[Tweets.user_id.in_(following_list)],
            order_by=[Tweets.likes_count.desc(), Tweets.created_at.desc()],  # type: ignore
            options=[
                selectinload(Tweets.author),
                selectinload(Tweets.media).selectinload(TweetMedia.media),
                selectinload(Tweets.likes).selectinload(Like.user),
            ],
        )

        for tweet in tweets:
            attachments = [tweet_media.media.file_path for tweet_media in tweet.media]
            likes = [
                {"user_id": like.user_id, "name": like.user.name}
                for like in tweet.likes
            ]
            tweet_dict = {
                "id": tweet.id,
                "content": tweet.content,
                "attachments": attachments,
                "author": {
                    "id": tweet.author.id,
                    "name": tweet.author.name,
                },
                "likes": likes,
            }
            tweets_list.append(tweet_dict)

        logger.info("Список твитов успешно получен для пользователя: %s", user.id)

        return {"result": True, "tweets": tweets_list}
