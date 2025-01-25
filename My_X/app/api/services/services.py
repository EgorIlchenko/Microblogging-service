from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.config import logger
from ...database.database import get_session
from ...database.models.models import Users
from ..user.repositoryes import UserRepository


async def get_current_user(
    api_key: str = Header(..., alias="api-key"),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Users:
    """
    Authenticate the current user based on the provided API key.

    This function retrieves the user associated with the given API key from the database
    and validates their existence. If the API key is invalid or the database query fails,
    appropriate HTTP exceptions are raised.

    Args:
        api_key (str): API key provided in the request header (alias: "api-key").
        session (AsyncSession): Database session dependency for executing queries.

    Returns:
        Users: The authenticated user object.

    Raises:
        HTTPException:
            - 401 Unauthorized if the API key is invalid or the user is not found.
            - 500 Internal Server Error if there is an issue with the database query.
    """
    logger.info("Получен запрос на проверку текущего пользователя с API-ключом")

    user_repo: UserRepository = UserRepository(session)
    logger.debug("Инициализирован UserRepository для проверки пользователя")

    try:
        user: Optional[Users] = await user_repo.get_by_api_key(api_key)
        logger.debug("Запрос в базу данных выполнен")
    except Exception as exp:
        logger.error("Ошибка при запросе к базе данных: %s", str(exp))
        raise HTTPException(status_code=500, detail="Internal server error")

    if not user:
        logger.warning("Пользователь с предоставленным API-ключом не найден")
        raise HTTPException(status_code=401, detail="Invalid API Key")

    logger.info("Пользователь успешно аутентифицирован")
    return user
