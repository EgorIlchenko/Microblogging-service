from typing import Any, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.config import logger
from ...database.base_repository import (
    AbstractLikeRepository,
    AbstractMediaRepository,
    AbstractTweetMediaRepository,
    AbstractTweetRepository,
)
from ...database.models.models import Like, Media, TweetMedia, Tweets


class TweetRepository(AbstractTweetRepository):
    """
    Repository for managing `Tweets` entities in the database.

    Provides methods to add, delete, retrieve, and filter `Tweets` with specific
    parameters or conditions.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            session (AsyncSession): The database session used for executing queries.
        """
        self.session: AsyncSession = session

    async def get_by_id(self, tweet_id: int) -> Optional[Tweets]:
        """
        Retrieve a tweet by its unique ID.

        Args:
            tweet_id (int): The unique identifier of the tweet.

        Returns:
            Optional[Tweets]: The tweet if found, or None if it doesn't exist.
        """
        logger.info("Поиск твита по ID: %s", tweet_id)
        query = select(Tweets).where(Tweets.id == tweet_id)
        result = await self.session.execute(query)
        tweet: Optional[Tweets] = result.scalar_one_or_none()
        logger.debug("Результат поиска твита: %s", tweet)

        return tweet

    async def add(self, tweet: Tweets) -> None:
        """
        Add a new tweet to the database.

        Args:
            tweet (Tweets): The tweet object to add.
        """
        logger.info("Добавление нового твита: %s", tweet)
        self.session.add(tweet)
        await self.session.commit()
        await self.session.refresh(tweet)
        logger.debug("Твит добавлен и обновлен: %s", tweet)

    async def delete(self, tweet: Tweets) -> None:
        """
        Delete a tweet from the database.

        Args:
            tweet (Tweets): The tweet object to delete.
        """
        logger.info("Удаление твита: %s", tweet)
        await self.session.delete(tweet)
        await self.session.commit()
        logger.debug("Твит удалён")

    async def filter(self, **kwargs) -> Any:
        """
        Filter tweets based on given conditions.

        Args:
            **kwargs: Filtering parameters.

        Returns:
            Any: A list of tweets matching the filters.
        """
        logger.info("Фильтрация твитов с параметрами: %s", kwargs)

        options = kwargs.pop("options", [])
        custom_filters = kwargs.pop("custom_filters", [])
        order_by = kwargs.pop("order_by", [])
        limit = kwargs.pop("limit", None)
        offset = kwargs.pop("offset", None)

        query = (
            select(Tweets)
            .outerjoin(Like, and_(Tweets.id == Like.tweet_id))
            .group_by(Tweets.id)
        )

        for field, value in kwargs.items():
            query = query.filter(and_(getattr(Tweets, field) == value))

        for custom_filter in custom_filters:
            query = query.filter(custom_filter)

        for option in options:
            query = query.options(option)

        if order_by:
            query = query.order_by(*order_by)

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        logger.debug("SQL-запрос перед выполнением: %s", query)

        result = await self.session.execute(query)
        tweets = result.scalars().all()
        logger.debug("Результат фильтрации твитов: %s", tweets)

        return tweets


class MediaRepository(AbstractMediaRepository):
    """
    Repository for managing `Media` entities in the database.

    Provides methods to add, delete, and filter `Media` objects.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            session (AsyncSession): The database session used for executing queries.
        """
        self.session: AsyncSession = session

    async def add(self, media: Media) -> None:
        """
        Add a new media object to the database.

        Args:
            media (Media): The media object to add.
        """
        logger.info("Добавление нового медиа: %s", media)
        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        logger.debug("Медиа добавлено и обновлено: %s", media)

    async def delete(self, media: Media) -> None:
        """
        Delete a media object from the database.

        Args:
            media (Media): The media object to delete.
        """
        logger.info("Удаление медиа: %s", media)
        await self.session.delete(media)
        await self.session.commit()
        logger.debug("Медиа удалено")

    async def filter(self, **kwargs) -> Any:
        """
        Filter media objects based on given conditions.

        Args:
            **kwargs: Filtering parameters, including:
                - options (List): Query options for eager loading or other modifications.
                - custom_filters (List): Custom SQLAlchemy filters.

        Returns:
            Any: A list of media objects matching the filters.
        """
        logger.info("Фильтрация медиа с параметрами: %s", kwargs)
        options: List = kwargs.pop("options", [])
        custom_filters: List = kwargs.pop("custom_filters", [])
        query = select(Media)

        for field, value in kwargs.items():
            query = query.filter(and_(getattr(Media, field) == value))

        for custom_filter in custom_filters:
            query = query.filter(custom_filter)

        for option in options:
            query = query.options(option)

        result = await self.session.execute(query)
        media = result.scalars().all()
        logger.debug("Результат фильтрации медиа: %s", media)

        return media


class TweetMediaRepository(AbstractTweetMediaRepository):
    """
    Repository for managing `TweetMedia` associations in the database.

    Provides methods to add, delete, and filter `TweetMedia` objects.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            session (AsyncSession): The database session used for executing queries.
        """
        self.session: AsyncSession = session

    async def add_all(self, rec: List[TweetMedia]) -> None:
        """
        Add multiple TweetMedia records to the database.

        Args:
            rec (List[TweetMedia]): A list of TweetMedia objects to add.
        """
        logger.info("Добавление нескольких TweetMedia: %s", rec)
        self.session.add_all(rec)
        await self.session.commit()
        logger.debug("TweetMedia добавлены")

    async def delete(self, rec: TweetMedia) -> None:
        """
        Delete a TweetMedia record from the database.

        Args:
            rec (TweetMedia): The TweetMedia object to delete.
        """
        logger.info("Удаление TweetMedia: %s", rec)
        await self.session.delete(rec)
        await self.session.commit()
        logger.debug("TweetMedia удалено")

    async def filter(self, **kwargs) -> Any:
        """
        Filter TweetMedia records based on given conditions.

        Args:
            **kwargs: Filtering parameters, including:
                - options (List): Query options for eager loading or other modifications.

        Returns:
            Any: The first TweetMedia object matching the filters, or None if no match is found.
        """
        logger.info("Фильтрация TweetMedia с параметрами: %s", kwargs)
        options: List = kwargs.pop("options", [])
        query = select(TweetMedia)

        for field, value in kwargs.items():
            query = query.filter(and_(getattr(TweetMedia, field) == value))

        for option in options:
            query = query.options(option)

        result = await self.session.execute(query)
        tweet_media = result.scalars().first()
        logger.debug("Результат фильтрации TweetMedia: %s", tweet_media)

        return tweet_media


class LikeRepository(AbstractLikeRepository):
    """
    Repository for managing `Like` entities in the database.

    Provides methods to add, delete, and filter `Like` objects.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            session (AsyncSession): The database session used for executing queries.
        """
        self.session: AsyncSession = session

    async def add(self, like: Like) -> None:
        """
        Add a new like to the database.

        Args:
            like (Like): The like object to add.
        """
        logger.info("Добавление лайка: %s", like)
        self.session.add(like)
        await self.session.commit()
        logger.debug("Лайк добавлен")

    async def delete(self, like: Like) -> None:
        """
        Delete a like from the database.

        Args:
            like (Like): The like object to delete.
        """
        logger.info("Удаление лайка: %s", like)
        await self.session.delete(like)
        await self.session.commit()
        logger.debug("Лайк удалён")

    async def filter(self, **kwargs) -> Any:
        """
        Filter likes based on given conditions.

        Args:
            **kwargs: Filtering parameters, including:
                - options (List): Query options for eager loading or other modifications.

        Returns:
            Any: The first like object matching the filters, or None if no match is found.
        """
        logger.info("Фильтрация лайков с параметрами: %s", kwargs)
        options: List = kwargs.pop("options", [])
        query = select(Like)

        for field, value in kwargs.items():
            query = query.filter(and_(getattr(Like, field) == value))

        for option in options:
            query = query.options(option)

        result = await self.session.execute(query)
        like = result.scalar_one_or_none()
        logger.debug("Результат фильтрации лайков: %s", like)

        return like
