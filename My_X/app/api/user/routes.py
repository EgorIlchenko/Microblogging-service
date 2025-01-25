from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.config import logger
from ...database.database import get_session
from ...database.models.models import Users
from ..services.services import get_current_user
from .schemas import GeneralAnswer, UserResponse
from .service import UserServices

router: APIRouter = APIRouter(prefix="/api", tags=["users"])


@router.post("/users/{id}/follow", response_model=GeneralAnswer)
async def subscribe_to_a_user(
    id: int,
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Subscribe the current user to another user.

    This endpoint allows an authenticated user to subscribe to another user by their ID.

    Args:
        id (int): The ID of the user to subscribe to.
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        GeneralAnswer: Confirmation of the subscription.

    Raises:
        HTTPException: If an error occurs while creating the subscription.
    """
    logger.info(
        "Запрос на подписку пользователя ID: %s на пользователя ID: %s", user.id, id
    )

    user_service: UserServices = UserServices(session)

    try:
        result = await user_service.add_subscribe(user=user, id=id)
        logger.info(
            "Подписка успешно добавлена: пользователь ID %s подписался на пользователя ID %s",
            user.id,
            id,
        )
        return result
    except Exception as exp:
        logger.error(
            "Ошибка при добавлении подписки пользователя ID %s на пользователя ID %s: %s",
            user.id,
            id,
            str(exp),
        )
        raise


@router.delete("/users/{id}/follow", response_model=GeneralAnswer)
async def delete_subscribe(
    id: int,
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Unsubscribe the current user from another user.

    This endpoint allows an authenticated user to unsubscribe from another user by their ID.

    Args:
        id (int): The ID of the user to unsubscribe from.
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        GeneralAnswer: Confirmation of the unsubscription.

    Raises:
        HTTPException: If an error occurs while deleting the subscription.
    """
    logger.info(
        "Запрос на удаление подписки пользователя ID: %s на пользователя ID: %s",
        user.id,
        id,
    )

    user_service: UserServices = UserServices(session)

    try:
        result = await user_service.delete_subscribe(user=user, id=id)
        logger.info(
            "Подписка успешно удалена: пользователь ID %s отписался от пользователя ID %s",
            user.id,
            id,
        )
        return result
    except Exception as exp:
        logger.error(
            "Ошибка при удалении подписки пользователя ID %s на пользователя ID %s: %s",
            user.id,
            id,
            str(exp),
        )
        raise


@router.get("/users/me", response_model=UserResponse)
async def get_me_data(
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Retrieve the current authenticated user's data.

    This endpoint returns information about the currently authenticated user.

    Args:
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        UserResponse: The current user's data.

    Raises:
        HTTPException: If an error occurs while retrieving the user's data.
    """
    logger.info("Запрос на получение данных текущего пользователя: ID %s", user.id)

    user_service: UserServices = UserServices(session)

    try:
        result = await user_service.get_my_data(user=user)
        logger.info("Данные текущего пользователя успешно получены: ID %s", user.id)
        return result
    except Exception as exp:
        logger.error(
            "Ошибка при получении данных текущего пользователя: ID %s: %s",
            user.id,
            str(exp),
        )
        raise


@router.get("/users/{id}", response_model=UserResponse)
async def get_user_data(
    id: int,
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Retrieve data for a specific user by ID.

    This endpoint allows an authenticated user to get information about another user.

    Args:
        id (int): The ID of the user to retrieve data for.
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        UserResponse: The data of the specified user.

    Raises:
        HTTPException: If an error occurs while retrieving the user's data.
    """
    logger.info(
        "Запрос на получение данных пользователя ID: %s от пользователя ID: %s",
        id,
        user.id,
    )

    user_service: UserServices = UserServices(session)

    try:
        result = await user_service.get_user_data_by_id(id=id)
        logger.info("Данные пользователя успешно получены: ID %s", id)
        return result
    except Exception as exp:
        logger.error("Ошибка при получении данных пользователя ID %s: %s", id, str(exp))
        raise
