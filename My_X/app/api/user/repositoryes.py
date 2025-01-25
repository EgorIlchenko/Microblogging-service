from typing import Any, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.config import logger
from ...database.base_repository import (
    AbstractFollowerRepository,
    AbstractUserRepository,
)
from ...database.models.models import Follower, Users


class UserRepository(AbstractUserRepository):
    """
    Repository for managing `Users` entities in the database.

    Provides methods for retrieving user information by specific attributes.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            session (AsyncSession): The database session used for executing queries.
        """
        self.session: AsyncSession = session

    async def get_by_api_key(self, api_key: str) -> Optional[Users]:
        """
        Retrieve a user by their API key.

        Args:
            api_key (str): The API key associated with the user.

        Returns:
            Optional[Users]: The user if found, or None if no user matches the API key.
        """
        logger.info("Запрос пользователя по API-ключу: %s", api_key)
        result = await self.session.execute(
            select(Users).where(Users.api_key == api_key)
        )

        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[Users]:
        """
        Retrieve a user by their unique ID.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            Optional[Users]: The user if found, or None if no user matches the ID.
        """
        logger.info("Запрос пользователя по ID: %s", user_id)
        query = select(Users).where(Users.id == user_id)
        result = await self.session.execute(query)

        return result.scalar_one_or_none()


class FollowerRepository(AbstractFollowerRepository):
    """
    Repository for managing `Follower` entities in the database.

    Provides methods for adding, deleting, and filtering follower relationships.
    """

    def __init__(self, session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session (AsyncSession): The database session used for executing queries.
        """
        self.session: AsyncSession = session

    async def add(self, follow: Follower) -> None:
        """
        Add a new follower relationship to the database.

        Args:
            follow (Follower): The follower relationship to add.
        """
        logger.info("Добавление подписки: %s", follow)
        self.session.add(follow)
        await self.session.commit()
        await self.session.refresh(follow)
        logger.debug("Подписка добавлена и обновлена: %s", follow)

    async def delete(self, follow: Follower) -> None:
        """
        Delete a follower relationship from the database.

        Args:
            follow (Follower): The follower relationship to delete.
        """
        logger.info("Удаление подписки: %s", follow)
        await self.session.delete(follow)
        await self.session.commit()
        logger.debug("Подписка удалена: %s", follow)

    async def get_subscribe(self, **kwargs) -> Optional[Follower]:
        """
        Retrieve a specific follower relationship based on given attributes.

        Args:
            **kwargs: Filtering parameters for the follower relationship.

        Returns:
            Optional[Follower]: The follower relationship if found, or None if no match is found.
        """
        logger.info("Запрос подписки с параметрами: %s", kwargs)
        query = select(Follower)
        for field, value in kwargs.items():
            query = query.filter(and_(getattr(Follower, field) == value))
        result = await self.session.execute(query)
        subscribe = result.scalar_one_or_none()
        logger.debug("Подписка найдена: %s", subscribe)

        return subscribe

    async def filter(self, **kwargs) -> Any:
        """
        Filter follower relationships based on given conditions.

        Args:
            **kwargs: Filtering parameters, including:
                - options (List): Query options for eager loading or other modifications.

        Returns:
            Any: A list of follower relationships matching the filters.
        """
        logger.info("Фильтрация подписок с параметрами: %s", kwargs)
        options: List = kwargs.pop("options", [])
        query = select(Follower)
        for field, value in kwargs.items():
            query = query.filter(and_(getattr(Follower, field) == value))
        for option in options:
            query = query.options(option)
        result = await self.session.execute(query)
        followers = result.scalars().all()
        logger.debug(
            "Фильтрация подписок завершена. Найдено: %d подписок", len(followers)
        )

        return followers
