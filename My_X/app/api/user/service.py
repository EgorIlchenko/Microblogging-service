from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...config.config import logger
from ...database.models.models import Follower, Users
from .repositoryes import FollowerRepository, UserRepository


class UserServices:
    """
    Service layer for managing user-related operations such as subscriptions and retrieving user
    data.

    This class provides methods to handle business logic for user interactions.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the UserServices instance with the required repositories.

        Args:
            session (AsyncSession): The database session for interacting with the database.
        """
        self.user_repo = UserRepository(session)
        self.follow_repo = FollowerRepository(session)

    async def add_subscribe(self, user: Users, id: int):
        """
        Subscribe the current user to another user.

        Args:
            user (Users): The currently authenticated user subscribing to another user.
            id (int): The ID of the user to subscribe to.

        Returns:
            dict: A dictionary indicating the success of the subscription.

        Raises:
            HTTPException:
                - 409 Conflict: If the user tries to subscribe to themselves.
                - 404 Not Found: If the target user does not exist.
        """
        logger.info(
            "Попытка подписки пользователя ID: %s на пользователя ID: %s", user.id, id
        )

        if id == user.id:
            logger.warning(
                "Пользователь ID %s пытается подписаться на самого себя.", user.id
            )
            raise HTTPException(
                status_code=409, detail="You can't subscribe to yourself"
            )

        requested_user: Users | None = await self.user_repo.get_by_id(user_id=id)

        if not requested_user:
            logger.warning("Пользователь ID %s не найден.", id)
            raise HTTPException(status_code=404, detail="User not found")

        new_subscribe: Follower = Follower(
            follower_id=user.id,
            followee_id=id,
        )

        await self.follow_repo.add(new_subscribe)
        logger.info(
            "Подписка успешно добавлена: пользователь ID %s подписался на пользователя ID %s",
            user.id,
            id,
        )

        return {"result": True}

    async def delete_subscribe(self, user: Users, id: int):
        """
        Unsubscribe the current user from another user.

        Args:
            user (Users): The currently authenticated user unsubscribing from another user.
            id (int): The ID of the user to unsubscribe from.

        Returns:
            dict: A dictionary indicating the success of the unsubscription.

        Raises:
            HTTPException:
                - 409 Conflict: If the user tries to unsubscribe from themselves.
                - 404 Not Found: If the target user or subscription does not exist.
        """
        logger.info(
            "Попытка отписки пользователя ID: %s от пользователя ID: %s", user.id, id
        )

        if id == user.id:
            logger.warning(
                "Пользователь ID %s пытается отписаться от самого себя.", user.id
            )
            raise HTTPException(
                status_code=409, detail="You can't unsubscribe from yourself"
            )

        requested_user: Users | None = await self.user_repo.get_by_id(user_id=id)

        if not requested_user:
            logger.warning("Пользователь ID %s не найден.", id)
            raise HTTPException(status_code=404, detail="User not found")

        follow: Optional[Follower] = await self.follow_repo.get_subscribe(
            follower_id=user.id, followee_id=id
        )

        if not follow:
            logger.warning(
                "Подписка не найдена: пользователь ID %s не подписан на пользователя ID %s",
                user.id,
                id,
            )
            raise HTTPException(
                status_code=404, detail="You haven't subscribed to this user yet"
            )

        await self.follow_repo.delete(follow)
        logger.info(
            "Подписка успешно удалена: пользователь ID %s отписался от пользователя ID %s",
            user.id,
            id,
        )

        return {"result": True}

    async def get_my_data(self, user: Users):
        """
        Retrieve data for the currently authenticated user, including followers and following.

        Args:
            user (Users): The currently authenticated user.

        Returns:
            dict: A dictionary containing the user's data, followers, and following.

        Raises:
            HTTPException: If an error occurs while retrieving the user's data.
        """
        logger.info("Получение данных текущего пользователя: ID %s", user.id)
        followers_query = await self.follow_repo.filter(
            followee_id=user.id,
            options=[selectinload(Follower.follower)],
        )

        following_query = await self.follow_repo.filter(
            follower_id=user.id,
            options=[selectinload(Follower.followee)],
        )

        followers: List = [
            {"id": follower.follower.id, "name": follower.follower.name}
            for follower in followers_query
        ]
        followings: List = [
            {"id": following.followee.id, "name": following.followee.name}
            for following in following_query
        ]
        logger.info("Данные текущего пользователя успешно получены: ID %s", user.id)

        return {
            "result": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "followers": followers,
                "following": followings,
            },
        }

    async def get_user_data_by_id(self, id: int):
        """
        Retrieve data for a specific user by their ID, including followers and following.

        Args:
            id (int): The ID of the user to retrieve data for.

        Returns:
            dict: A dictionary containing the user's data, followers, and following.

        Raises:
            HTTPException:
                - 404 Not Found: If the user does not exist.
        """
        logger.info("Получение данных пользователя ID: %s", id)

        requested_user: Users | None = await self.user_repo.get_by_id(user_id=id)

        if not requested_user:
            logger.warning("Пользователь ID %s не найден.", id)
            raise HTTPException(status_code=404, detail="User not found")

        followers_query = await self.follow_repo.filter(
            followee_id=id,
            options=[selectinload(Follower.follower)],
        )

        following_query = await self.follow_repo.filter(
            follower_id=id,
            options=[selectinload(Follower.followee)],
        )

        followers: List = [
            {"id": follower.follower.id, "name": follower.follower.name}
            for follower in followers_query
        ]
        followings: List = [
            {"id": following.followee.id, "name": following.followee.name}
            for following in following_query
        ]
        logger.info("Данные пользователя ID %s успешно получены.", id)

        return {
            "result": True,
            "user": {
                "id": requested_user.id,
                "name": requested_user.name,
                "followers": followers,
                "following": followings,
            },
        }
