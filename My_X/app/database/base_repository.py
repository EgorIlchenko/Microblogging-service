from abc import ABC, abstractmethod
from typing import Any, Optional

from .models.models import Follower, Tweets, Users


class AbstractUserRepository(ABC):
    @abstractmethod
    async def get_by_api_key(self, api_key: str) -> Optional[Users]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[Users]:
        pass


class AbstractFollowerRepository(ABC):
    @abstractmethod
    async def add(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def delete(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def get_subscribe(self, **kwargs) -> Optional[Follower]:
        pass

    @abstractmethod
    async def filter(self, **kwargs) -> Any:
        pass


class AbstractTweetRepository(ABC):
    @abstractmethod
    async def get_by_id(self, tweet_id: int) -> Optional[Tweets]:
        pass

    @abstractmethod
    async def add(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def delete(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def filter(self, **kwargs) -> Any:
        pass


class AbstractMediaRepository(ABC):
    @abstractmethod
    async def add(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def delete(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def filter(self, **kwargs) -> Any:
        pass


class AbstractTweetMediaRepository(ABC):
    @abstractmethod
    async def add_all(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def delete(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def filter(self, **kwargs) -> Any:
        pass


class AbstractLikeRepository(ABC):
    @abstractmethod
    async def add(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def delete(self, obj: Any) -> None:
        pass

    @abstractmethod
    async def filter(self, **kwargs) -> Any:
        pass
