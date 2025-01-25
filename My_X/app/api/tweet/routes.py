from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.config import logger
from ...database.database import get_session
from ...database.models.models import Users
from ..services.services import get_current_user
from .schemas import GeneralAnswer, MediaResponse, TweetCreate, TweetOut, TweetResponse
from .service import TweetServices

router: APIRouter = APIRouter(prefix="/api", tags=["tweets"])


@router.post("/tweets", response_model=TweetOut)
async def post_new_tweet(
    tweet: TweetCreate,
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Create a new tweet.

    This endpoint allows an authenticated user to create a new tweet.

    Args:
        tweet (TweetCreate): The tweet data to be created.
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        TweetOut: The details of the created tweet.

    Raises:
        HTTPException: If an error occurs during tweet creation.
    """
    logger.info("Запрос на создание нового твита от пользователя: %s", user.id)
    tweet_service: TweetServices = TweetServices(session)

    try:
        new_tweet = await tweet_service.add_new_tweet(user=user, tweet=tweet)
        logger.info("Новый твит создан: %s", new_tweet["tweet_id"])
        return new_tweet
    except Exception as exp:
        logger.error("Ошибка при создании твита: %s", str(exp))
        raise


@router.post("/medias", response_model=MediaResponse)
async def post_new_media(
    file: UploadFile,
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Upload a new media file.

    This endpoint allows an authenticated user to upload a media file to associate with a tweet.

    Args:
        file (UploadFile): The media file to upload.
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        MediaResponse: The details of the uploaded media.

    Raises:
        HTTPException: If an error occurs during media upload.
    """
    logger.info("Запрос на добавление медиа-файла от пользователя: %s", user.id)
    tweet_service: TweetServices = TweetServices(session)

    try:
        media = await tweet_service.add_media_files(user=user, file=file)
        logger.info("Медиа-файл добавлен: %s", media["media_id"])
        return media
    except Exception as exp:
        logger.error("Ошибка при добавлении медиа-файла: %s", str(exp))
        raise


@router.delete("/tweets/{id}", response_model=GeneralAnswer)
async def delete_tweet(
    id: int,
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Delete a tweet by its ID.

    This endpoint allows an authenticated user to delete their own tweet.

    Args:
        id (int): The unique identifier of the tweet to delete.
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        GeneralAnswer: Confirmation of the tweet deletion.

    Raises:
        HTTPException: If an error occurs during tweet deletion.
    """
    logger.info("Запрос на удаление твита с ID %s от пользователя: %s", id, user.id)
    tweet_service: TweetServices = TweetServices(session)

    try:
        result = await tweet_service.del_tweet(user=user, id=id)
        logger.info("Твит с ID %s удалён", id)
        return result
    except Exception as exp:
        logger.error("Ошибка при удалении твита с ID %s: %s", id, str(exp))
        raise


@router.post("/tweets/{id}/likes", response_model=GeneralAnswer)
async def put_like(
    id: int = Path(..., description="ID of the user to follow"),  # noqa: B008
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Add a like to a tweet.

    This endpoint allows an authenticated user to like a tweet.

    Args:
        id (int): The unique identifier of the tweet to like.
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        GeneralAnswer: Confirmation of the like addition.

    Raises:
        HTTPException: If an error occurs while adding the like.
    """
    logger.info(
        "Запрос на добавление лайка к твиту с ID %s от пользователя: %s", id, user.id
    )
    tweet_service: TweetServices = TweetServices(session)

    try:
        result = await tweet_service.add_like(user=user, id=id)
        logger.info("Лайк добавлен к твиту с ID %s", id)
        return result
    except Exception as exp:
        logger.error("Ошибка при добавлении лайка к твиту с ID %s: %s", id, str(exp))
        raise


@router.delete("/tweets/{id}/likes", response_model=GeneralAnswer)
async def delete_like(
    id: int,
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Remove a like from a tweet.

    This endpoint allows an authenticated user to remove their like from a tweet.

    Args:
        id (int): The unique identifier of the tweet to remove the like from.
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        GeneralAnswer: Confirmation of the like removal.

    Raises:
        HTTPException: If an error occurs while removing the like.
    """
    logger.info(
        "Запрос на удаление лайка с твита с ID %s от пользователя: %s", id, user.id
    )
    tweet_service: TweetServices = TweetServices(session)

    try:
        result = await tweet_service.del_like(user=user, id=id)
        logger.info("Лайк удалён с твита с ID %s", id)
        return result
    except Exception as exp:
        logger.error("Ошибка при удалении лайка с твита с ID %s: %s", id, str(exp))
        raise


@router.get("/tweets", response_model=TweetResponse)
async def get_list_tweets(
    limit: Optional[int] = Query(default=None),  # noqa: B008
    offset: Optional[int] = Query(default=None),  # noqa: B008
    user: Users = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    """
    Retrieve a list of tweets with pagination.

    Args:
        limit (Optional[int]): Number of tweets per page (default: 10).
        offset (Optional[int]): Number of tweets to skip from the start (default: 0).
        user (Users): The currently authenticated user (injected dependency).
        session (AsyncSession): The database session (injected dependency).

    Returns:
        TweetResponse: The paginated list of tweets.
    """
    logger.info("Запрос на получение списка твитов от пользователя: %s", user.id)
    tweet_service: TweetServices = TweetServices(session)

    try:
        tweets = await tweet_service.get_tweets(user=user, limit=limit, offset=offset)
        logger.info(
            "Список твитов успешно получен. Количество твитов: %d",
            len(tweets["tweets"]),
        )
        return tweets
    except Exception as exp:
        logger.error("Ошибка при получении списка твитов: %s", str(exp))
        raise
